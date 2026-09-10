"""Make a frozen screening manifest from the unchanged MRNF benchmark config."""
import argparse
import json
import sys
from pathlib import Path
from prepare_colmap import read_images

ROOT = Path(__file__).resolve().parents[2]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('dataset', type=Path)
    p.add_argument('output', type=Path, help='New directory holding config and experiment manifest')
    p.add_argument('--iterations', type=int, default=1200)
    p.add_argument('--width', type=int, default=512)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--timeout', type=float, default=300)
    p.add_argument('--grow-fraction', type=float, help='Candidate only: requires --baseline-run')
    p.add_argument('--baseline-run', type=Path)
    args = p.parse_args()
    if args.iterations < 400: p.error('screen must cross refinement transitions; use at least 400 iterations')
    if args.grow_fraction is not None and args.baseline_run is None: p.error('candidate needs a completed baseline run')
    if args.baseline_run:
        state=json.loads((args.baseline_run/'state.json').read_text())
        if state.get('status')!='complete': p.error('baseline has not completed successfully')
    dataset=args.dataset.resolve(); output=args.output.resolve()
    split=json.loads((dataset/'manifest.json').read_text())
    records=read_images(dataset/'sparse/0/images.bin')
    held=[r['name'].replace('\\','/') for i,r in enumerate(records) if i%split['test_every']==0]
    actual={r['group'] for i,r in enumerate(records) if i%split['test_every']==0}
    if actual!=set(split['heldout_groups']): p.error('staged modulo split mismatches its manifest')
    config=json.loads((ROOT/'eval/mrnf_optimization_params.json').read_text())
    # Shared screening schedule, identical for every scene and treatment.
    config.update(iterations=args.iterations, max_cap=100000, refine_every=100,
                  stop_refine=args.iterations-99, grow_until_iter=args.iterations*2//3,
                  fill_pacing_iter=0, sh_degree_interval=max(100,args.iterations//4),
                  eval_steps=[args.iterations], save_steps=[], enable_eval=True,
                  enable_save_eval_images=True)
    if args.grow_fraction is not None: config['grow_fraction']=args.grow_fraction
    output.mkdir(parents=True,exist_ok=False)
    cfg=output/'config.json'; cfg.write_text(json.dumps(config,indent=2)+'\n')
    exe=ROOT/'build-windows-release/LichtFeld-Studio.exe'
    train=[str(exe),'--headless','--safe-mode','--no-download','-d',str(dataset),'-o','{run_dir}',
           '--config',str(cfg),'--images','images','--test-every',str(split['test_every']),
           '--resize_factor','1','--max-width',str(args.width),'--eval','--perf-bench',
           '--perf-bench-warmup','100','--log-level','debug']
    candidate=args.grow_fraction is not None
    manifest={
        'source_root':str(ROOT),'kind':'candidate' if candidate else 'baseline',
        'evidence_level':'reduced-resolution and shortened screening only',
        'hypothesis':'Faster gradient-selected capacity growth improves early held-out quality under a fixed resource budget.' if candidate else 'Measure MRNF reference quality, runtime and memory on a grouped held-out split.',
        'expected_effect':'Higher PSNR/SSIM with bounded memory; possible overfitting or runtime regression.' if candidate else 'A valid reference measurement; no improvement claim.',
        'falsification_criterion':'Reject promotion if any scene regresses beyond measured reference variability, runtime/memory are not comparable, or validation fails.',
        'dataset':str(dataset),'split':{'train':split['train_groups'],'held_out':split['heldout_groups'],'held_out_images':held,'identity':split},
        'seed':args.seed,'effective_seed':{'mrnf_topology_noise':args.seed,'tensor_rng':42,'camera_sampler':'0x4c46535f73616d70','determinism':'seeded stochastic choices; floating point GPU determinism not guaranteed'},
        'config':config,'resource_budget':{'timeout_seconds':args.timeout,'vram_sample_seconds':0.25,'max_vram_mib':7000,'target_training_mib':6144},
        'train':{'command':train,'output_dir':'{run_dir}','env':{'LFS_RESEARCH_SEED':str(args.seed)}},
        'evaluate':{'command':[sys.executable,str(ROOT/'scripts/research_hillclimb/summarize_metrics.py'),'{run_dir}','--expected-iteration',str(args.iterations),'--expected-heldout',str(len(held))],'output_dir':'{run_dir}'},
        'provenance_files':[str(f) for f in (ROOT/'build-windows-release').glob('*.dll')],
        'baseline_run':str(args.baseline_run.resolve()) if args.baseline_run else None,
        'decision':'pending'
    }
    (output/'experiment.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(output/'experiment.json')

if __name__=='__main__': main()
