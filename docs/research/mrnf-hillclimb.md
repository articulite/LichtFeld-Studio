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
