# Architectural Note: Fixed Iteration Budget vs. Dataset-Size Scaling in KGS

**Date:** 2026-09-11  
**Topic:** The "30k within 300k" Anomaly & Strategy for Image-Count-Agnostic Fast Convergence  
**Author/Context:** Analysis of indoor multi-view cubemap training (`indoor-test-1`, 942 views, KGS strategy)

---

## 1. Executive Summary & Problem Statement

During training of the 942-image indoor cubemap dataset with anchored ceiling points, an important optimization anomaly was observed:

> **The Anomaly:**  
> Iteration 21,980–30,000 of a **314,000-step run** achieved vastly superior convergence, geometric accuracy, and image fidelity (**34.54 dB PSNR, 0.918 SSIM, 0.102 LPIPS, 0.0204 loss**) compared to iteration 30,000 of a **30,000-step run** on the exact same dataset.
>
> *Why does iteration 30,000 inside an extended schedule perform dramatically better than the final iteration 30,000 of a standard schedule?*

While the results of the extended run are phenomenal, the reliance on a hidden dataset multiplier (`steps_scaler = N / 300 = 3.14`) creates a mismatch between user expectations (predictable wall-clock time) and engine behavior (multi-hour runs).

This note formalizes why this happens and outlines how LichtFeld Studio can achieve this high-quality convergence within a fixed, predictable 30k target window.

---

## 2. Root Cause Analysis: The Mechanics Behind the Anomaly

The superiority of step 30,000 in the extended schedule is driven by four structural factors in the optimization engine:

### 2.1. Position Learning Rate Decay (The Kinetic Sweet Spot)
The Gaussian position learning rate decays exponentially/cosine from `position_lr_init` ($1.6 \times 10^{-4}$) to `position_lr_final` ($1.6 \times 10^{-6}$):
$$\text{LR}(t) = \text{LR}_{\text{final}} + (\text{LR}_{\text{init}} - \text{LR}_{\text{final}}) \cdot f\left(\frac{t}{T_{\text{total}}}\right)$$

* **In a 30,000-step run:** At step 25,000–30,000, $t / T \approx 0.85 - 1.0$. The position learning rate has decayed by **95%–99%**. Gaussians are essentially frozen in place. If a splat is 2 cm away from its true planar surface, gradients are too weak to move it.
* **In a 314,000-step run:** At step 30,000, $t / T \approx 0.095$ (only 9.5% through the schedule). The optimizer is still operating at **~90% of its maximum learning rate**. Gaussians possess full kinetic mobility to migrate, rotate, and snap into exact geometric surfaces.

### 2.2. Multi-Scale Progressive Resolution Runway
The progressive resolution pyramid schedule is linked to total iterations:
$$\text{Transition Iteration} = \text{progressive\_resolution\_fraction} \times T_{\text{total}} = 0.12 \times T_{\text{total}}$$

* **In a 30,000-step run:** $0.12 \times 30,000 = \mathbf{3,600 \text{ steps}}$. Across 942 images, each camera is seen only $\approx 3$ times before the model is forced into full resolution. High-frequency pixel noise traps Gaussians in shallow local minima before low-frequency geometry has stabilized.
* **In a 314,000-step run:** $0.12 \times 314,000 = \mathbf{37,680 \text{ steps}}$. The model enjoys an extensive coarse-to-fine runway at $1/4$ and $1/2$ resolution. Every camera is seen $\approx 40$ times in downsampled space, establishing a clean low-frequency room foundation. When full resolution arrives around step 30k, the underlying structure is already aligned.

### 2.3. Topology Freezing Boundary (`stop_refine`)
In KGS, active floater recycling and densification are gated by `stop_refine`:
* **In a 30,000-step run:** `stop_refine` fires at **step 25,000**. All pruning, splitting, and kinetic relocation shut down for the final 5,000 steps.
* **In a 314,000-step run:** `stop_refine` is scheduled for **step 78,500** ($25,000 \times 3.14$). At step 30k, KGS is actively recycling zero-opacity floaters from empty room space and moving them directly onto high-error edges (window frames, ceiling edges).

### 2.4. Epoch Budget Disparity
Because the trainer samples 1 image per step:
* A 100-image dataset at 30k steps receives **300 epochs**.
* A 942-image dataset at 30k steps receives only **31.8 epochs** (each camera seen ~31 times).
Scaling to 314k steps gave the 942-image dataset **333 epochs**, matching the sampling density of small scenes.

---

## 3. The Design Trade-Off: Scaling vs. Fixed Target

| Characteristic | Auto-Scaled Epochs (Current) | Fixed 30k Budget (Naive) | Ideal Hybrid Engine (Target) |
| :--- | :--- | :--- | :--- |
| **Step Count on 942 Views** | 314,000 steps | 30,000 steps | 30,000 steps |
| **Wall-Clock Time** | ~4.5 hours | ~20 minutes | ~20–25 minutes |
| **Convergence Quality** | **34.54 dB (Exceptional)** | ~31.6 dB (Starved) | **34.0+ dB (Target)** |
| **User Predictability** | Poor (hidden multiplier) | High | High |
| **Memory / Pruning** | High-mobility KGS | Premature freeze | Flatter LR plateau |

---

## 4. Architectural Roadmap: Achieving 34+ dB in a Fixed 30k Window

To deliver the benefits of the 314k run within a fixed, fast 30,000-step budget agnostic of image count, three engine improvements are recommended:

### Recommendation 1: Warm Cosine Learning Rate Schedule (Flat Plateau)
* Replace continuous exponential decay with a schedule that maintains full position learning rate ($\text{LR}_{\text{init}}$) across the first **60% of training** (steps 0 – 18,000).
* Begin cosine annealing only during the final 20–30% (steps 22,000 – 30,000).
* *Impact:* Gaussians retain mobility throughout the growth phase and do not freeze prematurely.

### Recommendation 2: Epoch-Grounded Resolution Pyramids
* Decouple `--progressive-resolution` from percentage of total steps.
* Define pyramid transitions in terms of minimum epochs:
  $$\text{Pyramid Transition} = \max(3,000, 15 \times \text{num\_images})$$
* *Impact:* Large datasets are guaranteed sufficient low-frequency convergence before transitioning to noisy high-resolution gradients.

### Recommendation 3: Multi-View Gradient Accumulation / Micro-Batching
* For datasets with $N > 300$ images, process a mini-batch of $K = 2 \text{ to } 4$ cameras per iteration (or accumulate gradients across $K$ views before `optimizer.step()`).
* In 30,000 iterations at $K = 4$, the model processes **120,000 image evaluations** in ~25 minutes—delivering the epoch volume of a 120k run within a 30k step timeline.

### Recommendation 4: Explicit, Transparent UI Options
* Provide an explicit mode selector in the Training Panel:
  * **Fast Interactive (30k Fixed):** Uses micro-batching and flat LR; strictly honors 30,000 steps.
  * **Exhaustive Quality (Scaled):** Displays upfront: *"Estimated 314,000 steps (~4.5 hrs) based on 942 images."*
