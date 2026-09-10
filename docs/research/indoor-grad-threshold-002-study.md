# Indoor Gradient Threshold Calibration (growth_grad_threshold: 0.002) — 2026-09-10

Completed configuration-only budget: one excluded 400-step warmup (`20260910T210320Z-9061a5a2`) and six measured runs across seeds 42, 43, 44, comparing baseline gradient threshold (`growth_grad_threshold: 0.003`) against calibrated threshold (`growth_grad_threshold: 0.002`) on the indoor development scene `sparse-cubic-v3` with standard growth fraction (`grow_fraction: 0.07`) and standard growth termination (`grow_until_iter: 2400`), preserving 1,200 post-growth refinement iterations. Runs were executed in a counterbalanced sequence (Warmup, B42, C42, C43, B43, B44, C44) to decouple thermal and cache drift. All seven train and evaluate exits were zero. Zero rebuilds, zero implementation modifications, zero evaluator edits, zero external downloads, and zero overwrites of previous run evidence.

The indoor `sparse-cubic-v3` split remains 126 training and 18 held-out views. Shared configuration: 3600 iterations, width 512, max_cap 100000, refine_every 100, stop_refine 3501, grow_until_iter 2400, grow_fraction 0.07, SH degree interval 900. Seven quality checkpoints were evaluated: 400, 800, 1200, 2400, 2800, 3200, 3600. Resource limits: 300 seconds/run timeout, 7000 MiB sampled VRAM ceiling, 250 ms sampling interval, sequential execution with strict GPU lock (`.git/hillclimb/gpu.lock`).

## Checkpoint Dynamics (7 Quality Checkpoints)

| Iteration | Mean baseline PSNR | Mean candidate PSNR | Paired mean gain dB | Baseline sample SD |
|---|---:|---:|---:|---:|
| 400 | 21.415839 | 21.315657 | -0.100182 | 0.135417 |
| 800 | 24.679385 | 24.643166 | -0.036219 | 0.136213 |
| 1200 | 26.799496 | 26.810562 | +0.011066 | 0.035911 |
| 2400 | 29.039206 | 29.093220 | +0.054013 | 0.138444 |
| 2800 | 29.523905 | 29.479548 | -0.044358 | 0.009368 |
| 3200 | 29.718517 | 29.686401 | -0.032115 | 0.017390 |
| 3600 | 29.769138 | 29.767866 | -0.001272 | 0.017145 |

These values represent means across three seeds (42, 43, 44). Final paired PSNR deltas regressed in 2 of 3 seeds: -0.064415 dB (seed 42), +0.094626 dB (seed 43), and -0.034027 dB (seed 44). Final paired SSIM deltas are -0.000769 (seed 42), +0.000640 (seed 43), and +0.000100 (seed 44).

## Per-Run Final Metrics at 3600 Iterations

| Seed / Treatment | Grad Threshold | Final SSIM | Gaussians | Harness sec | Internal perf sec | Sample peak MiB | CUDA peak MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| 42 / baseline | 0.003 | 0.838549 | 54466 | 16.359 | 15.927 | 518 | 1511.6 |
| 42 / candidate | 0.002 | 0.837780 | 54486 | 21.687 | 21.210 | 518 | 1511.6 |
| 43 / candidate | 0.002 | 0.838888 | 54327 | 22.344 | 21.777 | 518 | 1511.6 |
| 43 / baseline | 0.003 | 0.838248 | 54237 | 22.265 | 21.829 | 516 | 1511.6 |
| 44 / baseline | 0.003 | 0.838944 | 54206 | 19.562 | 19.039 | 516 | 1511.6 |
| 44 / candidate | 0.002 | 0.839044 | 54449 | 16.203 | 15.820 | 518 | 1511.6 |

## Analysis and Findings

1. **Resource Comparability Failure**:
   - Seed 42 elapsed time ratio reached 1.3261 (+32.6%), breaching the 15% comparability ceiling.
   - Final Gaussian capacity remained essentially unchanged (~54,421 vs ~54,303).
   - Sampled peak VRAM ratios were 1.000, 1.004, and 1.004, well within the 10% memory ceiling.

2. **Quality Failure & Trajectory Analysis**:
   - Candidate regressed final PSNR on 2 of 3 seeds (seed 42: -0.064 dB, seed 44: -0.034 dB) with a net negative mean delta (-0.001272 dB).
   - Trajectory analysis reveals that during post-growth refinement (iterations 2800, 3200, 3600), candidate mean PSNR trailed baseline across all 3 checkpoints (-0.044 dB, -0.032 dB, -0.001 dB).
   - In dense indoor environments, where primitive count is already high (~54k), lowering the gradient threshold admits lower-gradient noise points into the candidate pool, disrupting convergence during the post-growth phase without improving reconstruction fidelity.
   - Decision: **reject_screen; no promotion**. The candidate fails both the 15% elapsed cost ceiling and the zero-regression quality criterion on indoor data.

## Cross-Scene Comparison for `growth_grad_threshold: 0.002`

- **Outdoor (`test-1-2-v3`)**: Net positive gain (+0.089 dB mean PSNR, unanimous SSIM gain +0.0024), throughput matched/faster (-1.9% mean elapsed), but exhibited seed 43 variance (-0.091 dB dip).
- **Indoor (`sparse-cubic-v3`)**: Net negative delta (-0.001 dB mean PSNR, 2/3 seeds regressed in PSNR), seed 42 runtime breached 15% ceiling (ratio 1.326x).
- **Conclusion**: `growth_grad_threshold: 0.002` does not generalize across scenes. While sparse outdoor scenes benefit from broader candidate inclusion, dense indoor scenes suffer from candidate dilution.

## Invariant Verification

- All checkpoints have exactly 1 metrics row per eval step, finite PSNR/SSIM, valid timing and Gaussian counts (54,206–54,486 <= 100,000 cap).
- All 18 unique held-out camera views verified with finite per-image metrics at every checkpoint.
- Frozen executable SHA256 (`95954f5d825c123594712b85e0fb8fb53febb3e8038a264713fde08bffe2c915`), DLL provenance, dataset identity, and split fingerprints match the initial baseline (`20260910T184239Z-91cb6818`).
- Candidate configuration differs solely by `growth_grad_threshold` (0.003 vs 0.002).
- Topology updates (splits/prunes) verified to cease before iteration 3501 (`stop_refine: 3501`).
- LPIPS remains null (weights unavailable locally; no download attempted).

## Machine-Readable Evidence

- Summary JSON: `docs/research/indoor-grad-threshold-002-results.json`
- Campaign runner, plan, and checks: `results/research_hillclimb/indoor-grad-threshold-002-20260910/`
- Warmup run ID: `20260910T210320Z-9061a5a2`
- Measured baseline run IDs:
  - B42: `20260910T210324Z-afa2f47d`
  - B43: `20260910T210428Z-44c966f1`
  - B44: `20260910T210451Z-1e9a523e`
- Measured candidate run IDs:
  - C42: `20260910T210342Z-03123179`
  - C43: `20260910T210404Z-104cc783`
  - C44: `20260910T210512Z-52823e9d`

## Limitations

- Single indoor development scene (`sparse-cubic-v3`), reduced resolution (width 512), 3600 iterations.
- SfM cameras originally fit with all views.
- No bitwise GPU determinism across floating-point operations.
- LPIPS metric absent.

## Next Step

Proceed to Study 2: Screen Footprint Clamping (`max_screen_share: 0.2` vs baseline `0.3`) on outdoor `test-1-2-v3` to test anisotropic aspect ratio clamping and floater suppression under our standard bounded multi-seed protocol.
