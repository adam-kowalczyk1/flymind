# P3 — ile kosztuje wyuczenie oka od zera na mapie MaleCNS (oszacowanie 21 XI 2026)

**Pytanie:** T1/T1b pokazały, że właściwości oka wyuczone na mapie samicy (flyvis) nie przenoszą się na MaleCNS. Jedyna droga
„naprawdę bez tłumacza”: wyuczyć oko od zera na połączeniach MaleCNS, tak jak Lappalainen i in. (2024) uczyli flyvis.

## Co trzeba (zmierzone / sprawdzone w kodzie flyvis)
| rzecz | stan |
|---|---|
| Przepis uczenia flyvis | w pakiecie: zadanie = ruch obrazu (optic flow) na filmach Sintel, 250 000 kroków, partia 4, 19 klatek co 20 ms |
| Sieć | mała: 734 uczone liczby (właściwości typów), reszta stała z połączeń |
| Czas jednego kroku na tym Macu (CPU) | **0,21–0,23 s** (zmierzone: 4–8 wątków; + ~20 % na dekoder i dane) |
| Jeden model, pełne uczenie | **~17–21 h** na tym komputerze; 2 modele naraz (po 4 wątki) |
| Karta graficzna | **niepotrzebna** — sieć jest za mała, żeby GPU dużo dało (kroki czasu idą po kolei) |
| Dane Sintel | **trzeba pobrać**: MPI-Sintel-complete.zip z files.is.tue.mpg.de (ok. 5–6 GB); wolne miejsce 98 GB |
| Połączenia MaleCNS w formacie flyvis | prawie gotowe: `malecns_keys.csv` (typ→typ, przesunięcie, liczba synaps) z T0; trzeba dopisać typy bez danych (R1–R8, CT1, Am — dziś „hybryda”) i znaki; ok. pół dnia + sprawdziany |

## Plan, jeśli Adam się zgodzi
1. Zgoda na pobranie Sintel (5–6 GB, publiczny zbiór filmów do badań nad ruchem obrazu).
2. Plik połączeń MaleCNS dla flyvis + sprawdzian: na liczbach flyvis ta sama droga daje te same wyniki co oryginał.
3. Plan testu spisany przed uczeniem: najpierw próba (1 model, 50 000 kroków ≈ 4 h), potem 4 modele po 250 000 (≈ 2 doby).
   Kryterium jak T1b: kierunkowość T4/T5, stabilność — i na końcu to samo oko na nagraniu oko_r2.
4. Ryzyko: brak danych MaleCNS dla fotoreceptorów/CT1/Am (zostają z flyvis) — to wciąż częściowa hybryda; uczciwie opisane.

Koszt pieniężny: 0 zł (ten komputer). Koszt czasu: ok. 3 doby liczenia + ok. 1 dzień mojej pracy.
