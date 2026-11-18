# V6 — Network structure × ALIF dynamics (EXPLORATORY parameter study) — protocol r1, 2026-10-30 ~09:00
Drafted before any V5 v4.1 / v4.2 result was inspected. One element is conditional and its rule is fixed now (§2, family X).
Any change after results → r2 with reason. No confirmatory decision; all configurations are reported, including unfavourable ones.

## 1. Questions (from the mission brief)
Q1 Does the DATA/SWS difference persist under different ALIF thresholds? Q2 Does its sign change with adaptation strength?
Q3 Sensitivity to J0? Q4 Dependence on initial state (covered by V5 v4.1 E3/E5 at default; here only default initial state)?
Q5 Survival across input amplitude (each configuration is measured over 4–12 mV)? Q6 Regimes of functional equivalence?
Q7 Regimes where the control is better? Q8 Does the closed-loop distance interaction (V5 v4: S1 +0.51°, S2 −0.52°) follow
the open-loop response difference across configurations (structure × nonlinearity) or not?

## 2. Configurations (MODEL parameters; every one motivated, none tuned on results)
Default D0 = J0 0.2, v_th −45 mV (gap 7 mV), b_a 0.5 mV/spike, τ_a 300 ms, σ 2 mV (V5 v4 setting).
| Config | Change | Why |
|---|---|---|
| BA0, BA025, BA1 | b_a 0 / 0.25 / 1.0 | adaptation is a bio2 design choice without data; earlier artifacts show a high-drive reversal only with b_a > 0 |
| TH6, TH8 | v_th −46 / −44 (gap 6 / 8 mV) | threshold × recurrence interaction is the leading hypothesis for the weak-drive effect |
| J015, J025 | J0 0.15 / 0.25 | the J0 rule (V4) fixed 0.2; synaptic scale sets recurrent gain |
| SG0, SG6 | σ 0 / 6 mV (membrane SD ≈ 0 / 0.96 mV) | threshold sharpness; σ 2 gives only ≈ 0.32 mV |
| TA100, TA1000 | τ_a 100 / 1000 ms | adaptation time scale vs the 1 s step and the 3 s trial |
| BA0×TH6, BA0×TH8 | b_a 0 with gap 6 / 8 | 2×2 interaction block adaptation × threshold (with BA0, TH6, TH8, D0) |
| BA0×J015, BA0×J025 | b_a 0 with J0 0.15 / 0.25 | 2×2 interaction block adaptation × synaptic scale |
15 non-default configurations + D0. This is the complete list; nothing else will be added post hoc without an r2 note.

Networks: DATA, SWS_k (k = 8 410 001–050, the V5 v4.1 instances, rebuilt at the configuration's J0 — swap pattern identical
across J0, test T6), and family X = the V5 v4.2 single-block family with the largest |Δ DNa02 ipsi (6–9 mV)| whose CI excludes 0
(25 instances, its first 25 seeds); if no block family qualifies, X is omitted.

## 3. Open-loop measurements (engine `v5v41.simulate`, unchanged)
Per configuration and network: E1 (unilateral step, 4.0–12.0 mV step 0.25 = 33 levels, 4 reps, seeds 8 411 001–004) and E6
(I0 4–11 mV × δ ±2 mV, 4 reps). D0 uses the first 4 reps of the V5 v4.1 data (identical seeds and schedules; not re-simulated
for E1/E6; the 33-level E1 grid is a subset of the 49-level grid). Spontaneous rate (0 mV, 300 ms) and saturation recorded.

## 4. Closed-loop measurements (MuJoCo, `cl_runner.py` → frozen `loop.run_trial`)
Configurations D0, BA0, BA1, TH6, TH8, J015, J025, SG6 (8; the ones expected to move thresholds or recurrent gain most).
Decoder: per configuration, DATA calibrated with `v5v4.calibrate` (same procedure as V5 v4) on seeds 8 601 001–003; the same
decoder is used for SWS (and X) — common decoder, as in V5 v4 H1.
Scenes: seeds 8 600 001–8 600 120 (identical across configurations — common random numbers): 001–040 → S1 ρ ~ U[0.16, 0.22),
041–120 → S2 ρ ~ U[0.22, 0.28); az0 ~ U(−30°, 30°) (cl_runner.scene). Scene i pairs DATA with SWS instance ((i − 1) mod 50) + 1
(each instance used 2–3 times). P controller once (encoder only; independent of ALIF), scenes as above.
Outcome = V5 v4 final_abs_err (mean |e| over 2.5–3.0 s); also signed final error, overshoot, movement, last-second SD.

## 5. Analysis (pre-specified)
Open loop, per configuration: Δ (SWS − DATA) of DNa02 ipsi steady state averaged over 6–9 and 9–12 mV and over the configuration's
own window [I_th10(DATA), I_th10(DATA) + 3 mV]; Δ thresholds I_th10/I_th30; Δ small-signal gain G (E6) at I0 5–9; hierarchical
bootstrap CI95 (RNG 8 419 020). Q2/Q7: sign of each Δ per configuration; Q6 "functionally equivalent" for a configuration when
the CI95 of Δ DNa02 (own window) lies within ±5 Hz AND of Δ G within ±10 % of DATA's G (engineering tolerances fixed now).
Interaction contrasts in the two 2×2 blocks: (Δ_A1B1 − Δ_A0B1) − (Δ_A1B0 − Δ_A0B0) with bootstrap CI.
Closed loop, per configuration and stratum: d = err(DATA) − err(SWS); mean with cluster bootstrap CI95 (clusters = SWS instance,
RNG 8 419 021); median; zero pairs; pairs where only one network moved. Q8: across the 8 configurations, Spearman between the
open-loop Δ (own window) and closed-loop d per stratum (n = 8 — descriptive only). Statement "effect only in a narrow regime" if
the CI of d excludes 0 in ≤ 2 of 8 configurations. Regulator P is reported once as a reference.
Multiplicity: 16 configurations × several metrics — no p-value is used for a decision; CIs are descriptive.

## 6. Stop rules / outputs
Stage 1 / protected files before and after; any simulator error is reported (limit: abort a configuration after 5 errors).
Outputs `results/v6/` (openloop/raw, closedloop/*.jsonl, calibration.json, analysis*.json, figures, REPORT.md).
