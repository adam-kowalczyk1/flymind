# V6m — Mechanistic dissection of the DNa02 response to synchronous LC10a input (EXPLORATORY) — protocol r1, 2026-10-30 ~15:00

Written after V5 v4.3 and before any V6m simulation. Name "V6m" because `results/v6/` already holds the V6 parameter study; all
V6m outputs go to `results/v6m/` (new, isolated). Everything here is a COMPUTATIONAL ABLATION of a MODEL (ALIF, J0 0.2, b_a 0.5,
σ 2 mV, t_ref 2.2 ms, DATA downstream wiring). No statement about Drosophila; no biological manipulation is implied.

## 0. Starting point and facts that shape the design (checked 2026-10-30 ~14:50 on the DATA network)
- V5 v4.3: replaying B1 LC10a trains into the DATA network gives DNa02 ipsi −19.9 Hz vs DATA trains (7–9 mV); destroying
  cross-neuron alignment (circular shift, Poisson) removes ~90 % of that gap. Candidate (untested): DNa02 refractory/reset
  saturation during volleys.
- DNa02 receives NO direct LC10a input in this network: 65 (L) / 86 (R) intermediate inputs (exc Σw ≈ 530, inh Σw ≈ −70).
- DNa02 is NOT a pure sink: it projects to 21 intermediates. Changing DNa02 dynamics therefore also changes intermediate
  activity in the free replay → the clean DNa02-only test is done with intermediates clamped (Exp 1c).
- Engine (alif.py): dt 1 ms; refractoriness = v held at v_reset for ceil(t_ref) steps, input during that time is NOT integrated,
  but the synaptic current g keeps accumulating and decaying (τ_syn 5 ms); t_ref 2.2 → 3 blocked steps → min ISI 4 ms, r_max 250
  Hz. At t_ref 0 a neuron can fire every step (r_max 1000 Hz) but still resets to −52 mV after each spike (reset discards the
  supra-threshold charge) → "reset saturation" is a separate candidate from "refractory saturation".
- Adaptation: a += b_a per spike, τ_a 300 ms, per-neuron b_a supported natively by alif.ALIF.

## 1. Questions
Is the lower DNa02 response under B1-like synchronous LC10a input primarily caused by (H1) DNa02 refractoriness, (H2) ALIF
adaptation (DNa02 or intermediates), (H3) intermediate-layer temporal structure, (H4) an interaction, (H5) something else
(candidates fixed now: reset of supra-threshold charge in DNa02; synchronous intermediate inhibition; refractoriness in the
intermediates)? The refractory hypothesis is NOT assumed.

## 2. Framework (validated V5 v4.3 replay, extended)
Sources: free runs of DATA and B1 instances 8 421 001–010 (the v4.3 set) at LC10a current 7, 8, 9 mV, unilateral (L and R),
noise reps 8 411 001–008 (the v4.3 seeds → V0 must reproduce v4.3 exactly). Their LC10a trains are replayed into the DATA network
with all 275 LC10a clamped. New engine `v6m.step` = `v5v43.step_clamped` with (i) per-neuron t_ref vector, (ii) per-neuron b_a
vector (as alif.ALIF), (iii) optional per-neuron subtractive reset, (iv) clamping of any index set. With default vectors it must
equal `step_clamped` / `alif.ALIF.step` bit-for-bit (test T1).
Steady window 500–1000 ms; manipulations of trains only in 300–1000 ms (as v4.3).

## 3. Experiments (each a single-factor intervention relative to the v4.3 replay reference "REF"; nothing combined unless stated)
**Exp 1 — DNa02 refractoriness (free intermediates).** DNa02 (both) t_ref ∈ {0, 1, 2, 2.2 = REF, 4, 6} ms (blocked steps 0, 1,
2, 3, 4, 6). All other neurons t_ref 2.2.
**Exp 1b — intermediate refractoriness.** intermediates' t_ref ∈ {0, 4} ms; DNa02 and LC10a 2.2.
**Exp 1c — DNa02 refractoriness with intermediates clamped.** Intermediates (all 147) and LC10a clamped to the trains recorded in
the REF replay of the same source/level/side/rep; DNa02 t_ref ∈ {0, 2.2, 6}. Removes DN→intermediate feedback: DNa02 gets
identical input in every condition. Validation: at 2.2 it must reproduce REF DNa02 spikes exactly.
**Exp 2 — adaptation (refractoriness at 2.2 everywhere).** b_a ∈ {0, 0.25, 0.5 = REF, 1.0} mV/spike in (a) DNa02 only, (b)
intermediates only — two separate families, never combined with Exp 1. LC10a are clamped, so their adaptation is part of the
recorded trains and not manipulated.
**Exp 3 — intermediate-layer clamp.** Intermediates + LC10a clamped (as Exp 1c, DNa02 default). Intermediate trains from REF
are (i) replayed unchanged (M0 — identity validation), (ii) circularly shifted per neuron (MCIRC: per-neuron count and ISI
structure kept, cross-neuron alignment destroyed), (iii) jittered ±2, ±5, ±20 ms (MJ2, MJ5, MJ20), (iv) rate-matched Bernoulli
per neuron (MPOIS). Manipulations in 300–1000 ms only. Known confounds (stated now): MCIRC/MJ break the coupling between
intermediate spikes and the concurrent LC10a/DN state (irrelevant here: DNa02 receives only intermediate input and its feedback
is clamped away), MPOIS also removes each neuron's ISI structure, jitter collisions lose ≤ ~1 % spikes (counted).
**Exp 4 — synchrony dose–response at the LC10a input.** Synthetic LC10a trains with EXACTLY the per-neuron spike counts of the
DATA source train (300–1000 ms; 0–300 ms unchanged): each spike is placed, with probability p, at a shared population event
(events: Poisson process within the window, common to all LC10a of that side; spike time = event + U{−1,0,1} ms), otherwise
uniformly; generator seed = 8 441 000 + 300·level_index + 150·side_index + 10·grid_index + rep; collisions and ISIs < 4 ms
are re-drawn uniformly until valid (count preserved exactly; tested). Grid (11 points): primary event rate 10 Hz with p ∈ {0, 0.1, 0.2, 0.35, 0.5, 0.7, 0.9, 1.0};
secondary event rate 40 Hz with p ∈ {0.35, 0.7, 1.0} (same mean participation, smaller and more frequent volleys — tests whether
volley size or overall alignment matters). Design pilot (smoke seeds 8 490 045–053, 8 mV, before hashing this protocol): Fano10 of
DATA LC10a ≈ 6–9, B1 ≈ 35–43; 10 Hz grid spans ≈ 1 → 35, 40 Hz grid ≈ 1 → 25 — the 10 Hz grid was chosen to cover the B1 endpoint. Replayed into DATA under (a) REF dynamics, (b) DNa02 t_ref 0 (Exp 1 factor), (c) DNa02 b_a 0 (Exp 2 factor),
(d) intermediates t_ref 0 (Exp 1b factor) — each a single change, giving the synchrony→DNa02 slope with and without that
mechanism. Real trains (DATA, B1, v4.3 CIRC) are placed on the same synchrony axes.
**Exp 5 — other candidates (diagnostic).** (a) DNa02 subtractive reset (v ← v − (v_th − v_reset) instead of v ← v_reset) WITH DNa02
t_ref 0, compared against Exp 1 DNa02 t_ref 0 (hard reset) — keeps supra-threshold charge. Necessarily paired with t_ref 0: in this
engine v is held at v_reset during refractoriness, so with t_ref 2.2 a subtractive reset is wiped on the next step (null
manipulation; checked in the code before writing this line). F for 5a is computed relative to Exp 1 t_ref 0; (b) intermediate→DNa02 inhibitory weights set to 0 (structure ablation of the downstream
DATA wiring, identical for both sources). Each alone.
**Reference condition LCIRC** (all sets): REF dynamics with LC10a trains circularly shifted per neuron (v4.3 CIRC, new RNG) —
reproduces the original effect size inside V6m. **Replication set.** Fresh noise seeds 8 442 001–008 and B1 instances 8 421 011–020 (not used in v4.3): REF, Exp 1 (t_ref 0, 6),
Exp 1c (0), Exp 2a/2b (b_a 0), Exp 3 (M0, MCIRC), Exp 5a, LC10a circular shift (LCIRC). Analysed identically, reported separately.

## 4. Measurements (DNa02 ipsi; intermediates ipsi; window 500–1000 ms unless noted)
DNa02 rate; full DNa02 ipsi spike train (stored) → ISI distribution, fraction of ISIs at the configuration's floor (≤ blocked
steps + 1) and ≤ 4 ms; DNa02 adaptation state a (mean over window and at 1000 ms); latency = first DNa02 ipsi spike after step
onset (0 ms) and after 300 ms; DNa02 membrane: fraction of steps in refractory, mean "lost charge" proxy (v before reset − v_th
at spike steps); intermediate ipsi rate, intermediate adaptation mean; input checks: LC10a ipsi spike count per run (and
intermediate counts in Exp 3) before/after manipulation.
Synchrony of LC10a ipsi (and intermediates ipsi) per run, 500–1000 ms, several measures (all reported, none privileged):
Fano of the population count at 2, 5, 10, 20 ms bins; Golomb χ² (variance of population-mean count / mean single-neuron variance,
5 ms bins); mean pairwise Pearson correlation of 5 ms counts; volley participation = fraction of spikes falling in 2 ms bins whose
population count ≥ mean + 3 SD of the count (time-shuffled reference reported); population count CV (5 ms). Limitations stated in
the report (rate dependence, bin dependence, N dependence of χ, pairwise ≠ higher-order).

## 5. Analysis (pre-specified)
Unit structure: independent networks = B1 instances (10; replication 10 more) + the single DATA network; noise reps = repeated
measurements within a network; levels × sides are averaged within a rep (not treated as independent). Gap(cond) = mean DNa02(B1
trains) − mean DNa02(DATA trains) under the same condition. CI95: hierarchical bootstrap (resample B1 instances, then reps within
instance; DATA reps resampled), 10 000 draws, RNG 8 419 060; the SAME resample indices are used for every condition (paired),
so F(cond) = 1 − Gap(cond)/Gap(REF) gets a joint CI. Primary metric: absolute gap (Hz); secondary: relative gap
(Gap / DNa02(DATA trains)) — because ablations change the rate level.
Decision rules (fixed now):
- An ablation "removes most of the gap" if F ≥ 0.5 with CI lower bound > 0.25; "contributes" if the CI of F excludes 0
  (F < 0 = ablation enlarges the gap); "not supported" if the CI includes 0.
- H1 (DNa02 refractoriness) is SUPPORTED only if Exp 1c (t_ref 0, intermediates clamped) removes most of the gap AND Exp 4b
  flattens the synchrony slope (slope ratio t_ref0/REF with CI upper < 0.5) AND the replication agrees (same rule outcome). If Exp 1
  and Exp 1c disagree, the difference is attributed to DN→intermediate feedback, not to refractoriness.
- H2: same rule for Exp 2a / 2b at b_a 0 and Exp 4c.
- H3: intermediate temporal structure is REQUIRED for the gap if MCIRC removes most of the M0 gap (rule above, F relative to
  M0) and M0 reproduces REF exactly. MCIRC's residual gap is the part carried by intermediate rates.
- H5: Exp 5a/5b and Exp 1b with the same rule.
- Contributions are NOT summed across experiments (ablations are not additive by design); "quantified contribution" is reported
  only as each F with its CI.
Exp 4: per p, DNa02 mean over levels × sides per rep; slope of DNa02 vs each synchrony measure by OLS over p-levels (bootstrap
over reps, RNG 8 419 061); the DATA/B1 real trains are located on the synchrony axes; monotonicity reported as observed.
Everything is exploratory; no confirmatory claim; no p-values for decisions.

## 6. Validation (before interpretation) and stop rules
T1 engine identity with default vectors vs alif.ALIF and v5v43.step_clamped (free and clamped, ≥ 2 networks). T2 each ablation
changes only the intended vector entries (assert on parameter vectors per condition: all other entries equal REF). T3 REF replay
== v4.3 V0 numbers (DN counts equal to `results/v5v43/raw/*.npz` replay V0). T4 Exp 1c/3 identity clamp == REF DN spikes. T5 input
spike counts per run: LC10a identical across all non-manipulated conditions; Exp 4 per-neuron counts identical to the source; jitter
losses counted. T6 Stage 1 28/28 before/after; protected tree unchanged. Any failed validation → stop, fix, rerun the whole set,
report the failure.
