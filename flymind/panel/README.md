# FlyMind — panel (lokalny)

Strona w przeglądarce, z której jednym kliknięciem uruchamiasz istniejące pokazy i testy FlyMind i oglądasz wyniki.
Wszystko dzieje się na tym komputerze, w symulacji. Panel niczego w projekcie nie zmienia.

## Uruchomienie — jedna komenda

W Terminalu:

```bash
cd /Users/admin/so101_fly_project && .venv/bin/python -I -B flymind/panel/server.py
```

Potem otwórz w przeglądarce (Safari albo Chrome): **http://127.0.0.1:8770**

Zatrzymanie: w tym samym oknie Terminala naciśnij `Ctrl+C` (zatrzymuje też uruchomione pokazy).

## Co jest w panelu

**Zakładka „Uruchom”**

| Pozycja | Co robi | Okno |
|---|---|---|
| Pokaz 1 — ramię obraca się za piłeczką | `demo/demo.py`; wybór: sieć albo klasyczny regulator, tryb prezentacji, kąt i odległość piłeczki, przestawianie piłeczki, automatyczne zamknięcie | osobne okno MuJoCo |
| Pokaz 2 — całe ramię z sieci nogi muszki | `demo/demo_arm.py`; wybór: **kształt** (9: sześcian mały/średni/duży, walec, kula, płytka, belka, kształt L, klin) i **materiał** (5: guma przyczepna, śliskie tworzywo, stal, pianka/balsa, drewno), położenie, wariant znaku, tempo, automatyczne zamknięcie; ziarno stałe 20951 | osobne okno MuJoCo (po ok. minucie budowania sieci) |
| Test pokazu 1 | `demo/test_demo.py` | bez okna |
| Test pokazu 2 | `demo/test_demo_arm.py` | bez okna |
| Testy modułów | 20 zestawów `test_*.py` po kolei (`panel/run_module_tests.py`) | bez okna |

Pod spodem lista uruchomień: stan (działa / zakończone / błąd / zatrzymane), czas, log na żywo, przycisk „Zatrzymaj”,
dokładna komenda i katalog z zapisem.

**Zakładka „Filmy i liczby”** — wnioski prostym językiem, tabela kluczowych liczb (czytana z plików wyników przy każdym
otwarciu, z nazwą pliku źródłowego i poziomem dowodu; kontrole z tasowaniami i wynik negatywny całego ramienia są na
równi z resztą), 5 gotowych filmów i 3 wykresy.

**Zakładka „Jak to działa”** — krótka instrukcja.

## Czego panel celowo NIE robi

- Nie przyjmuje dowolnych komend ani dowolnych ziaren — tylko pozycje i wartości z zamkniętych list w `server.py`.
- Nie uruchamia eksperymentów 135 prób, nie używa ziaren testowych.
- Nie zawiera żadnego kodu do prawdziwego robota.
- Nie jest dostępny z sieci: słucha tylko na 127.0.0.1 (adres wpisany na stałe), odrzuca żądania z obcym nagłówkiem Host
  i żądania uruchomienia spoza własnej strony.
- Nie pisze do `results/` ani do żadnego istniejącego pliku. Każdy przebieg ma własny katalog
  `flymind/panel/runs/<data_godzina>_<pozycja>/` (`run.json` — parametry i komenda, `log.txt`, `result.json`).
- Nie wymaga żadnych dodatkowych bibliotek (tylko biblioteka standardowa Pythona).

## Pliki

`server.py` (serwer i zamknięta lista), `index.html` (strona), `run_module_tests.py` (kolejne uruchomienie testów modułów),
`.gitignore` (pomija `runs/`), `audit_log_panel_20261114.md` (co zrobiono i co sprawdzono), `runs/` (zapisy przebiegów).

## Gdy coś nie działa

- Po „Zatrzymaj” w logu pojawia się `KeyboardInterrupt` i kilka linii śladu → to normalne: panel zatrzymuje pokaz tak
  jak Ctrl+C. Stan „zatrzymane” (pomarańczowy) to nie błąd.
- „Panel nie odpowiada” na stronie → serwer w Terminalu został zamknięty; uruchom komendę jeszcze raz.
- `Address already in use` → panel już działa w innym oknie Terminala; po prostu otwórz adres w przeglądarce.
- Pokaz „działa”, ale okna nie widać → pokaz 2 buduje sieć ok. minuty; okno może też być schowane pod innymi (ikona
  Pythona w Docku).
- Przycisk pokazu jest szary → inne okno pokazu jeszcze działa (naraz może być otwarte jedno); zatrzymaj je.
- Chcesz inny kształt albo materiał w pokazie ramienia → zatrzymaj pokaz, zmień wybór na karcie i otwórz go ponownie
  (zmiana w trakcie działania okna nie jest możliwa bez zmiany `demo_arm.py`). Dostępny jest zestaw podstawowy 45
  przedmiotów; „trudnych” przedmiotów (lód, wolfram, jajko, młotek…) pokaz nie obsługuje.
