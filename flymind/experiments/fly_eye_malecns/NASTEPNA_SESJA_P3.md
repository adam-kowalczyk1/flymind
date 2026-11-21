# Dla następnej sesji: ocena P3 (oko flyvis uczone na połączeniach MaleCNS)

Stan 21 XI 20:45: 4 uczenia w tle (nohup), `data/flyvis/results/p3_malecns/9200/000–003` (000, 001 prawdziwe; 002, 003
potasowane), logi `flymind/results/fly_eye_malecns_20261120/p3_main_k.log`, ~3,6 s/krok. Plan: `PREREG_P3.md`.
1. ~23 XI: bramka G0 na modelu 000 po 50 000 krokach (`loss.h5`: średnia ostatnich vs pierwszych 1000 kroków < 0,8; brak NaN).
   FAILED → zatrzymać wszystkie (`pkill -f p3_train.py`), zapisać wynik.
2. ~25 XI wieczór (100 000 kroków, decyzja Adama): wczytać punkt kontrolny 100k każdego modelu, K1 = DSI T4/T5 jak w
   `t1_transplant.py` (`responses(net)` + `direction_selectivity_index`), K2 = strata walidacyjna vs flyvis 000–003,
   K3 = prawdziwe vs potasowane. Potem zatrzymać uczenie. Wynik → `WYNIK_P3.md`, commit + push (bez *.npz).
Wznowienie po przerwie: `RESUME=true flymind/experiments/fly_eye_malecns/run_p3_main.sh`.
