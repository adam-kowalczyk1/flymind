# FlyMind — odtworzenie wyników

Wszystko z katalogu repozytorium, zawsze `.venv/bin/python -I -B` (bez `__pycache__`, bez importu `bio2`).
Dane: `data/malecns/*-male-cns-v1.0-minconf-0.5.feather`. Wyniki zapisywane tylko do istniejącego `--out` (tryb „x”).

## Testy (V0)
```bash
for t in connectome snn_interface alif sensory decoder safety latency epg_ring encoder visual_path; do .venv/bin/python -I -B flymind/test_$t.py; done
```
```bash
.venv/bin/python -I -B flymind/test_so101.py --zgoda-sim
```

## Architektura (granice modułów)
| Warstwa | Moduł | Dane czy model |
|---|---|---|
| connectom | `connectome.py`, `visual_path.py` (wybór LC10a → pośrednie → DNa02), `epg_ring.py` | dane |
| synapsa → waga | `snn_interface.py` (J0, znak wg przekaźnika, `ModelEdge` osobno) | model |
| neuron | `alif.py` | model (parametry z literatury/bio2) |
| sensoryka | `sensory.py` (kontrakt klatki, bramka), `encoder.py` (detektor koloru → napęd LC10a) | model sensoryczny |
| odczyt | `decoder.py` (DNa02 L−P → ω) | model (kalibracja) |
| bezpieczeństwo | `safety.py` | klasyczny kod, źródła `snn:/classical:/script:` |
| symulator | `so101.py` | MuJoCo |
| pętla | `loop.py`, czas `latency.py` | — |

## Wyniki
| Wynik | Polecenie | Plik |
|---|---|---|
| V3.1 pierścień EPG | `.venv/bin/python -I -B flymind/v31_reproduce.py` | `results/v31_reproduce_20261028.txt` |
| V3.2 v1 / v2 | `.venv/bin/python -I -B flymind/v32_bump.py --protocol 1 --out flymind/results/v32/rerun` (i `--protocol 2`) | `results/v32/rerun/` |
| V3.2 v3 (potwierdzenie) | `.venv/bin/python -I -B flymind/v32_v3_confirm.py --out <katalog>` | `results/v32/v32_v3_confirm_*.json` |
| V3.4 chwyt | `.venv/bin/python -I -B flymind/v34_grip_inputs.py` | `results/v34_grip_inputs_20261028.txt` |
| V4 część A | `.venv/bin/python -I -B flymind/v4_open_loop.py --part A --out <katalog>` | `results/v4/v4_partA_*.json` |
| V4 część B v2 | `.venv/bin/python -I -B flymind/v4_open_loop.py --part B --version 2 --j0 0.2 --out <katalog>` | `results/v4/v4_partB_v2_*.json` |
| V5 potwierdzenie | polecenie w `validation/v5_confirm_manifest.json`; kod zamrożony w `validation/v5_frozen_code/` (uruchamiać po skopiowaniu do `flymind/` — ścieżki liczone od położenia pliku; bieżący kod z `--max-age 0.05` daje te same trajektorie) | `results/v5/v5_confirm_*.json` |
| V5 v2 (potwierdzenie) | polecenie w `validation/v5_v2_manifest.json`; analiza: `.venv/bin/python -I -B flymind/loop_v2.py --analyze <wynik>` | `results/v5/v5v2_20261029T065804.json`, `analysis_v5v2_confirm.json` |
| V5 ablacje (eksploracja) | `.venv/bin/python -I -B flymind/v5_ablation.py --part A --out <katalog>` (i `--part B`) | `results/v5_ablation/` |
| V5 v2 topologia (potwierdzenie) | polecenie w `validation/v5v2_topology_manifest.json`; analiza `--analyze` | `results/v5v2_topology/` |
| V5 v3 (potwierdzenie, zatwierdzone) | polecenie w `validation/v5v3_manifest.json`; reanaliza `.venv/bin/python -I -B flymind/audit_v5v3_independent.py`; nachylenia `v5v3_post_slopes.py` | `results/v5v3/` |
| V5 v3 — skala sygnału (eksploracja po przebiegu) | `.venv/bin/python -I -B flymind/v5v3_gain_check.py` | `results/v5v3/post_gain_check_dev1501_1520.json` |
| V5 analiza | `.venv/bin/python -I -B flymind/analyze_v5.py flymind/results/v5/v5_confirm_<czas>.json` | `results/v5/analysis_confirm.json` |

Uwaga: ponowny przebieg potwierdzający na tych samych ziarnach to odtworzenie, nie nowe potwierdzenie.
Wyniki V5 są deterministyczne dla danego ziarna, ale render MuJoCo zależy od sterownika GL — porównuj liczby, nie bajty.
