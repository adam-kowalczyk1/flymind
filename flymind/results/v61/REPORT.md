# V6.1 — Direct drive manipulation in closed loop: report (2026-10-30)

**Status: exploratory, completed. Verdict: PASS_WITH_LIMITATIONS — after correction** (red team RT61 NOT_READY on the draft: the
headline over-reached; all 9 required corrections applied, §6). MODEL + ENGINEERING manipulation; MuJoCo simulation only (no physical
arm); nothing here is a statement about the fly.

## 1. Design and execution
Protocol `program_v5v41/V61_PROTOCOL.md` (sha b74a011a…, written ~09:00 before any V5 v4.1+ result). The encoder output scale I_max
(mV per unit g; default 12) is set to 8, 10, 14, 16; camera, scenes, encoder saturation, safety layer and ALIF default unchanged; the V6
D0 DATA decoder (calibrated at I_max 12) is NOT recalibrated (verified for every record: slope 496.461). I_max therefore changes BOTH the
input drive and the loop gain of the fixed decoder — the two cannot be separated here. Scenes = V6 set (8 600 001–120; S1 ρ [0.16, 0.22)
n = 40, S2 [0.22, 0.28) n = 80); I_max 12 = the V6 D0 trials (re-used, not re-run through the V6.1 job path; scene/pairing identity with
V6 verified, 0 mismatches). The registered V6.1 scene pool 8 610 001–999 was not used. Networks DATA, SWS ((i−1) mod 50)+1, B1 (i−1)
mod 25. 1440 new trials, 0 errors (restart 2 → 8 workers at 88 records: no duplicates, no loss — RT61). Drive index = max(g_L, g_R) of a
separate static render of the initial frame × I_max (`drive_index.json`). Toy-relay reference (`v61_toy.py`).
Provenance (corrected): `v61_v7_analysis.py` was hashed at 14:31:46 — AFTER the V6.1 run had started (14:26:55) and after
`drive_index.json`, the toy output and ~88 I8 trial records existed; I had viewed 2 raw I8 records (to learn the record format) but no
summary. "Written before any V6.1 result was opened" in the draft was wrong. The hash record is self-written. RNG 8 419 030.

## 2. Results (d = err(DATA) − err(ctrl) [°]; positive = control lower error; CI95 cluster bootstrap over control instances)
| I_max [mV] | scene drive median S1 / S2 [mV] | DATA err S1 / S2 [°] | moved DATA S1 / S2 | SWS S1 | SWS S2 | B1 S1 | B1 S2 | zero pairs S1 / S2 |
|---|---|---|---|---|---|---|---|---|
| 8 | 6.0 / 4.5 | 8.38 / 12.18 | 0.57 / 0.06 | −1.20 (−1.91; −0.54) | −0.15 (−0.31; −0.02)* | −0.97 (−1.75; −0.24) | −0.11 (−0.25; −0.02)* | 17 / 75 |
| 10 | 7.5 / 5.6 | 1.89 / 8.09 | 0.95 / 0.40 | −0.32 (−0.75; +0.05) | −0.71 (−1.03; −0.41) | −0.18 (−0.54; +0.12) | −0.73 (−1.09; −0.39) | 2 / 48 |
| 12 (V6 D0) | 9.0 / 6.7 | 1.58 / 3.17 | 1.00 / 0.75 | +0.33 (+0.13; +0.55) | −0.66 (−1.02; −0.32) | +0.21 (−0.03; +0.45) | −0.21 (−0.53; +0.15) | 0 / 20 |
| 14 | 10.4 / 7.8 | 2.28 / 1.38 | 1.00 / 0.94 | +0.18 (+0.01; +0.36) | −0.01 (−0.26; +0.20) | +0.00 (−0.17; +0.16) | −0.05 (−0.31; +0.20) | 0 / 5 |
| 16 | 11.9 / 9.0 | 2.54 / 1.38 | 1.00 / 1.00 | −0.12 (−0.24; +0.01) | +0.24 (+0.12; +0.35) | −0.25 (−0.38; −0.12) | +0.30 (+0.20; +0.40) | 0 / 0 |
\* I8 S2 rests on 5 non-zero pairs of 80 (sign test p = 0.06) — not cited as an effect. All zero pairs are "neither moved"; "only the
control moved" never occurs. I8 S1: 90 % of Σd comes from 21 pairs where BOTH moved and DATA removed more of the initial error (2
only-DATA-moved pairs) — at low drive d measures progress toward the target, at I_max 12–16 steady-state accuracy/overshoot (different
quantities). Stratum contrast S1 − S2 (SWS) at fixed I_max: −1.05, +0.39, +1.00, +0.19, −0.35 (I8…I16) — the strata differ at every
I_max, with opposite-sign d at I16 (B1 CIs exclude 0).
Pre-specified drive model (OLS d ~ drive + ρ pooled over I_max): SWS drive +0.066 °/mV (+0.030; +0.105), ρ +0.08 (−3.4; +3.8); B1
drive +0.058, ρ +2.6 (CI incl. 0). It is mis-specified (RT61): the drive slope comes entirely from changing I_max — within every I_max
cell the scene-drive slope is ≤ 0; the scene drive index mostly measures azimuth (r = 0.81–0.86 with |az0|); with I_max terms the drive
slope is negative and ρ is −7.1 (−10.8; −3.3); within I_max 12 ρ is −21.9 (−35.5; −8.0); excluding I8/I10 drive is null and ρ −6.3
(−10.8; −1.9). The pooled "ρ ≈ 0" is a cancellation of opposite-signed slopes, not an absence of a distance effect.
Toy relay (no intermediate layer; reference): DNa02 0 Hz up to 6 mV, 22 Hz at 7, 60 at 8, 113 at 10 (DATA 50 / 83 / 161); small-signal G
38 Hz/mV at I0 7 (higher than DATA's 32), falling to 18 at I0 10 (DATA 47) — a differently shaped response.

## 3. Interpretation
- The pre-registered predictions are observed in direction: d(S1) becomes DATA-better as I_max decreases (+0.33 → −1.20 at 8, in a
  regime where the loop largely fails) and d(S2) becomes SWS-better as I_max increases (−0.66 → +0.24 at 16). So **changing the I_max gain
  (input drive and fixed-decoder loop gain together) reverses the sign of d in both strata.**
- What is NOT shown (corrected): that the sign is "governed by drive, not distance". The strata still differ at every I_max; S1 at
  I_max 16 has the highest drive but is DATA-better (contradicting a monotone drive account); within fixed I_max, ρ has a negative
  coefficient. d is a non-monotone function of I_max. An inverted-U in drive (SWS better at intermediate drive; both S1@12 and S2@16 have
  median drive ≈ 9 mV and d +0.33 / +0.24) is a POST-HOC hypothesis, not tested.
- B1 is "consistent with" SWS (same signs at 8, 10, 16), but d(SWS) and d(B1) share the DATA trial (r up to 0.95) and B1 shows no
  significant flip at I12 — agreement is partly mechanical.
- SESOI 0.5° (inherited): only I8 S1 has a CI beyond 0.5°, in a regime where the loop mostly fails.
- Cannot conclude: anything outside I_max 8–16, for a recalibrated decoder, or about the fly.

## 4. Limitations
Single decoder (D0) by design → drive and decoder mismatch are one manipulation; the drive index is per scene from a static render and
dominated by azimuth; matched-drive stratum contrasts are underpowered (CI widths 0.4–1.2°) and confounded with I_max; 40/80 scenes per
stratum; one parameter set; I12 arm re-used from V6.

## 5. Files
`v61_v7.py` (not hashed before the run), `v61_toy.py`, `v61_v7_analysis.py`; `results/v61/` (v61.jsonl 1440, drive_index.json, toy/,
analysis.json, analysis_stdout.txt, stdout*, stage1_post_*.json, redteam/RT61_review.md + RT61/ scripts).

## 6. Red team
RT61 (`redteam/RT61_review.md`, separate model instance; resampling seeds 8 498 401/402/404/405): data sound (1440 records, restart clean,
decoder and pairing verified, all numbers reproduce); NOT_READY on the draft for (1) headline over-reach, (2) mis-specified drive model,
(3) strata differ at fixed I_max, (4) low-drive mechanism, (5) B1 agreement partly mechanical, (6) provenance timing, (7) toy-gain
wording, (8) limitations, (9) unused seed pool — all corrected above.
