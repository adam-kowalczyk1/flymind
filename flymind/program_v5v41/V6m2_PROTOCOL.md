# V6m2 — DNa02-only factorial: does DNa02 refractoriness make synchronous intermediate input harmful? (EXPLORATORY, pre-registered)
Protocol r1, 2026-10-30 ~15:35; r2 ~15:45 (MASYNC sampler, see §1). Written after the V6m results and the V6m red team (RT-A…RT-D), before any V6m2 simulation.
MODEL-level computational ablations only (ALIF; DATA downstream wiring); no biological manipulation, no claim about Drosophila.
Outputs `results/v6m2/` (new, isolated).

## 0. Why
V6m (single-factor) left the role of DNa02 refractoriness metric- and parameter-dependent: E1c (DNa02 t_ref 0, intermediates clamped)
removes 21 % of the absolute gap but 59 % of the relative gap; at b_a 1.0 it removes 76 % (RT-C), at J0 0.25 it enlarges the gap. Two
red-team factorials (exploratory, small, post hoc) found that with DNa02 t_ref 0, destroying intermediate cross-neuron alignment ENLARGES
the B1 − DATA gap, whereas under REF it shrinks it (interaction +11.1 Hz, RT-B; +14.4 Hz, RT-D), and that removing the membrane leak alone
does not change the timing share (RT-D). Hypothesis to test (and try to falsify), H-RS: *DNa02's refractory block is what makes
synchronous intermediate input less effective than the same spikes spread in time (a per-volley cap); without it, synchrony is neutral
or beneficial.* Competing accounts: operating-point shift (t_ref 0 doubles DNa02's rate), leak/integration loss, intermediate count
differences alone (count route).

## 1. Design (DNa02 is the only free neuron: LC10a and all 147 intermediates clamped → identical input across DNa02 dynamics)
Sources and per-run intermediate trains: for each source network (DATA; B1 instances), level, side and noise rep, the free source run
gives LC10a trains; the REF replay into the DATA network (v4.3 framework) gives the intermediate trains (as V6m E1c/E3).
Intermediate input variants (manipulated in 300–1000 ms only):
- M0: unchanged (identity; must reproduce REF DNa02 exactly).
- MCIRC: per-neuron circular shift (keeps per-neuron counts and ISI structure in 300–1000 ms; destroys cross-neuron alignment).
- MASYNC: per-neuron exact counts in 300–1000 ms, spikes placed uniformly over all configurations with ISI ≥ 4 ms (exact sampler:
  n sorted distinct values u from range(700 − 3(n − 1)), t_k = u_k + 3k) — timing-free; the gap under MASYNC is the "count route".
  r2 (15:45, before any main-run output): r1 named v6m.synth(p = 0), whose rejection sampler fails for intermediates firing near the
  250 Hz ceiling (smoke run aborted, no data analysed); the exact sampler has the same target distribution.
DNa02 dynamics (each a single change relative to REF; both DNa02 neurons):
- REF (t_ref 2.2 → 3 blocked steps, hard reset, leak, b_a as arm).
- T0: t_ref 0.
- T0B: t_ref 0 + constant DNa02 bias current b* (rate-matched): b* chosen per arm BEFORE the main run by a calibration on separate seeds
  (DATA source, M0, arm levels, both sides) on the grid −60…0 mV step 2 to minimise |mean DNa02(T0, b) − mean DNa02(REF)|.
- T1: t_ref 1 (1 blocked step); T6: t_ref 6 (6 blocked steps).
- NOLEAK: membrane leak term (v_rest − v) removed for DNa02 only (input scaling dt/τ_m kept; RT-D definition); t_ref 2.2.
Arms: MAIN = default parameters (J0 0.2, b_a 0.5), DATA + B1 8 421 001–010, levels 7/8/9 mV, L/R, 8 reps;
robustness arms BA1 (global b_a 1.0; levels 9.5, 10.5 mV) and J025 (J0 0.25 for DATA and B1; levels 7.5, 8.0 mV), each DATA + B1
8 421 001–005, L/R, 8 reps. Arm levels = those used by RT-C (where the open-loop deficit is large and DNa02 below ceiling).
Seeds (registered, fresh): noise MAIN 8 443 001–008, arms 8 443 201–208; bias calibration MAIN 8 443 101–104, arms 8 443 301–304;
manipulation RNG numpy SeedSequence([8 444 000, arm, variant, level, side, rep, source]) — source-specific, so surrogate variability
enters the bootstrap (RT-D §5).

## 2. Outcomes and pre-specified analysis
DNa02 ipsi rate 500–1000 ms; gap = B1 − DATA (Hz) and log-ratio gap L = log(mean B1 / mean DATA). Timing effect
Δt(dyn) = gap(MASYNC) − gap(M0) (positive = removing synchrony shrinks the gap = synchrony harmful); also with MCIRC.
**Primary:** interaction I = Δt(REF) − Δt(T0B), in Hz and in L, MAIN arm, MASYNC. CI95 paired hierarchical bootstrap (B1 instances,
reps within instance, DATA reps; same indices across all cells), RNG 8 419 070; percentile AND jackknife-t intervals reported
(RT-B: percentile under-covers at n = 8); the decision uses the WIDER of the two.
**Decision rule (H-RS):** SUPPORTED in MAIN if (a) Δt(REF) > 0 (CI excludes 0), (b) I > 0 (CI excludes 0) on BOTH metrics, and (c)
Δt(T0B) ≤ 0.5·Δt(REF) (point) with CI upper bound < Δt(REF) point. "Generalises" if the sign of I is positive with CI excluding 0 (Hz)
in both robustness arms; otherwise "parameter-dependent". FALSIFIED in MAIN if I's CI includes 0 on either metric or Δt(T0B) ≥ Δt(REF).
Secondary (descriptive): same for T0 (rate not matched), T1, T6 (dose: Δt should decrease with fewer blocked steps if H-RS), NOLEAK
(H-RS predicts Δt(NOLEAK) ≈ Δt(REF): leak not required), MCIRC instead of MASYNC; count route = gap(MASYNC) under REF and T0B (share of
gap(M0)); rate-matched share of the full gap removed by DNa02 refractoriness: 1 − gap_M0(T0B)/gap_M0(REF) (Hz and L).
Per-level results reported (no decision per level). All results exploratory; ~40 intervals, no multiplicity adjustment.

## 3. Validation (stop if any fails)
V1 engine with default options == v6m.step (and therefore alif.ALIF) bit-for-bit; NOLEAK/bias touch only DNa02 entries. V2 M0 × REF ==
the REF replay DNa02 raster in every run. V3 MASYNC/MCIRC per-neuron counts in 300–1000 ms equal the source intermediate counts;
MASYNC ISI ≥ 4 ms inside the window. V4 MAIN REF source runs at noise seeds 8 443 0xx are new (no reuse of V6m seeds). V5 Stage 1 28/28
before/after; protected tree unchanged.
