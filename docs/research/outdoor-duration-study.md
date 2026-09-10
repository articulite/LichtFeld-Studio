# Outdoor Growth Duration Dynamics — 2026-09-10

Completed configuration-only budget: one excluded 400-step warmup (`20260910T191624Z-17274ab5`) and six measured runs across seeds 42, 43, 44, comparing baseline growth duration (`grow_until_iter: 2400`) against extended growth duration (`grow_until_iter: 3200`) at fixed baseline `grow_fraction: 0.07`. To remove the thermal/cache order confounding identified in the previous study, runs were executed in a counterbalanced sequence (Warmup, B42, C42, C43, B43, B44, C44). All seven train and evaluate exits were zero. Zero rebuilds, zero implementation modifications, zero evaluator edits, zero external downloads, and zero overwrites of previous run evidence.

The smaller outdoor `test-1-2-v3` split remains 112 training and 16 held-out views. Shared configuration: 3600 iterations, width 512, max_cap 100000, refine_every 100, stop_refine 3501, grow_fraction 0.07, SH degree interval 900. Seven quality checkpoints were evaluated: 400, 800, 1200, 2400, 2800, 3200, 3600. Resource limits: 300 seconds/run timeout, 7000 MiB sampled VRAM ceiling, 250 ms sampling interval, sequential execution with strict GPU lock (`.git/hillclimb/gpu.lock`).

## Checkpoint Dynamics (7 Quality Checkpoints)

| Iteration | Mean baseline PSNR | Mean candidate PSNR | Paired mean gain dB | Baseline sample SD |
|---|---:|---:|---:|---:|
| 400 | 11.135678 | 11.210864 | +0.075186 | 0.291009 |
| 800 | 13.538589 | 13.159465 | -0.379124 | 0.266317 |
| 1200 | 13.830239 | 13.572891 | -0.257349 | 0.328704 |
| 2400 | 13.855231 | 14.201913 | +0.346681 | 0.219488 |
| 2800 | 14.744383 | 14.775894 | +0.031511 | 0.255413 |
| 3200 | 14.739877 | 14.585647 | -0.154229 | 0.245674 |
| 3600 | 14.830011 | 14.742428 | -0.087583 | 0.280923 |

These values represent means across three seeds (42, 43, 44). Checkpoints along a single trajectory are correlated. Final paired PSNR deltas are -0.173623 dB (seed 42), +0.273036 dB (seed 43), and -0.362161 dB (seed 44). Final paired SSIM deltas are -0.000623 (seed 42), +0.002309 (seed 43), and -0.003821 (seed 44).

## Per-Run Final Metrics at 3600 Iterations

| Seed / Treatment | Grow Until | Final SSIM | Gaussians | Harness sec | Internal perf sec | Sample peak MiB | CUDA peak MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| 42 / baseline | 2400 | 0.406344 | 8492 | 14.734 | 14.225 | 498 | 1489.6 |
| 42 / candidate | 3200 | 0.405721 | 14114 | 15.188 | 14.672 | 516 | 1509.6 |
| 43 / baseline | 2400 | 0.403083 | 8438 | 14.938 | 14.426 | 506 | 1499.6 |
| 43 / candidate | 3200 | 0.405392 | 14049 | 14.875 | 14.370 | 516 | 1509.6 |
| 44 / baseline | 2400 | 0.408705 | 8519 | 15.937 | 15.446 | 500 | 1489.6 |
| 44 / candidate | 3200 | 0.404884 | 14088 | 14.437 | 13.968 | 516 | 1509.6 |

## Analysis and Findings

1. **Resource Comparability Screen Passed**:
   - Elapsed time ratios are 1.0308 (seed 42, +3.1%), 0.9958 (seed 43, -0.4%), and 0.9059 (seed 44, -9.4%). All pairs fall comfortably inside the predeclared 15% comparability band.
   - The counterbalanced execution order (BC, CB, BC) broke the systematic ~18–20% slowdown seen when candidates always ran second in the previous campaign.
   - Sampled peak VRAM ratios are 1.0361, 1.0198, and 1.0320 (+2.0% to +3.6%), well inside the 10% memory screening band.
   - Internal CUDA peak rose only by ~10–20 MiB (1509.6 MiB vs 1489.6–1499.6 MiB).
   - Final Gaussian capacity expanded moderately to ~14,084 (1.66x baseline), avoiding the 4.08x explosion (34.7k) caused by `grow_fraction: 0.14`.

2. **Quality Failure and Falsification**:
   - Despite passing the resource comparability screen, extending growth duration to 3200 failed the quality screening criteria.
   - Two out of three seeds suffered quality regressions in both PSNR and SSIM (seed 42: -0.174 dB, seed 44: -0.362 dB). The mean final PSNR delta is net negative (-0.088 dB).
   - Checkpoint dynamics reveal why: between iterations 2400 and 3200, the candidate continued adding Gaussians (reaching 14,084 at step 3200). This caused a quality dip at iteration 3200 (-0.154 dB delta) because newly spawned Gaussians disrupted scene coherence. With only 400 iterations remaining (3200 to 3600) before completion, the model had insufficient refinement steps to optimize and prune the newly added primitives. In contrast, the baseline had 1200 uninterrupted post-growth iterations (2400 to 3600), allowing its 8,483 Gaussians to converge cleanly to 14.830 dB mean PSNR.

Decision: **reject extended growth duration; no promotion**. Extending growth to 3200 is resource-comparable but counterproductive under this schedule length, as late-stage Gaussian creation truncates necessary post-growth refinement.

## Invariant Verification

- All checkpoints have exactly 1 metrics row per eval step, finite PSNR/SSIM, valid timing and Gaussian counts (8,438–14,114 <= 100,000 cap).
- All 16 unique held-out camera views verified with finite per-image metrics at every checkpoint.
- Frozen executable SHA256 (`95954f5d825c123594712b85e0fb8fb53febb3e8038a264713fde08bffe2c915`), DLL provenance, dataset identity, and split fingerprints match the initial baseline (`20260910T184132Z-d0eb9803`).
- Candidate configuration differs solely by `grow_until_iter` (2400 vs 3200).
- Topology updates (splits/prunes) verified to cease before iteration 3501 (`stop_refine: 3501`).
- LPIPS remains null (weights unavailable locally; no download attempted).

## Machine-Readable Evidence

- Summary JSON: `docs/research/outdoor-duration-results.json`
- Campaign runner, plan, and checks: `results/research_hillclimb/duration-study-20260910/`
- Warmup run ID: `20260910T191624Z-17274ab5`
- Measured baseline run IDs:
  - B42: `20260910T191628Z-f716675d`
  - B43: `20260910T191715Z-a63fe301`
  - B44: `20260910T191731Z-3c25458f`
- Measured candidate run IDs:
  - C42: `20260910T191644Z-c9238faa`
  - C43: `20260910T191700Z-fc56121d`
  - C44: `20260910T191748Z-ebcdc8f8`

## Limitations

- Single outdoor development scene (`test-1-2-v3`), reduced resolution (width 512), 3600 iterations.
- SfM cameras originally fit with all views.
- No bitwise GPU determinism across floating-point operations.
- LPIPS metric absent.

## Next Step

Budget exhausted; no automatic expansion. Having established that (1) doubling `grow_fraction` to 0.14 exceeds the 15% elapsed cost screen and (2) delaying growth termination to 3200 truncates post-growth refinement and harms quality, the most informative next campaign should evaluate whether higher initial capacity (`init_num_pts` or intermediate `grow_fraction` e.g. 0.10) combined with the standard 2/3 growth cutoff (leaving 1200 post-growth refinement steps) can capture quality gains within the 15% runtime band, or test the indoor scene `sparse-cubic-v3` across repeated seeds.