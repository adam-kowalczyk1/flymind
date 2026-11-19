# „GDZIE czuje” r1 — czy sieć odróżnia dotyk szczęki stałej (A0) od ruchomej (A1) (cel zapisany PRZED testem, 19 XI 2026)

## Hipoteza
Gdy receptory szczecinek nogi T2 L podzielimy wg mapy `touch_map.json` (grupa „udo” ← A0, grupa „goleń+stopa” ← A1; STATUS MAPY: HIPOTEZA
oparta na klastrach profilu wyjść, literatura nie podaje tabeli typ SNta → segment), to odpowiedź sieci (BrainNet, bez ramienia) zależy od miejsca
dotyku: wektor odpowiedzi różni się między „tylko A0” a „tylko A1”.
Zastrzeżenie z góry: grupy mają różną liczność (230 vs 92) i różne połączenia, więc odróżnialność jest oczekiwana prawie na pewno — to sprawdzenie
instalacji (czy sygnał „gdzie” przechodzi przez wspólną drogę czujnik → mózg), NIE dowód, że podział jest zgodny z anatomią ani że mucha „wie” GDZIE.
Który klaster = udo jest arbitralny; dlatego `swap` jest równorzędny, nie „zły”.

## Projekt
BrainNet(glu, "N"), Glu ∈ {−1, +1}. Brak ramienia. Wejście = odczuta siła w N bezpośrednio do `net.step([A0, A1, 0], ...)` (40 mV/N, maks. 40 mV; dłoń 0).
Próba: 0,5 s spoczynek, 0,5 s nacisk 2 N na JEDEN czujnik (A0 albo A1), 0,3 s po. Szum prądu σ = 2 mV w każdym neuronie (`ALIFParams(noise=2.0)`), nowa sieć SparseALIF
z nowym ziarnem w każdej próbie. 10 ziaren szumu na czujnik (20 prób na warunek).
Wektor odpowiedzi (7 liczb, średnia z okna nacisku 0,5–1,0 s, Hz): pule stawów j1, j2, j3 (P − N), DNg15, DNge078, MN prostownika Ti (press), MN zginaczy Ti (release).
Warunki: mapowania somato, swap, halves na sieci N; kontrola liczności „somato_bal” (grupa „udo” losowo zredukowana do 92 komórek, ziarno 21 947 800);
oraz mapowanie somato na 3 sieciach F (tasowanie `BrainNet(glu,"F",s)`, s = 21 947 901, 902, 903) — tylko zasięg „co zostaje po zniszczeniu struktury”.

## Metryki (osobno dla każdego warunku i Glu)
- ACC = dokładność klasyfikacji A0 vs A1 leave-one-out, najbliższa średnia, cechy standaryzowane (SD z puli, minimum 1 Hz; cechy stale zerowe odpadają).
- D' = (m1 − m0) / SD z puli wzdłuż osi łączącej średnie (rzut na tę oś, średnie liczone bez próby w pętli LOO nie są potrzebne — wersja pełna próby).
- Średnie odpowiedzi surowe (Hz) zapisuję w tabeli.

## Kryteria (z góry)
W1 (instalacja działa): somato, oba Glu: ACC ≥ 0,95 ORAZ D' ≥ 3.
W2 (lustro): swap: odległość(średnia A0_swap, średnia A1_somato) < 0,25 · odległość(A0_somato, A1_somato) w przestrzeni cech standaryzowanych, oba Glu (to jest test poprawności sprzętu/kodu mapowania, spodziewany pewny).
W3 (kontrola liczności): somato_bal oba Glu ACC ≥ 0,95 — jeśli nie, odróżnialność wynikała z różnej liczności grup, nie z samego miejsca; wtedy W1 raportuję jako „niejednoznaczne”.
Raportuję bez kryterium: halves, F (3 × 2), średnie surowe. FAILED jest dopuszczalne i raportowane tak samo.

## Ziarna
Szum: 21 947 000 – 21 947 999 (licznik 21 947 000 + kolejna próba w kolejności: warunek-sieć × czujnik × k). Tasowania F: 21 947 901–903. Podpróbka: 21 947 800. Wszystko jednorazowo.

## Zastrzeżenia z góry
Symulacja sieci bez ciała i bez prawdziwego czujnika; siła 2 N wstawiona wprost (nasycenie 40 mV od 1 N). Mapa segmentów jest hipotezą.
