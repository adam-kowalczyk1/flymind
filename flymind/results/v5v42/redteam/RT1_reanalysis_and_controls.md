# V5 v4.2 — Red team RT1: independent reanalysis and control verification (2026-10-30)

**Verdict: PASS_WITH_LIMITATIONS.** Every headline number reproduces exactly from the raw npz files. All 15 re-created block
instances match structure.json and pass all 17 properties. The attempt factor is not a confound. B1 is mixed inside the LC×LC
block exactly as much as SWS is. The B2 caveat (L1) is the reason for the limitations: at the mean-rate level, B2 is close to a
null manipulation under the E1 stimulus. So B2 tests the alignment hypothesis only weakly, and that conclusion needs narrower
wording.

Scope: read-only on project files. Helper scripts and outputs are in
`/private/tmp/claude-501/-Users-admin-so101-fly-project/075990a2-3231-4039-8d41-31f3fdcb9204/scratchpad/rt42/RT1/`
(`recompute.py` → `recompute.json`, `controls.py` → `controls.json`, `proxy.py`). I ran no new simulations, so no red-team seeds
were used. The only RNG was the bootstrap in `recompute.py` (seed 8 496 001). Re-created networks use the registered seeds
listed in structure.json. The code does not import `v5v41_analysis`, `v5v42_analysis` or bio2, and does not use MuJoCo.
Total CPU was about 4 min.

## 1. Recompute from raw npz (own code)
Definitions:
- **DNa02 ipsi.** Count column 4 for side L and column 5 for side R, ×100 Hz, steady bins 50–99 (500–1000 ms), mean over
  reps and sides, then a trapezoid average over levels.
- **LC10a ipsi Fano.** Column 0 (population count, 10 ms bins) at 7–9 mV, bins 50–99. Variance (ddof 0) divided by the mean,
  then nanmean over levels, sides and reps.
- **E6 G_small.** D = DN_L − DN_R steady rate, averaged over reps, then the OLS slope over |δ| ≤ 1.

| Family | ΔDN 6–9 (trap.) | ΔDN 6–9 (plain) | ΔDN 8–10 | ΔLC 6–9 | LC Fano E1 (DATA 11.27) | LC Fano noise 0 (DATA 78.6) | ΔG I0=7 | ΔG I0=10 |
|---|---|---|---|---|---|---|---|---|
| SWS | −17.434 | −17.482 | −22.972 | −0.003 | 38.93 (all 50 > DATA) | 106.9 | −15.67 | +21.36 |
| B1 LC×LC | −16.408 | −16.480 | −21.450 | +0.002 | 38.75 (50/50) | 106.8 | −15.21 | +22.25 |
| B2 LC→mid | −1.762 | −1.786 | −0.512 | −0.032 | 11.30 (range 10.8–11.8) | 77.9 | −3.47 | +0.48 |
| B3 mid→LC | −0.929 | −0.968 | −1.192 | −0.041 | 11.63 | 69.9 | −1.99 | −0.42 |
| B4 mid×mid | −0.962 | −1.022 | −1.843 | −0.017 | 11.54 | 76.8 | −3.40 | −2.06 |
| B5 ALL | −17.474 | −17.541 | −22.938 | −0.016 | 38.97 | 107.4 | −15.88 | +21.10 |

- **Agreement with analysis.json.** Every value matches to the third decimal for every family and metric. That covers the
  trapezoid and plain means, 8–10, LC, both Fano values, and G at 7 and 10.
- **B1 share.** B1 accounts for 16.408 / 17.434 = **94.1 %** of the SWS deficit. The sum B1..B4 is **−20.06** Hz against
  −17.43 Hz for SWS. These match the headline.
- **B1 vs SWS.** B1 is reliably smaller than SWS: +1.03 Hz, instance bootstrap CI (+0.90; +1.15), and analysis.json gives MW
  p 2e-17. The instance ranges only partly overlap (B1 50.9–52.1 Hz, SWS 49.7–51.1 Hz). "~94 %" is the right framing;
  "B1 = SWS" would not be.
- **B5 vs SWS.** The difference is −0.04 Hz with a CI that includes 0, so the re-implementation is confirmed.
- **CI caveat.** The author's hierarchical CIs, for example B1 (−17.39; −15.50), are wide mainly because of the noise in the
  single DATA network's 8 reps, which all families share. Instance-only CIs are about ±0.1 Hz. Two consequences:
  - Under the pre-registered rule "Δ CI overlaps the SWS Δ", B1's CI misses the SWS point Δ (−17.43) by 0.04 Hz. It does
    overlap SWS's CI. The report should say which reading it applies.
  - B2, B3 and B4 all have CIs that exclude 0: B3 (−1.92; −0.016), B4 (−1.92; −0.036). The pre-registered label for them is
    therefore "partial / unresolved", not "does not contribute". The report's wording ("minor") is compatible with this, but
    the label should be stated.
- **Non-additivity.** The sum is 2.6 Hz more negative than SWS. B2 + B3 + B4 add up to −3.65 Hz, while SWS − B1 is only −1.03 Hz.
  The interaction is therefore about 2.5× the residual that B1 leaves unexplained. "Mild" is fair relative to 17 Hz but large
  relative to the non-B1 effects. The off-LC blocks' isolated effects are mostly absorbed once LC×LC is shuffled.

## 2. Controls (re-created via `block_shuffle`, seeds xx001, xx025, xx050 per family, plus 3 SWS)
- **(c) sha.** All 15 block instances and 3 SWS instances reproduce the structure.json W sha256. The DATA sha also matches.
- **(b) Properties.** `side_shuffle.properties` passes all 17 KEYS for every instance, with no failures. All instances are
  complete (swaps = target).
- **(a) Outside the block.**
  - `np.array_equal(W1[~block], W0[~block])` is True for all 12 single-block instances. For B5, everything outside the four
    blocks is identical.
  - Nit: outside-block entries are value-identical, not byte-identical. DATA's W_data holds 2775 signed zeros (−0.0), and
    `block_shuffle` rebuilds W from `np.zeros`, which turns them into +0.0. This has no effect on the dynamics. The phrase
    "bit-identical" in the protocol, the report and the docstring should read "value-identical (signed zeros normalised)".
- **(d) Attempt factor 10 vs 3.**
  - B1 with cap 3 gives the **identical W**: same sha for all 3 instances, attempts/target 1.48–1.49. The rng sequence is the
    same and the loop stops at the target before either cap applies.
  - B3 (1.15–1.18) and B4 (2.00–2.02) also give the identical W at cap 3.
  - Only B2 needs a factor above 3 (attempts/target 3.38–3.41). At cap 3 it stops incomplete, at 20 891–21 190 of
    23 750 swaps, with an in-block changed fraction of 0.520–0.523 against 0.513–0.514 at cap 10. So it is already saturated.
  - **Not a confound for B1, B3 or B4.** For B2 the higher cap only lets the run finish; it does not mix the block more
    (0.51–0.52, the same as SWS in that block).
- **(e) B1 mixing vs SWS inside LC×LC.**

| | changed-edge fraction | |w| moved | top 10 % block edges moved | top 1 % block edges moved |
|---|---|---|---|---|
| B1 (3 inst.) | 0.801–0.813 | 0.788–0.796 | 0.92–0.93 | 0.59–0.71 |
| SWS (3 inst.) | 0.810–0.815 | 0.787–0.796 | 0.91–0.93 | 0.63–0.70 |

  The 50-instance family means in structure.json are 0.809 (B1) and 0.810 (SWS). LC×LC reciprocal pairs are 540 vs 544 and
  triangles 24 226 vs 24 184. The two are equivalent mixtures. The remaining 6 % gap to SWS cannot be blamed on weaker mixing
  inside LC×LC.

## 3. Is B2's small effect because B2 barely changes anything?
- **Structurally, no.** About 51 % of the 4750 LC→mid edges change partner, the same as SWS (0.515–0.518). That is 34 % of the
  block's |w|; SWS moves 33–34 %. About 39 % of the top-10 % block edges move. However, **0 % of the top-1 % LC→mid edges
  move**, in B2 and in SWS alike, because their exact weights are unique so the keys cannot be swapped. The report's figure,
  "moves 38 % of the strongest edges", refers to the whole network's top 5 % and is correct as stated.
- **Functionally, at the mean-rate level, almost yes (L1).** I took DATA's per-neuron steady spike counts (E1_ss, 8 mV,
  L driven) and multiplied them by the block weights:
  - LC10a ipsi rates are nearly homogeneous across neurons (CV 0.089, n = 135).
  - Swaps keep each mid neuron's (partner group, weight) multiset.
  - Result: B2 changes the LC→mid input vector to mid neurons by only **1.8–2.1 %** (relative L2, r = 0.9998).
  - For comparison: B1 changes the LC→LC input by 6 % (r = 0.997), B4 changes the mid→mid input by 13 %, and B3 changes the
    mid→LC input by 84 %.

  Under homogeneous unilateral drive, B2 is therefore close to mean-field-null by construction. Any effect it has must come
  through correlation structure (shared input), not through mean drive. This does not make the result wrong. It makes the
  "alignment hypothesis not supported" conclusion conditional on a near-uniform stimulus, which is a weak test of
  LC→mid targeting.

  The same proxy supports the author's main claim: B1 also leaves mean recurrent drive almost unchanged (6 %), yet it carries
  the 16 Hz effect and the full Fano increase. The B1 effect is a dynamic/synchrony effect, not a redistribution of mean input.

## 4. Other observations
- **Cross-family structure–function correlations** (lc_recip ρ 0.80, all_clust ρ 0.91, n = 300) come almost entirely from the
  two-cluster split between {SWS, B1, B5} and {B2, B3, B4}. They carry no information beyond the family means. Within B1,
  lc_recip gives ρ −0.29 (CI −0.52; −0.02), which is weak and of the opposite sign to the cross-family ρ. The report should
  not cite the n = 300 correlations as evidence for a specific statistic.
- **ΔG at I0 = 10 mV** is +21 to +22 for SWS and B1, so the gain is higher there. This is an operating-curve shift, not a
  uniform deficit. The report states it, and it is correct.

## 5. Required edits before the report is final
1. Change "bit-identical" to "value-identical (signed zeros)" in the protocol and report text. Optionally fix the docstring
   (code is frozen, so this is not required).
2. State the CI-overlap reading used for B1, and the formal label for B2–B4 ("partial / unresolved"; their CIs exclude 0).
3. Add L1: B2 preserves mean LC→mid input to about 2 % under the E1 stimulus, and the top-1 % LC→mid edges never move. The
   alignment hypothesis is therefore only weakly tested; a heterogeneous or topographic LC drive would be needed.
4. Restate the non-additivity relative to the non-B1 residual: sub-additive by 2.6 Hz against a 1.0 Hz residual.
