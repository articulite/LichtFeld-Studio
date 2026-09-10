import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/research_hillclimb'))
from decide import assess

class DecisionTests(unittest.TestCase):
    def test_missing_scene_is_retained_as_failure(self):
        with tempfile.TemporaryDirectory() as d:
            r=assess([Path(d)/'missing-baseline'],[Path(d)/'missing-candidate'])
            self.assertFalse(r['promotion']); self.assertEqual(r['decision'],'reject_screen'); self.assertEqual(len(r['pairs']),1)
    def test_positive_screen_does_not_promote(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[Path(d)/'b',Path(d)/'c']
            for i,p in enumerate(paths):
                p.mkdir()
                manifest={k:'same' for k in ['dataset_identity','split','requested_seed','executable_sha256','evaluator_fingerprints','provenance_files']}
                manifest['config']={'grow_fraction':0.07 if i==0 else 0.14}
                (p/'manifest.json').write_text(json.dumps(manifest))
                (p/'state.json').write_text(json.dumps({'status':'complete','elapsed_seconds':10,'vram':{'sampled_peak_mib':1000}}))
                (p/'summary.json').write_text(json.dumps({'psnr':25+i,'ssim':0.8+0.01*i,'lpips':0.2-0.01*i}))
            r=assess([paths[0]],[paths[1]])
            self.assertEqual(r['decision'],'retain_for_repeated_seed_screening'); self.assertFalse(r['promotion'])
    def test_unpaired_coverage_rejected(self):
        with self.assertRaises(ValueError): assess([Path('a')],[])

if __name__=='__main__': unittest.main()
