# Etap 0 — protokół infrastruktury wielu kroków czasowych (zapisany PRZED uruchomieniem testów, 2026-11-06)

Zakres: tylko infrastruktura i testy. Brak porównania DATA vs SWS, brak Etapu N, brak nowych eksperymentów sieciowych.
Drabinka dt: 1,0 (stary model, tryb `legacy`), 0,2; 0,1; 0,05 ms (tryb `exact`).

## Pliki
- `alif_dt.py` — `ALIFdt` (podklasa `alif.ALIF`, te same równania), całkowite liczniki refrakcji i opóźnienia, jawne reguły zaokrąglania, szum skalowany do stałej intensywności fizycznej.
- `v5v41_dt.py` — `simulate_dt`: odpowiednik `v5v41.simulate` w czasie fizycznym (ms), dekoder wołany z rzeczywistym dt.
- `test_stage0_dt.py` — testy kryteriów; wynik zapisany do `results/stage0/` (nowy plik, tryb „x”).
- Pliki zamrożone (`alif.py`, `v5v41.py`, `decoder.py`, `loop.py`, `cl_runner.py`, `v4_open_loop.py`) — NIE zmieniane.

## Semantyka czasu (konwencja; krok k obejmuje przedział [k·dt, (k+1)·dt))
- Spike zapisany w indeksie k ma znacznik czasu k·dt; przekroczenie progu nastąpiło w (k·dt, (k+1)·dt] (wykrycie na końcu kroku).
- Refrakcja: kroki k+1 … k+n_ref mają v = V_reset; swobodne całkowanie od kroku k+n_ref+1. n_ref = t_ref/dt (`exact`) albo ceil (`legacy`).
- Opóźnienie: spike z indeksu k zwiększa g neuronu docelowego na początku kroku k+n_delay (czyli v docelowe zapisane w indeksie k+n_delay już go zawiera). n_delay = delay/dt (`exact`) albo round (`legacy`, round Pythona).
- `exact` odmawia, gdy t/dt nie jest całkowite (tolerancja względna 1e-9). `legacy` istnieje tylko po to, by odtworzyć stary model przy dt = 1.
- Szum: `ALIFParams.noise` = σ na krok przy dt_ref = 1 ms (znaczenie historyczne). σ_krok = σ·√(dt_ref/dt), więc intensywność fizyczna (wariancja v) nie zależy od dt. Przy dt = 1 σ_krok = σ dokładnie.
- Strumień RNG przy różnych dt jest inny (inna liczba losowań) — przebiegi przy różnych dt NIE są sparowane szumem.

## Kryteria (z raportu rundy 3, sekcja „Minimalne kryteria zaliczenia Etapu 0”) i przypisane testy
| # | Kryterium | Test | Uwaga |
|---|---|---|---|
| 1 | Regresja bit w bit przy dt = 1: nowy harness = stare `results/v5v41/raw/DATA.npz` (1 poziom, 2 strony, 2 powtórzenia) i 1 próba pętli zamkniętej identyczna | T1a (sieć syntetyczna, stary vs nowy harness, wszystkie typy harmonogramu), T1b (ALIFdt vs ALIF), T1c (DATA, dt = 1, E1 8 mV i E3 8 mV, strony L/R, powt. 0–1 vs zapisany DATA.npz) | Pętla zamknięta: nowy kod jej nie dotyka; dowód = niezmienione sha `loop.py`, `alif.py`, `cl_runner.py`. Uruchomienie próby MuJoCo nie jest częścią tego etapu |
| 2 | Te same czasy spike'ów przy dt 1 i 0,1 → identyczne Hz, okna, biny, Fano | T2 (sztuczna sieć odtwarzająca zadany raster) | dodatkowo dt 0,2 i 0,05 |
| 3 | Efektywne t_ref i delay równe nominalnym dla każdego dt z drabinki (assert) | T3 | + odmowa dla dt 0,5 / 0,25 w trybie `exact` |
| 4 | f–I przy dt = 0,1 w granicach 2% od wzoru ciągłego dla D 10–100 mV | T4 (symulacja = wzór dyskretny dokładnie; wzór dyskretny vs ciągły) | wynik raportowany niezależnie od tego, czy przejdzie |
| 5 | Stacjonarna wariancja v w granicach 5% od analitycznej przy każdym dt | T5 | analityczna = ciągły OU σ²/(2τ_m); dodatkowo wzór dyskretny |
| 6 | Odpowiedź na pojedynczy impuls presynaptyczny zaczyna się w oczekiwanym kroku | T6 | + test zapisu czasu spike'u |
| 7 | Dekoder: τ EMA 50 ms przy każdym dt (odpowiedź impulsowa/skokowa) | T7 | dekoder `decoder.py` niezmieniony; sprawdzane wywołanie z harnessu |
| 8 | Benchmark dt = 0,1 dla jednej sieci i poziomu; przerwanie, jeśli > 3× prognozy | T8 (sieć syntetyczna 424 neurony, gęsta W) | sieć DATA przy dt ≠ 1 nie jest uruchamiana w Etapie 0 → część z siecią DATA odłożona do startu Etapu N |
| 9 | `alif.py` nietknięty (sha), nowy moduł osobno hashowany; protokół i kryteria zapisane przed uruchomieniem | T9 | sha porównywane z `results/v5v41/config.json` |

Kryteria nie są zmieniane po zobaczeniu wyników. Kryterium niespełnione = raportowane jako niespełnione.
