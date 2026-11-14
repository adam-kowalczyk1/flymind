# Could FlyMind become a tool/service for "smart management of connectomes and vision"? (Q6) — notes of 2026-11-12

Label key: VERIFIED = I opened that page/file in this session; REPORTED = search-result summary or earlier project note only; INFERRED = my reasoning; PROPOSED = idea. Budget was ~15 tool calls, so several tools were checked only on GitHub landing pages.

## 1. What do existing tools do, and not do?

### Takeaway
Data access/analysis (neuPrint, Codex, CAVE, NAVis), general simulators (Brian2, NEST, BMTK), SNN trainers (snnTorch, Norse, Nengo), chip stacks (Lava) and fly bodies (NeuroMechFly, flybody) all exist and are mature. None found is a "connectome -> versioned, provenance-tracked controller -> closed-loop test with built-in controls". Gaps sit between the tools, not inside any of them.

### Cited Findings
- NAVis: Python library for analysing/visualising neurons (skeletons, meshes, NBLAST, template-brain transforms); loads from neuPrint, FlyWire via companion fafbseg; can drive the NEURON simulator; 140 stars, GPL-3.0; page says nothing about spiking-network simulation or robotics. VERIFIED (landing page, 2026-11-12) — [NAVis](https://github.com/navis-org/navis)
- CAVE = "Connectome Annotation Versioning Engine", microservices for storing/versioning connectomics data and annotations; CAVEclient is the Python client, MIT, 45 stars. Page does not mention provenance or which datasets. VERIFIED — [CAVEclient](https://github.com/CAVEconnectome/CAVEclient)
- FlyWire data: public release snapshot 783 (Zenodo record published 2 June 2024); data reachable via Codex (browser), CAVEclient, navis, natverse and static exports; CC BY-NC 4.0 (note NC licence). Sources disagree on "latest" (guidelines page says 630). REPORTED — [Zenodo 783](https://zenodo.org/records/10676866), [FlyWire guidelines](https://flywire.ai/guidelines), [FlyWire blog](https://blog.flywire.ai/2024/12/20/how-to-use-flywire-for-connectomics/)
- neuprint-python: my fetch of github.com/neuprint/neuprint-python returned 404 (wrong org path), so not verified. FlyMind's own data layer (MaleCNS) is per project context, not a neuPrint check.
- BMTK (Allen Institute): builder + simulator + analysis, SONATA data format; biophysical models rely on NEURON; aimed at cortex-type models (tutorial: toy mouse V1). REPORTED (search summary) — [BMTK docs](https://alleninstitute.github.io/bmtk), [BRAIN Initiative listing](https://www.braininitiative.org/toolmakers/resources/brain-modeling-tools-bmtk-sonata-vnd/)
- snnTorch: PyTorch-based SNN training, MIT, 2.1k stars, has `export_nir`; no connectome mention. VERIFIED — [snnTorch](https://github.com/jeshraghian/snntorch)
- Nengo: Python library for large-scale neural models, spiking and non-spiking, 960 stars; page mentions no hardware backend or connectome. VERIFIED (landing page only) — [Nengo](https://github.com/nengo/nengo)
- Intel Lava: framework for neuromorphic hardware, BSD-3 core, some Loihi parts proprietary; repository ARCHIVED/read-only, Intel gives no support guarantee; Loihi extension via Intel Neuromorphic Research Community; 743 stars. VERIFIED — [Lava](https://github.com/lava-nc/lava)
- Sandia mapped the full FlyWire connectome (~140k neurons, ~50M synapses) onto 12 Loihi 2 chips (arXiv 2508.16792, Aug 2025); mentions a unified experiment-description language; no body/robot. REPORTED (search + earlier note) — [arXiv](https://arxiv.org/abs/2508.16792)
- NeuroMechFly v2 (Nature Methods, Nov 2024, FlyGym, MuJoCo): adds vision, olfaction, ascending feedback; includes a connectome-constrained visual-system network. REPORTED — [PubMed 39533006](https://pubmed.ncbi.nlm.nih.gov/39533006/), [bioRxiv](https://www.biorxiv.org/content/10.1101/2023.09.18.556649.full.pdf)
- flybody (Janelia/DeepMind, Nature 2025): MuJoCo fly, controlled by RL networks, not connectome. REPORTED — earlier project note `/Users/admin/so101_fly_project/research_notes/Projekt mózgu muchy dla inwestorów/konkurencja_stan_wiedzy.md` line 33.
- Whole-brain LIF on a connectome in Brian2/NEST GPU/GeNN etc. already open-source (Eon Systems repo, GPL-2.0+, plus hobby repos); Eon "embodied fly" Mar 2026 with hand-designed encoder/decoder. REPORTED — same note, lines 13, 34–47.
- Lacuna paper cluster "Closed-Loop Neuromechanical Simulation" (24 papers) already covers the Neurorobotics Platform (Human Brain Project, TUM/Knoll) that links spiking networks to simulated robots/bodies, and a 2026 "embodied brain / neuromechanical digital twins" paper. VERIFIED (Lacuna) — [cluster 6046](https://lacuna.tiptreesystems.com/direction/closed-loop-neuromechanical-simulation-6046)
- Not checked in this session: Brian2, NEST, Norse, neuPrint server itself (stars/licences/capabilities).

### Inferences
- A "connectome to controller" workflow is today done by ad-hoc scripts per paper/repo; none of the verified tools targets it (INFERRED from absence in the landing pages above, not from an exhaustive search).
- Lava being archived is a risk for any "chip bridge" built on it; NIR (via snnTorch export) is the more neutral interchange (INFERRED).

### Gaps
- No verified star/licence/feature data for Brian2, NEST, Norse, neuPrint, Codex features.
- Did not check whether Eon's body-coupling code was released after Mar 2026.

## 2. Gap candidates: does anyone already provide them?

### Takeaway
Candidate A (connectome-to-controller extraction with provenance), B (closed-loop harness with built-in controls) and D (bio-vision front-end) are not found as ready products; C (robot/chip bridges) is partly covered (Lava/NIR/LeRobot exist separately). B is the most defensible because FlyMind's own results show why controls matter.

### Cited Findings
- Lacuna hypothesis "Adoptive-Transfer Controls for Circuit Claims in Simplified Connectome Models" (generated 2026-10-04) states researchers "increasingly run whole fly connectomes as networks of very simple model neurons" and make causal circuit claims; it proposes standard in-silico controls (sham, dose-matched, host variants, purity) and neuron-model swaps, planned as "an open transfer library" - i.e. a control suite is an open, unbuilt idea. It cites a 630-neuron "digital fly" benchmark (Sinha) and says no reported result was found for activation patching in recurrent spiking networks. VERIFIED (Lacuna; hypotheses are AI-generated proposals, not published results) — [hypothesis 96cf83b9e458c5c2](https://lacuna.tiptreesystems.com/hypothesis/adoptive-transfer-controls-for-circuit-claims-in-simplified-connectome-models-96cf83b9e458c5c2)
- Lacuna hypothesis "Where Should a Connectome Controller Break Left-Right Symmetry?" names flyGNN (FlyWire connectome as recurrent message-passing net, imitation of an MLP teacher on flybody) as "the closest system", reports its authors note heavy memory cost and walking/turning-only scope. VERIFIED (Lacuna) — [hypothesis 71a140dc7994c4dd](https://lacuna.tiptreesystems.com/hypothesis/where-should-a-connectome-controller-break-leftright-symmetry-71a140dc7994c4dd); flyGNN paper (DBM @ NeurIPS 2025): [Lacuna](https://lacuna.tiptreesystems.com/work/whole-brain-connectomic-graph-neural-networks-enable-whole?utm_source=claude&utm_medium=mcp)
- FlyMind's own evidence that controls are the valuable part (from repo notes, not re-verified here): shuffled wiring 3/40 and mirrored 0/40 versus data 38/40 on the vision loop; but on grasping, 10 strength-matched shuffles scored 79–102 vs 90 for data, so "wiring gives no advantage" there. Source: task context (project numbers), e.g. `/Users/admin/so101_fly_project/research_notes/Projekt mózgu muchy dla inwestorów/nasze_wyniki.md`. REPORTED.
- Sign-of-synapse from predicted neurotransmitter is itself uncertain, flagged by Eon and Fly Brain Bridge. REPORTED — `konkurencja_stan_wiedzy.md` line 21.
- NeuroBench exists as community benchmark framework (algorithm and system tracks; ~100 co-authors, 50+ institutions; Nat Commun 2025); I could not confirm any fly-connectome workload in it. REPORTED — [arXiv 2304.04640](https://arxiv.org/pdf/2304.04640)
- Bio-vision front-end: NeuroMechFly v2 already exposes a connectome-constrained visual system model in simulation (REPORTED above); FlyMind's own camera->retina->LPLC2/LC4 plan is on paper only (task context).

### Inferences
- Gap B ("test harness with controls") is the best fit: it uses what the team has already built (shuffles, mirrors, classical baseline, seeds protocol) and answers a published methodological worry (Lacuna hypothesis above). INFERRED.
- Gap A is real but depends on MaleCNS/FlyWire access and licences (CC BY-NC for FlyWire) and on sign uncertainty; "compiler" risks overclaiming. INFERRED.
- Gap D is high-value but currently unbuilt by FlyMind; it cannot be sold. INFERRED.

### Gaps
- No exhaustive GitHub search done for existing "connectome control benchmark" repos; Froststar16/connectome-control and others are known from earlier notes only.

## 3. Two to three concrete concepts (PROPOSED)

### Takeaway
Three concepts of descending ambition: (1) "ConnectomeBench-lite": an open test harness with built-in negative controls; (2) a connectome-subcircuit extractor with provenance manifests; (3) a bio-vision front-end module. Only (1) and a thin version of (2) fit before the 1 Dec festival, and only as sim-based releases.

### Cited Findings
- (No external facts; concepts below are PROPOSED. Supporting facts are cited in sections 1–2.)

### Inferences
- PROPOSED concept 1, "control-first harness": input = list of neuron IDs/edges + body (MuJoCo SO-101 scene) + metric; the tool automatically runs data wiring vs strength-matched shuffles, mirror, and a classical baseline across fixed seeds, outputs a one-page verdict "wiring-specific / not wiring-specific". Rationale: FlyMind's own two results (vision loop specific, grasp not) are exactly the cases it distinguishes. Minimal release: the repo's existing runners cleaned up + README + 2 worked examples + hash-pinned seeds.
- PROPOSED concept 2, "circuit manifest": a YAML/JSON file recording dataset name and version, neuron IDs, synapse thresholds, sign rule, E/I assumption, seeds and code commit, so a circuit can be re-built bit-identically. Useful because FlyWire snapshots (630 vs 783) and MaleCNS versions differ and claims often cannot be reproduced. Feasible as a small script; no new data needed.
- PROPOSED concept 3, "bio-vision front end": camera frames -> retina/lamina model -> motion/loom signals; only after Adam's 12 Nov ruling is implemented properly (no artificial stimulation). NOT built; should be presented as roadmap only.
- Names for honest framing: "reproducible test harness for connectome-controller claims", not "connectome operating system".

### Gaps
- No user interviews done; concepts are not validated with any lab.

## 4. Who would use it, and evidence of demand

### Takeaway
Evidence of demand is real but indirect: a vibrant ecosystem of open reproductions, funded fly-emulation start-up (Eon), neuromorphic-benchmark community (NeuroBench), and AI-generated research proposals asking for exactly the controls idea. I found no direct evidence (job posts, grant calls, stated tool requests) for a "connectome management/vision" product, so any demand claim is weak.

### Cited Findings
- Eon Systems seed $3.5M (reported ~30 Dec 2025), fly-embodiment post 10 Mar 2026; sensory encoder and descending decoder hand-designed; code for body coupling reported unreleased in Mar 2026. REPORTED — `konkurencja_stan_wiedzy.md` lines 34–35, 83–95.
- Many hobby repos run connectome LIF models on NeuroMechFly/drones (Froststar16/connectome-control, erojasoficial-byte/fly-brain, connectocopter, flywire-brain-drone), with authors' own caveats (few seeds, hand-designed bridges). REPORTED — `konkurencja_stan_wiedzy.md` lines 40–43.
- Sandia/Loihi 2 and an FPGA fly olfactory model (2024) show that chip makers/labs already run fly connectomes as workloads. REPORTED — [PMC11238178](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11238178/), [arXiv 2508.16792](https://arxiv.org/abs/2508.16792)
- Neuromorphic market forecasts for 2030 range from ~0.3 to ~20 bn USD (aggregators); Innatera Series A 21 M USD total; treat as hype range. REPORTED — `rynek_inwestorzy.md` lines 8–17.
- NeuroBench: field "lacks standardized benchmarks" (motivation statement). REPORTED — [arXiv 2304.04640](https://arxiv.org/pdf/2304.04640)
- Education: Backyard Brains sells neuroscience kits (~60 countries, NIMH SBIR ~450k USD, older data). REPORTED — `rynek_inwestorzy.md` line 79.

### Inferences
- Realistic first users (INFERRED): (a) hobbyist/academic groups already writing ad-hoc fly-in-simulator scripts (they would use a control-first harness to avoid over-claiming); (b) neuromorphic groups needing realistic, sparse, recurrent benchmark workloads; (c) teachers/competitions. Robotics/drone firms are unlikely to buy a fly circuit today since the grasp result shows no wiring advantage over a classical baseline.
- Stars/grants/job posts were not collected; no evidence a paying market exists.

### Gaps
- Job posts, grant call texts, and GitHub issue requests were not searched (call budget).
- No evidence from drone/robotics companies about wanting fly-derived vision.

## 5. Feasibility and honest risks for a high-school-led project; minimal meaningful release

### Takeaway
A small, honest open-source release (harness + circuit manifest + two worked examples with negative controls) is feasible; a "platform" or "service" is not. The main risks are overclaim, data licences, no real-hardware results, and single-author capacity.

### Cited Findings
- Project facts (task context, not re-verified): all results MuJoCo simulation; one SO-101 arm not connected since one calibration; touch sensors simulation-only; MaleCNS ~1.2% of neurons used; colour encoder ruled artificial stimulation by Adam on 12 Nov 2026; E1/E2 pre-registrations, fly-eye plan, U1–U5 pending and unapproved.
- Data licence issue: FlyWire public data is CC BY-NC 4.0, which limits commercial use. REPORTED — [FlyWire guidelines](https://flywire.ai/guidelines). MaleCNS licence not checked here.
- Lava archived by Intel; Loihi access through INRC membership, systems not commercially available. VERIFIED — [Lava](https://github.com/lava-nc/lava)

### Inferences
- Minimal release (PROPOSED): repo folder with (1) harness runner, (2) circuit manifest schema + two manifests (LC10a->DNa02 vision loop; T2L grasp), (3) controls table with exact counts (38/40, 3/40, 0/40; 90 vs 79–102), (4) a README stating "simulation only, vision loop uses an artificial colour encoder (Adam's ruling), P-controller beats the network". Not claiming product status.
- Risks: overclaiming ("fly brain beats AI"), "novel tool" claim when ecosystem is crowded, legal/commercial use with NC data, bus factor (one student, much code written by AI — needs disclosure), no real-arm validation.
- For investors: sell the methodology/negative-control discipline and roadmap, not a revenue product; revenue claims would be unsupported. INFERRED.

### Gaps
- MaleCNS licence terms and redistribution rules not checked.
- No time/effort estimate validated by the team.

## 6. Lacuna novelty verdict

### Takeaway
Lacuna searches (hypotheses, clusters, papers; run 2026-11-12) show the broad space is Partially done: embodied connectome simulation and connectome-as-controller are published; a reusable control-first harness for connectome-controller claims is Open (only proposed as an AI-generated hypothesis). A connectome-derived controller for a robot arm was not found in Lacuna in the few queries I ran.

### Cited Findings
- "Closed-Loop Neuromechanical Simulation" direction (24 papers): includes Neurorobotics Platform (spiking networks to simulated robots), flybody Nature 2025, flyGNN, neuromechanical digital twins 2026. Verdict for "embodied connectome simulation": Partially done / Done in simulation. VERIFIED — [direction 6046](https://lacuna.tiptreesystems.com/direction/closed-loop-neuromechanical-simulation-6046)
- "Connectome-controller" papers: flyGNN (FlyWire as controller of flybody) — Done in simulation for walking/turning. VERIFIED (via hypothesis text) — [71a140dc7994c4dd](https://lacuna.tiptreesystems.com/hypothesis/where-should-a-connectome-controller-break-leftright-symmetry-71a140dc7994c4dd)
- "Controls for circuit claims in simplified connectome models" (shams, dose matching, model swaps): Open — exists only as a proposal; the hypothesis reports no result found for patching in recurrent spiking nets. VERIFIED — [96cf83b9e458c5c2](https://lacuna.tiptreesystems.com/hypothesis/adoptive-transfer-controls-for-circuit-claims-in-simplified-connectome-models-96cf83b9e458c5c2)
- Paper search "connectome simulation robot control Drosophila" returned only connectome-atlas papers (e.g. FlyEM hemibrain, [Lacuna](https://lacuna.tiptreesystems.com/work/a-connectome-of-the-adult-i-drosophila-i/version/art_60e7265cec5247008da672b15bd93083)) and unrelated robot-arm RL, i.e. no connectome-to-robot-arm paper surfaced there. VERIFIED (negative result; Lacuna is ML/AI-centric and incomplete for neuroscience).
- Hypothesis "Streaming Spiking Trunks for Cross-Embodiment Robot Policies" (77736adfba8ac021) and others surfaced for "spiking robot", but are generic SNN-policy ideas, not connectome-derived. REPORTED (title only) — [link](https://lacuna.tiptreesystems.com/hypothesis/streaming-spiking-trunks-for-cross-embodiment-robot-policies-77736adfba8ac021)

### Inferences
- Verdict table (INFERRED): connectome LIF in embodied fly sim = Done; connectome controller on a physical arm = Open (supported by earlier literature check in task context, SO-101 arXiv 2606.08881 for baselines); control-first harness = Open/partially proposed; chip bridge = Partially done (Sandia Loihi 2, no body).
- Lacuna covers ML/AI; neuroscience-tool papers (neuPrint etc.) are likely missing, so "Open" is a Lacuna-relative claim.

### Gaps
- Lacuna hypotheses are AI-generated proposals; I did not read the cited papers (flyGNN, Eon) at full text.
- Only ~6 Lacuna queries; no get_paper on flyGNN.
