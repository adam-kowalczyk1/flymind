# Bramka — opcja 2: flyvis (Lappalainen i in. 2024), zapisane PRZED pełnym uruchomieniem (16 XI 2026)

Po porażkach r1 i r2. Decyzja Adama: opcje na zmianę. Zainstalowane: flyvis 1.2.0 (PyPI) w `envs/flyvis`
(osobne środowisko, 1,5 GB, Python 3.12); gotowe modele `results_pretrained_models.zip` i `results_umap_and_clustering.zip`
z Google Drive autorów oficjalnym skryptem pakietu, sumy sha256 zgodne, 9,3 MB, w `data/flyvis` (pomijane przez git).
Próba dymna: model 000 (sprawdzenie API, bez oceny).

To NIE jest nasz konektom: flyvis używa konektomu FIB-SEM (fib25/fib19, samica), 65 typów, siatka 721 kolumn, neurony
nieimpulsowe, **parametry dopasowane przez autorów** (zadanie przepływu optycznego). Bramka sprawdza, czy ta gotowa część
daje działające czujniki ruchu, zanim połączę ją z MaleCNS.

- Modele: ensemble `flow/0000`, modele 000–049 (wszystkie 50, bez wyboru).
- Bodziec: `moving_edge_responses` z domyślnymi ustawieniami flyvis (krawędzie ON/OFF, 12 kierunków, 6 prędkości).
- DSI: `direction_selectivity_index` flyvis (średnia po prędkościach); T4 na ON (intensity 1), T5 na OFF (0).
- **G2-fv:** ≥ 3/4 podtypów T4 z medianą DSI (po 50 modelach) ≥ 0,20. T5 tak samo, raportowane.
- **G3-fv:** ≥ 3/4 podtypów T4 z medianą odległości kąta preferowanego od znanego z literatury
  (`angular_distance_to_known`) ≤ 30°.
- Bez tasowań (konektom flyvis nie jest naszym; kontrolą jest r1/r2 na MaleCNS). Kod: `flyvis_gate.py`.
Przejdzie → następny krok: most flyvis T4/T5 → MaleCNS (LPLC4 → DNp07 → noga), osobny cel.
