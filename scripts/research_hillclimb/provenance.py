"""Record source and build provenance without running LichtFeld Studio.

The report deliberately records evidence instead of treating an embedded Git
hash as proof that an executable was built from a clean tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
SOURCE_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cuh", ".cu", ".h", ".hh", ".hpp", ".in",
    ".py", ".cmake", ".json", ".toml", ".bat", ".ps1", ".sh",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def tracked_source_files() -> list[Path]:
    names = git("ls-files", "--cached", "--others", "--exclude-standard").splitlines()
    return sorted(
        ROOT / name for name in names
        if Path(name).suffix.lower() in SOURCE_SUFFIXES and (ROOT / name).is_file()
    )


def source_digest(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(str(path.relative_to(ROOT)).replace("\\", "/").encode())
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256(path)))
        digest.update(b"\n")
    return digest.hexdigest()


def build_metadata(build_dir: Path) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for relative in ("include/git_version.h", "CMakeCache.txt", "build.ninja"):
        path = build_dir / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if relative.endswith("git_version.h"):
            for key in ("GIT_COMMIT_HASH_SHORT", "GIT_TAGGED_VERSION"):
                match = re.search(rf"#define\s+{key}\s+\"([^\"]*)\"", text)
                if match:
                    metadata[key] = match.group(1)
        elif relative == "CMakeCache.txt":
            for key in (
                "CMAKE_BUILD_TYPE", "CMAKE_CXX_COMPILER", "CMAKE_CUDA_COMPILER",
                "CMAKE_GENERATOR", "VCPKG_OVERLAY_TRIPLETS",
            ):
                match = re.search(rf"^{re.escape(key)}:[^=]*=(.*)$", text, re.MULTILINE)
                if match:
                    metadata[key] = match.group(1).strip()
        else:
            match = re.search(r"-DLFS_CONFIGURED_GIT_COMMIT_HASH_SHORT=([^\s]+)", text)
            if match:
                metadata["NINJA_CONFIGURED_GIT_COMMIT_HASH_SHORT"] = match.group(1)
    return metadata


def runtime_files(build_dir: Path) -> list[Path]:
    # Keep this bounded to shipped runtime locations; omit dependency caches and
    # import libraries, which are not loaded by the application executable.
    roots = [build_dir, build_dir / "bin", build_dir / "src" / "python", build_dir / "extensions"]
    files: set[Path] = set()
    for root in roots:
        if root.is_dir():
            files.update(path for path in root.glob("*.dll") if path.is_file())
    exe = build_dir / "LichtFeld-Studio.exe"
    if exe.is_file():
        files.add(exe)
    return sorted(files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, default=ROOT / "build-windows-release")
    parser.add_argument("--output", type=Path, help="JSON output path; stdout when omitted")
    args = parser.parse_args()
    build_dir = args.build_dir.resolve()

    status = git("status", "--porcelain=v1")
    diff = git("diff", "--binary", "--no-ext-diff")
    sources = tracked_source_files()
    runtime = runtime_files(build_dir)
    head = git("rev-parse", "HEAD")
    report = {
        "schema": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": str(ROOT),
        "git": {
            "head": head,
            "status_porcelain": status.splitlines(),
            "dirty": bool(status),
            "diff_sha256": hashlib.sha256(diff.encode()).hexdigest(),
            "diff_bytes": len(diff.encode()),
        },
        "build_dir": str(build_dir),
        "build_metadata": build_metadata(build_dir),
        "executable_and_runtime": [
            {"path": str(path.relative_to(build_dir)).replace("\\", "/"), "sha256": sha256(path), "bytes": path.stat().st_size}
            for path in runtime
        ],
        "source": {
            "file_count": len(sources),
            "aggregate_sha256": source_digest(sources),
            "files": [
                {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path)}
                for path in sources
            ],
        },
        "assessment": {
            "embedded_commit_equals_head": build_metadata(build_dir).get("GIT_COMMIT_HASH_SHORT", "") == head[:8],
            "clean_tree_at_audit": not bool(status),
            "interpretation": "Commit equality is evidence only; inspect dirty/build records before using the executable as a clean baseline.",
        },
    }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
