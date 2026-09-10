# Outdoor Calibrated Growth Dynamics (grow_fraction: 0.085) — 2026-09-10

Completed configuration-only budget: one excluded 400-step warmup (`20260910T204913Z-f371d1a5`) and six measured runs across seeds 42, 43, 44, comparing baseline growth fraction (`grow_fraction: 0.07`) against calibrated growth fraction (`grow_fraction: 0.085`) on the outdoor development scene `test-1-2-v3` with standard growth termination (`grow_until_iter: 2400`), preserving 1,200 post-growth refinement iterations. Runs were executed in a counterbalanced sequence (Warmup, B42, C42, C43, B43, B44, C44) to decouple thermal and cache drift. All seven train and evaluate exits were zero. Zero rebuilds, zero implementation modifications, zero evaluator edits, zero external downloads, and zero overwrites of previous run evidence.

The outdoor `test-1-2-v3` split remains 112 training and 16 held-out views. Shared configuration: 3600 iterations, width 512, max_cap 100000, refine_every 100, stop_refine 3501, grow_until_iter 2400, SH degree interval 900. Seven quality checkpoints were evaluated: 400, 800, 1200, 2400, 2800, 3200, 3600. Resource limits: 300 seconds/run timeout, 7000 MiB sampled VRAM ceiling, 250 ms sampling interval, sequential execution with strict GPU lock (`.git/hillclimb/gpu.lock`).

## Checkpoint Dynamics (7 Quality Checkpoints)

| Iteration | Mean baseline PSNR | Mean candidate PSNR | Paired mean gain dB | Baseline sample SD |
|---|---:|---:|---:|---:|
| 400 | 11.101431 | 11.256036 | +0.154605 | 0.194705 |
| 800 | 13.177490 | 13.132866 | -0.044625 | 0.058418 |
| 1200 | 14.091110 | 13.772782 | -0.318328 | 0.161228 |
| 2400 | 14.307710 | 14.024565 | -0.283145 | 0.038833 |
| 2800 | 14.831395 | 14.680837 | -0.150558 | 0.096494 |
| 3200 | 14.814309 | 14.644557 | -0.169752 | 0.044903 |
| 3600 | 14.796911 | 14.697249 | -0.099662 | 0.043758 |

These values represent means across three seeds (42, 43, 44). Checkpoints along a single trajectory are correlated. Final paired PSNR deltas regressed in 2 of 3 seeds: -0.251475 dB (seed 42), -0.084907 dB (seed 43), and +0.037396 dB (seed 44). Final paired SSIM deltas are +0.002723 (seed 42), +0.004337 (seed 43), and -0.000081 (seed 44).

## Per-Run Final Metrics at 3600 Iterations

| Seed / Treatment | Grow Fraction | Final SSIM | Gaussians | Harness sec | Internal perf sec | Sample peak MiB | CUDA peak MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| 42 / baseline | 0.07 | 0.402837 | 8466 | 14.687 | 14.239 | 518 | 1501.6 |
| 42 / candidate | 0.085 | 0.405560 | 11648 | 15.187 | 14.761 | 508 | 1501.6 |
| 43 / baseline | 0.07 | 0.401673 | 8444 | 15.141 | 14.758 | 500 | 1489.6 |
| 43 / candidate | 0.085 | 0.406010 | 11728 | 15.031 | 14.615 | 500 | 1489.6 |
| 44 / baseline | 0.07 | 0.407033 | 8512 | 14.454 | 14.030 | 508 | 1501.6 |
| 44 / candidate | 0.085 | 0.406952 | 11717 | 15.422 | 15.001 | 500 | 1489.6 |

## Analysis and Findings

1. **Resource Comparability Screen Passed**:
   - Elapsed wall time ratios are 1.0338 (seed 42, +3.4%), 0.9917 (seed 43, -0.8%), and 1.0666 (seed 44, +6.7%). All pairs fall comfortably inside the predeclared 15% comparability ceiling.
   - Final Gaussian capacity expanded moderately to ~11,698 (1.38x baseline), maintaining high compute throughput.
   - Peak sampled VRAM ratios are 0.981, 1.000, and 0.984 (0% to -1.9%), well within the 10% ceiling.
   - In-process CUDA memory remained identical (~1489.6–1501.6 MiB).

2. **Quality Failure & Cross-Scene Divergence**:
   - Despite passing the resource comparability screen, `grow_fraction: 0.085` failed the quality criteria on the outdoor development scene.
   - Two out of three seeds suffered quality regressions in PSNR (seed 42: -0.251 dB, seed 43: -0.085 dB). The net mean PSNR delta is negative (-0.099662 dB, over 2.2x baseline SD).
   - Checkpoint dynamics reveal persistent underperformance across almost the entire schedule: from step 800 through 3600, candidate mean PSNR trailed baseline at every single checkpoint (-0.045 dB at 800, -0.318 dB at 1200, -0.283 dB at 2400, -0.151 dB at 2800, -0.170 dB at 3200, -0.100 dB at 3600).
   - At 11.7k Gaussians, the outdoor model appears caught in an unfavorable intermediate regime: it generates more primitives than baseline (8.5k) without having enough capacity to resolve fine foliage/car edges (which required ~16k–34k in the 0.10 and 0.14 studies), yet creates enough optimization noise to impede convergence within the 1,200 post-growth iterations.
   - Decision: **reject candidate; no promotion**.

## Cross-Scene Synthesis

Across our four systematic 3,600-iteration multi-seed campaigns:
1. `grow_fraction: 0.14`:
   - Outdoor: +0.223 dB gain, but 34.6k Gaussians pushed runtime to +18–20% (rejected by resource screen).
2. `grow_until_iter: 3200` at 0.07:
   - Outdoor: -0.088 dB regression (rejected: late-stage growth truncates post-growth refinement).
3. `grow_fraction: 0.10`:
   - Outdoor: +0.122 dB mean gain (passed runtime +5–6.6%, positive on seeds 43/44, but seed 42 regressed -0.009 dB; inconclusive).
   - Indoor: +0.202 dB mean gain across all seeds, but 96.5k Gaussians caused seed 42 runtime to rise +15.89% (rejected by resource screen).
4. `grow_fraction: 0.085`:
   - Indoor: +0.074 dB mean gain across all seeds, passed runtime (+4.2% to +5.1%, 72.9k Gaussians; retained for screening).
   - Outdoor: -0.100 dB mean regression across seeds, trailing baseline from step 800 to 3600 (rejected by quality screen).

**Core Scientific Conclusion**: The optimal Gaussian growth rate is fundamentally scene-dependent. The dense indoor scene `sparse-cubic-v3` has rich room geometry that benefits monotonically from higher growth fraction, where 0.085 provides the sweet spot for the 100k cap. In contrast, the sparse outdoor scene `test-1-2-v3` has a wide depth range with low initial point support where 0.085 underfits, requiring either higher growth fraction (0.10) with adaptive pruning, or a longer post-refinement schedule. A single static global `grow_fraction` scalar cannot simultaneously optimize both regimes without adaptive mechanisms.

## Invariant Verification

- All checkpoints have exactly 1 metrics row per eval step, finite PSNR/SSIM, valid timing and Gaussian counts (8,444–11,728 <= 100,000 cap).
- All 16 unique held-out camera views verified with finite per-image metrics at every checkpoint.
- Frozen executable SHA256 (`95954f5d825c123594712b85e0fb8fb53febb3e8038a264713fde08bffe2c915`), DLL provenance, dataset identity, and split fingerprints match the initial baseline (`20260910T184132Z-d0eb9803`).
- Candidate configuration differs solely by `grow_fraction` (0.07 vs 0.085).
- Topology updates (splits/prunes) verified to cease before iteration 3501 (`stop_refine: 3501`).
- LPIPS remains null (weights unavailable locally; no download attempted).

## Machine-Readable Evidence

- Summary JSON: `docs/research/outdoor-growth-085-results.json`
- Campaign runner, plan, and checks: `results/research_hillclimb/outdoor-growth-085-20260910/`
- Warmup run ID: `20260910T204913Z-f371d1a5`
- Measured baseline run IDs:
  - B42: `20260910T204917Z-8c8a9bd9`
  - B43: `20260910T205005Z-c1c489b0`
  - B44: `20260910T205021Z-c8d13805`
- Measured candidate run IDs:
  - C42: `20260910T204933Z-7b6b52e7`
  - C43: `20260910T204949Z-37861259`
  - C44: `20260910T205037Z-9e6e6bb3`

## Limitations

- Single outdoor development scene (`test-1-2-v3`), reduced resolution (width 512), 3600 iterations.
- SfM cameras originally fit with all views.
- No bitwise GPU determinism across floating-point operations.
- LPIPS metric absent.

## Next Step

Budget exhausted; no automatic expansion. Having established that scalar growth fraction scaling diverges across indoor (+0.074 dB at 0.085) and outdoor (-0.100 dB at 0.085) scenes, the next most informative investigation should explore whether error-map thresholding (`growth_grad_threshold` or `opacity_decay`) or scene-adaptive capacity bounds can decouple primitive densification from scene type, or test longer schedules (e.g. 7000 iterations) where post-growth convergence is less constrained.
