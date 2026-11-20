# Oko + VS/HS — test 2, 20 XI 2026: **PASS** (plan: PREREG_OKO_VSHS.md, c9abc03)
`oko_mucha.py --test2`, ziarna 24 101 001–010, G0 = 0,04628, OUT_FULL2 = 0,04322 (kalibracja 24 100 900 przed testem). 142 s.
K1 10/10, K2 10/10, K3 10/10, K4 10/10.

| scena | stosunek do zbliżania z VS/HS (mediana / max) | to samo oko BEZ VS/HS |
|---|---|---|
| ręka bokiem | 0,003 / 0,005 | 0,004 / 0,005 |
| kamera w bok, w górę/dół, po skosie | 0,000 / 0,000 | 0,000 / 0,000 |
| obrót kamery | 0,000 / 0,005 | 0,000 / 0,005 |
| oddalanie | 0,013 / 0,017 | 0,013 / 0,016 |
| nieruchoma rzecz | 0,009 / 0,012 | 0,009 / 0,012 |
| zmiana światła | 0,001 / 0,001 | 0,001 / 0,001 |
| ciemne pole wjeżdża | **0,060 / 0,090** | **0,170 / 0,194** |
| zbliżanie przy ruchu kamery (K4) | 0,903 / 0,981 | 0,977 / 1,047 |

Uczciwie: po naprawie sceny ruch kamery daje 0 także BEZ VS/HS — porażka testu 1 była winą sceny. VS/HS pomaga głównie
przy bardzo kontrastowej krawędzi (ciemne pole: 0,17 → 0,06) i kosztuje ~7 % sygnału zbliżania, gdy kamera się rusza.
Oko odpala przy θ ≈ 31°. To nadal sceny syntetyczne — prawdziwa kamera niesprawdzona.

## Z mózgiem muchy (live_avoid.py --video, --brake intact, sceny ziarna 24 102 001, 20 XI)
| scena | nowe oko (`--eye mucha`): ucieczka DNp01/02/04/11 max / średnio | stare oko (`--eye plama`) |
|---|---|---|
| zbliżanie | 250 / 38 Hz | 262 / 18 Hz |
| kamera w górę/dół | **0 / 0 Hz** | **300 / 17 Hz** (fałszywy alarm) |
| ciemne pole wjeżdża | 0 / 0 Hz | 0 / 0 Hz* |
| nieruchoma rzecz | 0 / 0 Hz | 0 / 0 Hz* |
\* stare oko uczy tła przez 1,5 s, a nagrania trwały ~2–2,5 s pętli — jego wynik tu niemiarodajny. Ramię w symulacji
od samego wzroku nie rusza (znane: LPLC2 → brak neuronów ruchowych przedniej nogi). Prawdziwa kamera: niesprawdzone.
