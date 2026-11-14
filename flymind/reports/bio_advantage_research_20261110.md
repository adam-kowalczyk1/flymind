# FlyMind — can fly-brain biology give a real advantage over VLA/VFA models?

Research report and proposed plan, 2026-11-10 (written 21:30 CET). Author: Claude (Fable 5.2), at the owner's request.
Status of this file: new, uncommitted, the only file created in this session. Nothing was simulated, trained, committed or changed.

Evidence labels used throughout: **VERIFIED** (checked now; command, file or URL given), **PARTIALLY VERIFIED**, **REPORTED**
(copied from a project document or a source I did not open myself), **INFERRED**, **HYPOTHESIS**, **NOT VERIFIED**, **FAILED**,
**NOT IMPLEMENTED**. Literature rows also say how the source was seen: *opened* (page text read) or *snippet* (search summary only).

---

## 0. Streszczenie dla Adama (po polsku, prostym językiem)

**Odpowiedź na pytanie: dziś nie, a w przyszłości tylko w wąskiej niszy.**

1. **Sieć muchy nie wygra z modelami VLA w tym, w czym one są dobre** (rozumienie poleceń, nowe przedmioty, wiele zadań).
   Nie wygra też z prostym klasycznym sterownikiem w dokładności. Wszystkie nasze pomiary to potwierdzają i przeliczyłem je
   dziś od nowa z surowych plików — zgadzają się.
2. **Znalazłem powód, dla którego nasze testy „dane kontra sieć przetasowana” nie mogły wykazać roli połączeń.** Sieć dostaje
   dziś jedną liczbę na wejściu („jak mocno dotyka pad”, „lewo czy prawo”) i oddaje jedną liczbę na wyjściu („jak mocno
   zacisnąć”, „w którą stronę obrócić”). Przy takim podłączeniu każda sieć, która po prostu „przepuszcza sygnał”, działa
   podobnie — także przetasowana. To nie jest dowód, że połączenia muchy są bezwartościowe; to dowód, że nasze zadanie ich nie
   potrzebuje.
3. **W danych jest coś, czego jeszcze nie używamy.** Sprawdziłem dziś w plikach MaleCNS: neurony wzrokowe wykrywające
   zbliżający się obiekt (LC4) są połączone z dwoma neuronami „ucieczki” tak, że *miejsce w polu widzenia* zamienia się na
   *kierunek odskoku*. To wrodzona „mapa: gdzie jest zagrożenie → w którą stronę uciec”, zapisana w liczbie synaps. Zgadza
   się to z publikacją w Nature z 2023 r. Takiej mapy przetasowanie nie zachowa — to pierwszy realny kandydat na test,
   w którym połączenia z danych powinny mieć znaczenie.
4. **Gdzie mucha może uczciwie dać przewagę nad VLA:** jako szybki, tani, niewymagający uczenia „odruch” pod wolnym,
   mądrym sterownikiem (jak rdzeń kręgowy pod mózgiem). Duże modele reagują co 0,1–1 s i nie mają odruchów; odruch muchy
   liczy się w ok. 2 ms na zwykłym procesorze. **Ale uwaga:** tę samą przewagę daje dowolny prosty odruch napisany ręcznie.
   Żeby powiedzieć „to zasługa muchy”, trzeba pokazać, że sieć z danych jest lepsza od przetasowanych. Tego dziś nie mamy.
5. **To się kłóci z jedną z Twoich zasad.** Realna nisza to „mucha jako odruch pod innym sterownikiem”, a nie „mucha steruje
   wszystkim”. Twoja zasada z 3 XI mówi, że ma sterować mucha, nawet kosztem jakości. Te dwie rzeczy da się pogodzić tylko
   częściowo — decyzja należy do Ciebie (pkt 9).

**Jedna decyzja do podjęcia:** czy zgadzasz się na plan z pkt 10 (najpierw analiza samych danych — bez symulacji, potem dwa
małe, z góry zarejestrowane testy w symulacji)? Do czasu Twojej zgody nic nie uruchamiam.

---

## 1. Question, scope and method

**Question.** Can anything in the biology of the fruit-fly nervous system (or another mapped nervous system) give FlyMind a
real, measurable advantage over current vision-language-action / vision-force-action models — where, how, and how would we
prove it?

**What I did (all read-only):**
- re-verified repository state, connectome file hashes and the two "unresolved conflicts";
- recomputed the headline numbers from the raw result files (JSON/JSONL; there are no CSVs for these stages);
- read the interface code between sensors, network and actuators;
- ran read-only queries on the three MaleCNS files (annotation table and edge list) to check whether candidate circuits exist;
- literature search (three research sub-agents with web access only, plus my own spot checks of the key citations).

**What I did not do:** no simulation, no training, no code written to the repository, no commit, no change to any existing
file, no contact with the physical arm. Queries and recomputations were run as inline commands, not saved as scripts.

---

## 2. Repository state — re-verified

### 2.1 Git and the two "conflicts"

| Item | Result | Status |
|---|---|---|
| HEAD | `664b61133f138b79b275840845cdf66d91f75fda`, branch `flymind/fly-first-control`; committed 2026-11-10 09:54 (`git log`) | VERIFIED |
| Working tree | 2 modified tracked files (`flymind/REPRODUCE.md`, `flymind/VALIDATION_PLAN.md`), 140 untracked entries (`git status --porcelain`) | VERIFIED |
| "HEAD 664b611 vs a7344e3" | Not a conflict. `a7344e3` (2026-11-09 21:15) was HEAD when the touch stage was frozen (`results/sensory_manipulation/FREEZE_v1.txt`, 07:52). `664b611` then committed the touch stage; the vision stage froze against `664b611` (`results/vision_manipulation/FREEZE_v3.txt`, 14:08). `FLYMIND_MASTER_CONTEXT.md` is dated 2026-11-07 and names `54155d4` — it is simply stale. | VERIFIED |
| "19 vs 25 tests" | Not a conflict. `test_object_handling.py` 14 + `test_sensory_manipulation.py` 5 = 19 (both tracked in `664b611`); `test_vision_manipulation.py` adds 6 = 25 and is untracked. Counted with `grep -c '^def test_'`; tests were **not** run now. | VERIFIED (count), NOT VERIFIED (pass/fail today) |

### 2.2 Connectome data hashes (`shasum -a 256 data/malecns/*.feather`)

| File | SHA-256 | vs `FREEZE_v1.txt` (sensory_manipulation, vision_manipulation) |
|---|---|---|
| `body-annotations-male-cns-v1.0-minconf-0.5.feather` | `2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2` | identical |
| `body-neurotransmitters-male-cns-v1.0.feather` | `95c9289220663abeb3409f3ad9e5a7f8a53f8093f5139d15502cd08da8879621` | identical |
| `connectome-weights-male-cns-v1.0-minconf-0.5.feather` | `e35da783d1c686b2b58b3b87cd6a403ae43bfcfba8bff28e08ef752c1a56afc1` | identical |

Status: VERIFIED. Note: there are eight files named `FREEZE_v*.txt`; only the two listed include the data files.

### 2.3 Headline numbers recomputed from raw files

Method: success counted from per-trial records (`runs[].objects[].success` or `trials[].success`), not from the stored
summary; Wilson 95 % interval; exact two-sided McNemar on trials paired by object and pose. All paths are under
`flymind/results/`. Caveat that applies to every p-value below: 135 trials are 45 objects × 3 poses, so trials are not
independent — p-values are indicative only.

| Claim in the brief | Recomputed | Raw file → SHA-256 | Status |
|---|---|---|---|
| Stiff contact: classical 101/135, network 84/135 | 101 and 84; paired: only-classical 21, only-network 4, p = 0.001 | `contact_audit/stiff_A_v1.json` → `9eebaef0d1bce613871c409a9abeca562bcf04a8f70af0a331d75846e8484cbf`; `contact_audit/stiff_B_v1.json` → `2fbaf3fa6f298069b40ea81b4d6ba45217eb4ebbaea24fe7961acc5764eccd90` | VERIFIED |
| Soft contact: classical 93, network 90, reflex 80 | 93 (60.6–76.1 %), 90 (58.4–74.1 %), 80 (50.8–67.2 %). Network vs classical 12/15, p = 0.70. **Network vs reflex 14/4, p = 0.031.** | `object_handling/B_base_v2.json` → `4d76d66f0f44e01fb3502b32a78276676353b71d1afbb76f5bd3b28e4180a054`; `sensory_manipulation/B_fly_search_glu-1_v1.json` → `2bb4afeda53a9ce46803413417c0102556c93b44b712dfa667311812798a4ef4`; `sensory_manipulation/D_reflex_search_v1.json` → `ac4e31759e201e4c1f3752759ec2f8ef82b80002efca28e38371c64dab67024b` | VERIFIED |
| 10 strength-matched shuffles: 101, 82, 80, 102, 83, 79, 82, 79, 99, 4 vs 90 | Exactly these. Data network ranks 4th of 11. Median shuffle 82. | `shuffle_matched/shuffle_17100011…20_v1.json` → `b83d1d79…118da`, `379c414c…bfd00`, `0b3fff1d…c1b23`, `9763f8fe…71b2`, `e57b1a64…5790`, `63023bbe…83dc`, `b0130faf…35d0`, `63a16552…fbfd`, `52cc9221…4373`, `ca3c32d6…d172` (full values in §12) | VERIFIED |
| Vision + touch gives no gain (discordant 5/4 and 3/3) | E vs B_cam 5/4 (p = 1.0); E vs E_blind 3/3 (p = 1.0); E 86, B_cam 85, E_blind 86, A_cam 98, F 80, D 0 | `vision_manipulation/{A_cam,B_cam,D_vis,E_vis_touch,E_blind_grasp,F_vis_touch_feco}_v3.json` (hashes in §12) | VERIFIED |
| Pad penetration > 2 mm in 16–23 of 135 | 16 (B, Glu −1), 23 (B, Glu +1), 16 (C), 21/21/21/18 (camera arms B/E/E_blind/F), 3 (classical oracle), 0 (classical camera), 0 (both stiff arms) | same files | VERIFIED |
| Joint speed up to 1.89 rad/s in the vision stage | max 1.890 rad/s in all six v3 arms (51–245 ticks above 1.5); oracle-stage arms max 0.987 | same files | VERIFIED |
| V5: network 38/40, P 40/40 | 38/40 and 40/40 in the stored analysis; median final error 1.41° vs 0.16°. Read from the analysis file, not recounted from trials. | `v5/analysis_confirm.json` → `035c7d7181f5835719210cd60e7f2ea89cbf96053cbfa4ffa4fbaf5f501fdb05` | PARTIALLY VERIFIED |
| V7 (1440 trials): network worse than P in all variants | 1440 rows. Mean final error DATA vs P: G1 12.56° vs 0.52°, G2 2.35° vs 0.25°, G3 1.38° vs 0.24°, G4 2.90° vs 0.98°. P better in 471 of 480 scene pairs (116, 120, 115, 120). So: worse in every block on average, not in every single pair. | `v7/v7.jsonl` → `f4416fd390aad5dce4f278f5be599bf30bd50f0ebb6ee87bbb91be2fe6bfd137` | VERIFIED |
| Network issues ~3 % of base commands and ~9 % of jaw commands (v3 demo series) | Demo series: jaw 702 of 7 937 ticks = **8.8 %** (matches); base 1 270 of 7 937 = **16.0 %** (does not match "3 %"). Share of *all* joint-commands issued by the network: 4.1 % (demo), 3.1 % (benchmark arm E). In benchmark arm E: base 6.2 %, jaw 12.6 % of ticks. The "3 %" most likely refers to the share of all joint commands. | `vision_manipulation/media/demo_E_vis_touch_v3.json` → `d1c061212c3996b9cf0dff01fd5d5fb96ab72ba3a12b3a2af8cdc6673e464421` | VERIFIED (my figures); the "3 % of base commands" wording NOT VERIFIED |

Two observations from the recomputation that the stage documents do not stress:
- Each of the three "good" shuffles (101, 102, 99) beats the data network in paired comparison (14/3, 13/1, 13/4); six
  shuffles are somewhat worse than it (79–83) and one collapsed (4). The shuffles split into two clusters, which is what one expects if the outcome depends on a
  scalar property (effective squeeze strength / dynamics), not on wiring. VERIFIED (numbers), INFERRED (interpretation).
- The data network does beat the one-line reflex in soft contact (14/4). Because shuffles do the same or better, this is an
  advantage of "a spiking network with temporal filtering" over "an instantaneous threshold", not of fly wiring. INFERRED.

---

## 3. New finding 1 — the interface makes wiring irrelevant by construction

**VERIFIED in code** (hashes: `fly_jaw.py` `7104d901…ca7d`, `sensory_manipulation.py` `260c2c25…6807`, `encoder.py`
`d1345990…1ae6`; full values in §12):

- **Touch input** (`fly_jaw.py:51–52`, `sensory_manipulation.py:122–125`): the 322 bristle neurons are split into two halves
  by list order; every neuron in a half receives the *same* current, proportional to the force on one pad. Input = 2 scalars.
- **Jaw output** (`fly_jaw.py:25–26, 53–54`, `sensory_manipulation.py:135–137`): torque = gain × (mean rate of 2 tibia-extensor
  motor neurons − mean rate of 11 tibia-flexor motor neurons). Output = 1 scalar.
- **Visual input** (`encoder.py:74–75`): every LC10a neuron on one side receives the same current. Input = 2 scalars.
  Output = DNa02 left minus right = 1 scalar.

Consequence (INFERRED, but it follows directly): with scalar-in / scalar-out, the network can only act as a transfer curve
(gain, threshold, saturation, delay, some temporal filtering). A degree- and weight-preserving shuffle keeps input neurons as
inputs and output neurons as outputs, so it yields *another* transfer curve of the same family. The shuffle control therefore
could not have detected a role for topology in these tasks, whatever the fly's wiring is worth. The existing results say
"this task does not need the wiring", not "the wiring is useless".

The one place where wiring specificity already showed up in project data is consistent with this: swapping the FeCO
flexion/extension channels dropped success from 83 to 41 (`feco_audit/swap_v1.json`, REPORTED from
`VISION_MANIPULATION_STAGE.md` §7). There the *identity* of the input channel mattered.

---

## 4. New finding 2 — an unused spatial sensorimotor map exists in the MaleCNS files

Read-only query, run today (pyarrow/pandas on the three feather files; neurons with `status == 'Traced'`; types from the
`type` column; retinotopic position from `assignedOlHex1/2`). **This was exploratory, not pre-registered.**

**Existence and size (VERIFIED):**

| Pathway (type → type) | Edges | Synapses | Note |
|---|---|---|---|
| LC4 (126 neurons: 71 L, 55 R) → DNp01 (giant fiber) | 126 | 6 362 | strictly same-side: L→L 3 782, R→R 2 580, L→R 0, R→L 0 |
| LPLC2 (185: 94 L, 91 R) → DNp01 | 185 | 4 862 | strictly same-side: L→L 2 642, R→R 2 220 |
| LC4 → DNp04 / DNp02 / DNp11 / DNp03 / DNp06 | 126 / 125 / 122 / 126 / 125 | 11 597 / 4 209 / 3 666 / 2 507 / 1 152 | |
| LPLC2 → DNp04 / DNp06 | 185 / 179 | 3 398 / 1 719 | |
| LPLC1 (134) → DNp03 / DNp06 / DNp11 | 134 / 134 / 107 | 3 602 / 2 773 / 1 041 | |

**Gradient (VERIFIED as a statistic; interpretation INFERRED):**
- Per-neuron synapse counts from LC4 onto DNp02 and onto DNp11 are **anti-correlated**: Spearman ρ = −0.65 (left, n = 71,
  p = 6.5e-10) and −0.73 (right, n = 55, p = 2.5e-10).
- LC4 neurons carry no hex coordinate themselves (0 of 9 201 visual-projection neurons do), but their columnar inputs do
  (Tm2, Tm4, Tm20, Tm1). Using the synapse-weighted mean input coordinate as each LC4's position: DNp11 count vs `hex2`
  ρ = **+0.78** (L, p = 1.3e-15) and **+0.75** (R, p = 3.4e-11); DNp02 count vs `hex2` ρ = −0.48 on both sides
  (p = 2.4e-05, 1.8e-04). DNp01 shows no gradient (ρ = +0.05, +0.23).
- 9 correlations were computed per side (8 position-vs-count, 1 count-vs-count); the ones quoted survive a Bonferroni
  correction and replicate across hemispheres. Also seen: DNp04 count falls along both axes (ρ −0.47 to −0.61).
- NOT VERIFIED: which retinal direction `hex2` corresponds to (anterior–posterior vs dorsal–ventral). Input coverage is
  uneven between sides (median 134 hex-annotated input synapses per LC4 on the left, 468 on the right).

**What the literature says about this pathway:** Dombrovski et al., *Nature* 613:534–542 (2023),
doi 10.1038/s41586-022-05562-8 — opposite synaptic-weight gradients from a looming-sensitive visual projection type onto two
descending neurons that promote opposite takeoff directions; the body text names LC4, DNp02 (backward takeoff) and DNp11
(forward takeoff); the motif is reported to generalise across 20 visual projection types. Status: *opened* (PMC9849133,
abstract and part of body); exact gradient directions per axis NOT VERIFIED by me.

**Why this matters:** it is a function that lives in per-neuron synapse counts. A weight-permuting shuffle destroys it, and a
scalar "same current to all neurons" encoder cannot use it. It is the first candidate in this project where data wiring
should beat shuffled wiring *by design of the biology*, not by luck.

Other data facts checked today (VERIFIED): 165 122 traced bodies, 1 314 descending, 1 846 ascending, 708 VNC motor,
9 201 visual-projection neurons; 23 720 optic-lobe neurons have hex coordinates (L1, L2, L3, L5, C2, C3, Mi1, Mi4, Mi9, Tm1,
Tm2, Tm4, Tm9, Tm20, T1); the middle-leg nerve carries 33 distinct bristle types (candidate somatotopy — function NOT
VERIFIED); leg campaniform sensilla (load sensors) are almost unannotated (4 per leg nerve), consistent with the earlier
decision to drop the load channel.

---

## 5. What the literature shows

### 5.1 VLA / VFA models (what they are good and bad at)

| Model | Facts | Source, how seen |
|---|---|---|
| RT-2 | 5B–55B parameters, 1–5 Hz, cloud inference | arXiv 2307.15818, *opened* |
| OpenVLA | 7B; ~6 Hz on one RTX 4090; 970k pretraining episodes; ~10–150 demonstrations to fine-tune; camera only | arXiv 2406.09246, *opened* |
| pi0 | ~3.3B; 50-action chunks, inference 73–86 ms on RTX 4090, re-planning every 0.5–0.8 s (actions inside a chunk are open-loop); ~10 000 h pretraining; no force/touch | arXiv 2410.24164, *opened* |
| SmolVLA | 450M; pretrained on 22.9k community episodes; 50 demonstrations per task; SO-100 multi-task 78.3 % (pi0 61.7 %, ACT 48.3 %); SO-101 pick-place 90 % in-distribution, 50 % out-of-distribution; no latency in ms given; no force/touch | arXiv 2506.01844, *opened* |
| GR00T N1 | 2.2B; slow module 10 Hz, fast module 120 Hz; 63.9 ms per 16-action chunk on an L40 GPU | arXiv 2503.14734, *opened* |
| Figure Helix | slow module 7–9 Hz, fast module 200 Hz, dual embedded GPUs; no success rates published | company blog, *opened*; "Helix 02" 1 kHz layer: press *snippet* only |
| Eka VFA | "about/up to 1 500 picks per hour", ">95 %", ≤ 1 kg; no paper, benchmark, protocol or trial counts published | TechCrunch 2026-10-20, *opened*; company claim, not independently verified |

Documented weaknesses relevant to this question:
- **Fragility to perturbation.** LIBERO-Plus (arXiv 2510.13626, *opened*): OpenVLA falls from 76.5 % to 1.1 % under camera
  perturbation; pi0 from 94.2 % to 15.8 % (camera) and 6.6 % (changed robot start pose); OpenVLA-OFT from 97.1 % to 59.7 %
  and 37.2 %.
- **Slow closed loop / open-loop chunks** (above).
- **No touch in the mainstream models; contact-rich tasks need an added fast layer.** Reactive Diffusion Policy (arXiv
  2503.02881, *opened*): slow policy at 1–2 Hz plus a fast tactile policy (< 1 ms, > 500 Hz after interpolation) raises
  peeling from 0.44 to 0.95 and bimanual lifting from 0.00 to 0.70. ForceVLA (arXiv 2505.22159, abstract *opened*): +23.2 %
  over pi0-based baselines.
- Energy per inference for a VLA: NOT FOUND. Formal safety guarantees: NOT FOUND.

**Reading:** the field itself is converging on "slow semantic policy + fast reactive layer". The fast layers that already
exist are *learned* small networks. That is exactly the slot a fly-derived reflex layer would have to earn.

### 5.2 Does connectome wiring help as a controller or as an architectural prior?

| Work | What was shown | Source, how seen |
|---|---|---|
| Shiu et al., *Nature* 634:210–219 (2024), doi 10.1038/s41586-024-07763-9 | Leaky integrate-and-fire model of 127 400 FlyWire neurons, one free parameter. Predicts feeding and antennal-grooming pathways; 91 % of 164 testable predictions matched. With shuffled weights the feeding motor neuron was activated in 1 of 100 runs versus 100 % with real wiring. Authors' limits: no gap junctions or neuromodulation; rates unreliable; results change if glutamate is excitatory. | *opened* via a text mirror |
| Lappalainen et al., *Nature* 634:1132–1140 (2024), doi 10.1038/s41586-024-07939-3 | Optic-lobe wiring fixed, neuron and synapse parameters *learned* on a motion task; tuning predictions agree with 26 studies. Exact shuffled-wiring numbers NOT VERIFIED. | *snippet* |
| Jin, Zhu, Zhang, Sui, "FlyGM", arXiv 2602.17997 (v3 June 2026) | Whole-brain connectome as a trained graph policy for a simulated *fly body*. Heading error 4.96–8.29° vs 7.77–13.55° for a degree-preserving rewired graph and 6.76–13.90° for a 4×512 MLP. One group; seeds not stated; weights are learned. | *opened* |
| Dhiman, arXiv 2604.04033 (April 2026) | In a fly visual-system model, apparent topology advantages "largely disappear" under fair initialisation and a degree-preserving null. | abstract *opened* |
| Eon Systems (March 2026) | Shiu brain + NeuroMechFly body. Critique: walking, grooming and navigation are scripted routines in the body model; the connectome acts as a trigger. No peer-reviewed paper found. | Carboncopies critique, *opened* |
| Reservoir computing on real connectomes | Mixed. Some fly/zebrafish reservoirs beat random nulls on some tasks (Morra et al. 2025, *snippet*); a 45-connectome study says simple topology features do not predict performance (arXiv 2211.00161, abstract *opened*). | as marked |
| Neural Circuit Policies (Lechner et al., *Nat. Mach. Intell.* 2:642–652, 2020, doi 10.1038/s42256-020-00237-3) | 19 control neurons, 253 synapses, lane keeping; claimed robustness and interpretability. C. elegans-*inspired* wiring, learned weights — not a measured connectome. | *snippet* |
| Loihi 2 robot-control study (Stewart et al., arXiv 2512.03911) | Energy-delay product ~5 % of a GPU, with worse position accuracy. | *snippet* |

**Reading.** (1) Real wiring beats shuffled wiring in sparse, nearly feed-forward sensory-to-motor read-outs (Shiu) — the same
class as the LC4 map in §4. (2) Every positive "embodied" result keeps the *fly body* and *learns* parameters. (3) Where
controls are strict, topology advantages shrink or vanish. (4) I found no paper in which a connectome-derived network
controls a robot manipulator better than a matched classical or learned baseline. NOT FOUND is not proof of absence.

### 5.3 Fly sensorimotor biology relevant to reflexes

All *snippet* unless marked; numbers in ms from full texts could not be obtained (pages blocked).
- Looming: LPLC2 detects radial expansion (Klapoetke et al., *Nature* 551:237–241, 2017, doi 10.1038/nature24626); LC4
  carries the velocity component and LPLC2 the size component of the giant-fiber response (Ache et al., *Curr. Biol.*
  29:1073–1081, 2019); giant-fiber spike timing selects a fast or a stable takeoff (von Reyn et al., *Nat. Neurosci.*
  17:962–970, 2014, doi 10.1038/nn.3741). Absolute escape latencies: NOT FOUND.
- Proprioception: FeCO claw = position, hook = direction, club = vibration (Mamiya, Gurung & Tuthill, *Neuron* 2018);
  hook (movement) signals are suppressed during self-generated movement by descending-driven presynaptic inhibition
  (Dallmann et al., *Nature* 2025, doi 10.1038/s41586-025-09554-2; title and DOI *opened*). This is the biological
  counterpart of the missing "reflex switch" noted in `VISION_MANIPULATION_STAGE.md` §7. Reflex reversal is established in
  stick insects; a direct Drosophila paper was NOT FOUND.
- Motor: size-ordered recruitment of leg motor neurons (Azevedo et al., *eLife* 9:e56754, 2020); premotor connection
  strength scales with motor-neuron size (Lesser, Azevedo et al., *Nature* 631:369–377, 2024, doi 10.1038/s41586-024-07600-z).
- Steering: DNa02 lengthens outside strides in turns (Yang et al., *Cell* 187:6290–6308, 2024,
  doi 10.1016/j.cell.2024.08.033); LC10a drives courtship pursuit (Ribeiro et al., *Cell* 2018; Hindmarsh Sten et al.,
  *Nature* 595, 2021).
- Limits of connectome data: transmitter prediction accuracy 87 % per synapse, 94 % per neuron (Eckstein et al., *Cell*
  187:2574–2594, 2024, doi 10.1016/j.cell.2024.03.016; abstract *opened*); glutamate is inhibitory in the antennal lobe
  (Liu & Wilson, *PNAS* 110:10294–10299, 2013) — evidence from one brain region only.
- Fly-brain power consumption, conduction delays, fastest reaction time: NOT FOUND in a primary source. Do not quote any.

### 5.4 Other mapped nervous systems

C. elegans (302 neurons), larval Drosophila, and the partial zebrafish and mouse-cortex datasets: none of them contains a
circuit that controls a grasping limb, and none has been shown to control a manipulator. The C. elegans line produced
compact *learned* controllers (Neural Circuit Policies), not connectome-derived ones. Status: INFERRED from §5.2; a
dedicated search for manipulation-relevant connectomes (e.g. octopus arm) was NOT done.

---

## 6. Candidate sources of advantage — assessed one by one

"Classical equivalent" = a hand-written controller with the same sensor information and latency budget.

| # | Candidate | VLA weakness it addresses | Classical equivalent | Could fly *wiring* matter? | Evidence in FlyMind today | Verdict |
|---|---|---|---|---|---|---|
| 1 | Fast reflex under a slow policy (touch → grip, looming → retreat) | slow loop, open-loop chunks, no touch | one-line reflex; learned fast layers already exist (RDP) | not with a scalar interface (§3) | network 90 vs reflex 80 (14/4), but shuffles 79–102 | Real niche, **generic** advantage; fly-specific part unproven |
| 2 | Compute and energy per decision | GPU, 70–300 ms per inference | P controller is cheaper still | no | network step 1.65 ms median per 10 ms tick on one CPU core (REPORTED, `VISION_MANIPULATION_STAGE.md` §10) | True but trivial; not a capability advantage |
| 3 | No demonstrations needed | 50+ demonstrations per task | also needs none | no | — | True but shared with classical; the engineering moves into encoder/decoder design |
| 4 | Innate spatial maps (retinotopic looming → escape direction; touch site → limb response) | VLAs must learn every sensorimotor mapping from data | hand-written lookup map | **yes — lives in per-neuron synapse counts** (§4) | not used; encoder gives all neurons the same current | **Best candidate for showing that wiring matters.** At best ties classical in performance |
| 5 | Posture holding by resistance reflex (FeCO) | none (servo firmware already does it at kHz) | PD loop | yes (channel identity; swap → 41/135) | FeCO hurts grasp (83 vs 90) | Biologically correct, practically redundant on SO-101 |
| 6 | Reflex gating during own movement (presynaptic inhibition, Dallmann 2025) | none specific | gain scheduling | possibly | the gating circuit is not in the network | Interesting biology; no advantage expected |
| 7 | Heading memory / object permanence (central complex ring) | short memory under occlusion | hold last value | weak | ring needs ×16 inhibition tuning; occlusion: network 18/20, classical 20/20 | No |
| 8 | Graceful degradation with dead sensors or neurons | fragility to perturbation | summing redundant sensors is equally graceful | no | untested; with 50 ms image delay network 17/40 | HYPOTHESIS, weak |
| 9 | Connectome as a prior for a *learned* policy (FlyGM-style) | data hunger | MLP of equal size | contested in the literature (§5.2) | not done; conflicts with "no training" | Long-term research option only, and shown for a fly body, not an arm |
| 10 | Neuromorphic hardware | power | microcontroller | no | no hardware | Out of scope before 1 December |

---

## 7. Answer — my independent judgment

Separated into what is shown and what is my opinion.

**Shown by FlyMind data (VERIFIED above):** in every head-to-head test so far the classical controller is equal or better;
data wiring is not distinguishable from strength-matched shuffles in grasping; vision–touch integration adds nothing.

**Shown by the literature:** VLAs are slow in closed loop, fragile to perturbation and mostly blind to touch; adding a fast
reactive layer under them gives large measured gains; real wiring beats shuffled wiring for sparse sensory-to-motor
read-outs; no one has shown a connectome-derived controller beating a matched baseline on a robot arm.

**My conclusions (INFERRED / opinion):**

1. **As a replacement for a VLA: no.** Different league of task breadth; nothing in fly biology supplies language, object
   semantics or dexterous planning.
2. **As a better controller than classical code on SO-101: no, for a structural reason.** A fly never evolved to drive a
   5-joint serial arm with a parallel jaw. The fly's evolved competence sits in walking, flight, escape, grooming and
   pursuit, tied to the fly's own body. On an arm, each borrowed reflex reduces to a simple function that a few lines of
   code implement with zero delay. The best the network can do there is tie.
3. **As a fast, cheap, demonstration-free reflex layer under a slow policy: yes, that niche is real and measurable** — but
   the advantage belongs to the *architecture* (a fast hard-wired layer), and a hand-written reflex or a small learned
   network gets it too. It is honest to say "FlyMind demonstrates the reflex-layer idea with a connectome-derived network";
   it is not honest to say "fly wiring gives the advantage" until wiring beats shuffles.
4. **The only fly-specific asset I can point to in the data is innate spatial sensorimotor maps** (§4). Testing one is the
   most direct way to obtain a first positive, shuffle-proof result about wiring. Even if it succeeds, the claim is "the
   connectome contains a usable, untrained sensorimotor map", not "it beats a VLA".
5. **Scientific value vs competitive value.** The project's defensible contribution is the *method* (connectome-derived
   network in a closed loop with shuffle, classical and null controls, honestly reported), not a performance advantage.

My rough probabilities (opinion, not measurement): data wiring beats shuffles on a spatial-map task — about 70–80 %;
a reflex layer improves a slow policy under perturbation — about 90 %, but generic; fly-derived network beats a matched
classical baseline on any SO-101 manipulation metric — under 5 %.

---

## 8. Devil's advocate — strongest reasons the answer is simply "no"

1. **Embodiment mismatch is fundamental**, not a tuning problem (§7.2).
2. **Everything the network adds is engineered around it.** Encoder, decoder, mapping of fly neurons to robot joints and
   all scaffolding are hand-made. A "spatial map" experiment would feed an engineered looming detector into ~126 neurons
   and read two; the biological part is a two-layer weighted sum. A critic will call that a lookup table with extra steps.
3. **Synapse count is not synaptic strength**; transmitter signs are predicted with known error; glutamate sign is assumed;
   neuromodulation, gap junctions and neuron-specific dynamics are absent. The model is generic ALIF dynamics on real wiring.
4. **Latency of the network itself is worse than classical:** touch → first motor-neuron spike ≥ 9 ms of model time, image →
   DNa02 25–74 ms, plus a 50 ms output filter (REPORTED, stage document §10). The "fast" claim holds only against a VLA.
5. **State-of-the-art VLAs already contain fast layers** (120–200 Hz; a 1 kHz layer is claimed). The latency gap is closing
   from their side with learned components that generalise better than a fixed reflex.
6. **The one robust positive in the literature (FlyGM) needed learned weights and a fly body**, and a stricter-controls
   paper found topology advantages vanishing.
7. **Our own evidence is all simulation**, with ideal images, green objects, a colour-blob encoder, and contact physics
   shown to change conclusions (93/90 → 101/84).
8. **Single connectome, single animal.** Any data-level statistic can only be replicated across hemispheres, not animals.
9. **Motivated reasoning risk.** After many negative results, a new "candidate where wiring should matter" is exactly what
   one would hope to find. That is why §10 starts with a data-only test with a kill criterion.

---

## 9. Conflicts with the owner's principles — stated explicitly

| Principle (`FLYMIND_MASTER_CONTEXT.md`, 3 Nov) | Conflict | Who decides |
|---|---|---|
| "The fly should control, not the algorithm, even if we lose quality" | The realistic advantage niche is the fly as a *reflex layer under* another controller. Pursuing "advantage over VLA" and "the fly controls everything" at once is not possible with present evidence: the more the fly controls, the larger the measured loss. | Adam |
| Inputs only from natural senses, no artificial stimulation | No conflict for §10. The looming encoder is camera-driven but engineered; it must be labelled ENGINEERING. | — |
| No tuning or training without consent | Candidate 9 (learned weights on connectome wiring) conflicts; I do not propose it now. Strength-matching of shuffles is a form of calibration and must be fixed before outcome data. | Adam, if ever wanted |
| Classical code only as safety, baseline or labelled scaffolding | The "slow-policy surrogate" in §10 is a baseline, labelled as such; it is not a VLA and must never be called one. | — |

---

## 10. Proposed plan (nothing below starts without approval)

Design principles: new files only; no shared or protected module is modified; no historical result is touched; every stage
has a pre-registration file written and hashed **before** it runs; seeds reserved in a registry after checking all existing
registries (I have not yet done that check — NOT VERIFIED); each stage has a kill criterion.

**Stage D0 — data only, no simulation (about half a day).**
Pre-registration file: `flymind/experiments/bio_advantage/D0_PREREG.md`.
- D0-a: for LC4, LPLC2 and LPLC1 onto DNp02, DNp04, DNp06, DNp11 (and DNp01 as a negative control): rank correlation between
  per-neuron synapse count and inferred retinotopic coordinate, each hemisphere separately; null = 1 000 permutations of
  weights within the same pre→post type pair. Because §4 already looked at LC4, LC4 counts as *exploratory*; LPLC2 and LPLC1
  pairs are the confirmatory set.
- D0-b: the same for LC10a onto the DNa02 path used today (does the data contain a graded "how far to turn" map?).
- D0-c: middle-leg bristle type × motor-neuron-pool path-weight matrix vs degree-preserving shuffles (is there a touch-site
  → muscle map?).
- Kill: if no confirmatory pair shows a gradient beyond the 95th percentile of its null in **both** hemispheres, the
  spatial-map line stops and the answer for wiring is "no evidence, stop looking in this dataset".

**Stage S1 — "is the network just a transfer curve?" (simulation, ~1–2 h compute).**
- Build a classical reflex that copies only the data network's measured static force→torque curve and step delay. Run the
  same 135 trials, soft and stiff contact.
- H1: paired outcomes equivalent to the data network (pre-set margin ±7 of 135; discordant-pair test plus an object-level
  cluster analysis, because 3 poses per object are not independent).
- If H1 holds: the grasp line is closed as "wiring-irrelevant by design" and no further shuffles are run on it.

**Stage S2 — spatial-map reflex (only if D0 passes; simulation, new scene and new module).**
- Task: an object approaches the gripper camera from a varied direction; the arm must retreat in the correct direction
  before contact. Input: engineered local-expansion signal delivered to each LC4/LPLC2 neuron at its data-derived
  retinotopic position. Output: DNp11 minus DNp02 rate → retreat direction (mapping fixed from Dombrovski 2023 before any run).
- Arms: DATA; ≥ 20 weight-permuted shuffles, strength-matched before outcome data; classical map with equal information;
  the same classical map throttled to a VLA-class loop (two settings taken from §5.1, e.g. 10 Hz with 100 ms delay and
  2 Hz with 500 ms) as a **slow-policy surrogate, not a VLA**; no reflex.
- Sample: 200 paired scenes; metrics: correct direction (binary), contact avoided (binary), reaction time.
- H2a (wiring): DATA ranks first among DATA + 20 shuffles on correct direction (one-sided p ≤ 1/21).
  H2b (cost of using the fly): DATA not worse than the classical map by more than 10 percentage points.
  H2c (niche): DATA avoids contact more often than both slow surrogates (exact McNemar).
- Kill: H2a fails → the project states plainly that connectome wiring has shown no measurable role in any task tried.

**Optional S3 — measured compute comparison on this Mac** (FlyMind tick vs one SmolVLA inference). Needs a model download
and the LeRobot environment; reports latency only, no task claim. Low priority.

**Not proposed before 1 December:** learned weights on connectome wiring; any hardware; changes to shared modules; 120 Hz loop.

**Poster (16 November), independent of the plan:** only verified statements — simulation only; MaleCNS wiring; the network
turns the base and closes the jaw; the classical controller is better; shuffled wiring performs the same in grasping; the
looming→direction map exists in the data (if D0 confirms it by then).

**Open safety items carried over (not addressed here):** joint speed 1.89 rad/s above the 1.5 limit (cause NOT VERIFIED);
pad penetration with soft contact. Both must be fixed before any hardware use.

---

## 11. Limits of this report

- Most biology and several VLA sources were seen only as search snippets; publisher pages blocked automated reading. Every
  such row is marked. No number from a snippet should go on the poster without opening the paper.
- Sub-agent reports are model output; I spot-checked arXiv 2604.04033, arXiv 2602.17997 and Dombrovski 2023 myself.
- The MaleCNS paper citation (Berg et al.; neuron count ~166 700) is *snippet* only; my own count of 165 122 uses
  `status == 'Traced'` and is a different definition.
- §4 is one exploratory analysis on one animal; the retinal meaning of the coordinate axis is unknown to me.
- V5 was read from its analysis file, not recounted. Tests were counted, not run.
- Probabilities in §7 are opinions.

## 12. Full SHA-256 values of files cited

```
8972809cc22ada303c8b3abbf8897f0caac61d72ba0388f6a6f83e55de8d271d  flymind/results/vision_manipulation/A_cam_v3.json
2c88c5b795cfea0437f35a25608ee3ef60f768fb8336564f8a86fe904329d911  flymind/results/vision_manipulation/B_cam_v3.json
424c86f4be56250538d8de69bc6f0438ac412760de1fc8ceb96381efd413d406  flymind/results/vision_manipulation/D_vis_v3.json
ea4ba4b62642764fc57d2c0b6d12b129ffe71bb4e17a1c2967449acca0d7cacd  flymind/results/vision_manipulation/E_vis_touch_v3.json
fb8fe3177c720cae7b1b59cb7e3c0b74f162ff2a08d969e803f1216589914012  flymind/results/vision_manipulation/E_blind_grasp_v3.json
9986e0637b09897e53151ca009dcc0a140d6a671f805d4638f3a62ae240c4353  flymind/results/vision_manipulation/F_vis_touch_feco_v3.json
d1c061212c3996b9cf0dff01fd5d5fb96ab72ba3a12b3a2af8cdc6673e464421  flymind/results/vision_manipulation/media/demo_E_vis_touch_v3.json
4d76d66f0f44e01fb3502b32a78276676353b71d1afbb76f5bd3b28e4180a054  flymind/results/object_handling/B_base_v2.json
2bb4afeda53a9ce46803413417c0102556c93b44b712dfa667311812798a4ef4  flymind/results/sensory_manipulation/B_fly_search_glu-1_v1.json
9ac92a04e174e7aff712e0941254835309ea7659a396bc9ba799ce54fae7a866  flymind/results/sensory_manipulation/B_fly_search_glu+1_v1.json
641500489604ead4ca254d17d62783c8b94b2b6eff4355f9905e6169f5159279  flymind/results/sensory_manipulation/C_fly_feco_search_v1.json
ac4e31759e201e4c1f3752759ec2f8ef82b80002efca28e38371c64dab67024b  flymind/results/sensory_manipulation/D_reflex_search_v1.json
937f3acf7debe279de382786a0c5a7a12824a558226edb6711b5a09850bf927a  flymind/results/sensory_manipulation/N_null_search_v1.json
9eebaef0d1bce613871c409a9abeca562bcf04a8f70af0a331d75846e8484cbf  flymind/results/contact_audit/stiff_A_v1.json
2fbaf3fa6f298069b40ea81b4d6ba45217eb4ebbaea24fe7961acc5764eccd90  flymind/results/contact_audit/stiff_B_v1.json
b83d1d79ccfd52272235a7901e712ec1564f02aa34ef64925e52c292394118da  flymind/results/shuffle_matched/shuffle_17100011_v1.json
379c414cc1cfece7a6a2aa161c6b5ab546f01444c447c0e772b02ae6d9dbfd00  flymind/results/shuffle_matched/shuffle_17100012_v1.json
0b3fff1dd5f557ebb272dbd7abdd379731ff27f41bc660c04e88a0a9442c1b23  flymind/results/shuffle_matched/shuffle_17100013_v1.json
9763f8fe7746f0576163f6d29589a4145cdeea3a627fb1521cc6350781de71b2  flymind/results/shuffle_matched/shuffle_17100014_v1.json
e57b1a64d1e3c4d1618e96bdfd407d1c452815e9a43e75dd1a782588136c5790  flymind/results/shuffle_matched/shuffle_17100015_v1.json
63023bbe0fa9270fd0c6c8b2070f0da4bb94e9cbd61fcb9b25e960ec5fa483dc  flymind/results/shuffle_matched/shuffle_17100016_v1.json
b0130faf6768dd595bd3352046b72e910a23101030126720b8aeeb97519c35d0  flymind/results/shuffle_matched/shuffle_17100017_v1.json
63a165525044722e1d6e8885288f979b1e8f97d2d052ed841120f23f8b5afbfd  flymind/results/shuffle_matched/shuffle_17100018_v1.json
52cc9221f860f34eb862ff24c1087357aece3c7092b2786fae9c8111d1314373  flymind/results/shuffle_matched/shuffle_17100019_v1.json
ca3c32d68552e8364333a39bde63b16ad9448111adee25d8d48aa6d5bacfd172  flymind/results/shuffle_matched/shuffle_17100020_v1.json
f4416fd390aad5dce4f278f5be599bf30bd50f0ebb6ee87bbb91be2fe6bfd137  flymind/results/v7/v7.jsonl
998209b712cbfffda52113cde39a073c2b310c1fdfa74a0c689e03020ee76160  flymind/results/v5/v5_confirm_20261028T220223.json
035c7d7181f5835719210cd60e7f2ea89cbf96053cbfa4ffa4fbaf5f501fdb05  flymind/results/v5/analysis_confirm.json
7104d901afd16e0236568d9e858ff4ad15a10f1d2799b9cb49ddc1f537b1ca7d  flymind/fly_jaw.py
260c2c25401cd52ab672858406c54a993da72abab5311eff70ef1866dd7a6807  flymind/sensory_manipulation.py
d134599053fa50125bb7fe0c665a2e48ff67a7278ad05a205b5a5d9da1f51ae6  flymind/encoder.py
```

## 13. Decisions for Adam

1. Approve, change or reject the plan in §10 (D0 first; S1 and S2 only after D0 and a written pre-registration).
2. Decide how to handle the conflict in §9: is "the fly as a reflex layer under another controller" an acceptable role?
3. Confirm that the poster may say plainly that shuffled wiring performs as well as fly wiring in grasping.

STOPPED AT CHECKPOINT 1 — awaiting Adam's approval.
