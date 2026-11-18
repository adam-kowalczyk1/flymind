# Formularz Explory — proponowane zmiany zdań (14 XI 2026)

Plik formularza (`reports/Explory 2026 – formularz zgłoszeniowy.md`) **nie został zmieniony** i nic nie zostało wysłane.
Poniżej tylko tekst do ręcznego wklejenia. Zmiany dotyczą pkt 33 („Dotychczasowe testy…”), akapit drugi i czwarty.

## Zmiana 1 (wymagana) — pkt 33, akapit 2

**Stare (jedno zdanie po drugim, razem 300 znaków):**
> W jednym z testów celowania w piłeczkę sieć oparta na danych konektomicznych osiągnęła 38 trafień na 40 prób. W tym samym
> zestawie testów sieć z przetasowanymi połączeniami osiągnęła 3/40, a sieć z zamienionymi stronami 0/40. Klasyczny regulator
> osiągnął 40/40, czyli w tym zadaniu był dokładniejszy.

**Nowe:**
> W jednym z testów celowania w piłeczkę sieć oparta na danych konektomicznych osiągnęła 38 trafień na 40 prób, a klasyczny
> regulator 40/40 i był dokładniejszy. Sieć z przetasowanymi połączeniami osiągnęła 3/40, ale to tasowanie osłabiało też
> połączenia; w dodatkowej kontroli, w której tasowanie zachowywało siłę połączeń po każdej stronie, przetasowana sieć
> również trafiała. Wynik pokazuje więc znaczenie podziału na stronę lewą i prawą, a nie szczegółów schematu połączeń.
> Test z zamienionymi stronami (0/40) traktuję tylko jako sprawdzenie, że układ naprawdę reaguje na obraz.

**Uzasadnienie:**
- „38/40 kontra 3/40” czytane samo sugeruje, że liczy się dokładny schemat połączeń. Kontrola Red Team
  (`flymind/VALIDATION_PLAN.md` § „V4/V5 — Red Team”, pkt 1): tasowanie zachowujące siłę wejścia i wyjścia każdego neuronu
  daje 10/10 (REPORTED — brak zachowanego pliku, dlatego w zdaniu nie ma liczby), a pierwotne tasowanie obniżało siłę wejścia
  neuronów wyjściowych ok. 2,4–4,3 razy (z ok. 462 do 107–193 mV na impuls).
- „0/40 zamienione strony” nie jest dowodem roli połączeń: każdy sterownik, który niesie informację o stronie, oblałby ten
  test (tamże, pkt 3). W oryginale stało obok 3/40 jak drugi dowód.
- Liczby 38/40, 3/40, 0/40, 40/40 — VERIFIED (`flymind/results/v5/analysis_confirm.json`), bez zmian.
- Spójne z plakatem (sekcja S4).

## Zmiana 2 (zalecana, żeby formularz zgadzał się z plakatem) — pkt 33, akapit 4

**Stare:**
> Przeprowadziłem również wstępne testy związane z dotykiem i sterowaniem chwytakiem. Ich wyniki traktuję jako pilotażowe:
> samo osiągnięcie poprawnego ruchu nie dowodzi jeszcze, że odpowiada za niego konkretna biologiczna organizacja połączeń.

**Nowe:**
> Przeprowadziłem również testy sterowania chwytem na podstawie dotyku. Sieć oparta na danych przeniosła do pudełka 90
> przedmiotów na 135 prób, klasyczny sterownik 93, prosty odruch 80, a sieci z przetasowanymi połączeniami od 4 do 102.
> Nie stwierdziłem więc przewagi biologicznego schematu połączeń. Próba sterowania całym ramieniem zakończyła się wynikiem
> negatywnym: sieć oparta na danych unosiła przedmiot, ale nie odłożyła żadnego na 135 prób. Te wyniki także dokumentuję.

**Uzasadnienie:** od złożenia formularza (9 XI) powstały pełne serie z kontrolami; „pilotażowe” jest już nieaktualne,
a plakat podaje te liczby. Wszystkie liczby VERIFIED (źródła w `POSTER_CONTENT.md`, tabela na końcu). Jeśli formularz
jest już złożony i nie można go edytować — zostawić, a różnicę wyjaśnić ustnie; plakat jest aktualniejszy.

## Czego nie ruszałem

Tytuł, pytanie badawcze, opis metody, pkt 32 i 36 są zgodne z plakatem. Zdanie z pkt 33 akapit 3 („wpływ dokładnej struktury
połączeń nie jest jednakowy we wszystkich warunkach”) pozostaje prawdziwe.
