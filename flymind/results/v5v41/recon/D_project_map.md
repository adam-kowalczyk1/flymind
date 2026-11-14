# D — FlyMind project map (built from code, 2026-10-30)

Scope: read-only reconstruction of the current FlyMind LC10a → intermediates → DNa02 → SO-101 pan model from source
(`flymind/*.py`) plus recomputation from data files. Numbers marked **[recomputed]** come from helper scripts
`/private/tmp/claude-501/-Users-admin-so101-fly-project/075990a2-3231-4039-8d41-31f3fdcb9204/scratchpad/recon/d_map.py`,
`d_map2.py`, `d_map3.py` (they call `visual_path.network(0.2)`, the encoder and `side_shuffle` helpers only; no MuJoCo,
no runner, no shuffle instances created). Labels: DATA / MODEL / ENGINEERING / CONTROL.

---------------------------------------------------------------------------------------------------------------------
## 1. Connectome data source and provenance

| File (`data/malecns/`) | Bytes | Rows | Columns (pyarrow schema) | Used for |
|---|---|---|---|---|
| `connectome-weights-male-cns-v1.0-minconf-0.5.feather` | 1 051 241 946 | 151 856 684 | body_pre:int64, body_post:int64, weight:int64 | edges (DATA) |
| `body-annotations-male-cns-v1.0-minconf-0.5.feather` | 14 483 314 | 211 577 | 36 cols incl. bodyId, type, instance, somaSide, rootSide, superclass, class, flywireType, hemibrainType, mancType, status, statusLabel, somaLocation … | population selection, side (DATA) |
| `body-neurotransmitters-male-cns-v1.0.feather` | 43 282 834 | 1 835 518 | body, cell_type, total_nt_predictions, predicted_nt_confidence, predicted_nt, ground_truth, celltype_total_nt_predictions, celltype_predicted_nt, celltype_predicted_nt_confidence, consensus_nt | NT → sign (DATA + MODEL) |

[recomputed] Paths are hard-coded in `visual_path.py:28-32`.

- DATA: `weight` = synapse count pre→post, already aggregated by the provider at synapse confidence ≥ 0.5; the threshold
  is known only from the file name and cannot be changed (no confidence column) — `connectome.py:5-11`, enforced in
  `connectome.load_edges` (`connectome.py:72-77`, refuses a different `minconf`).
- DATA: induced subgraph is loaded by streaming filter `body_pre ∈ bodies ∧ body_post ∈ bodies` (`connectome.py:82-86`);
  validation rejects nulls, ids ≤ 0, weight ≤ 0, duplicate pairs (`connectome.py:44-65`).
- ENGINEERING: `provenance()` records path/size/mtime/minconf and optional sha256 (`connectome.py:30-41`); the network
  build does not request sha256 (`visual_path.py:63` calls `load_edges(WEIGHTS, bodies=bodies)` with default
  `sha256=False`), so data-file integrity is not hash-bound inside the build itself (it may be covered by external
  integrity scripts — not verified here).
- Regions (EB/PB/LAL/AOTU…) are not distinguished: weights are summed over neuropils (`visual_path.py:11-12`) — MODEL.

## 2. Network construction (`visual_path.select/network`, `snn_interface.build`)

### 2.1 Populations and selection rule
- Input (DATA, selection = MODEL/exploratory choice): `type == 'LC10a'`, side = `somaSide` (`visual_path.py:39-41,51`).
  [recomputed] **in_L = 135, in_R = 140**. The docstring states LC10a was chosen *after* screening 8 visual types for a
  push-pull 2-hop signature (`visual_path.py:4-7`) — post-hoc, not a hypothesis test.
- Output (DATA): DNa02 L = body 523769, DNa02 R = body 10360, hard-coded and checked against annotations
  (`visual_path.py:34,43-45`). [recomputed] **1 + 1**.
- Intermediates (MODEL selection rule on DATA): any neuron with ≥ s_min = 5 synapses from the whole LC10a population
  (summed over all LC10a) AND ≥ 5 synapses to DNa02 L+R combined, excluding LC10a and DNa02 (`visual_path.py:33,48-50`).
  Side is not part of the rule. [recomputed] **mid = 147 (mid_L 58, mid_R 89 by somaSide)** — note the L/R asymmetry.
- Types of intermediates [recomputed]: LLPC1 43 (L 12 / R 31), AOTU015 8, AOTU001 7, AOTU002_a 5, LAL025 4, AOTU002_c 4,
  AOTU018 4, AOTU016_c/LoVP18/AOTU017/LAL300m/LAL301m/LAL028 3 each, AOTU019 2 (1 L, 1 R), LT51 2, LT82a 2, … plus
  singletons incl. **DNp09** (another descending neuron), **LC19, LC31b** (other lobula columnar types), pIP1, PVLP/AVLP,
  SMP148. Visual types in the mid layer (LLPC1, LoVP18, LT51, LT82a, LC19, LC31b) receive in this model only network input,
  not their real optic-lobe input — MODEL limitation.
- DNa02 input coverage [recomputed, DATA]: total DNa02 L+R input in the whole connectome 49 357 synapses; from the 147 mids
  6 022 (12.2 %). ~88 % of DNa02 input is not modelled (`visual_path.py:11`); no background drive replaces it except ALIF
  current noise (see §3).
- Totals [recomputed]: **424 neurons, 13 510 edges, 113 969 synapses, 0 self-loops, 0 model edges** (`W_model` all zero),
  `W_sha256 = e821b084…5ec40`.

### 2.2 Weight transform and signs
- MODEL: `W[post, pre] = sign[pre] · J0 · f(N)`, `f = identity` for `transform="linear"` (`snn_interface.py:107-112`).
  J0 = 0.2 mV/synapse (`loop.py:51`), chosen by the V4 Part A rule (smallest admissible J0 with DNa02 peak ≥ 20 Hz at
  g = 0.5; `v4_open_loop.py:32-35,94-103`). Synapse count is explicitly not physiological strength (`snn_interface.py:7-8`).
- NT assignment (DATA with MODEL precedence rule): per body, first non-'unclear' of `ground_truth → consensus_nt →
  celltype_predicted_nt` (`snn_interface.py:21,56-73`); missing NT → hard error, overrides need a reason.
  [recomputed] sources: ground_truth 323, consensus_nt 101 (all 101 are mids; their predicted_nt_confidence min 0.709,
  median 0.952; predicted_nt agrees with assigned NT in 100 %).
- Sign map (MODEL): ACh = +1, GABA = −1, **Glu = −1** (GluCl assumption, `snn_interface.py:22-24`); any other NT
  (DA, 5-HT, OA, HA) → error (`snn_interface.py:84-86`).
  [recomputed] NT composition: in_L/in_R 100 % ACh; DNa02 L/R ACh; mid: ACh 140, GABA 5 (AOTU019 L+R [ground_truth],
  VES041, PS002, SMP148 [consensus]), Glu 2 (LT51 L+R [consensus, conf 0.71/0.75]).
  **The Glu = inhibitory assumption touches only 2 neurons, |w| 50.6 mV of 22 793.8 (0.22 %), 2 edges to DNa02
  (−10.4 mV to DNa02_L from LT51 L, −8.2 mV to DNa02_R from LT51 R).** The decisive inhibitory element is GABAergic
  AOTU019 (ground truth): AOTU019_R → DNa02_L −59.4 mV (297 syn), AOTU019_L → DNa02_R −57.8 mV (289 syn) — the single
  strongest input to each DNa02.

### 2.3 Edge counts and |w| mass per block (J0 = 0.2) [recomputed]

Total |w| = 22 793.8 mV.

| Block (pre→post) | Edges | Σ|w| [mV] | |w| share | Σ w⁺ | Σ w⁻ | n⁺ / n⁻ |
|---|---|---|---|---|---|---|
| in→in   | 6 189 | 5 048.8 | 22.15 % | 5 048.8 | 0 | 6189 / 0 |
| in→mid  | 4 750 | 13 813.2 | 60.60 % | 13 813.2 | 0 | 4750 / 0 |
| **in→dn** | **0** | 0 | 0 | — | — | — |
| mid→in  | 310 | 127.2 | 0.56 % | 125.0 | −2.2 | 299 / 11 |
| mid→mid | 2 089 | 2 591.0 | 11.37 % | 2 182.0 | −409.0 | 1915 / 174 |
| mid→dn  | 151 | 1 204.4 | 5.28 % | 1 063.4 | −141.0 | 143 / 8 |
| dn→mid  | 21 | 9.2 | 0.04 % | 9.2 | 0 | 21 / 0 |
| dn→in, dn→dn | 0 | 0 | 0 | — | — | — |

Layer × side detail (edges, signed Σw mV): in_L→in_L 2960 / 2410.8; in_R→in_R 3229 / 2638.0; in_L→mid_L 2189 / 6242.4;
in_L→mid_R **2** / 0.8; in_R→mid_R 2559 / 7570.0; in_R→mid_L **0**; mid_L→dn_L 49 / 460.8; mid_L→dn_R 10 / −4.2;
mid_R→dn_R 76 / 464.8; mid_R→dn_L 16 / 1.0; mid_L→mid_R 151 / 102.6; mid_R→mid_L 151 / −82.0; mid_L→mid_L 593 / 692.4;
mid_R→mid_R 1194 / 1060.0.
DNa02_L input: 65 edges, +533.8 / −72.0 mV (ipsi mid_L +471.2/−10.4; contra mid_R +62.6/−61.6).
DNa02_R input: 86 edges, +529.6 / −69.0 mV (ipsi mid_R +476.0/−11.2; contra mid_L +53.6/−57.8).
Weight distribution: synapses per edge min 1, median 3, max 297; 26 % of edges have 1 synapse, 41 % ≤ 2.

Interpretation (DATA): LC10a are strictly hemilateral at the first hop (only 2 cross-side in→mid edges); there is no
direct LC10a→DNa02 edge; all lateralised drive is 2-hop via mids. 22 % of all |w| is LC10a↔LC10a recurrence
(per-LC10a recurrent input row sum median 17.4 mV, max 30.8 mV — large vs. the 7 mV threshold gap). This collapse of
axo-axonal AOTU synapses into point-neuron excitation is MODEL.

Descriptive lateralization index (`v5v2_topology.lateralization`, `W@W + W`, `v5v2_topology.py:67-75`): 307 437
(2-hop LC10a_L→DNa02 ipsi +74 794, contra −69 554; LC10a_R ipsi +81 216, contra −81 873) [recomputed].

### 2.4 SWS v2 swappability (key = (signed weight, layer_side(pre), layer_side(post)), `side_shuffle.py:58-61`) [recomputed]

638 keys, 338 with ≥ 2 members. "Swappable" = edge in a key of size ≥ 2 (what the runner reports as
`edges_in_swappable_keys`, `side_shuffle.py:84`). "Effective" = key additionally contains ≥ 2 distinct pre AND ≥ 2 distinct
post neurons (necessary condition for any accepted swap, since `b == d` and `(a,d) ∈ exists` reject — `side_shuffle.py:75`);
effective is an upper bound on what can move.

| Block | Edges | Swappable | Effective | Σ|w| | |w| swappable | |w| effective |
|---|---|---|---|---|---|---|
| in→in   | 6189 | 6184 (99.9 %) | 6184 | 5048.8 | 5022.8 (99.5 %) | 5022.8 |
| in→mid  | 4750 | 4672 (98.4 %) | 4617 | 13813.2 | 12245.6 (88.7 %) | 11131.6 (80.6 %) |
| mid→in  | 310 | 307 (99.0 %) | 297 | 127.2 | 123.0 (96.7 %) | 121.0 |
| mid→mid | 2089 | 1965 (94.1 %) | 1937 | 2591.0 | 1527.4 (59.0 %) | 1449.2 (55.9 %) |
| **mid→dn** | 151 | 66 (43.7 %) | **0** | 1204.4 | 148.0 (12.3 %) | **0** |
| **dn→mid** | 21 | 16 (76.2 %) | **0** | 9.2 | 4.6 (50 %) | **0** |
| total | 13510 | 13210 (97.8 %) | 13035 (96.5 %) | 22793.8 | 83.7 % | — |

**SWS cannot change any DNa02 input or output edge** (groups dn_L/dn_R have one neuron each) — the runner's
`edges_in_swappable_keys` (13 210) overstates what can change by 82 edges in DN-adjacent keys. Per-neuron in/out weight
multisets by partner group are preserved (`side_shuffle.py:11-17`, `properties` `side_shuffle.py:98-135`). Because both
encoder sides drive all LC10a of a side with the same current (`encoder.py:71-76`), what SWS effectively changes is *which*
LC10a/mid partners are wired, chiefly the reciprocity of LC10a↔LC10a (saved artifact
`results/v5v3_prep/v5v3_control_check_v2_20261029T165755.json`: recip_LC_LC 2450 → ~560, recip_mid_mid 599 → 249–266,
λ_max 26.07 → 26.3, LI_rel 1.0, changed_frac ≈ 0.67; decomposition shows the LC×LC block alone reproduces the SWS shift
of the DNa02 threshold curve at g = 0.5: 17.0 → 2.8 Hz). CONTROL.

SHUF_STR for comparison (`visual_path.shuffle(equal_weight=True)`, key = signed weight only, `visual_path.py:84-86`)
[recomputed]: 196 distinct signed weights, 45 singletons; 13 465 edges (99.67 %, 95.5 % of |w|) swappable with **no layer
or side constraint** → it can create in→dn and cross-side edges and destroys lateralization (saved
`results/v5v3/analysis_summary.txt`: SHUF_STR LI 0.153–0.322 vs SWS 1.0).

## 3. ALIF neuron (`alif.py`) — MODEL (Shiu et al. 2024 membrane, bio2-style adaptation; `alif.py:20-30`)

Update per dt = 1 ms step (`alif.py:70-84`):
- `g ← g + W·s(t−d) − g·dt/τ_syn` (current-based, mV jump per presynaptic spike), d = round(1.8/1) = **2 steps**
  (ring buffer, `alif.py:35-37,72-73`).
- `v ← v + dt/τ_m·(V_rest − v + gain·(g + I_ext + σξ) − a)`; refractory clamp v = V_reset while ref > 0; spike v ≥ V_th →
  V_reset, ref = T_ref; `a ← a − a·dt/τ_a + b_a·s`.
- Parameters (`alif.py:21-33`): V_rest = V_reset = −52, V_th = −45 → **threshold gap 7 mV**; τ_m 20, τ_syn 5, T_ref 2.2,
  delay 1.8 ms; τ_a 300 ms, **b_a 0.5 mV/spike**; noise σ default 0 but **2.0 in all loop/V4 runs** (`loop.py:50`,
  `v4_open_loop.py:63`); Euler guard dt/τ ≤ 0.5.
- Refractory quantization: ceil(2.2) = 3 blocked steps → **r_max 250 Hz** (`alif.py:9,39-42`).
- [recomputed] Effective noise: σ is i.i.d. per-step current, so membrane SD = 2·0.05/√(1−0.95²) ≈ **0.32 mV** (4.6 % of the
  gap) — "2 mV noise" is much weaker than its name suggests; the network is nearly deterministic and silent at rest
  (blank-image calibration offsets are exactly 0.0, `results/v5v4/run_meta_A_*.json`).
- [recomputed] Adaptation is strong: steady-state a ≈ b_a·r·τ_a = 7.5 mV at 50 Hz, 15 mV at 100 Hz (≥ the gap).
- Equations were transcribed from bio2/snn.py; equivalence was never tested (`alif.py:3,8`). Per-neuron gain = 1, no
  heterogeneity. No synaptic conductances, no compartments.

## 4. Input encoding (`encoder.py`) — MODEL (sensory) + ENGINEERING (camera)

- Chromatic contrast `c = (G − (R+B)/2)/mean luminance`, pixel counted if c > c_min = 0.15 (`encoder.py:62-63`); optional
  3×3 blur (V4 v2 / loop: `blur_px = 3`, `loop.py:52`).
- Left/right "eye" sensitivity `S_L(az) = σ(az/w)`, w = 10°, `S_R = 1 − S_L` (`encoder.py:45-47`).
- Drive per side `g_s = 1 − exp(−Σ c·S_s / e0)`, **saturation constant e0 = 60 px·contrast** (`encoder.py:29,64-66`).
- Current: all LC10a of side s get **I = I_max·g_s, I_max = 12 mV, range [0, 12) mV**, identical for every neuron of a side;
  all other neurons 0 (`encoder.py:30,71-76`). No retinotopy within LC10a.
- [recomputed] LC10a alone cross threshold only for g > 7/12 = 0.583, i.e. Σc·S > 52.5. Saved encoder renders
  (`results/v7_encoder_distance_az_20261029.txt`): at ρ = 0.22 m, az 0° max current 5.67 mV; ρ = 0.28 m, 4.14 mV → below
  the gap at the goal state (dead zone; only LC↔LC recurrence and 0.32 mV noise can lift it).
- [recomputed] Calibration stimulus (`v4_open_loop.spot`, r = 9 px green on grey) gives g = (0.91, 0.91) at az 0 and
  ≥ 0.97 on the ipsi side at ±10°, i.e. **near saturation on both sides** — a very different operating point from the
  closed-loop renders (g ≈ 0.35–0.55 at ρ 0.22–0.28). ENGINEERING/CONTROL mismatch.
- No-image / unusable frame → g = (0, 0) (`encoder.py:52-53`).

## 5. Output decoding

- Open-loop readout used for calibration (`v4_open_loop.OpenLoop.tick`, `v4_open_loop.py:116-123`): DNa02 L/R rates EMA
  τ = 50 ms per 1 ms step; `static_diff` = mean L−R over ticks 25–49 of 50 × 10 ms (250–500 ms) (`v4_open_loop.py:126-132`).
- Calibration `v5v4.calibrate` (CONTROL, `v5v4.py:50-60`): az −30…30° step 10° × ALIF seeds 5001–5003; offset = mean
  static_diff on blank image; slope = LSQ through (0, offset); refused if slope ≤ 2 Hz/rad (`v4_open_loop.py:68`).
  Results: DATA slope 492.12 Hz/rad, offset 0.0; TOY 306.08; STR_OWN 18.4–202.9 (median 124.3)
  (`results/v5v4/analysis_frozen.json` aux.calibration_slopes, run_meta).
- Closed-loop `SteerDecoder` (`decoder.py:67-102`), channels ('DNa02',) only (DNa01 absent), τ_rate 50 ms, readout filter
  τ_s = 0.10 s, gain 2.5 s⁻¹, w_max 1 rad/s (`loop.py:53`): `angle = (d_f − offset)/slope`, `ω = clip(2.5·angle, ±1)`.
- **Discrepancy:** `loop.run_trial` hard-codes `offset = [0.0]` (`loop.py:111`); the offset computed by `calibrate` is
  never passed (`v5v4.py:276-281` passes only `slope`). Harmless for DATA/TOY (measured offset exactly 0.0) and very likely
  for any shuffle (no input ⇒ silent network), but the STR_OWN offsets are not recorded in raw JSONL (`v5v4.py:276`), so it
  is unverified for those instances.
- P controller (CONTROL/ENGINEERING, `loop.py:86-93,133-137`): ω = clip(2.5·EMA_0.1s(gL − gR)/slope_p, ±1), slope_p
  fitted on the same synthetic spots, bypasses the SNN (no threshold, no dead zone).

## 6. MuJoCo integration (`so101.py`, `loop.py`) — ENGINEERING

- Tick 10 ms, 300 ticks = 3 s (`loop.py:54`); physics timestep 1 ms × n_sub 10 per tick (`so101.py:61-62,277-288`);
  SNN 10 × 1 ms steps per tick (`loop.py:141`) with the image of that tick held constant.
- Camera "eye" on the gripper body, fovy 70°, 96 × 128 px (`so101.py:69-72`); ball r 2.5 cm, 50 g, rgba (.1,.7,.2)
  (`so101.py:75-76,120`); arm pose fixed `Q_POSE` except pan (`loop.py:49,145`).
- Pan integration: `pan_t ← pan_t + PAN_LEFT·ω·dt`, PAN_LEFT = −1 (+ω = left = decreasing q) (`so101.py:37,51-53`,
  `loop.py:144`); after safety `pan_t = qt[0]` (anti wind-up, `loop.py:149`). Position servo tracks the target.
- Frame timing: `t_capture = t_receive = d.time` (`so101.py:228`) → sensor age is always 0 in simulation; no camera
  latency except the optional DelayLine dev runs (`loop.py:114,125`).
- Evaluation error = simulator-truth bearing (`loop.py:71-77`), never given to the controller. Metrics: success = all
  |e| < 5° over the last 0.5 s; final_abs_err = mean |e| over the last 0.5 s (`loop.py:166-174`).
- Same ALIF noise seed (= trial seed) for DATA, SWS, STR_* (`loop.py:109`); TOY has a different N so its noise draws differ.

## 7. Safety layer (`safety.py`) — ENGINEERING (classical code, not biology)

Order per joint: range − margin 0.05 rad → rate |Δtarget| ≤ v_max·dt = 1.5 rad/s · 0.01 → lead |target − q| ≤ max_lead
(**pan 0.02 rad**, others 0.3) → range again (`safety.py:39-50,113-134`); vision-stale hold if sensor_age > 0.05 s
(`safety.py:117-119`); fault/cmd-timeout/bad-command → hold (`safety.py:103-111`); source labels mandatory
(`safety.py:99-101`) and per-source flag counts (`safety.py:81-83`). ω_max·dt = 0.01 rad < 0.02 lead, so clipping is rare
(V5 v1: 0 flagged ticks without delay, 3600 with 50 ms delay — `results/v5/analysis_confirm.json`).

## 8. Controls (CONTROL)

| Control | Code | Preserves | Destroys / notes |
|---|---|---|---|
| SWS v2 (SHUF_WITHIN_SIDE) | `side_shuffle.shuffle_within_side`, `side_shuffle.py:47-85`; runner seed +400 000, 5·E swaps (`v5v4.py:260-263`) | edges, synapses, Dale, degrees, in/out strength, per-neuron (partner-group, weight) multisets, group×group block, all DNa02 edges | partner identity within groups; LC↔LC reciprocity (2450 → ~560); cannot touch mid→dn / dn→mid (§2.4) |
| SHUF_STR (equal_weight) | `visual_path.shuffle(..., equal_weight=True)`, `visual_path.py:71-102`; seed +200 000, 10·E swaps, checked by `v5v2_topology.check_shuffle` (`v5v2_topology.py:78-91`) | degrees, in/out strength, Dale, weight multiset | layer and side structure; LI drops to 0.15–0.32 |
| SHUF_DEG | `visual_path.shuffle(equal_weight=False)` | degrees, out-strength, Dale | in-strength too |
| DN-perm | `loop_v2.dn_permute`, `loop_v2.py:52-65` | DNa02 in-strength by sign | lateralization |
| TOY relay | `loop_v2.toy_relay`, `loop_v2.py:68-85` — MODEL edges only: every LC10a → ipsi DNa02 with n_syn = (Σ excitatory DNa02-side synapses in DATA)/n_LC10a[side] (≈ 19.8 syn = 3.95 mV each), no recurrence, own calibration | total excitatory DNa02 drive | everything else |
| P controller | `loop.py:133-137` | — | no SNN |
| Ablations | CUT_LC10a_AOTU, ABL_AOTU019 (`v5v2_topology.py:49-64`), swap sides / no vision / ablate LC10a (`loop.py`, `v4_open_loop.py:110-117`) | — | — |

## 9. Experiments and result files (headline numbers read from saved artifacts, not re-derived)

| Exp. | Script | Results | Headline |
|---|---|---|---|
| V3.1 / V3.2 / V3.4 (EPG ring, MN grip inputs — not in the steering loop) | `v31_reproduce.py`, `v32_bump.py`, `v32_v3_confirm.py`, `v34_grip_inputs.py`, `epg_ring.py` | `results/v31_reproduce_20261028.txt`, `results/v32/*`, `results/v34_grip_inputs_20261028.txt` | outside this map |
| V4 open loop (J0 rule, calibration) | `v4_open_loop.py` | `results/v4/v4_partA_*.json`, `v4_partB_*.json`, `v4_partB_v2_20261028T214641.json` | J0 = 0.2; slope ≈ 495.6 Hz/rad (V4 v2) |
| V5 v1 confirm (seeds 2011–2050) | `loop.py`, `analyze_v5.py` | `results/v5/v5_confirm_*.json`, `analysis_confirm.json` | snn 38/40, P 40/40, shuffle 3/40, swap 0/40 |
| V5 v2 | `loop_v2.py` | `results/v5/v5v2_20261029T065804.json`, `analysis_v5v2_confirm.json` | snn 28/50, eqshuffle 20, dnperm 9, toy 22, P 50 |
| V5 v2 topology (3001–3050) | `v5v2_topology.py` | `results/v5v2_topology/*`, `v5v2_topology_verification.json` | DATA 31/50, SHUF_STR 27, CUT 30, ABL_AOTU019 33, TOY 29, P 50 |
| Ablation / mechanism (dev) | `v5_ablation.py`, `v5_mech_strength.py` | `results/v5_ablation/*`, `results/v5_mech_strength/*` | exploratory |
| V5 v3 (3051–3100) | `v5v3.py`, `v5v3_control_check.py`, `v5v3_gain_check.py`, `v5v3_post_slopes.py` | `results/v5v3/*`, `results/v5v3_prep/*` | DATA−SWS −0.19 [−0.58, 0.16] (equiv.); DATA−STR −2.40 |
| V6 ALIF stability (dev) | `v6_stability.py` | `results/v6_stability/*` | exploratory |
| V7 encoder vs distance | `v7_encoder_distance.py` | `results/v7_encoder_distance*_20261029.txt` | dead-zone explanation (§4) |
| V5 v4 (4001–4450, frozen protocol) | `v5v4.py`, `v5v4_post_sws_slopes.py`, `v5v4_power*.py`, `audit_v5v4_independent.py` | `results/v5v4/analysis_frozen.json`, `raw_v5v4_{A,B}.jsonl`, `run_meta_*`, `post_sws_slopes.txt` | mean |e|: P 0.20°, DATA 2.88°, SWS 3.05°, STR_OWN 4.26°, TOY 4.31°, STR_SHARED 5.66°. H1 S1: d = +0.51 [0.41, 0.61] (SWS better); H1 S2: d = −0.52 [−0.71, −0.33] (DATA better); pooled −0.17. H2a DATA−STR_OWN −1.38; H2b +1.41; DATA−TOY −1.43; DATA−P +2.68. VALID = True |
| Integrity | `integrity_v5v41.py` | `results/v5v41/integrity_baseline.json` | Stage 1 28/28, v5v3/v5v4 manifests OK |

## 10. Known limitations and unresolved scientific questions

1. (DATA/MODEL) 88 % of DNa02 input unmodelled; mids that are visual neurons (LLPC1 ×43, LC19, LC31b, LT51, LT82a, LoVP18)
   lack their real input; DNp09 is in the hidden layer. The selection rule (≥ 5 / ≥ 5, L+R pooled) yields mid_L 58 vs
   mid_R 89 — unexplained asymmetry (proofreading? biology?), not tested.
2. (MODEL) Contralateral DNa02 rate is 0 at all drives in open loop (saved control check: contra = 0.0 at g 0.5–1.0), so
   the data's push-pull (AOTU019 GABA contra inhibition) is functionally invisible — consistent with ABL_AOTU019 not
   hurting (33/50 vs DATA 31/50). Without background DNa02 activity the inhibitory half of the circuit cannot matter.
3. (MODEL) Glu = inhibitory affects 0.22 % of |w|; the sign question that matters is GABA on AOTU019 (ground truth).
4. (MODEL/ENGINEERING) Threshold-dominated regime: 7 mV gap vs 12 mV max drive, e0 = 60 saturation and weak effective noise
   (0.32 mV) create a dead zone at the goal for ρ ≥ ~0.22 m; the SNN is 15× worse than the trivial P controller
   (2.88° vs 0.20°). Any "topology" effect is measured inside this dead-zone mechanics.
5. (CONTROL) Calibration is done in a near-saturated regime (synthetic 9 px spot, g ≈ 0.9 both sides) unlike closed-loop
   images; decoder slope therefore does not describe the loop's operating point; offset is ignored by `loop.py:111`.
6. (CONTROL) SWS can only change partner identity within layer×side groups and never DN edges; what it tests is mainly
   LC10a↔LC10a reciprocity/mid wiring. The V5 v4 result is a **stratum-dependent sign reversal** (S1 SWS better,
   S2 DATA better), already visible in V5 v3 bands (+0.53 near, −1.02 mid). Plausible but untested mechanism: SWS raises the
   DNa02 recruitment threshold (17 → ~3 Hz at g 0.5) → less overshoot when near (S1), bigger dead zone when far (S2).
   This is a gain/threshold effect, not evidence that connectome topology confers a control advantage.
7. (CONTROL) SHUF_STR destroys lateralization, so DATA vs SHUF_STR (H2) confounds topology with lateralization.
8. (MODEL) ALIF equations transcribed from bio2 without equivalence test; neuropil compartments collapsed; uniform per-side
   input to all LC10a (no retinotopy) makes LC10a statistically exchangeable within a side.
9. (ENGINEERING) Sim frames have zero sensor age; no camera latency/exposure; only pan is controlled; physical servo
   calibration not modelled.
10. Open: is the S1/S2 crossover robust to e0, I_max, σ, b_a (V6 explored ALIF only on dev seeds)? Would adding background
    DNa02 drive (to make inhibition observable) change H1? Why mid_L ≠ mid_R in count?
