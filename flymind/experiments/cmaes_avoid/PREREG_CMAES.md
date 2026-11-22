# PLAN (przed liczeniem) — CMA-ES: „ucz muchę ruszać się w nowym ciele” (22 XI 2026)

Spisane PRZED jakimkolwiek przebiegiem strojenia. Hash tego pliku i `cma_avoid.py` zapisać w `results/PRE_RUN_HASH.txt`
przed przebiegiem próbnym. Zmiany po wynikach = tylko jako opisane odstępstwo.

## Pytanie
Czy strojenie kilkudziesięciu pokręteł (bez zmiany połączeń z MaleCNS) uczy sieć muchy niezawodnie cofać ramię przed
dotykiem dłoni — i czy to zasługa połączeń z danych, a nie samego strojenia?

## Zadanie (wybór z kroku 3)
„Nie dać się dotknąć” (`step3_wiring/avoid.py`, test avoid r1 z 19 XI): ręka (kula 4 cm, 0,3 m/s) leci w dłoń chwytaka
z lewej / prawej / z przodu. Pasuje do pokazu: prawdziwe FSR → mózg muchy → ramię w symulacji (`live_avoid.py`).
Avoid r1 z głową: unika tylko 9/15 (FAILED A1), ale A2–A4 PASS → jest co poprawiać i jest uczciwa kontrola.
- Sieć **BrainNet** („pre” + 69 BM + 2 DNge078 + 2 DNg15 = 3 221 neuronów) zamiast głowy (15 tys., ~9 GB): jedna próba
  ~3 s. Bez wzroku (wzrok przeszkadzał w r1, a sieć bez głowy nie ma oka).
- Dotyk **hw2p** (jak pokaz): A0 szczęka stała → szczecinki nogi „udo”, P dłoń → BM; model czujnika `touch_map.Feel`.
- Glu −1, szum 2 mV, ziarno nerwów = ziarno szumu. Kinematyka bez fizyki (jak avoid r1).
- Pomiar czasu (rozwój, 22 XI, ziarna 26 100 001–002, przed tym planem): sieć bez strojenia cofa łokieć/nadgarstek po
  dotyku dłoni (dq ≈ −0,16 / −0,10 rad), dotyk 0,94–1,58 s zamiast 1,63–1,80 s (ramię nieruchome); bez dotyku stoi.
  Bark (staw 1) się nie rusza. Próba ~2,8 s przy obciążonym Macu.

## Pokrętła (sieć z danych i tasowania: 2 + 6 + liczba bloków + 1 ≈ 30)
Wszystkie w skali log: wzmocnienie = exp(x), x ∈ [−3, 3], start x = 0 (= sieć jak dotąd), σ₀ = 0,5.
1. Wejścia (2): siła pobudzenia receptorów z A0 i z dłoni.
2. Wyjścia (6): wzmocnienie puli POS i NEG motoneuronów dla stawów 1, 2, 3.
3. Bloki połączeń (≤ 25, tylko istniejące): mnożnik wszystkich synaps grupa_pre → grupa_post, grupy z adnotacji:
   S (czucie nogi), BM, DN (DNge078 + DNg15), I (interneurony VNC), M (motoneurony).
4. Hamowanie (1): mnożnik wszystkich synaps ujemnych.
Która synapsa istnieje, jej znak i względna waga wewnątrz bloku — z danych, NIE stroimy.

## Kontrole (każda strojona OSOBNO tym samym budżetem)
- **N** dane.
- **L-A, L-B** dwa tasowania „w obrębie warstw” (`side_shuffle`, kind L), ziarna 26 130 001 i 26 130 002, te same pokrętła
  (grupy neuronów te same, bo zależą od tożsamości neuronu, nie od połączeń). Porównanie N z tasowaniami = protokół
  „kontrole strojone osobno” (wniosek z przeglądu 21 XI: stroić pod dane i przenosić na tasowania = fałszywa przewaga).
- **Placebo** = L-A vs L-B: o ile różnią się dwa tasowania strojone tak samo (szum metody).
- **D „bez muchy”**: czujniki prosto do pul stawów: 2 wejścia + 6 wyjść + 12 wag czujnik→pula (20 pokręteł), ten sam
  filtr wyjścia i ten sam budżet. Tylko odniesienie: ile daje samo strojenie prostego drutu.

## Budżet i strojenie
- CMA-ES (`cma_avoid.py`, własna implementacja, sprawdzian `selftest`), λ = 12, **40 pokoleń** = 480 ocen na sieć.
- Ziarna CMA: N 26 140 001, L-A 26 140 002, L-B 26 140 003, D 26 140 004.
- Zbiór uczący: szum 26 110 001, 26 110 002 × 3 kierunki = 6 prób na ocenę, te same w każdym pokoleniu.
- Ocena próby: J = czas dotyku [s] − 0,02 · min(10, odstęp końcowy [cm]) + 2 · ruch przed pierwszym dotykiem [rad].
  (Kara za ruch bez dotyku: sieć nie może „uciekać na ślepo”.) Cel = średnie J, mniejsze lepsze.
- Wynik strojenia = środek rozkładu CMA po ostatnim pokoleniu (nie najlepszy pojedynczy punkt).
- Wątki: `OMP_NUM_THREADS=1`, `nice -n 10`; uczenie oka P3 NIE jest wyłączane.

## Przebieg próbny (przed pełnym)
Ziarna rozwojowe 26 100 011–012 zamiast uczących, 3 pokolenia, sieć N i D. Sprawdza: (a) `fast_step` daje to samo co
pomiar z 22 XI (x = 0, ziarno 26 100 001, lewa: czas dotyku 1,16 s), (b) czas pokolenia, (c) brak błędów.
Wyniki próbne NIE wchodzą do oceny. Jeżeli pokolenie trwa > 15 min, zmniejszyć do 30 pokoleń (opisać, zanim ruszy pełny).

## Test (RAZ, po zakończeniu strojenia wszystkich 4 sieci)
Ziarna szumu **26 120 001 – 26 120 005** × 3 kierunki = 15 scen (`CMA_FINAL_TEST=1`). Warunki:
- N strojona: full, numb (bez dotyku), lesion (wycięte wyjścia DNg15 + DNge078); N bez strojenia (x = 0): full.
- L-A, L-B strojone: full, numb.  D strojona: full, numb.
- Odniesienie „ramię nieruchome” T₀ na scenę (z avoid: 1,80 s z lewej, 1,63 s z prawej i z przodu; sprawdzane warunkiem frozen).
„Unika” = czas dotyku < T₀ − 0,2 s.

## Kryteria (liczone na teście, N = strojona sieć z danych)
- **C1 uczy się:** N unika w ≥ 13/15 scen ORAZ średni czas dotyku N ≤ (N bez strojenia) − 0,3 s.
- **C2 dzięki dotykowi:** N numb unika w ≤ 2/15 scen.
- **C3 dzięki drodze głowa→noga:** N lesion unika w ≤ 2/15 scen.
- **C4 dzięki połączeniom z danych:** średni czas dotyku N < średniej L-A − 0,2 s ORAZ < średniej L-B − 0,2 s.
- **C5 placebo:** |L-A − L-B| < min(L-A, L-B) − N (przewaga danych większa niż różnica między dwoma tasowaniami).
**PASS = C1 ∧ C2 ∧ C3 ∧ C4 ∧ C5.** Inaczej FAILED (z opisem, które kryterium padło).
D: tylko opis (oczekiwanie przed liczeniem: prosty drut nauczy się prawie idealnie; to pokazuje cenę „mucha decyduje”,
a nie porażkę muchy). Jeśli tasowania też dochodzą do ≥ 13/15, to C4/C5 rozstrzygają — piszemy to wprost.

## Ziarna
Rejestr `SEED_REGISTRY.md` w tym katalogu (zakres 26 100 000 – 26 199 999).
