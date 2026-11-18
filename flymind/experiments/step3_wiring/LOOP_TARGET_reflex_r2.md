# Krok 4 r2: „dwa czucia, dwa odruchy” na robocie, test 3× większy (cel zapisany PRZED testem, 16 XI 2026)

## Po co
Test r1 (`LOOP_TARGET_reflex_r1.md`, 24 ważne pary) dał werdykt **niespełniony**.
- Przy Glu +1 sieć z danych wygrała z każdym z 5 tasowań swobodnych (15 : 0).
- Z tasowaniami zachowującymi warstwy wygrała tylko z 3 z 5: L2 9 : 3, p 0,29; L3 5 : 6.

Wynik r1 zostaje bez zmian. Ten test to NOWY cel z NOWYMI ziarnami i nowymi tasowaniami. Pyta, czy przy trzykrotnie większej liczbie scen sieć z danych wygrywa z tasowaniami warstwowymi, czy remis z r1 był prawdziwy. Adam zgodził się na test 16 XI.

## Układ: bez zmian względem r1
- Kod `reflex.py` (hasz jak w krokach 4 i 5, w `PRE_TEST_HASHES.txt`). Nic nie strojone.
- Próby W i C oraz kryteria sukcesu pary są dosłownie jak w `LOOP_TARGET_reflex_r1.md`.
- Próba W działa tylko na walcu 60 mm (`cyl_thin`); próba C na walcu 50 mm.

## Test (raz)
- **Sceny:** trzy ziarna `--seed 21951`, `21952`, `21953` (sceny 21 951 000–149, 21 952 000–149, 21 953 000–149), po 6 póz × 5 materiałów, czyli 90 par scen (r1 miało 30).
- **Sieci:** N oraz po 5 nowych tasowań na rodzinę, każde dla obu znaków Glu. Razem 32 sieci × 3 ziarna = 96 przebiegów.
  - F1–F5: tasowania swobodne, ziarna 21 960 001–005.
  - L1–L5: zachowujące warstwy, ziarna 21 970 001–005.
  - G1–G5: warstwy + przynależność do nóg, ziarna 21 980 001–005.
- **Uruchomienie:** `one_reflex_r2.sh` + `reflex_r2_jobs.txt` (xargs -P 5 -L 1) → `results/step3_20261115/reflex_r2/`.

## Kryteria (analiza `analyze_reflex2.py`, zapisana przed testem; logika jak `analyze_reflex.py`)
- Para ważna, gdy w sieci N oba podjazdy są osiągalne. Analiza sprawdza, że ważność nie zależy od sieci.
- Wynik pary: OBA odruchy udane. Klucz pary = ziarno sceny, więc pary z trzech ziaren się nie zlewają.
- H-R(F), H-R(L), H-R(G): sieć z danych lepsza na wyniku OBA od każdego z 5 tasowań rodziny (McNemar dokładny + Holm w rodzinie, p_Holm < 0,05 i różnica > 0), osobno dla każdego Glu.
- **„Schemat połączeń ma znaczenie w zadaniu dla robota”** uznaję za potwierdzone dla danego Glu, gdy H-R(F) i H-R(L).
- H-R(G) mówi, czy wystarcza zachować podział na nogi.
- Opisowo: W, C i OBA dla każdej sieci oraz liczba tasowań, z którymi sieć z danych wygrała (n_beaten).

## Oczekiwania zapisane uczciwie
- **Glu +1:** H-R(F) bardzo prawdopodobnie spełnione: w r1 tasowania swobodne nigdy nie cofnęły ramienia, W 0/24 w 10 przebiegach.
- **H-R(L) niepewne.** W r1 jedno z 5 tasowań warstwowych (L3) dorównało danym, więc remis może się powtórzyć z innym L. Większa liczba scen pomoże tylko wtedy, gdy przewaga jest prawdziwa, ale mała (jak L2 9 : 3).
- **H-R(G):** raczej nie.
- **Glu −1:** raczej niespełnione, bo odruch cofania sieci z danych jest w tym wariancie za słaby (r1: W 5/24).
- Wynik negatywny jest wynikiem. Nie szukam poprawki „aż wyjdzie”: zmiana czegokolwiek po wyniku = nowy cel i nowe ziarna.

## Ograniczenia
- Symulacja, jeden zestaw parametrów neuronu.
- Mapowanie „dłoń = noga przednia T1 L, palce = noga środkowa T2 L” to wybór modelu.
- Próba W ma jeden kształt.
- Materiały w symulacji są sztywne.
