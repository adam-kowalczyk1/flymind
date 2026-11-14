# RT2: bug hunt. Is the DATA vs SWS difference in V5 v4.1 a software artifact?

Date: 2026-10-30. Scope: the E1 DATA vs SWS difference (DNa02 ipsilateral steady state). E6 was not re-simulated.
Read-only on every project file. Helper script and its outputs:
`/private/tmp/claude-501/-Users-admin-so101-fly-project/075990a2-3231-4039-8d41-31f3fdcb9204/scratchpad/rt41/RT2/rt2.py`
and `/private/tmp/claude-501/-Users-admin-so101-fly-project/075990a2-3231-4039-8d41-31f3fdcb9204/scratchpad/rt41/RT2/rt2_results.json`.
Interpreter: `.venv/bin/python -I -B`. No bio2, no MuJoCo, no git operations.

Seeds used:
- Registered objects re-created exactly: SWS 8410001 to 8410005, noise 8411001 to 8411003.
- New simulations (red-team pool only): shuffle instance seeds 8495001 to 8495031 and ALIF noise seeds 8495901 to 8495904.
- No forbidden seed was used.

**Verdict for this scope: PASS.** I found no software artifact. The DATA vs SWS difference survives the checks below:
- a code-path audit;
- bit-exact independent re-simulation, including my own re-implementation of the ALIF equations;
- an exact negative control (0 swaps gives Delta = 0);
- a monotonic shuffle dose-response.

The limitations in section 5 concern interpretation, not bugs.

---

## 1. Code-path audit (v5v41.py, alif.py, side_shuffle.py, analysis)

DATA and SWS go through the same path. Each item below was checked.

| Item | Where | Finding |
|---|---|---|
| Network base | `v5v41.py:59` | Both families start from the same `network(J0)` (J0 = 0.2). SWS is `shuffle_within_side(spec, gr, k)` of that same spec (`:67`). |
| Index sets (`idx`) | `v5v41.py:59-61` | `idx` (in_L/R, mid_L/R, DNa02_L/R) is built once from DATA groups and reused for SWS. This is correct, not an asymmetry: the shuffle keeps `bodies` and their order (`side_shuffle.py:85`), so the indices refer to the same neurons. The swap also keeps each neuron's layer×side group. |
| ALIF parameters | `v5v41.py:134-135, 141` | `P` is built per job from the same `ALIFParams(noise=2.0)` plus the job's `alif` overrides. The main run has no overrides (config.json `alif`). E1n0 sets noise to 0 the same way for every network. |
| Noise and init seeds | `v5v41.py:142` | `NOISE_SEEDS[r]` / `INITV_SEEDS[r]` are identical for every network: common random numbers. N = 424 for every network, so the noise draws are identical. |
| Schedules | `v5v41.py:136` | `schedules(job["smoke"])` is the same for every job. |
| Weight matrix used | `alif.py:54` | The simulation uses `spec.W = W_data + W_model` (`snn_interface.py:52-53`). `W_model` is all zeros in DATA (checked: `W_model.any() == False`). The shuffle refuses a non-zero W_model (`side_shuffle.py:50`) and copies it unchanged (`:85`). |
| dtype | `side_shuffle.py:81` | `np.zeros_like(spec.W_data)`. DATA and all checked SWS matrices are float64. |
| Instance hash check | `v5v41.py:132` vs `:168-181` | It hashes `W_data` only, not `W`. This is harmless because W_model is zero. The check uses the same `network(0.2)` and the same seed as `make_net`, and it would fail loudly on any mismatch. I re-created SWS 8410001 to 8410005 myself and their sha256 equal `instances.json`. |
| Shuffle rule | `side_shuffle.py:58-79` | Keys are (signed weight, group(pre), group(post)). Swaps are double edge swaps. The rule rejects b == d, a == d, c == b and existing target edges. No duplicate (post, pre) edges are possible, so no weight is lost at the `Wd[post, pre] = w` assignment (`:82`). `properties()` passes all 17 keys for all 50 instances, and `complete` is True for all of them. |
| Simulation loop | `v5v41.py:76-125` | Current goes only to LC10a of the driven side (`I[iI]`, `I[iC]`). The same `I` buffer is reused, but only those indices are written. The steady-state count window is the same for all networks. |
| Analysis mapping | `v5v41_analysis.py:33-55` | Column-to-population mapping per side is correct (ipsi/contra swap for side R). Steady window is bins 50 to 99 (500 to 1000 ms). Normalization uses `n_pop` = [135, 140, 58, 89, 1, 1], which is identical for all networks. |
| Range average | `v5v41_analysis.py:119-123` | Trapezoid over a non-uniform grid, applied the same way to DATA and SWS. My unweighted recomputation from the raw npz gives DATA 86.55 Hz and SWS mean 68.87 Hz, SD 0.341 Hz, 50/50 below DATA. The reported values are 86.56, 68.55 and 0.344. The small difference in the mean comes only from the weighting. |

**Bugs found: none** that could create or inflate the difference.

## 2. Independent re-simulation (my own loop, not `v5v41.simulate`)

Setup:
- Networks: `visual_path.network(0.2)`, plus `shuffle_within_side` with seeds 8410001 and 8410002. Their hashes equal `instances.json`.
- Simulation: my own loop calling `alif.ALIF.step`.
- Stimulus: left LC10a driven at 7, 8 and 9 mV, 1000 ms, noise seeds 8411001 to 8411003.
- Comparison: DNa02_L spikes and LC10a_L spikes in the 500 to 999 ms window, against `E1_counts[level, side 0, rep, 50:100, col]`.

**Result: 27/27 runs match exactly, for both DN and LC counts.** Examples (DNa02_L spikes / 0.5 s):

| I (mV) | DATA (seeds 1, 2, 3) | SWS_8410001 | SWS_8410002 |
|---|---|---|---|
| 7 | 21, 24, 28 | 19, 19, 18 | 19, 19, 18 |
| 8 | 34, 46, 40 | 26, 31, 27 | 26, 27, 27 |
| 9 | 65, 59, 68 | 47, 44, 43 | 44, 44, 48 |

I also wrote a second, fully independent numpy implementation of the documented ALIF equations, without using `alif.py` (same RNG consumption order). For DATA, SWS_8410001 and SWS_8410002 at 8 mV, seed 8411001, it gives the same (DN, LC) spike counts as `alif.ALIF`: (34, 801), (26, 904) and (26, 804). So the ALIF integrator does nothing network-specific.

## 3. Positive and negative controls: shuffle dose-response at 8 mV

Setup:
- Instance seeds 8495001 onward: 5 instances per dose, 1 for dose 0.
- Noise seeds 8495901 to 8495904, both sides driven in turn.
- DATA was re-simulated with the same noise seeds: DN ipsi 83.25 Hz, LC ipsi 13.08 Hz.
- Delta DN = SWS − DATA, mean over 2 sides × 4 reps.

| n_swaps_per_edge | swaps done | changed edges (of 13510) | mean Delta DN (Hz) | SD across instances | mean Delta LC (Hz) |
|---|---|---|---|---|---|
| 0 (negative control) | 0 | 0 (W identical to DATA) | **0.00 (exact)** | n/a | 0.000 |
| 0.001 | 14 | 27-28 | +1.55 | 3.09 | +0.15 |
| 0.01 | 136 | 264-269 | −1.20 | 2.43 | −0.09 |
| 0.1 | 1351 | 2321-2382 | −9.15 | 3.69 | +0.28 |
| 0.5 | 6755 | 6851-6991 | −21.65 | 2.46 | −0.21 |
| 1 | 13510 | 8516-8578 | −22.50 | 3.24 | −0.08 |
| 5 (registered) | 67550 | 9032-9094 | −23.30 | 1.05 | −0.19 |

How to read this:
- The response goes to DATA as swaps go to 0, and is bit-identical at 0 swaps.
- The effect grows monotonically and saturates at about 0.5 swaps/edge, where about 7000 edges have changed.
- The saturated value (−23.3 Hz) agrees with the registered per-level Delta at 8 mV (−23.04 Hz, from 50 instances × 8 reps).

This is what a real structural effect looks like, not a pipeline artifact. It also shows the result does not depend on the exact swap count used (5).

## 4. Is the small between-instance SD an artifact of identical networks?

No.
- **SWS vs DATA:** for DATA and SWS 8410001 to 8410005, every pair differs in 20822 to 20919 matrix entries, with edge Jaccard about 0.195-0.198.
- **SWS vs SWS:** every SWS pair differs in 20852 to 21086 entries, with Jaccard about 0.19-0.20.
- **Instance file:** `instances.json` reports distinct_W = True, any_equal_data = False, and pairwise changed-edge Jaccard 0.126 to 0.142.
- **Stored results:** the 50 stored per-instance 6-10 mV means take 49 distinct values (one tie). They span 68.31 to 69.71 Hz.

The 0.34 Hz SD is small for two legitimate reasons:
- **Averaging.** It is an average over about 33 levels × 2 sides × 8 reps. At a single level, sd_between is 0.66, 1.63 and 2.15 Hz at 7, 8 and 9 mV (analysis.json).
- **Common random numbers.** Every network sees identical noise (`v5v41.py:142`), so sd_between contains only network-to-network variation, not independent noise sampling.

Even my 4-rep, single-level estimate (SD 1.05 Hz at dose 5) is far smaller than |Delta| ≈ 23 Hz.

## 5. Limitations (not bugs)

1. **Common random numbers** (`v5v41.py:142`). DATA and every SWS instance share noise realizations.
   - "sd_between" is a network-only spread. It should not be read as the spread one would see with independent noise.
   - The hierarchical bootstrap (`v5v41_analysis.py:98-116`) resamples DATA reps and control reps independently, which ignores this pairing. That makes the CI on Delta conservative, not anti-conservative.
2. **Only one DATA network.** The CI on Delta comes from 8 noise reps of DATA (sd_within_data 5.9 Hz at 8 mV, larger than SWS's 3.8 Hz) plus the instance spread. It is not uncertainty over connectome reconstructions or over the choice of ALIF parameters. The labels stay as given: the effect is DATA structure tested under MODEL dynamics.
3. **SWS is a partial randomization.** Even at 5 swaps/edge, only about 67% of edges change. The rest sit in singleton (weight, group, group) keys or end up back in place. The control removes fine wiring within each group, notably LC10a reciprocity (2450 reciprocal pairs in DATA vs 544 in SWS_8410001). It keeps all group-level statistics.
4. **Not covered here:** E6 (the small-signal gain) and the analysis of thresholds and mechanism correlation. I only checked the per-level and range numbers that feed the E1 headline.

## 6. Summary of numbers checked against the claims

| Claim | Check | Status |
|---|---|---|
| E1 DN ipsi 6-10 mV: DATA 86.6, Delta −18.0 (CI −18.8 to −17.2), 50/50 below DATA, SD 0.34 | analysis.json, plus my unweighted recomputation from raw: 86.55 / 68.87 / SD 0.341 / 50/50 | Consistent |
| LC ipsi +0.10 Hz of 13.3; mid ipsi −1.15 | analysis.json; my dose 5: Delta LC −0.19 (4 reps, 8 mV only) | Consistent; Delta LC is near zero |
| I_th10: DATA 5.99, SWS 6.09 | analysis.json | Present (not recomputed) |
| E1n0 Delta −6.9 | analysis.json −6.88 | Present (not recomputed) |
| dDN vs dLC Spearman 0.59 | analysis.json 0.591, CI 0.38 to 0.76 | Present (not recomputed) |
