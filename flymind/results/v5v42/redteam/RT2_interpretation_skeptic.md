# V5 v4.2: Red team RT2, interpretation skeptic (2026-10-30)

Scope: what the V5 v4.2 single-block results let the author claim. I only read existing files. New simulations used red-team seeds
only, or re-created registered networks and checked them against the sha256 values in structure.json. Helper scripts and raw
outputs are in `/private/tmp/claude-501/-Users-admin-so101-fly-project/075990a2-3231-4039-8d41-31f3fdcb9204/scratchpad/rt42/RT2/`
(`feas.py`, `rp_pilot.py`, `data_null.py`, `rate_drive.py`, plus `*.json`/`*.npz` outputs). Total CPU time was under 5 min.
Labels: **DATA** = connectome counts; **MODEL** = simulated ALIF dynamics; **CONTROL** = shuffled networks.

**Verdict: PASS_WITH_LIMITATIONS.** The locus claim holds within this model: in open loop at D0 parameters, the LC×LC block
carries about 94 % of the SWS DNa02 deficit and all of the LC10a Fano increase. Three parts of the headline go too far:
the "mild non-additivity" finding, B3/B4 counted as non-zero contributions, and any reading of "synchrony" or of a single graph
statistic as the mediator.

## 0. Headline numbers re-checked from analysis.json (MODEL / CONTROL)
| Family | ΔDNa02 ipsi 6–9 mV [Hz] (CI95) | LC Fano (DATA 11.27) | mid Fano (DATA 9.32) | ΔG_small I0 = 7 / 10 | ΔDN noise 0 |
|---|---|---|---|---|---|
| SWS | −17.43 (−18.41; −16.50) | 38.93 | 22.61 | −15.7 / +21.4 | −2.67 |
| B1 LC×LC | −16.41 (−17.39; −15.50) | 38.75 | 22.56 | −15.2 / +22.2 | −2.59 |
| B2 LC→mid | −1.76 (−2.73; −0.82) | 11.30 | **12.55 (50/50 > DATA)** | −3.5 / +0.5 | +0.09 |
| B3 mid→LC | −0.93 (−1.92; **−0.02**) | 11.63 | 9.60 | −2.0 / −0.4 | **+2.19** |
| B4 mid×mid | −0.96 (−1.92; **−0.04**) | 11.54 | 9.39 | −3.4 / −2.1 | −0.03 |
| B5 ALL | −17.47 (−18.43; −16.55) | 38.97 | 22.62 | −15.9 / +21.1 | −2.68 |

The author's numbers are reproduced exactly. B1 − SWS = +1.03 Hz (+0.90; +1.15), so the remaining 6 % is real. B5 − SWS = −0.04 (−0.17; +0.08).

## (a) Reciprocity, triangles and clustering: can any one of them be singled out?
**Not from B1.** In the LC×LC block, B1 changes reciprocal pairs (2450 → 544), undirected triangles (20 502 → 24 207) and
clustering (0.633 → 0.310) together. They are not independent (DATA): LC×LC has 275 neurons and 6189 directed edges, all of
them within a side. The number of undirected edges equals directed edges minus reciprocal pairs, so it rises from 3739 to about
5645 (+51 %) when reciprocity is destroyed. The rise in triangles is therefore a mechanical by-product of the reciprocity loss
(more distinct edges). Clustering falls even so, because it is normalised by the larger undirected degrees.

The 300-instance Spearman correlations in analysis.json (lc_recip ρ 0.80, all_clust 0.91, lc_tri −0.80) are **not
structure–function evidence**. The points fall into two clusters (SWS/B1/B5 vs B2/B3/B4), so ρ is a two-group contrast
over pseudo-replicates. Within families ρ is null (SWS lc_recip 0.13, CI includes 0) or of the opposite sign (B1 lc_recip −0.29).
These values should not be cited.

**Reciprocity-preserving LC×LC control (RP-LC), proposed and piloted.**
- **Rule.** Same key as SWS: signed weight plus layer×side group of pre and post.
  - Reciprocal pairs are swapped as units: (a↔b, c↔d) → (a↔d, c↔b), only between pairs with the same key
    (g_a, g_b, w_ab, w_ba), and only when no edge exists in either direction between the new partners.
  - Non-reciprocal edges get ordinary double swaps, with an extra constraint that forbids creating a reciprocal pair.
  - 5 swaps per unit; the attempt cap is 10× the target.
- **Feasibility (DATA).**
  - 2345 of the 2450 reciprocal pairs fall in keys with ≥ 2 members (285 keys; the largest has 133 pairs).
  - 1288 of the 1289 single edges are swappable.
  - The target was reached in all 5 instances (18 695 swaps from about 30 700 attempts).
  - All 17 SWS invariants held, and every edge outside the block was unchanged.
  - Changed-edge fraction in LC×LC was 0.74; B1's is 0.81.
- **Structure (CONTROL).** Reciprocal pairs stayed at exactly 2450 and undirected edges at 3739. Triangles fell to 6954–7194
  and clustering to 0.20–0.21. Both are lower than in B1 and in DATA.
- **Pilot dynamics (MODEL, exploratory, not pre-registered).**
  - Setup: 5 RP-LC instances (shuffle seeds 8 496 101–105); levels 7, 8, 9 mV; both sides; noise seeds 8 496 001–004; ALIF noise 2 mV; unchanged `v5v41.simulate`.
  - References were re-simulated with the same red-team noise seeds: DATA, B1 8 421 001–002 and SWS 8 410 001–002 (sha checked).

| Network | DNa02 ipsi, mean of 7/8/9 mV [Hz] | LC ipsi Fano |
|---|---|---|
| DATA | 84.3 | 12.5 |
| SWS (2) | 64.8–65.2 | 37.8–38.3 |
| B1 (2) | 66.3–66.9 | 36.5–37.7 |
| RP-LC (5) | 67.8–71.0 | 33.3–34.9 |

- **Reading.** Preserving reciprocity, and with it the undirected edge count, does **not** restore DATA-like synchrony. It closes
  about 12 % of the Fano gap and about 14 % of the DNa02 gap. Every one of the 5 RP instances lies between B1 and DATA, so the
  effect is small but consistent. Reciprocity is a minor contributor at most.
- **Triangle count alone is also ruled out.** B1 has more triangles than DATA and RP-LC far fewer, yet both are synchronous.
- **Still candidates:** what RP-LC and B1 both destroy, namely normalised clustering and higher-order or local (possibly
  retinotopic) organisation of LC10a wiring.
- **Next controls:**
  - a clustering- or triangle-preserving rewiring (dK-2.5-type MCMC on the undirected LC graph, with the RP-LC pair rule);
  - the converse: keep clustering, break reciprocity;
  - if LC10a column or soma positions are available, a distance-binned swap that keeps spatial locality.
- **Limits of the pilot:** n = 5 instances, 4 noise reps, 3 levels, references with n = 2. It is a pilot, not a result.

## (b) Is "synchrony mediates the DNa02 deficit" supported?
**Only partly.** B1's construction plus one extra check makes "LC10a output **timing** carries the effect" nearly forced
within the model. It does not establish **population synchrony as measured by Fano** as the mediator.
- **For (MODEL).**
  - In B1 every block downstream of LC (LC→mid, mid×mid, mid→DN, mid→LC) is bit-identical to DATA, so any DNa02 change must
    pass through LC10a spike trains.
  - The mean LC rate is unchanged (Δ +0.002 Hz).
  - New check: from the stored per-neuron steady counts (E1_ss, 6–9 mV), I computed the timing-free, rate-weighted LC→mid drive
    Σ w·r. It changes by only −0.4 to −1.0 % in B1 (3 instances, sha checked), so redistributing rates across LC neurons does not
    explain the deficit. What reaches mid is a difference in temporal structure.
  - The pre-specified A2 discrimination rule is met: B1 shows SWS-level LC Fano and B2–B4 leave LC Fano at DATA level.
- **Against, or not yet shown.**
  1. Fano of a 10 ms population count is one summary of temporal structure. It does not separate pairwise correlation,
     common rate modulation or bursting. What matters to a given mid neuron is co-firing among **its own** presynaptic LC
     neurons, which was not measured.
  2. Fano is not a sufficient statistic. At noise 0 the SWS–DATA Fano gap is the same size (106.9 vs 78.6, Δ ≈ 28) as at noise 2
     (38.9 vs 11.3, Δ ≈ 28), but the DNa02 deficit is −2.7 Hz instead of −17.4.
  3. The relative 6–14 Hz power of the LC count is **lower** in SWS and B1 (0.41) than in DATA (0.53). The shuffled networks are
     more variable, but not more oscillatory in that band, so "oscillation" wording is not supported. (The v4.1 phrase "~3× more
     6–14 Hz power" refers to absolute power, which follows the variance.)
  4. At the mid stage, the timing-free mid→DNa02 drive falls by 12–13 % in B1 while the DNa02 rate falls by 24 %. Mid rate loss
     covers about half of the deficit. The rest is DNa02 nonlinearity and/or mid synchrony, which this design cannot tell apart.
  5. B2 raises mid Fano (12.6 vs 9.3 in all 50 instances) while leaving LC Fano unchanged, but its deficit is only −1.8 Hz. The
     claim "LC Fano at DATA level for B2–B4" is true, but mid synchrony is not at DATA level in B2.
- **What a causal test needs.**
  - Record all LC10a spike times (1 ms) from DATA and B1 under common noise.
  - Replay them as fixed spike sources into the DATA downstream network, with the mid→LC feedback cut (it is under 1 % of LC input).
  - Validation: DATA's own trains must reproduce DATA's DNa02 rate within noise.
  - Conditions:
    - (i) B1 trains, which should reproduce B1's DNa02 rate;
    - (ii) B1 trains with independent per-neuron jitter (±2, 5, 10, 20, 50 ms) or per-neuron circular shifts, which keep each
      neuron's rate and ISIs but remove cross-neuron synchrony;
    - (iii) DATA trains with synchrony injected, for example by reassigning spike identities within bins so that B1's population
      count profile is imposed at fixed per-neuron rates;
    - (iv) rate-matched Poisson trains.
  - Mediation is supported if DNa02 moves monotonically with the induced synchrony and both directions follow one dose–response
    curve. Then repeat the test with Fano replaced by synchrony among each mid neuron's own presynaptic LC neurons.
  - Cost: a wrapper around the frozen engine plus minutes of CPU.

## (c) Is the open-loop deficit relevant to closed loop?
**Not shown.** The −16 to −17 Hz is the ipsilateral DNa02 rate under **unilateral** drive; contralateral DNa02 is 0 in every
network. Near the target both sides are driven, so most of the deficit is common-mode and cancels in L−R (v4.1 §4).
What matters near the target is the small-signal gain G_small (E6) and the dead zone. B1 does reproduce the SWS G_small
profile (I0 7: −15.2 vs −15.7 Hz/mV; I0 10: +22.2 vs +21.4), which supports B1 as the open-loop locus of the L−R gain
difference as well. However, the closed-loop V5 v4 DATA/SWS effect was small (+0.51° in S1, −0.52° in S2) and changed sign.
No closed-loop run with B1 has been analysed yet: V6 family X = B1 is in progress, and its results were not opened for this review.
Until then, no behavioural or closed-loop statement about LC×LC should be made. E6 is also still open loop.

## (d) Does n = 50 per family mean much?
**Mostly no.**
- Between-instance spread is at noise level. For B1 at 6–9 mV, sd_between is 0.31 Hz against 0.96 within control and 1.45
  within DATA, consistent with RT1's ANOVA F ≈ 1. Each family behaves like one network.
- The CI ±0.95 Hz mainly reflects the **shared DATA reference**: one network × 8 noise reps. New check, DATA re-run with fresh
  seeds 8 496 011–026 (16 reps) at the E1 levels 6–9 mV:
  - the two independent 8-seed halves give 68.55 and 66.66 Hz, a 1.9 Hz difference between reference seed sets;
  - the 16-seed mean is 67.60 Hz vs the registered 67.83 Hz;
  - per-level differences between the registered reference and the fresh 16-seed mean reach −4.7 to +3.3 Hz.
- What n = 50 does show: the result is not specific to particular shuffle seeds, and B5 ≈ SWS. Five to ten instances plus 32 or
  more DATA noise reps would have been more informative.
- The 300-instance structure–function correlations are pseudo-replicated (see (a)).

## (e) Statements in the headline that go too far
1. **"Sum of block effects −20.1 (mild non-additivity)."**
   - The sum ΣΔ_B1..B4 − Δ_SWS counts the DATA reference **three extra times**: Σ ctrl − ctrl_SWS − 3·DATA.
   - With DATA reference error of about 1 Hz at the 6–9 mV range (see (d)), that gives about ±3 Hz, so the −2.6 Hz residual is
     within reference noise. analysis.json reports no CI for the additivity check.
   - Per level, the gaps look large (9 mV: Σ −42.6 vs SWS −30.2; 10 mV: −15.6 vs −7.1). This is exactly where B3 and B4 jump
     to −4/−5 Hz together, the signature of a single shared DATA-reference fluctuation, since per-level reference noise reaches several Hz.
   - Better wording: "additivity not resolvable with this design; consistent with additivity within reference noise".
2. **"B2–B4 −0.9 to −1.8 Hz."**
   - B3 and B4 CIs exclude 0 by only 0.02–0.04 Hz, against a 1.9 Hz spread between DATA seed sets. Under the pre-specified rule
     they are "partial / unresolved", not contributions, and should be reported per the rule.
   - B3's noise-0 Δ is +2.2 Hz, the opposite sign. B2's −1.8 Hz is the only one that plausibly differs from 0.
3. **"~94 %."**
   - Correct as the ratio of point estimates at D0, noise 2, trapezoid average over 6–9 mV (plain mean 16.5/17.5).
   - The remaining +1.0 Hz (+0.90; +1.15) is significant, so "B1 ≈ SWS" is wrong and "B1 carries most" is right.
   - The ratio holds for one parameter set only. V6 decides robustness across parameters.
4. **"Reproduces the LC10a population synchrony."** True for this one statistic (MODEL). It shows co-localisation, not
   mediation (see (b)). Do not write "synchrony mediates" or "LC×LC reciprocity/clustering causes".
5. **Implicit attribution to a graph statistic.** The protocol itself says single statistics cannot be isolated. The RP-LC pilot
   shows that reciprocity, the most salient candidate, accounts for at most about 15 %.
6. **Minor.**
   - Amendment A2 quotes mid Fano "4.6 vs 11.1", but analysis.json gives 9.32 vs 22.61 (the ratio is the same). The definition
     should be reconciled in REPORT.md.
   - All results are open-loop MODEL dynamics on one DATA network. Nothing here is a statement about the fly.

## What can be claimed (suggested wording)
"In the ALIF model at D0 (open loop, unilateral step, noise 2 mV), randomising only the LC10a×LC10a block, under all SWS
invariants, reproduces 94 % of the SWS DNa02 deficit at 6–9 mV, the SWS LC10a population Fano factor, and the SWS small-signal
L−R gain profile. Randomising any other single block leaves LC Fano at DATA level, with DNa02 changes of 1.8 Hz or less, two of
which cannot be told apart from reference noise. Because B1 leaves every downstream block intact and the rate-weighted LC→mid drive
changes by 1 % or less, the effect is carried by the temporal structure of LC10a output. Whether population synchrony mediates it,
and which LC×LC graph property produces it, is open: a reciprocity-preserving pilot did not restore DATA-like synchrony.
Relevance to closed-loop behaviour is untested (V6)."
