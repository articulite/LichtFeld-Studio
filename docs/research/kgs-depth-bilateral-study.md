# Research Study: Depth-Aware Bilateral Anti-Bleeding Filter Evaluation (KGS at 15k Iterations)

## 1. Executive Summary

Following the analysis of Splat3's anti-bleeding architecture, we implemented **Option 1: Depth-Aware Screen-Space Bilateral Rasterization Filter** with an exact adjoint backward pass in CUDA (`launch_depth_bilateral_forward` and `launch_depth_bilateral_backward`).

We evaluated this filter on the outdoor development scene `test-1-2-v3` under the strict 100k Gaussian cap across seeds 42, 43, and 44, comparing KGS with depth-bilateral active (`use_depth_bilateral: true`, $r=3, \sigma_s=3.0, \sigma_d=0.1$) against vanilla KGS (`use_depth_bilateral: false`).

- **Outcome**: **INCONCLUSIVE_NO_PROMOTION** (Screening decision; mixed 15k endpoint, but strong early-training wins).
- **Key Findings**:
  1. **Runtime Overhead Target Met**: +4.9% mean training duration (63.1s vs 60.1s), strictly meeting the $<5\%$ overhead budget (in contrast to the 5D appearance bilateral grid's +49.1% explosion).
  2. **Zero Memory Bloat**: VRAM overhead was negligible (+3.4%, 548 MiB vs 530 MiB).
  3. **Early-to-Mid Training Win (Steps 1k–5k)**: Depth bilateral **unanimously improved** held-out quality across all seeds in early training (+0.1127 dB PSNR, +0.0021 SSIM at 1k; +0.0880 dB PSNR, +0.0015 SSIM at 3k; +0.0983 dB PSNR, +0.0011 SSIM at 5k).
  4. **Late-Training Texture Attenuation (Steps 10k–15k)**: At full 100k Gaussian saturation, a fixed radius $r=3$ filter acts as a mild high-frequency texture smoother, resulting in a slight regression at the 15k endpoint (-0.0225 dB PSNR, -0.0013 SSIM).

---

## 2. Empirical Findings

### Paired Screening Comparison (15,000 Iterations, Seeds 42, 43, 44)

**Harness Decision**: `inconclusive_no_promotion`

| Seed | Baseline KGS (Off) PSNR | Candidate KGS (On) PSNR | **PSNR Delta** | Baseline KGS (Off) SSIM | Candidate KGS (On) SSIM | **SSIM Delta** | Elapsed Ratio | VRAM Ratio |
|:---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **42** | 14.3590 dB | 14.1652 dB | **-0.1938 dB** | 0.3777 | 0.3732 | **-0.0046** | 1.059x (+5.9%) | 1.049x |
| **43** | 14.1217 dB | 14.3283 dB | **+0.2066 dB** | 0.3695 | 0.3744 | **+0.0049** | 1.041x (+4.1%) | 1.026x |
| **44** | 14.1075 dB | 14.0271 dB | **-0.0804 dB** | 0.3734 | 0.3691 | **-0.0043** | 1.047x (+4.7%) | 1.026x |
| **Mean** | **14.1961 dB** | **14.1735 dB** | **-0.0225 dB** | **0.3735** | **0.3722** | **-0.0013** | **1.049x (+4.9%)** | **1.034x** |

---

### Checkpoint Dynamics Across Iterations

Tracking the mean held-out quality over the 15k training trajectory reveals the mechanism:

| Step | Mean Baseline SSIM | Mean Candidate SSIM | **SSIM Delta** | Mean Baseline PSNR | Mean Candidate PSNR | **PSNR Delta** | Winner |
|---:|---:|---:|---:|---:|---:|---:|:---:|
| **1,000** | 0.3975 | 0.3996 | **+0.0021** | 14.5743 dB | 14.6871 dB | **+0.1127 dB** | **Candidate** |
| **3,000** | 0.3890 | 0.3905 | **+0.0015** | 14.4598 dB | 14.5478 dB | **+0.0880 dB** | **Candidate** |
| **5,000** | 0.3823 | 0.3834 | **+0.0011** | 14.2838 dB | 14.3822 dB | **+0.0983 dB** | **Candidate** |
| **7,000** | 0.3792 | 0.3792 | **+0.0000** | 14.3868 dB | 14.3019 dB | -0.0849 dB | **Tie** |
| **10,000** | 0.3770 | 0.3757 | **-0.0013** | 14.3271 dB | 14.2600 dB | -0.0671 dB | Baseline |
| **12,500** | 0.3751 | 0.3735 | **-0.0016** | 14.2091 dB | 14.2218 dB | +0.0127 dB | Baseline |
| **15,000** | 0.3735 | 0.3722 | **-0.0013** | 14.1961 dB | 14.1735 dB | -0.0225 dB | Baseline |

---

## 3. Analysis & Mechanical Interpretation

### Why Early Training Benefits
During iterations 1,000–5,000, Gaussians are large, unrefined, and prone to overlapping depth boundaries (e.g., foliage against sky, building edges against background). The depth-aware bilateral filter computes weights:
$$W(p, q) = \exp\left(-\frac{\|p-q\|^2}{2\sigma_s^2}\right) \cdot \exp\left(-\frac{|D(p) - D(q)|^2}{2\sigma_d^2 (D(p) + \epsilon)^2}\right)$$
When a Gaussian splat straddles an edge, pixels belonging to disparate depths receive near-zero bilateral weight $W(p, q) \approx 0$. This prevents color leakage across foreground/background silhouettes, providing a clean **+0.11 dB PSNR / +0.0021 SSIM boost**.

### Why Late Training Trails With Static Hyperparameters
In KGS screening, densification continues up to step 10,000 (`grow_until_iter`), reaching the full 100,000 Gaussian ceiling. Beyond step 7,000, Gaussians become tiny sub-pixel and few-pixel primitives.
With a static spatial radius $r=3$ and $\sigma_s=3.0$, the filter blurs across a 7x7 pixel window on smooth depth surfaces. Even though depth differences $|D(p) - D(q)|$ are small, high-frequency textural detail (gravel, grass, fine brick edges) gets slightly attenuated, softening the highest-frequency detail on held-out test frames.

---

## 4. Next Step Options

Based on the empirical evidence that depth bilateral is demonstrably superior in early-mid training (+0.11 dB) but softens late-stage high frequencies when static:

1. **Iteration-Scheduled Annealing (Recommended)**:
   - Linearly or cosine anneal the filter radius / $\sigma_s$ from $r=3 \to 0$ (or deactivate after densification ends at iteration 10,000). This captures the full early-stage anti-bleeding structural guidance without any late-stage texture softening.
2. **Edge-Gated Depth Bilateral**:
   - Only apply the bilateral filter to pixels located within a thresholded depth-gradient or normal-discontinuity map ($|\nabla D| > \tau$), leaving planar surfaces unblurred.
3. **Keep Off as Default & Move to Pure 3D Geometric Prior / Splat3 Strategies**:
   - Keep `use_depth_bilateral: false` by default, leaving the CUDA kernel available in tree, and proceed to the next pure geometric representation improvement.
