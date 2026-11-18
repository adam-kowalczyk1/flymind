# V6m — Mechanistic dissection of the DNa02 response to synchronous LC10a input: report (2026-10-30)

**Status: exploratory computational ablations, completed. Verdict: PASS_WITH_LIMITATIONS — after correction.** My draft interpretation
was FALSIFIED by the red team (RT-B, RT-C, RT-D NOT_READY; RT-A PASS_WITH_LIMITATIONS) and rewritten; its decisive open point was then
tested in the pre-registered follow-up **V6m2** (`results/v6m2/REPORT.md`). §8 lists what changed.
Everything below is a property of a MODEL (ALIF, J0 0.2, b_a 0.5, σ 2 mV, t_ref 2.2 ms, τ_a 300 ms, dt 1 ms; DATA downstream wiring from
the MaleCNS connectome). "LC10a", "intermediates", "DNa02" are model populations named after connectome cell types. Ablations are
computational; none is a biological manipulation; nothing here is a claim about Drosophila.

## 1. Question, design, execution
Is the lower DNa02 response to B1-like synchronous LC10a input (V5 v4.3: −19.9 Hz replay gap; ~90 % removed by destroying LC10a
cross-neuron alignment) caused by (1) DNa02 refractoriness, (2) adaptation, (3) intermediate-layer temporal dynamics, (4) an
interaction, (5) something else? Protocol `program_v5v41/V6m_PROTOCOL.md` (sha b8cd8935…, frozen before the smoke run).
Framework: the validated v4.3 replay (LC10a of the DATA network clamped to recorded trains of DATA or B1 instances; 7/8/9 mV; L/R; 8 noise
reps). Single-factor ablations: Exp 1 DNa02 t_ref ∈ {0, 1, 2, 2.2 = REF, 4, 6} ms (= 0, 1, 2, 3, 4, 6 blocked 1-ms steps; refractoriness
holds v at reset and discards input during the block, the synaptic current keeps evolving); Exp 1b intermediate t_ref {0, 4}; Exp 1c DNa02
t_ref {0, 6} with intermediates clamped to their REF trains (then DNa02 is the ONLY free neuron: 424 = 275 LC10a + 147 intermediates + 2
DNa02 — a single-neuron integration test on recorded input); Exp 2 b_a {0, 0.25, 1} in DNa02 only / intermediates only; Exp 3
intermediates clamped (M0 identity, MCIRC circular shift, jitter ±2/5/20 ms, rate-matched Bernoulli MPOIS); Exp 4 synthetic LC10a
trains with the DATA source's per-neuron counts (exact in 300–1000 ms) and graded shared-event alignment (10 Hz events, placement
probability p 0–1; 40 Hz events p .35/.7/1) under REF, DNa02 t_ref 0, DNa02 b_a 0, intermediate t_ref 0; Exp 5 (a) DNa02 subtractive
reset with t_ref 0 (with t_ref > 0 a subtractive reset is a null manipulation in this engine — verified), (b) intermediate→DNa02
inhibition removed. Reference LCIRC = LC10a circular shift. Replication: noise 8 442 001–008, B1 8 421 011–020. Manipulation RNG seeds
depend only on rep (8 realisations shared across sources — paired design; surrogate variability not in the CIs). Post hoc Exp 6
(addendum A1, written after the results): DNa02-weighted intermediate input.
Run 14:43–14:56, 25 jobs, 0 errors; analysis script hashed before results; one post-hash bug fix (ordering only). Disclosure: the smoke
run (protocol frozen) used rep 1 of the main seeds and B1 8 421 001 (~1/80 of the main data seen before the full run).

## 2. Validation (all passed; RT-A independently re-implemented the engine: 24/24 free runs and 240/240 replays identical)
T1 engine identity with `alif.ALIF.step` / `v5v43.step_clamped`; T2 each condition changes only its intended parameter entries (29
conditions); T3 REF replay == v4.3 V0 for all 11 sources × 3 levels × 2 sides × 8 reps; T4 M0 clamp == REF rasters in every run; T5 clamp
mechanics (forced spikes == forcing array) in every non-LC-manipulated run — source fidelity itself rests on T3 and REF == free run;
Exp 4: 528 unique synthetic trains (2112 checks), per-neuron counts exact and ISI ≥ 4 ms inside 300–1000 ms (in the 500–1000 ms analysis
window LC10a counts deviate −6.5…+1 %); jitter losses MJ2 ≤ 0.4 %, MJ5/MJ20 1.3–2.9 %; MJ/MPOIS create intermediate ISIs < 4 ms
(5–15 % of spikes) that REF never has; MCIRC keeps per-neuron counts in 300–1000 ms (500–1000 ms: −2.4 % DATA / −3.4 % B1). Exp 6
re-simulation reproduces the main DNa02 counts (11/11). Stage 1 28/28 before/after.

## 3. Results (DNa02 ipsi, 500–1000 ms, mean of 3 levels × 2 sides; gap = B1 trains − DATA trains; F = 1 − gap/gap(ref); CI95 paired
hierarchical bootstrap. Precision is set by the 8 noise reps of the single DATA receiving network: B1 instances are almost identical
(between-instance SD ≈ 0.9 Hz main, ≈ 0 replication) and reps are crossed with source by common seeds; with n = 8 percentile intervals
under-cover (RT-B: under jackknife-t the main-set E1/E1c t_ref 0 F intervals include 0). ~45 unadjusted intervals.)
| Condition | DN DATA / B1 [Hz] | Gap (CI) | F abs (CI) — pre-registered rule | F on relative gap (RT-B/RT-D, secondary metric) | Replication F abs / rel |
|---|---|---|---|---|---|
| REF | 86.5 / 66.6 | −19.9 (−21.9; −17.9) | — | — | gap −18.8 |
| LCIRC (LC10a circ. shift) | 105.4 / 104.3 | −1.1 (−2.8; +0.4) | **+0.94 (+0.87; +1.02) removes most** | — | +0.80 removes most |
| E1 DN t_ref 0 | 165.9 / 150.9 | −15.0 | +0.25 (+0.08; +0.42) contributes | +0.61 (+0.52; +0.70) | +0.35 |
| E1 DN t_ref 1 / 2 | 125.4/102.4 · 102.1/80.0 | −23.0 · −22.2 | −0.16 · −0.11 (enlarge, absolute Hz only) | +0.20 · +0.06 | — |
| E1 DN t_ref 4 / 6 | 75.2/57.4 · 60.2/45.7 | −17.7 · −14.5 | +0.11 · +0.27 (absolute Hz only) | −0.03 · −0.05 | +0.26 (t6) |
| E1c DN t_ref 0, intermediates clamped | 164.5 / 148.9 | −15.6 (−19.9; −11.7) | +0.21 (+0.06; +0.37) contributes | **+0.59 (+0.51; +0.67) — would meet "removes most"** | +0.33 / +0.65 |
| E5a t_ref 0 + subtractive reset (vs E1 t_ref 0) | 197.0 / 182.2 | −14.8 | +0.01 (−0.10; +0.18) n.s. | +0.17 (+0.08; +0.31) | +0.01 / +0.17 |
| E2a DN b_a 0 | 103.7 / 80.9 | −22.8 | −0.15 (−0.20; −0.09) enlarges | +0.04 (+0.01; +0.09) | −0.21 / +0.00 |
| E2b intermediate b_a 0 | 108.4 / 89.0 | −19.5 | +0.02 (−0.06; +0.11) n.s. | +0.22 (+0.17; +0.28) | −0.03 / +0.19 |
| E1b intermediate t_ref 0 | 93.9 / 66.7 | −27.2 | −0.37 (−0.40; −0.33) enlarges | −0.26 | — |
| E3 MCIRC (vs M0) | 105.3 / 92.5 | −12.8 | +0.36 (+0.28; +0.42) contributes | +0.47 | +0.23 |
| E3 MJ2 / MJ5 / MJ20 | | −19.5 · −18.4 · −11.7 | +0.02 n.s. · +0.07 · +0.41 | | — |
| E3 MPOIS | 104.2 / 94.1 | −10.1 | +0.49 (+0.35; +0.66) contributes | +0.58 | — |
| E5b no intermediate→DN inhibition | 90.1 / 69.2 | −21.0 | −0.05 enlarges (weak test: ~85 % of that inhibition is contralateral and weakly driven) | −0.01 | — |
Per level (RT-B): the absolute-metric H1 outcome holds at 7/8/9 mV; MCIRC is null at 8 mV in both sets (carried by 9 mV); E2b changes
sign across levels; F at 7 mV is ill-defined (gap −8.7 Hz). E1 vs E1c (feedback): paired difference +0.65 ± 0.88 Hz (rep +0.42 ± 1.12) —
DN→intermediate feedback does not matter for the t_ref effect.
Mechanism measurements: DNa02 ISIs ≤ 4 ms REF DATA 20 % vs B1 41 %; adaptation state 12.7 vs 10.5 mV; intermediate rate 13.2 vs 12.1 Hz;
intermediate pairwise correlation (5 ms) 0.17 vs 0.41. First-spike latency (mean 41.9 ms; 55.8/38.9/31.0 ms by level) is unchanged by
DN-local ablations and by 300–1000 ms manipulations by construction; it differs between sources by ≤ 2 ms in 128/528 runs — uninformative.
**Exp 4 (synthetic synchrony, DATA network only, unit = rep, n = 8; F2).** DNa02 falls with alignment under every dynamics
(level-pooled; not monotone at every level). OLS slope vs Fano10: REF −0.91 (−0.97; −0.84), DN t_ref 0 −0.68 (ratio 0.59–0.90;
normalised by mean rate ≈ 0.46–0.51), DN b_a 0 ratio 1.20–1.26 (normalised ≈ 0.94–0.96: rate scaling), intermediate t_ref 0 ratio 1.29–1.36
(survives normalisation). Slopes are range-dependent (convex curves): over the DATA–B1 range the t_ref 0 / REF ratio is 0.87 (abs) / 0.54
(rel). Per level: DN t_ref 0 abolishes the synchrony effect at 7 mV but not at 9 mV. The surrogate (one family: shared Poisson events
±1 ms; realised event participation ≤ ~0.6 at 10 Hz, ~0.86 at 40 Hz) reproduces 70–93 % of the real gap depending on the synchrony
axis; the real trains lie on the REF curve only on the Fano5/10 axes (6–18 Hz below it on χ², pairwise r, volley, CV) — the real trains
carry structure the surrogate lacks. 40 Hz vs 10 Hz events: at equal Fano/χ²/r/volley score the 40 Hz trains are MORE harmful, at equal
placement probability p LESS harmful — no single synchrony measure is sufficient.
**Exp 6 (POST HOC).** Rate-weighted excitatory intermediate drive to DNa02, B1 vs DATA: REF −10.4 % (CI excl. 0; mostly a global
intermediate count deficit, n_mid −7.7 %), LCIRC −1.8 %, intermediate t_ref 0 +1.7 % (n.s.) with +51 % inhibitory drive for B1. Descriptive.

## 4. Interpretation (corrected after red team; V6m2 adds the decisive test)
- **Pre-registered rule outcomes (absolute gap, primary):** LCIRC removes most (robust: also at TH8, BA1, J025 per RT-C); DNa02
  refractoriness "contributes" (not "removes most") → H1 not supported as the SOLE primary cause by the pre-registered rule; DNa02 and
  intermediate adaptation do not remove the gap (H2 not supported); intermediate timing contributes (H3, 23–36 %; MPOIS 49 %).
- **But the H1 verdict is metric- and parameter-dependent (RT-B/C/D):** on the relative gap DNa02 t_ref 0 removes ~60 % (main and
  replication); a rate-matched check removes ~75 % (RT-D, exploratory); at b_a 1.0 t_ref 0 removes 76 % even of the absolute gap, at J0
  0.25 it enlarges it (DNa02 driven to ~290 Hz). The absolute-Hz "non-monotone t_ref dose–response" is an operating-point effect: in
  relative terms the gap shrinks monotonically as the block is shortened (−0.24 at 6 ms → −0.09 at 0) and saturates at ≥ 2–3 blocked
  steps. DNa02 adaptation effects are rate scaling (relative F ≈ 0).
- **Interaction (H4) — the key finding, from the red team and then V6m2:** with the model DNa02's refractory block removed, destroying
  intermediate synchrony no longer shrinks the B1 − DATA gap (RT-B +11.1 Hz, RT-D +14.4 Hz interaction; V6m2 pre-registered with fresh
  seeds: +21.2 Hz (+17.3; +25.0), log +0.55 in MAIN; BA1 +11.3; independent re-implementation +22.1). With the block, synchronous
  intermediate input is harmful; without it, synchrony is neutral to beneficial depending on how the operating point is set (additive
  bias vs gain matching, V6m2 RT-E/RT-F), and the operating regime itself can flip the sign (a −40 mV bias with the block intact makes
  synchrony beneficial). Removing the membrane leak or the hard reset does not change it. My draft claims "a DNa02 timing route that
  survives t_ref 0" and "leaky integration" were wrong and are withdrawn.
- **Current best account (MODEL level, V6m + V6m2):** LC10a synchrony (set by LC×LC wiring) reduces DNa02 output through (i) fewer
  intermediate spikes (count deficit; its upstream cause — intermediate refractoriness during synchronous LC10a volleys — is supported
  only by post-hoc Exp 6 and the multi-effect E1b ablation) and (ii) an interaction between synchronous intermediate input and the DNa02
  refractory block in a mean-driven regime (causally demonstrated in V6m2 MAIN/BA1). The two are non-additive; their shares depend on the
  surrogate used (MASYNC timing share 27–52 %, MTHIN ~57 %) and are not identified.
- **Cannot conclude:** the causal mechanism of the count route; behaviour outside the tested parameter sets/levels; anything about
  Drosophila (the model's refractory periods and synchrony are not constrained by data).

## 5. Synchrony measures and their limits
LC10a REF DATA vs B1: Fano10 11.8 / 37.7, χ² 0.053 / 0.183, pairwise r 0.047 / 0.181, volley 0.066 / 0.285 (shuffled reference ≈ 0.015);
LCIRC brings all to chance. Fano and CV scale with rate and bin width (not a problem within Exp 4 — counts fixed — or between DATA and B1
LC10a, counts within 0.3 %, but a problem for intermediate Fano across conditions with different rates, e.g. E1b: use pairwise r); χ²
depends on N; pairwise r ignores higher-order co-firing; the volley score depends on an arbitrary threshold; Exp 4 shows no single measure
predicts DNa02 output across surrogate families.

## 6. Limitations
One full parameter set (RT-C spot-checked TH8, BA1, J025 with a reduced design; V6m2 tested BA1 and J025 arms); one DATA receiving
network (every CI is conditional on it); single-factor design cannot detect interactions (the one tested is large); ablations that shift
DNa02's rate make absolute-gap F partly an operating-point effect; surrogate RNG shared per rep; Exp 4 one surrogate family; Exp 6 post hoc.

## 7. Next experiment
Done as V6m2 for the DNa02 level. Remaining: the count route — clamp the intermediates' INPUT (LC10a) and swap per-neuron intermediate
counts vs timing between sources (count-swap), with intermediate t_ref 0 at matched intermediate rates, to test whether intermediate
refractoriness causes the count deficit (pre-registered, analogous to V6m2).

## 8. Red team and changes
RT-A (`redteam/RT_A_implementation.md`, PASS_WITH_LIMITATIONS): independent engine; corrections to latency, T5 counts, jitter losses,
MCIRC window counts, Exp 4 participation, single-neuron design, E5b scope, RNG sharing — applied. RT-B (`RT_B_statistics.md`, NOT_READY):
relative-metric flips, interaction simulation (+11.1 Hz), unit structure, jackknife-t, per-level heterogeneity, Exp 4 range dependence —
applied. RT-C (`RT_C_parameter_dependence.md`, NOT_READY): parameter dependence of H1/H2/H5 (noted a v6m.BA0 constant that would
silently keep b_a 0.5 at other settings — not used by V6m itself; avoided in V6m2) — applied. RT-D (`RT_D_interpretation.md`,
NOT_READY): draft account contradicted (interaction +14.4 Hz; leak refuted; MPOIS bound; loop-locking alternative for part of MCIRC;
τ_m → ∞ definition wrong) — applied; its proposed DN-only factorial was run as V6m2. All reviewers are model instances (limited
independence), not human review.

## 9. Files
`v6m.py`, `test_v6m.py`, `v6m_analysis.py`, `v6m_figures.py`, `v6m_exp6.py`, `v6m_exp6_analysis.py`; protocol + addendum A1 in
`program_v5v41/`; `results/v6m/` (raw/25 npz, exp6/11 npz, analysis.json, exp6_analysis.json, figures F1–F3, stdout, config,
protocol_sha256_before_run.txt, run_done, redteam/RT_A…RT_D + scripts).
