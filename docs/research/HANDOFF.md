# Provider-neutral handoff: MRNF hill climb

## Status
Initial bounded cycle COMPLETE, 2026-09-10. No pending build or GPU job. Four successful runs, no failures. Read `mrnf-hillclimb.md` measured checkpoint and `initial-screen-results.json` for results. Do not reconstruct the conversation or repeat completed setup.

User authorized local bounded experiments on branch `codex/hillclimb-mrnf`, Luna subagents with primary review, resumability, cost restraint, and smaller dataset first. Luna work was reviewed/repaired; agents then hit usage limits. No upstream merge, large downloads, purchases or automation authorized.

## Results and interpretation
Candidate changes only grow_fraction .07 -> .14. PSNR gain outdoor+.571612dB, indoor+.495310dB; SSIM also increases. RETAIN FOR REPEATED-SEED SCREENING ONLY; NO PROMOTION. One seed42,1200 iterations,width512,cap100000. Outdoor render still severely underfit. LPIPS weights unavailable. First outdoor run incurred startup overhead, so no speedup claim. Internal CUDA peaks about1.43GiB differ from nvidia-smi samples445-469MiB: preserve both.

All runs under `results/research_hillclimb/runs`:
- Outdoor baseline `20260910T184132Z-d0eb9803`
- Indoor baseline `20260910T184239Z-91cb6818`
- Outdoor candidate `20260910T184307Z-0ec35d21`
- Indoor candidate `20260910T184321Z-100bcfc7`

Each has immutable manifest/hash, state, process records, logs, streaming VRAM, metrics and GT/render PNGs. All train/eval exit0; exact heldout names checked. Splitting/pruning observed and stopped before1101. Four-run budget exhausted. Do not expand this completed pass automatically.

## Next campaign
Declare a fresh bounded budget. Warm runtime, then alternating baseline/candidate at seeds42/43/44 on BOTH scenes. Calibrate baseline variability and compare internal perf plus total time. If gains survive, confirm at shared target iterations/resolution and matched time/memory. No independent final scene is available. SfM was fit using all views originally, a known limitation.

Use `scripts/research_hillclimb/README.md` and CLI `--help` for reproducible commands. Example (PowerShell repository root):
```powershell
python scripts/research_hillclimb/make_experiment.py results/research_hillclimb/staging/test-1-2-v3 results/research_hillclimb/specs/NEW_NAME --seed 43
python scripts/research_hillclimb/harness.py run results/research_hillclimb/specs/NEW_NAME/experiment.json --output-root results/research_hillclimb/runs
```
Candidate generation additionally takes `--grow-fraction 0.14` and --baseline-run COMPLETED_BASELINE_PATH. Pair with `decide.py`; evaluator remains outside candidate mutation scope. Always use new spec/output directories. Existing complete runs are evidence, never overwrite.

## Data and interruption safety
Valid staging only: `test-1-2-v3` outdoor112 train/16 eval; `sparse-cubic-v3` indoor126/18. Same parent `results/research_hillclimb/staging`. v2 INVALID and unused. Whole captures held out, adjacent captures excluded. Images are hardlinks: never edit staged files.
One GPU job at a time. Every existing run used300second timeout,250ms sampling,7000MiB sampled cutoff. Do not remove `.git/hillclimb/gpu.lock` until owner AND child PIDs from train.process.json/evaluate.process.json are confirmed dead. Failed/interrupted stages require fresh attempts; clean-stage resume is fingerprint-checked. No full RNG checkpoint continuation guarantee.

## Build and code
Implementation commits:4e91df09 opt-in seed;6f10bca3 harness; a6c19643 adapter. Final successful build `.git/hillclimb/build-final.log`; provenance `.git/hillclimb/built-provenance.json`. Source/executable/DLL hashes frozen per run. Dirty audit flag was untracked HANDOFF.md only. Avoid rebuilding after documentation commits: evaluated implementation remains a6c19643. Version refresh recompiled py_ui.cpp for about17CPUminutes.
Windows RTX5060 laptop8GB,MSVC14.44,CUDA12.8,SM120. Original73 cached vcpkg ABIs restored at original `build-windows-release/vcpkg_installed` prefix. `VCPKG_MANIFEST_INSTALL=OFF`. Do not blindly reinstall dependencies. Build helper `.git/hillclimb/build-research.cmd`; backups `.git/local-build-backup`; extra ignored `build-research-deps` copy remains. Preserve local workarounds. MCP discovery was completed via repository bridge; artifacts under `.git/hillclimb`. Follow AGENTS.md for new app operations.

17 Python tests and standalone C++ seed test passed; full GPU test suite not run. Default MRNF clock seeds preserved absent LFS_RESEARCH_SEED. Existing tensor/camera seeds unchanged. Seeded choices are not a claim of bitwise GPU determinism.

## Context and build-monitoring efficiency
- Start from this handoff and compact result JSON; read older research history only for a specific unresolved question.
- Run approved, bounded experiment batches sequentially with one GPU job at a time. Review one compact table per batch: exit status, quality checkpoints, Gaussian count, elapsed time, memory and decision.
- Redirect full build/training output to files. Prefer completion waits; avoid repeated log reads while a process is healthy. Read a short log tail on failure or suspected stall, and expand only around a specific error. Keep required user updates brief without rereading logs just to produce an update.
- Automatically extract metrics and sanity checks. Inspect raw logs only when validation fails or a result needs explanation; never repeatedly dump successful logs or full manifests into context.
- Freeze executable and evaluator across JSON-only experiments. Rebuild incrementally only for implementation changes; do not refresh version stamps or rebuild for documentation changes. Batch a few justified optional behaviors into one build, preserving MRNF defaults, then vary one behavior at a time.
- Delegate only concrete independent implementation/review work, with concise findings and file references. Avoid agents for routine polling.
- Update the handoff at meaningful checkpoints with completed run IDs, decision, blockers and exact next command. Keep it current instead of appending contradictory status histories.
- Short runs establish growth/convergence relationships, not final quality. Use multiple checkpoints, repeated seeds and longer matched-time comparisons before promotion; do not trade evidence integrity for token savings.
