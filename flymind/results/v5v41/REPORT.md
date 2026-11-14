# V5 v4.1 — Open-loop response characterization: report (2026-10-30)

**Status: exploratory diagnostic, completed. Red team: data/numbers PASS (RT2), re-analysis PASS_WITH_LIMITATIONS (RT1), my
initial mechanistic interpretation FAIL (RT3) — corrected below.** Overall verdict: PASS_WITH_LIMITATIONS.

## 1. What was done
Protocol `program_v5v41/V5v41_PROTOCOL.md` (sha dc569e02…, hashed before the run) + amendment A1 (E6, sha 59104af9…, written
before any main-run result was viewed). DATA network vs 50 independent SWS v2 instances (seeds 8 410 001–050), unchanged frozen
ALIF (noise 2 mV), identical input schedules and common noise seeds (8 411 001–008) for all 51 networks, no camera, no MuJoCo, no
feedback. Schedules: E1 unilateral step 4–12 mV (49 levels), E1n0 same with noise 0, E2 bilateral (contra 0.5·ipsi), E3/E3c
pre-adapted initial state, E4 ramp 4→12→4 mV (hysteresis), E5 random initial membrane potentials, E6 symmetric I0 ± δ/2.
Run 08:39–09:12 (1832 s), E6 run in parallel; 0 errors; Stage 1 28/28 before/after; protected tree unchanged.

Instance checks (`instances.json`): all 17 SWS invariants hold for 50/50; 50 distinct W; none equals DATA; pairwise Jaccard of the
changed-edge sets 0.13–0.14 (instances genuinely different; RT2: ~21 000 differing matrix entries per pair); LC×LC reciprocal
pairs 511–604 (DATA 2450), LC×LC undirected triangles 23 642–24 715 (DATA 20 502).

## 2. Results (Δ = SWS − DATA; CI95 hierarchical bootstrap: instances resampled, DATA reps resampled; n = 50 instances)
**E1 (unilateral step, noise 2 mV), DNa02 ipsilateral steady state (500–1000 ms):**
| Range | DATA [Hz] | Δ [Hz] | CI95 | instances ≥ DATA |
|---|---|---|---|---|
| 6–10 mV | 86.6 | **−18.0** | −18.8; −17.2 | 0/50 |
| 6–8 mV | 49.1 | −13.0 | −14.0; −12.0 | 0/50 |
| 8–10 mV | 124.0 | −23.0 | −23.8; −22.0 | 0/50 |
| 4–12 mV | 89.1 | −8.4 | −8.9; −7.9 | 0/50 |
Per level: 0 below 5.75 mV (both silent), negative from 6.0 to 10.0 mV (max −30 Hz at 9 mV), positive at 10.5–11 mV (+4…+7 Hz),
≈ 0 at 11.5–12 mV. Same sign on side L and side R, all 8 reps, three steady windows, median vs mean (RT1). The highest single SWS
run (71.8 Hz) is below the lowest DATA rep (84.9 Hz) in 6–10 mV.
Range averages are trapezoid-weighted over the non-uniform grid (plain mean of levels: 6–10 −17.7, 4–12 −11.4 Hz — RT1 D1).
**Along the pathway (E1, 6–10 mV):** LC10a ipsi mean rate DATA 13.27 Hz, Δ +0.10 (CI +0.06; +0.14) — tiny and of unstable sign
across ranges/sides/windows (RT1 L6); intermediates ipsi 13.27 Hz, Δ −1.16 (−1.24; −1.08); contralateral DNa02 0 Hz in every
network (one-sided drive never recruits it). Decoded angle with the common DATA decoder: Δ −2.10° (−2.19; −2.00) — under
UNILATERAL drive only; not a closed-loop quantity.
**Thresholds:** I_th10 DATA 5.99 vs SWS 6.09 mV (Δ +0.09; 50/50 higher), I_th30 6.49 vs 6.66 (Δ +0.17; 50/50 higher); LC10a onset
5.99 vs 6.03. The threshold shift explains ~20–37 % of the E1 deficit, the rest is a lower gain (ratio 0.73–0.85) (RT1 L4).
**Other properties:** latency and t_half equal except at 6.0 mV (SWS slower: +15 ms first spike, +122 ms t_half); saturation
≤ 0.2 % of neurons at 12 mV in all networks; transient peak (0–150 ms) ≈ 238 Hz in both (Δ −2.4, CI includes 0 in E1);
adaptation of DNa02 lower in SWS (follows its lower rate). **Hysteresis (E4):** large in both (mean |up − down| 6–10 mV
49.7 Hz DATA vs 49.6 median SWS; up-threshold 5.92 vs 5.94, down 6.37 vs 6.65 mV) — adaptation-driven, not network-specific.
**Initial state / input form:** E2 bilateral −17.5, E3 pre-adapted ipsi −17.2, E3c pre-adapted contra −18.6, E5 random v −16.9 Hz
(6–10 mV) — the effect does not depend on initial state or the contralateral 0.5 drive.
**Noise:** with noise 0 the deficit is −6.9 Hz (6–10) and essentially absent at 6–8 mV (−0.84 Hz; RT1 L5): a noise × network
interaction, not a pure connectivity property.
**E6 (symmetric operating point, small-signal L−R gain G = dD/dδ, |δ| ≤ 1 mV):** I0 4–5 mV: G = 0 in all networks (dead zone;
DATA silent for 82 % of δ at 5 mV, SWS 85–100 %). I0 6: DATA 33.3 vs SWS 27.0 Hz/mV (Δ −6.3, CI −9.7; −2.7); I0 7: 36.8 vs 21.1
(Δ −15.7, −21.4; −10.8); I0 8: −6.9 (−12.1; −2.1); I0 9: −5.0 (−7.8; −2.2) but sign window-dependent (RT1 L3); I0 10: SWS higher,
+21.4 (+16.4; +26.1); I0 11: +1.7 (−3.5; +7.7). Robust: DATA higher at 6–7 mV, SWS higher at 10 mV.

## 3. Mechanism — what is and is not supported
- **Variability:** between-instance SD (0.34 Hz for E1 6–10) is at the level expected from noise alone (instance×rep ANOVA
  F ≈ 1, RT1 L1): the SWS family behaves almost like one network. "Δ/SD_between" is therefore not a valid effect size, and the
  across-instance correlation ΔDN vs ΔLC (ρ 0.59) is trial-noise covariation (split-half ρ ≈ 0), withdrawn as mechanistic evidence.
- **Not supported (my first reading, rejected by RT3):** "the difference arises downstream of LC10a; P3 falsified". SWS keeps every
  neuron's (partner group, weight) multiset, so an equal MEAN LC10a rate is nearly guaranteed by construction and says nothing about
  the locus.
- **Supported correlate (RT3, verified by me):** LC10a population synchrony differs strongly — Fano factor of the LC10a ipsi
  population count (10 ms bins, 7–9 mV) DATA 11.3 vs SWS 38.9 (all 50 higher, min 38.2); intermediates 4.6 vs 11.1; SWS has ~3× more
  6–14 Hz power. The synchrony gap spans the same input range as the DNa02 deficit and reverses near 10.25 mV like it (RT3). DATA
  LC10a rates are slightly more heterogeneous (Gini 0.051 vs 0.045). Hypothesis (MODEL-level, correlational): the data LC×LC wiring
  desynchronises the LC10a population; synchronous volleys in SWS drive the few intermediates that carry ~half of the DNa02 input
  into saturation/refractoriness, lowering their mean output. Locus (LC×LC vs LC→mid vs mid×mid) unresolved → V5 v4.2 (amendment A2).
- Mid→LC feedback is < 1 % of LC10a input — implausible as the main cause.
- Prediction P1 (SWS weaker 6–9 mV): supported, and the effect extends to 10 mV; P2 (shrinks ≥ 10 mV): supported (reverses at
  10–11 mV); P3 (origin in LC10a layer): neither confirmed nor falsified at the level of mean rates; consistent with synchrony.
- The user-brief premise ("SWS weaker ~6–9 mV"): confirmed in this open-loop setting with 50 instances; earlier ≤ 6-instance
  artifacts that showed SWS STRONGER at 8–10 mV are not reproduced for 8–10 mV (here SWS weaker up to 10 mV, stronger 10.5–11 mV).

## 4. Relevance to the closed loop (not shown here)
Near the target both sides are driven nearly equally; per-side drive at az 0 is ≈ 8.1 mV at ρ 0.16 m, ≈ 6 mV at 0.22 m and ≈ 4.1 mV
at 0.28 m (static renders). The unilateral deficit is mostly common-mode and cancels in L−R; what reaches the decoder near the target
is the small-signal gain G (DATA up to 1.7× higher at 6–7 mV, lower at 10 mV) and the dead zone (DATA marginally narrower). A
higher L−R gain near 6–8 mV could produce more overshoot in S1 and a smaller dead zone could help in S2 — a hypothesis for the V5 v4
sign flip, to be tested in V6/V6.1. The 18 Hz figure itself is a model property, not evidence of a behavioural effect.

## 5. Limitations
One DATA network (CI = noise reps, not connectome uncertainty); one parameter set (J0 0.2, b_a 0.5, σ 2) — see V6; common random
numbers make the bootstrap conservative; no spike times stored (Fano cannot separate oscillation from pairwise correlation);
everything is MODEL dynamics on DATA structure — no statement about the fly.

## 6. Files
`v5v41.py`, `v5v41_e6.py`, `v5v41_analysis.py`, `v5v41_e6_analysis.py`, `test_v5v41.py` (8 tests); results `results/v5v41/`
(config.json, instances.json, raw/ 51 npz, E6/raw 51 npz, analysis.json, E6/analysis_E6.json, figures F1–F6, redteam/RT1–RT3,
recon/A–D, integrity_*.txt, protocol_sha256_before_run.txt, stdout).
