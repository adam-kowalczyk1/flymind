# V6m red team RT-C: does the result depend on one parameter configuration? (2026-10-30)

Reviewer: RT-C, an independent model instance. This is not a human review. Scope: whether the key qualitative V6m conclusions survive
at other ALIF parameter sets. I did not modify any repository file. All new files are under `results/v6m/redteam/RT_C/` plus this
review.

## 1. What I ran
- **Script:** `results/v6m/redteam/RT_C/rtc_run.py`. It calls `v6m.replay`, `v6m.step`, `v6m.summarise`, `v6m.sync_metrics`,
  `v5v43.manipulate`, `v5v43.current`, `v5v41.make_net` and `v5v42.make_block_net` unchanged. The only in-process changes are
  `ALIFParams` overrides and `v6m.BA0`, so that the baseline b_a vector equals the configuration's global b_a. `v6m.vectors`/`v6m.C`
  read `BA0` at call time (v6m.py:41, 86). Without this patch, BA1 replays would silently run at b_a 0.5.
- **Configurations:** the four below are V6 settings with an open-loop DATA > B1 deficit (`results/v6/REPORT.md`, read from
  `results/v6/openloop/<cfg>/` for B1 8 421 001–003). I picked the levels where that open-loop deficit is large and DN is below
  ceiling. This choice was made before any RT-C replay, but after seeing the V6 open-loop curves.
  - **D0:** the V6m set at 8 and 9 mV. It calibrates this reduced design against V6m.
  - **TH8:** v_th −44, gap 8 mV, at 9 and 10 mV.
  - **BA1:** global b_a 1.0, at 9.5 and 10.5 mV.
  - **J025:** J0 0.25, applied to both DATA and B1, at 7.5 and 8 mV.
- **Design:** DATA plus B1 instances 8 421 001–003; 2 levels; L and R; 4 reps. Conditions: REF, LCIRC, E1_DN_t0, E1c_DN_t0, E3_M0,
  E3_MCIRC, E1b_MID_t0 and E2a_DN_b00.
- **Seeds (RT-C range only):**
  - noise 8 498 201–204;
  - LCIRC rng 8 498 210–213;
  - MCIRC rng 8 498 220–223;
  - bootstrap 8 498 230 (absolute F) and 8 498 231 (relative F).
- **CPU:** 570 s user for the simulations (2:08 wall on 8 workers) plus about 1–2 min for the bootstraps, so under 15 min in total.
- **Analysis:**
  - Absolute gaps and F come from `v6m_analysis.gaps`, unchanged: the paired hierarchical bootstrap with 10 000 draws, and F for
    E3_MCIRC taken relative to E3_M0, as in V6m. Script `rtc_analysis.py`, output `rtc_analysis.json` and `analysis_stdout.txt`.
  - F on the relative gap uses the same resampling scheme. Script `rtc_relF.py`, output `relF_stdout.txt`. I also applied it to the
    V6m main raw files, which needed no new simulation.
- **Validation:** all checks passed in all 16 jobs (`run_stdout.txt`).
  - REF replay of the DATA source equals the free DATA run on all non-LC neurons (16/16 per config).
  - The E3_M0 identity clamp equals REF (16/16 per job).
  - LC10a trains are unchanged in the non-LC conditions (112/112).
  - The b_a/t_ref vectors match their intended values (128/128). This includes b_a = 1.0 in every non-ablated BA1 entry.

## 2. Results
DNa02 ipsi, 500–1000 ms, mean of 2 levels × 2 sides. The gap is B1 − DATA in Hz. Abs F is on the absolute gap (the primary metric);
rel F is on gap / DN_DATA (the secondary metric).

| Condition | V6m main (D0, 7–9 mV, 10 B1, 8 reps) | RT-C D0 (8–9) | RT-C TH8 (9–10) | RT-C BA1 (9.5–10.5) | RT-C J025 (7.5–8) |
|---|---|---|---|---|---|
| REF gap [Hz] (rel) | −19.9 (−0.23) | −23.2 (−0.23) | −25.8 (−0.31) | −14.5 (−0.25) | −23.7 (−0.21) |
| REF DN DATA / B1 | 86.5 / 66.6 | 101.2 / 78.0 | 83.8 / 57.9 | 59.1 / 44.6 | 111.8 / 88.1 |
| LCIRC abs F | +0.94 removes most | +0.77 (0.61; 0.96) removes most | +0.95 (0.85; 1.06) removes most | +0.97 (0.77; 1.21) removes most | +0.79 (0.63; 0.97) removes most |
| **E1c DN t_ref 0, abs F** | +0.21 (0.06; 0.37) contributes | +0.13 (−0.03; 0.37) n.s. | +0.14 (0.05; 0.22) contributes | **+0.76 (0.47; 1.08) REMOVES MOST** | **−0.75 (−1.22; −0.18) ENLARGES** |
| E1c DN t_ref 0, rel F | **+0.59 (0.51; 0.67) removes most** | +0.54 (0.45; 0.67) removes most | +0.51 (0.47; 0.57) removes most | +0.86 (0.70; 1.05) removes most | +0.33 (0.17; 0.51) contributes |
| E1c DN DATA / B1 [Hz] | 164.5 / 148.9 | 189.2 / 169.1 | 148.4 / 126.1 | 101.5 / 98.0 | 289.6 / 248.3 |
| E1 (free) vs E1c, abs F | 0.25 vs 0.21 | 0.08 vs 0.13 | 0.15 vs 0.14 | 0.74 vs 0.76 | −0.69 vs −0.75 |
| **E3_MCIRC (vs M0), abs F** | +0.36 (0.28; 0.42) | +0.35 (0.25; 0.48) | +0.28 (0.09; 0.42) | +0.43 (0.22; 0.63) | **+0.50 (0.38; 0.65)** (rule: just below 0.5) |
| E3_MCIRC, rel F | +0.47 (0.42; 0.52) | +0.47 (0.40; 0.57) | +0.42 (0.31; 0.52) | +0.50 (0.33; 0.66) | **+0.64 (0.56; 0.75) removes most** |
| E1b MID t_ref 0, abs F | −0.37 enlarges | −0.34 (−0.47; −0.24) enlarges | −0.12 (−0.16; −0.06) enlarges | **+0.05 (−0.09; 0.21) n.s.** | −0.06 (−0.12; −0.01) enlarges |
| E1b MID t_ref 0, rel F | −0.26 enlarges | −0.24 enlarges | +0.02 n.s. | **+0.15 (0.05; 0.28) contributes** | −0.04 n.s. |
| E2a DN b_a 0, abs F | −0.15 enlarges | −0.19 enlarges | −0.21 enlarges | −0.74 (−0.97; −0.53) enlarges | −0.19 enlarges |
| E2a DN b_a 0, rel F | **+0.04 (0.01; 0.09) contributes (F>0)** | +0.03 n.s. | +0.01 n.s. | −0.22 enlarges | −0.08 enlarges |

**Per-level gaps for E1c DN t_ref 0, compared with REF:**
- BA1: −9.4 vs −14.4 at 9.5 mV, and **+2.3** vs −14.6 at 10.5 mV.
- J025: −61.3 vs −28.7 at 7.5 mV, and −21.3 vs −18.7 at 8 mV.

**Mechanism correlates.** These are the same direction in every configuration:
- B1 has more ISIs ≤ 4 ms under REF (D0 0.40 vs 0.17, TH8 0.41 vs 0.08, BA1 0.49 vs 0.18, J025 0.67 vs 0.60).
- Intermediate Fano10 under REF is higher for B1 (about 20–23 vs 8–12).

**Calibration check.** RT-C D0 reproduces V6m main qualitatively for E1c, MCIRC, E1b and E2a. LCIRC is lower here (0.77 vs 0.94),
at 2 levels and 4 reps. So the differences in the other columns are not an artefact of the reduced design.

## 3. Findings (falsification attempts)
1. **"DNa02 refractoriness is NOT the primary cause" (REPORT.md:91, 109) depends on the parameter set.** It does not survive a
   one-factor change that V6 already treats as a valid regime.
   - At BA1 (global b_a 1.0), E1c DN t_ref 0 with intermediates clamped removes 76 % of the absolute gap (CI 0.47–1.08). That is
     "removes most" under the pre-registered rule (F ≥ 0.5, CI low > 0.25). The free E1 version agrees (0.74).
   - At J025 the same ablation ENLARGES the absolute gap (F −0.75), because DNa02 is driven to about 290 Hz and the absolute gap
     scales with rate.
   - Only D0 and TH8 reproduce the V6m pattern (F 0.13–0.21).
   - So across 4 settings, H1's absolute-gap label is n.s. / contributes / removes most / enlarges. The sign and size of the DNa02
     refractoriness contribution are set by the operating point, not by a fixed mechanism.
2. **Even at the V6m set, the H1 verdict depends on the metric.** On the protocol's secondary metric (relative gap), E1c removes 59 %
   (CI 0.51–0.67) in the V6m main data itself. RT-C D0 gives 54 % and TH8 51 %, both "removes most" on that metric.
   - The protocol makes the absolute gap primary, so the formal label is correct.
   - But the REPORT's prose (REPORT.md:91–94, 109–113) presents "not the primary cause" as a mechanistic conclusion. It mentions the
     relative-gap drop only as a side remark.
   - E1c doubles DNa02's rate (86 → 165 Hz). The absolute-gap F therefore mixes "mechanism removed" with "operating point moved". Both
     metrics need to be shown, and the claim has to be stated per metric.
3. **"Intermediate timing removes only part" (H3, REPORT.md:100) is mostly robust.** Absolute F for E3_MCIRC is 0.28–0.50 in all
   configurations, and never meets the "removes most" rule on the absolute gap. It is borderline at J025, where F ≈ 0.50 with CI low
   0.38 just misses the rule. On the relative gap it "removes most" at J025 (0.64, CI 0.56–0.75). "Only part" holds as "roughly 30–50 %,
   and up to ~2/3 on the relative metric". The "64–77 % residual carried by counts" in REPORT.md:111–112 is specific to the set and
   the metric.
4. **The H5 claim that "intermediate t_ref 0 enlarges the gap" (REPORT.md:104–108) varies widely with the parameter set.**
   - V6m main and D0: −0.34 to −0.37.
   - TH8: −0.12. J025: −0.06.
   - BA1: not significant (+0.05). On the relative metric BA1 is +0.15, meaning the ablation shrinks the gap there.
   - The "two opposite-sign effects of intermediate refractoriness" story may still hold, but the net sign is not stable. It must not
     be presented as a general property.
5. **The H2 wording ("DNa02 adaptation REDUCES the gap … partial compensation", REPORT.md:97) holds only in absolute Hz.**
   - The absolute-gap "enlarges" result for E2a is robust in all 4 configurations.
   - On the relative gap, removing DNa02 adaptation does nothing measurable at D0 and TH8.
   - In V6m main the relative F is +0.04 (0.01; 0.09), meaning the ablation slightly SHRINKS the relative gap.
   - It enlarges the relative gap only at BA1 and J025. "Compensation" is therefore a rate-scaling statement, not a mechanism.
6. **Robust across all tested settings:**
   - LCIRC removes most of the gap (abs F 0.77–0.97), so the effect is carried by LC10a alignment at every setting.
   - E1 ≈ E1c everywhere (|Δ F| ≤ 0.06), so DN→intermediate feedback is negligible.
   - The B1 excess of short DNa02 ISIs is present at every setting.
   - These conclusions can be stated as not depending on the parameter set within the tested range.
7. **The REPORT already concedes the limitation** ("Cannot conclude … that any of this holds at other parameter sets (one set
   tested)", REPORT.md:116; "One parameter set", :128). However, the "Best-supported account" bullet (:109) still states a mechanism
   ("neither of which is DNa02 refractoriness or adaptation") without that qualifier. RT-C now has counter-evidence at BA1, so the
   account has to be weakened, not just flagged.

**Limitations of this review:**
- 3 B1 instances, 4 reps and 2 levels per setting. The bootstrap CIs reflect mostly noise reps, as in V6m.
- Only 4 settings were tested, one factor at a time.
- Levels were chosen from V6 open-loop deficits.
- Exp 4/5/6 were not repeated at the other settings.
- At J025 under t_ref 0, DNa02 runs at about 290 Hz with 97 % of ISIs ≤ 4 ms, an extreme operating point.
- The reviewer is a model instance.

## 4. Verdict: **NOT_READY**
- **Holds:** the V6m numbers are reproducible, the validation holds, and the robust findings in Finding 6 can stand.
- **Must be corrected first:**
  - The headline H1 interpretation (REPORT.md:91, 109) is contradicted at BA1 on the primary metric.
  - The same interpretation flips sign at J025.
  - It reverses on the secondary metric at the V6m set itself.
  - H2/H5 directions are partly specific to the set and the metric.
- **Outlook:** PASS_WITH_LIMITATIONS is reachable once the corrections below are applied. No re-run of V6m is needed.

## 5. Required corrections to REPORT.md
1. **H1 (line 91):** replace "NOT supported as the primary cause" with a statement scoped to the set and the metric. For example: "at
   the V6m set, on the absolute gap, DNa02 refractoriness removes 21 % (rule: contributes); on the relative gap it removes 59 %
   (0.51–0.67, 'removes most'; RT-C); across parameter sets the absolute F ranges from −0.75 (J0 0.25) to +0.76 (b_a 1.0, 'removes
   most') (RT-C) → the role of DNa02 refractoriness is operating-point dependent and not resolved."
2. **Results table:** add a relative-gap F column (with CI) for at least E1c, E1, MCIRC, E1b and E2a. Use the V6m main values from
   RT-C `relF_stdout.txt`, or recompute them in `v6m_analysis.py` as a disclosed post-hoc addition.
3. **"Best-supported account" (line 109):** drop "neither of which is DNa02 refractoriness or adaptation". State the two-stage account
   as holding at the V6m set only, and cite the RT-C BA1 counter-example.
4. **H3 (line 100) and the residual figures (lines 111–112):** describe MCIRC as removing about 30–50 % of the absolute gap at all
   four RT-C settings, and up to 64 % of the relative gap (J0 0.25, "removes most" there). Give the "64–77 % carried by counts"
   residual as set-specific and absolute-metric-specific.
5. **H5 (line 104):** state that the net "intermediate t_ref 0 enlarges the gap" effect is set-dependent (−0.34 D0, −0.12 TH8,
   −0.06 J025, n.s. at BA1, and +0.15 on the relative gap at BA1).
6. **H2 (line 97):** qualify "DNa02 adaptation REDUCES the gap" as an absolute-Hz statement. On the relative gap, removing it gives
   +0.04 (0.01; 0.09) at the V6m set, a slight reduction, and does nothing measurable at TH8/D0. "Partial compensation" is a
   rate-scaling effect and not a separate mechanism.
7. **Robust results:** add a sentence listing the parameter-robust results: LCIRC removes most at all 4 settings; E1 ≈ E1c, so DN
   feedback is negligible; B1 has more short DNa02 ISIs and more synchronous intermediates.
8. **§6 Limitations / "Cannot conclude":** replace "one set tested" with "one set tested in full; RT-C spot-checked 3 further V6
   settings (TH8, BA1, J025; reduced design: 3 B1, 4 reps, 2 levels) — see §8". Also note that any ablation which shifts DNa02's
   rate (t_ref 0, b_a 0) makes the absolute-gap F partly an operating-point effect.
9. **§8 Red team:** cite this review, `results/v6m/redteam/RT_C_parameter_dependence.md`, together with its seeds (8 498 201–204,
   210–213, 220–223, 230, 231) and file list (`RT_C/rtc_run.py`, `rtc_analysis.py`, `rtc_relF.py`, `raw/*.npz` (16),
   `rtc_analysis.json`, `run_stdout.txt`, `analysis_stdout.txt`, `relF_stdout.txt`).
