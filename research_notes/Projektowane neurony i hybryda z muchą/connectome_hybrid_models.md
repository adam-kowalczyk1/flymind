# Connectome-derived networks combined with designed or learned modules in embodied controllers (research topic 2, 2026-11-13)

Method note: metadata of papers was checked via Crossref / Europe PMC APIs (labelled VERIFIED = existence, title, authors, year, abstract text). Results inside papers are REPORTED from abstracts only unless stated; several full texts (nature.com, bioRxiv PDF, eLife, Tuthill PDF) could not be read by the tools (403 / redirect / binary) - these are NOT VERIFIED beyond the abstract. Page summaries obtained through a WebFetch summariser are labelled "secondary/summariser". Nothing was run locally; no repo files modified.

## Q1. Drosophila hybrids: which part is connectome, which designed/learned, where is the interface, what controls proved the data part matters

### Takeaway
Every published fly "brain + body" system I found has a connectome (or connectome-constrained) module bolted to a designed or RL-trained body controller through a small, hand-chosen interface (a few descending neurons as decoder; designed sensory encoders). The only work that directly tests whether the connectome matters in such a chimera (the "digital sphinx") concluded that behavioural fidelity is achievable without biological fidelity. Of the systems below, I found no one reporting a shuffled-connectome control for brain->body behaviour, except as a critique.

### Cited Findings
- NeuroMechFly v2 (Wang-Chen, Stimpfling, Lam, Özdil, Genoud, Hurtak, Ramdya; Nature Methods, 12 Nov 2024; DOI 10.1038/s41592-024-02497-y; VERIFIED metadata): adds vision, olfaction, ascending motor feedback, complex terrain. Abstract (REPORTED, read: abstract) says it builds "biologically inspired" controllers using ascending feedback for path integration and head stabilisation, trains a reinforcement-learning controller for a multimodal navigation task, and illustrates fly-fly following using a connectome-constrained visual network. So: body + controllers are designed/learned; connectome enters only in the visual module (Lappalainen) in one demonstration. The abstract names no shuffle control and no trial counts (full text not read, NOT VERIFIED). — [Europe PMC record](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1038/s41592-024-02497-y&format=json&resultType=core); [DOI](https://doi.org/10.1038/s41592-024-02497-y)
- Lappalainen et al. (Nature, 11 Sep 2024; 10 authors listed in Crossref; DOI 10.1038/s41586-024-07939-3; VERIFIED metadata): connectivity of 64 optic-lobe motion-pathway cell types is fixed from data; single-neuron and single-synapse parameters are unknown and are OPTIMISED by deep learning to make the network detect motion. Model predictions agree with measured activity across 26 studies (REPORTED, read: abstract). The authors state success is more likely when neurons are sparsely connected. This is the template of "connectome fixes structure, training fits non-structural parameters". — [DOI](https://doi.org/10.1038/s41586-024-07939-3)
- Cowley et al. (Nature, 22 May 2024; DOI 10.1038/s41586-024-07451-8; VERIFIED metadata): "knockout training" - a deep network is perturbed during training so units match behavioural effects of silencing real cell types (more than a dozen types). One-to-one mapping of model units to visual projection neurons. Conclusion (REPORTED, read: abstract): combinations of visual projection neurons, including non-social ones, drive male-female interaction (population code), not one channel per behaviour. Relevant for us: it is a way to ANCHOR designed units to real cells using perturbation data, and it contradicts "one channel = one behaviour" (relevant to LC10a-only encoding). — [DOI](https://doi.org/10.1038/s41586-024-07451-8)
- flybody (Vaxenburg et al., Nature 2025, 23 Apr; 14 authors in Crossref; DOI 10.1038/s41586-025-09029-4; VERIFIED metadata): whole-body MuJoCo fly; controllers are neural networks trained with data-driven end-to-end RL, responding to high-level steering commands; hierarchical: a high-level controller trained to reuse a pretrained low-level flight controller for visually guided tasks (REPORTED, read: abstract). No connectome in the controller; it is a body/controller platform, i.e. the "designed/learned" side that connectome brains are plugged into. — [DOI](https://doi.org/10.1038/s41586-025-09029-4)
- Shiu et al. (Nature, 2 Oct 2024; 27 authors; DOI 10.1038/s41586-024-07763-9; VERIFIED metadata): LIF model of the whole adult central brain (>125,000 neurons, 50 M synapses) from connectivity + neurotransmitter identity. Computational activation of sugar/water gustatory neurons predicted neurons required for feeding; predicted motor-neuron-eliciting neurons validated by optogenetics; mechanosensory activation predicted the antennal grooming circuit (REPORTED, read: abstract). Validation compares model activation sets with experiments; it is NOT a closed-loop embodied behaviour, and the abstract reports no shuffled-connectome baseline (full text not read). — [DOI](https://doi.org/10.1038/s41586-024-07763-9)
- Pugliese, Chou, Abe, Turcu, Lancaster, Tuthill, Brunton, "Connectome simulations identify a central pattern generator circuit for fly walking" (bioRxiv 10.1101/2025.09.12.675944, 12 Sep 2025; Crossref also lists a Nature version DOI 10.1038/s41586-026-11195-y dated 28 Oct 2026; VERIFIED metadata, I did not open the Nature page). Abstract (REPORTED, read: abstract): dynamic simulations of VNC connectomes; activation screen of descending neurons found DNg100 as top driver of rhythmic leg motor activity; pruning isolated a 3-neuron rhythm circuit (1 inhibitory + 2 excitatory) "necessary and sufficient" for rhythm across all six legs and four connectome datasets; DNb08 prediction confirmed by optogenetics. Here the connectome IS the mechanism (lesion/pruning = the control), no designed premotor layer. Press summary (secondary, read: The Transmitter): rate-type recurrent model, connectome-only network oscillates without training; limits stated: no left-right coordination, only some motor neurons oscillate strongly, transmitter/biophysics unknown; independent critic R. Berg noted missing reciprocal inhibition. — [bioRxiv](https://doi.org/10.1101/2025.09.12.675944); [Nature DOI (metadata only)](https://doi.org/10.1038/s41586-026-11195-y); [The Transmitter](https://www.thetransmitter.org/systems-neuroscience/long-sought-walking-circuit-found-in-fruit-flies/)
- Independent VNC study (Sapkal et al., bioRxiv 2026, as named by The Transmitter, secondary; I did not locate the preprint itself, NOT VERIFIED): anatomical tracing, a five-neuron repeating network upstream of leg motor neurons, partial overlap with Pugliese circuit; headless-fly behaviour experiments; proprioceptive input needed to coordinate six legs. — [The Transmitter](https://www.thetransmitter.org/systems-neuroscience/long-sought-walking-circuit-found-in-fruit-flies/)
- Eon Systems "embodied brain emulation" page (company, read: summariser of eon.systems page; REPORTED): LIF whole-brain from FlyWire (~140,000 neurons, ~50 M synapses per page; The Register says ~125,000 neurons and Brian2 - numbers differ between sources), connected to NeuroMechFly v2 (87 joints, MuJoCo). Vision: Lappalainen-network activity "injected into matching LIF neurons" (company calls visual activations "decorative", do not substantially affect behaviour). Sensory encoders hand-designed (virtual taste, "dust"); motor decoder = a few descending neurons as handles (DNa01/DNa02 steering, oDN1 forward velocity, MN9 feeding, antennal DNs grooming); brain<->body sync every 15 ms; rate-to-torque/turn mapping "largely chosen by hand"; locomotion from existing NeuroMechFly controllers trained by imitation learning; VNC not included. The page reports NO ablations, controls or quantitative benchmarks and states results do not prove structure alone recovers the repertoire. — [Eon page](https://eon.systems/updates/embodied-brain-emulation)
- Critiques of Eon: S. Furber (via The Register, 16 Mar 2026, read: summariser) called the brain "machine learning, clamped into the shape of a fly connectome" and noted 0 Hz resting state; reporter notes unreported runtime. Carboncopies post argues it is not a functional upload. — [The Register](https://www.theregister.com/a/5224139); [Carboncopies](https://carboncopies.org/Blog/Posts/FruitFlyNotUploaded/Post/) (search snippet only, page not opened, NOT VERIFIED beyond snippet)
- "The digital sphinx: Can a worm brain control a fly body?" (Brunton, Abe, Hu, Tuthill; bioRxiv/eLife reviewed preprint 2026; DOI 10.64898/2026.03.20.713233 as listed by Europe PMC; VERIFIED metadata). Abstract (REPORTED, read: abstract): C. elegans connectome receives fly-body sensory input; an artificial neural network trained with deep RL maps worm motor-neuron activations to fly leg actuators; result "highly realistic fly walking" yet "biologically meaningless"; core peril: behavioural fidelity achievable without biological fidelity. A secondary summary also mentions a random-connectome variant generating realistic locomotion (from The Transmitter via a search summary, NOT VERIFIED; full text not read - eLife page failed to load and PDF was unreadable). — [Europe PMC](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.64898/2026.03.20.713233%22&format=json&resultType=core); [eLife reviews](https://elifesciences.org/reviewed-preprints/111516/reviews)
- Pospisil et al. (Nature 2024, DOI 10.1038/s41586-024-07982-0; VERIFIED metadata, abstract not read): "The fly connectome reveals a path to the effectome" - connectome-to-effect prediction; potentially useful as a validation of influence between neuron sets. — [DOI](https://doi.org/10.1038/s41586-024-07982-0)
- Open fork "malecns-embodied-fly" (Ryans-sS): web search found NO repository under that name or user; found instead related projects using MaleCNS: DesktopFly (github.com/DenisSergeevitch/desktop-fly) and FlySoul (github.com/heyobi/flysoul) - existence from search snippets only, not opened, NOT VERIFIED. — [FlySoul README](https://raw.githubusercontent.com/heyobi/flysoul/HEAD/README.md); [DesktopFly (gitee mirror)](https://gitee.com/rickqi/desktop-fly)

### Inferences
- INFERRED: the FlyMind architecture (encoder into identified cells, DNa02 decoder, classical rest) is the same pattern as Eon / NeuroMechFly v2, and shares their weakness: no published test showing the data wiring beats a generic substitute. Our own shuffle/relay red team already reproduces that critique.
- INFERRED: the strongest "data part matters" evidence in the literature is for circuit-internal mechanisms validated against physiology (Shiu, Pugliese, Lappalainen), not for closed-loop behaviour of a hybrid.
- INFERRED: Pugliese-type VNC rhythm generation is where a connectome could replace our "classical" part (CPG), but it is a leg-walking circuit, which has no direct counterpart in a 6-DOF arm.

### Gaps
- Full texts (NMF v2, Shiu, Lappalainen, Pugliese, sphinx) not read: trial counts and exact controls are unconfirmed. A reader with access should check whether Shiu/Lappalainen tested degree-preserving shuffles.
- No evidence found of any published shuffled-connectome control for a closed-loop hybrid other than the sphinx critique.
- Eon: neuron-count discrepancy (140,000 vs 125,000); whether its controllers are on the critical path is stated by company only.

## Q2. C. elegans and other embodied connectome models

### Takeaway
BAAIWorm is the best-documented closed-loop connectome-based body model, but its brain part is a restricted 136-neuron circuit with biophysical detail, and the abstract-level evidence is only qualitative behaviour reproduction. I found no embodied larval-zebrafish connectome model and no scientifically citable connectome-driven robot demo.

### Cited Findings
- BAAIWorm: Crossref lists "A simulated C. elegans with biophysically detailed neurons and muscle dynamics" (Nature Computational Science 2024, DOI 10.1038/s43588-024-00740-2, author list empty in Crossref; VERIFIED existence). Secondary sources (read: search summaries of PKU/hyper.ai pages): Lei Ma's team, published 16 Dec 2024 as "An integrative data-driven model simulating C. elegans brain, body and environment interactions"; 96 muscle cells in four quadrants; reproduces zig-zag movement toward attractants; 30 fps real-time claim is third party (REPORTED). A later review states the brain part is a restricted sensory-locomotor circuit of 136 neurons, not all 302 (secondary, State of Brain Emulation Report 2025, snippet only). — [DOI](https://doi.org/10.1038/s43588-024-00740-2); [State of Brain Emulation Report 2025](https://arxiv.org/pdf/2510.15745)
- OpenWorm c302 / Sibernetic: I did not retrieve a verifiable source in this session (Crossref query failed). NOT VERIFIED.
- Connectome-driven Lego robot and similar demos: not searched successfully; treat as anecdotal, NOT VERIFIED.
- Larval zebrafish embodied connectome model: query returned nothing in Europe PMC titles (TITLE:connectome AND zebrafish AND embodied: 0 results). NOT VERIFIED that none exists.

### Inferences
- INFERRED: the worm and fly cases confirm the pattern that an embodied connectome model reproduces behaviour with designed body/environment and parameter tuning; the sphinx paper shows this alone cannot show biological meaning.

### Gaps
- BAAIWorm quantitative results and controls, OpenWorm c302 verification, robot demos, zebrafish: not covered (tool budget).

## Q3. Insect-inspired circuits on robots with an engineered motor layer

### Takeaway
In insect-circuit robotics the biologically derived circuit usually outputs a heading/steering signal and an engineered locomotion layer translates it; the decision is in the circuit only for that one variable. I verified only two sources.

### Cited Findings
- Stone et al. (Current Biology 2017; 10 authors; DOI 10.1016/j.cub.2017.08.052; VERIFIED metadata): central complex path-integration circuit with anatomically identified neurons per step; "complete circuit for path integration and steering" that compares current and desired heading to produce a steering signal (REPORTED, read: abstract). The abstract does not mention a robot; robot implementations of this model are not verified here (NOT VERIFIED). — [DOI](https://doi.org/10.1016/j.cub.2017.08.052)
- Dupeyroux, Serres, Viollet, AntBot (Science Robotics 2019, DOI 10.1126/scirobotics.aau0307; VERIFIED metadata): six-legged robot, 14-pixel optical sensors (2 for UV polarisation compass, 12 for optic flow); mean homing error 0.67% reported (REPORTED, read: abstract). This is an ant-INSPIRED algorithm (path integration), not a neural circuit from a connectome; walking is engineered. — [DOI](https://doi.org/10.1126/scirobotics.aau0307)

### Inferences
- INFERRED: in AntBot the algorithm decides heading, hardware translates; there is no spiking circuit. In central-complex models, the circuit decides steering direction, engineered code converts it to motor commands. Both are "translator below decider" - the same split as FlyMind, with the same question of how thin the translation must be.

### Gaps
- Mushroom-body navigation robots, other robot realisations of Stone's model: not searched.

## Q4. Techniques for splicing designed neurons into a data network, and risks of the designed part dominating

### Takeaway
Published techniques: (a) fix connectivity, optimise non-structural parameters (Lappalainen); (b) perturbation-anchored mapping of learned units to cells (Cowley); (c) low-dimensional hand-chosen interface at descending neurons (Eon, NMF v2); (d) RL-trained readout from motor-neuron activity to actuators (sphinx). The sphinx paper is the explicit warning that a trained decoder can produce good behaviour from a meaningless brain.

### Cited Findings
- Training only non-structural parameters while keeping connectivity: Lappalainen et al. (above) - VERIFIED metadata, REPORTED mechanism (read: abstract). — [DOI](https://doi.org/10.1038/s41586-024-07939-3)
- Knockout training to align model units with real cells: Cowley et al. — [DOI](https://doi.org/10.1038/s41586-024-07451-8)
- Learned decoder from connectome motor neurons to body: sphinx paper (the decoder is an ANN trained with DRL; behaviour realistic, biology meaningless) — [Europe PMC](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.64898/2026.03.20.713233%22&format=json&resultType=core)
- Eon states behaviours depend heavily on the body model's existing controllers and the descending interface is a "deliberately low-dimensional readout layer" (REPORTED, read: summariser of company page). — [Eon page](https://eon.systems/updates/embodied-brain-emulation)
- Global synaptic gain J0 per synapse count / per-cell-type fitting in LIF connectome models: I did not retrieve a source in this session. NOT VERIFIED (see existing notes laczenie_modyfikacje.md / lif_model_parameters.md in the repo for earlier material).

### Inferences
- INFERRED: dominance of the designed part is detectable by the swap test: replace the fly module with a generic module of the same input/output interface and matched gain; if performance is equal, the designed interface decides. The sphinx result supports this logic and FlyMind's own relay/shuffle red team is an instance of it.
- HYPOTHESIS: an interface with a narrow bottleneck (2 DNa02 values -> one base angle) is the easiest to dominate by a trivial relay; a wider decoder with matched capacity across fly/shuffled arms would be a fairer test but also invites a learned decoder to do the work.

### Gaps
- No source found discussing J0-type global scaling risks; no paper found on mixing designed spiking neurons into identified cells with a dominance analysis beyond the sphinx and Eon caveats.

## Q5. Body mismatch: fly (6 legs, many muscles) to a 6-DOF arm

### Takeaway
I found no published fly-leg-to-robot-arm or fly-to-arm morphology mapping. Generic cross-morphology motion retargeting exists (human/animal to humanoid/quadruped/manipulator), but those are kinematic/learning methods that do not use fly circuits.

### Cited Findings
- Search for animal-to-robot-arm retargeting returned only adjacent work: STMR for quadrupeds ([arXiv 2404.11557](https://arxiv.org/abs/2404.11557v2)), Human2Humanoid ([arXiv 2606.03476](https://arxiv.org/pdf/2606.03476)), ACE cross-morphology retargeting tested incl. a manipulator and Spot ([ACE listing](https://aitopics.org/doc/arxivorg:27EB1433)). Read: search snippets only, NOT VERIFIED beyond that.
- Fly leg motor circuit data (MANC/MaleCNS VNC) exist, and Pugliese-type models show rhythm from VNC connectomes (above), but no mapping to arm joints is published as far as found.

### Inferences
- INFERRED: any fly-to-SO-101 mapping is a designed translation (choice of which MN/DN pairs stand for which joint) and must be presented as such; flexor/extensor antagonist pairs per leg joint offer a natural pairing per SO-101 joint (HYPOTHESIS, not tested).
- INFERRED: the video's "pos/neg per joint" neuron naming pattern suggests antagonist pairs per joint, consistent with this idea; this is an observation of the video (REPORTED), not a fact about the method.

### Gaps
- No published leg-to-arm mapping; retargeting papers not read beyond snippets.
- Founders, Inc. video (https://youtu.be/NIMEbZJHQBM) not opened; "98% collisions avoided" remains NOT VERIFIED (edit overlay, no trial count or controls).
