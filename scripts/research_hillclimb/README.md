# Measured MRNF research loop

The baseline configuration is `eval/mrnf_optimization_params.json`, kept unchanged.
`make_experiment.py` derives a deliberately short screening schedule, shared by all
scenes. A candidate may change only `grow_fraction`; it requires a completed
baseline. This is parameter hill climbing, not a claim of a new algorithm.

## Current local cycle

Read `docs/research/mrnf-hillclimb.md` first. Dataset preparations, manifests, logs,
models and rendered images live under the Git-ignored `results/research_hillclimb`.
Build evidence and local recovery commands live under `.git/hillclimb`.

The two supplied development scenes have 6 and 16 views per capture. Staging
preserves every selected capture group, excludes immediate temporal neighbors of
held-out captures, preserves COLMAP record order, and places validation images at
**zero-based indices 0, 8, 16, ...**. The source images are read-only hardlinks;
never edit them through the staged directory. Only sparse points supported by
selected training cameras are retained. Sparse geometry/colors were originally
reconstructed using all source views; this is not an independently reconstructed
train-only SfM benchmark. These small development subsets cannot establish
cross-scene generalization. Reserve new entire scenes for final testing.

```powershell
python scripts/research_hillclimb/prepare_colmap.py DATASET NEW_STAGING_DIR
python scripts/research_hillclimb/make_experiment.py NEW_STAGING_DIR NEW_SPEC_DIR
python scripts/research_hillclimb/harness.py validate NEW_SPEC_DIR/experiment.json
python scripts/research_hillclimb/harness.py run NEW_SPEC_DIR/experiment.json --output-root results/research_hillclimb/runs
```

The initial default is 1,200 iterations at maximum width 512, 100,000 Gaussian cap,
100-step refinement, growth through step 800, and refinement stopping at step
1,101 (off cadence). This exercises growth, pruning and stopping transitions.
It is **screening only**. Calibrate memory and elapsed time before increasing
settings. The cap is not a VRAM guarantee. Optional neural weights are not
downloaded; LPIPS is recorded if locally available. Ground truth is real held-out
images, with saved per-image metrics checked against the exact expected names.

## Provenance and seeds

`provenance.py` hashes source, executable and runtime DLLs. A matching embedded
commit or a `-dirty` marker is evidence, not proof of binary/source equivalence;
a successful rebuild plus frozen hashes is required for this cycle.

`LFS_RESEARCH_SEED` is an opt-in unsigned 64-bit MRNF seed. It derives topology
and noise RNG seeds from the operation and iteration. Without it, historical
clock seeding remains. The tensor seed remains 42 and camera shuffle seed remains
`0x4c46535f73616d70`. Fresh process repeats control MRNF randomness, not GPU floating
point nondeterminism. Checkpoint continuation of all RNG state is not established;
this cycle always starts from scratch. Changing the seed hook is outside candidate
mutation scope: every baseline and candidate uses the same frozen build.

## Interruption and failures

Each run has a unique directory, immutable `manifest.json` and hash sidecar,
`state.json`, process PID records, stage logs, and streaming `vram.jsonl`.
The GPU lock is repository-wide at `.git/hillclimb/gpu.lock`.
**Do not remove an existing lock until its owner and recorded child processes
have been inspected and are no longer running.** A dead owner can leave a live
training child. There is no automatic stale-lock recovery.

Failed or interrupted stages are never rerun over existing artifacts. Retry with
a new invocation/run directory and keep the failed attempt. A clean stage boundary
can resume using `--resume RUN_DIR`, provided source, dataset, commands and runtime
fingerprints match. Completed runs remain evidence and are not rerun. Resuming an
outer research cycle means reading these records, skipping verified completed
experiments, and selecting the next unattempted manifest.

The total per-run timeout includes training and evaluation. Exit 124 means timeout;
125 means the sampled VRAM ceiling was reached; ordinary nonzero exits and logs
are retained. Sampling uses GPU 0 and measures whole-device usage, including other
applications, at 250 ms by default. Its maximum is a **sampled lower bound on the
true peak**, complemented by `perf_bench.json` internal CUDA/allocator telemetry.
The peak includes in-process evaluation. Expensive perceptual evaluation may need
a separate process at larger resolutions.

## Candidate gate and decisions

After baseline measurement, create the smallest candidate with
`make_experiment.py ... --grow-fraction VALUE --baseline-run COMPLETED_RUN`.
Run the identical policy on both development scenes. Compare actual wall time and
memory, not just iteration count; use baseline repeated-seed variability to set
regression tolerances. Inspect saved GT/render crops. Record retain/reject/pending
and its evidence in the research log. No target-setting promotion from screening.
The evaluator and split preparation must stay frozen during candidate changes.

## Tests

```powershell
python -m unittest -q tests/python/test_research_harness.py tests/python/test_research_summarize.py tests/python/test_research_colmap.py
```

`tests/test_mrnf_research_seed_standalone.cpp` is a dependency-free C++20 smoke test.
Compile from the repository root with its root on the include path; it checks
seed parsing and repeatability across operation/iteration/seed changes. Existing
GPU MRNF strategy tests remain in `tests/test_mrnf_strategy.cpp`; a full GPU suite
is not implied by the standalone smoke test.
