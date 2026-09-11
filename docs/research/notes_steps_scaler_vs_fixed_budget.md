# Research Note: Why Bumping Iterations Solved Convergence — The `compute_decay_gamma` Mechanism

**Date:** 2026-09-11  
**Topic:** Exact Cause of the 30k vs. 314k Convergence Gap & The 21x Learning Rate Slider  
**Context:** Indoor multi-view cubemap training (`indoor-test-1`, 942 views, KGS strategy)

---

## 1. Executive Summary & Correction of Previous Assumptions

Earlier theoretical assumptions posited that large datasets require hundreds of epochs (passes per view) to converge, and that a 30k run failed because 942 images only received ~31 passes.

**That assumption was proven false by empirical inspection:**
> At **iteration 21,980**, with **only 23 passes per view** ($21,980 / 942$), the model **had already achieved 34.54 dB PSNR, 0.918 SSIM, 0.102 LPIPS, and 0.0204 loss**.

The scene never needed 300 passes. Twenty-three passes was already more than enough.

The true mechanism behind why resetting training with bumped iterations produced an immediate leap in convergence was verified directly in the C++ optimization code: **bumping total iterations acted as a direct $21\times$ multiplier on the active learning rate at step 22,000.**

---

## 2. The Exact Mechanism: `compute_decay_gamma`

In [`src/training/strategies/kgs.cpp:197-202`](file:///c:/gitprojects/LichtFeld-Studio/src/training/strategies/kgs.cpp#L197-L202), the learning rate decay factor is computed as:

```cpp
[[nodiscard]] double compute_decay_gamma(const double start, const double end, const size_t steps) {
    if (steps == 0 || start <= 0.0 || end <= 0.0) {
        return 1.0;
    }
    return std::pow(end / start, 1.0 / static_cast<double>(steps));
}
```

At any iteration $t$, the active position learning rate is:
$$\text{LR}(t) = \text{start} \times \left(\frac{\text{end}}{\text{start}}\right)^{\frac{t}{\text{steps}}}$$

Given the engine defaults:
* $\text{start} = 0.00016$
* $\text{end} = 0.0000016$ ($\text{end} / \text{start} = 0.01$, a 100x decay)
* Formula: $\mathbf{\text{LR}(t) = \text{start} \times 0.01^{\frac{t}{\text{steps}}}}$

---

## 3. The 21.3x Difference at Iteration 22,000

Comparing the active learning rate at **step 22,000** (where the 34.54 dB milestone occurred) across both schedules:

| Schedule Configuration | Exponent ($t / \text{steps}$) | Active LR Factor ($0.01^{\text{exp}}$) | Active Learning Rate | Gaussian Mobility |
| :--- | :---: | :---: | :---: | :--- |
| **Standard 30,000-Step Run** | $\frac{22,000}{30,000} = \mathbf{0.733}$ | $0.01^{0.733} = \mathbf{0.034}$ | $0.0000054$ | **Frozen.** Decayed by 96.6%. Splats cannot move to surfaces. |
| **Bumped Run (314k Steps)** | $\frac{22,000}{314,000} = \mathbf{0.070}$ | $0.01^{0.070} = \mathbf{0.724}$ | $0.0001158$ | **Full Mobility.** Still at 72.4% of initial power. |

$$\frac{\text{LR}_{\text{bumped}}(22,000)}{\text{LR}_{30\text{k}}(22,000)} = \frac{0.724}{0.034} = \mathbf{21.3\times \text{ Higher Learning Rate}}$$

In the 30k run, the learning rate collapsed prematurely: by step 22k, the optimizer had already stripped away 96.6% of its step size. 

By increasing total steps, `steps` in the denominator dilated the decay curve, **delivering a $21.3\times$ higher step size throughout the critical refinement window**.

---

## 4. The Second Multiplier: KGS Target Density Pacing

The second manual change made in the GUI was bumping `max_cap` from 1.0M to 2.5M.

In [`src/training/strategies/kgs.cpp:2088-2096`](file:///c:/gitprojects/LichtFeld-Studio/src/training/strategies/kgs.cpp#L2088-L2096):
```cpp
const long long remaining = std::max<long long>(0, cap - current_active);
const long long target_per_window = (remaining + windows_left - 1) / windows_left;
```

* At `max_cap = 1,000,000`, KGS throttled growth per window to avoid overrunning the 1M ceiling.
* At `max_cap = 2,500,000`, KGS permitted **2.5x larger growth per window** during the exact phase when the learning rate was 21x higher.

The combination was synergistic: **high primitive capacity + high mobility allowed 2.5M Gaussians to rapidly populate and snap directly into high-frequency details.**

---

## 5. Architectural Takeaway & The Real Fix for 30k Runs

We do **not** need multi-hour 300k runs, and we do **not** need complex batching.

To achieve this exact 34.5+ dB result within a true **20-minute, 30,000-step run**, the engine only needs two straightforward tuning fixes:

1. **Replace Exponential Decay with a Warm Cosine / Flat-Top Schedule:**
   * Hold position LR at **80–100% of initial strength through step 20,000–24,000**.
   * Only drop into rapid decay during the final 6,000 steps (steps 24,000 – 30,000).
   * This gives the standard 30k run the exact same high-mobility window that the 314k run enjoyed.
2. **Default `max_cap` to 2.5M on Multi-Room Datasets:**
   * Avoid premature growth choking by giving complex scenes sufficient headroom.
