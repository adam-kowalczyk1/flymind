# Oko bez tłumacza — raport z badania 20 XI 2026

**Pytanie Adama:** jak zbudować oko, z którego mucha (sieć z konektomu MaleCNS) odbiera sygnały sama, bez ręcznie pisanego tłumacza.
**Droga:** wziąć gotowy, opublikowany model oka muchy (flyvis, Lappalainen i in. 2024, Nature), który liczy wszystkie 65 typów
komórek od fotoreceptorów do T4/T5, i podłączyć go do prawdziwych komórek zbliżania z MaleCNS przez ich własne synapsy.
Każdy test miał plan zapisany w repo PRZED liczeniem.

## Wyniki

| krok | pytanie | wynik |
|---|---|---|
| T0b | czy mapy oka samicy (flyvis) i MaleCNS się zgadzają | **PASS** — zgodność 0,69; obwód kierunku prawie identyczny (Mi9→T4a 28 vs 27) |
| T1 | czy oko flyvis działa na liczbach synaps MaleCNS | **FAILED** — sieć eksploduje (napięcia ~10¹⁴), kierunkowość 0 |
| T1b | czy działa na samym „kształcie” połączeń MaleCNS | **FAILED** 2/20 — kierunek jasnych krawędzi (T4) przeżywa 17/20, ciemnych (T5) się rozpada |
| T2 v1 | LPLC2 + LPi MaleCNS na oku flyvis, uczone tylko właściwości typów | **FAILED** — błąd w moim kodzie uczenia (NaN); poprawiony, opisany |
| T2 v2 | to samo po poprawce | **FAILED** — AUC test 0,30–0,87 (cel 0,90); okablowanie potasowane tak samo dobre |
| T2c | czy prawdziwe okablowanie pomaga przy zbliżaniu na fakturze (nowe modele) | **FAILED** 1/6 |

## Co z tego wiemy (pewne)
1. **Wyuczonych właściwości oka nie da się przenieść z jednej mapy połączeń na drugą** — ani wprost, ani przez sam kształt.
   Oko na MaleCNS trzeba by **wyuczyć od nowa na MaleCNS** (tak jak flyvis uczono na mapie samicy).
2. **Żaden typ komórki oka nie mówi LPLC2 „zbliżanie” mocniej niż „ruch kamery”.** Szczyt sygnału z każdego typu wejścia
   jest większy przy ruchu kamery. Odrzucanie ruchu własnego musi robić hamowanie (komórki LPi) i dynamika — z LPi
   wychodziło lepiej (do 0,87–0,90) niż bez (0,19–0,55).
3. **Na poziomie „właściwości typów” prawdziwe okablowanie MaleCNS nie dało przewagi nad potasowanym** (9 modeli).
   Albo przewaga siedzi w szczegółach, których ten model nie ma (dendryty, kolce, ~29 % wejść LPLC2 spoza oka flyvis),
   albo potrzeba uczenia całości, nie tylko ostatniej warstwy.
4. Czego NIE wiemy: czy oko wyuczone od zera na MaleCNS zachowa się lepiej. Tego dziś nie liczyłem (za drogie na ten komputer).

## Co działa już teraz
Syntetyczne oko (`oko_mucha.py`: fotoreceptor → detektory ruchu ON/OFF → 32 jednostki LPLC2 z hamowaniem przeciwnym +
komórki VS/HS) **zdało test 2** i jest domyślnym okiem w `live_avoid.py`. To jest model zbudowany ręcznie według biologii
(Klapoetke 2017), a nie wyuczony z konektomu — uczciwie: to wciąż „tłumacz”, tylko wzorowany na muszym.
Na prawdziwej kamerze jeszcze nie sprawdzone.

## Propozycje (decyzja Adama)
- **P1 (zalecam, najpierw):** test nowego oka na prawdziwej kamerze — potrzebuję Ciebie przy komputerze (komenda w poprzednim raporcie).
- **P2:** kopia ruchu ramienia (sieć muchy wie, jak rusza ramieniem → może od razu odjąć ruch kamery). Tani test w symulacji; tak robią
  prawdziwe muchy (Kim i in. 2015, Fenk i in. 2021).
- **P3 (po Explory):** wyuczyć całe oko od zera na mapie MaleCNS (droga flyvis). To jedyna droga naprawdę „bez tłumacza”,
  ale wymaga wynajętej karty graficznej i kilku dni — najpierw oszacuję koszt.

Pliki: `flymind/results/fly_eye_malecns_20261120/` (WYNIK_T1, WYNIK_T1b, WYNIK_T2_v1, WYNIK_T2_v2, WYNIK_T2c), kod w
`flymind/experiments/fly_eye_malecns/`. Ziarna zużyte: 24 103 0xx, 24 104 0xx–3xx. Nic nie ruszało prawdziwego ramienia.
