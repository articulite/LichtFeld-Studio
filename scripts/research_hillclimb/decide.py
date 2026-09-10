"""Compare complete, paired screening runs without hiding failed scenes."""
import argparse
import json
from pathlib import Path


def assess(baselines, candidates):
    if len(baselines) != len(candidates) or not baselines:
        raise ValueError('supply one baseline and candidate per scene')
    pairs=[]
    for baseline,candidate in zip(baselines,candidates):
        row={'baseline':str(baseline),'candidate':str(candidate),'issues':[]}
        try:
            bm=json.loads((baseline/'manifest.json').read_text()); cm=json.loads((candidate/'manifest.json').read_text())
            bs=json.loads((baseline/'state.json').read_text()); cs=json.loads((candidate/'state.json').read_text())
            if bs.get('status')!='complete' or cs.get('status')!='complete':
                raise ValueError('failed or incomplete run; scene retained as failure')
            b=json.loads((baseline/'summary.json').read_text()); c=json.loads((candidate/'summary.json').read_text())
            for key in ['dataset_identity','split','requested_seed','executable_sha256','evaluator_fingerprints','provenance_files']:
                if bm[key]!=cm[key]: row['issues'].append(f'mismatched {key}')
            differences={k for k in bm['config'].keys()|cm['config'].keys() if bm['config'].get(k)!=cm['config'].get(k)}
            if differences!={'grow_fraction'}: row['issues'].append(f'candidate mutation scope: {sorted(differences)}')
            btime=bs['elapsed_seconds']; ctime=cs['elapsed_seconds']
            bmem=bs['vram']['sampled_peak_mib']; cmem=cs['vram']['sampled_peak_mib']
            row.update(psnr_delta=c['psnr']-b['psnr'],ssim_delta=c['ssim']-b['ssim'],
                       lpips_delta=(c['lpips']-b['lpips']) if c['lpips'] is not None and b['lpips'] is not None else None,
                       elapsed_ratio=ctime/btime, sampled_memory_ratio=cmem/bmem if bmem and cmem else None,
                       baseline_metrics=b,candidate_metrics=c)
            if ctime/btime > 1.15: row['issues'].append('elapsed cost exceeds screening comparability band (15%)')
            if not bmem or not cmem: row['issues'].append('missing VRAM measurement')
            elif cmem/bmem > 1.10: row['issues'].append('sampled memory exceeds screening comparability band (10%)')
        except (OSError,ValueError,KeyError,TypeError) as e:
            row['issues'].append(str(e))
        pairs.append(row)
    # This is only a screen: no statistical promotion from single-seed evidence.
    issues=any(p['issues'] for p in pairs)
    dominates=all(p.get('psnr_delta',-1)>0 and p.get('ssim_delta',-1)>=0 and (p.get('lpips_delta') is None or p['lpips_delta']<=0) for p in pairs)
    return {'decision':'reject_screen' if issues else ('retain_for_repeated_seed_screening' if dominates else 'inconclusive_no_promotion'),
            'promotion':False,'reason':'Screening only; repeated-seed variability and target-setting confirmation are required.',
            'resource_bands':'Predeclared screening bands, not calibrated quality regression tolerances.', 'pairs':pairs}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,action='append',required=True)
    p.add_argument('--candidate',type=Path,action='append',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); result=assess(a.baseline,a.candidate)
    with a.output.open('x',encoding='utf-8') as f: json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
