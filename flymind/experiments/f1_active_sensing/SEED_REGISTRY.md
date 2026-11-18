# F1 seed registry (registered 2026-11-01, before any F1 run)

Collision check 2026-11-01 (corrected after red team r1 M7 — the first regex required 9 digits and could not match these 7-digit seeds):
`grep -rEl '\b9[ _]?1[0-9]{2}[ _]?[0-9]{3}\b' flymind bio2` (*.py, *.json, *.md, *.txt, *.jsonl) → 3 files (results/v5v41, v5v42, v6
analysis.json), all matches are fraction digits of floats (e.g. 1.9109375, 31.9140625), not seeds → 0 seed uses. Positive control: the regex matches 9101001 (checked by red team r2).
Never used here: every pool in `flymind/program_v5v41/SEED_REGISTRY.md` (0–39, 300–399, 1001–1999, 2001–2100, 3001–3100, 4001–4450,
5001–5010, 6001–6010 and offsets, 8 4xx xxx, 8 6xx xxx, 8 7xx xxx, RNG 2201/2202/3301/3401/3402/7001/7002/7101/9401/9402/9501).

| Pool | Use |
|---|---|
| 9 101 001 – 9 101 060 | pilot units (0A). For every unit pool (pilot, confirm, robust), per unit u: ALIF noise seed u; pixel noise default_rng([u, 1]); stimulus default_rng([u, 2]); jitter default_rng([u, 3, crc32(condition name)]) (r3.1) |
| 9 102 001 – 9 102 600 | confirmatory units (0B/0C); only the first n (from confirm_params.json) are used |
| 9 103 001 – 9 103 200 | robustness units (0D); B1/SWS networks re-use the confirm instances; the same stimulus uniforms are reused across 0D variants (paired) |
| 9 104 001 – 9 104 010 | confirm B1 (LCxLC block shuffle) instances |
| 9 104 101 – 9 104 110 | confirm SWS v2 instances |
| 9 105 001 – 9 105 005 | pilot B1 instances |
| 9 105 101 – 9 105 105 | pilot SWS instances |
| 9 107 001 | analysis bootstrap RNG (confirm); 9 107 002 pilot; 9 107 003 robustness |
| 9 108 001 – 9 108 099 | smoke tests / unit tests, never analysed |
| 9 109 001 – 9 109 999 | red-team re-simulation |

## Stage 1 (closed loop) — RESERVED 2026-11-01, NOT USED (design d2, `stage1/STAGE1_DESIGN.md` §10; collision scan 9 111–9 119 xxx over flymind/ and bio2/: 0 hits)
| Pool | Use |
|---|---|
| 9 111 001 – 9 111 060 | Stage 1 pilot units |
| 9 112 001 – 9 112 400 | Stage 1 confirm units (first n) |
| 9 113 001 – 9 113 010 / 9 113 101 – 9 113 110 | Stage 1 confirm B1 / SWS instances |
| 9 113 201 – 9 113 205 / 9 113 301 – 9 113 305 | Stage 1 pilot B1 / SWS instances |
| 9 114 001 – 9 114 003 | Stage 1 decoder calibration (all networks) |
| 9 115 001 – 9 115 003 | Stage 1 analysis RNG (pilot, confirm, spare) |
| 9 118 001 – 9 118 099 | Stage 1 smoke / tests / feasibility |
| 9 119 001 – 9 119 999 | Stage 1 red team |

**Stage 1 status 2026-11-02:** CONSUMED — 9 111 001–060 (pilot), 9 112 001–400 (confirm, n = 400), 9 113 001–010, 101–110, 201–205, 301–305,
9 114 001–003, 9 115 001 (pilot analysis), 9 115 002 (confirm analysis), 9 115 003 (post-hoc `posthoc1.py`, exploratory),
smoke 9 118 001–003 / 010–029 / 040–041 / 050–053 / 060 / 090–091. Red team 9 119 xxx: only if the results red team re-simulates.

## Stage 1b (gated replication + harm) — RESERVED 2026-11-02, design d2 (`stage1b/STAGE1B_DESIGN.md` §7), NOT RUN
| Pool | Use |
|---|---|
| 9 121 001 – 9 121 200 | Stage 1b confirm units |
| 9 121 201 – 9 121 400 | reserved, unused |
| 9 123 001 – 9 123 002 | Stage 1b analysis RNG (+ spare) |
| 9 128 001 – 9 128 099 | Stage 1b smoke / tests / feasibility |
| 9 129 001, 002, 100 | CONSUMED: power/prediction planning |
| 9 129 003, 010–017 | CONSUMED: design red team r1 |
| 9 129 018 – 9 129 999 | further red teams |
