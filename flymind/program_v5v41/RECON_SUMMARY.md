# Reconnaissance before V5 v4.1 (2026-10-30) — project state, verified discrepancies, open questions

Full auditor reports (independent model instances, read-only, no simulation): `results/v5v41/recon/A_code_vs_protocol.md`,
`B_raw_recompute.md`, `C_claims_inventory.md`, `D_project_map.md`. Independence is limited (same model family, not human review).
Items marked **[verified]** were re-checked by me with my own commands; the rest are auditor findings with file:line evidence.

## State at start
- Stage 1 28/28; v5v3 and v5v4 manifests 18/18 each; 377 protected files hashed (`results/v5v41/integrity_baseline.json`,
  tree dfcabd78f1484c96). Working tree: only flymind/ changes from earlier sessions (REPRODUCE.md, VALIDATION_PLAN.md modified;
  many untracked flymind files); nothing in bio2/, assets/, data/. No commits made.
- V5 v4 frozen code = manifest = frozen copy (A). `v5v4.analyze` on the raw JSONL reproduces `analysis_frozen.json` (A); an
  independent from-scratch implementation reproduces every decision and number within bootstrap-RNG noise (B).

## Project map (short; full map in D)
- DATA: MaleCNS v1.0 (minconf 0.5) feather files; LC10a 135 L / 140 R (somaSide) → 147 intermediates (≥ 5 syn from LC10a and ≥ 5 to
  DNa02; 58 L / 89 R) → DNa02 L/R; 424 neurons, 13 510 edges, 0 model edges. |w| share: in→in 22.2 %, in→mid 60.6 %, mid→in 0.6 %,
  mid→mid 11.4 %, mid→dn 5.3 %, in→dn 0. Signs from NT (ground truth 323, consensus 101 neurons). Glu = inhibitory (MODEL) touches only
  2 LT51 neurons (0.22 % of |w|); the key inhibition is GABAergic AOTU019 (strongest single input to each contralateral DNa02).
- MODEL: W = sign · 0.2 mV · synapses; ALIF (τ_m 20, τ_syn 5, gap 7 mV, b_a 0.5, τ_a 300 ms, refractory → 250 Hz cap, delay 2 steps);
  noise σ = 2 mV is a per-step current, giving only **≈ 0.32 mV SD of membrane potential [verified analytically]** — the network is
  nearly deterministic and silent at rest.
- ENGINEERING: encoder g = 1 − exp(−E/60) per side → 12 mV·g to LC10a; camera 96×128; MuJoCo SO-101, 10 ms tick, 10 SNN steps/tick.
- CONTROL: SWS v2 (swaps inside keys (signed w, layer×side pre, layer×side post)); cannot change any edge to/from DNa02 (1-neuron
  groups); SHUF_STR; common decoder; toy relay; P controller.

## Verified discrepancies in earlier reports (frozen reports are NOT edited; corrections recorded here)
1. **[verified]** `V5v4_FINAL_REPORT.md:63,77` "P better in 450/450 pairs / in every scene" → P better in **446/450** (DATA ≤ P in
   seeds 4309, 4315, 4411, 4425; all S2). 2.68° is a mean.
2. **[verified]** Protocol `v5v4_protocol.md:37` "calibration equalises small-signal gain" is wrong as stated: the calibration
   spots drive the ipsilateral LC10a at **11.6–11.9 mV** for every |az| ≥ 10° (10.9 mV both sides at 0°); the L−R signal comes from
   the contralateral side falling 10.9 → 2.5 mV; the fit is weighted 64 % by |az| = 30°. It is a large-signal, near-saturation slope.
   H1 (common decoder) is not biased by this; H2a "after scale equalisation" holds only in that regime.
3. `V5v4_FINAL_REPORT.md:57` "SWS slopes 0.988–1.005 × DATA" rests on **10 of 450** instances (seeds 4001–4010).
4. `V5v4_FINAL_REPORT.md:56` "DATA advantage grows with distance, sign change at ρ ≈ 0.23 m" comes from a linear fit; six equal ρ
   bins give +0.29, +0.74, +0.43, −0.16, −0.90, −0.55 (not monotonic); inside S1 d does not depend on ρ (Spearman 0.03).
5. The "~7 mV ALIF threshold" (VALIDATION_PLAN:343, protocol) is the membrane gap, not the network onset: DNa02 onset is ≈ 6 mV of
   LC10a current (v6_stability default row: 0 Hz at 5.7 mV, 16 Hz at 6.0). To be measured directly in V5 v4.1.
6. VALIDATION_PLAN:376,396–398 still says the within-block pattern changes the mean error by ≤ ~0.5°; V5 v4 S2 −0.52 (CI to −0.71)
   and S2b −0.66 (CI to −0.99) contradict that summary; not retracted there.
7. "≥ SESOI" labels in V5 v4 come from point estimates (|d| 0.512 / 0.518); CI95 lower bounds 0.41 / 0.33 — the effect size relative
   to 0.5° is undetermined (bootstrap P(|mean| ≥ 0.5) ≈ 0.6). The report flags this; the category label overstates it.
8. The "SWS weaker at 6–9 mV" premise of this programme: no repository document states it; artifacts with ≤ 6 SWS instances
   (v6_stability seed 1401; control check v2 1401–1403; RT v2 1441–1443) show SWS weaker at ~6–7.8 mV and STRONGER at ~8.1–9.9 mV
   (with adaptation b_a 0.5 only). None of the 450 V5 v4 SWS instances has an open-loop curve.
9. In open loop with one-sided drive the contralateral DNa02 never fires, so data push-pull inhibition (AOTU019) is invisible there.
10. Minor: decoder offset hard-coded 0 (`loop.py:111`; STR_OWN offsets not logged); data files not sha256-pinned; success metric
    counts |az0| < 5° scenes as success without movement; S2 mean (−0.52) vs median (−0.11, CI includes 0) disagree — the S2 effect
    sits in the tails (46 pairs d < −2°; 9 scenes where only DATA moved, 0 where only SWS moved).

## Claims status (from C; unchanged by me unless marked)
- Independently checked: V5 v4 decision numbers (second implementation, B); V5 v3 numbers (result RT, bit-identical reruns).
- Author-only: the "strong vs weak drive" explanation of the S1/S2 sign flip (never tested with fixed drive); v6 robustness (one
  SWS instance, threshold direction only); "beyond signal scale" (10/450 slopes, small-signal regime not covered).
- Silent scope widening found in V5 v4 report wording (drive labels, v6 robustness, "structure replicated", "450/450").

## Questions taken into this programme
- Is there a DATA vs SWS difference in open-loop weak-drive response across 50 independent SWS instances (not 1–6)? Where along the
  pathway? → V5 v4.1. What is the small-signal L−R gain around a symmetric operating point? → V5 v4.1 amendment A1 (E6).
- Which block carries it? → V5 v4.2. Is the S1/S2 flip a drive effect or a distance/geometry effect? → V6.1 (fixed-geometry drive
  manipulation). Parameter dependence (b_a, threshold, J0, noise)? → V6.
