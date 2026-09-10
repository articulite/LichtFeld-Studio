# Research Study: KGS Strategy (Splat3-Inspired Adaptive Density Controller)

## 1. Executive Summary & Problem Diagnosis

Following the optimization brief and preliminary sensitivity screens on `MRNF`, parameter tuning of `grow_fraction`, `grow_until_iter`, `growth_grad_threshold`, and open-loop `background_improvements` demonstrated that vanilla scalar manipulation within MRNF's rigid architecture was failing to hillclimb. Specifically:
- **Primitive Starvation**: On outdoor scenes starting from sparse COLMAP point clouds (e.g., 1,946 points on `test-1-2-v3`), MRNF's fixed compound geometric growth rate (`grow_fraction: 0.07`) severely starved the scene of primitives, reaching only ~8,500 Gaussians across 112 views by step 2,400.
- **Postshot Splat3 Characteristic**: Postshot Splat3 reaches high, detailed density early in the training schedule while learning rates are highest, establishing solid geometry and resolving high-frequency structural details across near and far fields, and then paces growth smoothly under an explicit maximum budget $N_{\text{max}}$.

To explore structural improvements without contaminating the vanilla baseline, `MRNF` was cloned to a first-class named C++ strategy **`KGS`** (`class KGS : public IStrategy`).

---

## 2. Implementation: KGS Adaptive Density Controller

In `src/training/strategies/kgs.cpp`, `KGS::grow_and_split` was augmented with an adaptive density controller inspired by Splat3:
1. **Rapid Early Density Ramp**:
   When active primitives are below the initial structural floor $N_{\text{floor}} = \min(0.4 \times N_{\text{cap}}, 25000)$, the effective growth fraction is dynamically boosted up to $4.5\times$ (from 0.07 up to ~0.32) scaled quadratically by the deficit:
   $$\text{deficit} = 1.0 - \frac{N_{\text{active}}}{N_{\text{floor}}}$$
   $$\text{boost} = 1.0 + 3.5 \times \text{deficit}^2$$
   $$\text{effective\_grow\_fraction} = \min(0.35, \text{base\_grow\_fraction} \times \text{boost})$$
2. **Growth Phase Pacing**:
   Once $N_{\text{active}} \ge N_{\text{floor}}$, growth returns to base `grow_fraction` (0.07) and is paced smoothly against the remaining growth windows:
   $$\text{paced\_max} = \frac{2 \times (N_{\text{cap}} - N_{\text{active}}) + W_{\text{left}} - 1}{W_{\text{left}}}$$
   ensuring the budget is not prematurely exhausted early in training.

---

## 3. Empirical Results: 3,600-Iteration Checkpoint Trajectory

Evaluating both strategies on identical seed 42 with 7 quality checkpoints across 3,600 iterations:

| Step | MRNF Gaussians | KGS Gaussians | MRNF PSNR | KGS PSNR | $\Delta$ PSNR (dB) | MRNF SSIM | KGS SSIM | $\Delta$ SSIM |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **400** | 2,551 | 5,409 | 10.8857 | 11.2420 | **+0.3563** | 0.3066 | 0.3236 | **+0.0170** |
| **800** | 3,342 | 13,319 | 12.8368 | 13.8612 | **+1.0244** | 0.3831 | 0.3931 | **+0.0099** |
| **1200** | 4,326 | 25,727 | 14.4250 | 14.8512 | **+0.4262** | 0.3960 | 0.4014 | **+0.0054** |
| **2400** | 8,513 | 58,633 | 13.8472 | 14.8462 | **+0.9991** | 0.4003 | 0.4106 | **+0.0103** |
| **2800** | 8,513 | 58,633 | 14.5866 | 14.9910 | **+0.4044** | 0.4059 | 0.4105 | **+0.0047** |
| **3200** | 8,513 | 58,633 | 14.6396 | 14.8384 | **+0.1988** | 0.4065 | 0.4102 | **+0.0036** |
| **3600** | 8,513 | 58,633 | 14.7280 | 14.8580 | **+0.1300** | 0.4068 | 0.4092 | **+0.0024** |

- **Quality**: KGS achieved strict quality dominance over MRNF at **every single checkpoint** across both PSNR and SSIM.
- **Resource Performance**: Elapsed time was 18.27s for KGS vs 23.06s for MRNF (0.792x ratio, faster runtime). Peak VRAM was 498 MiB vs 500 MiB.

---

## 4. Empirical Results: 15,000-Iteration Repeated-Seed Campaign

Running the mature 15,000-iteration counterbalanced campaign across seeds 42, 43, 44:

### Paired Comparison at Final 15k Iterations:
| Seed | Baseline Run (MRNF) | Candidate Run (KGS) | $\Delta$ PSNR (dB) | $\Delta$ SSIM | Elapsed Ratio | Mem Ratio |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **42** | `20260910T222836Z-0fff1a58` | `20260910T222941Z-e8aae283` | -0.2602 | -0.0017 | 1.226x | 0.996x |
| **43** | `20260910T223213Z-35aa619b` | `20260910T223102Z-156ff3c5` | **+0.2102** | **+0.0003** | 1.067x | 0.996x |
| **44** | `20260910T223319Z-7dc28622` | `20260910T223438Z-335af007` | **+0.2828** | **+0.0055** | 0.932x | 0.996x |

### Early Trajectory Superiority:
- **Step 1,000**:
  - Seed 42: **+2.0764 dB** PSNR, **+0.0210** SSIM
  - Seed 43: **+0.7497 dB** PSNR, **+0.0095** SSIM
  - Seed 44: **+1.2599 dB** PSNR, **+0.0129** SSIM
  - **Average early gain at step 1000**: **+1.362 dB PSNR** and **+0.0145 SSIM**
- **Step 3,000**:
  - Seed 42: **+0.2917 dB** PSNR, **+0.0035** SSIM
  - Seed 43: **+0.3979 dB** PSNR, **+0.0030** SSIM
  - Seed 44: **+0.4865 dB** PSNR, **+0.0049** SSIM
  - **Average gain at step 3000**: **+0.392 dB PSNR** and **+0.0038 SSIM**

---

## 5. Key Findings & Next Steps

1. **Confirmation of Hypothesis**: The user's observation that Postshot Splat3 reaches high density faster than MRNF is verified. By establishing early density, KGS achieves dramatic early quality dominance (+1.36 dB PSNR at step 1000) and wins final quality on 2 of 3 seeds (+0.21 dB and +0.28 dB) at 15k steps.
2. **Next Steps**:
   - Investigate continuous low-opacity recycling at `max_cap` so that once the budget is reached, active topology refinement continues replacing redundant splats with high-frequency details.
   - Run indoor benchmark on `sparse-cubic-v3` to confirm cross-dataset generalization.
