# Research Study: Bilateral Grid Filtering Evaluation (KGS at 15k Iterations)

## 1. Executive Summary

This study investigated whether activating the built-in **Bilateral Grid Filtering** (`use_bilateral_grid: true`) improves reconstruction fidelity on the outdoor development scene `test-1-2-v3` under the strict 100k Gaussian cap.

- **Outcome**: **REJECT SCREEN; NO PROMOTION**.
- **Primary Failure Modes**:
  1. **Severe Runtime Regression**: +49.1% mean elapsed wall-clock time (82.7s vs 55.4s), drastically breaching the 15% comparability ceiling.
  2. **Unanimous SSIM Collapse**: -0.0061 mean SSIM loss across all three seeds (-0.0082, -0.0013, -0.0086).
  3. **Novel View Generalization Failure**: Bilateral grid acts as a per-training-camera appearance sponge; held-out evaluation views lack corresponding grid slices, causing uncompensated contrast degradation on unseen viewpoints.

---

## 2. Empirical Findings

### Paired Screening Comparison (15,000 Iterations, Seeds 42, 43, 44)

**Harness Decision**: `reject_screen` (Violates runtime comparability band on 3/3 seeds; uncompensated held-out SSIM degradation).

| Seed | Baseline KGS (Off) PSNR | Candidate KGS (On) PSNR | **PSNR Delta** | Baseline KGS (Off) SSIM | Candidate KGS (On) SSIM | **SSIM Delta** | Elapsed Ratio | VRAM Ratio |
|:---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **42** | 14.3367 dB | 14.1805 dB | **-0.1562 dB** | 0.3724 | 0.3642 | **-0.0082** | 1.484x (+48.4%) | 1.097x |
| **43** | 14.1655 dB | 14.3711 dB | **+0.2056 dB** | 0.3719 | 0.3705 | **-0.0013** | 1.517x (+51.7%) | 1.097x |
| **44** | 14.2106 dB | 14.3671 dB | **+0.1565 dB** | 0.3730 | 0.3644 | **-0.0086** | 1.473x (+47.3%) | 1.097x |
| **Mean** | **14.2376 dB** | **14.3062 dB** | **+0.0686 dB** | **0.3724** | **0.3664** | **-0.0061** | **1.491x (+49.1%)** | **1.097x** |

### Checkpoint SSIM Dynamics (Held-Out Test Views)

| Step | Mean Baseline SSIM (Off) | Mean Candidate SSIM (On) | **SSIM Delta** |
|---:|---:|---:|---:|
| **1,000** | 0.3973 | 0.3983 | +0.0010 |
| **3,000** | 0.3891 | 0.3869 | -0.0022 |
| **5,000** | 0.3828 | 0.3782 | -0.0046 |
| **7,000** | 0.3788 | 0.3733 | -0.0055 |
| **10,000** | 0.3766 | 0.3697 | -0.0069 |
| **12,500** | 0.3744 | 0.3682 | -0.0062 |
| **15,000** | 0.3724 | 0.3664 | **-0.0061** |

---

## 3. Deep Dive: Why Bilateral Grid Fails on Held-Out Evaluation

### 1. The 'Appearance Sponge' Generalization Trap
In LichtFeld Studio, the bilateral grid is parameterized per training camera UID:
`corrected_image = bilateral_grid_->apply(output.image, cam->uid())`
- During training, the 3D grid slices (16x16x8) learn affine color and luminance transforms specific to each individual training frame to absorb exposure and white-balance mismatches.
- This creates an optimization shortcut: gradient descent routes high-contrast radiometric error into the bilateral grid parameters rather than forcing the Gaussian primitives to learn accurate canonical scene radiance.
- **When evaluating held-out views**: The 16 test views have unseen camera poses and no corresponding trained grid slice. The test images are rendered directly from the Gaussian model. Because the Gaussians were under-optimized (having offloaded contrast to the training grids), the novel views suffer washed-out contrast and blurred structural boundaries, dropping held-out SSIM by up to **-0.0086**.

### 2. Computational Cost
Each training step executes:
1. Bilateral grid forward slice: `bilateral_grid_tv_forward_stage1_kernel` & `stage2_kernel`
2. Bilateral grid backward slice: `bilateral_grid_tv_backward_kernel`
3. Total variation regularization step: `bilateral_grid_->tv_loss_gpu(cam->uid()) * tv_weight`

This adds ~28 seconds of GPU overhead per 15k run (+49.1% training duration) and +9.7% peak VRAM usage, making it computationally non-viable for rapid hillclimbing under the fixed resource budget.

---

## 4. Conclusion & Strategy Decision

- **Decision**: Keep `use_bilateral_grid: false` for KGS.
- **Takeaway**: Appearance modeling via per-image bilateral grids helps visual rendering on training views, but actively degrades held-out structural fidelity (SSIM) unless paired with an explicit novel-view appearance inference mechanism (e.g. PPISP EXIF exposure transfer). Under strict held-out evaluation, pure canonical Gaussian optimization is superior.
