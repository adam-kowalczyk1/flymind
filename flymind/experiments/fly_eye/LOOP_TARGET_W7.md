# LOOP_TARGET — W7 „ramiona LPLC2 przypisane według kierunków zmierzonych w każdym modelu” (zapisane PRZED testem, 17 XI 2026)

Kontynuacja polecenia Adama „badaj dalej” (17 XI).

## Skąd hipoteza (ujawniona)
- W6 (bramka kierunkowości, `w6/gate_*.log`) = **NOT TESTABLE**: z modeli 000–019 przechodzą tylko 000 i 003 (próg ≥ 3).
- Obserwacja z bramki: w wielu modelach DI względem kierunków **modelu 000** jest silnie **ujemny** (np. 004: T4 −0,85; 005: −0,81;
  025, 026, 032, 033, 038–043 ujemne). Zatem etykieta „T4a/T5a” w różnych modelach flyvis nie zawsze oznacza ten sam kierunek ruchu.
  B1, B1b i W5 przypisywały ramiona LPLC2 według kierunków zmierzonych **tylko w modelu 000** (`PREREG_BRIDGE.md`).
  W modelu z odwróconym T4 „ruch na zewnątrz” trafia na złe ramię — zbliżanie wygląda jak oddalanie.
- Hipoteza: jeśli dla każdego modelu przypisać podtypy flyvis do ramion MaleCNS według kierunków zmierzonych w **tym** modelu
  (na krawędziach, bez LPLC2), odczyt AND da LPLC2 wybiórczy dla zbliżania.
- Uczciwie: to kalibracja etykiet modelu oka do anatomii (po jednej na model, z bodźca niezależnego od testu). Nazywam ją wprost.
  To nie jest dopasowanie do wyniku LPLC2.

## Przypisanie (`w7_run.py`)
Dla modelu k: odpowiedzi R[s, kierunek] podtypów T4 na jasną krawędź i T5 na ciemną krawędź, w 4 kierunkach (0°, 90°, 180°, 270°),
jak w `w6_gate.py`. Ramiona MaleCNS mają kierunki „na zewnątrz” a 180°, b 0°, c 90°, d 270° (po obrocie 30°; `PREREG_BRIDGE.md`).
Wybieram permutację π (osobno dla T4 i dla T5), która maksymalizuje Σ_g DI(π(g), kierunek ramienia g), gdzie
DI(s, kier.) = (R[s, kier.] − R[s, kier. + 180°]) / (suma). Przegląd 24 permutacji, bez parametrów.
Potem odczyt **identyczny jak W5** (`w5_and.readout`, AND i LIN, mapa `map_rot30.npz`, bodźce B1).

## Kontrole
- 23 pozostałe permutacje nałożone na przypisanie (jak W5): przypisanie z pomiaru musi wygrać ze wszystkimi.
- Obrót mapy 210° (odwrócony znak anatomii), modele 000–009, opisowo.

## Modele
flyvis 000–019 (dla nich reguły AND nie liczono; model 000 tylko w ślepej próbie dymnej W5). 020–049 nie wchodzą do testu.

## Kryteria (ciemny dysk, AND; jak W5)
- **W7 PASS:** mediana LI > 0 i zbliżanie wygrywa w ≥ 80 % przypadków (20 modeli × 7 środków) i przypisanie z pomiaru lepsze od każdej z 23 permutacji.
- Osobne etykiety: jasny dysk (AND); kamera (S3 > S1, S2, S2r, S4 w ≥ 80 % modeli). Opisowo: LIN; liczba modeli, w których przypisanie ≠ tożsamość.

## Przewidywanie
Jasny dysk: raczej PASS albo blisko. Ciemny: niepewne — w wielu modelach T5 ma słabe DI także po przypisaniu (bramka W6: T5 ≈ 0).

## Zasady
Jeden przebieg; najwyżej 3 procesy; bez ziaren; po wyniku nie zmieniam reguły przypisania, progów ani bodźców.
Wyniki: `flymind/results/fly_eye_20261117/w7/`.
