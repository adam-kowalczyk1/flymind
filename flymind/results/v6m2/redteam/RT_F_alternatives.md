# RT-F: V6m2 red team, alternative explanations (2026-10-30)

**Target:** the REPORT.md §3 reading: "a refractory block of ≥ 1 step in DNa02 is what turns synchronous intermediate input into a
disadvantage ... without it the sign reverses (coincidence summation) ... per-volley cap: input arriving during the block is
discarded". Also the T1 claim and the "80 % is not the refractory share" framing.

**Verdict: PASS_WITH_LIMITATIONS.** The core claim survived every attack: in this model a DNa02 spike block makes B1's synchronous
intermediate input cost spikes, and this holds on fresh seeds, with a second surrogate, at 7 DN operating points and at 3 synaptic
time constants. Three other parts did not survive:
- the claim that without the block synchrony *helps*;
- the 81 % figure;
- J025 as a "rate-matched" arm.

Those statements must be corrected (§5). One factual error was found (J025, §3c).

## 1. What I ran (post hoc, exploratory, MODEL level)
`RT_F/rtf_alt.py`, `RT_F/rtf_analysis.py`, `RT_F/rtf_raw.npz`, `RT_F/rtf_aux.json`, `RT_F/rtf_analysis.json`,
`RT_F/rtf_analysis_stdout.txt`.

**Set-up.** MAIN arm (J0 0.2, b_a 0.5). Sources: DATA plus B1 8 421 001–003 (reused networks). Levels 7/8/9 mV, sides L/R, 4 noise
reps 8 498 601–604. Manipulation seeds: SeedSequence bases 8 498 650 (MASYNC) and 8 498 660 (MTHIN).

**Stage 1.** Uses `v6m2.run` unchanged: a free source run, then the REF replay that produces the intermediate trains.

**Stage 2.** A DNa02-only re-simulation. With LC10a and all 147 intermediates clamped, and no DN→DN weights (`W[dn,dn] = 0`, asserted),
the ipsi DNa02 sees only `W[d,:]·S(t−2) + noise`. Two checks passed:
- REF × M0 equals the REF replay raster bit for bit in all 96 cells.
- T0B(−38) × M0 equals `v6m2.run` on a spot-check cell.

**New input: MTHIN.** For each paired cell (B1 k vs DATA, same level, side and rep), both intermediate trains are thinned at random,
per neuron, to min(n_DATA, n_B1) in 300–1000 ms. The per-neuron counts are then identical (asserted) and each train keeps its own
spike timing. gap(MTHIN) is a pure timing contrast that does not depend on MASYNC.

**Statistics.** CI = jackknife-t over the 4 reps (t₃ = 3.18), averaged over the 3 B1 instances, levels and sides. With n = 4 the CIs
are wide. ~40 conditions, no multiplicity correction. CPU: 1 063 s user + 111 s sys, under the 20 min limit.

**Replication of the main result** (independent seeds):

| | V6m2 MAIN | RT-F |
|---|---|---|
| Δt(REF) | +8.1 | **+6.1 (+0.9; +11.3)** |
| Δt(T0) | −7.2 | −8.7 (−16.9; −0.6) |
| I(T0) | +15.4 | +14.9 (+4.6; +25.1) |
| I(T0, bias −38) | +21.2 | +17.0 (+8.7; +25.3) |
| gap REF·M0 | −20.7 | −23.8 |

## 2. Results table (Hz; DATA/B1 = M0 rates; Δt = gap(MASYNC) − gap(M0); THIN = B1_thin − DATA_thin; I = Δt(REF) − Δt(cond); F = 1 − gap_M0/gap_M0(REF))
| DN variant | DATA / B1 | gap M0 | Δt (MASYNC) | gap THIN (equal counts) | I vs REF | F |
|---|---|---|---|---|---|---|
| REF (3 blocked steps, clamp, hard) | 88.0 / 64.2 | −23.8 | **+6.1 (+0.9; +11.3)** | **−13.5 (−21.2; −5.9)** | — | — |
| T0 (hard) | 168.2 / 144.7 | −23.5 | −8.7 (−16.9; −0.6) | +6.1 (−3.5; +15.8) | +14.9 (+4.6; +25.1) | +0.01 |
| T0_SUB (subtractive reset) | 200.8 / 174.6 | −26.3 | −8.8 (−17.3; −0.3) | +10.8 (+2.0; +19.6) | +14.9 | −0.11 |
| T0_SUBM (subtr. + several spikes/step) | 201.0 / 178.5 | −22.5 | −12.9 (−21.5; −4.3) | +14.7 (+6.5; +22.8) | +19.0 | +0.05 |
| BLK3_INT (3-step block, v integrates during block, hard) | 110.5 / 76.1 | −34.4 | +8.9 (+2.9; +14.9) | −23.4 (−35.0; −11.9) | −2.8 | −0.45 |
| BLK3_INT_SUB (pure cap: block, integrate, subtractive, charge kept) | 138.2 / 109.6 | −28.7 | +0.6 (−9.1; +10.4) | **−14.1 (−23.8; −4.5)** | +5.5 (−5.8; +16.7) | −0.21 |
| T1 | 127.3 / 98.5 | −28.8 | +3.9 (−1.0; +8.8) | −10.0 (−19.2; −0.8) | +2.2 (−3.2; +7.6) | −0.21 |
| T0 bias −10 / −20 / −30 / **−38** / −50 | 148 / 128 / 108 / **94** / 72 (DATA) | −19 / −15 / −11 / **−9.3** / −4.9 | −12.0 / −14.7 / −14.3 / **−10.9** / −9.4 (all CI < 0) | +9.7 / +13.8 / +17.1 / **+18.6** / +20.1 | +18 / +21 / +20 / **+17.0 (+8.7; +25.3)** / +15.5 | +0.19 / .37 / .54 / **.61** / .80 |
| **T0 gain 0.60** (×(g+noise); closest to REF rate on grid) | 104.7 / 86.0 | −18.6 | **−1.3 (−6.7; +4.1)** | **−0.2 (−4.0; +3.5)** | **+7.4 (−1.3; +16.1)** | **+0.22** |
| T0 gain 0.70 / 0.80 / 0.90 | 121 / 136 / 152 (DATA) | −21 / −21 / −20 | −1.8 / −5.0 / −9.8 | −0.4 / +3.0 / +5.6 | +7.9 / +11.1 / +15.9 | ≈ 0.1–0.2 |
| REF bias −10 / +10 / +20 | 78 / 99 / 115 (DATA) | −22 / −25 / −21 | +2.5 (−3.1; +8.1) / +10.0 / +7.8 | −10.5 / −16.2 / −13.6 | | |
| REF gain 0.9 / 1.1 / 1.2 / 1.3 | 84 / 92 / 97 / 100 | −23 … −28 | +5.5 / +7.9 / +8.9 / +9.2 (all CI > 0) | −12.1 … −17.2 | | |
| REF τ_syn 2 / 10 (DN only, PSC charge normalised) | 84 / 94 | −24 / −23 | +8.5 (+5.8; +11.2) / +4.4 (+0.2; +8.6) | −14.9 / −11.7 | −2.4 / +1.7 | |
| T0 τ_syn 2 / 10 | 164 / 165 | −29 / −29 | **−0.5 (−8.6; +7.7)** / −4.1 (−11.3; +3.2) | −2.6 / −2.2 | +6.6 (−2.3; +15.5) / +10.2 (+2.4; +17.9) | −0.23 / −0.23 |

DN ISI counts (M0, ISI = 1/2/3/4/5 ms, summed over 24 cells; DATA vs B1 8 421 001):

| Variant | DATA | B1 |
|---|---|---|
| T0 | 429/964/266/93/39 | **908**/512/111/32/18 |
| T1 | 0/291/700/190/88 | 0/551/347/85/34 |
| REF | 0/0/0/188/445 | 0/0/0/305/219 |

Intermediate counts (300–1000 ms, paired cells):
- B1 has 12.8 % fewer spikes than DATA.
- Per (cell, neuron): 78 % have equal counts (74 % are silent in both), 16 % have fewer for B1, 6 % have more.
- The top 10 neurons carry 46 % of the count difference. No neuron is near the 175-spike ceiling (max 150 / 137).

## 3. Alternatives tested

**(a) Hard reset vs refractory block: not the explanation.**
- At t_ref 0, swapping the hard reset for a subtractive one leaves Δt unchanged (−8.7 → −8.8). Discarding supra-threshold charge at
  reset does not, on its own, make synchrony harmful.
- Clamping v during the block is not needed either. With the block kept and v free to integrate during it (BLK3_INT), Δt is +8.9
  (REF +6.1) and THIN is −23.4.
- Pure cap with no charge loss (BLK3_INT_SUB): the two surrogates disagree.
  - MASYNC: Δt +0.6 (−9.1; +10.4), i.e. the effect vanishes.
  - MTHIN: −14.1 (−23.8; −4.5), the same as REF.
- I therefore cannot settle "cap" vs "cap × charge discarding" with MASYNC. The surrogate-free MTHIN contrast favours the cap itself
  (H-RS).
- The report's mechanistic sentence "input arriving during the block is discarded" is also literally inaccurate. Only the *membrane*
  integration is overwritten during the block. The synaptic current g keeps decaying with τ_syn and is delivered after the block.
  Consistent with this, Δt(REF) falls as DN τ_syn grows: +8.5 / +6.1 / +4.4 for τ 2 / 5 / 10.

**(b) dt = 1 ms, one spike per step.**
- Removing the per-step cap at t_ref 0 (T0_SUBM) makes the synchrony benefit stronger, not weaker (agrees with RT-D variant C).
- But the "benefit" at T0 is carried by **1-ms doublets**: B1 has 908 ISI-1 events vs 429 for DATA, i.e. instantaneous 1000 Hz. T1
  only forbids ISI = 1 ms, and Δt turns positive.
- So the T0/T1 contrast is "consecutive-step spikes allowed or not" at the integration time step. "≥ 1 blocked step (≥ 1 ms)" is a
  statement at the dt resolution. Sub-ms dead times were not tested and cannot be tested at dt = 1 ms.

**(c) The T0B bias changes the regime; rate matching depends on the method. This is the main new finding.**
- The pre-registered T0B adds −38 mV, 5.4 × the 7 mV reset-to-threshold distance. The resting equilibrium then lies far below
  v_reset, so the hard reset becomes *depolarising* relative to rest. DN turns into a fluctuation/coincidence detector: MASYNC halves
  DATA's output (90.7 → 47.4 Hz in V6m2).
- With every additive bias from −10 to −50 mV, Δt at t_ref 0 is −9 to −15, so the result is robust *within* the additive method.
- Rate-matching with a **multiplicative gain** on DN input instead (synaptic current and noise × g, same idea as weaker synapses)
  gives a different answer:
  - Δt(T0) moves monotonically toward 0 as gain falls: −8.7 (g 1.0) → −5.0 (0.80) → −1.3 (0.60).
  - MTHIN at g 0.60 is −0.2 (−4.0; +3.5).
  - At gain-matched rates, then, synchrony is **neutral** at t_ref 0, not beneficial.
  - The interaction shrinks to +7.4 (−1.3; +16.1), with a CI that includes 0 at n = 4.
  - The gain grid stopped at 0.60 (104.7 Hz vs REF 88); the trend suggests Δt ≈ 0 at the exact match.
- In REF, lowering DN drive also shrinks the harm: Δt +2.5 (−3.1; +8.1) at bias −10, against +5.5…+10 elsewhere. Δt(REF) is itself
  operating-point dependent, though positive at all 7 points.
- **Factual error (J025).** J025's calibration hit the grid edge. bias_calibration.json gives T0(−60) = 169.5 Hz vs REF 110.9, and the
  main run gives T0B DATA 169.8 vs REF 103.6. **J025's T0B is not rate-matched (+64 %).** The report's "calibrated ... so DATA's DNa02
  rate matches REF" is false for J025.
- In J025, Δt(REF) is also not significant (+6.2, CI −0.9; +13.3) and Δt(T0B) is n.s. (−16.2, CI −34.6; +2.3). "Generalises to J025"
  rests only on I, with an unmatched T0B.

**(d) Is "synchrony helps at t_ref 0" a MASYNC count-distribution artefact? Mostly no, but the decomposition depends on the surrogate.**
- MTHIN does not use MASYNC and holds per-neuron counts exactly equal. It gives the same sign as Δt in every no-block variant: T0
  +6.1 (n.s.), T0_SUB +10.8, bias −38 +18.6. With the block it gives the opposite sign: REF −13.5, T1 −10.0.
- The sign pattern is therefore not a MASYNC artefact. Its size in the no-block case is regime-dependent: ≈ 0 under gain matching and
  at τ_syn 2 or 10.
- The count/timing split is **not additive and depends on the surrogate.** Under REF:
  - count-only (gap MASYNC) = −17.7
  - timing-only (gap MTHIN) = −13.5
  - their sum, −31.2, is larger than the full gap of −23.8
- MTHIN puts the timing share at ~57 % of the gap. MASYNC (1 − countshare) puts it at ~26–39 %. The report's "count route ~60–70 % /
  DN refractory penalty ~30–40 %" is a MASYNC-specific number.

**(e) τ_syn at DNa02 (per neuron; PSC charge normalised by 5/τ).**
- The harm half is robust: Δt(REF) is +8.5 / +6.1 / +4.4 for τ 2 / 5 / 10, all CI > 0.
- The benefit half is not: Δt(T0) is −0.5 / −8.7 / −4.1, and at τ 2 the benefit disappears (CI −8.6; +7.7).
- I is +6.6 (n.s.) / +14.9 / +10.2.
- The size of the interaction is therefore specific to τ_syn = 5 ms.

## 4. T1 claim and the 80 % framing
- **T1.** The V6m2 MAIN result is Δt(T1) +6.6 (+1.9; +11.2). On independent seeds I get +3.9 (−1.0; +8.8), which is n.s. BA1 gives
  +0.4 and J025 +2.9 (−9.5; +15.4).
  - "1 blocked step suffices in MAIN" holds in 1 of 4 tests.
  - T1 runs at a different operating point (DATA 126 vs 87 Hz), and Δt(REF) itself varies with the operating point (§3c), so a T1
    vs REF comparison without rate matching is confounded.
  - The robust part is narrower: the jump from T0 to T1 forbids 1-ms doublets, and 3 vs 6 steps make no difference.
- **80 %.** F(T0B) is a property of the additive-bias regime:
  - V6m2: 81 %
  - RT-F, bias −38: 61 %
  - RT-F, gain 0.60: **22 % (5–39 %)**
  - RT-F, T0 unmatched: 1 %
  - J025: not rate-matched
- The report correctly says "the 80 % is NOT the refractory share". It still quotes 81 % as "removed by rate-matched DNa02 t_ref 0"
  in §2 and §3 as though it were a property of DNa02. It is not.
- The report also mixes three refractory-attributable shares without reconciling them:
  - Δt(REF)/gap = 39 %
  - I/gap = 74 % (T0) or 102 % (T0B)
  - F = 81 %

## 5. Required corrections to REPORT.md
1. §1/§2: state that J025's T0B is **not rate-matched**. The calibration hit the −60 mV grid edge: T0B DATA 169.8 Hz vs REF 103.6.
   Label J025's I(T0B) and F(T0B) as "unmatched". Note that in J025 Δt(REF) and Δt(T0B) are both n.s., so "generalises" rests on I
   alone.
2. §3 bullet 1: replace "without it ... the sign reverses (synchronous input is then more effective — coincidence summation)" with:
   "without the block, synchrony is neutral to beneficial depending on the operating-point manipulation:
   - beneficial with an additive bias or with no rate matching;
   - ≈ neutral with multiplicative gain rate-matching (RT-F: Δt −1.3, I +7.4 n.s.) and at DN τ_syn 2 ms."
   Keep the robust half: "with the block, B1's synchronous input is harmful (positive at 7 operating points, 3 τ_syn, and with a
   count-matched surrogate)".
3. §2/§3: give the 81 % (F T0B) as specific to the additive-bias control (−38 mV, 5.4 × the threshold gap, which moves DN into a
   fluctuation-driven regime) and add the gain-matched value (~22 %, RT-F, post hoc). Do not call it "removed by DNa02
   refractoriness" without this qualifier.
4. §3 bullet 2: drop or qualify "count route ~60–70 % / refractory penalty ~30–40 %". These are MASYNC-specific. A count-matched
   timing-only contrast (MTHIN) gives ~57 % timing under REF, and count-only plus timing-only (−31.2) exceeds the full gap (−23.8).
   The routes are not additive.
5. §3 mechanism sentence: replace "input arriving during the block is discarded" with "membrane integration during the block is
   overwritten; synaptic current carries over, decaying with τ_syn (Δt(REF) falls with DN τ_syn: +8.5/+6.1/+4.4 at 2/5/10 ms)". State
   that the hard reset is not required (t_ref 0 subtractive ≈ hard), the clamp is not required (block with free integration: Δt +8.9),
   and that "cap alone vs cap × charge loss" is surrogate-dependent (BLK3_INT_SUB: MASYNC +0.6 n.s., MTHIN −14.1).
6. §2/§3 T1: "1 blocked step suffices in MAIN" → "Δt(T1) > 0 in V6m2 MAIN only (n.s. in BA1, J025 and in RT-F's independent seeds,
   +3.9 (−1.0; +8.8)); T1 is not rate-matched". Add that T0 vs T1 is the contrast "1-ms (= dt) consecutive spikes allowed or not": the
   T0 synchrony benefit is carried by ISI = 1 ms doublets (B1 908 vs DATA 429). "≥ 1 ms" is a statement at dt resolution.
7. §4 Limitations: replace "the bias in T0B moves DNa02 toward fluctuation-driven firing (not neutral; T0 without bias agrees in
   MAIN/BA1)" with: "the result of the no-block condition depends on how rate is matched (additive bias vs gain), and the interaction
   magnitude depends on τ_syn". Add the dt = 1 ms resolution.
8. §6: list RT-F's runs as post hoc, n = 4 reps × 3 B1 instances, wide CIs, gain grid ending at 0.60 (not exactly rate-matched). They
   indicate fragility; they are not a pre-registered refutation.
