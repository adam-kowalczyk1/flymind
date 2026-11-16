# FlyMind — 16 XI 2026: nadgarstek (wynik testu) i „dozowanie siły” (sprawa 2)

Wszystko w symulacji. Cele zapisane przed testami (`PRE_TEST_HASHES.txt`), nowe ziarna wpisane wcześniej do
`experiments/step3_wiring/SEED_REGISTRY.md`, każdy test uruchomiony raz. Liczby i komendy: `audit_log_step3_20261115.md`
(kroki 29–37 — nadgarstek; D1–D5 — dawka). Nic nie zacommitowane.

Pracowały dwie sesje naraz. Druga sesja („FlyMind projekt status audit”) przeanalizowała test nadgarstka i prowadzi
nadgarstek dalej; ta sesja zajęła się dawką. Podział przekazała mi druga sesja jako zatwierdzony przez Adama.

## 1. Nadgarstek — test 21701

**FAILED o jedną próbę** (kryterium K5-A). Ruch nadgarstka po dotyku dłoni: 19 z 25 prób (próg: 20, czyli 80 %), dla obu
wariantów znaku Glu. Spoczynek nadgarstka przy chwycie: 30 z 30. Liczby sprawdziłem sam w
`wrist_test/analysis_wrist.json`; zgadzają się z logiem. [VERIFIED, model]
Droga z danych „szczecinki głowy → DNge078 → dźwigacz stępu” działa w modelu, ale nie w każdej próbie.
Porównanie z tasowaniami (K5-B): tasowania swobodne nigdy nie ruszają nadgarstkiem (H-R(F) potwierdzona, oba Glu);
tasowania warstwowe — potwierdzone tylko dla Glu +1. Ciąg dalszy prowadzi druga sesja (test 5b w toku).

## 2. Dozowanie siły zacisku — nowy test

**Pytanie:** czy sieć z danych lepiej niż sieci o przetasowanych połączeniach zamienia „jak mocno dotknięto” na
„jak mocno zacisnąć”? Bez robota: 9 poziomów dotyku padów (0–1 N), dane kontra 60 nowych tasowań na wariant znaku.

**Wynik według reguł zapisanych przed testem: FAILED.**

| | Glu +1 | Glu −1 |
|---|---|---|
| Zacisk sieci z danych przy pełnym dotyku | 0,90 N·m | 0,62 N·m |
| Najmocniejsze z 20 tasowań swobodnych / 20 warstwowych | 0,71 / 0,75 | 0,26 / 0,28 |
| Tasowania z zachowanym podziałem na nogi, które dorównały danym | 6 z 20 | 1 z 20 |
| „Czystość” zacisku (zaciskacz bez rozwieracza): tasowania lepsze lub równe danym | 15–20 z 20 | 2–18 z 20 |

Po ludzku:
- **Prawda:** przy pełnym dotyku sieć z danych zaciska mocniej niż każde z 40 tasowań swobodnych i warstwowych, przy obu
  znakach Glu. [VERIFIED, model]
- **Nie wiadomo dlaczego:** sieć z danych jest w ogóle „głośniejsza” od tasowań (znane od wczoraj). Druga miara miała
  pokazać, że to nie sama głośność, tylko lepszy podział pracy mięśni — i **nie pokazała**. Przy Glu +1 sieć z danych
  napina naraz zaciskacz (249 Hz) i rozwieracz (68 Hz), czyli współskurcz jest u niej większy niż u większości tasowań. [FAILED]
- Gdy przy tasowaniu zachowa się, które neurony należą do której nogi, przewaga w sile znika. [VERIFIED, model]
- Stopniowe dozowanie (więcej dotyku → więcej siły) mają też tasowania warstwowe — odrzuciłem to jako kryterium jeszcze
  przed testem, bo eksploracja to pokazała. [VERIFIED, eksploracja]

Bilans sprawy 2 bez zmian: schemat połączeń decyduje, **które** czucie uruchamia **który** ruch; na liczbach (ile
odłożonych przedmiotów, ile siły zacisku) przewaga sieci z danych da się wyjaśnić jej większą aktywnością, a nie
konkretnym układem połączeń.

## 3. Cztery kierunki, o które pytałeś — ocena

| Kierunek | Stan | Moja ocena |
|---|---|---|
| Dozowanie siły nacisku | zrobione dziś (wyżej) | Bez robota przegrało na kryterium „czystości”. Wersja na robocie ma sens dopiero, gdy będzie hipoteza, którą tasowania mogą przegrać; dziś jej nie ma. [INFERRED] |
| Połączenie mózg–odnóża | w toku w drugiej sesji | Najbliżej sukcesu: droga głowa → DNge078 → nadgarstek działa w 76 % prób; druga sesja znalazła też drugi szlak (DNg15). [REPORTED przez drugą sesję, nie sprawdzałem] |
| Pełniejszy układ wzrokowy | tylko plan (`reports/fly_eye_plan_20261112.md`) | Duży projekt (rdzeń ruchu 47 473 neurony). Czeka na 6 Twoich decyzji z §7 planu; bez nich nic nie zaczynam. Pierwszy krok to bramka G2: czy model T4/T5 w ogóle rozróżnia kierunek. [NOT IMPLEMENTED] |
| Więcej testów | możliwe od ręki | Najtańszy sensowny: test „dwa odruchy” z 3× większą liczbą scen (dziś 24 pary to mało na rozstrzygnięcie z tasowaniami warstwowymi). [PROP] |

## Uczciwe granice
Symulacja; neurony uproszczone; jeden zestaw parametrów; „pady = szczecinki nogi środkowej” i „mięśnie goleni = szczęka”
to nasz wybór, nie biologia; znak glutaminianu nieznany z danych, więc liczony dwukrotnie.
