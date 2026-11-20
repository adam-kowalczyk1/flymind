# T2 — komórki zbliżania MaleCNS zasilane okiem przez prawdziwe synapsy (spisane PRZED liczeniem, 20 XI 2026)

## Pytanie
Most B1/B1b/W2/W5–W8/D (16–17 XI) czytał LPLC2 jako sumę liniową „synapsa × aktywność T4/T5” z jednakowymi siłami — nie
odróżniał zbliżania od ruchu kamery. Tu nic nie jest liniowym odczytem ani ręcznym detektorem: komórki LPLC2 (91, prawa),
LC4 (55) i LPi (299) MaleCNS mają **wszystkie** swoje wejścia od typów, które liczy oko (LPLC2: 55,6 % całego wejścia,
LC4: 58,6 %), wejścia od LPi (LPLC2: 4,6 %) i od siebie nawzajem (LPLC2: 10,9 %), z liczbami synaps i znakami (NT) z MaleCNS.
Uczone są TYLKO właściwości typów, tak jak flyvis uczył oko: stała czasowa i spoczynek celu oraz każdego typu LPi, siła
każdego typu wejścia (≥ 0), siła LPi (na typ LPi) i rekurencji; plus 2 liczby progu odczytu. Pozostałe ~29 % wejść LPLC2
(typy spoza flyvis) — brak w modelu (ograniczenie, raportuję).
**Hipoteza H2:** połączenia MaleCNS pozwalają tym kilkudziesięciu liczbom zrobić z LPLC2 detektor zbliżania, który na
NOWYCH bodźcach odróżnia zbliżanie od ruchu kamery; na potasowanym okablowaniu (te same typy i liczby, przemieszane kolumny)
nie da się tego zrobić tak dobrze.

## Ustalenia
- Oko: modele flyvis 000, 001, 002 (wybrane z góry). Liczby synaps oka: MaleCNS, jeśli T1 PASS; inaczej flyvis (wtedy wynik
  opisany jako hybryda: oko na mapie samicy, komórki zbliżania na MaleCNS).
- Napęd (`t2_drive.py`): Σ znak·n_ij·relu(V) / całe wejście komórki z MaleCNS (dla LPi: / wejście od typów flyvis). Kolumny
  komórek pre z T0. Model (`t2_model.py`): τ dV/dt = −V + b + Σ_typ g_typ·napęd + Σ_LPi g·… + g_rec·…, wyjście relu(V),
  dt 10 ms, wynik bodźca = miękkie maksimum po komórkach i czasie. Adam lr 0,03, 600 kroków, 3 starty (ziarna 24 104 201–203),
  wybór startu po stracie TRENINGOWEJ.
- Bodźce (`t2_stim.py`, ziarna faktur 24 104 001–002 trening, 24 104 101–102 test): trening 66 (14 zbliżań: dysk ciemny/jasny,
  7 miejsc, l/v 40 ms; reszta: oddalanie, przesuwany dysk, błysk, ruch faktury w 4 strony i obrót). Test 44 (20 zbliżań):
  inne prędkości (l/v 20 i 80 ms), zbliżanie na fakturze, **zbliżanie w czasie ruchu kamery**, nowe faktury w ruchu, oddalanie,
  większy dysk przesuwany po fakturze.
- Kontrola okablowania: `t2_drive.py … shuffle` (ziarno 24 104 300 + model). Tylko raport: wariant bez LPi, wariant
  „nieuczony” (wszystkie siły 1, tylko próg), LC4 tym samym sposobem.

## Kryteria (cel LPLC2; PASS, gdy spełnione w ≥ 2 z 3 modeli)
- **K1:** AUC na zbiorze testowym ≥ 0,90.
- **K2:** AUC(prawdziwe okablowanie) − AUC(potasowane) ≥ 0,10.
- **K3:** średni wynik „zbliżanie w czasie ruchu kamery” ≥ 0,5 × średni wynik czystych zbliżań testowych.
Po wyniku niczego nie stroję pod ten test.
