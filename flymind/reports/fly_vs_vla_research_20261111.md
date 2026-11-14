# FlyMind — the fly versus VLA/VFA models, and what FlyMind can still prove

Research report and proposed plan, 2026-11-11. Author: Claude (Fable 5.2), at the owner's request.
A new effort that builds on `flymind/reports/bio_advantage_research_20261110.md` (not modified) and on Stage D0 (not modified).
Status of this file: new, uncommitted, **the only file created in this effort**. Nothing was simulated, trained, committed
or changed. No poster or Explory text was written.

Evidence labels: **VERIFIED** (checked now; command, file or URL given), **PARTIALLY VERIFIED**, **REPORTED** (copied from
a document or a source I did not open myself), **INFERRED**, **HYPOTHESIS**, **NOT VERIFIED**, **FAILED**,
**NOT IMPLEMENTED**. Literature rows also say how the source was seen: *full* (html text read), *abstract* (abstract or
metadata only), *snippet* (search summary only). Anything not marked *full* stays NOT VERIFIED for poster use.

---

## 0. Streszczenie dla Adama (po polsku, prostym językiem)

**Pytanie:** czego mucha nie ma, a modele VLA/VFA mają; co mucha ma, a one nie; i czy FlyMind może z tego zrobić
mierzalny wkład na 1 grudnia i na Explory 2027.

**Odpowiedź w trzech zdaniach.**
1. **Mucha nie ma tego, co stanowi siłę VLA:** języka, rozumienia dowolnych przedmiotów, uczenia się z pokazów, długich
   zadań i zręcznej manipulacji. Nasz model ma jeszcze mniej niż prawdziwa mucha: jej układ wzrokowy (ponad połowa
   neuronów) zastępujemy prostym wykrywaczem koloru, a uczenia się i pamięci nie modelujemy wcale.
2. **Mucha ma kilka rzeczy, których VLA nie mają:** wrodzone „mapy” zamieniające miejsce bodźca na kierunek ruchu (bez
   żadnych danych uczących), bardzo szybkie i tanie odruchy, uczenie się z jednego doświadczenia i w pełni znany schemat
   połączeń. Ale prawie wszystko z tej listy potrafi też prosty program napisany ręcznie — dlatego nie da się uczciwie
   powiedzieć „mucha jest lepsza”.
3. **Jeden mierzalny wkład jest realny do 1 grudnia, ale wąski i naukowy, nie „przewaga nad VLA”:** pierwszy test
   w zamkniętej pętli, w którym sieć z prawdziwymi połączeniami musi wygrać z sieciami przetasowanymi, bo mapa siedzi
   w połączeniach. Etap D0 (zrobiony dziś rano, osobny tor) pokazał, że takie mapy są w danych. W literaturze nie znalazłem
   nikogo, kto sterowałby ramieniem robota siecią z konektomu z takimi kontrolami — ale „nie znalazłem” to nie dowód, że
   nikt tego nie zrobił.

**Co się zmieniło względem raportu z 10 XI (moje poprawki):**
- Napisałem tam, że sieci przetasowane „robią to samo lub lepiej” niż sieć z danych. To było za mocne. Dokładnie: 3 z 10
  przetasowanych są lepsze od sieci z danych, 6 jest od niej gorszych i równych prostemu odruchowi, 1 się załamała.
  Wniosek „to zasługa filtrowania w czasie, nie połączeń” jest więc hipotezą, nie wynikiem.
- Wynik V5 (38/40 wobec 40/40) przeliczyłem teraz z surowych prób — potwierdzony.
- Oś mapy w oku: znalazłem w danych niezależną kotwicę (fotoreceptory górnego brzegu oka). Gradient LC4 biegnie wzdłuż
  osi przód–tył, tak jak w publikacji z Nature 2023. Który koniec jest „przodem” — nadal niesprawdzone.

**Sprzeczność z Twoją zasadą — nadal otwarta.** Są dwie możliwe role muchy i nie wybieram za Ciebie (pkt 8):
„ramię robi tylko to, co umie mucha” (zgodne z zasadą, bez użytecznego zadania) albo „mucha jako odruch pod innym
sterownikiem” (użyteczne, ale sprzeczne z zasadą). Ten sam eksperyment obsługuje obie role.

**Jedna decyzja:** czy zgadzasz się, żebym napisał rejestrację wstępną eksperymentów z pkt 10 (sam dokument)? Niczego nie
uruchamiam. Etapy S1 i S2 pozostają niezatwierdzone.

---

## 1. Scope, method, what was not done

Done, all read-only: re-verification of repository state, data hashes, the 10 November report and D0 files; recomputation
of the headline numbers from raw files; four inline read-only queries on the MaleCNS files (no script saved); three
literature sub-agents with web access only, plus my own checks that the two most important new papers exist under the
cited ids.

Not done: no simulation, no training, no code or pre-registration file written, no commit, no change to any existing file,
no test run, no contact with the robot, no poster text. D0 was neither re-run nor extended.

---

## 2. Re-verification (2026-11-11, 16:02 CET)

| Item | Result | Status |
|---|---|---|
| HEAD | `664b61133f138b79b275840845cdf66d91f75fda`; 2 modified tracked files (`REPRODUCE.md`, `VALIDATION_PLAN.md`), 144 untracked entries | VERIFIED (`git rev-parse`, `git status --porcelain`) |
| Connectome files | annotations `2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2`; transmitters `95c9289220663abeb3409f3ad9e5a7f8a53f8093f5139d15502cd08da8879621`; weights `e35da783d1c686b2b58b3b87cd6a403ae43bfcfba8bff28e08ef752c1a56afc1` — identical to `results/sensory_manipulation/FREEZE_v1.txt` and `results/vision_manipulation/FREEZE_v1…v3.txt` | VERIFIED (`shasum -a 256`) |
| 10 November report | present, SHA-256 `1b6e93ee463cc2f27284360b8d2fa5ed4c9599364dd38a48f06e9657995cb7d9`, not touched | VERIFIED |
| All 31 raw files listed in §12 of that report | every hash still matches (`shasum -c`: 31 OK, 0 failed) | VERIFIED |
| Tests | 19 tracked (14 + 5), 6 untracked; counted, **not run** | VERIFIED (count only) |

### 2.1 D0 status (separate track — reported, not modified)

D0 **finished** on 2026-11-11 (run 09:08–09:15, exit 0, single run). Files intact:
`experiments/bio_advantage/D0_PREREG.md` `de06eacb59c0f576ce3a420f8871def7bab1c7979ac9985c80b47ef361d6de39` (hash recorded
09:06:54, before the run); `d0_analysis.py` `9e1bb539740b2054690ded3a5b3e23eae220bb4015bfac88f26d7e6cd8c403c7`;
`D0_REPORT.md` `e0319ddbbf47f4702f534611eba134c1710976d3cb4ac108728781987c76477f`;
`results/bio_advantage/d0_v1/d0_results.json` `45725a6df9d2316a64a247cd5dc8004cec16fecf6f7b23edebfaf56216770ca4`;
`d0_stdout.txt` `d5ea0bdf9942a0503f5867a739a6ea683af0b07c1c829a8a5737f63a030cc25c`. VERIFIED.

Outcome (details in `D0_REPORT.md`): H-a PASS — 4 of 5 confirmatory pairs (LPLC2 → DNp04; LPLC1 → DNp03, DNp06, DNp11)
show a position gradient at p = 0.0001 in both hemispheres, LPLC2 → DNp06 failed (right side p = 0.024); H-b PASS but weak
for the registered primary quantity (LC10a → DNa02, R ≈ 0.3); H-c PASS (bristle types reach different motor pools, 0 of
100 shuffles as high). D0-a was recomputed blind by an independent instance; D0-b and D0-c were not. LC4 remains
exploratory. Seeds 19 100 000–19 100 999 are consumed.

### 2.2 Headline numbers recomputed again from raw files

Same method as on 10 November (per-trial records, Wilson 95 %, exact two-sided McNemar on trials paired by object and
pose; 135 trials = 45 objects × 3 poses, so p-values are indicative only). Paths under `flymind/results/`; full hashes
for the grasp files are in §12 of the 10 November report (all re-checked today).

| Claim | Recomputed today | Status |
|---|---|---|
| Stiff contact: classical 101/135, network 84/135 | 101, 84; only-classical 21, only-network 4, p = 0.001 (`contact_audit/stiff_A_v1.json`, `stiff_B_v1.json`) | VERIFIED |
| Soft contact: classical 93, network 90, reflex 80 | 93 (60.6–76.1 %), 90 (58.4–74.1 %), 80; network vs reflex 14/4, p = 0.031; network vs classical 12/15, p = 0.70 | VERIFIED |
| Shuffles 101, 82, 80, 102, 83, 79, 82, 79, 99, 4 vs 90 | exactly these (`shuffle_matched/shuffle_17100011…20_v1.json`) | VERIFIED |
| "Shuffles beat the reflex too" | **Only partly.** Shuffle vs reflex, discordant pairs: 28/7, 25/3, 21/2 (three shuffles clearly better than the reflex); 10/8, 9/9, 10/7, 12/13, 12/10, 10/11 (six indistinguishable from the reflex); 2/78 (one collapsed) | VERIFIED — corrects the wording of 10 November |
| Vision + touch vs touch alone | E 86, B_cam 85, E_blind 86; discordant 5/4 and 3/3 | VERIFIED |
| Pad penetration > 2 mm | 16 and 23 (oracle-stage network, Glu −1 / +1), 21/21/21/18 (camera arms), 0 (classical camera) | VERIFIED |
| Joint speed | max 1.89 rad/s in all six v3 arms | VERIFIED |
| Demo v3 command share | jaw 8.8 %, base 16.0 %, 4.1 % of all joint commands (`vision_manipulation/media/demo_E_vis_touch_v3.json`) | VERIFIED |
| V5 orientation | **recounted from the 240 raw trials**: network 38/40 (median error 1.41°), P 40/40 (0.16°), shuffled 3/40, sides swapped 0/40, no vision 0/40, network with 50 ms image delay 17/40 (`v5/v5_confirm_20261028T220223.json` → `998209b712cbfffda52113cde39a073c2b310c1fdfa74a0c689e03020ee76160`) | VERIFIED (was PARTIALLY VERIFIED) |
| V7 | unchanged from 10 November (file hash re-checked): P better on average in all four blocks, 471 of 480 pairs | VERIFIED (hash), REPORTED (numbers from yesterday's recomputation) |
| Network timing | compute for 10 network steps: median 1.65 ms, p99 1.84, max 7.88 (n = 16 486 ticks); camera → command median 5.79 ms (`vision_manipulation/latency_v3.json` → `221f856c9dbf5f4835056ce194d6d861d901dc664abf2526a5a13536d22aa5e5`). Model-time delay touch → first motor spike 9 ms at 1–2 N, 14 ms at 0.5 N, 29 ms at 0.25 N, none at 0.1 N; image → DNa02 25–74 ms (`vision_manipulation/net_latency_v1.txt` → `9e69447e85718b2fc6d4ff2f3f0c043a31bb2ff525f8f6eb8587f5ec417d1248`) | VERIFIED |

### 2.3 Corrections to my 10 November report

1. §2.3 there says shuffles "do the same or better" than the data network against the reflex. Precisely: the data network
   (90) ranks 4th of 11; three shuffles beat it, six are worse than it and equal to the reflex, one collapsed. That the
   network's edge over the reflex is "temporal filtering, not wiring" is a **HYPOTHESIS**; the existing data cannot decide it.
2. V5 is now recounted from raw trials.
3. The retinal meaning of the hex axes is now partly anchored (§5.2).
4. The interface finding (§3 there) stands: `fly_jaw.py:51–54`, `sensory_manipulation.py:119–137`, `encoder.py:74–75`
   (file hashes unchanged). VERIFIED yesterday; hashes re-checked today.

---

## 3. Three things to keep apart

Most confusion in this comparison comes from mixing three different objects:

- **The fly** — a real animal; what its nervous system can do is known from experiments (literature).
- **FlyMind** — a generic spiking model (ALIF) on a small slice of one male fly's wiring, with a hand-built encoder,
  decoder and scaffolding, in simulation (this repository).
- **VLA / VFA** — large learned policies trained on robot data (literature and company claims).

How small the slice is (VERIFIED from the annotation file, `status == 'Traced'`): 165 122 traced bodies. FlyMind's largest
network uses 1 931 of them (1.2 %); the V5 steering network 424 (0.26 %). 89 390 traced neurons (54.1 %) are optic-lobe
intrinsic — the fly's visual system — and FlyMind replaces all of them with a colour-blob encoder. Circuits present in
the data and unused: 4 064 Kenyon cells, 97 mushroom-body output neurons, 340 dopamine neurons (the learning circuit);
2 950 central-complex neurons (heading and navigation); 2 639 olfactory, 1 428 gustatory receptor neurons.

---

## 4. Comparison table

"Classical" = a hand-written controller with the same sensors. Sources for the literature cells are in §5.

| Capability | The fly (literature) | FlyMind today (repository) | VLA / VFA (literature) | Does a few-line classical controller have it? |
|---|---|---|---|---|
| Language, instructions | none | none | core capability | no |
| Recognising arbitrary objects | innate feature detectors plus learned associations; pattern memory invariant to retinal position | green-colour detector | strong but fragile (LIBERO-Plus) | no |
| Learning from demonstrations | none shown for motor skills | none | core (50–100 demonstrations per task) | no |
| Long multi-step tasks | innate sequences (grooming hierarchy) | classical scaffolding does it | yes, minutes; unseen long tasks still fail | only if scripted |
| Dexterous object manipulation | none found (reach in gap climbing, grooming) | one jaw, scalar torque | yes | scripted only |
| Online learning from one experience | yes in the animal (one training cycle) | **none** — no plasticity in the model | no deployed VLA does it; batch retraining needs hundreds of trajectories; sequential fine-tuning forgets | yes (a lookup table) |
| Innate sensor-to-motor maps | yes (looming position → escape direction) | present in data (D0), **unused** | must be learned | yes, if an engineer writes the map |
| Reaction speed | escape circuits; exact ms NOT FOUND in a primary source | network compute 1.65 ms per 10 ms tick; model delay 9–29 ms touch, 25–74 ms vision | tens to hundreds of ms per action chunk; moving objects cut most VLAs to ~1–13 % | yes, and faster |
| Compute | brain power NOT FOUND | one CPU core | GPU, 40–300 ms per inference | yes, and cheaper |
| Touch and body sense | rich (2 558 tactile, 1 454 proprioceptive neurons annotated) | 322 bristles + FeCO, collapsed to scalars | absent in mainstream VLAs; added in tactile/force variants and VFA | yes |
| Training data needed | none (evolution) | none, but the interface is hand-engineered | thousands of hours + per-task demonstrations | none |
| Inspectable mechanism | wiring known neuron by neuron | yes | no; features mostly memorised demonstrations | fully |
| Fit to a 5-joint arm with a jaw | none — evolved for a fly body | mapping is an engineering analogy | trained on the arm | designed for it |
| Robustness | — | fragile to image delay (17/40 at 50 ms) and to contact stiffness (90 → 84) | fragile to camera and start-pose changes | usually robust |

**Reading the last column:** every asset in which the fly beats a VLA (speed, cost, no data, transparency, built-in maps,
one-shot learning) is also available to a small hand-written controller. Every asset in which a VLA beats the fly
(language, semantics, demonstrations, dexterity) is unavailable to both the fly and the hand-written controller. So on a
robot arm the fly sits in the same corner as classical control — and classical control was designed for the arm.

---

## 5. Evidence behind the table

### 5.1 What FlyMind data show (VERIFIED unless marked)

- All performance comparisons to date: classical equal or better (§2.2).
- The interface is scalar-in / scalar-out, so the grasp and steering tasks could not reveal a role for wiring.
- D0: spatial structure exists in the wiring at three places (§2.1).
- Learning circuit in the data (read-only query today): projection neurons → Kenyon cells 22 586 edges, 390 928 synapses,
  3 812 Kenyon cells with such input, median 5 inputs of ≥ 5 synapses each; Kenyon cells → output neurons 463 640 synapses;
  dopamine neurons → Kenyon cells 225 127 synapses; output neurons reach 88 descending neurons directly (≥ 5 synapses).
  This shows the circuit is there. It says nothing about whether a model of it would learn. Classes taken from the
  annotation column `class` (`Kenyon_Cell`, `MBON`, `DAN`, `ALPN`).

### 5.2 Retinal axis of the looming map (new, exploratory, read-only)

`R7d` and `R8d` photoreceptors (82 and 76 traced; by standard nomenclature the dorsal-rim types — INFERRED from the type
name) have no hex coordinate, but their hex-annotated targets place them at the high-h1, high-h2 corner in both eyes:
offset from the eye centre about (+10 to +13, +14 to +16), i.e. direction ≈ 47–58° in hex space. So "dorsal" ≈ the h1 + h2
direction. The eye spans 7…71 along h1 + h2 and −19…+16 along h1 − h2. VERIFIED (numbers), INFERRED (dorsal).

The LC4 gradients found in D0 point at −46°/−45° (onto DNp02) and +116°/+120° (onto DNp11). They are 162–166° apart, i.e.
nearly opposite. The DNp02 gradient is 92–104° from the dorsal direction (perpendicular to it); the DNp11 gradient is
58–73° from it (mostly across, partly tilted dorsally). So the push–pull runs mainly along the axis perpendicular to
dorsal–ventral, i.e. the anterior–posterior axis. This agrees with Dombrovski et al.,
*Nature* 613:534–542 (2023), doi 10.1038/s41586-022-05562-8 (*abstract and part of body opened* on 10 November), who report
anterior–posterior gradients. **PARTIALLY VERIFIED:** the axis; **NOT VERIFIED:** which end is anterior.

### 5.3 What the literature shows about the fly

All *abstract* (Europe PMC) unless marked; DOIs were returned with matching titles; no full text was read.

- **Learning.** Odour–shock learning reaches its plateau within one training cycle of 12 shocks; memory still present at
  24 h (Tully & Quinn 1985, doi 10.1007/bf01350033). Mushroom body: about 2 000 Kenyon cells, 21 output
  neuron types, 20 dopamine neuron types, 15 compartments (Aso et al. 2014, doi 10.7554/eLife.04577); different dopamine
  types implement different learning rules (Aso & Rubin 2016, doi 10.7554/eLife.16135).
- **Input wiring to the learning circuit:** reported random (Caron et al. 2013, doi 10.1038/nature12063), later shown to be
  partly structured, and the structure made odour discrimination *worse* than random in simulation (Zheng et al. 2022,
  doi 10.1016/j.cub.2022.06.031).
- **Vision and memory.** Pattern recognition invariant to retinal position (Tang et al. 2004, doi 10.1126/science.1099839);
  short-term pattern memory in the fan-shaped body (Liu et al. 2006, doi 10.1038/nature04381); place learning (Ofstad et al.
  2011, doi 10.1038/nature10131); spatial working memory of "several seconds" (Neuser et al. 2008, doi 10.1038/nature07003).
- **Learning without the brain.** Headless flies learn to hold a leg position to avoid shock; over 90 % reach criterion
  (Booker & Quinn 1981, doi 10.1073/pnas.78.6.3940).
- **Navigation.** Heading held by persistent activity in the ellipsoid body (Seelig & Jayaraman 2015,
  doi 10.1038/nature14446); behaviour consistent with path integration (Kim & Dickinson 2017, doi 10.1016/j.cub.2017.06.026).
- **Action selection.** Grooming as a suppression hierarchy (Seeds et al. 2014, doi 10.7554/eLife.02951).
- **Manipulation.** Nothing found beyond grooming and visually guided reach in gap climbing (Pick & Strauss 2005,
  doi 10.1016/j.cub.2005.07.022). A statement about the search, not proof of absence.
- **Social learning.** Mate-choice copying claimed (Danchin et al. 2018, doi 10.1126/science.aat1590) and disputed
  (Thornquist & Crickmore 2019, doi 10.1126/science.aaw8012). Not motor imitation.
- **Timing and energy.** Fastest reflex latency and brain power: NOT FOUND in a primary source. Do not quote any.
- **Other insects.** Bumblebees learn ball rolling and string pulling (Loukola et al. 2017, doi 10.1126/science.aag2360;
  Alem et al. 2016, doi 10.1371/journal.pbio.1002564). Whether any such species has a mapped connectome was not searched.

### 5.4 What the literature shows about VLA / VFA (additions to the 10 November report)

- **Generalisation.** pi0.7 (arXiv 2604.15483, *full*, first two thirds): 60–80 % success on unseen tasks or unseen
  task–robot combinations versus > 90 % on seen ones; unseen long-horizon tasks stated as too complex.
- **On the same arm as ours.** Benchmark on SO-101 (Yu & Qiu, arXiv 2606.08881; sub-agent read *full*; I confirmed id and
  title): 4 tasks, 100 demonstrations each, 20 rollouts per cell — average success pi0.5 56.25 %, Wall-X 51.25 %, ACT
  33.75 %, SmolVLA 32.5 %; recovery after a failure pi0.5 30.8 %, SmolVLA 3.2 %.
- **Moving objects.** DynamicVLA (arXiv 2601.22153; sub-agent read *full*; I confirmed id and title): on its dynamic
  manipulation benchmark SmolVLA 12.7 %, pi0.5 11.1 %, pi0 8.1 %, OpenVLA-OFT 1.3 %, the purpose-built 0.4B model 47.1 %;
  object speeds up to 0.75 m/s in simulation; failures attributed to stale actions and delayed reaction. The paper's own
  speed figures conflict (88 Hz in text, ~4 Hz in a table) — NOT VERIFIED.
- **Latency.** Real-time chunking (arXiv 2506.07339, *full*): model latency 76–97 ms on an RTX 4090; with +100/+200 ms
  injected delay the standard smoothing methods failed, the proposed method did not degrade. Embedded: pi0.5 ~44 ms,
  GR00T N1.6 41–45 ms on Jetson Thor (forum post, not official). SmolVLA on Apple silicon: 111–205 ms per 50-action chunk
  on an M5 Pro (*snippet*; not our M1 Max).
- **Learning from experience.** pi*0.6 (arXiv 2511.14759, *full*, first three quarters): improvement by batch retraining
  on 300–600 autonomous trajectories per iteration. No deployed VLA learning from a single failure without retraining was
  found. Sequential fine-tuning of pi0.5 on real robots: backward transfer −81 without replay, fixed by replay
  (arXiv 2605.26820, *full*); an opposite simulation result with RL + LoRA (arXiv 2603.11653, *full*).
- **Touch.** ForceVLA 60.5 % vs 37.3 % without force (arXiv 2505.22159, *full*); Tactile-VLA, tactile at 100 Hz with a
  hybrid position–force controller underneath (arXiv 2507.09160, *full*); TacVLA (arXiv 2603.12665, *full*).
- **Opacity and fragility.** Sparse-autoencoder features of VLAs mostly correspond to memorised demonstrations
  (arXiv 2603.19183, *snippet*); adversarial attack success 52–92 % (arXiv 2509.03383, 2506.03350, *snippet*).
- **Energy per action:** NOT FOUND. **Eka VFA:** nothing new published between 20 October and 11 November 2026 was found;
  all figures remain company claims (TechCrunch 2026-10-20, *full*).

### 5.5 Where insect-derived ideas have given a measured advantage

| Level | Example | Measured against | Result | Seen |
|---|---|---|---|---|
| Algorithm idea (not real wiring) | Fly-olfaction hashing (Dasgupta et al., *Science* 2017, doi 10.1126/science.aam9868) | classical locality-sensitive hashing | better retrieval; numbers not seen; no test against modern search libraries found | *snippet* |
| Algorithm idea | Continual learning (Shen et al., arXiv 2107.07617) | EWC, GEM, replay variants | 0.86 vs 0.58–0.77 accuracy on a small benchmark; weak modern baselines | *full* |
| Algorithm idea | FlyLoRA (arXiv 2510.08396, NeurIPS 2025) | LoRA | +1–3 points single task; large gains when merging adapters | *full* |
| Real wiring, learned weights, fly body | FlyGM (arXiv 2602.17997) | degree-preserving rewired graph, MLP | 4.96–8.29° vs 7.84–13.55° heading error; one group, seeds not stated | *full* |
| Real wiring, stricter controls | Dhiman (arXiv 2604.04033) | degree-preserving null, shared initialisation | advantage largely disappears | *abstract* |
| Real wiring, other 2026 preprints | FLYNN (arXiv 2607.00025), FlyCNS (arXiv 2609.28816) | hand-crafted nets; full communication | "comparable"; weak structural prior | *abstract* |
| Hardware | Spiking controller on Loihi 2, 7-joint arm (arXiv 2403.08928) | laptop CPU | ~53 µJ vs ~3 800 µJ per inference at equal latency; no classical baseline | *full* |
| **Connectome-derived network controlling a robot arm** | — | — | **NOT FOUND** (searched directly) | — |
| **Small insect-derived controller vs a VLA on the same task** | — | — | **NOT FOUND** | — |

**Reading:** measured advantages exist at the level of *ideas* borrowed from the fly and of *hardware*; at the level of
*actual wiring* the evidence is thin, contested and limited to a simulated fly body. The two NOT FOUND rows are where a
careful project could add something — with the caveat that NOT FOUND is a statement about my search.

---

## 6. Answers to the three questions

### 6.1 What the fly lacks that VLA/VFA models have

Language; open-ended object understanding; learning a new skill from demonstrations; multi-minute tasks; transfer across
robots; dexterous manipulation. None of these can be supplied by any fly circuit, and FlyMind does not try. (Literature +
INFERRED.) FlyMind additionally lacks most of what the *fly* has: its visual system, learning, memory, internal states.

### 6.2 What the fly has that they lack

1. **Sensor-to-motor maps that exist without any training** — in the data at three places (D0, VERIFIED at the level of
   wiring; function NOT VERIFIED).
2. **Learning from a single episode** in the animal — VLAs need batch retraining and forget; the circuit is in the data,
   unmodelled (literature + VERIFIED counts).
3. **Reaction in milliseconds at negligible compute** — FlyMind 1.65 ms per tick on a CPU core against 40–300 ms on a GPU;
   VLAs lose most of their success when objects move (VERIFIED for FlyMind; literature for VLAs). No same-machine
   measurement exists yet.
4. **A mechanism one can read** — every neuron and connection identified, against features that mostly memorise
   demonstrations.
5. **Dense touch and body sense** — being added to VLAs now, at 10–100 Hz.

The honest qualifier (INFERRED): items 3–5 belong to any small hard-wired controller, and items 1–2 can be imitated by a
few lines of code. What is specific to the fly is that these properties come *from measured biology* rather than from an
engineer. That is a scientific point, not a performance one.

### 6.3 Can FlyMind turn this into a real, measurable contribution?

**For 1 December — yes, one, and it is narrow.** Not "an advantage over VLA". The contribution I think is real:

> A pre-registered closed-loop test in which a network built from measured fly wiring must, and a shuffled network must
> not, turn *where* a stimulus is into *which way* the arm moves — with a classical map as the ceiling and a slow-policy
> surrogate as the floor.

Why this one: (a) D0 shows the map is in the data; (b) by construction a weight-shuffle destroys it, so for the first time
the shuffle control has teeth; (c) no published connectome-to-robot-arm work with such controls was found; (d) it fits the
existing simulation. What it would establish if it works: real wiring carries a usable function into a robot loop without
training. What it would not establish: superiority over classical code (expected: slightly worse) or over a VLA (untested).

**A second, cheaper contribution:** a three-way capability table (§4) in which every FlyMind cell is a measured number and
every VLA cell is a source read in full — including, if approved, the inference time of a real small VLA on this same Mac.
It is a positioning result, not a win.

**For Explory 2027 (longer horizon):** a matched pair of opposite predictions — the looming map, where wiring should
matter, and the learning circuit, whose input wiring biology itself describes as near-random and where shuffling should
therefore *not* matter. Getting both predictions right would show the method can tell the two cases apart. HYPOTHESIS;
needs plasticity in the model, which touches the "no training" rule (§8).

**My estimate that the answer is "nothing in time":** real. The main experiment needs a new scene, an engineered looming
encoder and about a week of work plus review; with the demo on 1 December and approval not yet given, the margin is thin
(§10.4). Opinion, not measurement.

---

## 7. Devil's advocate — why FlyMind may not turn this into a contribution in time

1. **The "network" in the main experiment is nearly a weighted sum.** LC4 connects directly to DNp02 and DNp11. Feed an
   engineered looming signal into ~126 neurons, read two: a critic will call it a lookup table read from a file. The
   spiking dynamics add delay, not computation.
2. **The result is predictable from D0.** If the gradients are there, data will beat shuffles almost by arithmetic. A test
   whose outcome is known in advance is weak evidence; its value is only that it closes the loop on a robot.
3. **The hard part of looming detection is upstream** (optic lobe, 54 % of the neurons) and would be done by classical code.
4. **Sign and axis are not settled.** Which end of the map is "front" is NOT VERIFIED; the mapping of DNp11/DNp02 to an arm
   direction is an analogy to a fly's takeoff posture.
5. **Classical code will win again**, and the slow-policy surrogate is not a VLA. Any sentence comparing with "VLA" rests on
   a stand-in and published latencies.
6. **Time.** Twenty days, one person-equivalent, approvals pending, poster due on the 16th, two known safety defects open
   (1.89 rad/s; pad penetration). A red-teamed result by 1 December is possible but not likely to have slack.
7. **Everything is simulation**, with ideal images. The earlier project judgment that the first real novelty appears on
   hardware still stands, and hardware is excluded here.
8. **One animal, one hemisphere pair.** D0's replication is left versus right, not fly versus fly.
9. **Fast layers are arriving in VLAs** (tactile correction at 100 Hz and above; purpose-built dynamic models reach 47 %
   where others reach 1–13 %). The gap the fly would fill is closing with learned components.
10. **My own bias.** I proposed this direction yesterday; D0 passing makes it attractive to me. Adam should weigh that.

---

## 8. Conflicts with the owner's principles — stated, not resolved

| Principle (3 November) | Where the conflict is | Options (Adam decides) |
|---|---|---|
| "The fly should control, not the algorithm, even if we lose quality" | The only role in which the fly complements a VLA is a reflex layer *under* a planner — the fly then does not control the task. | **Role A — fly only:** the arm does only what fly circuits decide (track, dodge, close on touch); no pick-and-place; classical code = safety and posture. Consistent with the principle; no useful task. **Role B — reflex under a planner:** useful robot; conflicts with the principle. **Role C — both, each labelled.** The experiment in §10 is the same in all three; only the optional slow-planner arms and the demo framing differ. |
| Natural senses only, no artificial stimulation | No conflict: input is the camera. The looming encoder is ENGINEERING and must be labelled so. | — |
| No tuning or training without consent | (i) Strength-matching of shuffles is calibration; it must be fixed before outcome data. (ii) The learning-circuit idea needs a plasticity rule — the fly's own kind of learning, but still "learning" in the model. | Adam, before any such stage |
| Shuffle wording on the poster undecided | This report states the shuffle facts (§2.2) but writes no poster text. | Adam |

---

## 9. What each outcome would allow FlyMind to say (so results cannot be reinterpreted later)

| Outcome of the main experiment | Allowed statement | Not allowed |
|---|---|---|
| Data beats every shuffle; close to classical | "Measured fly wiring carries a position-to-direction map that works in a robot loop without training; shuffled wiring does not." | "Better than classical", "better than VLA" |
| Data beats shuffles but far below classical | The same, plus the measured cost | Hiding the cost |
| Data does not beat shuffles | "In no task tried has connectome wiring shown a measurable role." The line stops. | Re-running with new parameters until it works |
| Reflex arms beat the slow surrogate | "A fast hard-wired layer helps a slow policy; this is generic, not specific to the fly." | "The fly makes VLA better" |

---

## 10. Proposed plan (nothing starts without approval; S1 and S2 remain unapproved)

General rules for every item: new files only; no shared or protected module modified; no historical result touched;
pre-registration written and hashed before any run; seeds from a new range checked against all registries (19 100 xxx is
consumed); kill criteria fixed in advance; red team after each stage.

### 10.1 Tier 1 — candidates for 1 December

**E1 — spatial-map reflex in closed loop** (this is "S2" of 10 November, refined; needs explicit approval).
- Task: an object approaches the gripper camera from varied directions; the arm must move away in a direction that depends
  on where the object is.
- Network: LC4 → DNp02 / DNp11 from the data (literature-backed meaning; exploratory in D0), with LPLC2 → DNp06 / giant
  fiber as a second, D0-confirmed push–pull pair reported alongside.
- Refinements over the 10 November sketch:
  1. **Non-circular primary metric.** Not "correct direction" (that would use the map to define itself) but *location
     discrimination*: does the decoded output separate stimulus positions along the anterior–posterior axis? The axis is
     fixed from the independent anchor in §5.2 before any run.
  2. **Shuffles get every advantage:** each shuffle is given its own best output sign and gain, chosen on a calibration
     set; the data network gets one fixed setting.
  3. Arms: data; ≥ 20 weight-permuted shuffles; classical map with equal information; no reflex; and — only if Adam wants
     Role B or C — the classical map throttled to two published VLA-class latencies, labelled "slow-policy surrogate".
  4. ~200 paired scenes; exact McNemar and Wilson intervals; analysis clustered by scene family; effect sizes.
- Hypotheses: H1 data ranks first among data + shuffles; H2 data within a pre-set margin of the classical map; H3 (optional)
  reflex arms avoid contact more often than the slow surrogate.
- Kill: H1 fails → the wiring line stops and is reported as negative.

**E2 — is the grasp network just a transfer curve?** (this is "S1"; needs explicit approval). A classical reflex copying
only the network's measured force→torque curve and delay, same 135 trials, soft and stiff contact. Settles the HYPOTHESIS
in §2.3 point 1. About a day.

**E3 — same-machine timing of a real small VLA** (optional; needs approval to download model weights into the existing
LeRobot environment). One number: milliseconds per action chunk on this M1 Max, next to FlyMind's 1.65 ms. No task claim.

### 10.2 Tier 2 — for Explory 2027, not before 1 December

- **L0 (data only):** is projection-neuron → Kenyon-cell wiring in MaleCNS distinguishable from random? A D0-style test
  with a registered prediction ("close to random"), preparing the opposite-prediction pair of §6.3.
- **L1:** a learning-circuit module with a simple dopamine-gated rule — only if Adam accepts plasticity in the model.
- A real small VLA trained on the same simulated task for a true three-way benchmark; hardware, if the rule is lifted.

### 10.3 Not proposed

Weights learned by gradient descent on connectome wiring; any change to protected modules; the 120 Hz loop; new organisms.

### 10.4 Timeline (my estimate, opinion)

Pre-registration 1 day after approval; E2 1 day; E1 scene, encoder and checks 4–5 days, runs 1 day, red team 1–2 days;
demo assembly 2 days. If approval for E1 arrives after about 17 November, I do not expect a red-teamed E1 result by
1 December; the fallback is E2 plus D0 plus the existing stages, honestly labelled.

### 10.5 Open safety items (unchanged, not addressed here)

Joint speed 1.89 rad/s above the 1.5 limit (cause NOT VERIFIED); pad penetration under soft contact.

---

## 11. Limits of this report

- No full text was read for any biology paper; fly facts are from abstracts via Europe PMC. Several VLA papers were read
  only up to a length cut-off; numbers that exist only in figures were not seen.
- Sub-agent reports are model output. I confirmed that arXiv 2606.08881 and 2601.22153 exist with the cited titles; I did
  not re-read their tables.
- One paper title that I supplied to a sub-agent from memory did not exist; it was caught and is not cited here.
  One premise of mine (position-dependent pattern memory) was wrong and is corrected in §5.3.
- §5.2 is exploratory, post-D0, on one animal; "dorsal" rests on the type name.
- The capability table mixes measured cells (FlyMind) with literature cells of uneven quality.
- "NOT FOUND" always describes the search, never the world.
- Estimates of time and likelihood are opinions.

## 12. Decisions for Adam

1. May I write the pre-registration for E1 and E2 (document only)? Running them is a separate approval.
2. Which role for the fly — A, B or C (§8)? Only the optional slow-planner arms depend on it.
3. E3 (model download for a timing measurement): yes or no.
4. Tier 2 (learning circuit, plasticity in the model): keep as an Explory 2027 idea, or drop.

STOPPED AT CHECKPOINT 1 — awaiting Adam's approval.
