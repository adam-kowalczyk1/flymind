# Literature matrix: fly CX as "working memory" for target bearing (SO-101 occlusion experiment)

Evidence tags: **[D]** directly supported by primary evidence; **[M]** supported by computational model only; **[H]** reasonable but unverified hypothesis; **[U]** unsupported.
"Verified Y" = title/authors/year/venue/DOI confirmed via web search or Europe PMC this session. Findings were taken from abstracts and search summaries, not full texts (no numeric effect sizes were extracted). Anything marked "not verified" must be checked before citation.

## (a) Literature matrix

| Source | Method | Finding | Relevance | Limitation | Ver. |
|---|---|---|---|---|---|
| Seelig & Jayaraman 2015, *Nature* 521:186. "Neural dynamics for landmark orientation and angular path integration". doi:10.1038/nature14446 | 2P Ca imaging EPG, walking VR | Bump tracks heading vs visual landmark; in darkness updated by self-motion; persists without cues; ring-attractor-like | Core: heading bump, dark persistence, path integration | Encodes own heading vs a stable scene, not object position | Y |
| Green et al. 2017, *Nature*. "A neural circuit architecture for angular integration in Drosophila". doi:10.1038/nature22343 | Imaging, ephys, silencing/activation PEN | PEN (P-EN) shift the bump by angular velocity; needed for heading tracking in darkness; activation shifts bump | Justifies PEN-L/R asymmetric drive | Gain/accuracy numbers not extracted here | Y |
| Turner-Evans et al. 2017, *eLife* 6:e23496. "Angular velocity integration in a fly heading circuit". doi:10.7554/eLife.23496 | Imaging, EM-anatomy, model | Recurrent loops with angular shift integrate velocity | Same | Same | Y |
| Kim, Rouault, Druckmann, Jayaraman 2017, *Science* 356:849. "Ring attractor dynamics in the Drosophila central brain". doi:10.1126/science.aal4835 | Imaging + optogenetic bump overwrite, flying flies | Artificial bump is maintained with natural dynamics; local excitation + global inhibition gives a unique persistent bump | Gold-standard persistence/perturbation test | Persistence over seconds-to-minutes in flies, not task-level memory | Y |
| Turner-Evans et al. 2020, *Neuron* 108:145. "The neuroanatomical ultrastructure and function of a biological ring attractor". doi:10.1016/j.neuron.2020.08.006 (query had "Curr Biol": wrong venue) | EM/imaging/perturbation | Anatomical and functional basis of ring attractor incl. Delta7/PEN roles | Connectivity-function link | Abstract-level only | Y |
| Hulse et al. 2021, *eLife* 10:e66039. "A connectome of the Drosophila central complex reveals network motifs suitable for flexible navigation and context-dependent action selection". doi:10.7554/eLife.66039 | Hemibrain EM connectome | Full CX wiring: EPG/PEN/Delta7/PFL motifs | Source type of the weights | Synapse counts are not synaptic strengths/sign-verified | Y |
| Franconville et al. 2018, *eLife* 7:e37017. "Building a functional connectome of the Drosophila central complex". | Opto + imaging + pharmacology | Delta7 is a major bottleneck node (summary level) | Delta7 inhibition | Delta7 transmitter identity debated in reviews | Y (title/venue); doi not extracted |
| Fisher, Lu, D'Alessandro, Wilson 2019, *Nature* 576:121. "Sensorimotor experience remaps visual input to a heading-direction network". doi:10.1038/s41586-019-1772-4 | Ephys + imaging | Visual cue-to-bump map is plastic, individual-specific, remapped by visuomotor experience | Cue-to-bump mapping is learned, not fixed Gaussian | Fixed `cue_sigma` in model has no counterpart | Y |
| Kim, Hermundstad, Romani, Abbott, Jayaraman 2019, *Nature* 576:126. "Generation of stable heading representations in diverse visual scenes". doi:10.1038/s41586-019-1767-1 | Imaging, opto, model | Plasticity turns 2D visual scenes into stable heading; partial representation completed | Same | Same | Y |
| Westeinde et al. 2024, *Nature* 626:819. "Transforming a head direction signal into a goal-oriented steering command". doi:10.1038/s41586-024-07039-2 | Imaging, ephys, chemogenetics | PFL3R/PFL3L/PFL2 get heading copies shifted ~120deg, compare with goal vector; PFL3R active when fly is left of goal and drives rightward turns; PFL2 raises steering speed at large error | Source for PFL3 steering | Goal is an internal allocentric vector (FC2), not an egocentric visual target | Y |
| Mussells Pires, Zhang, Parache, Abbott, Maimon 2024, *Nature* 626:808. "Converting an allocentric goal into an egocentric steering signal". doi:10.1038/s41586-023-07006-3 | Imaging, opto, silencing | FC2 track goal angle; PFL3 combine EPG heading + FC2 goal; PFL3 block degrades goal orientation | Same | Same | Y |
| Rayshubskiy et al. 2025 (eLife 13), bioRxiv 2020. "Neural circuit mechanisms for steering control in walking Drosophila". doi:10.7554/eLife.102230 (preprint 10.1101/2020.04.04.024703) | Ephys, imaging, EM | DNa02 high-gain, brief steering, integrates HD-system and sensory drive; DNa01 low-gain, sustained; see-saw L/R | DNa01 vs DNa02 roles; contralateral PFL3->DNa02 | Journal year given as 2024/2025 in different records; reviewers note DNa02 is itself downstream of other DNs | Y |
| Yang et al. 2024, *Cell* 187:6290. "Fine-grained descending control of steering in walking Drosophila". doi:10.1016/j.cell.2024.08.033 (bioRxiv 2023) | Ephys, behaviour, connectome | A set of DNs (incl. DNa02, DNg13) tied to different limb gestures/steering | Steering is multi-DN and gesture-specific; one L-R rate difference is a simplification | Abstract-level only | Y |
| Ribeiro et al. 2018, *Cell* 174:607. "Visual projection neurons mediating directed courtship in Drosophila". doi:10.1016/j.cell.2018.06.020 | Silencing, imaging | LC10 small-moving-object neurons needed to orient to/maintain proximity to a female | Object pursuit uses LC10 (optic lobe -> AOTU), not the heading ring | Courtship-specific | Y |
| Aptekar et al. 2015, *J Neurosci* 35:7587. doi:10.1523/JNEUROSCI.0652-15.2015; Keles & Frye 2017, *Curr Biol* (LC11; DOI not verified) | Imaging | LC columnar cells compute figure-ground / small-object features | Object detection lives in lobula columnar pathways | Not behavioural proof of CX-independence | Y / DOI not verified |
| Neuser et al. 2008, *Nature* 453:1244. "Analysis of a spatial orientation memory in Drosophila". doi:10.1038/nature07003 | Genetic block, behaviour | Ring-neuron/EB-dependent spatial orientation memory for an out-of-sight visual target | Closest fly precedent for "memory of a target direction after it vanishes" | Behavioural; no bump readout; stored in CX-related circuits per authors | Y |
| Strauss & Heisenberg 1993, *J Neurosci* 13:1852. doi:10.1523/JNEUROSCI.13-05-01852.1993 | CX structural mutants | CX defects reduce walking speed/activity/turning | CX is a locomotor-control hub | Visual fixation content not confirmed here | Y |
| Sun et al. 2017, *Nat Neurosci* 20:1104 "Neural signatures of dynamic stimulus selection in Drosophila" | Imaging ring neurons | Ring neurons show stimulus selection between competing visual stimuli | Multi-object competition for bump | DOI not verified (likely 10.1038/nn.4581) | Y (cite) / DOI N |
| Stone et al. 2017, *Curr Biol* 27:3069. "An anatomically constrained model for path integration in the bee brain". doi:10.1016/j.cub.2017.08.052 | Anatomy + model + robot | CX-like path-integration model driving a robot | Robotics precedent; **bee**, not Drosophila; homing, not target tracking | | Y |
| Lappalainen et al. 2024, *Nature* 634:1132. doi:10.1038/s41586-024-07939-3 | Connectome-constrained deep nets (visual system) | Connectome + task optimisation predicts neural responses | Connectome alone leaves free parameters; they were fitted | Visual system, not CX | Y |
| Shiu et al. 2024, *Nature* 634:210. doi:10.1038/s41586-024-07763-9 | Whole-brain LIF from connectome | Synapse-count-weighted LIF model predicts sensorimotor circuit activity (feeding, grooming) | Precedent for synapse-count LIF | Not tested on CX heading dynamics | Y |
| Maslov & Sneppen 2002, *Science* 296:910. doi:10.1126/science.1065103; Rubinov & Sporns 2010, *NeuroImage* 52:1059. doi:10.1016/j.neuroimage.2009.10.003 | Network null models | Degree-preserving rewiring; null-model practice for brain networks | Shuffle controls | Binary-degree oriented; weighted/phase structure needs adaptation | Y |
| Orban de Xivry, Coppe, Blohm, Lefevre 2013, *J Neurosci* 33:17301. doi:10.1523/JNEUROSCI.2321-13.2013 | Kalman model of pursuit | Two Kalman filters (visual + memory) reproduce pursuit incl. target blanking | Kalman baseline under occlusion is the accepted human model | Human oculomotor, not fly | Y |
| Bennett & Barnes (several, *Exp Brain Res* ~2003-2006) | Human pursuit with transient occlusion | Eye velocity during blanking driven by predictive memory of target velocity | Occlusion paradigm precedent | Exact title/DOI not verified | N |

## (b) Answers to questions 1-8

**1. What the EPG bump encodes.**
- The bump tracks the fly's own heading relative to visual landmarks, or relative to self-motion when cues are absent. [D: Seelig 2015; Green 2017; Turner-Evans 2017]
- The cue-to-bump mapping is plastic and individual-specific. A given scene is mapped by experience, not by a fixed retinotopic rule. [D: Fisher 2019; Kim 2019]
- The bump is a world-centred (allocentric-like) heading estimate. Goal direction is held separately (FC2). PFL3 compares heading with goal and outputs an egocentric steering signal. [D: Westeinde 2024; Mussells Pires 2024]
- The connectome supports these motifs. [D: Hulse 2021]
- **Not shown:** that the bump encodes the egocentric bearing of a discrete moving object. [U in the literature as read here]

**2. Persistence in darkness and ring-attractor dynamics.**
- The bump persists without visual input and is maintained by self-motion updating. [D: Seelig 2015; Green 2017]
- An overwritten (optogenetically relocated) bump is maintained, with local excitation and global inhibition producing a single bump. [D: Kim 2017]
- Ring-attractor architecture is anatomically and functionally supported. [D: Turner-Evans 2020; Hulse 2021]
- Heading integration in darkness is imperfect and drifts. [D qualitatively; I did not extract drift rates or gain numbers. Obtain them from Seelig 2015/Green 2017 before comparing to the model.]
- Recurrent connectivity and Delta7 are required to the extent that bump-shape and single-bump persistence depend on them. [D for PEN: Green 2017. Delta7-specific necessity is [M]/partly D; not verified at paper level here.]
- The Delta7 x8 scaling in the model is an engineering choice. [U as biology]

**3. Self-motion input.**
- PEN neurons are the angular-velocity shift pathway; they are needed for tracking in darkness; activating them shifts the bump. [D: Green 2017; Turner-Evans 2017]
- In the model, an asymmetric PEN-L/PEN-R current calibrated by `u_for(omega)` mimics this. That is a biologically inspired mechanism with an engineered calibration. [M]
- Integration accuracy is finite in flies, with gain error and drift. The robot's calibrated linear lookup removes the fly-like error by construction. [H]

**4. PFL3 / goal steering / DNa01 vs DNa02.**
- PFL3 L/R compare heading with a goal vector; PFL3R drives rightward turns when the fly is left of goal. [D: Westeinde 2024; Mussells Pires 2024]
- PFL3->DNa02 contralateral arrangement is consistent with the see-saw L/R scheme. [D for anatomy per Rayshubskiy 2025 summary; MaleCNS documentation not verified]
- DNa02 is high-gain/brief steering; DNa01 is low-gain/sustained. [D: Rayshubskiy 2025] In the model, DNa01 is a modelled copy of the DNa02 path (the brief's own statement). That is not in the data. [U]
- Steering involves more DNs (e.g. DNg13) and limb gestures. [D: Yang 2024]
- A linear L-R decode times 2.5 is a controller choice. [H/engineered]
- No evidence was found that PFL3 normally carries an egocentric visual-object bearing. The goal in flies is an internal FC2 vector. [D that the goal is FC2-derived]

**5. Limits of mapping to a robot arm tracking a moving target.**
- Small-object detection and courtship pursuit use LC10 and other lobula-columnar pathways, plus ventral/AOTU routes, in the optic lobe. [D: Ribeiro 2018; Aptekar 2015]
- Fly spatial memory of an out-of-sight visual target depends on ring neurons/EB (a CX-related structure). [D: Neuser 2008] This is the best biological precedent for the idea, but it is behavioural and gives no readout of the bump encoding the target's egocentric bearing.
- I found **no** direct finding that "object fixation is CX-independent". Treat that as an open point, not a cited fact. [U]
- A moving target is not a landmark. Landmarks are static, far-field cues that anchor heading; a moving object would be a rival input (Sun 2017 shows ring-neuron stimulus selection).
- The CX-as-memory use is: bump at target bearing + PEN updates from arm rotation. This compensates **ego-motion only**. It holds the last bearing relative to the world, so it is a **stationary-target** memory. Target velocity is not represented, so under occlusion the CX gives ZOH + ego-motion compensation, not extrapolation. [H, from model structure]
- Setting goal = 0 makes the PFL3 comparator a "bearing -> 0" controller. That is formally a heading-vs-goal analogue with the target as reference (sign-inverted), not a biological claim. [H]
- Non-Gaussian, plastic cue mapping (Fisher 2019) means the Gaussian cue is a modelling shortcut.

**6. Shuffled-connectivity controls.**
Appropriate controls, in order of diagnostic value:
- (i) Lesion: delete Delta7, or PEN, or the EPG-EPG/Delta7 loop. This tests necessity (causal) and is the cleanest.
- (ii) Phase-scramble: randomly permute ring-phase labels of the weights while keeping each neuron's total in/out strength. This tests whether phase-specific structure matters.
- (iii) Degree/strength-preserving rewiring (Maslov-Sneppen style; for weighted networks use strength-preserving variants, with strength per node matched). [H: Maslov & Sneppen and Rubinov & Sporns describe null-model practice; I did not verify details for weighted ring structures]
- (iv) A hand-built idealised cosine ring with matched gains, to show the connectome weights add anything beyond ring symmetry.
- Re-tune global gains separately for each control (or report un-tuned and tuned results), otherwise the control fails for trivial stability reasons.
- Use many shuffle seeds and report the distribution, not one draw.
- Lappalainen 2024 is a reminder that connectome-based models use fitted, not purely connectome-derived, parameters. Shiu 2024 shows uniform-parameter synapse-count models can still predict sensorimotor behaviour.
- A synapse-count profile does not equal synaptic efficacy or sign. [D as general caveat]

**7. Persistent working memory vs cached/externally computed estimate.**
Standard criteria, all [H] as a checklist drawn from Kim 2017 and standard attractor practice:
- Activity (bump) persists after input is removed, with no external readout feeding it.
- Perturbation: relocate the bump mid-occlusion and check that behaviour follows the new location (Kim 2017 optogenetic overwrite as the analogue).
- Drift statistics: bump phase diffuses/drifts and the variance grows with occlusion time, as expected of an attractor with noise. A cache would show zero or externally imposed drift.
- Causal necessity: lesioning the recurrent loop or PEN abolishes persistence and degrades behaviour.
- Check for hidden state channels outside the SNN: whether `agent.py` passes the last cue, a clock, or the Kalman estimate to the controller. Also check whether the steering decoder is re-calibrated using ground truth during occlusion. These would make the result an "externally computed estimate".

**8. Kalman/ZOH baselines under occlusion.**
- Human pursuit during target blanking is well modelled as a visual Kalman filter plus a memory filter, with velocity memory sustaining pursuit. [D/M: Orban de Xivry 2013; Bennett & Barnes titles not verified]
- A constant-velocity Kalman filter is a fair, strong baseline for a moving target. Include ZOH, constant-velocity Kalman, and a lesioned-CX controller.
- Stone 2017 is a CX-inspired robot path-integration model (bee), not a target-tracking comparison. I found no paper comparing a ring-attractor model to a Kalman filter on occluded tracking. [U: do not claim novelty or precedent either way]

## (c) The model's biological claims, classified

| Claim in the model | Class |
|---|---|
| EPG ring with recurrent/Delta7 inhibition yields a persistent bump | Biological (supported) + biologically-inspired implementation |
| Weights from MaleCNS synapse-count profiles vs phase difference | Biologically-inspired (connectome-derived but idealised equal spacing; count != efficacy) |
| Delta7 inhibition x8 | Engineered |
| Self-rotation as asymmetric PEN-L/R current via calibrated `u_for(omega)` | Biological mechanism (PEN), engineered calibration |
| Gaussian current at the egocentric bearing of the target | Engineered; not shown to be what EPG encodes (unvalidated) |
| PFL3 goal input cos(theta - goal +/- 45deg), goal = 0 | Biologically-inspired (Westeinde 2024 ~ cosine goal comparison); goal semantics repurposed (unvalidated) |
| PFL3_L->DNa02_R, PFL3_R->DNa02_L | Biological (from data; MaleCNS source not verified here) |
| DNa01 as modelled copy of the DNa02 path | Unvalidated/engineered |
| Linear decode of DNa L-R rate difference x 2.5 -> angular velocity | Engineered |
| Bump acts as target working memory through occlusion | Unvalidated (needs controls in Q6/Q7); only supported by Neuser 2008 at behavioural level |
| CX as the pathway for target pursuit | Unsupported (LC10/optic-lobe pathways implicated; Ribeiro 2018) |

---
_PI verification (2026-10-27): all 24 DOIs in this file were resolved via api.crossref.org and the returned titles/years/
first authors match the cited works. Claims were extracted by the literature agent from abstracts/summaries, not full texts._
