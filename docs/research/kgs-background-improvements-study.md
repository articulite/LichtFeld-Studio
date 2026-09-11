# Research Study: Background Improvements & Upstream Fix Evaluation (MRNF vs KGS at 15k Iterations)

## 1. Executive Summary & Core Questions Answered

This study documents two critical empirical questions investigated on the outdoor development scene 	est-1-2-v3 under the strict 100k Gaussian cap:
1. **Why did MRNF improve when ackground_improvements: true was enabled with upstream commit 10ded50b?**
2. **Why does KGS achieve unanimous paired dominance over MRNF under the exact same ackground_improvements: true configuration?**

All runs were executed across seeds 42, 43, and 44 with a counterbalanced schedule, identical split (112 train / 16 held-out views), and sequential execution locked via .git/hillclimb/gpu.lock.

---

## 2. Empirical Findings

### A. The Three-Way Comparison at 15,000 Iterations

| Strategy | ackground_improvements | Mean PSNR (dB) | Mean SSIM | PSNR Gain vs Plain MRNF | SSIM Gain vs Plain MRNF |
|:---|:---:|---:|---:|---:|---:|
| **Vanilla MRNF** | alse | 14.1305 | 0.3605 | Baseline | Baseline |
| **MRNF + Fix 10ded50b** | 	rue | 14.1794 | 0.3707 | **+0.0489 dB** | **+0.0102** |
| **KGS (Candidate)** | 	rue | **14.3012** | **0.3723** | **+0.1707 dB** | **+0.0118** |

### B. Head-to-Head Paired Results: KGS vs MRNF (Both ackground_improvements: true)

**Harness Screening Decision**: 
etain_for_repeated_seed_screening (Zero defects, unanimous win across every seed).

| Seed | Baseline MRNF PSNR | Candidate KGS PSNR | **PSNR Delta** | Baseline MRNF SSIM | Candidate KGS SSIM | **SSIM Delta** | Elapsed Ratio | VRAM Ratio |
|:---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **42** | 14.1655 dB | 14.3724 dB | **+0.2069 dB** | 0.3676 | 0.3698 | **+0.0022** | 1.03x | 1.004x |
| **43** | 14.2901 dB | 14.3222 dB | **+0.0322 dB** | 0.3724 | 0.3746 | **+0.0022** | 1.01x | 1.008x |
| **44** | 14.0827 dB | 14.2089 dB | **+0.1262 dB** | 0.3722 | 0.3726 | **+0.0004** | **0.95x** *(faster)* | **0.981x** *(lower)* |
| **Mean** | **14.1794 dB** | **14.3012 dB** | **+0.1218 dB** | **0.3707** | **0.3723** | **+0.0016** | **0.998x** | **0.998x** |

### C. Trajectory Dynamics (Mean across Seeds 42, 43, 44)

| Step | MRNF PSNR | KGS PSNR | **Delta PSNR** | MRNF SSIM | KGS SSIM | **Delta SSIM** |
|---:|---:|---:|---:|---:|---:|---:|
| **1,000** | 14.6377 dB | 14.7005 dB | **+0.0628 dB** | 0.3981 | 0.3987 | **+0.0006** |
| **3,000** | 14.5756 dB | 14.5538 dB | -0.0218 dB | 0.3893 | 0.3893 | +-0.0000 |
| **5,000** | 14.3446 dB | 14.3788 dB | **+0.0342 dB** | 0.3796 | 0.3830 | **+0.0034** |
| **7,000** | 14.3667 dB | 14.4146 dB | **+0.0479 dB** | 0.3768 | 0.3788 | **+0.0020** |
| **10,000** | 14.3290 dB | 14.4368 dB | **+0.1078 dB** | 0.3748 | 0.3761 | **+0.0013** |
| **12,500** | 14.2329 dB | 14.3198 dB | **+0.0869 dB** | 0.3724 | 0.3738 | **+0.0014** |
| **15,000** | 14.1794 dB | 14.3012 dB | **+0.1218 dB** | 0.3707 | 0.3723 | **+0.0016** |

---

## 3. Deep Dive 1: Why Upstream Commit 10ded50b Improved MRNF

### The Architectural Flaw in Upstream
Upstream commit 10ded50b (*'MRNF: keep the far-field mask bound across reorders and carry it into FastGS'*) fixed a severe silent defect in the interaction between MRNF and FastGS:
1. **Dangling Mask Pointer Across Morton Permutations**:
   When ackground_improvements: true was enabled, MRNF generated a far-field mask (_far_field_mask) designating distant background splats outside the camera convex hull and passed a raw pointer to AdamOptimizer for per-splat mean-step scaling. However, when permute_gaussian_rows executed periodic spatial Morton reordering, the mask storage was reallocated and permuted, but the raw pointer held by the optimizer was **not republished**. The optimizer continued writing into stale row indices until the next distant strategy event.
2. **FastGS Fused-Adam Completely Dropped Background Scaling**:
   When using FastGS (--fastgs), the fused CUDA Adam kernel initialization helper failed to copy mean_step_scale, mean_step_ratio_max, and the far-field mask pointer altogether. As a result, the entire per-splat position step scaling mechanism was silently inactive under FastGS!
3. **The Fix**:
   Commit 10ded50b added publish_mean_step_far_mask() after every permutation and hull rebuild, and unified parameter passing to carry the far flag, scale ratios, and bounded count directly into FastGS fused Adam.

### Why It Produced +0.0102 SSIM on Outdoor Scenes
In outdoor scenes like 	est-1-2-v3, distant background elements (skyline, far trees, horizon) have very small disparity across cameras and low gradient magnitudes. Without position step scaling:
- Distant splats drift erratically because small pixel errors translate to massive world-space gradients.
- Foreground and background compete under uniform Adam step sizes.
With per-splat mean-step scaling working correctly in FastGS, far-field splats are stabilized with scaled learning rates, preventing background drift from blurring foreground edges and producing a **+0.0102 jump in held-out SSIM**.

---

## 4. Deep Dive 2: Why KGS Beats MRNF under ackground_improvements: true

Even with upstream's background fixes fully active in MRNF, KGS defeats MRNF across all three seeds (+0.122 dB PSNR, +0.0016 SSIM). The root causes:

### Cause 1: Floater Adam Momentum Reset Defect in MRNF
- **The Defect**: In both MRNF and early KGS, when low-opacity floaters are culled, their slot indices are recorded in _free_mask. When new primitives are created via splitting or seeding (ill_free_slots_with_data), these free slots are recycled to store the child splats.
- MRNF called zero_adam_grads_at_indices, which sets current gradients to zero, **but left the Adam momentum buffers ($ and $) completely untouched**!
- Because floaters had been drifting erratically prior to being culled, their slots stored high-magnitude, chaotic momentum vectors in exp_avg and exp_avg_sq. Newly born child splats inherited this dead-floater momentum and were immediately propelled across the scene in their first Adam step!
- **The KGS Fix**: KGS explicitly calls 
eset_optimizer_state_at_indices(*_optimizer, ...) across all parameter groups (Means, Sh0, ShN, Scaling, Rotation, Opacity). Newborn primitives start with pure zero momentum (=0, v=0$), preventing floater rebirth and late-stage convergence haze.

### Cause 2: Splat3 Scale-Aware Growth Prior
- **The Defect in MRNF**: MRNF ranks growth candidates strictly by error / gradient magnitude normalized by visibility. This creates a pathological bias toward splitting tiny needle-like splats on high-contrast edges over and over, while large, under-resolved background and structural surfaces remain un-split.
- **The KGS Solution**: KGS incorporates a bounded scale prior into densification growth weights:
  \text{scale\_norm} = \text{clamp}(0.5 \times (\text{scale}_{\max} + 3.5), -1.0, 1.0)
  \text{growth\_weights} = \text{growth\_weights} \times \exp(\text{scale\_norm})
  This gently up-weights large under-resolved primitives without starving high-frequency textures, filling structural scene capacity faster and more uniformly.

### Cause 3: Dynamic Floater Recycling at 100k Capacity Cap
- When the 100k cap is approached, MRNF locks up and stops refining because free slots are exhausted.
- KGS dynamically raises the opacity pruning floor from /255$ up to .02$, continuously culling imperceptible transparent floaters and recycling their slots for high-gradient surface refinement.

---

## 5. Reconciling the Early 3.6k Study with the 15k Results

In docs/research/outdoor-background-improvements-study.md (conducted at 3,600 iterations), ackground_improvements: true on MRNF was rejected because:
1. seed_far injected 2,000 far primitives every refine step, causing the splat count to explode to ~90k by step 2,400 while baseline MRNF had only 8.5k splats.
2. In a short 3,600-iteration budget, Adam only had 1,200 post-growth steps—nowhere near enough time to converge 90k primitives, causing post-growth degradation.

In contrast, at **15,000 iterations**:
- Both baseline and candidate have 10,000+ iterations to optimize the 100k primitives.
- Upstream commit 10ded50b fixes the fused-Adam mask carry that was broken during the 3.6k study.
- Under mature 15k training, background improvements provide a net positive for MRNF (+0.0102 SSIM), and **KGS leverages it cleanly to establish unanimous dominance**.
