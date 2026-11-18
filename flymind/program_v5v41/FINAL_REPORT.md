# FlyMind research programme 2026-10-30 — V5 v4.1 → V5 v4.3, V6, V6.1, V7, V6m, V6m2, V6m3: final report

(Updated after V6m3, run at the user's request after the first version of this report; sections A–K amended; then corrected after an independent cross-check of every number against the stage reports — 19
discrepancies and the listed over-claims fixed.)

All results concern a MODEL: an adaptive leaky integrate-and-fire network (ALIF) whose wiring is derived from the MaleCNS v1.0 connectome
(LC10a → 147 intermediates → DNa02, 424 neurons, 13 510 edges), driven by a camera encoder and decoded into a pan command in MuJoCo.
Labels: DATA = connectome-derived facts (neurons, edges, synapse counts); MODEL = dynamics and parameters chosen by design (ALIF, J0,
b_a, σ, t_ref…); ENGINEERING = encoder, decoder, safety layer, MuJoCo arm; CONTROL = shuffled networks (SWS v2, block shuffles) and
the engineering P controller. Nothing here is a statement about Drosophila; no physical SO-101 arm was used. Every stage is
EXPLORATORY; no confirmatory test was run and no confirmatory seed pool was consumed.

## A. Executive summary
- **Open loop (V5 v4.1):** with the data-derived wiring (DATA) the model DNa02 responds more strongly to unilateral LC10a drive near
  threshold than in 50 degree-preserving shuffles (SWS): −18.0 Hz (CI −18.8; −17.2) over 6–10 mV, 0/50 shuffles ≥ DATA (the SWS family
  behaves almost like one network — the CI reflects the 8 noise reps of the single DATA network, not 50 replications); reversed at
  10.5–11 mV. A noise × network interaction (−6.9 Hz without noise).
- **Locus (V5 v4.2):** shuffling only the LC10a×LC10a block (B1) reproduces ~94 % of the deficit and the full LC10a synchrony increase
  (Fano 38.8 vs 11.3); the other blocks contribute ≤ ~2 Hz (labelled partial/unresolved).
- **Route (V5 v4.3):** replaying B1 LC10a spike trains into the DATA network reproduces the gap (−19.9 Hz); destroying cross-neuron
  alignment removes ~90 % (residual ~10 %, 25 % at 8 mV) → the effect travels mostly (~80–90 %) through LC10a population co-firing.
- **Mechanism (V6m, V6m2):** my first mechanistic reading ("neither DNa02 refractoriness nor adaptation; a DNa02 timing route that
  survives t_ref 0; leak") was FALSIFIED by the red team. The pre-registered V6m2 follow-up shows (MAIN, replicated by an independent
  implementation): with the model DNa02's refractory block, synchronous intermediate input is harmful; removing the block removes this
  penalty (interaction +21.2 Hz, CI +17.3; +25.0; independent +22.1) — synchrony then becomes neutral to beneficial depending on how the
  operating point is set, and the operating regime itself can flip the sign. Adaptation is not required for the gap; DNa02 membrane leak
  and hard reset are not required for the DNa02 synchrony penalty.
  **V6m3 (pre-registered, MAIN + replication set):** the synchrony-dependent part (≈ 60 %; LCIRC F_A 0.63 / 0.59) of the model
  intermediates' drive deficit comes from their own refractory block acting on synchronous LC10a volleys; removing the block abolishes
  that part and turns synchrony into a gain, while a non-synchrony residual (−3.9…−4.7 %; −6.1 % at t_ref 0) persists, so the net ≈ 0 under
  t_ref 0 is a cancellation (LCIRC replication differs only in noise). With real intermediate trains, count and timing routes both carry the DNa02 gap (count share
  0.36–0.53 depending on the swap construction).
- **Parameter study (V6):** the open-loop deficit is sign-consistent under one-factor variation of b_a, threshold, τ_a, J0 (3-fold
  size range) and is not detected in window averages at σ 6 mV (+0.5, CI −1.0; +1.7; equivalence not shown; pointwise differences and
  ΔG(I0 9) +3.9 Hz/mV remain). Closed-loop DATA−SWS differences are small (none shown > 0.5°; 9/16 cells indeterminate) and their
  sign is parameter-dependent; the V5 v4 near/far interaction replicates at default parameters with new scenes, instances and
  calibration (+0.33 / −0.66°).
- **Drive (V6.1):** changing the encoder gain I_max (drive and fixed-decoder loop gain together) reverses the closed-loop sign in both
  strata (the S1 reversal at I_max 8 occurs where the loop largely fails; the I_max 8 S2 value rests on 5 non-zero pairs); "governed by drive, not distance" is NOT supported (strata differ at every I_max; non-monotone).
- **Generalization (V7):** near/far pattern reproduced at wider azimuths (fragile); far targets: loop mostly fails; σ 6: no
  difference; very near targets: sign reversed in a failing, oscillatory regime. The SNN controller is worse than the P reference
  everywhere.
- **Honest bottom line:** the connectome-derived LC10a×LC10a wiring, in this model, desynchronises the model LC10a population and thereby raises the model DNa02
  response near threshold, through an interaction with spike refractoriness. Whether this matters for closed-loop orienting depends
  on parameters, drive and decoder; no robust behavioural advantage of the data-derived wiring was found.

## B. Version history (each with its own protocol, output directory and report)
| Stage | Question | Protocol (sha prefix) | Output | Verdict |
|---|---|---|---|---|
| Recon | code vs protocol, raw recompute, claims inventory | RECON_SUMMARY.md | results/v5v41/recon | — (10 discrepancies listed, #10 minor) |
| V5 v4.1 | open-loop response DATA vs 50 SWS | V5v41_PROTOCOL (dc569e02) + A1 E6 (59104af9) | results/v5v41 | PASS_WITH_LIMITATIONS (my first mechanistic reading rejected by RT3) |
| V5 v4.2 | which connectivity block | V5v42_PROTOCOL (b142899b) + A2 (d710e3fe) | results/v5v42 | PASS_WITH_LIMITATIONS |
| V5 v4.3 | timing vs rate route (spike-train replay) | V5v43_PROTOCOL (5de36553) | results/v5v43 | PASS_WITH_LIMITATIONS |
| V6 | network × ALIF parameters, open + closed loop | V6_PROTOCOL (4d195e87) | results/v6 | PASS_WITH_LIMITATIONS (after 27 fixes) |
| V6.1 | closed-loop drive manipulation (I_max) | V61_PROTOCOL (b74a011a) | results/v61 | PASS_WITH_LIMITATIONS (headline corrected) |
| V7 | robustness outside the V5 v4 box | V7_PROTOCOL (969139e8) | results/v7 | PASS_WITH_LIMITATIONS (drive-band claim withdrawn) |
| V6m | mechanism: refractoriness / adaptation / intermediates / synchrony | V6m_PROTOCOL (b8cd8935) + A1 post hoc (c3b44a62) | results/v6m | PASS_WITH_LIMITATIONS (draft interpretation falsified, rewritten) |
| V6m2 | pre-registered DNa02-only factorial (refractoriness × synchrony) | V6m2_PROTOCOL r2 (f8faf355) | results/v6m2 | PASS_WITH_LIMITATIONS |
| V6m3 | intermediate refractoriness → count deficit; count-vs-timing 2×2 swap | V6m3_PROTOCOL r1 (fbeeb64a; 18/22 jobs) + r2 (f00db4bf; fallback, 4 jobs) | results/v6m3 | PASS_WITH_LIMITATIONS |
"V6m" was named to avoid colliding with results/v6 (the user's mechanism request was titled "V6"). V8 was not started (§H).

## C. Experimental results (n, CIs, tests; open loop Δ/gap = control − DATA; closed loop d = err(DATA) − err(control) [°], positive = control lower error)
**V5 v4.1** (50 SWS instances, 8 noise reps, hierarchical bootstrap): E1 DNa02 ipsi 6–10 mV −18.0 (−18.8; −17.2) Hz; 6–8 −13.0; 8–10 −23.0;
thresholds I_th10 5.99 vs 6.09, I_th30 6.49 vs 6.66 mV (50/50 higher); LC10a mean rate Δ +0.10 Hz; intermediates −1.16; noise 0 −6.9;
E2/E3/E3c/E5 −16.9…−18.6; hysteresis equal; E6 small-signal gain DATA higher at I0 6–7 (33.3 vs 27.0; 36.8 vs 21.1 Hz/mV), SWS higher at 10
(+21.4); LC10a Fano (7–9 mV) 11.3 vs 38.9. Between-instance SD at noise level (instances ≈ one network).
**V5 v4.2** (5 block families × 50; 6–9 mV): SWS −17.4, B1 LC×LC −16.4 (−17.4; −15.5), B2 −1.8, B3 −0.9, B4 −1.0, B5 ALL −17.5; B1 − SWS
+1.0 (+0.9; +1.2); LC10a Fano B1 38.8 vs B2–B4 ~11.3–11.6; reciprocity-preserving LC×LC pilot closes only 12–14 % of the gap.
**V5 v4.3** (DATA + 10 B1, 7/8/9 mV, 8 reps): replay gap V0 −19.9 (−21.8; −17.9); circular shift −1.7 (−2.9; −0.6); rate-matched Poisson
−2.1 (−5.4; +1.2); jitter ±20 ms −9.3; within-side train swaps keep the gap (−24.6/−25.4) → population co-firing matters.
**V6** (16 configs; open loop 50 SWS + 25 B1, 4 reps; closed loop 8 configs × 120 scenes × 3 networks + P = 3000 trials, 0 errors): own-window
ΔDN D0 −16.8 (−18.8; −14.7), BA0 −8.4, BA1 −5.7, TH6 −12.6, TH8 −15.0, J015 −11.1, J025 −14.6, SG0 −7.7, SG6 +0.5 (−1.0; +1.7); no
configuration met the equivalence rule; closed loop D0 S1 +0.33 (+0.12; +0.55), S2 −0.66 (−1.02; −0.33), d_S1 − d_S2 positive in 4/8
configs, reversed in TH6; Q8 Spearman (open- vs closed-loop) −0.12 (n = 8, no power); P 0.27 / 0.15°.
**V6.1** (I_max 8–16, 120 scenes, DATA/SWS/B1, 1440 new trials): SWS S1 −1.20 (I8) → +0.33 (I12) → −0.12 (I16); S2 −0.15 (I8, 5 non-zero
pairs) → −0.66 (I12) → +0.24 (+0.12; +0.35) (I16).
**V7** (4 blocks × 120 scenes, 1440 trials): G1 far −0.33 (−0.57; −0.10) (loop mostly fails); G2 near-half +0.21 (+0.04; +0.38), far-half
−0.33 (cluster −0.67; −0.03; scene CI incl. 0); G3 σ 6 +0.07 (n.s. by scene bootstrap); G4 near −0.20 (−0.34; −0.06) (success 0.17/0.09).
**V6m** (replay framework; DATA + 10 B1 + replication set; 8 reps; single-factor ablations; F = fraction of the gap removed):
LC10a circular shift F 0.94 (rep 0.80); DNa02 t_ref 0 (intermediates clamped) F 0.21 (+0.06; +0.37; percentile CI — includes 0 under jackknife-t, RT-B) absolute, 0.59 on the relative gap;
DNa02 b_a 0 F −0.15 (rate scaling); intermediate b_a 0 F 0.02 (rel 0.22); intermediate circular shift F 0.36; Bernoulli 0.49; subtractive
reset n.s.; synthetic synchrony dose–response monotone (level-pooled), reproducing 70–93 % of the real gap depending on the synchrony axis.
**V6m2** (DNa02-only factorial, 23 jobs, 0 errors): MAIN interaction +21.2 (+17.3; +25.0) Hz, log +0.55; BA1 +11.3 (+6.7; +15.9); J025 +22.4
(unmatched control); per level MAIN 9 mV +38.2 (+34.1; +42.3); independent replication +22.1 (+15.4; +28.8); gain-matched variant +7.4
(−1.3; +16.1).
**V6m3** (22 jobs; MAIN + REPLICATION, 8/9 mV): drive deficit REF −10.7 % (−12.9; −8.4) | −10.8 %; intermediate t_ref 0 gain-matched +2.2 %,
bias-matched +5.4 % → H-IR SUPPORTED in both sets (F_A 1.21 / 1.51, not a share; synchrony-dependent part ≈ 60 %; non-synchrony residual −3.9…−4.7 % under REF
(LCIRC) persists at t_ref 0: MT0 + LCIRC −6.1 %, MT0B + LCIRC −7.3 %, RT-H post hoc); count-swap (DNa02 block intact) C −12.2, Tm −10.9 Hz, count share 0.53 (0.46; 0.59) pre-registered, 0.36–0.46 with
bias-reduced constructions; DNa02 t_ref 0 gain-matched Tm +0.1 (−2.5; +2.6) Hz (8 mV −2.9, 9 mV +3.0; −1.7…+5.2 across constructions; interaction +7.5); unmatched T0:
B1 timing beneficial (+3…+10 Hz).

## D. Interpretation — claim / hypothesis / cannot conclude
**Claims (MODEL level, supported by pre-registered analyses and red-team checks):**
1. The data-derived LC10a×LC10a wiring lowers model LC10a population synchrony relative to degree-preserving shuffles, and this raises
   the model DNa02 response near threshold under unilateral drive (V5 v4.1–4.3).
2. The effect is mostly (~80–90 %) carried by cross-neuron spike alignment rather than mean rates (V5 v4.3, V6m LCIRC); a residual remains
   (V5 v4.3 ~10 %; V6m3 LCIRC ~40 % of the intermediate drive deficit and −4.5 Hz DNa02 gap).
3. At the default operating point, with the model DNa02 refractory block, synchronous intermediate input is less effective than the same
   spikes spread in time; removing the block removes this penalty (V6m2 MAIN/BA1; independent replication; with gain matching only as a
   trend, I +7.4, CI −1.3; +16.1). The operating regime also sets the sign: with the block intact a −40 mV DNa02 bias makes synchrony
   beneficial (RT-E F1).
4. The gap persists without adaptation (DNa02 b_a 0; intermediate b_a 0 removes only ~22 % of the relative gap), and the DNa02-level
   synchrony penalty does not require DNa02 membrane leak or the hard reset (leak and reset were not ablated in the intermediates).
5. The open-loop deficit is sign-consistent across one-factor parameter variations except at high noise (σ 6).
6. The model intermediates' refractory block converts LC10a synchrony into the synchrony-dependent ≈ 60 % of the intermediate drive
   deficit (V6m3, MAIN + replication set); a non-synchrony residual is not explained; count and timing routes both carry the DNa02 gap
   (split construction-dependent). Removing the intermediate block does not shrink the DNa02 gap in V6m3 Part A (−24.1 vs −23.1 Hz
   gain-matched), because B1 then recruits more inhibitory drive and more synchronous intermediate output (untested which matters).
**Hypotheses (suggested, not established):**
- The closed-loop sign pattern reflects gain/decoder mismatch interacting with drive (V6 RT2, V6.1); an inverted-U in drive was suggested
  post hoc and contradicted within V7.
- σ 6 removes the difference by desynchronising LC10a (equally explained by noise dominance).
**Cannot conclude:** anything about Drosophila (refractory periods, synchrony and parameters are not constrained by data); that the
connectome wiring improves closed-loop orienting (no robust advantage; SNN worse than P everywhere); a single mechanism or additive shares
of the count and timing routes; generality beyond the tested parameter sets, levels and dt = 1 ms; the closed-loop meaning of the
open-loop effect.

## E. Red-team findings (all reviewers were separate model instances — limited independence, not human review)
- V5 v4.1: RT3 rejected my "difference arises downstream of LC10a" reading (an equal mean LC10a rate is nearly guaranteed by construction) → replaced
  by the synchrony correlate.
- V5 v4.2: wording over-reach (additivity, B3/B4 labels, "reproduces"); reciprocity-preserving pilot.
- V5 v4.3: engine verified; common-shift and train-swap controls; replication.
- V6: 27 fixes — false Q5/Q7/ceiling/B1 statements, anti-conservative interaction CIs, missing Fano script, SESOI misuse, stratum-pattern
  evidence, decoder confound, Q8 power.
- V6.1: headline over-reach; mis-specified drive model; provenance timing error (analysis script hashed after the run started).
- V7: drive-band claim contradicted by V7's own data; G4 failing/oscillating regime; fragile G2.
- V6m: draft mechanism falsified (interaction found by two reviewers; leak refuted; metric and parameter dependence).
- V6m2: J025 not rate-matched; operating regime can flip the sign; matching-method dependence; "1 step suffices" not robust; wording.
- V6m3: RT-H — 18/22 jobs (not 17); QA net ≈ 0 is a cancellation and F_A is not a share; intermediate refractoriness explains only the
  synchrony-dependent ≈ 60 %; inhibitory intermediates silenced under rate matching (D_inh); Part A timing claim withdrawn; LCIRC /
  count-swap seeding deviations. RT-I — count-window mismatch (design defect); count share construction-dependent (0.36–0.53); ~half of
  the REF interaction is a random-addition artefact; "abolishes the timing effect" and "surrogate-free" withdrawn; nested bootstrap invalid
  (jackknife-t binding); Bonferroni check.
- Final report: independent cross-check (19 discrepancies, over-claims) — fixed.

## F. Reproducibility
Interpreter `.venv/bin/python -I -B` (Python 3.12.13, numpy 2.5.4, scipy 1.18.1, mujoco 3.17.0); multiprocessing spawn; no network access.
Commands (from the repo root):
- V5 v4.1: `flymind/v5v41.py --out flymind/results/v5v41 --protocol-sha256 dc569e02…`; E6 `flymind/v5v41_e6.py --out …/E6 --amendment-sha256 59104af9…`; analysis `v5v41_analysis.py`, `v5v41_e6_analysis.py`.
- V5 v4.2: `flymind/v5v42.py` (+ `--structure`), `v5v42_analysis.py`. V5 v4.3: `flymind/v5v43.py --out flymind/results/v5v43 --protocol-sha256 5de36553…`, `v5v43_analysis.py`.
- V6: `flymind/v6.py --openloop / --calibrate / --closedloop [--family-x B1]`, `v6_analysis.py --run flymind/results/v6 --v41 flymind/results/v5v41`, `v6_figures.py`, `v6_fano_posthoc.py`.
- V6.1 / V7: `flymind/v61_v7.py --out flymind/results/v61 --protocol-sha256 b74a011a… --drive-index --v61 --family-x B1`; `--out flymind/results/v7 --protocol-sha256 969139e8… --v7`; `v61_toy.py`; `v61_v7_analysis.py --v61 … / --v7 … --drive …`.
- V6m: `flymind/v6m.py --out flymind/results/v6m --protocol-sha256 b8cd8935…`; `v6m_analysis.py --run … --v43 flymind/results/v5v43`; `v6m_exp6.py`, `v6m_exp6_analysis.py`, `v6m_figures.py`.
- V6m2: `flymind/v6m2.py --out flymind/results/v6m2 --protocol-sha256 f8faf355…`; `v6m2_analysis.py --run …`; `v6m2_figures.py`.
- V6m3: `flymind/v6m3.py --out flymind/results/v6m3 --protocol-sha256 f00db4bf…` (r2; 18 r1 jobs kept), `v6m3_analysis.py --run …` (4f1d675a), `v6m3_figures.py`.
- Tests: `test_v5v41.py` (8), `test_block_shuffle.py` (7), `test_cl_runner.py` (6), `test_v5v43.py`, `test_v6m.py`, `test_v6m2.py`, `test_v6m3.py` — all OK.
Code sha256 prefixes (final): v5v41 1e2ff540, v5v42 52e9b59e, v5v43 7d042133, block_shuffle ca7fff36, side_shuffle 5895ab2a, cl_runner
ae7c9d8e, v6 db398df8, v6_analysis 53697c94, v61_v7 088697c9, v61_v7_analysis 956c5cd9, v6m f28f9a2d, v6m_analysis abb8f84d (post-hash
ordering fix of c0c7a656), v6m2 7aea3c18, v6m2_analysis 23360b5e, v6m3 02f93696 (r2; r1 e4422fc4), v6m3_analysis 4f1d675a, alif 13e36619, loop 05bc8cdf (protected, unchanged).
Randomization: seed registry `program_v5v41/SEED_REGISTRY.md` (SWS 8 410 001–050; noise 8 411 001–016; analysis RNG 8 419 0xx; block
families 8 42b 0xx; scenes 8 600/8 700; calibration 8 601 001–003; v4.3 8 430; V6m 8 440/8 441/8 442; V6m2 8 443/8 444; V6m3 8 445/8 446; red-team pools
8 495–8 499; smoke 8 490); collision scans 0 hits; no forbidden pool used. Protocol shas were recorded before each run in
`results/<stage>/protocol_sha256_before_run.txt` (V5 v4.3: in `results/v5v43/config.json`; amendment A1: `results/v5v41/E6/config.json`;
amendment A2 d710e3fe: stated in the V5 v4.2 report only, no machine record; V6m addendum A1 is post hoc; V6m3 r2 was hashed after the 18
r1 jobs, which ran under r1 fbeeb64a).

## G. Integrity report
`integrity_v5v41.py --compare results/v5v41/integrity_baseline.json` run at 17:13 (`final_20261030`) and 17:48 (`final_after_v6m3`) —
console output only — and at 17:56 (`final_saved`, saved to `program_v5v41/integrity_final_20261030.txt`): **Stage 1 28/28** (frozen_manifest_v4),
manifests v5v3 18/18, v5v4 18/18, protected tree 377 files dfcabd78f1484c96, changed 0, pycache same — INTEGRITY OK. Stage 1 28/28 also
in every post-run file of every stage. `git status` shows no modification in bio2/, assets/, data/, loop.py, loop_v2.py; frozen V5 v3/V5 v4
results and reports untouched; no commits made. Execution notes: one chained-launcher crash in V6 (0 trials affected); V6.1 restarted from
2 to 8 workers (resumable, verified); V6m2 r1 smoke failure → r2 sampler before any data; V6m3 r1 crash in one job → r2 fallback (18/22 r1 jobs kept unopened; rep 0 of two kept jobs re-run under r2 was bit-identical, RT-H); two red-team workflows interrupted by a usage
limit and re-run. Provenance errata: V6.1 analysis script hashed after the V6.1 run started (2 raw records seen); V6m and V6m2 timestamps in the
protocol texts and in SEED_REGISTRY.md (V6m "~15:00", V6m2 "~15:35/~15:45") are wrong — the V6m run was 14:43–14:56 and the V6m2 jobs
15:26–15:33 (file times authoritative); smoke runs used rep 1 of real seeds (disclosed per stage).

## H. Unresolved questions
1. (Resolved in part by V6m3: intermediate refractoriness × synchrony.) Open: the non-synchrony residual (~4 % drive) and the exact
   count/timing split (construction-dependent).
2. Why the no-block result depends on how the operating point is set (additive bias vs gain) — is "mean-driven vs fluctuation-driven
   regime" the right description?
3. Which LC×LC structural statistic (clustering, local/retinotopic wiring) produces the desynchronisation (reciprocity ruled out as main).
4. Whether any of this survives ALIF parameters constrained by data, dt < 1 ms, or a different neuron model.
5. The closed-loop relevance: decoder/gain mismatch vs structure; why near-field (G4) loops oscillate.
6. V8 was not justified: no robust closed-loop effect of the wiring was established to build on.

## I. Single recommended next experiment
(The previous recommendation — intermediate count-vs-timing dissection — was run as V6m3.) Next: test whether the refractoriness ×
synchrony mechanism survives a **data-constrained or alternative neuron model and finer time step**: rerun the V6m2 DNa02-only factorial
and the V6m3 Part A at dt 0.1 ms with (a) ALIF and (b) a conductance-based or adaptive-exponential neuron whose refractory/reset parameters
are set from published electrophysiology where available (labelled as such), pre-registered with the same decision rules. This is the
most efficient way to learn whether the mechanism is an artefact of 1-ms quantised refractoriness and the current parameter choices —
the main remaining threat to every mechanistic claim above.

## J. Independent verification checklist
- [ ] Run `integrity_v5v41.py --compare results/v5v41/integrity_baseline.json --label verify` → Stage 1 28/28, changed 0.
- [ ] Run all seven test files → OK.
- [ ] Check each protocol sha against `results/<stage>/protocol_sha256_before_run.txt` and file mtimes (run start after hash).
- [ ] Recompute V5 v4.3 replay gap and V6m LCIRC F from raw npz (v5v43_analysis.py, v6m_analysis.py).
- [ ] Recompute V6m3 D_rel(REF), F_A and the Part B C/Tm from `results/v6m3/raw/*.npz` (v6m3_analysis.py).
- [ ] Recompute the V6m2 MAIN interaction from `results/v6m2/raw/MAIN_*.npz` (dn[dyn, input, level, side, rep]; I = (gap MASYNC − gap M0)_REF − (…)_T0B).
- [ ] Re-run `test_v6m2.py`; re-simulate one MAIN B1 instance with `v6m2.job_run` and compare its npz bit-for-bit.
- [ ] Read every `redteam/` review and confirm each listed correction appears in the stage REPORT.md.
- [ ] Confirm no seed in 0–39, 300–399, 1001–1999 or the consumed pools appears in any config.json.

## K. Honest conclusion
Within this model, the connectome-derived LC10a×LC10a wiring makes the LC10a population fire less synchronously than matched shuffled
wiring. At the default operating point, and given the model neurons' refractory block, synchronous input is used less efficiently at
two stages: the intermediates' block turns synchronous LC10a volleys into fewer spikes (the synchrony-dependent ≈ 60 % of the drive
deficit), and DNa02's block turns synchronous intermediate input into fewer spikes. Asynchronous (DATA-like) input therefore drives the
model DNa02 harder — a structure × dynamics interaction, not a property of the wiring alone. Removing the intermediate block does not
shrink the DNa02 gap (−24.1 vs −23.1 Hz gain-matched in V6m3 Part A), because B1 then recruits more inhibitory drive (untested), so the
two stages are not independent levers. Both links are supported by
pre-registered, replicated simulations (V6m2, V6m3), but their sizes, the count/timing split and even the sign without the block depend on
the operating regime and on construction choices, and they rest on a 1-ms-quantised refractoriness that is not constrained by data. In
closed loop the wiring gives no robust advantage: differences are small, parameter-, drive- and decoder-dependent, and the spiking
controller is worse than a simple P controller everywhere. My own first mechanistic interpretation, and several later over-claims, were
wrong and were corrected by adversarial review. None of this is evidence about the fly.
