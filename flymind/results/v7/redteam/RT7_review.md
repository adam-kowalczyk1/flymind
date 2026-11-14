# RT-7 — Red-team review of V7 (robustness beyond the V5 v4 box), 2026-10-30

Reviewed: `program_v5v41/V7_PROTOCOL.md` (r1), `results/v7/REPORT.md` (DRAFT), `v61_v7.py`, `v61_v7_analysis.py`, `results/v7/v7.jsonl`,
`results/v7/analysis.json`, `results/v61/drive_index.json`, `results/v6/calibration.json`; for the cross-reading, `results/v61/REPORT.md`,
`results/v61/v61.jsonl`, `results/v6/closedloop.jsonl`.
Method: re-analysis of the existing JSONL/JSON only, no new trials. Scratch: `results/v7/redteam/RT-7/rt7_check.py` (+ `_stdout.txt`) and
`rt7_osc.py` (+ `_stdout.txt`). RNG: **8 498 411** (cluster bootstrap over SWS instances, 10 000 resamples) and **8 498 412** (scene-level
bootstrap, 5 000). `results/v7/redteam/RT7/` (15:33, another instance) was left untouched and was not used.
Python: `.venv/bin/python -I -B`, run from `/Users/admin/so101_fly_project`.

## 1. Integrity and pre-registration — mostly verified
| Check | Result |
|---|---|
| Records | 1440, 0 errors, 1440 unique names, 120 per (block × DATA/SWS/P) |
| Scenes | az0/ρ of every record re-derived from its seed with the `v7_scene` rule (`v61_v7.py:35-40`): 0 mismatches; drive-index rows match block, ρ (0 mismatches) |
| SWS mapping | k = 8 410 001 + (i mod 50) for every block: verified |
| G3 decoder / noise | G3 records carry slope 472.158 = `calibration.json` SG6, alif {"noise": 6.0}; G1/G2/G4 carry D0 496.461, alif {} (`v61_v7.py:102`). **SG6 slope is used** for G3, as the protocol requires |
| Visibility | n_px = 0 in 0/480 initial frames |
| Stage 1 after run | `stage1_post_20261030T153103.json`: 28/28 |
| Hashes | current sha256 of `V7_PROTOCOL.md` = 969139e8… and of `v61_v7_analysis.py` = 956c5cd9…; both match `protocol_sha256_before_run.txt` (written 14:31:46) |
| Order of events | analysis script mtime 14:31:45 → hash 14:31:46 → V7 `stdout.txt` created 15:02:57, first `v7.jsonl` write 15:03:21. **The "corresponding drive regime" rule in the docstring (`v61_v7_analysis.py:5-6`) was fixed before the V7 run: verified** |

Two timing qualifications (they do not change the V7 numbers):
- The docstring rule is **not in the protocol** (`V7_PROTOCOL.md:20-21` says only "corresponding drive regime"). It was added at 14:31:45, after
  the V6.1 run had started (`results/v61/stdout_part1_2workers.txt` created 14:26:55, `v61.jsonl` created 14:27:29, 88 records before the
  restart). File times can show that it predates V7, but not that it was "written before any V6.1 result was opened" (docstring line 2;
  V6.1 REPORT §1). The V6.1 hash file (`results/v61/protocol_sha256_before_run.txt`, 12:15:37) holds only the protocol hash. The analysis
  script was first hashed at 14:31:46, inside the V6.1 run. The rule G4 → S1 sign later failed, so there is no sign that it was tuned to the data.
- `V7_PROTOCOL.md` (mtime 08:53:16) says it was drafted "before any V5 v4.1+ result was inspected". `results/v5v41/E6_stdout.txt` already
  existed at 08:45:07. That is not proof the result was inspected, but the claim cannot be verified from the files. The runner `v61_v7.py` was
  never hashed (mtime 08:53:47, before the run).

## 2. Recomputed numbers — all REPORT §2 numbers reproduce
Means and paired d match `analysis.json` exactly (asserted to 1e-9). Cluster CIs from my independent RNG agree to within ±0.005.

| Cell | n | d(SWS) mean [cluster CI, RNG 8 498 411] | scene-bootstrap CI (8 498 412) | DATA succ / SWS succ | drive med [IQR] mV |
|---|---|---|---|---|---|
| G1 all | 120 | −0.327 [−0.565; −0.100] | [−0.584; −0.082] | 0.15 / 0.15 | 4.79 [4.02; 5.80] |
| G2 ρ<0.22 | 54 | +0.206 [+0.044; +0.381] | [+0.039; +0.390] | 0.87 / 0.85 | **10.73 [10.51; 11.10]** |
| G2 ρ≥0.22 | 66 | −0.334 [−0.665; −0.029] | **[−0.719; +0.028]** | 0.83 / 0.74 | 9.26 [8.80; 9.80] |
| G2 all | 120 | −0.091 [−0.280; +0.095] | [−0.318; +0.129] | 0.85 / 0.79 | 9.95 |
| G3 ρ<0.22 | 65 | +0.060 [−0.040; +0.164] | [−0.046; +0.167] | 0.95 / 0.95 | 9.11 |
| G3 ρ≥0.22 | 55 | +0.081 [−0.007; +0.169] | [−0.017; +0.179] | 1.00 / 1.00 | 6.92 |
| G3 all | 120 | +0.070 [+0.007; +0.136] | **[−0.003; +0.145]** | 0.97 / 0.97 | 8.07 |
| G4 all | 120 | −0.201 [−0.344; −0.059] | [−0.339; −0.060] | **0.17 / 0.09** | **10.77 [10.07; 11.25]** |

DATA − P (+12.03, +1.58, +2.53, +2.10, +1.54, +0.68, +1.14, +1.92), the success/moved figures, the overshoot differences (+0.39 / +0.24 / −0.74),
"91/120 identical" and "DATA moves 24 %" all reproduce. The P range "0.12–0.98°" holds at half-block level; at block level it is 0.24–0.98°.

**Rule logic (`v61_v7_analysis.py:138-140`)**: for sign +1 it tests `ci[0] > 0`, and for sign −1 it tests `−ci[1] > 0`, that is `ci[1] < 0`.
This is correct. My independent implementation gives the same six verdicts (G1 holds, G2n holds, G2f holds, G3n not shown, G3f not shown,
G4 not shown). Each d = err(DATA) − err(ctrl), the same convention as V5 v4 (`:45`).

## 3. Findings on claims
**F1 — The cross-reading "the S1 effect is confined to an intermediate drive band (~6–10 mV), not to near" (REPORT:34-35) is over-reach,
and V7's own data contradict it.**
- At matched initial drive, the sign flips with geometry. G2 near-half has median drive 10.73 mV and d = +0.21 (S1 sign, CI excludes 0).
  G4 has median 10.77 mV and d = −0.20. Restricted to drive in [10, 12) mV: G2-near d = +0.154 (n = 48) vs G4 d = −0.191 (n = 93). Two
  regimes with the same drive index and opposite signs cannot both lie inside or outside one "drive band". The REPORT leaves the half-block
  drive cells blank ("—", lines 19-24), and those are exactly the cells that show this.
- G2 far-half (9.26 mV) gives d = −0.33, while V6.1 cells at about the same drive give positive d (V6 S1 at I_max 12: 8.95 mV, d +0.33;
  V6 S2 at I_max 16: 8.95 mV, d +0.24; drive medians recomputed from `drive_index.json`).
- The band's limits do not fit V6.1 either. Positive (S1-sign) d occurs at 8.95 mV (I12 S1) and 10.44 mV (I14 S1, +0.18). Null or negative d
  occurs at 7.46 mV (I10 S1, −0.32) and 6.71 mV (I12 S2, −0.66). So "~6–10" would be "~9–11" at best, and G4 sits inside that range.
- The nearest V6.1 cell to G4 in drive is I14 S1 (10.44 mV, d +0.18, CI excludes 0), which has the **opposite** sign to G4. The cited
  corroboration "as at I_max 16 in V6.1 (S1 −0.12)" (REPORT:34) is a cell whose CI includes 0 (−0.24; +0.01; V6.1 REPORT table).
- `V7_PROTOCOL.md:3-4`: "Nothing here widens any earlier conclusion; V7 results are reported for their own region only." A conclusion
  about a band, built from V6.1 and V7 together, breaks this rule.
A more cautious reading the data can support: the initial-frame drive index does **not** order the V7 blocks by sign of d. G4 behaves like the
high-I_max V6.1 cells (see F2), which points to drive during the trial or near-field geometry rather than initial drive. That reading is a
hypothesis, not tested here.

**F2 — G4 is an oscillatory, mostly failing regime. "REVERSED" is formally correct but does not mean "stronger drive, otherwise
comparable".**
- Success is DATA 0.17 and SWS 0.09, against P 1.00 (the tolerance is 5° over the last 0.5 s, `loop.py:166-172`). The median SD of e over
  the last 1 s is DATA 2.56° / SWS 3.13° (P 0.002°); the median late max |e| is 5.4° / 5.9°. The SNN loops limit-cycle around the target,
  so final_abs_err, and hence d, measures a difference in oscillation amplitude.
- This matches V6.1 I14/I16 S1 (e_sd 2.5–3.0°, success 0.50–0.78), not V6 D0 S1 (success 0.95). G4 is more extreme than either.
- P's own error is 0.98° in G4, against 0.24–0.52° in G1–G3. That points to a near-field sensing or geometry effect that has nothing to do
  with the network. So ρ < 0.16 is not just "more drive". G4 also has no V5 v4 counterpart in drive: V6 S1 at I12 has IQR 8.17–9.51 mV,
  against G4's 10.07–11.25 mV. The S1-sign expectation for G4 was therefore an extrapolation.
- REPORT §4 notes "G1/G4 success rates low". §3, however, calls only G1 a failing loop (line 32) and reads G4 as a clean drive effect (line 34).
  The same caveat must apply to both.

**F3 — G1: "loop largely fails" is supported, but the stated mechanism is not.** DATA error is 12.56° vs P 0.52°, success 0.15, and DATA
moves in 29/120 scenes (supported). But "d reflects which network starts moving at all — DATA's lower threshold" (REPORT:33) is contradicted:
DATA-only movers number **2**, SWS-only movers 0, both-moved 27 and neither 91. Of the summed d (−39.2°), −33.6° (86 %) comes from the
27 pairs where both networks moved (mean d −1.25°), and only −5.6° from the 2 DATA-only scenes. The G1 difference is "given movement, DATA
corrects more", not "DATA moves more often".

**F4 — G2 "reproduced in both halves" is fragile.** (a) The far-half CI fails to exclude 0 under a scene-level bootstrap ([−0.719; +0.028]).
(b) The result depends on the split point. At ρ 0.20 or 0.21 neither half excludes 0 (near +0.08 [−0.15; +0.33], +0.14 [−0.04; +0.35];
far −0.17 [−0.43; +0.09], −0.23 [−0.50; +0.03]); at 0.23 or 0.24 both do. The 0.22 split is pre-specified (the V5 v4 boundary), so the
verdict stands, but "reproduced" should carry this caveat. (c) The six sign tests have no multiplicity adjustment. (d) The protocol speaks of
a "drive regime", yet the rule splits by ρ. A drive-based split at the midpoint of the V6 S1/S2 medians (7.83 mV at I12) places 119/120
G2 scenes in the S1 regime, where d = −0.08 [−0.27; +0.10]: "not shown". So the G2 verdict depends on using ρ as a stand-in for drive,
which is the very link V6.1 says is not causal.

**F5 — G3.** The decoder is correct (SG6, verified). Both halves are "not shown", agreed. "Overall +0.07° (CI just excludes 0)" holds only for
the cluster bootstrap; the scene bootstrap gives [−0.003; +0.145]. Report it as "≈ 0, CI touches 0 depending on resampling unit". The claim
"consistent with V6: σ 6 removes the open-loop difference" is a cross-reference I did not re-verify here. G3 drive (9.11 / 6.92 mV) matches
V6 S1/S2 at I12 (8.95 / 6.71), so G3 is in effect the V6 scene set with noise. That makes it the cleanest block in V7, and it shows no
S1/S2 pattern.

**F6 — Reporting gaps.** The half-block rows give only the mean, not the median, of DATA error (the header says "mean / median"). Half-block
drive medians are missing (see F1). There is no oscillation or e_sd metric, which is needed to read G4 (and also G2: DATA e_sd 1.51 vs SWS 0.95).
The DATA − P CIs in half rows are omitted; they all exclude 0, e.g. G2 near [+1.48; +1.68].

## 4. What stands
The data and analysis are sound. Integrity is clean, the decoder and noise settings are correct, the rule was operationalised before the run and
coded with the right sign handling, and every table number reproduces. Supported conclusions:
- P beats DATA in every block and half.
- G1 is a failing loop.
- G3 shows no DATA/SWS difference.
- G2 shows the V5 v4 sign pattern under the pre-specified ρ split (fragile).
- G4 shows DATA < SWS error in an oscillatory regime.
Not supported: the drive-band synthesis (F1), the G1 threshold mechanism (F3), and the reading of G4 as a clean "strong drive" test (F2).

## Verdict: **NOT_READY**
The interpretation in §3 needs rework. Once corrections 1–5 are made, V7 is PASS_WITH_LIMITATIONS as an exploratory, own-region report.

## Required corrections
1. Remove or rewrite REPORT:34-35, "S1 'SWS better' effect is confined to an intermediate drive band (~6–10 mV), not to 'near'". Replace it
   with the counter-evidence: G2-near (10.73 mV, +0.21) vs G4 (10.77 mV, −0.20); the nearest V6.1 drive cell I14 S1 (10.44 mV) has +0.18; and
   the I16 S1 cell cited is CI-includes-0. State that the initial-frame drive index does not explain the sign across V7 blocks, and that any
   cross-study synthesis belongs in a separate, labelled hypothesis section (`V7_PROTOCOL.md:3-4`).
2. Add the G4 failure and oscillation facts: success 0.17 / 0.09, e_sd_last1s median 2.56 / 3.13°, late |e| max about 5.5°, P error 0.98° (near-field
   effect even for P). Qualify "REVERSED" as "reversed, in an oscillatory regime with no V5 v4 drive counterpart (G4 drive IQR 10.1–11.3 mV
   vs V5 v4 S1 8.2–9.5 mV)". Apply the same failing-regime caveat as for G1.
3. Correct the G1 mechanism (REPORT:33). Only 2 scenes are DATA-only movers; 86 % of d comes from the 27 both-moved pairs (mean d −1.25°). Drop
   "which network starts moving at all / DATA's lower threshold", or recast it as "smaller residual error given movement".
4. G2: report the scene-bootstrap CI for the far half ([−0.72; +0.03]), the split-point sensitivity (0.20 / 0.21 → neither half excludes 0), and
   the fact that a drive-based split gives "not shown". Note that six sign tests are unadjusted. Soften "reproduced in both halves" to
   "reproduced at the pre-specified ρ 0.22 split; fragile".
5. G3: replace "CI just excludes 0" with the resampling-unit dependence (scene bootstrap [−0.003; +0.145]).
6. Fill in the half-block drive medians and DATA error medians in the §2 table, and add a residual-oscillation column (e_sd_last1s).
7. Correct the provenance wording (REPORT §1; V6.1 REPORT §1; `v61_v7_analysis.py:2` as quoted). The analysis script was hashed at
   14:31:46, after the V6.1 run started (14:26:55) and before the V7 run (15:02:57). Say "before the V7 run and before V6.1 completed",
   not "before any V6.1 result". Note that the drive-regime rule lives in the script, not the protocol, and that `v61_v7.py` was not hashed.
8. Use the P range at block level (0.24–0.98°), or label 0.12° as the half-block G2-far value.
