# Biology and robot vision (question 11): numbers and products, as of 2026-11-12

Scope note: this UPDATES /Users/admin/so101_fly_project/flymind/reports/bio_vision_20261112.md (which already covers Gallego 2019, Gehrig&Scaramuzza Nature 2024 [20 fps RGB + events = latency of 5000 fps camera at 45 fps bandwidth], Paredes-Vallés Science Robotics 2024, Maisak 2013, Klapoetke 2017, Wu 2016, Yue&Rind 2006, MaleCNS counts). Only NEW material is below. Labels: VERIFIED = I read the source text/listing in search output; REPORTED = vendor/press/secondary summary or abstract only; INFERRED = my reasoning; PROPOSED = idea. Nearly everything below is REPORTED (search-engine summaries of pages; no full-paper read), so treat numbers as "to verify before the poster". Publisher PDFs were not opened.

## 1. Event/neuromorphic cameras: latency, power, market, robot results

### Takeaway
Event sensors are real products with vendor-quoted latency of ~100-150 microseconds and tens of mW (GenX320 sub-50 mW, 320x320; IMX636 1280x720, 50-205 mW depending on document). The market is small (industrial segment ~USD 0.2-0.3B in 2025) and analyst numbers disagree by 3x. Best robot result remains the TU Delft neuromorphic drone (200 Hz, +7-12 mW network). All REPORTED.

### Cited Findings
- GenX320: 320x320 array, 6.3 um pixels, >140 dB dynamic range; latency <150 us at 1000 lux and <1000 us at 5 lux; <50 mW sensor-only; "down to 36 uW" only in an ultra-low-power mode (vendor, REPORTED) — [Prophesee GENX320 product brief 2025](https://prophesee.ai/wp-content/uploads/2025/01/GENX320-Product-Brief-2025-DICE-OK.pdf); [CNX Software, Pi 5 starter kit, 2025-08-27](https://www.cnx-software.com/2025/08/27/prophesee-starter-kit-genx320-camera-for-raspberry-pi-5-enables-low-latency-event-detection/). A different Prophesee sheet quotes 120 us pixel latency (same source family; conflict is between documents, not resolved).
- GenX320 has a Raspberry Pi 5 starter kit (2025) — [Prophesee kit page](https://www.prophesee.ai/event-based-starter-kit-genx320-raspberry-pi-5/). Relevant for FlyMind: a cheap physical event camera exists. (Which camera Adam actually owns: NOT VERIFIED; project memory says only FaceTime camera is evidenced.)
- IMX636 (Sony+Prophesee): 1280x720 (~0.92 MP), 4.86 um pixels, latency <100 us at 1000 lux and <1000 us at 5 lux; dynamic range >120 dB (80 mlux-100 klux). Power CONFLICTS: 150 mW max (AAMR-C brief June 2024), 205 mW max / 5 mW standby (Sept 2024), 50-70 mW typical / <100 mW peak (Prophesee docs) — [IMX636 brief](https://prophesee.ai/wp-content/uploads/2024/05/IMX636-Product-Brief-2024-v3.0.pdf); [Prophesee docs](https://docs.prophesee.ai/stable/hw/sensors/imx636.html).
- Market: SNS Insider USD 2.53B (2024) -> 6.19B by 2032 (CAGR 11.86%) for "event camera"; Fortune Business Insights USD 8.04B (2025) -> 24.98B (2034); Mordor (event-based industrial vision systems) USD 0.27B (2025) -> 1.14B (2031); Spherical Insights USD 0.18B (2025). Vendor-report estimates with different definitions — [GlobeNewswire/SNS Insider 2025-11-07](https://www.globenewswire.com/news-release/2025/11/07/3183362/0/en/Event-Camera-Market-Size-to-Surpass-USD-6.19-Billion-by-2032-at-a-CAGR-of-11.86-Research-by-SNS-Insider.html); [Fortune BI](https://fortunebusinessinsights.com/segmentation/event-camera-market-110552); [Mordor](https://www.mordorintelligence.com/industry-reports/event-based-industrial-vision-systems-market); [Spherical Insights](https://www.sphericalinsights.com/blogs/top-15-companies-in-global-event-based-vision-systems-market-statistics-report-till-2035).
- Industry events: CenturyArks launched first commercial MIPI event camera module on IMX636 (Prophesee, Oct 2025); iniVation launched Aeveon sensor (Mar 2025); IDS + Prophesee expanded collaboration (Mar 2026) — same Mordor/Spherical-Insights-derived summary above (secondary; not checked at primary).
- TU Delft fully neuromorphic drone (Paredes-Vallés et al., Science Robotics 9(90), May 2024, doi:10.1126/scirobotics.adi0591): SNN on Intel Loihi, DVS240 camera, ~200 Hz, 0.94 W idle + 7-12 mW for the network; hover, landing, sideways flight with yaw; assumed static, textured, flat surface; 16x16 pixel regions of interest (secondary summaries) — [TU Delft record](https://research.tudelft.nl/en/publications/fully-neuromorphic-vision-and-control-for-autonomous-drone-flight/); [DroneXL 2024-05-16](https://dronexl.co/2024/05/16/neural-tech-insect-sized-flying-robots/); [Crossref](https://api.crossref.org/works/10.1126%2FSCIROBOTICS.ADI0591).

### Inferences
- INFERRED: the "7-12 mW" is the network only; the 0.94 W idle dominates, so "milliwatt drone" claims need the whole-system caveat.
- INFERRED: GenX320's 320x320 resolution is far below the fly's ~890 columns/eye in the data (see bio_vision report), but is in the right order for a retina model. For a poster, say "a camera of this class could feed a retina model", not "fly eye".
- INFERRED: market figures cannot support an investor claim; quote the range and its disagreement, or omit.

### Gaps
- No primary check of the Prophesee 2026 product brief (a July 2026 GENX320 brief URL exists: prophesee.ai/wp-content/uploads/2026/07/GENX320-Product-Brief-2026-CN1.pdf) — not opened.
- Sony IMX636 official Sony datasheet not found; power conflict unresolved.
- Prophesee/iniVation financial status 2025-26 (revenues, funding) not found.

## 2. Insect mechanisms in engineering: Reichardt/T4-T5, LGMD/LPLC2 looming, Opteran, compound eyes

### Takeaway
Insect-inspired collision cues (LGMD, now LPLC2) are demonstrated on micro-robots and small drones with percent-level detection rates in small lab arenas, not on cars at scale. Opteran is the one commercial insect-vision company, but its numbers are vendor claims from 2021-22 and I found no 2025-26 update. Artificial compound eyes (CurvACE 2013) exist but are lab devices.

### Cited Findings
- 2025 review of LGMD in neuro-robotic integration (Qin, Peng, Yue, Fu; arXiv 2501.02982): LGMD models improved collision-free navigation in ground and aerial robots; classic LGMD struggles to separate looming from receding/translating motion (secondary excerpt) — [arXiv 2501.02982](https://arxiv.org/abs/2501.02982v2). Earlier survey: [arXiv 1904.02048](https://ar5iv.arxiv.org/html/1904.02048).
- Fly LPLC2-based "ALVS" on a Colias micro-robot (~4 cm, ARM Cortex-M4F, OV7670 camera, ~70 KB model, 72x99 grayscale at 30 fps): 96.1% collision detection vs 93.7% for an LGMD2 system in arena tests; escape direction correct for threats roughly -35 to +35 degrees, which LGMD2 could not do. arXiv 2509.13827 (Sept 2025). Source is a review-site summary, not the PDF; unclear if spiking — [themoonlight.io review](https://www.themoonlight.io/review/how-fly-neural-perception-mechanisms-enhance-visuomotor-control-of-micro-robots); [arXiv listing mirror](https://fugumt.com/fugumt/paper_check/2509.13827v1_enmode).
- LPLC2 tuning arises in shallow networks trained to detect collisions (Zhou et al., eLife 2022) — [eLife 72067](https://elifesciences.org/articles/72067). Useful claim: loom selectivity is a natural solution to the collision task, not a fly oddity.
- Opteran (Sheffield spin-out, honeybee-based): optic flow at 10 kHz under 1 W on a small FPGA; claimed 2x accuracy vs FlowNet2s (company slide deck); ODK-2 with 2 or 4 MIPI cameras, 150 fps, ~30 g, <1 W; pilots in cobot arms, drones, mining robots — [Edge AI and Vision Alliance](https://www.edge-ai-vision.com/2021/10/opterans-journey-to-complete-natural-intelligence-for-machines/); [Opteran slides 2022](https://www.edge-ai-vision.com/wp-content/uploads/2022/05/E1W06_Marshall_Opteran_2022.pdf); [eeNews Europe](https://www.eenewseurope.com/en/dev-board-for-insect-like-visual-ai). Funding: GBP 2.1M seed (2020), USD 12M (June 2022) — [tech.eu 2022-06-24](https://tech.eu/2022/06/24/opteran-weaves-in-12-million-to-develop-ai-driven-by-brain-biomimicry-inspired-by-insects). Oct 2024: tested in a Mars-rover simulation with Airbus — [TNW 2024-10-23](https://thenextweb.com/news/airbus-space-rover-tests-opteran-insect-brains-natural-intelligence).
- "Fewer than 10,000 pixels is enough for autonomy" (Opteran, 2021) — [Edge AI Vision](https://www.edge-ai-vision.com/2021/03/fewer-than-10000-pixels-is-enough-for-autonomy/). Vendor claim.
- CurvACE (Floreano et al., PNAS 2013, doi:10.1073/pnas.1219068110): curved hemispherical-FOV artificial compound eye, programmable low-power processing, ~150 fps (press). A 2014 Sensors paper: 180x60 degree FOV, 630 ommatidia, 1.75 g. Press says "<1 mm" thick (a "1.5 mm" figure I had in mind was NOT found); page numbers conflict between listings — [EPFL PDF](https://infoscience.epfl.ch/record/186234/files/PNAS-2013-Floreano-9267-72.pdf); [EPFL LIS](https://www.epfl.ch/labs/lis/?p=361); [phys.org](https://phys.org/news/2013-05-insect-sized-artificial-compound-eye-video.html).

### Inferences
- INFERRED: Reichardt/T4-T5 is the engineering baseline for "cheap optic flow"; Opteran's claim, if real, is a commercial version of it. No independent benchmark found.
- INFERRED: I found NO self-driving-car deployment of LGMD/LPLC2; "cars" appear only as research motivation. Do not claim automotive use.
- INFERRED: 2023-2026 artificial compound eyes: my searches returned only 2013-14 CurvACE; recent literature not found.

### Gaps
- No 2025-26 Opteran status (funding, customers, product); search returned only up to Oct 2024.
- Original PDF of arXiv 2509.13827 not read; number 96.1% to verify.
- DelFly optic-flow results not searched; 2023-2026 compound-eye cameras not found.

## 3. Connectome-constrained vision; spiking vision on neuromorphic chips

### Takeaway
Lappalainen 2024 is verified at the abstract level: a model built from the wiring of 64 optic-lobe cell types, with unknown single-neuron/synapse parameters fitted by deep learning to do motion detection, matches neural data across 26 studies. It is a neuroscience result, not a robot-vision result. Spiking vision hardware shows large energy savings but accuracy lags on hard tasks.

### Cited Findings
- Lappalainen et al., Nature 634, 1132-1140 (2024), doi:10.1038/s41586-024-07939-3: 64 cell types, motion pathways; predictions agree with experiments from 26 studies; works better when connectivity is sparse — [MPI-IS record](https://is.mpg.de/publications/lappalainennature24); [Tuebingen AI Center news](https://tuebingen.ai/news/researchers-combine-the-power-of-artificial-intelligence-and-the-wiring-diagram-of-a-brain-to-predict-brain-cell-activity). Press date 2024-09-11 vs issue Oct 2024 (minor conflict).
- Speck (SynSense) in robotics: average ~2.7 mW (baseline CPU subtracted) in visual place recognition, stated as 0.5% of a Jetson Nano and 0.02% of an Intel CPU — [arXiv 2408.16754](https://arxiv.org/pdf/2408.16754v1.pdf). Speck: each event through a 9-layer spiking CNN in ~3.36 us (original Speck paper, secondary summary) — [arXiv 2304.06793](https://arxiv.org/abs/2304.06793). The "0.7 mW" figure I looked for was NOT found.
- Loihi 2 vs GPUs: April 2026 preprint (Gamage et al., arXiv 2605.00146) reports lowest per-inference dynamic energy on Loihi 2 for SNN object detection vs Jetson Orin Nano/Nano and Apple M2, but Jetson Orin Nano reached higher inference rates (abstract-level) — [arXiv 2605.00146](https://arxiv.org/abs/2605.00146).
- Accuracy gap: SNNs match ANNs on small static benchmarks but lag on ImageNet and modern tasks (secondary summary); a non-peer-reviewed Sept 2025 review reports up to ~3x efficiency vs matched ANNs — [theorempath](https://theorempath.com/topics/spiking-neural-networks); [Preprints.org 202509.2072](https://www.preprints.org/manuscript/202509.2072).

### Inferences
- INFERRED: no head-to-head found of a connectome-derived vision network vs CNN/ViT/DINO on robot tasks. The honest statement is "not tested anywhere I could find"; FlyMind would be an early case, not a proven advantage.
- INFERRED: the energy argument applies to neuromorphic hardware; FlyMind runs on a MacBook M1 Max, so it gets none of the energy benefit.

### Gaps
- Lappalainen: no accuracy/latency/energy numbers vs CNN (not designed for that); full text not read.
- No peer-reviewed numeric Loihi 2 vs CNN accuracy-gap source found.
- No verified Speck/Loihi numbers vs DINO specifically.

## 4. Where bio-vision loses, the honest niche, and what FlyMind's fly-eye plan could show

### Takeaway
Bio-vision loses to large models on recognition and semantics (INFERRED, consistent with the secondary sources above) and wins, if anywhere, on fast, cheap, low-power motion/collision cues. For FlyMind the defensible simulation claim is a loom/stop reflex from camera pixels through the real wiring with controls, not a better vision system.

### Cited Findings
- Sources above show wins only in: latency (~100-150 us sensors), power (mW-level chips), small robots (4 cm Colias, 7-12 mW drone network) — see sections 1-3.
- Hybrid beats events-only (Gehrig & Scaramuzza 2024) — already VERIFIED in /Users/admin/so101_fly_project/flymind/reports/bio_vision_20261112.md.
- MaleCNS data: LPLC2->DNp01 4862 synapses, LC4->DNp01 6362; D0 PASS for LPLC2->DNp04 spatial maps — /Users/admin/so101_fly_project/flymind/reports/bio_vision_20261112.md sec. 2 (VERIFIED by file read there) and task context.

### Inferences
- INFERRED: what the fly-eye plan could show in simulation: (a) pixel input -> retina/lamina -> motion core (47,473 neurons) -> LPLC2/LC4 -> DNp01 stop, with gate G2; (b) controls: shuffled wiring, no-image, mirrored, and a classical looming-threshold baseline (tau/optical expansion) which will likely match or beat it on accuracy — the fair claim is "the fly wiring does it too", not "better".
- INFERRED: camera choice. Simulation: rendered MuJoCo frames converted to events by frame differencing (no hardware). Hardware later: GenX320 (320x320, Pi 5 kit, <50 mW) fits a motion core; a normal webcam also works if frames are processed. Event camera adds nothing to a nonmoving scene (noted in bio_vision report).
- INFERRED: honest poster line: "vision input today is a colour heuristic; the fly-eye path is planned and tested in simulation only."
- PROPOSED: compare the same collision-stop task against Colias/ALVS-like 96.1% numbers only as context (different tasks), not as a benchmark.

### Gaps
- No evidence any connectome-derived network has been tested for robot collision avoidance in published work (my search found none; earlier project literature check also none for arms).
- Compute cost of 47k neurons in real time on M1 Max not measured; no data.
- Whether event-camera input to a connectome-derived retina model is biologically faithful is NOT VERIFIED (photoreceptors are analogue; see bio_vision report).
