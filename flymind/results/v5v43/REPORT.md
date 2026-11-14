# V5 v4.3 — LC10a spike-train replay: report (2026-10-30)

**Status: exploratory, completed. Verdict: PASS_WITH_LIMITATIONS (red team §5; wording corrected).**

## 1. Question and design
Protocol `program_v5v41/V5v43_PROTOCOL.md` (sha 5de36553…, written before any v4.3 simulation). V5 v4.2 located most of the open-loop
DATA vs SWS difference in the LC10a×LC10a block (B1) and found it co-localised with LC10a population synchrony while mean LC10a rates
and rate-weighted LC→intermediate drive were unchanged. Here the timing of LC10a spikes is manipulated directly: LC10a trains recorded
from DATA and from 10 B1 instances (E1 drive 7/8/9 mV, both sides, 8 noise reps) are replayed into the DATA network with all 275
LC10a neurons clamped (their recurrence and membrane ignored). B1's downstream wiring is identical to DATA's, so the replay isolates
"which LC10a spike trains arrive" from everything else. Manipulations only in 300–1000 ms, measured 500–1000 ms.

Validation (protocol §4): identity replay reproduces the free source run spike-for-spike for DATA and all 10 B1 instances
(intermediates and DNa02 exactly; `test_v5v43.py` and `analysis.json.validation`). Stage 1 28/28 after the run.

## 2. Results (DNa02 ipsi steady state, mean over 3 levels × 2 sides; gap = B1 trains − DATA trains; CI95 bootstrap over
instances × reps and DATA reps)
| Variant | DN (DATA trains) | DN (B1 trains) | Gap [Hz] | CI95 | Gap / Gap(V0) | LC10a Fano DATA / B1 |
|---|---|---|---|---|---|---|
| V0 identity | 86.5 | 66.6 | **−19.9** | −21.8; −17.9 | 1.00 | 11.8 / 37.7 |
| jitter ±1 ms | 86.3 | 66.9 | −19.4 | −21.5; −17.2 | 0.97 | 11.7 / 37.1 |
| jitter ±2 ms | 86.3 | 67.4 | −18.9 | −21.0; −16.8 | 0.95 | 11.7 / 36.1 |
| jitter ±5 ms | 87.8 | 69.6 | −18.2 | −20.3; −16.0 | 0.91 | 10.9 / 31.3 |
| jitter ±10 ms | 90.1 | 74.8 | −15.3 | −17.2; −13.3 | 0.77 | 9.0 / 22.7 |
| jitter ±20 ms | 98.7 | 89.3 | −9.3 | −10.7; −8.0 | 0.47 | 6.0 / 11.9 |
| circular shift per neuron | 105.8 | 104.0 | **−1.7** | −2.9; −0.6 | 0.09 | 0.8 / 0.9 |
| rate-matched Bernoulli | 104.0 | 101.9 | **−2.1** | −5.4; +1.2 | 0.10 | 0.9 / 0.9 |
Per level (gap V0 → circular): 7 mV −8.7 → +1.4; 8 mV −21.2 → −5.2 (residual 25 %); 9 mV −29.8 → −1.4. Spike counts are preserved
(jitter collisions ≤ 0.1 %; Bernoulli −0.8 %).

## 3. Interpretation
- Pre-registered rule: Gap(CIRC) and Gap(POIS) ≤ 25 % of Gap(V0) → **timing route supported**. In this model, the LC10a×LC10a wiring
  changes the DNa02 response mainly through the temporal (cross-neuron) structure of LC10a spike trains, not through their rates.
- Red-team controls (RT1, seeds 8 497 xxx): (i) one circular shift COMMON to all LC10a (same 300 ms cut, alignment kept) leaves the
  gap at −21.0 Hz and DATA at 86.9 Hz → the window discontinuity is not the cause; (ii) permuting/swapping whole trains among LC10a of
  the same side (population count time course kept exactly) does NOT shrink the gap (−24.6 / −25.4 Hz) → what matters is population
  co-firing (the summed LC10a volley timing), not neuron-specific spike patterns; (iii) replication with new seeds: V0 −20.5, CIRC −1.8 Hz.
- Robustness: the ≤ 25 % rule holds pooled and at each level, but fails for 8 mV left side under CIRC (31 %); at 7 mV CIRC/POIS flip
  the sign slightly (+0.7…+2.2 Hz, V0 gap only ~9 Hz); the jitter dose-response is monotonic on average, not in every cell; all 10
  B1 instances shrink individually (−18…−22 → −0.4…−2.9 Hz).
- Direction: removing cross-neuron alignment RAISES DNa02 for both sources (DATA +19 Hz, B1 +37 Hz); the more synchronous B1 trains
  are the less effective. Descriptively: synchronous LC10a volleys drive DNa02 less than asynchronous input of the same rate. The
  data-derived LC×LC wiring yields less synchronous LC10a activity than the shuffled wiring and therefore a larger DNa02 response.
  DATA's own synchrony also suppresses DNa02 by ~20 Hz relative to
  asynchronous input. Why synchronous input is less effective is a candidate mechanism only: mean intermediate rate does not explain it
  (under CIRC DATA's intermediate rate FALLS 13.4 → 12.2 Hz while DNa02 RISES 87 → 105 Hz); synchrony propagates to intermediates (Fano
  9 vs 22.5) and DNa02 then has 42 % of ISIs at the refractory floor (≤ 4 ms) with B1 trains vs 20 % with DATA and 1 % under CIRC →
  refractory/reset saturation during volleys is the leading candidate; adaptation and the intermediate layer were not separated
  (test: clamp intermediates or set t_ref → 0).
- Residual: ~10 % overall (25 % at 8 mV; CIRC CI excludes 0, POIS CI includes 0) — a small, unattributed residual (untouched 0–300 ms
  onset with τ_a 300 ms, small LC count differences, −0.2 Hz intermediate gap — not separable).
- The V0 gap (−19.9 Hz at 7–9 mV from rest) is not the same number as v4.2's −16.4 Hz (6–9 mV): different level sets.
- Scope: MODEL dynamics (ALIF, J0 0.2, b_a 0.5, σ 2) on DATA structure, unilateral drive, open loop. No claim about the fly, and
  "causal" means: within this simulated network, manipulating only spike timing removes the difference.

## 4. Files
`v5v43.py`, `test_v5v43.py`, `v5v43_analysis.py`; `results/v5v43/` (config.json, raw/11 npz, analysis.json, run_done.json).

## 5. Red team
`redteam/RT1_replay_redteam.md` (separate model instance): engine identical to alif.ALIF.step line by line; manipulations correct
(POIS violates refractoriness in ~2.6 % of spikes — irrelevant, CIRC agrees); controls and replication above; wording fixes applied.
Verdict PASS_WITH_LIMITATIONS. The bootstrap ignores shared noise seeds between DATA and B1 (conservative).
