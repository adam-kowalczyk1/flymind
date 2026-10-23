# Drosophila courtship-pursuit steering circuit: LC10a -> AOTU019 / AOTU025 -> DNa02 -> turning

Researched 2026-10-23. The main source is Collie et al. (Wilson lab), "Specialized parallel pathways for adaptive control of visual object pursuit". It was posted as a bioRxiv preprint on 2025-04-26 (doi:10.1101/2025.04.23.650240) and published in *Neuron* in 2026 (Cell Press PII S0896-6273(26)00001-2; the Neuron DOI was not confirmed because cell.com returned 403). Figure values marked **(fig-read)** were read by eye from the rendered preprint PDF figures. They are approximate, roughly ±10%, and are not exact published numbers.

## Q1. What does LC10a encode?

### Takeaway
LC10a cells are cholinergic visual projection neurons. They detect small moving objects in a retinotopic map of the ipsilateral visual field (about −15° to 165° azimuth per side, with ~15° of binocular overlap) and project to the AOTU. Their gain is turned up by P1-mediated arousal: the pathway is "dormant" unless P1 is active. Steering follows the right-minus-left difference in LC10a output.

### Cited Findings
- LC10 neurons preferentially respond to small moving objects through an antagonistic, motion-based center-surround mechanism. Males with LC10 silenced cannot orient toward or stay near a female. Unilateral LC10 activation reproduces orienting and ipsilateral wing extension. P1-controlled courtship arousal increases how strongly LC10 induces wing extension (Ribeiro et al. 2018, Cell 174:607). — [Janelia summary](https://www.janelia.org/node/49331); [FlyBase ref](https://flybase.org/reports/FBrf0239559)
- LC10a is cholinergic (VFB citing Davis et al. 2020). — [VFB LC10a FBbt_00111747](https://www.virtualflybrain.org/term/lc10a-fbbt_00111747/)
- Hindmarsh Sten et al. 2021 (Nature 595:549, doi:10.1038/s41586-021-03714-w) report that LC10a gain is selectively increased during courtship, raising sensitivity to moving targets. P1 activity tracks pursuit intensity and tunes LC10a gain. "The LC10a pathway lies dormant in the brain unless P1 neurons are active." P1 does not innervate the AOTU directly; it acts like a rheostat on LC10a gain. — [PMC8973426](https://pmc.ncbi.nlm.nih.gov/articles/PMC8973426); [Springer](https://link.springer.com/article/10.1038/s41586-021-03714-w)
- In the same paper, P1 activity predicts LC10a evoked responses almost linearly (slope m ≈ 0.85–0.86, r = 0.68). P1 activity correlates with the Tracking Index (r = 0.69 ± 0.075). — [PMC8973426](https://pmc.ncbi.nlm.nih.gov/articles/PMC8973426)
- LC10a responses as a population are stronger to progressive (front-to-back) than regressive motion. Unilateral LC10a activation drives acute ipsilateral turning. — [PMC8973426](https://pmc.ncbi.nlm.nih.gov/articles/PMC8973426)
- **Hindmarsh Sten 2021 spiking model (directly reusable).** These are the paper's model parameters, not measured biology.
  - Units are LIF neurons with spike-rate adaptation: τm = 10 ms, V_rest = −65 mV, Rm = 10 MΩ, E_K = −70 mV, threshold −50 mV, reset to V_rest, Δg_sra = 14 nS per spike, τ_sra = 200 ms, Euler step 3 ms.
  - There are 20 LC10a units per hemisphere in the tethered model, each covering 10.5° (0–180° field with 15° binocular overlap). The free-behavior model uses 40 units of 7.5° each.
  - Input current is Ie = Sf·Σ 1/[(1+e^(β·t_i−α))(1+e^(−σ·t_i+κ))] with κ = 0.849, σ = 5.527, α = −0.186, β = 15.588, and Sf = 1.5 nA (tethered) or 2.5 nA (free). Input is driven mostly by motion in the past 500 ms.
  - Turn = (right spikes − left spikes): a net 200 spikes gives a 1 rad turn (tethered), and 300 spikes/s ≈ 1 rad/s in the P1-modulated and free-behavior models.
  - The model is sensitive to angular position, not retinal size, and treats LC10a as fully selective for progressive motion.
  - — [PMC8973426](https://pmc.ncbi.nlm.nih.gov/articles/PMC8973426)
- Collie et al. assigned LC10a meshes anterior–posterior visual coordinates from −15° to 165° by mapping the lobula's medial–lateral axis onto retinal azimuth. — [bioRxiv 2025.04.23.650240](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
- LC10a outputs are selective: each downstream cell receives input from only a subset of the LC10a population. AOTU019 samples mostly LC10a cells covering the frontal field, and AOTU025 samples mostly lateral-field LC10a cells. — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
- Cowley et al. 2024 (Nature, doi:10.1038/s41586-024-07451-8) used "knockout training" of a deep network to map model units onto visual projection neuron types. They found a combinatorial population code in which most LC types, not LC10a alone, contribute to representing the female and driving courtship behavior. — [Princeton summary](https://research.princeton.edu/news/how-fruit-flies-see-love-ai-model-male%E2%80%99s-visual-neurons-during-courtship)
- Ribeiro lab (unpublished, Chen & Ribeiro): silencing AOTU008, described as a major LC10a target, reduced time spent following. — [LMU project PDF](https://cms-cdn.lmu.de/media/19-biologie/gsn_ribeiro_project_2.pdf) (preliminary, not peer-reviewed)

### Inferences
- For a robot, LC10a can be modeled as a bank of ipsilateral, position-tuned small-target motion detectors, about 20 per side, tiling 0–180° with ~15° frontal overlap. An "arousal" scalar would multiply their gain, with 0 meaning the pathway is off.

### Gaps
- No primary source found for the anatomical LC10a count per hemisphere. A non-peer-reviewed GitHub project built on FlyWire v783 lists 115 left and 119 right LC10a ([fruitfly-lab](https://github.com/webergithub/fruitfly-lab)). **Unverified**: confirm in FlyWire Codex or the Schlegel/Matsliah 2024 cell-type tables. The "20 per side" figure is a model choice, not an anatomical count.
- The full text of Cowley 2024 was not read, so its quantitative LC10a findings are not included.

## Q2. What are AOTU019 and AOTU025 (transmitter, midline crossing, targets, push-pull)?

### Takeaway
AOTU019 is GABAergic (inhibitory). There is one per hemisphere, its receptive field covers the frontal/midline region, and it projects across the midline to the **contralateral** DNa02 (and other steering DNs). AOTU025 is cholinergic (excitatory), has a lateral/peripheral receptive field, and projects to the **ipsilateral** DNa02. Because ipsilateral excitation and contralateral inhibition act on the left/right DNa02 pair together, the circuit forms a "see-saw" push-pull. Depolarizing either cell turns the fly toward its own side.

### Cited Findings
- "AOTU025 is cholinergic, whereas AOTU019 is GABAergic" (EM-based transmitter prediction plus genetic evidence, Fig. S2b). — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
- AOTU019 is inhibitory and contralateral, with dendritic compartments in both the AOTU and the LAL. AOTU025 is excitatory and ipsilateral, with dendrites only in the AOTU (Fig. 2a legend). — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
- "There is only one AOTU019 cell in each hemisphere, and this is only one of 14 cells postsynaptic to LC10a and presynaptic to DNa02." — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
- The other 12 types that are LC10a-postsynaptic and DNa02-presynaptic (Fig. 1c) are CB0359, AOTUv3B, AOTU027, LAL027, AOTU015b, AOTU026, AOTU015a, CB2070, CB3127, AOTU012, CB0356, and LAL028/029. All non-AOTU019 inputs are predicted excitatory. — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
- **Receptive fields.** AOTU019 fires most for objects near the midline, with a peak of ~38 spikes/s at about +30° (fig-read, Fig. 1h). AOTU025 peaks at ~43 spikes/s at about +55–60° and stays elevated out to ~120° (fig-read). Baseline is ~15–20 spikes/s for both (fig-read). Response latency is 39.98 ± 8.46 ms for AOTU019 and 35.88 ± 9.52 ms for AOTU025. — [bioRxiv Fig. 1](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
- **Direction selectivity.** AOTU019 is more direction-selective than AOTU025 (p < 0.05). It fires more when the object moves away from the midline, which is when the error is growing. The model uses DSI = 0.7 for AOTU019. — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
- **Current injection.**
  - Depolarization raised firing by about 30–50 spikes/s, from ~20 to ~70 spikes/s (fig-read, Fig. 2b), and drove ipsilateral turning of about +50°/s peak (fig-read) for both cell types (p < 0.0001).
  - Depolarizing AOTU019 also increased forward velocity (p < 0.005).
  - Hyperpolarizing AOTU019 drove contralateral turning (p < 0.05). Hyperpolarizing AOTU025 did not (p = 0.362).
  - — [bioRxiv Fig. 2b](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
- **Firing rate vs. later turning (Fig. 2h, rotational velocity 200 ms after firing).** The relation is roughly linear for both cells. Turning goes from about −50°/s at 0 spikes/s to about +80–90°/s at 80 spikes/s, crossing zero near 30–40 spikes/s (fig-read). That gives a slope of about 1.7 °/s per spike/s (fig-read). The two cell types did not differ (p = 0.156). — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
- Firing leads turning. Median peak cross-correlation lag with rotational velocity is about −225 ms for AOTU019 and about −190 ms for AOTU025 (fig-read, Fig. 2g). AOTU025 correlates more strongly with turning, and with a shorter lag (p < 0.01). — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
- **Gain modulation.**
  - Arousal raised AOTU019 activity more than AOTU025 activity (p < 0.0001).
  - AOTU019 firing rises with forward velocity, from ~18 to ~38 spikes/s over 0–10 mm/s (fig-read, Fig. 4f), and its changes are nearly synchronous with forward-velocity changes (lag −3.00 ± 8.46 ms).
  - High forward velocity increases the AOTU019 right-minus-left visual response (p < 0.01) but not the AOTU025 one (p = 0.768).
  - Kir2.1 silencing of AOTU019 lowered steering gain (p < 0.05, p < 0.01).
  - — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
- Female-specific arousal neurons connect more strongly to AOTU019 than to AOTU025. AOTU019 has an unusually thick cable diameter and makes strong connections onto some flight-steering DNs (Fig. S1c). — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
- **Functional division of labor.** AOTU025 detects the object in the periphery and steers it into the central zone. AOTU019 detects the object inside the central zone, steers it to the midline, and increases forward velocity. — [Neuron 2026](https://www.cell.com/neuron/fulltext/S0896-6273(26)00001-2); [Wilson lab page](https://wilson.hms.harvard.edu/publication/specialized-parallel-pathways-adaptive-control-visual-object-pursuit)

### Inferences
- **Sign table for a small SNN:**

  | Connection | Sign | Side |
  |---|---|---|
  | LC10a → AOTU019 | + | ipsilateral |
  | LC10a → AOTU025 | + | ipsilateral |
  | AOTU025 → DNa02 | + | ipsilateral |
  | AOTU019 → DNa02 | − | contralateral |
  | Other minor AOTU/CB/LAL → DNa02 | + | ipsilateral |

- With this wiring, an object on the right excites the right DNa02 through AOTU025-R and inhibits the left DNa02 through AOTU019-R. Both effects push R−L positive, so the turn is to the right, toward the object.

### Gaps
- No AOTU025 cell count per hemisphere was found in the text. Fig. 1c shows a single bar, which suggests about one cell per side, but this is **unverified**.
- No numeric connectivity was found for the arousal (P1/pC1) inputs onto AOTU019/AOTU025.

## Q3. DNa02 and other steering DNs

### Takeaway
DNa02 is a single cell per side. It is a high-gain, transient steering DN whose right-minus-left firing rate is linearly related to the fly's rotational velocity, and it leads turning by about 150–200 ms. Its partner DNa01 is lower-gain and sustained. Several other DNs (DNa03, DNb02, DNg13, DNa11, DNa01) also receive AOTU019/AOTU025 output. DNa02's inputs follow a see-saw pattern: excitation of one copy usually comes with inhibition of the other.

### Cited Findings
- Rayshubskiy, Holtz, Bates, Vanderbeck, Serratosa Capdevila, Rockwell & Wilson, eLife 2025 (doi:10.7554/eLife.102230). DNa02 predicts transient high-gain steering and DNa01 predicts sustained low-gain steering. Rotational velocity is linearly related to the right-minus-left DNa02 firing rate. DNa02 and DNa01 have largely non-overlapping brain inputs, and there is one cell per hemisphere for each. — [eLife 102230](https://elifesciences.org/articles/102230)
- In that paper, DNa02 is recruited about 150 ms before a stimulus-evoked turn. Slopes of rotational velocity vs. firing rate differ between DNa02 and DNa01 (p = 10⁻⁴, n = 4). — [eLife 102230](https://elifesciences.org/articles/102230)
- Connectome motif (FlyWire v783):
  - PFL3 (12 per hemisphere) excites the ipsilateral DNa02, DNa03 and LAL010, which in turn excite DNa02. PFL3 also excites cells that inhibit the contralateral DNa02/DNa03/LAL010.
  - Inputs such as MBON32 form a see-saw: excitation of one DNa02 is accompanied by inhibition of the other.
  - Glutamatergic connections are treated as inhibitory.
  - — [eLife 102230](https://elifesciences.org/articles/102230)
- Optogenetics is weak. Unilateral ReaChR activation of DNa02 gave only a small ipsilateral rotational bias. Bilateral GtACR1 silencing did not change rotational speed. Reviewers note that DNa02 alone cannot drive all turning and point to DNp09 and DNa03 as stronger turn drivers. — [eLife 102230](https://elifesciences.org/articles/102230); [eLife reviews](https://elifesciences.org/reviewed-preprints/102230/reviews)
- In Collie et al., the right-minus-left DNa02 visual response to rightward motion pulses peaks at about 30–40 spikes/s (fig-read, Fig. 2e, n = 11). The weighted sum of AOTU019 and AOTU025 right-minus-left activity predicts DNa02 right-minus-left activity. The matching turn peaks are about 100–180°/s (fig-read, Fig. 2f). DNa02 right-minus-left activity drives steering about 200 ms later. — [bioRxiv Fig. 2](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
- Behavioral steering gain during pursuit (slope of rotational velocity vs. object position in the frontal ±60°) has a median of about 2.0 °/s per ° at low forward speed and about 3.3 °/s per ° at high forward speed (fig-read, Fig. 4d; n = 40, p < 0.0001). Rotational velocity reaches about ±130°/s (low speed) to ±180°/s (high speed) at ±60° (fig-read, Fig. 4c). — [bioRxiv Fig. 4](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
- Yang et al. 2024 (Cell 187:6290, doi:10.1016/j.cell.2024.08.033). Each steering DN type is a single left/right pair. Ipsiversive types are DNa01, DNa02, DNb05 and DNg13; DNb06 is contraversive. DNa02 shortens ipsilateral stride, mainly through the return stroke, and bilateral activation lowers forward velocity. DNg13 lengthens contralateral stride. DN firing leads rotational velocity and stride changes by about 150 ms. DNa02's stride-locked modulation is "only about 15 spikes/sec", about 10% of its dynamic range, which implies a range of roughly 150 spikes/s. DNa02 receives direct central-complex (PFL3) and ascending-neuron input. — [PMC12778575](https://pmc.ncbi.nlm.nih.gov/articles/PMC12778575/)

### Inferences
- For yaw control: ω(t) = k·(DNa02_R − DNa02_L)(t − ~200 ms). Rough scales are a DN right-minus-left difference of 30–40 spikes/s for a 100–180°/s turn, and a closed-loop behavioral gain of 2–3.3 °/s per °.
- A forward-speed or arousal term should scale the AOTU019 pathway gain up, but not the AOTU025 pathway gain.

### Gaps
- DNa02's neurotransmitter was not confirmed in the sources read (it is commonly assumed cholinergic, but **unverified** here).
- The absolute numeric slope of rotational velocity vs. DNa02 rate (°/s per spike/s) from Rayshubskiy is only in figures and was not extracted.
- Braun et al. 2024 and Sapkal et al. 2024 (DN network papers) were not reviewed within the tool budget.

## Q4. Concrete synapse counts and neuron numbers

### Takeaway
The only published counts found are in Collie et al. Fig. 1c (FlyWire/FAFB v783, connections ≥5 synapses, averaged across hemispheres). AOTU019 and AOTU025 each receive about 1,400–1,500 LC10a synapses. AOTU019 sends about 180 synapses to DNa02 and about 500 in total to steering DNs. AOTU025 sends about 170 to DNa02 and about 300 in total. All values below are **fig-read** (±10%), not tabulated numbers.

### Cited Findings
All rows come from Collie et al. 2025/2026, Fig. 1c ([bioRxiv](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)): FlyWire/FAFB v783 with fafbseg v0.14.1, connections <5 synapses excluded, counts per cell averaged across hemispheres, read by eye from the bar chart.

| Pre → Post | Synapses (fig-read) | Sign / side |
|---|---|---|
| LC10a (all) → AOTU019 | ~1,450–1,500 | + (ACh), ipsi |
| LC10a (all) → AOTU025 | ~1,400–1,450 | + (ACh), ipsi |
| LC10a → CB0359 (next largest) | ~550 | + |
| AOTU019 → DNa02 | ~180 | − (GABA), **contralateral** |
| AOTU019 → DNa03 | ~210 | − (GABA), contralateral (inferred from "targets contralateral copies of these DNs") |
| AOTU019 → DNb02 | ~50 | − |
| AOTU019 → DNa11 | ~45 | − |
| AOTU019 → DNa01 | ~10 | − |
| AOTU019 → all steering DNs | ~500 | |
| AOTU025 → DNa02 | ~170 | + (ACh), **ipsilateral** |
| AOTU025 → DNa03 | ~105 | + ipsi |
| AOTU025 → DNa11 | ~20 | + ipsi |
| AOTU025 → all steering DNs | ~300 | |
| Each of the other 12 LC10a→DNa02 types → DNa02 | ~20–70 each | + ipsi |

- DNa03 sends most of its output to other DNs within the central brain, including strong connections onto DNa02 (Fig. S1b). — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
- In Collie's network model, each AOTU cell's contribution is weighted by its synapse count onto DNa02. The model equations are DNa02_R = AOTU025_R − AOTU019_L, DNa02_L = AOTU025_L − AOTU019_R, and r = k·(DNa02_R − DNa02_L), with k = 1.2. Other settings are a 200 ms delay, 100 Hz simulation steps, 2 Hz low-passed perturbation noise, and success defined as staying within ±10°. — [bioRxiv Methods](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
- Neuron counts per hemisphere:
  - AOTU019: 1 per hemisphere (Collie) — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.04.23.650240v1.full)
  - DNa02: 1 per hemisphere; DNa01, DNb05, DNb06 and DNg13 are also single pairs (Rayshubskiy; Yang) — [eLife](https://elifesciences.org/articles/102230); [PMC12778575](https://pmc.ncbi.nlm.nih.gov/articles/PMC12778575/)
  - PFL3: 12 per hemisphere — [eLife](https://elifesciences.org/articles/102230)
  - LC10a: ~115–119 per hemisphere in FlyWire according to a non-peer-reviewed project, **unverified** — [fruitfly-lab](https://github.com/webergithub/fruitfly-lab)
- The hobby simulation in that project uses the rule weight = synapse count × transmitter sign × 0.275 mV with a 1.8 ms delay (a Shiu et al.-style LIF). This is a modeling convention, not data. — [fruitfly-lab](https://github.com/webergithub/fruitfly-lab)

### Inferences
- The two pathways have similar weight onto DNa02 (~180 vs ~170). So a 1:1 weighting of AOTU019 (inhibitory, contralateral) against AOTU025 (excitatory, ipsilateral) is consistent with the data, and Collie's model uses exactly this weighting.
- Per individual LC10a cell, the synapse count onto AOTU019 is on the order of 5–60 (Fig. 1d colour scale 5–60).

### Gaps
- No tabulated (exact) synapse counts were found. Exact values need a FlyWire Codex or connectome-file query (FlyWire v783 `connections` table, filter by `AOTU019`, `AOTU025`, `DNa02`). Downloading those files was outside this task's permissions.
- Male-specific (MaleCNS) counts were not found. Collie used the female FAFB brain and notes that comparing against a male connectome is future work.
- Fig. S1 (supplement with the full AOTU→DN matrix and flight DNs) was not in the main PDF and was not read.
