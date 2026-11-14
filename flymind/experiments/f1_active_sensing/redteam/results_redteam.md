# F1 Stage 0 confirmatory results: red-team review (read-only)

MODEL experiment (ALIF network on MaleCNS-derived wiring + engineering encoder). Nothing here concerns a real fly.
Scope: results/analysis_confirm.json recomputed from results/confirm/u*.feather and u*.npz with independent code (analysis.py not called).

**VERDICT: PASS_WITH_ISSUES.** The numbers reproduce exactly and the protocol was followed. The main problem is interpretation.

## Reproduction (all agree with analysis_confirm.json)
- H1 arms: BSC(DATA, D, stat) = 0.325 and BSC(DATA, D, sin_f0.5_A4) = 0.4275.
  - Criterion c = 0 for both, FA = 0.
  - My own bootstrap: Δ = 0.1025, CI95 [0.0675, 0.140], CI90 [0.0725, 0.135].
- S1 = 0.065, S2 = 0.000, S3 = −0.020, S4 = −0.020, S6 = −0.0025.
  - S6 was recomputed from the stored g with systems.thresh_D and lowpass_drive: Δ(TH_LP) = 0.105, Δ(TH) = 0.105.
- Data integrity:
  - 200 units (9102001–9102200), 200 feather and 200 npz files, 93 rows each, 0 NaN, no missing or extra units.
  - All rows carry manifest sha e3e3be9f…, which equals the sha256 of manifest_confirm.json. run_meta shows errors [] and Stage-1 pre/post OK.
  - Pilot units 9101001–060 do not overlap with confirm.
  - Per-unit rho and az match `default_rng([u,2])` (checked for 2 units).
  - Manifest hashes of analysis.py, PROTOCOL.md, protocol.json and confirm_params.json are unchanged. Only figures.py differs from the manifest (post-hoc plotting, harmless).
- Stimuli (npz theta, cam_R, bearing):
  - stat is all zeros.
  - sin: amplitude exactly 4°, residual vs A·sin(2πft+φ_u) = 0.
  - jshuf: window and pre-window multisets equal sin's, RMS = A/√2 and mean = 0 exactly.
  - jrms and jvel: RMS and mean exact. jvel velocity ratio 0.805–1.198, at most 18 draws.
  - MT: cam_R constant and bearing = az0 − θ to 5e-16.
  - bearing = az0 − θ in the camera-rotation conditions.

## Findings

**1. MAJOR — interpretation: "memoryless threshold" is wrong, "low-pass threshold" is only partly right.**
- Memoryless TH shows no sensitivity to temporal structure: TH sin − jshuf = +0.005.
- DATA shows S1 = +0.065, so it is sensitive.
- DATA jshuf = jrms = 0.3625 (peaks 2.1×A for jrms), and jvel = sin = 0.4275. Peak height alone does not explain the benefit; dwell near the peak does.
- TH_LP (τ = 20 ms, θ fitted to stat) reproduces DATA only for slow motion: jshuf 0.4075 vs 0.3625, jrms 0.420 vs 0.3625. Its S1 would be 0.0375.
- Re-running TH_LP at other τ: τ = 40–80 ms gives jshuf 0.38–0.365 and jrms 0.387–0.358, which matches DATA. So DATA behaves like a threshold on a slow integrator (τ ≈ 40–80 ms), not τ = 20 ms.
- S6 equivalence is therefore evidence about slow sinusoids only. θ_LP was fitted to DATA's stationary BSC (one free parameter).
- Wording: "the benefit is reproduced by a threshold on a low-pass-filtered encoder drive, with τ ≥ 40 ms needed to mimic the SNN's insensitivity to fast jitter; it is not specific to the SNN".

**2. MAJOR — the benefit comes from the encoder's eccentricity ramp, not from any wiring.**
- The encoder has S_L = σ(az/10°), which is an engineering parameter.
- The ipsi drive correlates r = −0.98 with θ (mean over units). Its half peak-to-peak is 11.8% of the mean at A = 4°.
- Window-mean ipsi drive is unchanged: 5.495 → 5.481 mV (−0.3%).
- Window-max drive rises: 5.68 → 6.10 mV.
- Fraction of time above 5.93 mV is not increased: 0.339 → 0.336 for L and 0.279 → 0.261 for R.
- What does the work is brief or sustained threshold crossing, which is the "ever crosses" statistic of the c = 0 rule.
- Wording: "the effect depends on the encoder gain slope at |az| 8–12° and on the target sitting near the SNN's effective threshold of about 5.9 mV (drive ≥ 5.9 mV separates hits from misses; AUC 0.999)".

**3. MAJOR — the effect is operating-point dependent.**
- For TH, Δ(sin − stat) is 0.005 at θ = 4 mV (ceiling) and 0.010 at 8 mV (floor), against 0.10–0.18 at 5–7 mV.
- P (linear, FA 5%) is at BSC = 1.0 over the whole of range D, whereas DATA has BSC 0.43.
- The "benefit" partly recovers a loss that the spike threshold itself introduces.
- Range D was chosen so that DATA's threshold sits inside it.
- Because the range is 0.14 m wide, SESOI 0.07 BSC = 1 cm. The 1.4 cm shift is about 5% of the roughly 26.5 cm stationary threshold.

**4. MINOR/MAJOR — wording of the H1 and S1 classifications.**
- H1: SUPPORTED is correct per rule: est 0.1025 ≥ 0.07 and CI95 > 0. But the CI95 lower bound is 0.0675, i.e. below SESOI. Say "detectably positive, point estimate above SESOI, lower bound at SESOI (≈ 0.95 cm)".
- S1: DETECTABLE-BELOW-SESOI is the literal output of `classify`.
  - Rule order: SUPPORTED needs est ≥ 0.07 (0.065 fails). EQUIVALENT needs CI90 ⊂ (−0.07, 0.07), but CI90 = [0.045, 0.085] fails. DETECTABLE then applies, since CI95 excludes 0.
  - The code follows PROTOCOL §8 and the CI95/CI90 use is correct.
  - The label misleads: the CI includes values above SESOI (up to 0.09), so "below SESOI" is not established.
  - Wording: "S1 = +0.065 [0.042, 0.090]: positive, point estimate just under SESOI, SESOI not excluded".
- Every other class matches the rules, including S2, S3, S4 and S6 EQUIVALENT.
- F-b fires through S2 only. Report it as "no periodicity specificity, but partial dependence on slow temporal structure (S1)".

**5. MINOR — FA comparison is fair but vacuous.**
- DATA no-target D = 0 in all 200 trials under stat and under every motion condition. Max no-target drive is 0.035 mV, far below the 5.9 mV threshold.
- Motion does not change the FA rate.
- Upper bound on FA with 200 trials is about 1.5%.
- The FA-matched criterion is vacuous and the hit rate is for a distractor-free scene. P's FA is 0.05 while DATA's is 0, so cross-system BSC is not FA-matched. Only within-system Δ is interpretable.

**6. MINOR — sensitivity to the response criterion.**
- Δ(c) with a spike-count criterion on |D|: 0.103 for c ≤ 5, 0.070 at c = 10, 0.042 at c = 20.
- The benefit shrinks if more than a few DNa02 spikes are demanded. Report as "at c = 0".

**7. MINOR — other checks.**
- The J_shuf velocity ratio is 19.6–24.7× the sinusoid's, versus "3–12×" in PROTOCOL §8.
- Per-instance table: DATA Δ ranks 12 of 20 controls. Wiring non-specificity holds only against the B1 (LCxLC block) and SWS shuffles, not against removal of the LC10a→DNa02 path.
- The hit rate by az tercile is 0.104 / 0.114 / 0.090, so there is no eccentricity artifact within 8–12°.
- No wrong-side response occurred in any condition. Hit_L 0.455 vs hit_R 0.40 shows scene asymmetry, and F-h is not triggered.
- sin and jvel D are 98% correlated (common random numbers), so the identical BSC 0.4275 is plausible and not a data duplication.
- The stored `k` column is from the range-C draw and is unused in range D (k = 1).
- results/robust has 490 files but there is no analysis_robust.json. F-g (0D) is unevaluated, so the Stage-1 recommendation rule (not F-g) is not yet satisfiable.
- 17 of 20 B1/SWS Δ values exceed 0.07 (per_instance), consistent with S3 and S4.
- 11 of 16 grid cells are Holm-positive. Only A = 4 cells are SUPPORTED, A ≤ 2° are EQUIVALENT, and the effect is flat in f (0.08–0.103).

## Recommended headline
"In this model, a self-generated 4° / 0.5 Hz camera rotation shifts the stationary-target detection distance by about 1.4 cm (BSC +0.10 [0.07, 0.14], FA = 0, distractor-free). The shift is reproduced by a low-pass threshold control, by wiring-shuffled networks, and by aperiodic motion of matched RMS and velocity. It is an encoder-gain × spike-threshold effect, not an SNN-, wiring- or periodicity-specific one."
