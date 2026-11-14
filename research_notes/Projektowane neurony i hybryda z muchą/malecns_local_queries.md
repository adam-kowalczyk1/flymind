# Topic 3b: what of the brain / VNC division is available in the LOCAL MaleCNS v1.0 data (read-only queries, 2026-11-13)

All numbers below are VERIFIED: computed by us from the local Feather files with the scripts in `SCR` = `/private/tmp/claude-501/-Users-admin--claude-spares-spare-72aeAc/18088efc-118a-40f7-a6fd-25f3036bed30/scratchpad/malecns_queries/` (stdout saved next to each script as `*.out`; scripts are also appended at the end of this file in case the scratchpad is cleaned). Data: `body-annotations-...-minconf-0.5.feather` (211,577 rows), `body-neurotransmitters-...feather` (1,835,518 rows), `connectome-weights-...-minconf-0.5.feather` (151,856,684 rows). Python: `/Users/admin/so101_fly_project/.venv/bin/python -I -B`. No repo file was modified. No web was used.

Conventions / traps found while querying (apply to everything below):
- The weights file refers to many bodies that are NOT in the annotations file: 133,806,112 of the 303,713,368 edge endpoints (44%) are not annotated bodies (unproofread fragments / small segments). I call them `not_in_annotations`. They take most DN output at weight >=1 (see c). Always say which threshold and which denominator you use.
- Side of a motor neuron is `somaSide`; `rootSide` is empty for all MNs and for all DNs (same convention as `flymind/leg_circuit.py`). Leg MNs are `superclass == vnc_motor` with `exitNerve` in ProLN (T1), MesoLN (T2), MetaLN (T3).
- `class` is empty (NaN) for all DNs and all MNs; the useful field is `type` plus `subclass`.
- Synapse "weight" = synapse count per neuron pair. Edge threshold t means a pair needs >= t synapses.

## a) Counts by superclass; DNs by side; distinct DN types

### Takeaway
The data fully separate "brain-to-VNC command" (1,314 DNs, 480 named types, L656/R648/M10) from "VNC premotor" (13,161 vnc_intrinsic) from "VNC motor" (708 vnc_motor, leg 319), with 1,846 ascending neurons as the return path. So the brain/VNC split is a first-class annotation in this dataset, and 44,877 bodies have no superclass at all.

### Cited Findings
- Superclass counts (`SCR/q1_annotations.py`, out `q1_annotations.out`): ol_intrinsic 89,403; NaN 44,877; cb_intrinsic 32,164; **vnc_intrinsic 13,161**; visual_projection 9,201; vnc_sensory 6,370; ol_sensory 6,098; cb_sensory 4,868; **ascending_neuron 1,846; descending_neuron 1,314; vnc_motor 708**; visual_centrifugal 563; sensory_ascending 537; **cb_motor 107**; vnc_efferent 94; cb_endocrine 72; ENS 50; vnc_tbc 38; vnc_sensory_tbc 36; vnc_endocrine 22; cb_sensory_tbc 14; sensory_descending 12; efferent_ascending 8; efferent_descending 4; cb_efferent 4; visual_projection_tbc 2; sensory_ascending_tbc 2; descending_neuron_tbc 2. VERIFIED.
- DNs: 1,314 bodies; somaSide L 656, R 648, M 10; `nunique(type)` = **480** (4 DN bodies have no type; nunique ignores them). rootSide and class are NaN for all DNs. VERIFIED.
- ANs: 1,846 bodies, 567 distinct types, somaSide L 930 / R 907 / M 9. VERIFIED.
- vnc_motor 708: L 355 / R 353; by exitNerve: MesoLN 116, MetaLN 122, ProLN 81, AbN4 72, AbNT 64, AbN2 44, AbN1 30, ADMN 28, AbN3 28, DProN 28, ProAN 24, VProN 22, MesoAN 19, PDMNa 16, PDMNp 6, CvN 4, DMetaN 4. By subclass: ad 214, fl 135, hl 130, ml 116, wm 67, nm 24, hm 16, xm 6. VERIFIED.
- cb_motor 107 (brain-side MNs): exitNerve PhN 40, MxLbN 26, CvN 20, AN 15, ON 5, none 1; L 54 / R 53. VERIFIED.

### Inferences
- INFERRED: the DN count (1,314 with 656+648 on the two sides) is a bilateral population, so "DNa02 left minus right" in FlyMind is one pair out of ~657 DN pairs; the read-out is a very narrow slice of the DN population.

### Gaps
- 9 DN bodies carry the note "does not reach the VNC" (see h), so the true DN count is slightly lower than 1,314. The 44,877 NaN-superclass bodies were not examined.

## b) Leg motor neurons: neuromere x side, exitNerve, joint-like names; T2 left and T1 left tables

### Takeaway
Leg MNs: 319 (T1 81, T2 116, T3 122), mirror-symmetric (T2 58+58). 79% of T2 MNs and 100% of T1-left MNs carry a muscle/joint name (Tr, Fe, Ti, Ta, ltm, rotator, ...); the other T2 MNs are numbered `MNml..`. Annotation gaps: no tarsus-named MNs in T2/T3, and the 'fl' subclass has 54 MNs outside the leg nerve.

### Cited Findings
- Leg MN counts by exitNerve / somaSide / neuromere (`SCR/q2_legmn.py`, `q2_legmn.out`): ProLN L 41 / R 40 (all T1, subclass fl); MesoLN L 58 / R 58 (all T2, subclass ml); MetaLN L 62 / R 60 (all T3, subclass hl). Total 319. VERIFIED.
- Total subclass `ml` = 116 = exactly MesoLN L+R, so the T2 leg selection by nerve is complete for ml. But `fl` = 135 while ProLN has only 81: 54 fl MNs exit by DProN 8, ProAN 24, VProN 22 (non-leg nerves, `q1_annotations.out` crosstab); and `hl` = 130 vs MetaLN 122: 8 hl exit by AbN1. So selecting T1 or T3 legs by exit nerve alone may miss MNs of the same neuromere. VERIFIED (counts); what those 54 do is NOT VERIFIED.
- Named-by-muscle share (keyword grouping, `SCR/q3_jointgroups.py`, `q3_jointgroups.out`): T1 L 100% / R 95% (2 MNs have no type); T2 L 79.3% / R 79.3% (12 of 58 are numbered MNml29/77-82); T3 L 82.3% / R 83.3% (3+3 no type, 8+7 numbered MNhl). VERIFIED.
- **T2 left (58 MNs; the leg FlyMind uses)**, by type name (count): Tr flexor 7; Ti flexor 5; Acc. ti flexor 6; Ti extensor 2; Tr extensor 2; Acc. tr flexor 2; Fe reductor 3; Sternotrochanter 2; Pleural remotor/abductor 3; Sternal adductor 1; Sternal anterior rotator 2; Sternal posterior rotator 4; Tergotr. 1; ltm MN 3; ltm1-tibia 1; ltm2-femur 2; numbered MNml78 4, MNml80 3, MNml29/77/79/81/82 1 each (12). VERIFIED.
- T2L joint-like groups (grouping is my keyword rule in q3): coxa-level (remotor/rotator/adductor/tergotr.) 11; trochanter/femur (Tr flexor/extensor, Acc.Tr, Sternotr., Fe reductor) 16; femur-tibia (Ti flexor/extensor, Acc.Ti, ltm1-tibia) 14; long tendon muscle (ltm, ltm2-femur) 5; **tarsus 0**; numbered, no muscle name 12. VERIFIED (counts under that rule).
- **T1 left (41 MNs)**: Acc. ti flexor 10; Acc. tr flexor 3; Fe reductor 4; Ta depressor 5; Ta levator 2; Ti extensor 2; Ti flexor 5; Tr extensor 1; Tr flexor 1; ltm MN 4; ltm1-tibia 2; ltm2-femur 2. Groups: femur-tibia 19; trochanter/femur 9; ltm 6; **tarsus 7**; coxa-level named 0. VERIFIED.
- Distinct leg-MN type names across all three legs (34): Acc. ti/tr flexor, Fe reductor, Pleural remotor/abductor, Sternal adductor/anterior rotator/posterior rotator, Sternotrochanter, Ta depressor, Ta levator, Tergotr., Ti extensor/flexor, Tr extensor/flexor, ltm, ltm1-tibia, ltm2-femur plus numbered MNml29, 76-83 and MNhl29, 59, 60, 64, 65, 87, 88. VERIFIED.

### Inferences
- INFERRED: tarsus-named MNs appear only in T1 (7+7). T2 and T3 have none by name. Either they are among the numbered MNml/MNhl, or they are not annotated; the data do not say. Anything FlyMind would call "gripper = claw/tarsus MN" in T2 cannot be selected by name.
- INFERRED: T1 has 0 coxa-named MNs on ProLN, which fits the 54 fl MNs on other nerves (gap above), but this link is not shown.
- INFERRED: flexor/extensor pairs (Ti flexor 5 + Acc. ti flexor 6 vs Ti extensor 2 on T2L) are the nearest anatomical analogue of an antagonist pair (like a joint open/close), but this is name-based, not tested for function. HYPOTHESIS: T2L Ti flexor+Acc.Ti group vs Ti extensor group is the natural "two-neuron-group per joint" analogue of the pos/neg joint pairs seen in the inspiration video.

### Gaps
- Muscle identity/function comes from the names only. The leg-region-to-SO-101-joint mapping is not in the data.

## c) Where DN output goes; what feeds leg MNs; DNa02, DNa01, DNp09

### Takeaway
Direct DN-to-MN contact is a small minority: DNs put 2.0% of all their synapse weight (5.6% of weight onto annotated targets; 5.7% at edge threshold >=5) directly on vnc_motor. The bulk goes to vnc_intrinsic (14.8% / 41.9% / 38.4%) and the brain-side (cb_/ol_/visual_ 21-25%), and ~65% at threshold 1 goes to unannotated fragments. Leg MNs get 84-88% of input from vnc_intrinsic and only 6-7% directly from DNs (T2L), 2% from sensory. The three FlyMind-relevant DNs hardly touch leg MNs directly.

### Cited Findings
- DN output by postsynaptic superclass, threshold 1 (`SCR/q4_scan.py` then `q4_report.py`, `q4_report.out`; total 11,578,566 synapses): not_in_annotations 64.6%; vnc_intrinsic 14.8%; cb_intrinsic 7.5%; descending_neuron 5.2%; ascending_neuron 3.7%; **vnc_motor 2.0%** (229,565); cb_motor 1.0%. VERIFIED.
- Same, annotated targets only (`q6_annotated_only.out`; total 4,102,860): vnc_motor 5.6%; vnc_intrinsic 41.9%; ascending (AN + sensory_ascending + efferent_ascending) 10.6%; brain-side cb_*/ol_*/visual_* 25.4%; DN-to-DN 14.6%. VERIFIED.
- Same at edge threshold >=5 (`SCR/q6_scan_thr.py 5`, `q6_report_thr5.out`; total 3,694,203): vnc_intrinsic 38.4%; cb_intrinsic 17.2%; DN 13.7%; not_in_annotations 9.8%; AN 9.4%; **vnc_motor 5.7%** (211,149); cb_motor 2.8%. VERIFIED.
- DN input (thr 1): cb_intrinsic 55.6%, DN 12.2%, AN 11.6%, visual_projection 5.9%; vnc_intrinsic only 3.0%. So DNs are fed from the brain (and ANs), as expected. VERIFIED.
- Input to **T2L leg MNs** (thr 1, 225,935 syn): vnc_intrinsic 84.1%; descending_neuron 6.4%; not_in_annotations 4.4%; ascending_neuron 2.5%; vnc_sensory 2.3%; vnc_motor 0.2%. At thr >=5 (198,864 syn): vnc_intrinsic 88.4%; DN 6.7%; AN 2.5%; vnc_sensory 2.1%. VERIFIED.
- Input to **T1L leg MNs** (thr 1, 61,567): vnc_intrinsic 77.4%; DN 8.8%; not_in_annotations 7.5%; AN 4.0%; vnc_sensory 2.0%. thr>=5: 84.3 / 9.6 / AN 3.9 / sens 1.6. All leg MNs (904,684): vnc_intrinsic 82.5%, DN 6.2%, AN 2.5%, vnc_sensory 2.3%. VERIFIED.
- **DNa02** (`SCR/q5_dn_types.py`, `q5_dn_types.out`): 2 bodies (1 L, 1 R); output 47,622 syn, of which 69.6% to unannotated fragments, vnc_intrinsic 16.7%, cb_intrinsic 5.5%, vnc_motor 3.2%. Top typed post types (syn): IN08A006 899; Sternal anterior rotator MN 776; IN19A003 629; IN13B001 483; PS137 379; INXXX468 370; IN04B081 316; DNge026 274; IN07B006 273 (the largest bucket is "no type" 33,235). Direct onto leg MNs (thr 1): T2L 161 syn onto 8/58 MNs (from 1 DN body); T1L 87 (6/41); T3L 201 (9/62); T2R 170 (8/58); any leg MN 888 (Sternal anterior rotator MN 567, Fe reductor MN 133, MNhl59 64, Pleural remotor/abductor 45, Ti flexor 22). VERIFIED.
- **DNa01**: 2 bodies; output 40,323 (70.5% unannotated, vnc_intrinsic 24.4%, vnc_motor 1.2%). Top typed: IN12B003 503; IN07B104 410; IN01A038 347; IN09A002 290; IN21A003 277; IN21A011 276; INXXX464 259; IN13B006 246; IN07B009 238. Direct: T2L 64 syn onto 16/58; any leg 426 (Pleural remotor/abductor 138, Fe reductor 92, Ti flexor 84, Sternal posterior rotator 52). VERIFIED.
- **DNp09**: 2 bodies; output 39,234 (75.8% unannotated, vnc_intrinsic 9.2%, cb_intrinsic 5.8%, ascending 4.3%, DN 4.2%, vnc_motor 0.2%). Top typed: IN07B006 314; DNa11 222; CB0397 214; DNg100 214; AN06B088 201; IN06B030 158; DNg75 149; DNg52 138; AN08B100 137. Direct to leg MNs: T2L 2 syn onto 1 MN; T2R 16 (3 MNs); T1/T3 0; any leg 18 (MNml81 10, Tr flexor 4). Any vnc_motor 93 (tpn MN 32, MNad34 18). VERIFIED.
- Top DNs by direct synapses onto T2L MNs (thr >=5): DNg105 (R) 1,707; DNge079 (L) 1,320; DNg93 (R) 1,004; DNg74_b (R) 613; DNg108 (R) 516; DNg74_a (R) 506; DNge059 (L) 472; DNge035 (R) 396 (`q7_hops_nt_an.out`). VERIFIED. DNa02 does not appear in that top 8.

### Inferences
- INFERRED: in this data a DN is mostly a hub into premotor interneurons, not a motor-neuron driver. Even for DNa02 (a "steering" DN) the single largest typed motor target is a coxa-level rotator MN (Sternal anterior rotator MN 776 syn), which is anatomically consistent with leg-base rotation; this is about the leg only, not about the SO-101 base pan.
- INFERRED: leg MNs are driven 84-88% by VNC interneurons, so "the VNC does the translation from command to joint torque" is what the connectome says. Direct touch/proprioceptive input to MNs is ~2%: a hybrid that wires sensors straight to MNs would not mimic the fly.
- INFERRED: the large unannotated-fragment bucket (65% of DN output at thr 1, 10% at thr >=5) means the proofreading coverage of DN output is incomplete; any "fraction" at thr 1 is distorted by it.

### Gaps
- Brain-side vs VNC-side location of a synapse is not in these three files (no ROI). "cb_intrinsic target" is the best proxy for DN output made in the brain. No per-ROI split was done (it would need syn-points, 13 GB).

## d) Hop structure: DNs reaching T2L MNs

### Takeaway
At edge threshold >=5, 87 DNs (78 types) touch T2L MNs directly, but 887 of 1,314 DNs (67.5%; 413 types) reach them in two hops through 1,114 vnc_intrinsic premotor neurons. So almost every DN is "within two hops" of the leg, and reachability alone is non-selective.

### Cited Findings (`SCR/q7_hops_nt_an.py`, `q7_hops_nt_an.out`; T2L = 58 MNs; DN = superclass descending_neuron)
- thr >=1: 1-hop DNs 135 (121 types); premotor INs 1,570; 2-hop DNs 1,188 (473 types); 2-hop-only 1,053. VERIFIED.
- **thr >=5**: 1-hop DNs 87 (78 types); premotor vnc_intrinsic with >=5 syn onto a T2L MN 1,114; DNs with >=5 syn onto one of those INs 887 (413 types); 2-hop only (not 1-hop) 800; 1-hop DNs are a subset of the 2-hop set, so 1-or-2-hop = 887 of 1,314. 49 of 58 T2L MNs receive >=5 syn from at least one DN directly. VERIFIED.
- thr >=10: 1-hop 69 (66 types); premotor INs 909; 2-hop 683 (349 types). VERIFIED.
- Specific DNs at thr >=5: DNa02 1 of 2 bodies 1-hop, 2 of 2 2-hop; DNa01 1/2 and 2/2; DNp09 0/2 and 2/2. VERIFIED.

### Inferences
- INFERRED: the 2-hop count does not weight the path (no minimum total path strength, no sign), so it is an upper bound on influence, not a measure of control. For a causal claim one needs path-weighted influence or a perturbation test.
- INFERRED: DNp09 reaches the leg only through the VNC interneurons, so any claim "DNp09 drives leg MNs" must be via INs. Same holds for the 2 DNa02 and DNa01 bodies, except 1 body each with a small direct input.

### Gaps
- Only 2 hops and only T2L. 3-hop reachability, and the path-weighted/signed version, were not computed.

## e) Neck MNs and other non-leg MNs; possible analogies

### Takeaway
Non-leg MNs are well annotated: neck 24 (VNC `nm`) + 20 brain-side CvN, wing 67, haltere 16, abdominal 214, proboscis/pharynx 66 (PhN 40, MxLbN 26). Nothing is a gripper in the fly. The closest anatomical analogies are by function only and are INFERRED.

### Cited Findings (`SCR/q8_nonleg_search.py`, `q8_nonleg_search.out`)
- vnc_motor non-leg: **nm (neck motor) 24** (L12/R12, all T1 neuromere; exit DProN 20, CvN 4; types MNnm03/07,12/08/09/10/11/13/14, ADNM1 MN, ADNM2 MN, FNM2); **wm (wing motor) 67** (L33/R34; ADMN 28, MesoAN 19, PDMNa 14, PDMNp 6; DLMn, DVMn 1-3, STTMm, TTMn and named wing steering MNs hg1-4, i1, i2, iii1, iii3, b1-3, ps1, ps2, tp1, tp2, tpn); **hm (haltere) 16** (L8/R8, T3, exit AbN1; hi1, hi2, hiii2, hDVM, MNhm03/42/43); **xm 6** (MNxm01-03; exit DMetaN 4, PDMNa 2); **ad (abdominal) 214** (A1 56, A2 28, A3/A4 22 each, ... exit AbN1-4, AbNT). VERIFIED.
- cb_motor 107 by nerve: PhN 40 (types include MN3L, MN3M, MN5, MN9, MN10, MN11D/V, MN12D, MNx01-05, CEM), MxLbN 26 (MN1, MN2Da, MN2Db, MN2V, MN4a, MN4b, MN6, MN7, MN8, MN13), CvN 20 (CvN4-7, GNG276, GNG283, GNG641, GNG648, GNG650, GNG653), AN 15, ON 5. VERIFIED.
- Other efferent-like: vnc_efferent 94 (mostly AbNT 38, AbN4 18), cb_endocrine 72 (NCC 71), vnc_endocrine 22, efferent_ascending 8, efferent_descending 4, ENS 50. VERIFIED.

### Inferences
- INFERRED analogies (function only, not tested): neck MNs (nm 24 + CvN 20) control head orientation in several axes, so they are the nearest fly analogue of a multi-axis "wrist" (flex/roll) output; wing steering MNs (hg, i, iii, b, ps, tp) are an example of many small muscles tuning one appendage; proboscis MNs (PhN, MxLbN) are the fly's grasp/feeding effector and could be a loose analogue of a gripper open/close. HYPOTHESIS: none of these is an anatomical homologue of a robot wrist or gripper; a wrist roll is not a fly joint at all.
- INFERRED: leg tarsus (Ta levator/depressor, T1 only by name) is the nearest leg analogue of "end effector".

### Gaps
- No functional annotation of these MNs in the data beyond names; the DN to neck/wing/proboscis pathways were not queried here.

## f) Neurotransmitter composition (the Glu sign issue)

### Takeaway
DNs are 71% ACh (931 of 1,314), 18% GABA, 8% Glu by `consensus_nt`; the three FlyMind DNs (DNa02, DNa01, DNp09, all 6 bodies) are ACh. Premotor vnc_intrinsic neurons onto T2L MNs are 54% ACh, 27% GABA and **19% glutamate** by synapse weight, so the unresolved sign of glutamate affects about a fifth of the premotor drive.

### Cited Findings (`q7_hops_nt_an.out`; NT table columns: body, cell_type, predicted_nt, predicted_nt_confidence, celltype_predicted_nt, consensus_nt...)
- consensus_nt over all 1,835,518 NT rows: unclear 1,671,117; acetylcholine 104,193; glutamate 29,443; gaba 22,196; histamine 8,024; dopamine 396; octopamine 101; serotonin 48. VERIFIED.
- DNs (all 1,314 are in the table): consensus_nt by body: ACh 931, GABA 241, Glu 104, unclear 36, serotonin 2; by distinct type: ACh 332, GABA 79, Glu 49, unclear 20, serotonin 1. predicted_nt by body: ACh 928, GABA 243, Glu 104, unclear 17, serotonin 11, octopamine 11. VERIFIED.
- DNa02, DNa01, DNp09 (both bodies each): consensus and predicted = acetylcholine. VERIFIED.
- Synapse-weighted NT of DN to vnc_motor (all weights, 229,565 syn): ACh 66.8%, GABA 27.0%, Glu 4.2%, unclear 1.9%. DN to T2L MN (>=5, 13,364 syn): ACh 51.0%, GABA 46.0%, Glu 2.9%. VERIFIED.
- Premotor vnc_intrinsic to T2L MN (all weights, 190,020 syn, 1,570 bodies): consensus ACh 54.1%, GABA 26.7%, Glu 19.0%; by body ACh 828, GABA 480, Glu 245, unclear 16, histamine 1. Restricted to the 1,114 neurons with >=5 syn: ACh 626, GABA 286, Glu 196 bodies; weights 54.0 / 26.7 / 19.3%. Median predicted_nt_confidence of those 1,114 = 0.955; share with confidence <0.5 = 0.4%. VERIFIED.
- T2L MNs themselves: consensus Glu 38, unclear 19, ACh 1 (58). This is the neuromuscular transmitter, not the sign of their central synapses. VERIFIED (counts); interpretation INFERRED.

### Inferences
- INFERRED: the 46% GABA share of DN to T2L MN synapses (at >=5) shows that DNs can inhibit leg MNs directly; in a network where DN output is modelled as excitatory-only, that part would have the wrong sign.
- INFERRED: since 196 of 1,114 premotor neurons (17.6%) are Glu, the Glu sign (inhibitory via GluCl in many central/VNC contexts but not settled for MaleCNS in FlyMind's own audit) should be an explicit test arm (sign = -1, 0, +1) in any leg-circuit claim. The data cannot decide it.

### Gaps
- The sign of each NT at each synapse is not in the data (only NT identity). The rule behind `consensus_nt` was not checked here (see `malecns_data_access.md`).

## g) Ascending neurons from the T2 left leg region: count and brain targets

### Takeaway
196 ANs have their soma in T2-left; 415 ANs are either T2-left-soma or get >=5 syn directly from T2-left leg sensory neurons. Only about 30-33% of their (>=5) output goes to brain-side cb_intrinsic; about 30% stays in the VNC (vnc_intrinsic), and 8-10% goes to DNs. The top targets are auditory/ventrolateral (AVLP) and gnathal (GNG) type families and a set of DNs, which makes a short ascending-to-descending loop.

### Cited Findings (`q7_hops_nt_an.out`, section g)
- ANs by soma neuromere/side: T1 369 L / 349 R / 4 M; **T2 196 L / 194 R**; T3 199 L / 194 R / 1 M; abdominal 4-55 per segment. 196 T2-left ANs, 168 distinct types; entryNerve is empty for all of them. VERIFIED.
- Leg input side: sensory_ascending entering MesoLN left = 16 bodies (7 types; subclass leg bristle 10, chordotonal organ 4, leg 2); vnc_sensory entering MesoLN left = 661. ANs receiving >=5 syn directly from those (vnc_sensory + sensory_ascending) = 299. Union (soma T2L OR such input) = 415. VERIFIED.
- Output of the 196 soma-T2L ANs (edges >=5): vnc_intrinsic 30.7%; cb_intrinsic 29.5%; not_in_annotations 11.5%; ascending_neuron 11.1%; descending_neuron 9.6%; vnc_motor 3.0%. Top brain-side post types (syn): AVLP377 1,473; AVLP084 1,288; LPT114 1,146; AVLP374 1,115; DNge037 1,039; DNg100 1,009; DNg108 993; DNge122 992; GNG313 956; DNa13 955; GNG651 (cb_motor) 945. VERIFIED.
- Output of the 415 union ANs: cb_intrinsic 33.3%; vnc_intrinsic 28.3%; AN 12.5%; DN 8.1%. Top brain-side types: AVLP374 5,932; AVLP084 4,849; AVLP377 4,842; AVLP353 3,992; AVLP615 3,909; AVLP542 3,448; AVLP354 3,128; AVLP400 2,978; (no-type cb_intrinsic 10,589). Top DN targets: DNg108 2,452; DNge079 2,003; DNge122 2,003; DNg35 1,885; DNg100 1,885; DNge037 1,650; DNge049 1,598; DNp06 1,530. VERIFIED.
- The 16 leg sensory-ascending neurons: targets GNG016 515, SLP234 201, GNG489 200, GNG566 185, mAL6 177; DN targets DNg103 127, DNpe007 94, DNge038 55. VERIFIED.

### Inferences
- INFERRED: the data contain a return path from the T2-left leg to the brain (hundreds of ANs, many onto DNs), but the targets are mostly ventrolateral/gnathal families. None of the top targets is LC10a-related or a known visual-steering type. A hybrid that only closes the loop at the body/DNa02 level skips this feedback.
- INFERRED: ascending neurons are also VNC-local (30% to vnc_intrinsic), so "ascending = sensory feedback to brain" is only part of their output.

### Gaps
- No brain neuropil (ROI) breakdown, no NT/sign for AN output, no separation of ANs by function. Area names like AVLP/GNG are read from type names, not from an ROI table. Not checked whether any of these ANs target LC10a or the 147 FlyMind intermediates.

## h) Annotations hinting at reaching, aimed leg movement, grooming, moonwalker

### Takeaway
The annotation has no function labels. Literature names survive only in `synonyms` (199 of 1,314 DNs have a synonym). There is **no** "groom", "walk", "locomot", "escape", "backward", "steer", or "reach" function annotation. What exists is: MDN (moonwalker, synonym of a 2018 paper's DNp50), Hampel 2015 aDN1/aDN2, DNp01 as giant fiber, and 9 DN bodies explicitly noted as possibly not DNs.

### Cited Findings (`q8_nonleg_search.out`, `q9_synonyms.py`, `q9_synonyms.out`)
- Searched type, instance, synonyms, matchingNotes, flywireType, hemibrainType, mancType, supertype, serialMotif for substrings. 0 hits for: groom, moonwalk, backward, steer, jump, takeoff, walk, locomot, escape, looming, courtship, song, feeding, flight, landing (synonyms/matchingNotes). VERIFIED (absence in these columns).
- Type `MDN`: 4 DN bodies (2 L, 2 R), synonym "Carreira-Rosario 2018: DNp50". VERIFIED. (Moonwalker identity: the type is named MDN; that this is the backward-walking command neuron is REPORTED by the cited 2018 paper, not checked here.)
- `aDN`: DNg62 (2 bodies) = synonym "Hampel 2015: aDN1"; DNge078 (2 bodies) = "Hampel 2015: aDN2" (the antennal grooming literature, from my memory of that paper, NOT VERIFIED here). A cb_intrinsic type AOTU103m also carries "aDN" with other authors' names (different neurons; do not mix). VERIFIED (the strings).
- `oDN`: DNg97 (2). `giant fiber`: DNp01 (2 bodies; synonym "Kennedy and Broadie 2018: GF"). VERIFIED.
- "reach" hits (9 bodies: DNge031, DNp52, DNg86, DNpe048, DNg77) are all the matchingNotes phrase "does not reach the VNC", e.g. "Very likely not a DN but a central brain neuron". Not reaching movements. VERIFIED. Consequence: 9 of 1,314 DN bodies are flagged as possibly not DNs.
- DN synonym sources (author-year strings): Cachero 2010 (76 bodies), Sterne 2021 (22), Matsuo 2016 (18), Vaughan 2014 (16), Sapkal 2024 (11), Babski 2024 (8), Shiu 2022 (8), Carreira-Rosario 2018 (4), Hampel 2015 (4), others fewer. VERIFIED (counts of strings).
- Name-pattern counts among DNs: DNa 54 bodies (26 types), DNb 42 (17), DNp 320 (126), DNg 856 (294), MDN 4. No DN type is named by function. VERIFIED.

### Inferences
- INFERRED: the dataset cannot be queried for "the neuron that makes a leg reach" by annotation. Any choice of DN for aimed movement would rest on outside literature plus our own connectivity analysis (e.g. which DNs have the 2-hop influence on a given MN group), not on a label in MaleCNS.
- INFERRED: published lines I could not match to a type here (e.g. any DN claimed for visual targeting) must not be asserted; for DNa02 FlyMind already relies on the 'DNa02' type name, whose behavioural role (turning) comes from the literature, not from these tables.

### Gaps
- Not searched: free-text fields beyond those listed (`itoleeHl`, `trumanHl`, `statusLabel`). Did not check DNg12, DNg-type grooming matches from outside sources.

## Reproduce

```
SCR=/private/tmp/claude-501/-Users-admin--claude-spares-spare-72aeAc/18088efc-118a-40f7-a6fd-25f3036bed30/scratchpad/malecns_queries
PY="/Users/admin/so101_fly_project/.venv/bin/python -I -B"
cd $SCR
$PY q1_annotations.py   > q1_annotations.out      # a), e) counts
$PY q2_legmn.py         > q2_legmn.out            # b) leg MN tables
$PY q3_jointgroups.py   > q3_jointgroups.out      # b) joint-like groups
$PY q4_scan.py          > q4_scan.out             # c) one streaming pass (7 s), writes q4_scan.pkl
$PY q4_report.py        > q4_report.out
$PY q6_scan_thr.py 5    > q6_scan_thr5.out        # c) same at edge threshold >=5 (writes q6_scan_thr5.pkl)
$PY q6_report.py 5      > q6_report_thr5.out
$PY q5_dn_types.py      > q5_dn_types.out         # c) DNa02/DNa01/DNp09
$PY q7_hops_nt_an.py    > q7_hops_nt_an.out       # d), f), g)
$PY q8_nonleg_search.py > q8_nonleg_search.out    # e), h)
$PY q9_synonyms.py      > q9_synonyms.out         # h)
```
Runtime: seconds to ~1 minute each; peak memory a few GB (the full weights file was streamed or filtered, never fully loaded). `q6_annotated_only.out` came from the inline snippet that reads `q4_scan.pkl` (annotated-only DN fractions: drop the `not_in_annotations` column and renormalise; reproduced by `M.loc['descending_neuron'].drop('not_in_annotations')` in `q4_report.py`'s matrix).

Known script quirks: `q4_scan.py` contains a dead no-op line (`np.add.at ... if False else None`); `q6_report.py` is `q4_report.py` with a pickle name from argv. No result depends on them.

### Script sources (verbatim copies)

#### q1_annotations.py
```python
import pandas as pd
pd.set_option('display.width',250); pd.set_option('display.max_rows',500); pd.set_option('display.max_columns',50)
D='/Users/admin/so101_fly_project/data/malecns/'
a=pd.read_feather(D+'body-annotations-male-cns-v1.0-minconf-0.5.feather',columns=['bodyId','type','instance','superclass','class','subclass','somaSide','rootSide','somaNeuromere','exitNerve','entryNerve','mancType'])
print('rows',len(a))
print('== a) superclass counts'); print(a.superclass.value_counts(dropna=False))
dn=a[a.superclass=='descending_neuron']
print('DN total',len(dn)); print('DN by somaSide',dn.somaSide.value_counts(dropna=False).to_dict()); print('DN by rootSide',dn.rootSide.value_counts(dropna=False).to_dict())
print('DN distinct type',dn.type.nunique(),' DN with NaN type',dn.type.isna().sum())
print('DN class',dn['class'].value_counts(dropna=False).head(10).to_dict())
an=a[a.superclass=='ascending_neuron']; print('AN total',len(an),'distinct type',an.type.nunique(), 'somaSide',an.somaSide.value_counts(dropna=False).to_dict())
print('== b) vnc_motor'); mn=a[a.superclass=='vnc_motor']
print(pd.crosstab(mn.exitNerve.fillna('NA'),mn.somaSide.fillna('NA'),margins=True))
print(pd.crosstab(mn.somaNeuromere.fillna('NA'),mn.somaSide.fillna('NA'),margins=True))
print('subclass',mn.subclass.value_counts(dropna=False).to_dict()); print('class',mn['class'].value_counts(dropna=False).to_dict())
print('type NaN',mn.type.isna().sum(),'of',len(mn))
print('== cb_motor'); cb=a[a.superclass=='cb_motor']; print(len(cb)); print(cb.exitNerve.value_counts(dropna=False).to_dict()); print(cb.type.value_counts(dropna=False).head(30).to_dict()); print(cb.somaSide.value_counts(dropna=False).to_dict())
```

#### q2_legmn.py
```python
import pandas as pd, re
pd.set_option('display.width',250); pd.set_option('display.max_rows',500)
D='/Users/admin/so101_fly_project/data/malecns/'
a=pd.read_feather(D+'body-annotations-male-cns-v1.0-minconf-0.5.feather',columns=['bodyId','type','instance','superclass','subclass','somaSide','somaNeuromere','exitNerve','mancType'])
mn=a[a.superclass=='vnc_motor']
for nerve,name in [('MesoLN','T2'),('ProLN','T1'),('MetaLN','T3')]:
    for side in 'LR':
        s=mn[(mn.exitNerve==nerve)&(mn.somaSide==side)]
        print(f'\n== {name} {side} nerve={nerve} n={len(s)}  type NaN={s.type.isna().sum()}  neuromere={s.somaNeuromere.value_counts(dropna=False).to_dict()}')
        print('subclass',s.subclass.value_counts(dropna=False).to_dict())
        if side=='L' and name in('T1','T2'):
            print(s.groupby(s.type.fillna('NA')).agg(n=('bodyId','size'),subclass=('subclass',lambda x:','.join(sorted(set(map(str,x))))),manc=('mancType',lambda x:','.join(sorted(set(map(str,x)))[:3])),inst=('instance',lambda x:list(x)[0])).to_string())
# type-name joint patterns
print('\n== distinct leg MN type names (all legs, both sides)')
leg=mn[mn.exitNerve.isin(['ProLN','MesoLN','MetaLN'])]
print(sorted(leg.type.dropna().unique()))
print('instance examples',leg.instance.dropna().unique()[:15])
pat=re.compile(r'coxa|trochanter|femur|tibia|tarsus|flexor|extensor|levator|depressor|promotor|remotor|rotator|Tr_|Fe_|Ti_|Ta_|Cx|STR|LTM|sr|tpGRM|ltm|fle|tadm|Tr|Fe|Ti|Ta',re.I)
```

#### q3_jointgroups.py
```python
import pandas as pd, re
pd.set_option('display.width',250)
D='/Users/admin/so101_fly_project/data/malecns/'
a=pd.read_feather(D+'body-annotations-male-cns-v1.0-minconf-0.5.feather',columns=['bodyId','type','superclass','somaSide','exitNerve'])
mn=a[(a.superclass=='vnc_motor')&a.exitNerve.isin(['ProLN','MesoLN','MetaLN'])].copy()
def grp(t):
    if not isinstance(t,str): return 'unannotated(NaN type)'
    s=t.lower()
    if re.match(r'mn(ml|hl|fl)\d+',s): return 'numbered MNxx (no muscle name)'
    if 'ta ' in s and ('depressor' in s or 'levator' in s): return 'tarsus (Ta depressor/levator)'
    if s.startswith('ti ') or 'acc. ti' in s or s.startswith('ltm1'): return 'femur-tibia (Ti flexor/extensor, Acc.Ti, ltm1-tibia)'
    if 'ltm' in s: return 'long tendon muscle (ltm, ltm2-femur)'
    if 'tr ' in s[:3] or 'acc. tr' in s or 'sternotroch' in s or 'fe reductor' in s: return 'trochanter/femur (Tr flexor/ext, Acc.Tr, Sternotr., Fe reductor)'
    if any(k in s for k in ['remotor','rotator','adductor','promotor','tergotr']): return 'coxa-level (remotor/rotator/adductor/tergotr.)'
    return 'other'
mn['g']=mn.type.map(grp)
mn['leg']=mn.exitNerve.map({'ProLN':'T1','MesoLN':'T2','MetaLN':'T3'})
print(pd.crosstab(mn.g,[mn.leg,mn.somaSide],margins=True).to_string())
named=mn[~mn.g.isin(['unannotated(NaN type)','numbered MNxx (no muscle name)'])]
print('\nmuscle-named share per leg/side:'); print((named.groupby(['leg','somaSide']).size()/mn.groupby(['leg','somaSide']).size()).round(3))
print('\nT2L ltm detail', mn[(mn.leg=='T2')&(mn.somaSide=='L')&mn.type.fillna('').str.startswith('ltm')].type.value_counts().to_dict())
print('number of leg MN overall',len(mn))
```

#### q4_scan.py
```python
# one streaming pass over the weights: superclass x superclass synapse matrix + leg-MN input by pre superclass
import pandas as pd, numpy as np, pyarrow.dataset as ds, pickle, time
D='/Users/admin/so101_fly_project/data/malecns/'
a=pd.read_feather(D+'body-annotations-male-cns-v1.0-minconf-0.5.feather',columns=['bodyId','type','superclass','somaSide','exitNerve'])
a['sc']=a.superclass.fillna('NA_unannotated')
cats=sorted(a.sc.unique())+['not_in_annotations']; cid={c:i for i,c in enumerate(cats)}; K=len(cats)
ids=a.bodyId.values.astype(np.int64); order=np.argsort(ids); ids_s=ids[order]
code=a.sc.map(cid).values.astype(np.int16)[order]
# leg MN flag per T2L etc: group codes 0=none,1=T1L,2=T2L,3=T3L,4=T1R,5=T2R,6=T3R
lg=np.zeros(len(a),dtype=np.int8)
m=(a.superclass=='vnc_motor')
for k,(n,s) in enumerate([('ProLN','L'),('MesoLN','L'),('MetaLN','L'),('ProLN','R'),('MesoLN','R'),('MetaLN','R')],1):
    lg[(m&(a.exitNerve==n)&(a.somaSide==s)).values]=k
lg=lg[order]
def look(x):
    i=np.searchsorted(ids_s,x); i[i>=len(ids_s)]=len(ids_s)-1
    ok=ids_s[i]==x
    return i,ok
M=np.zeros((K,K),dtype=np.int64); L=np.zeros((7,K),dtype=np.int64)
f=ds.dataset(D+'connectome-weights-male-cns-v1.0-minconf-0.5.feather',format='ipc')
t0=time.time(); n=0; miss=0
for b in f.to_batches(batch_size=4_000_000):
    pre=b.column('body_pre').to_numpy(); post=b.column('body_post').to_numpy(); w=b.column('weight').to_numpy()
    ip,okp=look(pre); iq,okq=look(post)
    miss+=int((~okp).sum()+(~okq).sum())
    ok=np.ones(len(pre),bool)
    cp=np.where(okp,code[ip],K-1); cq=np.where(okq,code[iq],K-1); ww=w
    np.add.at(M,(cp,cq),ww) if False else None
    M+=np.bincount(cp.astype(np.int64)*K+cq,weights=ww,minlength=K*K).reshape(K,K).astype(np.int64)
    g=np.where(okq,lg[iq],0); sel=g>0
    L+=np.bincount(g[sel].astype(np.int64)*K+cp[sel],weights=ww[sel],minlength=7*K).reshape(7,K).astype(np.int64)
    n+=len(b)
print('rows',n,'missing-id endpoints',miss,'sec',round(time.time()-t0))
pickle.dump((cats,M,L),open('q4_scan.pkl','wb'))
```

#### q4_report.py
```python
import pickle, pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',50)
cats,M,L=pickle.load(open('q4_scan.pkl','rb'))
M=pd.DataFrame(M,index=cats,columns=cats); 
def show(title,ser,top=14):
    ser=ser[ser>0].sort_values(ascending=False); tot=ser.sum()
    print(f'\n{title} total={tot}'); print(pd.DataFrame({'syn':ser,'pct':(100*ser/tot).round(1)}).head(top).to_string())
show('c1) ALL DN (descending_neuron) OUTPUT by post superclass',M.loc['descending_neuron'])
show('c1) DN INPUT by pre superclass',M['descending_neuron'])
print('\n-- groups (DN output): vnc_motor / vnc_intrinsic / ascending(AN+sensory_asc+eff_asc) / brain(cb_*,ol_*,visual_*) / other')
r=M.loc['descending_neuron']; tot=r.sum()
g={'vnc_motor':r['vnc_motor'],'vnc_intrinsic':r['vnc_intrinsic'],'ascending (ascending_neuron+sensory_ascending[_tbc]+efferent_ascending)':r[['ascending_neuron','sensory_ascending','sensory_ascending_tbc','efferent_ascending']].sum(),
'cb_*/ol_*/visual_* (brain-side)':r[[c for c in cats if c.startswith(('cb_','ol_','visual_'))]].sum(),'descending (DN->DN)':r['descending_neuron']+r['descending_neuron_tbc']}
g['other']=tot-sum(g.values())
for k,v in g.items(): print(f'  {k:75s}{int(v):>10d} {100*v/tot:5.1f}%')
legs=['none','T1L','T2L','T3L','T1R','T2R','T3R']
Ldf=pd.DataFrame(L,index=legs,columns=cats)
for lg in ['T2L','T1L']:
    show(f'c2) INPUT to {lg} leg MNs by pre superclass',Ldf.loc[lg],top=10)
allL=Ldf.loc[['T1L','T2L','T3L','T1R','T2R','T3R']].sum(); show('c2) INPUT to ALL leg MNs by pre superclass',allL,top=10)
sens=[c for c in cats if 'sensory' in c]
for lg in ['T2L','T1L']:
    s=Ldf.loc[lg]; t=s.sum()
    print(f'\n{lg}: DN {100*s["descending_neuron"]/t:.1f}%  vnc_intrinsic {100*s["vnc_intrinsic"]/t:.1f}%  sensory(any) {100*s[sens].sum()/t:.1f}%  vnc_motor {100*s["vnc_motor"]/t:.1f}%  ascending {100*s[["ascending_neuron","sensory_ascending","sensory_ascending_tbc"]].sum()/t:.1f}%  not_in_annotations {100*s["not_in_annotations"]/t:.1f}%  NA_unannotated {100*s["NA_unannotated"]/t:.1f}%')
```

#### q5_dn_types.py
```python
import pandas as pd, numpy as np, pyarrow.dataset as ds
pd.set_option('display.width',250); pd.set_option('display.max_rows',200)
D='/Users/admin/so101_fly_project/data/malecns/'
a=pd.read_feather(D+'body-annotations-male-cns-v1.0-minconf-0.5.feather',columns=['bodyId','type','instance','superclass','subclass','somaSide','exitNerve','entryNerve','somaNeuromere','class'])
a['sc']=a.superclass.fillna('NA_unannotated')
dn=a[a.superclass=='descending_neuron']
for t in ['DNa02','DNa01','DNp09']:
    s=dn[dn.type==t]; print(t,len(s),s.somaSide.value_counts().to_dict(), s.bodyId.tolist())
print('DN types matching patterns:'); 
for p in ['groom','DNg','aDN','moon','MDN','DNp','DNa','DNb']:
    m=dn[dn.type.fillna('').str.contains(p,case=False)|dn.instance.fillna('').str.contains(p,case=False)]
    print(' ',p,len(m),'bodies',m.type.nunique(),'types')
W=ds.dataset(D+'connectome-weights-male-cns-v1.0-minconf-0.5.feather',format='ipc')
info=a.set_index('bodyId')
def post_table(ids):
    t=W.to_table(filter=ds.field('body_pre').isin(ids)).to_pandas()
    return t
def lab(b): 
    return b.map(info['type']).fillna('(no type)')
legMN={}
for k,(n,s) in {'T1L':('ProLN','L'),'T2L':('MesoLN','L'),'T3L':('MetaLN','L'),'T1R':('ProLN','R'),'T2R':('MesoLN','R'),'T3R':('MetaLN','R')}.items():
    legMN[k]=set(a.bodyId[(a.superclass=='vnc_motor')&(a.exitNerve==n)&(a.somaSide==s)])
allleg=set().union(*legMN.values())
print('\n== c) per DN type: top10 post types, and direct synapses onto leg MNs')
for t in ['DNa02','DNa01','DNp09']:
    ids=dn.bodyId[dn.type==t].astype(int).tolist()
    e=post_table(ids); tot=e.weight.sum()
    e['ptype']=lab(e.body_post); e['psc']=e.body_post.map(info['sc']).fillna('not_in_annotations')
    print(f'\n--- {t}: n={len(ids)} total output syn={tot}, distinct post bodies={e.body_post.nunique()}')
    print('by post superclass:',(e.groupby('psc').weight.sum().sort_values(ascending=False)/tot*100).round(1).head(8).to_dict())
    g=e.groupby(['ptype']).weight.sum().sort_values(ascending=False).head(10); print(g.to_string())
    for k,v in legMN.items():
        x=e[e.body_post.isin(v)]
        print(f'  direct -> {k} leg MNs: {x.weight.sum()} syn onto {x.body_post.nunique()}/{len(v)} MNs, from {x.body_pre.nunique()} DN bodies')
    xx=e[e.body_post.isin(allleg)]; print('  direct -> ANY leg MN:',xx.weight.sum(), ' top types',xx.groupby('ptype').weight.sum().sort_values(ascending=False).head(5).to_dict())
    xa=e[e.psc=='vnc_motor']; print('  direct -> any vnc_motor:',xa.weight.sum(), xa.groupby('ptype').weight.sum().sort_values(ascending=False).head(6).to_dict())
```

#### q6_scan_thr.py
```python
# one streaming pass over the weights: superclass x superclass synapse matrix + leg-MN input by pre superclass
import pandas as pd, numpy as np, pyarrow.dataset as ds, pickle, time, sys
THR=int(sys.argv[1])
D='/Users/admin/so101_fly_project/data/malecns/'
a=pd.read_feather(D+'body-annotations-male-cns-v1.0-minconf-0.5.feather',columns=['bodyId','type','superclass','somaSide','exitNerve'])
a['sc']=a.superclass.fillna('NA_unannotated')
cats=sorted(a.sc.unique())+['not_in_annotations']; cid={c:i for i,c in enumerate(cats)}; K=len(cats)
ids=a.bodyId.values.astype(np.int64); order=np.argsort(ids); ids_s=ids[order]
code=a.sc.map(cid).values.astype(np.int16)[order]
# leg MN flag per T2L etc: group codes 0=none,1=T1L,2=T2L,3=T3L,4=T1R,5=T2R,6=T3R
lg=np.zeros(len(a),dtype=np.int8)
m=(a.superclass=='vnc_motor')
for k,(n,s) in enumerate([('ProLN','L'),('MesoLN','L'),('MetaLN','L'),('ProLN','R'),('MesoLN','R'),('MetaLN','R')],1):
    lg[(m&(a.exitNerve==n)&(a.somaSide==s)).values]=k
lg=lg[order]
def look(x):
    i=np.searchsorted(ids_s,x); i[i>=len(ids_s)]=len(ids_s)-1
    ok=ids_s[i]==x
    return i,ok
M=np.zeros((K,K),dtype=np.int64); L=np.zeros((7,K),dtype=np.int64)
f=ds.dataset(D+'connectome-weights-male-cns-v1.0-minconf-0.5.feather',format='ipc')
t0=time.time(); n=0; miss=0
for b in f.to_batches(batch_size=4_000_000):
    pre=b.column('body_pre').to_numpy(); post=b.column('body_post').to_numpy(); w=b.column('weight').to_numpy()
    ip,okp=look(pre); iq,okq=look(post)
    miss+=int((~okp).sum()+(~okq).sum())
    ok=np.ones(len(pre),bool)
    keep=w>=THR; pre=pre[keep];post=post[keep];w=w[keep];ip=ip[keep];iq=iq[keep];okp=okp[keep];okq=okq[keep]
    ok=np.ones(len(pre),bool)
    cp=np.where(okp,code[ip],K-1); cq=np.where(okq,code[iq],K-1); ww=w
    np.add.at(M,(cp,cq),ww) if False else None
    M+=np.bincount(cp.astype(np.int64)*K+cq,weights=ww,minlength=K*K).reshape(K,K).astype(np.int64)
    g=np.where(okq,lg[iq],0); sel=g>0
    L+=np.bincount(g[sel].astype(np.int64)*K+cp[sel],weights=ww[sel],minlength=7*K).reshape(7,K).astype(np.int64)
    n+=len(b)
print('rows',n,'missing-id endpoints',miss,'sec',round(time.time()-t0))
pickle.dump((cats,M,L),open(f'q6_scan_thr{THR}.pkl','wb'))
```

#### q7_hops_nt_an.py
```python
import pandas as pd, numpy as np, pyarrow.dataset as ds
pd.set_option('display.width',250); pd.set_option('display.max_rows',200)
D='/Users/admin/so101_fly_project/data/malecns/'
a=pd.read_feather(D+'body-annotations-male-cns-v1.0-minconf-0.5.feather',columns=['bodyId','type','superclass','subclass','somaSide','rootSide','exitNerve','entryNerve','somaNeuromere'])
nt=pd.read_feather(D+'body-neurotransmitters-male-cns-v1.0.feather')
print('NT columns',list(nt.columns),'rows',len(nt)); print('consensus_nt values',nt.consensus_nt.value_counts(dropna=False).to_dict()); print('predicted_nt values',nt.predicted_nt.value_counts(dropna=False).to_dict())
info=a.set_index('bodyId'); ntx=nt.drop_duplicates('body').set_index('body')
W=ds.dataset(D+'connectome-weights-male-cns-v1.0-minconf-0.5.feather',format='ipc')
dn=a[a.superclass=='descending_neuron']; dnids=set(dn.bodyId.astype(int)); inn=set(a.bodyId[a.superclass=='vnc_intrinsic'].astype(int))
mn2=a[(a.superclass=='vnc_motor')&(a.exitNerve=='MesoLN')&(a.somaSide=='L')]; mn2ids=mn2.bodyId.astype(int).tolist()
print('T2L MN',len(mn2ids))
# edges into T2L MN
e_mn=W.to_table(filter=ds.field('body_post').isin(mn2ids)).to_pandas()
e_dn=W.to_table(filter=ds.field('body_pre').isin(list(dnids))).to_pandas()
print('\n== d) hops to T2L MNs (DN identity = descending_neuron superclass)')
for t in [1,5,10]:
    h1=e_mn[(e_mn.body_pre.isin(dnids))&(e_mn.weight>=t)]
    dn1=set(h1.body_pre)
    ins_to_mn=e_mn[(e_mn.body_pre.isin(inn))&(e_mn.weight>=t)]
    ins=set(ins_to_mn.body_pre)
    h2=e_dn[(e_dn.body_post.isin(ins))&(e_dn.weight>=t)]
    dn2=set(h2.body_pre)
    # DN->IN->MN paths
    print(f'thr>={t}: 1-hop DNs={len(dn1)} (types {a[a.bodyId.isin(dn1)].type.nunique()}) | premotor INs (>=t onto T2L MN)={len(ins)} | DNs reaching those INs (2-hop)={len(dn2)} (types {a[a.bodyId.isin(dn2)].type.nunique()}) | 1-hop OR 2-hop={len(dn1|dn2)} | 2-hop only={len(dn2-dn1)} | of {len(dnids)} DNs total')
    if t==5:
        mnreached=set(h1.body_post); print('   T2L MNs reached directly by >=1 DN:',len(mnreached),'of',len(mn2ids))
        d1=h1.groupby('body_pre').weight.sum().sort_values(ascending=False).head(8)
        print('   top 1-hop DNs by synapses to T2L MNs:'); print(pd.DataFrame({'type':d1.index.map(info['type']),'side':d1.index.map(info['somaSide']),'syn':d1.values}).to_string())
        for nm in ['DNa02','DNa01','DNp09']:
            ids=set(dn.bodyId[dn.type==nm]); print(f'   {nm}: 1-hop={len(ids&dn1)}/{len(ids)}  2-hop={len(ids&dn2)}/{len(ids)}')
# f) NT
print('\n== f) NT')
d=dn.copy(); d['cons']=d.bodyId.map(ntx.consensus_nt); d['pred']=d.bodyId.map(ntx.predicted_nt)
print('DN bodies in NT table:',d.bodyId.isin(ntx.index).sum(),'/',len(d))
print('DN consensus_nt (bodies):',d.cons.fillna('NaN').value_counts().to_dict()); print('DN predicted_nt (bodies):',d.pred.fillna('NaN').value_counts().to_dict())
print('DN consensus_nt (types, distinct):',d.drop_duplicates('type').cons.fillna('NaN').value_counts().to_dict())
# synapse-weighted by DN output to vnc_motor
ev=e_dn[e_dn.body_post.map(info['superclass'])=='vnc_motor'].copy(); ev['cons']=ev.body_pre.map(ntx.consensus_nt).fillna('NaN')
print('DN->vnc_motor synapse-weighted NT (thr1):',(ev.groupby('cons').weight.sum()/ev.weight.sum()*100).round(1).to_dict(), 'total',ev.weight.sum())
h1=e_mn[(e_mn.body_pre.isin(dnids))&(e_mn.weight>=5)].copy(); h1['cons']=h1.body_pre.map(ntx.consensus_nt).fillna('NaN')
print('DN->T2L MN (>=5) synapse-weighted NT:',(h1.groupby('cons').weight.sum()/h1.weight.sum()*100).round(1).to_dict(),'total',h1.weight.sum())
pm=e_mn[e_mn.body_pre.isin(inn)].copy(); pm['cons']=pm.body_pre.map(ntx.consensus_nt).fillna('NaN'); pm['pred']=pm.body_pre.map(ntx.predicted_nt).fillna('NaN')
print('premotor vnc_intrinsic->T2L MN (all weights) synapse-weighted consensus_nt:',(pm.groupby('cons').weight.sum()/pm.weight.sum()*100).round(1).to_dict(),'total',pm.weight.sum())
print('   ... predicted_nt (per neuron):',(pm.groupby('pred').weight.sum()/pm.weight.sum()*100).round(1).to_dict())
p5=pm[pm.weight>=5]; print('   (>=5 edges) consensus:',(p5.groupby('cons').weight.sum()/p5.weight.sum()*100).round(1).to_dict(),'edges',len(p5),'bodies',p5.body_pre.nunique())
bodies=pm.drop_duplicates('body_pre'); print('   premotor IN bodies (any weight)',len(bodies),'consensus (bodies):',bodies.cons.value_counts().to_dict())
b5=p5.drop_duplicates('body_pre'); print('   premotor IN bodies (>=5)',len(b5),'consensus (bodies):',b5.cons.value_counts().to_dict())
print('   confidence of predicted_nt for premotor IN bodies (>=5): median',ntx.predicted_nt_confidence.reindex(b5.body_pre).median().round(3),' share conf<0.5:',round((ntx.predicted_nt_confidence.reindex(b5.body_pre)<0.5).mean(),3))
print('   what DNa02 consensus_nt is:',d[d.type=='DNa02'][['bodyId','cons','pred']].values.tolist(),'DNa01:',d[d.type=='DNa01'][['bodyId','cons','pred']].values.tolist(),'DNp09:',d[d.type=='DNp09'][['bodyId','cons','pred']].values.tolist())
mnn=mn2.copy(); mnn['cons']=mnn.bodyId.map(ntx.consensus_nt); print('   T2L MN NT itself:',mnn.cons.fillna('NaN').value_counts().to_dict())
# g) ascending
print('\n== g) ascending neurons from T2L')
an=a[a.superclass=='ascending_neuron']
print('AN by somaNeuromere/side:'); print(pd.crosstab(an.somaNeuromere.fillna('NA'),an.somaSide.fillna('NA')).to_string())
anT2L=an[(an.somaNeuromere=='T2')&(an.somaSide=='L')]; print('AN with soma T2 left:',len(anT2L),'distinct types',anT2L.type.nunique()); print('exit/entry nerve',anT2L.entryNerve.fillna('NA').value_counts().to_dict())
sa=a[a.superclass.isin(['sensory_ascending','sensory_ascending_tbc'])]; saT2L=sa[(sa.entryNerve=='MesoLN')&(sa.rootSide=='L')]
print('sensory_ascending entering MesoLN left:',len(saT2L),'types',saT2L.type.nunique(),'subclass',saT2L.subclass.value_counts(dropna=False).to_dict())
sens=a[a.superclass.isin(['vnc_sensory','vnc_sensory_tbc'])&(a.entryNerve=='MesoLN')&(a.rootSide=='L')]; sids=set(sens.bodyId.astype(int)); print('vnc_sensory entering MesoLN left',len(sids))
e_s=W.to_table(filter=ds.field('body_pre').isin(list(sids|set(saT2L.bodyId.astype(int))))).to_pandas()
ean=e_s[(e_s.weight>=5)&(e_s.body_post.map(info['superclass'])=='ascending_neuron')]
print('ANs receiving >=5 syn directly from T2L leg sensory (vnc_sensory+sensory_ascending):',ean.body_post.nunique())
anset=set(ean.body_post)|set(anT2L.bodyId.astype(int))
print('union (soma T2L OR direct T2L-sensory input):',len(anset))
def targets(ids,label):
    e=W.to_table(filter=ds.field('body_pre').isin(list(ids))).to_pandas(); e=e[e.weight>=5]
    e['psc']=e.body_post.map(info['superclass']).fillna('not_in_annotations'); e['pt']=e.body_post.map(info['type']).fillna('(no type)')
    print(f'\n[{label}] n={len(ids)}  output edges>=5: synapses by post superclass:',(e.groupby('psc').weight.sum().sort_values(ascending=False)/e.weight.sum()*100).round(1).head(8).to_dict())
    br=e[e.psc.isin(['cb_intrinsic','descending_neuron','cb_motor','visual_projection','cb_sensory','visual_centrifugal','ol_intrinsic'])]
    print(' top brain-side post TYPES:'); print(br.groupby(['psc','pt']).weight.sum().sort_values(ascending=False).head(12).to_string())
    print(' top DN targets:',br[br.psc=='descending_neuron'].groupby('pt').weight.sum().sort_values(ascending=False).head(8).to_dict())
targets(anT2L.bodyId.astype(int),'AN soma T2L')
targets(anset,'AN union T2L')
targets(set(saT2L.bodyId.astype(int)),'sensory_ascending MesoLN-L')
```

#### q8_nonleg_search.py
```python
import pandas as pd, re
pd.set_option('display.width',250); pd.set_option('display.max_rows',300); pd.set_option('display.max_colwidth',80)
D='/Users/admin/so101_fly_project/data/malecns/'
a=pd.read_feather(D+'body-annotations-male-cns-v1.0-minconf-0.5.feather')
print('all columns:',list(a.columns))
mn=a[a.superclass=='vnc_motor']
print('== e) vnc_motor non-leg: subclass x exitNerve'); nl=mn[~mn.exitNerve.isin(['ProLN','MesoLN','MetaLN'])]
print(pd.crosstab(nl.subclass.fillna('NA'),nl.exitNerve.fillna('NA'),margins=True).to_string())
for sc in ['nm','wm','hm','xm','ad']:
    s=mn[mn.subclass==sc]; print(f'\nsubclass {sc}: n={len(s)} sides={s.somaSide.value_counts().to_dict()} neuromere={s.somaNeuromere.value_counts().to_dict()} nerves={s.exitNerve.value_counts().to_dict()}')
    print('  types:',s.type.fillna('NaN').value_counts().to_dict() if sc!='ad' else list(s.type.fillna('NaN').value_counts().head(12).items()))
print('\n== cb_motor by exitNerve (brain-side MNs) and types'); cb=a[a.superclass=='cb_motor']
print(cb.groupby(cb.exitNerve.fillna('NA')).agg(n=('bodyId','size'),types=('type',lambda x:sorted(set(map(str,x)))[:14])).to_string())
print('\n== other efferent-like superclasses'); 
for sc in ['vnc_efferent','cb_efferent','efferent_ascending','efferent_descending','vnc_endocrine','cb_endocrine','ENS']:
    s=a[a.superclass==sc]; print(sc,len(s),'nerves',s.exitNerve.fillna('NA').value_counts().head(6).to_dict(),'types',sorted(set(map(str,s.type)))[:6])
print('\n== h) text search over type/instance/synonyms/matchingNotes/flywireType/hemibrainType/mancType')
cols=['type','instance','synonyms','matchingNotes','flywireType','hemibrainType','mancType','supertype','serialMotif']
pats=['groom','reach','moonwalk','MDN','aDN','oDN','DNg12','antennal','foreleg','proboscis','escape','giant','GF','DNp01','looming','takeoff','jump','walking','steer','turn','backward','locomot','fru','courtship','song','P1']
for p in ['groom','reach','moonwalk','backward','steer','aDN','oDN','giant fiber','jump','takeoff','walk','locomot','escape']:
    hit=pd.Series(False,index=a.index); 
    for c in cols:
        if c in a.columns: hit|=a[c].astype(str).str.contains(p,case=False,na=False)
    h=a[hit]; print(f'\n"{p}": {len(h)} bodies')
    if len(h): print(h.groupby(['superclass','type'],dropna=False).size().sort_values(ascending=False).head(8).to_string())
mdn=a[a.type.astype(str).str.contains('MDN')]; print('\nMDN rows:'); print(mdn[['bodyId','type','instance','superclass','somaSide','synonyms','matchingNotes','mancType','flywireType','hemibrainType']].to_string())
```

#### q9_synonyms.py
```python
import pandas as pd
pd.set_option('display.width',250); pd.set_option('display.max_colwidth',120)
D='/Users/admin/so101_fly_project/data/malecns/'
a=pd.read_feather(D+'body-annotations-male-cns-v1.0-minconf-0.5.feather')
cols=['type','instance','synonyms','matchingNotes']
def h(p,sc=None,case=True):
    m=pd.Series(False,index=a.index)
    for c in cols: m|=a[c].astype(str).str.contains(p,case=case,na=False)
    x=a[m]; 
    if sc: x=x[x.superclass==sc]
    return x[['bodyId','type','superclass','somaSide','synonyms','matchingNotes']]
print('reach (case-insens) hits:'); print(h('reach',case=False).to_string())
print('\naDN (case-sens) hits:'); print(h('aDN').to_string())
print('\nDN synonyms nonnull count:',a[a.superclass=="descending_neuron"].synonyms.notna().sum(),'of',(a.superclass=="descending_neuron").sum())
x=a[(a.superclass=='descending_neuron')&a.synonyms.notna()]
print(x.groupby('synonyms').size().sort_values(ascending=False).head(0))
print('\nDN synonyms sample (distinct types, first 40):'); print(x.drop_duplicates('type')[['type','synonyms']].head(40).to_string())
print('\nDN with synonyms mentioning author refs, by source word:')
import re
src=x.synonyms.str.extract(r'^([A-Za-z\-\. ]+ (?:et al\.? )?\d{4}|[A-Za-z\-]+ \d{4}|[^:]+):')[0].value_counts().head(25); print(src.to_string())
print('\nlooking for terms in ANY synonyms/matchingNotes of all superclasses:')
for p in ['groom','walk','locomot','reach','escape','backward','giant','steer','turn','courtship','song','feeding','flight','landing','take','looming']:
    m=a.synonyms.astype(str).str.contains(p,case=False,na=False)|a.matchingNotes.astype(str).str.contains(p,case=False,na=False)
    print(p,int(m.sum()), a[m].type.dropna().unique()[:6].tolist())
```
