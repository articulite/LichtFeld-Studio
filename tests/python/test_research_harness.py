import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "research_hillclimb"))
import harness  # noqa: E402


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "dataset").mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def manifest(self, train=0, evaluate=0, timeout=10):
        py = sys.executable
        return {"hypothesis": "schedule reduces floaters", "expected_effect": "higher PSNR", "falsification_criterion": "no gain", "train": {"command": [py, "-c", f"print('train'); raise SystemExit({train})", "{run_dir}"], "output_dir": "{run_dir}"}, "evaluate": {"command": [py, "-c", f"print('eval'); raise SystemExit({evaluate})", "{run_dir}"], "output_dir": "{run_dir}"}, "dataset": str(self.root / "dataset"), "split": {"train": ["a"], "held_out": ["b"]}, "seed": 7, "config": {"iterations": 10}, "resource_budget": {"timeout_seconds": timeout, "vram_sample_seconds": 0.01}}

    def write(self, value):
        path = self.root / "manifest.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_validate_requires_held_out_split(self):
        value = self.manifest(); del value["split"]["held_out"]
        self.assertTrue(any("held_out" in e for e in harness.validate_manifest(value)))

    def test_validate_rejects_overlap_and_nan_budget(self):
        value = self.manifest(); value["split"]["held_out"] = ["a"]; value["resource_budget"]["timeout_seconds"] = "nan"
        errors = harness.validate_manifest(value)
        self.assertTrue(any("disjoint" in e for e in errors)); self.assertTrue(any("finite" in e for e in errors))

    def test_gpu_lock_contention_is_fail_closed(self):
        lock_path = self.root / "gpu.lock"
        with harness.GpuLock(lock_path):
            with self.assertRaisesRegex(RuntimeError, "GPU lock is held"):
                with harness.GpuLock(lock_path):
                    pass

    def test_interrupted_state_cannot_rerun(self):
        path = self.write(self.manifest()); output = self.root / "runs"
        self.assertEqual(harness.run(path, output, dry_run=True), 0)
        run = next(output.iterdir())
        (run / "state.json").write_text(json.dumps({"status": "training"}))
        with self.assertRaisesRegex(ValueError, "interrupted"):
            harness.run(path, output, resume=run)

    def test_dry_run_records_provenance(self):
        path = self.write(self.manifest()); output = self.root / "runs"
        self.assertEqual(harness.run(path, output, dry_run=True), 0)
        run = next(output.iterdir())
        record = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn("source", record); self.assertEqual(record["effective_seed"], "unknown")

    def test_failure_exit_is_preserved_and_cannot_resume(self):
        path = self.write(self.manifest(train=9)); output = self.root / "runs"
        self.assertEqual(harness.run(path, output), 9)
        run = next(output.iterdir())
        with self.assertRaisesRegex(ValueError, "terminal failed"):
            harness.run(path, output, resume=run)

    def test_timeout_returns_124_and_keeps_log(self):
        value = self.manifest(timeout=0.05); value["train"]["command"] = [sys.executable, "-c", "import time; time.sleep(5)", "{run_dir}"]
        path = self.write(value)
        self.assertEqual(harness.run(path, self.root / "runs"), 124)
        run = next((self.root / "runs").iterdir())
        self.assertIn("TIMEOUT", (run / "train.log").read_text())

    def test_resume_rejects_changed_manifest(self):
        value = self.manifest(evaluate=4); path = self.write(value); output = self.root / "runs"
        self.assertEqual(harness.run(path, output), 4)
        run = next(output.iterdir()); value["seed"] = 8; path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "does not match"):
            harness.run(path, output, resume=run)


if __name__ == "__main__":
    unittest.main()
