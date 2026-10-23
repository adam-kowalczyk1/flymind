# Drosophila (and insect) leg proprioceptive reflexes and motor neuron recruitment, for a bio-inspired gripper controller

Status: research notes, 2026-10-23. Every claim has an inline source. Claims tagged **[from memory, not re-verified]** come from the researcher's background knowledge. No page fetched in this session confirmed them, so check them before citing.

## Q1. How many tibia flexor MNs per leg, and how are they classified (fast / intermediate / slow)? What does the size principle look like in Drosophila leg MNs?

### Takeaway
The tibia flexor pool has about 15 MNs (Azevedo 2020). Three genetically identified neurons span a size gradient. **Fast** MNs are large, input resistance about 150 MΩ, about 10 µN per spike, and silent at rest. **Intermediate** MNs give about 1 µN per spike, input resistance about 300 MΩ. **Slow** MNs are small, input resistance about 700 MΩ, under 0.1 µN per spike, and fire tonically at about 30 Hz. Recruitment normally runs slow → intermediate → fast, but descending or premotor inhibition can override it. The FANC connectome shows how the order arises: each premotor neuron gives synaptic weight proportional to the size of its target MN (Lesser 2024).

### Cited Findings
**Azevedo et al. 2020, eLife 9:e56754, "A size principle for recruitment of Drosophila leg motor neurons" (Azevedo AW, Dickinson ES, Gurung P, Venkatasubramanian L, Mann RS, Tuthill JC), DOI 10.7554/eLife.56754**
- The fly leg has 14 muscles innervated by 53 MNs. The tibia flexor pool has about 15 MNs, and the study characterised 3 identified neurons at the extremes of the pool — [eLife](https://elifesciences.org/articles/56754). The bioRxiv preprint said 52 MNs per leg; the published version and the Dryad dataset say 53 — [bioRxiv 730218](https://www.biorxiv.org/content/10.1101/730218v2), [Dryad](https://datadryad.org/dataset/doi:10.5061/dryad.76hdr7stb).
- Driver lines: fast = R81A07-Gal4, intermediate = R22A08-Gal4, slow = R35C09-Gal4 — [eLife](https://elifesciences.org/articles/56754).
- The fast MN is born in the embryo and persists through metamorphosis. The intermediate and slow MNs are born during metamorphosis. Soma, dendrite and axon size all rank fast > intermediate > slow — [eLife](https://elifesciences.org/articles/56754).
- Resting membrane potential: fast about −68 mV, intermediate about −60 mV, slow about −48 mV — [eLife](https://elifesciences.org/articles/56754).
- Input resistance: fast about 150 MΩ, intermediate about 300 MΩ, slow about 700 MΩ — [eLife](https://elifesciences.org/articles/56754).
- Spontaneous firing: fast and intermediate MNs are silent at rest. Slow MNs fire at about 30 Hz at rest, and this firing sets the fly's resting tibia force/tone — [eLife](https://elifesciences.org/articles/56754).
- Force from one spike: fast about 10 µN, intermediate about 1 µN, slow under 0.1 µN. One fast spike moved the force probe about 50 µm and one intermediate spike about 5 µm (probe spring constant 0.22 µN/µm) — [eLife](https://elifesciences.org/articles/56754).
- Force summation: two spikes give about 1.6× the force of one (fast and intermediate MNs), and force saturates at about 10 spikes. Fast and intermediate MNs reach half-maximal force in about 8.5 ms — [eLife](https://elifesciences.org/articles/56754).
- Maximum tibia flexion force is about 100 µN, roughly 10× body weight — [eLife](https://elifesciences.org/articles/56754).
- Recruitment order is generally slow → intermediate → fast. The exception is rapid leg waving, where inhibition suppressed slow MNs. The authors conclude that presynaptic input can override intrinsic excitability — [eLife](https://elifesciences.org/articles/56754).
- Functional roles: large, fast units handle high-force ballistic movements and small, slow units handle low-force postural control. The paper also says the size principle is not the only rule for recruitment, because the three classes get distinct proprioceptive feedback — [eLife abstract](https://elifesciences.org/articles/56754v1).
- Calcium imaging found 3 flexor activity clusters. "Flexor 1" was active only during large, fast movements — [eLife](https://elifesciences.org/articles/56754).
- Optogenetics: activating fast MNs caused rapid, sustained flexion and interrupted walking. Activating slow MNs caused tibia extension and interrupted walking. Activating intermediate MNs raised walking speed and started walking in stationary flies. Silencing fast or intermediate MNs lowered the probability that a stationary fly started walking — [eLife](https://elifesciences.org/articles/56754).
- Fly leg MNs are not GABAergic: a Gad1-Gal4 line labelled no leg axons — [eLife](https://elifesciences.org/articles/56754).

**Lesser et al. 2024, Nature 631:369–377, "Synaptic architecture of leg and wing premotor control networks in Drosophila", DOI 10.1038/s41586-024-07600-z** (bioRxiv 10.1101/2023.05.30.542725)
- One front leg has 69 MNs. They receive 220,747 synapses from 1,411 premotor neurons (preMNs). Each of the 18 leg muscles is innervated by 1 to 10 MNs, and the accessory tibia flexor has the most, with 10 — [bioRxiv full text](https://www.biorxiv.org/content/10.1101/2023.05.30.542725v1.full).
- Premotor modules: Tibia Flex A, B and C; Tibia Extend; Coxa Swing; Trochanter Extend. "Tibia Flex A" contains 5 main tibia flexor MNs and 4 accessory tibia flexor MNs — [bioRxiv](https://www.biorxiv.org/content/10.1101/2023.05.30.542725v1.full).
- A MN's number of input synapses scales with its surface area. The text gives r = 0.94 and the figure legend r = 0.95. The slope is 0.45 synapses/µm² in the text but 0.34 in the legend, an internal inconsistency in the preprint — [bioRxiv](https://www.biorxiv.org/content/10.1101/2023.05.30.542725v1.full).
- In most leg modules, a preMN's synaptic weights are proportional to the size of its target MNs, which the authors present as the circuit basis for hierarchical (size-ordered) recruitment. Wing premotor networks lack this proportionality — [Lesser 2024 abstract via IDEAS/RePEc](https://ideas.repec.org/a/nat/nature/v631y2024i8020d10.1038_s41586-024-07600-z.html), [Harvard connectomics page](https://connectomics.hms.harvard.edu/publications/synaptic-architecture-leg-and-wing-premotor-control-networks-drosophila).
- Within the extensor and flexor modules, a preMN gives the same output weight to every MN, even though preMN total synapse counts vary about 100-fold. Excitation and inhibition onto MNs are roughly balanced: E/I = 0.99 ± 0.72 (SD). About 3% of MN input synapses come directly from sensory neurons — [bioRxiv](https://www.biorxiv.org/content/10.1101/2023.05.30.542725v1.full).
- Tibia extensor: 2 MNs, FETi (fast extensor tibiae) and SETi (slow extensor tibiae). In FANC, FETi receives 14,904 input synapses and SETi 7,090 — [Azevedo 2024 bioRxiv](https://www.biorxiv.org/content/10.1101/2022.12.15.520299v1.full).

**Development (Baek & Mann 2009; Brierley et al. 2012)**
- Adult leg MNs come from at least 11 neuroblast lineages, and two lineages produce most of them. Each MN has a characteristic birth time and stereotyped dendrites — [Baek & Mann 2009, J Neurosci 29:6904–6916, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6665603).
- A few leg MNs are embryonic and most are born post-embryonically from 5 neuroblasts per hemineuromere. Lineage 15 is the largest. The study also describes a myotopic map — [Brierley et al. 2012, J Comp Neurol 520:1629–1649](https://scicrunch.org/22120935), [KCL record](https://kclpure.kcl.ac.uk/portal/en/publications/developmental-origins-and-architecture-of-drosophila-leg-motoneur/).
- A Mann lab paper cites about 50 MNs per leg, based on Baek & Mann 2009 and Brierley 2012 — [Enriquez et al. 2018, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC5941948).

**MANC (male VNC) — Cheong et al., eLife RP 96084, "Transforming descending input into motor output: An analysis of the Drosophila Male Adult Nerve Cord connectome", DOI 10.7554/eLife.96084 (v2 2025, v3 also available)**
- MANC has 392 leg MNs: T1 142, T2 119, T3 131. These are totals across both sides, so about 71 per front leg. All 142 T1 MNs were identified, and 198 of the 252 T2/T3 MNs were putatively identified through serial homology — [eLife RP 96084](https://elifesciences.org/reviewed-preprints/96084).
- T1 muscle targets were assigned by NBLAST matching to FANC. Naming: systematic type = "MN" + segment code (fl/ml/hl = front/middle/hind leg) + two-digit number, and literature names are kept where they exist (e.g. "Ti extensor MN") — [eLife RP 96084](https://elifesciences.org/reviewed-preprints/96084).
- About 49% of leg MNs have reconstruction defects because their axons were damaged during dissection. Some T3 tibia flexor and accessory tibia flexor MNs were inconsistent across segments — [eLife RP 96084](https://elifesciences.org/reviewed-preprints/96084).
- Direct descending input is small, about 7% of MN input on average. There are about 404 DNs for 392 leg MNs — [eLife RP 96084](https://elifesciences.org/reviewed-preprints/96084).
- MANC overview paper: Takemura et al., eLife RP 97769, DOI 10.7554/eLife.97769, about 23,000 neurons — [eLife RP 97769](https://elifesciences.org/reviewed-preprints/97769).

### Inferences
- MN counts per front leg agree across datasets: 69 (FANC T1L), 70 (FANC T1R), about 71 (MANC T1/2), and 53 / about 50 from light microscopy. Light microscopy undercounts relative to EM. For modelling, about 70 MNs per leg is the safer figure.
- "About 15 tibia flexor MNs" (Azevedo 2020) and "5 main + 4 accessory in Tibia Flex A, with further flexor MNs in modules B and C" (Lesser 2024) do not conflict. The roughly 15 most likely covers main plus accessory tibia flexors spread across the A/B/C modules.
- For a gripper: the per-spike force ratio slow : intermediate : fast is roughly <0.1 : 1 : 10 µN, about two orders of magnitude, and the input-resistance ratio is about 700 : 300 : 150 MΩ. The engineering analogue is 3 actuator "units" with exponentially increasing gain, driven by one shared command through thresholds set by input resistance. The low-threshold unit runs tonically and sets resting tone.
- Proportional preMN weighting (Lesser) means one shared command signal can recruit units in size order without separate per-unit channels. A gripper can use one scalar command split across tiers by threshold.

### Gaps
- An exact count of tibia flexor MNs per module (A/B/C) and the mapping of the Azevedo 2020 fast/intermediate/slow neurons to FANC/MANC IDs are in the FANC Appendix A atlas (Azevedo 2024) and Lesser 2024 Extended Data. These were not read: the PDFs exceeded the fetch limit.
- No direct measurement of per-class recruitment thresholds in Hz or mV was found beyond the input-resistance and resting-potential differences. There is no Drosophila "force–frequency curve" per class beyond "saturation at about 10 spikes".
- MANC per-muscle counts are in Fig. 7C of Cheong et al., which could not be read in text form.

## Q2. ltm (long tendon muscle) MNs: count, function (claw/tarsus grip), names

### Takeaway
The ltm is a multi-joint muscle with fibres in the femur (ltm2) and the tibia (ltm1). Both parts insert onto one long tendon (retractor unguis) that pulls the tarsal claw, so it is the fly's main "grip" muscle. FANC T1L has 4 clearly identified ltm MNs (2 for ltm1, 2 for ltm2) plus 4 smaller ltm MNs with uncertain targets, about 8 in total. This group includes small DIP-α-positive ltm MNs.

### Cited Findings
- The ltm has fibres in the femur (ltm2) and tibia (ltm1) inserting onto the same long tendon. It controls the tarsal claw, and the long tendon is the retractor unguis — [Azevedo et al. 2024 bioRxiv (FANC; Nature 631:360–368, DOI 10.1038/s41586-024-07389-x)](https://www.biorxiv.org/content/10.1101/2022.12.15.520299v1.full).
- 4 ltm MNs with extensive medial branches: 2 target ltm2 and 2 target ltm1. The targets of 4 smaller ltm MNs are uncertain — [Azevedo 2024 bioRxiv](https://www.biorxiv.org/content/10.1101/2022.12.15.520299v1.full).
- The FANC supplementary MN table lists the categories "ltm femur", "ltm tibia", "ltm uncertain" and "ltm dipalpha", each with 2 MNs and all in the ProLN nerve. This came from a search-result summary of the Nature SI, not a direct read — [Nature SI PDF (Caltech record)](https://authors.library.caltech.edu/records/zzp0n-qys09/preview/41586_2024_7389_MOESM1_ESM.pdf).
- Lesser 2024 Extended Data Fig. 4 describes 4 ltm MN groups, including small DIP-α ltm MNs — [Lesser bioRxiv](https://www.biorxiv.org/content/10.1101/2023.05.30.542725v1.full).
- The tarsus has no intrinsic muscles; tarsal/claw movement comes from tendons of muscles in proximal segments — [search summary of Drosophila leg imaging (eLife RP)](https://elifesciences.org/reviewed-preprints/96084v1/figures) (secondary; needs confirmation).

### Inferences
- About 8 ltm MNs per leg in 4 pairs, with "small DIP-α" MNs among them. Pairs of large and small MNs suggest the ltm also has a size/recruitment hierarchy. This is not measured physiologically.
- For a gripper: the closest biological analogue of the SO-101 jaw is ltm → retractor unguis, a single tendon driven by two muscle bodies in different segments. In the fly, a femur–tibia posture change shifts the tendon path, so grip force depends on posture. That is worth modelling if the gripper is tendon-driven.

### Gaps
- No physiology was found (force per spike, input resistance, firing rate) for ltm MNs. Azevedo 2020 covered only the tibia flexor.
- MANC names/IDs for ltm MNs (systematic MNfl## type) could not be read from Cheong et al. Fig. 7C. A neuPrint (MANC) query on `type` containing "LTM" or "ltm" is needed.
- The function of the DIP-α ltm subtype is unknown.

## Q3. Campaniform sensilla (CS) in Drosophila legs: locations, encoding, connectivity, latency

### Takeaway
CS are cuticular strain sensors arranged in fields, groups or single sensilla, usually near joints, with the highest density on the trochanter. They encode loads and resisted muscle forces, not unresisted movement. Their response is directional, most sensitive to forces in the plane of joint movement. These properties are best characterised in the stick insect (Zill lab). In Drosophila, location and arrangement were mapped by Dinges et al. 2021, and the strain mechanics of the femoral field by FEM (Dinges 2022). No source in this session gave Drosophila CS→MN connectivity or latency.

### Cited Findings
- CS detect deformations of the exoskeleton from resisted movements or external perturbations. They are arranged in fields, groups or single sensilla, usually near joints — [Dinges et al., "Location and arrangement of campaniform sensilla in Drosophila melanogaster", J Comp Neurol 529(4):905–925 (online 2020, print 2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9065962) (abstract via search summary; full text could not be fetched — access verification page).
- The femoral CS field was studied with nano-CT plus FEA. Socket and collar affect strain distribution across the whole field — [Dinges et al. 2022, J R Soc Interface](https://par.nsf.gov/search/author:%22Dinges,%20Gesa%20F%22). A parametric FEM of the femoral field lets CS location, orientation and material be varied — [bioRxiv 2023.07.24.550300](https://www.biorxiv.org/content/10.1101/2023.07.24.550300.full.pdf), [NSF PAR record](https://par.nsf.gov/biblio/10627448-parametric-finite-element-model-leg-campaniform-sensilla-drosophila-study-campaniform-sensilla-location-arrangement).
- Drosophila femoral CS sit on the ventral femur, which suggests sensitivity to forces in the plane of the joint — Zill et al. 2016 conference abstract, from search summary — [pwvas.org](https://pwvas.org/index.php/pwvas/article/view/116).
- Stick insect: CS are found on all leg segments distal to the coxa but are concentrated on the trochanter. Trochanteral CS encode loads and muscle forces — [Zill et al. 2012, J Neurophysiol, PMC3774582](https://pmc.ncbi.nlm.nih.gov/articles/PMC3774582).
- Stick insect tibial CS respond most strongly to loads in the plane of joint movement. They encode muscle forces (tested by pulling the tibial flexor tendon) and do not fire during unresisted movement — [Zill et al. 2013, Arthropod Struct Dev (search summary)](https://pmc.ncbi.nlm.nih.gov/articles/PMC5740276).
- Stick insect premotor processing of load (CS) and movement (fCO) feedback for the femur–tibia joint is distributed across a premotor network — Gebehart, Schmidt & Büschges 2021, J Neurophysiol **[from memory, not re-verified]**.
- Connectome context: about 3% of leg MN input synapses come directly from sensory neurons of all types — [Lesser bioRxiv](https://www.biorxiv.org/content/10.1101/2023.05.30.542725v1.full). The Tuthill lab connectome work on leg sensory input (Lee, Dallmann, Cook, Tuthill, Agrawal 2024 bioRxiv, "Divergent neural circuits for proprioceptive and exteroceptive sensing of the Drosophila leg") focuses on the femoral chordotonal organ (FeCO), not CS — [PMC11071415](https://pmc.ncbi.nlm.nih.gov/articles/PMC11071415.2).
- Approximate count: about 45–50 CS per leg, grouped into fields on the trochanter (several), femur, tibia and tarsus — **[from memory, not re-verified; check Dinges 2021 Table 1]**.

### Inferences
- For a gripper: CS behave like a directional force/strain sensor near the joint that ignores free movement and responds only to resisted movement, i.e. contact or load. The robot equivalent is the servo current/torque error (commanded vs measured position under load), not position. That is the natural "CS channel" for the SO-101 jaw.
- Stick-insect CS signals are known to excite/stabilise stance muscles (load → keep pushing). A Drosophila-inspired grip loop could likewise use the load signal for positive feedback on the tonic slow-unit command (hold), but only in the "active grasp" state (see Q4).

### Gaps
- The number of CS per field in Drosophila, and their afferent projections and partners in FANC/MANC, could not be confirmed (Dinges 2021 full text and FANC SI not readable in this session).
- No Drosophila CS reflex latency was found, and no CS spike-encoding data (gain vs load, adaptation) for Drosophila. Only stick-insect data were seen, and their latencies were not extracted.
- No 2024–2026 paper with full Drosophila CS connectomics was found. This may exist (Tuthill/Agrawal labs) but was not found by search.

## Q4. Reflex reversal (resistance reflex vs assistance reflex / "active reaction") and state-dependent feedback in Drosophila

### Takeaway
In the stick insect femur–tibia joint at rest, stretching the femoral chordotonal organ (signals flexion) triggers a **resistance reflex**: extensor excitation opposes the movement. In the active animal (walking), the same stimulus produces an **"active reaction"** / assistance reflex, in which flexion is allowed or reinforced. This is reflex reversal, and it depends on behaviour (present in forward walking, absent in backward walking). In Drosophila the closest documented mechanism is state-dependent gating. During active (self-generated) movement, movement-encoding FeCO "hook" afferents are suppressed by GABAergic presynaptic inhibition from 9A interneurons, while position signals (claw) pass through (Dallmann et al. 2025, Nature). Azevedo 2020 saw "occasional reflex reversal" in tibia flexor MNs.

### Cited Findings
- Definition: stretching the fCO (flexion) in a resting stick insect produces a resistance reflex that resists the joint movement. In an active insect the same stimulus produces an active reaction (AR), in which the muscles let flexion continue — [neuromechanical model paper, NSF PAR 10335092](https://par.nsf.gov/servlets/purl/10335092).
- In the model, inhibiting the flexion position and velocity afferents produced reflex reversal in the robot leg's FTi joint, which supports a mechanism of selective afferent inhibition — [NSF PAR 10335092](https://par.nsf.gov/biblio/10335092).
- Reflex reversal reinforces stance-phase output and depends on behaviour. Front-leg fCO flexion signals regularly evoke reversal in tibial MNs during forward walking, but not during backward walking — [Hellekes 2012 dissertation, Univ. Cologne](https://kups.ub.uni-koeln.de/4844/1/Dissertation_Katja_Hellekes_2012.pdf).
- Primary historical sources — **[bibliographic details from memory, not re-verified]**:
  - Bässler U. 1976, "Reversal of a reflex to a single motoneuron in the stick insect Carausius morosus", Biol Cybern 24:47–49 (cited in the reference lists found; title confirmed by search summary, content not read).
  - Bässler U. 1988, "Functional principles of pattern generation for walking movements of stick insect forelegs: the role of the femoral chordotonal organ afferences", J Exp Biol 136:125–147.
  - Bässler U. & Büschges A. 1998, "Pattern generation for stick insect walking movements — multisensory control of a locomotor program", Brain Res Rev 27:65–88. Not found by search in this session.
- Drosophila, Azevedo 2020: all three tibia flexor classes receive FeCO feedback, but it differs by class. Amplitude is largest in slow MNs and smallest in fast ones. Slow MNs respond to tibia movements under 1°, while fast MNs never spiked from feedback, and intermediate MNs spiked only during very fast extension. Fast and slow MNs hyperpolarise at the onset of flexion, and intermediate MNs depolarise after flexion ends. Reflex reversal was observed occasionally — [eLife 56754](https://elifesciences.org/articles/56754).
- Drosophila, Dallmann et al. 2025, Nature 647(8089):445–453, "Selective presynaptic inhibition of leg proprioception in behaving Drosophila" (preprint: "Presynaptic inhibition selectively suppresses leg proprioception in behaving Drosophila", bioRxiv 10.1101/2023.10.20.563322):
  - Axons of movement-encoding FeCO "hook" neurons are suppressed whenever flies move their legs actively (walking, grooming). Position-encoding "claw" axons are active across behaviours, and "club" axons are not suppressed — [PMC10634730](https://pmc.ncbi.nlm.nih.gov/articles/PMC10634730), [FlyBase FBrf0263858](https://flybase.org/reports/FBrf0263858.html).
  - The passive model fits hook axons with r = 0.68 on the treadmill vs r = 0.86 during passive movement, and claw axons with r = 0.91 during behaviour — [PMC10634730](https://pmc.ncbi.nlm.nih.gov/articles/PMC10634730).
  - The inhibition comes from GABAergic 9A interneurons: 83.1% of GABAergic input to hook axons is from 9A, and one "chief 9A" neuron supplies 56.8% of hook presynaptic input. 68.3% of the chief 9A's input is descending, including the excitatory DNs BDN2, oDN1 and DNa02 (walking/turning) and DNg12 (grooming). Its strongest input is an inhibitory "web" DN that is active at rest and silent during active movement, so it disinhibits 9A during movement. 9A activity correlates with self-generated, not passive, movement — [PMC10634730](https://pmc.ncbi.nlm.nih.gov/articles/PMC10634730).
  - Silencing 9A had only subtle effects on walking. The authors suggest hook suppression may prevent recruitment of postural (resistance) reflexes during voluntary movement — [PMC10634730](https://pmc.ncbi.nlm.nih.gov/articles/PMC10634730). Data: [Dryad](https://datadryad.org/dataset/doi:10.5061/dryad.gqnk98t16); PDF: [Tuthill lab](https://faculty.washington.edu/tuthill/docs/Dallmann_et_al-2025-Nature.pdf).
- Drosophila FeCO → postural reflex circuits: 13Bα neurons encode femur–tibia angle and mediate postural changes in tibia position. 9Aα neurons encode movement direction, vibration and angle. Activating 10Bα (vibration) causes walking flies to pause — [Agrawal et al. 2020, eLife 60299](https://elifesciences.org/articles/60299.pdf).

### Inferences
- The two mechanisms differ. Stick-insect reflex reversal flips the *sign* of feedback (resist → assist). The Drosophila mechanism found so far *gates* (removes) the movement-velocity channel during active movement and keeps the position channel. Both achieve the same effect: postural resistance does not fight voluntary movement. No published sign flip by the same mechanism has been shown in Drosophila, beyond "occasional" reversal in Azevedo 2020.
- For a gripper, a state machine maps onto this directly:
  - **idle/holding** → resistance reflex on (position error → corrective torque, PD on position). The velocity channel is on.
  - **active closing** → gate the velocity/movement channel (the 9A analogue), keep position feedback, and optionally switch load feedback (CS analogue) to assistance (positive feedback on grip force up to a limit).
  - A single "active movement" command acts as the "web DN" switch that controls the gating.
- Fly feedback is class-specific: the strongest feedback goes to slow/tonic units and fast units receive almost none. So the gripper's low-force holding tier should carry most of the reflexive correction, while the high-force tier stays feed-forward/ballistic.

### Gaps
- No quantitative reflex latencies were found in this session, for Drosophila (FeCO→MN, CS→MN) or for the stick insect. Known orders of magnitude (stick-insect resistance reflex tens of ms) are not confirmed.
- The original Bässler & Büschges papers were not read in this session. The details above come from secondary sources (Hellekes 2012, the NSF PAR model paper).
- No Drosophila paper showing true sign reversal (resistance → assistance) during walking was found. Azevedo 2020 only reports "occasional reversal". This is an open question, not a negative result.
