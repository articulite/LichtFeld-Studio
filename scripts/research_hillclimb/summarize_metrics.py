"""Strict, candidate-independent summary of one harness run."""
import argparse
import csv
import json
import math
import re
from pathlib import Path


def summarize(run_dir: Path, metrics: Path, output: Path, expected_iteration: int | None = None, expected_heldout: int | None = None) -> dict:
    state = json.loads((run_dir / "state.json").read_text())
    if state.get("status") not in {"evaluating", "complete"} or state.get("train_exit") != 0:
        raise ValueError("run is incomplete or training failed")
    with metrics.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.reader(stream))
    if not rows:
        raise ValueError("metrics.csv is empty")
    if rows[0] and rows[0][0].lower() in {"iteration", "step"}:
        rows = rows[1:]
    if not rows:
        raise ValueError("metrics.csv has no data rows")
    values = rows[-1]
    if len(values) < 6:
        raise ValueError("metrics.csv requires iteration, psnr, ssim, lpips, time_per_image, num_gaussians")
    try:
        iteration = int(values[0]); psnr = float(values[1]); ssim = float(values[2]); lpips = None if values[3] == "" else float(values[3]); time_per_image = float(values[4]); num_gaussians = int(values[5])
    except ValueError as exc:
        raise ValueError("metrics.csv contains non-numeric final metrics") from exc
    if expected_iteration is not None and iteration != expected_iteration:
        raise ValueError(f"final iteration {iteration} != expected {expected_iteration}")
    if any(not math.isfinite(x) for x in (psnr, ssim, time_per_image) if x is not None) or (lpips is not None and not math.isfinite(lpips)):
        raise ValueError("final metrics contain non-finite values")
    if expected_heldout is not None:
        text = (run_dir / "train.log").read_text(encoding="utf-8", errors="replace")
        found = re.findall(r"(?:train\s*\+\s*(\d+)\s+val|train/val split:\s*\d+\s+train,\s*(\d+)\s+val)", text, flags=re.I)
        counts = [int(value) for pair in found for value in pair if value]
        if not counts or counts[-1] != expected_heldout:
            raise ValueError("held-out count is missing or does not match expected count")
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    expected_names = manifest.get("split", {}).get("held_out_images")
    if expected_names:
        per_image = run_dir / f"eval_step_{iteration}" / "per_image_metrics.csv"
        with per_image.open(newline="", encoding="utf-8") as stream:
            image_rows = list(csv.DictReader(stream))
        names = [r["image_name"].replace("\\", "/") for r in image_rows]
        if len(names) != len(set(names)) or set(names) != set(expected_names):
            raise ValueError("evaluated images differ from the frozen held-out split")
        if any(not math.isfinite(float(r[k])) for r in image_rows for k in ("psnr", "ssim")):
            raise ValueError("non-finite per-image metrics")
    perf_path = run_dir / "perf_bench.json"
    perf = json.loads(perf_path.read_text()) if perf_path.is_file() else {}
    result = {"iteration": iteration, "psnr": psnr, "ssim": ssim, "lpips": lpips, "time_per_image": time_per_image, "num_gaussians": num_gaussians, "elapsed_seconds": state.get("elapsed_seconds"), "vram": state.get("vram"), "perf_wall_seconds": perf.get("wall_seconds"), "perf_peak_cuda_used_bytes": perf.get("peak_cuda_used_bytes"), "metrics_rows": len(rows)}
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--metrics", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-iteration", type=int)
    parser.add_argument("--expected-heldout", type=int)
    args = parser.parse_args()
    run = args.run_dir.resolve(); metrics = (args.metrics or run / "metrics.csv").resolve(); output = (args.output or run / "summary.json").resolve()
    try:
        print(json.dumps(summarize(run, metrics, output, args.expected_iteration, args.expected_heldout), indent=2))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
