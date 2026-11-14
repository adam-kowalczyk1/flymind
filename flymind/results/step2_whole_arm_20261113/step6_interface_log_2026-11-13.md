# Krok 6 — interfejs na żywo — osobny log (treść = §5.8 w step2_log_2026-11-13_part5.md, skopiowana 14 XI 01:4x)

## 5.8 Krok 6 — interfejs na żywo (wykonał agent Sonnet; sprawdzone przeze mnie)

| # | Co | Plik / komenda | Wynik |
|---|---|---|---|
| 6.1 | Nowy pokaz (demo.py bez zmian): okno MuJoCo + panel: raster WSZYSTKICH neuronów sieci sterujących (ArmNet + LegJaw), pule POS/NEG na staw z częstościami, Δcel na takt, moment szczęki, źródło komendy każdego stawu, faza, linia „dane / model / inżynieria” | `flymind/demo/demo_arm.py` (sha `4312db6a…1744`) | — |
| 6.2 | Test zgodności z eksperymentem | `.venv/bin/python -I -B flymind/demo/test_demo_arm.py` (uruchomiony przeze mnie 19:1x; ziarno 20951, cube_S/hard_grip) | **WSZYSTKIE TESTY OK** — T1: 23 pola wyniku identyczne z `joint_net.run_trial`; T2: sha całej trajektorii z przechwytywaniem impulsów = bez (`50b22ed1…`); T3: częstości z impulsów = `ArmNet.r`; T4: źródła komend ⊂ statystyki SafetyLayer; T5: ziarno testowe odrzucane — **VERIFIED** |
| 6.3 | Nagranie i zrzuty (bez okna) | `--media flymind/demo/media_arm_20261113/` (MP4 1600×900, 447 klatek; 3 PNG) | Zrzut „lift” obejrzany przeze mnie: panel i scena poprawne — VERIFIED |
| 6.4 | Liczba neuronów na rastrze | z sieci, nie wpisana | **4100 = ArmNet 2593 + LegJaw 1507** (nie 2916: 2916 to sieć T2 L + T1 L + wzrok z `tick_cost`; tu sterują dwie sieci: ramię i osobna szczęka, obwód T2 L występuje w obu). Wzroku w tym pokazie nie ma |
| 6.5 | Wydajność (agent, obciążenie ~200, więc pesymistycznie) | `--bench` | 53 takty/s bez panelu (0,53× czasu rzeczywistego), 47 takty/s z panelem 20 kl./s (0,47×) — REPORTED (nie powtórzone na wolnej maszynie) |
| 6.6 | Okno interaktywne | `.venv/bin/mjpython flymind/demo/demo_arm.py --seed 20951` | Uruchomione przez agenta do czystego wyjścia; **samego okna nikt nie widział — NOT VERIFIED** |

