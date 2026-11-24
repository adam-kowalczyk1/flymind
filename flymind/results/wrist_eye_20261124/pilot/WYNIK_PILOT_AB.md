# Pilotaż A/B: FlyEye v2 w pętli z siecią i trzema stawami (24 XI 2026, tylko MuJoCo)
Plan przed przebiegiem: `experiments/wrist_eye/PREREG_PILOT_AB.md`, skróty `PRE_TEST_HASHES.txt`; liczby `analysis.json`; kierunki etapów (po fakcie) `etapy_po_fakcie.txt`; wykres `pilot_AB.png`.
80 przebiegów (10 ziaren × A, B, B1, C × Glu −1, +1). A i B identyczne co do bitu do pierwszej innej klatki 20/20. Flagi SafetyLayer, strażnik, kontakty: 0 we wszystkich. C (kula stoi): komenda 0.

**Odpowiedź.** Obraz na żywo zmienił komendy po pierwszym ruchu w 20/20 par (pierwsza inna klatka 10 ms po pierwszej komendzie; pierwsza inna komenda 30–80 ms po niej). Ale zmiany NIE
odróżniają się od kontroli B1 (szum obrazu o 1 poziom): kryterium „zauważalnie zmienił ruch” niespełnione w żadnym stawie i oknie, przy żadnym Glu.

| 2. zbliżenie | A − B (mediana; min…max) | |A − B| mediana | B1 − B: |mediana| ; p95 | ten sam znak |
|---|---|---|---|---|
| Glu −1 bark | 0,00° (−0,19…0,19) | 0,05° | 0,14° ; 0,19° | 6/10 |
| Glu −1 łokieć | +0,01° (−0,04…0,37) | 0,03° | 0,02° ; 0,26° | 6/10 |
| Glu −1 nadgarstek | 0 | 0 | 0 | – |
| Glu +1 bark | −0,7° (−3,2…3,4) | 1,7° | 2,5° ; 3,2° | 6/10 |
| Glu +1 łokieć | −3,2° (−5,7…−1,5) | 3,2° | 1,8° ; 3,9° | 10/10 |
| Glu +1 nadgarstek | +0,2° (−2,0…1,5) | 0,4° | 1,0° ; 2,3° | 6/10 |

**Gdzie zanika — Glu −1** (2. zbliżenie, mediana A wobec B; w nawiasie ile par na plus; B1): sygnał oka +4,5 % (10/10; B1 +0,4 %), komórki oka +5,8 % (10/10), mózg +5,5 % (9/10), DN +5,5 % (8/10),
rdzeń +5,2 % (8/10; B1 −0,1 %), neurony ruchowe stawów −6 % (3/10), komendy ±0. Gubi się między interneuronami rdzenia a neuronami ruchowymi: 32 neurony dają łącznie ok. 16 impulsów na 2 s.
Ruch ramienia w 1. zbliżeniu to ok. 0,3° obrotu kamery; sygnał oka obcięty do 40 mV w obu.
**Glu +1:** pierwsza reakcja to napad (~−32° łokcia w 2 s, dalej do −105°); kamera odwraca się (94° przed 2. zbliżeniem), kula znika: sygnał oka A 0 mV od 1,57 s. Mimo utraty całego sygnału
sieć jedzie dalej prawie tak samo: mózg −5 %, DN −3 %, rdzeń −2 %, MN +4 %, komendy łokcia −10 % (10/10, ale poniżej p95 B1). Zanika w samopodtrzymującej się aktywności sieci.

**Ograniczenia:** 10 ziaren, jedna kula/tor/poza; bez tasowań; oko = kod; kontrola B1 to jeden rodzaj zaburzenia; A/B1 nie mają tego samego rodzaju zmian. Pilotaż, nie test hipotezy.
