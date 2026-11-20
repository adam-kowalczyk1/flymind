# T2c — przewaga prawdziwego okablowania przy zbliżaniu na fakturze: **FAILED** (20 XI 2026)

Kryterium (PREREG_T2c.md): AUC(prawdziwe) − AUC(potasowane) dla zbliżań na fakturze ≥ 0,10 w ≥ 5 z 6 modeli (003–008).
Wynik: **1 / 6** (t2c_result.json).

| model | faktura: prawdziwe | potasowane | różnica | AUC test całe: prawdziwe / potasowane |
|---|---|---|---|---|
| 003 | 0,41 | 0,36 | +0,05 | 0,77 / 0,74 |
| 004 | 0,76 | 0,33 | **+0,43** | **0,90** / 0,72 |
| 005 | 0,29 | 0,46 | −0,17 | 0,71 / 0,78 |
| 006 | 0,42 | 0,42 | +0,00 | 0,73 / 0,77 |
| 007 | 0,42 | 0,41 | +0,02 | 0,77 / 0,76 |
| 008 | 0,54 | 0,45 | +0,10 (0,099) | 0,81 / 0,78 |

Średnia różnica +0,07, mediana +0,03. Przewaga widziana po fakcie w T2 v2 (modele 000, 001) się nie potwierdziła —
była głównie przypadkiem. Łącznie na 9 modelach: AUC test ≥ 0,90 tylko raz (model 004).
