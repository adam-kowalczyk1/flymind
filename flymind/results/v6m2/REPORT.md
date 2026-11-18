# V6m2 — Model DNa02-only factorial: does the model's DNa02 refractory block make synchronous intermediate input harmful? (2026-10-30)

**Status: exploratory, pre-registered. Verdict: PASS_WITH_LIMITATIONS** (RT-E replication, RT-F alternatives, RT-G statistics — all
PASS_WITH_LIMITATIONS; 28 required corrections applied, §6). MODEL-level computational ablations (ALIF; DATA downstream wiring). Not a
biological manipulation; DNa02 here is a model neuron; no claim about Drosophila.

## 1. Why and design
V6m's single-factor ablations left DNa02 refractoriness metric- and parameter-dependent, and two red-team factorials (post hoc) found that
removing the DNa02 refractory block reverses the effect of intermediate synchrony. V6m2 tests this with DNa02 as the ONLY free neuron:
LC10a and all 147 intermediates are clamped to recorded trains (from the REF replay of DATA or B1 LC10a trains), so every DNa02 variant
receives identical input. Intermediate input: M0 (unchanged), MCIRC (per-neuron circular shift), MASYNC (exact per-neuron counts in
300–1000 ms, uniform with ISI ≥ 4 ms). DNa02: REF (3 blocked 1-ms steps), T6 (6), T1 (1), T0 (0), T0B (0 + additive DNa02 bias
calibrated on separate seeds so that DATA × M0 matches REF on average), NOLEAK (leak term removed, block kept). Arms: MAIN (default; DATA +
B1 8 421 001–010; 7/8/9 mV), BA1 (b_a 1.0; DATA + B1 001–005; 9.5/10.5 mV), J025 (J0 0.25; DATA + B1 001–005; 7.5/8 mV); L/R; 8 reps. BA1
and J025 share noise (8 443 201–208), calibration seeds and B1 instances — robustness at two further settings, not independent
replication. Δt = gap(MASYNC) − gap(M0) (> 0: removing synchrony shrinks the B1 deficit = synchrony harmful). Primary: I = Δt(REF) −
Δt(T0B), Hz and log-ratio; CI = wider of nested hierarchical bootstrap and jackknife-t over reps (a crossed bootstrap gives the same
decisions, RT-G).
**Rate matching (corrected):** "rate-matched" holds only for DATA × M0 on the level average. MAIN b* −38 mV (per level: +21 % at 7 mV),
BA1 −34 mV (−20 % at 10.5 mV). **J025 is NOT rate-matched**: the calibration hit the −60 mV grid edge (T0B DATA × M0 169.8 Hz vs REF 103.6)
— its T0B is an "unmatched, partially biased t_ref 0". Under MASYNC the T0B rates are far below REF (MAIN DATA 47 vs 107 Hz; at 7 mV 1.0 /
0.4 Hz, 178 zero-rate B1 cells) — log metrics at that floor (MAIN 7 mV, BA1) are unreliable.
**Timeline (from file times; the "~15:35/~15:45" written in the protocol text are wrong clock estimates):** r1 sha 15:18:58; r1 smoke run
aborted (sampler failure; r1 `v6m2.py` sha d6fd9980 not preserved); r2 saved 15:21:30; r2 smoke run (scratchpad) 15:22–15:24 wrote rep-1
DNa02 npz 37 s before the analysis-script hash (15:24:37) — its values were not opened; the main rep 1 is bit-identical to it (RT-G);
calibration 15:24:37–15:26:05; jobs 15:26:05–15:33:01; 23 jobs, 0 errors. Checks in every run: M0×REF == REF replay, counts preserved,
MASYNC ISI ≥ 4 ms; Stage 1 28/28 after the run.

## 2. Results (Hz; CI = wider interval; ~288 statistics computed, ~60 reported, unadjusted unless stated)
| Arm | gap REF·M0 | Δt REF | Δt T6 | Δt T1 | Δt NOLEAK | Δt T0 | Δt T0B | **I = Δt(REF) − Δt(T0B)** (Hz; log) |
|---|---|---|---|---|---|---|---|---|
| MAIN | −20.7 (−24.4; −17.1) | +8.1 (+4.7; +11.6) | +8.7 | +6.6 (+1.9; +11.2) | +9.0 | −7.2 (−12.6; −1.8) | −13.0 (−16.1; −10.0) | **+21.2 (+17.3; +25.0); +0.55 (+0.48; +0.62)** |
| BA1 | −14.2 | +4.1 (+0.7; +7.5) | +4.6 | +0.4 (n.s.) | +3.0 (n.s.) | −9.4 (−13.3; −5.4) | −7.2 (−9.9; −4.5) | **+11.3 (+6.7; +15.9); +0.71** |
| J025 (T0B unmatched) | −15.7 | +6.2 (−0.9; +13.3) n.s. | +6.9 | +2.9 (n.s.) | +4.5 (n.s.) | −3.9 (n.s.) | −16.2 (−34.6; +2.3) n.s. | +22.4 (+7.2; +37.5); +0.35 |
Per level (Δt REF / Δt T0B / I T0B, Hz): MAIN 7 mV +3.3 / −1.3 / +4.5 (floor), 8 mV +5.8 / −14.9 / +20.7, 9 mV +15.3 / −22.9 / **+38.2
(+34.1; +42.3), log +0.44 (no floor)**; BA1 9.5 mV +2.2 / −0.5 / +2.7, 10.5 mV +6.0 / −13.9 / +19.9; J025 7.5 mV +8.5 / −5.6 / +14.1, 8 mV +4.0 /
−26.7 / +30.7. The effect grows with drive; I is not established at the lowest level of any arm; criterion (a) holds per level only at MAIN
9 and BA1 10.5.
Pre-registered decision (MAIN): (a) Δt(REF) > 0 ✓, (b) I > 0 in Hz ✓ and log ✓, (c) Δt(T0B) ≤ 0.5·Δt(REF) with CI upper < Δt(REF) ✓ →
**H-RS SUPPORTED in MAIN** (I positive for all 8 seeds, all 10 B1 instances, both sides; survives Bonferroni over 60 tests — RT-G).
Generalisation rule (I > 0, CI excl. 0, Hz) met in BA1 and J025; BA1 meets all MAIN criteria; J025 fails (a), is unmatched, its T0 and
MCIRC interactions include 0 and its I does not survive a 6-test Bonferroni.
Secondary: I with MCIRC: MAIN +18.2 (+15.1; +21.2), BA1 +10.9, J025 +7.9 (n.s.). I with T0 (no matching): MAIN +15.4 (+12.1; +18.6), BA1
+13.5, J025 +10.1 (n.s.). NOLEAK interaction: MAIN −0.9 (n.s.), BA1 +1.1 (n.s.), J025 +1.7 (+0.8; +2.5); with MCIRC two small interactions
exclude 0 with opposite signs (MAIN −1.5, J025 +2.6) → leak not required. T6 vs REF: n.s. in Hz but IL|T6 −0.06 / −0.08 / −0.045 (CIs
exclude 0) — on the log metric the dose order T0 < T1 < REF < T6 holds in all arms.
Shares (MASYNC-specific, with CIs): count share gap(MASYNC)/gap(M0) under REF MAIN 0.61 (0.48; 0.73), BA1 0.71 (0.51; 0.92), J025 0.60
(0.24; 0.97) → timing share 27–52 % (MAIN), 8–49 % (BA1), 3–76 % (J025) — a timing share, not identified as purely refractory. Under T0B the
count share is undefined (denominator CI includes 0). F(T0B) = 1 − gap(T0B)/gap(REF) = 81 % (MAIN) is specific to the additive-bias
control.

## 3. Red-team replication and falsification attempts (post hoc, exploratory)
- **RT-E (independent implementation, new B1 8 421 011–015, new seeds 8 498 501–504, own bias −40 mV):** I +22.1 (+15.4; +28.8) Hz,
  +0.63 log; all 5 instances +21.0…+23.2; a window-preserving MASYNC gives +23.8 (spike redistribution into the analysis window ruled
  out). Code audit: bias and NOLEAK touch DNa02 only; seeds source-specific; signs as reported.
- **RT-E F1 — the operating regime also sets the sign:** with the block INTACT, a −40 mV DNa02 bias makes synchrony beneficial (Δt log
  −0.22, CI excl. 0); about half of I(T0B) (46 % Hz, 58 % log) is reproduced by the bias shift alone. The interaction still holds at
  equal bias (+12.0) and at matched rate (+24.4).
- **RT-F — matching method:** with multiplicative-gain rate matching instead of additive bias, synchrony at t_ref 0 is ≈ neutral (Δt
  −1.3, (−6.7; +4.1)) and I +7.4 (−1.3; +16.1) includes 0; the gap removed falls from 81 % to ~22 % (gain grid ended at 0.60, 105 vs 88 Hz —
  not exactly matched; 3 B1 × 4 reps). Hard reset not required (t_ref 0 subtractive ≈ hard); holding v during the block not required
  (block with free integration Δt +8.9); "block alone vs block × charge loss" is surrogate-dependent. A count-matched surrogate (MTHIN:
  both trains thinned to equal per-neuron counts, own timing) reproduces the sign pattern and puts the timing share at ~57 % under REF;
  count-only + timing-only exceed the full gap (non-additive). DN τ_syn: harm under the block persists at 2/5/10 ms (+8.5/+6.1/+4.4); the
  no-block benefit disappears at τ_syn 2 ms. The t_ref 0 synchrony benefit is carried by 1-ms (= dt) doublets (B1 908 vs DATA 429).
- **T1:** Δt(T1) > 0 only in V6m2 MAIN; n.s. in BA1, J025, RT-E (+1.3, −6.7; +9.3) and RT-F (+3.9, −1.0; +8.8) → evidence for "1 step
  suffices" is inconsistent; T1 is not rate-matched.

## 4. Interpretation (MODEL level, corrected)
- **Robust:** with the model DNa02's refractory block in place, B1's more synchronous intermediate input yields fewer DNa02 spikes than
  the same spikes spread in time (Δt > 0 in MAIN and BA1; replicated with an independent implementation, new instances and seeds; at three
  τ_syn values; with two different surrogates). Removing the block removes this synchrony penalty (I > 0 in MAIN and BA1 under every
  matching scheme tested, though with gain matching only as a trend). Without the block, synchrony is **neutral to beneficial depending on
  how the operating point is set** (beneficial with additive bias or no matching; ≈ neutral with gain matching). The membrane leak is not
  required; the hard reset is not required.
- **Mechanism wording (corrected):** during the block the membrane integration is overwritten (v held at reset) while the synaptic
  current carries over, decaying with τ_syn — input arriving during the block is attenuated, not discarded. A "per-volley cap" is a
  description of this model rule; it was not measured at the volley level.
- **Not robust / withdrawn:** "the block is what turns synchrony into a disadvantage" as a sufficient statement (RT-E F1: the operating
  regime also sets the sign); "81 % of the gap removed by DNa02 refractoriness" (additive-bias specific; ~22 % with gain matching);
  "count 60–70 % / refractory 30–40 %" (surrogate-specific, non-additive); "1 blocked step suffices"; "generalises across 3 parameter
  sets" (BA1 yes; J025 unmatched and weaker).
- **Answer to the V6m question (model level):** the reduced DNa02 response to B1-like synchronous input involves an interaction between
  input synchrony and the DNa02 refractory block (H4) in a mean-driven operating regime, plus a count deficit already present in the
  intermediates (origin not causally tested; post-hoc evidence points to intermediate refractoriness). Adaptation and leak are not
  required. Nothing here is a statement about the fly.

## 5. Limitations
Effective n = 8 shared noise seeds on one DATA receiving network (B1 between-instance SD 0–0.4 Hz); effect concentrated at the highest
level of each arm; additive-bias rate matching is regime-changing and only level-averaged; J025 unmatched; dt = 1 ms resolution limits
"≥ 1 step" statements; MASYNC also removes per-neuron ISI/burst structure (MCIRC and MTHIN agree in sign); no multiplicity adjustment
beyond the RT-G Bonferroni check; red-team checks are post hoc with small n.

## 6. Red team
RT-E (`redteam/RT_E_replication.md`; seeds 8 498 501–599), RT-F (`RT_F_alternatives.md`; 8 498 601–604), RT-G (`RT_G_statistics.md`; RNG
8 498 701–703). All PASS_WITH_LIMITATIONS. Corrections applied: J025 not rate-matched (all three), conditional sign statement, bias-regime
finding, matching-method dependence, per-level table, floor disclosure, T6 log-metric, T1 inconsistency, shares with CIs, mechanism
wording, timeline erratum, both smoke runs, model language, NOLEAK MCIRC interactions, shared seeds in arms. Reviewers are separate model
instances (limited independence), not human review.

## 7. Files
`program_v5v41/V6m2_PROTOCOL.md` (r2), `v6m2.py`, `test_v6m2.py`, `v6m2_analysis.py`, `v6m2_figures.py`; `results/v6m2/` (raw/23 npz,
bias_calibration.json, analysis.json, analysis_stdout.txt, figures/V6m2_F1_interaction.png, config, stdout, run_done,
protocol_sha256_before_run.txt, redteam/RT_E, RT_F, RT_G + scripts).
