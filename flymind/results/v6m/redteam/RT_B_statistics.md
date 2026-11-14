# V6m red team — RT-B (statistics) — 2026-10-30

Reviewer: RT-B, independent, statistics. Job: try to falsify the V6m DRAFT (`results/v6m/REPORT.md`), not confirm it.
Nothing existing was modified. New files are only this review and `results/v6m/redteam/RT_B/` (scripts + stdout + one npz).

**Seeds used (all inside the RT-B range 8 498 101–199):**
- analysis RNG: 8 498 101 (main), 8 498 102 (rep), 8 498 103 (E4), 8 498 104 (supplement), 8 498 105 (interaction analysis);
- new simulation: noise seeds 8 498 111–118, circular-shift RNG 8 498 151–158.

The simulation reused the existing DATA network and B1 instances 8 421 001–010. These are fixed model objects; the new seeds add no
new network randomness. CPU: 580 s user (≈ 10 min) for the simulation and ≈ 1 min for the analyses. No MuJoCo, no commits.

Scripts and outputs:
- `results/v6m/redteam/RT_B/rtb_recompute.py` → `rtb_recompute_stdout.txt`: recomputes from raw npz only (gaps, F, CIs under 3
  bootstrap schemes, relative F, variance components, per-level/side results, E4).
- `rtb_supp.py` → `rtb_supp_stdout.txt`: small-sample jackknife-t intervals, 99.8 % intervals, 7 mV denominator, E4 per level.
- `rtb_sim_interaction.py` / `rtb_sim_analysis.py` → `sim_interaction.npz`, `rtb_sim_analysis_stdout.txt`: the new simulation.

## 1. Reproduction from raw npz (no analysis.json): PASS
I recomputed the point estimates, gaps and F values from `raw/{main,rep}_{DATA,B1_*}.npz` (summ[..., "dn"]). They match
`analysis_stdout.txt` and REPORT §3 to the printed precision for every condition I was asked about:

| set | condition | gap | F |
|---|---|---|---|
| main | REF | −19.9 | — |
| main | LCIRC | −1.1 | +0.94 |
| main | E1c_DN_t0 | −15.6 | +0.21 |
| main | E1_DN_t0 | −15.0 | +0.25 |
| main | E2a_DN_b00 | −22.8 | −0.15 |
| main | E2b_MID_b00 | −19.5 | +0.02 |
| main | E3_MCIRC | −12.8 | +0.36 vs M0 |
| main | E1b_MID_t0 | −27.2 | −0.37 |
| main | E5a | −14.8 | +0.01 vs E1_t0 |
| rep | REF | −18.8 | — |
| rep | LCIRC | — | +0.80 |
| rep | E1c_t0 | — | +0.33 |
| rep | E1_t0 | — | +0.35 |
| rep | E2a | — | −0.21 |
| rep | E2b | — | −0.03 |
| rep | MCIRC | — | +0.23 |
| rep | E5a | — | +0.01 |

- With the original resampling scheme (my own RNG) the gap CIs agree within 0.1 Hz and the F CIs within 0.01.
- The noise seeds are identical across DATA and all B1 files (asserted).
- I found no arithmetic, indexing or replay-mismatch error in `v6m_analysis.py`.
- The pre-registered rule labels (`label()`, v6m_analysis.py:17–22) are applied as written.

## 2. Pseudoreplication and unit structure
**Common random numbers.** Every replay uses the same noise seed `sd` for DATA and for every B1 instance, both in the source free
run (v6m.py:239) and in the replay (v6m.py:265). The LC/intermediate manipulation RNGs are also shared across sources
(`8_440_000+100·vi+r`, v6m.py:252/261). Reps are therefore a factor crossed with source, not nested in it. The bootstrap
(v6m_analysis.py:41–45) treats them as nested: it draws reps independently per instance, and draws DATA reps independently of B1
reps. Strictly, this breaks the pairing.

**Does the pairing matter? Empirically, very little.** The correlation of DATA rep means with B1-mean rep means is −0.38 (main) and
+0.59 (rep), i.e. weak and of inconsistent sign. A crossed bootstrap (instances plus shared reps) gives REF
[−22.1; −17.5] against the original [−21.8; −17.9], and similar shifts elsewhere (`rtb_recompute_stdout.txt`). The one exception
is E3_MPOIS: the crossed CI is [−11.7; −8.0] against the original [−13.7; −6.4], because its Bernoulli RNG is shared per rep. The
original scheme is conservative there.

**B1 instances add almost no independent information.**

| variance component, REF | main | rep |
|---|---|---|
| between-instance SD | 0.94 Hz | 0.00 Hz |
| residual SD | 2.47 Hz | 2.54 Hz |
| MS_inst / MS_resid | 2.17 | 0.58 |

The rep set shows zero instance variance. The precision of the gap is dominated by the single DATA network's 8 reps: DATA rep
SD 2.68, so SE ≈ 0.95 Hz, against a total bootstrap SE of 1.01 Hz. REPORT.md:37 ("units: 10 independent B1 networks + 1 DATA
network") overstates the independent sample. In practice the effective n is ≈ 8 noise seeds, and every CI is conditional on one
DATA network. REPORT.md:128 says this only in part.

**Small-sample under-coverage.** Percentile bootstrap over n = 8 reps is too narrow: the bootstrap SE is shrunk by √(7/8) and uses
z instead of t₇. The paired per-rep gap (unit = shared seed, n = 8) gives the following:

| condition | t₇ 95 % CI | bootstrap CI |
|---|---|---|
| REF (main) | −19.9 ± 2.74 | ± ≈2.0 |
| E1c_t0 (main) | −15.6 ± 5.86 | [−19.9; −11.8] |

A leave-one-rep-out jackknife-t on F (`rtb_supp_stdout.txt`):
- E1c_DN_t0 main: F +0.21 [−0.01; +0.44]. It now includes 0, so the main-set label "contributes" is not robust.
- E1_DN_t0 main: F +0.25 [−0.00; +0.50], the same problem.
- Replication: E1c +0.33 [+0.19; +0.47] and MCIRC +0.23 [+0.09; +0.38] stay robust.
- Other labels that flip: E2b_MID_b10 (99.8 % interval [−0.03; +0.18]).

**Levels and sides.** These are correctly averaged within a rep and never treated as independent units. They share the noise seed, so
they are not independent anyway.

## 3. Is F = 1 − gap/gap_ref well-behaved?
**Pooled: yes.**
- REF / E3_M0 denominator: bootstrap CV 5.1 % (main and rep); the least negative draw was −16.3 (main).
- E1_DN_t0 as the E5a denominator: CV 15 %; the least negative draw was −7.5, so it never comes near 0.
- The percentile CI of the ratio is acceptable here.

**Per level: no.** At 7 mV the REF gap is −8.7 Hz with per-rep values from +0.1 to −17.4 (SE 2.24). F CIs at 7 mV are therefore
uninformative:

| condition at 7 mV | F (95 % CI) |
|---|---|
| E1c_t0 | +0.14 [−0.51; +0.91] |
| E5a | −0.12 [−0.60; +1.65] |

Some bootstrap draws hit a zero denominator (a divide-by-zero warning in my run; counts/0.5 are discrete). Any per-level F reported
at 7 mV needs a Fieller-type interval, or should not be reported.

## 4. Absolute vs relative gap: changes several stated conclusions
The protocol makes the absolute gap primary (§5), and the rule outputs in §3 of the report are correct for it. But the report's
interpretation (§4) states mechanistic conclusions that only hold in absolute Hz. The relative F below is
1 − relgap/relgap_ref, with a crossed bootstrap (and jackknife-t in brackets):

| condition | F_abs (main / rep) | F_rel main [CI] | F_rel rep [CI] | Consequence |
|---|---|---|---|---|
| E1c_DN_t0 | +0.21 / +0.33 | **+0.59 [+0.50; +0.68]** (jk-t [+0.48; +0.70]) | **+0.65 [+0.59; +0.71]** | Under the pre-registered rule applied to the secondary metric, this is "removes most" in BOTH sets |
| E1_DN_t0 | +0.25 / +0.35 | +0.61 [+0.51; +0.71] | +0.66 [+0.60; +0.73] | same |
| E1_DN_t1 / t2 / t4 / t6 | −0.16 / −0.11 / +0.11 / +0.27 | +0.20 / +0.06 / −0.03 / −0.05 | — | In relative terms the t_ref dose–response IS monotone (−0.090, −0.184, −0.217, −0.230, −0.236, −0.241 for t_ref 0, 1, 2, 2.2, 4, 6). The "not monotone" claim (REPORT.md:92–93) is an absolute-Hz artefact of the rate change |
| E2a_DN_b00 | −0.15 / −0.21 | +0.04 [+0.01; +0.08] | +0.00 [−0.05; +0.06] | "DNa02 adaptation REDUCES the gap" (REPORT.md:97) is rate scaling: the relative gap is unchanged |
| E2b_MID_b00 | +0.02 / −0.03 | **+0.22 [+0.17; +0.28]** | **+0.19 [+0.15; +0.23]** | "Intermediate adaptation has no measurable effect" (REPORT.md:98) is false in relative terms (contributes, both sets) |
| E3_MCIRC | +0.36 / +0.23 | +0.47 [+0.42; +0.53] | +0.38 [+0.29; +0.47] | The "residual 64–77 %" becomes ≈ 53–62 % |
| E5a (vs E1_t0) | +0.01 / +0.01 | +0.17 [+0.08; +0.29] | +0.17 [+0.07; +0.28] | "not supported" becomes "contributes" (relative) |
| E1b_MID_t0 | −0.37 | −0.26 [−0.30; −0.22] | — | unchanged (enlarges) |
| LCIRC | +0.94 / +0.80 | +0.95 / +0.84 | — | unchanged |

E4 relative slope (slope ÷ DN at p = 0), from `rtb_recompute_stdout.txt`:
- DN_t0/REF ratio: 0.51 [0.41; 0.60], against 0.75 [0.60; 0.89] absolute.
- DN_b0/REF ratio: 0.96 [0.94; 0.99], against 1.22 absolute. The "×1.2 steeper" claim is also rate scaling.

Under the relative metric, H1 would still fail the conjunction rule, but only because the E4 upper bound is 0.60 (> 0.5).
"H1 NOT supported as the primary cause" (REPORT.md:91) must therefore be stated as metric-dependent. On the absolute metric, DNa02
refractoriness explains 21–33 %. On the relative metric it explains ≈ 60–65 % of the proportional deficit in both sets and halves
the synchrony slope.

## 5. New simulation (own seeds): the "timing route survives DNa02 t_ref 0" claim is falsified
REPORT.md:111–112 attributes stage (ii) to a DNa02-level timing loss that "survives DNa02 t_ref 0". This was inferred from single
factors (E1c_t0 residual −15.6 Hz). The decisive cell, intermediate circular shift with DN t_ref 0, was never run.

I ran it: intermediates clamped to their REF trains (identity, M0) or circularly shifted (MC), each with DN t_ref 2.2 or 0. The
inputs were DATA + B1 8 421 001–010, 7/8/9 mV, L/R, new noise seeds 8 498 111–118. Checks: identity clamp == REF in every run, and
circular-shift counts preserved. The new seeds reproduce the main effects: M0 gap −18.4 [−21.0; −16.4], timing F at REF +0.27,
t0 F_abs +0.18 / F_rel +0.58.

| intermediates | DN t_ref 2.2: gap (rel) | DN t_ref 0: gap (rel) |
|---|---|---|
| timing intact (M0 / T0) | −18.4 (−0.217) | −15.1 (−0.092) |
| circularly shifted (MC / MCT0) | −13.4 (−0.126) | **−21.2 (−0.142)** |

- At DN t_ref 0, destroying the intermediate timing ENLARGES the gap: F_abs −0.40 [−0.93; −0.02], F_rel −0.55 [−1.07; −0.16].
- Interaction (timing effect at REF minus timing effect at t0): +11.1 Hz [+7.5; +14.7].
- By level: 7 mV +3.7 [−0.8; +8.4]; 8 mV +15.4 [+11.3; +19.7]; 9 mV +14.4 [+9.2; +19.9].

So in this model, synchronous intermediate input lowers DNa02 output relative to time-shifted input ONLY when DNa02 has a refractory
period. Without refractoriness, synchrony is neutral to beneficial. The residual E1c_t0 gap is the count route, not a timing route.

This is an interaction (H4), which the single-factor design could not detect. It undercuts both the "neither of which is DNa02
refractoriness" sentence (REPORT.md:109–112) and the leak candidate. Caveats: it is exploratory, it combines two factors (which
the protocol avoided by design), and it uses one extra noise sample.

The Exp 6 numbers fit this reading:
- DATA-vs-B1 excitatory drive deficit: −10.4 % at both REF and DN t0.
- DN relative gap: −23 % at REF, but −9 % (E1_t0) / −9.5 % (E1c_t0) at t0, about equal to the drive deficit.
- MCIRC at REF gives −12 %.

## 6. Per-level heterogeneity (crossed bootstrap within level; `rtb_recompute_stdout.txt`)
The level-averaged F is weighted towards levels with a large gap (main gaps: 7 mV −8.7, 8 mV −21.2, 9 mV −29.8; rep: −9.2, −25.4,
−21.8). The main and rep sets also disagree on which level carries the largest gap.

- **Absolute H1 rejection holds at every level.** No level reaches F ≥ 0.5:
  - E1c_t0 main: 7 mV +0.14 [−0.51; +0.91] (not supported), 8 mV +0.20 [+0.01; +0.45], 9 mV +0.24 [+0.12; +0.39];
  - rep: +0.25 (n.s.), +0.30, +0.40;
  - relative F is 0.57–0.67 at every level in both sets, i.e. homogeneous.
- **E3_MCIRC is NOT homogeneous.**
  - main: 7 mV +0.32 [−0.06; +0.68], **8 mV +0.14 [−0.06; +0.29] (not supported)**, **9 mV +0.52 [+0.41; +0.64]** (point estimate
    meets "removes most");
  - rep: +0.06, +0.12 (n.s.), +0.44;
  - the pooled "contributes 23–36 %" is carried by 9 mV, and the effect is null at 8 mV in both sets.
- **E2b_MID_b00 changes sign across levels, and this replicates.**
  - main: −0.18 / −0.20 (enlarges, CI excl. 0 at 8 mV) / +0.23 (contributes);
  - rep: −0.03 / −0.23 / +0.21;
  - "F ≈ 0, no measurable effect" is a cancellation of opposite-signed effects, not an absence of effect.
- **E2a_DN_b00** is −0.23 / −0.25 / −0.05 (9 mV n.s.).
- **E4 DN_t0 slope by level**:
  - 7 mV: +0.12 Hz/Fano. The synchrony effect is abolished: DN_t0 64.8 → 75.1 Hz while REF falls 52.2 → 33.1.
  - 8 mV: ratio 0.76 (rel 0.54).
  - 9 mV: ratio 1.23, steeper than REF (rel 0.77).
  - So the pooled ratio 0.59–0.90 averages a full flattening at 7 mV and no flattening at 9 mV.
- **"DNa02 falls monotonically with alignment under every dynamics" (REPORT.md:72)** holds only for the level-pooled means
  (v6m_analysis.py:114–115). Per level it fails:
  - L0 REF 52.2 → 54.6 (p 0 → 0.1);
  - L2 REF 108.4 → 114.4 (p 0.7 → 0.9);
  - L0 DN_t0 is non-monotone and increasing.

## 7. Exp 4 slope analysis and the "~85 %" claim
- **Slope point values and CIs reproduce:** REF −0.908; DN_t0/REF ratio [0.595; 0.892]. Resampling x jointly with y changes
  nothing ([0.593; 0.888]), and neither does a cell-level bootstrap ([0.567; 0.916]).
- **The linear model is mis-specified.** All curves are convex: the quadratic coefficient is positive for every dynamics, and R²
  is 0.92–0.98. The OLS slope therefore depends on the range. Over the range that actually spans DATA → B1 (p 0.35–0.9), the
  slopes are REF −0.706 and DN_t0 −0.616, i.e. absolute ratio 0.87 (relative 0.54). The pre-registered "upper < 0.5" criterion is
  thus also range-dependent.
- **n = 8 reps, percentile bootstrap:** the interval is too narrow (same issue as §2). The x-positions are grid means, while the
  Fano10 SD within a grid point is 4–10 units at p ≥ 0.35.
- **The "~85 %" figure is robust in size but has no CI, and the curve location is metric-specific.**
  - Linear interpolation of the REF synthetic curve at the real synchrony values gives the following share of the real −19.9 Hz
    gap:

    | metric | share of real gap |
    |---|---|
    | Fano10 | 91 % (−18.1 Hz) |
    | Fano5 | 92 % |
    | χ² | 92 % |
    | pairwise r | 93 % |
    | volley | 90 % |
    | CV5 | 89 % |
    | Fano20 | 80 % (B1 lies outside the grid range, extrapolation clamped) |

    The report's −17.5 / ~85 % comes from nearest grid points, not from interpolation. "≈ 80–93 % depending on metric" is the
    honest statement.
  - "The real trains fall on the REF curve" (REPORT.md:75) holds for Fano10 and Fano5 only:
    - χ² places DATA at 92.5 Hz (real 86.5) and B1 at 74.2 Hz (real 66.6);
    - volley places DATA at 100.9 Hz (real 86.5) and B1 at 83.0 Hz (real 66.6).
  - "B1 counts differ by < 1 %": true for main (−0.28 %), but −1.12 % in the rep set.

## 8. Multiplicity and decision rules
- **Number of intervals.** Main has 24 F intervals and rep has 9, plus 12 E4 ratio intervals × metrics, plus Exp 6. All are at
  95 % with no adjustment, and with n = 8 percentile bootstrap. Labels that are not robust to a 99.8 % (≈ Bonferroni 25) interval
  or to the jackknife-t interval:
  - E1c_DN_t0 main [−0.05; +0.52];
  - E1_DN_t0 main [−0.04; +0.59];
  - E2b_MID_b10 [−0.03; +0.18].
- **Robust labels:** LCIRC "removes most" (both sets), E1b_MID_t0, E2a, E3_MCIRC, E3_MJ20, E3_MPOIS, E1_DN_t6 and E1c_DN_t6, and
  the replication-set labels.
- **The H1 conjunction rule** (v6m_analysis.py:154–155) is coded as pre-registered. It fails on two of its three legs (absolute
  metric), so "not supported" is the correct rule output.
- **The rule does not record the relative metric.** The relative CIs are computed (v6m_analysis.py:52) but no label is attached to
  them. The report should show the secondary-metric rule outcome next to the primary one, because the two disagree for H1 (Exp 1c
  leg), H2a, H2b and E5a.
- **"E1 ≈ E1c → feedback irrelevant" (REPORT.md:94)** is supported by the paired difference E1 − E1c gap: +0.65 ± 0.88 Hz main and
  +0.42 ± 1.12 Hz rep (t₇). This CI should be quoted instead of "≈".
- **E3_M0 label** reads "not supported (CI includes 0)" with F ≡ 0 and CI [0, 0] (v6m_analysis.py:17–22). This is cosmetic: it
  should read "identity".

## 9. Verdict: **NOT_READY**
The numbers are correct and reproducible, the rule outputs are faithful to the protocol, and the LCIRC reference effect is robust.
Three things block sign-off of the interpretation in §4:
1. A new simulation inside my seed range contradicts the report's central mechanistic sentence (timing route survives DN t_ref 0).
   It shows a strong, replicated-in-sign interaction: DNa02 refractoriness × intermediate synchrony, +11 Hz [+7.5; +14.7].
2. Several stated conclusions flip under the pre-specified secondary (relative) metric.
3. Key pooled F values hide level-specific or sign-changing effects.

## Required corrections to REPORT.md
1. Make §4 H1 metric-explicit. State that E1c_t0 F_rel = +0.59 [+0.50; +0.68] main and +0.65 [+0.59; +0.71] rep. This meets the
   "removes most" rule on the secondary metric. Add that the E4 relative slope ratio is 0.51 [0.41; 0.60]. Replace "NOT supported
   as the primary cause" with "absolute-gap rule not met; on the relative gap DNa02 refractoriness accounts for ≈ 60 %;
   metric-dependent".
2. Correct the "t_ref dose–response is not monotone" claim (REPORT.md:92–93). The relative gap is monotone in t_ref (−0.090 at
   t_ref 0 to −0.241 at 6 ms); the non-monotonicity is an absolute-Hz rate effect.
3. H2 (REPORT.md:97–99):
   - "DNa02 adaptation REDUCES the gap … steepens slope ×1.2" is rate scaling (F_rel +0.04 / +0.00; relative slope ratio 0.96).
     Restate as "no proportional effect".
   - "Intermediate adaptation has no measurable effect" is wrong on the relative metric (F_rel +0.22 / +0.19, CI excl. 0). It also
     hides a replicated sign change across levels (7/8 mV enlarge, 9 mV contributes).
4. Remove or qualify "timing route; survives DNa02 t_ref 0" (REPORT.md:111–112) and the "neither of which is DNa02 refractoriness"
   framing. Report the RT-B interaction result (§5 above): at DN t_ref 0, intermediate circular shift enlarges the gap; the
   interaction is +11.1 Hz [+7.5; +14.7]. The best-supported account must include a DNa02-refractoriness × input-synchrony
   interaction (H4).
5. Report per-level F for E1c_t0, E3_MCIRC, E2a and E2b, and E4 slopes per level. State that:
   - MCIRC is null at 8 mV in both sets and carried by 9 mV;
   - E4 DN_t0 abolishes the synchrony effect at 7 mV but not at 9 mV;
   - monotonicity in E4 holds only for level-pooled means (fix REPORT.md:72).
6. Fix the unit statement (REPORT.md:37). B1 instance variance is ≈ 0 (rep: MS ratio 0.58), so the precision is set by 8 noise seeds
   of one DATA network. Reps are crossed with source by common random numbers (v6m.py:239/265), not nested. The bootstrap
   (v6m_analysis.py:41–45) ignores this. The effect is small here, except for MPOIS, where the CI is too wide.
7. Add a small-sample caveat. With n = 8 the percentile intervals under-cover. Under jackknife-t, the main-set E1c_t0 and E1_t0 F
   intervals include 0, so the "contributes" label rests on the replication set. Either report t-based or BCa intervals, or flag
   the labels as fragile.
8. Replace "~85 %" with an interpolated value and a range across metrics (≈ 80–93 %; Fano10 91 %). Restrict "real trains fall on
   the REF curve" to Fano5/10; under χ², pairwise r and volley the real trains lie 6–18 Hz below the curve. Correct "B1 counts
   differ by < 1 %" for the rep set (−1.1 %).
9. State that the E4 OLS slope is range-dependent (convex curves): over the DATA–B1 range p 0.35–0.9 the DN_t0/REF ratio is 0.87
   absolute and 0.54 relative. The "CI upper < 0.5" leg of H1 is therefore sensitive to the grid range.
10. Multiplicity: state that about 45 intervals were made with no adjustment. List which labels survive a 99.8 % interval. Do not
    report per-level F at 7 mV without a Fieller-type interval: its denominator SE is 2.2 Hz on an 8.7 Hz gap, and some draws hit a
    zero denominator.
11. Quote the E1 − E1c paired difference CI (+0.65 ± 0.88 Hz; rep +0.42 ± 1.12) instead of "E1 ≈ E1c".
12. In §6 (Limitations), add: single factors cannot detect interactions, and the one interaction tested (by RT-B) is large.
    Contributions quoted as F are conditional on the absolute metric and on level weighting (the gap grows with level, so the
    pooled F is dominated by 8–9 mV).
