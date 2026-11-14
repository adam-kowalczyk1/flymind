# V6m red team RT-D — interpretation and alternative explanations (REPORT.md §3–§7)

Reviewer RT-D, 2026-10-30. Read: V6m_PROTOCOL.md (sha b8cd8935… matches `protocol_sha256_before_run.txt`), V6m_ADDENDUM_A1_posthoc.md,
results/v6m/REPORT.md (DRAFT), v6m.py, test_v6m.py, v6m_analysis.py, v6m_exp6.py, v6m_exp6_analysis.py, v5v43.py, alif.py, analysis.json,
exp6_analysis.json, analysis_stdout.txt, stdout.txt, raw/*.npz. No existing file was modified. Everything here is about the MODEL. My own
simulations are post hoc red-team checks: exploratory, small n, not pre-registered.

New files (all under `results/v6m/redteam/RT_D/`, plus this review):
- `rtd_dn_nonlin.py` (+ `raw/`, `run_stdout.txt`): DN-only factorial, LC10a + all 147 intermediates clamped to each run's REF replay.
- `rtd_fb.py` (+ `raw_fb/`, `fb_stdout.txt`): DN-feedback subset test and a replication of the key interaction on fresh reps.
- `rtd_analysis.py` (+ `analysis_stdout.txt`): relative-gap F with the V6m paired bootstrap on the V6m raw npz, and Exp 4 re-reads.

**Seeds used (RT-D range 8 498 301–399 only):** noise 8 498 301–304 (test 1) and 8 498 305–308 (test 2); circular-shift offsets
8 498 351–354 (test 1) and 8 498 365–368 (test 2); bootstrap RNGs 8 498 398 and 8 498 399. Network instances reused, so no new
structural seeds: DATA, B1 8 421 001–003. CPU about 7 min in total (232 s + 165 s + about 20 s). Validation: the engine copy
`step_x` with default options reproduced the REF replay DNa02 count exactly in 96/96 runs (test 1) and 96/96 runs (test 2, assert).

---

## Summary of the attack

The data and validation look sound (T1–T5 are as reported). I found no hidden change to the neuron dynamics and no replay mismatch
in the parts I re-ran. **The interpretation has a problem, though: the central claim in §4 is contradicted by the report's own
secondary metric and by a cheap factorial check.** That claim is "a two-stage account, neither of which is DNa02 refractoriness;
the DN timing route survives t_ref 0; candidate leaky integration". With intermediates clamped, the DN-level "timing route" (the
M0→MCIRC effect) disappears and reverses sign when DNa02 refractoriness is removed. Removing the leak leaves it untouched.

## 1. Is "H1 not supported" fair? (REPORT l. 91–96, table l. 40–58)

Under the pre-registered rule (absolute gap is primary, protocol §5), "H1 not SUPPORTED" is procedurally correct. E1c gets F +0.21
(+0.06; +0.37), which is "contributes", not "removes most". But two things are wrong with how the report uses this result.

(a) **The rule outcome is "contributes", so DN refractoriness is not excluded.** The account at l. 109 ("two stages, neither of
which is DNa02 refractoriness") contradicts the report's own table (E1c contributes 21 %, replication 33 %).

(b) **The verdict depends on the metric, and the absolute metric is confounded by the operating point.** The protocol itself added the
relative gap "because ablations change the rate level". DNa02 goes from 86 to 165 Hz at t_ref 0. Below is F computed on the relative
gap, using the V6m paired hierarchical bootstrap (the same scheme as `v6m_analysis.gaps`, 10 000 draws, RNG 8 498 399) on the V6m raw
npz (`RT_D/analysis_stdout.txt` §2):

| condition | F abs (report) | **F rel (RT-D)** | would-be rule on rel |
|---|---|---|---|
| E1c DN t_ref 0 (main) | +0.21 (+0.06; +0.37) | **+0.59 (+0.51; +0.67)** | removes most |
| E1c DN t_ref 0 (replication) | +0.33 | **+0.65 (+0.59; +0.72)** | removes most |
| E1 DN t_ref 0 | +0.25 | +0.61 (+0.52; +0.70) | removes most |
| E1 DN t_ref 1 / 2 | −0.16 / −0.11 "enlarges" | **+0.20 / +0.06** (reduces) | contributes |
| E1 DN t_ref 4 / 6 | +0.11 / +0.27 "contributes" | **−0.03 / −0.05** | ≈ 0 / slightly enlarges |
| E5a subtractive reset (vs E1 t0) | +0.01 n.s. | **+0.17 (+0.08; +0.31)**, replication +0.17 (+0.06; +0.29) | contributes |
| E2a DN b_a 0 | −0.15 "enlarges" | +0.04 (+0.01; +0.09) | ≈ 0 |
| E2b intermediate b_a 0 | +0.02 n.s. | **+0.22 (+0.17; +0.28)**, replication +0.19 | contributes |
| E3 MCIRC / MPOIS (vs M0) | +0.36 / +0.49 | +0.47 / +0.58 | contributes / removes most |

The E4 criterion behaves the same way. The slope ratio in Hz is 0.75 (DN t_ref 0 / REF). Normalised by each curve's mean DN rate
(84.0 vs 137.9 Hz over the 10 Hz grid), it becomes **≈ 0.46**, which is at the pre-registered < 0.5 bound (rough CI ≈ 0.36–0.55 from
scaling the reported CI). The "DN b_a 0 steepens the slope ×1.2" result (l. 97–98) becomes **×0.94** after normalisation (mean
109.9 Hz), so it is a pure rate-scale effect. The intermediate t_ref 0 steepening (×1.30) survives normalisation.

(c) **Operating-point-matched check (RT-D test 1, exploratory).** A DN bias current is added in the DN-only clamp design so the DATA-train
rate is about the same in both dynamics (`RT_D/analysis_stdout.txt` §1):

| DN dynamics | DATA / B1 [Hz] | gap | rel |
|---|---|---|---|
| REF, bias +10 mV | 96.5 / 76.7 | −19.8 | −0.21 |
| REF, bias −10 mV | 75.0 / 57.8 | −17.2 | −0.23 |
| t_ref 0, bias −30 mV | 103.7 / 98.9 | **−4.8** | −0.05 |
| t_ref 0, bias −20 mV | 122.5 / 115.2 | −7.3 | −0.06 |

At a matched DATA rate of about 100 Hz, removing DN refractoriness removes about 75 % of the ABSOLUTE gap (−19.8 → −4.8 Hz). The REF
relative gap barely moves with bias (−0.21…−0.23), so the small relative gap at t_ref 0 is not caused by the rate doubling. If
anything it shrinks further at lower rates. The bias is not a neutral manipulation: it pushes the neuron towards fluctuation-driven
firing, where synchrony helps. So this is evidence, not proof.

**Fair wording:** "By the pre-registered absolute rule, DNa02 refractoriness contributes (21–33 %) but does not remove most of the
gap, so H1 is not supported as the sole primary cause. The relative metric (F 0.59–0.65) and an exploratory operating-point-matched
check (about 75 %) give the opposite reading, so the H1 conclusion depends on the metric." Leave the pre-registered label as it is,
and drop "neither is DNa02 refractoriness".

## 2. Is the non-monotone t_ref dose-response a quantization or operating-point artifact? (l. 92–94)

- **Quantization.** The engine maps t_ref 0/1/2/2.2/4/6 to 0/1/2/3/4/6 blocked steps (`v6m.py:66–67, 77`: `v[ref>0]=v_reset;
  ref-=dt`). The order of the points is therefore valid. "t_ref 0" still leaves a one-spike-per-1-ms-step cap, plus a hard reset to
  v_rest = v_reset, so a spike on consecutive steps needs g + I − a ≥ 140 mV. I removed that cap (variant C: t_ref 0, subtractive
  reset, several spikes per step allowed). The DN timing effect then reverses even more strongly (§3), so the quantization does not
  hide a residual refractory-like mechanism that would rescue the report's reading.
- **Operating point.** The non-monotonicity exists only in absolute Hz. The relative gap is monotone and saturating: t_ref 0 → 6 gives
  −0.090, −0.184, −0.217, −0.230, −0.236, −0.241 (log ratio −0.094 … −0.276). The absolute curve is this saturating relative curve
  multiplied by a DATA rate that falls with t_ref, which produces the extremum at 1–2 ms. Saturation once the dead time is ≥ 2–3 steps
  is what a per-volley cap predicts: once the dead time covers a volley, each volley yields at most one DN spike. **"1–2 ms ENLARGE
  the gap" and "t_ref 4–6 contributes" are rate-scaling statements and should be labelled that way.**

## 3. Is the "two-stage account" demonstrated? (l. 100–115)

**Stage (ii), the "timing route at DNa02 that survives t_ref 0, subtractive reset and b_a 0", was never tested.** No V6m condition
combines DN t_ref 0 with an intermediate surrogate. The claim is an inference from E1c leaving −15.6 Hz. I ran the missing factorial
(intermediates clamped, so DN input is identical across dynamics within a run):

| DN dynamics (RT-D test 1, reps 301–304) | gap M0 | gap MCIRC | F_timing = 1 − MCIRC/M0 (CI) |
|---|---|---|---|
| A REF (t_ref 2.2, hard reset) | −18.8 | −9.9 | **+0.47 (+0.25; +0.68)** |
| B t_ref 0, hard reset | −13.7 | −16.7 | −0.22 (−1.33; +0.25) |
| C t_ref 0, subtractive, multi-spike | −10.8 | −19.2 | −0.77 (−5.73; +0.02) |
| D = C + no leak (perfect integrator) | −27.9 | −24.0 | +0.14 (−0.43; +0.46) |
| E no leak only (t_ref 2.2, hard) | −19.7 | −10.4 | **+0.47 (+0.26; +0.72)** |

Replication on fresh reps 305–308 (`RT_D/fb_stdout.txt`): the change in gap from M0 to MCIRC is **+6.5 Hz (+3.9; +9.1) under REF** and
**−7.9 Hz (−13.3; −2.5) under DN t_ref 0**. The interaction is **+14.4 Hz (+10.8; +18.3)**.

What this means for the model:
- The DN-level timing effect depends on DNa02's refractory block. Without the block, synchronous intermediate input is more effective
  than the same counts spread in time, as expected for coincidence detection by a leaky integrator. B1's synchrony then partly offsets
  its count deficit. The −15.6 Hz left at E1c t_ref 0 is therefore count route minus a synchrony benefit, not a refractoriness-independent
  timing route.
- **The leaky-integration candidate is refuted in this test.** Removing only the leak leaves the timing share unchanged (0.47 vs
  0.47). In the perfect integrator (D) the timing share is about 0, as it must be, which is a positive control for the design.
- Stage (i), the count route, is supported, but its size is overstated. MCIRC keeps each neuron's ISI and burst structure. MPOIS
  (pre-registered) also removes that structure and leaves −10.1 Hz, i.e. **≤ 51 % absolute (42 % relative)**, not "64–77 %" (l. 114).
  Exp 6 is post hoc and correlational. It shows a 10.4 % excitatory drive deficit, but most of it is a global intermediate count deficit
  (n_mid −7.7 %, exc partners −7.6 %), so the "WHICH" part of "WHICH and HOW MANY" (l. 102) is small. The causal evidence for the count
  route is MPOIS, not Exp 6.
- The link "the two routes interact through intermediate refractoriness" comes from a single ablation (E1b) that changes rates,
  synchrony and inhibition at once (the report says so itself at l. 108). It is suggested, not demonstrated. One reading consistent
  with my result: E1b makes the intermediate output more synchronous, so DN refractory losses grow. That is the same DN mechanism, not a
  separate route.
- **Alternative: DN→intermediate→DN loop locking.** DNa02 excites 21 intermediates, which carry 44 % (L) / 18 % (R) of DNa02's
  excitatory input weight, so some REF intermediate spikes are time-locked to DN's own spikes, and MCIRC breaks that locking. I shifted
  only these 21 neurons (MCIRC_fb) or only the other 126 (MCIRC_nonfb). The results were +3.2 Hz (+0.5; +5.8) and +4.1 Hz (+1.7; +6.6),
  which adds up to about the full +6.5. The loop subset contributes about half of the timing effect with about 30 % of the weight. That
  fits partial loop locking but does not prove it. Report it as unresolved. (E1 ≈ E1c rules out feedback only for the t_ref effect,
  not for the MCIRC effect.)
- Cross-side and inhibitory structure is an unlikely explanation for the residual. Inhibitory drive is about 6 % of excitatory drive
  (Exp 6: −333 vs 5410), and E5b (removing intermediate→DN inhibition) changes F by −0.05 (relative −0.01).
- The "correlate" arguments (l. 95–96 and the "fraction of time refractory 0.26 vs 0.20" line) do not test the mechanism. A per-volley
  cap depends on whether input arrives during the dead time, not on the total refractory time. And "B1 still has more 1 ms ISIs at
  t_ref 0" is what the count route plus volley bursting predicts.

## 4. Exp 4: "~85 % reproduction" and "40 Hz vs 10 Hz" (l. 71–80, 124–125)

- **The 40 Hz claim reverses on the participation axis.** At EQUAL participation p, 40 Hz events are less harmful: DN is 91.9 vs 87.2 Hz
  (p 0.35), 74.5 vs 72.2 (p 0.7) and 69.2 vs 64.3 (p 1.0). "Many small volleys are more harmful" holds only on axes (Fano, χ², pairwise
  r, volley score) that grow superlinearly with volley size. At a fixed fraction of aligned spikes, larger volleys are worse, which is
  again what a per-volley cap predicts. Restate it as "no single synchrony metric is sufficient", and give both readings.
- **"The real trains fall on the REF curve" holds only on the Fano5/Fano10 axes.** The 10 Hz family was built to span Fano10. On the
  other axes the synthetic curve predicts, for DATA, χ² 92.5, pairwise 92.4, volley 100.9 and CV 91.1 Hz (real 86.5), and for B1
  74.2 / 73.9 / 83.0 / 73.4 Hz (real 66.6). The real trains are 6–16 Hz below the surrogate. **The gap fraction is fairly robust**
  (70 % on Fano2, 80 % on Fano20 where B1 lies outside the grid, 89–93 % on all others) only because the offsets roughly cancel between
  sources. Wording: "one surrogate family (shared Poisson events ±1 ms) with DATA counts reproduces 70–93 % of the gap depending on the
  synchrony axis used for interpolation; the real trains carry additional structure the surrogate lacks."
- Fano rate dependence is NOT a problem inside Exp 4 (per-neuron counts are fixed exactly) or between DATA and B1 LC10a (lc_win
  1256.8 vs 1253.3, 0.3 %). It is a problem for cross-condition intermediate Fano comparisons with different rates (E1b: 13 → 20 Hz).
  The pairwise-r axis (0.171/0.412 → 0.255/0.589) supports the same direction, so cite r instead of Fano there.
- Exp 4 uses only the DATA network, with unit = rep (n = 8). The slope CIs come from resampling reps only.

## 5. Statistics / pseudoreplication

The unit handling matches the protocol. The B1 instances are nearly identical (per-instance REF gap −18.2…−21.8), so the CI reflects
noise reps. The receiving network is always the single DATA network, so every CI is conditional on that network (n = 1 downstream
structure). The surrogate RNG seeds (`v6m.py:252, 261`: `8_440_000 + 100·vi + r`) are shared by all sources for a given rep, so only
8 surrogate draws exist and the bootstrap over B1 instances does not sample surrogate randomness. That is a minor issue: F CIs for
LCIRC/MCIRC/MJ/MPOIS are slightly optimistic. Contributions that are "not summed" is correctly stated.

## 6. Biology language and labelling

There is no sentence presenting model properties as Drosophila biology (l. 4–6 and l. 117 disclaim it explicitly). Labelling gaps:
(i) the H5 bullet (l. 104–108) uses Exp 6 numbers (−10.4 % → +1.7 %, +51 % inhibitory drive) without "post hoc"; (ii) the "Best-supported
account" (l. 109–115) rests on Exp 6 and on an untested inference, but is presented as the main conclusion. It should be labelled
"hypothesis-generating; stage (ii) contradicted by RT-D post-hoc factorial". (iii) §7's "no-leak ablation (τ_m → ∞)" (l. 135) is
technically wrong for this engine. In `alif.py:75` / `v6m.py:65`, τ_m also scales the input (`v += dt/τ_m·(v_rest − v + g + I − a)`),
so τ_m → ∞ silences all input. The correct ablation drops only the (v_rest − v) term, as in `RT_D/rtd_dn_nonlin.py`
(`keepleak`). In any case it is now tested and negative.

## 7. Single most efficient next experiment

A **pre-registered DN-only factorial with intermediates clamped** (cheap: DN input is fixed, about 4 min CPU per 100 runs here): DNa02
dynamics {REF, t_ref 0, t_ref 0 + bias matched to the REF DATA rate, t_ref 1, t_ref 6} × intermediate input {M0, MCIRC, MPOIS,
count-swap (DATA timing with B1 per-neuron counts via the Exp 4 generator at the intermediate layer, and the reverse)}, on fresh seeds,
the 10 main B1 instances and 8 reps. Pre-register as primary the **interaction** (gap change from M0 to MCIRC/MPOIS under REF minus the
same under t_ref 0), with both absolute and log-ratio metrics fixed in advance. It decides in one design whether stage (ii) is DNa02
refractoriness (RT-D says yes: interaction +14.4 Hz), separates the count and timing routes cleanly through count-swap, and fixes the
metric ambiguity through rate matching. Add one alternative parameter set (for example J0 or b_a) as a robustness arm only if the
first is decisive.

---

## Verdict: **NOT_READY**

The data, validations and pre-registered rule outcomes are sound. But §4's main interpretation ("two stages, neither DNa02
refractoriness; DN timing route survives t_ref 0; leak candidate") is contradicted by the report's own secondary metric and by an
exploratory RT-D factorial whose interaction CI excludes 0 on two independent rep sets. §4/§7 need rewriting before the report is
final. No rerun of the V6m main data is needed.

## Required corrections to REPORT.md

1. §4 H1 (l. 91–96): keep the pre-registered label ("contributes; not SUPPORTED as sole primary cause"). Add the relative-metric
   result (E1c F_rel +0.59 (+0.51; +0.67), replication +0.65) and the normalised E4 slope ratio of about 0.46, and state that the H1
   conclusion depends on the metric. Cite the RT-D rate-matched check (about 75 % at about 100 Hz) as exploratory.
2. Delete "neither of which is DNa02 refractoriness" (l. 109) and "timing route; survives DNa02 t_ref 0, subtractive reset and b_a 0"
   (l. 112). Neither condition was tested with an intermediate surrogate, and the RT-D factorial shows the DN timing effect
   disappears or reverses at t_ref 0 (interaction +14.4 Hz (+10.8; +18.3)).
3. Remove "leaky integration" as the leading candidate (l. 112–113, l. 116). Report that removing the leak alone leaves the timing
   share unchanged (0.47 vs 0.47, RT-D, exploratory).
4. Relabel the t_ref dose-response (table l. 43–46, l. 92–94): "enlarges" at 1–2 ms and "contributes" at 4–6 ms are absolute-Hz
   operating-point effects. In relative terms the gap shrinks monotonically as refractoriness is reduced and saturates at ≥ 2–3
   blocked steps. Give the blocked-step mapping.
5. H2 (l. 97–99): "DNa02 adaptation reduces the gap / partial compensation / slope ×1.2" is an absolute-scale effect (F_rel +0.04;
   normalised slope ratio about 0.94). "Intermediate adaptation has no measurable effect" holds only in absolute terms (F_rel +0.22,
   replication +0.19).
6. E5a (l. 94–95): "not the cause" → "no effect on the absolute gap; reduces the relative gap by 17 % (CI excludes 0)".
7. H3 / contributions (l. 101–103, l. 114): use MPOIS (≤ 51 % absolute, 42 % relative) as the bound on the count route, not "MCIRC
   residual 64–77 %". Note that MCIRC keeps single-neuron burst structure and that the DN→intermediate loop subset (21 neurons) carries
   about half of the MCIRC effect (RT-D, unresolved). Cite Exp 6 as descriptive (mostly a global intermediate count deficit), not as
   identifying the residual.
8. Label every use of Exp 6 as post hoc (H5 bullet l. 104–108 and the account l. 109–115), and label the two-stage account
   "hypothesis-generating".
9. Exp 4 (l. 75–80, l. 124–125): state that "real trains fall on the REF curve" holds only on Fano5/Fano10 (6–16 Hz off on χ², r,
   volley, CV). Give the gap reproduction as 70–93 % depending on the axis, for one surrogate family. Add that at equal participation p
   the 40 Hz events are less harmful (91.9/74.5/69.2 vs 87.2/72.2/64.3 Hz), so "many small volleys are more harmful" is axis-dependent.
10. Remove the "fraction of time refractory 0.26 vs 0.20" and floor-ISI arguments as evidence against refractoriness, or label them
    non-diagnostic for a per-volley cap mechanism.
11. §7 (l. 133–136): correct the "τ_m → ∞" no-leak definition (τ_m also scales the input in `alif.py:75`) and replace §7 with the
    pre-registered DN-only factorial with the interaction as primary (RT-D §7).
12. §6: add that the surrogate RNG offsets are shared across sources per rep (8 draws), so the CIs of the surrogate conditions do not
    include surrogate variability. Also add that every CI is conditional on the single DATA receiving network.
