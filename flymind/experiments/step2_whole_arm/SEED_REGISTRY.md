# Rejestr ziaren — krok 2 (całe ramię z dwóch obwodów nóg)

Zakres zarezerwowany dla kroku 2: **20 000 000 – 20 999 999** (sprawdzone 2026-11-13: brak użycia w innych SEED_REGISTRY.md
pod flymind/; najwyższe wcześniej użyte to 19 399 999).

| Ziarna | Użycie | Data | Status |
|---|---|---|---|
| 20 000 001 – 20 000 005 | neuron_report.py: f–I z szumem σ = 2 mV (pojedynczy neuron) | 2026-11-13 | ZUŻYTE (v1 i v2 — ten sam przebieg, deterministyczny) |
| 20 000 010 | tick_cost.py: szum drogi wzrokowej przy pomiarze czasu taktu (wynik czasu, nie zachowania) | 2026-11-13 | ZUŻYTE |
| 20 101 000 – 20 101 449 | (b) TRENING: ziarna scen `--seed 20101` (45 przedmiotów × 1 poza) | 2026-11-13 | w użyciu (pętla) |
| 20 110 001 – 20 110 002 | (b) TRENING: tasowania S1–S2 | 2026-11-13 | w użyciu (pętla) |
| 20 201 000 – 20 201 449 | (b) TEST: ziarna scen `--seed 20201` (45 × 3 pozy) — RAZ, na końcu | 2026-11-13 | zarezerwowane |
| 20 210 001 – 20 210 005 | (b) TEST: tasowania S1–S5 | 2026-11-13 | zarezerwowane |
| 20 299 999 | (b) bootstrap przedziałów ufności | 2026-11-13 | zarezerwowane |
| 100 (istniejące) | iteracja 0: regresja ramienia K wobec B_fly_search_glu-1_v1 (te same ziarna co historyczny wynik, ponowne użycie do porównania co do bitu) | 2026-11-13 | ponowne użycie |
| 20 300 000 – 20 999 999 | podzielone 2026-11-13 18:15 (przed pierwszym przebiegiem stawów c–e, ramienia, konfliktu) — poniżej | — | — |
| 20 301 000 – 20 301 449 / 20 310 001 – 002 | (c) elbow_flex TRENING: sceny `--seed 20301` / tasowania S1–S2 | 2026-11-13 | w użyciu (pętla) |
| 20 401 000 – 20 401 449 / 20 410 001 – 005 / 20 499 999 | (c) TEST `--seed 20401` ×3 pozy / S1–S5 / bootstrap — RAZ | 2026-11-13 | zarezerwowane |
| 20 501 000 – 20 501 449 / 20 510 001 – 002 | (d) wrist_flex TRENING `--seed 20501` / S1–S2 | 2026-11-13 | w użyciu (pętla) |
| 20 601 000 – 20 601 449 / 20 610 001 – 005 / 20 699 999 | (d) TEST `--seed 20601` / S1–S5 / bootstrap — RAZ | 2026-11-13 | zarezerwowane |
| 20 701 000 – 20 701 449 / 20 710 001 – 002 | (e) wrist_roll TRENING `--seed 20701` / S1–S2 | 2026-11-13 | w użyciu (pętla) |
| 20 801 000 – 20 801 449 / 20 810 001 – 005 / 20 899 999 | (e) TEST `--seed 20801` / S1–S5 / bootstrap — RAZ | 2026-11-13 | zarezerwowane |
| 20 951 000 – 20 951 449 | (5) całe ramię: iteracja 0 / kontrola uruchomienia `--seed 20951` | 2026-11-13 | w użyciu |
| 20 901 000 – 20 901 449 / 20 910 001 – 005 / 20 949 999 | (5) całe ramię TEST `--seed 20901` / S1–S5 / bootstrap — RAZ | 2026-11-13 | zarezerwowane |
| 20 961 000 – 20 961 449 | (7) konflikt bodźców: pilot/kalibracja bodźca `--seed 20961` | 2026-11-13 | w użyciu |
| 20 971 000 – 20 971 449 / 20 980 001 – 005 / 20 990 000 – 20 990 999 / 20 999 999 | (7) TEST `--seed 20971` / tasowania / szum drogi wzrokowej / bootstrap — RAZ | 2026-11-13 | zarezerwowane |
| 20 952 001 | (5) iteracja 0 całego ramienia: tasowanie S1 (zamiast omyłkowo użytego 20 910 001 — przerwane przed zapisem) | 2026-11-13 19:30 | ZUŻYTE |
| 20 952 002 – 20 960 999, 20 972 000 – 20 979 999 | wolne (rezerwa) | — | WOLNE |
