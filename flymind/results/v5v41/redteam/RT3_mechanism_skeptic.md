# RT3: mechanism skeptic. Is the V5 v4.1 DATA vs SWS difference really "downstream of LC10a"?

Red team, 2026-10-30. Scope: the author's tentative interpretation *"LC10a population rate is equal, intermediates and DNa02
are lower, so the difference is downstream of LC10a and P3 (origin in the LC10a layer via LC×LC recurrence) is falsified."*
Verdict at the end.

## 0. What was done (and not done)
- Stored data only. Inputs: `results/v5v41/raw/*.npz` (`E1_ss`, `E1n0_ss`, `E1_counts`, `E1n0_counts`),
  `results/v5v41/E6/raw/*.npz`, `results/v5v41/E6/analysis_E6.json`, `results/v5v41/analysis.json`, `instances.json`.
- **No new simulation.** No ALIF noise seeds were used. To get each network's own W, I rebuilt the registered objects:
  `visual_path.network(0.2)` (DATA) and `side_shuffle.shuffle_within_side(spec, layer_side_labels(...), s)` for s = 8 410 001–050.
  All 51 `sha256(W_data)` matched `instances.json` (an assert in the script). No other seeds were touched. No MuJoCo, no bio2.
- I did **not** read any V5 v4.2 result files, so this report cannot contaminate v4.2's pre-specified analysis.
- Scripts (scratchpad, read-only use of the project):
  `/private/tmp/claude-501/-Users-admin-so101-fly-project/075990a2-3231-4039-8d41-31f3fdcb9204/scratchpad/rt41/RT3/mech.py`,
  `.../rt41/RT3/mech2.py`, `.../rt41/RT3/mech3.py`. Outputs are in the same folder: `mech.json`, `mech2.json`, `mech3.json`.
- Window: E1 steady state (500–1000 ms). Per-neuron rate = `E1_ss / (reps · 0.5 s)`. Levels 7.0–9.0 mV (17 levels).
  Metrics are computed per level and per driven side, then averaged. "z" = (SWS mean − DATA) / between-instance SD.
- Units. Mean synaptic input is in mV: u = τ_syn · W · r, with τ_syn = 5 ms. The "DN-weighted" indices Σ_m W[DN,m]·u_m are in
  arbitrary units, so I compare them only between networks.

## 1. A structural fact that frames everything (CONTROL, by construction)
SWS v2 keeps, for every neuron, the multiset of (partner group, signed weight) of its inputs and of its outputs
(`side_shuffle.properties`). Two consequences:
- If every ipsi LC10a neuron fired at the same rate, every intermediate would get exactly the same mean LC input in DATA and
  in SWS. The mid→DNa02 weights cannot change either (1-neuron groups).
- So a **rate-based feedforward** account of the 18–22 Hz DNa02 deficit needs one of two things: within-group LC rate
  heterogeneity that lines up with the wiring, or within-group heterogeneity at the mid layer (mid×mid). Otherwise the
  difference has to sit in **temporal structure** (synchrony or correlations), which equal mean rates do not reveal.

The author's inference "LC mean rate equal ⇒ LC layer equal" therefore uses the one statistic that SWS is built to leave
nearly unchanged.

## 2. (a) Per-neuron LC10a rate distribution, 7–9 mV, noise 2 mV (E1)
| metric (ipsi) | DATA | SWS mean (SD; min–max) | z | SWS ≥ DATA |
|---|---|---|---|---|
| DNa02 ipsi [Hz] | 86.1 | 64.4 (0.39; 63.6–65.3) | −55 | 0/50 |
| LC10a mean [Hz] | 13.23 | 13.26 (0.037) | +0.9 | 39/50 |
| LC10a SD across neurons [Hz] | 1.194 | 1.036 (0.012; 1.008–1.061) | −13.5 | 0/50 |
| LC10a Gini | 0.0511 | 0.0448 (0.0005) | −12.8 | 0/50 |
| LC10a max [Hz] | 16.58 | 16.25 (0.07) | −4.8 | 0/50 |
| LC10a pop. Fano (10 ms bins) | **11.3** | **38.9** (0.31; 38.2–39.8) | +89 | 50/50 |
| mid ipsi mean [Hz] | 13.16 | 11.76 (0.06) | −23 | 0/50 |
| mid ipsi max [Hz] | 133.4 | 105.7 (0.47) | −59 | 0/50 |
| mid ipsi pop. Fano | 9.3 | 22.6 (0.12) | +111 | 50/50 |

Findings:
- The **per-neuron LC distribution differs**, beyond the between-instance spread and in all 50 instances. DATA is more
  heterogeneous (SD +15 %, Gini +14 %, higher top tail). The size is small in absolute terms (about 0.16 Hz of SD).
- The much larger difference is **temporal**. With equal mean rates, the LC10a population is about 3.5× more synchronous in
  SWS (Fano of the 10-ms population count is 38.9 vs 11.3). The steady-state population spectrum peaks at about 12 Hz (DATA)
  vs 14 Hz (SWS), and SWS has about 3× the power at 6–14 Hz. LC10a fires about 13 Hz, so this looks like population volleys
  near one spike per cycle. They are stronger and more phase-locked in SWS.
- Level dependence (E1, Fano LC DATA / SWS → DNa02 DATA / SWS):
  6.25 mV 15/41 → 22/16 Hz; 7 mV 17/50 → 48/38; 8 mV 12/40 → 84/61; 9 mV 6.5/24 → 127/97; 10 mV 3.5/6.6 → 163/156;
  10.25 mV 3.1/4.2 → 163/169 (sign flip); ≥ 10.75 mV the Fano values are equal (≈ 2 → 1) and so is DNa02. The synchrony gap and
  the DNa02 deficit appear and disappear over the **same input range**, including the sign reversal of ΔDN near 10.25 mV.
- Identity: per-neuron LC rate ranks agree well between DATA and SWS (Spearman 0.87, range 0.85–0.88; mid 0.99). Common random
  numbers give every neuron index the same noise sequence in all networks, which inflates this agreement. It does not show
  that "the same LC neurons fire for structural reasons".

Answer to (a): **yes.** The LC10a layer is not equal in DATA and SWS. Its mean rate is equal. Its rate heterogeneity differs a
little and its population synchrony differs a lot. "Equal LC rate" is true only for the population mean.

## 3. (b) Alignment of LC activity with output pathways
For each ipsi LC neuron, g_LC = Σ_mid W[DN_ipsi, mid] · W[mid, LC] is its 2-hop weight onto ipsi DNa02, computed with each
network's own W. The alignment index is A2 = τ² Σ_LC r_LC g_LC = N·(r̄·ḡ + cov(r, g)). The mean ḡ is identical in all
networks (preserved by construction). Only cov(r, g) can carry an effect.

| (7–9 mV, noise 2) | DATA | SWS mean (SD) | SWS ≥ DATA |
|---|---|---|---|
| Spearman(r_LC, g_LC) | **+0.26** | −0.04 (0.024) | 0/50 |
| cov term (a.u.) | +0.43 | −0.07 (0.03) | 0/50 |
| A2 total (a.u.) | 26.25 | 25.81 (0.07); ΔA2 = −1.7 % | 0/50 |
| SWS wiring with DATA LC rates | — | 26.06; below DATA in 50/50 | |
| DATA wiring with SWS LC rates | — | 25.88 | |
| DN-weighted mid input from mid×mid (a.u.) | +0.09 | −0.43 (0.07) | 0/50 |
| network input to DNa02 ipsi from mid ipsi [mV] | 54.0 | 46.8 (0.27); −13 % | 0/50 |

- **An alignment exists in DATA and SWS destroys it.** In DATA, the more active LC10a neurons project, through intermediates, a
  little more onto ipsi DNa02 (ρ 0.26 vs −0.04, all 50 instances lower). Both parts of the decomposition contribute: SWS
  wiring alone (with DATA rates) and the changed LC pattern each lower A2.
- **It is small and inconsistent by side.** In linear rate terms, the alignment loss is −1.7 % of DN-weighted LC input, while the
  actual mid→DNa02 drive falls 13 % and the DNa02 rate falls 25 %. The mid×mid contribution to the DN-weighted input changes by
  a similar amount (−0.52 a.u., vs −0.44 for the LC route). The top-decile check splits by side. On the R side the most active
  10 % of LC10a have above-average g (701 vs 580). On the L side they have below-average g (533 vs 554).
- **At noise 0 the alignment explains nothing.** ΔA2 = +0.07 (SWS ≥ DATA in 29/50), yet ΔDNa02 is still −4.0 Hz (7–9 mV) and
  mid→DN drive is −1.8 mV.
- **The rate-based account fails at the neurons that matter.** Four intermediates carry about half of the ipsi DNa02 drive:
  404 and 418 (L side), 412 and 279 (R side). For each, I took the change in mean input (from each network's rates and W) and
  multiplied it by that mid's f–I slope in DATA (estimated across levels):

  | mid | DATA [Hz] | SWS [Hz] | Δ mean input [mV] (LC / mid) | rate-predicted Δ [Hz] |
  |---|---|---|---|---|
  | 404 (L) | 79.0 | 64.0 | −0.82 / −0.39 | −2.2 |
  | 418 (L) | 54.1 | 45.1 | **+0.64** / +0.10 | **+1.5** |
  | 412 (R) | 89.5 | 73.8 | −2.11 / −0.18 | −3.9 |
  | 279 (R) | 64.2 | 54.4 | **+0.83** / +0.02 | **+1.7** |

  The actual losses are 9–16 Hz. Mean-input changes predict at most about a quarter of that, and for two of the four
  neurons they predict the wrong sign. Across ipsi intermediates, the rate change is anti-correlated with the DATA rate
  (Spearman −0.67 L, −0.70 R): the most active intermediates lose the most. That pattern fits input that arrives in
  synchronous volleys, which wastes drive on strongly driven neurons through refractoriness and adaptation. It does not fit a
  shift in mean input.
- The author's "dDN vs dLC Spearman 0.59" describes the between-instance scatter only (SD 0.34 Hz around −17.4; dLC ±0.06 Hz).
  The A2 index gives the same ρ (0.58), because A2 is dominated by r̄. It says nothing about the 18 Hz offset. Across instances,
  LC Fano also correlates with dDN (ρ −0.43: more synchrony, larger deficit). This is unadjusted for dLC and only descriptive.

Answer to (b): DATA has a measurable LC-activity/output-pathway alignment that SWS breaks. As a linear feedforward mechanism it
is **too small to explain ΔDNa02**, it is side-inconsistent at the top decile, and it is absent at noise 0. It may still
contribute; v4.2 B2 tests that.

## 4. (c) Relevance of an 18 Hz unilateral difference to the closed loop
- The unilateral deficit is mostly a **common-mode** level change. At the symmetric point (E6, δ = 0) mean DNa02 is also lower
  in SWS: 38.4 vs 29.7 Hz at 7 mV, 50.0 vs 44.1 at 8 mV, 65.4 vs 58.2 at 9 mV. A common-mode change cancels in D = L − R.
- What the loop sees near the target is the differential gain G(I0) and the dead-zone edge:

  | I0 [mV] | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
  |---|---|---|---|---|---|---|---|---|
  | G_small DATA / SWS [Hz/mV] | 0/0 | 0/0 | 33/27 | 37/21 | 39/32 | 48/43 | 44/65 | 36/38 |
  | in °/mV (common decoder) | 0/0 | 0/0 | 3.9/3.1 | 4.3/2.5 | 4.6/3.8 | 5.6/5.1 | 5.1/7.6 | 4.2/4.4 |
  | both DN silent, fraction DATA / SWS | 1/1 | 0.82/0.94 | 0.02/0.11 | 0 | 0 | 0 | 0 | 0 |
  | LC Fano at δ = 0, DATA / SWS | – | – | 6.9/5.0 | 17/49 | 11/40 | 6.4/25 | 3.7/6.6 | 1.6/1.6 |

- So the open-loop difference **does carry over to the differential channel** at 6–9 mV (DATA up to 1.7× more sensitive at
  7 mV) and **reverses at 10 mV**. That reversal is the same regime-dependent pattern seen in E1, and the synchrony gap tracks
  it again. At 4–5 mV, which amendment A1 names as the near-target regime, **both networks sit in the dead zone**. There the
  question "which is more sensitive" has no answer; the threshold is what matters, and thresholds are nearly equal
  (I_th10 5.99 vs 6.09).
- The V5 v4 closed-loop differences were ±0.5°, with the sign depending on regime. A 1.7× open-loop gain difference therefore
  did not become a large behavioural difference, which suggests the loop's feedback absorbs gain changes. The open-loop
  18 Hz is a valid **model property** (MODEL × CONTROL). It is **not** evidence of behavioural relevance, and should not be
  presented as such.
- Aside, relevant to the loop: both families have a rightward symmetric-point bias D(δ = 0) < 0, and it is larger in DATA at
  8–9 mV (−17/−28 vs −10/−17 Hz, i.e. about −3.2° vs −2.0° at 9 mV; CI excludes 0 only at 9 mV). This reflects DATA's L/R
  asymmetry (LC 135/140, mid 58/89). In closed loop it would bias the steady state more than the gain difference does.

## 5. (d) Alternative explanations
| hypothesis | evidence in stored data | status |
|---|---|---|
| H1 Synchrony / collective dynamics in the LC layer (SWS breaks LC×LC structure → stronger population volleys → strongly driven intermediates and DNa02 saturate per volley) | Fano 3.5× in all 50 instances; same input range as ΔDN including the 10.25 mV reversal; also at the E6 symmetric point; most active mids lose most; rate-based account fails on top mids; across instances ρ(Fano, dDN) = −0.43 | **Best-supported hypothesis**; correlational only. Population count Fano cannot separate pairwise correlation from oscillation, and per-neuron spike times are not stored. |
| H2 Feedforward alignment (LC heterogeneity × LC→mid re-pairing) | ρ(r, g) 0.26 vs −0.04 (real), but ΔA2 only −1.7 %, side-inconsistent, null at noise 0 | Real but **insufficient** as the main cause. Possible minor contributor. |
| H3 mid→LC feedback | mean feedback to LC 0.010 mV vs LC×LC 1.23 mV (< 1 %); it does change (−11 %), but as a consequence of lower mid rates | **Implausible as the primary cause**. Could still pace timing; B3 tests it. |
| H4 mid×mid recurrence | DN-weighted mid×mid input change (−0.52) is as large as the LC route (−0.44); several top mids lose mid-sourced input (e.g. 298: −1.26 mV) | **Open**, comparable in linear size to H2. B4 tests it. |
| H5 Noise × structure interaction | noise 0: ΔDN −4.0 Hz (7–9 mV) vs −21.7 at 2 mV; Fano DATA 79 → 11 when noise is added, SWS 107 → 39. Independent noise desynchronises DATA much more than SWS | **Supported as a modifier.** It fits H1: DATA's structure makes the LC population easier to desynchronise. Not separable from H1 here. |
| "Downstream origin" (author) | LC per-neuron distribution and LC temporal structure differ; the per-mid changes are not explained by mean input | **Not supported.** The pre-written rule in Protocol §5 ("identical LC10a rates ⇒ downstream") was applied to the population mean only. The protocol stored per-neuron rates and population time courses, and those already differ at the LC layer. |

## 6. What v4.2 must show to tell these apart
(v4.2 protocol r1 is already registered; the items below are things to check within it or to add as a dated exploratory
amendment **before** its results are opened.)
1. **Add the synchrony mediator.** For every family, compute LC10a ipsi and mid ipsi population Fano (10 ms bins, 500–1000 ms)
   and the 6–14 Hz power of the population count from the stored `E1_counts` (no new runs needed). Report it together with
   ΔDNa02 per family, per level.
2. **Discrimination table (E1, 6–9 mV, noise 2):**
   - H1 (LC×LC-generated synchrony): B1 reproduces ΔDNa02 (same sign, CI overlapping SWS) **and** raises LC Fano to about the
     SWS level. B2, B3 and B4 leave LC Fano at the DATA level. Within B1, ΔDN tracks ΔFano. At noise 0 (E1n0), B1's ΔDN
     shrinks the way SWS's does.
   - H2 (feedforward alignment): B2 reproduces ΔDNa02 while LC Fano and the LC Gini stay at DATA values. ρ(r_LC, g_LC) drops
     to about 0 in B2 but not in B1. B1 is null.
   - H3: B3 reproduces (prior low: 0.6 % of |w|).
   - H4: B4 reproduces, LC Fano unchanged, mid Fano and mid max changed.
   - Interaction: Σ_B1..B4 Δ ≠ Δ_SWS. In particular, B1 + B2 could be needed together if synchronous volleys only hurt when they
     land on the DN-projecting mids (H1 × H2).
3. **B1 confound.** B1 changes LC×LC reciprocity, triangles and clustering together. A positive B1 locates the effect in the
   block, not in any single graph statistic.
4. **Recommended causal test (v4.3, not v4.2).** v4.1 does not store per-neuron LC spike trains. Record the ipsi LC10a
   spike rasters, then replay them as fixed input to the downstream network (mid + DNa02, LC×LC removed) in four crosses:
   DATA rasters into DATA wiring, DATA rasters into SWS wiring, SWS rasters into DATA wiring, SWS rasters into SWS wiring.
   Add a fifth condition: DATA rasters with spike times jittered or circularly shifted per neuron (rates kept, synchrony
   destroyed). H1 predicts that the raster origin decides ΔDN and that jitter removes it. H2 predicts that the wiring decides
   it. This needs new runs, so it needs a registered seed pool and a protocol.
5. **Loop relevance (c).** Any mechanism claim should be checked against G_small(I0) in E6 and the dead-zone edge, not only
   the unilateral steady state. A mechanism that explains the E1 deficit should also explain the G reversal at 10 mV.

## 7. Limitations of this red-team analysis
- Population Fano and spectra come from 10-ms counts over 0.5 s (2 Hz resolution). Without spike times there are no pairwise
  correlations, phase-locking or spike-triggered measures.
- Mean-input calculations are rate-based and time-averaged. They ignore delays, fluctuations and nonlinearity, which is
  exactly why they fail; the failure is evidence against a mean-rate mechanism, not a measurement of the alternative.
  The f–I slopes are estimated across levels in DATA, where synchrony also varies.
- Common random numbers inflate per-neuron identity agreement between networks.
- All statements are correlational. Synchrony could be a co-effect of the same rewiring rather than the cause of the mid
  and DNa02 losses.
- Labels: the network edges are DATA; ALIF, J0, noise and τ_syn are MODEL; the mV range is ENGINEERING; SWS, the common decoder
  and CRN are CONTROL. Results concern this model, not the fly.

## 8. Verdict
**FAIL** for the mechanistic interpretation as worded ("difference downstream of LC10a; P3 falsified"). The stored data show
that the LC10a layer differs between DATA and SWS:
- per-neuron heterogeneity: z ≈ −13, all 50 instances below DATA;
- population synchrony: 3.5×, all 50 instances above DATA, with the same level dependence as ΔDNa02.

The rate-based "downstream" account also fails for the intermediates that carry about half of DNa02's drive. The descriptive
E1/E6 numbers this interpretation rests on are not in question; I reproduce ΔDNa02 and the equal LC mean.

Suggested replacement wording: *"LC10a mean rate is unchanged, but LC10a population synchrony is about 3.5× higher and rate
heterogeneity slightly lower in SWS. The locus (LC×LC-driven synchrony vs feedforward re-pairing vs mid×mid) is unresolved and
deferred to V5 v4.2 (B1–B4) plus a raster-replay test. P3 is neither confirmed nor falsified."*
