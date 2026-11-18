# Panel FlyMind — log kroków (14 XI 2026)

Cel: lokalny panel HTML do uruchamiania istniejących pokazów i testów jednym kliknięciem i oglądania wyników.
Zasady dotrzymane: tylko nowe pliki w `flymind/panel/`; żaden istniejący skrypt, moduł wspólny ani wynik nie został zmieniony;
serwer wyłącznie na 127.0.0.1; zamknięta lista komend; bez benchmarków 135 prób i bez ziaren testowych; bez kodu sprzętowego;
bez push; bez kodu/SDK Artificial Brains; **bez nowych zależności** (tylko biblioteka standardowa Pythona, czysty HTML/JS bez
bibliotek z internetu). Warunki STOP nie wystąpiły.

| # | Co i dlaczego | Komenda / plik | Wynik |
|---|---|---|---|
| 1 | Sprawdzić opcje skryptów pokazów, żeby panel dawał tylko istniejące parametry | `flymind/demo/demo.py` l. 1020–1054, `flymind/demo/demo_arm.py` l. 600–684 | `demo.py`: `--mode snn/p`, `--present`, `--az`, `--rho`, `--jump`, `--seconds`; ziarno szumu stałe `SEED0 = 9 900 001` (poza pulami). `demo_arm.py`: `--item` (tylko zestaw `base`, 45 przedmiotów), `--seed` (wymagane; sam odrzuca ziarna testowe), `--pose`, `--glu`, `--speed`, `--seconds` |
| 2 | Wybrać ziarno pokazu ramienia | `experiments/step2_whole_arm/SEED_REGISTRY.md` | 20951 = „kontrola uruchomienia” (już użyte w teście pokazu i nagraniu) — jedyne w panelu, wpisane na stałe; pola ziarna brak |
| 3 | Serwer (biblioteka standardowa) | `flymind/panel/server.py` | `ThreadingHTTPServer` na stałym `127.0.0.1:8770` (bez opcji adresu); zamknięta lista 5 pozycji; parametry tylko z list/zakresów; odrzuca obcy nagłówek Host, a żądania uruchomienia bez nagłówka panelu lub z obcym Origin; media tylko z listy 8 kluczy; liczby czytane z plików wyników przy każdym żądaniu |
| 4 | Testy modułów jako jedna pozycja | `flymind/panel/run_module_tests.py` | uruchamia po kolei te same 20 zestawów co w `STATUS_20261114.md` rozdz. 4, kod 0 tylko gdy wszystkie OK |
| 5 | Strona | `flymind/panel/index.html` | zakładki: Uruchom (karty z opisem, etykietą dowodu, parametrami; lista uruchomień ze stanem, logiem na żywo, „Zatrzymaj”), Filmy i liczby (wnioski, tabela liczb z plikami źródłowymi, 5 filmów, 3 wykresy), Jak to działa |
| 6 | Wyjścia poza `results/` | `flymind/panel/runs/<czas>_<pozycja>/` (`run.json`, `log.txt`, `result.json`); `flymind/panel/.gitignore` = `runs/` | każdy przebieg w nowym katalogu (`os.makedirs(exist_ok=False)`, pliki w trybie „x”) |
| 7 | Adres nasłuchu | `lsof -iTCP:8770 -sTCP:LISTEN` | `127.0.0.1:8770` — VERIFIED; próba przez adres sieciowy komputera: brak połączenia (kod 000) |
| 8 | Zabezpieczenia API (curl) | żądania z obcym Host, bez nagłówka panelu, z obcym Origin; pozycja `rm -rf`; parametr `seed`; `item` z „; touch x”; `rho = 5`; `mode` z doklejonym `--media`; `/media/../server.py` | odpowiednio 403, 403, 403, „pozycja spoza listy”, „nieznane parametry: ['seed']”, „wartość spoza listy”, „poza zakresem”, „wartość spoza listy”, 404 — VERIFIED |
| 9 | Liczby w zakładce wyników = pliki | `GET /api/numbers` | 16 wierszy; zgodne z `STATUS_20261114.md` i `POSTER_CONTENT.md` (38/40, 3/40, 90/135, 93, 80, tasowania 4–102, 101/84, 0/135 ×2, K 81/89, tasowania ramienia, łokieć 0/45 i 32/45 z etykietą eksploracyjną); „10/10” z etykietą REPORTED — VERIFIED |
| 10 | Filmy i obrazy dostępne | `GET /api/jobs` (pole `exists`), `Range: bytes=0-999` na filmie | 8/8 plików istnieje; odpowiedź 206 z 1000 bajtów (przewijanie filmów działa) — VERIFIED |
| 11 | **Test pokazu 1 uruchomiony z panelu** (klik w przeglądarce) | pozycja `test_demo` → `runs/20261114_171757_test_demo/` | „zakończone”, kod 0, 75 s, „WSZYSTKIE TESTY OK” — **VERIFIED** |
| 12 | **Test pokazu 2 uruchomiony z panelu** | `test_demo_arm` → `runs/20261114_171757_test_demo_arm/` | „zakończone”, kod 0, 73 s, T1–T5 OK, sha trajektorii `50b22ed1…` jak w raporcie kroku 2 — **VERIFIED** |
| 13 | **Testy modułów uruchomione z panelu** | `module_tests` → `runs/20261114_171757_module_tests/` | „zakończone”, kod 0, 214 s, „20/20 zestawów OK” — **VERIFIED**. (Trzy powyższe szły równocześnie) |
| 14 | **Pokaz 1 otwarty z panelu** (sieć, kąt 20°, 0,20 m, zamknięcie po 12 s) | `demo_v5` → `runs/20261114_171839_demo_v5/` | proces zakończony sam, kod 0, 23 s; log: 424 neurony, 829 taktów, 168 klatek okna, 13,2 kl./s — uruchomienie **VERIFIED**; **to, co było widać w oknie: NOT VERIFIED** (nikt nie oglądał) |
| 15 | **Pokaz 2 otwarty z panelu i zatrzymany przyciskiem „Zatrzymaj”** | `demo_arm` → `runs/20261114_171918_demo_arm/` | stan „zatrzymane”, kod −15 po 150 s; `pgrep` — żaden proces nie został; **okno: NOT VERIFIED**. Uwaga: po SIGTERM Python zgłosił „leaked shared_memory” (niesprzątnięta pamięć współdzielona panelu pokazu) |
| 16 | Poprawka zatrzymywania (po kroku 15) | `server.py` → `stop()` | najpierw SIGINT (jak Ctrl+C, skrypt może posprzątać), po 4 s SIGTERM, po kolejnych 4 s SIGKILL; dotyczy całej grupy procesów |
| 17 | Prośba właściciela w trakcie pracy: zmiana kształtu i materiału w pokazie ramienia | `server.py` (`SHAPES`, `MATS`, `P_choice` z opisami), `index.html` (opisy w listach) | zamiast jednej listy 45 nazw technicznych — dwie listy po polsku: **kształt** (9) i **materiał** (5). Opisy z `object_handling.py` (wymiary = połówki × 2; tarcie i „odpowiednik” materiału z komentarzy). Zestaw „trudny” (lód, wolfram itd.) pominięty — `demo_arm.find_item` przyjmuje tylko zestaw `base`, a zmiana skryptu = warunek STOP. Zmiana kształtu w trakcie działającego okna też wymagałaby zmiany `demo_arm.py` — dlatego wybór działa przy otwarciu pokazu |
| 18 | Zabezpieczenia nowych list (curl, po restarcie serwera) | `shape = cube_XS`, `mat = ice`, stary parametr `item`, `shape` z doklejonym `--seed 20901` | „spoza listy”, „spoza listy”, „nieznane parametry”, „spoza listy” — VERIFIED; serwer nadal tylko `127.0.0.1:8770` |
| 19 | **Pokaz 2 z innym przedmiotem otwarty z panelu** (kula, stal, zamknięcie po 45 s) | `demo_arm` → `runs/20261114_172303_demo_arm/`; komenda `demo_arm.py --item sphere/heavy --seed 20951 …` | „zakończone”, kod 0, 71 s; log: „sieć: 2593 + 1507 = 4100 neuronów; koniec próby: success False, grasp True, lift False, reasons no_lift, no_lift” — uruchomienie z wybranym kształtem i materiałem **VERIFIED** (zgodne z wynikiem negatywnym kroku 2); **okno: NOT VERIFIED** |
| 20 | Łagodne zatrzymanie (nowa wersja) | (a) pokaz 1 z panelu, „Zatrzymaj” po 10 s (klik w przeglądarce) → `runs/20261114_172430_demo_v5/`; (b) pokaz 2 (`--item cube_L/mid`) zatrzymany po 75 s, gdy okno już działało → `runs/20261114_172457_demo_arm/` (to samo żądanie `/api/stop`, które wysyła przycisk) | (a) „zatrzymane”, kod −2 (Ctrl+C), 0 procesów; (b) „zatrzymane”, kod −2, **0 ostrzeżeń „leaked shared_memory”** (wcześniej 1), 0 procesów — VERIFIED. W logu zostaje ślad `KeyboardInterrupt` — normalny przy Ctrl+C, opisany w README |
| 21 | Kontrola końcowa | `git status --short`, `git diff --stat` | pliki śledzone bez zmian (`git diff --stat` puste); jedyna nowość: `flymind/panel/` (6 plików + `runs/` pomijany przez `.gitignore`); żadnego nowego `__pycache__`. Nic nie zacommitowano, nic nie wypchnięto. Serwer testowy zatrzymany Ctrl+C po sprawdzeniach |

## Podsumowanie poziomów dowodu

| Co | Poziom |
|---|---|
| Serwer tylko na 127.0.0.1, zamknięta lista, odrzucanie złych wartości | VERIFIED (kroki 7, 8, 18) |
| Testy pokazów i testy modułów uruchomione z panelu | VERIFIED (kroki 11–13: kod 0) |
| Uruchomienie pokazów z panelu (procesy, parametry, kody wyjścia) | VERIFIED (kroki 14, 19) |
| Zatrzymywanie z panelu | VERIFIED (kroki 15, 20) |
| Liczby i filmy w zakładce wyników | VERIFIED (kroki 9, 10) |
| **To, co widać w oknach MuJoCo** (pokaz 1 i 2) | **NOT VERIFIED** — okna otwierały się na tym Macu, ale nikt ich nie oglądał; nie robiłem zrzutów ekranu pulpitu |
| Odtwarzanie filmów w przeglądarce właściciela (Safari/Chrome) | NOT VERIFIED (sprawdzone tylko, że serwer wysyła pliki z obsługą przewijania) |
