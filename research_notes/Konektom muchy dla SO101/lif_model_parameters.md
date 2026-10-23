# LIF / ALIF parameters for connectome-constrained Drosophila simulation (for a NumPy ALIF network, dt = 1 ms)

Research date: 2026-10-23. Primary sources read: the Shiu et al. 2024 Methods (Europe PMC full text PMC11446845), `model.py` from philshiu/Drosophila_brain_model (raw GitHub), Lappalainen et al. 2024 Methods (PMC11525180), Betkiewicz et al. 2020 Methods (PMC7294456), Vaxenburg et al. 2025 (PMC12310536), Eon Systems' technical post, and the Loihi 2 port of the Shiu model (arXiv HTML).

## 1. Shiu et al. 2024 (Nature): exact LIF parameters, weight formula, sign mapping, Poisson input, repo

### Takeaway
The Shiu model is a current-based LIF with an exponentially decaying synaptic variable g, measured in mV. Parameters: V_rest = V_reset = −52 mV, V_th = −45 mV (7 mV above rest), τ_m = 20 ms, τ_syn = 5 ms, refractory period 2.2 ms, delay 1.8 ms. Each weight is w = sign(pre) × N_syn × 0.275 mV. W_syn = 0.275 mV is the model's only free parameter. ACh, DA, 5-HT and OA count as excitatory (+1); GABA and Glu count as inhibitory (−1). Input neurons get Poisson drive at 10–260 Hz (150 Hz by default in code), and each Poisson event has weight 250 × W_syn.

### Cited Findings
- **Equations (Methods):** dv_i/dt = (g_i − (v_i − V_resting)) / T_mbr; dg_i/dt = −g_i / τ; g_i ← g_i + w_j,i when neuron j spikes. On a spike, v is reset and g is set to 0 mV. v cannot change during the refractory period. — [Shiu et al. 2024, Nature 634:210, Methods (PMC11446845)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/), DOI [10.1038/s41586-024-07763-9](https://doi.org/10.1038/s41586-024-07763-9)
- **Values (Methods):**
  - V_resting = −52 mV; V_reset = −52 mV; V_threshold = −45 mV.
  - R_mbr = 10 kΩ·cm²; C_mbr = 2 µF·cm⁻²; T_mbr = C×R = 20 ms.
  - T_refractory = 2.2 ms; τ (synapse decay) = 5 ms; T_dly = 1.8 ms ("time delay from spike to change in membrane potential").
  - W_syn = 0.275 mV, the free parameter.
  - — [Shiu et al. 2024 Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/)
- **Sources the code cites for each constant** (comments in `default_params`):
  - V and τ_m: Kakaria & de Bivort 2017, doi:10.3389/fnbeh.2017.00008.
  - τ = 5 ms: Jürgensen et al., doi:10.1088/2634-4386/ac3ba6.
  - t_rfc = 2.2 ms: Lazar et al., doi:10.7554/eLife.62362.
  - t_dly = 1.8 ms: Paul et al. 2015, doi:10.3389/fncel.2015.00029.
  - "w_syn: Free parameter".
  - — [model.py, philshiu/Drosophila_brain_model](https://github.com/philshiu/Drosophila_brain_model/blob/main/model.py)
- **The code:**
  - Brian2 equations: `dv/dt = (v_0 - v + g) / t_mbr : volt (unless refractory)`, `dg/dt = -g / tau : volt (unless refractory)`.
  - Threshold `v > v_th`; reset `v = v_rst; w = 0; g = 0 * mV`.
  - Synapses: `Synapses(neu, neu, 'w : volt', on_pre='g += w', delay=t_dly)` with `syn.w = df_con['Excitatory x Connectivity'] * w_syn`.
  - Trial: t_run = 1000 ms, n_run = 30.
  - — [model.py](https://github.com/philshiu/Drosophila_brain_model/blob/main/model.py)
- **Weight formula (Methods):** w_j,i = (FlyWire synapse count) × (+1 if j is excitatory, −1 if j is inhibitory) × W_syn. This is linear in synapse count. Excitatory and inhibitory synapses have equal magnitude. — [Shiu et al. 2024 Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/)
- **How W_syn was chosen:** "such that activation of sugar GRNs at 100 Hz resulted in roughly 80% of maximal MN9 firing". — [Shiu et al. 2024 Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/)
- **Robustness checks:**
  - W_syn ±30%: predictions matched the default model in 90.2% of cases (−30%) and 95% of cases (+30%). Accuracy was 85% and 88%, against 91% for the default.
  - Inhibitory:excitatory ratio ±50%: accuracy 88–89%.
  - Not tested: V_rest, V_th, τ_m, T_dly, T_ref. The authors argue these mainly rescale firing rates.
  - — [Shiu et al. 2024 Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/)
- **NT → sign mapping:**
  - NT predictions come from Eckstein et al. (ref. 3), made per synapse. Cleft score cutoff is 50.
  - A neuron is inhibitory if more than half of its presynaptic sites are predicted GABA or Glu.
  - "Neurons predicted to be dopaminergic, octopaminergic or serotonergic are assigned to the excitatory category."
  - Each neuron is exclusively excitatory or inhibitory (Dale's principle).
  - FlyWire-wide breakdown: about 55% ACh, 24% Glu, 14% GABA, 7% DA/OA/5-HT.
  - — [Shiu et al. 2024 Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/)
- **Glu-as-excitatory control:** if glutamate is assumed excitatory instead, the bitter/Ir94e inhibition result disappears. The optogenetic false-positive rate rises from 1% to 16%. — [Shiu et al. 2024 Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/)
- **Poisson input:**
  - Rates in the paper: sugar GRNs 10–200 Hz, water GRNs 20–260 Hz. The top 200 neurons were re-activated at 25–200 Hz. Silencing sweeps used 50–120 Hz in 10 Hz steps.
  - "Activated" means firing above 0 Hz.
  - In code: `r_poi = 150 Hz` by default and `f_poi = 250` ("250 is sufficient to cause spiking"). Each Poisson event therefore adds 250 × 0.275 = 68.75 mV to g. Poisson-target neurons have refractory set to 0 ms.
  - — [Shiu et al. 2024 Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/); [model.py](https://github.com/philshiu/Drosophila_brain_model/blob/main/model.py)
- **Dataset:** all 127,400 proofread neurons of FlyWire materialization v630. The repo also ships v783 files (`Completeness_783.csv`, `Connectivity_783.parquet`). The v630 files are `2023_03_23_completeness_630_final.csv` and `2023_03_23_connectivity_630_final.parquet`. — [Shiu Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/); [repo README](https://github.com/philshiu/Drosophila_brain_model)
- **Stated limitations:**
  - No gap junctions, non-spiking neurons, internal state, neuropeptides or neuromodulation.
  - Basal rate is 0 Hz, so "inhibitory connections to an inactive neuron have no effect".
  - Absolute firing rates are "unlikely to be accurate".
  - Reported accuracy: 91% across 164 tested predictions, 84% when the split-GAL4 screen is excluded.
  - — [Shiu et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/)
- **Loihi 2 port of the same model:**
  - Rescaled to v₀ = v_r = 0 and v_th = 7 mV.
  - Integer weights range from −2405 to 1897; most have magnitude under 100.
  - At a 1 ms step, the 2.2 ms refractory period and the 1.8 ms delay both round to 2 steps.
  - The 1 ms step "largely mitigates" the error from feeding Poisson input into g.
  - — [Wang et al. 2025, arXiv:2508.16792](https://arxiv.org/html/2508.16792v1)

### Inferences
- **The synapse is a single exponential, not an α-function.** The paper and code say "α-synapse", but the equations are a first-order exponential in g, low-pass filtered by the membrane. Port the equations, not the label.
- **PSP size per synapse (my calculation, not in the paper).** A kick of w into g produces a membrane peak of 0.158·w at about 9.2 ms; with Euler at dt = 1 ms the peak is 0.177·w. So one synapse gives about 0.043 mV. About 160 near-coincident synapse-spikes are needed to cross the 7 mV gap. A 50-synapse connection gives about 2.2 mV.
- **Each Poisson event forces a spike.** A 68.75 mV kick gives a peak of about 10.8 mV, which is above the 7 mV gap. The output rate of an input neuron is therefore roughly the Poisson rate. In a small network you can simply inject spikes.
- **Direct NumPy port at dt = 1 ms:**
  - `v += dt/20*(-52 - v + g)`; `g *= exp(-dt/5)`.
  - On a spike: `v = -52`, `g = 0`, refractory for 2 steps.
  - Spikes arrive at the postsynaptic neuron 2 steps later (delay 1.8 ms → 2 steps).
  - `W = sign[:,None] * N_syn * 0.275` (mV).
- **W_syn may need re-tuning.** It was fit for a 127k-neuron graph with very large fan-in. A small subnetwork has far less convergent input and will probably go silent at 0.275 mV. Re-calibrate it against an observable output, as Shiu did with "80% of max MN9 at 100 Hz input", rather than copying the number.

### Gaps
- The Methods do not say whether connections were filtered by a minimum synapse count before simulation, or whether the v630 parquet was pre-thresholded. I did not open the parquet.
- I did not read Supplementary Tables 9–11 (robustness details).

## 2. Is glutamate inhibitory in the insect CNS (GluCl)?

### Takeaway
Yes, in many central circuits. Glutamate acts through the glutamate-gated chloride channel GluClα, which is blocked by picrotoxin. Liu & Wilson 2013 is the canonical citation. It is not universally inhibitory, though. It is excitatory at the larval NMJ through iGluRs (my background knowledge, not checked in this session). Shiu et al. explicitly call the "Glu = inhibitory" rule a default assumption.

### Cited Findings
- **Liu & Wilson 2013:** about one-third of antennal-lobe local neurons are glutamatergic. Iontophoresed glutamate hyperpolarizes all major AL cell types. The effect is blocked by picrotoxin or by knocking down GluClα. Knocking down GluClα in projection neurons disinhibits their odor responses. — [Liu & Wilson 2013, PNAS 110:10294–10299 (PubMed 23729809)](https://pubmed.ncbi.nlm.nih.gov/23729809/); [PMC3690841](https://pmc.ncbi.nlm.nih.gov/articles/PMC3690841)
- **Shiu et al.:** "Although glutamate can be either excitatory or inhibitory in Drosophila, by default we assume that glutamate is inhibitory". They add that it "is not feasible to predict whether a particular glutamatergic connection is excitatory or inhibitory at a brainwide scale". — [Shiu et al. 2024 Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/)
- **Lappalainen et al.:** histaminergic, GABAergic and glutamatergic outputs are hyperpolarizing; cholinergic outputs are depolarizing. A few connections were changed based on receptor-expression data (e.g. R8 photoreceptor outputs). — [Lappalainen et al. 2024 Methods (PMC11525180)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11525180/)

### Inferences
- For a fly-brain-derived network, set ACh = +1 and GABA = Glu = −1. Treat DA, 5-HT and OA as +1, which is Shiu's default but biologically weak. Histamine is −1 (it matters only if you include photoreceptors). Keep a flag to flip Glu to +1 as an ablation, as Shiu did.

### Gaps
- I did not fetch a primary citation for glutamate being excitatory at the NMJ or in specific central synapses.

## 3. Log-scaled weights ln(1 + N_syn): any precedent? Pros and cons vs linear

### Takeaway
I found no connectome-constrained Drosophila simulation that uses ln(1 + N_syn). The main models (Shiu 2024, Lappalainen 2024, the Loihi port, Tschopp 2018) all use weights linear in synapse count, with a global or per-cell-type scale factor. FlyWire weight distributions are heavy-tailed or lognormal, which is the usual motivation for compressing them. But measured physiological strength in the lateral horn rises roughly linearly with synapse number, which argues for keeping linear weights.

### Cited Findings
- **Shiu:** linear, w = sign × N_syn × 0.275 mV. — [Shiu et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/)
- **Lappalainen:** linear, per cell-type pair (see Q4). — [PMC11525180](https://pmc.ncbi.nlm.nih.gov/articles/PMC11525180/)
- **Tschopp et al. 2018 hexagonal-lattice CNN:** weight initialized as synapse count divided by a normalization factor of 75 (linear). — [arXiv:1806.04793](https://arxiv.org/pdf/1806.04793)
- **Loihi 2 port:** linear integer counts × 0.275 mV, capped to 9-bit [−256, 255]; capping affected about 0.007% of weights. — [arXiv:2508.16792](https://arxiv.org/html/2508.16792v1)
- **Weight distributions:** hemibrain weights fit a lognormal (μ = 4.75, σ = 0.79 in that preprint's units). — [arXiv:2407.17220](https://arxiv.org/html/2407.17220v1). A 2026 bioRxiv whole-brain fit on FlyWire v783 reports that its fitted model reproduces lognormal synaptic weights. — [bioRxiv 2026.08.21.745055](https://www.biorxiv.org/content/10.64898/2026.08.21.745055v1.full). I saw these only as search snippets.
- **Physiology vs. synapse count:** a hemibrain lateral-horn study reports that measured connection strength scales roughly linearly with synapse number or density. I saw this only as a search-result summary, not the full text. — [PMC8825683](https://pmc.ncbi.nlm.nih.gov/articles/PMC8825683)
- **Alternative normalization:** fraction of a neuron's total input (input-normalized weights), used in the FlyWire cell-typing paper. Seen as a search snippet. — [Schlegel et al. 2024, Nature](https://www.nature.com/articles/s41586-024-07686-5)

### Inferences
- **Pros of ln(1 + N):**
  - It compresses the range (counts span about −2400 to +1900), so a few huge edges cannot dominate.
  - A single global scale works across a small extracted subnetwork, and the network is less prone to runaway excitation.
  - It is gentler for fixed-point or quantized hardware.
- **Cons of ln(1 + N):**
  - It breaks the "5 synapses = half of 10 synapses" assumption, which has partial physiological support and is used by every validated model.
  - It flattens the strong/weak distinctions that carry the circuit logic. Shiu showed that shuffling weights destroys the MN9 prediction (1/100 shuffled runs vs 100% for the real connectome).
  - Published W_syn values can no longer be compared with your model.
  - It is a free modelling choice, so it must be justified and ablated against linear.
- **Recommendation:** keep linear W = sign·N·w_syn as the baseline that reproduces Shiu. If compression is needed, add it as a flagged option (log1p, or per-postsynaptic input normalization) and report both.

### Gaps
- My searches found no paper with log1p weights on a fly connectome. It may exist in unindexed theses or ML papers (e.g. graph-RL controllers like arXiv:2602.17997, whose weight transform I could not see from the abstract).

## 4. Lappalainen et al. 2024 (Nature): how synapse counts became weights

### Takeaway
The model is a non-spiking, threshold-linear rate network. Each weight is w_ij = α_(ti,tj) × σ_(ti,tj) × N_(ti,tj,Δu,Δv):
- N is the EM synapse count (fixed).
- σ ∈ {−1, +1} is the sign from transmitter and receptor data (fixed).
- α ≥ 0 is a trainable unitary-synapse strength, one per cell-type pair (604 of them).

Weights are therefore linear in count within a cell-type pair, with a learned scale for each pair.

### Cited Findings
- **Synapse equation:** s_ij = α σ N f(V_j), where f is threshold-linear (ReLU) graded release. Neuron dynamics: τ_ti dV_i/dt = −V_i + Σ_j s_ij + V_rest_ti + e_i. — [Lappalainen et al. 2024, Nature 634:1132–1140, Methods (PMC11525180)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11525180/), DOI [10.1038/s41586-024-07939-3](https://doi.org/10.1038/s41586-024-07939-3)
- **Initialization:**
  - α = 0.01 / ⟨N⟩, where ⟨N⟩ is the mean synapse count of that filter. α is clamped to stay non-negative.
  - V_rest ~ N(0.5, 0.05) (arbitrary units).
  - τ = 50 ms at initialization, clamped so τ ≥ Δt.
  - Integration step is 20 ms; a smaller step gave no improvement.
  - — [PMC11525180](https://pmc.ncbi.nlm.nih.gov/articles/PMC11525180/)
- **Size:**
  - 45,669 neurons, 1,513,231 connections, 64 cell types, hexagonal lattice 31 columns across.
  - Free parameters: 734 (65 V_rest + 65 τ + 604 α).
  - Fixed from the connectome: 604 signs and 2,355 synapse counts.
  - Example: 5 Mi1→T4 synapses are exactly half as strong as 10 Mi1→T4 synapses.
  - — [PMC11525180](https://pmc.ncbi.nlm.nih.gov/articles/PMC11525180/)

### Inferences
- **A cheap middle ground for a small ALIF network:** keep N and the signs fixed and learn one gain per (pre-type, post-type) pair. Lappalainen showed that signs plus connectivity carry most of the predictive power when unitary strengths are fitted to a task.

### Gaps
- None for weights. I did not extract the per-cell-type τ values after training.

## 5. Adaptive LIF (spike-frequency adaptation) parameters for insect neurons; Drosophila-specific adaptation models

### Takeaway
None of the whole-brain fly models (Shiu, Eon, the Loihi port) includes adaptation. The best-documented insect ALIF parameter set is from Betkiewicz, Lindner & Nawrot 2020 (eNeuro), a Drosophila-scaled olfactory network: adaptation time constant τ_A = 389 ms and spike-triggered current ΔI_A = 0.132 nA. With g_L = 28.95 nS, that equals a jump of about 4.56 mV per spike on a 10 ms membrane, with threshold 13 mV above rest.

### Cited Findings
- **Betkiewicz et al. 2020, Table 2.** The same parameters apply to PNs, LNs and KCs; adaptation follows Treves 1993.
  - c_m = 289.5 pF; g_L = 28.95 nS.
  - E_L = −70 mV; V_reset = −70 mV; V_T = −57 mV; τ_ref = 5 ms.
  - E_E = 0 mV, τ_E = 2 ms; E_I = −75 mV, τ_I = 10 ms.
  - w0 = 1 nS; w_PK = 5 nS.
  - **ΔI_A = 0.132 nA; τ_A = 389 ms**; adaptation-current variance σ_I² = 87.1 pA².
  - ORN background 20 Hz Poisson; odor evoked up to +40 Hz.
  - — [Betkiewicz, Lindner & Nawrot 2020, eNeuro 7(2) ENEURO.0305-18.2020 (PMC7294456)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7294456/)
- **Role of SFA in that model:** it produces temporally sparse KC responses and phasic PN responses. Odor identity is held in neurons' adaptation (calcium) levels. — [PMC7294456](https://pmc.ncbi.nlm.nih.gov/articles/PMC7294456/)
- **Related models:**
  - Farkhooi, Muller & Nawrot (CNS 2009 / arXiv:1007.2345) use a conductance-based IF with SFA (from Muller et al. 2007) for PN→KC sparsening. No parameters on the abstract page. — [arXiv:1007.2345](https://arxiv.org/abs/1007.2345)
  - Lee, Kostal, Kanzaki & Kobayashi 2023 (BioSystems) show that SFA reproduces the phasic Drosophila PN response and encodes the rate of change of input. I did not get their parameters. — [Kostal lab page](https://www.biomed.cas.cz/~kostal/publication/2023-biosystems-ryota-sfa-orn)
- **No adaptation in the whole-brain models:** the Shiu model has none (equations above). Eon's 2026 embodied model lists "no internal state, plasticity" among its limitations and reports no change to the LIF. — [Eon Systems, 10 Mar 2026](https://eon.systems/updates/embodied-brain-emulation)

### Inferences
- **Adding adaptation to the Shiu port at dt = 1 ms.** Use an adaptation variable a in mV units:
  - Membrane: `v += dt/τ_m * (V_rest − v + g − a)`.
  - Decay: `a *= exp(−dt/τ_a)`.
  - On a spike: `a += Δa`.
  - From Betkiewicz: τ_a = 389 ms. Δa ≈ 4.6 mV on a 13 mV rest-to-threshold gap is about 35% of the gap.
  - Scaled to Shiu's 7 mV gap, Δa ≈ 2–2.5 mV. Start there with τ_a ≈ 200–400 ms, then tune so a 150 Hz-driven neuron adapts to roughly half its onset rate.
  - These are my derived starting values, not published fly-brain values.
- **Alternative: threshold adaptation** (Bellec-style ALIF): V_th,eff = V_th + β·a. It is equivalent for the steady-state rate and keeps v untouched.
- **Keep sensory-input neurons non-adapting** (or adapt them separately). Shiu drives them with forced spikes, and adapting them would change the meaning of the stimulus rate.

### Gaps
- I found no Drosophila whole-brain or connectome-constrained model with fitted adaptation parameters.
- I did not read Pospisil et al. 2024 (Nature, "effectome") in this session. My understanding, unverified, is that it uses linear dynamics, not ALIF.
- Bellec et al. 2018 ALIF constants (τ_a, β) are not sourced here.
- I did not open the Lee et al. 2023 PN-SFA parameters.

## 6. Prior work closing the loop between a fly connectome model and a body or robot (2024–2026)

### Takeaway
The most direct precedent is Eon Systems (March 2026). It ran the Shiu LIF on FlyWire inside NeuroMechFly v2 (MuJoCo), syncing brain and body every 15 ms. Descending neurons were read out through a hand-tuned mapping into pre-trained locomotion controllers. NeuroMechFly v2 itself closed the loop with a Lappalainen-style connectome-constrained visual network for fly following. flybody (Vaxenburg 2025) is a MuJoCo body controlled by RL or imitation-trained ANNs, not by a connectome. Several 2026 arXiv papers use connectome graphs as RL controllers for fly bodies or robots.

### Cited Findings
- **Eon Systems (10 Mar 2026):**
  - Brain: Shiu LIF on FlyWire (~140k neurons, ~50M synapses), signs from Eckstein et al. 2024, no reported LIF changes. A Lappalainen visual model feeds vision.
  - Body: NeuroMechFly v2 (MuJoCo, 87 joints), not flybody.
  - Readout neurons: DNa01/DNa02 → steering, oDN1 → forward velocity, MN9 → feeding, antennal DNs → grooming. These drive imitation-trained controllers.
  - Coupling: brain and body sync every 15 ms. The mappings and scalings are hand-tuned.
  - Eon's own words: vision is "decorative"; the VNC is not modeled; escape is not implemented in the body.
  - — [Eon: How the Eon Team Produced a Virtual Embodied Fly](https://eon.systems/updates/embodied-brain-emulation); [Eon: We've Uploaded a Fruit Fly](https://eon.systems/updates/weve-uploaded-a-fruit-fly)
  - Critique: the brain mostly selects among predetermined behaviors. — [Columbia Science Review](https://www.thecolumbiasciencereview.com/online-articles/scientists-just-downloaded-a-fly-brain-into-a-computer-or-did-they)
- **NeuroMechFly v2 (Wang-Chen et al., Nature Methods 2024):** adds vision, olfaction, ascending feedback and complex terrain. Demonstrates closed-loop fly following with a connectome-constrained visual network, plus RL multimodal navigation. — DOI [10.1038/s41592-024-02497-y](https://doi.org/10.1038/s41592-024-02497-y); [EPFL postprint](https://epfl.ch/labs/ramdya-lab/wp-content/uploads/2024/08/NMF2_postprint.pdf)
- **flybody (Vaxenburg et al. 2025, Nature):**
  - MuJoCo, 102 DoF; integration step about 0.1 ms (wingbeat about 200 Hz).
  - Controllers are imitation/RL-trained ANNs, steered by 6-DoF "descending" commands.
  - The connectome appears only as future work.
  - Code: [github.com/TuragaLab/flybody](https://github.com/TuragaLab/flybody).
  - — [Vaxenburg et al. 2025 (PMC12310536)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12310536/), DOI [10.1038/s41586-025-09029-4](https://doi.org/10.1038/s41586-025-09029-4)
- **Jin, Zhu, Zhang & Sui (arXiv:2602.17997, Feb–Jun 2026):** the whole-brain connectome as a graph-structured controller for a simulated biomechanical fly, trained with deep RL. They claim better sample efficiency than baselines. Details beyond the abstract were not read. — [arXiv:2602.17997](https://arxiv.org/abs/2602.17997)
- **Guan et al. (arXiv:2609.27001, Sep 2026):** a "fly-inspired recurrent controller" with 3,609 neural states drives a simulated Unitree G1 humanoid through a motor-neuron-labelled readout. The connectome usage is not described in the abstract. — [arXiv:2609.27001](https://arxiv.org/abs/2609.27001)
- **Also seen:** FlyCNS (arXiv:2609.28816), connectome-grounded embodied control (title only). — [arXiv:2609.28816](https://arxiv.org/pdf/2609.28816)

### Inferences
- **Eon's architecture is the template closest to SO-101:**
  - A small set of named readout neurons.
  - Hand-designed rate → command mapping.
  - A conventional low-level controller.
  - Brain/body sync on a 10–20 ms tick. At dt = 1 ms, that is 15 brain steps per control tick.
- **Readout rates are noisy.** Expect to low-pass them with a window of about 50–100 ms, since Shiu reports rates averaged over 30 × 1 s trials.

### Gaps
- No physical-robot closed loop with a fly connectome LIF was confirmed. The 2026 arXiv items are simulation-only by their abstracts, and I did not read their methods.
- I found no public GitHub repo for Eon's embodied fly.
