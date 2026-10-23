# MaleCNS v1.0 + MANC: dostęp do danych bez tokenu neuPrint (stan na 2026-10-23)

## Where is MaleCNS v1.0 published, and is there a public bulk download?

### Takeaway
MaleCNS v1.0 is the neuPrint dataset `male-cns:v1.0`, released 2026-06-08 and published in Cell on 2026-09-03 (preprint bioRxiv 10.1101/2025.10.09.680999). It has a **public, anonymous** bulk download as Apache Arrow Feather files in the GCS bucket `gs://flyem-male-cns/v1.0/connectome-data/flat-connectome/`. I verified with HTTP HEAD that every file returns `HTTP 200` with no credentials. The neurons, types, NT and weights tables come to about 1.1 GB and need no token.

### Cited Findings
- Project page: https://male-cns.janelia.org/. neuPrint dataset name `male-cns:v1.0`, Clio `male-cns:v1.0-v1.0`. Timeline: v0.9 on 2025-10-03, preprint v2 on 2025-10-30, NeuronBridge on 2025-11-07, v1.0 on 2026-06-08, Cell paper on 2026-09-03 — [male-cns.janelia.org](https://male-cns.janelia.org/)
- The release notes give v0.9 as 2025-10-05, which disagrees with the 2025-10-03 on the home page. v1.0 = "minor proofreading changes and refinement of neuron annotations" — [Release notes](https://male-cns.janelia.org/release/)
- Paper: "Sexual dimorphism in the complete Drosophila male central nervous system connectome", Cell, article S0092-8674(26)00942-6 — [Cell](https://www.cell.com/cell/fulltext/S0092-8674(26)00942-6); the Cell Press collection is at [Male fly connectome](https://www.cell.com/consortium/male-fly-connectome). Preprint: https://www.biorxiv.org/content/10.1101/2025.10.09.680999v2 — [male-cns.janelia.org](https://male-cns.janelia.org/). VFB cites v0.9 as "Berg et al. (2025)" — [VFB LC10a_L](https://www.virtualflybrain.org/term/lc10a_l-malecns26963-vfb_jrmc25kr/)
- Download page with file descriptions — [MaleCNS Downloads](https://male-cns.janelia.org/download/)
- **Verified by me with `curl -I` and the GCS JSON API, 2026-10-23, no credentials. Byte sizes as reported by GCS.** Base URL `https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/`:
  | File | Bytes | Updated | Contents |
  |---|---|---|---|
  | `body-annotations-male-cns-v1.0-minconf-0.5.feather` | 14,483,314 | 2026-06-03 | types/classes/sides, without NT |
  | `body-neurotransmitters-male-cns-v1.0.feather` | 43,282,834 | 2026-06-08 | NT per neuron + consensus per type |
  | `body-stats-male-cns-v1.0-minconf-0.5.feather` | 778,062,826 | 2026-06-03 | pre/post counts for all segments |
  | `connectome-weights-male-cns-v1.0-minconf-0.5.feather` | 1,051,241,946 | 2026-06-03 | full graph body_pre→body_post |
  | `connectome-weights-male-cns-v1.0-minconf-0.5-traced-only.feather` | 508,025,642 | 2026-06-03 | traced neurons only (not on the download page, but in the bucket) |
  | `connectome-weights-male-cns-v1.0-minconf-0.5-significant-only.feather` | 502,169,298 | 2026-06-03 | "significant" bodies only (not on the download page) |
  | `syn-partners-male-cns-v1.0-minconf-0.5[-traced-only/-significant-only].feather` | 6.78 GB / 2.97 / 2.97 | 2026-06-03 | synapse pairs with xyz |
  | `syn-points-male-cns-v1.0-minconf-0.5.feather` | 13,061,489,098 | 2026-06-03 | synapse points |
  | `tbar-neurotransmitters-male-cns-v1.0.feather` | 2,651,680,218 | 2026-06-08 | NT probabilities per T-bar |
  — [GCS listing](https://storage.googleapis.com/storage/v1/b/flyem-male-cns/o?prefix=v1.0/connectome-data/flat-connectome/&fields=items(name,size,updated))
- More in the same bucket: v1.0 segmentation `gs://flyem-male-cns/v1.0/segmentation`, SWC skeletons `gs://flyem-male-cns/v1.0/segmentation/skeletons-malecns/skeletons-swc/<bodyId>.swc`, mirrored skeletons and JRC2018U, ROIs `gs://flyem-male-cns/rois/fullbrain-roi-v4` and `.../malecns-vnc-neuropil-roi-v0`, the full Neo4j 4.4.16 database `gs://flyem-male-cns/v1.0/database/neo4j`, and the CSV inputs `gs://flyem-male-cns/v1.0/database/neuprint-inputs` — [Downloads](https://male-cns.janelia.org/download/). The `v1.0/database/` prefix also contains `dvid-exports/` — [GCS listing](https://storage.googleapis.com/storage/v1/b/flyem-male-cns/o?prefix=v1.0/database/&delimiter=/&fields=prefixes)
- There is no Parquet or Zenodo deposit for the data itself. The only CSVs are the neuPrint inputs — [Downloads](https://male-cns.janelia.org/download/). On Zenodo there is only the R package natverse/malecns (e.g. 0.4.2), whose default is now v1.0. v0.9 can still be selected via `choose_mcns_dataset()` — [Zenodo natverse/malecns](https://zenodo.org/records/21993186)
- Codex (FlyWire) also hosts "MCNS v1.0 (CNS)": 166,700 neurons, 6,242,118 connections. Exports there require Google sign-in — [codex.flywire.ai](https://codex.flywire.ai/api/download)

### Inferences
- Minimal path with no account: `pd.read_feather("https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/body-annotations-male-cns-v1.0-minconf-0.5.feather")` plus the NT file plus `connectome-weights-...-traced-only.feather` (0.5 GB). Join on bodyId, filter by `type`. That covers neuron/type/connection/NT for any cell type without neuPrint.
- `-traced-only` is probably the best choice for a model of named types, because it drops fragments and halves the size. Its exact definition (traced vs significant) is not described on the download page.
- minconf-0.5 = synapse confidence threshold of 0.5 (from the file name). Weights from neuPrint `male-cns:v1.0` should agree with this file, but I did not check that.

### Gaps
- The download page does not define "traced-only" or "significant-only". Check the README or the paper's Methods.
- The full Cell citation (author list, volume, pages, DOI) is not in the sources I read. Only the article ID S0092-8674(26)00942-6 is known.

## Is a neuPrint token required? Is it free? Is there anonymous access?

### Takeaway
neuprint-python requires a token (`Client(..., token=...)` or the env var `NEUPRINT_APPLICATION_CREDENTIALS`). The token comes from signing in to neuprint.janelia.org with a Google account (Account → Auth Token), and per community docs it is free. The dataset-metadata endpoint answers without a token. Bulk data is available without any token at all, via the GCS bucket above.

### Cited Findings
- The token is copied from the Account menu after signing in to neuPrint. It is passed via `token=` or `export NEUPRINT_APPLICATION_CREDENTIALS=<token>`. Docs are for neuprint-python 0.6.4. Example: `Client('neuprint.janelia.org', dataset='hemibrain:v1.2.1', token=...)`, then `c.fetch_custom(cypher)` — [neuprint-python quickstart](https://connectome-neuprint.github.io/neuprint-python/docs/quickstart.html)
- Sign-in uses a Gmail/Google account, and you may be able to register a Gmail address without an authentication process — [neuprintr README](https://github.com/natverse/neuprintr). Token at neuprint.janelia.org/account — [debivort lab script](https://lab.debivort.org/odor-loci-of-individuality/OLOI_AL_model/connectomics/hemibrain_access_token.py)
- The download page says: neuPrint API requires a free account and token — [MaleCNS Downloads](https://male-cns.janelia.org/download/)
- **My test (2026-10-23):** `GET https://neuprint.janelia.org/api/dbmeta/datasets` without a token returns HTTP 200 and the list of datasets (metadata only).

### Inferences
- Treat neuPrint as optional: only for convenience (ROI-split queries, `fetch_adjacencies`, `NeuronCriteria`). Everything needed for a connectivity model is in the Feather files. The agent did not create an account; the user has to do the Google sign-in themselves if they want neuPrint.
- If a token is needed, the minimal steps are: open neuprint.janelia.org → Login (Google) → Account → copy Auth Token → `export NEUPRINT_APPLICATION_CREDENTIALS=...` → `Client('neuprint.janelia.org', dataset='male-cns:v1.0')`.

### Gaps
- I did not test whether `/api/custom/custom` (Cypher) works without a token. By the documentation it does not.
- I found no official neuPrint page with the current terms of service or account approval rules as of 2026.

## Data schema (neurons, connections, NT, confidence)

### Takeaway
I read the schemas straight from the Arrow headers of the v1.0 files, using an HTTP Range request for the first 256 KB, without downloading the files. Neurons are keyed by `bodyId`/`body` (int64). Connections are `body_pre, body_post, weight` (weight = synapse count). NT comes in 7 classes with per-neuron and per-type confidence, plus `consensus_nt`.

### Cited Findings (schemas read directly from the files at [flat-connectome](https://storage.googleapis.com/storage/v1/b/flyem-male-cns/o?prefix=v1.0/connectome-data/flat-connectome/&fields=items(name,size,updated)))
- **body-annotations** (no NT): `bodyId:int64, type, instance, group:double, somaSide, rootSide, superclass, class, subclass, supertype, flywireType, hemibrainType, mancType, mancBodyid:double, mancGroup:double, mancSerial, mcnsSerial, serialMotif, statusLabel (dict), status, vfbId, itoleeHl, trumanHl, birthtime, synonyms, dimorphism, matchingNotes, fruDsx, entryNerve, exitNerve, somaNeuromere, receptorType, somaLocation:list<int64>, tosomaLocation:list<int64>, assignedOlHex1, assignedOlHex2`
- **body-neurotransmitters**: `body:int64, cell_type, total_nt_predictions:int32, predicted_nt, predicted_nt_confidence:double, ground_truth, celltype_total_nt_predictions:int32, celltype_predicted_nt, celltype_predicted_nt_confidence:double, consensus_nt`
- **connectome-weights**: `body_pre:int64, body_post:int64, weight:int64`
- **body-stats**: `body, pre:int32, post:int32, status_fine, superclass, class, type, instance, downstream, synweight, rank`
- **tbar-neurotransmitters** (per synapse): `point_id, x, y, z, conf, sv, body, major, primary, nt_acetylcholine_prob, nt_dopamine_prob, nt_gaba_prob, nt_glutamate_prob, nt_histamine_prob, nt_octopamine_prob, nt_serotonin_prob, split`. So there are **7 NT classes: acetylcholine, dopamine, GABA, glutamate, histamine, octopamine, serotonin**. There is no tyramine class.
- **syn-partners**: `x_pre, y_pre, z_pre, body_pre, conf_pre, x_post, y_post, z_post, body_post, conf_post, primary_post`. **syn-points** has `kind` (PreSyn/PostSyn), body, ROI, xyz in 8 nm voxels — [Downloads](https://male-cns.janelia.org/download/)
- Per-neuron NT aggregation is described in the manuscript's Methods — [Downloads](https://male-cns.janelia.org/download/)
- For comparison, MANC v1.0 (`manc-v1.0-neuron-properties.feather`, read from its header) is camelCase with per-neuron NT probabilities: `predictedNt, predictedNtProb, ntAcetylcholineProb, ntGabaProb, ntGlutamateProb, ntUnknownProb`, plus `type, instance, systematicType, class, subclass, hemilineage, somaNeuromere, entryNerve, exitNerve, target, origin, serial, serialMotif, group, somaSide, rootSide, roiInfo (struct per ROI), inputRois, outputRois, status, cropped` — [flyem-manc-exports](https://storage.googleapis.com/storage/v1/b/flyem-manc-exports/o?prefix=v1.0/)

### Inferences
- The MaleCNS Feather files use snake_case (`body_pre`). neuPrint/neuprint-python uses camelCase (`bodyId_pre`, `bodyId_post`, `weight`, `predictedNt`, `consensusNt`). Map the names when switching between the two.
- For a model, use `consensus_nt` (per type) as the synapse sign: ACh = excitatory; GABA = inhibitory; Glu is usually inhibitory in the central brain (GluCl), but that is general knowledge and not taken from these sources. Then use `predicted_nt_confidence` as a filter.
- MANC has only 3 NT classes plus unknown in its properties table. MaleCNS has 7.

### Gaps
- The definitions of `ground_truth`, `split`, `major`/`primary`, and the exact rule behind `consensus_nt` (threshold or vote) are not on the download page. They are in the Methods of the Cell paper, which I did not read.
- I did not download any whole file, so there are no value distributions or row counts. Codex gives 166,700 neurons and 6,242,118 connections for MCNS v1.0 — [Codex](https://codex.flywire.ai/api/download)

## Do LC10a, AOTU019, AOTU025, DNa02 and leg MNs (Ti flexor, ltm) exist under these names?

### Takeaway
Confirmed in MaleCNS by individual VFB pages: **LC10a** (`type=LC10a`, `flywireType=LC10a`), **Ti flexor MN**, **Ti extensor MN** and **ltm1-tibia MN** (the latter as `type` and `mancType`, superclass `vnc_motor`). Leg MNs are named after the muscle (`Ti flexor MN`, `ltm1-tibia MN`, `tpn MN`), not with `IN..`. The `INxxAnnn` codes are MANC's systematic names for interneurons. **DNa02, AOTU019 and AOTU025 were not confirmed** by any MaleCNS-specific source I found.

### Cited Findings
- LC10a_L (MaleCNS:26963): type LC10a, flywireType LC10a, visual_projection, cholinergic, CC-BY 4.0, data from v0.9 — [VFB LC10a_L](https://www.virtualflybrain.org/term/lc10a_l-malecns26963-vfb_jrmc25kr/); also [LC10a_R 22750](https://www.virtualflybrain.org/term/lc10a_r-malecns22750-vfb_jrmc25kc/), [LC10a_R 86507](https://www.virtualflybrain.org/term/lc10a_r-malecns86507-vfb_jrmc25nw/). Other subtypes exist too: LC10c-1, LC10c-2, LC10e — [VFB LC10c-1](https://www.virtualflybrain.org/term/lc10c-1_r-malecns40738-vfb_jrmc25vw/)
- Ti flexor MN_L (MaleCNS:819112): type = mancType = "Ti flexor MN", superclass vnc_motor, soma in the metathoracic neuromere, "tibial depressor motor neuron" in the FBbt ontology, male-cns v0.9 — [VFB Ti flexor MN_L](https://www.virtualflybrain.org/term/ti-flexor-mn_l-malecns819112-vfb_jrmc0nn2/)
- ltm1-tibia MN (MaleCNS:858248 L, 914837 R, 803523 R): mancType "ltm1-tibia MN", NB2-3 lineage, pretarsal depressor muscle (long tendon muscle), T2/T3 — [VFB ltm1-tibia MN_L](https://www.virtualflybrain.org/term/ltm1-tibia-mn_l-malecns858248-vfb_jrmc02tz/), [_R 914837](https://www.virtualflybrain.org/term/ltm1-tibia-mn_r-malecns914837-vfb_jrmc02u2/), [_R 803523](https://www.virtualflybrain.org/term/ltm1-tibia-mn_r-malecns803523-vfb_jrmc02u3/)
- Ti extensor MN (tibial levator MN) — [VFB Ti extensor MN_L](https://www.virtualflybrain.org/term/ti-extensor-mn_l-malecns801234-vfb_jrmc0nmn/); tpn MN — [VFB tpn MN_L](https://www.virtualflybrain.org/term/tpn-mn_l-malecns801185-vfb_jrmc02zt/)
- "Ti-ltm: Tibia-long tendon muscle" as an axon bundle label in the 2019 developmental paper on leg MNs — [eLife/PMC6391070](https://pmc.ncbi.nlm.nih.gov/articles/PMC6391070/figure/fig1)
- In MANC, the muscle targets of T1 leg MNs were matched to FANC (NBLAST), and serial homology identified targets for another 50% of leg MNs — [Cheong et al. eLife RP 96084](https://elifesciences.org/reviewed-preprints/96084v2/figures)
- DNa02 is in the FBbt ontology (Namiki 2018): one neuron per hemisphere, ipsilateral, LAL/PS etc. → T1–T3 leg neuropils. The left-right difference in DNa02 activity is linearly related to turning ("see-saw" model) — [VFB FBbt_00047573](https://www.virtualflybrain.org/term/descending-neuron-of-the-anterior-dorsal-brain-dna02-fbbt_00047573/); [eLife 102230](https://elifesciences.org/articles/102230v1). Searches turned up MaleCNS pages for DNc02 and DNd02, but not DNa02 — [VFB DNd02](https://www.virtualflybrain.org/term/dnd02sad039_l-malecns11160-vfb_jrmc37op/)
- The MaleCNS annotation table has the columns `flywireType`, `hemibrainType` and `mancType`, plus `synonyms`. A name from FlyWire or hemibrain can be looked up in several columns — schema (above).

### Inferences
- DNa02, AOTU019 and AOTU025 are hemibrain/FlyWire types. MaleCNS is matched to FlyWire (the `flywireType` column), so it is very likely they exist under the same names. That is unconfirmed. The check, with no token, takes one ~14 MB file:
  `a=pd.read_feather(URL_annotations); a[a.type.isin(["LC10a","AOTU019","AOTU025","DNa02"])|a.flywireType.isin([...])|a.hemibrainType.isin([...])]`
- For leg MNs, filter `superclass=="vnc_motor"` and `type.str.contains("Ti flexor|ltm|Ti extensor")`. Use `somaNeuromere`/`exitNerve` to pick the leg (T1/T2/T3) and `somaSide` for the side.

### Gaps
- No primary source confirms DNa02, AOTU019 or AOTU025 in MaleCNS v1.0. VFB shows v0.9, and names may have changed in v1.0, because the v1.0 release notes say "refinement of neuron annotations".
- I have no full list of MANC MN types (e.g. other "ltm2-femur MN" types and naming variants). It is in Cheong et al. 2024 or `type` in MANC, which I did not download.

## Alternatives: MANC, FlyWire FAFB, BANC (URLs and licenses)

### Takeaway
MANC v1.0 has a public bucket `gs://flyem-manc-exports/v1.0/` (Feather/CSV, 2023). MANC v1.2.1 is in neuPrint (`manc:v1.2.1`), but the bucket has only v1.0. FlyWire FAFB v783 is on Zenodo 10.5281/zenodo.10676866, CC-BY-4.0, public, Feather. BANC v888 is visible on Codex, but I did not verify any bulk download for it.

### Cited Findings
- MANC: neuPrint `manc:v1.2.1` and `manc:v1.0`. v1.0 released 2023-06-06, v1.2 on 2024-03-11. Bucket `flyem-manc-exports`, neuroglancer `gs://manc-seg-v1p2/manc-v1.2.3-neuprint-layers.json`. CC-BY 4.0. Papers: Takemura et al. ([eLife RP 97769](https://elifesciences.org/reviewed-preprints/97769)), Marin et al. ([RP 97766](https://elifesciences.org/reviewed-preprints/97766/)), Cheong et al. ([RP 96084](https://elifesciences.org/reviewed-preprints/96084)) — [Janelia MANC](https://www.janelia.org/project-team/flyem/manc-connectome)
- **Verified listing** of `https://storage.googleapis.com/flyem-manc-exports/v1.0/...` (only the `v1.0/` prefix exists): `manc-v1.0-neuron-properties.feather` (17,188,218 B); `manc-traced-adjacencies-v1.0/traced-neurons.csv` (629,548 B), `traced-connections.csv` (75,262,163 B), `traced-connections-per-roi.csv` (159,195,790 B) plus a README; `neuprint_manc_v1.0/neuprint_manc_v1.0_ftr/Neuprint_Neurons_manc_v1.ftr` (917,907,106 B), `Neuprint_Neuron_Connections_manc_v1.ftr` (736,271,930 B) and others; `neuprint_manc_v1.0_csv.tar.gz` (5.29 GB); `manc-synapse-partners-2023-05-03-215e08-minconf-0.0.feather.bz2` (1.12 GB) — [GCS listing](https://storage.googleapis.com/storage/v1/b/flyem-manc-exports/o?prefix=v1.0/&fields=items(name,size,updated))
- FlyWire Zenodo 10676866 "FlyWire Whole-brain Connectome Connectivity Data", v783.0, 2024-06-02, **license cc-by-4.0** (from the Zenodo API). Files: `proofread_connections_783.feather` (852,022,274 B), `flywire_synapses_783.feather` (9.49 GB), `per_neuron_neuropil_count_pre_783.feather` (16.9 MB), `..._post_783.feather` (234 MB), `proofread_root_ids_783.npy` (1.1 MB) — [Zenodo 10676866](https://zenodo.org/records/10676866), [API](https://zenodo.org/api/records/10676866)
- FlyWire skeletons + NBLAST: Zenodo 10877326 (v2, 2024-03-27, ~6.6 GB). Annotations (types, NT, side) are on GitHub `flyconnectome/flywire_annotations` — [Zenodo 10877326](https://zenodo.org/record/10877326); [flywire_annotations](https://github.com/flyconnectome/flywire_annotations)
- Codex lists FAFB v783 (139,255 neurons), BANC v888 (158,262), MANC v1.2.1 (23,665), MAOL v1.1 (52,445), MCNS v1.0 (166,700). "Download Data" on Codex requires Google sign-in — [Codex download](https://codex.flywire.ai/api/download)

### Inferences
- For the brain-to-legs pathway (LC10a → AOTU → DN → VNC → leg MNs), **MaleCNS v1.0 alone is enough**: brain and VNC in one animal, with no cross-dataset matching. MANC/FlyWire are useful as validation (the `mancType`/`flywireType` columns give the matching for free).
- If MANC v1.2.1 is needed in bulk without a token: use the MANC v1.0 bucket, or the VNC part of MaleCNS. The MANC v1.0 properties have no `consensusNt` and only 3 NT classes.

### Gaps
- BANC: I did not verify the bulk download URL or the license (not checked within the call budget).
- FlyWire Codex terms of use beyond CC-BY on Zenodo: the FlyWire paper mentions community principles of access — [search result, Nature Methods/FlyWire](https://link.springer.com/article/10.1038/s41592-021-01330-0) — not read in detail.

## Licensing

### Takeaway
MaleCNS v1.0: CC-BY 4.0. MANC: CC-BY 4.0. FlyWire v783 (Zenodo): CC-BY 4.0. All of them require attribution (citing the papers). None of them restricts commercial or competition use.

### Cited Findings
- MaleCNS: "licensed under CC-BY" (CC BY 4.0) — [male-cns.janelia.org](https://male-cns.janelia.org/), [Downloads](https://male-cns.janelia.org/download/); VFB pages for MaleCNS neurons: CC-BY_4.0 — [VFB Ti flexor MN_L](https://www.virtualflybrain.org/term/ti-flexor-mn_l-malecns819112-vfb_jrmc0nn2/)
- MANC: CC-BY 4.0 — [Janelia MANC](https://www.janelia.org/project-team/flyem/manc-connectome)
- FlyWire v783 connectivity: `cc-by-4.0` — [Zenodo API 10676866](https://zenodo.org/api/records/10676866)

### Inferences
- CC-BY 4.0 allows derived works (e.g. a controller for SO-101 trained or built on the connectome) on the condition of attribution: cite the Cell 2026 paper for MaleCNS, Takemura/Marin/Cheong for MANC, and the FlyWire Nature 2024 papers.

### Gaps
- Licenses for the code tools (neuprint-python, natverse) and for BANC were not checked.
