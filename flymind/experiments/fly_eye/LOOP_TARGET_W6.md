# LOOP_TARGET — W6 „LPLC2-AND tylko w modelach flyvis z działającym torem OFF (T5)” (zapisane PRZED testem, 17 XI 2026)

Kontynuacja polecenia Adama „badaj dalej” (17 XI).

## Skąd hipoteza (analiza po fakcie W5, ujawniona)
W5 (LPLC2, reguła AND, modele 020–049) = FAILED. Analiza po fakcie na modelach 020–029 (`w5_posthoc_dsi.py`, `w5/w5_posthoc_dsi.log`):
na pełnych krawędziach o kontraście bodźców B1 T4 rozróżnia kierunek dla krawędzi jasnej (średnie DI +0,49),
ale **T5 dla krawędzi ciemnej prawie wcale (−0,01)**. Wszystkie dzisiejsze porażki dotyczą głównie ciemnych obiektów
(B1, W2, W2b, W5). Hipoteza: wąskim gardłem jest kierunkowość toru OFF w części modeli flyvis, nie odczyt.
Uwaga: W2b pokazał, że wybór modeli po jednej cesze (T2) nie pomógł; ten test może skończyć się tak samo.

## Bramka modeli (`w6_gate.py`, niezależna od LPLC2)
Dla każdego z 50 modeli: DI ośmiu podtypów na pełnych krawędziach (T4 — krawędź jasna, T5 — krawędź ciemna). Model przechodzi, gdy
średnie DI T4 ≥ 0,3, średnie DI T5 ≥ 0,3 i każdy podtyp ma DI > 0. Próg 0,3 wybrany przed uruchomieniem bramki
(połowa mediany DSI T4 z bramki G2-fv 16 XI, ok. 0,4–0,58).

## Test
- Modele testowe: te z **000–019**, które przejdą bramkę. Dla nich reguły AND jeszcze nie liczono (model 000 tylko w ślepej próbie dymnej W5).
  Modele 020–049 nie wchodzą do testu (tam wynik W5 już znam) — z nich raportuję tylko, ile przechodzi bramkę.
- Mniej niż 3 modele testowe → **NOT TESTABLE** (bez zmiany progu).
- Kod, mapa, bodźce, reguły, miary: **identyczne jak W5** (`w5_and.py`, `w5_analysis.py`, `map_rot30.npz`). Kamera jak W5.

## Kryteria (jak W5)
- **W6 PASS (ciemny dysk, AND):** mediana LI > 0, zbliżanie wygrywa w ≥ 80 % przypadków, układ prawdziwy lepszy od każdej z 23 permutacji.
- Osobne etykiety: jasny dysk (AND); kamera (S3 > S1, S2, S2r, S4 w ≥ 80 % modeli). Opisowo: LIN.
- Dodatkowo, opisowo: czy modele 020–049, które przechodzą bramkę, wypadły w W5 lepiej niż te, które nie przechodzą (mediana LI na model, AND, ciemny).

## Zasady
Jeden przebieg; najwyżej 3 procesy; bez ziaren; po wyniku nie zmieniam progu bramki ani reguł.
PASS → wolno pisać: „w modelach flyvis z kierunkowym torem OFF odczyt AND z ramion MaleCNS daje LPLC2 wybiórczy dla zbliżania”.
FAILED → linia LPLC2 z flyvis zamknięta na tej drodze; raport.
Wyniki: `flymind/results/fly_eye_20261117/w6/`.
