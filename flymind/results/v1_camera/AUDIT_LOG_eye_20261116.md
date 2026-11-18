# Dziennik pracy — oko muchy (16 XI 2026)

| godz. | krok | dowód | etykieta |
|---|---|---|---|
| 14:27 | Bramka r1 (MaleCNS, parametry jednakowe) zapisana i uruchomiona | gate/PRE_GATE_HASHES.txt, GATE_RESULT_20261116.md | G1 PASS, G2/G3 FAILED — VERIFIED |
| 14:57 | Bramka r2 (stałe czasowe z literatury) | gate_r2/GATE_RESULT_r2_20261116.md | G2/G3 FAILED — VERIFIED |
| 15:49 | flyvis 1.2.0 zainstalowany (envs/flyvis), modele pobrane oficjalnym skryptem, sha256 zgodne; plan bramki zapisany | gate_flyvis/PRE_GATE_HASHES.txt | VERIFIED |
| 20:55 | Bramka flyvis, 50 modeli | gate_flyvis/GATE_RESULT_flyvis_20261116.md | G2-fv, G3-fv PASS — VERIFIED |
| 21:00 | Eksploracja: kierunki T4/T5 modelu 000 moimi krawędziami (T5 silne, DSI 0,48–0,77 → słabe T5 w bramce to skutek miary flyvis, INFERRED); osie Mi9→Mi4 w MaleCNS; obrót map 30° | PREREG_BRIDGE.md §„Co zostało ustalone” | VERIFIED (liczby), REPORTED (znak z literatury) |
| 21:10 | Ramiona LPLC2 w MaleCNS zgodne z kierunkami flyvis (180°, −11°, 92°, −95°) | PREREG_BRIDGE.md | VERIFIED |
| 21:15 | Próba dymna modele 40–41: poprawka bodźca (skok przy pojawieniu się); odczyt liniowy nie odrzuca przesuwania | PREREG_BRIDGE.md | VERIFIED (dym) |
| 21:21 | Plan B1 zapisany, sumy plików | bridge_b1/PRE_BRIDGE_HASHES.txt | — |
| 21:22 | Test B1 uruchomiony (modele 000–009, mapy 30° i 210°) | bridge_b1/run_rot*.log | w toku |

Ziarna: brak (flyvis i odczyt deterministyczne). Wspólne moduły: bez zmian. Commit: brak (czeka na zgodę Adama).
| 17 XI 06:31 | B1 zakończony (drugi przebieg do 06:31 — komputer spał); sumy po teście zgodne | bridge_b1/B1_RESULT_20261117.md | B1 FAILED (ciemny: wygrane 59 %, 5./24) — VERIFIED; jasny dysk spełnia 3/3 — raport |
| 17 XI 06:33 | B1b zapisany (jasny dysk, nowe modele 010–019, kod bez zmian), uruchomiony | bridge_b1b/PRE_B1b_HASHES.txt | w toku |
| 17 XI | B1b zakończony; sumy po teście zgodne | bridge_b1b/B1b_RESULT_20261117.md | B1b FAILED (jasny: LI 0,089, wygrane 63 %, 1./24) — VERIFIED. STOP na polecenie Adama |
