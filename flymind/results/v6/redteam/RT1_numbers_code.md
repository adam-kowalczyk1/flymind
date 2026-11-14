# V6 red team RT1: numbers and code (2026-10-30)

Reviewer: independent RT1 (numbers and code). Scope: `program_v5v41/V6_PROTOCOL.md` r1, `results/v6/REPORT.md` (DRAFT),
`results/v6/analysis.json`, `v6.py`, `v6_analysis.py`, `cl_runner.py`, `results/v6/analysis_stdout.txt`,
`results/v6/closedloop.jsonl`, `results/v6/openloop/<cfg>/*.npz`, `results/v5v41/raw` + `E6/raw` (D0 source).

**Method.** I wrote my own recompute scripts. They do not import `v6_analysis` or `v5v41_analysis`. They read only raw npz/jsonl:
own steady state = spikes in bins 50–99 / 0.5 s; own trapezoid; own threshold interpolation; own loop-based hierarchical and
cluster bootstraps; G from `np.polyfit` on |δ| ≤ 1. Scripts are in the session scratchpad (`rt1/ol.py`, `cl.py`, `fano.py`, `ceil.py`, `inter.py`).
**No new simulations were run** (no noise seeds used). My bootstrap RNG seeds were 8 495 601–8 495 603. They are resampling RNGs, not
simulation seeds. No existing file was modified. This file is the only one written.
Protocol sha256 matches `protocol_sha256_before_run.txt` (4d195e87…6468). All 4 `stage1_post_*.json` have ok = 28/28.

## 1. Independent recomputation: open loop (SWS family, Δ = SWS − DATA, DNa02 ipsi, Hz)

| Config | I_th10 RT1 | Δ 6–9 RT1 (CI) | Δ 9–12 RT1 (CI) | Δ own RT1 (CI) | Δ I_th30 | Δ G(I0 7) RT1 (CI) | vs REPORT |
|---|---|---|---|---|---|---|---|
| D0 | 6.02 | −15.88 (−17.87; −13.94) | −4.74 (−6.76; −3.39) | −16.80 (−18.82; −14.75) | +0.098 | −11.84 (−15.52; −9.44) | match |
| SG6 | 4.96 | +1.15 (−0.62; +2.88) | −0.24 (−0.55; +0.11) | +0.49 (−1.06; +1.66) | +0.040 | +0.43 (−3.10; +3.91) | match |
| TH8 | 7.10 | −5.92 (−6.49; −5.37) | −21.11 (−22.28; −19.42) | −15.04 (−16.50; −13.66) | +0.069 | −1.01 (−3.54; +1.47) | match |
| BA1 | 6.10 | −5.53 (−6.17; −4.92) | −14.39 (−15.31; −13.32) | −5.74 (−6.27; −5.20) | +0.943 | −5.27 (−10.34; −1.46) | match |
| J025 | 5.92 | −13.71 (−15.06; −12.11) | +7.25 (+5.43; +9.61) | −14.63 (−16.38; −12.98) | +0.069 | −10.37 (−18.22; −1.46) | match |

I also recomputed all of the other 11 configurations. Every point estimate in REPORT §2 / `analysis_stdout.txt` reproduces to ±0.01 Hz.
CI endpoints differ by ≤ 0.1 (bootstrap RNG only). Q6 for SG6 also reproduces: G CI at I0 8 is (−7.63; +1.92) against DATA 46.9, and
at I0 6 it is (−5.61; +4.28) against 41.8. Both fail ±10 %. **I0 7 passes** (±4.11 against CI −3.10; +3.91). B1 own-window values reproduce
(TH8 −15.00, BA1 −5.53, SG6 +0.55, BA0 −6.63).

## 2. Independent recomputation: closed loop (d = err(DATA) − err(ctrl), °, cluster bootstrap over control instance)

| Config | fam | S1 d (CI) RT1 | S2 d (CI) RT1 | zeros S2 | DATA err S1/S2 | vs REPORT |
|---|---|---|---|---|---|---|
| D0 | SWS | +0.333 (+0.116; +0.545) | −0.665 (−1.018; −0.307) | 20 | 1.58 / 3.17 | match |
| BA1 | SWS | +0.624 (+0.293; +0.961) | −0.295 (−0.565; −0.028) | 20 | 2.03 / 2.72 | match |
| TH6 | SWS | −0.187 (−0.294; −0.082) | +0.119 (−0.066; +0.289) | 4 | 2.07 / 1.60 | match |
| J015 | SWS | +0.151 (+0.015; +0.293) | −0.403 (−0.683; −0.137) | 21 | 0.74 / 4.05 | match |
| J025 | SWS | +0.084 (−0.045; +0.213) | +0.337 (+0.069; +0.639) | 19 | 2.70 / 3.11 | match |
| D0 | B1 | +0.208 (−0.019; +0.452) | −0.205 (−0.535; +0.150) | 20 | — | match |

I also recomputed the other 10 cells (BA0, TH8, SG6 × SWS/B1, and the remaining B1 cells). All means match `analysis_stdout.txt` to 3 decimals and all CIs to ±0.03.
- P controller: S1 0.2745°, S2 0.1487° (40 / 80 trials) → report 0.27 / 0.15 ✔.
- Q8 Spearman (SWS, own-window Δ against d): S1 −0.119, S2 +0.190 ✔. For reference, Pearson is +0.09 / +0.28.
- "Narrow regime" counts reproduce: SWS S1 4/8, SWS S2 4/8.
- 3000 records, 3000 unique names, 0 errors. Count per (config, family) = 120. P = 120.

## 3. Closed-loop pairing, shared scenes and decoders: all checks passed
For all 8 configs × 120 scenes I checked:
- the SWS k = SWS_SEEDS[(i−1) mod 50] (= protocol ((i−1) mod 50)+1);
- the B1 k = 8 421 001 + ((i−1) mod 25);
- DATA k = null;
- seed, az0, ρ and stratum are identical in the DATA, SWS and B1 records, and across all 8 configs plus P (common random numbers);
- the S1/S2 boundary is at 8 600 040, with ρ inside the stated ranges;
- `slope` in every record equals `calibration.json[cfg].slope`;
- the record's `alif` / `J0` matches `CONFIGS[cfg]`.
There were **0 violations**. The report's slope list (§1) matches `calibration.json`.

Structural notes:
- In S1, scenes 1–40 map to 40 distinct SWS instances. The SWS "cluster" bootstrap is therefore an iid bootstrap in S1.
- B1 has 25 clusters against 50 for SWS. Some of the significance differences between B1 and SWS are therefore power differences (see W7).
- I did not re-run the calibration. Reproducing it needs the registered seeds 8 601 001–003, which are outside my allowed range. It was verified as "used consistently", not as "correctly computed".

## 4. Ceiling claim (r_max = 1000/(dt·(ceil(t_ref/dt)+1)) = 250 Hz with t_ref 2.2 ms, dt 1 ms ✔)

Grid levels where DATA and the SWS mean are both ≥ 249 Hz / ≥ 240 Hz (13 levels per window):

| Config | 6–9 ≥249 | 9–12 ≥249 | 6–9 ≥240 | 9–12 ≥240 | DATA max |
|---|---|---|---|---|---|
| BA0 | 5/13 | 13/13 | 9/13 | 13/13 | 250.0 |
| BA0×TH6 | 13/13 | 13/13 | 13/13 | 13/13 | 250.0 |
| BA0×J025 | 12/13 | 13/13 | 13/13 | 13/13 | 250.0 |
| BA0×TH8 | 0/13 | 2/13 | 0/13 | 10/13 | 249.8 |
| BA0×J015 | 0/13 | 0/13 | 0/13 | 2/13 | 244.2 |
| **TA100** | 0/13 | 0/13 | 0/13 | **9/13** | **249.5** |
| BA025 | 0/13 | 0/13 | 0/13 | 2/13 | 244.2 |
| J025 | 0/13 | 0/13 | 0/13 | 0/13 | 239.0 |
| all others | 0 | 0 | 0 | 0 | ≤ 231 |

- The † flags in the table are correct for BA0 9–12, BA0×TH6 (all windows) and BA0×J025 (all windows).
- **The claim at REPORT l.59–60 is overstated.** It says "All b_a = 0 cells have DNa02 near or at the 250 Hz ceiling over much of the range".
  BA0×J015 never reaches 250 (max 244, only 2/13 levels ≥ 240 in 9–12). BA0×TH8 is near the ceiling only in 9–12.
- **A non-b_a = 0 configuration is ceiling-limited and is not flagged:** TA100 9–12 (DATA 249.5 Hz at 12 mV; 9/13 levels ≥ 240).
  Its Δ 9–12 = −2.2 Hz is ceiling-compressed. J025 9–12 (the "+7.3 Hz reversal") runs at DATA 220–239 Hz, about 10 Hz below the ceiling.
  Not artefactual, but compressed.
- BA0 own window (levels 6.0–8.75) contains 4 ceiling levels. Its whole deficit comes from **one grid level**: at 6.0 mV DATA is 164.2 Hz and SWS 39.3 Hz.
  At 5.75 mV both are 0. At 6.25 mV the values are 234 against 224. So BA0's −8.4 Hz is a ≈ 0.1–0.2 mV threshold shift on a near-step onset,
  sampled by a single 0.25 mV grid point. REPORT l.42 says "5.75–6.5 mV"; the effect is at 6.0 mV only.
- The BA0 cell (A0B0) is in **all four** interaction contrasts. All four therefore carry the ceiling (the report says so; fine).

## 5. Post-hoc LC10a Fano (REPORT table column, footnote l.39–42)
**No script and no output file produces these numbers.** There is nothing in `v6_analysis.py`, `analysis.json` or any `results/v6` file. The
values cannot be reproduced exactly. My implementation follows the footnote definition: summed ipsi LC10a count (column 0), 10 ms bins 50–99, levels 7.0–9.0
(9 levels), var/mean per (level, side, rep), averaged; SWS = mean of SWS 8 410 001–010.

| Config | REPORT D/S | RT1 ddof 0 D/S | RT1 ddof 1 D/S | RT1 pooled var/mean D/S |
|---|---|---|---|---|
| D0 | 11.3 / 39.2 | 11.6 / 38.8 | 11.9 / 39.6 | 10.5 / 36.2 |
| BA0 | 0.5 / 0.5 | 0.5 / 0.5 | 0.5 / 0.5 | 0.4 / 0.4 |
| BA1 | 25.8 / 55.4 | 26.7 / 57.4 | 27.2 / 58.6 | 27.1 / 57.5 |
| TH8 | 15.1 / 44.6 | 16.4 / 46.8 | 16.8 / 47.8 | 17.3 / 52.6 |
| J025 | 10.1 / 29.0 | 11.9 / 30.2 | 12.2 / 30.8 | 10.8 / 27.0 |
| SG0 | 81.2 / 104.9 | 82.8 / 105.1 | 84.5 / 107.3 | 71.9 / 98.6 |
| SG6 | 1.6 / 1.6 | 1.7 / 1.8 | 1.8 / 1.9 | 1.7 / 1.8 |

- The qualitative pattern reproduces: SWS is 2–3× DATA in D0, BA1, TH8, J025; SG6 is about equal; BA0 is about 0.5 in both. The exact values do not
  reproduce (differences up to 1.8 in DATA and 2.2 in SWS; J025 DATA 10.1 against 11.6–12.2). The report must cite the script that produced them.
- **The post-hoc correlation (l.62–66) omits configurations that weaken it.** It says the deficit is absent "exactly where" the synchrony difference is absent.
  The configurations below are not in the report table:

  | Config | Fano DATA / SWS (RT1) | Δ own [Hz] |
  |---|---|---|
  | TH6 | 5.6 / 14.1 | −12.6 |
  | J015 | 13.8 / 40.9 | −11.1 |
  | BA025 | 4.5 / 14.0 | −16.2 |
  | TA100 | 2.7 / 5.7 | −13.8 |
  | SG0 | 82.8 / 105.1 (ratio 1.27) | −7.7 |

  These are consistent in direction. The exception is SG0, where the synchrony ratio is only 1.27 and a clear deficit remains. **BA0 (Fano 0.5 / 0.5, equal) has a clear deficit (−8.4 Hz)**,
  which contradicts "absent exactly where synchrony is absent". The report explains it away because the deficit sits outside the Fano window, but that is a post-hoc
  window argument. The report says "7 configurations"; the table has 7 Fano entries, of which BA0 is a counter-example.

## 6. Does the analysis code implement protocol §5?
| §5 item | Code | Status |
|---|---|---|
| Windows 6–9, 9–12, own [I_th10, I_th10+3] | `v6_analysis.py:59–69`, `range_avg` (v5v41_analysis.py:119–123) | **Deviation (minor).** `range_avg` integrates only over grid points inside the window, so "own" = [ceil₀.₂₅(I_th10), floor₀.₂₅(I_th10+3)] (2.75 mV wide, e.g. D0 6.25–9.0). With exact-interval interpolation, D0 own is −16.08 (not −16.80), J025 −13.88 (not −14.63), TH8 −14.74 (not −15.04), SG6 +0.51, BA1 −5.73. This changes no conclusion; it should be documented. |
| Δ I_th10 / I_th30 with hierarchical CI | l.70–74 | **Partial.** Point Δ and control percentiles only, no bootstrap CI. |
| Δ G (E6) at I0 5–9, hierarchical CI | l.75–81 | ✔ (all I0 4–11 computed). |
| Q6 equivalence: own CI within ±5 Hz AND Δ G CI within ±10 % | l.82–84 | **Under-specified in protocol, filled post hoc.** The code uses I0 6, 7, 8. The protocol states no I0 set for Q6. The report (l.53) calls "±10 % G at I0 6–8" pre-registered. A DATA G of 0 at any I0 (TH8 I0 6; BA0×TH6, BA0×J025) auto-fails Q6. This is reasonable, but undocumented. |
| Interaction contrasts with bootstrap CI | l.91–108 | **Formula ✔** (A1 = b_a 0.5, A0 = b_a 0; point values reproduce: +0.54, +3.99, +3.66, −5.96). **CI ✘.** The bootstrap resamples only SWS instances and treats the DATA rep mean of each of the 4 configs as fixed, which is inconsistent with the §5 hierarchical scheme. Resampling DATA reps and control reps as well (instances paired across configs) gives the CIs below. All CIs widen 6–9×, and **gap6 no longer excludes 0**. Also, each cell uses its own "own" window, so a contrast mixes different current ranges. |
| Closed loop d per stratum, cluster bootstrap, RNG 8 419 021, median, zero pairs, one-moved | l.112–149 | ✔ (reproduced). |
| Outcomes "signed final error, overshoot, movement, last-second SD" (§4 l.41) | l.130, 145 | **Partial.** Only overshoot difference and movement are summarised; signed error and last-1 s SD are recorded in the jsonl but never analysed or reported. |
| Q8 Spearman n = 8 | l.163–169 | ✔. |
| "Spontaneous rate … and saturation recorded" (§3) | l.86 | **D0 spontaneous rate not measured.** `load_cfg` for D0 sets no `spont`, so `z.get("spont", 0)` returns a placeholder 0. The v5v41 raw files have no spontaneous field. No saturation metric is computed (the ceiling notes are ad hoc). |

Interaction CIs with full resampling:

| Contrast | Point | CI as reported | CI with full resampling |
|---|---|---|---|
| b_a×gap6 | +0.54 | (+0.05; +1.01) | **(−3.08; +4.16)** |
| b_a×gap8 | +3.99 | (+3.6; +4.4) | (+0.99; +7.02) |
| b_a×J0.15 | +3.66 | (+3.3; +4.0) | (+0.82; +6.48) |
| b_a×J0.25 | −5.96 | (−6.4; −5.5) | (−8.96; −3.01) |

Other code notes (no impact found):
- `dn_ss` LC: column 0 is always the stimulated-side LC10a (`v5v41.simulate` l.117), so dividing by n_pop[side] is correct.
- B1 = largest single-block family by the §2 rule. B5 (ALL) is larger but is not single-block. ✔
- `v6.py:134` and `:137` pairing matches the protocol.

## 7. Claim-level discrepancies in REPORT.md

W1. **Q5 (l.51) is false as stated.** It says "in all 15 non-ceiling configurations the deficit is largest within ~3 mV above DATA's threshold".
  (a) There are 16 configurations, and 2–3 are ceiling cells, so "15 non-ceiling" is miscounted.
  (b) Location of the most negative Δ(level) on the SWS-mean curve:
  - **BA1: 11.25 mV, 5.2 mV above I_th10 (−19.8 Hz).** Its 9–12 Δ (−14.4) is 2.5× its own-window Δ (−5.7).
  - **TH8: 10.5 mV, 3.4 mV above, outside its own window.** Its 9–12 Δ (−21.1) exceeds its own-window Δ (−15.0).

  Others are within ~3 mV: D0 9.0, J015 9.25, SG0 9.75, TA1000 9.25.

W2. **B1 "follows SWS within ~1–2 Hz in every non-D0 configuration" (l.43) is false.** Own-window B1 against SWS:
  - BA0×TH8: −6.42 against −10.62 (4.2 Hz, B1 = 60 % of SWS)
  - BA0×J015: −3.33 against −6.35 (3.0 Hz, 52 %)
  - TA100: −10.28 against −13.79 (3.5 Hz, 75 %)
  - BA025: −13.78 against −16.21 (2.4 Hz)
  - J025 9–12: +10.19 against +7.25 (2.9 Hz)
  - TA100 6–9: −9.6 against −13.15 (3.6 Hz)

W3. **"Family X (B1), which reproduces ~94 % of the open-loop deficit" (l.90).** The 94 % is the V5 v4.2 D0 figure (6–9 mV). V6 has no D0 B1 cell.
  Across the V6 configurations, B1/SWS own-window ranges from 52 % to 103 %. Cite the 94 % as "at default parameters (V5 v4.2)".

W4. **"B1 … same sign as SWS in 6/8 × 2 cells" (l.90) is wrong.** The count is 13/16: S1 5/8 (differs in BA0, J025, SG6) and S2 8/8.
  **"B1 and SWS differ in TH8 S2 and J015" (l.91) is incomplete.** CI-excludes-0 status differs in 6 cells: D0 S1, D0 S2, BA1 S2, TH8 S2,
  J015 S1 and J025 S2. J015 S2 is significant for both. With 25 against 50 clusters, part of this is power.

W5. **Ceiling sentence (l.59–60), see §4.** "All b_a = 0 cells … near or at the ceiling over much of the range" does not hold for BA0×J015
  (max 244 Hz) and holds only at 9–12 for BA0×TH8. TA100 9–12 needs a ceiling note (not only b_a = 0 cells).

W6. **Interaction CIs (l.58–59)** omit DATA rep noise (§6 above). Replace them with the full-resampling CIs, or label them "conditional on DATA rep means".
  With full resampling, b_a×gap6 includes 0.

W7. **"Q6 … pre-registered … ±10 % G at I0 6–8" (l.53).** The I0 set is not in the protocol. Say "I0 6–8 chosen at analysis (protocol: 'Δ G')".
  Also state that SG6 passes at I0 7 and fails at I0 6 and 8.

W8. **SESOI 0.5° (l.86)** is not defined in V6_PROTOCOL.md. It is inherited from V5v41_PROTOCOL.md l.67 (where it applied to decoded angle). Label it as inherited, not pre-registered for V6.

W9. **Spontaneous activity "0 spikes in every network and configuration" (l.44).** D0 was not measured in V6 (placeholder 0, `v6_analysis.py:86`).
  Restrict the claim to the 15 simulated configurations, or cite V5 v4.1 for D0.

W10. **Fano column / post-hoc paragraph (l.39–42, 62–66).**
  - Add the producing script or a results file, because the numbers are not reproducible from the repository (RT1 differs by up to ~2).
  - Report the Fano values for all configurations computed, including TH6, J015, BA025 and TA100.
  - Acknowledge that BA0 (equal Fano, deficit present) and SG0 (ratio 1.27, deficit present) do not fit "absent exactly where synchrony is absent".
  - Soften to "in 5 of 7 checked configurations".

W11. **BA0 footnote (l.42)** "deficit sits at 5.75–6.5 mV" should read "at a single grid level (6.0 mV: DATA 164 against SWS 39 Hz; 5.75 both 0; 6.25 234 against 224)". This is a sub-0.25 mV onset shift, so its magnitude in Hz is grid-resolution dependent.

W12. **Own window definition (l.20)** should state the grid-snapping convention (effective width 2.75 mV). Its effect is up to 0.75 Hz (D0, J025).

W13. **The closed-loop zero pairs ARE the "neither network moved" scenes** (zeros = neither_moved in every cell). In those scenes DATA error is about the initial offset, and P moves (mean 0.19°).
  They make up 27 % of the D0 S2 DATA error sum and 57 % of TH8's. The D0 S2 mean d (−0.665) falls to −0.46 when the 3 most negative scenes are dropped. "Carried by a minority of scenes" (l.88–89) is supported. I suggest quoting this sensitivity.

W14. Minor: TH8 DATA S2 err is 7.745. The table shows 7.75 and the text 7.7; use one value.

## 8. Items checked and found correct
All open-loop point estimates and CIs (16 configs, SWS and B1), Δ I_th30, Δ G(I0 7), BA0/BA025/BA1 Q2 sequence, J025 +7.3 reversal, SG6 Q6 failure
reason, all closed-loop d / CI / median / zeros / DATA err (8 configs × SWS and B1 × 2 strata), P errors, Q8 Spearman, narrow-regime counts,
scene pairing and CRN across configs, decoder slope usage, protocol sha, Stage 1 28/28 ×4, the SESOI statement itself (no CI beyond 0.5°), 3000 records / 0 errors.

## Verdict: **PASS_WITH_LIMITATIONS**
Every number the conclusions rest on reproduces independently from raw files, and the closed-loop pairing and decoder sharing are correct.
Several pieces of descriptive wording are factually wrong or overstated:
- W1: Q5 claim
- W2: B1 within 1–2 Hz
- W4: sign/significance count
- W5: ceiling scope
- W10: the post-hoc Fano "exactly where" claim

The interaction CIs are too narrow (W6), and the Fano numbers have no producing code (W10). None of these reverses the main open-loop or closed-loop
conclusions, but they must be fixed before the report leaves DRAFT.

### Required wording fixes (minimum)
1. l.51 Q5: "in most configurations the deficit is largest within ~3 mV above DATA's threshold; exceptions BA1 (max at 11.25 mV, 9–12 Δ −14.4) and TH8 (10.5 mV, 9–12 Δ −21.1)". Also fix the configuration count.
2. l.43: "B1 follows SWS within ≤ 2 Hz in most configurations; up to 4.2 Hz smaller in BA0×TH8, 3.0 in BA0×J015, 3.5 in TA100".
3. l.90: "~94 % (at default parameters, V5 v4.2)"; "same sign as SWS in 13/16 cells (S1 5/8, S2 8/8)"; list the 6 cells with discordant CI status and note that B1 has 25 clusters.
4. l.59–60: restrict the ceiling statement to BA0 (≥ 8 mV), BA0×TH6, BA0×J025 (whole range) and BA0×TH8 (9–12). State that BA0×J015 is below the ceiling. Add a ceiling note for TA100 9–12.
5. l.58–59: replace the interaction CIs with ones that include DATA rep resampling (RT1: gap6 −3.1; +4.2 · gap8 +1.0; +7.0 · J0.15 +0.8; +6.5 · J0.25 −9.0; −3.0), or label them "conditional on DATA".
6. l.53: "±10 % G at I0 6–8 (I0 set chosen at analysis; protocol states only Δ G)". Note that SG6 passes at I0 7.
7. l.86: "SESOI 0.5° (inherited from V5 v4.1 protocol, not re-registered in V6)".
8. l.44: "0 spikes in every simulated network/configuration (D0 not re-measured in V6)".
9. Table footnote and l.62–66: name the Fano script/output; report Fano for all configurations computed; replace "exactly where" with a count that includes BA0 and SG0 as non-fitting cases.
10. l.42: BA0 deficit is "at the 6.0 mV grid level (onset shift < 0.25 mV)", not "5.75–6.5 mV".
11. §2 header / l.20: document the grid-snapped own window (effective [ceil(I_th10), floor(I_th10+3)] on the 0.25 mV grid).
12. §5 Limitations: add "signed final error and last-second SD recorded but not analysed (protocol §4)"; "Δ thresholds without CI"; "decoder calibration not independently re-run".
