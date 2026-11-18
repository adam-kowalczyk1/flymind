# Alien-space scan for FlyMind: novel, under-explored directions linking fly biology, connectomes and robot AI/vision (state as of 2026-11-12)

Method note. Lacuna = read-only map of ML/AI literature. Its "hypotheses" are machine-generated research proposals (all of those below carry generated_at 2026-10-04), NOT validated results. Every mapping from a Lacuna hypothesis to fly biology is my INFERENCE and is labelled so. Labels: VERIFIED (I opened the primary page/record this session), REPORTED (abstract/secondary only), INFERRED (my reasoning), PROPOSED (idea, nothing run). No simulation was run, no repo file touched.

## 1. What does Lacuna's hypothesis space contain for connectome / fly-vision / looming / learning / neuromodulation / tooling queries?

### Takeaway
Lacuna's hypothesis corpus is ML-centric: queries phrased as "connectome-constrained robot control", "mushroom body few-shot", "connectome tooling" returned nothing on-topic (9, 26 and ~4,700 loose hits, top results unrelated). Useful material appears only when queries are phrased in ML/robotics vocabulary (event camera, looming/time-to-contact, self-generated events, wiring cost, few-shot fixes); the fly mapping then has to be supplied by us.

### Cited Findings
- Query "connectome-constrained neural network robot control" (hypothesis): total_results 9, top hits unrelated (DC rail voltage control, translation pacing, GNSS) — VERIFIED via search_lacuna, 2026-11-12. No Lacuna hypothesis targets connectome-derived robot controllers.
- Query "mushroom body few-shot learning robot": 26 hits, none about mushroom bodies; closest is few-shot adaptation of robot policies — [Where to Adapt When Objects Move: Localizing Few-Shot Fixes for Robot Policies](https://lacuna.tiptreesystems.com/hypothesis/where-to-adapt-when-objects-move-localizing-few-shot-fixes-for-robot-policies-6591e3909a578dc2). It proposes that a robot policy failure after object relocation sits in the action pathway, not perception, and that a cheap probe on 1–5 demos can say which module to adapt (VERIFIED: read the proposal text).
- Query "neuromodulation internal state robot controller": 1,344 loose hits, none about neuromodulation of robots (top: LLM-written controllers, "Spline Dose-Response Objectives for Deep Neuromodulation" = clinical). Direction effectively absent — VERIFIED via search_lacuna.
- Query "insect fly vision robot perception looming detection" and "spiking looming detector event camera robot collision" surface four relevant proposals, all VERIFIED by reading them:
  - [Rendering Expected Looming: Map-Checked Time-to-Contact for First-Person Cameras](https://lacuna.tiptreesystems.com/hypothesis/rendering-expected-looming-map-checked-time-to-contact-for-first-person-cameras-ba5166a6ca1f8c60): rotation contributes a depth-independent divergence 3(y·wx − x·wy) to optical expansion, so camera rotation can be subtracted exactly; the proposal's 2D TTC baselines (Binary TTC etc.) break under sharp rotations. (I re-derived the divergence formula from the standard rotational-flow equations: it is correct.)
  - [Homeostatic Spiking Inputs for Zero-Shot Event-Camera Control](https://lacuna.tiptreesystems.com/hypothesis/homeostatic-spiking-inputs-for-zero-shot-event-camera-control-9a5b2d4c4f5443c1): first layer of spiking neurons whose thresholds adapt online to local event rate, so a policy trained on one sensor transfers to another without wide randomisation; it explicitly lists "hand-coded normalisation + ordinary network" as the main rival that might tie.
  - [Do Dendritic Coincidence Detectors Survive the Event-Camera Reality Gap?](https://lacuna.tiptreesystems.com/hypothesis/do-dendritic-coincidence-detectors-survive-the-event-camera-reality-gap-d5ab83b9f0cc0fd5): coincidence (AND) terms reject uncorrelated sensor noise but scale with rate squared; divisive normalisation by recent branch activity is the proposed fix.
  - [Spiking Event-Camera Receivers That See Optical Blockages Coming](https://lacuna.tiptreesystems.com/hypothesis/spiking-event-camera-receivers-that-see-optical-blockages-coming-2938968486791286): events from an occluder's approaching edge predict loss of line of sight; relevant mainly as a sensor-physics analogy.
- Query "biologically inspired insect-brain control of robot manipulator spiking": top hits generic spiking robot policies, e.g. [Streaming Spiking Trunks for Cross-Embodiment Robot Policies](https://lacuna.tiptreesystems.com/hypothesis/streaming-spiking-trunks-for-cross-embodiment-robot-policies-77736adfba8ac021) (energy tracks scene change, not control rate; the proposal itself says change-gated quantised nets may tie) — VERIFIED.
- "Subtracting the Hand's Own Motion": [event-based slip sensing in occluded dexterous grasps](https://lacuna.tiptreesystems.com/hypothesis/subtracting-the-hand-s-own-motion-event-based-slip-sensing-inside-occluded-a17ccc56b94fdc43) — the robot predicts the events its own fingers will cause (efference copy) and treats the residual as evidence of slip; cites a prior finding that feeding joint states into a visual model made it take shortcuts, so proprioception is used to "explain away" input — VERIFIED.
- "Committing to a Wiring Layout Before Training": [proposal](https://lacuna.tiptreesystems.com/hypothesis/committing-to-a-wiring-layout-before-training-d9444f83b9d2eb02) — its gating experiment "rewind weights, keep the final wiring layout, retrain" separates benefit that lives in the layout from benefit that lives in training dynamics — VERIFIED.
- One hit is pure noise for FlyMind: "Rerandomized Connectome Releases" concerns human fMRI connectome privacy, not fly wiring — VERIFIED, ignore. Likewise "Does a Body's Internal Composition Decide How It Should Be Controlled?" is human body-composition simulation — ignore.

### Inferences
- The absence of any on-topic hypothesis is itself a signal of a Lacuna blind spot (biology-first work is published in Nature/Cell/bioRxiv, which Lacuna covers thinly), not proof that the field is empty. It cannot be used to claim novelty on its own.
- Three real "bridges" exist between Lacuna's ML proposals and what FlyMind already has: sensor-statistics invariance (event cameras ↔ fly lamina/T4-T5), self-motion vs object-motion (optical expansion/rotation ↔ LPLC2 looming + wrist-camera rotation), and efference-copy cancellation (self-generated events ↔ arm's own motion).

### Gaps
- Lacuna hypotheses were not checked for the key terms "MaleCNS", "FlyWire", "Kenyon" because the engine ranks lexically and returned generic ML items; no proposal explicitly uses a connectome as a prior.
- get_hypothesis returns no abstract fields ("abstract" empty) and no evidence of peer review; none of the proposals has been run by anyone.

## 2. Clusters: which directions are saturated vs sparse?

### Takeaway
Spiking-network energy/efficiency, event-camera representation learning, neuromorphic hardware gaps and visual self-occlusion in manipulation are crowded (hundreds to >1,500 papers each). The directions that touch FlyMind's distinctive ground — time-to-contact from expansion, cancelling self-generated sensory input, predictive sensorimotor control, wiring-cost/topographic organisation — hold only ~15–30 papers each in Lacuna.

### Cited Findings
Saturated (n_papers as shown by search_lacuna, 2026-11-12; VERIFIED):
- [Energy Efficient Computing with Spiking Neural Networks](https://lacuna.tiptreesystems.com/direction/energy-efficient-computing-with-spiking-neural-networks-23868) — 1,555 papers.
- [Surrogate Gradient Learning for SNNs](https://lacuna.tiptreesystems.com/direction/surrogate-gradient-learning-for-spiking-neural-networks-24429) — 589; [Low Latency SNN Inference](https://lacuna.tiptreesystems.com/direction/low-latency-spiking-neural-network-inference-23852) — 410.
- [Asynchronous Perception with Event Cameras](https://lacuna.tiptreesystems.com/direction/asynchronous-perception-with-event-cameras-23862) — 421; [Spatio-Temporal Aggregation for Event-Based Vision](https://lacuna.tiptreesystems.com/direction/spatio-temporal-aggregation-for-event-based-vision-17929) — 285.
- [Closing the Neuromorphic Hardware Deployment Gap](https://lacuna.tiptreesystems.com/direction/closing-the-neuromorphic-hardware-deployment-gap-25184) — 776.
- [Overcoming Visual Self Occlusion in Robotic Manipulation](https://lacuna.tiptreesystems.com/direction/overcoming-visual-self-occlusion-in-robotic-manipulation-26808) — 1,284.
- [Translating Static Connectomes into Dynamic Functional Models](https://lacuna.tiptreesystems.com/direction/translating-static-connectomes-into-dynamic-functional-models-19037) — 349 (mostly human/neuro-imaging flavour; INFERRED from title/top terms only).
- [Bridging the Correlational Causal Gap in Neuroscience](https://lacuna.tiptreesystems.com/direction/bridging-the-correlational-causal-gap-in-neuroscience-18302) — 513.

Moderate: [Divisive Normalization for Adaptive Gain Control](https://lacuna.tiptreesystems.com/direction/divisive-normalization-for-adaptive-gain-control-4786) — 145; [Neuromechanical Entrainment for Adaptive Locomotion (CPGs)](https://lacuna.tiptreesystems.com/direction/neuromechanical-entrainment-for-adaptive-locomotion-13716) — 156.

Sparse (VERIFIED counts):
- [Time to Contact Estimation from Visual Expansion](https://lacuna.tiptreesystems.com/direction/time-to-contact-estimation-from-visual-expansion-1118) — 16 papers (top terms include "visual looming estimation", "event-driven proportional control").
- [Canceling Self Generated Noise with Internal Forward Models](https://lacuna.tiptreesystems.com/direction/canceling-self-generated-noise-with-internal-forward-models-8617) — 25; [Predictive Sensorimotor Control via Internal Forward Models](https://lacuna.tiptreesystems.com/direction/predictive-sensorimotor-control-via-internal-forward-models-8618) — 28.
- [Mitigating Ego-Motion Noise in Event-Based Vision](https://lacuna.tiptreesystems.com/direction/mitigating-ego-motion-noise-in-event-based-vision-24896) — 14.
- [Topographic Neural Organization via Distance Dependent Regularization](https://lacuna.tiptreesystems.com/direction/topographic-neural-organization-via-distance-dependent-regularization-6222) — 23; [Overlapping Neural Circuits in Motor Control](https://lacuna.tiptreesystems.com/direction/overlapping-neural-circuits-in-motor-control-4397) — 7.
- [Bidirectional Alignment of Biological and Artificial Intelligence](https://lacuna.tiptreesystems.com/direction/bidirectional-alignment-of-biological-and-artificial-intelligence-7411) — 35 (the "neuroscience-informed AI" umbrella is small in Lacuna).

No cluster exists for "connectome-derived robot controller", "mushroom body", or "neuromodulation of robot controllers" (searches returned generic SNN/RL clusters) — VERIFIED.

### Inferences
- Do not pitch FlyMind on "spiking = energy efficient" or "event cameras": those lanes are saturated (INFERRED from cluster sizes) and our sim evidence does not address them.
- Sparse + biologically natural: looming/expansion, reafference cancellation, ego-motion vs object-motion — each lines up with an existing FlyMind or fly-eye-plan component (LPLC2/LC4 loom, wrist rotation, arm's own motion).

### Gaps
- Cluster sizes are Lacuna's own counts, which may exclude bioRxiv/neuroscience papers, so "sparse" means sparse within the ML corpus.

## 3. Novelty check: is "a connectome-derived Drosophila spiking network controls a robot arm, tested against shuffled, mirrored and classical controls" new?

### Takeaway
PARTIALLY DONE. Connectome-derived fly networks driving simulated bodies/agents, including shuffled/rewired controls, already exist as preprints and community code (Sept–Nov 2026). I found no work that drives a robot ARM with a connectome-derived network, none with mirrored controls, none with strength-matched shuffle ensembles, and none that reports the data net failing to beat shuffles on a task. The robot-arm + honest-controls combination is OPEN as far as these searches reach (Lacuna, arXiv abstract pages, web search, Europe PMC, one curated GitHub list — not exhaustive).

### Cited Findings
- Closest peer-reviewed substrate: whole-brain LIF model from the FlyWire connectome, Shiu et al., Nature 2024, DOI 10.1038/s41586-024-07763-9 — REPORTED via [Lacuna record](https://lacuna.tiptreesystems.com/work/a-drosophila-computational-brain-model-reveals-sensorimotor/version/art_8bfe965ce3a446abb5df764b59745ecb).
- Closest paper in Lacuna: Gao, "From Connection Loss to Collision: Closed-Loop Fault Assessment of a Fly-Connectome SNN", arXiv [2611.06940](https://arxiv.org/abs/2611.06940), 31 Oct 2026 ([Lacuna](https://lacuna.tiptreesystems.com/work/from-connection-loss-to-collision-closed-loop-fault)). Uses the Shiu LIF model (138,639 neurons, FlyWire v783) in a synthetic pursuit-escape plant, compares proportional vs relay control laws, deletes up to 50% of connection rows (11/48 collisions proportional vs 0/48 relay). Not a robot, no shuffle controls in the summary — VERIFIED from Lacuna full summary and arXiv abstract page; full PDF not opened.
- [FlyCNS](https://arxiv.org/abs/2609.28816) (Zhang, Lin, Lu, 23 Sep 2026): Drosophila-connectome-inspired information routing for a Unitree Go1 in simulation; the connectome is only a weak prior on communication budget, policies learned with RL — VERIFIED (abstract page).
- [Humanoid Locomotion with a Fly-Inspired Recurrent Controller](https://arxiv.org/abs/2609.27001) (22 Sep 2026): 3,609 continuous states, simulated Unitree G1, 61/63 conditions vs 62/63 privileged reference; page does not say it is connectome-derived — VERIFIED (abstract page).
- [Kuklev, arXiv 2609.24565](https://arxiv.org/abs/2609.24565) (21–22 Sep 2026): frozen fly visual-system connectome model on architectural drawings; rewiring that preserves degrees/type pairs/signs cost 0.271–0.356 accuracy across 3 seeds, but the intact circuit did not beat its own moving retina and task-trained CNNs won on clean data (0.971–0.980 vs 0.835) — VERIFIED (abstract page). This is the closest published "wiring matters but trained nets still win" honesty precedent.
- Community MaleCNS projects (not peer-reviewed): [fly-self-driving](https://github.com/suanmiao/fly-self-driving) — full MaleCNS graph (165,122 neurons, 25,563,197 synapses), steering a simulated car from a 64×32 image; learns one gain per synapse and one leak per neuron (25,728,319 parameters), frozen random pixel map into 4,114 optic-lobe neurons, frozen random readout from 708 ventral-cord neurons; randomly rewired graph 16/20 (traffic) and 18/20 (no traffic) vs main model 19–20/20, MLP 18/20 and 20/20; "one training seed per condition"; built Sept 2026 — VERIFIED (README fetched). [fly-cartpole](https://github.com/Curt-Park/fly-cartpole) — 5,459-neuron MaleCNS flight-stabilisation circuit, CartPole: wiring only 275.6 ± 9.4, self-tuned 499.9 ± 0.3, shuffled connections 165.9 ± 182.8, random pushes 22.1 ± 0.8; five sensor gains learned; author attributes most of the wiring's contribution to pathway signs — VERIFIED (README fetched, no date shown). Other items from the curated list ([awesome-fly](https://github.com/cobanov/awesome-fly)) — flyhard, fly-swing, flydoom (one repo "compares a MaleCNS-constrained controller against rewired and conventional networks"), Closed-Loop Fly — are REPORTED (list author's one-line summaries, not independently verified; the eganeganegan/flydoom URL returned 404 when fetched).
- Embodied-fly platforms: NeuroMechFly v2, Nature Methods 2024, DOI 10.1038/s41592-024-02497-y; flybody "Whole-body physics simulation of fruit fly locomotion", Nature 2025, DOI 10.1038/s41586-025-09029-4 — VERIFIED metadata via Europe PMC. Connectome-constrained fly visual network: Lappalainen et al., Nature 2024, DOI 10.1038/s41586-024-07939-3, PMID 39261740 — VERIFIED metadata via Europe PMC.
- Company claims of a "connectome brain in a NeuroMechFly body" (Eon Systems) — REPORTED only via press ([Glitchwire](https://glitchwire.com/news/odyssey-drops-a-fruit-fly-brain-into-its-world-model-and-lets-it-fly/), [Futurism](https://futurism.com/science-energy/research-fly-brain-matrix)); dataset (FlyWire vs MaleCNS) unspecified. Not used as evidence.
- Non-connectome fly-inspired looming and mushroom-body robotics are older and established: Zhao et al., "A fly inspired solution to looming detection for collision avoidance", iScience 2023, DOI 10.1016/j.isci.2023.106337 (virtual-robot tests; VERIFIED abstract via Europe PMC); Ardin et al., "Using an Insect Mushroom Body Circuit to Encode Route Memory in Complex Natural Environments", PLoS Comput Biol 2016, DOI 10.1371/journal.pcbi.1004683 (VERIFIED metadata).
- Hand-designed Drosophila-flight-inspired spiking circuit on a 2-DoF robot arm with dopamine-modulated STDP exists (ScienceDirect S1746809419302216, found via web search; REPORTED, abstract snippet only): so "fly-inspired circuit on an arm" is not new; "connectome-derived (MaleCNS) circuit on an arm with null controls" is what I did not find.

### Inferences
- Verdict by component: (a) connectome-derived fly SNN in closed loop with a simulated body — DONE (preprints/community, Sept–Nov 2026); (b) shuffled/rewired control — PARTIALLY DONE (fly-self-driving, fly-cartpole, Kuklev; typically one shuffle or 3 seeds); (c) mirrored control, strength-matched shuffle ensembles (FlyMind: 10 matched shuffles, 4 to 102 vs 90 for data), preregistered seeds, a real SO-101 arm — OPEN in what I found; (d) honest negative result on the grasp task — unusual; Kuklev is the only close precedent.
- Pitch consequence: claim "first" only for the specific combination, phrased as "we found no prior work" with the search scope stated. Never claim "first connectome controller".
- fly-self-driving trains 25.7M synapse gains by DAgger, FlyMind keeps data-derived weights and lets the circuit decide; under Adam's rule (3 Nov 2026) this is a real design difference, though it also means FlyMind's circuit performs worse than a fully trained one (INFERRED).
- fly-self-driving feeds pixels through a frozen random map into optic-lobe neurons; whether Adam would call that "natural senses" is his ruling (his 12 Nov ruling on the colour encoder suggests it might also be judged artificial stimulation; INFERRED).

### Gaps
- Did not open the PDF of arXiv 2611.06940; the shuffle/mirror question for it rests on the abstract and Lacuna summary.
- Peer-reviewed literature on "connectome-derived network + robot arm" was searched only through Europe PMC title queries, Lacuna and web search; a Google Scholar/Semantic Scholar sweep was not run.
- Eon Systems and Odyssey claims could not be verified (press only).

## 4. Selected proposals (7), ranked for a high-school project with one SO-101 arm, a MacBook M1 Max and MaleCNS data

### Takeaway
Best fit: P1 (audit kit + what in the wiring matters), P2 (camera-statistics invariance of the fly-eye front end) and P3 (looming vs own rotation) — all can start data-only or in simulation with the FaceTime camera, and all respect "the circuit decides, inputs via natural senses". P4 (reafference) and P5 (mushroom-body localised learning) are the most original but need an Adam ruling on where classical code may sit. P6/P7 are speculative. Everything below is PROPOSED; nothing is approved or run.

### Cited Findings
Selection rule: Lacuna permalink where an ML proposal exists; for fly-side parts I name concepts and mark them INFERRED because Lacuna has no fly-side record.

**P1. Connectome Controller Audit Kit + "what in the wiring matters" decomposition** (rank 1)
- Lacuna anchors: [Committing to a Wiring Layout Before Training](https://lacuna.tiptreesystems.com/hypothesis/committing-to-a-wiring-layout-before-training-d9444f83b9d2eb02) (layout vs dynamics test), cluster [Topographic Neural Organization via Distance Dependent Regularization](https://lacuna.tiptreesystems.com/direction/topographic-neural-organization-via-distance-dependent-regularization-6222) (23 papers, sparse).
- Bridged concepts: wiring layout/sign/topology ↔ shuffled, mirrored and strength-matched controls; tooling ↔ reusable test harness (community repos run one seed per condition: fly-self-driving README; fly-cartpole shuffle 165.9 ± 182.8).
- Minimal first experiment (simulation, uses existing V5 loop, new preregistered seeds): replace "shuffle" by a ladder — weights-only shuffle, sign-preserving, degree-preserving, type-pair-preserving, mirror — and report which rung removes the 38/40 result (data net 38/40, shuffled 3/40, mirrored 0/40 from project context). Output: a one-page audit table plus a small open script others can run on any MaleCNS circuit.
- Why humans overlook it: papers report the win of the intact circuit; controls are an afterthought (Kuklev 2609.24565 is the exception) and tooling does not earn citations.
- Feasibility: simulation/data-only; zero hardware. Rule compatibility: full (analysis of controls, no stimulation change). Risk: seeds must be new; needs Adam's approval of a pre-registration.
- Evidence level: Lacuna side REPORTED (proposal), precedent VERIFIED.

**P2. Camera-statistics invariance for the fly-eye front end (lamina-like adaptation + T4/T5-like coincidence)** (rank 2)
- Lacuna anchors: [Homeostatic Spiking Inputs for Zero-Shot Event-Camera Control](https://lacuna.tiptreesystems.com/hypothesis/homeostatic-spiking-inputs-for-zero-shot-event-camera-control-9a5b2d4c4f5443c1), [Do Dendritic Coincidence Detectors Survive the Event-Camera Reality Gap?](https://lacuna.tiptreesystems.com/hypothesis/do-dendritic-coincidence-detectors-survive-the-event-camera-reality-gap-d5ab83b9f0cc0fd5); cluster [Divisive Normalization for Adaptive Gain Control](https://lacuna.tiptreesystems.com/direction/divisive-normalization-for-adaptive-gain-control-4786) (145, moderate), [Mitigating Ego-Motion Noise in Event-Based Vision](https://lacuna.tiptreesystems.com/direction/mitigating-ego-motion-noise-in-event-based-vision-24896) (14, sparse).
- Bridged concepts: sensor sim-to-real mismatch (contrast threshold, noise, hot pixels) ↔ photoreceptor/lamina gain adaptation and the motion core's correlator (coincidence) stage in the fly-eye plan O0–O6 (INFERRED mapping; plan exists on paper only).
- Minimal first experiment (data + webcam, no arm): record 3 clips of the same hand/object motion with different exposure/contrast on the FaceTime camera; run the planned retina→motion front end with and without an adaptation stage; measure how much the LPLC2/LC4 readouts drift across the 3 conditions. Prediction from the Lacuna proposal: normalisation flattens the drift; falsifier: a fixed hand-coded normaliser ties it (the proposals themselves name this as the likely rival).
- Why overlooked: ML teams treat sensor mismatch as an augmentation problem; fly neuroscientists do not test camera-like input statistics.
- Feasibility: simulation/webcam. Rule compatibility: good — camera is a natural sense; adaptation must be part of the retina/lamina model (neurons in data), not a classical pre-filter, otherwise it is classical code deciding (flag for Adam).
- Evidence level: Lacuna REPORTED; fly mapping INFERRED.

**P3. Looming vs own-rotation: can the fly loom circuit tell "something is coming" from "my wrist turned"?** (rank 3)
- Lacuna anchors: [Rendering Expected Looming](https://lacuna.tiptreesystems.com/hypothesis/rendering-expected-looming-map-checked-time-to-contact-for-first-person-cameras-ba5166a6ca1f8c60); cluster [Time to Contact Estimation from Visual Expansion](https://lacuna.tiptreesystems.com/direction/time-to-contact-estimation-from-visual-expansion-1118) (16 papers, sparsest on-topic).
- Bridged concepts: optical expansion/divergence and its rotation term ↔ LPLC2/LC4 loom detection and the wrist camera's own rotation. Documented fly-inspired looming models already exist (Zhao et al. iScience 2023, DOI 10.1016/j.isci.2023.106337); open is the arm-mounted-camera ego-rotation false-alarm test with a connectome-derived readout.
- Minimal first experiment (simulation, after fly-eye plan stage with LPLC2 exists): stimulus set A = pure camera rotation (yaw/pitch sweeps), B = true looming at known time-to-contact, C = both; measure false loom rate of LPLC2→DNp01 on A. Use the analytic fact that rotational divergence = 3(y·wx − x·wy) (derived/checked by me) to define the "classical subtraction" baseline against which the circuit's own behaviour is compared (comparison only, not in the loop).
- Why overlooked: forward-driving datasets dominate TTC work; the Lacuna proposal itself says current estimators break under sharp rotation and bumps.
- Feasibility: simulation (stimuli synthetic) then FaceTime camera clip. Rule compatibility: good if only the circuit decides stop/loom; the subtraction baseline must not enter the loop.
- Evidence level: Lacuna REPORTED; formula VERIFIED by derivation; fly mapping INFERRED.

**P4. Reafference: the arm's own motion as an efference-copy input to the fly circuit** (rank 4)
- Lacuna anchors: [Subtracting the Hand's Own Motion](https://lacuna.tiptreesystems.com/hypothesis/subtracting-the-hand-s-own-motion-event-based-slip-sensing-inside-occluded-a17ccc56b94fdc43); clusters [Canceling Self Generated Noise with Internal Forward Models](https://lacuna.tiptreesystems.com/direction/canceling-self-generated-noise-with-internal-forward-models-8617) (25) and [Predictive Sensorimotor Control via Internal Forward Models](https://lacuna.tiptreesystems.com/direction/predictive-sensorimotor-control-via-internal-forward-models-8618) (28), both sparse; saturated neighbour: [visual self-occlusion in manipulation](https://lacuna.tiptreesystems.com/direction/overcoming-visual-self-occlusion-in-robotic-manipulation-26808) (1,284).
- Bridged concepts: corollary discharge / efference copy ↔ arm's own gripper/finger motion flooding the camera. Fly-side route PROPOSED: commanded joint velocity enters as proprioception (a natural sense per Adam's rule), and the cancellation must be done by circuit pathways, not by classical subtraction.
- Minimal first experiment (data-only): census in MaleCNS of pathways from proprioceptive/leg-sensory neurons (FeCO, already mapped in FlyMind) to optic-lobe or LPLC2-input cell types; count them against degree-matched random sources. If absent, the idea is dead cheaply. (I did not verify any such pathway; this is a pure PROPOSED test.)
- Why overlooked: robotics does cancellation analytically; fly-connectome people study vision and locomotion separately.
- Feasibility: data-only first; simulation later. Rule compatibility: delicate — the Lacuna version subtracts in classical code, which violates the top rule; only the circuit-based variant is admissible. Needs Adam's ruling.
- Evidence level: Lacuna REPORTED; fly side entirely PROPOSED.

**P5. Mushroom-body-style "fix only the module that broke" few-shot learning** (rank 5)
- Lacuna anchor: [Where to Adapt When Objects Move](https://lacuna.tiptreesystems.com/hypothesis/where-to-adapt-when-objects-move-localizing-few-shot-fixes-for-robot-policies-6591e3909a578dc2). Lacuna has no mushroom-body hypothesis or cluster (VERIFIED absence); prior art for the robot side: Ardin et al. 2016 (DOI 10.1371/journal.pcbi.1004683).
- Bridged concepts: localising adaptation to one module ↔ fly learning concentrated in the Kenyon cell–MBON synapses gated by dopaminergic neurons (FlyMind leaves 4064 Kenyon cells, 97 MBON, 340 DAN unused — project context).
- Minimal first experiment (data-only, then sim): trace from the touch/FeCO pathways already in FlyMind to DANs and to the MBONs they gate; test whether a touch-evoked "tag" reaches a compartment that projects (through MBON) to descending neurons already driving the gripper. A negative path census closes the idea at zero cost.
- Why overlooked: ML few-shot work tunes adapters; mushroom-body robotics is mostly olfaction/route memory; nobody pairs a MaleCNS-derived MB with arm grasping.
- Feasibility: data-only → simulation; a plasticity rule is classical code implementing a biological rule — compatibility with "the circuit decides" PROPOSED to be put to Adam. Highest originality, highest risk; probably out of reach by 1 Dec.
- Evidence level: Lacuna REPORTED; MB mapping INFERRED.

**P6. Internal-state gain as the only "context" channel** (rank 6, speculative)
- Lacuna: no on-topic hypothesis or cluster for neuromodulation of robot controllers (VERIFIED absence); generic "state space" RL clusters only.
- Idea: one scalar state (e.g., recent-touch history or arousal-like variable) modulating gain of loom/stop pathways through modulatory cell types present in MaleCNS; it is the biologically honest replacement for W3 (small frozen VLM modulating eye sensitivity) discussed in the project. PROPOSED.
- First experiment: data-only count of modulatory (aminergic) inputs onto LPLC2/DNp01 vs shuffle. Rule compatibility: fine if state derives from natural senses; weak evidence base.

**P7. Honest energy/latency accounting as a side metric (not a headline)** (rank 7, "saturated lane" warning)
- Lacuna anchors: [Streaming Spiking Trunks](https://lacuna.tiptreesystems.com/hypothesis/streaming-spiking-trunks-for-cross-embodiment-robot-policies-77736adfba8ac021) (own text: change-gated dense nets may match), clusters [Energy Efficient Computing with SNNs](https://lacuna.tiptreesystems.com/direction/energy-efficient-computing-with-spiking-neural-networks-23868) (1,555 papers) and [Closing the Neuromorphic Hardware Deployment Gap](https://lacuna.tiptreesystems.com/direction/closing-the-neuromorphic-hardware-deployment-gap-25184) (776).
- Minimal experiment (simulation): log synaptic events per control step against scene change using the existing loop (project reports touch→command median 1.29 ms); compare with a change-gated dense net. Do not claim energy savings: no neuromorphic hardware, and the lane is crowded.

### Inferences
- Order of work if Adam approves any: P1 (audit; reuses finished sims, strongest for judges and for "honest science"), then P2→P3 (both live inside the fly-eye plan and use the camera already owned), then P4 data census (cheap kill test).
- Investor/competition angle (INFERRED): a published, reusable audit kit plus one clean negative-or-positive result on the fly eye is more defensible than any performance claim; community repos show the niche is active but uses single seeds.
- Nothing here changes the earlier verified limits: all results are MuJoCo simulation, no real-arm test, touch sensors sim-only.

### Gaps
- None of the Lacuna proposals has been tested by anyone; their baselines and numbers are theirs, not ours.
- MaleCNS pathway claims in P4–P6 were not checked against data this session (rule: do not run analyses); they are census proposals, not facts.
- Hardware feasibility beyond the FaceTime camera is unknown; no event camera is owned (OV9281/GenX320 are only candidates per project notes), so every P2/P3 test must use ordinary frames, not real events.
