# Indoor Intermediate Growth Dynamics (grow_fraction: 0.10) — 2026-09-10

Completed configuration-only budget: one excluded 400-step warmup (20260910T193412Z-1cc9a886) and six measured runs across seeds 42, 43, 44, comparing baseline growth fraction (grow_fraction: 0.07) against intermediate growth fraction (grow_fraction: 0.10) with standard growth termination (grow_until_iter: 2400), preserving 1,200 post-growth refinement iterations. Runs were executed in a counterbalanced sequence (Warmup, B42, C42, C43, B43, B44, C44) to decouple thermal and cache drift. All seven train and evaluate exits were zero. Zero rebuilds, zero implementation modifications, zero evaluator edits, zero external downloads, and zero overwrites of previous run evidence.

The indoor `sparse-cubic-v3` split has 126 training and 18 held-out views (across 3 held-out capture groups). Shared configuration: 3600 iterations, width 512, max_cap 100000, refine_every 100, stop_refine 3501, grow_until_iter 2400, SH degree interval 900. Seven quality checkpoints were evaluated: 400, 800, 1200, 2400, 2800, 3200, 3600. Resource limits: 300 seconds/run timeout, 7000 MiB sampled VRAM ceiling, 250 ms sampling interval, sequential execution with strict GPU lock (`.git/hillclimb/gpu.lock`).

## Checkpoint Dynamics (7 Quality Checkpoints)

| Iteration | Mean baseline PSNR | Mean candidate PSNR | Paired mean gain dB | Baseline sample SD |
|---|---:|---:|---:|---:|
| 400 | 21.283658 | 21.095467 | -0.188191 | 0.112907 |
| 800 | 24.957629 | 24.756745 | -0.200884 | 0.148560 |
| 1200 | 26.655327 | 26.931373 | +0.276046 | 0.301921 |
| 2400 | 29.025513 | 29.167021 | +0.141508 | 0.095149 |
| 2800 | 29.447919 | 29.638227 | +0.190308 | 0.026010 |
| 3200 | 29.676111 | 29.852880 | +0.176768 | 0.057818 |
| 3600 | 29.722748 | 29.924594 | +0.201847 | 0.053288 |

These values represent means across three seeds (42, 43, 44). Checkpoints along a single trajectory are correlated. Final paired PSNR deltas are uniformly positive: +0.185385 dB (seed 42), +0.275645 dB (seed 43), and +0.144510 dB (seed 44). Final paired SSIM deltas are likewise uniformly positive: +0.003264 (seed 42), +0.003218 (seed 43), and +0.002666 (seed 44).

## Per-Run Final Metrics at 3600 Iterations

| Seed / Treatment | Grow Fraction | Final SSIM | Gaussians | Harness sec | Internal perf sec | Sample peak MiB | CUDA peak MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| 42 / baseline | 0.07 | 0.838156 | 54454 | 18.891 | 18.497 | 518 | 1511.6 |
| 42 / candidate | 0.10 | 0.841420 | 96480 | 21.875 | 21.470 | 502 | 1495.6 |
| 43 / baseline | 0.07 | 0.838133 | 54325 | 19.500 | 18.970 | 518 | 1511.6 |
| 43 / candidate | 0.10 | 0.841351 | 96193 | 19.985 | 19.552 | 502 | 1495.6 |
| 44 / baseline | 0.07 | 0.837709 | 54301 | 19.593 | 19.143 | 518 | 1511.6 |
| 44 / candidate | 0.10 | 0.840375 | 96552 | 20.172 | 19.724 | 502 | 1495.6 |

## Analysis and Findings

1. **Uniform Quality Dominance Across All Seeds**:
   - The candidate achieved unambiguous, unanimous quality improvements across all three seeds on indoor `sparse-cubic-v3`.
   - Paired PSNR gains: seed 42 (+0.185 dB), seed 43 (+0.276 dB), and seed 44 (+0.145 dB). Mean final gain: **+0.201847 dB**, which is 3.79x the baseline standard deviation (0.053288 dB).
   - Paired SSIM gains: seed 42 (+0.00326), seed 43 (+0.00322), and seed 44 (+0.00267).
   - Checkpoint dynamics reveal that after an initial growth phase (steps 400-800), quality gains are consistently positive from iteration 1200 through completion (+0.276 dB at 1200, +0.142 dB at 2400, +0.190 dB at 2800, +0.177 dB at 3200, +0.202 dB at 3600).

2. **Resource Comparability Failure on Seed 42**:
   - On indoor geometry, `grow_fraction: 0.10` expanded final Gaussian count from ~54,360 to ~96,408 (1.77x baseline), approaching the 100,000 cap.
   - For Seed 42, candidate elapsed wall time was 21.875s versus baseline 18.891s, producing an elapsed ratio of **1.1589** (+15.89%). This breaches the predeclared 15% elapsed-cost comparability band.
   - In the counterbalanced pairs, elapsed ratios were tightly bounded: 1.0248 (+2.48% for seed 43) and 1.0286 (+2.86% for seed 44). However, because seed 42 exceeded the 1.15 limit, the automated assessment flags this pair.
   - Sampled peak VRAM was 502 MiB candidate vs 518 MiB baseline (ratio 0.969), well within the 10% memory screening ceiling.
   - In-process CUDA memory remained bounded (~1495.6 MiB vs 1511.6 MiB).
   - Decision: **reject_screen / no promotion**. While the candidate achieves robust, unanimous quality gains across all seeds on indoor data, the seed 42 runtime ratio (+15.89%) exceeds the strict 15% comparability ceiling.

## Invariant Verification

- All checkpoints have exactly 1 metrics row per eval step, finite PSNR/SSIM, valid timing and Gaussian counts (54,301–96,552 <= 100,000 cap).
- All 18 unique held-out camera views verified with finite per-image metrics at every checkpoint.
- Frozen executable SHA256 (95954f5d825c123594712b85e0fb8fb53febb3e8038a264713fde08bffe2c915), DLL provenance, dataset identity, and split fingerprints match the initial baseline (20260910T184239Z-91cb6818).
- Candidate configuration differs solely by grow_fraction (0.07 vs 0.10).
- Topology updates (splits/prunes) verified to cease before iteration 3501 (stop_refine: 3501).
- LPIPS remains null (weights unavailable locally; no download attempted).

## Machine-Readable Evidence

- Summary JSON: `docs/research/indoor-intermediate-growth-results.json`
- Campaign runner, plan, and checks: `results/research_hillclimb/indoor-intermediate-growth-20260910/`
- Warmup run ID: `20260910T193412Z-1cc9a886`
- Measured baseline run IDs:
  - B42: `20260910T193416Z-d70de4cc`
  - B43: `20260910T193520Z-94669d55`
  - B44: `20260910T193540Z-dc5e36b5`
- Measured candidate run IDs:
  - C42: `20260910T193436Z-119c7a42`
  - C43: `20260910T193459Z-f6b0836a`
  - C44: `20260910T193601Z-838acda7`

## Limitations

- Single indoor development scene (`sparse-cubic-v3`), reduced resolution (width 512), 3600 iterations.
- SfM cameras originally fit with all views.
- No bitwise GPU determinism across floating-point operations.
- LPIPS metric absent.

## Next Step

Budget exhausted; no automatic expansion. Cross-scene synthesis reveals contrasting constraints:
1. On outdoor `test-1-2-v3`, `grow_fraction: 0.10` passes runtime (+5.0% to +6.6%) and achieves net positive gain (+0.122 dB), but has small seed-level variance on seed 42 (-0.009 dB).
2. On indoor `sparse-cubic-v3`, `grow_fraction: 0.10` uniformly dominates in quality across all seeds (+0.202 dB mean PSNR, +0.003 SSIM), but expands Gaussians to 96.5k, pushing seed 42 runtime to +15.89%, just breaching the 15% comparability screen.

The most informative next step should test a slightly more conservative growth fraction (e.g. `grow_fraction: 0.085` or `0.090`) to determine if it can reliably satisfy the 15% elapsed cost ceiling on indoor scenes while maintaining the positive quality gains across both scenes.
