# Task B: Independent recomputation of V5 v4 from raw data (2026-10-30)

**Inputs (read-only):** `flymind/results/v5v4/raw_v5v4_A.jsonl` (225 lines), `raw_v5v4_B.jsonl` (225 lines).
**Code (written from scratch, saved outside the repo):**
`/private/tmp/claude-501/-Users-admin-so101-fly-project/075990a2-3231-4039-8d41-31f3fdcb9204/scratchpad/recon/b_recompute.py` (main),
`.../recon/b_extra.py` (extras plus an automated diff against `analysis_frozen.json`), `.../recon/b_frag.py` (how fragile the SESOI labels are).
Full outputs are in `.../recon/out.txt`, `out_extra.txt` and `out_frag.txt`. Interpreter: `.venv/bin/python -I -B` (numpy 2.5.4, scipy 1.18.1).
**Settings:** paired bootstrap of the mean, 10 000 resamples, RNG seed 8419901. Sign-flip permutation test, 200 000 draws, RNG seed 8419902, p = (k+1)/(N+1), two-sided on |mean|.
t-CI95 with Student df = n−1. Holm correction over 2 tests. TOST at ±0.5°, defined as both CI95s inside (−0.5, +0.5), which is equivalent to TOST at α 0.025 per side (protocol `validation/v5v4_protocol.md:28-29`).
I read `v5v4.py` and `audit_v5v4_independent.py` only **after** I had my own numbers, to compare against them.
No simulation, runner or network construction was executed.

Sign convention: d = err(first) − err(second). d > 0 means the second condition (the control) has the lower error.

---

## 0. Bottom line

* **Every number that drives a decision reproduces.** Both H1 categories are the same: S1 "control better, effect ≥ SESOI" and S2 "DATA better, effect ≥ SESOI". Equivalence (TOST) is not shown in either stratum. H2a and H2b are both significant. **There is no decision difference.**
* Across 98 fields compared automatically, plus 30 compared by hand, the only differences > 0.005° are **bootstrap endpoints**, and they are Monte-Carlo noise from the different RNG seeds (§6).
* **Two factual errors in the report**, both CONTROL/ENGINEERING claims and neither one touches H1 or H2:
  1. `V5v4_FINAL_REPORT.md:63` says the P regulator was better in "450/450" pairs, and `:77` says "in every scene". In the raw data P beats DATA in **446/450** pairs (§5).
  2. `V5v4_FINAL_REPORT.md:57` says "SWS slopes 0.988–1.005 × DATA" with no qualifier. The source `results/v5v4/post_sws_slopes.txt:2-11` covers only **10 of 450** SWS instances (seeds 4001–4010).
* **Over-readings in the report:**
  * The claim that "DATA's advantage grows with distance, sign change at ρ ≈ 0.23" (`:56`) comes from a linear fit. Binned d is flat inside S1 and not monotonic inside S2 (§2).
  * The median d in S2 is −0.107 with a bootstrap CI of [−0.463, 0.000]: the S2 effect is carried by the tails (§3).
  * The "success" metric counts trials where the arm never moved as successes when |az0| < 5° (§5).

---

## 1. Integrity (CONTROL)

| Check | Result |
|---|---|
| Records per file / malformed lines | A 225, B 225 / 0 |
| Seeds | 450 unique, exactly 4001–4450; **0 duplicates, 0 missing, 0 extra**; A = 4001–4225, B = 4226–4450, both monotonic |
| Conditions | all 6 (DATA, SWS, STR_OWN, STR_SHARED, TOY, P) present in all 450 records; none extra |
| NaN / None in final_abs_err, az0, rho, sws_li_rel, str_li_rel, sws_changed_frac | **none** |
| `error` non-null / `calibration_refused` / `safety_ticks_flagged` > 0 | **none** |
| Stratum vs seed vs ρ range (S1 = 4001–4150, ρ ∈ [0.16, 0.22); S2 = 4151–4450, ρ ∈ [0.22, 0.28)); az0 ∈ (−30, 30) | all consistent |
| Duplicated scenes (identical az0, ρ) | 0 |
| Slopes | DATA = SWS = STR_SHARED = 492.1187 in every record; TOY = 306.0800; STR_OWN 18.42 / 124.34 / 202.86 (min / median / max), 450 unique; P null |
| sws_li_rel | 1.0 in all 450 records (max deviation 4.4e−16), so it carries **no information** per trial |
| sws_changed_frac | 0.6603–0.6776 (sd 0.0029), a very narrow range |

**Note on the slope field (CONTROL):** the raw `slope` stored for SWS is the DATA decoder slope, not the SWS instance's own small-signal slope. The raw data therefore cannot verify the report's claim that SWS slopes match DATA. See §5.

---

## 2. Per-condition errors (reproduced exactly)

| Cond | mean | median | success | S1 mean / median (succ) | S2 mean / median (succ) |
|---|---|---|---|---|---|
| DATA | 2.87725 | 1.94757 | 352 | 1.72095 / 1.75537 (141) | 3.45540 / 2.40450 (211) |
| SWS | 3.05178 | 1.91015 | 336 | 1.20864 / 0.99186 (141) | 3.97335 / 3.29150 (195) |
| STR_OWN | 4.25595 | 3.06309 | 282 | 2.28335 / 1.66427 (111) | 5.24226 / 4.32050 (171) |
| STR_SHARED | 5.66358 | 4.58852 | 227 | 1.82208 / 1.38963 (138) | 7.58432 / 7.10798 (89) |
| TOY | 4.30679 | 2.97950 | 282 | 0.55062 / 0.52598 (150) | 6.18487 / 5.72800 (132) |
| P | 0.19646 | 0.18341 | 450 | 0.27706 / 0.30263 (150) | 0.15615 / 0.16491 (300) |

Every value matches `analysis_frozen.json:5-128` and the table in `V5v4_FINAL_REPORT.md:39-46` to within 1e−5.

## 3. H1: d = DATA − SWS, per stratum

| | S1 (n 150) | S2 (n 300) |
|---|---|---|
| mean d | **+0.51232** | **−0.51795** |
| median d | +0.54341 | −0.10650 |
| SD / d_z | 0.6269 / +0.817 | 1.7168 / −0.302 |
| bootstrap CI95 (seed 8419901) | [+0.41072, +0.61329] | [−0.71221, −0.32432] |
| bootstrap CI90 | [+0.42646, +0.59468] | [−0.68168, −0.35642] |
| t-CI95 | [+0.41116, +0.61347] | [−0.71302, −0.32289] |
| p_perm (200k) / Holm | 5.0e−6 (= 1/200001, the floor) / 1.0e−5 | 5.0e−6 (floor) / 1.0e−5 |
| Wilcoxon (Pratt) | 4.38e−15 | 7.40e−8 |
| TOST, formal t (max one-sided p) | 0.595 (not equivalent) | 0.572 (not equivalent) |
| both CI95 ⊂ ±0.5? | no | no |
| zeros / >+1° / <−1° | 0 / 44 / 2 | 57 / 39 / 97 |
| **Category (protocol §6)** | **control better, effect ≥ SESOI** | **DATA better, effect ≥ SESOI** |

These are identical to `analysis_frozen.json:135-185` and `V5v4_FINAL_REPORT.md:51-52`.

* **p values (CONTROL):** frozen p_perm = 9.9999e−6 = 1/100001, which is the floor for 100k draws. The report's "1·10⁻⁵" (`:51-52`) should be read as "< 1e−5, at the MC resolution". No permutation reached |mean| in either run.
* **How fragile the "≥ SESOI" label is:** under the bootstrap, P(|mean| ≥ 0.5) = **0.60** for S1 and **0.57** for S2 (`out_frag.txt`). Both categories sit essentially on the 0.5° boundary. The report says this itself (`V5v4_FINAL_REPORT.md:53-54`), and I agree with it.

**Descriptive results (match):**

| Quantity | My value | Frozen / report |
|---|---|---|
| Pooled | −0.17453, boot [−0.31688, −0.03499], t [−0.31593, −0.03313], p_perm 0.0157 | p_perm 0.01545, MC noise |
| S2a [0.22, 0.25) | n 152, −0.38325, boot [−0.60769, −0.17361] | |
| S2b [0.25, 0.28) | n 148, −0.65630, boot [−0.98123, −0.33500] | |
| OLS d ~ 1 + ρ + \|az0\| | 3.3669 − 14.5804·ρ − 0.01185·\|az0\| (SE 0.502 / 2.099 / 0.0080) | exact match |

The OLS sign change happens at ρ = 0.231 when |az0| = 0, and at **ρ = 0.219** when |az0| is at its mean (≈15°). The report's "ρ ≈ 0.23" (`:56`) is correct only for |az0| = 0.

**Success, McNemar (exact):**

| Pair | First only | Second only | p |
|---|---|---|---|
| DATA–SWS | 29 | 13 | 0.0195 |
| DATA–STR_OWN | 84 | 14 | 2.46e−13 |
| STR_SHARED–STR_OWN | 27 | 82 | 1.26e−7 |
| DATA–TOY | 79 | 9 | 4.15e−15 |
| DATA–P | 0 | 98 | 6.31e−30 |

All match the frozen values exactly.

## 4. H2 (Holm over 2)

| | H2a DATA − STR_OWN | H2b STR_SHARED − STR_OWN |
|---|---|---|
| mean / median | −1.37870 / −0.47752 | +1.40762 / +1.05181 |
| boot CI95 | [−1.81953, −1.03222] | [+0.99505, +1.76834] |
| t-CI95 | [−1.77757, −0.97984] | [+1.01732, +1.79793] |
| p_perm / Holm | 5e−6 / 1e−5 | 5e−6 / 1e−5 |
| zeros | 57 | 75 |
| significant (p_Holm < 0.05 and boot CI excludes 0) | **yes** | **yes** |
| S1 / S2 means (descriptive) | −0.56239 / −1.78686 | −0.46127 / +2.34207 |

Both match `analysis_frozen.json:273-330` and `V5v4_FINAL_REPORT.md:59-61`.

Other comparisons:

| Comparison | Result |
|---|---|
| DATA − TOY | −1.42954, boot [−1.68227, −1.17796] |
| DATA − P | +2.68079, boot [+2.45318, +2.91821]; 348 pairs with d > 1, 0 pairs with d < −1 |
| Spearman (STR_OWN slope vs STR_OWN error) | −0.0752 (p 0.111); matches |
| H2a vs str_li_rel (new) | Spearman +0.118, p 0.012: the more lateralization STR_OWN keeps, the less DATA's advantage. This is descriptive only. |

---

## 5. Beyond the report

### (1) Zero d pairs

| | S1 | S2 |
|---|---|---|
| d == 0 exactly | 0/150 (0.000) | **57/300 (0.190)** |
| \|d\| < 0.1 | 14 | 75 |
| Zeros where DATA and SWS **both did not move** (err = \|az0\| ± 0.01) | n/a | 57/57: every zero is structural |
| DATA did not move, SWS moved | 0 | **0** |
| SWS did not move, DATA moved | 0 | **9**, d sum −31.05, mean −3.45; **20 % of the S2 d sum** |
| Both moved | 150, mean +0.512 [0.409, 0.612] | 234, mean **−0.531** [−0.759, −0.305] |

The 9 SWS-only no-move seeds are 4172, 4195, 4328, 4386, 4399, 4401, 4407, 4425 and 4441; all are in raw_v5v4_B.jsonl, at line = seed − 4225.

**Asymmetry (MODEL):**
* DATA crosses the activation threshold in every scene where SWS does. SWS stays silent in 9 scenes where DATA moves, and never the other way round.
* DATA also overshoots more: overshoot DATA − SWS is +0.51° on average in S1 and +0.33° in S2. In S1, corr(d, Δovershoot) = +0.38.
* A single explanation fits both strata. DATA behaves as if it were slightly **more excitable / higher gain** than SWS. Near targets (S1) that hurts through overshoot; far targets (S2) it helps by crossing threshold.
* This is a hypothesis, not tested. It matches the report's own alternative, "nonlinearity of the ALIF threshold" (`:79-80`). It suggests the small-signal calibration slope (verified on only 10 SWS instances) does not capture the gain difference that matters.

### (2) d by ρ (6 equal bins) and by |az0| (3 bins)

| ρ bin | n | mean d | t95 | boot95 | median | zeros | mean d among both-moved pairs |
|---|---|---|---|---|---|---|---|
| [0.16, 0.18) | 41 | +0.285 | [+0.075, +0.495] | [+0.078, +0.484] | +0.337 | 0 | +0.285 |
| [0.18, 0.20) | 59 | **+0.741** | [+0.600, +0.883] | [+0.604, +0.879] | +0.790 | 0 | +0.741 |
| [0.20, 0.22) | 50 | +0.428 | [+0.256, +0.601] | [+0.260, +0.594] | +0.448 | 0 | +0.428 |
| [0.22, 0.24) | 105 | −0.160 | [−0.342, **+0.021**] | [−0.342, +0.018] | −0.034 | 10 | −0.170 |
| [0.24, 0.26) | 89 | **−0.905** | [−1.359, −0.450] | [−1.351, −0.463] | −0.921 | 10 | −0.733 |
| [0.26, 0.28) | 106 | −0.548 | [−0.901, −0.194] | [−0.893, −0.192] | 0.000 | 37 | −0.819 |

* Within S1, d does not depend on ρ: Spearman +0.027, p 0.74. The S1 profile is an inverted U, peaking at 0.18–0.20.
* Within S2, Spearman is −0.144 (p 0.012). The last bin's mean is diluted by 37 structural zeros. Among pairs where both moved, the ordering is monotonic (−0.17, −0.73, −0.82), but with wide CIs.
* Near the boundary the transition is smooth: ρ [0.21, 0.22) gives d +0.38 (n 21) and [0.22, 0.23) gives +0.13 (n 48). There is no step artifact at 0.22.
* So the report's "DATA's advantage grows with distance" (`:56`) holds only as a coarse S1-to-S2 contrast, not as a linear trend.

| \|az0\| bin | Pooled mean d [t95] | S1 mean d [t95] | S2 mean d [t95] (zeros) |
|---|---|---|---|
| [0, 10) | −0.089 [−0.297, +0.120] | +0.547 [0.360, 0.733] | −0.439 [−0.724, −0.154] (54) |
| [10, 20) | −0.176 [−0.404, +0.051] | +0.500 [0.309, 0.692] | −0.518 [−0.828, −0.209] (3) |
| [20, 30) | −0.255 [−0.546, +0.036] | +0.487 [0.332, 0.641] | −0.588 [−0.990, −0.186] (0) |

The S1 effect is constant across azimuth. In S2 it grows mildly with |az0|. 54 of the 57 S2 zeros fall at |az0| < 10°; no-move trials go up to |az0| = 12.9°.

### (3) S1: many small differences or a few large ones?

**Answer: many moderate, consistent differences. It is a distributional shift, not driven by outliers.**

* Quantiles (0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100 %): −1.33, −1.05, −0.58, −0.35, +0.10, **+0.54**, +1.03, +1.25, +1.39, +1.66, +1.70.
* 78 % of pairs are positive (sign test p 3e−12). The maximum d is 1.70°, and no pair has d > 2.
* Trimmed means: 5 % → +0.530 [0.427, 0.628]; 10 % → +0.543; 20 % → +0.558 [0.443, 0.674]; 25 % → +0.560.
* Median +0.543, boot CI [0.414, 0.690]. Hodges–Lehmann +0.535.
* The top 10 |d| pairs contribute 19.5 % of Σd; without them the mean is still +0.442. Without the top 30 it is +0.335.
* It takes 36 of the 117 positive pairs to make up 50 % of the positive mass.

**S2, for contrast: heavy-tailed, and the median is about 0.**

* Quantiles: −7.23, −5.80, −3.70, −2.47, −1.26, **−0.11**, +0.10, +1.25, +1.74, +4.36, +5.72.
* Median −0.107, boot CI **[−0.463, 0.000]**. Hodges–Lehmann −0.420.
* Trimmed 20 % → −0.411 [−0.555, −0.266]; trimmed 25 % → −0.361 [−0.500, −0.229]. The trimmed CIs exclude 0, but by the 25 % trim the CI no longer reaches past −0.5.
* Pairs with d < −2: 46; with d > +2: 14. Fifteen positive pairs carry half of the positive mass.
* The S2 "≥ SESOI" result therefore depends on the mean of a heavy-tailed distribution. It is partly driven by threshold events (SWS-only no-move, §1).

### (4) d vs per-trial sws_changed_frac and sws_li_rel

* **sws_li_rel** is 1.0 in every trial, so it cannot explain anything. The constraint holds by construction (CONTROL OK).
* **sws_changed_frac** spans only 0.660–0.678. Spearman(d, changed_frac):

| | Spearman | p |
|---|---|---|
| S1 | −0.082 | 0.32 |
| S2 | +0.016 | 0.78 |
| all | +0.013 | 0.79 |

* Spearman(|d|, changed_frac) is about 0 in every stratum.
* By tercile, S1 gives +0.65, +0.43, +0.46 and S2 gives −0.46, −0.40, −0.67, with overlapping CIs.
* Conclusion: the small variation in how many synapses SWS changed does not explain the variation in d. With this range there is also no power to detect a dose–response (CONTROL limitation).

### (5) Duplicates, NaNs, missing data

None, see §1. The analysis code `v5v4.py:135` excludes only records whose `error` field is set. A NaN in final_abs_err with no error string would not be excluded. That is a latent gap, but nothing in this data triggers it.

### Additional findings

* **The P claim is wrong (ENGINEERING).** `V5v4_FINAL_REPORT.md:63` ("P lepszy w 450/450 parach") and `:77` ("w każdej scenie") are false. DATA ≤ P in 4 pairs:
  * seed 4309: az0 27.1, DATA 0.078 vs P 0.146
  * seed 4315: az0 0.07, DATA 0.071 vs P 0.169
  * seed 4411: az0 0.02, DATA 0.019 vs P 0.263
  * seed 4425: az0 6.3, DATA 0.157 vs P 0.179

  These are lines 84, 90, 186 and 200 of raw_v5v4_B.jsonl. The correct count is 446/450. Frozen `better_gt1 = 0` (`analysis_frozen.json:357-380`) shows only that no pair has DATA better by more than 1°. The magnitude (+2.68°) is unaffected.
* **The "success" metric is contaminated (ENGINEERING / CONTROL).** `loop.py:165-172` defines success as |e| < 5° for the whole final 0.5 s.
  * A trial with |az0| < 5° counts as a success **even if the arm never moved**. There are 70 such scenes (28 in S1, 42 in S2).
  * No-move successes: DATA 36, SWS 38, STR_OWN 39, STR_SHARED 39, TOY 45.
  * Also, 116 DATA successes have err > 2°, and 82 trials have `t_first_within` set yet fail.
  * Success counts and the McNemar tests (`V5v4_FINAL_REPORT.md:41-46, 57`) should be read with this in mind. They are not part of the decision.
* **SWS slope claim (CONTROL).** `V5v4_FINAL_REPORT.md:57` states "Nachylenia SWS 0,988–1,005 × DATA" as a general fact, but `results/v5v4/post_sws_slopes.txt:2-11` lists only seeds 4001–4010, all in S1. The protocol (`validation/v5v4_protocol.md:66`) cites a separate pre-run check (487–498). The claim covers 10/450 instances and should say so.
* **Correlated Monte-Carlo noise in the frozen analysis (CONTROL, minor).** `v5v4.py:70-80` builds a fresh `default_rng(9402)` / `default_rng(9401)` on every call. As a result:
  * comparisons with the same n (S1 vs H2 vs D) reuse the same resample indices and sign matrices;
  * the 90 % and 95 % CIs reuse the same draws.

  This is valid, but the MC errors are correlated across comparisons. It does not change any result.

---

## 6. Discrepancies vs `analysis_frozen.json` and `V5v4_FINAL_REPORT.md` (threshold > 0.005°)

**Automated comparison** (`b_extra.py`): 98 fields covering condition means, medians, success counts and per-stratum values, and for H1 S1/S2 and H2a/H2b the n, mean, median, boot95, boot90, t95, d_z, zeros, >1, <−1 and Wilcoxon p. 97 of 98 are within tolerance. The one exception:

| Field | Frozen | Mine | Diff | Cause |
|---|---|---|---|---|
| H2b boot95 lower (`analysis_frozen.json:307`) | 0.98965 | 0.99505 | +0.0054 | MC: across 20 seeds I get a mean of 0.9945, SD 0.0025 |

**Compared by hand** (S2a, S2b, DATA−TOY, DATA−P, pooled):

| Field | Frozen | Mine | Diff | MC SD of endpoint (20 seeds) |
|---|---|---|---|---|
| S2a boot95 upper (`:214-216`) | −0.17965 | −0.17361 | +0.0060 | 0.0023 |
| S2b boot95 lower (`:237-239`) | −0.98974 | −0.98123 | +0.0085 | 0.0044 |
| S2b boot95 upper | −0.32843 | −0.33500 | −0.0066 | 0.0040 |
| DATA−P boot95 upper (`:361-363`) | 2.90923 | 2.91821 | +0.0090 | 0.0029; the frozen value is about 2.6 SD below the MC mean of 2.9168 |

* All other endpoints are within 0.005, including DATA−TOY (max 0.0049) and everything pooled.
* t-CIs, means, medians, d_z, counts and the OLS fit agree to < 1e−5.
* p_perm differs only through the MC resolution: 5e−6 here vs 1e−5 frozen; Holm 1e−5 vs 2e−5; pooled 0.0157 vs 0.0154.
* Rounded report values that are affected: DATA−P CI reported as "+2,46; +2,91" (`:63`), mine 2.45 / 2.92. That is MC only.
* **No decision or category changes.**

**Report text vs data (beyond numerical tolerance):**
1. `:63` and `:77`: P better in 450/450 / every scene. **False, it is 446/450.**
2. `:57`: SWS slope range presented as general. **It is based on 10/450 seeds.**
3. `:56`: "advantage grows with distance; sign change at ρ ≈ 0.23". **This is a linear-fit artifact.** Within S1 the effect is flat (or an inverted U); 0.23 applies only at |az0| = 0, and 0.219 at mean |az0|.
4. `:51-52`: p = 1·10⁻⁵ is the **floor** of the 100k MC test, not an estimate.
5. Not stated in the report: the S2 median d is about 0 (CI includes 0); 19 % of S2 pairs are structural zeros; 20 % of the S2 effect mass comes from 9 threshold-failure pairs.

## 7. Open questions

* Is the S1/S2 sign flip a single gain/excitability difference between DATA and SWS (DATA overshoots more and activates in 9 scenes where SWS does not), rather than a property of the motif? A test would compare the SWS slopes measured on **all 450 instances** with d, and could match gain in closed loop. This needs new runs and is outside the scope of read-only work.
* Should a future protocol use a robust co-primary statistic, such as a trimmed mean or Hodges–Lehmann, for S2? There the mean and the median disagree in magnitude (−0.52 vs −0.11).
* The success definition should require movement, or should exclude |az0| < tol.
* H2a correlates with str_li_rel (ρ_s +0.12, p 0.012). The share of H2a that comes from loss of lateralization could be quantified descriptively from the existing data.
