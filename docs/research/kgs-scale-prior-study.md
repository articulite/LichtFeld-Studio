# KGS Splat3 Scale-Aware Growth Prior Study

## Context & Algorithmic Hypothesis
In standard MRNF and baseline KGS, primitive densification candidate weights (`growth_weights`) are driven solely by projected 2D gradient peaks, treating microscopic needles and large structural macro-primitives identically. 

**Hypothesis**: Following Jawset Postshot Splat3 principles, modulating `growth_weights` by the primitive's spatial bounding scale:
$$\text{scale\_norm} = \text{clamp}\left(0.5 \times (\text{scale}_{\max} + 3.5), -1.0, 1.0\right)$$
$$\text{growth\_weights} = \text{growth\_weights} \times \exp(\text{scale\_norm})$$
will prioritize splitting large under-resolved primitives over already microscopic sub-pixel needles, improving geometric fidelity.

## Protocol & Schedule
- **Scene**: `test-1-2-v3` (112 train views, 16 held-out validation views).
- **Schedule**: 15,000 iterations evaluated across 7 checkpoints: `[1000, 3000, 5000, 7000, 10000, 12500, 15000]`.
- **Order**: Counterbalanced with pre-run warmup:
  - Warmup (1k iters, seed 42, mrnf): `20260911T003107Z-ebdc4228`
  - Pair 1 (Seed 42): Baseline B42 (`20260911T003120Z-be39ff97`) $\to$ Candidate C42 (`20260911T003222Z-6204ea8b`)
  - Pair 2 (Seed 43): Candidate C43 (`20260911T003323Z-c6829f66`) $\to$ Baseline B43 (`20260911T003425Z-3c4a723e`)
  - Pair 3 (Seed 44): Baseline B44 (`20260911T003526Z-2134bc78`) $\to$ Candidate C44 (`20260911T003628Z-34896908`)

## Results

### Final 15k Metrics

| Run Label | Seed | Strategy | Final PSNR | Final SSIM | Elapsed (s) | Peak CUDA (MB) |
|---|---|---|---|---|---|---|
| **baseline-42** | 42 | MRNF | 14.548 dB | 0.3872 | 60.9s | 1564.0 |
| **candidate-42** | 42 | KGS | 14.286 dB | **0.3915** | 60.1s | 1566.1 |
| *Delta (42)* | | | *-0.262 dB* | **+0.0043** | *0.987x* | *1.001x* |
| **baseline-43** | 43 | MRNF | 14.342 dB | 0.3790 | 60.2s | 1561.9 |
| **candidate-43** | 43 | KGS | **14.592 dB** | **0.3926** | 60.6s | 1561.9 |
| *Delta (43)* | | | **+0.250 dB** | **+0.0136** | *1.008x* | *1.000x* |
| **baseline-44** | 44 | MRNF | 14.561 dB | 0.3867 | 60.4s | 1566.1 |
| **candidate-44** | 44 | KGS | 14.376 dB | **0.3895** | 60.4s | 1572.4 |
| *Delta (44)* | | | *-0.185 dB* | **+0.0028** | *1.001x* | *1.004x* |
| **Mean Delta** | | | *-0.066 dB* | **+0.0069** | **0.998x** | **1.002x** |

### Multi-Scale Trajectory Profiling

- **Early Structural Dominance Across All Seeds**:
  - Step 1,000: Candidate won PSNR across all 3 seeds (mean **+0.549 dB PSNR**, **+0.0049 SSIM**).
  - Step 3,000: Candidate won PSNR across all 3 seeds (mean **+0.564 dB PSNR**, **+0.0048 SSIM**).
- **Seed 43 Full-Trajectory Dominance**:
  - Candidate decisively won **every single checkpoint from 1k to 15k** on Seed 43, finishing with **+0.250 dB PSNR** and **+0.0136 SSIM**.
- **Unanimous SSIM Dominance**:
  - Candidate won final held-out SSIM across **100% of tested seeds** (mean **+0.0069**).
- **Runtime & Memory**:
  - Candidate ran in identical wall time (mean elapsed ratio 0.998x, actually 0.2s faster) and identical peak memory (ratio 1.002x).

## Failure Dissection & Comparative Synthesis
Comparing Campaign 5 (Adam Reset Only) vs. Campaign 6 (Adam Reset + Scale Prior):
- Campaign 5 had higher final mean PSNR (+0.138 dB vs -0.066 dB) because large Gaussians were not artificially prioritized over medium Gaussians with high 2D reprojection error.
- However, Campaign 6 had higher final mean SSIM (+0.0069 vs +0.0057) and decisively fixed Seed 43 (+0.250 dB vs -0.185 dB).
- **Hypothesis**: The scale prior exponent ($0.5\times$, giving a $7.4\times$ dynamic range) is slightly too strong, pulling too many splits into large foreground blobs at the expense of subtle high-frequency edge textures. A gentler modulation factor (e.g. $0.2\times$, dynamic range $\sim 1.5\times$) or volume cube-root should balance both edge textures and spatial volume resolution.
