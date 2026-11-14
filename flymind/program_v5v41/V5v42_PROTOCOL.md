# V5 v4.2 — Single-block connectivity controls (EXPLORATORY) — protocol r1, 2026-10-30 ~08:50
Written before ANY V5 v4.1 result was inspected (only the instance checks of v4.1 had been read). No confirmatory decision.

## 1. Question
SWS v2 changes partner identity inside four connectivity blocks at once. Which block(s) carry any DATA vs SWS difference in the
open-loop response: LC10a×LC10a, LC10a→intermediate, intermediate→LC10a, intermediate×intermediate — or does it require a
combination? This does not isolate single graph statistics (reciprocity, triangles, clustering, assortativity change together
inside a block); it isolates WHICH EDGES are randomised.

## 2. Controls (CONTROL; `flymind/block_shuffle.py`, tests `test_block_shuffle.py` 7 checks)
Rule = SWS v2 restricted to one block: double edge swaps inside keys (signed weight, layer×side group of pre, of post) and only
among edges whose (layer(pre), layer(post)) is in the block; edges outside the block are bit-identical to DATA (checked per
instance). 5 swaps per block edge; attempt cap 10× target (block LC→mid cannot reach its target under the SWS cap 3× because
the block is dense; per-block changed-edge fraction is then equal to what SWS itself achieves in that block: 0.52 vs 0.51–0.52).
| Family | Block | Edges (|w| share) | Seeds (registry) |
|---|---|---|---|
| B1 | LC10a → LC10a | 6189 (22.2 %) | 8 421 001–050 |
| B2 | LC10a → intermediate | 4750 (60.6 %) | 8 422 001–050 |
| B3 | intermediate → LC10a | 310 (0.6 %) | 8 423 001–050 |
| B4 | intermediate → intermediate | 2089 (11.4 %) | 8 424 001–050 |
| B5 | all blocks (= SWS v2 rule; bit-identical to `shuffle_within_side` for the same seed, test T1) | 13 338 | 8 425 001–050 |
Reference families reused from V5 v4.1 (same networks, same noise seeds, same schedules — no re-simulation): DATA, SWS
(8 410 001–050). Edges to/from DNa02 (mid→DNa02 151, DNa02→mid 21) cannot change under any family (1-neuron groups).
Preserved in every family (checked per instance with `side_shuffle.properties`, 17 keys): neuron/edge/synapse counts, weight
multiset, Dale, per-neuron in/out degree and strength, per-neuron (partner group, weight) multisets, group×group block sums.

## 3. Structural characterisation (before any dynamics; `v5v42.py --structure` → structure.json)
Per instance (all families + DATA + SWS): whole-network reciprocal pairs, triangles (undirected), average clustering, degree
assortativity (out→in, in→in, out→out over edges), number of strong / weak components and largest strong component; LC×LC block:
edges, |w|, reciprocal pairs, triangles, clustering; mid×mid: reciprocal pairs, triangles; LC↔mid: reciprocal pairs (LC→mid edge
with the reverse mid→LC edge); |w| per block; strongest-edge preservation (top 1 % / 5 % |w| DATA edges at the same position);
changed-edge fraction per block. Known non-preservable: B2 or B3 alone change LC↔mid reciprocal pairs (involve both blocks);
B1 changes LC×LC reciprocity, triangles and clustering together (not separable by this design).

## 4. Dynamics (unchanged engine `v5v41.simulate`, ALIF noise 2 mV, seeds 8 411 001–008, CRN)
E1 (unilateral step, 49 levels 4–12 mV, 8 reps), E1n0 (noise 0, 1 rep), E6 (symmetric I0 ± δ/2, I0 4–11 mV, δ ±2 mV, 8 reps) —
identical definitions to V5 v4.1 and amendment A1.

## 5. Analysis (pre-specified, descriptive)
- Per family F and metric m (E1: DNa02 ipsi, LC10a ipsi, mid ipsi steady state, decoded angle; thresholds I_th10, I_th30, I_lc1;
  E6: small-signal gain G_small per I0): Δ_F = mean over F instances − DATA, hierarchical bootstrap CI95 (as V5 v4.1, RNG
  8 419 010), DATA's rank in the F distribution; also F vs SWS (difference of family means; bootstrap over instances of both).
- Attribution rule (written now): a block "reproduces" the SWS effect if its Δ CI overlaps the SWS Δ and excludes 0 with the same
  sign; "does not contribute" if its Δ CI includes 0 and is narrower than |Δ_SWS|; otherwise "partial / unresolved".
- Additivity check: Σ_{B1..B4} Δ_F vs Δ_SWS (and vs Δ_B5) per level; non-additivity → interaction between blocks.
- Structure–function (descriptive): across all block-family instances, Spearman of ΔDNa02 (6–9 mV) with LC×LC reciprocal pairs,
  LC×LC triangles, LC↔mid reciprocal pairs, mid×mid triangles (bootstrap CI over instances, RNG 8 419 011); confounded statistics
  are reported as confounded.
- B5 vs SWS: distributions should agree (same rule, different seeds) — a check of the re-implementation and of seed-to-seed spread.

## 6. Stop rules / outputs
STOP on Stage 1 ≠ 28/28, protected-file change, property failure, outside-block change, incomplete swaps, duplicate W.
Outputs `results/v5v42/` (structure.json, config.json, raw/*.npz, analysis*.json, figures/, REPORT.md). All instances reported.
