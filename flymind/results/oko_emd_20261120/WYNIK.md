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
