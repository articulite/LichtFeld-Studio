# Provider-neutral handoff: MRNF hill climb

## Status
Latest outdoor growth duration campaign COMPLETE, 2026-09-10. No pending build or GPU job. Read `outdoor-duration-study.md` and `outdoor-duration-results.json` first. Seven new successful runs (one warmup, six measured), zero failures; fresh budget exhausted. Candidate (extended growth to 3200 vs 2400) passes resource comparability (elapsed ratios 0.91-1.03) under counterbalanced ordering, but regresses quality across 2 of 3 seeds with -0.087583 dB net mean PSNR delta. NO PROMOTION. All previous runs (initial 4-run screen and 7-run growth fraction study) remain immutable preserved evidence.

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

## Latest campaign: Outdoor Growth Duration
Configuration-only outdoor `test-1-2-v3`, seeds 42/43/44, baseline `grow_until_iter: 2400` vs candidate `3200` at fixed `grow_fraction: 0.07`, 3600 iterations, width 512, cap 100000. Seven quality checkpoints: 400, 800, 1200, 2400, 2800, 3200, 3600. Counterbalanced execution order: Warmup, B42, C42, C43, B43, B44, C44.

New run IDs:
- Warmup (400 iters, seed 42): `20260910T191624Z-17274ab5`
- B42: `20260910T191628Z-f716675d`
- C42: `20260910T191644Z-c9238faa`
- C43: `20260910T191700Z-fc56121d`
- B43: `20260910T191715Z-a63fe301`
- B44: `20260910T191731Z-3c25458f`
- C44: `20260910T191748Z-ebcdc8f8`

Local plan/runner/checks: `results/research_hillclimb/duration-study-20260910/`.
Decision: **reject extended duration; no promotion**. The candidate successfully passed the 15% elapsed cost screen (elapsed ratios 1.0308, 0.9958, 0.9059) and expanded Gaussians moderately to 14,084 (1.66x baseline), but regressed final quality across 2 of 3 seeds (seed 42: -0.174 dB, seed 44: -0.362 dB, mean delta: -0.088 dB). Checkpoint dynamics confirm that continuing growth up to iteration 3200 leaves insufficient post-growth refinement steps (400 vs 1200 in baseline), truncating convergence.

Next exact read-only command: `Get-Content docs/research/outdoor-duration-study.md`. No pending training command.

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