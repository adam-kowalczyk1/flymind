# Phase 2 literature matrix (Workstream A): causal perturbation, drift, ablation, steering, comparators

Tags: **[D]** primary evidence; **[M]** model only; **[H]** hypothesis; **[U]** unsupported / not found.
"DOI Y" = resolved this session (Europe PMC or Crossref) with title, first author and year matching. "Read" = what I actually read: FT = full text (Europe PMC XML or PDF), PF = partial full text, AB = abstract or search summary only. Numbers come from FT/PF unless marked AB.

## (a) Matrix

| Source (year, venue) | DOI | Read | Method | Finding (numbers) | Relevance | Limitation |
|---|---|---|---|---|---|---|
| Kim, Rouault, Druckmann, Jayaraman 2017, *Science* 356:849 | 10.1126/science.aal4835 Y | FT | 2P imaging plus CsChrimson in EPG, flying flies. Single spot, 8 EB positions, 80 mW instantaneous, **1.047 s** on, bar removed, no other cue. Behaviour variant: bar kept, **2.5 s** on. | New bump grows while the old one declines and vanishes. After light-off the bump amplitude settles at natural level and "stayed in the induced location for several seconds" or slowly drifted (3 s analysed in 0.5 s bins; CsChrimson off-kinetics hold it ~0.5 s). Visual shifts: small shifts "flow", large ones "jump". Jump threshold power did not differ for 90 vs 180 deg shifts (P=0.102). Behaviour: 47 stim vs 98 control trials, 10 flies; turning higher at 1-2.5 s (P=0.00018); turning variance rose with bump shift. In flight in darkness the bump persisted but "seldom tracked" turns. | Causal overwrite test; local-excitation ring attractor | Persistence is seconds, not minutes. Behaviour effect is a stripe-fixation perturbation, not goal steering. |
| Seelig & Jayaraman 2015, *Nature* 521:186 | 10.1038/nature14446 Y | PF | EB imaging, walking in darkness | Standing in dark: PVA before stop vs restart slope 0.96+-0.17 (499 bouts, 11 flies); bout 6.7+-5.1 s, dPVA 0.017+-0.76 rad; persisted >30 s. Walking in dark: PVA/ball-rotation gain 0.47+-1.2 (397 bouts), r=0.60+-0.42. Low velocities poorly tracked. | Source of the fly drift and gain numbers | Gain is relative to ball rotation, which is not true body rotation. Tethered. |
| Green et al. 2017, *Nature* 546:101 | 10.1038/nature22343 Y | PF | P2X2/ATP and shibire-ts on PEN | Pressure pulses of 5-20 psi, 20 ms, in darkness. Ball-to-phase gains fitted per trace: EPG 0.75, PEN1 1.0 (hand-picked), PEN2 1.40 and 0.89. Lag ~300 ms. shibire-ts at 32 C: dark tracking fails, closed-loop bar tracking not consistently impaired; 34 C: signal dim or blurred. No numeric drift rate. | PEN is the rotation updater | Gains are curve-fits to single examples. |
| Turner-Evans et al. 2017, *eLife* 6:e23496 | 10.7554/eLife.23496 Y | PF | PEN ephys, imaging, shibire-ts | PEN bandwidth 145+-82 deg/s; response lag 130+-73 ms. PEN shibire: bump weaker and more variable. | Velocity input range and lag | Block incomplete (authors' words). |
| Turner-Evans et al. 2020, *Neuron* 108:145 | 10.1016/j.neuron.2020.08.006 Y | PF (first ~40%) | shibire-ts on EPG, Delta7; Kir2.1 on PEN2 | EPG block: bump gone. Delta7 block: bump less visible and erratic, width unchanged, bar tracking less consistent. PEN2 Kir: **dark bump nearly abolished, bump returns with a closed-loop stripe**. Authors say EPG-PEN1 loops "may contribute" to persistence (untested). | Ablations dissociating dark persistence from cue drive | Delta7 not the only inhibition source. |
| Green et al. 2019, *Nat Neurosci* 22:1460 | 10.1038/s41593-019-0444-x Y | PF (94%) | Bar jumps; P2X2 stimulation of PEN in complete darkness | Bar jumps +-90/180 deg: turning changed (P=0.002, 0.001); ~350 ms lag. Flies re-set the bar after 30 s darkness (goal kept >=30 s). PEN stimulation moved EPG phase; turning followed (CCW P=3e-3, 11 flies; CW P=2e-2, 15 flies; shifts 45-135 deg); EPG-phase-to-turn lag ~100 ms; ~77% trials had a stable pre-phase. Control: no-Gal4 flies, no consistent turns. EPG shibire impaired fixation. | Strongest evidence that a shifted heading bump changes steering | Needs an internal goal; the fly's own held heading. Magnitude gain not given. |
| Rayshubskiy et al. 2025, *eLife* 14:e102230 | 10.7554/eLife.102230 Y | FT | DNa02 patch plus EPG imaging; P2X2 on PEN1 | 87+-10 stimulations per fly (every 15-25 s). Compensatory turn goes the shortest way; returns bump to start in 40% of trials. 18 CW vs 35 CCW jumps give different turn velocities (P<0.05, 4 flies). DNa02 bursts before the turn (R2=0.51, example). Controls lacking PEN1-Gal4: 35% returns. Only DNa02, not DNa01, gets direct PFL3 input. DNa02 silencing: small effect. | Closes bump to DNa02 to turn | PFL3 is "likely origin" (inferred). 4 flies. Darkness is stated in the reviewer reply. |
| Westeinde et al. 2024, *Nature* 626:819 | 10.1038/s41586-024-07039-2 Y | PF | Imaging, ephys, ATP stimulation | Cue jumps of 90/180 deg every 60 s; flies turn back to goal. PFL2 stimulation: turning (direction unpredictable) and backward steps. Loops shifted ~120 deg between PFL types. | Steering form (resolver) | PFL3-specific activation not seen in text read. Goal is internal. |
| Mussells Pires et al. 2024, *Nature* 626:808 | 10.1038/s41586-023-07006-3 Y | PF | FC2 and PFL3 CsChrimson; TNT/shibire | FC2 repositioning: headings differ by 166 deg (predicted ~180). PFL3 LAL stimulation (2 s): ipsilateral turns; no turn in 8% of trials. Controls: no-CsChrimson flies; PFL1 gave no turn. Partial PFL3 silencing (10+-1.6 of 24 cells): 0.55-1.33 fewer goal directions. Wind-memory task: after airflow off (test window starts 5 s later, lasts 30 s) and 180 deg bar jump, controls return to the old heading; **EPG>shibire flies do not**. | Causal PFL3; memory without the cue | Weak behavioural effect. |
| Yang et al. 2024, *Cell* 187:6290 | 10.1016/j.cell.2024.08.033 Y | PF | DN imaging | R-L difference of DNa01/02, DNb05/06, DNg13 linearly correlates with rotational velocity. | Linear L-R readout is a fair simplification | Correlation, not gain. No PFL3 test. |
| Giraldo et al. 2018, *Curr Biol* 28:2845 | 10.1016/j.cub.2018.07.002 Y | PF | Kir2.1 in EPG (3 lines), sun menotaxis | Silenced flies lose menotaxis, show frontal phototaxis; stripe fixation unchanged (P=0.101). Controls: Kir2.1 x empty split-GAL4. Memory holds 5 min to 2 h (untested in silenced flies). EPG tracks sun. Bump perturbation not done. | EPG necessity for held headings | No bump shift. |
| Lyu, Abbott, Maimon 2022, *Nature* 601:92 | 10.1038/s41586-021-04067-0 Y | PF | EPG shibire; Kir2.1/GtACR1/CsChrimson on PFN, LNO1, SpsP | Without EPG output the PFR bump no longer tracks the bar. Manipulations offset PFR relative to EPG by ~180 deg. Controls: driver-only, effector-only, 25 C. | Heading bump feeds downstream signals | EPG bump was not relocated; no steering readout. |
| Vafidis et al. 2022, *eLife* 11:e69841 | 10.7554/eLife.69841 Y | PF | Learned rate-based ring attractor (60 HD units) | Gain ~1 path integration in darkness for |w|<500 deg/s. D (variance/time) = **24.5 deg^2/s**; with perturbed weights 82.3+-15.7. Also: bump "can stay put only for several seconds" (citing Kim 2017). | Reference attractor drift [M] | Rate model, not spiking. |
| Noorman et al. 2024, *Nat Neurosci* 27:2207 (preprint title: "Accurate angular integration with only a handful of neurons") | 10.1038/s41593-024-01766-5 Y | PF (first 100k chars) | Theory plus fly imaging, n=10 | Optimal ring needs as few as 4 neurons. Tuning tolerance and noise robustness (1/2D) grow linearly with N. Small nets trade robustness for precision. Fly standing drift is not different from zero (Watson U2 P 0.12-1.0; 5 x 20 min per fly), lower than the model predicted. | What attractor size buys | Darkness not confirmed in text read. |
| Kutschireiter et al. 2023, *PNAS* 120 | 10.1073/pnas.2210622120 Y | PF | Theory: circular Kalman filter | Conventional ring attractors do not represent uncertainty; the circular Kalman filter is the benchmark; cues combine by vector addition. | The right comparator | Theory. |
| Khona & Fiete 2022, *Nat Rev Neurosci* 23:744 | 10.1038/s41583-022-00642-0 Y | AB | Review | Attractors give persistence, error correction, noisy cue integration. | Advantage list [H] | Not read in full. |
| Skaggs et al. 1995 (NIPS 7:173); Zhang 1996 (*J Neurosci* 16:2112, 10.1523/JNEUROSCI.16-06-02112.1996 Y); Burak & Fiete 2012 (*PNAS*, 10.1073/pnas.1117386109 Y) | Skaggs: none, **N** | not read | Theory | Origins of the shifted-loop HD ring and noise limits on persistence (my background knowledge, titles only verified). | Theory lineage | Skaggs citation unverified; Crossref search returned a different paper. |

## (b) Answers

**1. Causal perturbation of the heading bump.**
- Kim 2017: 1.047 s two-photon CsChrimson pulse at one of 8 positions with the bar removed. The new bump grew while the old one decayed (a relocation, not a smooth sweep). It then stayed for "several seconds" or drifted slowly. [D]
- The jump vs flow split is for visual shifts: small shifts flow, large shifts jump. Optogenetic jump threshold was distance-independent (P=0.102). [D]
- Behaviour with the bar in closed loop (2.5 s pulse): more turning (P=0.00018) with larger variance for larger shifts; no tidy identity relation. [D]
- Steering following a shifted bump is shown by Green 2019 (P2X2 on PEN, darkness, lag ~100 ms) and Rayshubskiy 2025 (shortest-path compensatory turn, 40% full returns, DNa02 burst). [D] Both rely on the fly holding its own goal. Westeinde 2024 shows the same effect with visual cue jumps. [D]
- Sham/control: no-CsChrimson flies with the same laser (Kim, Mussells Pires); no-Gal4 flies with the same ATP puff (Green, Rayshubskiy); a cell-type control, PFL1 (Mussells Pires); Kir2.1 x empty split-GAL4 (Giraldo). No study used a "right place, wrong time" or reversed-sign sham. [U]
- Giraldo 2018 and Lyu 2022 show EPG necessity, not a relocation-to-steering test. [D]

**2. Drift and integration gain in darkness.**
- Persistence: >30 s standing in darkness (Seelig). Optogenetic bump: seconds before drifting (Kim; Vafidis cites this). [D]
- Standing-bout error SD is 0.76 rad (43.5 deg) at mean bout 6.7 s [D, Seelig]. If diffusive (var = D t) this gives D ~ 280 deg^2/s, or ~17 deg at 1 s. **This is my derivation**: it ignores the spread of bout lengths and imaging noise, so it is a rough upper bound. The model's 14 deg at 1 s is the same order. [derived]
- Noorman: flies' standing drift is statistically zero over the test window. The two fly sources disagree, so quote the range, not a point value. [D]
- Gain: Seelig 0.47+-1.2 in the dark (ball rotation), Green 0.75-1.40 (per-trace fits). Gain varies by fly. A model gain of 1.32 sits inside the fitted range but is calibrated, not emergent. [D, M]
- Model reference: Vafidis D = 24.5 (ideal) to 82 deg^2/s, giving 1-s SD of 4.9-9.1 deg. [M]

**3. Silencing and ablation.**
- PEN: shibire-ts removes dark tracking while closed-loop bar tracking is not consistently impaired (Green 2017). PEN2 Kir removes the dark bump while a stripe restores it (Turner-Evans 2020). This is the best "removes persistence, spares cue-driven bump" lesion. [D]
- EPG output block: phase unstable in both bar and dark; phase velocity still follows the bar "reasonably" (Green 2019). Not a clean dissociation. [D]
- Delta7 block: bump dim and erratic, width unchanged, bar tracking worse. It degrades both cue and dark behaviour. [D] No Delta7 test of standing persistence found. [U]
- Standing-in-dark persistence under silencing was not measured directly. [U]

**4. PFL3 to DNa02 to steering.**
- Sufficiency: PFL3 LAL stimulation gives ipsilateral turns (8% failures); PFL1 does not. [D]
- Necessity: partial PFL3 silencing costs 0.55-1.33 goal directions (weak); DNa02 silencing had small effects. A strict necessity claim for PFL3 to DNa02 is not made. [U]
- Anatomy: only DNa02 gets direct PFL3 input; PFL3 is "likely origin" of the DNa02 error burst (Rayshubskiy). [D anatomy, H causal chain]
- Steering follows the bump in darkness with a ~100 ms lag (Green 2019) and DNa02 burst precedes the turn (Rayshubskiy). [D] Wind-memory task: EPG block abolishes steering to a remembered direction (Mussells Pires). [D]
- No evidence that steering follows a remembered egocentric target bearing. Flies' goal is an internal vector, not a cue-derived bearing. [U]
- Kim 2017: in tethered flight the bump in darkness seldom followed turns. Persistence and tracking can dissociate. [D]

**5. "Matched non-neural comparator".**
- Meaning: a model given the same inputs, calibration, output decoder, noise statistics and delays, with the recurrent bump replaced by a scalar state. [H]
- Natural set: (i) ZOH; (ii) scalar integrator with matched velocity gain and injected noise (diffusion D); (iii) circular Kalman filter for noisy cues (Kutschireiter). [H]
- Fair attractor advantages: error correction of off-manifold perturbations (neuron dropout, spike noise, a transient distractor); vector fusion of cues; graceful degradation; winner-take-all selection among cues (Kim 2017). [H, supported by Khona & Fiete AB, Kutschireiter]
- Unfair expectations: beating a noiseless integrator in a noiseless sim; zero drift (finite-N noise causes diffusion; small nets are less robust, Noorman); extrapolating target motion; beating a Kalman filter that has a velocity model; using a lookup `u_for` that makes the network an engineered integrator and then claiming emergent accuracy. [H]
- Match noise at the equivalent point, or either side wins by construction. [H]

**6. Claims that stay model-level.**
- Any statement that the bump encodes an egocentric target bearing. [U in flies]
- That PFL3 with goal=0 implements target pursuit. Goal is an FC2 vector. [M]
- The numerical gain, noise and drift (calibrated lookup, Delta7 x8). [M]
- The DNa01 copy and the x2.5 L-R decode. [M]
- Occlusion memory as a result about flies. Only Mussells Pires' wind-memory task and Green's 30 s darkness are analogues, and both are goal-directed heading tasks. [H]

## (c) Literature-derived reference values (provisional; none is a requirement for the robot model)

| Quantity | Value | Source | Caveat |
|---|---|---|---|
| Dark persistence, standing | >30 s | Seelig 2015 | Tethered, imaging; not a task |
| Standing bout error | SD 0.76 rad at mean 6.7 s | Seelig 2015 | Includes imaging noise |
| Implied 1-s error (derived) | ~17 deg (D ~280 deg^2/s) | My calculation from Seelig | Assumes diffusion; rough upper bound |
| Model-attractor diffusion | 24.5-82 deg^2/s (SD 4.9-9.1 deg at 1 s) | Vafidis 2022 | Rate model, not flies |
| Dark gain (PVA / ball rotation) | 0.47+-1.2 | Seelig 2015 | Ball rotation not body rotation |
| Fitted phase gains | 0.75 to 1.40 | Green 2017 | Hand-fitted per trace |
| Optogenetic bump hold | several seconds, 1.047 s stimulus | Kim 2017 | Drifts away |
| Bump to turn lag | ~100 ms (Green); 150 ms neural-to-behaviour (Rayshubskiy); ~350 ms heading-minus-goal to turn (Green) | Green 2019; Rayshubskiy 2025 | Treadmill inertia included |
| Full return after bump shift | 40% of trials (35% in no-PEN1-Gal4 controls) | Rayshubskiy 2025 | 4 flies; 40 vs 35% is a small contrast |
| Goal memory in darkness | >=30 s | Green 2019 | Lower bound; longer not tested |

**Phase-1 corrections:** Kim 2017 persistence is "several seconds" for the optogenetic bump (Seelig gives >30 s for standing in darkness). Kim 2017 flight bump seldom tracked turns in darkness. Noorman's published title differs from the preprint title.

---
_PI verification (2026-10-27): all 18 DOIs in this file resolve via api.crossref.org to matching titles/first authors (verify/doi_check_phase2.txt). Quantitative values were extracted by the agent from full/partial texts via Europe PMC and the Kim 2017 PDF; the PI did not re-read the papers. Seelig 2015 "~17 deg at 1 s" is the agent's derivation, not a reported number._
