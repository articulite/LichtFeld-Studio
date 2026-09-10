# Outdoor Screen Footprint Clamping (max_screen_share: 0.2) — 2026-09-10

Completed configuration-only budget: one excluded 400-step warmup (20260910T210900Z-6192ca35) and six measured runs across seeds 42, 43, 44, comparing baseline screen footprint clamping (max_screen_share: 0.3) against tightened clamping (max_screen_share: 0.2) on the outdoor development scene test-1-2-v3 with standard growth fraction (grow_fraction: 0.07) and standard growth termination (grow_until_iter: 2400), preserving 1,200 post-growth refinement iterations. Runs were executed in a counterbalanced sequence (Warmup, B42, C42, C43, B43, B44, C44) to decouple thermal and cache drift. All seven train and evaluate exits were zero. Zero rebuilds, zero implementation modifications, zero evaluator edits, zero external downloads, and zero overwrites of previous run evidence.

The outdoor test-1-2-v3 split remains 112 training and 16 held-out views. Shared configuration: 3600 iterations, width 512, max_cap 100000, refine_every 100, stop_refine 3501, grow_until_iter 2400, grow_fraction 0.07, SH degree interval 900. Seven quality checkpoints were evaluated: 400, 800, 1200, 2400, 2800, 3200, 3600. Resource limits: 300 seconds/run timeout, 7000 MiB sampled VRAM ceiling, 250 ms sampling interval, sequential execution with strict GPU lock (.git/hillclimb/gpu.lock).

## Checkpoint Dynamics (7 Quality Checkpoints)

| Iteration | Mean baseline PSNR | Mean candidate PSNR | Paired mean gain dB | Baseline sample SD |
|---|---:|---:|---:|---:|
| 400 | 11.168204 | 9.970455 | -1.197749 | 0.385448 |
| 800 | 13.540939 | 12.657974 | -0.882965 | 0.291797 |
| 1200 | 13.897662 | 13.382474 | -0.515188 | 0.204813 |
| 2400 | 14.205800 | 14.208985 | +0.003185 | 0.152419 |
| 2800 | 14.660950 | 14.784551 | +0.123601 | 0.046304 |
| 3200 | 14.688233 | 14.806572 | +0.118339 | 0.050349 |
| 3600 | 14.702075 | 14.787305 | +0.085230 | 0.049042 |

These values represent means across three seeds (42, 43, 44). Checkpoints along a single trajectory are correlated. Final paired PSNR deltas are +0.105772 dB (seed 42), -0.010642 dB (seed 43), and +0.160560 dB (seed 44), yielding a net mean PSNR delta of +0.085230 dB. Final paired SSIM deltas are -0.001906 (seed 42), -0.001835 (seed 43), and +0.001865 (seed 44), regressing in 2 of 3 seeds (net mean SSIM delta: -0.000625).

## Per-Run Final Metrics at 3600 Iterations

| Seed / Treatment | Max Screen Share | Final PSNR | Final SSIM | Gaussians | Harness sec | Internal perf sec | Sample peak MiB | CUDA peak MiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 / baseline | 0.3 | 14.730936 | 0.405164 | 8482 | 16.141 | 15.717 | 506 | 1499.6 |
| 42 / candidate | 0.2 | 14.836708 | 0.403258 | 8691 | 15.781 | 15.338 | 506 | 1499.6 |
| 43 / baseline | 0.3 | 14.729837 | 0.401683 | 8475 | 15.672 | 15.195 | 506 | 1499.6 |
| 43 / candidate | 0.2 | 14.719195 | 0.399848 | 8694 | 14.218 | 13.843 | 514 | 1499.6 |
| 44 / baseline | 0.3 | 14.645451 | 0.402437 | 8462 | 15.781 | 15.334 | 508 | 1501.6 |
| 44 / candidate | 0.2 | 14.806011 | 0.404302 | 8687 | 15.813 | 15.377 | 506 | 1499.6 |

## Analysis and Findings

1. **Resource Comparability Screen Passed**:
   - Elapsed wall time ratios are 0.9779 (seed 42, -2.2%), 0.9069 (seed 43, -9.3%), and 1.0030 (seed 44, +0.3%). Candidate runs were ~3.7% faster on average, safely passing within the +/-15% comparability band.
   - Final Gaussian capacity increased moderately from ~8,473 to ~8,691 (+2.57%, ratio 1.026x) due to oversized coarse splats being aggressively split.
   - Peak sampled VRAM ratios are 1.000, 1.016, and 0.996 (+1.6% to -0.4%), well within the 10% memory ceiling.
   - In-process CUDA memory remained stable (~1499.6–1501.6 MiB).

2. **Quality Dynamics and Screen Footprint Mechanics**:
   - Clamping max screen share from 0.3 to 0.2 penalizes primitives that project to >20% of viewport area. In the early training regime (iterations 400–1200), this triggered premature splitting of broad coverage splats before high-frequency detail had formed.
   - Consequently, early quality collapsed severely: -1.198 dB at iteration 400, -0.883 dB at iteration 800, and -0.515 dB at iteration 1200.
   - As training progressed and Gaussians densified toward iteration 2400, the deficit disappeared (+0.003 dB at iteration 2400).
   - During post-growth refinement (iterations 2400–3600), the smaller primitives converged effectively, yielding strong late PSNR gains: +0.124 dB at 2800, +0.118 dB at 3200, and +0.085 dB at 3600.
   - However, structural fidelity (SSIM) suffered: 2 out of 3 seeds regressed (-0.0019 in seed 42, -0.0018 in seed 43), with a net mean SSIM loss of -0.000625. Furthermore, seed 43 experienced a slight final PSNR regression (-0.0106 dB).
   - Decision: **inconclusive / no promotion**. While tighter footprint clamping ultimately refines peak PSNR in 2 seeds (+0.106 dB, +0.161 dB), the severe early disruption (-1.20 dB) and final SSIM regressions (2/3 seeds) preclude promoting `max_screen_share: 0.2` as an unconditional win.

## Invariant Verification

- All checkpoints have exactly 1 metrics row per eval step, finite PSNR/SSIM, valid timing and Gaussian counts (8,687–8,694 <= 100,000 cap).
- All 16 unique held-out camera views verified with finite per-image metrics at every checkpoint.
- Frozen executable SHA256 (95954f5d825c123594712b85e0fb8fb53febb3e8038a264713fde08bffe2c915), DLL provenance, dataset identity, and split fingerprints match the initial baseline (20260910T184132Z-d0eb9803).
- Candidate configuration differs solely by max_screen_share (0.3 vs 0.2).
- Topology updates (splits/prunes) verified to cease before iteration 3501 (stop_refine: 3501).
- LPIPS remains null (weights unavailable locally; no download attempted).

## Machine-Readable Evidence

- Summary JSON: docs/research/outdoor-screen-share-02-results.json
- Campaign runner, plan, and checks: results/research_hillclimb/outdoor-screen-share-02-20260910/
- Warmup run ID: 20260910T210900Z-6192ca35
- Measured baseline run IDs:
  - B42: 20260910T210904Z-0e17b068
  - B43: 20260910T210953Z-42ce8ddb
  - B44: 20260910T211010Z-955f1aa1
- Measured candidate run IDs:
  - C42: 20260910T210921Z-f910eab7
  - C43: 20260910T210938Z-4c3307bd
  - C44: 20260910T211027Z-8ce421f9

## Limitations

- Single outdoor development scene (test-1-2-v3), reduced resolution (width 512), 3600 iterations.
- SfM cameras originally fit with all views.
- No bitwise GPU determinism across floating-point operations.
- LPIPS metric absent.

## Next Step

Budget exhausted; no automatic expansion. Having established that:
1. `growth_grad_threshold: 0.002` benefits outdoor (+0.089 dB mean PSNR, unanimous SSIM gain) but regresses indoor (-0.001 dB PSNR, runtime ratio 1.326x), and
2. `max_screen_share: 0.2` causes severe early trajectory collapse (-1.20 dB @ 400) and SSIM regression (2/3 seeds) despite late PSNR recovery (+0.085 dB),
the next most informative campaign in the optimization brief is Study 3: Background Improvements & Ratio-Rank Guidance (`background_improvements: true` vs `false`) on the outdoor development scene `test-1-2-v3`.
