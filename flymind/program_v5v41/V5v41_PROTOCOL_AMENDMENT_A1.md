# V5 v4.1 — protocol amendment A1 (2026-10-30 ~09:00), written while the main run was in progress and BEFORE any of its results
were inspected (only instances.json — the network checks — had been read).

Reason (recon audit, `results/v5v41/recon/A_code_vs_protocol.md`, verified by me): the shared DATA decoder (V5 v4) is calibrated with
spot images that drive the ipsilateral LC10a at 11.6–11.9 mV (encoder near saturation) while the contralateral side drops from
10.9 to 2.5 mV; near the target in the closed loop both sides are driven weakly and almost equally (≈ 4–7 mV). Schedules E1–E5 drive
one side (or a fixed 0.5 ratio) and therefore do not measure the small-signal L−R gain around a symmetric operating point, which
is what the loop sees close to the target.

Added experiment (exploratory, same 51 networks, same noise seeds 8 411 001–008, same analysis principles as §5):
- E6 SYMMETRIC OPERATING POINT ± ASYMMETRY: I_L = I0 + δ/2, I_R = I0 − δ/2, 1000 ms from rest;
  I0 ∈ {4, 5, 6, 7, 8, 9, 10, 11} mV, δ ∈ {−2, −1, −0.5, 0, +0.5, +1, +2} mV; 8 reps.
  Measures: steady-state D = DNa02_L − DNa02_R [Hz] and decoded angle (common DATA decoder) vs δ; small-signal gain
  G(I0) = OLS slope of rep-mean D on δ over |δ| ≤ 1 mV [Hz/mV] and over all δ; symmetric-point bias D(δ = 0); "dead zone" =
  fraction of δ with both DNa02 silent. Comparison DATA vs 50 SWS as in §5 (hierarchical bootstrap, RNG 8 419 003).
Prediction (written now): G is small or zero below ~6 mV for all networks (dead zone); DATA vs SWS differences in G are of
the same sign as the E1 steady-state difference at the same I0.
Outputs: `results/v5v41/E6/`. Runner `flymind/v5v41_e6.py` (imports v5v41.simulate unchanged).
