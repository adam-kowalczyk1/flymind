# Seed registry — FlyMind research programme V5 v4.1 → V7 (registered 2026-10-30 ~08:37, BEFORE any run of this programme)

All pools below are EXPLORATORY (diagnostic / parameter studies). None is a confirmatory pool. No confirmatory test is run in this
programme; any future confirmatory test needs a new pool and explicit user approval.

Collision check (2026-10-30 ~08:35): regex `\b8[4-7][0-9]_?[0-9]{3}_?[0-9]{3}\b` over flymind/ and bio2/ (*.py, *.json, *.md, *.txt, *.jsonl):
0 matches. Forbidden pools (never used here): 0–39, 300–399, 1001–1999, 2001–2005, 2011–2100, 3001–3100, 4001–4450, 5001–5010,
6001–6010 and all their derived offsets (+100 000, +200 000, +400 000, +500 000), RNG seeds 2201, 2202, 3301, 3401, 3402, 7001, 7002,
7101, 9401, 9402, 9501. In particular the V5 v4 SWS instances (404 001–404 450) are NOT recreated: V5 v4.1 uses fresh instances.

| Pool | Range | Use | Stage |
|---|---|---|---|
| SWS v2 instances | 8 410 001 – 8 410 050 | `side_shuffle.shuffle_within_side(spec, layer_side_labels, seed)` — 50 independent networks | V5 v4.1 (+ reused as the SWS family in v4.2, V6, V6.1, V7 — explicitly shared, not silent) |
| ALIF noise reps | 8 411 001 – 8 411 016 | `alif.ALIF(spec, P, seed)` noise stream for repetition r (common random numbers across networks) | open-loop parts of all stages |
| random initial v | 8 412 001 – 8 412 016 | initial membrane potentials (E5) | V5 v4.1, V6 |
| analysis RNG | 8 419 001 – 8 419 099 | bootstrap / permutation in analysis scripts | all stages |
| block-shuffle instances | 8 42b 001 – 8 42b 050, b = 1..5 | b=1 LC×LC, 2 LC→mid, 3 mid→LC, 4 mid×mid, 5 all blocks (re-implementation check) | V5 v4.2 |
| closed-loop scenes (+ ALIF noise of the trial) | 8 600 001 – 8 600 999 | MuJoCo scenes | V6 |
| closed-loop scenes | 8 610 001 – 8 610 999 | MuJoCo scenes | V6.1 |
| closed-loop scenes | 8 700 001 – 8 700 999 | MuJoCo scenes | V7 |
| smoke tests | 8 490 001 – 8 490 099 | pipeline checks only, never analysed | all stages |
| decoder calibration (ALIF noise) | 8 601 001 – 8 601 003 | `v5v4.calibrate(spec, idx, seeds=…)` under V6/V6.1/V7 parameter variants (same procedure as V5 v4) | V6, V6.1, V7 (added 2026-10-30 ~08:50, before any closed-loop run) |
| red-team / independent re-simulation | 8 495 001 – 8 495 999 | noise seeds or extra instances used by red-team agents for their own checks (each agent records what it used) | all stages (added 2026-10-30 09:16) |
| red-team pool (v4.2 RT) | 8 496 001 – 8 496 999 | same use as 8 495 xxx, V5 v4.2 red team | added 2026-10-30 12:15 |
| V5 v4.3 replay manipulations | 8 430 001 – 8 430 999 | RNG for jitter / circular shifts / Poisson surrogates (seed = 8 430 000 + 100·variant + rep) | V5 v4.3 (added 2026-10-30 ~12:40, before any v4.3 run) |
| red-team pool (v4.3 RT) | 8 497 001 – 8 497 999 | red-team checks of V5 v4.3 | added 2026-10-30 12:35 |
| V6m manipulation RNG | 8 440 001 – 8 440 999 | jitter / circular shift / Poisson surrogates of LC10a or intermediate trains (seed = 8 440 000 + 100·variant + rep) | V6m mechanism study (added 2026-10-30 ~15:00, before any V6m run) |
| V6m synthetic synchrony generator | 8 441 001 – 8 441 999 | shared-event surrogate LC10a trains (seed = 8 441 000 + 300·level_index + 150·side_index + 10·grid_index + rep) | V6m Exp 4 (added 2026-10-30 ~15:00) |
| V6m fresh noise reps (replication) | 8 442 001 – 8 442 016 | ALIF noise streams for the V6m replication set (with B1 instances 8 421 011–020, not used in V5 v4.3) | V6m (added 2026-10-30 ~15:00) |
| red-team pool (V6m RT) | 8 498 001 – 8 498 999 | red-team checks of V6m | added 2026-10-30 ~15:00 |
| V6m2 noise + bias calibration | 8 443 001 – 8 443 999 | MAIN noise 001–008, MAIN bias calibration 101–104, arm noise 201–208, arm calibration 301–304 | V6m2 (added 2026-10-30 ~15:35, before any V6m2 run) |
| V6m2 manipulation RNG | 8 444 000 (SeedSequence base) | SeedSequence([8 444 000, arm, variant, level, side, rep, source]) for MCIRC / MASYNC | V6m2 (added 2026-10-30 ~15:35) |
| V6m3 noise + calibration | 8 445 001 – 8 445 999 | MAIN noise 001–008, calibration 101–104, replication noise 201–208 | V6m3 (added 2026-10-30, before any V6m3 run) |
| V6m3 count-swap RNG | 8 446 000 (SeedSequence base) | SeedSequence([8 446 000, set, level, side, rep, source, block]) | V6m3 |
| red-team pool (V6m3 RT) | 8 499 001 – 8 499 999 | red-team checks of V6m3 | added 2026-10-30, before any V6m3 run |

Erratum (2026-10-30 17:58): the "added ~15:00" (V6m) and "~15:35" (V6m2) times above are wrong clock estimates; file times show the V6m
pools were registered before the V6m run (14:43) and the V6m2 pools before the V6m2 jobs (15:26). The ordering "registered before any run"
holds; the clock values do not.
