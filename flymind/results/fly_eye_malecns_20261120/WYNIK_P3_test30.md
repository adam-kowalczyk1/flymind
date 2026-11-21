# P3 — test 30 min uczenia oka na połączeniach MaleCNS (21 XI 2026, Mac, CPU)

Uruchomienie: `run_p3_test30.sh` (twarde zatrzymanie po 40 min). Sintel pobrany (5,24 GB, 28 min), rozpakowany (5,8 GB,
`data/flyvis/SintelDataSet`, poza gitem). Jednorazowe przerabianie filmów na siatkę oka: ~8 min.

| | wynik |
|---|---|
| sieć MaleCNS buduje się i uczy | tak, bez NaN |
| pamięć | 4,9 GB (szczyt) |
| prędkość 15:12–15:14 | 12 kroków / ~16 s = **~1,3 s/krok** (nie 0,33 jak sam model — reszta to przygotowanie danych w jednym wątku, `num_workers` = 0) |
| prędkość od 15:14 | ~12 kroków / 6–7 min (~30 s/krok) — w tym czasie Mac był mocno zajęty (średnie obciążenie ~14, działał GeForce NOW); przyczyny nie rozstrzygam |
| kroków w 40 min | 180 z planowanych 4000 |
| strata | 12 zapisów, 310–2840, za mało kroków, żeby ocenić uczenie |

## Co to znaczy dla planu
Przy 1,3 s/krok: 250 000 kroków ≈ **90 h ≈ 3,8 doby na model**; 4 modele po 2 naraz ≈ 7,5 doby (Mac bez innych ciężkich
zadań). Moje wcześniejsze oszacowanie (25–30 h) było za niskie — nie liczyło przygotowania danych.
Możliwe przyspieszenie: równoległe ładowanie danych (`num_workers` > 0) — niesprawdzone.
