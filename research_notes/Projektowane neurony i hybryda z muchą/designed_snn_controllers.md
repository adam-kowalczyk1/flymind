# Hand-designed spiking controllers for robot arms: models, wiring, joint encoding, systems, and the Founders Inc video (topic 1a, 2026-11-13)

Scope note: research only. About 14 tool calls. Most items were checked at abstract level (Crossref / Europe PMC / Semantic Scholar metadata); only Zaidel 2021 was read in (most of) the full text through a summarising fetch tool. Everything else is labelled with what was actually read. Nothing in the repo was changed.

## Q1. Which neuron models are used in robot SNN control, and why

### Takeaway
LIF (and NEF-style rate-tuned LIF ensembles) dominate the arm/drone controllers I could verify; Hodgkin-Huxley and Izhikevich appear in the literature on SNNs generally, but the Bing 2018 survey (as read) names no robot-control example for them. Typical parameters are mostly NOT stated in the papers I could read.

### Cited Findings
- Zaidel et al. 2021 use LIF neurons in NEF ensembles; LIF parameters (refractory period, RC constant, max rates) are not stated in the text; intercepts had to be changed from uniform to triangular in 5D because uniform performed poorly. REPORTED (read: full text via summarising tool, not by us) — [Zaidel et al., Front. Neurorobot. 2021](https://www.frontiersin.org/articles/10.3389/fnbot.2021.631159/full), DOI 10.3389/fnbot.2021.631159 (metadata VERIFIED via Crossref).
- The Bing et al. 2018 survey describes LIF as one of the most widely used models, names Hodgkin-Huxley as influential, and cites Izhikevich only for property comparisons and an R-STDP rule, with no robot-control Izhikevich example in the part I read (first ~100k of 220k characters). It gives no count of real-robot vs simulation studies. REPORTED (read: roughly the first half of the full text via summarising tool) — [Bing et al. 2018](https://www.frontiersin.org/articles/10.3389/fnbot.2018.00035/full), DOI 10.3389/fnbot.2018.00035 (metadata VERIFIED via Crossref).
- A 2024 review exists on brain-inspired biomimetic robot control (Mompo Alepuz, Papageorgiou, Tolu); I read only the abstract start, not its model statistics. REPORTED (read: abstract) — DOI 10.3389/fnbot.2024.1395617, [Crossref record](https://api.crossref.org/works/10.3389/fnbot.2024.1395617).
- DeWolf et al. 2016 model motor cortices and cerebellum with anatomically organised spiking neurons controlling a nonlinear three-link arm, and claim it accounts for data across 19 studies. REPORTED (read: abstract) — [DeWolf et al. 2016](https://doi.org/10.1098/rspb.2016.2134).

### Inferences
- INFERRED: robot SNN work picks LIF because it is cheap and supported by Loihi/Nengo toolchains; this is our reading of the above, not a statement found in a source.
- INFERRED: FlyMind's ALIF choice is already more detailed than most of the engineered controllers surveyed here.

### Gaps
- Typical numeric LIF parameters in robot controllers: not found (not stated in the Zaidel text).
- No verified source found for Izhikevich or HH used in a robot arm controller; may exist, not searched deeply.
- Brian2, NEST, Norse, snnTorch, Lava, PyNN: I did not open their documentation; any statement about their `synapse(pre, post, weight)`-like APIs is NOT VERIFIED here (only Nengo/NEF appears through the papers above).

## Q2. How connections are designed by hand

### Takeaway
Three styles show up in verified sources: (a) NEF compilation, where function approximation yields decoders and encoder-decoder products become weights, optionally refined online by PES; (b) hand-built hierarchies of motor primitives combined by an error signal; (c) small hand-structured Hebbian circuits on analogue hardware. Learned adaptation is usually bolted onto a designed skeleton.

### Cited Findings
- NEF: Zaidel connect "Current q" to "Target q" ensembles with weights computed from source decoders and target encoders; the PES rule adapts decoders online; PID is built as P, I and D paths with an integrator (A'=1, B'=tau) and a derivative from two synapses with different time constants. Gains in simulation: kp=1, ki=0.1, kd=0.35, tau=0.1. The text gives conflicting Loihi parameters (tau=10 ms, kp=-1, ki=-0.1) against the caption saying same as simulation. REPORTED (read: full text via summarising tool) — [Zaidel 2021](https://www.frontiersin.org/articles/10.3389/fnbot.2021.631159/full).
- Tieck et al.: reaching without inverse kinematics; a spiking network represents motions as a hierarchy of motor primitives and combines correction primitives using an error signal; two simulated experiments. REPORTED (read: abstract) — [Tieck et al. 2019, IJCINI](https://doi.org/10.4018/ijcini.2019010101).
- Hulea, Uleru, Caruntu 2021: a simple adaptive SNN in analogue hardware, Hebbian training, drives a shape-memory-alloy robotic finger joint; independent neural paths correspond to angle intervals (place coding); sensors convert joint angle and compression force into spike frequency. REPORTED (read: abstract) — [Europe PMC, PMID 33924453](https://doi.org/10.3390/s21082730).
- Stagsted et al. 2020: P, I and D gains as synaptic weights; populations where spikes encode measured, control or error values; tested on a mobile robot and a 1-DOF UAV; first reported fully neuromorphic PID on Loihi interfaced to a UAV. REPORTED (read: secondary summary of abstract and a reviewer comment; full text not readable) — [RSS XVI p74](https://roboticsproceedings.org/rss16/p074.html).
- Michaelis, Lehr, Tetzlaff 2020: an "anisotropic network" on Loihi encodes sequences of activity patterns, each representing a robot action, used to generate multidimensional trajectories for a robot arm; main issue named is the time-scale gap between millisecond spiking and hundreds of milliseconds control. REPORTED (read: abstract) — [Front. Neurorobot. 2020](https://doi.org/10.3389/fnbot.2020.589532).
- CPG: Ijspeert's review of central pattern generators in animals and robots exists (metadata only). VERIFIED existence — [Ijspeert 2008, Neural Networks](https://doi.org/10.1016/j.neunet.2008.03.014). I did not read it; no claim about content.

### Inferences
- INFERRED: a designed `synapse(pre, post, weight)` with hand-set weights corresponds to the "Connections hand-wired" end of this spectrum; NEF is the principled version where weights come from a target function.
- INFERRED: in every verified example, which weights come from design and which from learning is a stated design choice, which is exactly what FlyMind lacks for its connectome part (weights come from synapse counts, not from a function).

### Gaps
- Braitenberg-style circuits in arm control: only seen as a baseline in a lane-keeping comparison in the Bing survey; no arm example found.
- Explicit Brian2/NEST/PyNN code examples for arm control: not found or opened.

## Q3. Joint encoding: antagonist pairs, rate/population/place coding

### Takeaway
I found no verified published example that matches "per-joint positive-direction and negative-direction neuron pairs with named theta/beta neurons". Verified examples are adjacent: agonist-antagonist or flexor-extensor output cells, angle-interval place coding, and NEF vector coding in one ensemble.

### Cited Findings
- Zaidel encode the five joint angles as one 5-D vector in a single ensemble; whether positive/negative paired encoders are used per joint is not stated, and the paper's DOF count (6 DOF, 9 servos, 5 joints in IK) is not explained. REPORTED (read: full text via summarising tool) — [Zaidel 2021](https://www.frontiersin.org/articles/10.3389/fnbot.2021.631159/full).
- Hulea et al. 2021: place/interval coding of angle, with angle-specific neural paths; sensor value converted to spike frequency (rate coding of feedback). REPORTED (read: abstract) — [Hulea 2021](https://doi.org/10.3390/s21082730).
- The Bing survey (as read) mentions a steering model based on an agonist-antagonist muscle system driven by output-neuron spike counts (Kaiser et al. 2016) and output cells controlling flexor and extensor muscles (Chadderdon et al. 2012). REPORTED (read: secondary, via survey) — [Bing 2018](https://www.frontiersin.org/articles/10.3389/fnbot.2018.00035/full). I did not open the primary papers.
- Candidate hits not read at all: Chen et al. 2020 "Bio-inspired SNN for control of a 4-DoF robotic arm" ([DOI 10.1109/iciea48937.2020.9248389](https://doi.org/10.1109/iciea48937.2020.9248389)) and Bouganis and Shanahan 2010, STDP-trained 4-DoF arm ([DOI 10.1109/ijcnn.2010.5596525](https://doi.org/10.1109/ijcnn.2010.5596525)). Existence VERIFIED (Crossref); content NOT VERIFIED.

### Inferences
- INFERRED: push-pull pos/neg pairs per joint are a natural, standard-looking design (they mirror agonist/antagonist muscles), and the on-screen names in the video fit that pattern; but I found no source to say anyone published that exact scheme for SO-101.
- INFERRED: for FlyMind, DNa02 left minus right is already a push-pull pair for base rotation, designed by us as the readout; this is a point to be flagged openly in the report as "translation".

### Gaps
- Concrete published per-joint pos/neg pair architecture with servo decoding: NOT found. Chen 2020 and Bouganis 2010 are the most likely places to look.
- Motor-neuron-to-servo decoding details (smoothing, rate window): not found in material read.

## Q4. Concrete groups and systems (what was designed, learned, trial counts, controls, sim vs real)

### Takeaway
Existence checked for all but the iCub arm-level claim. Measured evidence is thin: the papers I could read give few trial counts, rarely give statistical baselines, and often state results qualitatively or in figures. Most arm results are simulation; the Loihi results are mostly error traces, not a physical arm run.

### Cited Findings
- Zaidel et al. 2021 (Supic group, NEF IK + PID, 6-DOF arm). Designed: NEF structure, PID. Learned: IK via PES online. Trials: reachability map with 10,000 sampled points (no motion), two random points for motion; Loihi trial count not stated; no repetitions or seeds stated. Baselines: none external. Accuracy claim 1 mm. Motion results from MuJoCo; Loihi results are IK/PID traces, no physical-arm motion reported in the text. The abstract itself says "simulation as well as on Intel's Loihi". REPORTED (read: full text via summarising tool + abstract) — [Zaidel 2021](https://www.frontiersin.org/articles/10.3389/fnbot.2021.631159/full).
- DeWolf, Stewart, Slotine, Eliasmith 2016: spiking model of motor cortices and cerebellum, three-link arm, adaptation to kinematic and dynamic changes; stability argued mathematically; compared with 19 studies' data. Simulation. REPORTED (read: abstract) — [DeWolf 2016](https://doi.org/10.1098/rspb.2016.2134). DeWolf's 2021 Science Robotics piece "Spiking neural networks take control" exists (VERIFIED metadata, perspective, content not read) — [DOI](https://doi.org/10.1126/scirobotics.abk3268).
- Steffen, Simone, Damberger, DeWolf, Ly, Eliasmith 2026 (ICONS): NEF/SPA spiking architecture; basal-ganglia action selection between arm and locomotion; co-simulation Nengo + Isaac Sim; target reaching, digit drawing, path following, switching. Simulation only per abstract. REPORTED (read: abstract) — [DOI 10.1145/3822454.3822466](https://doi.org/10.1145/3822454.3822466), preprint listed by Semantic Scholar as arXiv 2606.11034 (not opened; id taken from tool output).
- Tieck et al. 2019 (FZI Karlsruhe): motor-primitive hierarchy, target reaching, two simulated experiments (workspace coverage; extreme and random targets), no planning or inverse kinematics. Simulation; trial counts not read. REPORTED (read: abstract) — [IJCINI 2019](https://doi.org/10.4018/ijcini.2019010101). A second Tieck paper on six-legged locomotion with spiking motor primitives and behaviour-based architecture exists (VERIFIED metadata) — [IROS 2019, DOI 10.1109/iros40897.2019.8968128](https://doi.org/10.1109/iros40897.2019.8968128).
- Stagsted et al. 2020 (RSS XVI): SNN PID on Loihi, 1-DOF UAV and a mobile robot; a reviewer said conventional PID gave better overshoot, oscillations and steady-state error (reviewer opinion, REPORTED via a search-tool summary of the RSS page). Numbers: not read. [RSS page](https://roboticsproceedings.org/rss16/p074.html). A follow-up "Event-based PID controller fully realized in neuromorphic hardware: a one DoF study" is listed at [ETH research collection](https://www.research-collection.ethz.ch/entities/publication/aa0d6b9c-722b-4c1f-9a97-710c87ed4c19) (existence from search result only).
- Bing et al. 2018 survey: VERIFIED existence and metadata; content summarised above — [DOI](https://doi.org/10.3389/fnbot.2018.00035).
- Juarez-Lora, Ponce-Ponce, Sossa, Rubio-Espino 2022: R-STDP SNN with step-forward encoding for self-tuning motion control of a joint robotic arm with changing friction; network placed in a loop with a PID receiving the same inputs; "simulations" demonstrate compensation; a 1-DOF arm per search summary. Simulation. Quantitative performance not read. REPORTED (read: abstract) — [PMID 35663727](https://www.pubmed.gov/35663727/), [DOI 10.3389/fnbot.2022.904017](https://doi.org/10.3389/fnbot.2022.904017).
- Hulea et al. 2021: analogue-hardware SNN, one finger joint; only qualitative result in abstract ("finger stopped in the angle interval"). REPORTED (read: abstract) — [DOI 10.3390/s21082730](https://doi.org/10.3390/s21082730).
- Looming/LGMD: Fu et al. 2021 test two LGMD-inspired models as the only collision sensor on micro robots with abrupt braking in physical crash scenarios (arena with LCD floor); the abstract states robustness is "corroborated" with no numbers in the part read. Real micro-robots, not arms. REPORTED (read: abstract via Europe PMC, PMID 34422912) — [Front. Robot. AI 2021](https://doi.org/10.3389/frobt.2021.529872). A 2025 LGMD neuro-robotic integration paper exists (Qin, Peng, Yue, Fu; metadata only) — [DOI 10.1098/rsif.2025.0433](https://doi.org/10.1098/rsif.2025.0433). Note: LGMD circuit is handcrafted from locust biology, not from a connectome; no controls tested against a trivial brake threshold in the text I read (NOT VERIFIED either way).
- iCub / neuromorphic: Kreiser et al. 2020 (on-chip SNN for head pose of iCub, [DOI 10.3389/fnins.2020.00551](https://doi.org/10.3389/fnins.2020.00551)), Vasco et al. 2016 (vergence control with neuromorphic iCub, [DOI 10.1109/humanoids.2016.7803355](https://doi.org/10.1109/humanoids.2016.7803355)), D'Angelo et al. 2022 (attentive system on SpiNNaker, [DOI 10.1088/2634-4386/ac6b50](https://doi.org/10.1088/2634-4386/ac6b50)). Existence VERIFIED (Crossref); content NOT read. These are perception/head/gaze tasks, not arm control, as far as titles say.

### Inferences
- INFERRED: across verified items, the "no external baseline, few or no stated repetitions, qualitative claims" pattern is common; this matches FlyMind's own lesson that single-number success needs shuffled/trivial controls.
- INFERRED: none of the verified arm papers claims a connectome-derived network; all are engineered. So FlyMind's hybrid has no direct precedent in this set.

### Gaps
- Numbers (trials, errors) for Tieck, Stagsted, Juarez-Lora, Fu: not read (abstract only or unreadable PDF). The RSS PDF was fetched but could not be decoded here (no PDF text tool).
- DeWolf / Applied Brain Research adaptive arm control on Loihi hardware specifically: not verified; only the 2016 simulation model and a 2021 perspective piece were confirmed.
- Ijspeert CPG robot results: only the review's existence verified.

## Q5. The Founders, Inc. video (https://youtu.be/NIMEbZJHQBM)

### Takeaway
Only the oEmbed metadata could be confirmed: title and channel. No repo, paper, website, product, press or "ant brain" claim was found in public sources by me. Who Alexander is and how the system works remain unknown.

### Cited Findings
- Title: "he invented an "artificial brain""; channel: Founders, Inc. (handle @fdotinc). VERIFIED via YouTube oEmbed on 2026-11-13 — [oEmbed endpoint](https://www.youtube.com/oembed?url=https://youtu.be/NIMEbZJHQBM&format=json).
- Upload date, description, links in description: NOT retrievable; the watch-page fetch returned only the page title (the fetch tool saw no description). NOT VERIFIED — [watch page](https://www.youtube.com/watch?v=NIMEbZJHQBM).
- Two web searches (one standard, one extended) for the channel plus title plus SO-101 plus spiking returned no page about this video or any "Alexander" artificial brain; results were unrelated (SpikerBot kit, Preprints.org Serv-Arm SNN paper, Google Brain). NOT VERIFIED that nothing exists, only that I found nothing.
- Observations from the video as supplied in the brief (UI "SO101 Full Cortical Body Motion v1.15", neurons such as shoulder_pan_pos_theta1, spike raster, membrane voltage plot, synapse(pre, post, weight), tabs Training and Connect to Robot, caption "98% of collisions avoided without training") are REPORTED from the owner's viewing; I did not watch the video. The caption has no trial count or control (NOT VERIFIED).
- "Ant brain" claims: none found in any source I searched. No data about an ant brain were on screen per the brief.

### Inferences
- INFERRED: with neuron names that are joint names plus direction plus Greek letters, the design is hand-assigned, not from an anatomical dataset; whether the Greek suffixes mean anything (e.g. receptor type, layer) is unknown.

### Gaps
- Author identity, date, repo, paper, method, trial protocol for the "98%" claim: not found; ask Adam for a transcript, the description text, or the full title card, or watch with a tool that reads captions.

## Q6. Which known method the on-screen design most resembles

### Takeaway
INFERRED only: a joint-named, push-pull, hand-wired SNN with a synapse builder, a spike raster/Vm viewer and a "Training" tab is closest to a hand-designed agonist/antagonist reflex or Braitenberg-style circuit for each joint, optionally with plasticity (R-STDP/Hebbian) added for the Training tab, rather than to NEF compilation or a connectome model.

### Cited Findings
- Closest verified analogues in structure: agonist-antagonist output cells (Kaiser 2016, Chadderdon 2012 via the Bing survey) and angle-interval path coding with Hebbian training (Hulea 2021); R-STDP on a joint arm in simulation (Juarez-Lora 2022). Sources as in Q3 and Q4.
- "Collision avoidance without training" is a claim of the LGMD/looming type in the literature, where the circuit is handcrafted and tested physically (Fu 2021, abstract level) — [Fu et al. 2021](https://doi.org/10.3389/frobt.2021.529872). Whether the video uses such a circuit is unknown.

### Inferences
- INFERRED: the likeliest reading of "no training needed" is that avoidance comes from hand-designed wiring (reflex-like), so a "98%" figure would measure the designer's rule, not learning; without trial count and a trivial-controller baseline, it cannot be compared with FlyMind numbers.
- HYPOTHESIS: the design could be run in FlyMind as a "designed layer" beside the connectome part, but whatever the layer decides will count as the designed part's decision, not the fly's, under the 3 Nov rule; this is for the report's rules section, not decided here.

### Gaps
- No evidence that any labelled variable (theta, beta) corresponds to a known model component; the video itself must be examined.
