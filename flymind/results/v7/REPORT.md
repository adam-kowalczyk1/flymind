# V7 — Robustness beyond the V5 v4 operating box: report (2026-10-30)

**Status: exploratory, completed. Verdict: PASS_WITH_LIMITATIONS — after correction** (red team RT-7 NOT_READY on the draft; all 8
corrections applied, §5). MODEL + MuJoCo simulation; no physical arm; nothing about the fly. Results apply to their own regions only and
are not pooled with V5 v4 (protocol "own region only" rule).

## 1. Design and execution
Protocol `program_v5v41/V7_PROTOCOL.md` (r1, written ~09:00 before any V5 v4.1+ result; sha 969139e8… hashed before the run). Analysis
`v61_v7_analysis.py` hashed 14:31:46 — before the V7 run (15:02:57) but after the V6.1 run had started (see V6.1 report); the
"corresponding drive regime" rule lives in that script's docstring, not in the protocol; `v61_v7.py` was not hashed. RNG 8 419 040.
Four blocks × 120 scenes: G1 far ρ U[0.28, 0.40); G2 wide azimuth |az0| U(30°, 40°) at ρ [0.16, 0.28); G3 ALIF noise σ 6 mV (SG6 decoder,
slope 472.16, verified); G4 near ρ U[0.12, 0.16); DATA, SWS ((i−1) mod 50)+1, P. 1440 trials, 0 errors; scenes re-derived from seeds
with 0 mismatches (RT-7); Stage 1 28/28 after the run. Operationalisation: G4 and the ρ < 0.22 half of G2/G3 → V5 v4 S1 sign (d > 0); G1
and the ρ ≥ 0.22 half → S2 sign (d < 0); "pattern holds" if the cluster CI excludes 0 in that direction (sign logic verified by RT-7).

## 2. Results (d = err(DATA) − err(SWS) [°], CI95 cluster bootstrap over SWS instances [scene bootstrap, RT-7]; DATA − P likewise)
| Block | n | drive median [IQR] mV | DATA err mean / median | success D / S / P | e_sd last 1 s, median D / S | d (SWS) cluster [scene] | rule | d (P) |
|---|---|---|---|---|---|---|---|---|
| G1 far | 120 | 4.8 [4.0; 5.8] | 12.56 / 11.86 | 0.15 / 0.15 / 1.00 | — | −0.33 (−0.57; −0.10) [−0.58; −0.08] | pattern holds (S2 sign) | +12.0 |
| G2 ρ < 0.22 | 54 | 10.7 [10.5; 11.1] | 1.99 / 1.96 | 0.87 / 0.85 / 1.00 | | +0.21 (+0.04; +0.38) [+0.04; +0.39] | pattern holds (S1 sign) | +1.58 |
| G2 ρ ≥ 0.22 | 66 | 9.3 [8.8; 9.8] | 2.65 / 1.90 | 0.83 / 0.74 / 1.00 | | −0.33 (−0.67; −0.03) [−0.72; +0.03] | holds (cluster CI only) | +2.53 |
| G3 σ 6, ρ < 0.22 | 65 | 9.1 [8.2; 9.8] | 1.84 / 1.84 | 0.95 / 0.95 / 1.00 | | +0.06 (−0.04; +0.16) | not shown | +1.54 |
| G3 σ 6, ρ ≥ 0.22 | 55 | 6.9 [6.0; 7.8] | 0.84 / 0.72 | 1.00 / 1.00 / 1.00 | | +0.08 (−0.01; +0.17) | not shown | +0.68 |
| G3 all | 120 | 8.1 | 1.38 / 1.47 | 0.97 / 0.97 / 1.00 | | +0.07 (+0.01; +0.14) [−0.003; +0.145] | — | +1.14 |
| G4 near | 120 | 10.8 [10.1; 11.3] | 2.90 / 2.77 | 0.17 / 0.09 / 1.00 | 2.56 / 3.13 | −0.20 (−0.34; −0.06) [−0.34; −0.06] | not shown — reversed | +1.92 |
P error by block 0.24–0.98° (G4 0.98°: a near-field effect even for P). G1: 91/120 pairs had neither network move; 27 both moved (86 % of
Σd, mean d −1.25°), 2 only-DATA. G4: late |e| max median 5.4° / 5.9°; 17 % / 18 % of final |e| ≥ 5°. Overshoot DATA − SWS: G2 +0.39°, G3
+0.24°, G4 −0.74°.

## 3. Interpretation (own regions only)
- G2 (initial errors 30–40°): the V5 v4 near/far pattern is reproduced at the pre-specified ρ 0.22 split, but fragile: the far half's
  scene-bootstrap CI includes 0, splitting at ρ 0.20 or 0.21 leaves neither half significant, and a drive-based split gives "not shown";
  six unadjusted sign tests.
- G1 (far): "pattern holds" formally, in a regime where the SNN loop largely fails (DATA error 12.6°, 24 % of scenes with movement, P
  0.5°); d comes mostly from pairs where both moved and DATA got closer (not from "which network starts moving").
- G4 (near, strongest drive): the S1 sign is not reproduced — it is reversed (−0.20), in an oscillatory, failing regime (success 0.17 /
  0.09; residual oscillation 2.6° / 3.1°) whose drive (IQR 10.1–11.3 mV) lies outside anything in V5 v4 S1 (8.2–9.5 mV).
- G3 (σ 6): no DATA/SWS difference in either half; the overall +0.07° excludes 0 only under the cluster bootstrap (scene bootstrap
  −0.003; +0.145) — below any practical threshold. Consistent with V6 (σ 6 removes the open-loop difference).
- DATA vs P: P has lower error in every block (P is an engineering reference only).
- Withdrawn (draft over-reach): "the S1 effect is confined to an intermediate drive band (~6–10 mV)". V7's own data contradict it — G2
  near (drive 10.7 mV) d +0.21 vs G4 (10.8 mV) d −0.20; the nearest V6.1 cell (I14 S1, 10.4 mV) is +0.18. The initial-frame drive index
  does not explain the sign across V7 blocks. Cross-study synthesis belongs in a separate hypothesis section (final report §D).
- Cannot conclude: anything about moving targets, lighting, distractors (not run); anything about the fly.

## 4. Limitations
120 scenes per block (54–66 per half); one decoder per noise level; single parameter set; G1/G4 are failing regimes; drive index from the
initial frame only; the drive-regime rule was in the analysis script, not the protocol.

## 5. Red team
RT-7 (`redteam/RT7_review.md`, separate model instance; RNG 8 498 411/412; the `redteam/RT7/` folder is a partial scratch from an
earlier attempt cut off by a usage limit): all numbers reproduce, sign logic and SG6 decoder verified; NOT_READY on the draft for the
drive-band over-reach, missing G4 failure/oscillation facts, the G1 mechanism, G2 fragility, G3 resampling dependence, missing columns,
provenance wording and the P range — all corrected above.

## 6. Files
`v61_v7.py`, `v61_v7_analysis.py`; `results/v7/` (v7.jsonl 1440, analysis.json, analysis_stdout.txt, stdout, stage1_post_*.json,
protocol_sha256_before_run.txt, redteam/); drive index rows in `results/v61/drive_index.json`.
