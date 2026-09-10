# Indoor Calibrated Growth Dynamics (grow_fraction: 0.085) — 2026-09-10

Completed configuration-only budget: one excluded 400-step warmup (`20260910T194116Z-835c2a28`) and six measured runs across seeds 42, 43, 44, comparing baseline growth fraction (`grow_fraction: 0.07`) against calibrated growth fraction (`grow_fraction: 0.085`) on the indoor scene `sparse-cubic-v3` with standard growth termination (`grow_until_iter: 2400`), preserving 1,200 post-growth refinement iterations. Runs were executed in a counterbalanced sequence (Warmup, B42, C42, C43, B43, B44, C44) to decouple thermal and cache drift. All seven train and evaluate exits were zero. Zero rebuilds, zero implementation modifications, zero evaluator edits, zero external downloads, and zero overwrites of previous run evidence.

The indoor `sparse-cubic-v3` split has 126 training and 18 held-out views (across 3 held-out capture groups). Shared configuration: 3600 iterations, width 512, max_cap 100000, refine_every 100, stop_refine 3501, grow_until_iter 2400, SH degree interval 900. Seven quality checkpoints were evaluated: 400, 800, 1200, 2400, 2800, 3200, 3600. Resource limits: 300 seconds/run timeout, 7000 MiB sampled VRAM ceiling, 250 ms sampling interval, sequential execution with strict GPU lock (`.git/hillclimb/gpu.lock`).

## Checkpoint Dynamics (7 Quality Checkpoints)

| Iteration | Mean baseline PSNR | Mean candidate PSNR | Paired mean gain dB | Baseline sample SD |
|---|---:|---:|---:|---:|
| 400 | 21.339207 | 21.211569 | -0.127637 | 0.076936 |
| 800 | 24.575917 | 24.705800 | +0.129883 | 0.446089 |
| 1200 | 26.770249 | 26.790026 | +0.019777 | 0.072242 |
| 2400 | 29.119933 | 29.150569 | +0.030637 | 0.071356 |
| 2800 | 29.542890 | 29.572910 | +0.030020 | 0.069641 |
| 3200 | 29.731320 | 29.822790 | +0.091471 | 0.051373 |
| 3600 | 29.797315 | 29.871751 | +0.074436 | 0.023107 |

These values represent means across three seeds (42, 43, 44). Checkpoints along a single trajectory are correlated. Final paired PSNR deltas are uniformly positive across all seeds: +0.080681 dB (seed 42), +0.033495 dB (seed 43), and +0.109131 dB (seed 44). Final paired SSIM deltas are likewise uniformly positive across all seeds: +0.000890 (seed 42), +0.001768 (seed 43), and +0.001103 (seed 44).

## Per-Run Final Metrics at 3600 Iterations

| Seed / Treatment | Grow Fraction | Final SSIM | Gaussians | Harness sec | Internal perf sec | Sample peak MiB | CUDA peak MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| 42 / baseline | 0.07 | 0.838511 | 54322 | 18.266 | 17.863 | 518 | 1511.6 |
| 42 / candidate | 0.085 | 0.839401 | 72649 | 19.219 | 18.818 | 518 | 1505.6 |
| 43 / baseline | 0.07 | 0.838689 | 54512 | 17.984 | 17.568 | 518 | 1511.6 |
| 43 / candidate | 0.085 | 0.840457 | 73066 | 18.797 | 18.397 | 512 | 1505.6 |
| 44 / baseline | 0.07 | 0.838793 | 54377 | 18.187 | 17.764 | 518 | 1511.6 |
| 44 / candidate | 0.085 | 0.839896 | 72930 | 19.016 | 18.595 | 512 | 1505.6 |

## Analysis and Findings

1. **Resource Comparability Screen Fully Passed**:
   - Elapsed wall time ratios are 1.0510 (seed 42, +5.1%), 1.0450 (seed 43, +4.5%), and 1.0418 (seed 44, +4.2%). All pairs fall comfortably inside the predeclared 15% comparability ceiling.
   - This directly resolves the failure mode seen with `grow_fraction: 0.10` on indoor data, where Gaussian growth to 96.5k pushed seed 42 runtime to +15.89%.
   - By calibrating `grow_fraction` to 0.085, final Gaussian capacity is controlled to ~72,882 (1.34x baseline), avoiding near-cap congestion while delivering sufficient primitive density.
   - Sampled peak VRAM ratios are 1.000, 0.988, and 0.988 (0% to -1.2%), well within the 10% memory ceiling.
   - In-process CUDA memory remained bounded (~1505.6 MiB vs 1511.6 MiB).

2. **Quality Screening & Dominance**:
   - The candidate achieved unanimous, positive quality gains across all three seeds:
     - Seed 42: +0.080681 dB PSNR, +0.000890 SSIM
     - Seed 43: +0.033495 dB PSNR, +0.001768 SSIM
     - Seed 44: +0.109131 dB PSNR, +0.001103 SSIM
   - Net mean PSNR delta is **+0.074436 dB**, which is 3.22x the baseline sample standard deviation (0.023107 dB).
   - SSIM improved across all three seed pairs.
   - Checkpoint dynamics confirm quality gains consistently positive from iteration 800 through final convergence (2400: +0.031 dB, 2800: +0.030 dB, 3200: +0.091 dB, 3600: +0.074 dB).
   - Decision: **retain for repeated-seed screening; no promotion**. The candidate successfully satisfies both the resource comparability screen (elapsed ratios +4.2% to +5.1%) and the quality improvement criteria across all seeds on indoor data. Under our protocol, screening on a single scene/schedule retains the candidate for multi-scene validation and does not warrant target-setting promotion.

## Invariant Verification

- All checkpoints have exactly 1 metrics row per eval step, finite PSNR/SSIM, valid timing and Gaussian counts (54,322–73,066 <= 100,000 cap).
- All 18 unique held-out camera views verified with finite per-image metrics at every checkpoint.
- Frozen executable SHA256 (`95954f5d825c123594712b85e0fb8fb53febb3e8038a264713fde08bffe2c915`), DLL provenance, dataset identity, and split fingerprints match the initial baseline (`20260910T184239Z-91cb6818`).
- Candidate configuration differs solely by `grow_fraction` (0.07 vs 0.085).
- Topology updates (splits/prunes) verified to cease before iteration 3501 (`stop_refine: 3501`).
- LPIPS remains null (weights unavailable locally; no download attempted).

## Machine-Readable Evidence

- Summary JSON: `docs/research/indoor-growth-085-results.json`
- Campaign runner, plan, and checks: `results/research_hillclimb/indoor-growth-085-20260910/`
- Warmup run ID: `20260910T194116Z-835c2a28`
- Measured baseline run IDs:
  - B42: `20260910T194120Z-62259ee7`
  - B43: `20260910T194219Z-bafbd608`
  - B44: `20260910T194238Z-c4734796`
- Measured candidate run IDs:
  - C42: `20260910T194139Z-0a542599`
  - C43: `20260910T194200Z-19d382bb`
  - C44: `20260910T194258Z-11dddab3`

## Limitations

- Single indoor development scene (`sparse-cubic-v3`), reduced resolution (width 512), 3600 iterations.
- SfM cameras originally fit with all views.
- No bitwise GPU determinism across floating-point operations.
- LPIPS metric absent.

## Next Step

Budget exhausted; no automatic expansion. Having established that `grow_fraction: 0.085` successfully passes the 15% elapsed-cost screen (+4.2% to +5.1%) and achieves unanimous positive quality gains across all seeds on indoor `sparse-cubic-v3`, the most informative next campaign should evaluate whether `grow_fraction: 0.085` achieves comparable Pareto-efficiency on the outdoor scene `test-1-2-v3` across repeated seeds (42/43/44), testing whether a single unified growth rate (0.085) can dominate baseline 0.07 across BOTH development scenes within the 15% elapsed-cost band.
