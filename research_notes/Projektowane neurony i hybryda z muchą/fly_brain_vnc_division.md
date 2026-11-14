# Drosophila: division of roles between brain and ventral nerve cord (VNC), and an arm-controller analogue

Research only, 2026-11-13. Sources read via Europe PMC (abstracts, and full text via PMC where stated), Crossref metadata. nature.com, biorxiv.org and eLife web pages returned 403/blocked; Lesser 2024 and Azevedo 2024 full texts failed (HTTP 500), so only their abstracts were read. Label for each claim: VERIFIED = publication exists and the stated sentence or number was read by us in the abstract or full text (the scientific result itself is REPORTED by the authors unless noted); everything else is labelled INFERRED / HYPOTHESIS / NOT VERIFIED.

## 1. Descending neurons (DNs) as a bottleneck: counts, command vs population code, direct DN-to-MN fraction

### Takeaway
The neck connective carries only ~1,300 DNs (earlier light-level estimate ~700) from the brain to the VNC, against ~1,860 ascending neurons going back, so the brain-to-body channel is narrow. "Command-like" DNs rarely act alone: they recruit other DNs (population control), and direct DN-to-motor-neuron contacts are sparse, so most motor patterning happens in VNC interneurons.

### Cited Findings
- Namiki et al. 2018 estimated ~350 DNs per side (~700 total; max 356 somata, mean 321 +/- 23, N=4) and described 190 DNs in 98 types, i.e. about half of all DNs; nerve cord is layered into neuropils for walking vs flight. VERIFIED (read: full text via PMC) — [eLife 34272, PMID 29943730](https://doi.org/10.7554/eLife.34272)
- MANC (male nerve cord) neck connective holds 1,328 DNs, 1,862 ANs, 733 MNs (of ~23,500 reconstructed neurons incl. 13,066 INs, 5,927 sensory neurons). VERIFIED (read: full text via PMC) — [Cheong et al., eLife 96084, PMID 42474298](https://doi.org/10.7554/eLife.96084)
- Across three EM datasets (female brain, female nerve cord, male nerve cord): 1,315-1,347 DNs, 1,733-1,865 ANs, 535-611 sensory ascending neurons; 51% of DN cell types matched to light-level driver lines. VERIFIED (read: full text via PMC) — [Stürner et al., Nature 2025, PMID 40307549](https://doi.org/10.1038/s41586-025-08925-z)
- Cheong et al.: direct DN-MN connections are infrequent; coordinated wing+leg action (e.g. take-off) "rarely emerges from monosynaptic connections between DNs and MNs", instead relies on VNC-intrinsic hub neurons with high input and output degree; for lower-tectulum DNs only 13 of 92 gave >=1% of synaptic input onto any MN. Exceptions: most neck MNs, some abdominal, wing and haltere MNs get >20% (up to ~60%) of input directly from DNs. No single global "fraction of DN output going directly onto MNs" was found in the text we read. VERIFIED (read: full text via PMC) — [eLife 96084](https://doi.org/10.7554/eLife.96084)
- Braun et al. 2024: command-like DNs thought to act alone in fact co-activate larger DN populations via direct excitatory DN-DN connections in the brain; DNs with many downstream DNs need network co-activation to drive complete behaviours; behaviour-specific DN clusters inhibit each other. 85% of all DNs have axon collaterals in the gnathal ganglion; 73% of DN-DN synapses in the brain are in the GNG. VERIFIED (read: abstract + full text via PMC) — [Nature, PMID 38839968](https://doi.org/10.1038/s41586-024-07523-9)
- Braun et al., headless-fly test: turning evoked by DNa01 and DNa02 stimulation, and backward retreat by DNp42, were lost in decapitated (headless) animals; DNa02 has monosynaptic connections to 18 other DNs and "weakly triggers turning". Authors' interpretation: such broadcaster DNs need co-recruited DN populations; stand-alone DNs (oviDN, DNg11, Mute, DNg14) still worked headless. REPORTED (read: full text via PMC, Extended Data legends) — [same paper](https://doi.org/10.1038/s41586-024-07523-9)
- Lesser et al. 2024: leg and wing premotor networks cluster into modules linking MNs of muscles with related function; in most leg modules the synaptic weight of each premotor neuron is proportional to the size of its target MN (basis of hierarchical recruitment); wing premotor networks lack this proportionality. REPORTED (read: abstract) — [Nature, PMID 38926579](https://doi.org/10.1038/s41586-024-07600-z)
- Azevedo et al. 2024 (female VNC, FANC): ~45 million synapses, ~14,600 neuronal cell bodies; motor-neuron atlas of leg and wing MNs mapped to muscles. REPORTED (read: abstract) — [Nature, PMID 38926570](https://doi.org/10.1038/s41586-024-07389-x)
- Takemura et al. MANC connectome paper (eLife 97769) exists as a reviewed preprint; metadata only, content not read. NOT VERIFIED beyond existence — [Crossref DOI 10.7554/eLife.97769](https://doi.org/10.7554/eLife.97769)

### Inferences
- INFERRED: "command neuron" is too simple. A DN alone is often insufficient; a population of DNs plus VNC interneurons composes the behaviour. A single FlyMind "DNa02 left minus right" readout is therefore a very reduced stand-in for a descending population.
- INFERRED: since the brain-to-VNC channel is ~1,300 axons and DN-MN links are sparse, the biological division is "brain chooses and modulates, VNC patterns joints". It matches FlyMind's current split structurally (network at DN level, classical code below), but the classical code in FlyMind (IK, scripts) does much more than the VNC does (it plans reach geometry), see section 6.

### Gaps
- Global fraction of DN output onto MNs vs INs: Cheong Fig. 3D plots DN output by neuron class, but no single number was found in the text read; need the figure or the MANC data (neuPrint) to compute. Not computed by us.
- Takemura 2024 and Marin 2024 (MANC annotation) content not read (pages blocked, Europe PMC search returned nothing).

## 2. What the VNC does on its own: CPGs, reflexes, interleg coordination, proprioception, headless flies

### Takeaway
The VNC contains local rhythm and reflex circuitry and receives leg proprioceptive feedback; the brain's DNs mainly initiate, steer and modulate rather than time each step. Direct evidence in Drosophila for autonomous stepping rhythm is thinner than in big insects, and is mostly inferred from them.

### Cited Findings
- Review: walking in insects rests on CPG networks interacting with peripheral (leg) feedback for single-leg stepping and interleg coordination; descending signals alter these for forward/backward walking, curve walking and speed. REPORTED (read: abstract) — [Bidaye, Bockemuhl, Buschges 2018, J Neurophysiol](https://doi.org/10.1152/jn.00658.2017)
- Review notes most mechanosensory-motor work was done in locusts, cockroaches, crickets and stick insects; Drosophila adds genetic tools. REPORTED (read: abstract) — [Tuthill & Wilson 2016, Curr Biol](https://doi.org/10.1016/j.cub.2016.06.070)
- Leg proprioceptors (femoral chordotonal organ type) encode leg position/movement features in Drosophila. REPORTED (read: Crossref title only; content not read, NOT VERIFIED beyond existence) — [Mamiya et al. 2018, Neuron](https://doi.org/10.1016/j.neuron.2018.09.009)
- Azevedo et al. 2020: tibia flexor MNs form a gradient; large fast MNs drive high-force ballistic movements, small slow MNs drive postural movements; recruitment mostly slow-to-fast, but fast/intermediate/slow MNs also receive distinct proprioceptive feedback, so the size principle is not the only recruitment mechanism. REPORTED (read: abstract) — [eLife 56754](https://doi.org/10.7554/eLife.56754)
- Headless flies still execute some DN-evoked behaviours (grooming-like foreleg rubbing via DNg11, abdominal curling, ovipositor extension), which shows VNC circuits can produce complete motor patterns when triggered at the DN level. REPORTED (read: full text, Braun 2024) — [Braun et al.](https://doi.org/10.1038/s41586-024-07523-9)
- Hampel 2015: a multilayer circuit (mechanosensory chordotonal neurons -> brain interneurons -> descending neurons) elicits stereotyped antennal grooming; each layer is sufficient, layers differ in the duration of grooming they elicit. REPORTED (read: abstract) — [eLife 08758](https://doi.org/10.7554/eLife.08758)

### Inferences
- INFERRED: a VNC-like layer for an arm would own reflexes and per-joint recruitment (force gradients), while higher layers pick goals. This supports giving a hybrid system a per-joint low layer, but not necessarily a hand-written one (see principle "fly must steer").

### Gaps
- Headless-walking studies and Hampel/Seeds grooming-after-decapitation literature: only Braun 2024 was read; no source found in this session for "walking in headless Drosophila after stimulation" beyond that. Searches returned nothing relevant.
- Quantitative evidence for a Drosophila leg CPG (vs. feedback-driven stepping): not found; the review abstract refers to insects generally.

## 3. Steering DNs used by FlyMind: DNa01, DNa02, DNp09

### Takeaway
DNa02 and DNa01 are brain steering DNs whose left-right difference predicts and influences heading; DNp09 (P9) drives forward walking with ipsilateral turning. They act by recruiting other DNs and VNC leg circuits, not by driving MNs directly.

### Cited Findings
- Rayshubskiy et al. 2025: two descending cell types predict/influence heading; one predicts sustained low-gain steering, the other transient high-gain steering; they integrate internal head-direction steering with stimulus-driven steering; "see-saw" inputs, i.e. one hemisphere up while the other goes down. REPORTED (read: abstract) — [eLife 102230, PMID 40690376](https://doi.org/10.7554/eLife.102230). Which type corresponds to DNa01 vs DNa02 was not checked by us (INFERRED from earlier note that DNa02 is the one with see-saw left-right difference; see local note malecns_data_access.md).
- Bidaye et al. 2020: P9 (DNp09) drives forward walking with ipsilateral turning, receives input from courtship-promoting neurons and visual projection neurons, and is needed for a male to pursue a female; BPN drives straight fast walking. REPORTED (read: abstract) — [Neuron, PMID 32822613](https://doi.org/10.1016/j.neuron.2020.07.032)
- Braun 2024: DNp09, MDN, DNa01, DNa02, DNb02 fall in "walking"/"steering" DN clusters (3 and 9), split by hemisphere (right mostly cluster 3, left cluster 9); DNa02 triggers only weak turning on its own and the effect disappears without the head. REPORTED (read: full text) — [Braun et al.](https://doi.org/10.1038/s41586-024-07523-9)
- Bidaye et al. 2014: MDN descending neurons drive backward walking, with ascending MAN neurons sustaining it. REPORTED (read: abstract) — [Science, PMID 24700860](https://doi.org/10.1126/science.1249964)

### Inferences
- INFERRED (important for FlyMind): the lateralization result (left DNa02 minus right DNa02 -> base rotation) is biologically sensible as a see-saw readout, but Braun 2024 implies that DNa02 activity alone is a weak and incomplete turning command; this agrees with the red-team finding that FlyMind's score reflects lateralization rather than a network topology.

### Gaps
- Synaptic pathway DNa02 -> VNC -> leg MNs in MANC (Cheong Fig. 8I-J has a Bayesian traversal example for DNa02 and DNa08, not interpreted by us).
- Whether DNa02 exists under that name in MaleCNS v1.0: previously unconfirmed in local notes; local data not queried in this subtask.

## 4. Leg motor neuron pools and joint/muscle mapping

### Takeaway
A fly leg has 14 muscles driven by 53 motor neurons (published figure used in Azevedo 2020), organised in lineage-based pools with a myotopic map. This is a much smaller MN pool than one might expect, with graded size/force within each pool.

### Cited Findings
- Fly leg: 14 muscles innervated by 53 MNs (citing Baek & Mann 2009, Brierley 2012 and others). VERIFIED (read: full text via PMC) — [Azevedo 2020, eLife 56754](https://doi.org/10.7554/eLife.56754). Our earlier local note records that the bioRxiv version said 52 and the published version 53 (secondary, from our notes, not rechecked).
- Baek & Mann 2009: leg MNs arise from at least 11 neuroblast lineages, two lineages generate the majority; each MN has a characteristic birth time, lineage, muscle target and stereotyped dendritic arbor; lineages are not dedicated to one muscle or segment. REPORTED (read: abstract) — [J Neurosci 2009, PMID 19474317](https://doi.org/10.1523/JNEUROSCI.1585-09.2009)
- Brierley et al. 2012: most leg MNs are postembryonic, from five neuroblasts per hemineuromere; a stereotyped architecture with a myotopic map links MN dendrites to the muscles they innervate. REPORTED (read: abstract) — [J Comp Neurol, PMID 22120935](https://doi.org/10.1002/cne.23003)
- Azevedo 2024: MN atlas of leg and wing MNs with muscle targets from driver lines and X-ray holographic nanotomography. REPORTED (read: abstract) — [Nature](https://doi.org/10.1038/s41586-024-07389-x)
- MANC: 733 MNs in the whole nerve cord, T1 MN identities matched to FANC, T2/T3 by serial homology. VERIFIED (read: full text) — [Cheong et al.](https://doi.org/10.7554/eLife.96084)

### Inferences
- INFERRED: number of joints per leg and mapping to SO-101: not given in the sources read. A leg has several segments (coxa, trochanter, femur, tibia, tarsus) from general knowledge; muscles act on more than one joint axis, so a one-MN-pool-per-SO-101-joint map is a design choice, not biology. Muscle-to-joint table in Azevedo 2024 supplementary was not read.
- HYPOTHESIS: for an SO-101 with 6 actuators, a minimal analogue would be 1 agonist/antagonist MN pool per joint with graded size, using the fly's size-principle architecture. Untested.

### Gaps
- Joints per leg and the muscle-to-joint table (Azevedo 2024 supplement; Brierley/Baek tables): not obtained.
- Exact MN count for the T2L leg in MaleCNS: not queried here.

## 5. Reaching-like or aimed movements; ascending neurons and efference copy

### Takeaway
Flies do show aimed and goal-directed leg movements: grooming aimed at touched body sites and front-leg reaching across gaps. Circuit-level evidence puts the stimulus-location-to-action mapping in somatotopic sensory pathways into the brain with descending output, whereas the leg coordination of the reach itself is only behaviourally characterised. ANs send behavioural-state/efference-like signals back to the brain.

### Cited Findings
- Pick & Strauss 2005: freely walking flies facing a chasm estimate gap width visually (parallax from vertical edges on the far side), and for surmountable gaps combine three behavioural adaptations to maximise front-leg reach; adaptations can be impaired separately, so they are distinct subunits; each leg pair contributes differently. No circuit identified. REPORTED (read: abstract) — [Curr Biol 2005, PMID 16111941](https://doi.org/10.1016/j.cub.2005.07.022)
- Calle-Schuler et al. 2025/2026: bristle mechanosensory neurons around the head project somatotopically; EM brain reconstruction identifies pathways, including a cholinergic hemilineage 23b that elicits aimed head grooming, controlling stimulus-aimed grooming (brain circuits). REPORTED (read: abstract) — [eLife 108044, PMID 42253234](https://doi.org/10.7554/eLife.108044); preprint [bioRxiv 2025.05.19.654894](https://doi.org/10.1101/2025.05.19.654894)
- Chen et al. 2023: hundreds of genetically identified ANs encode behavioural states; self-motion goes to the anterior ventrolateral protocerebrum (integrative sensory hub) and discrete actions go to the gnathal ganglia (action selection). REPORTED (read: abstract) — [Nat Neurosci, PMID 36959417](https://doi.org/10.1038/s41593-023-01281-z)
- Fujiwara et al. 2017: horizontal-system visual cells carry a walking-movement signal independent of vision, and promote leg-based turning; visual and non-visual direction selectivity cooperate only when input matches the expected one (efference-copy-like). REPORTED (read: abstract) — [Nat Neurosci, PMID 27798632](https://doi.org/10.1038/nn.4435)
- Stürner 2025: chains of connected DNs and ANs span the neck, which "may subserve motor sequences" (authors' hedge). REPORTED (read: abstract) — [Nature](https://doi.org/10.1038/s41586-025-08925-z)
- Count: ~1,733-1,865 ANs vs ~1,315-1,347 DNs; ANs outnumber DNs. VERIFIED (read: full text) — [Stürner et al.](https://doi.org/10.1038/s41586-025-08925-z)

### Inferences
- INFERRED: the fly has no known "reach to a 3-D target" circuit analogous to arm kinematics; aimed grooming is a discrete-site lookup, and gap crossing is a posture adaptation. Calling a fly circuit a template for arm reaching to arbitrary targets is not supported by these sources.
- INFERRED: ascending signals (AN > DN count) mean a fair analogue for an arm needs a feedback path from the low layer (joint state) to the "brain" network; FlyMind's current loop gives the network image and touch, but not joint-state efference copy. NOT IMPLEMENTED in FlyMind (as far as the task context states).

### Gaps
- Which circuits (brain vs VNC) generate front-leg targeting in gap crossing: no circuit-level paper found in this session.
- Aimed leg movement toward touched body parts other than the head (e.g. thorax/wing grooming) and Eichler 2024: not read.

## 6. Implication for an arm: DN-level command from brain vs joint-level coordination in a VNC-like layer

### Takeaway
Biology supports a three-tier picture: (a) brain selects goal and steering signals as a population over ~1,300 DNs; (b) VNC interneurons convert them into patterns, with sparse direct DN-MN links; (c) MN pools with size-ordered recruitment and proprioceptive feedback. For an arm, this is an analogy to design from, not evidence that a fly connectome can run a 6-joint arm.

### Inferences (all INFERRED / HYPOTHESIS)
- INFERRED: current FlyMind has tier (a) as 2 readouts (DNa02 L-R; gripper force) and replaces tiers (b) and (c) with hand-written classical code (IK, scripts). This is a larger classical share than the fly's VNC, so the "who decides" question depends on how much planning the classical layer already encodes.
- HYPOTHESIS: a more faithful hybrid would let MaleCNS VNC interneurons/MN (data are in MaleCNS superclass `vnc_motor`, per local note) form the low layer, with a thin designed translator at the MN stage mapped to SO-101 joint targets, so that translation does not hide decisions. Untested, not approved.
- HYPOTHESIS: control for separating the roles: shuffle or replace the VNC-like layer while keeping the DN-level code fixed (and the reverse), since the fly literature shows population and VNC structure matter (Braun 2024: DN-population recruitment; Cheong 2026: VNC hubs, not direct DN-MN).
- INFERRED caution: Braun 2024 headless result (DNa02 turning lost) shows single-DN readouts can be misleading about which stage generates a behaviour. Equivalent caution applies to reading base rotation from only DNa02.
- INFERRED: a pair of neurons per joint (pos/neg), as seen on screen in the Founders, Inc. video, resembles the flexor/extensor MN pools, but the video evidence is only on-screen text and not a published method (REPORTED observation, not verified).

### Gaps
- No published example found in this session of a connectome-derived VNC layer driving a robot arm; not searched exhaustively (outside this subtask).
- No quantitative estimate available of how much of a reaching movement a fly VNC would plan versus a classical IK.
