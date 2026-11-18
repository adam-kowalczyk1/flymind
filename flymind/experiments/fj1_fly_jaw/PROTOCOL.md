# FJ1: szczęka SO-101 sterowana obwodem dotykowym nogi muchy (replikacja konfiguracji dostrojonej w pilocie)

**Status:** v1, spisany 2026-11-03 przed uruchomieniem. Po red teamie zostanie zamrożony sumami sha256 w manifeście.
To MODEL w symulacji MuJoCo, nie mucha i nie prawdziwy robot.

## Co dokładnie badamy

**Badane:** wyłącznie sterowanie szczęką. O momencie szczęki od pierwszego dotyku do końca próby decyduje obwód
czuciowo-ruchowy lewej środkowej nogi (T2 L) z MaleCNS v1.0 (`leg_circuit.py`, 1507 neuronów), uruchomiony jako `SparseALIF`.

**Niebadane:** ramię sięga po piłeczkę klasycznym rusztowaniem (`reach.py`, źródło `classical:reach`). Wynik FJ1 nie mówi
nic o sterowaniu ramieniem przez muchę.

**Wejście [MODEL]:** dotyk padów [N] × 40 mV/N (maksymalnie 40 mV) trafia do receptorów szczecinkowych tej nogi. Połowa
receptorów przypada na pad stały, połowa na ruchomy.

**Wyjście [MODEL, ANALOGIA]:** moment = 0,005 N·m/Hz × (pula „Ti extensor MN” − pule „Ti flexor MN” i „Acc. ti flexor MN”).
Prostownik oznacza zaciskanie. To mapowanie wybrano PO pilocie, który pokazał, że dotyk pobudza głównie prostownik.
FJ1 testuje je na nowych warunkach. Mucha nie ma chwytaka: to analogia, nie biologia chwytu.

## Parametry zamrożone z pilota (bez zmian w FJ1)

| Parametr | Wartość |
|---|---|
| J0 | 0,2 mV/synapsę |
| gain | 40 mV/N |
| rate_tau | 50 ms |
| k | 0,005 N·m/Hz |
| odstęp stałego padu | 4 mm |
| dosuw boczny | 8 mm, z prędkością 0,02 rad/s |
| trzymanie | 150 taktów |
| uniesienie | 6 cm |
| ALIF | `ALIFParams()` bez zmian, szum 0 |

## Warunki (nowe względem pilota)

- **Siatka:** 12 pozycji piłeczki, promień 0,17 / 0,20 / 0,23 m × azymut −25° / −10° / +10° / +25°.
- **Pilot używał innych pozycji:** (0,25; 0,03), (0,20; −0,10) i (0,22; 0,10), czyli promienie ok. 0,22–0,25 m.
- **Wymiana siatki:** pierwotna siatka miała promienie 0,19 / 0,23 / 0,27 m. Planer nie osiągał punktów 0,27 m
  (sprawdzenie samego IK, przed jakimkolwiek wynikiem chwytu), więc siatkę wymieniono na obecną.
- **Determinizm:** symulacja jest deterministyczna, więc jedna próba na pozycję i ramię.

## Ramiona

| Ramię | Sterownik szczęki | Liczba prób |
|---|---|---|
| A−1 | obwód z danych, Glu = −1 (glutaminian hamuje) | 12 |
| A+1 | obwód z danych, Glu = +1 | 12 |
| C−1 | ten sam obwód przetasowany (podwójne zamiany krawędzi o identycznej wadze ze znakiem: zachowane stopnie wejścia i wyjścia oraz siła wejściowa każdego neuronu), 10 instancji, ziarna 9 201 001–010 | 120 |
| C+1 | jw. dla Glu = +1, ziarna 9 201 011–020 | 120 |
| D | trywialny odruch klasyczny: dowolny pad > 0,2 N → 0,5 N·m zamykania, inaczej 0 (bez pamięci) | 12 |

**Nie robimy:** ramienia „wyrocznia”, bo D już zamyka szczękę od pierwszego dotyku, oraz ramienia „odcięte wejście”, bo bez
wejścia obwód milczy z konstrukcji (test sprawdzony w `test_fly_jaw.py`).

## Miara

**Sukces próby** = wszystkie trzy warunki naraz:
- piłeczka uniesiona o ≥ 40 mm na końcu;
- obie szczęki > 0,2 N na końcu;
- zero kontaktów ramienia ze stołem.

**Dodatkowo raportowane:**
- uniesienie [mm];
- siły na końcu;
- takt pierwszego momentu zamykającego;
- częstości pul;
- źródła komend.

## Hipotezy i reguły decyzji (ustalone przed uruchomieniem)

**H1 (zdolność), osobno dla Glu = −1 i Glu = +1.**
- POTWIERDZONA, gdy A ma ≥ 10/12 sukcesów.
- ODRZUCONA, gdy ≤ 7/12.
- Pomiędzy wynik jest NIEROZSTRZYGNIĘTY.

**H2 (znaczenie konkretnych połączeń), osobno dla każdego znaku.**
- POTWIERDZONA, gdy spełnione są oba warunki:
  - sukcesy A są większe od sukcesów KAŻDEJ z 10 instancji C;
  - średnia C ≤ A − 4 (o co najmniej 4 sukcesy na 12).
- ODRZUCONA, gdy średnia C ≥ A − 1.
- Pomiędzy wynik jest NIEROZSTRZYGNIĘTY.

**H3 (czy obwód daje więcej niż trywialny odruch)** jest tylko raportowana, nie twierdzimy jej z góry.
- Jeśli D ≥ A: obwód muchy działa, ale nie daje przewagi nad prostym odruchem. Tak to opiszemy.
- Sukces D nie jest sukcesem biologii.

**Główne twierdzenie dozwolone przy H1 i H2 potwierdzonych** (dla danego znaku): „w tym modelu obwód dotykowy nogi muchy
z danych, przy zamrożonym mapowaniu, steruje szczęką tak, że chwyta i podnosi piłeczkę w nowych pozycjach, a działa to
dzięki konkretnym połączeniom, nie samej liczbie i sile połączeń”.

## Czynniki zakłócające i ograniczenia

1. Mapowanie wyjścia wybrano po pilocie, więc przewaga A nad C może częściowo wynikać z tego wyboru. C ma tę samą listę
   neuronów i to samo mapowanie, ale tasowanie zmienia, które MN dostają sygnał.
2. Klasyczne rusztowanie (dosuw boczny) daje pierwszy kontakt i kształtuje warunki.
3. Fizyka piłeczki (toczenie) i geometria szczęk (ruchoma szczęka obraca się) mogą dominować nad sterownikiem.
4. Brak szumu, więc wyniki nie obejmują zmienności neuronalnej.
5. n = 12 pozycji to mało, a rozróżnialność jest ograniczona.
6. Glu = ±1 to dwa skrajne założenia, a nie prawda biologiczna.

## Przebieg

1. Red team tego protokołu.
2. Poprawki.
3. Zamrożenie (sha256 kodu w manifeście).
4. Smoke: pozycja z pilota poza siatką, ziarna smoke, wyniki nieanalizowane.
5. `--run`.
6. Analiza `analyze_fj1.py`, spisana przed uruchomieniem `--run`.
7. Red team wyników.

## Ujawnienie po smoke (2026-11-03, przed red teamem i przed `--run`)

**Smoke** (pozycja z pilota 0,25 / 0,03, poza siatką, ziarna 9 208 001–002): sukces we wszystkich 5 ramionach (A−1, C−1, A+1, C+1, D),
także w obu przetasowanych kontrolach. Potok działa.

To ostrzeżenie, że H2 może nie przejść. **Protokołu z tego powodu NIE zmieniono**: zmiana reguł po zobaczeniu wyniku
byłaby dopasowaniem. Smoke nie wchodzi do analizy.

## Poprawki po red teamie r1 (2026-11-03, przed `--run`)

Red team r1 dał werdykt PASS WITH ISSUES (bez blokerów). Na własnych ziarnach 9 209 xxx ustalił:
- **Zadanie jest progowe:** stały moment po dotyku ≥ ok. 0,14 N·m daje 12/12, ≤ 0,12 N·m daje 0/12. Odruch D dał 12/12.
- **Pozycje to pseudo-powtórzenia:** wynik jest prawie identyczny na wszystkich 12.
- **Przetasowane instancje działają „wszystko albo nic”:**
  - Glu −1: 4 z 10 instancji udanych na każdej pozycji;
  - Glu +1: 10 z 10 udanych.
- **Tasowanie nie zachowuje klas neuronów:** tworzy np. więcej połączeń receptor → MN. Krawędzie o unikalnej wadze zostają
  na miejscu.

**Progi H1/H2, mapowanie, tasowanie i ziarna pozostają bez zmian.** Ich zmiana po tych wynikach byłaby dopasowaniem po fakcie.

**Dodane, bez wpływu na reguły:**
1. Ramię N (moment 0 po dotyku): kontrola, czy rusztowanie samo chwyta.
2. Wtórna tabela instancji C (sukcesy każdej instancji, liczba instancji ≥ A). Jednostką jest instancja, nie pozycja.
3. W programie:
   - zabezpieczenie przed nadpisaniem wyników;
   - status błędu zamiast przerwania całego przebiegu;
   - zapis przycięć momentu przez warstwę bezpieczeństwa;
   - zapis kąta szczęki na końcu i taktu pierwszego dotyku;
   - pełniejszy manifest (dane, MJCF, analiza, wersje bibliotek).
4. W analizie: kontrola integralności (każda próba ok, 12 na instancję, oczekiwane źródła komend) oraz neutralne
   sformułowanie H3 osobno dla każdego znaku.

**Ograniczenia dopisane do interpretacji:**
- FJ1 jest replikacją konfiguracji dostrojonej w pilocie (gain, dosuw, mapowanie, k), a nie niezależnym testem zdolności.
- Pulę „prostownik” wybrano po zobaczeniu odpowiedzi obwodu z danych, więc H1 i H2 zależą od tego wyboru.
- C to tasowanie zachowujące stopnie i siłę wejściową, ale nie warstwy receptor → IN → MN. Wygrana A nad C nie odróżniłaby
  „konkretnych połączeń” od „struktury warstw”.
- 12 pozycji nie jest 12 niezależnymi obserwacjami.

**Język raportu ustalony z góry:**

| Wynik | Znaczenie |
|---|---|
| H1 potwierdzona | obwód z danych potrafi przy tym rusztowaniu dać moment zamykający wystarczający do chwytu i uniesienia |
| H2 nierozstrzygnięta lub odrzucona | brak dowodu, że liczą się dokładnie te połączenia |
| D ≥ A | brak przewagi nad trywialnym odruchem; zadanie jest rozwiązywalne jedną linijką kodu |
| N = 0 | moment z obwodu jest konieczny, czyli rusztowanie samo nie chwyta |

Nic z tego nie jest dowodem, że mucha chwyta.
