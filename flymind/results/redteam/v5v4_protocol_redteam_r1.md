# Red Team protokołu FlyMind V5 v4 (SZKIC r1, przed zamrożeniem) — runda 1

Data: 2026-10-29. Rola: niezależna (osobna instancja modelu — niezależność ograniczona: ten sam typ modelu, ten sam kontekst repozytorium), adwersaryjna ocena PROJEKTU przed zamrożeniem i uruchomieniem.
Nic w repozytorium poza tym plikiem nie zostało zmienione. Nie importowano bio2. Żadnych prób w pętli zamkniętej (`loop.run_trial` nie wywołane).
Skrypty i surowe wyjścia: `/private/tmp/claude-501/-Users-admin-so101-fly-project/31945ef1-39f8-4198-827d-6c45c0d388b2/scratchpad/redteam_v5v4/` (a1.py, c1.py, e1.py, p1.py–p4.py).
Użyte ziarna: wyłącznie 8001–8999 (szum ALIF w kalibracjach, instancje kontroli 8101–8108 i 8201–8212, RNG symulacji 8001–8004). Żadnych ziaren zakazanych ani z rezerwowanych pul 4001–4240 / 5001–5010 / 6001–6010 (ani pochodnych). Odczyt istniejących wyników V5 v3 (ziarna 3051–3100) był tylko do analizy statystycznej (opublikowane dane, nie uruchamiane).
Wszystkie komendy: `/Users/admin/so101_fly_project/.venv/bin/python -I -B <skrypt>` ze `sys.path.insert(0,'/Users/admin/so101_fly_project/flymind')`.

## 0. Werdykt: **NOT READY**

Brak BLOCKER-ów (kod i statystyka są poprawne w rdzeniu, testy zielone), ale są **3 MAJOR**, które należy naprawić przed zamrożeniem:
- **M1** — uzasadnienie granicy ρ < 0,28 m zawiera błąd faktyczny (kierunek zależności od |az| odwrócony); granica nie jest „strukturalna", a wycina sceny, w których V5 v3 pokazał największe efekty na korzyść DATA (selekcja w stronę „równoważne").
- **M2** — moc dla równoważności w S2 (i w S1 przy konserwatywnym SD) jest krucha: przy SD z górnego przedziału ufności P(równoważność | δ=0) spada z 0,70 do 0,14 (S2); przy δ = −0,2° (wartość z V5 v3) do 0,13–0,44. Protokół obiecuje decyzję, której n = 120/warstwę nie zapewnia.
- **M3** — §0 pomija wynik Red Teamu V5 v3 (replikacja na dev 1001–1044: struktura warstw NIE odtwarza się), a S2 obejmuje dwa reżimy o przeciwnych znakach w V5 v3 (0,22–0,24: +0,68; 0,24–0,28: −1,23) → równoważność średniej w S2 może maskować kancelację znaków; granica 0,22 nie jest neutralna.

Reszta (MINOR/INFO) to poprawki tanie. Po naprawie M1–M3 oczekuję READY.

## 1. Komendy uruchomione

```
cd /Users/admin/so101_fly_project
.venv/bin/python -I -B flymind/test_v5v4.py            # OK: V5 v4 testy techniczne (18 asercji)
.venv/bin/python -I -B flymind/test_side_shuffle.py    # OK: side_shuffle v2 (28 asercji)
.venv/bin/python -I -B flymind/test_v5v3_analysis.py   # OK: analiza V5 v3 (18 asercji)
loop.stage1_hashes()  ->  n 28, mismatched []          # Stage 1 zgodny
$S/a1.py  # surowe d (DATA−SWS) V5 v3 posortowane po ρ            (dane opublikowane, 3051–3100)
$S/p1.py  # SD/zera/średnie w warstwach V5 v3, bootstrap SD, nieaktywne sceny
$S/p2.py  # symulacja mocy: siatka SD × δ, n = 120 (reguła t-CI jak v5v4_power.py)
$S/p3.py  # rozmiar bootstrapowego TOST na granicy ±0,5 (skośny kształt d), 3000 powt. × 1000 prób
$S/p4.py  # błąd I rodzaju testu zmiany znaku przy skośnym d (v5v4.perm_test, 1500 powt.)
$S/c1.py  # v5v4.calibrate(..., seeds=(8001..8009)) dla DATA, TOY, 8 instancji SWS, 12 instancji STR
$S/e1.py  # statyczne rendery (bez pętli): max(g)·12 mV dla siatki ρ × az 0–30°
```
($S = scratchpad/redteam_v5v4.) Hash szkicu: `shasum -a 256 flymind/validation/v5v4_protocol_DRAFT.md` = 8212812d… ; `v5v4.py` = 65b5b693….

## 2. Lista problemów

### M1 — MAJOR — uzasadnienie ρ < 0,28 m jest błędne faktycznie i selekcyjne
Plik: `validation/v5v4_protocol_DRAFT.md:13-14` (§0), `:29-34` (§2 pkt 1), `v5v4.py:31` (`STRATA`).
Protokół: „dla ρ ≥ 0,28 m prąd LC10a (12 mV·g) < ~7 mV progu przy |az| ≥ 15° → sieć milczy, d = 0 strukturalnie".
Fakty (moje rendery, deterministyczne, `e1.py`; max(g)·12 mV, wiersze ρ, kolumny az = 0/5/10/15/20/25/30°):
```
0.28   4.14 4.96 5.74 6.45 7.08 7.72 8.37
0.30   3.77 4.57 5.30 5.97 6.59 7.20 7.83
0.33   3.26 4.06 4.66 5.29 5.90 6.54 7.09
0.35   2.96 3.69 4.28 4.92 5.51 6.04 6.73
```
- Napęd **rośnie** z |az|, nie maleje. Przy ρ = 0,28 prąd przekracza ~7 mV od |az| ≈ 20°, przy ρ = 0,30 od ≈ 25°, przy 0,33 od 30°. Zdanie „przy |az| ≥ 15°" jest odwrócone (plik `v7_encoder_distance_20261029.txt` mierzy tylko az = 0 i 15°, więc wniosek jest ekstrapolacją poza zmierzony zakres).
- Dane V5 v3 (opublikowane, `a1.py`/`p1.py`): wśród 18 scen z ρ ≥ 0,28 **5 jest niezerowych**, wszystkie z |az| ≥ 23,9° (ρ 0,284/0,303/0,305/0,309/0,329; d = +0,28, −3,44, +0,46, −1,98, −2,48; średnia z niezerowych −1,43°). Czyli granica 0,28 NIE daje „d ≡ 0 strukturalnie" i wycina właśnie część przestrzeni z największymi różnicami na korzyść DATA. W ρ < 0,28 średnia V5 v3 to −0,074° (n = 32) — czyli obszar, który wygląda najbardziej „równoważnie". Wybór domeny po obejrzeniu wyniku w stronę H0 zwiększa szansę na „równoważne".
- Strefa ciszy to obszar w (ρ, az), nie granica po ρ. Dodatkowo próg jest rozmyty szumem ALIF (2 mV): w V5 v3 ρ = 0,205, az = 1,2° (6,4 mV < 7) ma d ≠ 0.
- §2 sam przyznaje, że motywacja jest „eksploracyjna" z V5 v3 (to uczciwe), ale pkt (1) przedstawia ją jako mechanizm niezależny od wyników, co jest nieprawdą w tej formie.
Naprawa (przed zamrożeniem): (a) przepisać §0/§2 zgodnie z faktami (napęd rośnie z |az|; cisza dla małych |az| przy ρ ≥ 0,28; w V5 v3 5/18 niezerowych); (b) jawnie ograniczyć zakres wniosków do „ρ < 0,28 m, az ~ U(−30°, 30°)" i napisać, że domena wycina aktywne sceny o dużym |az| z V5 v3; (c) lepiej: dodać zarejestrowaną, opisową (bez decyzji) warstwę S3 = ρ ∈ [0,28; 0,35], |az| ≥ 20° (nowa pula ziaren), albo zdefiniować „aktywność" kryterium z deterministycznego renderu (max(g)·12 mV ≥ próg), niezależnym od zachowania, zamiast cięcia po ρ.

### M2 — MAJOR — n = 120/warstwę nie zapewnia obiecanych decyzji (S2 równoważność, S1 przy konserwatywnym SD)
Plik: `v5v4_power.py:18-45`, wynik `results/v5v4_power_20261029.txt`; protokół `:63-66`.
- SD z V5 v3: S1 = 0,642 (n = 15, 0 zer), S2 = 1,863 (n = 17, 4 zera). Bootstrap 95 % SD: S1 [0,40; 0,82], S2 [0,92; 2,41]; górna granica jednostronna χ² 95 %: S1 0,94, S2 2,64 (`p1.py`). Protokół sam zauważa, że S1 jest zaniżone, ale tabela mocy tego nie pokazuje.
- Moja symulacja (`p2.py`; ten sam kształt d i reguła t-CI co `v5v4_power.py`, SD skalowane, n = 120, 4000 powt.). P(równoważność ±0,5° | δ) / P(przewaga α 0,025 | δ):
```
S1 SD 0,64: δ=0 1,00 | δ=-0,2 1,00 / 0,90 | δ=-0,5 0,03 / 1,00
S1 SD 1,30: δ=0 0,98 | δ=-0,2 0,75 / 0,30 | δ=-0,5 0,02 / 0,98
S1 SD 1,60: δ=0 0,89 | δ=-0,2 0,55 / 0,20 | δ=-0,5 0,02 / 0,90
S1 SD 2,00: δ=0 0,60 | δ=-0,2 0,37 / 0,13 | δ=-0,5 0,02 / 0,72
S2 SD 1,86: δ=0 0,70 | δ=-0,2 0,44 / 0,12 | δ=-0,5 0,04 / 0,80   (= wynik protokołu)
S2 SD 2,64: δ=0 0,14 | δ=-0,2 0,13 / 0,06 | δ=-0,5 0,03 / 0,44
S2 SD 3,00: δ=0 0,01 | δ=-0,5 0,01 / 0,35
```
- Rachunek analityczny (normalny, α jednostronne 0,025): n potrzebne dla P(równoważność) ≥ 0,8: S2 SD 1,86 → n ≈ 146 (δ=0) / 302 (|δ|=0,2); SD 2,64 → 294 / 608; S1 SD 1,3 → 72 / 148.
- V5 v3 pooled d = −0,19° (nie 0): przy takim prawdziwym δ i SD S2 = 1,86 równoważność w S2 ma szansę ~0,44, nie 0,70. Obiecane w §5 „30 % szans na brak rozstrzygnięcia przy δ = 0" jest więc optymistycznym punktem krańcowym.
- Symulacja używa testu t jako przybliżenia, nie faktycznej reguły (perm. + bootstrap) — patrz m1; zer jest mniej niż w docelowym rozkładzie (sceny z małym |az| w S2 są nieme: 4/17).
Naprawa: (1) dodać do §5 tabelę wrażliwości na SD (powyżej) i na δ = ±0,2; (2) zwiększyć n w S2 (≥ 300 ziaren w S2, nowa zarejestrowana pula — S1 może zostać 120) albo (3) zarejestrować regułę „bramkującą": równoważność w warstwie jest możliwym wnioskiem tylko jeśli zaobserwowane SD ≤ ~2,0° (inaczej z góry „nie rozstrzygalne"), albo (4) zredukować wariancję: kowariaty ρ i |az| (ANCOVA) jako analiza główna sparowana, albo odrzucić z analizy równoważności sceny niemym z deterministycznego renderu (zdefiniowane z góry, M1c).

### M3 — MAJOR — pominięty niekorzystny wynik eksploracyjny i niejednorodność S2
Plik: `validation/v5v4_protocol_DRAFT.md:9-15` (§0), `:32-34` (§2).
- Red Team V5 v3 (`results/redteam/v5v3_result_redteam.md` §5, §7) zaraportował replikację na dev 1001–1044: średnia d zgodna (−0,230), ale **struktura warstw nie replikuje się** (S1 −0,013, 9 ujemnych / 11 dodatnich; Spearman(d, ρ) = −0,18, p = 0,24), oraz DATA − SHUF_STR(własne nachylenie) = −0,98 (CI95 −1,52…−0,47), czyli ok. połowa efektu H2. §0 szkicu cytuje tylko dev 1501–1520 (−1,45/+1,17, n = 20) i opis warstw V5 v3 — bez informacji, że replikacja warstw zawiodła. To dotyczy wprost uzasadnienia stratyfikacji (jest to „wiedza przed napisaniem" w sensie §0).
- Wewnątrz S2 dane V5 v3 mają zmianę znaku: ρ ∈ [0,22; 0,24): n = 6, średnia +0,68; ρ ∈ [0,24; 0,28): n = 11, średnia −1,23 (`p1.py`). TOST na średniej S2 może więc zakończyć się „równoważne" przy kancelacji efektów przeciwnych znaków (dokładnie ten problem, który warstwy miały rozwiązać). Granica 0,22 „na pół" jest arytmetycznie neutralna, ale nie neutralna informacyjnie: tnie zakres tak, że S2 dostaje oba reżimy, a S1 jednorodny dodatni (+0,47, SD 0,64).
- S1 w V5 v3: średnia +0,47 ± 0,17 (SE) leży praktycznie na SESOI = 0,5. Wynik S1 jest więc na krawędzi „równoważne / kontrola lepsza" — protokół nie zapowiada tego jako przewidywania.
Naprawa: (a) dopisać do §0 jawnie wynik replikacji dev 1001–1044 (struktura warstw nie odtwarza się; H2 ≈ połowa po wyrównaniu skali); (b) zarejestrować jako opis (bez decyzji) model d ~ ρ + |az| (np. regresja z robust SE lub LOESS) w każdej warstwie i łącznie, oraz w §7 zastrzeżenie, że „równoważne w S2" nie wyklucza efektów przeciwnych znaków podwarstw; (c) zapisać przewidywania (nie kryteria): S1 średnia d ≈ +0,3…+0,5 (kontrola lepsza lub równoważne), S2 niejednoznaczne; (d) rozważyć granicę 0,24 zamiast 0,22 TYLKO jeśli zostanie uczciwie opisana jako dobrana po V5 v3 (inaczej zostawić 0,22 i opisać konsekwencje).

### m1 — MINOR — bootstrapowy TOST i test zmiany znaku są lekko antykonserwatywne przy skośnym d
Plik: `v5v4.py:59-69`, `:89-99`.
- Rozmiar reguły „CI95 percentylowe ⊂ (−0,5; 0,5)" na granicy, n = 120, skośny kształt d z V5 v3 (`p3.py`, 3000 powt.): S2-kształt SD 1,86, granica górna: 0,0207 (nominal 0,025); SD 2,6: 0,0240; S1-kształt ×2 (SD 1,28): 0,0310; granica dolna S2: **0,0397** (≈ 1,6 × nominal).
- Test zmiany znaku przy średniej 0 i skośnym d (`p4.py`, α 0,025): S2 0,0300; ρ<0,28 0,0307 (SE ≈ 0,004). Test sprawdza symetrię, nie średnią.
- Poprawność korespondencji TOST ⇔ CI: **prawidłowa** (dwa testy jednostronne po α = 0,025 ⇔ (1−2α) = 95 % CI ⊂ (−Δ, Δ); Bonferroni na 2 warstwy poprawnie daje 0,025 zamiast 0,05).
Naprawa: zarejestrować, że „równoważne" wymaga jednocześnie CI95 percentylowe ORAZ CI95 BCa (lub t) ⊂ (−0,5; 0,5); raportować oba. Dla przewagi: p_perm z Holmem i CI95 BCa bez zera.

### m2 — MINOR — SESOI ±0,5° jest uzasadniony inżyniersko, nie naukowo
Plik: `:36-40`.
- Rozdzielczość: fov poziomy 2·atan(tan 35°·128/96) = 86,0°, /128 = 0,67°/kol. — liczba poprawna. Ale SESOI dotyczy ŚREDNIEJ różnicy błędu końcowego (uśrednianie daje rozdzielczość poniżej piksela), więc „poniżej 1 kolumny" nie implikuje nieistotności dla średniej.
- Odniesienie P ≈ 0,3° jest poprawne (V5 v3: 0,314), ale to dokładność innej architektury, nie próg istotności różnicy DATA vs SWS.
- Skala: średnie błędy SNN w ρ<0,28 to ok. 1,8° (S1) do ≥3° (S2) — 0,5° to 15–30 % błędu. DATA − TOY = 1,25° w V5 v3. Margines „równoważne" jest więc nadal porównywalny z dużą częścią różnic między architekturami.
- Dodatkowo S1 w V5 v3 miał +0,47 (patrz M3) — SESOI leży na wyniku poprzedniego eksperymentu; sam protokół twierdzi, że nie jest kalibrowany do V5 v3, co jest wiarygodne (zaostrzono z 1° na 0,5°), ale warto napisać to jawnie z liczbą.
Naprawa: nazwać SESOI „progiem inżynieryjnym (nieistotne dla sterowania w tej pętli)", dopisać zdanie o relacji do DATA − TOY, i nie nazywać „równoważne" stwierdzeniem o topologii.

### m3 — MINOR — etykieta „DATA lepsza" przy efekcie poniżej SESOI
Plik: `v5v4.py:89-99`.
Etykieta „DATA lepsza" (bez dopisku) pojawia się też, gdy CI95 przekracza −0,5 (np. średnia −0,3, CI [−0,6; −0,05]) — mimo że istotność praktyczna nie jest wykazana. Dopisek „w granicach SESOI" jest tylko dla CI ⊂ ±SESOI. Naprawa: rozdzielić „DATA lepsza (istotna, CI poniżej −SESOI)" od „DATA lepsza (nieistotna praktycznie / niedowiedziona)" albo wymagać hi < −SESOI dla czystej etykiety. Dostosować `test_v5v4.py:20-25`.

### m4 — MINOR — analizy wrażliwości: tylko łączne, jednokierunkowe
Plik: `v5v4.py:136-143`; protokół `:76-79`.
`sensitivity_H1_pooled_excluded_as_worst` wstawia `+max|d|` zawsze (najgorzej dla DATA tylko jeśli to DATA padło; gdy padł SWS — odwrotnie), liczy tylko łącznie, a decyzje są per warstwa; dla równoważności najgorsze jest ±max|d|. Nie ma wrażliwości dla H2. Naprawa: wrażliwość per warstwa, w obu kierunkach (+max|d| i −max|d|), także dla H2a/H2b; kategoria raportowana tylko jeśli stabilna.

### m5 — MINOR — odmowa kalibracji dla SWS/STR_OWN: sztuczna przewaga i brak STOP
Plik: `v5v4.py:190-193`, `:167-168`; protokół `:76-79`.
- Odmowa SWS daje d = błąd(DATA) − |az0| (silnie ujemne → „DATA lepsza" z artefaktu); STOP jest tylko dla DATA/TOY. Naprawa: STOP/oznaczenie, jeśli odmówiono SWS w > 1 próbie (lub ≥ 3 ziarnach łącznie), wrażliwość per warstwa (jest tylko łączna).
- `success=False` przy odmowie, choć brak ruchu przy |az0| < 5° jest „sukcesem" w innych warunkach (niespójne tylko dla metryki pomocniczej).
- Próg `slope ≤ 2 Hz/rad` jest bardzo łagodny: nachylenie 5 Hz/rad zostaje zaakceptowane i daje wzmocnienie ×100 (bang-bang przy w_max). Moje otwarte-pętle: 20/20 instancji OK (SWS 487–498, STR 82–205 Hz/rad, brak odmów) — ryzyko niskie, ale reguła powinna mieć dolny próg względny (np. ≥ 10 % nachylenia DATA albo jawna flaga).

### m6 — MINOR — rodziny testów i łączny wniosek H1
Plik: `:17-25`.
Rodziny: H1-przewaga (Holm/2), H1-równoważność (Bonf./2), H2 (Holm/2) — trzy osobne α = 0,05 bez korekty między rodzinami. Pytania są różne, więc to obronne, ale musi być napisane („rodziny rozłączne, FWER nie jest kontrolowany między H1 i H2; H1 i H2 to różne pytania"). Mieszanie przewagi i równoważności w tej samej warstwie jest spójne (wyniki wykluczają się, poza „DATA lepsza w granicach SESOI" = istotna i trywialna), ale brak macierzy wyniku łącznego dla dwóch warstw (np. S1 równoważne + S2 DATA lepsza → „heterogeniczne"). Naprawa: dopisać tabelę 4×4 → zdanie dozwolone.

### m7 — MINOR — odporność runnera
Plik: `v5v4.py:160-161`, `:194-203`, `:207`, `:209-215`, `:218-238`.
- Ucięta ostatnia linia JSONL (kill podczas zapisu) → `json.loads` rzuca wyjątek, wznowienie niemożliwe; protokół §6 twierdzi „rekord częściowy nie powstaje" — zapis nie jest atomowy. Naprawa: `try/except` na ostatniej linii, zapis `write+flush+fsync`, albo plik tymczasowy + rename.
- Łapany jest tylko `SimError`; `DecoderError`/`ValueError` w `run_trial` zabija proces, a ponowne uruchomienie powtarza to samo ziarno w nieskończoność (deterministyczne). Naprawa: jawna obsługa i zapis `error`.
- `errs` zerowany przy każdym wznowieniu; limit 2 % liczony od `len(seeds)` wywołania (nie od historii). Naprawa: liczyć błędy z JSONL.
- STOP „Stage 1 po" i „kod ≠ manifest" (protokół `:78-79`) NIE są egzekwowane przez runner: Stage 1 po przebiegu tylko drukowany (`:215`), hashe kodu zapisywane do meta dopiero na końcu (`:210-212`), brak `validation/v5v4_manifest.json` i sprawdzenia przed startem. Naprawa: porównanie z manifestem przed pierwszą próbą; post-check kończy `sys.exit` z kodem ≠ 0 i flagą w meta.
- `analyze()` (`:102-144`) nie sprawdza zbioru ziaren: ani równości z 4001–4240, ani duplikatów, ani mieszania rekordów dymnych (6001–…), jeśli `--out` ma ten sam `raw_v5v4.jsonl`. Naprawa: asercja `set(seed) == set(range(4001,4241))` dla analizy potwierdzającej, zakaz dwóch katalogów wyjściowych (jedna kanoniczna ścieżka w protokole), zapis hasha JSONL.
- Brak zdefiniowanej procedury, jeśli test dymny 6001–6002 (uruchamiany JUŻ po zamrożeniu — runner wymaga sha) ujawni błąd: nowa wersja protokołu? Dopisać.

### m8 — MINOR — testy
Plik: `test_v5v4.py:46-48`.
Odmowa „ziaren spoza pul" nie jest testowana osobno: `--approved-protocol-sha256 x` oraz brak `validation/v5v4_protocol.md` odmawiają PRZED sprawdzeniem ziaren. Brak testów: odmowa kalibracji w `run`, wznowienie, ucięty JSONL, analiza z wykluczeniami per warstwa. Docstring `h1_category` (`v5v4.py:90`) wskazuje „Protokół §5", właściwie §1.

### m9 — MINOR — metryki pomocnicze nie analizowane
Plik: `v5v4.py:102-144`, protokół `:70-71`.
Czas do |e| < 5°, przeregulowanie i takty z flagą bezpieczeństwa są zapisywane, lecz `analyze` ich nie liczy (tylko sukces i nachylenia). Naprawa: dodać lub usunąć z §6.

### m10 — MINOR — ryzyko pomylenia właściwości modelu z mózgiem muchy
Protokół ma zastrzeżenie (`:26-27`) i dobre rozdzielenie etykiet. Brakuje: (a) w §7 szablonu zdań dozwolonych dla każdej kategorii; (b) zastrzeżenia, że efekt wewnątrz bloku LC10a×LC10a działa przez próg odpowiedzi DNa02 w regionie napędu ≈ 7 mV (własność ALIF + J0 + enkodera), pojedynczy konektom (MaleCNS v1.0), jedno J0 = 0,2, znak Glu = hamowanie (MODEL); (c) „DATA lepsza" ≠ „topologia z mózgu muchy jest lepsza dla orientacji", a „równoważne" ≠ „tożsamość połączeń LC10a nieistotna" (tożsamość LC10a jest niewidoczna dla pętli — jednakowy prąd na stronę). Naprawa: dopisać szablon raportu.

### m11 — MINOR — SHUF_STR bez sprawdzenia osiągnięcia celu zamian
Plik: `v5v4.py:180-181`, `visual_path.py:88-98`.
`SWS` ma asercję `complete` (osiągnięty cel zamian), `shuffle(equal_weight=True)` nie raportuje ani nie sprawdza, czy `done` osiągnęło cel (pętla może się skończyć wcześniej). `check_shuffle` sprawdza `changed_edges > 0`. Naprawa: asercja `rep["shuffle"]["swaps"] == 10*E` lub jawny próg (np. ≥ 95 %).

### INFO
- **I1** Offset kalibracji = 0,0 w 22/22 instancjach (DATA, TOY, 8 SWS, 12 STR) przy 3 trójkach ziaren 8001–8009 — sieci milczą na pustym obrazie, więc ignorowanie offsetu w dekoderze (`loop.py:111` przekazuje `[0.0]`) jest nieszkodliwe.
- **I2** Powtarzalność kalibracji (`c1.py`): DATA 494,3/499,2/497,7 (protokół 492,1 dla 5001–5003, różnica ≈ 1 %); TOY 303–310; SWS 487–498; STR_OWN w obrębie instancji 1–6 % (np. 139,2/154,3/145,9), między instancjami 82–206 Hz/rad. Kalibracja DATA jest JEDNĄ realizacją wspólną dla wszystkich 240 prób (pseudoreplikacja ≈ ±0,5 % wzmocnienia — pomijalne), a STR_OWN ma ±3–6 % szumu wzmocnienia — lekko niekorzystne dla STR_OWN (zawyża DATA − STR_OWN, bardzo mało wobec −1,45°).
- **I3** Uczciwość dekodera (pkt 4): procedura jest jednakowa dla DATA/SWS/STR_OWN/TOY (te same bodźce, ziarna, reguła); STR_SHARED jest celowo rozregulowane 1,3–8× (to jest H2b). Kalibracja jest na silnym napędzie (plamka r = 9 px ≈ ρ 0,16) i wyrównuje WZMOCNIENIE małosygnałowe, nie progi — przy ρ ≥ 0,22 napęd jest bliżej progu, więc „po wyrównaniu skali" H2a nadal zawiera różnice nieliniowości (protokół to zastrzega, `:55-56`).
- **I4** Wyciek kalibracyjny (pkt 5): brak. Kalibracja używa bodźców syntetycznych i ziaren ALIF 5001–5003, liczona raz na instancję przed próbą, bez wyników zachowania; instancje wyprowadzone z ziarna próby nie zależą od jej wyniku. Wspólny szum ALIF = ziarno próby dla wszystkich warunków SNN to poprawne wspólne liczby losowe (CRN); sceny i ALIF wykorzystują `default_rng(ziarno)`, ale na 999 ziarnach (8001–8999) Spearman(az0, szum[0]) = −0,002, (ρ, szum[1]) = 0,051 — brak mierzalnego sprzężenia. Parzystość ziarna → warstwa nie wpływa na dynamikę.
- **I5** Informacja o prawdzie: sterownik dostaje tylko obraz (+ propriocepcję warstwy bezpieczeństwa); `bearing()` służy wyłącznie do oceny (`loop.py:118,158`). Brak ukrytych ścieżek wykrytych. Zera (sieć milcząca) dają d ≡ 0 tylko dla dokładnie tej samej odpowiedzi, co poprawnie obsługuje test zmiany znaku.
- **I6** Poprawne: Holm (`v5v4.py:72-78`), znak d, ziarna instancji (+400 000/+200 000), pule i `FORBIDDEN` identyczne z tekstem, rozmiary warstw 120/120 (sprawdzone w teście), korespondencja TOST ⇔ CI95, progi 5 błędów / 2 %.
- **I7** „Brak użycia 4001–4240 itd. w 57 plikach": spot-check — wyszukiwanie liczb przy słowach seed/ziarn w `flymind/` i `bio2/results` znalazło 4xxx/5001–5010/6001–6010 tylko w plikach v5v4 (kod, test, szkic); pochodne 404 0xx/204 0xx/104 0xx/504 0xx nie występują. Liczby „57" nie weryfikowałem.

## 3. Odpowiedzi na pytania 1–12 (skrót)

1. **Falsyfikowalność.** Częściowa. H1 i H2 są testami dwustronnymi z zapowiedzianymi kategoriami, więc „wynik" jest zawsze możliwy, ale dla S2 (M2) i przy S1 na krawędzi SESOI (M3) duża część wyników to „nie wykazano ani różnicy, ani równoważności". Brak zapisanych przewidywań kierunkowych. H2a z założenia nie rozdziela mechanizmów (uczciwie zapisane).
2. **SESOI.** Obronny jako próg inżynieryjny, nie naukowy (m2).
3. **Moc.** Nie dla S2 równoważności; krucha dla S1 przy wyższym SD (M2).
4. **Uczciwość dekodera.** Tak proceduralnie; drobne asymetrie szumu kalibracji (I2, I3).
5. **Wyciek kalibracji.** Nie (I4).
6. **Kontrole.** SWS izoluje wzorzec w bloku LC10a×LC10a (zachowuje resztę); STR_OWN vs STR_SHARED izoluje skalę dekodera; H2a nie rozdziela lateralizacji od architektury (zapisane). TOY — inny model, nie kontrola izolująca.
7. **Jednostka/CI/TOST.** Jednostka (ziarno, sparowanie) poprawna; korespondencja TOST poprawna; percentylowy bootstrap lekko antykonserwatywny przy skośnym d (m1). Instancje SWS losowane na ziarno — wnioskowanie o DATA vs rozkład kontroli × sceny (wariancja realizacji wchłonięta w SD).
8. **Wielokrotność.** Spójna w obrębie rodzin; rodziny wymagają jawnej deklaracji, brak macierzy wyniku łącznego (m6).
9. **Ukryte ścieżki.** Nie znaleziono (I4, I5).
10. **ρ < 0,28.** Nie jest niezależne od wyników i uzasadnienie mechanistyczne jest błędne w kierunku zależności od |az| (M1); granica 0,22 neutralna arytmetycznie, nieneutralna informacyjnie (M3).
11. **Uczciwość przy null/odwróceniu/niejednoznaczności.** Kategorie są dobre („kontrola lepsza", „nie wykazano…"), ale brak macierzy wyniku łącznego, szablonu zdań i zastrzeżenia o kancelacji w S2 (m6, m10, M3).
12. **Model vs mózg.** Zastrzeżenia są, ale wymagają szablonu raportu (m10).

## 4. Tabela twierdzeń

| Twierdzenie protokołu | Weryfikacja | Wynik |
|---|---|---|
| 18 asercji testów zielone | `test_v5v4.py` | zgodne |
| Stage 1 28/28 | `loop.stage1_hashes()` | zgodne (28, brak niezgodnych) |
| DATA slope 492,1, TOY 306,1 (ziarna 5001–5003) | nie powtarzane na zakazanych ziarnach; na 8001–9 DATA 494–499, TOY 303–310 | zgodne co do rzędu (±1 %) |
| Dla ρ ≥ 0,28 sieć milczy przy |az| ≥ 15° | `e1.py`, V5 v3 | **FAŁSZ w tej formie** (napęd rośnie z |az|; 5/18 niezerowych) — M1 |
| Granica 0,22 nie dobrana do wyników | `p1.py` | arytmetycznie tak; S2 zawiera zmianę znaku V5 v3 — M3 |
| fov 86°, 0,67°/kol. | obliczenie | zgodne |
| P ≈ 0,3° | V5 v3 (0,314) | zgodne |
| V5 v3: H1 −0,19, CI90 [−0,51; +0,10], warstwy +0,53/−1,02/−0,47, H2 −2,40 | `analysis_summary.txt` | zgodne |
| Dev 1501–1520: STR_OWN +1,17, DATA−STR 2,62→1,45 | `v5v4_power.py` czyta plik: −1,45 i +1,17 | zgodne; pominięta replikacja 1001–1044 — M3 |
| SD S1 ≈ 0,64, S2 ≈ 1,86 | `p1.py` | zgodne (0,642; 1,863); CI SD szerokie — M2 |
| Moc S2 0,70 / 0,80 / ≈1,0; S1 ≈ 1,0; H2 ≥ 0,94 | `v5v4_power_20261029.txt`, `p2.py` | zgodne przy punktowym SD; kruche — M2 |
| TOST α 0,025/warstwę ⇔ CI95 | rachunek, `p3.py` | poprawne; rozmiar empiryczny 0,02–0,04 — m1 |
| Holm, SESOI, CI 95/90, 100 000 perm., 10 000 boot., ziarna 4401/4402 | `v5v4.py:32,59-78` | zgodne |
| Pule i FORBIDDEN, offsety +400 000/+200 000 | `v5v4.py:29-36,176,180` | zgodne |
| Kategorie H1 | `v5v4.py:89-99`, test | zgodne (m3: etykieta przy efekcie < SESOI) |
| Wykluczenie/odmowa/STOP | `v5v4.py:104-108,190-208` | zgodne poza: STOP „kod ≠ manifest" i „Stage 1 po" nieegzekwowane (m7) |
| Wznowienie bez podwójnego liczenia, brak rekordu częściowego | `v5v4.py:160-161,204-205` | działa, ale zapis nieatomowy (m7) |
| Kalibracja bez wycieku | kod, `c1.py` | zgodne (I4) |
| Offset ignorowany w dekoderze | `loop.py:111`, `c1.py` | nieszkodliwy (I1) |
| Brak użycia pul 4001–4240… w 57 plikach | grep | spot-check zgodny; „57" niezweryfikowane |

## 5. Wymagane zmiany przed READY (kolejność)
1. M1: przepisać uzasadnienie ρ < 0,28; zakres wniosków; opcjonalnie S3 opisowa lub kryterium aktywności z renderu.
2. M2: tabela wrażliwości SD/δ w §5; zwiększyć n w S2 albo reguła bramkująca precyzji albo kowariaty.
3. M3: dopisać replikację dev 1001–1044 do §0; opis d ~ ρ + |az|; przewidywania; zastrzeżenie o kancelacji w S2.
4. m1, m3, m4, m5, m7 (egzekwowanie STOP/manifest, atomowy zapis, walidacja zbioru ziaren w `analyze`), m6, m10 — tanie, zrobić przed zamrożeniem.

## 6. Podsumowanie (10 linii)
1. Jestem osobną instancją modelu (ograniczona niezależność: ten sam typ modelu i kontekst repozytorium co autor).
2. Werdykt: NOT READY — 0 BLOCKER, 3 MAJOR (M1–M3), 11 MINOR, 7 INFO.
3. M1: uzasadnienie ρ < 0,28 jest odwrócone względem |az| (rendery: napęd rośnie z |az|; V5 v3: 5/18 scen ρ ≥ 0,28 niezerowych, średnia −1,43°), a cięcie wybiera domenę „równoważną" (−0,07° w ρ < 0,28).
4. M2: n = 120/warstwę — S2 równoważność P = 0,70 tylko przy SD 1,86; SD 2,64 → 0,14; δ = −0,2° → 0,13–0,44; S1 przy SD 1,6 → 0,89 (δ=0), 0,55 (δ=−0,2).
5. M3: pominięta replikacja dev 1001–1044 (warstwy się nie replikują), S2 zawiera zmianę znaku V5 v3 (+0,68 / −1,23), S1 leży na krawędzi SESOI (+0,47).
6. TOST ⇔ CI95 przy α 0,025 jest poprawne; Holm i kod zgodne z tekstem; bootstrapowe CI ma rozmiar 0,02–0,04 przy skośnym d (BCa/t jako drugi warunek).
7. Dekoder i kalibracja: procedura uczciwa, brak wycieku, offset = 0 w 22/22 instancji, brak odmów; asymetria szumu wzmocnienia STR_OWN ±3–6 %.
8. Kod vs protokół: STOP „kod ≠ manifest" i „Stage 1 po" nieegzekwowane; `analyze` nie waliduje zbioru ziaren; zapis JSONL nieatomowy.
9. Testy: `test_v5v4.py` 18/18, `test_side_shuffle.py` 28/28, `test_v5v3_analysis.py` 18/18, Stage 1 28/28; użyto tylko ziaren 8001–8999, bez pętli zamkniętej.
10. Po naprawie M1–M3 (i tanich MINOR) ponowna runda r2 powinna dać READY; raport: `/Users/admin/so101_fly_project/flymind/results/redteam/v5v4_protocol_redteam_r1.md`.
