# T2c — czy prawdziwe okablowanie MaleCNS pomaga przy zbliżaniu NA FAKTURZE (spisane PRZED liczeniem, 20 XI 2026)

Skąd: opis po T2 v2 (WYNIK_T2_v2.md) — potasowane okablowanie wykrywało dysk na szarym tle, ale nie na fakturze; prawdziwe
lepiej na fakturze (2 z 3 modeli). To jest hipoteza po fakcie, więc sprawdzam ją na NOWYCH modelach oka.

- Modele flyvis 003–008 (6, wybrane z góry). Napęd i uczenie BEZ zmian: `t2_drive.py orig real|shuffle M`, `t2_model.py … LPLC2 full`
  (uprząż v2, te same ziarna startów 24 104 201–203; ziarno tasowania 24 104 300 + model).
- Miara (`t2c_eval.py`, napisany przed przebiegiem): AUC zbliżań na fakturze (Tloomtex_* i Tloomself_*, 8 bodźców) wobec
  wszystkich negatywów testu (24 bodźce).
- **PASS:** prawdziwe − potasowane ≥ 0,10 w ≥ 5 z 6 modeli. Raport też: AUC test całe, AUC czystych zbliżań, AUC trening.
- Po wyniku niczego nie stroję. Jeśli FAILED — przewaga z T2 v2 była przypadkiem.
