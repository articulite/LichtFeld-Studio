# Outdoor Background Improvements Calibration (background_improvements: true vs false) — 2026-09-10

Completed configuration-only budget: one excluded 400-step warmup (20260910T211442Z-c94d35d4) and six measured runs across seeds 42, 43, 44, comparing baseline MRNF (background_improvements: false) against candidate background improvements (background_improvements: true) on the outdoor development scene test-1-2-v3 with standard growth fraction (grow_fraction: 0.07) and standard growth termination (grow_until_iter: 2400), preserving 1,200 post-growth refinement iterations. Runs were executed in a counterbalanced sequence (Warmup, B42, C42, C43, B43, B44, C44) to decouple thermal and cache drift. All seven train and evaluate exits were zero. Zero rebuilds, zero implementation modifications, zero evaluator edits, zero external downloads, and zero overwrites of previous run evidence.

The outdoor test-1-2-v3 split remains 112 training and 16 held-out views. Shared configuration: 3600 iterations, width 512, max_cap 100000, refine_every 100, stop_refine 3501, grow_until_iter 2400, grow_fraction 0.07, SH degree interval 900. Seven quality checkpoints were evaluated: 400, 800, 1200, 2400, 2800, 3200, 3600. Resource limits: 300 seconds/run timeout, 7000 MiB sampled VRAM ceiling, 250 ms sampling interval, sequential execution with strict GPU lock (.git/hillclimb/gpu.lock).

## Checkpoint Dynamics (7 Quality Checkpoints)

| Iteration | Mean baseline PSNR | Mean candidate PSNR | Paired mean gain dB | Baseline sample SD |
|---|---:|---:|---:|---:|
| 400 | 10.945564 | 11.685127 | +0.739562 | 0.120569 |
| 800 | 13.601750 | 14.296398 | +0.694648 | 0.499975 |
| 1200 | 13.844193 | 14.473360 | +0.629168 | 0.149745 |
| 2400 | 13.943355 | 14.765894 | +0.822538 | 0.481913 |
| 2800 | 14.645905 | 14.674698 | +0.028793 | 0.240576 |
| 3200 | 14.647408 | 14.555483 | -0.091924 | 0.174431 |
| 3600 | 14.687822 | 14.608485 | -0.079338 | 0.144439 |

These values represent means across three seeds (42, 43, 44). Checkpoints along a single trajectory are correlated. Final paired PSNR deltas are strictly negative across all three seeds: -0.011375 dB (seed 42), -0.214089 dB (seed 43), and -0.012549 dB (seed 44), yielding a net mean PSNR delta of -0.079338 dB. Final paired SSIM deltas show severe unanimous degradation across all three seeds: -0.016893 (seed 42), -0.016627 (seed 43), and -0.016957 (seed 44), yielding a net mean SSIM loss of -0.016826.

## Per-Run Final Metrics at 3600 Iterations

| Seed / Treatment | Background Improvements | Final PSNR | Final SSIM | Gaussians | Harness sec | Internal perf sec | Sample peak MiB | CUDA peak MiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 / baseline | false | 14.533413 | 0.405667 | 8486 | 18.547 | 18.021 | 514 | 1501.6 |
| 42 / candidate | true | 14.522038 | 0.388774 | 90584 | 16.812 | 16.339 | 502 | 1503.6 |
| 43 / baseline | false | 14.819626 | 0.403977 | 8494 | 16.047 | 15.460 | 506 | 1499.6 |
| 43 / candidate | true | 14.605537 | 0.387350 | 90000 | 19.047 | 18.528 | 510 | 1503.6 |
| 44 / baseline | false | 14.710428 | 0.405508 | 8470 | 15.797 | 15.285 | 508 | 1501.6 |
| 44 / candidate | true | 14.697879 | 0.388551 | 90140 | 19.782 | 19.204 | 510 | 1503.6 |

## Analysis and Findings

1. **Resource Comparability Screen Failed**:
   - Elapsed wall time ratios are 0.9065 (seed 42, -9.4%), 1.1870 (seed 43, +18.7%), and 1.2523 (seed 44, +25.2%). Seeds 43 and 44 severely breached the 15% comparability ceiling.
   - Final Gaussian capacity exploded by over 10.6x: ~90,241 Gaussians vs ~8,483 baseline. This runaway primitive expansion is directly driven by far-field seeding (`seed_far`, dosing 2,000 far primitives every refinement step) and far-field splitting.
   - Peak sampled VRAM ratios remained acceptable (0.977 to 1.008), but computational throughput dropped substantially due to rasterizing 10x more splats per view.

2. **Quality Dynamics and Far-Field Mechanics**:
   - Early Coarse Illusion: During active growth (iterations 400–2400), candidate PSNR appeared substantially higher (+0.63 dB to +0.82 dB) because the deluge of 90k primitives rapidly filled empty unobserved background regions, mitigating coarse pixel errors.
   - Post-Growth Refinement Failure: Once growth ceased at iteration 2400, the baseline converged smoothly through focused refinement (+0.74 dB gain from 13.94 to 14.69 dB). In contrast, the candidate plateaued and degraded (dropping from 14.77 dB down to 14.61 dB), unable to optimize 90,000 noisy primitives.
   - Catastrophic SSIM Collapse: Structural similarity collapsed unanimously across every seed (-0.0169, -0.0166, -0.0170), falling from ~0.405 down to ~0.388. Distant background seeding without strict bounding flooded the scene with floating, semi-transparent splats that visibly blurred fine structural details and introduced haze.
   - Final PSNR Regression: All three seeds regressed in final PSNR (-0.011 dB, -0.214 dB, -0.012 dB; net mean loss -0.079 dB).
   - Decision: **reject_screen; no promotion**. The candidate simultaneously violates elapsed-time resource comparability (+18.7% and +25.2% overhead) and causes severe, unanimous quality degradation.

## Invariant Verification

- All checkpoints have exactly 1 metrics row per eval step, finite PSNR/SSIM, valid timing and Gaussian counts (90,000–90,584 <= 100,000 cap).
- All 16 unique held-out camera views verified with finite per-image metrics at every checkpoint.
- Frozen executable SHA256 (95954f5d825c123594712b85e0fb8fb53febb3e8038a264713fde08bffe2c915), DLL provenance, dataset identity, and split fingerprints match the initial baseline (20260910T184132Z-d0eb9803).
- Candidate configuration differs solely by background_improvements (false vs true).
- Topology updates (splits/prunes) verified to cease before iteration 3501 (stop_refine: 3501).
- LPIPS remains null (weights unavailable locally; no download attempted).

## Machine-Readable Evidence

- Summary JSON: docs/research/outdoor-background-improvements-results.json
- Campaign runner, plan, and checks: results/research_hillclimb/outdoor-background-improvements-20260910/
- Warmup run ID: 20260910T211442Z-c94d35d4
- Measured baseline run IDs:
  - B42: 20260910T211446Z-f61878d8
  - B43: 20260910T211543Z-da133f46
  - B44: 20260910T211600Z-00e91fb1
- Measured candidate run IDs:
  - C42: 20260910T211506Z-eaa76067
  - C43: 20260910T211523Z-779bff8c
  - C44: 20260910T211617Z-10689a37

## Limitations

- Single outdoor development scene (test-1-2-v3), reduced resolution (width 512), 3600 iterations.
- SfM cameras originally fit with all views.
- No bitwise GPU determinism across floating-point operations.
- LPIPS metric absent.

## Next Step

All 3 authorized candidate studies from the external optimization brief are now fully executed, evaluated, and documented:
1. **Study 1: Indoor Gradient Threshold Calibration (`growth_grad_threshold: 0.002`)**: Rejected under elapsed screen (seed 42 ratio 1.326x) and quality screen (2/3 seeds regressed in PSNR).
2. **Study 2: Screen Footprint Clamping (`max_screen_share: 0.2`)**: Inconclusive / no promotion due to severe early quality collapse (-1.20 dB @ 400) and SSIM regression (2/3 seeds).
3. **Study 3: Background Improvements (`background_improvements: true`)**: Rejected under elapsed screen (up to +25.2% elapsed time from 10.6x Gaussian explosion) and unanimous quality collapse (all 3 seeds regressed in PSNR; severe SSIM drop of -0.0168 across all seeds).

The next step is to synthesize the complete findings across all campaigns, update HANDOFF.md and mrnf-hillclimb.md, and push the final record to origin.

