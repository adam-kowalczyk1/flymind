# V6 red team RT2: interpretation skeptic (2026-10-30)

Scope: claims in `results/v6/REPORT.md` §2–§4 (DRAFT), checked against `program_v5v41/V6_PROTOCOL.md` r1, `results/v6/analysis.json`,
`analysis_stdout.txt`, `closedloop.jsonl`, `calibration.json`, `openloop/<cfg>/*.npz`, `v6.py`, `v6_analysis.py`, `cl_runner.py`.
No existing file was modified. **No new simulation was run** (so no noise seeds from 8 495 601–699 were used for simulation). The
re-analyses below only re-read existing records. numpy RNG seeds 8 495 601–8 495 604 were used for my own bootstrap/permutation draws.
Interpreter: `/Users/admin/so101_fly_project/.venv/bin/python -I -B`, run from `/Users/admin/so101_fly_project`.
Everything I computed beyond `analysis.json` is post hoc and descriptive. It is labelled [RT2 re-analysis].

Re-analysis notes. Closed-loop contrasts use a cluster bootstrap over SWS instances (4000–5000 draws). B1−SWS contrasts resample scenes,
since B1 and SWS clusters are crossed, so they are approximate. Open-loop pointwise CIs reuse `v5v41_analysis.compare` (hierarchical) at
a single level.

---

## A. Numbers reproduced (no discrepancy)
- Every Δ and CI in the §2 table matches `analysis_stdout.txt` / `analysis.json`. So do the interaction contrasts (+0.54, +3.99, +3.66,
  −5.96), every closed-loop d and CI in the §3 table, the zero-pair counts, P (0.274 / 0.149) and Q8 (−0.119 / +0.190).
- I reproduced the post-hoc LC10a Fano column from the npz files (stimulated-side LC10a column 0, bins 50–99, 7–9 mV). BA1 25.8/55.4,
  TH8 15.1/44.6, J025 10.1/29.0, SG0 81.2/104.9, SG6 1.6/1.6, BA0 0.5/0.5. All 50 SWS instances give the same values ±0.2. **No script
  in the repository produces this column.** `v6_analysis.py` does not compute it, and `v6m*/v5v43*` compute related but different
  quantities. Reproducibility therefore currently depends on this review.

## B. Factual errors in §2–§4 (the text contradicts the repository's own numbers)

**B1. Q5 (REPORT:50–51) is false as stated.** The text says "in all 15 non-ceiling configurations the deficit is largest within ~3 mV
above DATA's threshold".
- The count is wrong. 16 configurations minus the 2 full-ceiling cells (BA0×TH6, BA0×J025) leaves 14, not 15.
- BA1 is a direct counterexample in the report's own table (REPORT:26). Its 9–12 mV Δ is −14.4 Hz against an own-window Δ of −5.7. The
  largest pointwise deficit is −19.8 Hz at 11.25 mV, 5.2 mV above I_th10 = 6.10 [RT2 re-analysis on `dn_curve_*`].
- TH8 is borderline. Its peak deficit is −35.6 Hz at 10.5 mV (own window 7.10–10.10), and its 9–12 Δ (−21.1) is larger than its own Δ
  (−15.0).

**B2. Q7 (REPORT:56) leaves out open-loop "control stronger" cases.** Pointwise SWS > DATA with CI excluding 0 [RT2, hierarchical
bootstrap at a single level]:
- TH6: +11.4 Hz at 8.75 mV (4.4; 17.4)
- SG0: +10.9 at 10.75 (9.2; 12.5)
- SG6: +5.4 at 6.5 (3.1; 8.7)

These come on top of J025 (+21.3 at 9.75, CI 15.7; 30.7) and D0 (+8.9 at 10.5, CI 5.1; 13.1). They are pointwise and unadjusted (33
levels × 16 configurations), but the text names only J025 and D0. Q3's statement that the reversal "moves into the 9–12 window"
(REPORT:49–50) is one reading. The same feature also appears at 8.75 mV under TH6 and at 10.75 mV under SG0. A single "moving
reversal" is an interpretation, not a measurement. No shift was estimated.

**B3. "absent at σ 6" (REPORT:55, 63, 100–101) over-reaches.** Under SG6 the window averages are ~0, but the difference is not:
- pointwise Δ DNa02 is −2.9 Hz at 6.0 mV (CI −5.3; −0.7) and +5.4 Hz at 6.5 mV (3.1; 8.7), a sign-changing difference that the window
  average cancels;
- Δ G is +3.9 Hz/mV at I0 9 (CI +2.4; +5.6, +10 % of DATA's 38.3) and +3.4 at I0 10 (+0.9; +6.0) (`analysis.json`
  openloop.SG6.families.SWS.G_small).

The defensible wording is "the window-averaged DNa02 difference is not detected at σ 6. Equivalence is not shown, and pointwise and
gain differences remain."

**B4. "Family X (B1) follows SWS within ~1–2 Hz in every non-D0 configuration" (REPORT:43) is false.** Own window, B1 vs SWS:

| Config | B1 | SWS | Gap | B1 share of SWS deficit | CIs |
|---|---|---|---|---|---|
| TA100 | −10.3 | −13.8 | 3.5 Hz | — | non-overlapping |
| BA0×TH8 | −6.4 | −10.6 | 4.2 | 60 % | non-overlapping |
| BA0×J015 | −3.3 | −6.4 | 3.0 | 52 % | non-overlapping |
| BA025 | −13.8 | −16.2 | 2.4 | — | — |

At 9–12 mV: J025 +10.2 vs +7.3, and TH6 +2.0 vs −0.4. So the "LC×LC block carries ~94 %" locus from V5 v4.2 (D0 only) does not
transfer to b_a = 0 or τ_a = 100. REPORT:90 nevertheless uses "~94 %" as a property of B1 in the closed-loop discussion. In V6 the B1
share of the SWS own-window deficit is 52–103 % across configurations (CL configurations: BA0 79 %, BA1 96 %, TH6 90 %, TH8 100 %,
J015 96 %, J025 88 %; no D0 cell).

**B5. "B1 and SWS differ in TH8 S2 and J015" (REPORT:91–92) commits the difference-in-significance fallacy, and it names the wrong
cells.**

Direct paired contrast, d_B1 − d_SWS = err(SWS) − err(B1), same scenes [RT2]:

| Cell | Contrast (CI) | Report says |
|---|---|---|
| TH8 S2 | −0.13 (−0.43; +0.17) | differ |
| J015 S1 | −0.05 (−0.19; +0.07) | differ |
| J015 S2 | +0.02 (−0.19; +0.24) | differ |
| **D0 S2** | **+0.46 (+0.20; +0.73)** | B1 "CIs include 0" |
| **J025 S1** | **−0.17 (−0.29; −0.06)** | — |
| **SG6 S1** | **−0.24 (−0.39; −0.08)** | — |

The cells the report says differ show no difference. The cells where B1 and SWS actually differ are D0 S2, J025 S1 and SG6 S1. The D0
S2 result is the informative one. B1 has the SWS-like open-loop deficit at D0 (V5 v4.2: −16.4 vs −17.4 Hz, 6–9 mV) but **half the SWS
closed-loop S2 effect**. That is a direct, within-D0 dissociation of the open-loop deficit from the closed-loop d, and it is stronger
evidence for the §4 "not a predictor" point than Q8. The report misses it.

**B6. "same sign as SWS in 6/8 × 2 cells" (REPORT:90).** The count is 13/16. Signs differ in BA0 S1, J025 S1 and SG6 S1. The agreement
is also not independent evidence. d_SWS and d_B1 share the DATA term (scene-level r = 0.23–0.75), so agreement in sign is partly
guaranteed by construction. Report the paired B1−SWS contrast instead.

**B7. "SWS Fano 2–3× DATA" (REPORT:64).** D0 is 39.2/11.3 = 3.5×. Write "2–3.5×".

**B8. The zero pairs are mis-described (REPORT:88–89, 80).** They are not generic "far scenes". In D0, BA0, BA1, J015 and J025 they are
the S2 scenes with small initial azimuth (|az0| ≤ 9.0°) where no network moves (dead zone). In every case all three networks did not
move. The error equals |az0| and d = 0 by construction. TH8's 46 S2 zeros extend to |az0| = 19.1°. TH6 has 4 and SG6 has 0 zero pairs,
so "medians ~0 in S2 for every configuration … many identical-error pairs" is wrong for SG6 (0 zeros, median +0.009) and TH6 (median
+0.109 against a mean of +0.119; the median is not ~0 relative to the mean). The "S2 means carried by a minority of scenes" claim is
supported: in D0 S2, 10 of 80 scenes contribute −42.1 of the −53.2 total, while 40 negative / 20 positive / 20 zero. Keep the claim and
add these numbers.

**B9. Pairs where only one network moved.** Protocol §5 requires reporting them. The values are 0–2 per cell (`analysis.json`
only_data_moved / only_ctrl_moved), but REPORT §3 omits them. Add one line.

## C. Over-reach and wording

**C1. "robust" (REPORT:99–101).** The design varies one factor at a time by ±1 step around a single default, plus two 2×2 blocks that
the report itself declares uninterpretable because of the ceiling. That shows local sign consistency, not robustness. Across the "robust"
range the own-window deficit varies 3-fold (−5.7 to −16.8 Hz) and the 6–9 mV deficit 3-fold (−5.4 to −15.9). In the combination cells
it shrinks to −4.8 (BA0×TH6) and −0.3 (BA0×J025), partly ceiling-driven. It disappears with σ, a free parameter that no data constrains.
The default σ 2 gives a membrane SD of ≈ 0.32 mV (protocol line 19), so the effect lives in a low-noise regime. Scale is also an issue:
absolute Hz deficits are compared across configurations whose DATA maxima range 34–250 Hz (TA1000 34, BA1 85, BA0 250). Relative to
DATA's own-window rate the deficit is −3 % (BA0) to −26 % (TH8) [RT2].
Suggested wording: "sign-consistent (SWS < DATA near DATA's threshold) in every one-factor variation of b_a (0–1), gap (6–8 mV), τ_a
(100–1000 ms) and J0 (0.15–0.25), with 3-fold variation in size; not detected in window averages at σ 6 mV; joint variation only in two
ceiling-confounded 2×2 blocks."

**C2. The post-hoc synchrony observation (REPORT:62–66, 100–101) is presented as stronger than it is.**
- "absent exactly where the LC10a synchrony difference is absent" rests on one configuration (SG6).
- It is contradicted by BA0: Fano 0.5 / 0.5, equal, yet an own-window deficit of −8.4 Hz with CI (−9.6; −7.3). The report removes BA0
  with a post-hoc window argument (REPORT:41–42). That is special pleading unless the Fano is re-measured in BA0's deficit range (5.75–6.5
  mV) and reported.
- Among the configurations with a synchrony difference the dose-response is not monotone. BA1 has a 2.1× Fano ratio and the smallest
  deficit (−5.7). SG0 has a 1.29× ratio and a −7.7 deficit.
- There is a common-cause alternative. Raising σ adds independent per-neuron noise, which both decorrelates population spiking (lower
  Fano, trivially) and linearises/dithers the f–I curves (DATA I_th10 falls from 6.02 to 4.96 mV). That second effect can wash out any
  recurrent-structure effect on threshold crossing whether or not timing carries it. "Consistent with the V5 v4.3 timing account" should
  be "also consistent with noise dominance masking recurrent structure; the two are not distinguished here (causal test: V6m)". Fano
  values have no CI (10 SWS instances, one DATA network, 4 reps).
- §4 bullet 1 joins the post-hoc finding to the pre-registered model claim in one sentence. Move it to a separate "post hoc,
  hypothesis-generating" bullet.

**C3. SESOI 0.5° (REPORT:86–87, 102).**
- Source: the V6 protocol defines no SESOI. The 0.5° whole-CI rule comes from `V5v41_PROTOCOL.md:67`, and V5 v4's H1 table in
  `VALIDATION_PLAN.md:364` uses 1°. Cite the source and state that it is inherited, not pre-registered for V6.
- Symmetric misuse: "small (|d| ≤ 0.66°, none shown > SESOI)" uses absence of a supra-SESOI demonstration as evidence of smallness. Only
  cells whose CI lies inside ±0.5° are shown small: SWS S1 BA0, TH6, J015, J025, SG6 and SWS S2 TH6, SG6 (7/16). The other 9/16 are
  **indeterminate** relative to SESOI. Their CIs reach −1.02 (D0 S2), +0.95 (BA1 S1), −0.68 (J015 S2), +0.64 (J025 S2), +0.62 (BA0 S2),
  +0.59 (TH8 S1), −0.57 (TH8 S2, BA1 S2) and +0.55 (D0 S1). "|d| ≤ 0.66°" quotes point estimates.
- Power context: V5 v4 had 150/300 scenes per stratum, V6 has 40/80. The V6 CIs are roughly 2× wider, so many "CI includes 0" cells are
  underpowered rather than null.
- Absolute degrees on very different baselines: DATA S2 error ranges 0.93° (SG6) to 7.75° (TH8). −0.66° is 21 % of D0's DATA S2 error,
  and 4× P's whole S2 error.

**C4. "the V5 v4 S1/S2 pattern is a property of the default parameter set (and two others: BA1, J015)" (REPORT:102–103).**
- Wrong evidence: the claim is built from separate significance per stratum. The V5 v4 pattern is a stratum × network interaction. The
  direct contrast d_S1 − d_S2 [RT2 cluster bootstrap] is:
  - positive with CI excluding 0 in **D0 +1.00 (0.59; 1.40), BA1 +0.92 (0.52; 1.31), J015 +0.55 (0.24; 0.89) and also TH8 +0.51
    (0.05; 0.99)**;
  - **reversed in TH6 −0.31 (−0.54; −0.08)**;
  - indistinguishable from 0 in BA0, J025 and SG6.

  So the pattern appears in 4/8 configurations including TH8, not "default + two".
- Heterogeneity is better shown directly. The scenes and SWS pairings are identical across configurations (common random numbers), so
  config − D0 contrasts are paired [RT2]:
  - S2 differs from D0 for BA0 +0.89 (0.42; 1.37), TH6 +0.78 (0.42; 1.13), J025 +1.00 (0.49; 1.56), SG6 +0.75 (0.40; 1.10) and
    TH8 +0.42 (0.00; 0.83);
  - S1 differs for TH6 −0.52 (−0.74; −0.29) and J025 −0.25 (−0.47; −0.03);
  - BA1 and J015 are not distinguishable from D0 in either stratum.

  This supports "parameter-dependent" better than the significance counts do. It also shows BA1 and J015 are consistent with D0, not
  "two others" with their own property.
- "not a general property of DATA vs SWS wiring": "general" here means general over 8 unconstrained model parameter sets. Say so.
- "D0 reproduces the V5 v4 stratum pattern on new scenes" (REPORT:82). Three things are new: scenes, SWS instances (V5 v4.1
  8 410 001–050 instead of the V5 v4 instances) and decoder calibration (slope 496.5 vs V5 v4 492.1; seeds 8 601 001–003). Listing all
  three makes the replication stronger and more honest. Also give the magnitudes: S1 +0.33 vs +0.51, S2 −0.66 vs −0.52.

**C5. Decoder recalibration is a confound across configurations, and the report understates it (REPORT:110–112 lists it only as a
limitation).**
- The decoder is fitted to DATA in each configuration and then imposed on SWS/B1. d therefore measures (network, DATA-tuned decoder)
  pairs, and DATA always runs at its own calibration point while SWS runs off it.
- Slopes range 177–554 Hz/rad. Post hoc, the decoder slope ranks the closed-loop d better than the pre-registered open-loop predictor
  does: Spearman(slope, d) = −0.76 (S1) and +0.71 (S2), against −0.12 / +0.19 for Q8's x [RT2, n = 8, driven largely by BA1's 177].
- A competing account for the S1+/S2− pattern needs no "structure" at all. A network with lower effective gain than the calibration
  network overshoots less on strong-drive (S1) scenes and under-drives on weak-drive (S2) scenes. Overshoot difference DATA − SWS in S1:
  D0 +0.45°, BA1 +1.09°, TH6 −0.25° (sign follows d).
- At D0 the V5 v4 per-SWS calibrations were ≈ 0.99 × DATA (`results/v5v4/post_sws_slopes.txt`), so the confound may be small there. It
  is unmeasured in the other configurations because SWS was never calibrated per configuration.
- Add to §3/§4: "cross-configuration differences in d are confounded with decoder slope and with DATA's baseline error (0.74–7.75°); they
  cannot be attributed to the ALIF parameter acting on the structure difference alone."

**C6. Q8 with n = 8 (REPORT:94–96, 105).**
- "does NOT follow" claims a negative from a test with almost no resolving power. The critical |ρ| for exact two-sided p < 0.05 at n = 8
  is ≈ 0.71. Exact permutation p is 0.79 (S1) and 0.67 (S2). The bootstrap CIs of ρ are (−0.97; +0.68) and (−0.73; +0.85) [RT2].
- The x variable has little leverage: 7/8 values lie in −5.7 to −16.8 Hz, and SG6 is the only point near 0.
- The analysed quantity is not the protocol's Q8 quantity. Q8 (protocol line 9) asks about the closed-loop interaction (S1 vs S2); the
  analysis correlates each stratum separately. Using d_S1 − d_S2 gives ρ = −0.12 (same conclusion, but it should be the reported
  statistic).
- The result is fragile to scaling. With the open-loop Δ expressed relative to DATA's own-window rate, ρ becomes −0.62 (S1), +0.69 (S2)
  and −0.60 (S1−S2), near the critical value [RT2, post hoc].
- Wording: "No monotone association was detected (n = 8; ρ CI spans roughly −0.9 to +0.8). The data neither support nor exclude a
  moderate-to-strong link." The within-D0 B1 dissociation (B5) is the better evidence for "the open-loop deficit alone does not determine
  d". "SG6 is the only configuration where both are ~0" is true but uninformative, since σ 6 also changes DATA's baseline (S2 0.93°).

**C7. Multiplicity.** The report says "CIs descriptive" (REPORT:110) but bolds individual cells and builds claims on them, such as TH6
"control better" in S1 and J025 S2. Closed loop alone has 8 × 3 × 2 = 48 CIs, and open loop several hundred. The pre-registered
narrow-regime rule is fine: 4/8 against ≈ 0.4 expected under a global null. Single cells are not. Add: "individual bold cells are
unadjusted; with ~48 closed-loop CIs ≈ 2–3 exclusions of 0 are expected by chance."

**C8. Interaction contrasts' CIs are anti-conservative (REPORT:57–58).** `v6_analysis.py:91–107` subtracts the fixed DATA mean curve
and bootstraps SWS instances only. The 4-rep noise of the four DATA references is ignored (cf. V5 v4.2 RT2(d), ±2–3 Hz). The CIs (e.g.
+0.05; +1.0) are therefore too narrow. Since the report already calls them uninterpretable, add only "CIs ignore DATA rep noise".

**C9. P comparison (REPORT:79–80).** "DATA itself is far worse than P in every configuration" is numerically true (J015 S1 0.74 vs 0.27
is 2.7×; elsewhere 6–50×). P, however, is an engineering controller with its own calibration (`L.calibrate_p`), run once with the D0
seed set. It is a ceiling reference, not a comparator for structure. Keep it, and say "reference only; not part of any DATA/SWS
inference".

**C10. Q6 implementation choice.** The protocol §5 G range is I0 5–9; Q6 is implemented at I0 6–8 (`v6_analysis.py:82`). The report
states "I0 6–8" (REPORT:53), but it is an unregistered choice. Flag it as such. It does not change the verdict: SG6 fails at I0 8, and at
I0 9 under the full range.

## D. Model vs biology
- §4 correctly labels the main claim "MODEL-level" and says "Cannot conclude … anything about the fly" (REPORT:99, 104). I found no
  sentence asserting fly biology.
- Residual risks:
  - "LC10a synchrony", "DNa02 at the refractory ceiling" and "LC10a fires regularly" name model populations with fly cell-type names.
    Add once in §2: "LC10a/DNa02 denote model populations built from connectome cell types".
  - The parameter sweep varies quantities (b_a, σ, τ_a) that the report itself calls "design choices without data" (protocol line 16).
    Every "regime" in §2–§4 is a region of model parameter space, and no range is claimed to be the biological one. Say so in §4.
  - "noise desynchronises LC10a" (REPORT:65) describes the model.

## E. Alternative explanations to state in §4
1. **Noise dominance (common cause)** for the SG6 co-disappearance of the deficit and the Fano difference (C2).
2. **Decoder/gain mismatch** (DATA-tuned decoder) for the S1+/S2− pattern and its configuration dependence, with no structure-specific
   mechanism needed (C5).
3. **Baseline operating point / dead zone**: d is bounded by DATA's own error and by the shared dead zone (identical zero pairs). Loops
   that barely work (BA0 5–6°, TH8 S2 7.75°) or work very well (SG6 S2 0.93°) compress d mechanically.
4. **Ceiling (250 Hz)** for every b_a = 0 cell (acknowledged).

## F. Verdict: **NOT_READY**
The underlying data and the pre-registered computations are sound, and §A reproduces them. Several §2–§3 statements, however,
contradict the repository's own numbers (B1, B2, B4, B5, B6, B8), and the central §4 interpretations rely on significance-difference
reasoning and on SESOI non-exceedance read as smallness (C3–C6). These are wording and reporting fixes plus a few already-computed
contrasts. No new simulation is needed. With the fixes below the report would be PASS_WITH_LIMITATIONS.

## G. Required wording fixes
1. REPORT:50–51 (Q5) → "In 12 of 14 non-ceiling configurations the largest deficit lies near DATA's threshold. Exceptions: BA1 (largest
   at ~11 mV, 9–12 Δ −14.4 vs own −5.7) and TH8 (peak at 10.5 mV, just above its own window)."
2. REPORT:56 (Q7) and :49–50 (Q3) → list TH6 (+11.4 Hz at 8.75 mV), SG0 (+10.9 at 10.75) and SG6 (+5.4 at 6.5) as pointwise
   SWS > DATA levels (unadjusted). Replace "moves into the 9–12 window" with "a high-drive SWS > DATA crossing appears at 8.75–10.75 mV in
   D0, TH6, J025 and SG0; its shift with parameters was not estimated."
3. REPORT:55, 63, 100–101 → replace "absent at σ 6" with "not detected in window averages at σ 6 (own −1.0; +1.7 Hz). Pointwise
   (6.0 / 6.5 mV) and G (I0 9–10, +10 %) differences remain. Equivalence not shown."
4. REPORT:43 → "B1 is within ~1–2 Hz of SWS in most configurations but not in TA100 (−10.3 vs −13.8), BA0×TH8 (−6.4 vs −10.6) or
   BA0×J015 (−3.3 vs −6.4)." REPORT:90 → drop "~94 %" or write "~94 % at D0 (V5 v4.2); 52–103 % across V6 configurations".
5. REPORT:90–92 → replace the B1-vs-SWS sentence with the paired contrasts: B1 − SWS at D0 S2 +0.46 (+0.20; +0.73), J025 S1 −0.17, SG6
   S1 −0.24; TH8 S2 and J015 not different. Add "at D0, B1 reproduces the open-loop deficit but only about half of the SWS S2
   closed-loop effect". Fix "6/8 × 2" to "13/16", noting the shared DATA term.
6. REPORT:64 → "2–3.5×". REPORT:62–66 → add the BA0 counterexample, the non-monotone BA1/SG0 cases and the noise-dominance alternative.
   Remove the post-hoc clause from the §4 model claim and give it its own "post hoc" bullet.
7. REPORT:86–87, 102 → replace "small (|d| ≤ 0.66°)" with "7/16 cells are shown within ±0.5°; 9/16 are indeterminate (CIs reach
   1.0°); none is shown beyond 0.5°". Cite the SESOI source (V5v41_PROTOCOL:67; not in the V6 protocol). Note the reduced n vs V5 v4
   (40/80 vs 150/300).
8. REPORT:82, 102–103 → base the stratum-pattern claim on the S1 − S2 contrast (D0, BA1, J015, TH8 positive; TH6 reversed; BA0, J025,
   SG6 ~0) and on the paired config − D0 contrasts. Replace "a property of the default parameter set (and two others)" with "present in
   4/8 tested model parameter sets, reversed in 1, absent in 3; differs from D0 for BA0, TH6, J025 and SG6". In REPORT:82, list the new
   SWS instances and decoder calibration and give the magnitudes.
9. §3/§4 → add the decoder-slope / DATA-baseline confound (C5) as an interpretive caveat next to the configuration-dependence claim, not
   only in §5.
10. REPORT:88–89 → zero pairs = S2 scenes with |az0| ≤ 9° (TH8 ≤ 19°) where no network moved. "Medians ~0" does not hold for TH6 or SG6.
    Add the only-one-moved counts (0–2 per cell).
11. REPORT:94–96, 105 (Q8) → "no monotone association detected; n = 8 gives no power to exclude a moderate-to-strong one (exact p
    0.79 / 0.67; ρ CIs ≈ −0.9 to +0.8)". Report the S1 − S2 version per protocol Q8. Point to the D0 B1 dissociation as the stronger
    evidence.
12. REPORT:99 → replace "robust" with "sign-consistent under one-factor variation; magnitude varies 3-fold" (C1). State that σ, the
    parameter that removes the effect, is unconstrained by data.
13. REPORT:57–58 → "interaction CIs ignore DATA rep noise (anti-conservative)".
14. §2 → one line saying that LC10a/DNa02 denote model populations, and that every regime is a model-parameter regime.
15. Add the script (or the inline code) that produces the Fano column, so it can be reproduced without this review.
