# RT1 — red team of V5 v4.3 (LC10a spike-train replay), 2026-10-30

Scope: protocol `program_v5v41/V5v43_PROTOCOL.md`, `v5v43.py`, `test_v5v43.py`, `v5v43_analysis.py`, `results/v5v43/` (raw, analysis.json).
Read-only; helper scripts in the session scratchpad `rt43/` (struct.py, perside.py, ctrl.py; ctrl output ctrl_out.npy / ctrl_stdout.txt).
New simulations: noise seeds 8 497 001–004, manipulation RNG 8 497 100 + 10·variant + rep; DATA + B1 8 421 001–005; 7/8/9 mV, L/R;
single core, ~95 s.

**Verdict: PASS_WITH_LIMITATIONS.** The replay is exact, the result replicates with fresh seeds, the two obvious artifacts
(discontinuity at 300 ms, broken within-neuron structure) are excluded, and an extra control shows that the
**population count time course** (not which neuron fires which train) carries the gap. The mechanism *below* "synchrony" is not
isolated, the per-cell rule is violated once, and some wording needs tightening.

## 1. Engine identity
- `step_clamped` (v5v43.py:31–47) vs `ALIF.step` (alif.py:70–84), line by line: identical (same order of g update, noise draw of all
  N neurons, v update, refractory clamp, threshold, reset, ref, adaptation, buffer, t). The only addition is `spk[cidx] = forced`
  after thresholding, so the RNG stream and every non-LC update are unchanged. Clamped LC10a keep their own v/a/ref, but these only
  act through `spk`, so they are dead state. Same defaults (`gain=1`, `b_a=0.5`) in source and replay.
- `test_v5v43.py` run: OK (DATA and B1 identity replay exact, all 424 neurons). analysis.json validation true for all 11 sources;
  my rerun asserts V0 == free run for DN and mids in all 144 new runs.
- B1 V0 replay into the DATA network equals the free B1 run exactly, which shows B1's downstream wiring is functionally DATA's.
- Minor: clamping also cuts the small non-LC→LC feedback (|W| sum 127 vs 5049 for LC×LC). Under manipulation, the LC trains
  cannot react to downstream changes (open loop at LC). This does not matter for the conclusion.

## 2. Manipulations
- Jitter: the reflection at both window edges is correct (t<0 → −t; t≥L → 2(L−1)−t). Collision losses are ≤0.15 % (J20).
  Jitter can create ISIs shorter than the refractory period; this is negligible at ~13 Hz.
- CIRC keeps the exact counts and ISIs, but it also flattens the slow rate trend inside 300–1000 ms. As a result, the LC ipsi spikes in
  500–1000 change by about 1–2 % (DATA 907→898, B1 914→895). The shift is small and goes the same way for both sources.
- POIS refractory violation: P(ISI<3 ms) is about 2.6 % at 13 Hz. This does not matter, because CIRC keeps the ISIs exactly and gives the same answer.
- **Discontinuity/adaptation-mismatch artifact excluded:** CIRC_COMMON (one offset shared by all 275 LC10a). It has the same per-neuron
  cut at 300 ms and the same wrap, but keeps cross-neuron alignment. Result: gap −21.0 Hz (V0 −20.5), DATA DN 86.9 (V0 87.2). The DN rise
  under CIRC therefore comes from desynchronization, not from the cut.
- Onset 0–300 ms is the same for all variants within a source, so it cannot produce the gap *shrinkage*. It may contribute to the
  residual (§5).

## 3. Per level / per side (author data)
CIRC fraction of the V0 gap: 7 mV L −0.08, R −0.25; 8 mV L **+0.31**, R +0.17; 9 mV L +0.04, R +0.06. POIS: −0.21…+0.18.
The protocol rule (≤25 %) holds pooled and at every level, but **fails for 8 mV L under CIRC**. Please report this.
All 10 B1 instances shrink individually (V0 −18.2…−21.8 → CIRC −0.4…−2.9).
The jitter dose-response is monotonic in the pooled data and at 9 mV, but not in every cell (7 mV R: J5 −9.2 and J10 −9.6 vs V0 −8.8).
Write "monotonic on average".
At 7 mV, CIRC/POIS reverse the sign (+0.7…+2.2 Hz). The V0 gap there is only about 9 Hz.

## 4. Extra control (requested) and mechanism
| variant (fresh seeds, 5 B1 × 4 reps) | DN DATA / B1 [Hz] | gap | LC Fano D/B | mid Fano D/B | DN ISI≤4 ms D/B |
|---|---|---|---|---|---|
| V0 | 87.2 / 66.8 | −20.5 | 10.2 / 36.9 | 9.0 / 22.5 | 0.20 / 0.42 |
| CIRC (replication) | 105.4 / 103.7 | −1.8 | 0.8 / 0.9 | 2.0 / 1.9 | 0.01 / 0.01 |
| CIRC_COMMON | 86.9 / 65.9 | −21.0 | 10.5 / 36.3 | 9.3 / 22.1 | 0.21 / 0.40 |
| SWAP_RATE (permute within side among rate-sorted groups of 4) | 91.3 / 66.8 | −24.6 | 10.2 / 36.9 | 10.4 / 22.5 | 0.14 / 0.41 |
| PERM_SIDE (full permutation within side) | 91.8 / 66.5 | −25.4 | 10.2 / 36.9 | 10.2 / 22.4 | 0.10 / 0.41 |

SWAP_RATE and PERM_SIDE keep each side's population count time course exactly. Neuron-to-target assignment is scrambled.
The gap does **not** shrink: it grows by about 20 %, because DATA gains about 4 Hz while B1 is unchanged.
So within this model, the operative variable is population-level co-firing (the summed count time course), not neuron-specific spike patterns.
This supports the author's reading and sharpens it.

Mechanism (Q4): DNa02 receives **no direct LC10a input**. All of it arrives via the mids (mid→DN weights up to 43.6, so one spike is
nearly suprathreshold). Mean mid rate does *not* explain DN: under CIRC, DATA's mid rate falls (13.4→12.2) while DN rises
(87→105). LC synchrony propagates to the mids (mid Fano 9→22.5 for B1). DN then spends 42 % of its ISIs at the refractory floor
(≤4 ms, r_max 250 Hz) vs 20 % for DATA and 1 % under CIRC. The most likely loss is therefore refractory/reset saturation of DNa02
(and possibly of the mids) during volleys. This is consistent, but **not isolated**: adaptation (τ_a 300 ms, b_a 0.5) and the
mid-layer nonlinearity were not dissected. A test would be: clamp mids to V0 vs CIRC trains with DN free, and/or set t_ref→0.
Until then, "synchronous volleys are less effective" is an **input–output description plus a candidate mechanism**, not a demonstrated mechanism.

## 5. Residual ~10 %
CIRC −1.7 Hz (CI −2.9; −0.6, excludes 0); POIS −2.1 (CI includes 0); replication −1.8.
Candidates, not separated:
- the untouched 0–300 ms onset, which carries state into 500–1000 with τ_a 300 ms;
- small LC count/rate differences (V0 B1 +8 spikes; CIRC −3);
- the mid-rate gap (−0.2 Hz).

Say "small, unattributed residual". Do not treat it as a rate route.

## 6. Wording
- OK: "in this model, the LC×LC effect on DNa02 travels through LC10a population co-firing (timing), not through mean rates".
  Replay is a genuine intervention, but it is causal *within the model* only.
- Over-reach to avoid:
  - any statement about the fly;
  - "synchrony is less effective" as a mechanism, without §4's caveat;
  - "monotonic" without "on average";
  - "reproduces the −19.9 Hz gap" as if it were v4.2's −16.4 Hz. Different levels (7–9 vs 6–9 mV) and start from rest; the V0
    replay reproduces *its own* free runs exactly, which is the claim to state.
- The DN increase under desynchronization is ~+20 Hz for DATA too. DATA's own synchrony also suppresses DN, which the report should state.
- Bootstrap resamples DATA reps independently, although DATA and B1 share noise seeds (pairing unused). This is conservative and fine.
- The verdict rests on one parameter set and is open loop.
