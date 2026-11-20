# T1b — sam „kształt” połączeń MaleCNS w oku flyvis: **FAILED** (20 XI 2026)

Kryterium (PREREG_T0_T1.md, spisane przed liczeniem): ≥ 12 z 20 modeli z medianą DSI T4a–d ≥ 0,2 **i** T5a–d ≥ 0,2
**i** max |V| < 100. Wynik: **2 / 20** (modele 000 i 010). Kontrola `shape_shuffle`: 1 / 10.

| | DSI ≥ 0,2 | to samo + stabilna | kierunek pref. < 45° od znanego | mediana DSI | mediana odległości |
|---|---|---|---|---|---|
| T4 (ON), shape, 20 modeli | 17 | 14 | 15 | 0,48 | 18° |
| T5 (OFF), shape | 2 | 2 | 4 | 0,06 | 87° |
| T4, shuffle, 10 modeli | 8 | 8 | 6 | 0,40 | 37° |
| T5, shuffle | 1 | 1 | 4 | 0,09 | 84° |
| flyvis bez zmian (model 000) | T4 0,52 / T5 0,68 | — | — | — | T4 6°, T5 11° |

Stabilnych sieci (max |V| < 100): shape 14 / 20, shuffle 9 / 10. Skrajne: model 014 |V| ≈ 3·10¹¹.

## Co to znaczy (opis, nie test — po wyniku)
- Ścieżka ON (T4) przeżywa podmianę układu przestrzennego na MaleCNS: kierunek wychodzi blisko znanego (mediana 18°).
  Ale przeżywa też potasowanie (DSI 0,40) — więc kierunkowość T4 we flyvis nie siedzi głównie w układzie przesunięć;
  kierunek preferowany jest bliżej znanego przy kształcie MaleCNS (18° vs 37°), przy 10 modelach kontroli to tylko wskazówka.
- Ścieżka OFF (T5) się rozpada w obu wariantach. Nie wiem jeszcze dlaczego; kandydaci: CT1 i Am zostały z flyvis
  (brak w danych MaleCNS w kolumnach), a T5 korzysta z CT1; albo mapowanie współrzędnych kolumn dla Tm9/Tm1 jest przesunięte.
- Wniosek dla projektu: właściwości wyuczone na mapie samicy nie przenoszą się na MaleCNS ani wprost (T1), ani przez sam
  kształt (T1b). Zgodnie z PREREG_T2 test T2 idzie na liczbach flyvis (hybryda: oko na mapie samicy, komórki zbliżania MaleCNS).

Pliki: t1b_shape_[abcd].json, t1b_shuf_[ab].json, logi t1b_*.log.
