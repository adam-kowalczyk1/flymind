# E1 — pre-registration, draft r2: a position map stored in fly wiring, in a robot loop

**Status: DRAFT r2, written 2026-11-11. NOT APPROVED TO RUN. NOT FROZEN. NOT HASHED FOR A RUN.**
This file replaces draft r1 (`E1_PREREG.md`, SHA-256 `2bf9446faccdca1e01d114e1d7bf47e1fd38b431a42ef846ec3b217fbbe10aff`,
left untouched on disk). Reason for the revision: r1 named LC4 → DNp02 / DNp11 as the only primary network and mentioned
only in its last section that this map was exploratory in D0. That decided the map quietly. r2 lays the choice out first
(§2) and registers **two** maps with declared roles.

No code for E1 exists; nothing has been run; no reserved seed has been used. Building and running E1 needs a separate,
explicit approval of the finished document; only then is its SHA-256 recorded in `E_PREREG_SHA256_before_run.txt`. Any
SHA-256 quoted for this draft identifies the text only. Author: Claude (Fable 5.2).

Simulation only (MuJoCo). No robot, no training of weights, no commit, no change to any existing file or protected
module. If the scene cannot be built without modifying a protected module, work stops and the owner is asked.

Evidence labels used below: VERIFIED (read or computed today from the named file), REPORTED (stated by a source I did not
fully check), INFERRED, HYPOTHESIS, NOT VERIFIED, FAILED, NOT IMPLEMENTED.
Other labels: **DATA** = taken from MaleCNS files; **MODEL** = neuron dynamics and signs we assume; **ENGINEERING** =
everything built around it (cameras, encoder, decoder, arm motion).

## 0. Streszczenie dla Adama (po polsku)

- **Co się zmieniło:** wybór mapy jest teraz na początku dokumentu, z tabelą wszystkich kandydatów — także tych, które w
  D0 nie przeszły.
- **Dwie mapy, dwie role (moja propozycja, do Twojej akceptacji lub zamiany):**
  - **Główna: LC4 → DNp02 / DNp11.** Jedyna para „przeciwsobna” (jeden cel dostaje więcej z jednego końca oka, drugi z
    przeciwnego) i jedyna z opisanym w literaturze znaczeniem. **Ale w D0 była tylko eksploracyjna** — widziałem ją, zanim
    zapisałem przewidywania.
  - **Druga, też w pełni zarejestrowana: LPLC2 → DNp04.** To para, którą przewidziałem z góry i która w D0 przeszła w obu
    półkulach. Ma jednak tylko jeden cel, więc daje słabszy test (siła reakcji zamiast kierunku).
- **Co kontroluje która mapa:** główna rozstrzyga, czy linia „rola połączeń” idzie dalej. Tylko druga pozwala powiedzieć
  „mapa przewidziana z góry i potwierdzona w danych działa też w pętli”.
- **Zamiana ról** jest opisana w §2.6 i nie wymaga nowego projektu — wystarczy Twoja decyzja przed zamrożeniem.
- Ramiona z „wolnym sterownikiem” pozostają opcjonalne; rola muchy nie jest tu rozstrzygana.
- Nic nie uruchomiono. To nie jest wynik i nie jest tekst na plakat.

## 1. Question

In the MaleCNS wiring the number of synapses from individual visual projection neurons onto certain descending neurons
changes systematically with the neuron's position in the eye (D0). Question: **if such wiring is put in a closed loop
with a simulated arm, does the arm's response depend on *where* an approaching object is — and does that dependence
disappear when only those synaptic weights are shuffled?**

This tests whether measured wiring carries a usable function without any training. It is **not** a test of an advantage
over a classical controller (expected: the classical map is as good or better), **not** a comparison with a VLA (none is
run) and **not** a statement about the real arm.

## 2. Map choice — laid out before the design

### 2.1 Where the candidates come from

- 10 November: while writing the first report I looked at LC4 → DNp02 / DNp11 in the data and saw opposite gradients.
  That observation was not predicted in advance. It is why D0 exists.
- D0 (`D0_PREREG.md`, SHA-256 `de06eacb59c0f576ce3a420f8871def7bab1c7979ac9985c80b47ef361d6de39`, hashed before the run)
  therefore registered **five other pairs** as confirmatory — LPLC2 → DNp04, LPLC2 → DNp06, LPLC1 → DNp03, LPLC1 → DNp06,
  LPLC1 → DNp11 — and listed every LC4 pair as an "exploratory repeat".
- So "exploratory" for LC4 means: *seen before any prediction was written*. It does not mean weak. "Confirmatory" for an
  LPLC pair means: *predicted, then tested once under fixed rules*.

All numbers in §2.2 were re-read today from `flymind/results/bio_advantage/d0_v1/d0_results.json`
(SHA-256 `45725a6df9d2316a64a247cd5dc8004cec16fecf6f7b23edebfaf56216770ca4`, equal to the recorded value;
`D0_REPORT.md` SHA-256 `e0319ddbbf47f4702f534611eba134c1710976d3cb4ac108728781987c76477f`, also equal). VERIFIED.
D0 was not rerun and no D0 file was changed.

### 2.2 All candidates, including the ones that failed

R = strength of the position gradient (0 = none, 1 = perfect), left / right hemisphere; p from 10 000 permutations.
Angle = direction of the gradient in the eye's hex coordinates. For orientation: the axis used for the test stimulus
(§6) is the h1 − h2 direction, i.e. −45° or, at its other end, +135°.

| # | Candidate map | D0 status | D0 outcome (L / R) | Gradient angle L / R | Read-out it allows | Neurons with a usable eye position (L / R) |
|---|---|---|---|---|---|---|
| 1 | **LC4 → DNp02 and DNp11** | **exploratory** (seen 10 Nov) | DNp02: R 0.75 / 0.85; DNp11: R 0.84 / 0.86; all p = 0.0001. Opposite weights: Spearman ρ −0.65 / −0.73 (p = 0.0001) | −46° / −45° and +116° / +120° (162° / 164° apart) | **push–pull inside one population**: a signed difference of two targets | 71 of 71 / 55 of 55 |
| 2 | **LPLC2 → DNp04** | **confirmatory — PASS** | R 0.81 / 0.73, p = 0.0001 both; stays at p = 0.0001 in both sensitivity runs; left side recomputed blind by an independent instance (0.810) | −50° / −49° | one gradient: a graded response, no opponent | 92 of 94 / 91 of 91 |
| 3 | LPLC2 → DNp06 | confirmatory — **FAILED** | R 0.42 / 0.29; p = 0.0001 / **0.024** (independent recheck 0.029). Fails the registered rule (p < 0.01 in both hemispheres) | 177° / −141° (42° apart between hemispheres) | — | 92 of 94 / 91 of 91 |
| 4 | LPLC2 → DNp06 versus DNp01 (giant fiber) as a push–pull pair | ρ condition registered as secondary: **met** (ρ −0.39 / −0.43, p ≤ 0.0002). But one member is #3 (**FAILED**), and for the other (LPLC2 → DNp01: R 0.73 / 0.83) **no prediction was registered** | mixed | DNp01: 12° / 23° | push–pull, but resting on a failed pair and an unpredicted one | as #3 |
| 5 | LPLC1 → DNp03, DNp06, DNp11 | confirmatory — **PASS** (all three) | R 0.70 / 0.73; 0.67 / 0.80; 0.75 / 0.69; all p = 0.0001 | −163° / −166°; 156° / 173°; 135° / 125° | gradients point the same way, **not push–pull** (ρ +0.52 / +0.71 for DNp03 vs DNp06; other pairs not replicated) | **56 of 68** / 66 of 66 |
| 6 | LC4 → DNp04 | exploratory | R 0.63 / 0.64, p = 0.0001 | −141° / −113° (27° apart between hemispheres) | one gradient | 71 of 71 / 55 of 55 |
| 7 | LC4 → DNp01 (giant fiber) | exploratory | R 0.18 / 0.26, p 0.33 / 0.15 — **no gradient** | — | — | — |
| 8 | LPLC2 → DNp04 versus LPLC1 → DNp11, combined into one push–pull read-out | each member confirmatory PASS (#2, #5); **the pairing itself was noticed today** in the angle table (−50° vs +135°/+125°) and has no prediction and no source behind it | — | nearly opposite | push–pull across two different populations — a construction of mine | as #2 and #5 |

Correction recorded here: the 11 November report (§10.1) called candidate #4 "a second, D0-confirmed push–pull pair".
That was too strong. Only the secondary ρ condition was met; LPLC2 → DNp06 failed its primary test on the right. The
report file is not edited; this sentence is the correction.

### 2.3 What the differences mean for E1

| Property | #1 LC4 → DNp02 / DNp11 | #2 LPLC2 → DNp04 |
|---|---|---|
| Was the map predicted before I looked? | **No.** | **Yes**, and it passed. |
| Is the chain "predicted → found in data → tested in the loop" unbroken? | No. | Yes. |
| Strength in D0 | 0.75–0.86 | 0.73–0.81 |
| Same direction in both hemispheres | yes (within 1–4°) | yes (within 1°) |
| Alignment with the test axis (−45° / +135°) | DNp02 within 1°; DNp11 15–19° off | within 5° |
| Read-out | signed (direction). Anything that scales both targets together — object speed, overall drive — cancels in the difference. | unsigned (amount only). Object speed changes the amount directly, so position is harder to tell apart from speed. Expected to discriminate less well, for a reason that is not about wiring. INFERRED |
| Outside evidence of meaning | Dombrovski et al., *Nature* 613:534–542 (2023), doi 10.1038/s41586-022-05562-8: opposite gradients from LC4 onto DNp02 (backward takeoff) and DNp11 (forward takeoff). REPORTED — I opened the abstract and part of the body on 10 November, not the full text; exact gradient directions NOT VERIFIED by me. | None that I have checked. What DNp04 does behaviourally: NOT VERIFIED. |
| Which end of the axis is "front" | NOT VERIFIED from independent anatomy | NOT VERIFIED (same axis) |
| How it got on the list | chosen by me after seeing it was strong — the risk is that a hand-picked best case flatters the result | picked today among four passing confirmatory pairs because it is (narrowly) the strongest and lies on the test axis — also a choice made after seeing D0, though the gradient itself was predicted |

Why the other candidates are not run in E1: #3 failed; #4 rests on #3 and on an unpredicted pair; #5 has no opponent pair,
its three gradients lie 0–10°, 21–38° and 59–62° away from the test axis, and on the left 12 of 68 neurons have no usable eye position
(they could not be given a receptive field); #6 is exploratory and less consistent between hemispheres; #7 has no gradient;
#8 would be a new construction invented after reading the D0 table. They are **reserved**: not run, not dropped from the
record, and usable later only under a new pre-registration.

### 2.4 The case for each as primary

**For LC4 as primary.** The primary test also carries the rule that can end the whole "role of wiring" line (§10). That
rule is only fair if a failure can be read as "wiring did not matter" rather than "the read-out was weak". The push–pull
read-out is the cleaner instrument. It is also the only map with a published behavioural reading.

**Against LC4 as primary.** It was not predicted. It was selected because it looked strongest. A pass on it cannot be
described as confirming something foreseen, and the size of the effect may be flattering.

**For LPLC2 → DNp04 as primary.** It is the only strong candidate with an unbroken pre-registration chain. A pass on it
is the more defensible sentence scientifically.

**Against LPLC2 → DNp04 as primary.** Its single-target read-out is the weaker instrument (see table). If it failed, the
line-ending rule would fire for a reason that may have nothing to do with wiring. It has no known behavioural meaning in
this project.

### 2.5 Declaration (exit taken: both maps pre-registered, roles declared)

| Role | Map | Origin label that must accompany every result |
|---|---|---|
| **PRIMARY** | #1 LC4 → DNp02 / DNp11 | "map first seen in an exploratory analysis; reported in the literature" |
| **SECONDARY — pre-registered replication on a predicted map** | #2 LPLC2 → DNp04 | "map predicted and confirmed in D0" |
| Reserved, not run | #3–#8 | — |

What the roles control, and nothing else:
- The **primary** hypothesis H1 carries the kill rule and the headline of the report.
- The **secondary** hypothesis H1-S alone decides whether the sentence "a map predicted in advance and confirmed in the
  data also works in the loop" may be said. A pass on the primary map never licenses that sentence.
- Neither result can stand in for the other. Both are reported in full whatever happens.
- Both maps get the same scenes, the same number of shuffles, the same gates and the same freeze.

This declaration is my proposal. It is not a finding, and it becomes the registered choice only if the owner approves
this document. Exploratory D0 results are not upgraded by it.

### 2.6 Swap clause (the owner may choose the other way round)

If the owner prefers LPLC2 → DNp04 as primary, the design below is unchanged except: H1-S becomes the primary hypothesis
and carries the kill rule; H1 (LC4) becomes secondary; H2, N2 and DIRECT move to the LPLC2 map; H3 stays defined on the LC4
map only (it needs a direction). The document is then re-issued as r3 with this table changed, before any freeze. My
stated reservation in that case: a primary failure would be harder to interpret (§2.4).

## 3. What I have already seen

- The gradients, angles and correlations of all candidates in §2.2 (D0 and, for LC4, 10 November).
- The dorsal direction in hex coordinates, anchored by R7d/R8d photoreceptors (11 November, exploratory): dorsal ≈ the
  h1 + h2 direction, so the h1 − h2 axis is roughly front–back. PARTIALLY VERIFIED (axis); which end is front: NOT VERIFIED.
- **Not seen:** any simulation of LC4, LPLC2, DNp02, DNp11 or DNp04; any closed-loop outcome; the size or content of the
  networks in §4.
- Known weakness, stated in advance: given D0, a difference between data and shuffled wiring is expected almost by
  arithmetic, for both maps. The informative quantities are how large and reliable the effect is per trial under noise
  and dynamics, its cost against the classical map, whether it replicates in the other hemisphere, and whether it holds
  on the predicted map.

## 4. Networks (DATA + MODEL)

Built by one rule for both maps (the pattern of `visual_path.select`):
- all neurons of the visual type on one side (`type` exactly `LC4` or `LPLC2`, by `somaSide`);
- the target neuron(s): for each descending type, the neuron receiving most synapses from that population (D0 rule) —
  DNp02 and DNp11 for the primary map, DNp04 for the secondary;
- every other body with ≥ 5 synapses from the population **and** ≥ 5 synapses onto a target;
- all data edges among these bodies. Size and composition are reported whatever they are.

Dynamics: the project's ALIF with default parameters, signs from the project's default map (glutamate −1), background
noise σ = 2 mV as in V5. J0 (mV per synapse) from the grid {0.05, 0.1, 0.2} by the rule in §7, chosen per map, identical
for every network arm of that map.

Hemisphere: **right** is run first for both maps, **left** is a full replication. Reason given in r1 — better position
coverage on the right for LC4 (median 468 hex-annotated input synapses per neuron versus 134) — comes from my 10 November
report and was not recomputed today (REPORTED). D0 itself shows every LC4 on both sides above the 20-synapse threshold.
The figure is recomputed and recorded in the pre-freeze data check (§7).

Secondary variant **DIRECT** (primary map only): the visual neurons, the targets and the edges among them, no
intermediates.

## 5. Controls

- **N1 — map-only shuffle (20 instances per map and hemisphere):** the weights of each visual-population → target block
  are randomly permuted among the neurons of that population (for the primary map: LC4 → DNp02 and, independently,
  LC4 → DNp11; for the secondary: LPLC2 → DNp04). Every other edge is untouched. Each target keeps exactly the same set of
  input weights; only *which neuron carries which weight* changes. (The project's edge-swap shuffle cannot be used here:
  in D0, 69–71 of 71 and 53–54 of 55 LC4, and 94 of 94 and 91 of 91 LPLC2, already connect to their target, so swaps are
  rejected. VERIFIED from `d0_results.json`.)
- **N2 (primary map, right hemisphere, 10 instances):** N1 plus the project's degree-preserving edge-swap shuffle of all
  remaining edges.
- **CLASSICAL (ceiling):** receives exactly the same per-neuron input currents as the network and uses a hand-written
  rule on the current-weighted mean position along the map axis — its sign (primary map) or a linear ramp of it
  (secondary map). No neurons, no delay.
- **NO-REFLEX (floor):** the arm does not react.
- **SLOW-1 / SLOW-2 — optional, not part of the default run.** Run only if the owner chooses role B or C for the fly;
  that choice is not made here. They are the CLASSICAL rule of the LC4 map throttled to 10 Hz with 100 ms delay and to
  2 Hz with 500 ms delay: **slow-policy surrogates, not VLAs**, and never to be described as a VLA result.

## 6. Scene, senses, action (ENGINEERING — labelled as such in every report)

- Arm in a fixed, registered pose, gripper forward axis horizontal, free space on the tested side.
- **Eye:** two virtual cameras on the gripper per tested side, each 90° × 90°, 64 × 64 pixels, 100 Hz, together covering
  azimuth 0° (straight ahead) to 180° (straight behind) and elevation ±45°. The real SO-101 has no such cameras.
- **Position of each visual neuron:** from its hex-annotated inputs (D0 method A, ≥ 20 synapses). u = projection on
  h1 − h2, mapped linearly to azimuth 0–180°; v = projection on h1 + h2, mapped to elevation. A neuron without a usable
  position (2 of 94 LPLC2 on the left) gets no input current in any arm.
- **Which end of u is "front" is not known from independent anatomy.** For running the experiment it is set from the
  literature: the end where LC4 → DNp02 weights are larger is "front" (REPORTED, Dombrovski et al. 2023). Any statement
  that the arm moves in the *correct* direction is circular with respect to D0 and may be reported only as "consistent
  with the published mapping". No primary measure depends on this choice.
- **Stimulus:** a dark sphere (radius 3 cm) starts 0.5 m away and moves at constant speed (uniform 0.5–1.0 m/s) straight
  to the point where the gripper camera was at onset, then stops. Class **A** approaches from azimuth 30–70°, class **P**
  from 110–150°; elevation ±20°. A scene is rejected and redrawn, from geometry alone and before any controller is run,
  if the path passes through the arm. The same scenes serve both maps (both gradients lie along u, §2.2).
- **Encoder:** each visual neuron gets a current proportional to the rate at which the dark object's coverage of its
  receptive field grows (expansion only), capped at 12 mV (the V5 amplitude). The same encoder for LC4 and LPLC2. It
  replaces the fly's optic lobe; it is not the fly.
- **Decoder and motion, primary map:** fore–aft velocity of the gripper = gain × (DNp11 rate − DNp02 rate).
  **Secondary map:** retreat velocity = gain × DNp04 rate (one direction only). Rates filtered with the project's 50 ms
  constant; motion realised by classical differential kinematics and passed through the unmodified safety layer. The
  network decides *whether, when, how much and (primary map) which way*; classical code only turns that into joint motion.

## 7. Development pool, data check and freeze

- **Pre-freeze data check (data only, no seeds):** file hashes equal `results/vision_manipulation/FREEZE_v3.txt`; the
  E1 network builder reproduces the D0 counts of the registered blocks exactly (population sizes and synapse totals in
  `d0_results.json`); position coverage per population and side is recomputed and recorded. Any mismatch stops the work.
- Development scenes: seeds 19 300 000–19 300 199 (never used in the confirmatory run), shared by both maps.
- On the development pool only **DATA and CLASSICAL** of each map may be run. **No shuffled network of either map is
  run before the freeze.**
- Settings fixed there, per map, each by a rule that involves no shuffle:
  - J0: the smallest grid value at which the DATA network's target neuron(s) fire in ≥ 90 % of development trials and
    none exceeds 200 Hz on average during the approach.
  - Receptive-field width from {10°, 15°, 20°} and the rate scale: the pair that maximises CLASSICAL's score on that
    map's primary measure; ties → the smaller width.
  - Decoder gain: the value at which the DATA network's median displacement at impact time is 5 cm.
  - Arm pose and the scene-rejection rule (shared).
- **One freeze for both maps:** hashes of all E1 code and of the settings file recorded in `E1_FREEZE.txt` before any
  confirmatory scene or any shuffle of either map is run. Nothing changes afterwards.

## 8. Confirmatory run, measures, hypotheses

- Scenes: 200 per hemisphere (100 class A, 100 class P), seeds 19 310 000–19 310 199 (right), 19 311 000–19 311 199 (left);
  identical scenes and identical noise seed (scene seed + 50 000) for every arm of both maps.
- Per trial: displacement of the gripper along its forward axis between stimulus onset and nominal impact time;
  first-command latency; whether the sphere touches the gripper; maximum joint speed; safety flags.

**Measure for the primary map (unchanged from r1) — position discrimination by direction.** Response = sign of the
displacement, or "none" if smaller than 5 mm. Accuracy = the larger of (share of trials with "forward" for class P and
"backward" for class A) and (the opposite pairing). No response counts as an error. Every controller, including every
shuffle, gets its own better pairing.

**Measure for the secondary map — position discrimination by amount.** Response amount = |displacement| divided by the
approach duration. Score = folded AUC: the probability that a randomly drawn class-A trial has a larger amount than a
randomly drawn class-P trial, or one minus that, whichever is larger (ties count one half; 0.5 = no discrimination,
1 = perfect). No threshold is fitted. Every controller gets its own better direction.

Neither measure depends on which end of the axis is called "front".

| Hypothesis | Map and role | Rule |
|---|---|---|
| **H1 — primary** | LC4 → DNp02 / DNp11, right | DATA accuracy strictly higher than each of the 20 N1 instances (rank 1 of 21; probability under "no difference" ≤ 1/21 = 0.048) |
| **H1-rep** | the same, left | the same. "In both hemispheres" requires H1 and H1-rep |
| **H1-S — secondary** | LPLC2 → DNp04, right | DATA folded AUC strictly higher than each of its 20 N1 instances (rank 1 of 21) |
| **H1-S-rep** | the same, left | the same |
| **H2 — cost** | primary map, right | DATA not worse than CLASSICAL by more than 10 percentage points: upper one-sided 95 % bound of (CLASSICAL − DATA), paired bootstrap over scenes (10 000 resamples, seed 19 390 001), ≤ 10 |
| **H3 — optional, roles B/C only** | LC4 map | with the literature front/back assignment, DATA avoids contact in more scenes than SLOW-1 and than SLOW-2 (exact McNemar, each p < 0.025). A property of *any* fast layer; never "better than a VLA" |

Multiplicity, stated plainly: H1 and H1-S are two tests at ≤ 0.048 each, not corrected, because they license two
different sentences and neither substitutes for the other. If there were no real effect in either map, the chance that at
least one would pass is at most about 0.095. That number is quoted wherever only one of the two passes.

Always reported, for both maps: the score with a 95 % interval (Wilson for accuracy, bootstrap for AUC); DATA minus median
N1 with paired bootstrap interval; DATA against the best N1 instance and against CLASSICAL (exact McNemar for accuracy;
paired bootstrap for AUC); the score by azimuth band and by approach speed; latency distribution. For a common scale, the
folded AUC of the signed displacement is also given for the LC4 map — descriptive only; no ranking of the two maps is
registered.

Secondary, descriptive: N2 and DIRECT (primary map); sign-only analysis without the 5 mm threshold; consistency with the
published mapping; contact-avoided rates for all arms.

## 9. Validity gates (checked before any hypothesis is read)

- G1: CLASSICAL reaches ≥ 90 % accuracy (primary map) and folded AUC ≥ 0.90 (secondary map) — checked per map.
- G2: NO-REFLEX: displacement below 5 mm in all scenes and contact in ≥ 95 % of scenes.
- G3: maximum joint speed ≤ 1.5 rad/s and no safety latch in any arm. (The earlier 1.89 rad/s defect, whose cause is
  still open, must not appear.)
- G4: module hashes equal `E1_FREEZE.txt` before and after.
- A failed gate makes the affected map's run **void** — no conclusion about wiring for that map; G2–G4 failures void
  both. One repair-and-restart per map is allowed, on the development pool only, with fresh confirmatory scenes
  19 312 000–19 312 199 (right), 19 313 000–19 313 199 (left) and fresh shuffle instances (§11). A second failure ends
  that map as NOT COMPLETED.
- Not a gate: a DATA network that barely responds is a **result** (its score falls and the hypothesis fails), not a void
  run.

## 10. Outcomes: kill rule and allowed statements

| Outcome | What may be said | What may not |
|---|---|---|
| H1 + H1-rep hold, H2 holds | "A position map stored in measured fly wiring (first seen in an exploratory analysis; reported in the literature) works in a simulated robot loop without training; shuffling only those weights removes it; the cost against a hand-written map is at most 10 points." | "better than classical", "better than a VLA", "works on the robot", "confirmed a prediction" |
| H1 holds, H2 fails | the same without the cost claim; the measured cost is stated | hiding the cost |
| H1 holds, H1-rep fails | "in one hemisphere only" | "in both" |
| H1-S + H1-S-rep also hold | in addition: "The same holds for a second map that was predicted in advance and confirmed in the data." | ranking the two maps |
| H1 holds, H1-S fails or is not completed | the primary sentence, plus: "It did not hold (or was not tested successfully) on the map that had been predicted in advance, so the result rests on a hand-picked map." | "predicted in advance", generalising to "the fly's maps" |
| **H1 fails, H1-S holds** | "The declared primary map failed. A secondary, predicted map passed its own test (one test of two; chance of at least one false pass about 0.095)." E1 is reported as **FAILED on its primary hypothesis**. No further experiment on this line without a new pre-registration and the owner's decision. | "E1 succeeded"; re-running the LC4 map; presenting the secondary as if it had been primary |
| **H1 fails and H1-S fails (or is not completed)** | "In no task tried has connectome wiring shown a measurable role in FlyMind." **The wiring line stops.** | re-running with other settings, seeds or networks |
| H3 holds | "a fast hard-wired layer helps a slow policy; generic, not specific to the fly" | "the fly improves a VLA" |

## 11. Seeds (all inside the range already reserved for E1; none used)

Range 19 300 000–19 399 999 is reserved for E1 in `SEED_REGISTRY.md`. Allocation in this draft:

| Use | Seeds |
|---|---|
| Development scenes (both maps) | 19 300 000–19 300 199 |
| Confirmatory scenes, right / left (both maps) | 19 310 000–19 310 199 / 19 311 000–19 311 199 |
| Restart scenes, right / left | 19 312 000–19 312 199 / 19 313 000–19 313 199 |
| N1, LC4 map, right / left | 19 320 001–020 / 19 321 001–020 |
| N2, LC4 map, right | 19 322 001–010 |
| N1, LPLC2 → DNp04 map, right / left | 19 323 001–020 / 19 324 001–020 |
| Shuffle instances after a restart | the corresponding seed + 100 |
| Noise | scene seed + 50 000 |
| Bootstrap | 19 390 001 |

`SEED_REGISTRY.md` still lists the r1 allocation and is not edited in this revision; the two new sub-ranges
(19 323 xxx, 19 324 xxx) and the restart rule lie inside the reserved E1 range. The registry is brought in line when the
document is approved.

## 12. What E1 cannot show, whatever the outcome

Simulation with ideal images and virtual cameras the real arm does not have; looming detection is done by engineered
code; one animal; synapse counts are not strengths and signs are predictions; the mapping from a fly's escape to an arm
motion is an analogy; the primary map was not predicted in advance; the secondary map has no known behavioural meaning.
No statement about VLAs follows from E1. D0 showed structure in synapse counts, not behaviour.

## 13. Changes from draft r1, each with its reason

| Change | Reason |
|---|---|
| New §2: all candidate maps, their D0 status including failures, the case for each, an explicit declaration and a swap clause | r1 decided the map quietly |
| LPLC2 → DNp04 added as a fully registered secondary map (network, N1, measure, hypotheses H1-S and H1-S-rep, gate, seeds) | so that a result on a hand-picked map is checked on a predicted one |
| New measure (folded AUC of response amount) for the secondary map only | that map has one target and therefore no direction; r1's measure cannot be applied to it |
| Kill rule: the line stops only if H1 fails **and** H1-S does not pass; "H1 fails, H1-S holds" is a new row | with two registered maps, r1's sentence "in no task tried…" could be false after a secondary pass. This makes the stop slightly harder to trigger; the bound (about 0.095) is stated |
| Allowed statements carry an origin label for each map | so that exploratory origin cannot be dropped later |
| One freeze for both maps; no shuffle of either map before it | no peeking across maps |
| Gates and restart defined per map; restart uses fresh shuffle instances | r1 did not say what a restart does to shuffles |
| Pre-freeze data check added; the 468 / 134 coverage figure marked REPORTED | it was not recomputed in D0 |
| Neurons without an eye position get no current | needed for LPLC2 on the left (2 of 94); r1 did not need it |
| Correction of the 11 November report's phrase "D0-confirmed push–pull pair" | LPLC2 → DNp06 failed on the right |

Kept from r1 because I still stand by them: direction-based primary measure independent of the front/back assignment;
no shuffle before the freeze; 20 N1 instances and the rank rule; CLASSICAL ceiling and NO-REFLEX floor; H2 margin; right
hemisphere first with left as replication; slow-policy arms optional and never called a VLA.

## 14. Reporting

All arms, gates and hypotheses of both maps — including failures — go to `E1_REPORT.md` with raw file paths and SHA-256;
outputs only in `flymind/results/bio_advantage/e1_v1/` (must not exist beforehand). An independent instance recomputes
both primary tables from the raw trial file before the report is final. Deviations are listed explicitly; thresholds
are not changed after the run.

**STOPPED — awaiting Adam's approval. Nothing in this document has been run.**
