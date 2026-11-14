# Recon A: does the frozen V5 v4 code implement the frozen protocol?

Date: 2026-10-30. Scope: read-only review plus recomputation from saved artifacts. No MuJoCo, no runner in run mode, and no network built from any seed pool.
Helper scripts (scratchpad, not in the repo):
`/private/tmp/claude-501/-Users-admin-so101-fly-project/075990a2-3231-4039-8d41-31f3fdcb9204/scratchpad/recon/a_sha.py` (hashes),
`.../recon/a_enc.py` (pure image encoding of the calibration stimuli),
`.../recon/a_recompute.py` (scenes, ties and a full re-run of `v5v4.analyze` on the raw JSONL).
Labels: DATA, MODEL, ENGINEERING, CONTROL.

## 0. Verdict

The code implements the protocol as written. Every condition, seed offset, stratum, statistic, exclusion rule and STOP rule I checked matches. Re-running `v5v4.analyze()` on `results/v5v4/raw_v5v4_{A,B}.jsonl` reproduces `results/v5v4/analysis_frozen.json` with no difference at rtol 1e-12, `validity` excepted.

The main problem is a premise in the protocol. The code does not deviate from it. The decoder calibration (CONTROL) runs at near-saturated encoder drive, and 64% of the slope-fit weight comes from |az| = 30°. The protocol (`validation/v5v4_protocol.md:37`) says the calibration "equalizes small-signal gain". That is not what the code does. The closed-loop metric window (2.5–3.0 s, bearing near 0°) sits in a regime the calibration never samples.

Both H1 "effect ≥ SESOI" categories also rest on point estimates within 0.02° of the 0.5° boundary.

## 1. Integrity (sha256)

| Check | Result |
|---|---|
| `validation/v5v4_frozen_code/*`: 18 files, the same set as `v5v4_manifest.json` `code_sha256` | equal sets |
| current `flymind/<f>` == manifest, for all 18 | True for all 18 |
| frozen copy == manifest, for all 18 | True for all 18 |
| `validation/v5v4_protocol.md` == `protocol_sha256` (f648c7ea…) | True |
| seed registry, Red Team r1/r2/r3 sha256 | True for all |
| `run_meta_A/B`: `VALID`, stage1 pre/post mismatches, `code_mismatch_post` | True, [], [], [] for both |
| Import closure of the runner: every flymind module it imports is in the manifest | yes (alif, connectome, decoder, encoder, latency, loop, loop_v2, safety, sensory, side_shuffle, snn_interface, so101, v4_open_loop, v5v2_topology, visual_path) |

Gap (MINOR, DATA integrity): the MaleCNS feather files are not sha256-pinned anywhere in the V5 v4 chain. The bio2 Stage 1 manifest `deps_sha256` (24 files) contains no `malecns` or feather entry. `v5v4_manifest.json` `data_files_stat` stores `[size, atime, mtime]`, and nothing enforces it (no reference in `v5v4.py` or `loop.py`). Today the size and mtime still match. The atime differs, which is expected after reads.

## 2. Item-by-item

| # | Item | Protocol | Code | Status |
|---|---|---|---|---|
| 1 | 6 conditions | §4 table, `protocol.md:52-59` | `CONDS` `v5v4.py:30`; plan `v5v4.py:269-271` | MATCH |
| 2 | DATA = `network(0.2)` with the DATA decoder | `:54` | `v5v4.py:246,269`; `loop.J0 = 0.2` `loop.py:51` | MATCH |
| 3 | SWS = `shuffle_within_side(spec, layer_side_labels, seed+400000)`, 17-property assertion and swap target | `:55` | `v5v4.py:247,260-263`; `KEYS` holds 17 names (`side_shuffle.py:138-140`); target 5·E, `complete` (`side_shuffle.py:69,83`) | MATCH |
| 4 | Each trial's SWS is a distinct instance | `:55`, `:69` | rebuilt inside the per-seed loop, `v5v4.py:260`, seed `s+400000` (404001–404450, distinct per trial); deterministic `default_rng(seed)` (`side_shuffle.py:66`). Not stored: no SWS seed or W hash in the record (`v5v4.py:272-274`). Proxy: `sws_changed_frac` takes 121 distinct values across 450 records (rounded to 4 dp, range 0.6603–0.6776). `sws_li_rel` = 1.0 for all, as designed | MATCH by code. Bitwise distinctness was not re-verified, because that would mean building networks from a consumed pool |
| 5 | STR_OWN / STR_SHARED: the same SHUF_STR instance, `shuffle(equal_weight=True)`, seed+200000, assertions, 10·E swaps | `:56-57` | `v5v4.py:264-268`; `check_shuffle(..., True)` `v5v2_topology.py:78-91`. `str_li_rel` takes 450 distinct values (0.092–0.341) | MATCH |
| 6 | TOY = `loop_v2.toy_relay`, own decoder | `:58` | `v5v4.py:249-250`, `loop_v2.py:61-85`; slope 306.08 | MATCH |
| 7 | P on gL − gR | `:59` | `loop.py:133-137`; `slope_p = calibrate_p((96,128))` `v5v4.py:253`; recomputed slope_p = 1.4931 g/rad | MATCH |
| 8 | Scenes: az0 ~ U(−30, 30), ρ ~ U within the stratum; 4001–4150 → S1, 4151–4450 → S2 | `:60` | `trial_spec_v4` `v5v4.py:43-47`. Recomputed for all 450 records: 0 mismatches. S1 ρ ∈ [0.1614, 0.2193], S2 ρ ∈ [0.2207, 0.2798]; az ∈ [−29.8, 30.0] | MATCH |
| 9 | Identical scene and ALIF seed across conditions | `:61` | the same `trs` and `s` go to every `run_trial` (`v5v4.py:281`); `ALIF(spec, P, seed)` `loop.py:109` | MATCH |
| 10 | Q_POSE, 3 s, 10 ms tick | `:61` | `loop.py:49,54` (300 × 0.01 s; SNN 10 × 1 ms) | MATCH |
| 11 | Calibration: spot_clip at −30…30° in 10° steps, plus a blank image, ALIF seeds 5001–5003, MNK slope through the blank offset, refused if slope ≤ 2 | `:62-64` | `v5v4.py:50-60` → `V4.static_diff` (`v4_open_loop.py:126-132`: a fresh network per image, 500 ms, mean of the L−R rate over 250–500 ms); blur 3 (`VERSION[2]`, `v4_open_loop.py:69`, set at `v5v4.py:53`); `MIN_SLOPE` 2.0 | MATCH. See §3 for what it actually equalizes |
| 12 | Offset = blank L−P | `:63` | computed (`v5v4.py:58`) but never used: `SteerDecoder(..., [0.0], [slope])` hard-codes 0 (`loop.py:111`). DATA and TOY offsets are 0.0 (run_meta). STR_OWN offsets are not recorded (`v5v4.py:276`) | MINOR deviation, unverifiable for 450 STR_OWN instances. Probably harmless: the blank gives g = 0 and the network is silent apart from noise |
| 13 | Calibrated once per network, before its trials | `:65` | DATA and TOY once per shard; both shards give 492.1187 and 306.0800. STR_OWN per trial (`v5v4.py:268`) | MATCH |
| 14 | Decoder: DATA for DATA, SWS, STR_SHARED; own for STR_OWN and TOY | `:65` | `v5v4.py:269-271`. Records: one slope value (492.1187) for DATA, SWS and STR_SHARED; STR_OWN has 450 distinct slopes in 18.4–202.9 (6 below 50) | MATCH |
| 15 | Sign convention: + = left; d = first − second, d < 0 ⇔ first better | `:25` | encoder +az → gL > gR (verified on spot(+20)); `bearing` + = left (`loop.py:71-77`); `dd = E(DATA) − E(SWS)` `v5v4.py:153`; H2a = DATA − STR_OWN, H2b = STR_SHARED − STR_OWN `v5v4.py:167` | MATCH. Closed-loop sign is empirically consistent: P succeeds 450/450 |
| 16 | Main metric: mean \|e\| over 2.5–3.0 s, e from simulator truth | `:82` | `metrics`: `abs(e[-50:]).mean()` (`loop.py:172`). e is sampled at the start of each tick (`loop.py:118`), so the window is ticks 250–299 = t 2.50–2.99 s. `e_deg` is rounded to 0.001° before the metric (`loop.py:159`) | MATCH (cosmetic: the post-last-action state is excluded; 0.001° quantization) |
| 17 | Sign-flip permutation test, 100000 draws, seed 9401, two-sided | `:84` | `perm_test` `v5v4.py:70-73` (abs mean, +1 correction; p floor 1e-5) | MATCH |
| 18 | Paired percentile bootstrap, 10000 draws, seed 9402, 95% and 90%, plus t CI95 | `:83` | `boot_ci`, `t_ci` `v5v4.py:76-86` | MATCH |
| 19 | TOST ±0.5 at α 0.025 per stratum ⇔ both CI95 inside (−0.5, 0.5) | `:28-29` | `h1_category` `v5v4.py:110` (1 − 2·0.025 = 95%, so this is correct) | MATCH |
| 20 | Superiority: Holm over {S1, S2}, p_Holm < 0.05 and the bootstrap CI95 excludes 0 | `:27`, `:85` | `holm` `v5v4.py:89-95` (correct step-down, monotone); `v5v4.py:114-117` | MATCH |
| 21 | Size category from the mean d (≥ 0.5) | `:85-87` | `v5v4.py:112-113` | MATCH (but see §4) |
| 22 | H2: Holm over {H2a, H2b}; significant ⇔ p_Holm < 0.05 and CI95 excludes 0 | `:31-32` | `v5v4.py:167-170` | MATCH |
| 23 | Descriptive: pooled, S2a/S2b, OLS d ~ ρ + \|az0\| with classical SE, Wilcoxon (Pratt), d_z, zeros, \|d\| > 1 | `:30`, `:84`, `:115` | `v5v4.py:98-104,158-165` | MATCH |
| 24 | Exclusions: an error excludes the seed from all error comparisons and counts as failure for success; two-sided sensitivity | `:91-92` | `v5v4.py:135-137,143,181,189-197` | MATCH. Not exercised: 0 errors |
| 25 | STR_OWN refusal: error = \|az0\|, failure; > 10% → H2 uninterpretable; DATA or TOY refusal → STOP | `:93-94` | `v5v4.py:251-252,277-279,173-178` | MATCH. 0 refusals |
| 26 | Error limits: > 5 per condition or > 2% of the shard, counting resumed records | `:96-97` | `v5v4.py:254,292-293`. "Per condition" is counted per shard; the protocol does not say per shard or overall | MINOR ambiguity, not triggered |
| 27 | Code/protocol vs manifest at start; Stage 1 pre/post; VALID flag | `:95-100` | `v5v4.py:237-242,294-301,321-326,330-331` | MATCH. The analysis reads every `run_meta_*` in the directory of the first file only and does not check that they are exactly {A, B} or compare their `protocol_sha256` (`v5v4.py:322-326`). The procedural rule in `:117-119` mitigates this. Now: 2 metas, both VALID |
| 28 | Seed refusal / forbidden ranges | `:71` | `FORBIDDEN` `v5v4.py:38-39`, `v5v4.py:335` | MATCH |
| 29 | Duplicate or incomplete seed set → STOP | `:97-98` | `v5v4.py:129-134`. Recomputed: 450 unique, exactly 4001–4450, 0 malformed lines | MATCH |
| 30 | Frozen protocol header | — | `protocol.md:1` still reads "SZKIC r3 … do zamrożenia" (draft r3, to be frozen) although it is the frozen, hashed file | COSMETIC |

## 3. Calibration: what does it equalize? (CONTROL vs ENGINEERING). Severity: MAJOR for interpretation

I encoded the exact calibration stimuli through the same encoder path. This is pure image encoding with `V4.V.update(VERSION[2])` and `TargetEncoder(SHAPE, blur 3)`, exactly as in `OpenLoop.__init__` (`v4_open_loop.py:111`) and `v5v4.py:53`.

| az [°] | n_px (after blur) | gL | gR | I_L [mV] | I_R [mV] |
|---|---|---|---|---|---|
| −30 | 310 | 0.210 | 0.989 | 2.52 | 11.87 |
| −20 | 308 | 0.447 | 0.985 | 5.36 | 11.82 |
| −10 | 308 | 0.734 | 0.968 | 8.80 | 11.62 |
| 0 | 308 | 0.908 | 0.908 | 10.90 | 10.90 |
| +10 / +20 / +30 | 308 / 308 / 310 | 0.968 / 0.985 / 0.989 | 0.734 / 0.447 / 0.210 | 11.62 / 11.82 / 11.87 | 8.80 / 5.36 / 2.52 |
| blank | 0 | 0 | 0 | 0 | 0 |

(The raw disc is 256 px. ALIF threshold ≈ v_th − v_rest = 7 mV at gain 1, `alif.py:21-23`.)

- **Encoder saturation (ENGINEERING):** the ipsilateral drive is g ≥ 0.968 for every |az| ≥ 10°. The `1 − exp(−E/e0)` term (`encoder.py:66`) is saturated. The whole L−R calibration signal comes from the contralateral side sweeping from 8.8 mV (suprathreshold) to 2.5 mV (subthreshold) while the ipsilateral side stays pinned near 11.9 mV.
- **Fit weight:** the slope through the blank offset is `Σ(Y−off)·X / ΣX²` (`v5v4.py:59`). The az = 0 points carry 0% of the weight, |az| = 10° 7.1%, |az| = 20° 28.6% and |az| = 30° 64.3%. The slope is a chord dominated by the largest azimuths. It is not a small-signal derivative.
- **Closed-loop operating range (ENGINEERING, from saved static renders, `results/v7_encoder_distance_az_20261029.txt`, `results/v7_encoder_distance_20261029.txt`):** max LC10a drive is 8.1 mV at ρ 0.16 and az 0 (257 px), 5.7–10.0 mV at ρ 0.22, 4.9–9.2 at ρ 0.25 and 4.1–8.4 at ρ 0.28. At az ≈ 0, which is where the bearing sits during the metric window, S2 drive is 4.1–5.7 mV per side: subthreshold. The calibration's az = 0 drive is 10.9 mV per side, stronger than any S1 or S2 scene. The calibration spot is roughly equal to the nearest ball (ρ 0.16) in pixel count, but it has higher chromatic contrast.
- **Time regime (MODEL):** calibration reads 250–500 ms after a fresh network reset (`v4_open_loop.py:127-131`), while closed-loop error is read at 2.5–3.0 s of continuous drive with adaptation τ_a = 300 ms (`alif.py:29`).

**Consequences:**
- (a) The claim at `protocol.md:37` ("Kalibracja wyrównuje wzmocnienie małosygnałowe", i.e. the calibration equalizes small-signal gain) is incorrect. The calibration equalizes a large-signal chord at near-saturated drive.
- (b) H2a ("DATA − STR_OWN after scale equalization", `protocol.md:31`) equalizes scale only in that regime. STR_OWN slopes of 18–203 Hz/rad against DATA's 492 mean that STR_OWN loop gains near az ≈ 0 are not controlled.
- (c) H1 shares one decoder, so this is not a direct DATA-vs-SWS bias. However, the N3 justification (SWS slopes 0.988–1.005 × DATA; `protocol.md:113-114`, `results/v5v4/post_sws_slopes.txt`) is a large-signal statement. The final-error metric reflects near-zero-bearing, threshold and dead-zone behaviour, for which there is no calibration evidence.
- (d) DNa02 rate saturation inside the network cannot be assessed without simulation.

## 4. Statistics: findings that follow from the frozen rule (code faithful)

The recomputation equals `analysis_frozen.json`:
- S1: d̄ = +0.512°, CI95 boot [0.414, 0.612], t [0.411, 0.613], p_Holm 2e-5 → "kontrola lepsza, efekt ≥ SESOI" (control better, effect ≥ SESOI).
- S2: d̄ = −0.518°, CI95 [−0.713, −0.329] → "DATA lepsza, efekt ≥ SESOI" (DATA better, effect ≥ SESOI).

Issues:
- **MODERATE:** both "≥ SESOI" labels depend on point estimates only 0.012° and 0.018° past the 0.5° boundary. Both CI95 contain values below SESOI (0.41 and −0.33). The rule in `protocol.md:85-86` / `v5v4.py:112` is a point-estimate threshold, not an inferential test of |δ| > 0.5°. Report these as "significant, with size relative to SESOI not established inferentially".
- **Sign reversal between strata:** in S1, SWS is better by about +0.5° uniformly across the |az0| bins [0,10), [10,20) and [20,30] (+0.55, +0.50, +0.49; 0 ties). In S2, DATA is better (−0.44, −0.52, −0.59). The protocol does not decide on a pooled H1 (`:88`), and the code respects that.
- **Structural zeros (S2):** 57/300 S2 trials have DATA = SWS exactly. In these, mean error equals mean |az0| (4.338°), so neither network moved. The |az0| values reach 12.9°, and 54 of the 96 S2 trials with |az0| < 10° are ties; S1 has none. The mean over the 243 non-tied S2 trials is −0.640°. This matches the expectation in `protocol.md:44` and does not affect the category.
- Using the same perm-test seed for every test means correlated sign matrices across tests of equal n. This is negligible.

Other results:
- Condition means: P 0.196° (450/450 successes), DATA 2.88°, SWS 3.05°, STR_OWN 4.26°, TOY 4.31°, STR_SHARED 5.66°.
- H2a −1.38° and H2b +1.41°, both significant; H2 is interpretable (0 refusals).
- Errors: 0. Exclusions: 0.

## 5. Discrepancies by severity

| Sev | Finding | Where |
|---|---|---|
| MAJOR (interpretation) | Calibration is at saturated drive and its slope is dominated by \|az\| = 30°, but the protocol calls it small-signal gain equalization. The calibration regime does not overlap the metric regime (S2 drive at az 0 is subthreshold) | `protocol.md:37,62-66`; `v5v4.py:50-60`; `v4_open_loop.py:126-136`; `encoder.py:66` |
| MODERATE | The "≥ SESOI" categories rest on point estimates 0.512 and −0.518; the CIs reach below SESOI | `protocol.md:85-86`; `v5v4.py:112` |
| MINOR | Blank offset computed and discarded (decoder offset hard-coded 0); STR_OWN offsets not logged | `v5v4.py:58,276`; `loop.py:111` |
| MINOR | SWS and STR instance identity is not logged (no seed or hash in records); distinctness is guaranteed only by the code | `v5v4.py:272-274` |
| MINOR | Data feather files not sha-pinned; `data_files_stat` not enforced | `v5v4_manifest.json`; `loop.py:58-63` |
| MINOR | Error limit "per condition" is counted per shard (protocol ambiguous) | `v5v4.py:254,292` |
| MINOR | The analysis VALID check does not require exactly the {A, B} metas or check their protocol sha | `v5v4.py:322-326` |
| COSMETIC | Frozen protocol header still says draft r3 | `protocol.md:1` |

## 6. Open questions

1. Why is SWS uniformly better by about 0.5° in S1 at every |az0|, while DATA is better in S2? A uniform offset that does not depend on azimuth points to near-zero-bearing (residual and dead-zone) dynamics, which the calibration does not probe.
2. Would a calibration at closed-loop-matched drive (ρ-matched contrast, small |az|) change the STR_OWN slopes, and with them H2a?
3. Are the 450 SWS instances bitwise distinct? Checking this needs a rebuild from 404001–404450, which is a consumed pool and is not done here.
4. Were all 450 STR_OWN blank offsets 0? This is unlogged.
