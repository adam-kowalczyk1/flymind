# V6.1 — Direct drive manipulation (EXPLORATORY) — protocol r1, 2026-10-30 ~09:00 (before any V5 v4.1+ result was inspected)

## 1. Question
In V5 v4 the DATA − SWS difference changed sign between near (S1) and far (S2) targets. Distance changes the neural drive
(LC10a current = I_max · g, g from the encoder) but also image size, geometry and loop dynamics. Is the sign governed by the DRIVE
itself? Drive is manipulated independently of target distance, azimuth, camera geometry and MuJoCo motion.

## 2. Open loop (no camera, no MuJoCo, no feedback) — already measured
V5 v4.1 E1/E2/E6 and V5 v4.2 (block families) deliver DATA vs SWS (and single-block) responses at controlled LC10a currents
4–12 mV incl. 6–10 mV. V6.1 re-uses them; no new open-loop simulation except the toy relay below.
Simplified relay control (MODEL; `loop_v2.toy_relay`, unchanged): E1 + E6 at default ALIF, 4 reps (seeds 8 411 001–004) — a
reference for what a network with no intermediate layer does at the same drive.

## 3. Closed loop with fixed geometry, varied drive gain (ENGINEERING manipulation)
The encoder output scale I_max (mV per unit g) is set to 8, 10, 12 (default), 14, 16 mV; camera, scene geometry, encoder
saturation, decoder (the D0 DATA decoder of V6, calibrated at I_max 12 — NOT recalibrated, so only the drive changes), safety
layer and ALIF default are unchanged. Scenes: the V6 scene set (seeds 8 600 001–120; S1 40, S2 80); I_max 12 = V6 D0 trials
(re-used, not re-run). Pairs: DATA vs SWS instance ((i − 1) mod 50) + 1; family X of V6 (if selected) as third network.
Prediction if the sign is drive-governed: d(S1) moves toward DATA-better (negative) as I_max decreases, d(S2) toward SWS-better
(positive) as I_max increases; i.e. d depends on I_max·g, not on ρ. If d keeps the stratum sign at every I_max, drive alone does
not explain the flip (geometry/dynamics confound remains).

## 4. Analysis (pre-specified)
d = err(DATA) − err(ctrl) per I_max × stratum, mean with cluster bootstrap CI95 (clusters = SWS instance, RNG 8 419 030), median,
zero pairs, only-one-moved counts. Drive index per trial: initial LC10a drive of the scene, max(g_L, g_R)·I_max at t = 0, computed
from the first camera frame (recorded per trial by re-encoding the initial render, ENGINEERING). Descriptive model:
d ~ drive_index + ρ (OLS, cluster-robust bootstrap) pooled over I_max; the coefficient on ρ conditional on drive tells whether
distance matters beyond drive. Not causal beyond the manipulated factor (I_max).
Outputs `results/v61/`.
