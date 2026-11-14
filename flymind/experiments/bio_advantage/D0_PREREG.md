# D0 — pre-registration: are there spatial sensorimotor maps in the MaleCNS wiring? (data only)

Written 2026-11-11 **before** the analysis script was run. Owner approval for Stage D0: chat message "Tak, zacznij D0"
(2026-11-11), following `flymind/reports/bio_advantage_research_20261110.md` §10. Author: Claude (Fable 5.2).

Scope: graph statistics on the three MaleCNS v1.0 files. **No simulation, no neuron dynamics, no robot, no training, no
commit.** No existing file is modified. Outputs go only to `flymind/results/bio_advantage/d0_v1/`.

The SHA-256 of this file is recorded in `PREREG_SHA256_before_run.txt` and the script refuses to run if it differs.

## 1. What I have already seen (so the reader can judge what is truly confirmatory)

- Seen on 2026-11-10 (exploratory): per-neuron gradients for **LC4** → DNp01, DNp02, DNp04, DNp11 in both hemispheres.
  LC4 results are therefore **exploratory** here and cannot pass the confirmatory rule.
- Seen: only the **total** synapse counts for LPLC2 → DNp01/04/06 and LPLC1 → DNp03/06/11. Their per-neuron gradients
  have **not** been looked at. These are the confirmatory set.
- Not seen at all: anything in D0-b (LC10a path) and D0-c (bristle types → motor pools).

## 2. Data and definitions (fixed)

- Files: `data/malecns/body-annotations-male-cns-v1.0-minconf-0.5.feather`,
  `body-neurotransmitters-male-cns-v1.0.feather`, `connectome-weights-male-cns-v1.0-minconf-0.5.feather`; hashes must equal
  those in `results/vision_manipulation/FREEZE_v3.txt`.
- A population = all bodies whose `type` equals the name exactly, split by `somaSide` (L, R).
- For a visual population on side s and a descending type, the target neuron is whichever of the two neurons of that type
  receives more synapses from that population (recorded in the output).
- **Retinotopic position** of a neuron: synapse-weighted mean of (`assignedOlHex1`, `assignedOlHex2`) over its presynaptic
  partners that have both coordinates. Method A (direct) is used for a population if at least 80 % of its neurons have
  ≥ 20 such input synapses; otherwise method B: positions are first computed by method A for every presynaptic partner of
  the population, and the neuron's position is the synapse-weighted mean of its partners' positions (partners without a
  position ignored; a neuron needs ≥ 20 synapses from positioned partners). Neurons below the threshold are excluded and
  counted. Which retinal direction each hex axis corresponds to is unknown to me, so the statistic below is axis-agnostic.
- **Gradient statistic R**: multiple correlation between the rank of a per-neuron quantity y and position, from the
  least-squares plane rank(y) ~ a·h1 + b·h2 + c. Reported with the direction angle atan2(b, a).
- **Null**: 10 000 random permutations of y across the neurons of the same population and side (this is the same as
  permuting synaptic weights within one pre-type → post-neuron block). p = (1 + #{R_null ≥ R_obs}) / 10 001.
- RNG seeds: range **19 100 000 – 19 100 999** reserved for D0 (not present in any registry or file under `flymind/` on
  2026-11-11); see `SEED_REGISTRY.md` in this folder.

## 3. D0-a — looming pathways (primary, decides the spatial-map line)

y = number of synapses from each visual neuron onto the target descending neuron (0 if no edge).

**Confirmatory pairs (5):** LPLC2 → DNp04, LPLC2 → DNp06, LPLC1 → DNp03, LPLC1 → DNp06, LPLC1 → DNp11.

- **Rule for one pair:** PASS if p < 0.01 in the left **and** in the right hemisphere.
- **H-a (line-level):** at least one of the five pairs passes. Under independence the chance of a false pass is about
  5 × 0.01² = 0.0005.
- **Kill criterion:** if no pair passes, the spatial-map line has no confirmatory support in this dataset. I will say so
  and recommend not building Stage S2; the LC4 observation then stays an unconfirmed exploratory result.

**Secondary (reported, do not change the verdict):**
- "Opposite gradients": for each visual type and side, Spearman ρ between per-neuron counts onto each pair of its targets,
  permutation p (10 000). A push–pull read-out for S2 needs one pair with ρ < 0 and p < 0.01 in both hemispheres.
- Exploratory repeats: LC4 → DNp01, DNp02, DNp04, DNp11. Negative-control-style report: LPLC2 → DNp01 (the literature
  expects the giant fiber not to encode direction; no prediction is registered).
- Sensitivity: (i) y = fraction of the neuron's total output synapses instead of the count; (ii) inclusion threshold 50
  instead of 20.

## 4. D0-b — does the LC10a → DNa02 path used by FlyMind carry position, or only side?

- Network: exactly the project's `visual_path.network(J0=1.0)` (135 + 140 LC10a, intermediates, DNa02 L/R; signs from the
  project's default sign map — a **model assumption**, glutamate = −1).
- y_i (primary) = signed two-hop weight of LC10a neuron i onto the same-side DNa02 minus onto the opposite-side DNa02,
  i.e. (W·W)[DNa02_ipsi, i] − (W·W)[DNa02_contra, i]. Paths longer than two hops are ignored.
- **H-b:** R between y and position has p < 0.01 in both hemispheres.
- Reading fixed in advance: pass → the path may encode *how far* to turn, a retinotopic encoder is worth testing;
  fail → the path encodes side only, and a retinotopic encoder would not help the existing V5 loop.
- Also reported: the same with unsigned weights; the coefficient of variation of y; the number of zero-sign neurons.

## 5. D0-c — do different leg-bristle types reach different motor pools?

- Circuits: the project's `leg_circuit.select("T2", side)` for side L and R (two sides = internal replication); raw
  synapse counts from `connectome.load_edges` (unsigned — no transmitter-sign assumption).
- Bristle neurons = sensory group "mechanosensory bristle"; bristle types = their `type` label, types with ≥ 8 neurons on
  that side. Motor pools = motor-neuron `type` labels.
- Path weight from bristle b to motor neuron m = direct synapses + Σ over all other circuit neurons k of
  count(b→k) · count(k→m). For each bristle type, the weights are summed over its neurons and over each pool and
  normalised to a distribution over pools.
- **Statistic S** = mean pairwise Jensen–Shannon divergence (base 2) between the bristle types' distributions.
- **Null:** degree-preserving double-edge swaps on the circuit's count matrix using the project's own
  `visual_path.shuffle(…, equal_weight=False)`; 100 shuffles, seeds 19 100 101 – 19 100 200. If one shuffle takes longer
  than 60 s, only the first 20 are run and this is stated.
- **H-c:** S_data is larger than every shuffled S on **both** sides.
- Secondary: label-permutation null (10 000). Caveat registered now: bristle types were defined partly by connectivity,
  so a significant label-permutation result is expected and carries little weight; the shuffle null is the test.
- Secondary: for the two pool groups used by `fly_jaw.py` (PRESS = "Ti extensor MN"; RELEASE = "Ti flexor MN",
  "Acc. ti flexor MN"), the per-type index (press − release)/(press + release) and its range.
- Limitation registered now: the data do not tell me where on the leg each bristle type sits.

## 6. What D0 cannot show, whatever the outcome

Synapse counts are not physiological strength; transmitter signs are predictions; one animal; no dynamics. A PASS means
"the wiring contains a spatial pattern beyond chance", not "the pattern controls behaviour" and not "an advantage".

## 7. Reporting

All tests, including failures, are reported in `D0_REPORT.md` with the raw output file path and SHA-256. Thresholds and
definitions in this file are not changed after the run; any deviation is listed under "Deviations".
