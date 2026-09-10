# Outdoor growth dynamics — 2026-09-10

Completed configuration-only budget: one excluded 400-step warmup and six measured runs, seeds 42/43/44, alternating baseline .07 and candidate .14. All seven train/evaluate exits were zero. No rebuild, implementation change, evaluator change, download, or previous-result overwrite.

The smaller outdoor `test-1-2-v3` split remains 112 training and 16 held-out views. Shared settings: 3600 iterations, width512, cap100000, refine_every100, grow_until_iter2400, stop_refine3501, SH interval900; evaluation at400/800/1200/2400/3600. The generator scales the schedule with duration, so the earlier 1200-step campaign is not a matched continuation or direct control. Each run started fresh. Limits:300 seconds/run,7000MiB sampled ceiling,250ms sampling, one GPU process at a time.

| Iteration | Mean baseline PSNR | Mean candidate PSNR | Paired mean gain dB | Baseline sample SD |
|---|---:|---:|---:|---:|
|400|11.339303|11.228535|-.110768|.176255|
|800|13.247032|13.842866|+.595835|.163890|
|1200|13.834036|14.486315|+.652280|.150935|
|2400|13.768725|14.655928|+.887203|.337229|
|3600|14.617215|14.840006|+.222791|.075725|

These are three seed means, not confidence intervals or independent scene replicates. Checkpoints are correlated. Final paired gains are +.229165,+.235911,+.203296dB; SSIM improves in all three pairs.

| Seed/treatment | Final SSIM | Gaussians | Harness seconds | Internal perf seconds | Sample peak MiB | CUDA peak MiB |
|---|---:|---:|---:|---:|---:|---:|
|42/.07|.403294|8484|11.859|11.374|504|1497.6|
|42/.14|.407563|34707|14.250|13.800|514|1507.6|
|43/.07|.402992|8502|12.406|11.919|498|1489.6|
|43/.14|.407264|34504|14.688|14.189|512|1505.6|
|44/.07|.403703|8511|12.453|11.993|498|1499.6|
|44/.14|.408324|34701|14.687|14.108|514|1507.6|

Growth .14 produces about4.08x the final Gaussians. Counts are unchanged between the2400 and3600 checkpoints, although split/prune topology updates continue through3500; constant count does not imply a frozen topology. Its quality advantage peaks at2400 and contracts after growth ends; checkpoint trends therefore do not support judging this treatment from a single early score. This is an observed relationship, not proof of a causal mechanism. All candidate elapsed ratios exceed the predeclared15% comparability band (roughly18–20% slower); internal perf also rises roughly18–21%. These timing scopes include evaluation overhead and are not pure optimization throughput. Fixed baseline-then-candidate ordering leaves thermal/cache drift confounded with treatment. No speedup or matched-time quality claim.

Decision: **reject this candidate under the current resource-comparability screen; no promotion**. Faster capacity growth improves final quality slightly, but the extra capacity/cost is not justified by this screen. Retain all evidence for future study, not the candidate as an established improvement. Both inspected seed42 final renders remain severely blurred with foreground artifacts; one view per treatment is diagnostic only.

Validation: every checkpoint has exactly one ordered metrics row, finite PSNR/SSIM and timing/count values, count within cap, and the exact16 unique held-out names with finite per-image PSNR/SSIM. Final evaluator passed unchanged. Manifest hash sidecars verified; executable, evaluator, DLL, dataset and split fingerprints match the initial outdoor baseline. Paired configuration differences are only grow_fraction. Splitting stops before3501. LPIPS remains unavailable, no weights fetched. Preserve the discrepancy between sampled whole-device memory and internal CUDA accounting; neither is substituted for the other.

Machine-readable evidence: `outdoor-growth-results.json`. Local plan, runner, checkpoint checks, index and logs: `results/research_hillclimb/growth-study-20260910/`. Warmup: `20260910T190129Z-5ed6bfbc`. Measured run IDs are in the result JSON. Initial results remain intact.

Limits: one development scene, only one held-out capture group, SfM originally fit with all views, reduced resolution/duration, no complete RNG continuation guarantee, no independent final scene. Luna reviewed the plan and result interpretation; primary reviewed its findings and directly checked artifacts and renders.

Budget exhausted; no automatic expansion. Next proposed campaign requires a fresh bounded budget: hold this schedule fixed and compare checkpoint quality at matched elapsed budgets with balanced treatment order, or separately vary growth duration while retaining .07. Do not change fraction and growth duration together. No next GPU command is authorized by this completed budget. Read this report and HANDOFF.md before generating new specs.
