# Most B1b — potwierdzenie na jasnym dysku. Zapisane PRZED testem (17 XI 2026)

Hipoteza z raportu B1 (`flymind/results/v1_camera/bridge_b1/B1_RESULT_20261117.md`): dla jasnego, zbliżającego się dysku
odczyt LPLC2 przez połączenia MaleCNS jest wybiórczy dla zbliżania i zależy od prawdziwego układu podtypów.
Potwierdzam na **nowych modelach flyvis 010–019** (w B1 nieużyte; 10 kolejnych wg rankingu autorów, bez wyboru).

Kod, mapa (obrót 30°), bodźce, odczyt: identyczne jak B1 (`bridge_prep.py`, `bridge_loom.py`, `bridge_analysis.py`, sumy jak w
`bridge_b1/PRE_BRIDGE_HASHES.txt`). Wariant główny 1 (z hamowaniem LPi). Werdykt z pól `cases.pol1` pliku JSON
(pole `B1_pass` w JSON dotyczy ciemnego dysku i tu jest tylko raportem).

**B1b PASS**, gdy dla jasnego dysku spełnione są wszystkie trzy warunki: `median_LI_identity` > 0, `frac_loom_wins` ≥ 0,80 i `identity_beats_all_perms` = true.
Raport: ciemny dysk, wariant 0. Bez ziaren.
Przejdzie → plan B2 (LPLC2 → … → noga w MuJoCo, jasny zbliżający się obiekt). Nie przejdzie → efekt z B1 był przypadkiem.
