# RT1 — Independent re-analysis of V5 v4.1 (E1, E1n0, E6) from raw npz

Date 2026-10-30. Scope: E1 / E1n0 steady-state DNa02, LC10a and intermediate ("mid") rates, thresholds, the mechanism
correlation, and the E6 small-signal gain. The code is my own. I did not import, copy or read `v5v41_analysis.py` or
`v5v41_e6_analysis.py`. I read `v5v41.py` / `v5v41_e6.py` only to learn the array layouts.

- Scripts: `/private/tmp/claude-501/-Users-admin-so101-fly-project/075990a2-3231-4039-8d41-31f3fdcb9204/scratchpad/rt41/RT1/reanalysis.py`
  and `.../rt41/RT1/extra.py`.
- Outputs: `.../rt41/RT1/reanalysis_out.json` and `.../rt41/RT1/extra_out.json`.
- Seeds: bootstrap RNG **8495101** (red-team pool), B = 10 000. The spot re-simulation used only the registered objects:
  DATA, SWS 8410001 and SWS 8410050, with noise seeds 8411001, 8411004 and 8411008. I ran no other simulation.
- Labels: DATA = the connectome network. MODEL = ALIF, J0, noise. CONTROL = SWS v2, CRN, the common decoder.
  ENGINEERING = the mV scale. All results describe this model, not the fly.

## Verdict: **PASS_WITH_LIMITATIONS**

Every headline number is reproduced, and the raw data can be regenerated bit-exactly. The direction of the E1 result
(DATA > SWS for DNa02 ipsi, 6–10 mV) is very robust. Three of the author's claims are over-read: the "between-instance SD",
the mechanism correlation, and the "DATA higher at 6–9 mV" claim for E6. Details follow.

## 1. Definitions I used (from the runner layout)

- `E1_counts[level, side(L,R), rep, 10 ms bin, pop]`, with pops = (LC ipsi, LC contra, mid_L, mid_R, DN_L, DN_R).
- `n_pop = [in_L 135, in_R 140, mid_L 58, mid_R 89, 1, 1]`. LC ipsi is divided by in_L for side L and by in_R for side R.
  DN ipsi is DN_L for side L and DN_R for side R. Mid ipsi is mid_L for side L and mid_R for side R.
- Steady state = 500–1000 ms after onset (bins 50–99), in Hz.
- Per network: the mean over 8 reps and both sides.
- Range metric: I first used a plain mean over levels. That gave small mismatches (see §2). The author's numbers are
  reproduced exactly by a **trapezoidal integral over I divided by the range width**, and I adopted that rule for every
  comparison below.
- Bootstrap: resample the 50 instances; within each one, resample its 8 reps. Resample DATA's 8 reps independently.
- E6: D = DN_L − DN_R in the steady state. G_small is the OLS slope of D on δ over |δ| ≤ 1. Because the slope is linear in
  D, the mean of per-rep slopes equals the slope of the rep-mean, so the bootstrap runs on per-rep slopes.

## 2. Reproduction of the reported numbers (mine vs analysis.json / analysis_E6.json)

| Quantity (E1, noise 2) | Mine | Author | Match |
|---|---|---|---|
| DN ipsi 6–10: DATA / SWS mean | 86.559 / 68.552 | 86.559 / 68.552 | exact |
| Δ 6–10 [CI95] | −18.006 [−18.79; −17.19] | −18.006 [−18.80; −17.19] | exact (CI to ±0.03, Monte Carlo) |
| Δ 6–8 / Δ 8–10 | −13.041 / −22.972 | −13.041 / −22.972 | exact |
| Δ 6–9 / Δ 4–12 | −17.434 / −8.376 | same | exact |
| SD between (6–10) | 0.344 | 0.344 | exact |
| SWS ≥ DATA (6–10) | 0/50 | frac 0.00 | exact |
| LC ipsi 6–10: DATA / Δ | 13.273 / +0.103 [0.06; 0.14] | 13.273 / +0.103 | exact |
| Mid ipsi 6–10 Δ | −1.155 [−1.24; −1.08] | −1.155 | exact |
| I_th10: DATA (L,R) / SWS | 5.993 (6.023, 5.963) / 6.086 | same | exact; per-instance max diff 0 |
| I_th30: DATA / SWS | 6.491 / 6.662 | same | exact |
| I_LC1: DATA / SWS | 5.992 / 6.031 | same | exact |
| E1n0 Δ 6–10 | −6.883 | −6.883 | exact |
| Mechanism ρ(dDN, dLC), 6–9 | 0.590 | 0.591 | dDN per instance identical (max diff 2e−14) |
| Per-level DN ipsi, all 49 levels | — | — | max abs diff 0.0 (DATA and SWS mean) |
| E6 G_small DATA / SWS at I0 = 6, 7, 8, 9, 10, 11 | 33.25/26.98, 36.75/21.09, 39.15/32.30, 48.35/43.39, 43.75/65.11, 36.05/37.78 | same | exact |
| E6 G_small Δ CI at 7 mV | [−21.15; −10.80] | [−21.35; −10.81] | within Monte Carlo error |
| E6 D curves (all I0, δ) | — | — | max abs diff 0.0 |

**Discrepancies found:**

1. **D1: the range-averaging rule is not stated in the protocol.** §5 of the protocol says "mean over levels", but
   analysis.json uses a trapezoidal integral over the 0.125/0.25-mV mixed grid. This is not an error, and it is arguably
   the right choice for a non-uniform grid. The results do depend on it, though:
   - Plain mean over levels: Δ 6–10 = −17.67, Δ 4–12 = **−11.36** (author −8.38), LC 4–12 = +0.19 (author +0.23).
   - Only the 0.25-mV grid: Δ 6–10 = −16.93 and LC ipsi 6–8 = **+0.06**. The author's −0.08 changes sign.

   Recommendation: state "trapezoid / width" in the report.
2. Nothing else. Every count and every value of `frac_ctrl_ge_data` agrees.
3. **Integrity: the stored data regenerate exactly.**
   - Re-simulating with `v5v41.simulate` reproduces the stored counts bit-exactly in all 15 checks. That covers E1 at
     8 mV, sides L and R, reps 1 and 8, plus E6 at I0 = 7, δ = +0.5, rep 4, for DATA, SWS_8410001 and SWS_8410050.
     The W sha256 values match instances.json.
   - E6 runs at (I0 = 5, δ = +2) are bit-identical to the E1 runs at 6.0 mV, side L. The contra LC side at 4 mV fires
     0 spikes, and the noise draws are shared. This explains why std_delta is identical to 12 digits at E1 6.0 mV and
     E6 G_all at 5 mV. It is consistent, not a bug.

## 3. Robustness of "all 50 SWS below DATA" (DN ipsi)

| Window | Range | Both sides: Δ [CI], n below | Side L: Δ, n below | Side R: Δ, n below | Median-of-instances Δ |
|---|---|---|---|---|---|
| 500–1000 | 6–10 | −18.01 [−18.77; −17.20], 50 | −18.77, 50 | −17.24, 50 | −18.02 |
| 500–1000 | 6–8 | −13.04, 50 | −12.74, 50 | −13.34, 50 | −13.02 |
| 500–1000 | 8–10 | −22.97, 50 | −24.80, 50 | −21.14, 50 | −22.98 |
| 300–1000 | 6–10 | −16.83 [−17.64; −16.16], 50 | −17.90, 50 | −15.76, 50 | −16.84 |
| 300–1000 | 6–8 / 8–10 | −13.15 / −20.51, 50 / 50 | 50 / 50 | 50 / 50 | — |
| 700–1000 | 6–10 | −16.66 [−18.66; −14.77], 50 | −17.34, 50 | −15.98, 50 | −16.68 |
| 700–1000 | 6–8 / 8–10 | −12.68 / −20.64, 50 / 50 | 50 / 50 | 50 / 50 | — |

**Per rep, using the CRN pairing (SWS_k rep r vs DATA rep r):** 50/50 below in all 8 reps, in all windows and ranges.
- In 6–10 at 500–1000, the highest single SWS (instance, rep) value is 71.8 Hz. The lowest DATA rep is 84.9 Hz.
- Taking the median over reps instead of the mean gives Δ −18.20, still 50/50 below.

**Per level (noise 2):** all 33 levels from 6 to 10 mV have 50/50 SWS below DATA.

**Answer:** the claim "all 50 below DATA" holds per side, per rep, per window (300, 500 and 700 to 1000 ms), and with a
median. The size of Δ moves by at most about 1.4 Hz across windows and about 1.5 Hz between sides.

**Other pathway stages:**
- Mid ipsi: Δ −1.07 to −1.16 Hz, 50/50 below in every window and side.
- LC ipsi is window- and side-dependent in direction, although tiny in magnitude:
  - 6–10: +0.08 to +0.12 Hz. With the 700–1000 window, side L, only 21/50 SWS are above DATA.
  - 6–8: −0.01 to −0.17 Hz. Side L, 500–1000: 31/50 below.
  - "LC nearly identical" is fine as a statement of magnitude. Any directional LC statement is not robust.

## 4. Findings that limit interpretation

**L1. The "between-instance SD 0.34 Hz" is pure sampling noise, not structural spread.**
- I ran a two-way (instance × CRN-rep) decomposition of the per-rep DN ipsi 6–10 values over the 50 SWS instances:
  MS_instance 0.95, MS_residual 0.82, MS_rep 12.5.
- That gives F_instance = 1.16 (two-way) or 0.90 (one-way). The estimated structural variance between instances is 0.
- If there were no structure at all, the expected SD between instances would be √(MS_within/8) = 0.36 Hz. The observed
  value is 0.34.
- So the 50 instances are statistically indistinguishable from each other. std_delta = −52 is Δ divided by a noise SE,
  not by a structural spread, so it should not be quoted as an effect size.
- The large rep effect shows that the shared noise seed drives correlated responses across all SWS networks. The SWS
  family is close to one dynamical object.
- The DATA-vs-family difference itself is real and robust (§3). Its uncertainty is dominated by DATA's own 8 reps:
  within-rep SD 1.22, SE ≈ 0.43.

**L2. The mechanism correlation ρ(dDN, dLC) = 0.59 is trial-noise covariation, not a structural mechanism.**

| Estimate | Value |
|---|---|
| LC from reps 1–4 vs DN from reps 5–8 | ρ = −0.09 |
| LC from reps 5–8 vs DN from reps 1–4 | ρ = +0.10 |
| Same half (reps 1–4 / reps 5–8) | 0.70 / 0.65 |
| Split-half reliability of dDN across instances | ρ = 0.09 |
| Split-half reliability of dLC across instances | ρ = −0.04 |
| Within-instance trial-level correlation (DN vs LC, rep deviations) | r = 0.69 |
| dDN at noise 0 vs dDN at noise 2 | ρ = 0.12 |

- The correlation exists only when DN and LC come from the same runs. The instance ranking has almost no reliability.
- At noise 0, ρ = 0.62, but that is a single deterministic realisation per network, and it does not predict the noise-2
  ranking.
- The dDN range across instances is −18.09 to −16.70; the dLC range is ±0.06 Hz.
- Recommendation: withdraw ρ = 0.59 (and its CI 0.38–0.76) as evidence that LC-level variation drives DN differences.
  The reciprocity and triangle correlations are also uninformative, because the SWS family is homogeneous: LC
  reciprocal pairs are 511–604, against DATA 2450.

**L3. The E6 claim "DATA higher at I0 6–9 mV" is window- and estimator-sensitive at 8–9 mV.**

| I0 | G_small Δ, 500–1000 (SWS ≥ DATA) | 300–1000 | 700–1000 | G_all Δ, 500–1000 |
|---|---|---|---|---|
| 6 | −6.27 (0/50) | −9.49 (0/50) | −13.01 (0/50) | −5.21 (0/50) |
| 7 | −15.66 (0/50) | −12.01 (0/50) | −11.45 (0/50) | −11.25 (0/50) |
| 8 | −6.85 (0/50) | −9.41 (0/50) | −2.28 (**6/50**) | −9.78 (0/50) |
| 9 | −4.96 (0/50) | **+5.89 (50/50)** | −7.96 (0/50) | **+2.69 (48/50)** |
| 10 | +21.36 (50/50) | +16.75 (50/50) | +10.04 (50/50) | +14.13 (50/50) |
| 11 | +1.73 (43/50) | −1.73 (3/50) | +4.69 (46/50) | +2.89 (50/50) |

- Robust: DATA higher at 6–7 mV; SWS higher at 10 mV.
- 8 mV is mostly DATA-higher, but small at 700–1000. 9 mV flips sign with the window and with G_all. 11 mV is
  indeterminate.
- DATA's G_small is one network with a per-rep SD of 4–9 Hz/mV, so the "0/50" and "50/50" counts mainly reflect DATA's
  single noisy estimate against a tight SWS family. Leave-one-rep-out ranges for DATA are ±1–2 Hz/mV.
- Amendment prediction "E6 ΔG has the same sign as E1 Δ at the same I0": fails at 10 mV. E1 at 10 mV has SWS lower
  (ratio 0.96), while E6 G_small has SWS higher.

**L4. "Thresholds nearly equal" is true in mV, but the shift is systematic and accounts for a material part of Δ.**
- I_th10: +0.093 mV, 50/50 SWS > DATA (side L 50/50, side R 49/50).
- I_th30: +0.172 mV, 50/50.
- Shifting the DATA E1 curve right by 0.093 mV / 0.172 mV reproduces −3.6 Hz / −6.6 Hz of the −18.0 Hz Δ (6–10), i.e.
  20–37 %. The remainder is a gain reduction: SWS/DATA ratio 0.73–0.85 from 6.5 to 9.5 mV, rising to 0.96 at 10 mV.
- "Same threshold, lower gain" should be written as "a small systematic threshold shift plus a gain reduction".

**L5. The weak-drive (6–8 mV) effect depends heavily on noise.**
- Noise 0: Δ 6–8 = −0.84 Hz (noise 2: −13.0), and Δ 6–10 = −6.9 Hz.
- At noise 0, only 7 of the 33 levels in 6–10 mV have all 50 SWS below DATA. At some levels, no SWS instance is below
  DATA.
- At noise 0, I_th10 is equal (7.161 vs 7.159 mV), and I_th30 is higher for SWS on side R (49/50) but not on side L
  (6/50).
- The 2 mV noise (MODEL) is part of the effect, so the effect should be reported as a noise × network interaction.

**L6. Side asymmetry.** Both families respond more strongly on side R: E1 DATA 6–10 is L 83.3 / R 89.9, and E6 has a
negative D at δ = 0. Δ is a little larger on side L (−18.8 vs −17.2). The conclusions are the same on both sides.

## 5. Summary of claims checked

| Claim | Status |
|---|---|
| E1 DN ipsi 6–10: DATA 86.6, Δ −18.0 [−18.8; −17.2] | REPRODUCED (trapezoid rule; plain mean −17.7) |
| All 50 SWS below DATA | REPRODUCED and ROBUST (per side, rep, window, median; all 33 levels) |
| SD between 0.34 Hz | REPRODUCED, but it is a noise floor (F ≈ 1); it must not be read as structural homogeneity or as an effect size |
| LC ipsi +0.10 of 13.3 | REPRODUCED; magnitude robust, direction not robust (sign depends on range, weighting, side, window) |
| Mid ipsi −1.16 | REPRODUCED (−1.155) and robust |
| I_th10 5.99 vs 6.09 | REPRODUCED; systematic shift (50/50), explains 20–37 % of Δ |
| Noise 0: Δ −6.9 | REPRODUCED; 6–8 mV effect almost gone (−0.84) |
| E6 DATA higher at 6–9 mV (e.g. 36.8 vs 21.1 at 7) | REPRODUCED for 500–1000 G_small; NOT ROBUST at 8–9 mV (window, G_all) |
| E6 SWS higher at 10 mV (+21) | REPRODUCED and robust in sign (+10 to +21) |
| Mechanism ρ 0.59 | REPRODUCED numerically; INVALID as a mechanism estimate (cross-half ρ ≈ 0) |
