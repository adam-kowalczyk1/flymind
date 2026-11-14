# Seed registry — bio_advantage

Checked on 2026-11-11: no seed of the form 19 xxx xxx appears in any `SEED_REGISTRY.md` / `v5v4_seed_registry.md`
or in any `.md`, `.py`, `.sh`, `.txt` file under `flymind/`.

| Range | Stage | Use | State |
|---|---|---|---|
| 19 100 000 – 19 100 999 | D0 (data only) | permutation tests and edge-swap shuffles; exact seeds in `d0_analysis.py` | **consumed** 2026-11-11 (run `results/bio_advantage/d0_v1`): 19 100 001, 19 100 090–091, 19 100 101–200 used; rest of the range retired |

Do not reuse these seeds for any confirmatory purpose.

## Reservations added 2026-11-11 (pre-registration drafts E2 and E1 — nothing run yet)

Checked the same day: no seed of the form 19 2xx xxx or 19 3xx xxx appears in any registry or in any `.md`, `.py`, `.sh`,
`.txt` file under `flymind/` outside this folder and `flymind/reports/`.

| Range | Stage | Use | State |
|---|---|---|---|
| 19 200 000 – 19 200 999 | E2 (transfer curve) | 19 200 001 bootstrap only; E2 re-uses benchmark scene seeds 100 000–100 442 and rebuilds shuffles 17 100 011–020 (see `E2_PREREG.md` §4, §7) | reserved, unused |
| 19 300 000 – 19 399 999 | E1 (spatial-map reflex) | development scenes 19 300 000–199; confirmatory 19 310 000–199 (right), 19 311 000–199 (left); restart pool 19 312 000–199, 19 313 000–199; N1 shuffles 19 320 001–020, 19 321 001–020; N2 19 322 001–010; noise = scene seed + 50 000; bootstrap 19 390 001 | reserved, unused |
