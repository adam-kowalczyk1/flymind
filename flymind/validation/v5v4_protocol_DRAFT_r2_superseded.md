# V5 v4 — protokół (SZKIC r2, 2026-10-29; po Red Team r1 — NIEZAMROŻONY, NIEURUCHOMIONY)

Historia: r1 → `v5v4_protocol_DRAFT_r1_superseded.md`; Red Team r1 (`results/redteam/v5v4_protocol_redteam_r1.md`): NOT READY
(3 MAJOR, 11 MINOR) — poprawki niżej oznaczone [M1]–[M3], [m]. Kod: `flymind/v5v4.py` (r2; r1 w `results/v5v4_r1_runner_superseded.py.txt`),
testy `flymind/test_v5v4.py` (21 asercji, zielone), moc `flymind/v5v4_power_r2.py` → `results/v5v4_power_r2_20261029.txt`.
Etykiety: DATA (connectom MaleCNS v1.0), MODEL (ALIF, J0 0,2, Glu = hamowanie, przekaźnik), ENGINEERING (enkoder, kamera, MuJoCo,
warstwa bezpieczeństwa, regulator P), CONTROL (tasowania, kalibracja dekodera). Wynik dotyczy modelu, nie mózgu muchy.

## 0. Wiedza przed napisaniem (jawnie) [M3]
- V5 v3 (3051–3100, potwierdzające): H1 DATA − SWS v2 = −0,19° (CI90 −0,51; +0,10) łącznie; opis warstw: ρ 0,16–0,24 +0,53°,
  0,24–0,30 −1,02°, 0,30–0,35 −0,47°; w zakresie ρ < 0,28: n = 32, średnia −0,07°; w S2 podzakresy przeciwnych znaków
  (0,22–0,24 +0,68°, 0,24–0,28 −1,23°) — średnia warstwy może ukrywać efekty przeciwnych znaków (kancelacja).
- Red Team V5 v3 — replikacja na ziarnach dev 1001–1044: d łączne −0,23° powtórzone, ale struktura warstw NIE (warstwa bliska
  −0,01° zamiast +0,53°; Spearman(d, ρ) p 0,24). Struktura warstw z V5 v3 jest więc niepewna.
- Skala sygnału (eksploracja dev 1501–1520, mój kod; RT dev 1001–1044): SHUF_STR z własną kalibracją poprawia się o ~1,0–1,2°;
  DATA − SHUF_STR maleje z −2,0…−2,6° do −1,0…−1,45°.
- Enkoder [M1] (rendery statyczne `results/v7_encoder_distance_az_20261029.txt`): prąd LC10a (12 mV·g) ROŚNIE z |az|; nadprogowy
  (> ~7 mV) przy ρ 0,22 od |az| ≈ 10°, ρ 0,25 od ≈ 15°, ρ 0,28 od ≈ 20°, ρ 0,30 od ≈ 25°, ρ 0,33 od ≈ 30°; przy |az| = 0 podprogowy
  już od ρ ≈ 0,20. Uzasadnienie w r1 („podprogowy dla |az| ≥ 15° przy ρ ≥ 0,28”) było BŁĘDNE (oparte tylko na az 0° i 15°).
- Przewidywania (zapisane teraz, nie kryteria): S1 — równoważne lub mała przewaga kontroli; S2 — mała przewaga DATA lub
  nierozstrzygnięte; H2a — DATA lepsza o ~1°; H2b — STR_SHARED gorsza o ~1°.

## 1. Pytania i hipotezy (d = błąd(pierwszy) − błąd(drugi); d < 0 ⇔ pierwszy lepszy)
- **Rodzina H1 (główna):** DATA vs SWS (SHUF_WITHIN_SIDE v2), osobno w S1 [0,16; 0,22) i S2 [0,22; 0,28).
  (a) przewaga — test permutacyjny zmiany znaku średniej d, Holm na {S1, S2}, α 0,05;
  (b) równoważność — TOST ±0,5° przy α 0,025 na warstwę (Bonferroni na 2) ⇔ OBA przedziały 95 % (bootstrap percentylowy
  i t-Studenta) ⊂ (−0,5°; +0,5°) [m: rozmiar samego bootstrapu 0,021–0,040].
  Wynik łączny S1+S2, podpasma S2a [0,22; 0,25) i S2b [0,25; 0,28) oraz regresja d ~ ρ + |az0| (OLS) — opis [M3], bez decyzji.
- **Rodzina H2 (skala sygnału vs reszta):** H2a DATA − STR_OWN (po wyrównaniu skali); H2b STR_SHARED − STR_OWN (efekt samej
  kalibracji na tej samej instancji). Holm na {H2a, H2b}, α 0,05; decyzja: p_Holm < 0,05 ∧ CI95 bootstrap bez 0.
- Opis (bez decyzji): DATA − TOY, DATA − P; sukces (McNemar, bez korekty), czas do |e| < 5°, przeregulowanie [m].
Zakres wniosków ograniczony z góry: SWS v2 zachowuje lateralizację, architekturę warstw, wejścia DNa02, skład grup i multizbiory
wag; różni się w praktyce wzorcem w bloku LC10a×LC10a (wzajemność, trójkąty, klasteryzacja, asortatywność razem); 57–58 % masy |w|
nie jest ruszane. SHUF_STR niszczy jednocześnie lateralizację, architekturę warstw i wzorce w blokach; H2a po wyrównaniu skali NIE
rozdziela lateralizacji od architektury warstw. Kalibracja wyrównuje wzmocnienie małosygnałowe, nie progi ani nieliniowość.

## 2. Zakres ρ < 0,28 m i warstwy — uzasadnienie uczciwe [M1]
Ograniczenie wynika z polecenia projektu i z rekomendacji Red Team V5 v3 (motywacja EKSPLORACYJNA z wyników V5 v3), a NIE
z mechanizmu wykluczającego obszar ρ ≥ 0,28: tam sieć jest aktywna przy dużych |az| (V5 v3: 5/18 scen niezerowych, średnia d
−1,43°). Konsekwencja: **wnioski dotyczą wyłącznie ρ ∈ [0,16; 0,28) i az0 ~ U(−30°, 30°)**; obszar ρ ≥ 0,28 m pozostaje
nierozstrzygnięty i nie jest testowany. Granica 0,22 m dzieli zakres na połowy (nie dobrana do wyników). W S1 sieć jest
nadprogowa dla większości scen; w S2 tylko dla |az| powyżej ~10–20° — dlatego S2 zawiera więcej zer strukturalnych.

## 3. SESOI = ±0,5° — granica INŻYNIERYJNA [m]
Uzasadnienie wyłącznie inżynieryjne (nie biologiczne): 128 kolumn na ~86° → 0,67°/kolumnę; enkoder rozmywa 3×3 px; różnica < 0,5°
jest poniżej rozdzielczości kamery i poniżej 10 % tolerancji sukcesu (5°); regulator P na tym enkoderze osiąga ~0,3°.
Nie wynika z wyników V5 v3. „Równoważne” znaczy: |różnica średnich| < 0,5° w danej warstwie — nie „topologia nieistotna”.

## 4. Warunki (6), sceny, dekodery
| Warunek | Definicja | Status |
|---|---|---|
| DATA | `visual_path.network(0.2)`; dekoder DATA | DATA + MODEL |
| SWS | `shuffle_within_side(spec, layer_side_labels, ziarno + 400 000)`; asercja 17 własności + cel zamian; dekoder DATA | CONTROL |
| STR_OWN | `shuffle(equal_weight=True)`, ziarno + 200 000, asercje + cel zamian; dekoder kalibrowany na tej instancji | CONTROL |
| STR_SHARED | ta sama instancja SHUF_STR; dekoder DATA | CONTROL |
| TOY | `loop_v2.toy_relay`; dekoder własny | MODEL |
| P | regulator P na gL − gR | ENGINEERING |
Sceny `trial_spec_v4`: az0 ~ U(−30°, 30°); ρ ~ U w warstwie; ziarna 4001–4150 → S1, 4151–4450 → S2; identyczne sceny dla wszystkich
warunków ziarna; Q_POSE, 3 s, takt 10 ms; ziarno ALIF = ziarno próby (wspólne dla warunków SNN; RT r1: brak sprzężenia scena–szum).
**Kalibracja (CONTROL):** `v5v4.calibrate` — bodźce syntetyczne spot_clip az −30…30° co 10° + pusty obraz, ziarna ALIF 5001–5003,
jedyny parametr: slope (offset = L−P dla pustego obrazu; RT r1: offset = 0 we wszystkich 22 sprawdzonych instancjach); cel: MNK
L−P DNa02 względem azymutu; liczona raz na sieć przed jej próbami i zamrożona; slope ≤ 2 Hz/rad → odmowa. Dekoder DATA (492,1 Hz/rad)
obsługuje DATA, SWS (nachylenia SWS 487–498 ≈ DATA — bez dodatkowego szumu kalibracji) i STR_SHARED; własny: STR_OWN, TOY (306,1).
Kalibracja nie widzi scen ani wyników pętli zamkniętej (RT r1: brak przecieku).

## 5. Ziarna i liczebność [M2]
Potwierdzające **4001–4450** (S1 150, S2 300); instancje SWS 404 001–404 450, SHUF_STR 204 001–204 450; kalibracyjne 5001–5003;
test dymny 6001–6002 (dev). Historia: 4001–4450 (+0 / 100 000 / 200 000 / 400 000 / 500 000), 5001–5010, 6001–6010 — brak w 57 plikach
JSON wyników/manifestów/scratchpadu i w kodzie. Runner odmawia ziaren 0–39, 300–399, 1001–1999, 2001–2005, 2011–2100, 3001–3100.
Moc (resampling kształtu d z V5 v3, SD jako parametr; TOST z CI t — z wymogiem obu CI moc nieco niższa):
| Warstwa | n | SD | P(równoważność): δ = 0 / −0,2 | P(przewaga): δ = −0,2 / −0,5 / −1,0 |
|---|---|---|---|---|
| S1 | 150 | 0,64 / 1,0 / 1,6 / 2,0 | 1,00 / 1,00 / 0,95 / 0,77 ; 1,00 / 0,97 / 0,66 / 0,47 | 0,96–0,17 ; ≥ 0,82 ; 1,00 |
| S2 | 300 | 1,86 / 2,3 / 2,64 / 3,0 | 0,99 / 0,94 / 0,85 / 0,69 ; 0,81 / 0,63 / 0,53 / 0,44 | 0,36–0,13 ; ≥ 0,78 ; 1,00 |
Wniosek: rozstrzygnięcie jest prawdopodobne dla δ = 0 i |δ| ≥ 0,5°; dla |δ| ≈ 0,2° wynik będzie zwykle „nie wykazano ani różnicy,
ani równoważności” — i tak zostanie zaraportowany. n ustalone z góry; bez zwiększania zależnego od wyniku.
Wykonanie: 2 shardy równolegle (A: 4001–4225, B: 4226–4450), osobne pliki JSONL; analiza łączy oba i wymaga kompletu 450 ziaren.

## 6. Metryki i analiza
Główna: błąd końcowy = średnie |e| w 2,5–3,0 s (e z prawdy symulatora, tylko ocena). Jednostka analizy: ziarno (scena), porównania
sparowane. CI: bootstrap par percentylowy (10 000, ziarno 4402) 95 % i 90 % + CI t 95 %; test: permutacyjny zmiany znaku
(100 000, ziarno 4401); pomocniczo Wilcoxon (Pratt), d_z, liczba zer, liczba par |d| > 1°.
Kategorie H1 per warstwa [m]: „DATA lepsza, efekt ≥ SESOI”; „DATA lepsza, efekt < SESOI (praktycznie pomijalny)”; analogicznie
„kontrola lepsza …”; „równoważne w granicach ±SESOI”; „nie wykazano ani różnicy, ani równoważności”. p > 0,05 ≠ „brak efektu”.
Macierz wyniku: kategoria S1 × kategoria S2 raportowana w całości; brak jednego „wyniku łącznego” H1.

## 7. Braki, wykluczenia, przerwanie, wznowienie
- Błąd próby (wyjątek symulatora/kodu albo NaN) → ziarno wykluczone ze WSZYSTKICH porównań błędu (sparowanie), w sukcesie = porażka.
  Wrażliwość per warstwa w OBU kierunkach (wykluczone jako d = +max|d| i −max|d|) [m].
- Odmowa kalibracji STR_OWN → błąd = |az0| (brak ruchu), sukces = porażka; wrażliwość H2 bez tych ziaren; > 10 % odmów → H2
  oznaczona jako nieinterpretowalna [m]. Odmowa kalibracji DATA lub TOY → STOP. (SWS nie ma własnej kalibracji.)
- STOP (brak analizy potwierdzającej): Stage 1 niezgodny przed przebiegiem; kod ≠ manifest albo protokół ≠ manifest przy starcie
  (egzekwowane w runnerze) [m]; naruszenie własności SWS/SHUF_STR lub nieosiągnięty cel zamian [m]; > 5 błędów w jednym warunku lub
  > 2 % prób w shardzie; duplikat ziarna lub niekompletny zbiór 450 ziaren w analizie [m]. Stage 1 lub kod niezgodny PO przebiegu →
  `VALID = false` w metadanych, wynik raportowany wyłącznie jako nieważny.
- Wznowienie: 1 linia JSONL = 1 kompletne ziarno (zapis + fsync); ponowne uruchomienie tym samym poleceniem pomija ziarna z poprawną
  linią, uszkodzoną linię traktuje jak brak (ziarno liczone od nowa); analiza odrzuca duplikaty.

## 8. Raportowanie i szablon zdań [m]
Raport: wszystkie warunki, warstwy, podpasma, regresja, porównania (także nieistotne); liczby zaplanowane/wykonane/wykluczone/odrzucone;
nachylenia kalibracji; odstępstwa; rozdzielenie DATA/MODEL/ENGINEERING/CONTROL. Szablony:
„W modelu (ALIF, J0 0,2, enkoder inżynieryjny) wzorzec połączeń z connectomu MaleCNS wewnątrz bloków warstwa×strona [zmienił / nie zmienił
o więcej niż 0,5° / nie wykazano] błąd orientacji w warstwie …” — NIGDY „mózg muchy …”. „Równoważne” zawsze z „w granicach ±0,5°,
dla ρ … m”. Fixed-drive — osobne pytanie, poza tym protokołem.
