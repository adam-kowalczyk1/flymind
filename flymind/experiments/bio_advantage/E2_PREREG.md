# E2 — pre-registration: is the grasp network just a transfer curve?

**Status: DRAFT r1, written 2026-11-11. NOT APPROVED TO RUN.** The owner approved writing this document only
("Tak, napisz", 2026-11-11). No code for E2 exists; nothing has been run. Running E2 needs a separate, explicit approval;
at that moment this file's SHA-256 is recorded in `E_PREREG_SHA256_before_run.txt` and the script must refuse to start if
the hash differs. Author: Claude (Fable 5.2).

Simulation only (MuJoCo). No robot, no training, no commit, no change to any existing file or protected module.
Background: `flymind/reports/fly_vs_vla_research_20261111.md` §2.3 and §10.1 ("E2", called "S1" on 10 November).

## 1. Question

In the grasp benchmark the network receives two numbers (force on each pad) and returns one (jaw torque)
(`fly_jaw.py:51–54`, `sensory_manipulation.py:119–137`). Claim to test: **in this task the network behaves like a fixed
input–output curve with simple linear dynamics; nothing about its internal wiring is needed to reproduce what it does.**
If true, the grasp task cannot say anything about wiring, and the earlier statement "the network's edge over the one-line
reflex comes from temporal filtering" is supported. If false, the network does something more in this task than a curve
(which would still not be evidence about wiring).

## 2. What I have already seen

All existing results of the grasp stage (`results/sensory_manipulation`, `contact_audit`, `shuffle_matched`), including
per-trial outcomes. Nothing about any surrogate controller, because none exists.

Trial-level disagreement between existing controllers on the same 135 trials (computed 2026-11-11 from the raw files, used
below to set the margin): the network run twice — 0 of 18 re-run trials differ; the network with glutamate −1 vs +1 — 10;
network vs the ten shuffles — 17, 12, 14, 14, 13, 21, 14, 19, 17, 86; network vs network + FeCO — 15; vs one-line reflex —
18; vs classical controller — 27; soft vs stiff contact for the network — 26.

## 3. Controllers

All use the existing driver interface `step(touch, q, qd) → torque`, `reset()` and are run through the existing
`sensory_manipulation.run_trial` exactly like arm B (trigger "search", glutamate −1, oracle percept). Scaffolding, scene,
objects and success criteria are untouched.

- **NET** — the existing network `sensory_manipulation.LegJaw(FlyCfg(trigger="search"))`. Re-run, not copied.
- **M0 (static curve)** — torque = g(f1, f2), where g is NET's measured steady-state map (below). No memory, no delay.
- **M1 (curve + linear dynamics)** — torque(t) = Σ_k h(k) · g(f1(t−k), f2(t−k)), where h is NET's measured, normalised
  response to a step input (below). This is the standard "static nonlinearity followed by a linear filter" model.

**How g and h are measured — open loop, without the robot, before any trial, and never adjusted afterwards:**
- g: for every pair (f1, f2) on the grid 0, 0.05, …, 1.0 N × 0, 0.05, …, 1.0 N (441 points; the network's input saturates
  at 1 N), reset NET, hold the input for 120 control ticks (1.2 s), take the mean torque over ticks 60–119 — the same
  procedure as the existing reference measurement in `shuffle_matched.py`. Between grid points: bilinear interpolation;
  inputs above 1 N are clipped to 1 N.
- h: reset NET, apply (0.5, 0.5) N for 300 ticks (3 s); h = tick-to-tick increments of the torque, divided by the final
  mean torque (ticks 240–299), truncated to 300 taps. If the final mean torque is not positive the experiment stops
  (reported as FAILED to build M1).
- **No parameter of M0 or M1 may be fitted to benchmark outcomes.** They are functions of the open-loop measurement only.

## 4. Runs

| Arm | Contact | Trials |
|---|---|---|
| NET, M0, M1 | soft (as benchmark v2) | the same 135 (45 objects × 3 poses; scene seeds 100 000–100 442, the fixed benchmark set used by every earlier arm) |
| NET, M0, M1 | stiff (contact time constant 0.002 s for all materials, exactly as `contact_audit.py`) | the same 135 |
| Secondary E2-c: M1 built in the same way for each of the ten existing shuffles (shuffle seeds 17 100 011–020, with their recorded gain scale) | soft | the same 135 each |

The shuffle seeds are re-used only to rebuild the *same* ten networks whose results already exist; no new shuffle is drawn.
Shadow logging: during the NET runs, the torque M1 *would* have produced on the same input stream is computed and stored
(M1 does not act).

Outputs go only to `flymind/results/bio_advantage/e2_v1/` (must not exist beforehand). At most 8 processes.

## 5. Validity gates (checked before looking at any comparison)

- G1: NET re-run gives 90/135 (soft) and 84/135 (stiff) with every per-trial outcome identical to
  `sensory_manipulation/B_fly_search_glu-1_v1.json` and `contact_audit/stiff_B_v1.json`. If not, the environment has
  changed: the run is **void**, nothing is concluded, the cause is reported.
- G2: hashes of the protected and stage modules equal those in `results/vision_manipulation/FREEZE_v3.txt` before and
  after the run.

## 6. Hypotheses and decision rules

Primary measure: number of the 135 trials on which two controllers give a different success/failure outcome ("discordant
trials"). Margins fixed from §2:

| Discordant trials vs NET | Reading |
|---|---|
| ≤ 7 | **equivalent** — closer to NET than NET is to itself with a different glutamate sign (10) |
| 8–11 | close — as close as that sign variant |
| ≥ 12 | **not equivalent** — as different from NET as a shuffled network |

- **H-E2a (primary):** M1 vs NET, soft contact: ≤ 7 discordant trials.
- **H-E2b:** M1 vs NET, stiff contact: ≤ 7 discordant trials.
- Both hold → "in the grasp benchmark the network is behaviourally equivalent to a transfer curve with linear dynamics".
  The grasp task is then closed as a place to look for effects of wiring; no further shuffles are run on it.
- H-E2a fails (≥ 12) → the network does more than a curve here. This is reported as such; it is **not** evidence about
  wiring, and no parameter is changed to rescue the surrogate.
- 8–11 → reported as "close"; no claim of equivalence.

Reported with every comparison: successes with Wilson 95 % intervals; discordant pairs split by direction with the exact
two-sided McNemar p; the same recomputed per object (45 clusters: object counted as success if ≥ 2 of 3 poses succeed),
because poses of one object are not independent.

Secondary, descriptive (do not change the verdict):
- M0 vs NET and M0 vs M1 (how much the dynamics matter); M0 and M1 vs the one-line reflex result (80/135).
- Shadow agreement: R² between NET's torque and M1's shadow torque over all ticks with contact; reading fixed now:
  R² ≥ 0.90 → "the curve explains at least 90 % of the torque".
- E2-c: across the 11 networks (data + 10 shuffles), Spearman correlation between the success of each network's M1
  surrogate and the success of the network itself (existing results 90; 101, 82, 80, 102, 83, 79, 82, 79, 99, 4).
  Reading fixed now: ρ ≥ 0.8 → "differences between shuffled networks are explained by their transfer curves".

## 7. Seeds

No new random scenes. Benchmark scene seeds 100 000–100 442 and shuffle seeds 17 100 011–020 are re-used as described in
§4. One new seed for bootstrap intervals, if any are reported: 19 200 001 (range 19 200 000–19 200 999 reserved for E2 in
`SEED_REGISTRY.md`).

## 8. What E2 cannot show

It is one task, in simulation, with an oracle percept. Equivalence in this task says nothing about tasks with spatially
structured input (that is E1). It does not compare with any VLA.

## 9. Reporting

Everything, including failed gates and failed hypotheses, goes to `E2_REPORT.md` with raw file paths and SHA-256.
Deviations from this document are listed explicitly. Thresholds are not changed after the run.
