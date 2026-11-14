# V5 v4.2 — Single-block connectivity controls: report (2026-10-30)

**Status: exploratory, completed. Verdict: PASS_WITH_LIMITATIONS (both red-team reviewers PASS_WITH_LIMITATIONS; corrections applied).**

## 1. What was done
Protocol `program_v5v41/V5v42_PROTOCOL.md` (r1, written before any V5 v4.1 result; sha in `protocol_sha256_before_run.txt`) +
analysis amendment A2 (synchrony mediators, sha d710e3fe…, written before any v4.2 dynamics result was opened).
Controls (`block_shuffle.py`, tests 7/7): the SWS v2 swap rule restricted to one block; edges outside the block value-identical to
DATA (checked for every instance; not byte-identical: 2775 DATA entries of −0.0 become +0.0 — no dynamical effect, RT1). 5 families × 50 instances (seeds 8 421–8 425 0xx); reference DATA and SWS from V5 v4.1 (same
networks, noise seeds, schedules). Open-loop schedules E1 (unilateral, 4–12 mV), E1n0 (noise 0), E6 (symmetric ± δ).
Run 09:15–10:35, 250 networks, 0 errors; structure step 301 instances distinct, all invariants OK; Stage 1 28/28 before/after;
protected tree unchanged.

## 2. Structure (medians per family; `structure.json`)
| Family | LC×LC recip. pairs | LC×LC triangles | LC×LC clustering | LC↔mid recip. pairs | mid×mid triangles | whole-net clustering | top-1 % / top-5 % strongest edges kept | total |w| |
|---|---|---|---|---|---|---|---|---|
| DATA | 2450 | 20 502 | 0.633 | 231 | 5466 | 0.558 | 1.00 / 1.00 | 22 793.8 |
| SWS | 544 | 24 184 | 0.310 | 66 | 6029 | 0.342 | 0.96 / 0.64 | same |
| B1 LC×LC | 540 | 24 226 | 0.310 | 231 | 5466 | 0.371 | 1.00 / 1.00 | same |
| B2 LC→mid | 2450 | 20 502 | 0.633 | 72 | 5466 | 0.426 | 0.95 / 0.62 | same |
| B3 mid→LC | 2450 | 20 502 | 0.633 | 81 | 5466 | 0.545 | 1.00 / 1.00 | same |
| B4 mid×mid | 2450 | 20 502 | 0.633 | 231 | 6020 | 0.528 | 1.00 / 1.00 | same |
| B5 ALL | 549 | 24 164 | 0.310 | 66 | 5980 | 0.342 | 0.96 / 0.64 | same |
Weight multiset, signs, synapse counts, per-neuron degrees/strengths and (partner group, weight) multisets: identical in all
families (by construction, checked). One strong component in every network. Inside a block the graph statistics change together:
B1 lowers LC×LC reciprocity (−78 %) and clustering (−51 %) but RAISES undirected triangles (+18 %) — they cannot be separated by
this design. B2 and B3 each also change LC↔mid reciprocal pairs (motifs spanning two blocks — not preservable when one block is
shuffled alone). Changed-edge fraction inside the shuffled block equals SWS's in that block (B1 0.81, B2 0.52, B3 0.86, B4 0.63).

## 3. Dynamics (Δ = family − DATA, CI95 hierarchical bootstrap; DNa02 ipsi steady state, E1, noise 2 mV)
| Family | Δ DN 6–9 mV [Hz] | Δ DN 8–10 | Δ DN noise 0 (6–10) | Δ I_th30 [mV] | Δ G(I0 7) [Hz/mV] | Δ G(I0 10) | LC10a Fano 7–9 mV (DATA 11.3) | mid Fano (DATA 9.3) |
|---|---|---|---|---|---|---|---|---|
| SWS | −17.4 (−18.4; −16.5) | −23.0 | −6.9 | +0.17 | −15.7 (−21.3; −11.0) | +21.4 | 38.9 | 22.6 |
| **B1 LC×LC** | **−16.4 (−17.4; −15.5)** | −21.5 | −6.5 | +0.15 | −15.2 (−20.9; −10.5) | +22.2 | **38.8** | 22.6 |
| B2 LC→mid | −1.8 (−2.7; −0.8) | −0.5 (CI incl. 0) | +1.7 | +0.01 | −3.5 (CI incl. 0) | +0.5 (CI incl. 0) | 11.3 | 12.6 |
| B3 mid→LC | −0.9 (−1.9; −0.02) | −1.2 | +3.0 | +0.01 | −2.0 (CI incl. 0) | −0.4 | 11.6 | 9.6 |
| B4 mid×mid | −1.0 (−1.9; −0.04) | −1.8 | +1.5 | −0.01 | −3.4 (CI incl. 0) | −2.1 | 11.5 | 9.4 |
| B5 ALL | −17.5 (−18.4; −16.6) | −22.9 | −6.9 | +0.17 | −15.9 | +21.1 | 39.0 | 22.6 |
LC10a mean rate Δ ≤ 0.04 Hz in every family. Family vs SWS (6–9 mV): B1 +1.0 Hz (CI +0.9; +1.2), B2–B4 +15.7…+16.5, B5 −0.04
(CI includes 0 — re-implementation check passed). Additivity: Σ(B1..B4) = −20.1 Hz vs SWS −17.4; the sum re-uses the single DATA reference four times (its rep noise ≈ ±2–3 Hz,
RT2 (d)) and has no CI → additivity UNRESOLVED (B2+B3+B4 = −3.7 vs the SWS − B1 residual of −1.0 Hz).
LC10a 6–14 Hz relative power: DATA 0.535, SWS/B1/B5 0.411, B2–B4 0.54 (the synchrony difference is broadband, not a 6–14 Hz peak
increase in this measure). At noise 0 LC10a Fano is DATA 78.6 vs B1/SWS 107 (the synchrony difference persists without noise;
the DNa02 difference shrinks).

## 4. Interpretation (pre-registered rules, A2; wording corrected after red team)
- **Locus:** the LC10a×LC10a block carries most of the open-loop DATA vs SWS difference at this parameter set: B1 alone gives ~94 %
  of the SWS DNa02 deficit (6–9 mV; B1 − SWS = +1.0 Hz, CI +0.9; +1.2 — B1 ≠ SWS), the E6 gain pattern, the threshold shift and the
  full LC10a synchrony increase. CI-overlap reading used: B1's CI (−17.4; −15.5) touches but does not contain SWS's point estimate
  (−17.43) — "reproduces most of", not "reproduces".
- B2, B3, B4: CIs exclude 0 by small margins (B3/B4 by 0.02–0.04 Hz) → pre-registered label **"partial / unresolved"** (not
  "does not contribute"). B2 is close to a null manipulation at the mean-rate level under uniform drive: LC10a rates are nearly
  uniform (CV 0.09) and swaps keep each intermediate's (partner group, weight) multiset, so mean LC→mid input changes by only ~2 %
  (RT1 L1). "Alignment hypothesis not supported" is limited to near-uniform drive.
- **Synchrony:** the block that changes LC10a synchrony is the block that changes DNa02 (co-localisation). B1 changes rate-weighted
  LC→mid drive by < 1 %, so the effect travels through LC10a output TIMING (RT2). But Fano is NOT shown to be THE mediator: at noise 0
  the Fano gap is similar (~28) while the DNa02 deficit is only −2.7 Hz; B2 raises intermediate Fano (12.6 vs 9.3) with little
  DNa02 change; relative 6–14 Hz power is LOWER in SWS/B1 → no "oscillation" wording. Causal test needed (§7).
- **Which LC×LC statistic?** Not identified by v4.2 (reciprocity, clustering, triangles change together; triangles rise
  mechanically because fewer reciprocal pairs means more undirected edges). Red-team pilot (RT2, exploratory, 5 instances, 3
  levels, seeds 8 496 101–105 / 8 496 001–004; not re-run by me): a reciprocity-PRESERVING LC×LC shuffle still produces SWS-like
  synchrony (Fano 33–35 vs B1 37–38, DATA 12.5) and closes only ~12–14 % of the DNa02 gap → reciprocity is at most a minor
  contributor; triangle count alone is also ruled out. Remaining candidates: clustering / local (possibly retinotopic) LC wiring.
- Across-family structure–function correlations (n = 300, ρ 0.80–0.91) are a two-cluster contrast between {SWS, B1, B5} and
  {B2, B3, B4} over pseudo-replicates; within-family ρ is null — not cited as evidence for any statistic.
- All of this is MODEL dynamics (ALIF, J0 0.2, b_a 0.5, σ 2) on DATA structure; no statement about the fly; open-loop unilateral
  deficit ≠ behavioural effect (closed loop: V6 family X = B1).

## 5. Limitations
Within-family spread is noise-level, so n = 50 estimates the family mean; CIs are dominated by the single DATA reference's 8 noise
reps (RT2: two halves of 16 fresh DATA seeds differ by 1.9 Hz; per-level reference error −4.7…+3.3 Hz) — ≥ 32 DATA reps would help
more than more instances. One parameter set; Fano from 10 ms summed counts (no spike times).

## 6. Red team
RT1 (`redteam/RT1_reanalysis_and_controls.md`): independent recomputation matches analysis.json to 3 decimals for all families;
controls re-created (3 per family) — sha, 17 invariants, outside-block identity, completion all OK; attempt cap 3 vs 10 not a
confound (only B2 needs > 3 and is saturated at 0.52 changed fraction); B1 mixes LC×LC as much as SWS. PASS_WITH_LIMITATIONS.
RT2 (`redteam/RT2_interpretation_skeptic.md`): wording over-reach (additivity, B3/B4 labels, "reproduces"), Fano-as-mediator not
shown, reciprocity-preserving pilot (above). PASS_WITH_LIMITATIONS. Both reviewers are separate model instances (limited
independence), not human review.

## 7. Next (not run here)
V5 v4.3 candidates: (a) LC10a spike-train replay into DATA downstream wiring (validate with DATA's own trains; jitter / circular
shift B1 trains; inject synchrony into DATA trains; rate-matched Poisson) — the causal test of the timing route; (b) clustering-
preserving LC×LC control; (c) ≥ 32 DATA noise reps for the reference.
