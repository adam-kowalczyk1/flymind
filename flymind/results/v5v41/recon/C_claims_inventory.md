# Task C: claims inventory for FlyMind V5 v3, V5 v4, the SWS control, the drive/threshold mechanism, v6 stability and the v7 encoder

Date: 2026-10-30. Read-only reconnaissance. The only file written in the repo is this report. Helper scripts (they only read saved JSON, JSONL and TXT; they run no simulation, build no network and use no seed pool) are in
`/private/tmp/claude-501/-Users-admin-so101-fly-project/075990a2-3231-4039-8d41-31f3fdcb9204/scratchpad/recon/`:
- `c_v6.py`: v6 ipsi curves, DATA vs SWS for each amplitude.
- `c_cross.py`: DATA onset and SWS crossover point for each v6 setting.
- `c_recomp.py`: recomputes V5 v4 from the raw JSONL, the mech-strength B post-hoc contrast and the V5 v3 gain check.
- `c_p.py`: lists the DATA vs P pairs.

All of them were run as `.venv/bin/python -I -B`. The bootstrap RNG seed was 77001, which is used only to resample saved numbers.

Labels used below: DATA (supported by the connectome), MODEL (a computational assumption), ENGINEERING (encoder, camera, simulator) and CONTROL (shuffles and calibration).
Status values: **IND** = INDEPENDENTLY_CHECKED (the evidence file is named), **AUTH** = AUTHOR_ONLY, **UNSUP** = UNSUPPORTED (no artifact found), **CONTRA** = CONTRADICTED. "+R" means I recomputed the claim from saved artifacts in this recon, and the result agrees unless stated otherwise.
A note on independence: every "Red Team" (RT) is a separate instance of the same model, and the "independent" audit scripts were written by the same author. The documents say this themselves (`V5v4_FINAL_REPORT.md:21,26`; `results/redteam/v5v3_result_redteam.md:55`).

---

## 0. Headline findings

1. **CONTRADICTED: "P controller better in 450/450 pairs" and "P better by 2.7° in every scene"** (`V5v4_FINAL_REPORT.md:63`, `:77`). In the raw JSONL, DATA−P > 0 in **446/450** pairs. In 4 pairs DATA is better than P: seeds 4309, 4315, 4411 and 4425, all in S2, with d = −0.067, −0.098, −0.244 and −0.021°. `analysis_frozen.json` gives `zeros 0` and `better_gt1 0`, so the analysis output never said 450/450; it was misread. 2.68° is the mean, not a per-scene value. This is minor in size, but it is a factual error in the final report.
2. **The ALIF threshold "~7 mV" is contradicted by the saved response curves.** The claim appears at `VALIDATION_PLAN.md:343`, in the header of `results/v7_encoder_distance_az_20261029.txt:1`, in `validation/v5v4_protocol.md:20` and in the RT r1 m10 note "≈ 7 mV". At the V5 configuration (J0 0.2, noise 2, b_a 0.5, delay 1.8), the DATA DNa02 ipsi response is 0 Hz at 5.7 mV, 16.3 Hz at 6.0 mV, 31 Hz at 6.3 mV, and 88 Hz at 6.9 mV (`results/v6_stability/v6_stability_20261029T170806.json`, default row). g30 is 0.523, which is 6.28 mV. Across the 20 v6 settings, DATA onset lies at 5.4–6.6 mV. `results/v5v3_prep/v5v3_control_check_v2_*.json` and `results/v5_mech_strength/*A*.json` agree: DATA gives 17 Hz at g = 0.5, i.e. 6 mV. The functional onset is therefore about 6 mV, not 7, and every "silent region" boundary derived from "> ~7 mV" is shifted.
3. **"SWS weaker than DATA under weak drive" holds only for about 6.0–7.8 mV, not across 6–9 mV.** At the V5 configuration SWS (one instance, seed 1401) is weaker by 6.5–14.3 Hz from 6.0 to 7.8 mV, and *stronger* by 2.6–9.0 Hz from 8.1 to 9.9 mV (Section 4). Two other open-loop artifacts show the same pattern. The author file `results/v5v3_prep/v5v3_control_check_v2_20261029T165755.json` has SWS 1401–1403 and ALIF seeds 1001–1015. The RT file `results/redteam/v5v3_control_v2_redteam.md:55-69` has SWS 1441–1443 and ALIF seeds 1101–1110; its raw output still exists in the other session's scratchpad at `.../31945ef1-.../scratchpad/redteam3v2/b3.out`. Both show SWS weaker at 6.0, 6.6 and 7.2 mV and stronger at 8.4 mV. No document states the claim as "6–9 mV". The closest wording is "weak drive", e.g. `AUTONOMOUS_RESEARCH_LOG.md:45` and RT v2 `:69`.
4. **The high-drive sign reversal exists only with ALIF adaptation (b_a = 0.5).** In all 9 v6 settings with b_a = 0, SWS never exceeds DATA by more than 2 Hz at any amplitude. In 9 of the 11 b_a = 0.5 settings it does, with the crossover between 6.3 and 9.9 mV. The two exceptions are J0 0.15 with noise 2 or 3, where SWS stays below or equal to DATA. The V5 v4 report explains S1 ("control better") with this open-loop sign reversal (`V5v4_FINAL_REPORT.md:66-69`) and cites V6 as evidence of robustness: "threshold direction constant in 18/20" (`:79-80`). But v6 Δg30 measures only the *threshold* direction. The reversal that would explain S1 depends on a MODEL parameter (b_a), and this is not disclosed.
5. **The v6 stability evidence rests on one SWS instance** (seed 1401, rebuilt for each J0; `v6_stability.py:6,78`). It shares that instance, and ALIF seeds 1001–1010, with the control check v2 artifact, so the two are not independent. The 18/20 result meets the pre-registered ≥ 90 % rule exactly at the boundary. Two of the 18 "positive" Δg30 are 0.0002 g, one is 0.0 and one is −0.0053. The plan says "≤ 0.014 g" (`VALIDATION_PLAN.md:340`); in mV that is ≤ 0.17 mV.
6. **The drive mechanism for V5 v4 (S1 = strong drive, so control better; S2 = weak drive, so DATA better) was never tested in closed loop.** The proposed decisive test, a loop at fixed drive g 0.5 vs 0.7, is listed as not executed (`VALIDATION_PLAN.md:391-392`, `AUTONOMOUS_RESEARCH_LOG.md:89`, RT `v5v3_result_redteam.md:133`). V5 v4 did not run it. In V5 v4, "drive" is confounded with ρ. Within S1, d is flat in |az0| (+0.55, +0.50, +0.49 for |az0| in 0–10, 10–20 and 20–30°), even though initial drive rises strongly with |az| (`v7_encoder_distance_20261029.txt`: at ρ 0.16, 8.1 mV at 0° and 10.2 mV at 15°). So initial drive does not predict d within a stratum. Status: **AUTH** (interpretation) and **UNSUP** (causal).
7. **"Effect beyond signal scale" in V5 v4 rests on 10 of 450 SWS instances, and only on small-signal gain.** `results/v5v4/post_sws_slopes.txt` covers SWS 4001–4010: 0.988–1.005 × DATA. The report states "SWS slopes 0.988–1.005 × DATA" without the n (`V5v4_FINAL_REPORT.md:57`; `AUTONOMOUS_RESEARCH_LOG.md:111`). Calibration is done at strong drive (RT r1 I3, `v5v4_protocol_redteam_r1.md:139`). The weak-drive response, where DATA and SWS do differ (findings 3 and 4), is not equalised. "Beyond signal scale" should read "beyond small-signal decoder gain".
8. **A stale V5 conclusion contradicts V5 v4.** `VALIDATION_PLAN.md:396-398` (the final V5 conclusion, written after V5 v3) says the within-block pattern "does not change the mean error by more than ~0.5°". This was not retracted after V5 v4, which found S2 −0.52° (CI −0.71; −0.33) and S2b −0.66° (CI −0.99; −0.33). Lines 376 and 397 should be marked as superseded. The same file's header table (`VALIDATION_PLAN.md:21`) still says "topology from data +16 pp (sensitivity to weak stimulus)". That figure is a V5 v1/v2-era result, later shown to be confounded with signal scale (`VALIDATION_PLAN.md:322-325`).
9. **The encoder claim "silent for ρ ≥ 0.28" in `VALIDATION_PLAN.md:343-344` was never corrected there**, although it was corrected in the protocol. RT r1 M1 showed that drive rises with |az| (`v5v4_protocol_redteam_r1.md:38-52`). The author confirmed this (`AUTONOMOUS_RESEARCH_LOG.md:99`) and fixed `validation/v5v4_protocol.md:20-21`. Two further points: the "~7 mV" threshold itself is too high (finding 2), and "the dead zone is not topology" is only approximately true, because DATA and SWS differ at the dead-zone edge (6.0 mV: 16.3 vs 2.0 Hz). That edge difference is the operating range of the S2 effect.
10. **The independent evidence for V5 v4 results is weak.** No result Red Team was run (`V5v4_FINAL_REPORT.md:26`). `audit_v5v4_independent.py` is written by the same author, reads the raw JSONL and uses pandas/scipy. I recomputed the means, strata, d, CIs, zeros and the regression root from the raw JSONL and they match (Section 2C). Some RT evidence lives only in `/private/tmp/.../31945ef1-.../scratchpad/`, which is volatile: the files exist today, but they are not under the repo.

---

## 1. What I read

`V5v4_FINAL_REPORT.md` (93 lines); `VALIDATION_PLAN.md:282-408` (V5 v2, autonomous session, V5 v3, V5 v4); `AUTONOMOUS_RESEARCH_LOG.md` (112); `NEXT_SESSION.md` (23); `results/redteam/v5v3_control_redteam.md`, `v5v3_control_v2_redteam.md`, `v5v3_result_redteam.md`, `v5v4_protocol_redteam_r{1,2,3}.md`; `results/v6_stability/*` and `v6_stability.py` (sha256 6c39ad81…, matching `protocol_sha256_before_run.txt`); `results/v5_mech_strength/*`; `results/v7_encoder_distance*.txt`; `results/v5v3/*`; `results/v5v4/*`; `results/v5v3_prep/v5v3_control_check_v2_*.json`; `results/v5v4_run_integrity.txt`; `validation/v5v4_protocol.md` (grep only).
Hashes checked: `validation/v5v4_protocol.md` = f648c7ea…0ce0, which matches the report's line 12 and both `run_meta_*.json`. `validation/v5v3_protocol.md` = a0f09809…cb2a8, which matches `VALIDATION_PLAN.md:348`.

---

## 2. Claims table

### 2A. V5 v3 (confirmatory, seeds 3051–3100, n = 50)

| # | Claim (source) | Supporting artifact | Status |
|---|---|---|---|
| A1 | H1 DATA−SWS v2 −0.19° (CI95 −0.58; +0.16; CI90 −0.51; +0.10), p 0.33, "equivalent within SESOI 1°" (`VALIDATION_PLAN.md:364`; `AUTONOMOUS_RESEARCH_LOG.md:84`) | `results/v5v3/analysis_summary.txt:7`; `audit_independent.txt` | **IND**: `v5v3_result_redteam.md:59-75` recomputed from scratch with 10⁶ permutations, p 0.333; reran seeds 3051–3052 bit-identically (`:79-83`) |
| A2 | H2 −2.40°, H3 −2.21°, p_Holm 2·10⁻⁵ (`VALIDATION_PLAN.md:365-366`) | `analysis_summary.txt:9,11` | **IND** (RT result §3) |
| A3 | Strata +0.53 / −1.02 / −0.47 (`VALIDATION_PLAN.md:370-371`) | `analysis_summary.txt:8` | **IND** for the numbers (RT §3). The *replication* of the strata structure failed on dev 1001–1044 (RT `:98`) |
| A4 | "Opposite signs consistent with open loop (sign depends on drive)" (`VALIDATION_PLAN.md:371-372`) | open-loop curves (control check v2, RT v2 b3) | **AUTH** interpretation. RT `:98` calls the strata "weakly reproducible" |
| A5 | "In ~92 % the advantage of DATA over SHUF_STR disappears ... the deficit is due to lateralisation/layers/scale" (`VALIDATION_PLAN.md:377-379`) | H3/H2 = 2.21/2.40 = 0.92 | **AUTH**; the arithmetic is correct. The causal attribution is a package claim; RT `:112-113` says H3 is not a pure topology test |
| A6 | "~45 % of H2 is signal scale" (`VALIDATION_PLAN.md:388-390`; `AUTONOMOUS_RESEARCH_LOG.md:87-88`) | `results/v5v3/post_gain_check_dev1501_1520.json` | **IND**: RT made its own estimate of ~50 % on 1001–1044 (`v5v3_result_redteam.md:114-118`). +R: DATA−STR_shared −2.617 → DATA−STR_own −1.445 (my CI −2.42; −0.53); own−shared −1.172 (CI −2.35; −0.16); fraction 0.448. n = 20 dev seeds, and 7/20 pairs are identical across all three conditions |
| A7 | Calibration slopes SWS 492–495, SHUF_STR 59–157 (`VALIDATION_PLAN.md:372-373`; `AUTONOMOUS_RESEARCH_LOG.md:86`) | `results/v5v3/post_slopes.txt` | **AUTH**, and **only 5 of 50 instances** (3051–3055). The n is not stated in the plan or the log; RT §2 table `:49` states it |
| A8 | Final V5 conclusion: the within-block pattern "does not change the mean error by more than ~0.5°" (`VALIDATION_PLAN.md:396-398`; also `:376` "~0.5–0.6°") | V5 v3 pooled CI90 | **CONTRA by a later artifact, if it is read as a statement about the pattern rather than the V5 v2 scene mixture.** V5 v4 `analysis_frozen.json` gives S2 −0.518 (CI95 −0.713; −0.329) and S2b −0.656 (−0.990; −0.328). Not retracted |
| A9 | "Unresolved: the pattern's effect in the narrow weak-drive range (ρ 0.24–0.30)" (`VALIDATION_PLAN.md:399`) | — | Superseded by V5 v4 S2 and never updated |

### 2B. SWS control (SHUF_WITHIN_SIDE v2) and the weak-drive mechanism

| # | Claim (source) | Artifact | Status |
|---|---|---|---|
| B1 | v2 preserves 17 properties, LI 1.0000, identical DNa02 inputs and layers, λ_max 26.3 (`VALIDATION_PLAN.md:334-336`; `AUTONOMOUS_RESEARCH_LOG.md:43-45`) | `results/v5v3_prep/v5v3_control_check_v2_20261029T165755.json`; V5 v4 raw `sws_li_rel` 1.0–1.0000000000000004, `sws_changed_frac` 0.660–0.678 (+R) | **IND**: `v5v3_control_v2_redteam.md:34-51` (reran on 1441–1443) |
| B2 | "The difference under weak drive comes entirely from the LC10a×LC10a block" (`AUTONOMOUS_RESEARCH_LOG.md:45`; `VALIDATION_PLAN.md:335-336`) | control check v2 decomposition (seed 1401): DATA+LC×LC_SWS 3.0 Hz at g 0.5 (SWS 2.8); SWS+LC×LC_DATA 15.7 (DATA 17.0) | **IND**: RT v2 `:55-69` (instance 1441, b3.out present in the old scratchpad) and RT v1 `:96` |
| B3 | The pattern changes reciprocity, triangles, clustering and assortativity *together*, so the mechanism is not identified (`AUTONOMOUS_RESEARCH_LOG.md:52-53`; `V5v4_FINAL_REPORT.md:72-73`) | RT v2 `:37-53` | **IND** (RT) |
| B4 | 57–58 % of |w| mass is untouched by the control (`V5v4_FINAL_REPORT.md:73`) | RT v2 `:49` | **IND** (RT only) |
| B5 | "The effect changes sign with drive" (RT v2 `:69`, `:132`; `AUTONOMOUS_RESEARCH_LOG.md:53`) | RT v2 b3: g 0.70 SWS +3…+6 Hz; control check v2: g 0.7 SWS +4.4/+6.8/+5.5 Hz; v6 default: SWS > DATA at 8.1–9.9 mV | **IND** at the V5 configuration (b_a 0.5). **Scope: b_a-dependent.** With b_a = 0 there is no reversal in any of 9 settings (Section 4.3) |
| B6 | **"SWS has a weaker steady-state response than DATA under weak drive, ~6–9 mV LC10a current"** (this was the requested search) | See Section 4 | No document states it in this form. Supported for **~6.0–7.8 mV** (V5 configuration, 4 independent SWS instances in 3 artifacts: 1401 in v6 and check v2, 1402–1403 in check v2, 1441–1443 in RT v2). **Contradicted for ~8.1–9.9 mV**, where SWS is stronger. Across all 20 v6 settings, SWS < DATA in 133 of 220 cells in the 6–9 mV window |

### 2C. V5 v4 (confirmatory, seeds 4001–4450, 450 × 6 = 2700 trials)

All numerical rows were checked against `results/v5v4/analysis_frozen.json` and `audit_independent.txt`, and +R recomputed from `raw_v5v4_{A,B}.jsonl` by `c_recomp.py`.

| # | Claim (source) | Artifact | Status |
|---|---|---|---|
| C1 | 2700/2700 trials, 0 errors, 0 exclusions, 0 calibration refusals, 0 malformed lines; VALID (`V5v4_FINAL_REPORT.md:19,34`) | `analysis_frozen.json` validity; `run_meta_{A,B}` VALID true; `results/v5v4_run_integrity.txt` | **AUTH**, +R (450 unique seeds 4001–4450, 0 errors) |
| C2 | Code = manifest = frozen copy; Stage 1 28/28 before and after (`:17-18`) | `v5v4_run_integrity.txt`; `run_meta` stage1_pre/post n 28 and mismatched [] | **AUTH**. RT r3 verified the diffs before the run, not after |
| C3 | Condition means (table `:41-46`): DATA 2.88 (S1 1.72, S2 3.46), SWS 3.05 (1.21, 3.97), STR_OWN 4.26, STR_SHARED 5.66, TOY 4.31 (S1 0.55), P 0.20 | `analysis_frozen.json` conds | **IND** (second implementation by the same author); +R exact |
| C4 | H1 S1 +0.512° (CI +0.414; +0.612), d_z 0.82, "control better, ≥ SESOI" (`:51`) | `analysis_frozen.json` H1.S1 | **IND** (author's second implementation); +R +0.512 (+0.411; +0.613), 117 positive / 33 negative / 0 zero. The category uses the point mean; the CI lower bound is 0.41 < 0.5, which the report itself notes (`:53-54`) |
| C5 | H1 S2 −0.518° (−0.713; −0.329), "DATA better, ≥ SESOI" (`:52`) | same | **IND** (author); +R −0.518 (−0.715; −0.324), 57 zeros, 85 positive / 158 negative. The CI upper bound −0.33 is inside the SESOI band, as noted at `:54` |
| C6 | Pooled −0.175 (CI −0.32; −0.04), cancellation (`:55`) | pooled_descriptive | **IND** (author); +R |
| C7 | Sub-bands S2a −0.38, S2b −0.66 (`:55-56`) | subbands_descriptive | **AUTH**, matches the artifact |
| C8 | Regression d = 3.37 − 14.6·ρ − 0.012·|az0|, "DATA's advantage grows with distance; sign changes at ρ ≈ 0.23" (`:56-57`) | regression_descriptive | **AUTH**. The coefficients match. +R root: ρ = 0.231 at |az| 0, 0.219 at |az| 15, 0.207 at |az| 30. "Grows with distance" is true only for the linear fit. In 0.02-wide bins d is non-monotone: [0.16,0.18) +0.29, [0.18,0.20) +0.74, [0.20,0.22) +0.43, [0.22,0.24) −0.16, [0.24,0.26) −0.91, [0.26,0.28) −0.55, and the last bin has 37/106 zeros. The |az| coefficient is not significant (SE 0.008) |
| C9 | McNemar success DATA vs SWS 29 vs 13, p 0.02 (`:57`) | aux.success_mcnemar | **AUTH**, matches the artifact |
| C10 | "SWS slopes 0.988–1.005 × DATA" (`:57`; `AUTONOMOUS_RESEARCH_LOG.md:111`) | `results/v5v4/post_sws_slopes.txt` | **AUTH**. Only **10 of 450** instances (4001–4010); the n is not stated in the report. Consistent with RT r2 N3 (10 other instances, 0.989–1.008; `v5v4_protocol_redteam_r2.md:50`) |
| C11 | H2a −1.38° (−1.82; −1.03); H2b +1.41° (+0.99; +1.77); H2b S1 −0.46, S2 +2.34 (`:59-61`) | H2 | **IND** (author); matches |
| C12 | STR_OWN slopes 18–203 Hz/rad (median 124); Spearman −0.08 (p 0.11) (`:61`) | aux | **AUTH**, matches. Note: the 18.4 Hz/rad instance runs with ~27× DATA-relative decoder gain. The refusal threshold is 2 Hz/rad (RT r1 m5) |
| C13 | DATA−TOY −1.43°; DATA−P +2.68° (`:63`) | D | **AUTH**, matches |
| C14 | **"P better in 450/450 pairs (348 by > 1°)"** (`:63`) and **"P better by 2.7° in every scene"** (`:77`) | raw JSONL | **CONTRA**: P is better in 446/450 (+R, `c_p.py`); DATA is better in seeds 4309, 4315, 4411 and 4425. "348 > 1°" is correct (`worse_gt1 348`) |
| C15 | "Near targets (strong drive) the random pattern gives the smaller error; farther targets (weak drive) favour the data pattern" (`:66-68`) | strata results (C4/C5) and open-loop curves (B5) | The strata facts are **IND**. The **drive mapping is AUTH/UNSUP** (finding 6): drive was never manipulated in closed loop, and d is flat in |az0| within S1 (+R) |
| C16 | "On 450 new seeds the strata structure was replicated" (`:69-70`) | V5 v3 strata vs V5 v4 strata | **AUTH**, partially. The sign pattern (+ near, − far) reappears. The strata boundaries differ (0.24 in V5 v3, 0.22 in V5 v4). In [0.22, 0.24), V5 v3 gave +0.68 (n 6; RT r1 `:75`) and V5 v4 gives −0.16 (n 105, +R), so the sub-band sign is not replicated |
| C17 | "Calibration equalises only small-signal gain" (`:73-74`) | RT r1 I3 | **IND** (RT). This scopes "beyond signal scale" in `:67` (finding 7) |
| C18 | "V6 exploration: threshold direction constant in 18/20 settings, but small" (`:79-80`) | v6 JSON | **AUTH**, numbers match. It is used as robustness support for a closed-loop sign pattern that v6 does not measure, and the reversal depends on b_a (finding 4) |
| C19 | RT r1 NOT READY → r2 READY → r3 READY (`:22-25`) | `results/redteam/v5v4_protocol_redteam_r{1,2,3}.md` | **IND** (RT files exist). These are **protocol** reviews only; no result RT was run (`:26`) |

### 2D. v6 stability (`v6_stability.py`; `results/v6_stability/v6_stability_20261029T170806.json`)

| # | Claim (source) | Artifact | Status |
|---|---|---|---|
| D1 | Δg30 (SWS − DATA) positive in 18/20 settings; J0 0.15–0.25, noise 1–3 mV, b_a 0/0.5, delay 1/1.8/3 ms (`VALIDATION_PLAN.md:339-341`) | JSON summary `frac_positive 0.9`, `delta_range [-0.0053, 0.0139]`; stdout | **AUTH**, matches. The pre-registered rule is "≥ 90 %" (`v6_stability.py:10`), and 18/20 meets it exactly. Two of the 18 positive values are 0.0002, one setting is 0.0 and one is −0.0053 |
| D2 | Magnitude ≤ 0.014 g (`:340`) | delta_range | **AUTH**, matches (≤ 0.17 mV) |
| D3 | No spontaneous activity, contra 0, saturation ≤ 1.3 % (`:340`) | stdout: spont 0.0 and kontra 0.0 in every row; sat max 0.013 | **AUTH**, matches |
| D4 | "Direction robust at the criterion boundary; effect very small" (`:341`) | — | **AUTH**, an honest wording. **Unstated scope:** 1 SWS instance (seed 1401; `v6_stability.py:6,78`), ALIF seeds 1001–1010, open loop, a single 30 Hz criterion, no SEM stored. The crossover point and the high-drive reversal are parameter-dependent (Section 4.3) |

### 2E. Encoder (v7)

| # | Claim (source) | Artifact | Status |
|---|---|---|---|
| E1 | LC10a current 12 mV·max(g): ρ 0.28 → 4.14 mV at 0° and 6.45 mV at 15° (`VALIDATION_PLAN.md:343`) | `results/v7_encoder_distance_20261029.txt` | **AUTH** (ENGINEERING, deterministic render) |
| E2 | Drive increases with |az|; table for ρ 0.22–0.35 × |az| 0–30° (`AUTONOMOUS_RESEARCH_LOG.md:99`; protocol `:20`) | `results/v7_encoder_distance_az_20261029.txt` | **IND**: RT r1 e1.py (`v5v4_protocol_redteam_r1.md:42-47`) and RT r2 (`v5v4_protocol_redteam_r2.md:19`, identical cells) |
| E3 | "Falls below threshold (~7 mV) for ρ ≥ 0.28 m" (`VALIDATION_PLAN.md:343`) | E2 table | **CONTRA**: drive is 7.08 mV at ρ 0.28 / |az| 20° and 8.37 mV at 30° (az file). In V5 v3, 5 of 18 scenes with ρ ≥ 0.28 were non-zero (RT r1 `:49`). Corrected in the protocol but **not in the plan** |
| E4 | ALIF threshold "~7 mV" (`VALIDATION_PLAN.md:343`; az file header line 1; protocol `:20`) | v6 ipsi curves; control check v2; mech A | **CONTRA**: DATA onset is ~6.0 mV and g30 is 6.28 mV at the V5 configuration (Section 4.1). Note also RT r1 `:50`: ρ 0.205, az 1.2° (6.4 mV) gave d ≠ 0 |
| E5 | "The SNN dead zone is ENGINEERING × MODEL, not topology" (`VALIDATION_PLAN.md:344`) | v6 | **AUTH**, approximately right. Topology shifts the dead-zone edge slightly (6.0 mV: DATA 16.3 Hz vs SWS 2.0 Hz), and that edge is where S2 operates |

### 2F. Mechanism LC10a → AOTU (`v5_mech_strength.py`)

| # | Claim (source) | Artifact | Status |
|---|---|---|---|
| F1 | 62 % of LC10a output synapses go to AOTU* (`VALIDATION_PLAN.md:327-328`) | docstring in the A/B JSON protocol: 58 458/94 310 | **AUTH** (DATA count, computed by the script) |
| F2 | Slopes DATA 496, CUT 196, RAND_CUT 262–276, SCALE 253 (`AUTONOMOUS_RESEARCH_LOG.md:56`) | `v5_mech_strength_A_20261029T170217.json` calib | **AUTH**, matches |
| F3 | Closed loop d vs DATA: CUT +0.73 (0.27; 1.22), RAND_CUT +1.94 (0.99; 2.90), SCALE +2.51 (1.46; 3.58) (`:57`) | `v5_mech_strength_B_*.json` tests | **AUTH**; +R (0.727 / 1.935 / 2.505; 17/50 zeros) |
| F4 | Post hoc CUT − RAND_CUT −1.21° (−1.85; −0.62) (`:57`; `VALIDATION_PLAN.md:330`) | **no artifact** contains it | **UNSUP** by any saved artifact. +R from `runs`: −1.207 (−1.84; −0.61), so the number is reproducible |
| F5 | "Red Team (own): ... PASS_WITH_LIMITATIONS"; "gain does not explain it" (`AUTONOMOUS_RESEARCH_LOG.md:58-59`) | none in `results/redteam/` | **AUTH**: a self-review only, with no RT file. My observation from the same artifacts: the closed-loop deficit order CUT < RAND_CUT < SCALE (0.73 < 1.94 < 2.51) matches the order of the **weak-drive response** (g 0.55: 22.0 / 17.0–17.9 / 14.1 Hz; g 0.5: 4.2 / 0 / 0) and does **not** match the slope order (196 < 253 < 262–276). This is consistent with the view that the response near threshold (~6–6.6 mV), not small-signal slope, predicts closed-loop error. It is descriptive only, with 3 conditions |
| F6 | "LC10a → AOTU explains 43 %" retracted (`VALIDATION_PLAN.md:332`; `NEXT_SESSION.md:16`) | — | Retraction recorded; consistent |

---

## 3. Numbers that differ between documents and artifacts

| Item | Document | Artifact or recomputation |
|---|---|---|
| DATA vs P pairs | "450/450" (`V5v4_FINAL_REPORT.md:63`), "in every scene" (`:77`) | 446/450 (`c_p.py`) |
| Threshold | "~7 mV" (`VALIDATION_PLAN.md:343`, az file header, protocol `:20`) | onset 6.0 mV, g30 6.28 mV (v6 default row) |
| ρ ≥ 0.28 silent | `VALIDATION_PLAN.md:343` | 7.08–8.37 mV at |az| 20–30° (az file) |
| H1 p values | report: p 1·10⁻⁵, p_Holm 2·10⁻⁵ | `audit_independent.txt`: 5·10⁻⁶ / 1·10⁻⁵ (a permutation-floor difference; harmless) |
| V5 v3 [0.22, 0.24) sub-band sign | "structure replicated" (`V5v4_FINAL_REPORT.md:70`) | V5 v3 +0.68 (n 6) vs V5 v4 −0.16 (n 105) |
| V5 v3 equivalence "≤ ~0.5°" | `VALIDATION_PLAN.md:376,397` | V5 v4 S2 CI to −0.71, S2b to −0.99 |

---

## 4. The requested check: SWS vs DATA steady-state response under weak drive (~6–9 mV)

Source: `results/v6_stability/v6_stability_20261029T170806.json`, `ipsi_curve`. The values are mean DNa02 ipsi rates in Hz over a 300 ms open-loop run, averaged over ALIF seeds 1001–1010 and both sides (20 values per point; `v6_stability.py:37-49`). AMPS are 0.40–1.00 in steps of 0.025, with LC10a current = 12 mV·amp. **SWS = one instance, seed 1401** (`v6_stability.py:78`), rebuilt for each J0. No SEM is stored. For scale: RT v1 measured the noise SD of DATA r(0.50) between 5-seed sets at about 7 Hz (`v5v3_control_redteam.md:89`), so SE at 20 values is roughly 3 Hz near threshold.

### 4.1 V5 configuration (J0 0.2, noise 2 mV, b_a 0.5, delay 1.8 ms)

| mV | DATA | SWS | SWS−DATA |
|---|---|---|---|
| 5.70 | 0.0 | 0.0 | 0.0 |
| **6.00** | 16.3 | 2.0 | **−14.3** |
| 6.30 | 31.0 | 24.5 | −6.5 |
| 6.60 | 61.2 | 50.5 | −10.7 |
| 6.90 | 88.3 | 81.5 | −6.8 |
| 7.20 | 98.3 | 90.5 | −7.8 |
| 7.50 | 116.8 | 105.2 | −11.6 |
| 7.80 | 134.2 | 126.5 | −7.7 |
| **8.10** | 147.7 | 150.3 | **+2.6** |
| 8.40 | 161.3 | 169.2 | +7.9 |
| 8.70 | 176.2 | 185.2 | +9.0 |
| 9.00 | 188.5 | 194.2 | +5.7 |
| 9.30 | 196.0 | 199.0 | +3.0 |
| 9.60 | 202.0 | 203.2 | +1.2 |
| 9.90 | 207.0 | 207.5 | +0.5 |
| 10.2–12.0 | 212–226 | 210–226 | −0.5 … −2.5 |

In this configuration SWS is weaker over 6.0–7.8 mV (7 points, −6.5 to −14.3 Hz), stronger over 8.1–9.9 mV (+0.5 to +9.0 Hz), and within ±2.5 Hz at 10 mV and above.

**Two other artifacts, same configuration (g → mV = 12·g):**
- Author, `results/v5v3_prep/v5v3_control_check_v2_20261029T165755.json`, ALIF seeds 1001–1015, SWS 1401/1402/1403. SWS−DATA (Hz):
  - 6.0 mV: −14.2 / −14.1 / −16.1
  - 6.6 mV: −9.8 / −9.6 / −10.2
  - 7.2 mV: −5.0 / −4.7 / −7.6
  - **8.4 mV: +6.8 / +4.4 / +5.5**
  - 12 mV: −0.9 / −1.6 / −1.9

  SEM is 0.5–1.8 Hz, so the 6.0–7.2 and 8.4 mV differences are each several SEM.
- RT, `results/redteam/v5v3_control_v2_redteam.md:57-59` (raw output in `.../31945ef1-.../scratchpad/redteam3v2/b3.out`), ALIF seeds 1101–1110, SWS 1441–1443. SWS−DATA (Hz):
  - 6.0 mV: −8.2 / −8.0 / −9.7
  - 6.6 mV: −10.0 / −11.5 / −10.3
  - 7.2 mV: −8.3 / −6.2 / −6.3
  - **8.4 mV: +3.0 / +4.5 / +6.0**

That makes 6 distinct SWS instances in total (1401–1403 author, 1441–1443 RT), all at the V5 configuration. None of them is one of the 450 instances actually used in the V5 v4 closed loop (seed + 400 000). Instance 1401 appears in both v6 and check v2, so those two are not independent.

### 4.2 All 20 v6 settings, 6.0–9.0 mV window (11 points each)

SWS−DATA in Hz at 6.0 | 6.3 | 6.6 | 6.9 | 7.2 | 7.5 | 7.8 | 8.1 | 8.4 | 8.7 | 9.0 mV. "Neg/pos" counts points with SWS < DATA and SWS > DATA. Δg30 is in g units.

| Setting | SWS−DATA (Hz), 6.0 → 9.0 mV | Neg/pos | Mean | Δg30 |
|---|---|---|---|---|
| J0 .15, n 1, b 0 | 0, 0, −25.7, −8.7, −3.9, −2.6, −2.1, −1.9, −2.3, −3.5, −2.3 | 9/0 | −4.8 | +0.0068 |
| J0 .15, n 1, b .5 | 0, 0, −3.7, −6.7, −5.4, −8.9, −9.2, −9.0, −6.3, −7.0, −2.5 | 9/0 | −5.3 | +0.0128 |
| J0 .15, n 2, b 0 | −0.8, −23.1, −11.1, −3.9, −2.2, −0.7, −2.0, −1.8, −1.8, −2.3, −2.3 | 11/0 | −4.7 | +0.0039 |
| J0 .15, n 2, b .5 | −0.7, −3.1, −6.0, −5.9, −10.0, −5.5, −9.6, −5.1, −3.5, −3.0, −0.2 | 11/0 | −4.8 | +0.0080 |
| J0 .15, n 3, b 0 | +0.9, −6.0, −1.7, −1.2, −2.3, −1.5, −1.2, −2.3, −2.0, −2.5, −4.2 | 10/1 | −2.2 | +0.0002 |
| J0 .15, n 3, b .5 | +2.0, +2.7, −0.6, −3.4, −0.5, −1.2, 0, −0.4, +2.5, +1.7, −1.1 | 6/4 | +0.2 | −0.0053 |
| J0 .20, n 1, b 0 | 0, 0, −4.9, −3.3, −3.2, −1.5, −0.8, 0, −0.3, −0.3, 0 | 7/0 | −1.3 | +0.0002 |
| J0 .20, n 1, b .5 | 0, 0, −14.4, −13.4, −5.5, −6.6, −2.7, −6.0, −0.4, +8.0, +9.1 | 7/2 | −2.9 | +0.0139 |
| J0 .20, n 2, b 0 | −27.7, −8.3, −4.6, −3.2, −3.0, −0.8, −0.8, −1.1, 0, 0, +0.5 | 8/1 | −4.5 | +0.0070 |
| **J0 .20, n 2, b .5 (V5)** | −14.3, −6.5, −10.7, −6.8, −7.8, −11.6, −7.7, +2.6, +7.9, +9.0, +5.7 | 7/4 | −3.7 | +0.0070 |
| J0 .20, n 3, b 0 | −6.0, −5.7, −5.2, −2.8, −2.3, −2.0, −0.5, −1.0, −0.1, +0.4, 0 | 9/1 | −2.3 | +0.0107 |
| J0 .20, n 3, b .5 | −5.2, +2.3, +1.0, −10.8, −3.8, +1.8, +0.2, +2.0, +4.4, +2.6, +4.1 | 3/8 | −0.1 | +0.0076 |
| J0 .25, n 1, b 0 | ≈ 0 throughout (−0.3 … 0) | 4/0 | −0.1 | 0.0 |
| J0 .25, n 1, b .5 | 0, 0, −6.7, +1.3, +2.8, +14.0, +13.5, +25.3, +31.0, +35.7, +35.3 | 1/8 | +13.8 | +0.0008 |
| J0 .25, n 2, b 0 | −13.8, −1.2, −0.5, … ≈ 0 | 8/1 | −1.5 | +0.0014 |
| J0 .25, n 2, b .5 | −5.0, −8.4, +7.0, +3.8, +2.0, +3.4, +11.2, +22.9, +27.9, +21.2, +17.8 | 2/9 | +9.4 | +0.0017 |
| J0 .25, n 3, b 0 | −2.5, −0.5, −0.7, … ≈ 0 | 5/2 | −0.3 | +0.0016 |
| J0 .25, n 3, b .5 | +1.0, −6.0, −5.8, +6.0, +9.0, +2.2, +7.5, +17.1, +22.3, +16.8, +8.5 | 2/9 | +7.2 | +0.0042 |
| J0 .20, n 2, b .5, delay 1.0 | −12.7, −5.6, −9.5, −13.9, −13.5, −15.3, −14.0, −12.3, −6.5, +3.0, +3.4 | 9/2 | −8.8 | +0.0089 |
| J0 .20, n 2, b .5, delay 3.0 | −13.8, −8.7, −6.1, +1.3, −3.6, −3.0, +9.1, +9.8, +9.5, +11.3, +1.3 | 5/6 | +0.7 | +0.0090 |

In total, SWS < DATA in 133 of 220 cells in the window. Δg30 > 0 (SWS needs more drive to reach 30 Hz) in 18/20 settings, yet in 4 of those settings SWS is *stronger* than DATA for most of 7–9 mV (J0 0.25 with b_a 0.5; J0 0.2 with noise 3 and b_a 0.5). **The threshold direction and the steady-state response above threshold are different quantities. v6 reports only the threshold.**

### 4.3 Crossover (first amplitude where SWS > DATA + 2 Hz), from `c_cross.py`

- **b_a = 0, 9 settings: no crossover at any amplitude** (4.8–12 mV). SWS is weaker or equal everywhere.
- **b_a = 0.5, 11 settings:** crossover at 6.3–9.9 mV in 9 of them.
  - 6.3 mV: J0 .15 noise 3; J0 .20 noise 3.
  - 6.6–7.2 mV: all three J0 .25 settings.
  - 7.8–8.7 mV: J0 .20 noise 1 and noise 2, and the two delay variants.
  - 9.9 mV: J0 .15 noise 1.
  - No crossover in the window: J0 .15 noise 2 (whole curve) and J0 .15 noise 3, where the curves cross briefly but never by more than 2.7 Hz.
- DATA onset (first non-zero point) ranges from 5.4 to 6.6 mV.

**Conclusion of Section 4.** The statement "SWS has a weaker steady-state response than DATA under weak drive" is supported at the V5 configuration for roughly 6.0–7.8 mV. The evidence is the v6 default row (1 instance), the author's control check v2 (3 instances) and RT v2 (3 other instances), with differences of about 5–16 Hz. Above about 8 mV the sign reverses, by +3 to +9 Hz. The window "6–9 mV" is therefore wrong at its upper end. Both the reversal and the crossover location depend on the MODEL: they require b_a = 0.5, and the crossover moves with J0 and noise. No open-loop curve exists for any of the 450 SWS instances used in V5 v4.

---

## 5. Scope: what is explicitly scoped, and where scope was widened without saying so

**Explicitly scoped (good):**
- V5 v4: "only ρ ∈ [0.16; 0.28) m, az0 ∈ (−30°, 30°), one configuration (J0 0.2, threshold 5 synapses, ALIF b_a 0.5, encoder V4 v2); ρ ≥ 0.28 untested" (`V5v4_FINAL_REPORT.md:75-76`). Also protocol `:42` and `:108` ("In the model (ALIF, J0 0.2, engineering encoder) ...").
- V5 v4 "not a claim about the fly brain" (`:71`). "Calibration equalises only small-signal gain" (`:73-74`). Effect size at the SESOI boundary (`:53-54`). No result RT was run (`:26`).
- V5 v3: "the result concerns this model (J0 0.2, ALIF, ENGINEERING encoder), not the fly" (`VALIDATION_PLAN.md:379-380`). "Equivalent" refers to the V5 v2 scene distribution (`:397-398`, after RT `v5v3_result_redteam.md:100`).
- v6: exploration only, not used to pick parameters (`v6_stability.py:2-3`). "Direction robust at the criterion boundary" (`VALIDATION_PLAN.md:341`).
- Mech: exploration on dev seeds (`VALIDATION_PLAN.md:327`); the "43 %" claim was retracted (`:332`).

**Scope widened without saying so:**
1. `V5v4_FINAL_REPORT.md:66-67` says "beyond lateralisation **and signal scale**". This holds only for small-signal decoder gain, and is measured on 10/450 instances (C10). The same report restricts it at `:73-74`, but the headline sentence does not.
2. `V5v4_FINAL_REPORT.md:67-68`: the "strong drive / weak drive" regime labels are presented as the explanation. Drive was never manipulated in closed loop; this is ρ relabelled as drive (finding 6).
3. `V5v4_FINAL_REPORT.md:79-80`: V6 "18/20" is used as robustness support across J0 and noise. It covers the threshold direction for 1 SWS instance in open loop, and the reversal needed for the S1 sign appears only with b_a 0.5 (Section 4.3).
4. `V5v4_FINAL_REPORT.md:57` and `AUTONOMOUS_RESEARCH_LOG.md:111`: SWS slope range given with no n (10/450). `VALIDATION_PLAN.md:372` and `AUTONOMOUS_RESEARCH_LOG.md:86`: V5 v3 slopes given with no n (5/50).
5. `V5v4_FINAL_REPORT.md:63,77`: "450/450" and "in every scene" turn a mean into a universal claim (CONTRA).
6. `VALIDATION_PLAN.md:343`: "silent for ρ ≥ 0.28" generalised from az 0/15° to all az. It was corrected in the protocol and left uncorrected in the plan.
7. `VALIDATION_PLAN.md:396-398`: the V5 v3 "≤ ~0.5°" conclusion still stands as the "final V5 conclusion" after V5 v4 showed per-stratum effects of about 0.5° with CIs reaching −0.71 (S2) and −0.99 (S2b).
8. `VALIDATION_PLAN.md:21` (summary table): "topology from data +16 pp (sensitivity to weak stimulus)". This V5 v2-era figure is superseded by the scale-confound audit (`:322-325`) and by V5 v3/v4, and is not updated.
9. `V5v4_FINAL_REPORT.md:69-70`: "the structure replicated" is asserted without noting that the strata boundaries differ between V5 v3 and V5 v4, or that the V5 v3 sign in [0.22, 0.24) (+0.68) did not replicate (−0.16).

---

## 6. Open questions

1. Is the S1 "control better" result driven by the high-drive reversal (SWS steeper at 8–10 mV, b_a-dependent)? Or does it come from the differential L−R gain at the near-target operating point, where both sides are driven, at ρ 0.16–0.20 and az ≈ 0 (6.4–8.1 mV)? Descriptively, S1 overshoot is larger for DATA (median 3.57° vs 2.99° for SWS, +R). A fixed-drive closed-loop test, or an open-loop *bilateral* operating-point analysis, has never been done.
2. None of the 450 V5 v4 SWS instances has an open-loop response curve. The 6 instances that were characterised (1401–1403, 1441–1443) are not from the confirmatory pool. Are the instance-to-instance spread at 6 mV and the crossover point stable across instances?
3. The weak-drive difference (6.0–7.8 mV) and the dead-zone edge (onset ~6 mV) coincide. How much of S2's −0.52° is a dead-zone-edge effect, i.e. DATA stopping closer because its threshold is lower? Mechanically this is a small threshold shift (Δg30 0.007 g ≈ 0.08 mV) amplified by the loop. The report's "alternatives" line (`:79`) mentions ALIF threshold nonlinearity, but it is not quantified.
4. Should the ~7 mV threshold be corrected to ~6 mV in the plan, the protocol notes and the az table header? Doing so would shift the "silent region" map (e.g. ρ 0.28 at |az| 15° = 6.45 mV, which is above onset).
5. The evidence is volatile. RT scripts and raw outputs (`/private/tmp/claude-501/.../31945ef1-.../scratchpad/{redteam3,redteam3v2,redteam_v5v3,redteam_v5v4}`) and an unreported V5 v4 audit directory (`.../scratchpad/results_audit_v5v4/`, 11 .py files dated 2026-10-30 08:16–08:21, no outputs) live outside the repo. Several IND statuses depend on those files surviving.
6. The mech post-hoc contrast CUT − RAND_CUT has no saved artifact, although it is recomputable (−1.207). The "own Red Team" of the mechanism has no file.
