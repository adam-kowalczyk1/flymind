# V6m2 red team — RT-G (statistics and reporting) — 2026-10-30

Reviewer: RT-G, independent. Scope: statistics, decision logic and the accuracy of `results/v6m2/REPORT.md` (DRAFT). The goal was to
falsify, not confirm. I modified no existing file. I wrote this review plus `results/v6m2/redteam/RT_G/rtg_recompute.py` and
`rtg_recompute_stdout.txt`. I ran no new simulations. Analysis RNG: 8 498 701 (nested bootstrap), 8 498 702 (crossed bootstrap),
8 498 703 (per-level crossed bootstrap). CPU time was about 7 s.

Every number below comes from the raw npz (`results/v6m2/raw/*.npz`, `dn` = [dyn 6, input 3, level, side 2, rep 8]). I checked
the results against `analysis.json`, but no result depends on it.

## 1. Reproduction: PASS
- **Exact match.** I wrote an independent stat function (`rtg_recompute.py`). For all 96 statistics in each of the 3 arms, the
  point estimates and jackknife-t bounds match `analysis.json` with a difference of 0.0. The `ci_wide` values recompute exactly.
  The per-level values match `analysis.json` `per_level` exactly.
- **Bootstrap check.** I re-ran the percentile bootstrap with the same nested scheme and my own RNG. It reproduces the json
  percentile CIs to within about 0.1 Hz (e.g. MAIN I: json [+18.38; +24.01], RT-G [+18.40; +24.02]).
- **Common seeds.** All B1 files carry the same noise seeds and the same bias as the DATA file (asserted).
- **Smoke run versus main run.** The smoke npz in the scratchpad (`v6m2_smoke/raw/MAIN_DATA.npz`, `MAIN_B1_8421001.npz`, 1 rep)
  are bit-identical to rep 1 of the main-run files. The run is deterministic, so the main-run rep 1 is a re-run of the smoke rep,
  not a separate draw.

## 2. Decision logic: the code matches the protocol
`v6m2_analysis.decide` implements protocol §2 as written:
- (a) the wider-CI lower bound of Δt(REF) is above 0;
- (b) the wider-CI lower bound of I is above 0, in Hz and in log;
- (c) Δt(T0B) ≤ 0.5·Δt(REF) at the point estimate, and the wider-CI upper bound of Δt(T0B) is below the Δt(REF) point;
- FALSIFIED = either I CI includes 0, or Δt(T0B) ≥ Δt(REF) at the point estimate;
- "generalises" = the Hz I is positive with the wider CI excluding 0, in BA1 and in J025.

MAIN meets all four criteria, so SUPPORTED is correct.

Edge cases. Neither is triggered in this run.
- An I whose CI lies entirely below 0 counts as "excludes 0" in `ex0`. It would therefore be neither SUPPORTED nor FALSIFIED. The
  protocol is silent on this case.
- The generalisation rule asks for nothing beyond the sign of the Hz I. It does not require (a), (c) or a successful rate match.

When I apply the full criteria to the robustness arms:
- BA1 meets (a), (b) and (c).
- **J025 fails (a):** Δt(REF) is +6.2 with wider CI [−0.9; +13.3].

## 3. Pseudoreplication and units
**The design.** The design is crossed, not nested. The same noise seed `sd` drives the LC10a source run, the REF replay and every
DNa02 run, for DATA and for every B1 instance, at every level and side. The analysis averages levels and sides within each rep,
which is correct.

**The two CI methods.**
- The percentile bootstrap draws reps independently for each instance, and DATA reps separately. This breaks the crossing.
- The jackknife-t leaves out one rep everywhere. It respects the crossing but ignores variance between instances.

**What the data show:**

| | MAIN | BA1 | J025 |
|---|---|---|---|
| B1 between-instance SD, REF·M0 (Hz) | 0.42 | 0.00 | 0.00 |
| B1 between-instance SD, REF·MASYNC (Hz) | 0.30 | 1.56 | 0.45 |
| corr(DATA rep, B1 rep-mean), REF·M0 | −0.31 | −0.23 | +0.44 |
| I per B1 instance (Hz), range | 18.8 to 23.3 (10/10 > 0) | 10.3 to 12.3 | 20.1 to 24.7 |
| I with one B1 instance left out (Hz), range | 20.9 to 21.4 | 11.1 to 11.6 | 21.8 to 22.9 |
| I per shared noise seed (Hz) | 15.4 to 27.7 (8/8 > 0) | 0.8 to 16.9 (8/8) | −6.9 to 45.4 (7/8) |
| SE of I: nested pct / crossed bootstrap / jackknife | 1.45 / 1.62 / 1.64 | 1.67 / 1.91 / 1.95 | 5.13 / 6.04 / 6.41 |

- **B1 instances carry almost no independent information.** The effective sample size is 8 shared noise seeds on one DATA network.
  The "10 B1" and "5 B1" counts should not be read as independent replicates.
- **The percentile interval under-covers.** Its SE is 10–20 % below the crossed-bootstrap SE. The "wider of the two" rule protects
  the decisions: with a crossed bootstrap that also resamples instances, every decision is unchanged.
- **Wording.** REPORT §1 calls the bootstrap a "paired hierarchical bootstrap". It is paired only across cells, not across sources.
- **The arms are not independent replications.** BA1 and J025 use the same noise seeds (8 443 201–208) and the same B1 instances
  (8 421 001–005). These are also the first 5 MAIN instances.

## 4. Per-level heterogeneity
Protocol §2 says "Per-level results reported". **REPORT.md reports no per-level results.** This is a protocol-reporting deviation.

Per-level values. CI = the wider of the jackknife-t over reps and a crossed bootstrap (4 000):

| arm / level | gap REF·M0 | Δt(REF) | Δt(T0B) | **I (Hz)** | I (log) | T0B·MASYNC rate, DATA / B1 |
|---|---|---|---|---|---|---|
| MAIN 7 | −8.3 [−10.8; −5.7] | +3.3 [−0.9; +7.4] | −1.3 [−5.0; +2.5] | **+4.5 [−1.7; +10.7]** | +1.01 [−0.67; +2.47] | **1.0 / 0.4 Hz** |
| MAIN 8 | −24.2 | +5.8 [−0.3; +11.9] | −14.9 | **+20.7 [+15.6; +25.8]** | +0.95 [+0.83; +1.08] | 36.0 / 15.0 |
| MAIN 9 | −29.7 | +15.3 [+9.8; +20.9] | −22.9 | **+38.2 [+34.1; +42.3]** | +0.44 [+0.39; +0.49] | 105.2 / 75.7 |
| BA1 9.5 | −11.0 | +2.2 [−1.7; +6.0] | −0.5 [−4.1; +3.0] | **+2.7 [−1.6; +7.0]** | +0.87 [+0.59; +1.19] | 8.9 / 3.7 |
| BA1 10.5 | −17.5 | +6.0 [+1.7; +10.3] | −13.9 | **+19.9 [+10.1; +29.7]** | +0.73 [+0.55; +0.92] | 22.9 / 13.8 |
| J025 7.5 | −20.7 | +8.5 [−0.2; +17.1] | −5.6 [−32.9; +21.7] | **+14.1 [−7.2; +35.3]** | +0.52 [+0.32; +0.73] | 66.4 / 40.3 |
| J025 8.0 | −10.7 | +4.0 [−3.5; +11.4] | −26.7 | **+30.7 [+16.0; +45.3]** | +0.28 [+0.18; +0.39] | 109.6 / 92.3 |

**The Hz interaction is not established at the lowest level of any arm.** At MAIN 7, BA1 9.5 and J025 7.5 the CI includes 0. The
interaction grows steeply with drive (MAIN: 4.5, 20.7, 38.2 Hz).

**Criterion (a) holds at only 2 of the 7 levels:** MAIN 9 and BA1 10.5. "Synchrony is harmful under REF" is a pooled result that
comes mostly from the top level.

**The log metric has a floor problem in T0B × MASYNC.** At MAIN 7 the −38 mV bias plus asynchronous input nearly silences DNa02
(DATA 1.0 Hz, B1 0.4 Hz). MAIN has 178 B1 (level, side, rep) cells at exactly 0 Hz. The per-level log-ratios there (1.01 at
MAIN 7) are not interpretable. The pooled IL is computed on pooled means, which level 9 dominates, so the floor affects it less.

**At the one level free of the floor, the primary result is at its strongest.** At MAIN 9 the T0B·MASYNC rates are 105 and 76 Hz,
and both metrics strongly support I > 0. The MAIN conclusion therefore does not rest on the floor artefact.

**Sides differ.**
- BA1: I is L +14.8 [+8.4; +21.3] and R +7.8 [+1.4; +14.2]. Δt(REF) on side R is +1.8 [−2.6; +6.3], which includes 0.
- J025: I on side R is +12.9 [−2.9; +28.7], which includes 0.

## 5. Rate matching (T0B) is not achieved in J025, and only on average elsewhere
`bias_calibration.json`, J025: the chosen bias sits at the lower edge of the pre-registered grid (−60 mV). At that bias the
calibration rate is 169.5 Hz against a REF target of 110.9 Hz. The main run gives:

| arm | level | DATA·M0 REF | DATA·M0 T0B | difference |
|---|---|---|---|---|
| J025 | 7.5 | 95.5 Hz | 162.9 Hz | **+71 %** |
| J025 | 8.0 | 111.8 Hz | 176.8 Hz | **+58 %** |

The calibration therefore failed in J025. J025 "T0B" is in fact t_ref 0 with partial bias.

REPORT §1 says the bias was "calibrated on separate seeds so DATA's DNa02 rate matches REF", and the §2 column is headed
"Δt T0B (rate-matched)". **Both statements are false for J025.**

In MAIN and BA1 the match holds only on the average across levels:
- MAIN level 7: +21 %
- BA1 level 10.5: −20 %

**The match holds only in M0, not in MASYNC.** For DATA in MAIN, T0B·MASYNC is 47.4 Hz against REF·MASYNC 107.3 Hz, so Δt(T0B) is
measured at a much lower operating point. This makes the Hz interaction partly a contrast of operating points. T0 (unbiased, higher
rate) brackets T0B from the other side and gives I > 0 in MAIN (+15.4 [+12.1; +18.6]) and BA1 (+13.5). This is the strongest
argument against an operating-point artefact. **In J025 the bracket fails:** I(T0) is +10.1 [−5.5; +25.8], and the MCIRC I(T0B) is
+7.9 [−14.1; +29.9].

## 6. "Generalises" with 5 B1 instances and 2 levels
The pre-registered rule is literally met: BA1 I = +11.3 [+6.7; +15.9]; J025 I = +22.4 [+7.2; +37.5].

The evidence from J025 is weak:
1. T0B is not rate-matched (§5).
2. Δt(REF) is not significant, so criterion (a) fails.
3. The bracket fails (§5): I(T0) and the MCIRC I(T0B) both have CIs that include 0.
4. The Hz I is not significant at 7.5 mV or on side R (§4).
5. The 5 B1 instances add no variance (§3). The arms share noise seeds and B1 IDs.
6. With a Bonferroni correction over the 6 decision tests (a, b-Hz, b-log, c, BA1, J025; jackknife-t, t₇ quantile 3.8), the J025
   Hz I has CI [−1.0; +45.7] and BA1 Δt(REF) has [−1.1; +9.3]. Both include 0. The J025 result survives m = 2.

BA1 is solid: the full criteria hold, and I > 0 holds under every resampling scheme.

## 7. Multiplicity
- **Interval counts.** The protocol says "~40 intervals" and REPORT §4 says "~60". `analysis.json` holds 288 (96 per arm).
- **Primary.** One pre-registered conjunction, which needs no adjustment.
- **With Bonferroni m = 60 (t₇ quantile 5.58), these survive:** MAIN I (Hz [+12.0; +30.3]; log [+0.38; +0.72]); BA1 I (Hz
  [+0.45; +22.2]); IL|T6 < 0 in MAIN and BA1, and J025 at the bound [−0.09; −0.00].
- **These do not survive:**
  - MAIN Δt(REF) [−0.04; +16.3]
  - MAIN Δt(T1) "one blocked step already makes synchrony harmful" [−4.5; +17.6]
  - MAIN Δt(NOLEAK)
  - J025 Hz I [−13.4; +58.2]
  - every J025 Δt

The secondary sentences in REPORT §2–§3 should be marked as unadjusted.

## 8. Count share and other ratio statistics
- countshare|REF is stable. Its denominator, gap REF·M0, lies well away from 0. Values: MAIN 0.61 [0.48; 0.73], BA1 0.71
  [0.51; 0.92], J025 0.60 [0.24; 0.97]. The REPORT gives "~60–70 %" as point estimates only. J025's CI runs from 0.24 to 0.97.
- **countshare|T0B is undefined.** Its denominator, gap T0B·M0, has a CI that includes 0 (or nearly does) in every arm: MAIN −4.0
  [−8.6; +0.5], BA1 +0.1 [−2.9; +3.1], J025 −5.5 [−26.8; +15.7].
  - BA1 point estimate −56.7. Jackknife CI [−365; +252]. 35 of 10 000 replicates in my nested bootstrap are ±inf. This is the source
    of the RuntimeWarning at the top of `analysis_stdout.txt`.
  - MAIN: percentile [2.5; 14.3] against jackknife [−0.4; 8.9].
  - The REPORT does not quote it, which is correct. Protocol §2 does ask for "count route under REF and T0B". The REPORT should
    state that the T0B share is undefined, not omit it silently.
- **Fmatch.** BA1 Fmatch|T0B is 1.01, i.e. the gap sign reverses. J025 Fmatch|T0B is [−0.63; 1.93].
- **The "~30–40 %" share of the DNa02 refractory penalty in §3 has no estimate or CI behind it.** It is 1 − countshare|REF. Its CIs
  are MAIN 27–52 %, BA1 8–49 % and J025 3–76 %. As a timing share it is also not identified as purely refractory, because under
  t_ref 0 the timing term changes sign.

## 9. Check of REPORT §2–§3 numbers against analysis.json
Every table cell in §2 matches the wider CI in `analysis.json`, rounded to 0.1. I checked 27 cells plus the secondary numbers:
- MCIRC interactions;
- T0 +15.4 [+12.1; +18.6];
- NOLEAK −0.9 / +1.1 / +1.7 [+0.8; +2.5];
- T6 −0.5;
- T1 +1.6 [−0.3; +3.4];
- Fmatch 81 % [62; 100] / 83 %, BA1 ~100 %, J025 65 % / 80 %;
- countshare 0.61 [0.48; 0.73] / 0.71 / 0.60;
- gap T0B·MASYNC −17.0;
- short ISI 0.20 vs 0.41.

I found no arithmetic error. The errors are in the wording:
1. **"T6 vs REF: −0.5 (n.s.) → more refractoriness than 3 steps adds nothing" and §3 "3 vs 6 steps make no difference".** These
   hold in Hz only. On the log metric, IL|T6 is −0.060 [−0.075; −0.047], −0.080 [−0.109; −0.050] and −0.045 [−0.065; −0.026]. All
   three CIs exclude 0, so T6 has a larger relative synchrony penalty than REF in every arm. IL|T1 > 0 and IL|T0 > 0 in every arm.
   The log metric therefore shows the full dose order T0 < T1 < REF < T6 that the protocol predicted under H-RS. The REPORT
   understates its own dose evidence and makes a claim that one metric contradicts.
2. **§3: "without it (0 blocked steps; rate-matched or not), the sign reverses".** This is not shown in J025. Δt(T0) is −3.9
   [−23.8; +15.9], the MCIRC Δt(T0) is +2.35 (positive), and Δt(T0B) is [−34.6; +2.3].
3. **§3: "a refractory block of ≥ 1 time step … is what turns synchrony into a disadvantage" and "Δt +4…+9 Hz".** BA1 Δt(T1) is
   +0.4 [−3.3; +4.1] and J025 Δt(REF) has a CI that includes 0. The caveat later in the same bullet ("1 step suffices in MAIN (not
   in BA1)") contradicts the opening sentence.
4. **§3: "holds at three parameter sets".** Only the Hz sign of I holds, with the J025 caveats in §6.
5. **§2 NOLEAK: "BA1 +1.1 (n.s.)".** This is correct. Unmentioned: MAIN I|NOLEAK|MCIRC is −1.5 [−3.0; −0.01] and J025 MCIRC is +2.6
   [+0.9; +4.3]. Both exclude 0 and have opposite signs. All are small relative to Δt, so "leak not required" stands, but the
   statement is not a null.

## 10. Timeline and disclosure (file mtimes and hash records)
Ordering is intact. The r2 protocol (sha f8faf355) and the analysis script (sha 23360b5e, mtime 15:24:36) were hashed at 15:24:37.
That is before the calibration output (15:26:05) and before the first main npz (15:29:23). All current file hashes equal the
recorded ones. The clock times written in the documents, however, are wrong:

| statement | file evidence |
|---|---|
| Protocol header "r1 ~15:35; r2 ~15:45"; r2 note "(15:45, before any main-run output)" | r1 sha recorded 15:18:58; r2 file saved 15:21:30; r2 sha 15:24:37; **main run finished 15:33:01** |
| REPORT §1 "Execution … 15:1x–15:33" | calibration 15:24:37–15:26:05; jobs 15:26:05–15:33:01 |
| AUTONOMOUS_RESEARCH_LOG "Run started ~15:50" | 15:24:37 |

The protocol times are later than the end of the run. A reader who trusts them would conclude that r2 was written after the
results. The protocol cannot be edited without breaking its hash, so the correction must go into the REPORT as an erratum.

**The smoke disclosure is incomplete.** There were two smoke runs:
- **r1 smoke:** aborted in the r1 rejection sampler. It left no artefact I could find, so "no data seen" cannot be verified.
- **r2 smoke:** completed. Config `v6m2_smoke/config_20261030T152334.json`: `smoke: true`, protocol sha f8faf355. It ran the full
  MAIN calibration (bias −38, identical) and wrote DNa02 npz for DATA and B1 8 421 001, rep 1, at 15:23:55 and 15:24:00. That is
  **37 s before the analysis script was hashed**.

"Its DNa02 values were not opened" cannot be checked. The risk is low: one rep of two sources, and the analysis follows protocol §2
closely. The disclosure should still name both smoke runs, say where they ran (scratchpad, outside the results tree) and give the
times. The r1 version of `v6m2.py` (sha d6fd9980) is not preserved. The claim that r2 changed only the sampler therefore cannot be
diffed.

## 11. Model versus biology language
The language is mostly correct. The status line, the §3 heading "(MODEL level)", "in this model", "(model level)" and the "Not
shown: … Drosophila" line are all appropriate. Two fixes:
1. The title asks "does DNa02 refractoriness make …" with no model qualifier. Suggested: "in the ALIF model, does model-DNa02
   refractoriness …".
2. §3 "This is a per-volley cap: within a volley DNa02 can emit at most one spike per (block + 1) steps". This is a property of the
   model's hard-reset rule, not a measured mechanism. No volley-level analysis was done. It should be phrased as the model rule
   that would produce the effect.

## Verdict: PASS_WITH_LIMITATIONS
The primary MAIN result is robust to every check I could apply:
- exact reproduction;
- crossed bootstrap;
- 8/8 shared seeds and 10/10 B1 instances positive;
- both sides;
- levels 8 and 9 on both metrics;
- Bonferroni-60.

The robustness and secondary claims in the REPORT overstate the evidence. Specifically: J025 is not rate-matched, per-level results
are missing, the "T6 = REF" claim is metric-dependent, "generalises" rests on weak J025 evidence, and the timestamps and smoke
disclosure are inaccurate.

### Required corrections to REPORT.md
1. **§1 and the §2 header (J025 T0B):** state that the J025 calibration hit the grid edge (−60 mV) and failed. DATA T0B·M0 is
   +58 % / +71 % above REF at 8.0 / 7.5 mV. Rename the column "T0B (rate-matched in MAIN/BA1 on average; NOT in J025)". Give the
   per-level mismatch for MAIN 7 mV (+21 %) and BA1 10.5 mV (−20 %).
2. **Generalisation wording:** replace "generalises across the 3 tested parameter sets" with something like: "pre-registered
   generalisation rule met (Hz I > 0 in BA1 and J025). BA1 meets all MAIN criteria. J025 fails (a), is not rate-matched, its T0 and
   MCIRC interactions include 0, and its I does not survive a 6-test Bonferroni. The arms share noise seeds and B1 instances 001–005,
   and between-instance variance is about 0, so this is robustness at two parameter settings, not independent replication."
3. **Add a per-level (and per-side) table**, as protocol §2 requires (cf. §4 of this review). State that the Hz I is not established
   at the lowest level of any arm and grows with drive, and that criterion (a) holds per level only at MAIN 9 and BA1 10.5.
4. **Disclose the T0B × MASYNC operating point:** DATA 47.4 Hz against REF·MASYNC 107.3 Hz in MAIN, and 1.0 / 0.4 Hz at MAIN 7 mV
   (178 zero-rate B1 cells). Per-level log-ratios at the floor are uninterpretable. Note that MAIN 9 mV (no floor) still gives
   I = +38.2 [+34.1; +42.3] Hz and +0.44 [+0.39; +0.49] log.
5. **Correct "T6 vs REF … adds nothing" (§2) and "3 vs 6 steps make no difference" (§3):** these are Hz only. Give IL|T6 (−0.060,
   −0.080, −0.045; all CIs exclude 0) and report the log-metric dose order T0 < T1 < REF < T6 in all arms.
6. **§3 first bullet:** restrict "≥ 1 blocked step suffices" and "Δt +4…+9 Hz" to MAIN. Restrict "the sign reverses at 0 blocked
   steps" to MAIN and BA1, since J025 Δt(T0) and Δt(T0B) have CIs that include 0 and the MCIRC Δt(T0) is positive. Replace "holds
   at three parameter sets" accordingly.
7. **Give CIs for the share statements:** count route REF MAIN 0.61 [0.48; 0.73], BA1 [0.51; 0.92], J025 [0.24; 0.97]. Present the
   "~30–40 % refractory penalty" as 1 − countshare with CIs (MAIN 27–52 %, BA1 8–49 %, J025 3–76 %), noting it is a timing share
   and not identified as purely refractory. State that countshare under T0B is undefined (denominator CI includes 0; BA1 bootstrap
   replicates infinite).
8. **§3/§4 (units and CIs):**
   - Say the effective n is 8 shared noise seeds on one DATA network, with B1 between-instance SD 0–0.4 Hz (REF·M0).
   - Say the bootstrap is nested, not paired across sources. A crossed bootstrap gives SEs equal to the jackknife and changes no
     decision.
   - Give the interval count consistently (288 computed, about 60 reported; the protocol said about 40).
   - Mark the secondary claims that do not survive Bonferroni-60 as unadjusted: MAIN Δt(REF), Δt(T1), Δt(NOLEAK), and all of J025.
9. **Timeline erratum:**
   - The protocol-header and r2-note clock times ("~15:35", "~15:45") are wrong. Actual times: r1 sha 15:18:58, r2 saved 15:21:30,
     r2 and analysis sha 15:24:37, calibration 15:24:37–15:26:05, jobs 15:26:05–15:33:01.
   - Fix "15:1x–15:33".
   - Flag the research-log "Run started ~15:50" as wrong.
10. **Smoke disclosure:** name both smoke runs (the aborted r1 run, and the completed r2 run in the scratchpad at 15:22–15:24 that
    wrote rep-1 DNa02 npz 37 s before the analysis hash). State that the main rep 1 is bit-identical to the smoke rep, and that the
    r1 `v6m2.py` (sha d6fd9980) was not preserved.
11. **Model language:** qualify the title (model DNa02). Rephrase "This is a per-volley cap" as the model's hard-reset/refractory
    rule, which was not measured at volley level.
12. **NOLEAK:** mention the two MCIRC NOLEAK interactions that exclude 0 with opposite signs (MAIN −1.5, J025 +2.6). They are small
    and do not change "leak not required", but they stop it reading as a null.
