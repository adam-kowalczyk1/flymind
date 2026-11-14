# V7 — Robustness and generalization beyond the V5 v4 operating regime (EXPLORATORY) — protocol r1, 2026-10-30 ~09:00
Drafted before any V5 v4.1+ result was inspected. V5 v4 conclusions are limited to ρ 0.16–0.28 m, |az0| < 30°, J0 0.2, default ALIF
and encoder. V7 asks whether the DATA vs SWS pattern and the SNN-vs-P comparison survive outside that box. Nothing here widens
any earlier conclusion; V7 results are reported for their own region only.

## 1. Dimensions (each a separate scene set; seeds 8 700 001+ by block, registry)
| Block | Seeds | ρ [m] | az0 | Other | Why |
|---|---|---|---|---|---|
| G1 far | 8 700 001–120 | U[0.28, 0.40) | U(−30°, 30°) | default | untested far region (V5 v3 had 0.28–0.35 partially) |
| G2 wide azimuth | 8 700 201–320 | U[0.16, 0.28) | U(30°, 40°) × random sign | default | larger initial errors, near field-of-view edge |
| G3 noise | 8 700 401–520 | U[0.16, 0.28) | U(−30°, 30°) | ALIF σ 6 mV | input/neural noise (membrane SD ≈ 0.96 mV vs 0.32) |
| G4 near | 8 700 601–720 | U[0.12, 0.16) | U(−30°, 30°) | default | very strong drive (closer than any confirmatory scene) |
Conditions: DATA, SWS (instance ((i − 1) mod 50) + 1 from 8 410 001–050), P. Decoder: V6 D0 DATA decoder (G3: the V6 SG6 decoder).
Initial orientation: the arm always starts at pan 0 and the target bearing az0 is the initial error (initial orientation and
azimuth are the same variable in this task). Moving targets and simulation-condition changes (lighting, distractors) are NOT
run here (they need new scene code — would be new engineering, not a robustness check of the current model); listed as open.

## 2. Analysis (pre-specified, descriptive)
Per block: mean/median final error per condition; d = err(DATA) − err(SWS) with cluster bootstrap CI95 (RNG 8 419 040); success,
movement, overshoot; DATA − P. Statement rules: "pattern holds" only if the V5 v4 stratum sign is reproduced with a CI excluding 0
in the corresponding drive regime; otherwise "not shown". No pooling with V5 v4 data.
Outputs `results/v7/`.
