# RT-61 — Red-team review of V6.1 (direct drive manipulation, I_max 8–16) — 2026-10-30

Reviewer: RT-61 (subagent). Scope: `program_v5v41/V61_PROTOCOL.md`, `results/v61/REPORT.md` (DRAFT), `v61_v7.py`, `v61_v7_analysis.py`,
`v61_toy.py`, `cl_runner.py`, `results/v61/{v61.jsonl, analysis.json, drive_index.json, toy/}`, `results/v6/{closedloop.jsonl, calibration.json}`.
Re-analysis of existing files only; no MuJoCo trials; no existing file modified. Scratch: `results/v61/redteam/RT61/`
(`check_integrity.py`, `reanalysis.py` + `reanalysis_stdout.txt`, `extra.py` + `extra_stdout.txt`).
Resampling RNG used (red-team pool 8 498 xxx): **8 498 401** (cell CIs, 10 000 resamples), **8 498 402** (drive-model variants, 5 000),
**8 498 404** (further model variants, 4 000), **8 498 405** (matched-drive band contrasts, 4 000). 8 498 403 was not used.

## 1. Integrity, pairing, execution — PASS

| Check | Result |
|---|---|
| v61.jsonl lines / parse failures / trailing partial line | 1440 / 0 / none (file ends with `\n`) |
| Unique names; expected set {I8,I10,I14,I16} × {DATA,SWS,B1} × seeds 8 600 001–120 | 1440 unique, 0 missing, 0 extra, 0 duplicates |
| Errors | 0 |
| Restart 2 → 8 workers | first 88 records are all I8 (consistent with "restarted at 88 records"); `stdout.txt` "trials to run: 1352" = 1440 − 88; no duplicate, no loss. Interleaving I8/I10 at records ~354–370 is `imap_unordered`, not duplication. Wall time first 88 = 2.5 s/trial (2 workers) vs 7.9 s (8 workers) — contention only. |
| Decoder slope | all 1440 V6.1 records and all 360 V6 D0 records: slope = 496.461155479431 = `calibration.json["D0"]["slope"]` (`v61_v7.py:98`). Verified: D0 for every I_max. |
| Encoder | V6.1 `enc = {"i_max": im}` per config (360 each); V6 D0 `enc = null` → `EncoderParams(blur_px=3)` default `i_max = 12.0` (`encoder.py:30`, `cl_runner.py:32`). ALIF `{}`, J0 0.2, cond `snn` everywhere. |
| Scene / pairing identity vs V6 D0 | for every V6.1 record, (az0_deg, rho, stratum, k) is bit-identical to the V6 D0 record of the same (family, seed): 0 mismatches. Each seed maps to one SWS k (50 clusters) and one B1 k (25 clusters) across all five I_max. ALIF noise seed = scene seed in both runs. |
| drive_index.json | 120 V6 scene rows, scenes identical to the trial scenes, 0 scenes with n_px = 0. |
| Protocol sha | `V61_PROTOCOL.md` sha256 = b74a011a… = `protocol_sha256_before_run.txt`. |
| Analysis sha | `v61_v7_analysis.py` sha256 = 956c5cd9… as stated. |

Recomputed cell statistics (RNG 8 498 401) reproduce `analysis.json` / REPORT §2 table to Monte-Carlo precision (largest CI-bound
difference 0.013°, e.g. SWS I10 S1 upper +0.066 vs +0.053; no CI changes its relation to 0). All table entries (means, moved
fractions, zero pairs) in `REPORT.md:19–23` are correct.

Not verifiable from files: (a) that the I12 (V6 D0) trials would be bit-identical if re-run through the V6.1 job path (expected by
code reading; not re-run per instructions); (b) the "DATA 50/83/161" and "DATA 32 → 47" open-loop reference numbers in `REPORT.md:27–28`
(from V5 v4.1, outside scope).

## 2. Pre-registration timing — LIMITATION
- `REPORT.md:14` says the analysis script was "written and hashed 956c5cd9… before any V6.1 result was opened". The only hash record is
  self-written: `results/v7/protocol_sha256_before_run.txt` timestamp `2026-10-30T14:31:46`; file mtime 14:31:45. At that moment
  `drive_index.json` (14:27:18), the toy output (14:29) and ~88 I8 trial records already existed (run started 14:27). The script also
  contains `toy()` (`v61_v7_analysis.py:66–74`), written after the toy outputs existed. Nothing indicates peeking, but "before any
  V6.1 result existed" is false and "before any was opened" is unverifiable. State this precisely.
- `SEED_REGISTRY.md` registers a V6.1 scene pool 8 610 001–999 that was never used (V6.1 re-uses V6 scenes, as the protocol says).
  Note it as unused.

## 3. The drive-index model does not support "ρ adds nothing" — MAJOR

Pre-specified model (`V61_PROTOCOL.md:26–28`, `v61_v7_analysis.py:93–116`): d ~ drive + ρ pooled over I_max, drive = max(g_L, g_R)·I_max.
Replicated exactly (SWS drive +0.066 [+0.030; +0.105], ρ +0.08 [−3.4; +3.7]). Problems:

1. **The drive coefficient is the manipulated factor, not scene drive.** Adding I_max dummies (SWS): drive −0.148 [−0.209; −0.088],
   ρ −7.1 [−10.8; −3.3]; I_max dummies +0.53…+1.35. With dummies + S2 indicator: drive −0.087 [−0.144; −0.033]. Within every I_max
   cell the scene-level drive slope is ≤ 0 (SWS: I8 −0.63, I10 −0.58, I12 −0.08, I14 −0.08, I16 −0.04). The pooled +0.066 °/mV is entirely
   the between-I_max effect; the drive index adds nothing beyond I_max and has the opposite sign within I_max.
2. **Within a stratum the drive index is mostly azimuth.** r(drive, |az0|) = +0.81 (S1), +0.86 (S2); r(drive, ρ) = −0.43 / −0.41.
   max(g_L, g_R) is large when the target is lateral (one "eye" gets most pixels). "Conditional on drive" within cells is largely
   "conditional on azimuth"; with dummies + g_L+g_R + |az| + ρ, |az| is the only scene term that matters (−0.030 °/° [−0.042; −0.019]),
   ρ −3.0 [−10.9; +5.5] (uninformative).
3. **The pooled ρ null is a cancellation of heterogeneous slopes.** Within-I_max ρ coefficients (SWS, given drive): I8 +1.2 [−7.3; +10.6],
   I10 −21.3 [−34.2; −8.3], **I12 −21.9 [−35.5; −8.0]**, I14 −9.4 [−19.1; −0.3], I16 +2.5 [−1.8; +6.5]. In the V6 D0 configuration itself,
   ρ predicts d given drive.
4. **The null is driven by the failing-loop regime.** Excluding I8: SWS ρ −4.5 [−9.2; −0.2] (excludes 0). Excluding I8 and I10
   (the regime where the loop works): drive +0.018 [−0.025; +0.064] (includes 0), ρ −6.3 [−10.8; −1.9] (excludes 0). I.e. in the
   operating regime the pre-specified model gives the **opposite** reading: drive not detectable, distance detectable. (B1 is weaker:
   excl. I8/I10 drive +0.006 [−0.040; +0.054], ρ −1.3 [−5.3; +2.4] — both null.)
5. Collinearity: pooled r(drive, ρ) = −0.46, VIF 1.27 — not severe; the problem is mis-specification (non-monotone d(drive), regime
   change, scene drive ≈ azimuth), not collinearity. The CI on ρ (±3.5 °/m pooled) also only bounds ρ effects to ~±0.4° across the
   0.12 m range, of the order of the effects being explained.
6. Stratum-at-matched-drive (the most direct test of "not distance"): S1 − S2 d in drive bands, cluster bootstrap (RNG 8 498 405):
   SWS [6, 8) mV −0.18 [−0.81; +0.42]; [8, 11) +0.16 [−0.09; +0.40]; [11, 13) −0.08 [−0.28; +0.11]; B1 all include 0. No detectable
   stratum effect at matched drive — but CI widths 0.4–1.2° and every band mixes I_max levels (i.e. decoder loop gains). With
   I_max dummies + drive + S2 restricted to I_max ≥ 12: SWS S2 −0.30 [−0.63; −0.01] (excludes 0), B1 +0.06 [−0.27; +0.37].
   Specification-dependent; neither "distance matters" nor "distance does not matter" is established.

Conclusion: the statement "ρ adds nothing detectable given drive" (`REPORT.md:36–37`) is the literal pre-specified output, but it is
not robust (flips with the I_max term, with exclusion of I8, and within the D0 configuration) and cannot be used as support for
"not by target distance as such".

## 4. "Sign governed by drive level, not distance" — OVERSTATED

- The two directional predictions (`V61_PROTOCOL.md:19–20`) were met as stated (S1 +0.33 → −0.32 → −1.20; S2 −0.66 → −0.01 → +0.24).
- But I_max at a fixed D0 decoder changes the input level **and** the effective loop gain (ω per unit image error) and the operating
  point relative to the decoder calibration. `REPORT.md:49–50` concedes "drive and decoder mismatch are the same manipulation",
  yet the headline (`REPORT.md:34–35`) attributes the sign to "the LC10a drive level". The data cannot separate drive from loop gain.
- At every fixed I_max the two strata still differ (S1 − S2, SWS): I8 −1.05, I10 +0.39, I12 +1.00, I14 +0.19, I16 −0.35 — at I16 the
  strata again have opposite signs (S1 −0.12, S2 +0.24; B1 S1 −0.25 [−0.38; −0.12], S2 +0.30 [+0.20; +0.40]). Distance therefore
  still determines the sign at fixed gain; what I_max shows is that the distance effect is modulated by gain.
- A monotone drive account is falsified: S1 at I16 has the highest drive (median 11.9 mV) yet is DATA-better (B1 CI excludes 0),
  whereas the account predicts the most SWS-better value. A non-monotone (inverted-U-like) drive-only account is *compatible* with
  the cell medians (e.g. S1@I12 and S2@I16 both median 8.95 mV, d +0.33 / +0.24), but it was not pre-specified and is not tested.
- The S1 low-drive confirmation is low-information: at I8/I10 the loop is failing (DATA err 8.4° S1 / 12.2° S2 at I8) and DATA is
  known from open loop to have the lower threshold; "the network that moves more wins" is expected regardless of any distance effect.

Defensible wording: "With geometry and decoder fixed, changing the encoder gain I_max (input drive and fixed-decoder loop gain together)
changes the sign of d in both strata; d is a non-monotone function of I_max; a drive-only account is compatible with but not
demonstrated by these data, and distance is not shown to be irrelevant."

## 5. Low-drive regime: "which network moves" — PARTLY WRONG

`REPORT.md:39–40`: "there d reflects which network starts moving at all (threshold), with most pairs identical."
Decomposition (SWS; B1 analogous):

| Cell | zero pairs (all = neither moved) | both moved: n, mean d | only DATA moved: n, Σd | only ctrl moved | share of Σd from one-moved pairs |
|---|---|---|---|---|---|
| I8 S1 | 17/40 | 21, −2.05 | 2, −4.9 | 0 | 0.10 |
| I8 S2 | 75/80 | 3, −2.23 | 2, −5.1 | 0 | 0.43 |
| I10 S1 | 2/40 | 38, −0.34 | 0 | 0 | 0 |
| I10 S2 | 48/80 | 28, −1.55 | 4, −13.7 | 0 | 0.24 |

- Only-control-moved = 0 in every cell; DATA moved whenever the control moved.
- I8 S1 is **not** "which starts moving": 90 % of Σd comes from 21 both-moved pairs where DATA removes more initial error (mean
  progress |az0| − err: DATA 6.5° vs SWS 5.3°, of 14.9°). It is "which moves further in an under-actuated loop" (gain/threshold).
- I8 S2 (d −0.15, CI excludes 0) rests on 5 non-zero pairs of 80 (seeds 8 600 064, 070, 102, 108, 118; 2 only-DATA-moved). All 5 are
  negative (exact sign test two-sided p = 0.0625). The "CI excludes 0" there is fragile and should not be reported as an effect.
- Zero pairs: 167 in total (SWS), every one a pair where neither network moved (final err = |az0| within 0.0034°).
- At I8/I10 the error measures progress towards the target, at I12–16 steady-state accuracy/overshoot; d is a different quantity in
  the two regimes, which further argues against pooling them in one linear model (§3).

## 6. B1 "reproduces" the drive dependence — QUALIFY
`REPORT.md:41`. d(SWS) and d(B1) share the DATA trial: r(d_SWS, d_B1) per cell 0.45–0.95 (0.88–0.95 at I8 S2, I10). At low drive
both controls fail identically (r(err_SWS, err_B1) 0.96–1.00), so agreement is partly mechanical. B1 does not reproduce the I12
baseline stratum flip with significance (S1 +0.21 [−0.03; +0.45], S2 −0.21 [−0.53; +0.15]) and is null at I14. "Same signs at 8, 10, 16"
is correct; "reproduced" should be "consistent with".

## 7. Minor
- `REPORT.md:28–29`: "a much weaker … drive response than the network" — at I0 7 mV toy G_small = 38.0 Hz/mV vs DATA 32 (as quoted):
  the toy is *higher* there; weaker only for E1 rates and for I0 ≥ 9 (toy 27.4 / 17.5 / 14.4). Reword.
- `REPORT.md:28`: "0 Hz up to 6 mV" — toy dn_ipsi is 0 up to 6.25 mV, 3.25 Hz at 6.5. Fine, could say "≤ 6.25".
- `REPORT.md:24`: medians are also 0 at B1 I12 S2 and B1 I10 S1 (2 zeros only); list or say "≈ 0".
- Protocol §4 asks for "only-one-moved counts"; they are in `analysis.json` but not in the report — add (table in §5 above).
- SESOI statement (`REPORT.md:45`) correct; add that in the operating regime (I_max ≥ 12) no cell's |d| CI lies beyond 0.5°.
- Drive index is computed once per scene from a separate static render at `L.Q_POSE` (`v61_v7.py:43–54`), not "per trial" as in
  `V61_PROTOCOL.md:25–26`; equivalent if the trial's first frame is identical — state it, it is not checked.
- Cluster bootstrap: within a cell S1 has 40 singleton clusters (k = i for i < 40), so it equals an ordinary scene bootstrap there; fine.

## Verdict: **NOT_READY**
Data, pairing, decoder, scene identity and the 2 → 8 worker restart all check out; every reported number reproduces. No new trials are
needed. But the central interpretive claim ("sign governed by the LC10a drive level, not by target distance as such"; "ρ adds nothing")
does not follow from the evidence and must be rewritten before the report can pass.

## Required corrections
1. Rewrite the headline (`REPORT.md:34–35`) to attribute the sign change to the I_max gain manipulation (input drive and fixed-decoder
   loop gain, not separable), drop "not by target distance as such", and say d is non-monotone in I_max.
2. Replace "ρ adds nothing detectable given drive" (`REPORT.md:36–37`) by the robustness results: with I_max terms the drive-index
   slope is negative and ρ is −7.1 [−10.8; −3.3]; within I12 ρ is −21.9 [−35.5; −8.0]; excl. I8/I10 drive is null and ρ −6.3 [−10.8; −1.9]
   (SWS). State that the pre-specified model is mis-specified (non-monotone d, regime change, scene drive ≈ |az|, r = 0.81–0.86).
3. Report that at every fixed I_max S1 and S2 differ (incl. opposite signs at I16, B1 CIs excluding 0), and that S1@I16 contradicts a
   monotone drive account; present the inverted-U reading only as a post-hoc hypothesis.
4. Correct the low-drive bullet (`REPORT.md:39–40`): I8 S1 is dominated by both-moved pairs (DATA moves further), not by onset; add the
   zero / both-moved / only-one-moved table; flag I8 S2 as resting on 5 non-zero pairs (sign test p = 0.0625) and do not cite its CI as
   an effect; note only-ctrl-moved = 0 everywhere.
5. Qualify the B1 claim (`REPORT.md:41`): shared DATA trial (r(d) up to 0.95), no significant I12 flip, null at I14 → "consistent with".
6. Correct the pre-registration timing statement (`REPORT.md:14`): analysis script hashed 14:31:46, after drive_index, toy outputs
   and ~88 I8 trials existed; the hash record is self-written.
7. Fix the toy-relay comparison wording (`REPORT.md:28–29`): toy small-signal gain exceeds DATA at I0 7 mV.
8. Add to Limitations: drive index is per scene from a separate static render, dominated by azimuth; matched-drive stratum contrasts
   are underpowered (CI widths 0.4–1.2°) and confounded with I_max; the I12 arm is re-used from V6 and was not re-run through the
   V6.1 job path.
9. Note the unused registered V6.1 scene pool (8 610 001–999) in the report or the seed registry.
