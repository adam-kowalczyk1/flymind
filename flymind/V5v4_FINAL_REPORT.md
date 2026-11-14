# FlyMind V5 v4 — raport końcowy (2026-10-30)

**Status: PASS_WITH_LIMITATIONS** — eksperyment przeszedł wszystkie bramki i jest ważny (VALID); wyniki rozstrzygają H1 i H2
w zarejestrowanych granicach; ograniczenia niżej.

## 1. Pytanie badawcze
Czy w modelu FlyMind (ALIF, J0 0,2, enkoder inżynieryjny, MuJoCo) wzorzec połączeń z connectomu MaleCNS wewnątrz bloków warstwa×strona
zmienia błąd orientacji ramienia, przy zachowanej lateralizacji, architekturze warstw, wejściach DNa02 i skali sygnału (H1, osobno w warstwach
ρ [0,16; 0,22) i [0,22; 0,28) m)? Jaka część różnicy DATA vs SHUF_STR wynika ze skali sygnału / kalibracji dekodera (H2)?

## 2. Protokół i hashe
`validation/v5v4_protocol.md` (r3) sha256 f648c7ea3d8631fc257a398f2c168798d32a823dc5a3667dfab0cfa9da790ce0; manifest `validation/v5v4_manifest.json`
(18 plików kodu, rejestr ziaren, raporty RT, stat plików danych); kopia kodu `validation/v5v4_frozen_code/`; historia r1, r2 zachowana
(`v5v4_protocol_DRAFT_r1_superseded.md`, `…_r2_superseded.md`, `results/v5v4_r1_runner_superseded.py.txt`, `…_r2_…`).

## 3. Audyt bezpieczeństwa
Stage 1: 28/28 przed (21:50, 22:18) i po (07:37). Kod V5 v4 = manifest = kopia przed testem dymnym, po nim, przed i po przebiegu; protokół,
rejestr, raporty RT i pliki danych bez zmian. Artefakty V5 v3 nienaruszone (kontrola po przebiegu). bio2/assets/data bez zmian, brak
`__pycache__`, brak commitów, brak fizycznego ramienia. `--analyze` → `validity.VALID = true` (0 linii uszkodzonych, 2 shardy VALID).

## 4. Red Team (osobna instancja modelu — ograniczona niezależność, nie recenzja ludzka)
- r1 (`results/redteam/v5v4_protocol_redteam_r1.md`): NOT READY — M1 błędne uzasadnienie ρ < 0,28 (potwierdzone moim renderem), M2 krucha moc,
  M3 nieujawniona replikacja i ryzyko kancelacji; 11 MINOR. Poprawione w r2.
- r2: READY, 9 MINOR (N1–N9); N1, N2, N6–N9 poprawione przed zamrożeniem, N3–N5 przyjęte jako ograniczenia.
- r3 (diffy): READY, 3 MINOR (rozwiązane procedurą).
- Niezależnego Red Teamu WYNIKÓW nie przeprowadzono; wyniki zweryfikowano drugą implementacją analizy (`audit_v5v4_independent.py`).

## 5. Rejestr ziaren (`validation/v5v4_seed_registry.md`)
Potwierdzające 4001–4450 (S1 4001–4150, S2 4151–4450), SWS +400 000, SHUF_STR +200 000, kalibracja 5001–5003, test dymny 6001–6002,
RNG analizy 9401/9402 (reanaliza 9501). Pule sprawdzone jako wolne przed rejestracją; zakazane pule odrzucane przez runner.

## 6. Przebieg
Shardy A (4001–4225) i B (4226–4450), start 2026-10-29 22:18, koniec 07:29 / 07:37 (spowolnienie w nocy — przebieg ciągły, bez wznowień).
Zaplanowane 450 ziaren × 6 warunków = 2700 prób; wykonane 2700; błędy symulatora 0; wykluczenia 0; odmowy kalibracji 0; linie uszkodzone 0.
Surowe dane: `results/v5v4/raw_v5v4_{A,B}.jsonl`; logi `stdout_{A,B}.txt`; metadane `run_meta_{A,B}_*.json`; analiza `analysis_frozen.json`;
reanaliza `audit_independent.txt`; nachylenia SWS `post_sws_slopes.txt`; integralność `results/v5v4_run_integrity.txt`.

## 7. Wyniki (d = błąd(pierwszy) − błąd(drugi); d < 0 ⇔ pierwszy lepszy)
| Warunek | błąd śr. / mediana | S1 śr. (sukces /150) | S2 śr. (sukces /300) |
|---|---|---|---|
| DATA | 2,88 / 1,95° | 1,72° (141) | 3,46° (211) |
| SWS (CONTROL) | 3,05 / 1,91° | 1,21° (141) | 3,97° (195) |
| STR_OWN (CONTROL) | 4,26 / 3,06° | 2,28° (111) | 5,24° (171) |
| STR_SHARED (CONTROL) | 5,66 / 4,59° | 1,82° (138) | 7,58° (89) |
| TOY (MODEL) | 4,31 / 2,98° | 0,55° (150) | 6,18° (132) |
| P (ENGINEERING) | 0,20 / 0,18° | 0,28° (150) | 0,16° (300) |

**H1 (główna, per warstwa; przewaga: Holm na 2; równoważność: TOST α 0,025, oba CI95 ⊂ ±0,5°):**
| Warstwa | n | d śr. | CI95 bootstrap | CI95 t | d_z | p (perm) | p_Holm | Kategoria |
|---|---|---|---|---|---|---|---|---|
| S1 [0,16; 0,22) | 150 | **+0,512°** | +0,414; +0,612 | +0,411; +0,613 | +0,82 | 1·10⁻⁵ | 2·10⁻⁵ | kontrola lepsza, efekt ≥ SESOI |
| S2 [0,22; 0,28) | 300 | **−0,518°** | −0,713; −0,329 | −0,713; −0,323 | −0,30 | 1·10⁻⁵ | 2·10⁻⁵ | DATA lepsza, efekt ≥ SESOI |
Równoważność (TOST) — w żadnej warstwie nie wykazana. Uwaga: etykieta „≥ SESOI” wynika ze średniej (|d| ≈ 0,51–0,52°); przedziały ufności
obejmują też wartości poniżej 0,5° (S1 od 0,41°, S2 do −0,33°) — wielkość efektu jest na granicy SESOI.
Opis (bez decyzji): łącznie −0,175° (CI −0,32; −0,04 — kancelacja przeciwnych znaków); podpasma S2a [0,22; 0,25) −0,38° (−0,60; −0,18),
S2b [0,25; 0,28) −0,66° (−0,99; −0,33); regresja d = 3,37 − 14,6·ρ − 0,012·|az0| (SE: 0,50; 2,10; 0,008) — przewaga DATA rośnie z odległością,
znak zmienia się przy ρ ≈ 0,23 m. Sukces DATA vs SWS: 29 vs 13 par rozbieżnych (McNemar p 0,02, bez korekty). Nachylenia SWS 0,988–1,005 × DATA.

**H2 (Holm na 2):** H2a DATA − STR_OWN = −1,38° (CI −1,82; −1,03), p_Holm 2·10⁻⁵ — DATA lepsza także po wyrównaniu skali kalibracją;
H2b STR_SHARED − STR_OWN = +1,41° (CI +0,99; +1,77), p_Holm 2·10⁻⁵ — sama kalibracja dekodera zmienia błąd tej samej sieci o ~1,4°,
ale niejednorodnie: S1 −0,46°, S2 +2,34° (opis). Nachylenia STR_OWN 18–203 Hz/rad (mediana 124; DATA 492); Spearman(slope, błąd) −0,08 (p 0,11).
H2 interpretowalne (0 odmów).
**Opis:** DATA − TOY −1,43° (−1,68; −1,17); DATA − P +2,68° (+2,46; +2,91) — regulator P lepszy w 450/450 parach (348 o > 1°).

## 8. Interpretacja, ograniczenia, alternatywy
- **Wynik eksperymentu (model, MuJoCo):** wzorzec połączeń z danych wewnątrz bloków warstwa×strona MA mierzalny wpływ na sterowanie ponad
  lateralizację i skalę sygnału, ale jego kierunek zależy od reżimu: przy bliskich celach (silny napęd) losowy wzorzec daje mniejszy błąd
  (+0,51°), przy dalszych (słaby napęd) wzorzec z danych daje mniejszy błąd (−0,52°). Wielkość ≈ SESOI (0,5°). Zgodne z obserwacją w pętli
  otwartej sprzed protokołu (znak odpowiedzi zależy od napędu) i z opisem warstw V5 v3 — które Red Team uznał za niereplikowane na dev;
  na nowych 450 ziarnach struktura się powtórzyła.
- **Co to NIE jest:** przewaga „topologii muchy” — wzorzec z danych nie jest jednoznacznie lepszy; nie jest to twierdzenie o mózgu muchy.
- **Identyfikacja przyczynowa:** SWS zmienia razem wzajemność, trójkąty, klasteryzację i asortatywność bloku LC10a×LC10a (nie rozdzielone);
  57–58 % masy |w| nie testowane. H2a po wyrównaniu skali nie rozdziela lateralizacji od architektury warstw. Kalibracja wyrównuje tylko
  wzmocnienie małosygnałowe; H2b pokazuje, że wybór dekodera sam zmienia wynik o rząd efektu H1 — porównania sieci są wrażliwe na odczyt.
- **Zakres:** tylko ρ ∈ [0,16; 0,28) m, az0 ∈ (−30°, 30°), jedna konfiguracja (J0 0,2, próg 5 synaps, ALIF b_a 0,5, enkoder V4 v2).
  Obszar ρ ≥ 0,28 m nietestowany.
- **Jakość sterowania vs wartość wyjaśniająca:** regulator P jest lepszy o 2,7° w każdej scenie; wartość wyjaśniająca topologii jest
  osobnym, małym efektem modelowym.
- **Alternatywy:** efekt może wynikać z nieliniowości progu ALIF (próg × rekurencja), a nie z konkretnego motywu; inny J0/szum może zmienić
  punkt zmiany znaku (eksploracja V6: kierunek progu stały w 18/20 ustawień, ale wielkość mała).
- DATA = connectom MaleCNS (droga LC10a → pośrednie → DNa02, wagi, przekaźniki); MODEL = ALIF, J0, znak Glu, przekaźnik TOY;
  ENGINEERING = enkoder, kamera, MuJoCo, bezpieczeństwo, regulator P; CONTROL = SWS, SHUF_STR, kalibracja dekodera.

## 9. Pliki utworzone w flymind/ (V5 v4)
`v5v4.py`, `test_v5v4.py`, `v5v4_power.py`, `v5v4_power_r2.py`, `v5v4_post_sws_slopes.py`, `audit_v5v4_independent.py`, `V5v4_STAGE_A_AUDIT.md`,
`V5v4_FINAL_REPORT.md`; `validation/v5v4_protocol.md`, `v5v4_protocol_DRAFT.md`, `v5v4_protocol_DRAFT_r1_superseded.md`, `…_r2_superseded.md`,
`v5v4_manifest.json`, `v5v4_seed_registry.md`, `v5v4_frozen_code/`; `results/v5v4/` (surowe, logi, metadane, analizy), `results/v5v4_power_*.txt`,
`results/v5v4_calibration_check_20261029.txt`, `results/v5v4_run_integrity.txt`, `results/v5v4_r1_runner_superseded.py.txt`, `…_r2_…`,
`results/v7_encoder_distance_az_20261029.txt`, `results/redteam/v5v4_protocol_redteam_r{1,2,3}.md`.

## 10. Status końcowy: PASS_WITH_LIMITATIONS
Następny krok (wymaga zgody): niezależny Red Team wyników V5 v4; potem rozdzielenie motywów bloku LC10a×LC10a (np. kontrola zachowująca
wzajemność) jako nowy protokół na nowej puli ziaren.
