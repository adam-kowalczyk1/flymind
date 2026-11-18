# F1 Stage 0 (r3.1) code red team

Scope: stimulus.py, systems.py, runner.py, analysis_core.py, analysis.py, manifest.py, tests/test_f1.py against PROTOCOL.md r3.1 §13 and protocol.json.
Method: full read of all files plus the frozen encoder, loop, so101, alif, block_shuffle and side_shuffle code.
Pure-numpy and import-only checks, run with `.venv/bin/python -I -B`. I read only the smoke outputs (9108030–31). I did not touch the pilot directory, run runner.py or run MuJoCo.
Check scripts and synthetic data are in the scratchpad (`chk*.py`, `synth*.py`, `fake*/`). Nothing under the project was written.

**Verdict: PASS_WITH_FIXES.** I found no CRITICAL defect. I found no bug that makes the pilot1 numbers wrong, so no pilot1 unit needs discarding.

The MAJOR items are integrity and verification gaps, plus one analysis-design hole (S6 matching). The analysis code is where fixes are cheapest, because it has not yet been used on real data.

Note on hashes: every file listed in `manifest_pilot.json` currently matches its recorded hash. Any fix to runner.py, analysis.py, analysis_core.py or tests/test_f1.py needs a new manifest before pilot2 starts, because the runner refuses to start on a mismatch. Record both manifests for provenance, since pilot1 was produced under the old hashes.

---------------------------------------------------------------------------------------------------

## MAJOR

**M1. The runner does not enforce the integrity claims of PROTOCOL §10.** (runner.py:157–163, 176–178, 188–194; tests/test_f1.py:167–171; manifest.py:14–16)
- The runner checks only (a) the hash of the manifest file, (b) the hashes of the 10 files in `m["sha256"]`, and (c) the Stage-1 hashes from `loop.stage1_hashes()`.
- `m["deps_sha256"]` covers encoder.py, alif.py, visual_path.py, so101.py, block_shuffle.py, side_shuffle.py, sensory.py and others. It is recorded but never compared. `m["data_sha256"]` is also never compared.
- Stage 1 covers bio2/, assets/ and the frozen manifest list. `integrity_v5v41` protects only bio2/, assets/, data/, validation/, results/v5v3 and v5v4, plus loop.py and loop_v2.py. Neither covers encoder.py, alif.py, visual_path.py, so101.py or the two shuffle modules, which are the actual scientific dependencies of F1.
- Failing scenario: someone touches encoder.py or side_shuffle.py between `manifest.py` and the confirm run. Nothing stops the run and the manifest silently lies.
- §10 says "F1 pre-snapshot unchanged outside this directory". The test comment says "run by the runner wrapper", but no such snapshot or wrapper exists (`grep snapshot` finds only the PROTOCOL text).
- T9 therefore tests only `integrity_v5v41 --compare`, which is the old baseline.
- Fix, in the runner before starting: recompute `deps_sha256` and `data_sha256` from the manifest and `sys.exit` on mismatch. Also assert that `confirm_params.json` is in `m["sha256"]` for confirm and robust, because manifest.py includes it only if it exists at manifest time.
- Fix, in the tests: either implement the F1 pre/post tree snapshot or delete the claim from §10.

**M2. Resumability and provenance (runner.py:139–143, 179–180).** There are three related problems.
- (a) Atomicity. Each unit is written as `.feather` (xb) and then `.npz` (xb), and the skip test looks only for the `.npz`.
  - If the process dies between the two writes, a feather exists without an npz. A restart re-runs the unit, `open(feather,"xb")` raises FileExistsError, and the unit is recorded as an ERROR forever. Meanwhile `analysis.load()` globs the feather and crashes on the missing npz (analysis.py:40,45).
  - If the process dies inside the npz write, a truncated npz exists, the unit is skipped as done, and the analysis later fails with BadZipFile.
  - Fix: write both to temp names, then `os.replace` the npz last. Skip only if both exist, or write the npz first and the feather last and skip on the feather.
- (b) Mixed code versions. A resumed run may use a different manifest than the units already on disk. Nothing in a unit file records the manifest or code hash, and there is no check that existing files came from the same manifest.
  - This is realistic right now: if this review leads to an edit and a re-manifest and pilot1 is resumed, the pilot becomes a mix of code versions that cannot be told apart afterwards.
  - Fix: put `manifest_sha256` into every unit's npz (`arr["manifest_sha256"]`) and into `run_meta`. Have `analysis.load()` assert that a single manifest sha (or an explicit allow-list) is present. At minimum, refuse to resume if the existing `run_meta_*.json` files in `out/` carry a different `manifest_sha256`.
- (c) `draw_stimulus()` (runner.py:71–80) reads `confirm_params.json` whenever it exists, for every stage including pilot1, pilot2 and smoke.
  - Failing scenario: pilot-rules has written confirm_params.json, then a missing pilot unit is re-run (or a smoke run is made). It draws rho and k from the R3-adjusted ranges, so the unit is paired with different stimuli from its 59 siblings.
  - Fix: read `confirm_params.json` only when `stage in ("confirm","robust")`; otherwise use protocol.json ranges.

**M3. Verification gaps: the hash-locked analysis.py has no test, and several §10 tests are weak or trivial.**
- analysis.py (classify, sk_valid, hier_idx, the R1–R4/R2/R3D rules, the F-a…F-h logic, the S6-unmatched path) is untested.
  - The only "analysis self-check" is `analysis_core.py __main__`, which covers criterion, bsc, auc, mi and holm. It does not cover classify, SK, the bootstrap indexing or the rules.
  - I ran analysis.py end-to-end on synthetic confirm, pilot and robust data: 200 units, the full confirm plan, R3 and R3D branches. It runs without error and the logic reads correctly (details below). Unit tests would still make the check reproducible.
- T1 (test_f1.py:43–50) passes trivially. `ST.motion("sin", …, A=0)` returns `np.zeros` through the same code path as `stat`, so the test compares two identical θ arrays and only re-tests determinism (duplicating T10).
  - It does not test that a code path with amplitude 0 equals the pristine camera.
  - Fix: render with `m.cam_quat = q_local0` untouched versus `pose(0.0)`, and sin with A=1e-9 versus stat.
- T8 (163–165) claims "B1 differs from DATA only inside LC10a×LC10a" but asserts only that the rows of `mid` are unchanged.
  - I verified separately that it is in fact true: all B1 diffs are LC10a×LC10a, with 0 diffs in DNa02 or mid rows.
  - Nothing is asserted for SWS (whose diffs touch mid rows by design), for `W_model`, or for the neuron order and idx identity of B1 and SWS relative to DATA.
  - Fix: assert the support of the B1 diff ⊂ in×in. For B1 and SWS, assert W.shape and that the bodies list and idx are identical.
- T9 (167–171): see M1.
- T14 (draws ledger stored per unit and condition) is not tested. The test only prints `n` from `motion()`. Nothing checks that `jit_draws` in the feather and `…|draws` in the npz exist and are correct.
- "currents identical to encoder.currents" and "LIN equals the encoder contrast without c_min" are not tested. I checked both by reading and by comparing; they are equal. `systems.controls()` is what T3 and the P test exercise, but the pipeline uses `analysis.Data._ctrl` (analysis.py:76–86), which is a separate re-implementation. I verified `controls()` and `_ctrl` agree to 1e-9 on random data, but no test pins this.
- No test covers `runner.plan()` (conditions, networks, range-C subset, unit lists), the unit→instance map `(u−first) mod n`, or the unit alignment of `Data.D`.
- Fix: add a small pure-numpy `tests/test_analysis.py`, run before the confirm manifest, covering the following.
  - classify() on synthetic bootstrap vectors, in rule order, including EQUIVALENT before DETECTABLE.
  - sk_valid(), including `increasing=True`.
  - hier_idx() size and pairing.
  - plan() invariants per stage.
  - `pick` versus the analysis `inst` formula.
  - `_ctrl` versus `controls`.
  - Data.D alignment under shuffled unit order.
  - The "S6 not tested" path.

**M4. Holm family size when S6 is "not tested" (analysis.py:363–367).**
- `AC.holm` is applied to `fam.values()` *before* the unmatched S6 stub is added, so with an unmatched TH_LP the correction is over 5 tests. §8 says "Holm over 6 at 0.05", and R2 sized the family with α/6.
- Failing scenario: TH_LP unmatched; S1–S5 are adjusted with m=5, and S1–S5 p_holm and reject flags are less conservative than the pre-registered rule.
- Fix: include a dummy p=1 for S6 in the Holm call, so the family stays at 6. Alternatively state the rule "Holm over the tests actually run" in the protocol.
- Related: R2 (analysis.py:249,257) always includes S6 in `max(n_required)`. If TH_LP is unmatched, S6 may inflate n for a test that will not be run. Exclude S6 from the max when `th["TH_LP"]["matched"]` is false.

**M5. S6 premise (matched control) is not re-verified on the confirm range after R3D (analysis.py:222–241, 359–367).**
- R4 matches θ_TH and θ_LP on the pilot range D (target = pilot DATA stat BSC). R3D then re-centres range D (:237–241) precisely when the pilot DATA BSC is at an extreme.
- On the new confirm range DATA stat is near 0.5 by construction, but the controls keep thresholds tuned to the old extreme BSC. The two stationary BSCs are then generally not within 0.05, i.e. TH_LP is no longer "MATCHED" in the §4 sense.
- Confirm still runs S6 whenever the *pilot* match flag was true. In my synthetic R3D run, `match_err` and `matched` are reported for the old range only.
- Fix: in `confirm()` compute |BSC_TH_LP,stat − BSC_DATA,stat| on the confirm range D and write it next to the S6 result. If it exceeds `th_match_max`, label S6 "matched on pilot range only" (or "not tested", per the protocol's wording). Alternatively, apply R4 after R3D, which needs a protocol decision.

---------------------------------------------------------------------------------------------------

## MINOR

**m1. SESOI and measurability comparisons are not float-safe (analysis.py:164,166,168,180–181).**
- BSC differences are multiples of 1/(2n). I measured that 25 % of differences that are exactly 0.07 in rational arithmetic evaluate below 0.07 in float: of 173 exact 28-hit differences at n=200, 44 gave d < 0.07, e.g. 0.57 − 0.5 = 0.06999999999999995.
- Consequence: an estimate exactly at the SESOI can be classed DETECTABLE/INCONCLUSIVE instead of SUPPORTED, or HARMFUL can be missed. The same applies to `meas()` at 0.1 and 0.9 and to the 0.05 match tolerance, and to `lo95 > 0` where bs is exactly 0.
- Fix: `full >= SESOI - 1e-9`, `full <= -SESOI + 1e-9`, `-SESOI < lo90 - 1e-9`, and likewise for meas() and the match test.

**m2. R3D uses the full SK validity (edges and monotone) (analysis.py:237–238).** The protocol text for R3D says "fails the SK edge check (§5)". §5 defines validity as edges AND monotonicity, so the code is consistent with §5 but stricter than the R3D wording. Pin the interpretation in the protocol, or use `v["edges"]` for R3D.

**m3. Failure/stop rule not enforced (runner.py:136–138,182–194; analysis.py:331).**
- §10 says more than 1 % of trials excluded means STOP. The runner excludes whole units on any exception (an unaccepted J_vel draw, a render failure) and prints them, but the exit code is 0 and there is no ratio check.
- `analysis.confirm()` analyses whatever units are on disk (`n = len(X.u)`) and does not compare it with `cp["n_units"]`. A missing unit therefore disappears silently; missing trials only raise if a unit is partially present.
- Fix: in the runner, `sys.exit(1)` if `len(errors)/len(jobs) > 0.01`. In `confirm()`/`robust()`, assert `n == cp["n_units"]` (or `PR["robust"]["n"]`) and list the excluded units in the result.
- Also exit non-zero if `post["mismatched"]` (runner.py:194 only prints).

**m4. Exploratory `try/except (KeyError, ValueError): pass` (analysis.py:386–389) hides missing data.**
- A truly missing stream (for example mt on range C) and a bug both vanish. `res["sdt"]` just lacks the key.
- F-h then does `expl[...]`, which raises KeyError, but the rest is silent.
- Fix: whitelist the expected-missing combinations (B1/SWS with mt, and range C for conditions not in `rangeC`) and re-raise otherwise.

**m5. Descriptive neural measures differ slightly from the protocol (analysis.py:273–309; systems.py:118–124).**
- Latencies: the protocol says "correct trials only". `lat_decision_ms` and `lat_dn_ipsi` are averaged over all target trials in which a spike exists. Wrong-side responses are included and not filtered.
- The decision side is `sign(D)`, not the FA-matched criterion; this is identical for the SNN (c=0).
- `fano_D_left` assumes at most one L row per unit (true).
- `data_rank_from_top` (analysis.py:402) compares DATA's full-sample Δ with per-instance Δ computed on about n/10 units, which is not like for like. The column `data_delta_same_units` exists; the rank should use it.

**m6. 0D robustness (analysis.py:419–440; runner.py:66,76).**
- `small_ball` uses the fixed `rho_m = [0.1584, 0.2592]` from protocol.json (original range × 0.72) and ignores R3D. If R3D re-centres range D, the small-ball range no longer equals "range D × 0.72". Scale from `range_D_rho` in confirm_params.
- `robust()` uses 2000 resamples, not the 10 000 of §8. The F-g determination is CI95 > 0 per variant. The B1 and SWS terms use a plain, not a hierarchical, bootstrap. `classify` is called without SK (default True).
- All of these are marked exploratory, but F-g feeds the Stage-1 recommendation. Use `PR["n_boot"]` and `sk_valid`.

**m7. Seeds and registry hygiene.**
- Bootstrap seeds are `9107001 + crc32(name) % 1000` (analysis.py:345). That range covers 9107001–9108000 and so can coincide with registry rows 9107002 (pilot) and 9107003 (robust). Statistically harmless, and not a reproducibility problem, but the registry says "9 107 001 = confirm bootstrap RNG".
- The neural-table seed is +7. State both derivations in SEED_REGISTRY.md.
- For a different test name with the same crc%1000 the bootstrap stream is identical. Probability about 1e-3 per pair, no effect on validity.

**m8. Manifest and environment (manifest.py:33–39; systems.py/ALIF).**
- `env_info` lists numpy, mujoco, pandas and pyarrow, but not scipy. scipy is used by `uniform_filter` (encoder and LIN) and by `norm.ppf` (R2).
- BLAS thread variables are None, and 9 spawned workers do `W @ spikes` matvecs.
- I confirmed that D and the spike counts for one random-drive trial are identical with `VECLIB_MAXIMUM_THREADS=1` and with the default, so this is a hygiene issue only. Pin `OMP_NUM_THREADS=VECLIB_MAXIMUM_THREADS=1` in the run recipe anyway, since T10 runs in one process only.

**m9. Dead and stale code in hash-locked files.**
- `analysis_core.summarize` (:69–76) uses `sesoi=0.05` and a "TRIVIAL" class that is not in §8. `boot` (:61) and `unit_bsc` (:27) are unused.
- `systems.controls` (:67–72) duplicates `analysis._ctrl`.
- A future edit could call the wrong classifier. Delete `summarize`, `boot` and `unit_bsc`, or make `analysis.py` import and use them.
- `protocol.json` keys `window_frames`, `time_s` and `frame_ms` are never used, because the code hard-codes W0=100, T=300 and 10 ms. A consistency assert is cheap.

**m10. Protocol §3 recording list is only partly stored (runner.py:125–126).** θ̇, θ̈ and camera position are not saved; only θ, bearing, cam_R and ball are, and only for the D-left stimulus. θ̇ and θ̈ are derivable from θ. The camera position is checked only in T6 for a single trajectory (< 1e-12). Store `rec["cam_pos"]` once per unit, or relax the sentence.

**m11. Doc/claim precision.**
- §4/§5 say "P and TH silent without target → c = 0". In smoke unit 9108030 the no-target g reaches 2.6e-3 (not 0), so P(no target) is tiny but non-zero. The criterion c for P is therefore small and positive. This is handled correctly by the generic criterion, but the "vacuous matching" wording and the T4 text "no-target drive 0" are only approximately true. TH and TH_LP are exactly 0 at σ 10 (θ ≥ 4 mV ≫ 0.03 mV); `th_curve` asserts it.
- SUPPORTED and HARMFUL are not gated by measurability or SK validity (analysis.py:164–167). This follows the rule order in §8, so it is not a bug, but an H1 SUPPORTED with an arm at BSC 0.95 reports a "threshold shift" only if SK-valid. The code does that correctly.

---------------------------------------------------------------------------------------------------

## Verified OK (no finding)

**stimulus.py**
- Camera yaw: `local = q_b⁻¹ ⊗ q_z(θ) ⊗ q_b ⊗ q_local0`.
  - I checked this against scipy rotations with random q_b and q_local0: |R_world − Rz(θ)·R_b·R_local| < 4e-16, and the quaternion norm is 1.
  - θ > 0 rotates the forward vector counter-clockwise from above (left).
  - Bearing = az0 − θ: recorded bearing error 4e-16 in the smoke data (it comes from `fk`, which uses the same modified model cam_quat).
  - The MT ball sits on the horizontal circle of radius rho around the eye with z = r, at ψ0 + (az0 − θ). It is restored to the az0 position afterwards.
- Cache key `(mode, round(θ,12))`.
  - The cache is cleared in every `set_target`, and the scene is stateless w.r.t. θ history (`mj_forward` recomputes everything). The ball position is constant per target in "camera" mode and is part of the θ-dependent state in "mt" (separate mode key).
  - `imgs[k] = img` copies, so there is no aliasing. J_shuf θ values are exact permutations of the sin values, so the keys coincide.
  - Two different images cannot share a key except for θ within 1e-12 rad. No cross-target leak.
- motion():
  - sin: whole cycles in the window for f ∈ {0.5,1,2,4}; I verified the window mean is below 1e-12 and RMS is exactly A/√2 for random phases.
  - jshuf: permutes `s[:100]` and `s[100:]` independently, window RMS exact, mean 0.
  - jrms: whole-trace scaling by the window RMS, exact (1.0000, 1e-18 mean).
  - jvel: σ_t = 1/(2√2πf)/10 ms gives V_rms = A/2σ_t = 2πfA/√2, as intended. Kernel `valid` length is T, acceptance ±20 % as written. Over 200 draws per cell the mean draws are 3.1/1.9/1.4/1.1 (max 14), well below the 1000 limit; median peak/A is 1.2–1.8, matching §8.

**systems.py**
- Pixel noise: `rint(randn·σ)` as int16 added to int16 image then clipped equals `clip(rint(img + n))`; 0 mismatches over 3.5e7 samples.
- Encoder: stateless and shared. LIN reproduces the encoder blur, contrast, column sum and `S_L − S_R` without c_min or saturation.
- Currents: `I[:, in_L] = 12·g_L` held 10 ms, equal to `encoder.currents`.
- ALIF: fresh per trial, seed = unit, noise drawn unconditionally (N = 424, CRN tested). Steps 1000–2999 ↔ frames 100–299. D = DNa02_L − DNa02_R. DNa02_L and DNa02_R are single neurons (idx sizes 1), so D is a small integer and D=0 is common; this is by design.
- `paircorr` is consistent with V6m `paircorr5`. The Fourier phase reference is the θ at ms resolution over the same window origin; verified a synthetic −0.5 rad lag is recovered exactly.
- `Networks.pick`: `(u − first) mod n` is identical to the analysis `inst = (u − units_first) % 10`.
- B1 differs from DATA only inside LC10a×LC10a; W_model is empty.
- `ema`/`lowpass_drive` equal exact 1-ms filtering sampled at frame ends: 3.6e-15 max error.
- `thresh_D`: correct for scalar, [K] and batched [N,T,2] inputs (loop-compared); the P filter is a = exp(−0.1) as in loop.py.

**runner.py**
- Per-unit streams `[u,1]` noise, `[u,2]` stimulus (order rho, |az|, k, φ), `[u,3,crc32(name)]` jitter. A single noise array is shared by all trials of a unit.
- Every condition has an N trial.
- `plan()` matches §7 and §13 for pilot1, pilot2, confirm (DATA 21 conditions, B1 and SWS 5, range C for 6) and robust (stat, sin*, J_shuf; range D only), including the 153 rows per pilot unit I see in smoke. Instances come from `PROTO`, and B1 and SWS seed pools match the SEED_REGISTRY.
- Outputs are written with "x" or "xb" only, under `results/<stage>`. The runtime render-determinism check is correct. There is no Python `hash()` anywhere.

**analysis.py and analysis_core.py**
- `criterion`: smallest c ≥ 0 with P(|D| > c) ≤ 0.05, checked at n = 60/137/200/400.
- BSC counts "none" as wrong, and the criterion is re-estimated in each resample (the `Nn[idx]` argument).
- `hier_idx` draws instances with replacement, then units with replacement within each drawn instance; the same `idx` is applied to the DATA and control terms. The pairing by unit id via `reindex(self.u)` is correct.
- `classify` order is SUPPORTED, HARMFUL, EQUIVALENT, DETECTABLE-BELOW-SESOI, UNMEASURABLE, INCONCLUSIVE.
- The p rule is min(1, 2·min(P(≤0), P(≥0))) with floor 1/n_boot, and p = 1 for a point mass at 0.
- `sk_valid` edge (15 %), 7 bins and monotone tolerance 0.15; `increasing=True` reflects k correctly.
  - Simulated psychometric curves (slope 0.08–0.2, n = 200/400) pass the check with ≥ 96.5 %, so the check is not noise-fragile.
- R1 tie rule (larger A, then lower f); R2 formula `ceil(1.2·((z_{1−α/2}+z_pw)·SD/0.07)²)` and the achieved-power expression; R3 centre `kb − b(kb−ka)`; R3D centre; R4 argmin, first minimum on ties. `thresh_D` batched with the 401-point grid is correct.
- Pilot data cannot leak into the confirm estimates: stages are separate directories, the unit pools are disjoint, and `ranges()` ignores confirm_params for the pilot.
- F-a…F-h follow §9, including the S6-not-tested stub (`"negative" in fam["S6"]` guards F-c).
- The determinism items hold: the neural-table RNG is consumed in a fixed order, and there is no `hash()` or set iteration that affects values.
- Synthetic end-to-end runs (200-unit confirm with the full plan, 60-unit pilot with R3D, and 40-unit × 4-variant robust) executed without error.

## Not verified (could not, within the constraints)
- T1–T7, T10 and the A1 cache test were not re-run. They need MuJoCo and the GPU, so I rely on the authors' pass record, which this review has not seen as an artifact.
- Quality of the pilot data itself was not inspected.
