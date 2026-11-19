# LOOP_TARGET avoid r1 — „nie dać się dotknąć”, test (19 XI 2026)

Spisane PRZED uruchomieniem ziaren testowych. Hash SHA-256 tego pliku zapisany w
`results/step3_20261115/avoid_r1/PRE_TEST_HASH.txt` przed pierwszym przebiegiem testowym.

## Pytanie
Czy sieć z danych (noga „pre” + BM + DNg15/DNge078 + głowa 11 tys. + wszystkie komórki LPLC2/LC4/LPLC1/LC6/LC16)
sama, bez reguły „uciekaj”, skraca czas, przez który ręka (kula 4 cm, 0,3 m/s) dotyka chwytaka — i czy to zasługa
połączeń z danych (tasowania), dotyku (bez dotyku), drogi głowa→noga (wycięcie DNg15+DNge078) i MIEJSCA dotyku (mapa)?

## Układ (kod `avoid.py`, tryb wsadowy)
- Glu −1 (główny). Glu +1 tylko raport (18 XI: napad głowy).
- Szum 2 mV; ziarna szumu = ziarna nerwów: 21 949 001 – 21 949 005 (5). Kierunki ręki: left, right, front.
- Dotyk **hw2p** (GŁÓWNY, zmiana 19 XI po próbie rozwojowej — patrz niżej): czują tylko 2 krążki FSR402:
  A0 szczęka stała → grupa szczecinek T2 L „udo” (`touch_map.json`, status: HIPOTEZA, klaster połączeń), P „dłoń” (spód
  serwa między szczękami) → szczecinki głowy BM (jak dłoń w krokach 5–6); model czujnika `touch_map.Feel` (5,1 kΩ, „typ”).
  Ręka celuje w dłoń (`--aim palm`).
- Dotyk **hw2** (sprawdzian „gdzie”): A0 szczęka stała + A1 szczęka ruchoma (obecny projekt czujników, oba → szczecinki
  nogi T2 L), dłoń bez czujnika; ręka celuje między szczęki (`--aim tips`).
- Dotyk **sim3** (porównanie z 18 XI): 3 punkty (pady + dłoń), ręka w dłoń (`--aim palm`).
- Warunki sieci z danych: full, frozen (ramię stoi), numb (bez dotyku), blind (bez wzroku), lesion (bez DNg15+DNge078).
- Tasowania (tylko full, tryby sim3 i hw2p): F ×4 (ziarna 21 949 901–904), L ×2 (21 949 911–912) — L tylko jeśli czas budowy pozwoli
  (decyzja przed testem: TAK — budowa L zmierzona 19 XI: 7,3 min, 7,7 GB).
- Mapa udo/goleń: tylko „somato” (mapa jest hipotezą; test WHERE r1 pokazał, że podział nie zmienia rozróżnialności) —
  porównanie swap/halves z poprzedniej wersji tego pliku USUNIĘTE przed testem.
- Glu +1: tylko hw2p full/frozen (raport, bez kryteriów).
- Zmiana przed testem (19 XI, ziarno rozwojowe 21 948 001, kierunki left/front): sam dotyk szczęk (hw2) prawie nie
  rusza ramienia (dq ≤ 0,02 rad), dotyk dłoni (sim3, hw2p) cofa bark o ~0,7 rad z lewej. Stąd układ główny hw2p
  i nowe kryterium G (przewidywanie oparte na tej próbie — zaznaczone).

## Miara (na próbę)
`touched_s` — czas [s], gdy siła geometryczna w którymkolwiek z 3 punktów (pady, dłoń) > 0,2 N (ta sama miara dla
sim3 i hw2, niezależna od czujników). Pomocniczo `end_gap_cm`.
Para = ten sam kierunek i ziarno (15 par na sieć/warunek).

## Kryteria (hw2p, Glu −1; każde liczone automatycznie przez `analyze_avoid.py`)
- **A1 unika:** full < frozen − 0,2 s w ≥ 4/5 ziaren, w KAŻDYM z 3 kierunków.
- **A2 dzięki dotykowi:** numb ≥ frozen − 0,2 s w ≥ 4/5 ziaren w każdym kierunku (bez dotyku nie unika).
- **A3 dzięki drodze głowa→noga:** lesion ≥ frozen − 0,2 s w ≥ 4/5 ziaren w każdym kierunku.
- **A4 dzięki połączeniom z danych:** średnie touched_s (15 par) danych < średniej KAŻDEGO tasowania o ≥ 0,2 s.
- **G „miejsce decyduje”:** hw2 (same szczęki): full ≥ frozen − 0,2 s w ≥ 4/5 ziaren w każdym kierunku (dotyk szczęk
  NIE wywołuje unikania), przy spełnionym A1 dla hw2p.
PASS „unika dotyku dzięki połączeniom” = A1 ∧ A2 ∧ A3 ∧ A4. „Miejsce dotyku decyduje” = G ∧ A1 (osobno).
Wzrok (full vs blind): tylko opis, bez tezy. sim3 i hw2: te same A1–A4 raportowane jako opis.

## Ziarna rozwojowe
21 948 001 – 21 948 099 (sprawdzanie kodu, budżet czasu) — wyniki NIE wchodzą do testu.
