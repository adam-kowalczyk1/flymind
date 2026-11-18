# V6 — Network structure × ALIF dynamics (parameter study): report (2026-10-30)

**Status: exploratory parameter study, completed. Verdict: PASS_WITH_LIMITATIONS** (RT1 numbers/code PASS_WITH_LIMITATIONS; RT2
interpretation NOT_READY on the draft → all 15 + 12 required wording fixes applied below; §9).
LC10a / DNa02 / "intermediates" denote MODEL populations built from connectome cell types; every "regime" below is a region of model
parameter space (b_a, σ, τ_a, J0, v_th are design choices without data); nothing here is a statement about the fly.

## 1. What was done
Protocol `program_v5v41/V6_PROTOCOL.md` r1 (sha 4d195e87…, written before any V5 v4.1+ result; no r2). 16 configurations (D0 + 15,
the complete pre-registered list), open loop (E1 unilateral 4–12 mV, 33 levels, 4 reps; E6 symmetric I0 4–11 ± δ, 4 reps) for DATA,
50 SWS v2 instances (8 410 001–050) and family X = **B1 LC×LC** (pre-registered rule: largest |Δ DNa02 6–9 mV| among V5 v4.2 block
families with CI excluding 0), first 25 instances (8 421 001–025). D0 open loop = first 4 reps / 33-level subset of V5 v4.1 (same seeds
and schedules; no B1 cell at D0; D0 spontaneous rate not re-measured). Closed loop (MuJoCo, frozen `loop.run_trial` via `cl_runner.py`):
8 configurations × 120 scenes (8 600 001–120; S1 ρ [0.16, 0.22) n = 40; S2 [0.22, 0.28) n = 80) × {DATA, SWS, B1} + P once = **3000
trials, 0 errors**. Pairing scene i ↔ SWS ((i−1) mod 50)+1 and B1 (i−1) mod 25 verified (RT1, 0 violations); identical scenes across
configurations (common random numbers). Decoder per configuration calibrated on DATA (8 601 001–003), shared by SWS/B1; slopes (Hz/rad)
D0 496.5, BA0 516.0, BA1 176.9, TH6 530.7, TH8 436.1, J015 400.6, J025 553.8, SG6 472.2. Stage 1 28/28 in all 4 post-run files.
Execution note: a chained duplicate launcher found 0 remaining trials, then crashed on a same-second Stage-1 file name — no data
affected. Analysis `v6_analysis.py` (RNG 8 419 020/021) → `analysis.json`; post-hoc Fano `v6_fano_posthoc.py` → `posthoc_lc_fano.json`;
figures `figures/V6_F1_openloop_curves.png`, `V6_F2_closedloop_d.png`.
Window conventions: "own" = DATA's [I_th10, I_th10 + 3 mV] snapped to the 0.25 mV grid; the Q6 G criterion was evaluated at I0 6–8
(an analysis-time choice — the protocol states only "Δ G"); the 0.5° SESOI is inherited from `V5v41_PROTOCOL.md` (not re-registered
in V6). Recorded but not analysed: signed final error, last-second SD (protocol §4); threshold deltas have no CI.

## 2. Open loop — DATA vs SWS (Δ = SWS − DATA, DNa02 ipsi steady state; CI95 hierarchical bootstrap)
| Config | DATA I_th10 | Δ DN 6–9 [Hz] (CI) | Δ DN 9–12 (CI) | Δ DN own (CI) | Δ I_th30 [mV] | Δ G(I0 7) | LC10a Fano own window DATA / SWS (post hoc) |
|---|---|---|---|---|---|---|---|
| D0 | 6.02 | −15.9 (−17.8; −13.9) | −4.7 (−6.8; −3.4) | −16.8 (−18.8; −14.7) | +0.10 | −11.8 (−15.6; −9.5) | 11.8 / 40.6 |
| BA0 (b_a 0) | 5.77 | −7.7 (−8.8; −6.7) | −0.02 † | −8.4 (−9.6; −7.3) | +0.15 | +4.6 | 1.2 / 1.7 |
| BA025 | 5.88 | −15.0 (−16.9; −11.7) | −3.8 | −16.2 | +0.14 | −22.1 | 7.5 / 21.5 |
| BA1 (b_a 1) | 6.10 | −5.5 (−6.2; −4.9) | −14.4 (−15.3; −13.3) | −5.7 (−6.3; −5.2) | +0.94 | −5.3 | 23.4 / 53.3 |
| TH6 (gap 6) | 4.94 | −7.7 (−9.6; −5.7) | −0.4 (−1.0; +0.1) | −12.6 (−15.0; −10.5) | +0.16 | −7.5 | 9.9 / 30.5 |
| TH8 (gap 8) | 7.10 | −5.9 (−6.5; −5.4) | −21.1 (−22.3; −19.4) | −15.0 (−16.6; −13.6) | +0.07 | −1.0 | 14.1 / 47.5 |
| J015 | 6.26 | −8.5 (−9.6; −7.4) | −9.3 (−10.7; −7.2) | −11.1 (−12.6; −9.6) | +0.44 | −4.2 | 12.2 / 36.4 |
| J025 | 5.92 | −13.7 (−15.1; −12.2) | +7.3 (+5.4; +9.7) | −14.6 (−16.4; −12.9) | +0.07 | −10.4 | 11.9 / 31.9 |
| SG0 (σ 0) | 7.17 | −1.4 (−1.6; −1.2) | −6.5 (−7.1; −6.0) | −7.7 (−8.1; −7.3) | +0.12 | +0.4 | 61.1 / 87.5 |
| SG6 (σ 6) | 4.96 | +1.2 (−0.6; +2.9) | −0.2 (−0.6; +0.1) | +0.5 (−1.0; +1.7) | +0.04 | +0.4 (−3.1; +3.8) | 1.7 / 1.7 |
| TA100 | 5.90 | −13.2 (−14.2; −12.1) | −2.2 † (9–12 near ceiling) | −13.8 | +0.09 | +14.3 | 6.4 / 16.7 |
| TA1000 | 6.62 | −5.4 (−6.0; −4.9) | −5.6 | −6.3 | +2.51 | −11.8 | 11.5 / 39.7 |
| BA0×TH6 | 4.76 | 0.00 † | 0.00 † | −4.8 (−6.3; −3.3) | +0.05 | 0.0 † | 1.0 / 1.0 |
| BA0×TH8 | 6.80 | −10.4 (−12.1; −7.9) | −2.5 † | −10.6 | +0.15 | −20.5 | 2.3 / 4.1 |
| BA0×J015 | 6.02 | −7.2 (−7.9; −6.2) | −4.3 | −6.4 | +0.04 | +19.2 | 2.2 / 5.1 |
| BA0×J025 | 5.76 | −0.2 (−0.4; −0.1) † | 0.00 † | −0.3 (−0.4; −0.1) † | +0.00 | 0.0 † | 0.5 / 0.5 |
† DNa02 at or near the 250 Hz refractory ceiling in both networks over that range (BA0 ≥ 8 mV; BA0×TH6 and BA0×J025 whole range;
BA0×TH8 and TA100 at 9–12 mV): a zero difference there is a ceiling artefact, not equivalence. BA0×J015 stays below the ceiling (max
244 Hz). BA0's deficit sits at the single 6.0 mV grid level (DATA 164 vs SWS 39 Hz; both 0 at 5.75) — an onset shift < 0.25 mV.
Relative to DATA's own-window rate the deficit ranges −3 % (BA0) to −26 % (TH8). Spontaneous activity: 0 spikes in every simulated
network/configuration (D0 not re-measured).
Family X (B1): within ≤ 2 Hz of SWS in most configurations, but smaller in TA100 (−10.3 vs −13.8), BA0×TH8 (−6.4 vs −10.6), BA0×J015
(−3.3 vs −6.4); across V6 configurations B1 carries 52–103 % of the SWS deficit (~94 % at D0 in V5 v4.2).

**Q1 (thresholds):** SWS < DATA near DATA's threshold at gap 6 and 8 mV (own −12.6, −15.0 Hz).
**Q2 (adaptation):** sign unchanged with b_a in the own window (b_a 0 / 0.25 / 0.5 / 1: −8.4 / −16.2 / −16.8 / −5.7); at 9–12 mV the
difference is ceiling-limited at b_a 0 and largest at b_a 1 (−14.4).
**Q3 (J0):** SWS < DATA near threshold at J0 0.15 and 0.25.
**Q5 (amplitude):** in 12 of 14 non-ceiling configurations the deficit is largest near DATA's threshold; exceptions BA1 (largest at
~11.25 mV) and TH8 (10.5 mV, just above its own window). Above threshold size and sign depend on the configuration.
**Q6 (equivalence: own-window ΔDN CI within ±5 Hz AND ΔG CI within ±10 % at I0 6–8):** met by no configuration. SG6 meets the DN part
(−1.0; +1.7) and the G part at I0 7, but not at I0 8 (−7.6; +1.9 vs DATA 46.9) → "equivalence not shown". At σ 6 the difference is not
detected in window averages, but pointwise differences remain (6.0 / 6.5 mV, opposite signs that cancel) and ΔG at I0 9 is +3.9 (+2.4;
+5.6) Hz/mV (~+10 %).
**Q7 (control stronger):** a high-drive SWS > DATA crossing appears at 8.75–10.75 mV in D0, TH6, J025 and SG0 (pointwise CIs excluding
0, unadjusted: TH6 +11.4 Hz at 8.75 mV, SG0 +10.9 at 10.75, J025 9–12 window +7.3; SG6 +5.4 at 6.5); how it shifts with parameters
was not estimated.
**Interaction contrasts (pre-specified 2×2, Δ own window):** with the analysis as pre-specified (DATA reference fixed): b_a×gap6 +0.5
(+0.05; +1.0), b_a×gap8 +4.0, b_a×J0.15 +3.7, b_a×J0.25 −6.0 — these CIs ignore DATA rep noise (anti-conservative); resampling DATA reps
too (RT1): gap6 (−3.1; +4.2), gap8 (+1.0; +7.0), J0.15 (+0.8; +6.5), J0.25 (−9.0; −3.0). All b_a = 0 cells are partly ceiling-limited →
the contrasts are **not interpretable as mechanistic interactions**.
**Post-hoc synchrony check (not pre-registered; `v6_fano_posthoc.py`, all 50 SWS, no CI):** the SWS/DATA LC10a Fano ratio in DATA's own
window is 2.3–3.4 in the 11 configurations with the largest deficits, ≈ 1.0 in SG6 (Δ +0.5 Hz) — but the pattern is not exact: BA0
(ratio 1.4, Δ −8.4), SG0 (1.4, −7.7) and BA0×TH6 (1.05, −4.7, ceiling-affected) have deficits without a large synchrony ratio, and BA1 /
TA1000 have large ratios (2.3 / 3.4) with small deficits (−5.7 / −6.3). The SG6 co-disappearance is also explained by noise dominance
(σ 6 decorrelates spiking AND smooths the f–I curve, DATA I_th10 6.02 → 4.96 mV) — the two accounts are not distinguished here (causal
tests: V5 v4.3 replay, V6m).

## 3. Closed loop (d = err(DATA) − err(ctrl) [°]; positive = control lower error; CI95 cluster bootstrap over control instances)
| Config | DATA err S1 / S2 [°] | SWS S1 | SWS S2 | B1 S1 | B1 S2 | S2 zero pairs | d_S1 − d_S2 (SWS; RT2) |
|---|---|---|---|---|---|---|---|
| D0 | 1.58 / 3.17 | +0.33 (+0.12; +0.55) | −0.66 (−1.02; −0.33) | +0.21 (−0.02; +0.45) | −0.21 (−0.54; +0.15) | 20 | +1.00 (+0.59; +1.40) |
| BA0 | 5.92 / 5.19 | +0.01 (−0.39; +0.41) | +0.23 (−0.19; +0.62) | −0.25 (−0.79; +0.18) | +0.30 (−0.08; +0.69) | 20 | ~0 |
| BA1 | 2.03 / 2.72 | +0.62 (+0.28; +0.95) | −0.29 (−0.57; −0.04) | +0.64 (+0.34; +0.97) | −0.23 (−0.52; +0.03) | 20 | +0.92 (+0.52; +1.31) |
| TH6 | 2.07 / 1.60 | −0.19 (−0.30; −0.08) | +0.12 (−0.07; +0.30) | −0.16 (−0.28; −0.05) | +0.08 (−0.08; +0.24) | 4 | −0.31 (−0.54; −0.08) |
| TH8 | 1.60 / 7.75 | +0.26 (−0.02; +0.59) | −0.25 (−0.57; +0.08) | +0.12 (−0.21; +0.47) | −0.37 (−0.58; −0.19) | 46 | +0.51 (+0.05; +0.99) |
| J015 | 0.74 / 4.05 | +0.15 (+0.01; +0.29) | −0.40 (−0.68; −0.14) | +0.10 (−0.08; +0.27) | −0.38 (−0.69; −0.11) | 21 | +0.55 (+0.24; +0.89) |
| J025 | 2.70 / 3.11 | +0.08 (−0.05; +0.21) | +0.34 (+0.07; +0.64) | −0.09 (−0.22; +0.04) | +0.26 (−0.07; +0.57) | 19 | ~0 |
| SG6 | 1.77 / 0.93 | +0.11 (−0.05; +0.26) | +0.08 (−0.02; +0.18) | −0.13 (−0.26; +0.00) | +0.05 (−0.03; +0.13) | 0 | ~0 |
Zero pairs = S2 scenes with |az0| ≤ 9° (TH8 ≤ 19°) where no network moved; "only one network moved" occurs in 0–2 pairs per cell. P
controller (reference only, encoder-based engineering controller, not part of any DATA/SWS inference): S1 0.27°, S2 0.15°.
Individual cells are unadjusted: ~48 closed-loop CIs → 2–3 exclusions of 0 expected by chance alone.

- **D0 replication of V5 v4:** with new scenes, new SWS instances (8 410 001–050 instead of the V5 v4 instances) and a new DATA
  calibration (slope 496.5 vs 492.1), D0 shows the V5 v4 stratum interaction: S1 +0.33 (V5 v4 +0.51), S2 −0.66 (V5 v4 −0.52),
  d_S1 − d_S2 +1.00 (+0.59; +1.40).
- **Parameter dependence (stratum × network interaction, d_S1 − d_S2):** positive in 4/8 configurations (D0, BA1, J015, TH8),
  reversed in TH6 (−0.31), indistinguishable from 0 in BA0, J025, SG6. Paired config − D0 contrasts (same scenes and pairings; RT2): S2
  differs from D0 for BA0 +0.89, TH6 +0.78, J025 +1.00, SG6 +0.75, TH8 +0.42 (CI lower bound 0.00); S1 differs for TH6 −0.52 and J025
  −0.25; BA1 and J015 are not distinguishable from D0. Pre-registered "narrow regime" rule: CI excludes 0 in 4/8 per stratum → not
  "narrow", but the direction is not common to all parameter sets.
- **Confound for all cross-configuration statements:** the decoder is DATA-calibrated per configuration and imposed on SWS/B1; slopes
  range 177–554 Hz/rad and DATA's baseline error 0.74–7.75°. Post hoc, decoder slope ranks d better than the open-loop deficit
  (Spearman −0.76 S1, +0.71 S2; n = 8, driven by BA1). A lower-gain network under a DATA-tuned decoder overshoots less near (S1) and
  under-drives far (S2) — a structure-free account of the S1+/S2− sign (overshoot difference S1: D0 +0.45°, BA1 +1.09°, TH6 −0.25°,
  sign follows d). Cross-configuration differences in d therefore cannot be attributed to the ALIF parameter acting on the structure
  difference alone. Loops that barely work (BA0, TH8 S2) or work very well (SG6 S2) also compress d mechanically.
- **SESOI 0.5° (inherited):** 7/16 SWS cells are shown within ±0.5° (S1 BA0, TH6, J015, J025, SG6; S2 TH6, SG6); 9/16 are
  indeterminate (CIs reach −1.02 D0 S2, +0.95 BA1 S1); none is shown beyond 0.5°. n per stratum is 40/80 (V5 v4: 150/300) → CIs ≈ 2×
  wider; "CI includes 0" cells are underpowered rather than null.
- **B1 vs SWS (paired contrast B1 − SWS, RT2):** different at D0 S2 +0.46 (+0.20; +0.73), J025 S1 −0.17, SG6 S1 −0.24; not different in
  TH8 S2 and J015. **At D0, B1 reproduces the open-loop deficit (~94 %) but only about half of SWS's S2 closed-loop effect** — the
  strongest evidence here that the open-loop unilateral deficit alone does not determine d. Same sign as SWS in 13/16 cells (partly
  built in by the shared DATA term).
- **Q8:** the protocol's quantity (closed-loop interaction d_S1 − d_S2 vs open-loop Δ own) gives Spearman −0.12; per stratum S1 −0.12,
  S2 +0.19 (exact p 0.79 / 0.67; ρ CIs ≈ −0.9 to +0.8; n = 8; x has little leverage, 7/8 values in −5.7…−16.8 Hz; with Δ expressed
  relative to DATA's rate ρ becomes −0.62 / +0.69 — fragile). No monotone association detected; the data neither support nor exclude
  a moderate-to-strong link.

## 4. Interpretation
- MODEL-level claim (pre-registered measures): the open-loop SWS < DATA difference near DATA's threshold is sign-consistent under every
  one-factor variation of b_a (0–1), threshold gap (6–8 mV), τ_a (100–1000 ms) and J0 (0.15–0.25), with ~3-fold variation in size; it is
  not detected in window averages at σ 6 mV — a parameter no data constrains (default σ 2 gives ≈ 0.32 mV membrane SD, a low-noise
  regime). Joint variation was tested only in two ceiling-confounded 2×2 blocks.
- Post hoc, hypothesis-generating: LC10a synchrony differences accompany most large deficits, with clear exceptions (§2); noise
  dominance is an equally good account of the σ 6 result.
- Closed loop: the V5 v4 stratum interaction replicates at D0 with new scenes, instances and calibration; across the 8 parameter sets it
  is present in 4, reversed in 1 and absent in 3; these differences are confounded with decoder slope and DATA's baseline performance.
  No closed-loop difference is shown to exceed the 0.5° SESOI; 9/16 cells cannot exclude it.
- Cannot conclude: that the connectome-derived wiring improves or worsens closed-loop orienting in general (over these 8 model parameter
  sets); which mechanism links the open-loop deficit to d; anything about Drosophila.
- Alternative explanations kept open: noise dominance (σ 6), decoder/gain mismatch (S1+/S2− sign), baseline operating point / shared
  dead zone (bounds d), 250 Hz ceiling (b_a = 0 cells).

## 5. Limitations
4 reps per open-loop cell; one DATA network (CI = noise reps); one-factor-at-a-time design; ~hundreds of open-loop and 48 closed-loop
CIs without multiplicity correction; 40/80 scenes per stratum; decoders recalibrated per configuration (not independently re-run);
B1 has 25 clusters and no D0 open-loop cell; ceiling effects in b_a = 0 cells; post-hoc Fano without CI; signed error and last-second
SD not analysed; threshold deltas without CI.

## 6. Files
`v6.py`, `v6_analysis.py`, `v6_figures.py`, `v6_fano_posthoc.py`, `cl_runner.py` (+ `test_cl_runner.py`); `results/v6/` (openloop/<cfg>/
76 npz × 15, closedloop.jsonl 3000 records, calibration.json, analysis.json, analysis_stdout.txt, posthoc_lc_fano.json, figures/,
stage1_post_*.json, stdout_*.txt, redteam/).

## 9. Red team
RT1 (`redteam/RT1_numbers_code.md`): all open-/closed-loop numbers, pairing, decoders, Q8 and Stage 1 reproduced from raw files;
discrepancies in Q5, B1-vs-SWS wording, ceiling scope, BA0 window, interaction CIs (DATA noise ignored), missing Fano script, Q6 I0
set, SESOI source — all fixed above. Verdict PASS_WITH_LIMITATIONS.
RT2 (`redteam/RT2_interpretation.md`): draft NOT_READY (15 wording fixes: Q5/Q7 errors, σ 6 over-reach, B1 inference from significance
differences, SESOI misuse, stratum-pattern evidence, decoder confound, zero pairs, Q8 power, "robust", model-vs-biology line, Fano
script); with fixes PASS_WITH_LIMITATIONS. All 15 applied. Both reviewers are separate model instances (limited independence), not
human review.
