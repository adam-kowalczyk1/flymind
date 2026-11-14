# E1 — pre-registration: does a position map stored in fly wiring work in a robot loop?

**Status: DRAFT r1, written 2026-11-11. NOT APPROVED TO RUN.** The owner approved writing this document only
("Tak, napisz", 2026-11-11). No code for E1 exists; nothing has been run. Building and running E1 needs a separate,
explicit approval; at that moment this file's SHA-256 is recorded in `E_PREREG_SHA256_before_run.txt`, and the
confirmatory script must refuse to start if the hash differs. Author: Claude (Fable 5.2).

Simulation only (MuJoCo). No robot, no training of weights, no commit, no change to any existing file or protected
module. If the scene cannot be built without modifying a protected module, work stops and the owner is asked.
Background: `flymind/reports/fly_vs_vla_research_20261111.md` §6.3, §7, §10.1; `D0_REPORT.md`. This is the experiment
called "S2" on 10 November.

Labels: **DATA** = taken from MaleCNS files; **MODEL** = neuron dynamics and signs we assume; **ENGINEERING** = everything
we build around it (cameras, encoder, decoder, arm motion).

## 1. Question

D0 showed that in the MaleCNS wiring the number of synapses from each LC4 visual neuron onto the descending neurons DNp02
and DNp11 changes systematically with the neuron's position in the eye, in opposite directions for the two targets.
Question: **if that wiring is put in a closed loop with a simulated arm, does the arm's response depend on *where* an
approaching object is — and does that dependence disappear when only those synaptic weights are shuffled?**

This is a test of whether measured wiring carries a usable function without any training. It is **not** a test of an
advantage over a classical controller (expected: the classical map is as good or better) and **not** a comparison with a
VLA (none is run).

## 2. What I have already seen (so the reader can judge what is confirmatory)

- LC4 → DNp02 / DNp11 gradients in both hemispheres (10 November, exploratory; repeated in D0 as exploratory; recomputed
  blind by an independent instance). Their direction in hex coordinates (−46°/−45° and +116°/+120°).
- The dorsal direction in hex coordinates, anchored by R7d/R8d photoreceptors (11 November, exploratory).
- **Not seen:** any simulation of LC4, DNp02 or DNp11; any closed-loop outcome; the size or content of the network
  defined in §3. The closed-loop outcomes are new data.
- Known weakness, stated in advance: given D0, a difference between data and shuffled wiring is expected almost by
  arithmetic. The informative quantities are how large and how reliable the effect is per trial under noise and dynamics,
  its cost against the classical map, and whether it replicates in the other hemisphere.

## 3. Network (DATA + MODEL)

- Hemisphere: **right** is primary (better position coverage: median 468 hex-annotated input synapses per LC4 vs 134 on
  the left); **left** is a full replication.
- Bodies, by rule (the same pattern as `visual_path.select`): all LC4 of that side (`type == 'LC4'`, `somaSide`); the
  DNp02 and DNp11 neuron that receives most synapses from that population (D0 rule); every other body with ≥ 5 synapses
  from the LC4 population **and** ≥ 5 synapses onto either target. All data edges among these bodies. The resulting size
  and composition are reported, whatever they are.
- Dynamics: the project's ALIF with default parameters, signs from the project's default map (glutamate −1), background
  noise σ = 2 mV as in V5. J0 (mV per synapse) is taken from the grid {0.05, 0.1, 0.2} by the rule in §6; it is identical
  for every network arm.
- Secondary variant **DIRECT**: only LC4, DNp02, DNp11 and the edges among them (no intermediates).

## 4. Controls (the point of the experiment)

- **N1 — map-only shuffle (primary, 20 instances per hemisphere):** within the hemisphere, the weights of the LC4 → DNp02
  edges are randomly permuted among the LC4 neurons, and independently the weights of the LC4 → DNp11 edges. Every other
  edge is untouched. Each target neuron keeps exactly the same set of input weights, so total input strength is matched
  by construction; only *which LC4 neuron carries which weight* changes. (The project's edge-swap shuffle cannot be used
  for this block: nearly every LC4 already connects to both targets, so swaps are rejected. Stated here so nobody is
  surprised later.)
- **N2 (secondary, 10 instances):** N1 plus the project's degree-preserving edge-swap shuffle of all remaining edges.
- **CLASSICAL (ceiling):** receives exactly the same per-neuron input currents as the network (equal information) and
  decides by a hand-written rule: sign of the current-weighted mean position along the map axis. No neurons, no delay.
- **NO-REFLEX (floor):** the arm does not react.
- **SLOW-1 / SLOW-2 (optional — run only if the owner chooses role B or C in the report's §8):** the CLASSICAL rule
  throttled to 10 Hz with 100 ms delay, and to 2 Hz with 500 ms delay. These are **slow-policy surrogates, not VLAs**; the
  two settings are taken from published VLA latencies and may never be described as a VLA result.

## 5. Scene, senses, action (ENGINEERING — all labelled as such in every report)

- Arm in a fixed, registered pose with the gripper's forward axis horizontal and free space on the tested side.
- **Eye:** two virtual cameras on the gripper per tested side, each 90° × 90°, 64 × 64 pixels, 100 Hz, together covering
  azimuth 0° (straight ahead) to 180° (straight behind) on that side and elevation ±45°. This copies the fly's geometry
  (one eye per side, front to back). The real SO-101 has no such cameras; E1 says nothing about hardware.
- **Position of each LC4** in the eye: from its hex-annotated inputs (D0 method A). Map axis u = projection on the
  h1 − h2 direction (the axis perpendicular to the dorsal direction anchored on 11 November); v = projection on h1 + h2.
  u is mapped linearly onto azimuth 0–180°, v onto elevation. **Which end of u is "front" is not known from independent
  anatomy.** For running the experiment it is set from the literature: the end where LC4 → DNp02 weights are larger is
  "front" (Dombrovski et al., Nature 2023). Consequence, stated now: any statement that the arm moves in the *correct*
  direction is circular with respect to D0 and is reported only as "consistent with the published mapping". The primary
  measure in §7 does not depend on this choice.
- **Stimulus:** a dark sphere (radius 3 cm) starts 0.5 m away and moves at constant speed (uniform 0.5–1.0 m/s) in a
  straight line to the point where the gripper camera was at onset, then stops. Approach azimuth: class **A (front)**
  30–70°, class **P (rear)** 110–150°; elevation ±20°. A scene is rejected and redrawn, from geometry alone and before
  any controller is run, if the path passes through the arm.
- **Encoder:** each LC4 gets a current proportional to the rate at which the dark object's coverage of its receptive
  field grows (expansion only), capped at 12 mV (the V5 amplitude). Receptive-field width and the rate scale are fixed by
  §6. This replaces the fly's optic lobe; it is not the fly.
- **Decoder and motion:** fore–aft velocity of the gripper along its forward axis = gain × (DNp11 rate − DNp02 rate),
  rates filtered with the project's 50 ms constant; realised by classical differential kinematics (scaffolding) and passed
  through the unmodified safety layer. The network decides *whether, when and which way*; classical code only turns that
  into joint motion. Posture is otherwise held by a script.

## 6. Development pool and freeze (how the engineering choices are fixed without peeking)

- Development scenes: seeds 19 300 000–19 300 199 (never used in the confirmatory run).
- On the development pool only **DATA and CLASSICAL** may be run. **No shuffled network is run before the freeze**, so no
  setting can be chosen because it separates data from shuffles.
- Settings fixed there, each by a rule that does not involve any shuffle:
  - J0: the smallest grid value at which the DATA network's two target neurons together fire in ≥ 90 % of development
    trials and neither exceeds 200 Hz on average during the approach.
  - Receptive-field width from {10°, 15°, 20°} and the rate scale: the pair that maximises CLASSICAL accuracy; ties → the
    smaller width.
  - Decoder gain: the value at which the DATA network's median displacement at impact time is 5 cm.
  - Arm pose and the scene-rejection rule.
- Then: hash of all E1 code and of the settings file recorded in `E1_FREEZE.txt`; nothing changes afterwards.

## 7. Confirmatory run, measures, hypotheses

- Scenes: 200 per hemisphere (100 class A, 100 class P), seeds 19 310 000–19 310 199 (right), 19 311 000–19 311 199
  (left). Identical scenes and identical noise seed (scene seed + 50 000) for every arm. Shuffle instance seeds
  19 320 001–020 (N1 right), 19 321 001–020 (N1 left), 19 322 001–010 (N2, right).
- Per trial: displacement of the gripper along its forward axis between stimulus onset and nominal impact time;
  **response** = its sign, or "none" if smaller than 5 mm; first-command latency; whether the sphere touches the gripper;
  maximum joint speed; safety flags.

**Primary measure — position discrimination, independent of the front/back assignment:** for one controller, accuracy =
the larger of (share of trials in which "forward" goes with class P and "backward" with class A) and (the opposite
pairing). Trials with no response count as errors. Every controller, including every shuffle, gets its own better
pairing. Chance is slightly above 50 %.

| Hypothesis | Rule |
|---|---|
| **H1 (wiring matters) — primary** | Right hemisphere: DATA accuracy is strictly higher than that of each of the 20 N1 instances (rank 1 of 21; chance of that under "no difference" ≤ 1/21 = 0.048). |
| **H1-rep** | The same in the left hemisphere. The claim "in both hemispheres" requires H1 and H1-rep. |
| **H2 (cost of using the fly)** | DATA is not worse than CLASSICAL by more than 10 percentage points: upper one-sided 95 % bound of (CLASSICAL − DATA) accuracy, paired bootstrap over scenes (10 000 resamples, seed 19 390 001), ≤ 10. |
| **H3 (optional, roles B/C only)** | With the literature front/back assignment, DATA avoids contact in more scenes than SLOW-1 and than SLOW-2 (exact McNemar, each p < 0.025). Reported as a property of *any* fast layer; never as "better than a VLA". |

Effect sizes always reported: DATA accuracy with Wilson 95 % interval; DATA minus median N1 with paired bootstrap interval;
exact McNemar of DATA against the best N1 instance and against CLASSICAL; accuracy by azimuth band; latency distribution.

Secondary, descriptive: N2; DIRECT variant; sign-only analysis (response sign regardless of the 5 mm threshold);
consistency with the published mapping (share of trials with "backward" for class A and "forward" for class P);
contact-avoided rates for all arms.

## 8. Validity gates (checked before any hypothesis is read)

- G1: CLASSICAL accuracy ≥ 90 % (the task is solvable from what the encoder provides).
- G2: NO-REFLEX: displacement below 5 mm in all scenes and contact in ≥ 95 % of scenes (the stimulus really arrives).
- G3: maximum joint speed ≤ 1.5 rad/s and no safety latch in any arm. (The earlier 1.89 rad/s defect must not appear.)
- G4: module hashes equal `E1_FREEZE.txt` before and after.
- If G1–G4 fail: the run is **void** — no conclusion about wiring. One repair-and-restart is allowed, on the development
  pool only, with fresh confirmatory seeds 19 312 000–19 312 199 (right) and 19 313 000–19 313 199 (left); a second
  failure ends E1 as NOT COMPLETED.
- Separate from the gates: if the DATA network gives no response in more than half of the scenes, that is a **result**
  (H1 fails), not a void run.

## 9. Kill criteria and allowed statements

| Outcome | What may be said | What may not |
|---|---|---|
| H1 and H1-rep hold, H2 holds | "A position map stored in measured fly wiring works in a simulated robot loop without training; shuffling only those weights removes it; the cost against a hand-written map is at most 10 points." | "better than classical", "better than a VLA", "works on the robot" |
| H1 holds, H2 fails | the same without the cost claim; the measured cost is stated | hiding the cost |
| H1 holds, H1-rep fails | "in one hemisphere only" | "in both" |
| **H1 fails** | "In no task tried has connectome wiring shown a measurable role in FlyMind." **The wiring line stops.** | re-running with other settings, seeds or networks |
| H3 holds | "a fast hard-wired layer helps a slow policy; generic, not specific to the fly" | "the fly improves a VLA" |

## 10. Seeds

Range 19 300 000–19 399 999 reserved for E1 in `SEED_REGISTRY.md` (not present in any registry or file under `flymind/`
on 2026-11-11). Exact uses are listed in §6–§8.

## 11. What E1 cannot show, whatever the outcome

Simulation with ideal images and virtual cameras the real arm does not have; looming detection is done by engineered code;
one animal; synapse counts are not strengths and signs are predictions; the mapping from fly escape direction to arm
motion is an analogy; LC4 was exploratory in D0. No statement about VLAs follows from E1.

## 12. Reporting

All arms, gates and hypotheses — including failures — go to `E1_REPORT.md` with raw file paths and SHA-256; outputs only in
`flymind/results/bio_advantage/e1_v1/` (must not exist beforehand). An independent instance recomputes the primary table
from the raw trial file before the report is final. Deviations are listed explicitly; thresholds are not changed after
the run.
