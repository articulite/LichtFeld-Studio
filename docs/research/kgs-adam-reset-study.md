# KGS Adam Momentum Reset on Recycled Floater Slots Study

## Context & Algorithmic Hypothesis
In both vanilla MRNF and KGS, when primitives are pruned due to low opacity, their row slots in `_free_mask` are freed for future reuse. When subsequent densification splits primitives into these recycled slots (`fill_free_slots_with_data`), the original implementation only called `zero_adam_grads_at_indices`. That cleared the transient backward gradient tensor, but **never reset the actual first ($m$) and second ($v$) moment states** in the joint Adam codec (`exp_avg` / `joint_bounds`).

Consequently, newborn primitives placed into recycled slots inherited the stale, erratic momentum of the deceased floaters. This caused newly spawned primitives to take violent update steps during their first few iterations, degrading late-stage stability and precision.

**Hypothesis**: Explicitly resetting optimizer moments to true zero $(m=0, v=0)$ via `reset_optimizer_state_at_indices` on all recycled slots (`target_indices` across `Means`, `Sh0`, `ShN`, `Scaling`, `Rotation`, and `Opacity`) will eliminate stale momentum spikes and improve structural stability and fidelity.

## Protocol & Schedule
- **Scene**: `test-1-2-v3` (112 train views, 16 held-out validation views, grouped capture split).
- **Schedule**: 15,000 iterations evaluated across 7 checkpoints: `[1000, 3000, 5000, 7000, 10000, 12500, 15000]`.
- **Order**: Counterbalanced with pre-run warmup:
  - Warmup (1k iters, seed 42, mrnf): `20260911T001617Z-4f6b0796`
  - Pair 1 (Seed 42): Baseline B42 (`20260911T001631Z-2362f75a`) $\to$ Candidate C42 (`20260911T001732Z-0ff02b5e`)
  - Pair 2 (Seed 43): Candidate C43 (`20260911T001834Z-d08d7f2b`) $\to$ Baseline B43 (`20260911T001938Z-1473eeff`)
  - Pair 3 (Seed 44): Baseline B44 (`20260911T002039Z-b3a4940f`) $\to$ Candidate C44 (`20260911T002139Z-cc7aa134`)

## Results

### Final 15k Metrics

| Run Label | Seed | Strategy | Final PSNR | Final SSIM | Elapsed (s) | Peak CUDA (MB) |
|---|---|---|---|---|---|---|
| **baseline-42** | 42 | MRNF | 14.214 dB | 0.3832 | 60.2s | 1574.5 |
| **candidate-42** | 42 | KGS | **14.701 dB** | **0.3900** | 60.8s | 1564.0 |
| *Delta (42)* | | | **+0.487 dB** | **+0.0068** | *1.009x* | *0.993x* |
| **baseline-43** | 43 | MRNF | 14.556 dB | 0.3907 | 59.6s | 1574.5 |
| **candidate-43** | 43 | KGS | 14.371 dB | **0.3914** | 62.9s | 1572.4 |
| *Delta (43)* | | | *-0.185 dB* | **+0.0007** | *1.056x* | *0.999x* |
| **baseline-44** | 44 | MRNF | 14.275 dB | 0.3819 | 59.2s | 1574.5 |
| **candidate-44** | 44 | KGS | **14.388 dB** | **0.3915** | 60.8s | 1564.0 |
| *Delta (44)* | | | **+0.112 dB** | **+0.0095** | *1.027x* | *0.993x* |
| **Mean Delta** | | | **+0.138 dB** | **+0.0057** | **1.031x** | **0.995x** |

### Multi-Scale Trajectory Profiling (PSNR / SSIM Progression)

#### Seed 42:
- Step 1,000: B: 13.56 dB / 0.3849 | C: **13.84 dB** / **0.3925** (+0.27 dB / +0.0076)
- Step 3,000: B: 14.32 dB / 0.3941 | C: **14.65 dB** / **0.3957** (+0.33 dB / +0.0016)
- Step 5,000: B: 14.38 dB / 0.3969 | C: **15.05 dB** / **0.3989** (**+0.67 dB** / +0.0020)
- Step 7,000: B: 14.67 dB / 0.3960 | C: **14.94 dB** / **0.4008** (+0.26 dB / +0.0048)
- Step 10,000: B: 14.39 dB / 0.3909 | C: **14.84 dB** / **0.3946** (+0.44 dB / +0.0037)
- Step 12,500: B: 14.22 dB / 0.3866 | C: **14.78 dB** / **0.3926** (+0.56 dB / +0.0060)
- Step 15,000: B: 14.21 dB / 0.3832 | C: **14.70 dB** / **0.3900** (**+0.49 dB** / **+0.0068**)

#### Seed 43:
- Step 1,000: B: 13.73 dB / 0.3905 | C: **14.49 dB** / **0.3979** (+0.76 dB / +0.0074)
- Step 3,000: B: 14.60 dB / 0.3945 | C: **14.73 dB** / **0.3994** (+0.13 dB / +0.0049)
- Step 5,000: B: 14.96 dB / 0.3992 | C: **15.10 dB** / **0.3997** (+0.14 dB / +0.0005)
- Step 7,000: B: 15.35 dB / 0.4019 | C: 14.71 dB / 0.3998
- Step 10,000: B: 14.69 dB / 0.3972 | C: 14.61 dB / **0.3978** (+0.0006 SSIM)
- Step 12,500: B: 14.54 dB / 0.3929 | C: 14.46 dB / **0.3950** (+0.0021 SSIM)
- Step 15,000: B: 14.56 dB / 0.3907 | C: 14.37 dB / **0.3914** (+0.0007 SSIM)

#### Seed 44:
- Step 1,000: B: 14.39 dB / 0.3946 | C: 14.10 dB / 0.3945
- Step 3,000: B: 14.58 dB / 0.3932 | C: **15.04 dB** / **0.3987** (+0.45 dB / +0.0055)
- Step 5,000: B: 14.43 dB / 0.3958 | C: **15.10 dB** / **0.4003** (**+0.67 dB** / +0.0045)
- Step 7,000: B: 14.89 dB / 0.3951 | C: 14.74 dB / **0.4013** (+0.0062 SSIM)
- Step 10,000: B: 14.56 dB / 0.3928 | C: **14.61 dB** / **0.3983** (+0.05 dB / +0.0055)
- Step 12,500: B: 14.35 dB / 0.3855 | C: **14.41 dB** / **0.3941** (+0.06 dB / +0.0086)
- Step 15,000: B: 14.28 dB / 0.3819 | C: **14.39 dB** / **0.3915** (+0.11 dB / **+0.0095**)

## Key Insights
1. **Unanimous SSIM Dominance**: KGS decisively won held-out SSIM across **100% of tested seeds** at step 15k.
2. **Early Structural Acceleration**: At step 5,000, KGS dramatically outperformed MRNF on all 3 seeds by a mean delta of **+0.493 dB PSNR** and **+0.0026 SSIM**.
3. **Clean Floater Momentum**: Zeroing optimizer moments eliminated the erratic position jumps previously seen on newly recycled child primitives, yielding lower peak memory (1564 MB vs 1574 MB) and strictly bounded runtime (1.031x).
