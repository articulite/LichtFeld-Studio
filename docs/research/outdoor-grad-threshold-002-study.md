# Outdoor Gradient Threshold Calibration (growth_grad_threshold: 0.002) — 2026-09-10

Completed configuration-only budget: one excluded 400-step warmup (20260910T205601Z-9d8c09e8) and six measured runs across seeds 42, 43, 44, comparing baseline gradient threshold (growth_grad_threshold: 0.003) against calibrated threshold (growth_grad_threshold: 0.002) on the outdoor development scene 	est-1-2-v3 with standard growth fraction (grow_fraction: 0.07) and standard growth termination (grow_until_iter: 2400), preserving 1,200 post-growth refinement iterations. Runs were executed in a counterbalanced sequence (Warmup, B42, C42, C43, B43, B44, C44) to decouple thermal and cache drift. All seven train and evaluate exits were zero. Zero rebuilds, zero implementation modifications, zero evaluator edits, zero external downloads, and zero overwrites of previous run evidence.

The outdoor 	est-1-2-v3 split remains 112 training and 16 held-out views. Shared configuration: 3600 iterations, width 512, max_cap 100000, refine_every 100, stop_refine 3501, grow_until_iter 2400, grow_fraction 0.07, SH degree interval 900. Seven quality checkpoints were evaluated: 400, 800, 1200, 2400, 2800, 3200, 3600. Resource limits: 300 seconds/run timeout, 7000 MiB sampled VRAM ceiling, 250 ms sampling interval, sequential execution with strict GPU lock (.git/hillclimb/gpu.lock).

## Checkpoint Dynamics (7 Quality Checkpoints)

| Iteration | Mean baseline PSNR | Mean candidate PSNR | Paired mean gain dB | Baseline sample SD |
|---|---:|---:|---:|---:|
| 400 | 11.313942 | 11.353446 | +0.039505 | 0.235594 |
| 800 | 13.633223 | 13.373401 | -0.259822 | 0.238099 |
| 1200 | 13.890409 | 13.662263 | -0.228146 | 0.483010 |
| 2400 | 14.196797 | 14.226059 | +0.029262 | 0.138843 |
| 2800 | 14.633281 | 14.739639 | +0.106359 | 0.103866 |
| 3200 | 14.590809 | 14.707183 | +0.116373 | 0.079939 |
| 3600 | 14.603573 | 14.692727 | +0.089154 | 0.050706 |

These values represent means across three seeds (42, 43, 44). Checkpoints along a single trajectory are correlated. Final paired PSNR deltas are +0.246630 dB (seed 42), -0.090774 dB (seed 43), and +0.111607 dB (seed 44). Final paired SSIM deltas are strictly positive across all three seeds: +0.002456 (seed 42), +0.000160 (seed 43), and +0.004542 (seed 44), yielding a net mean SSIM gain of +0.002386.

## Per-Run Final Metrics at 3600 Iterations

| Seed / Treatment | Grad Threshold | Final SSIM | Gaussians | Harness sec | Internal perf sec | Sample peak MiB | CUDA peak MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| 42 / baseline | 0.003 | 0.404943 | 8471 | 14.657 | 14.265 | 506 | 1499.6 |
| 42 / candidate | 0.002 | 0.407399 | 8516 | 14.140 | 13.716 | 508 | 1501.6 |
| 43 / baseline | 0.003 | 0.405574 | 8453 | 14.687 | 14.308 | 500 | 1469.6 |
| 43 / candidate | 0.002 | 0.405734 | 8457 | 14.422 | 14.023 | 500 | 1489.6 |
| 44 / baseline | 0.003 | 0.402429 | 8509 | 14.328 | 13.933 | 506 | 1499.6 |
| 44 / candidate | 0.002 | 0.406971 | 8481 | 14.235 | 13.852 | 500 | 1469.6 |

## Analysis and Findings

1. **Resource Comparability Screen Passed**:
   - Elapsed wall time ratios are 0.9649 (seed 42, -3.5%), 0.9842 (seed 43, -1.6%), and 0.9947 (seed 44, -0.5%). All runs executed with equal or slightly improved throughput, easily satisfying the +/-15% comparability band.
   - Final Gaussian capacity remained tightly controlled at ~8,485 (virtually identical to baseline's ~8,478, ratio 1.001x).
   - Peak sampled VRAM ratios are 1.004, 1.000, and 0.988 (+0.4% to -1.2%), well within the 10% memory ceiling.
   - In-process CUDA memory remained stable (~1469.6–1501.6 MiB).

2. **Quality Dynamics and Threshold Mechanics**:
   - Lowering growth_grad_threshold from 0.003 to 0.002 changed the spatial placement of newly grown Gaussians rather than expanding total Gaussian volume (8,485 vs 8,478). By lowering the candidacy barrier by 33%, splats in moderate-gradient areas (e.g. road surface and foliage boundaries) were able to enter the Gumbel selection pool.
   - During early growth (iterations 800–1200), candidate mean PSNR trailed baseline (-0.260 dB and -0.228 dB), as newly introduced moderate-gradient primitives require optimization steps to settle.
   - However, once growth ceased at iteration 2400, candidate performance surged during the 1,200 post-growth refinement iterations: +0.029 dB at 2400, +0.106 dB at 2800, +0.116 dB at 3200, and +0.089 dB at 3600.
   - Structural similarity (SSIM) improved unanimously across all three seeds (+0.0025, +0.0002, +0.0045; mean delta +0.002386).
   - In PSNR, seeds 42 and 44 achieved substantial gains (+0.2466 dB and +0.1116 dB). However, seed 43 experienced a -0.0908 dB dip.
   - Under our predeclared falsification criterion, which requires consistent, non-regressing improvements across all seeds, the single-seed PSNR dip prohibits promotion.
   - Decision: **inconclusive / no promotion**. The candidate successfully decouples primitive placement from total count, yields positive post-growth convergence (+0.089 dB mean PSNR, +0.0024 mean SSIM), and passes all resource screens, but seed 43 exhibits stochastic variance that prevents unconditional promotion.

## Invariant Verification

- All checkpoints have exactly 1 metrics row per eval step, finite PSNR/SSIM, valid timing and Gaussian counts (8,453–8,516 <= 100,000 cap).
- All 16 unique held-out camera views verified with finite per-image metrics at every checkpoint.
- Frozen executable SHA256 (95954f5d825c123594712b85e0fb8fb53febb3e8038a264713fde08bffe2c915), DLL provenance, dataset identity, and split fingerprints match the initial baseline (20260910T184132Z-d0eb9803).
- Candidate configuration differs solely by growth_grad_threshold (0.003 vs 0.002).
- Topology updates (splits/prunes) verified to cease before iteration 3501 (stop_refine: 3501).
- LPIPS remains null (weights unavailable locally; no download attempted).

## Machine-Readable Evidence

- Summary JSON: docs/research/outdoor-grad-threshold-002-results.json
- Campaign runner, plan, and checks: 
esults/research_hillclimb/outdoor-grad-threshold-002-20260910/
- Warmup run ID: 20260910T205601Z-9d8c09e8
- Measured baseline run IDs:
  - B42: 20260910T205605Z-23480790
  - B43: 20260910T205651Z-ee72233f
  - B44: 20260910T205706Z-38e38129
- Measured candidate run IDs:
  - C42: 20260910T205620Z-7a29ccb6
  - C43: 20260910T205635Z-8634e754
  - C44: 20260910T205722Z-c6848fb2

## Limitations

- Single outdoor development scene (	est-1-2-v3), reduced resolution (width 512), 3600 iterations.
- SfM cameras originally fit with all views.
- No bitwise GPU determinism across floating-point operations.
- LPIPS metric absent.

## Next Step

Budget exhausted; no automatic expansion. Having established that:
1. growth_grad_threshold: 0.002 controls primitive count to ~8.48k (identical to baseline) and yields strong post-growth refinement (+0.089 dB mean PSNR, unanimous SSIM gains +0.0024), but retains seed 43 variance, and
2. grow_fraction: 0.085 succeeds on indoor (+0.074 dB) but regresses outdoor (-0.100 dB),
the next most informative campaign should evaluate whether growth_grad_threshold: 0.002 stabilizes the indoor scene sparse-cubic-v3 under matched 3,600-iteration settings, or test combined calibration on a longer refinement schedule (e.g. 5,000–7,000 iterations).
