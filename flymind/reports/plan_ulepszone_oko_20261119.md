# Plan: ulepszone wejście oka (LPLC2, LC4 i reszta „zbliżania”) — 19 XI 2026

Status: **PLAN, nic nie uruchomione** poza jednym odczytem danych (rozpoznanie niżej). Prawdziwe ramię: nie dotyczy (tylko symulacja).

## 1. Po co
Dziś (`avoid.py`, linie 89–96) nasz kod liczy dwie liczby: jak szybko ręka rośnie w polu widzenia i z której strony jest.
Potem wpuszcza **ten sam prąd** do wszystkich ~375 komórek pięciu typów zbliżania po danej stronie
(LPLC2, LC4, LPLC1, LC6, LC16). U prawdziwej muchy:
- każda komórka patrzy na swój kawałek pola widzenia (ręka z góry zapala inne komórki niż ręka z boku);
- typy liczą co innego: LC4 głównie **szybkość** nadlatywania, LPLC2 głównie **wielkość** plamy.
  Wielkie włókno (DNp01) łączy oba sygnały i wybiera szybki albo porządny skok (Ache i in. 2019; von Reyn i in. 2017 — do potwierdzenia w streszczeniach przy K0).

Cel: wejście oka bliższe prawdziwej musze, żeby mózg muchy dostawał „gdzie” i „jak szybko”, a nie jedną liczbę na stronę.

## 2. Uczciwie: czym to NIE jest
To nadal **nasz kod pobudzający wybrane neurony** — ta sama kategoria co dziś i co koder koloru → LC10a
(decyzja Adama 12 XI: „sztuczne pobudzanie wybranych neuronów”). Ulepszenie robi to wierniej, ale **nie jest to oko muchy**
(prawdziwe oko z flyvis jest zamrożone do po Explory po sześciu nieudanych testach). Na plakacie: „wejście oka liczone naszym kodem,
rozłożone na komórki według mapy pola widzenia odczytanej z połączeń muchy”.

## 3. Rozpoznanie (19 XI, tylko odczyt danych MaleCNS)
- Kolumny oka mają położenia w danych dla **obu oczu** (`assignedOlHex1/2`; np. Mi1: 875 L, 887 R).
- LPLC2 i LC4 nie mają własnego położenia, ale da się je wyliczyć ze środka ciężkości wejść z komórek kolumnowych:

| typ | strona | komórek | mediana synaps z kolumn | mediana kolumn | rozrzut (kolumny) |
|---|---|---|---|---|---|
| LC4 | L | 71 | 134 | 30 | 2,6 |
| LC4 | R | 55 | 468 | 52 | 2,9 |
| LPLC2 | L | 94 | 57 | 14 | 1,8 |
| LPLC2 | R | 91 | 118 | 25 | 2,0 |

  Środki komórek pokrywają prawie całe oko (kolumny 4–34 z 1–36 i 3–36 z 1–39) — mapa jest, nie trzeba jej wymyślać.
- Słabe miejsce: to tylko **jeden krok** (wejścia od komórek z adnotacją kolumny). LPLC2 dostaje głównie T4/T5, które tej adnotacji
  w większości nie mają — stąd mało synaps (57) i za wąskie pola. K0 użyje drogi dwukrokowej jak most B1 (`v1_camera_input/bridge_prep.py`:
  położenie T4 = środek wejść Mi1, T5 = Tm1/Tm2/Tm4/Tm9) — kod już jest i był sprawdzony 16–17 XI.

## 4. Kroki

**K0 — mapa pól widzenia (tylko odczyt, ~pół dnia).** Plik `flymind/experiments/step3_wiring/eye_rf.py` → `eye_rf.json`.
- Dla każdej komórki 5 typów zbliżania (obie strony): środek i rozmiar pola (kolumny → kąty; odstęp kolumn ok. 5°, do potwierdzenia),
  liczony dwukrokowo; jednokrokowy jako sprawdzian.
- Orientacja oka względem głowy: kierunek przód/góra z danych (gradient numerów kolumn) + jedno jawne założenie zapisane w pliku.
- **Bramka G-K0** (spisana przed liczeniem): ≥ 90 % komórek ma pole; pola LPLC2 i LC4 razem pokrywają ≥ 80 % kolumn każdego oka;
  mediana rozmiaru pola LPLC2 w granicach podanych w literaturze (sprawdzę liczbę przed liczeniem). Nie przechodzi → stop i raport.

**K1 — nowe wejście oka (kod, ~pół dnia).** W `avoid.py` flaga `--eye uniform|rf` (domyślnie `uniform` = dziś, bez zmian).
- Ręka rzutowana do „oczu” (oś przy chwytaku, jak dziś): położenie kątowe i rozmiar kątowy θ osobno dla lewego i prawego oka.
- Każda komórka dostaje prąd ∝ nakładanie się ręki z jej polem (waga Gaussa):
  - LC4: × szybkość rośnięcia dθ/dt (jak dziś);
  - LPLC2: × rozmiar θ, bramkowany rośnięciem (bez rośnięcia = 0);
  - LPLC1, LC6, LC16: × dθ/dt (uproszczenie, zapisane).
- **Ta sama łączna dawka**: suma prądu w populacji przy tej samej ręce ma być taka jak w `uniform`,
  żeby różnice wynikały z rozkładu, a nie z siły.
- `_check()`: ręka z lewej zapala głównie komórki lewego oka; ręka nieruchoma → LPLC2 0; `uniform` daje bit w bit stary JSON (próba r2 i 21950001).

**K2 — rozwój (ziarna 21 955 001–099, tylko symulacja, ~1 dzień).** Te same 5 ustawień ręki co przegląd 19 XI, 3 kierunki,
z wzrokiem / bez, mucha bez zmian i z wyciszonym hamulcem; dodatkowo ręka **z góry**. Patrzę na:
czas odpalenia DNp01 przed dotykiem, hamulec DNg98+DNg70, MDN, unikanie. Kontrole: (a) **tasowanie pól** (losowe przypisanie środków
w obrębie typu) — jeśli wynik ten sam, mapa nie ma znaczenia; (b) **zamiana typów** (LC4 dostaje sygnał LPLC2 i odwrotnie).

**K3 — test (spisany i zahashowany po K2, przed uruchomieniem; ziarna 21 956 001–005 + losowanie kontroli 21 956 901).**
Kandydaci na hipotezy (wybór po K2):
- H1: wynik „hamulec” r1 utrzymuje się z nowym okiem (S unika ≥ 4/5 na kierunek, N słabiej o ≥ 0,3 s) — powtórzenie pod nowym wejściem;
- H2: mapa ma znaczenie — z prawdziwymi polami zachowanie różni się od tasowania (np. ręka z góry vs z boku);
- H3: szybkość ma znaczenie — przy szybkiej ręce wielkie włókno odpala wcześniej względem dotyku niż przy wolnej, a zamiana typów to psuje.

**K4 — raport po polsku, commit, push** (`origin flymind/fly-first-control`, bez `*.npz`, `raw/`, `.DS_Store`), wpis w `SEED_REGISTRY.md` i pamięci.

## 5. Ryzyka
- Przeliczenie kolumn na kąty i orientacja oka mogą być niedokładne (jedno założenie, jawnie zapisane).
- Może się okazać, że mapa niczego nie zmienia (H2 nie przejdzie) — to też uczciwy wynik.
- Nowe wejście może zmienić wynik hamulca — dlatego `uniform` zostaje domyślne, a pokaz/panel się nie zmieniają, dopóki K3 nie przejdzie.
- Pamięć: ~7 GB na proces → najwyżej 2–3 równolegle; długie przebiegi pod `caffeinate`.
- Czas: K0–K3 ok. 3 dni → koniec ok. 23 XI, w terminie badań (do 27 XI).

## 6. Decyzje dla Adama
1. Czy zgadzasz się, że to nadal „sztuczne pobudzanie wybranych neuronów” (jak dziś), tylko wierniejsze? Bez tej zgody — nie robię.
2. Zakres: tylko K0 (sam odczyt mapy, bez zmian w zachowaniu) czy od razu K0–K3?
3. Jeśli K3 przejdzie: czy nowe oko ma się stać domyślne w podglądzie mózgu i pokazie, czy zostaje tylko w badaniach?
