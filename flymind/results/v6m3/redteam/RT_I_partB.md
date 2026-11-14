# RT-I — red team of V6m3 Part B (count-swap, statistics) — 2026-10-30

Scope: Part B of `results/v6m3/REPORT.md` (DRAFT), protocol r2. Goal: falsify. Python `.venv/bin/python -I -B` from the repo root;
no existing file modified; outputs only in `results/v6m3/redteam/RT_I/`. New simulations used only seeds 8 499 101–199 (noise 8 499 101–108;
swap RNG roots 8 499 150 / 8 499 160; bootstrap 8 499 190/191). CPU ≈ 19 min total (s2 ≈ 10.7 min, s4 ≈ 7.7 min). The two re-runs that
used original MAIN seeds are verification only (no new randomness drawn from them).
Scratch: `s0_struct.py`, `s1_raw.py`, `s2_swap_sim.py` → `swap_sim.json`, `s3_stats.py` → `s3_stats_stdout.txt`, `s4_stratified.py` →
`stratified.json`, `s5_strat_stats.py` → `s5_stdout.txt`, `s6_paired.py` → `s6_stdout.txt`.
All new simulations here are exploratory red-team checks. They are not pre-registered: 4 B1 instances (8 421 001/004/007/010) × 2 levels × 2 sides × 8 new
noise reps. CIs are jackknife-t over reps (t_7), with a rep-only paired bootstrap shown next to them.

## 1. Reproduction (passes)
- **Raw → analysis.json.** I recomputed every Part B estimate and jackknife-t CI (REF/T0/T0G; C, Tm, gap, interaction, share) from `raw/*.npz`.
  They match `analysis.json` to 1e-9, checked by asserts in `s3_stats.py`.
- **Re-simulation.** With the original seeds and RNG, the MAIN B1 8 421 001 (8 mV, L, rep 0) and 8 421 004 (9 mV, R, rep 5) cells reproduce
  the raw npz bit-exactly for all 4 cells × 3 dynamics.
- **Wiring.** DNa02 gets no LC10a input (W[DNa02, LC10a] = 0) and no DNa02↔DNa02 input. Only the 147 intermediates drive it: L has 61 exc / 4 inh
  partners, R has 82 / 4. Switching the LC10a source between cells therefore cannot leak into DNa02.
- **REPORT §2 Part B table vs analysis.json.** Every cell mean, C, Tm, share, interaction and CI matches after rounding. Also correct: log scale
  (C −0.132, Tm −0.118, share 0.53 (0.47; 0.59)), REP T0/T0G Tm +4.4 / +1.3, routes and added fractions (MAIN 2.75 % / 12.17 %). Exceptions:
  - Decomposition-order line: BB − DB = −14.47, which rounds to **−14.5**, not −14.4. BB − BD = −15.77, which rounds to **−15.8**, not −15.7. The count share with counts
    first is 0.374, which rounds to **0.37**, not 0.38.
  - REP DB added fraction is 2.4 %, not reported. The BD fraction is level-dependent: 14.3 % at 8 mV and 10.0 % at 9 mV (MAIN; REP 14.7 / 9.7).

## 2. Statistics
- **Which CI is binding.** In Part B the jackknife-t is the binding interval for every quantity. The nested bootstrap is 2–3× narrower. Examples for C|REF:
  bootstrap (−12.9; −11.5) vs jackknife-t (−13.8; −10.7); share 0.503–0.554 vs 0.464–0.592.
- **Why the nested bootstrap is too narrow (pseudoreplication).**
  - DD is bit-identical across all 10 B1 instances, because it uses the same DATA source and seed.
  - Instance-to-instance spread is small. The SD of instance means is 0.0–1.4 Hz, against 1.4–3.9 Hz across reps. An instance-only bootstrap
    of the share gives [0.517; 0.538] in MAIN.
  - Resampling reps independently inside each instance therefore treats ~80 units as roughly independent when the real unit is n = 8 reps.
- **The pseudoreplication changes a secondary reading.** Under the bootstrap, T|T0 is +2.75 [+1.06; +4.52] (MAIN) and +4.43 [+1.86; +6.90] (REP).
  Both exclude 0, so the "n.s." in the REPORT holds only because the wider-of rule picked the jackknife. A rep-only paired bootstrap agrees with
  the jackknife-t: T|T0 is [−0.07; +6.55].
- **Effective n.** n = 8 is confirmed as the right unit. The per-rep share is right-skewed: MAIN 0.42–0.73, REP 0.46–0.83 (rep 2).
- **Bonferroni (×40, t_7 quantile 5.20).** The protocol §4 promises this check, but the REPORT does not include it.
  - Survives: C|REF (−15.6; −8.8), Tm|REF (−17.4; −4.4), interaction|REF (−11.0; −3.2), and the same quantities in REP.
  - Share|REF widens to (0.39; 0.67) in MAIN and (0.34; 0.72) in REP.
  - T|T0 and T|T0G stay n.s.
- **Per level / per side.** All per-cell shares, MAIN REF:

  | Cell | share | CI |
  |---|---|---|
  | 8 L | 0.52 | (0.37; 0.66) |
  | 8 R | 0.56 | — |
  | 9 L | 0.55 | — |
  | 9 R | 0.47 | (0.35; 0.59) |

  In REP the range is 0.47–0.60, and 9 R is again the lowest at 0.467. The gap ranges from −18 to −31 Hz by cell, and in MAIN 9 L has a much
  larger C than 9 R (−17.4 vs −9.7). There is no significant heterogeneity in the share. Per instance the share is 0.51–0.54 in MAIN and
  0.44–0.58 in REP.
- **T0/T0G per level (raw).** In MAIN T0G at 8 mV, Tm = −2.9 (−4.8; −1.1), which excludes 0. At 9 mV it is +3.0. So the pooled +0.05 comes
  from opposite signs at the two levels.
- **Protocol deviation (not reported).** Protocol §1 says the swap RNG is SeedSequence([8 446 000, set, level, side, rep, source, neuron-block]).
  The code uses [8 446 000, set, li, si, r, src_id], and DB and BD draw sequentially from one RNG. This does not affect validity, but it should be stated.

## 3. Attack on the count-swap (main finding)
Two independent defects bias the pre-registered estimator toward a larger count share and a larger |interaction|.

**(a) The count window does not match the outcome window.** Counts are matched over 300–1000 ms, but DNa02 is scored over 500–1000 ms.
- B1's spike deficit is relatively larger in 300–500 ms. The swap redistributes spikes with the timing source's time profile, so in the
  scored window:
  - the DNa02-weighted excitatory drive of DB is **2.0 % below** BB (5766 vs 5885);
  - the drive of BD is **1.7 % above** DD (6648 vs 6537).
- Each swapped cell therefore overshoots by ~17–18 % of the DD−BB drive gap (652). Both overshoots inflate |C|.
- Fix tested (U2): the same uniform swap, applied separately in 300–500 and 500–1000. Drives then match exactly.

**(b) Added spikes at uniform random times are asynchronous.**
- Ipsilateral pairwise r (5 ms bins): BB 0.381, BD_U 0.327, BD with spikes drawn from the timing source's own same-side population PSTH
  (CT) 0.358. DD is 0.144.
- So BD_U is ~23 % of the way from B1 synchrony back toward DATA. This raises BD and inflates |C| through the BB − BD term.

**Count share C/(C + Tm), REF, same noise for every construction** (my sims; 4 instances; n = 8 reps):

| Construction | count share (jack-t CI) | Tm [Hz] | interaction [Hz] |
|---|---|---|---|
| U = v6m3 method (my seeds) | 0.530 (0.450; 0.610); re-draw 0.543 | −10.8 | −5.3 |
| CC: added spikes copied from the count source's own times | 0.556 (0.471; 0.641) | −10.1 | −7.8 |
| CT: added spikes from the timing source's population PSTH | 0.492 (0.420; 0.564) | −11.6 | −4.1 |
| MTHIN: both thinned to per-neuron min (300–1000) | 0.431 (0.359; 0.504) | T at matched counts −13.0 | — |
| **U2: uniform, window-stratified** | **0.461 (0.386; 0.536)** | −12.3 | −5.6 |
| **CT2: PSTH addition, window-stratified** | **0.435 (0.375; 0.494)** | −12.9 | −3.7 |
| **MTHIN2: thinning, window-stratified** | **0.361 (0.298; 0.424)** | T at matched counts −14.6 | — |

Paired differences, same noise: share(U) − share(U2) = +0.08 (−0.05; +0.22); share(U) − share(CT2) = +0.11 (−0.01; +0.23);
share(U) − share(MTHIN2) = +0.18 (+0.06; +0.31).

The method reproduces: U on my seeds gives 0.530 against 0.528 in the original. Per cell CT2 (8 L / 8 R / 9 L / 9 R) gives 0.50 / 0.42 / 0.42 / 0.41,
against U 0.68 / 0.58 / 0.53 / 0.39.

**Reading:**
- The pre-registered estimate 0.53 sits at the top of the range across constructions.
- The constructions that remove the two defects give **0.36–0.46**.
- Two of the three stratified constructions (CT2, MTHIN2) have CI upper bound < 0.5. By the pre-registered rule applied to them,
  **timing would be "dominant"**.
- The pre-registered "neither dominant" holds only for the biased estimator.
- "Both routes present" is robust: in every construction C and Tm have CIs that exclude 0.
- About half of the REF interaction (−7.1 → −3.7 Hz) is a swap artefact.
- Additional check, *DNa02 0–300 ms preamble* (adaptation τ_a = 300 ms carries the timing source's 0–300 ms count into the window): with a common
  DATA preamble, the share moves only 0.530 → 0.531 (U) and 0.492 → 0.494 (CT). This effect is negligible.

**T0 / T0G ("timing effect vanishes / is abolished").**
- In the original raw data, Tm ≈ 0 is the average of two opposite-sign path effects. Both CIs exclude 0 in MAIN:
  - T0G: BD − DD = −3.7 (−6.5; −1.0) and BB − DB = +3.8 (+1.3; +6.3);
  - T0: −3.2 and +8.7 (+4.6; +12.8).
- The interaction is as large as the gap: +7.5 for T0G and +11.9 for T0, against gaps of −11.2 and −17.8.
- Across constructions, T0G Tm = +0.2 (U), +2.8 (+0.2; +5.4) (CT), +1.4 (CC), +5.2 (+2.7; +7.6) (MTHIN), −1.7 (−3.4; −0.05) (U2), +0.75 (CT2),
  +2.0 (−0.4; +4.4) (MTHIN2).
- T0 Tm = +3.5 (U), +7.3 (+1.5; +13.1) (CT), +9.8 (+5.5; +14.2) (MTHIN).
- So without the DNa02 block, B1 timing changes from harmful (≈ −11…−15 Hz) to neutral or **beneficial**. Its sign and size depend on the construction.
- The large T0G interaction under U (+8.3) drops to +1.6 under CT2, so it is mostly a swap artefact as well.
- The pre-registered secondary expectation, "Tm ≥ 0 or near 0", is met. "Abolishes the timing effect" and "independent, surrogate-free
  confirmation" are overstatements: BD contains 12 % random (surrogate) spikes.

## 4. Verdict: **PASS_WITH_LIMITATIONS**
What stands:
- the numbers, code and validation reproduce exactly;
- the pre-registered QB outcome under the pre-registered estimator (both routes present; share CI spans 0.5);
- that the DNa02 block carries the timing penalty.

What does not stand: the count share 0.53, "comparable amounts", "plausible range 0.4–0.7" and "abolishes the timing effect". These
are biased or construction-dependent, as shown in §3. No rerun is required. The corrections below are mandatory before the report is final.

## 5. Required corrections to REPORT.md
1. **§2 decomposition-order line.** Correct the rounding: BB − DB = −14.5 (not −14.4), BB − BD = −15.8 (not −15.7), counts-first
   share 0.37 (not 0.38).
2. **§1 / §2: added-spike fractions.** Report the REP DB added fraction (2.4 %) and the level dependence of BD (≈ 14 % at 8 mV, 10 % at 9 mV).
   State that the added fraction is relative to the count source's 300–1000 ms spikes.
3. **New §2 sub-item, count-window mismatch.** Disclose that counts were matched over 300–1000 ms but DNa02 is scored over 500–1000 ms.
   In the scored window DB has 2.0 % less and BD 1.7 % more DNa02-weighted drive than its count source (≈ 18 % of the drive gap each). Both
   inflate |C|. State this as a pre-registered design defect.
4. **Replace "count share 0.53, plausible range 0.4–0.7 given the swap construction"** in §2 and §3. Keep the pre-registered estimate
   0.53 (0.46; 0.59), and add the RT-I construction sensitivity:
   - window-stratified uniform 0.46 (0.39; 0.54);
   - stratified PSTH-addition 0.44 (0.38; 0.49);
   - stratified min-thinning 0.36 (0.30; 0.42).
   Conclude that "the count share is 0.36–0.53 depending on construction; bias-reduced constructions put it below 0.5, and in two of them
   timing is 'dominant' by the pre-registered rule". "Neither dominant" must be qualified as specific to the pre-registered (biased)
   estimator. The Shapley path shares (0.37 / 0.68) are a separate quantity, not bounds on construction bias. Delete "both routes carry the gap in comparable amounts".
5. **Interaction.** State that roughly half of the REF interaction (−7.1 Hz) is attributable to random-time spike addition: it is −3.7 Hz
   under PSTH addition. Report the T0/T0G interactions (+11.9 / +7.5) next to Tm in the text, not only in the table.
6. **§3 QB, "Removing the DNa02 block … abolishes the timing effect".** Replace with: "reduces the timing effect from ≈ −11 Hz to
   within about ±3 Hz (T0G). The sign depends on construction and level: T0G 8 mV −2.9 (−4.8; −1.1), 9 mV +3.0. The pooled ≈ 0 averages
   opposite-sign paths (BD − DD −3.7, BB − DB +3.8, both CI ≠ 0). Under T0, B1 timing becomes beneficial (+3…+10 Hz)." Delete
   "surrogate-free": BD contains ~12 % random-time spikes.
7. **§2 / §4 CIs.** State that in Part B the jackknife-t is binding throughout, and that the nested bootstrap is invalid here
   (pseudoreplication: DD identical across instances, reps resampled independently per instance; 2–3× too narrow). Under the bootstrap
   alone T|T0 would exclude 0 in both sets.
8. **§4: report the Bonferroni check** that protocol §4 promises. C, Tm and the interaction under REF survive ×40. The share widens to
   (0.39; 0.67) in MAIN and (0.34; 0.72) in REP.
9. **§2: per-level / per-side numbers for Part B.** Give the share per (level, side), MAIN 0.47–0.56 and REP 0.47–0.60, and the gap,
   −18 to −31 Hz. Note that 9 mV R is the lowest share in both sets.
10. **§1: disclose the swap-RNG deviation.** The SeedSequence has no source/neuron-block keys, unlike protocol §1, and DB and BD share one stream.
11. **§4 Limitations.** Replace "count-swap adds random spikes (BD 12 %), biasing the split" with the quantified bias above (point 4). Add
    the count-window mismatch (point 3).
