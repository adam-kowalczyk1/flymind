# Red Team protokołu FlyMind V5 v4 — runda 2 (przegląd SZKICU r2, przed zamrożeniem)

Data: 2026-10-29. Osobna instancja modelu (ograniczona niezależność: ten sam typ modelu i kontekst repozytorium co autor poprawek i co mój r1).
Poza tym plikiem nic w repozytorium nie zmieniono. Bez bio2, bez pętli zamkniętej, bez commitów. Ziarna użyte wyłącznie 8001–8999 (kalibracje SWS 8001–8003, instancje 8300–8307 i 8400–8404 i 8500–8509). Zakazane pule i rezerwowane 4001–4450 / 5001–5010 / 6001–6010 nie użyte.
Scratch: `/private/tmp/claude-501/-Users-admin-so101-fly-project/31945ef1-39f8-4198-827d-6c45c0d388b2/scratchpad/redteam_v5v4/r2a.py`.

## 0. Werdykt: **READY** (0 BLOCKER, 0 MAJOR) — z 9 uwagami MINOR; zalecam naprawić N7 i N6 PRZED zamrożeniem (po zamrożeniu kod nie może się zmienić)

Wszystkie 3 MAJOR z r1 są rozwiązane. Poprawki nie wprowadziły nowych błędów istotnych dla ważności wniosków. Pozostałe uwagi są tanie.

## 1. Komendy
```
cd /Users/admin/so101_fly_project
.venv/bin/python -I -B flymind/test_v5v4.py     # OK: V5 v4 r2 testy techniczne (21 asercji)  (ostrzeżenie scipy ConstantInputWarning z syntetycznych danych — nieszkodliwe)
.venv/bin/python -I -B $S/r2a.py                # shuffle(equal_weight) 8/8 osiąga cel zamian (135 100 = 10·E), SWS 5/5 complete; nachylenia SWS (10 instancji) 486,7–495,8 → stosunek do 492,1 = 0,989–1,008
grep (ziarna 4241–4450 i pochodne 404/204/104/504 241–450) w flymind, bio2/results, research_notes, reports, results
```
Grep: liczby 42xx–44xx przy "seed/ziarn" oraz pochodne występują tylko w plikach protokołu/Red Team (r1, r2 szkice), nie w wynikach ani kodzie innych etapów — rozszerzona pula 4241–4450 czysta (spot-check; liczba „57 plików” niezweryfikowana).
Rendery z `results/v7_encoder_distance_az_20261029.txt` porównane z moimi z r1 (`e1.py`): wspólne komórki identyczne (ρ 0,28/0,30/0,33/0,35 × az 0–30°), np. 0,28/20° = 7,08, 0,33/30° = 7,09; nowe wiersze 0,22 i 0,25 zgodne ze stwierdzeniem w §0 (0,22: nadprogowe od ~10°; 0,25: od ~13–15°).

## 2. Tabela r1 → r2

| r1 | Status | Uwagi |
|---|---|---|
| M1 błędne uzasadnienie ρ<0,28 | **ROZWIĄZANE** | §0 i §2 przepisane zgodnie z faktami (napęd rośnie z |az|, 5/18 scen niezerowych, średnia −1,43°); wnioski jawnie ograniczone do ρ∈[0,16; 0,28) i az~U(−30°,30°); obszar ρ≥0,28 „nierozstrzygnięty”. Nie dodano S3 ani kryterium aktywności z renderu (moja opcja (c)) — akceptowalne, bo zakres wniosków jest uczciwie zawężony. Uwaga: §2 powołuje się na „polecenie projektu” (niezweryfikowalne dla mnie) oraz na rekomendację RT V5 v3, która sama opierała się na tym samym błędnym założeniu — protokół to mówi („motywacja eksploracyjna”). |
| M2 moc | **ROZWIĄZANE** | n S1=150, S2=300; tabela wrażliwości na SD; liczby w tabeli §5 zgodne z `v5v4_power_r2_20261029.txt` (sprawdziłem każdą komórkę) i z moim rachunkiem normalnym (S2 n=300, SD 1,86, δ=0: 0,99; SD 2,64, δ=−0,2: ≈0,50 vs 0,53). Przy |δ|≈0,2 rozstrzygnięcie nadal jest niepewne (0,13–0,81) — protokół mówi to otwarcie i obiecuje raport „nie wykazano”. Zgodne z zasadą „n z góry”. |
| M3 pominięta replikacja / niejednorodność S2 | **ROZWIĄZANE** | §0 ujawnia replikację dev 1001–1044, podzakresy S2 z przeciwnymi znakami, zastrzeżenie o kancelacji; podpasma S2a/S2b i regresja (opis); przewidywania zapisane. Granica podpasm 0,25 (nie 0,24) — opis, bez decyzji, OK. |
| m1 rozmiar TOST/bootstrap | **ROZWIĄZANE** | Równoważność wymaga obu CI95 (bootstrap + t); test w `test_v5v4.py` (tlo=−0,55 → „nie wykazano”). Test zmiany znaku nadal ~0,03 przy skośnym d (nieopisane w protokole; INFO). |
| m2 SESOI | **ROZWIĄZANE** | Nazwany progiem inżynieryjnym; brak odniesienia do DATA−TOY — nieistotne. |
| m3 etykiety | **CZĘŚCIOWO** | Rozdzielone ≥/< SESOI, ale „<SESOI (praktycznie pomijalny)” decyduje średnia, nie CI (patrz N8). |
| m4 wrażliwość | **CZĘŚCIOWO** | Per warstwa, oba kierunki — OK dla błędów symulatora. Dla H2 tylko wrażliwość na odmowy STR_OWN, nie na wykluczone błędy. |
| m5 odmowa kalibracji | **ROZWIĄZANE inaczej** | SWS bierze dekoder DATA → brak odmowy SWS (patrz N3). STR_OWN: wrażliwość + >10 % → H2 nieinterpretowalna (`analyze` flaga `interpretable`). |
| m6 rodziny / macierz | **ROZWIĄZANE** | Rodziny nazwane, macierz S1×S2 w §6. Brakuje jednego zdania „FWER nie kontrolowany między H1 i H2” (kosmetyka). |
| m7 runner | **W WIĘKSZOŚCI** | Manifest/protokół sprawdzane na starcie; VALID po przebiegu; asercja celu zamian STR; `analyze` waliduje komplet i duplikaty; fsync; wyjątki łapane per próba. Zostają N1, N6, N7. |
| m8 testy | **CZĘŚCIOWO** | Dodane: wznowienie z uciętą linią, duplikat/brak ziarna, kategorie. Nadal: odmowa „ziaren spoza pul” maskowana przez sha (`--approved-protocol-sha256 x`); brak testu ścieżki manifestu/`VALID`/`--shard`. |
| m9 metryki pomocnicze | **ROZWIĄZANE** | McNemar, t_first_within, przeregulowanie, Spearman nachylenie–błąd. |
| m10 model vs mózg | **ROZWIĄZANE** | Szablony §8, etykieta „wynik dotyczy modelu”. |
| m11 cel zamian STR | **ROZWIĄZANE** | `v5v4.py:245`; empirycznie 8/8 instancji osiąga 135 100 zamian, więc STOP nie jest przesadnie wrażliwy. |

## 3. Nowe problemy wprowadzone / ujawnione w r2

**N7 — MINOR (napraw przed zamrożeniem) — sklejenie rekordu po uciętej linii i analiza bez tolerancji.** `v5v4.py:269-272` dopisuje rekord trybem "a" bez sprawdzenia, czy plik kończy się „\n”. Po awarii w środku zapisu (linia uszkodzona bez znaku nowej linii, scenariusz z `test_v5v4.py` z `'{"seed": 4003, "conds": {"DA'`) następny poprawny rekord zostanie doklejony do tej samej linii → obie części nieparsowalne → `load_done` nadal uważa ziarno za niewykonane (będzie liczone dwa razy, wynik poprawny dopiero od trzeciej linii), a `--analyze` (`v5v4.py:296`: `json.loads` bez try) **wyjątkiem przerwie analizę na jakimkolwiek uszkodzonym wierszu**. Test sprawdza tylko `load_done`. Naprawa: przed dopisaniem upewnić się, że plik kończy się „\n” (albo zapisać „\n” przed rekordem, gdy ostatni bajt ≠ „\n”); w `--analyze` pomijać i zliczać nieparsowalne linie (raportować), wymagać kompletu ziaren. Po zamrożeniu nie wolno już zmienić kodu (manifest), więc to trzeba zrobić teraz.

**N6 — MINOR — flaga VALID i manifest nie są wiążące dla analizy.** `analyze` czyta wyłącznie JSONL; `VALID=false` w `run_meta_*` nie zatrzymuje analizy, a manifest nie jest przypięty hashem w protokole (ten, kto edytuje kod, edytuje też manifest; runner sprawdza tylko zgodność wzajemną). Naprawa: protokół zapisuje sha256 manifestu (np. w §7 i w logu zamrożenia), `--analyze` przyjmuje pliki meta i odmawia, jeśli któryś ma `VALID=false` lub brakuje meta dla ziaren; w analizie raport zawiera sha manifestu.

**N1 — MINOR — limity błędów liczone per shard i resetowane przy wznowieniu.** `v5v4.py:233, 274`: `errs` zerowane przy każdym uruchomieniu; limit „>5 błędów w jednym warunku” dotyczy jednego shardu (łącznie do 10/warunek na 450 ziaren) a „>2 %” — długości `seeds` danego wywołania. Protokół (§7) mówi „w shardzie”, więc jest spójny, ale słabszy niż w r1 (dla całości) i niewidoczny po wznowieniu. Naprawa: liczyć błędy z JSONL (shard + wznowienie) i w `analyze` egzekwować globalny limit (5 na warunek, 2 % wszystkich) jako warunek analizy potwierdzającej, albo dopisać do protokołu, że limit jest per shard i wznowienie go nie zeruje.

**N2 — MINOR/INFO — ziarna RNG analizy 4401/4402 leżą wewnątrz puli potwierdzającej 4001–4450** (`v5v4.py:36`). Brak wpływu praktycznego (inny cel; mierzalnego sprzężenia nie ma — r1 I4), ale łamie konwencję „RNG analiz poza pulami”. Naprawa: np. 7401/7402 (poza pulami, ten sam rząd co 7101 w testach) — zmiana w protokole i kodzie jednocześnie.

**N3 — INFO/MINOR — SWS z dekoderem DATA.** Uczciwe: to ten sam dekoder co w V5 v3 (porównywalność), usuwa szum kalibracji i odmowy, izoluje wzorzec topologii. Zmierzone przeze mnie (10 instancji SWS, ziarna kalibracji 8001–8003): nachylenia 486,7–495,8, czyli 0,989–1,008 względem 492,1 (DATA na tych ziarnach: 494,3) — niedopasowanie wzmocnienia ≤ ~1 %, pomijalne wobec SESOI. Konsekwencja uboczna: r2 w ogóle nie rejestruje nachylenia instancji SWS (brak diagnostyki odstających instancji; `analyze` liczy nachylenia tylko dla DATA/STR_OWN/TOY). Zalecenie (opcjonalne): wyliczać `calibrate(sws)` jako DIAGNOSTYKĘ (nieużywaną przez dekoder), zapisywać i raportować; flaga, jeśli odchyla się >10 % od DATA.

**N4 — MINOR — nierówne n i wagi.** Holm na {S1 (150), S2 (300)} jest poprawny. Wynik łączny („opis”) i H2 (łącznie) ważą S2 2:1, a nie 1:1 jak w r1 — H2 jest więc dominowane przez S2, gdzie jest więcej scen ciszy. Naprawa: napisać to w §1 (H2 = średnia po rozkładzie scen 150:300), wynik per warstwa już jest opisowo w kodzie (`per_stratum_descriptive`).

**N5 — MINOR — regresja d ~ ρ + |az0| (OLS).** `v5v4.py:157-163`: SE klasyczne (homoskedastyczne), model liniowy, choć odpowiedź jest progowa (cisza ↔ aktywność zależy od ρ i |az| łącznie), zero-inflated i zmienia znak wewnątrz S2. Jako opis jest OK, ale SE mogą wprowadzać w błąd. Zalecenie: SE HC3 (lub bootstrap par), dodać człon ρ·|az| albo wersję w warstwach; napisać „opis, bez wnioskowania”.

**N8 — MINOR — etykieta „efekt < SESOI (praktycznie pomijalny)” zależy od średniej** (`v5v4.py:113,115`). Przykład: średnia −0,45, CI95 [−0,9; 0,0] → „praktycznie pomijalny”, mimo że CI dopuszcza efekt >0,5. Zalecenie: „pomijalny” tylko gdy CI95 (oba) ⊂ ±SESOI; w przeciwnym razie „efekt < SESOI (punktowo), niedookreślony”. Test `test_v5v4.py` (−0,45; −0,05) nadal przejdzie.

**N9 — MINOR — brak testów ścieżek `run`/shardów.** Nie sprawdzono: niezgodność manifestu, `VALID`, odmowa gdy `--shard` pominięty, nakładanie shardów (`--shard A --seeds 4226-4450` jest dozwolone; duplikat wykryty dopiero w analizie, co jest bezpieczne, ale marnuje uruchomienie), STOP przy uszkodzeniu SWS.

## 4. Sprawdzone wprost i bez uwag
- Stratyfikacja po zakresie ziaren (4001–4150 → S1, 4151–4450 → S2; dev 6001–6005 → S1) zamiast parzystości: poprawnie zrealizowana w `trial_spec_v4` (test: 150/300, ρ w granicach). Zakresy ziaren nie wprowadzają zależności dynamiki od warstwy (ALIF zależy tylko od wartości ziarna; r1 I4). Shard B (4226–4450) zawiera wyłącznie S2, A: cały S1 + 75 S2 — wynik niezależny od kolejności, bo ziarna są niezależne; wyniki shardów muszą być identyczne z uruchomieniem sekwencyjnym (deterministyczne).
- `analyze`: Holm, sparowanie, wykluczenia (dowolny warunek z błędem → wykluczenie ze wszystkich), regresja liczona na tych samych wierszach co `y` (kolejność `ok` zachowana), McNemar, wrażliwość per warstwa w obu kierunkach (`worst_for_DATA`/`best_for_DATA`).
- Zgodność protokół ↔ kod: pule/FORBIDDEN, offsety +400 000/+200 000, SESOI, CI (bootstrap 10 000 + t), permutacje 100 000, kategorie, STOP (Stage 1, manifest/protokół na starcie, cel zamian STR, własności SWS, błędy), `interpretable` (>10 % odmów STR_OWN), brak odmowy SWS.
- Moc: tabela §5 odpowiada plikowi; sformułowanie „bez zwiększania zależnego od wyniku” jest właściwe.

## 5. Odpowiedzi na pytania koordynatora
- **Stratum po zakresie ziaren vs parzystość:** poprawne i prostsze; brak wpływu na dynamikę. Zwracam uwagę tylko na asymetrię shardów (B tylko S2) — bez konsekwencji.
- **Limit błędów per shard:** słabszy niż w r1 i zerowany przy wznowieniu (N1).
- **Nierówne n i Holm:** poprawne; zmienia się ważenie wyniku łącznego i H2 (N4).
- **DATA-dekoder dla SWS:** uczciwy i zgodny z V5 v3 (N3), nachylenia SWS ±1 % od DATA.
- **Specyfikacja regresji:** akceptowalna jako opis; SE klasyczne i liniowość są słabe (N5).

## 6. Podsumowanie (10 linii)
1. Jestem osobną instancją modelu (ograniczona niezależność od autora i od mojego r1).
2. Werdykt r2: READY — 0 BLOCKER, 0 MAJOR, 9 MINOR (N1–N9); `test_v5v4.py` 21/21 zielone.
3. M1, M2, M3 z r1 rozwiązane: uzasadnienie ρ<0,28 zgodne z renderami (zweryfikowane), n=150/300 z uczciwą tabelą mocy, ujawniona replikacja dev i kancelacja w S2.
4. Z 11 MINOR z r1: 8 rozwiązanych, 3 częściowo (etykiety, wrażliwość H2, testy).
5. Wymaga poprawy przed zamrożeniem: N7 (doklejenie rekordu do uciętej linii i crash `--analyze` na uszkodzonym wierszu) oraz N6 (VALID/manifest niewiążące dla analizy).
6. Zalecane: N1 (globalny limit błędów liczony z JSONL), N2 (ziarna RNG 4401/4402 poza pulą), N8 (etykieta „pomijalny” z CI), N5 (HC3).
7. Dekoder DATA dla SWS jest uczciwy: nachylenia 10 instancji SWS = 0,989–1,008 × 492,1; dodaj diagnostykę nachylenia SWS (N3).
8. Przy |δ|≈0,2° wynik będzie często „nie wykazano” (P równoważności 0,44–0,81 w S2) — protokół to jawnie mówi i raportuje uczciwie.
9. Ziarna: tylko 8001–8999; pula 4241–4450 i pochodne czyste (spot-check); brak pętli zamkniętej, bio2 i commitów.
10. Raport: `/Users/admin/so101_fly_project/flymind/results/redteam/v5v4_protocol_redteam_r2.md`.
