# Provider-neutral handoff: MRNF hill climb

## Status
Latest outdoor screen footprint clamping (max_screen_share: 0.2) campaign COMPLETE, 2026-09-10. No pending build or GPU job. Read `outdoor-screen-share-02-study.md` and `outdoor-screen-share-02-results.json` first. Seven new successful runs (one warmup, six measured), zero failures; fresh budget exhausted. Candidate (`max_screen_share: 0.2` vs baseline `0.3` at standard `grow_fraction: 0.07`, `grow_until_iter: 2400` on outdoor `test-1-2-v3`) passed resource comparability screens (elapsed ratio 0.963x, -3.7% faster, peak VRAM 1.004x) and achieved late PSNR gains (+0.085 dB mean PSNR). However, tightening max screen footprint caused severe early quality collapse (-1.20 dB @ iter 400, -0.88 dB @ iter 800) due to premature splitting of broad primitives, and regressed final SSIM across 2 of 3 seeds (net mean SSIM delta -0.000625). INCONCLUSIVE; NO PROMOTION. All previous runs remain immutable preserved evidence.

User authorized local bounded experiments on branch `codex/hillclimb-mrnf`, Luna subagents with primary review, resumability, cost restraint, and smaller dataset first. Luna work was reviewed/repaired; agents then hit usage limits. No upstream merge, large downloads, purchases or automation authorized.

## Historical campaigns summary
All runs under `results/research_hillclimb/runs`:
- **Initial 1200-iteration screen** (seeds 42, 1200 iters, baseline .07 vs candidate .14):
  - Outdoor baseline `20260910T184132Z-d0eb9803`
  - Indoor baseline `20260910T184239Z-91cb6818`
  - Outdoor candidate `20260910T184307Z-0ec35d21`
  - Indoor candidate `20260910T184321Z-100bcfc7`
- **Outdoor growth fraction campaign** (seeds 42/43/44, 3600 iters, baseline .07 vs candidate .14):
  - Warmup `20260910T190129Z-5ed6bfbc`
  - B42 `20260910T190133Z-d57991e9`, C42 `20260910T190145Z-4d929aff`
  - B43 `20260910T190201Z-da3866f5`, C43 `20260910T190214Z-b373c376`
  - B44 `20260910T190230Z-ac9e1443`, C44 `20260910T190243Z-ffdd8176`
  - Result: Rejected under 15% elapsed-cost screen (+18-20% time from 4.08x Gaussians).
- **Outdoor growth duration campaign** (seeds 42/43/44, 3600 iters, baseline 2400 vs candidate 3200):
  - Warmup `20260910T191624Z-17274ab5`
  - B42 `20260910T191628Z-f716675d`, C42 `20260910T191644Z-c9238faa`
  - C43 `20260910T191700Z-fc56121d`, B43 `20260910T191715Z-a63fe301`
  - B44 `20260910T191731Z-3c25458f`, C44 `20260910T191748Z-ebcdc8f8`
  - Result: Rejected under quality screen (-0.088 dB mean PSNR delta from truncated post-growth refinement).
- **Outdoor intermediate growth campaign** (seeds 42/43/44, 3600 iters, baseline .07 vs candidate .10):
  - Warmup `20260910T192745Z-d78d8c28`
  - B42 `20260910T192748Z-6e03044b`, C42 `20260910T192802Z-f5f2fe46`
  - C43 `20260910T192817Z-08d64f48`, B43 `20260910T192832Z-3676ea09`
  - B44 `20260910T192846Z-f06dc53e`, C44 `20260910T192900Z-38873c9e`
  - Result: Inconclusive / no promotion (passed elapsed cost +5-7%, net mean gain +0.122 dB, but seed 42 regressed -0.009 dB).
- **Indoor intermediate growth campaign** (seeds 42/43/44, 3600 iters, baseline .07 vs candidate .10):
  - Warmup `20260910T193412Z-1cc9a886`
  - B42 `20260910T193416Z-d70de4cc`, C42 `20260910T193436Z-119c7a42`
  - C43 `20260910T193459Z-f6b0836a`, B43 `20260910T193520Z-94669d55`
  - B44 `20260910T193540Z-dc5e36b5`, C44 `20260910T193601Z-838acda7`
  - Result: Rejected under screen (unanimous gain +0.202 dB mean PSNR, but seed 42 elapsed ratio 1.1589 exceeded 15% band).
- **Indoor calibrated growth campaign** (seeds 42/43/44, 3600 iters, baseline .07 vs candidate .085):
  - Warmup `20260910T194116Z-835c2a28`
  - B42 `20260910T194120Z-62259ee7`, C42 `20260910T194139Z-0a542599`
  - C43 `20260910T194200Z-19d382bb`, B43 `20260910T194219Z-bafbd608`
  - B44 `20260910T194238Z-c4734796`, C44 `20260910T194258Z-11dddab3`
  - Result: Retained for repeated-seed screening (passed elapsed cost +4-5%, unanimous quality dominance +0.074 dB mean PSNR across all seeds).
- **Outdoor calibrated growth campaign** (seeds 42/43/44, 3600 iters, baseline .07 vs candidate .085):
  - Warmup `20260910T204913Z-f371d1a5`
  - B42 `20260910T204917Z-8c8a9bd9`, C42 `20260910T204933Z-7b6b52e7`
  - C43 `20260910T204949Z-37861259`, B43 `20260910T205005Z-c1c489b0`
  - B44 `20260910T205021Z-c8d13805`, C44 `20260910T205037Z-9e6e6bb3`
  - Result: Rejected under quality screen (-0.100 dB mean PSNR delta from underfitting).
- **Outdoor gradient threshold calibration campaign** (seeds 42/43/44, 3600 iters, baseline .003 vs candidate .002):
  - Warmup `20260910T205601Z-9d8c09e8`
  - B42 `20260910T205605Z-23480790`, C42 `20260910T205620Z-7a29ccb6`
  - C43 `20260910T205635Z-8634e754`, B43 `20260910T205651Z-ee72233f`
  - B44 `20260910T205706Z-38e38129`, C44 `20260910T205722Z-c6848fb2`
  - Result: Inconclusive / no promotion (passed elapsed cost -1.9%, net mean gain +0.089 dB, unanimous SSIM gain, but seed 43 regressed -0.091 dB).
- **Indoor gradient threshold calibration campaign** (seeds 42/43/44, 3600 iters, baseline .003 vs candidate .002):
  - Warmup `20260910T210320Z-9061a5a2`
  - B42 `20260910T210324Z-afa2f47d`, C42 `20260910T210342Z-03123179`
  - C43 `20260910T210404Z-104cc783`, B43 `20260910T210428Z-44c966f1`
  - B44 `20260910T210451Z-1e9a523e`, C44 `20260910T210512Z-52823e9d`
  - Result: Rejected under elapsed screen (seed 42 ratio 1.326x exceeded 15% ceiling) and quality screen (2/3 seeds regressed in PSNR).

## Latest campaign: Outdoor Screen Footprint Clamping (0.2)
Configuration-only outdoor `test-1-2-v3`, seeds 42/43/44, baseline `max_screen_share: 0.3` vs candidate `0.2` at fixed `grow_fraction: 0.07`, `grow_until_iter: 2400`, 3600 iterations, width 512, cap 100000. Seven quality checkpoints: 400, 800, 1200, 2400, 2800, 3200, 3600. Counterbalanced execution order: Warmup, B42, C42, C43, B43, B44, C44.

New run IDs:
- Warmup (400 iters, seed 42): `20260910T210900Z-6192ca35`
- B42: `20260910T210904Z-0e17b068`
- C42: `20260910T210921Z-f910eab7`
- C43: `20260910T210938Z-4c3307bd`
- B43: `20260910T210953Z-42ce8ddb`
- B44: `20260910T211010Z-955f1aa1`
- C44: `20260910T211027Z-8ce421f9`

Local plan/runner/checks: `results/research_hillclimb/outdoor-screen-share-02-20260910/`.
Decision: **inconclusive_no_promotion**. The candidate passed elapsed cost (0.907–1.003, -3.7% mean) and sampled VRAM screens (0.996–1.016) with Gaussian count rising slightly (+2.6% to 8,691). While it achieved late PSNR convergence (+0.085 dB mean gain), it caused severe early trajectory degradation (-1.198 dB @ 400) and regressed final SSIM in 2 of 3 seeds (net mean delta -0.000625).

Next exact read-only command: `Get-Content docs/research/outdoor-screen-share-02-study.md`. No pending training command.

## Data and interruption safety
Valid staging only: `test-1-2-v3` outdoor 112 train / 16 eval; `sparse-cubic-v3` indoor 126 / 18. Same parent `results/research_hillclimb/staging`. v2 INVALID and unused. Whole captures held out, adjacent captures excluded. Images are hardlinks: never edit staged files.
One GPU job at a time. Every existing run used 300 second timeout, 250 ms sampling, 7000 MiB sampled cutoff. Do not remove `.git/hillclimb/gpu.lock` until owner AND child PIDs from train.process.json/evaluate.process.json are confirmed dead. Failed/interrupted stages require fresh attempts; clean-stage resume is fingerprint-checked. No full RNG checkpoint continuation guarantee.

## Build and code
Implementation commits: 4e91df09 opt-in seed; 6f10bca3 harness; a6c19643 adapter. Final successful build `.git/hillclimb/build-final.log`; provenance `.git/hillclimb/built-provenance.json`. Source/executable/DLL hashes frozen per run (`95954f5d825c123594712b85e0fb8fb53febb3e8038a264713fde08bffe2c915`). Avoid rebuilding after documentation commits: evaluated implementation remains a6c19643.
Windows RTX 5060 laptop 8GB, MSVC 14.44, CUDA 12.8, SM120. Original 73 cached vcpkg ABIs restored at original `build-windows-release/vcpkg_installed` prefix. `VCPKG_MANIFEST_INSTALL=OFF`. Do not blindly reinstall dependencies.

## Context and build-monitoring efficiency
- Start from this handoff and compact result JSON; read older research history only for a specific unresolved question.
- Run approved, bounded experiment batches sequentially with one GPU job at a time. Review one compact table per batch: exit status, quality checkpoints, Gaussian count, elapsed time, memory and decision.
- Redirect full build/training output to files. Prefer completion waits; avoid repeated log reads while a process is healthy.
- Automatically extract metrics and sanity checks.
- Freeze executable and evaluator across JSON-only experiments.
- Update the handoff at meaningful checkpoints with completed run IDs, decision, blockers and exact next command. Keep it current instead of appending contradictory status histories.