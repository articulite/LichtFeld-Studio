# MRNF hill-climb research resume log

## Objective and constraints
Improve held-out quality versus unchanged MRNF at matched elapsed time and peak memory on an 8 GB laptop. One GPU-heavy job at a time. No upstream merge, large dataset download, purchased compute, or recurring job. Reduced runs are screening only. No promotion without measurements.

## Current state (2026-09-09)
- Branch: codex/hillclimb-mrnf. Starting source: fe7d9029e6071890b63b0ba695d793443f5ac85b; clean at start.
- GPU: NVIDIA RTX 5060 laptop family, 8151 MiB total; initial idle sample 43 MiB, driver 592.15. Target initial training usage approximately 6 GiB, subject to calibration.
- Read AGENTS.md and .git/local-build-backup/README. Preserve backup patch; do not commit machine workarounds.
- MCP initialized through repository bridge with LFS_EXECUTABLE pointing to build-windows-release/LichtFeld-Studio.exe. Required catalog/state resources and tool schemas captured in .git/hillclimb/*.json (local evidence).
- Executable reports v0.5.3-539-gfe7d9029-dirty. Commit matches starting source; exact dirty build provenance not yet established. No training measurements yet.
- Bridge discovery process exited and cleaned up its app child. No GPU training started.
- Luna agents assigned: MRNF read-only inspection, build/data read-only inspection, and resumable harness implementation. Primary agent reviews all changes.

## Resume
Read this log, git status, and scripts/research_hillclimb documentation. Inspect any run manifests/status and live processes before launching anything. Never reuse a result simply because its directory exists. Check build provenance and dataset split identity before interpreting quality. Keep pending/failed experiments explicit. Update this file after each gate and commit useful code/docs only; bulky local evidence stays excluded.

## Pending gates
1. Locate real datasets and select contrasting held-out scenes; verify capture grouping and leakage controls.
2. Establish executable/source provenance or rebuild with isolated local settings.
3. Validate harness, profile conservative MRNF baseline duration and memory, then declare bounded initial run budget.
4. Implement one isolated candidate only after baseline, exercise relevant transitions, screen and decide with evidence.

## Review checkpoint (2026-09-09, bootstrap ongoing)
- User supplied second dataset: C:/Users/Admin/Pictures/Lichtfield/test-1-2/colmap, 16 perspective views per capture. First source has six views per capture.
- IMPORTANT: staging directories ending v2 are INVALID: heldout record offset was 7 but app evaluates index modulo8 ==0. Do not train/use them. Corrected v3 preparation and CPU tests pending.
- MRNF ratio ranking is gated by background_improvements=false; toggling ratio rank alone is a no-op. Prefer one effective config change (e.g. grow_fraction) after baseline.
- Default MRNF topology/noise seeds use wall clock. Opt-in LFS_RESEARCH_SEED helper in progress, baseline default unchanged; separate fresh processes required. No checkpoints reused.
- Reviewed harness: fail-closed interrupted/failed runs, global GPU lock, command/data/source fingerprints and actual evaluator checks being corrected. Test counts/evidence must be verified by primary.
- A subagent attempted a build that triggered dependency removal/reinstall before interruption. No active build process remains from that attempt. Original runtime DLLs/exe are intact; original vcpkg installed tree is incomplete. Do not run normal vcpkg install blindly.
- Recovery: all 73 original package ABIs found in local vcpkg archive cache; extracted into build-research-deps/x64-windows. Existing CMake cache backed up in .git/hillclimb/CMakeCache.before-deps-repath.txt, references repointed to isolated dependencies, VCPKG_MANIFEST_INSTALL=OFF. Configure succeeded via .git/hillclimb/configure-research.cmd; logs there. No tracked local CMake workarounds applied. Compiler/runtime warnings about MSVC redist packaging remain; runtime libs already present.
- No baseline or candidate training measurements yet. Next: finalize validated split/helper, rebuild, sanity-check, profile baseline, set bounded budget.

## Resume checkpoint (2026-09-10 03:17 PDT)
- Interruption recovered. Luna agents hit account usage limits; primary finished their partial edits and review.
- Valid staging directories are sparse-cubic-v3 (126 train/18 eval images, 21/3 capture groups) and test-1-2-v3 (112/16 images, 7/1 groups). Independent primary readback confirms every modulo-0 image belongs to the expected held-out group. Intra-capture center spreads are below 5e-15. Original source images visually inspected: dim interior versus outdoor driveway/vegetation. v2 directories remain invalid and unused.
- Seed helper repaired after review (undefined function/iteration references in partial agent edits). Research seeds now derive from base seed plus operation/iteration, with no process-global counter. Standalone C++20 seed test passed. Baseline defaults unchanged when environment variable is absent.
- 12 harness/evaluator tests plus 2 COLMAP parser tests passed. Primary added streaming whole-device VRAM/free/total samples, process PID records, and exact per-image held-out identity validation. No algorithm candidate has run yet.
- Build recovery refinement: restoring dependencies at a new prefix forced 649 rebuild targets. Stopped that owned build and restored the exact 73 cached ABI packages at their original prefix. Preserved incomplete vcpkg update records under .git/hillclimb/interrupted-vcpkg-updates; original status database again corresponds to restored package files. No new dependency builds/downloads. VCPKG_MANIFEST_INSTALL remains OFF. Isolated copy build-research-deps remains available. Configure-restored.log confirms success.
- Current build command: .git/hillclimb/build-research.cmd, log .git/hillclimb/build-restored.log. Builds original prefix with four jobs. Inspect active process before continuing. No training job started.
- Prepared baseline specs: results/research_hillclimb/specs/profile-indoor/experiment.json and profile-outdoor/experiment.json. Each has 1200 iterations, max width512, Gaussian cap100000, refinement100, stop1101, grow-until800, seed42, 300-second total limit and sampled VRAM cutoff7000 MiB. These are screening/profile runs only, not target baselines.
- Next: finish build and source/binary stamp verification, run indoor baseline profile through harness, calibrate bounded remaining budget, run outdoor baseline, then one effective candidate if gates pass. Never run profile specs against old executable claiming seeded behavior.

## Measured checkpoint — 2026-09-10 11:46 PDT (supersedes pending notes above)

Initial bounded cycle COMPLETE: two baselines and two candidates, zero failed GPU runs. User requested smaller outdoor set first; this order was followed. Final build exited0 (.git/hillclimb/build-final.log), embedded commit a6c19643 matches evaluated source; executable/DLL/source hashes frozen in each run and .git/hillclimb/built-provenance.json. Audit dirty flag refers to untracked HANDOFF.md only. Documentation added after freezing does not warrant recompilation. Version-stamp refresh unnecessarily recompiled py_ui.cpp for about17 CPU minutes; avoid repeating this for documentation.

Candidate changes only grow_fraction .07 -> .14; all other config, split, evaluator, seeds and executable identical. Budget fixed at four successful screening runs, now exhausted. All runs used seed42,1200 iterations,width512,100000 cap,300second timeout and7000MiB sampled ceiling. These small scenes were well below6GiB; this does not test near-budget behavior.

| Scene/treatment | PSNR | SSIM | Gaussians | Harness seconds | Internal perf seconds | Sample peak MiB | CUDA peak MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| Outdoor MRNF |11.677371|.378334|3125|27.360|6.452|445|1459.6|
| Outdoor grow .14 |12.248983|.385140|4864|4.547|3.960|455|1459.6|
| Indoor MRNF |26.129745|.801747|20970|5.250|4.503|469|1463.6|
| Indoor grow .14 |26.625055|.807925|32662|5.218|4.690|457|1461.6|

Exact state/summary values, hashes, and observed split/prune iterations are committed in initial-screen-results.json. Harness wall time includes startup/evaluation; internal perf is a different scope. Outdoor first process had large startup overhead (possible cache/initialization effect, not isolated). No speedup claim. Indoor internal time rose4.15%; sampled/in-process memory stayed similar. Whole-device nvidia-smi samples and CUDA accounting disagree on this Windows machine; retain both, do not claim445MiB is the true peak. Sampling is a lower bound, not a guarantee. LPIPS null in all runs because cached weights absent; no download performed.

Run directories under results/research_hillclimb/runs:
- Outdoor baseline: 20260910T184132Z-d0eb9803
- Indoor baseline: 20260910T184239Z-91cb6818
- Outdoor candidate: 20260910T184307Z-0ec35d21
- Indoor candidate: 20260910T184321Z-100bcfc7

Every train/evaluate exit was0, final iteration1200, exact heldout names/counts verified. Both candidates and baselines exercised actual splitting and soft pruning; observed topology changes stop before1101 and training continues to1200. Existing defaults remain unchanged without opt-in research seed. Seed does not promise bitwise GPU determinism or complete checkpoint RNG continuation.

Visual inspection: each run's eval_step_1200/0.png contains GT/render comparison. Outdoor candidate makes car/vegetation structure more visible, but both outdoor renders are severely blurred/underfit. Indoor candidate shows slightly clearer curtain/table edges; fine texture remains missing. One inspected image per treatment is diagnostic, not a perceptual validation study.

Decision: RETAIN FOR REPEATED-SEED SCREENING ONLY; NO PROMOTION. PSNR gains +.571612 outdoor,+.495310 indoor and SSIM gains +.006806,+.006178 are one-seed screening observations. Automated decision at results/research_hillclimb/decision-grow14.json verifies paired invariants; manual timing caveat above limits its interpretation. No measured variability tolerance, target-settings confirmation, independent test scene or validated floater reduction exists.

Next most informative experiment: warm runtime first, repeat both treatments on both scenes at seeds42/43/44 in alternating order with a newly declared bounded budget. Calibrate baseline variability and use internal training/perf time alongside total time. If gains survive, increase shared iterations/resolution and compare at matched elapsed-time and memory budgets. Outdoor underfitting and tiny initial point count require checking convergence before attributing the gain to a generally better strategy. Do not expand this completed pass automatically.

## Outdoor growth follow-up � 2026-09-10

Completed the newly authorized configuration-only outdoor campaign: one warmup plus six runs, three seeds and five quality checkpoints. See `outdoor-growth-study.md` and `outdoor-growth-results.json` for the current conclusion: reject grow .14 under the elapsed-cost screen; no promotion. This supersedes the initial retain decision for the tested longer outdoor schedule only. No rebuild or changes to existing evidence. HANDOFF.md contains the current resume state.

## Outdoor growth duration follow-up — 2026-09-10

Completed configuration-only growth duration campaign: one warmup plus six measured runs across seeds 42/43/44 with seven quality checkpoints and counterbalanced execution order. Evaluated baseline (grow_until_iter: 2400) against extended growth (grow_until_iter: 3200) at grow_fraction: 0.07. See outdoor-duration-study.md and outdoor-duration-results.json. The candidate passed the 15% elapsed cost screen (elapsed ratios 0.91–1.03) but regressed quality across 2 of 3 seeds (-0.088 dB mean PSNR delta). Decision: reject extended duration; no promotion. HANDOFF.md updated with current resume state.

## Outdoor intermediate growth follow-up — 2026-09-10

Completed configuration-only intermediate growth campaign: one warmup plus six measured runs across seeds 42/43/44 with seven quality checkpoints and counterbalanced execution order. Evaluated baseline (grow_fraction: 0.07) against intermediate growth (grow_fraction: 0.10) with standard growth termination (grow_until_iter: 2400) at 3600 iterations. See outdoor-intermediate-growth-study.md and outdoor-intermediate-growth-results.json. The candidate passed the 15% elapsed cost screen (elapsed ratios 1.050–1.066, +5.0% to +6.6%) and sampled VRAM screen (+0.8% to +3.2%), achieving net positive mean PSNR gain (+0.122 dB) across all 7 checkpoints and positive deltas on seeds 43 (+0.137 dB) and 44 (+0.238 dB). However, seed 42 exhibited a marginal regression (-0.0092 dB PSNR, -0.0012 SSIM). Decision: inconclusive / no promotion under the strict zero-regression screening criteria. HANDOFF.md updated with current resume state.

## Indoor intermediate growth follow-up — 2026-09-10

Completed configuration-only indoor intermediate growth campaign: one warmup plus six measured runs across seeds 42/43/44 with seven quality checkpoints and counterbalanced execution order. Evaluated baseline (grow_fraction: 0.07) against intermediate growth (grow_fraction: 0.10) on indoor scene sparse-cubic-v3 with standard growth termination (grow_until_iter: 2400) at 3600 iterations. See indoor-intermediate-growth-study.md and indoor-intermediate-growth-results.json. The candidate achieved unanimous quality dominance across all three seeds (+0.185 dB, +0.276 dB, +0.145 dB; mean PSNR gain +0.202 dB; SSIM +0.003). However, Gaussian count expanded to 96.5k (close to the 100k cap), causing seed 42 elapsed time to rise by +15.89% (21.88s vs 18.89s), breaching the strict 15% comparability ceiling. Decision: reject_screen / no promotion under the 15% elapsed cost ceiling. HANDOFF.md updated with current resume state.

## Indoor calibrated growth follow-up (0.085) — 2026-09-10

Completed configuration-only indoor calibrated growth campaign: one warmup plus six measured runs across seeds 42/43/44 with seven quality checkpoints and counterbalanced execution order. Evaluated baseline (grow_fraction: 0.07) against calibrated growth (grow_fraction: 0.085) on indoor scene sparse-cubic-v3 with standard growth termination (grow_until_iter: 2400) at 3600 iterations. See indoor-growth-085-study.md and indoor-growth-085-results.json. The candidate passed the 15% elapsed cost screen across all three seeds (elapsed ratios 1.042–1.051, +4.2% to +5.1%) with Gaussian count controlled to ~72.9k (1.34x baseline). It achieved unanimous quality dominance across all three seeds (+0.081 dB, +0.033 dB, +0.109 dB; net mean PSNR gain +0.074436 dB; SSIM +0.0013). Decision: retain for repeated-seed screening; no promotion. HANDOFF.md updated with current resume state.

## Outdoor calibrated growth follow-up (0.085) — 2026-09-10

Completed configuration-only outdoor calibrated growth campaign: one warmup plus six measured runs across seeds 42/43/44 with seven quality checkpoints and counterbalanced execution order. Evaluated baseline (grow_fraction: 0.07) against calibrated growth (grow_fraction: 0.085) on outdoor scene test-1-2-v3 with standard growth termination (grow_until_iter: 2400) at 3600 iterations. See outdoor-growth-085-study.md and outdoor-growth-085-results.json. The candidate passed the 15% elapsed cost screen (elapsed ratios 0.992–1.067, +3.1% mean) and expanded Gaussians moderately to ~11.7k (1.38x baseline). However, it regressed final quality across 2 of 3 seeds (seed 42: -0.251 dB, seed 43: -0.085 dB; net mean PSNR delta -0.100 dB). Decision: reject candidate; no promotion. Combined cross-scene synthesis demonstrates that optimal growth rate is scene-dependent (indoor benefits from 0.085, outdoor underfits at 0.085). HANDOFF.md updated with current resume state.

## Outdoor gradient threshold calibration follow-up (0.002) — 2026-09-10

Completed configuration-only outdoor gradient threshold calibration campaign: one warmup plus six measured runs across seeds 42/43/44 with seven quality checkpoints and counterbalanced execution order. Evaluated baseline (growth_grad_threshold: 0.003) against calibrated threshold (growth_grad_threshold: 0.002) at standard grow_fraction: 0.07 on outdoor scene test-1-2-v3 with standard growth termination (grow_until_iter: 2400) at 3600 iterations. See outdoor-grad-threshold-002-study.md and outdoor-grad-threshold-002-results.json. The candidate comfortably passed elapsed cost screens (ratios 0.965–0.995, -1.9% mean) and sampled VRAM screens (0.988–1.004) with final Gaussian count held virtually identical to baseline (~8,485 vs ~8,478). It achieved unanimous positive SSIM gains across all three seeds (+0.002386 mean) and positive post-growth PSNR convergence (+0.089154 dB net mean gain). However, seed 43 exhibited a -0.0908 dB dip in final PSNR. Decision: inconclusive / no promotion under strict zero-regression screening threshold. HANDOFF.md updated with current resume state.

## Indoor gradient threshold calibration follow-up (0.002) — 2026-09-10

Completed configuration-only indoor gradient threshold calibration campaign: one warmup plus six measured runs across seeds 42/43/44 with seven quality checkpoints and counterbalanced execution order. Evaluated baseline (growth_grad_threshold: 0.003) against calibrated threshold (growth_grad_threshold: 0.002) at standard grow_fraction: 0.07 on indoor scene sparse-cubic-v3 with standard growth termination (grow_until_iter: 2400) at 3600 iterations. See indoor-grad-threshold-002-study.md and indoor-grad-threshold-002-results.json. The candidate failed the 15% elapsed cost screen on seed 42 (elapsed ratio 1.3261, +32.6%) and regressed final quality across 2 of 3 seeds (seed 42: -0.064 dB, seed 44: -0.034 dB; net mean PSNR delta -0.001272 dB). Decision: reject_screen; no promotion. Combined cross-scene synthesis shows that growth_grad_threshold: 0.002 does not generalize across scenes. HANDOFF.md updated with current resume state.

## Outdoor screen footprint clamping follow-up (0.2) — 2026-09-10

Completed configuration-only outdoor screen footprint clamping campaign: one warmup plus six measured runs across seeds 42/43/44 with seven quality checkpoints and counterbalanced execution order. Evaluated baseline (max_screen_share: 0.3) against tightened clamping (max_screen_share: 0.2) at standard grow_fraction: 0.07 on outdoor scene test-1-2-v3 with standard growth termination (grow_until_iter: 2400) at 3600 iterations. See outdoor-screen-share-02-study.md and outdoor-screen-share-02-results.json. The candidate passed elapsed cost screens (ratios 0.907–1.003, -3.7% mean) and sampled VRAM screens (0.996–1.016) with Gaussian count rising slightly (+2.6% to ~8,691). While it achieved late PSNR convergence (+0.085 dB mean gain), it caused severe early trajectory degradation (-1.198 dB @ iter 400, -0.883 dB @ iter 800) due to premature splitting of broad primitives, and regressed final SSIM in 2 of 3 seeds (net mean delta -0.000625). Decision: inconclusive / no promotion under strict zero-regression screening threshold. HANDOFF.md updated with current resume state.
