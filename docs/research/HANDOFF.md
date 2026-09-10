# Provider-neutral handoff: MRNF hill climb

## Status
Latest indoor intermediate growth campaign COMPLETE, 2026-09-10. No pending build or GPU job. Read `indoor-intermediate-growth-study.md` and `indoor-intermediate-growth-results.json` first. Seven new successful runs (one warmup, six measured), zero failures; fresh budget exhausted. Candidate (`grow_fraction: 0.10` vs baseline `0.07` on indoor `sparse-cubic-v3` at standard `grow_until_iter: 2400`) achieves unanimous quality dominance across all three seeds (+0.185 dB, +0.276 dB, +0.145 dB; mean PSNR gain +0.201847 dB; SSIM +0.003). However, Gaussian count expanded to 96.5k (close to 100k cap), causing seed 42 elapsed time ratio to reach 1.1589 (+15.89%), breaching the strict 15% elapsed-cost comparability ceiling. REJECT UNDER SCREEN / NO PROMOTION. All previous runs (initial 4-run screen, 7-run outdoor growth fraction, 7-run outdoor growth duration, 7-run outdoor intermediate growth) remain immutable preserved evidence.

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

## Latest campaign: Indoor Intermediate Growth (0.10)
Configuration-only indoor `sparse-cubic-v3`, seeds 42/43/44, baseline `grow_fraction: 0.07` vs candidate `0.10` at fixed `grow_until_iter: 2400`, 3600 iterations, width 512, cap 100000. Seven quality checkpoints: 400, 800, 1200, 2400, 2800, 3200, 3600. Counterbalanced execution order: Warmup, B42, C42, C43, B43, B44, C44.

New run IDs:
- Warmup (400 iters, seed 42): `20260910T193412Z-1cc9a886`
- B42: `20260910T193416Z-d70de4cc`
- C42: `20260910T193436Z-119c7a42`
- C43: `20260910T193459Z-f6b0836a`
- B43: `20260910T193520Z-94669d55`
- B44: `20260910T193540Z-dc5e36b5`
- C44: `20260910T193601Z-838acda7`

Local plan/runner/checks: `results/research_hillclimb/indoor-intermediate-growth-20260910/`.
Decision: **reject under screen; no promotion**. The candidate achieved unanimous quality dominance across all three seeds on indoor data (+0.185 dB, +0.276 dB, +0.145 dB; mean PSNR delta +0.202 dB; SSIM +0.003). However, Gaussian count expanded to 96,408 (1.77x baseline, approaching 100k cap), causing seed 42 elapsed time to increase by +15.89% (21.88s vs 18.89s), breaching the strict 15% comparability ceiling.

Next exact read-only command: `Get-Content docs/research/indoor-intermediate-growth-study.md`. No pending training command.

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