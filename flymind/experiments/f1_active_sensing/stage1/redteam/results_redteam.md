# F1 Stage 1 confirm - red team of results (read-only review, 2026-11-02)

**Verdict: PASS_WITH_ISSUES.** All numbers reproduce and the crash/restart left no trace. No blocker. The conclusions need
re-wording: claims 4 and 5 are over-interpreted, and the main engineering context (the linear P controller) is missing.
Scripts: scratchpad rt.py..rt6.py (own code, `python -I -B`, nothing written under stage1/results).

## A. Independent recomputation from raw u*.json / .npz (own bootstrap, 10 000 draws, own lock-in)
| quantity | analysis_confirm.json | mine |
|---|---|---|
| H1 (DATA W sin-none) | 0.1275 [0.0925, 0.165] | 0.1275 [0.0925, 0.1625]; arms 0.2675 / 0.395 |
| S1 sin-jvel | -0.0425 [-0.07, -0.015] | -0.0425 [-0.07, -0.0175] |
| S2 (hierarchical, 10 inst x 40 units) | -0.005 [-0.045, 0.0325] | -0.005 [-0.0425, 0.0325]; flat bootstrap [-0.0375, 0.0275] |
| S3 | 0.01 [-0.0375, 0.0525] | 0.01 [-0.0375, 0.0525] |
| S4 | 0.0025 [-0.0425, 0.0475] | 0.0025 [-0.04, 0.045]; TH none 0.165 (gate OK), dTH 0.125 |
| S10 S / W | 1.7857 [1.7576, 1.8132] / 0.2613 | 1.7857 [1.7567, 1.8137] / 0.2613 |
| gated S10 (posthoc C), S / W | 0.0839 / 0.0908 | 0.0839 / 0.0908 (CI [0.066, 0.102]) |
- `s10_deg` stored in json = my lock-in from npz `pan`: max |diff| 8e-8 deg (400 units x 4 trials). `success` re-derived from stored e(t)
  (|e|<5 for ticks 550-599): 0 mismatches over all non-N trials.
- 0 invalid ticks, 0 excluded, 1 manifest sha in all 16 400 rows, `hashes()` == manifest_confirm.json now.
- Frozen analysis vs STAGE1_DESIGN.md: estimators, windows (0.75-4.75 s, linear detrend, lock-in), SESOI 0.10, precedence
  SUPPORTED>HARMFUL>EQUIVALENT>DETECTABLE>UNMEASURABLE>INCONCLUSIVE (analysis1.py:47-62), Holm family S1-S4,S7-S9 (:21), harm margins
  0.05 / 1 deg / 1 deg, S6 conditional Clopper-Pearson, RNG streams (A4) all match. S7/S8/S9 as "arm - sin" equal the design's
  difference of differences (none cancels). No discrepancy.

## B. Crash / restart (question c): no corruption or bias found
- Restarts verified in confirm_stdout.txt: 225 units in run 1 (4 workers), +40 in run 2 (8 workers), +135 in run 3. By mtime:
  units 9112001-225 / 226-265 / 266-400 match the three phases; 537-min gap = power-off.
- All 400 npz pass `zipfile.testzip` (CRC), 205 arrays each, all 400 json parse with 41 rows, 0 `.part` files. npz/json mtimes within 17 ms.
- Per-phase DATA W dH1 = 0.124 / 0.100 / 0.141 and none = 0.244 / 0.250 / 0.311; differences are within unit-sampling noise (n = 40..225 draws
  different rho), no systematic shift; S10-S 1.78 / 1.76 / 1.80.
- Strongest check: I re-simulated DATA sin W and gated W of units 9112010 (run 1), 9112240 (8-worker run), 9112300 (run 3) with
  cl_sense.run: omega and pan_t identical (diff 0.0), e(t) diff 5e-7 deg (float32 storage). Result is bit-deterministic across worker count and restarts.
- Residual: os.replace without fsync (runner1.py:140-144) - not an issue here, but "265 units validated" has no saved log.

## C. Issues
**1. (major, framing) The linear P controller solves the "weak" range without any motion.** P none/sin W success = 1.00/1.00, S 1.00/1.00
(analysis_confirm.json describe, `P|*`); TH none S = 1.00 while DATA none S = 0.955. "Weak/far target" is a property of the spiking path's
threshold (DATA none W 0.2675, cliff at rho~0.28), and dither only moves that cliff by ~1.8 cm. Fix: state in the headline and in every
Stage-2 sentence: "a linear P read-out of the same encoder reaches 100 % in W with no motion; the dither compensates a threshold nonlinearity
of the SNN/TH path". Stage-2 is doubly not recommended.

**2. (major, over-interpretation) Claim 4 "S10 HARMFUL" is a proxy flag, not an observed loss.**
- S5 NOT-HARMFUL: success S 0.955 -> 0.965 (est -0.01 [-0.0325, 0.0125]); final error +0.064 deg [-0.005, 0.135] vs 1 deg margin.
- The 1.79 deg is simply the tracker following image motion: world motion `mt` gives 1.82, `virtual` 1.84, P 1.81, TH 1.71 (describe s10_deg minus none).
  For `mt` this is correct tracking. S10 cannot tell "following" from "counter-steering": `lockin` takes abs(), so the reference phase phi is irrelevant
  (cl_sense.py:224). Phase evidence exists only in my check: complex pan_t response / theta_s in S = -0.76+0.54j (|.|=0.93, 145 deg); in W 0.00+0.11j.
- Harm was visible before the pilot: STAGE1_DESIGN.md s14 F3/R5 reports S-range S10 gain 1.51 deg (0.5 Hz) and 1.76 deg (1 Hz), both > the 1 deg margin;
  R5 averaged W and S (0.90 / 0.95) so G-d did not fire. G-b was therefore predictable, not a surprise.
- Fix wording: "G-b fires by the frozen rule through S10 in S (pan_t 1 Hz amplitude +1.79 deg, margin 1 deg). S5 (success, final error) and S6 are
  NOT-HARMFUL; the S10 excess equals the response of any reactive tracker to 4 deg of image motion and was already present in the F3 feasibility data."
  Keep "Stage 2 not recommended (frozen rule)".

**3. (major, circular) Claim 5 "gated fixes S10" is true by construction.** The gate opens only when |omega| > 0.10 rad/s and the pan_t f-component
exists only when the target is seen. Mean |theta_s| in 0.75-4.75 s: S sin 1.255 deg, S gated 0.050 deg (4 %); W sin 1.458, W gated 1.126 (77 %).
So in S the dither is essentially off and lock-in +0.08 deg says nothing about a "fix". Genuine evidence = S7 (gain kept in W: 0.39 vs 0.395, CI
[-0.020, 0.0075]) and S success 0.9525. Also omega_on = 0.10 is the R3 floor and gating state cycles (1 s quiet rule) - not examined. Wording:
"gated keeps the W gain and, because it is off after detection, shows no S10 excess; whether this is a usable policy needs a new pre-registered test
with its own harm metric (transitions, tracking cost, false-detection gating)". Do not use "fix".

**4. (major, wording) Claim 5 "onset direction ... refuting" is not supported.** toward-away = -0.034, CI [-0.100, +0.037] (posthoc_confirm.json),
n = 183 / 217; it excludes toward>away by 0.04 but allows away>toward by up to SESOI. The split is a function of phi only (sign of the 0.3 s mean of
theta_s, posthoc1.py:40-41). Use: "no evidence for an onset-direction effect; post hoc, CI +-0.07". Sign convention is right: sign(pan_end)*side = -1
in 400/400 units (docstring says 50/50 - update).

**5. (minor) Claim 4 "63 %" is computed correctly but is a commanded quantity.** posthoc1.py:44-45 uses q0 = pan_t + theta_s = qt[0] (post-safety
command), not measured joint angle (q0_tr is not stored in npz). Recompute: S 1.225/1.936 = 0.633 (mine 0.633), W 1.047. Ratio of means, no CI.
Say "commanded base-pan dither" and add: in W (where the dither matters) 105 % is kept, i.e. no cancellation there.

**6. (minor) Claim 2 jvel.** Matching verified: RMS ratio jvel/sin 1.0000, velocity ratio mean 1.02 (0.80-1.20), corr with jvel-sin outcome 0.06, jvel>sin in all
velocity terciles (+0.038/+0.030/+0.060) - the advantage is not a velocity artefact. But "EQUIVALENT" is only +-0.10 (= SESOI) while Holm p = 0.017 says a
nonzero 4 pt difference; and in S jvel is worse (0.927 vs sin 0.965; vs none -0.0275 [-0.055, 0.000], S10 0.68). Write: "jvel equivalent within +-0.10, nominally +4 pts
better in W (Holm p 0.017), nominally worse in S (untested)".

**7. (minor) H1 range dependence (claim 1, 6).** Success vs rho is a cliff: rho<0.26 none 0.86/sin 0.99; 0.26-0.30 (n=113) 0.09 -> 0.41 (+0.32);
>=0.30 (174 units, 43.5 % of W) 0/174 for both none and sin. Terciles [0.20, 0.18, 0.0] therefore mean "dither never reaches past ~0.30 m", and the
H1 value (0.1275) depends on how much of W lies on each side of the cliff (R1 left W unchanged at p0 = 0.317). p = 0.0001 is the bootstrap floor
(write p < 1e-4). Report rho50 shift 1.8 cm with CI (0.0925-0.165)*14 cm = 1.3-2.3 cm.

**8. (minor) Holm is reported but classification uses unadjusted CIs** (analysis1.py:47-62, 124); R2 used alpha/7. State this; no classification changes under Holm
(S1 stays EQUIVALENT; p_holm 0.0168).

**9. (minor) Replay figure (question f).** `pick_unit` (figures1.py ~120-123) returns the lowest unit where none fails and sin succeeds: confirmed 9112003 is
the first of 55 such units (4 units show the reverse). figures1.py mtime 18:24:33 precedes any confirm output and pilot figures (18:24:35) were made with it, so the
rule predates the data; but it is documented only in the figures1.py docstring (not in the design or manifest) and the figure title omits it. Add to suptitle:
"unit selected on outcome (none fails, sin succeeds; 55/400 units, reverse 4/400) - illustrative, not typical".

**10. (minor) posthoc1.py hygiene.** Output opened with "w" (others "x"); RNG 9115003 is the reserved spare seed (documented in docstring, fine); asserts only after
writing (:67-68); not in manifest OWN (neither is figures1.py). Label already says EXPLORATORY - keep.

## D. Claim-by-claim
1 SUPPORTED: holds (recomputed). 2: holds for S2/S3/S4; jvel wording per issue 6. 3: holds (S7 -0.005, S8 -0.005, S9 -0.0025 all recomputed or identical).
4: Stage-2 non-recommendation holds by frozen rule; "harm" interpretation per issues 2, 5. 5: gated as hypothesis only (issues 3, 4). 6: holds, cliff context (issue 7).
