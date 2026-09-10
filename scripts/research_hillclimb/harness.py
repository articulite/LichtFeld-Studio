"""Resumable experiment runner for the hill-climbing research loop.

The runner deliberately treats training and evaluation as separate commands. It
records enough provenance to make a result auditable and never infers success
from an output file left by an earlier run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import secrets
import shlex
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


REQUIRED = {
    "hypothesis", "expected_effect", "falsification_criterion", "train",
    "evaluate", "dataset", "split", "seed", "config", "resource_budget",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8")


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def source_snapshot(root: Path) -> dict[str, str]:
    commit = _git(root, "rev-parse", "HEAD")
    diff = _git(root, "diff", "--no-ext-diff", "--binary", "HEAD")
    return {
        "git_commit": commit,
        "git_diff_sha256": hashlib.sha256(diff.encode()).hexdigest(),
        "git_diff": diff,
    }


def dataset_identity(dataset: Any, root: Path) -> dict[str, Any]:
    """Return stable identity without copying a potentially huge dataset."""
    value = str(dataset)
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    result: dict[str, Any] = {"declared": value, "resolved": str(path.resolve())}
    if path.is_file():
        result.update({"kind": "file", "sha256": sha256_file(path), "bytes": path.stat().st_size})
    elif path.is_dir():
        entries = sorted(p for p in path.rglob("*") if p.is_file())
        digest = hashlib.sha256()
        for entry in entries:
            digest.update(str(entry.relative_to(path)).replace("\\", "/").encode())
            digest.update(sha256_file(entry).encode())
        result.update({"kind": "directory", "file_count": len(entries), "listing_sha256": digest.hexdigest()})
    else:
        result["kind"] = "missing"
    return result


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors = [f"missing required field: {key}" for key in sorted(REQUIRED - manifest.keys())]
    for field in ("train", "evaluate"):
        if not isinstance(manifest.get(field), dict) or not manifest[field].get("command"):
            errors.append(f"{field}.command must be a non-empty list or string")
        elif manifest[field].get("output_dir") != "{run_dir}":
            errors.append(f"{field}.output_dir must be '{{run_dir}}' so artifacts cannot be stale")
        elif "{run_dir}" not in " ".join(_command(manifest[field]["command"])):
            errors.append(f"{field}.command must reference {{run_dir}} for isolated artifacts")
    budget = manifest.get("resource_budget")
    if not isinstance(budget, dict):
        errors.append("resource_budget must be an object")
    else:
        try:
            timeout = float(budget.get("timeout_seconds"))
            if not math.isfinite(timeout) or timeout <= 0:
                errors.append("resource_budget.timeout_seconds must be finite and positive")
        except (TypeError, ValueError):
            errors.append("resource_budget.timeout_seconds is required and must be finite")
    split = manifest.get("split")
    if not isinstance(split, dict) or not split.get("train") or not split.get("held_out"):
        errors.append("split.train and split.held_out must be non-empty arrays")
    elif set(split["train"]) & set(split["held_out"]):
        errors.append("split.train and split.held_out must be disjoint")
    try:
        interval = float(budget.get("vram_sample_seconds", 1.0)) if isinstance(budget, dict) else 0
        if not math.isfinite(interval) or interval <= 0:
            errors.append("resource_budget.vram_sample_seconds must be finite and positive")
    except (TypeError, ValueError):
        errors.append("resource_budget.vram_sample_seconds must be finite and positive")
    if not isinstance(manifest.get("config"), dict):
        errors.append("config must be an object")
    return errors


class GpuLock:
    def __init__(self, path: Path):
        self.path = path
        self.handle = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.handle = self.path.open("x", encoding="utf-8")
        except FileExistsError as exc:
            raise RuntimeError(f"GPU lock is held: {self.path}; unlock explicitly after auditing the owner") from exc
        self.handle.write(json.dumps({"pid": os.getpid(), "started_at": datetime.now(timezone.utc).isoformat()}))
        self.handle.flush()
        return self

    def __exit__(self, *_):
        if self.handle:
            self.handle.close()
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


class VramSampler:
    def __init__(self, interval: float = 1.0, output: Path | None = None):
        self.interval = interval
        self.output = output
        self.samples: list[dict[str, Any]] = []
        self.stop = threading.Event()
        self.thread: threading.Thread | None = None

    def _sample(self):
        while not self.stop.is_set():
            try:
                raw = subprocess.check_output(
                    ["nvidia-smi", "--id=0", "--query-gpu=memory.used,memory.free,memory.total", "--format=csv,noheader,nounits"],
                    text=True, stderr=subprocess.DEVNULL, timeout=5,
                )
                used, free, total = [int(v.strip()) for v in raw.strip().split(",")]
                self.samples.append({"at": time.time(), "used_mib": used, "free_mib": free, "total_mib": total})
            except (OSError, subprocess.SubprocessError, ValueError):
                self.samples.append({"at": time.time(), "used_mib": None})
            if self.output:
                with self.output.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(self.samples[-1]) + "\n")
            self.stop.wait(self.interval)

    def __enter__(self):
        self.thread = threading.Thread(target=self._sample, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=max(1.0, self.interval * 2))

    def summary(self) -> dict[str, Any]:
        observed = [s["used_mib"] for s in self.samples if s["used_mib"] is not None]
        return {
            "sampled_peak_mib": max(observed) if observed else None,
            "sample_count": len(self.samples),
            "valid_sample_count": len(observed),
            "measurement": "sampled peak from nvidia-smi; unavailable means no valid sample",
        }


def _command(value: Any) -> list[str]:
    return value if isinstance(value, list) else shlex.split(str(value), posix=(os.name != "nt"))


def _command_fingerprints(value: Any, root: Path) -> list[dict[str, str]]:
    result = []
    for token in _command(value):
        path = Path(token)
        if not path.is_absolute():
            path = (root / path).resolve()
        if path.is_file():
            result.append({"path": str(path), "sha256": sha256_file(path)})
    return result


def _expand_run_dir(value: str, output: Path) -> str:
    return value.replace("{run_dir}", str(output))


def _run_stage(stage: str, spec: dict[str, Any], output: Path, timeout: float | None, default_cwd: Path, sampler=None, max_vram=None) -> int:
    command = [_expand_run_dir(item, output) for item in _command(spec["command"])]
    log = output / f"{stage}.log"
    if log.exists():
        attempt = 2
        while (output / f"{stage}.attempt{attempt}.log").exists():
            attempt += 1
        log = output / f"{stage}.attempt{attempt}.log"
    env = os.environ.copy()
    env.update({str(k): str(v) for k, v in spec.get("env", {}).items()})
    cwd = Path(spec.get("cwd", default_cwd))
    if not cwd.is_absolute():
        cwd = (default_cwd / cwd).resolve()
    with log.open("w", encoding="utf-8") as stream:
        stream.write("$ " + " ".join(shlex.quote(x) for x in command) + "\n")
        stream.flush()
        try:
            proc = subprocess.Popen(command, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT)
            _write_json(output / f"{stage}.process.json", {"pid": proc.pid, "command": command, "started_at": time.time()})
            try:
                deadline = time.monotonic() + timeout if timeout is not None else float("inf")
                while proc.poll() is None:
                    if max_vram and sampler and (sampler.summary()["sampled_peak_mib"] or 0) >= max_vram:
                        stream.write(f"\nVRAM limit reached: {max_vram} MiB\n")
                        proc.kill(); proc.wait()
                        return 125
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise subprocess.TimeoutExpired(command, timeout)
                    try:
                        return proc.wait(timeout=min(0.5, remaining))
                    except subprocess.TimeoutExpired:
                        continue
                return proc.returncode
            except subprocess.TimeoutExpired:
                stream.write(f"\nTIMEOUT after {timeout}s\n")
                proc.kill()
                proc.wait()
                return 124
            except BaseException:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait()
                raise
        except OSError as exc:
            stream.write(f"\nEXECUTION ERROR: {exc}\n")
            return 127


def _write_json(path: Path, value: Any):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(_json_bytes(value) + b"\n")
    os.replace(temporary, path)


def run(manifest_path: Path, output_root: Path, resume: Path | None = None, dry_run: bool = False) -> int:
    output_root = output_root.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError("; ".join(errors))
    root = Path(manifest.get("source_root", manifest_path.parent)).resolve()
    if resume:
        run_dir = resume.resolve()
        recorded_hash_path = run_dir / "manifest.sha256"
        if not recorded_hash_path.is_file() or recorded_hash_path.read_text(encoding="utf-8").strip() != sha256_file(run_dir / "manifest.json"):
            raise ValueError("resume run manifest has been modified")
        immutable = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        if immutable.get("input_manifest_sha256") != sha256_file(manifest_path):
            raise ValueError("resume manifest does not match immutable run manifest")
        resolved = immutable
        current_source = source_snapshot(root)
        if current_source["git_commit"] != resolved["source"]["git_commit"] or current_source["git_diff_sha256"] != resolved["source"]["git_diff_sha256"]:
            raise ValueError("resume source commit or diff fingerprint changed")
        if dataset_identity(manifest["dataset"], root) != resolved["dataset_identity"]:
            raise ValueError("resume dataset fingerprint changed")
        if _command_fingerprints(manifest["evaluate"]["command"], root) != resolved["evaluator_fingerprints"]:
            raise ValueError("resume evaluator fingerprint changed")
        if _command_fingerprints(manifest["train"]["command"], root) != resolved["train_fingerprints"]:
            raise ValueError("resume training command fingerprint changed")
        if _command_fingerprints(manifest.get("provenance_files", []), root) != resolved.get("provenance_files", []):
            raise ValueError("resume runtime provenance fingerprint changed")
    else:
        output_root.mkdir(parents=True, exist_ok=True)
        run_dir = output_root / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4))
        run_dir.mkdir()
        resolved = dict(manifest)
        resolved.update({
            "input_manifest_sha256": sha256_file(manifest_path),
            "source": source_snapshot(root),
            "dataset_identity": dataset_identity(manifest["dataset"], root),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "requested_seed": manifest["seed"],
            "effective_seed": manifest.get("effective_seed", "unknown"),
        })
        executable = _command(manifest["train"]["command"])[0]
        executable_path = Path(executable)
        if not executable_path.is_absolute():
            executable_path = (root / executable_path).resolve()
        resolved["executable_sha256"] = sha256_file(executable_path) if executable_path.is_file() else "unavailable"
        resolved["evaluator_fingerprints"] = _command_fingerprints(manifest["evaluate"]["command"], root)
        resolved["train_fingerprints"] = _command_fingerprints(manifest["train"]["command"], root)
        resolved["provenance_files"] = _command_fingerprints(manifest.get("provenance_files", []), root)
        _write_json(run_dir / "manifest.json", resolved)
        (run_dir / "manifest.sha256").write_text(sha256_file(run_dir / "manifest.json") + "\n", encoding="utf-8")
    if dry_run:
        print(json.dumps({"run_dir": str(run_dir), "manifest": resolved}, indent=2))
        return 0
    state_path = run_dir / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"status": "pending"}
    if resume and state.get("status") in {"training", "evaluating"}:
        raise ValueError("interrupted run is not resumable; start a new unique run")
    if state.get("status") == "failed":
        raise ValueError("terminal failed run cannot be resumed; start a new unique run to retry")
    timeout = resolved.get("resource_budget", {}).get("timeout_seconds")
    lock_path = root / ".git" / "hillclimb" / "gpu.lock"
    experiment_started = time.monotonic()
    previous_elapsed = float(state.get("elapsed_seconds", 0))
    previous_vram = state.get("vram", {})
    deadline = experiment_started + float(timeout) - previous_elapsed
    def record_resources(sampler):
        measured = sampler.summary()
        peaks = [x for x in (previous_vram.get("sampled_peak_mib"), measured.get("sampled_peak_mib")) if x is not None]
        measured["sampled_peak_mib"] = max(peaks) if peaks else None
        for key in ("sample_count", "valid_sample_count"):
            measured[key] += previous_vram.get(key, 0)
        state["vram"] = measured
        state["elapsed_seconds"] = previous_elapsed + time.monotonic() - experiment_started
    with GpuLock(lock_path), VramSampler(float(resolved.get("resource_budget", {}).get("vram_sample_seconds", 1.0)), run_dir / "vram.jsonl") as sampler:
        if state.get("train_exit") is not None and state["train_exit"] != 0:
            return int(state["train_exit"])
        if state.get("train_exit") is None:
            state["status"] = "training"
            _write_json(state_path, state)
            code = _run_stage("train", resolved["train"], run_dir, max(0.001, deadline - time.monotonic()), root, sampler, resolved["resource_budget"].get("max_vram_mib"))
            state["train_exit"] = code
            state["status"] = "training_complete" if code == 0 else "failed"
            record_resources(sampler)
            _write_json(state_path, state)
            if code != 0:
                return code
        if state.get("eval_exit") is None:
            state["status"] = "evaluating"
            _write_json(state_path, state)
            code = _run_stage("evaluate", resolved["evaluate"], run_dir, max(0.001, deadline - time.monotonic()), root, sampler, resolved["resource_budget"].get("max_vram_mib"))
            state["eval_exit"] = code
            state["status"] = "complete" if code == 0 else "failed"
            record_resources(sampler)
            _write_json(state_path, state)
            return code
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("manifest", type=Path)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("manifest", type=Path)
    run_parser.add_argument("--output-root", type=Path, default=Path("results/research_hillclimb"))
    run_parser.add_argument("--resume", type=Path)
    run_parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.action == "validate":
            errors = validate_manifest(json.loads(args.manifest.read_text(encoding="utf-8")))
            if errors:
                for error in errors:
                    print(error, file=sys.stderr)
                return 2
            print("manifest valid")
            return 0
        return run(args.manifest, args.output_root, args.resume, args.dry_run)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
