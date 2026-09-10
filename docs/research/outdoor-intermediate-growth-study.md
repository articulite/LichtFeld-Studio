# Outdoor Intermediate Growth Dynamics (grow_fraction: 0.10) — 2026-09-10

Completed configuration-only budget: one excluded 400-step warmup (20260910T192745Z-d78d8c28) and six measured runs across seeds 42, 43, 44, comparing baseline growth fraction (grow_fraction: 0.07) against intermediate growth fraction (grow_fraction: 0.10) with standard growth termination (grow_until_iter: 2400), preserving 1,200 post-growth refinement iterations. Runs were executed in a counterbalanced sequence (Warmup, B42, C42, C43, B43, B44, C44) to decouple thermal and cache drift. All seven train and evaluate exits were zero. Zero rebuilds, zero implementation modifications, zero evaluator edits, zero external downloads, and zero overwrites of previous run evidence.

The smaller outdoor 	est-1-2-v3 split remains 112 training and 16 held-out views. Shared configuration: 3600 iterations, width 512, max_cap 100000, refine_every 100, stop_refine 3501, grow_until_iter 2400, SH degree interval 900. Seven quality checkpoints were evaluated: 400, 800, 1200, 2400, 2800, 3200, 3600. Resource limits: 300 seconds/run timeout, 7000 MiB sampled VRAM ceiling, 250 ms sampling interval, sequential execution with strict GPU lock (.git/hillclimb/gpu.lock).

## Checkpoint Dynamics (7 Quality Checkpoints)

| Iteration | Mean baseline PSNR | Mean candidate PSNR | Paired mean gain dB | Baseline sample SD |
|---|---:|---:|---:|---:|
| 400 | 11.138560 | 11.206162 | +0.067603 | 0.150181 |
| 800 | 13.190955 | 13.446558 | +0.255603 | 0.362841 |
| 1200 | 13.742771 | 13.988860 | +0.246089 | 0.344709 |
| 2400 | 13.983481 | 14.314425 | +0.330944 | 0.089284 |
| 2800 | 14.512702 | 14.728057 | +0.215355 | 0.186357 |
| 3200 | 14.537361 | 14.572705 | +0.035344 | 0.119030 |
| 3600 | 14.542782 | 14.664720 | +0.121937 | 0.053244 |

These values represent means across three seeds (42, 43, 44). Checkpoints along a single trajectory are correlated. Final paired PSNR deltas are -0.009214 dB (seed 42), +0.137233 dB (seed 43), and +0.237793 dB (seed 44). Final paired SSIM deltas are -0.001216 (seed 42), +0.002110 (seed 43), and +0.004367 (seed 44).

## Per-Run Final Metrics at 3600 Iterations

| Seed / Treatment | Grow Fraction | Final SSIM | Gaussians | Harness sec | Internal perf sec | Sample peak MiB | CUDA peak MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| 42 / baseline | 0.07 | 0.404389 | 8486 | 13.093 | 12.725 | 504 | 1497.6 |
| 42 / candidate | 0.10 | 0.403173 | 15885 | 13.750 | 13.406 | 508 | 1477.6 |
| 43 / baseline | 0.07 | 0.403706 | 8496 | 13.110 | 12.775 | 508 | 1501.6 |
| 43 / candidate | 0.10 | 0.405816 | 15853 | 13.875 | 13.494 | 516 | 1509.6 |
| 44 / baseline | 0.07 | 0.400022 | 8467 | 13.047 | 12.669 | 500 | 1469.6 |
| 44 / candidate | 0.10 | 0.404389 | 15941 | 13.906 | 13.522 | 516 | 1509.6 |

## Analysis and Findings

1. **Resource Comparability Screen Passed**:
   - Elapsed time ratios are 1.0503 (seed 42, +5.0%), 1.0584 (seed 43, +5.8%), and 1.0658 (seed 44, +6.6%). All pairs fall comfortably inside the predeclared 15% comparability ceiling.
   - This directly resolves the key failure mode of the previous growth study (grow_fraction: 0.14), which inflated runtime by +18–20% due to an over-expansion to 34.6k Gaussians.
   - At grow_fraction: 0.10, final Gaussian capacity reaches ~15,893 (1.87x baseline), achieving a balanced capacity increase without degrading computational throughput.
   - Sampled peak VRAM ratios are 1.0079, 1.0157, and 1.0320 (+0.8% to +3.2%), well below the 10% memory ceiling.
   - In-process CUDA memory usage remained bounded (~1477–1510 MiB).

2. **Quality Dynamics & Screening Decision**:
   - Net mean PSNR delta across all 3 seeds is positive (+0.121937 dB), and positive at all 7 quality checkpoints across the entire training trajectory.
   - Paired quality gains are strong and positive on 2 of 3 seeds: seed 43 gained +0.137233 dB PSNR and +0.002110 SSIM; seed 44 gained +0.237793 dB PSNR and +0.004367 SSIM.
   - However, Seed 42 exhibited a small regression (-0.009214 dB PSNR, -0.001216 SSIM). While this delta is small relative to baseline variation (baseline SD is 0.053244 dB), our predeclared falsification criterion requires consistent improvement across all seeds without regressions.
   - Consequently, the candidate does not satisfy the unanimous dominance condition required for promotion.
   - Decision: **inconclusive / no promotion**. Intermediate growth (0.10) successfully controls elapsed cost (+5–6.6%) while expanding capacity and driving positive mean quality gains (+0.122 dB), but does not yet meet the strict bar for candidate promotion due to seed 42 variability.

## Invariant Verification

- All checkpoints have exactly 1 metrics row per eval step, finite PSNR/SSIM, valid timing and Gaussian counts (8,467–15,941 <= 100,000 cap).
- All 16 unique held-out camera views verified with finite per-image metrics at every checkpoint.
- Frozen executable SHA256 (95954f5d825c123594712b85e0fb8fb53febb3e8038a264713fde08bffe2c915), DLL provenance, dataset identity, and split fingerprints match the initial baseline (20260910T184132Z-d0eb9803).
- Candidate configuration differs solely by grow_fraction (0.07 vs 0.10).
- Topology updates (splits/prunes) verified to cease before iteration 3501 (stop_refine: 3501).
- LPIPS remains null (weights unavailable locally; no download attempted).

## Machine-Readable Evidence

- Summary JSON: docs/research/outdoor-intermediate-growth-results.json
- Campaign runner, plan, and checks: 
esults/research_hillclimb/intermediate-growth-20260910/
- Warmup run ID: 20260910T192745Z-d78d8c28
- Measured baseline run IDs:
  - B42: 20260910T192748Z-6e03044b
  - B43: 20260910T192832Z-3676ea09
  - B44: 20260910T192846Z-f06dc53e
- Measured candidate run IDs:
  - C42: 20260910T192802Z-f5f2fe46
  - C43: 20260910T192817Z-08d64f48
  - C44: 20260910T192900Z-38873c9e

## Limitations

- Single outdoor development scene (	est-1-2-v3), reduced resolution (width 512), 3600 iterations.
- SfM cameras originally fit with all views.
- No bitwise GPU determinism across floating-point operations.
- LPIPS metric absent.

## Next Step

Budget exhausted; no automatic expansion. Having established that (1) grow_fraction: 0.10 passes resource comparability (+5–6.6% elapsed time) and achieves net positive quality gain (+0.122 dB mean PSNR) across the outdoor trajectory, but exhibits small seed variance, the most informative next campaign should evaluate whether this intermediate growth rate (0.10 vs 0.07) generalizes to the indoor scene sparse-cubic-v3 across repeated seeds (42/43/44) under matched schedule settings, or test whether a fine-tuned growth rate (e.g. 0.09) or adaptive densification threshold eliminates the seed 42 regression.
