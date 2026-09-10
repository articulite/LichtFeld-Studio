import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "research_hillclimb"))
import summarize_metrics  # noqa: E402


class SummarizeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.run = Path(self.tmp.name)
        (self.run / "state.json").write_text(json.dumps({"status": "evaluating", "train_exit": 0, "elapsed_seconds": 2, "vram": {"sampled_peak_mib": 100}}))
        (self.run / "train.log").write_text("Loaded dataset into scene: 10 train + 3 val cameras\n")
        (self.run / "metrics.csv").write_text("iteration,psnr,ssim,lpips,time_per_image,num_gaussians\n10,25.0,0.9,0.2,0.1,100\n")
        (self.run / "perf_bench.json").write_text(json.dumps({"wall_seconds": 4, "peak_cuda_used_bytes": 123}))

    def tearDown(self): self.tmp.cleanup()

    def test_evaluating_state_is_summarizable(self):
        result = summarize_metrics.summarize(self.run, self.run / "metrics.csv", self.run / "summary.json", 10, 3)
        self.assertEqual(result["psnr"], 25.0); self.assertEqual(result["perf_wall_seconds"], 4)

    def test_wrong_iteration_rejected(self):
        with self.assertRaisesRegex(ValueError, "iteration"):
            summarize_metrics.summarize(self.run, self.run / "metrics.csv", self.run / "summary.json", 11)

    def test_missing_metrics_rejected(self):
        (self.run / "metrics.csv").unlink()
        with self.assertRaises((OSError, ValueError)):
            summarize_metrics.summarize(self.run, self.run / "metrics.csv", self.run / "summary.json")

    def test_failed_train_rejected(self):
        (self.run / "state.json").write_text(json.dumps({"status": "evaluating", "train_exit": 7}))
        with self.assertRaisesRegex(ValueError, "training"):
            summarize_metrics.summarize(self.run, self.run / "metrics.csv", self.run / "summary.json")


if __name__ == "__main__": unittest.main()
