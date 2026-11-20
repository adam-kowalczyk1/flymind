# Oko „jak u muchy” — test syntetyczny 20 XI 2026: **FAILED** (plan: PREREG_OKO_EMD.md, df85e57)
`oko_mucha.py --test`, ziarna 24 100 001–010, OUT_FULL = 0,0537 (kalibracja 24 100 900, przed testem). Czas 98 s.
- K1 wybiórczość: **7/10** (próg 9). Winna jedna scena: kamera w górę/dół 50°/s — stosunek do zbliżania mediana 0,236, max 0,362.
  Pozostałe mediany: ręka bokiem 0,003, kamera w bok 0,066, obrót 0,000, oddalanie 0,013, nieruchoma rzecz 0,008, światło 0,001.
- K2 strona: 10/10. K3 zapominanie nieruchomej rzeczy: 10/10 (po 1,5 s wyjście 0,000 szczytu).
- Odpala (50 % szczytu) przy θ ≈ 31° (mediana).
- Stare oko (`Eye`, tylko raport; uwaga: uczy tła przez 1,5 s, więc scen od 0,5 s nie widzi uczciwie): kamera w bok/górę
  1,26 × zbliżania, obrót 1,16, ręka bokiem 0,50 — czyli stare oko myli ruch kamery ze zbliżaniem; nowe tłumi go 4–∞ razy.
Hipoteza (NIESPRAWDZONA, post hoc): siatka 40×25 jest szersza niż wyższa, jednostki LPLC2 przy górnym/dolnym brzegu mają
obcięte pola, więc przy ruchu pionowym ramiona nie znoszą się symetrycznie. Zgodnie z planem nie stroję stałych pod ten test.

## Diagnoza po teście (20 XI, wynik FAILED zostaje)
Scena 6 „kamera w górę/dół” była ZŁA: faktura tła za mała, od t ≈ 1,9 s w kadr wjeżdża czarne pole (0), przy 2,5 s
zajmuje 60 % kadru (`scene("pan_v")`: min 0, frac < 10 = 0,2 → 0,6). Szczyt fałszywego sygnału przy t = 2,9 s. Szum w ciemnym
kadrze NIE jest przyczyną (stała jasność 5–140 + σ 3 → 0,000–0,002 OUT_FULL). Wniosek: oko reaguje na bardzo kontrastową
krawędź (czarne pole, log-kontrast ~2,9 wobec ~1,1 krążka; detektor Reichardta rośnie z kwadratem kontrastu). To realna
słabość (w prawdziwym obrazie są czarne przedmioty), więc w teście 2 jest osobna scena „ciemne pole wjeżdża”.
