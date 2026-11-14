# Topic 6: Novelty check and research map (Lacuna / Alien Space of Science)

Method note: Lacuna MCP tools loaded and worked (VERIFIED: calls returned data on 2026-11-13). Lacuna covers ML/AI only; neuroscience hits are partial. Lacuna metadata = REPORTED. Searches run: ~12 (paper/cluster/hypothesis). No local pipeline code run. Lacuna has no citation graph, so "absence" below = absence in a keyword/semantic search, not proof.

## 1. Novelty check: connectome-derived Drosophila SNN decides high-level commands via natural senses; fixed hand-designed spiking "spinal" layer (antagonist pairs per joint) drives a 6-DOF arm; causal controls measure who decides

### Takeaway
Verdict: PARTIALLY DONE (INFERRED). Each ingredient has prior work (connectome-driven fly models, whole-fly body simulation, spiking arm control with antagonist-style populations), but I found no paper combining them: a connectome SNN as the decider + fixed spiking translator + a non-fly robot arm + shuffle/relay/silencing controls on "who decides". The control part (strength-preserving shuffles, trivial relays) is the least covered, but that is a keyword-search absence only. Our own red-team result (lateralisation, not topology) means the "connectome decides" claim is currently not supported even if the combination is open.

### Deconstruction (INFERRED)
- Problem: attribute control decisions to a biological circuit versus designed glue in a hybrid brain-body controller; embodied use of a real connectome for a non-native body.
- Method: connectome-derived ALIF SNN, fixed hand-built spiking motor layer (antagonist pairs), causal controls (silencing, strength-preserving shuffle, trivial relay).
- Domain: Drosophila MaleCNS, SO-101 6-DOF arm in MuJoCo.

### Cited Findings
Closest prior work, per ingredient:
- Connectome as controller of an embodied fly (graph NN, not spiking): flyGNN uses the FlyWire graph as unweighted directed graph, trained by imitation of a flybody MLP teacher in MuJoCo; reproduces gait initiation, straight walking, turning; authors list dropped synapse weights/neurotransmitters and locomotion-only scope as limits. Jin and Sui, DBM @ NeurIPS 2025 (REPORTED, read: Lacuna summary only; a teacher-trained student, so decisions are learned not wired) — [Lacuna](https://lacuna.tiptreesystems.com/work/whole-brain-connectomic-graph-neural-networks-enable-whole/version/art_09437fe0f3f7424797a64790108ec78d) ; [OpenReview](https://openreview.net/forum?id=KFmIRruzvL)
- Whole-brain LIF model from the connectome predicting sensorimotor processing (Shiu et al., Nature 2024): existence and metadata VERIFIED via Crossref (title, year 2024, first author Shiu). Content not read by me. — [DOI](https://doi.org/10.1038/s41586-024-07763-9)
- Connectome-constrained networks predicting activity in the fly visual system (Lappalainen et al., Nature 2024): existence VERIFIED via Crossref — [DOI](https://doi.org/10.1038/s41586-024-07939-3)
- Whole-body physics fly model (Vaxenburg et al., Nature 2025): existence VERIFIED via Crossref (title "Whole-body physics simulation of fruit fly locomotion") — [DOI](https://doi.org/10.1038/s41586-025-09029-4). NeuroMechFly v2 (Wang-Chen et al., 2024): VERIFIED via Crossref — [DOI](https://doi.org/10.1038/s41592-024-02497-y)
- Spiking LIF model of the fly optic lobe from the connectome, orientation maps emerge from wiring (first author Liew per Lacuna text): arXiv record exists, 2609.01330, published 2026-09-01 (VERIFIED via arXiv API; authors not read). Lacuna lists the same title as NeurIPS 2025 on OpenReview, a date mismatch I did not resolve (NOT VERIFIED which is the primary version). — [arXiv](https://arxiv.org/abs/2609.01330) ; [Lacuna](https://lacuna.tiptreesystems.com/work/connectome-based-modelling-reveals-orientation-maps/version/art_81ac3b3bfe0d4c28bdba11929ffe9160)
- Recent fly-connectome-on-hardware/robotics adjacent items found by arXiv API (titles only; REPORTED, not read): FPGAFly, 166.7k-neuron fly connectome on one FPGA (2610.38118, 2026-10-28) — [arXiv](https://arxiv.org/abs/2610.38118). Not a robot arm, but is the nearest "fly connectome SNN on neuromorphic-style hardware" item.
- Spiking arm control with designed population structure: Spaun-style adaptive arm control, DeWolf et al., Proc. R. Soc. B 2016, existence VERIFIED via Crossref; 111 citations per Lacuna (REPORTED) — [DOI](https://doi.org/10.1098/rspb.2016.2134). Many-joint arm control with recurrent SNN (IROS 2021) — [Lacuna](https://lacuna.tiptreesystems.com/work/many-joint-robot-arm-control-with-recurrent-spiking/version/art_16a53cca1f104ead9c30a39dd67475e9). Adaptive arm control with spiking RNN on digital accelerator, arXiv 2405.12849 (VERIFIED via arXiv API, 2024-05-21) — [arXiv](https://arxiv.org/abs/2405.12849). All are designed/learned, not connectome-derived.
- Survey of SNN robot control (Bing et al., Front. Neurorobotics 2018; VERIFIED via Crossref) — [DOI](https://doi.org/10.3389/fnbot.2018.00035)
- Population-coded SNN for continuous control (Tang et al., CoRL 2020; 137 cit. per Lacuna, REPORTED) — [Lacuna](https://lacuna.tiptreesystems.com/work/deep-reinforcement-learning-with-population-coded-spiking/version/art_0e7a037ae52c428cbc1d03f27247694e)
- Lacuna cluster for the structure-function problem ("Translating Static Connectomes into Dynamic Functional Models", 349 papers): explicitly frames connectome-to-behaviour as open, notes static wiring does not reveal function, and mentions causal "effectome" work using the connectome as prior (REPORTED, read: Lacuna cluster summary) — [Lacuna](https://lacuna.tiptreesystems.com/direction/translating-static-connectomes-into-dynamic-functional-models-19037)
- Searches for hypotheses on shuffled-connectivity / topology-versus-statistics controls returned only unrelated items (vessel topology, backdoor ablation); no Lacuna item on rewired-null controls for connectome models (NOT FOUND, so open in Lacuna's ML framing).

### Inferences
- The "who decides" control design (strength-preserving shuffle, trivial relay, silencing) is standard-in-spirit null-model practice in network neuroscience, but I found no connectome-robotics paper applying it. Novelty there is low in method and modest in application. (INFERRED)
- Biggest novelty risk is not a prior paper but our own data: red-team shows a trivial left->left relay gives 20/20 and strength-preserving shuffle 10/10, so the headline claim would not survive a reviewer. (INFERRED from project context)
- Fly-body work (flybody, NeuroMechFly) keeps the connectome and the body inside the same species; a fly-brain-to-foreign-body transfer is the actual gap, and also where translation layers can silently do the deciding. (INFERRED)

### Gaps
- Lacuna does not index neuroscience/robotics journals well (Nature, Nature Methods items not found by name search); novelty cannot be certified from it. A bioRxiv/Europe PMC sweep for "MaleCNS" and "connectome" + "robot arm" is still needed.
- Authors of the Liew et al. paper and the arXiv/NeurIPS date mismatch not resolved.
- Shiu et al. and flybody content not read, only existence confirmed.

## 2. Research map (4 directions)

### Takeaway
SNN control and neuromorphic hardware are saturated on the efficiency/training side; connectome-to-behaviour and "who decides" attribution are open. (INFERRED from Lacuna cluster sizes.)

### Cited Findings
- SNN robot/arm control: saturated on small tasks, thin on honest controls. Leading: DeWolf 2016, Bing 2018 survey, Tang 2020 (links in section 1). Surrounding Lacuna clusters are huge and efficiency-oriented: "Energy Efficient Computing with SNNs" 1555 papers, "Surrogate Gradient Learning" 589, "Low Latency SNN Inference" 410 (REPORTED, Lacuna) — [23868](https://lacuna.tiptreesystems.com/direction/energy-efficient-computing-with-spiking-neural-networks-23868), [24429](https://lacuna.tiptreesystems.com/direction/surrogate-gradient-learning-for-spiking-neural-networks-24429), [23852](https://lacuna.tiptreesystems.com/direction/low-latency-spiking-neural-network-inference-23852)
- Connectome-constrained models: active and growing. Shiu 2024, Lappalainen 2024, Liew (2026 arXiv), flyGNN 2025, plus effectome work (Pospisil et al., via Lacuna cluster text, REPORTED) (links above). Open: embodiment with real synapse signs/weights and causal null controls; flyGNN explicitly drops weights and neurotransmitters.
- Neuromorphic control: Lacuna cluster "Closing the Neuromorphic Hardware Deployment Gap" 776 papers, "Overcoming the Reality Gap in Robotic Control" 834 papers (REPORTED) — [25184](https://lacuna.tiptreesystems.com/direction/closing-the-neuromorphic-hardware-deployment-gap-25184), [28247](https://lacuna.tiptreesystems.com/direction/overcoming-the-reality-gap-in-robotic-control-28247). Open for us: no real-arm test yet (sim only).
- Bio-inspired insect robotics: Lacuna's insect-robot hypothesis search returned only generic robot-controller items, i.e. weak coverage (NOT VERIFIED beyond that). Embodied fly models: NeuroMechFly v2, flybody (VERIFIED existence).

### Inferences
- Saturated: spiking-network efficiency, surrogate-gradient training, conversion. Open: attribution of decisions in hybrid brains; connectome-derived (not learned) deciders in non-native bodies. (INFERRED)

### Gaps
- Citation counts and "leading papers" for insect robotics not obtainable from Lacuna; needs a non-Lacuna search.

## 3. Alien hypotheses (machine-generated: HYPOTHESIS; metadata REPORTED; generated 2026-10-04 per Lacuna)

None is a direct match; Lacuna returned no hypothesis on connectome-controlled robots (search "biological connectome spiking network robot control neuromorphic" gave 1 result, below).

### Cited Findings
- L1, "Context as Threshold: Spiking Networks Whose Firing Rules Encode Biological Context" (id c6ae390947e2d494): proposes folding feature-wise modulation into SNN firing thresholds so context switching costs a closed-form threshold update; tested on protein function retrieval. Relevance to us: the idea that "context" (e.g. neuromodulation, which has no effect in our model) could act through per-neuron thresholds. HYPOTHESIS, weakly relevant, protein domain. — [Lacuna](https://lacuna.tiptreesystems.com/hypothesis/context-as-threshold-spiking-networks-whose-firing-rules-encode-biological-c6ae390947e2d494)
- L2, "Function-Guided Connectome Completion with Discrete Flow Matching" (id 9a0b2a7c568b7d58): proposes asking how much a known function (fly head-direction ring attractor, 439-neuron circuit) constrains wiring, scored by masked-edge recovery against a cell-type block-model baseline; includes a "wrong function" control to rule out reward hacking. Relevance: shows the same many-to-one structure-function problem and a control philosophy similar to our shuffle/relay controls; suggests a cell-type block model as the proper null instead of a plain shuffle. HYPOTHESIS. — [Lacuna](https://lacuna.tiptreesystems.com/hypothesis/function-guided-connectome-completion-with-discrete-flow-matching-9a0b2a7c568b7d58)
- L3, "Screening Robot Controller Structures by How They Fail Early" (id df03531b999b55a0): proposes a cheap early score (10th-percentile return on out-of-range physics) to pick controller structures, noting transfer often depends on structure such as fixed gait plus learned residual. Relevance: our fixed spiking translator plus fly decider is a "structure" choice; its out-of-range-perturbation test resembles our 50 ms delay test. HYPOTHESIS, about learned controllers. — [Lacuna](https://lacuna.tiptreesystems.com/hypothesis/screening-robot-controller-structures-by-how-they-fail-early-df03531b999b55a0)

### Inferences
- L2 gives the most actionable idea: replace plain shuffle with a cell-type-preserving block-model null and add a deliberately wrong-function control. (INFERRED; HYPOTHESIS, untested by us)

### Gaps
- None of L1-L3 has been checked for soundness; Lacuna content is machine-generated. Their cited art_ IDs were not individually verified.
