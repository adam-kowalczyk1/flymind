# V5 v4.1 — Open-loop response characterization (EXPLORATORY DIAGNOSTIC) — protocol r1, written 2026-10-30 before any run

Status: exploratory. No confirmatory decision, no confirmatory seed pool. Written and hashed before the main run; a smoke test
(seeds 8 490 0xx, outputs in the session scratchpad, not analysed) only checks the pipeline. Any later change → r2 with reason.

## 0. Prior knowledge (explicit)
- V5 v4 (confirmatory, closed loop): DATA − SWS = +0.51° in S1 (ρ 0.16–0.22, strong drive; SWS better) and −0.52° in S2
  (ρ 0.22–0.28, weak drive; DATA better). The sign depends on regime.
- v6_stability (exploratory, ONE SWS instance, seed 1401): the 30 Hz threshold of ipsilateral DNa02 is slightly higher for SWS
  (Δg30 > 0 in 18/20 settings, ≤ 0.014 g ≈ 0.17 mV). The calibration of the shared decoder (azimuths −30…30°, mostly strong drive)
  equalises a small-signal slope (SWS 0.988–1.005 × DATA) but not thresholds.
- User brief: an independent audit suggested SWS has a weaker steady-state response than DATA under weak drive (~6–9 mV LC10a
  current). The source of that statement was not found in the repository (recon task C checks); it is treated as a hypothesis.
- LC10a current = 12 mV · g (encoder, ENGINEERING); ALIF threshold gap v_th − v_rest = 7 mV (MODEL).

## 1. Question
Do DATA and SWS v2 networks respond differently to IDENTICAL controlled LC10a input currents in the weak-drive range, without
target, camera, MuJoCo or closed-loop feedback? Where along the pathway (LC10a → intermediates → DNa02) does any difference appear,
and does it survive changes of initial state, noise and input range?

Predictions (written now; not decision criteria): P1 ipsilateral DNa02 steady-state rate SWS < DATA for I ≈ 6–9 mV;
P2 the difference shrinks for I ≥ 10 mV; P3 the difference is already present in the LC10a population (LC×LC recurrence).

## 2. Networks (unit of between-network inference = network instance)
- DATA (DATA + MODEL): `visual_path.network(0.2)` — 424 neurons (LC10a L 135 / R 140, mid L 58 / R 89, DNa02 L/R), data edges only.
- SWS_k, k = 1..50 (CONTROL): `side_shuffle.shuffle_within_side(spec, layer_side_labels(spec, idx), 8 410 000 + k)` — unchanged
  frozen code. Required checks per instance BEFORE simulation: all 17 `side_shuffle.KEYS` properties True, `complete` True.
  Independence checks: 50 distinct W (sha256 of W_data bytes), pairwise Jaccard of the changed-edge sets, LC×LC reciprocity per
  instance; instances are generated from distinct seeds by the same procedure — independent draws, not copies.
- No new network code; ALIF dynamics = `alif.ALIF` unchanged (`ALIFParams(noise=2.0)`, dt 1 ms, as in the closed loop).

## 3. Input schedules (identical for all 51 networks; current in mV to LC10a of the stated side, all other neurons 0)
Common random numbers: repetition r = 1..8 uses ALIF seed 8 411 000 + r for every network (paired noise across networks).
Both sides are driven separately (ipsi = driven side; DNa02 ipsi = DNa02 of that side).
- E1 STEP-UNI (primary): rest → constant I on ipsi LC10a for 1000 ms, contra 0. Levels: 4.0–12.0 step 0.25 plus 6.0–10.0 step
  0.125 (49 levels). Noise 2 mV, 8 reps; plus noise 0 (deterministic), 1 rep.
- E2 STEP-BILAT: ipsi I, contra 0.5·I (overlap of the two encoder "eyes"), 6.0–10.0 step 0.25 (17 levels), 8 reps.
- E3 PRE-ADAPTED initial state: 500 ms ipsi at 10 mV, then step to I (6.0–10.0 step 0.25) for 1000 ms; variant E3c: the 500 ms
  pre-drive is on the CONTRA side. 8 reps.
- E4 RAMP (hysteresis): ipsi I linear 4 → 12 mV over 4000 ms, then 12 → 4 mV over 4000 ms. 8 reps.
- E5 RANDOM INITIAL v: v(0) ~ U(v_rest, v_th) per neuron (RNG 8 412 000 + r), then E1 step, levels 6.0–10.0 step 0.5, 8 reps.

## 4. Measurements (per run; 10 ms bins)
Population spike counts per bin: LC10a ipsi, LC10a contra, mid L, mid R, DNa02 L, DNa02 R; mean adaptation a per population
(LC10a ipsi, mid, DNa02 ipsi) at bin ends; per-neuron rates in the steady-state window (rep-averaged).
Derived (pre-specified):
1. steady-state rate = mean rate 500–1000 ms after step onset (E1/E2/E3/E5); 2. population rates as above;
3. adaptation a at end of step; 4. pre-decoder output D = DNa02_L − DNa02_R rate [Hz];
5. post-decoder output = common DATA decoder, angle = (D − offset)/slope with offset 0, slope 492.1187 Hz/rad (the frozen V5 v4
   DATA decoder, `results/v5v4/run_meta_A_*.json`), reported in degrees; also the full SteerDecoder filter chain (τ_rate 50 ms,
   τ_s 0.1 s) final value; 6. steady state as 1; 7. transient = peak of the 20 ms-binned DNa02 ipsi rate in 0–150 ms and
   peak/steady ratio; 8. latency = time of the first DNa02 ipsi spike after onset (censored at 1000 ms), and t_half = first time the
   τ 50 ms-filtered DNa02 ipsi rate reaches half its steady state; 9. input-output slope = finite-difference dR/dI of steady state;
   10. thresholds I_th10 / I_th30 = interpolated current where rep-mean DNa02 ipsi steady state reaches 10 / 30 Hz, and LC10a
   threshold I_LC1 (LC10a ipsi mean ≥ 1 Hz); 11. saturation = fraction of neurons ≥ 0.9 r_max (r_max 250 Hz) and DNa02 / r_max;
   12. hysteresis (E4) = mean and max |up − down| DNa02 ipsi rate at equal I (0.25 mV bins), and threshold shift up vs down;
   13. variability: between-instance SD (of rep means) and within-instance SD (across reps).
No decoder is fitted per instance (common DATA decoder only).

## 5. Analysis plan (pre-specified, descriptive / estimation; no confirmatory test)
- For each metric m and level I: Δ_k(I) = m_SWS_k(I) − m_DATA(I). Report mean Δ over k, hierarchical bootstrap CI95 (B 10 000,
  RNG 8 419 001: resample instances; within DATA and within each resampled instance resample reps), between-instance SD,
  within-instance SD, DATA's rank: fraction of SWS instances with m_SWS ≥ m_DATA (two-sided "DATA is extreme" if < 2.5 % or > 97.5 %),
  standardised Δ / SD_between. Repetitions of one network are never treated as independent networks.
- Ranges: 6–10 mV (primary), 6–8, 8–10, 4–12 (sensitivity); integrated difference over a range = mean over levels.
- Sensitivity: noise 0 vs 2 (E1), initial state E1 vs E3 vs E3c vs E5, unilateral vs bilateral (E2), side L vs R.
- Decoded angle: compare Δ (degrees) to SESOI 0.5°; claim "exceeds SESOI" only if the whole CI95 lies beyond ±0.5°.
- Mechanism (descriptive): Δ along the pathway (LC10a ipsi → mid ipsi/contra → DNa02); across instances, Spearman correlation of
  ΔDNa02 (6–9 mV) with ΔLC10a rate, LC×LC reciprocity, LC×LC triangle count (CI by bootstrap over instances, RNG 8 419 002).
  Pre-written interpretation rule: a difference already present in LC10a ipsi rates (beyond between-instance spread) locates the
  origin at the LC10a layer (LC×LC recurrence or mid→LC feedback — not separable here, v4.2); identical LC10a rates with different
  DNa02 locates it downstream. Attribution to single blocks is deferred to V5 v4.2. ALIF-vs-connectivity is deferred to V6.
- Multiplicity: many levels × metrics; everything is descriptive. Patterns must be consistent across neighbouring levels and sides
  to be called a pattern.

## 6. Validity / stop rules
STOP if: Stage 1 ≠ 28/28 or any protected file changes (integrity_v5v41.py before/after); any SWS instance fails a property;
duplicate W among instances; NaN/inf in state. All instances and all runs are reported; no exclusions.

## 7. Outputs (`flymind/results/v5v41/`)
config.json, instances.json (checks), raw_E*.npz, analysis.json, figures/*.png, REPORT.md, integrity_*.txt. Code: `flymind/v5v41.py`
(runner), `flymind/v5v41_analysis.py` (analysis), `flymind/test_v5v41.py`. Independent re-analysis by a separate implementation.

## 8. Labels
DATA: connectome-derived network (edges, weights ∝ synapse counts, NT signs). MODEL: ALIF, J0 0.2, Glu = inhibitory, noise.
ENGINEERING: the mV range (12 mV · g from the encoder) — no camera here. CONTROL: SWS v2, common decoder, CRN noise.
Results concern this model, not the fly.
