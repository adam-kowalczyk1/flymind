# FlyMind — dziennik pracy autonomicznej

Statusy: `PLANNED`, `IN_PROGRESS`, `BLOCKED`, `DONE`. Etykiety: `DATA`, `MODEL`, `ENGINEERING`, `CONTROL`.
Integralność sprawdzana skryptem `scratchpad/integrity.py` (kopia logiki: hashe z `bio2/results/cx_causal_phase2_20261027_174754/frozen_manifest_v4.json`,
git status vs baseline, `bio2/__pycache__`, pliki bio2/assets/data nowsze niż dokumentacja flymind).

## Plan sesji (2026-10-29, program autonomiczny)
| # | Zadanie | Kryterium ukończenia | Status |
|---|---|---|---|
| 0 | Inwentaryzacja, integralność, pliki stanu | log + NEXT_SESSION, Stage 1 28/28 | DONE |
| 1 | Audyt V5 v2 (niezależny skrypt) | wszystkie liczby odtworzone lub rozbieżności opisane | DONE |
| 2 | Kontrola SHUF_WITHIN_SIDE + protokół V5 v3 | testy, Red Team, szkic protokołu | DONE (kontrola v2 PASS kodu; protokół r3) |
| 2b | Przebieg potwierdzający V5 v3 | jeden przebieg wg r3, analiza, Red Team | DONE — H1 niepotwierdzona (równoważne ±1°); RT PASS_WITH_LIMITATIONS |
| 3 | Mechanizm LC10a → AOTU: rola bloku vs siła sygnału | eksploracja dev + Red Team | DONE (PASS_WITH_LIMITATIONS) |
| 4 | Stabilność efektu DATA vs kontrola wobec parametrów ALIF/J0 (eksploracja, pętla otwarta) | tabela wrażliwości | DONE |
| 5 | Audyt enkodera i pętli | raport | DONE (odległość/próg; reszta z RT V4/V5 i V5 v2) |
| 6 | Rozdzielenie rekurencji LC10a×LC10a od bloku AOTU w pętli zamkniętej | — | PLANNED (po decyzji o V5 v3; pilotaż kontrastu H1 przed zatwierdzeniem świadomie pominięty) |

## Wpisy

### 2026-10-29 16:13 — integralność przed pracą (V5 v3 prep)
Stage 1 28/28, protokół OK, manifest 2f061a60…; zmiany tylko w flymind/ (`results/v5v3_prep_integrity.txt`).
Repozytorium: commit użytkownika 23ff163 (flymind/ śledzony); niezacommitowane po nim wyłącznie zmiany agenta w flymind/.
Dane źródłowe: `data/malecns/{body-annotations,body-neurotransmitters,connectome-weights}-male-cns-v1.0-minconf-0.5.feather`.

### 2026-10-29 — Audyt V5 v2 (DONE) — `audit_v5v2_independent.py` → `results/audit_v5v2_independent_20261029.txt`
- Manifest = bieżący kod = kopia zamrożona; 9 warunków × 50 ziaren, sceny sparowane bez rozbieżności, brak duplikatów.
- Średnie d i CI (bootstrap innym ziarnem, CI t) zgodne z raportem.
- Rozbieżność metodyczna: p zależą od obsługi zer (16/50 par d = 0, sieć bez ruchu dla dalekich celów). Protokół V5 v2 nie
  precyzował metody. SHUF_STR istotne we wszystkich wariantach (p_Holm 0,00025–0,036); CUT_LC10a_AOTU istotne w wariantach
  Wilcoxona, NIE w teście znaków (0,36) → twierdzenie o mechanizmie słabsze niż raportowane.
- Indeks lateralizacji: jawne wyliczenie ścieżek = wynik macierzowy; wartości per próba zgodne. Ograniczenie definicji: ≤ 2 skoki.
- Powtarzalność: 18/18 prób identycznych (ziarna 3001–3002, 9 warunków) — wcześniej, `scratchpad/topo_repro`.
- **Wspólny dekoder (`audit_shared_decoder.py` → `results/audit_shared_decoder_20261029.txt`):** własne nachylenie kalibracji
  SHUF_STR (instancje V5 v2) 101–147 Hz/rad vs DATA 496 → ze wspólnym dekoderem SHUF_STR pracowała przy ~20–30 % wzmocnienia
  pętli DATA. Różnica DATA − SHUF_STR w V5 v2 może więc wynikać częściowo ze SKALI SYGNAŁU, nie z topologii. Nowa kontrola
  SHUF_WITHIN_SIDE v2: 491–494 Hz/rad (≤ 1 %) — tego zakłócenia nie ma.

### 2026-10-29 — Kontrola SHUF_WITHIN_SIDE (DONE — v2; wpis pierwotnie IN_PROGRESS)
- v1 (tylko somaSide): testy OK, ale Red Team (`results/redteam/v5v3_control_redteam.md`) — FAIL jako izolacja: tworzy
  krawędzie LC10a → DNa02 (0 → 28–95), zmienia λ_max 26,1 → 34,9, architekturę warstw; 6 krawędzi niesie 76 % masy ścieżek.
  Zweryfikowane moim kodem (`scratchpad/verify3/v.py`).
- v2 (warstwa × somaSide): `side_shuffle.py`, `test_side_shuffle.py` (27 asercji, OK, w tym przypadki RT A/B/C),
  `v5v3_control_check.py` → `results/v5v3_prep/v5v3_control_check_v2_*.json`: wszystkie 17 własności, LI 1,0000, λ_max 26,3,
  kontra 0 Hz, architektura identyczna; różnica przy słabym napędzie w całości z bloku LC10a×LC10a (wzajemne pary 2450 → ~560).
- Szkic protokołu: `validation/v5v3_protocol_DRAFT.md`; runner `v5v3.py` odmawia bez sha256 zatwierdzonego protokołu.

### 2026-10-29 17:0x — Red Team r2 kontroli v2 (`results/redteam/v5v3_control_v2_redteam.md`)
Werdykt: kod kontroli PASS (jedna luka `properties()` — brak multizbiorów (grupa, waga) per neuron; NAPRAWIONE, test P2 dodany,
28 asercji); protokół FAIL do czasu B1–B3 → protokół r3 (H1 jedyna główna α 0,05; H2/H3 Holm z 2; D1/D2 opis; warstwy ρ;
limit 2 błędów symulatora na warunek; analiza wrażliwości). `v5v3.analyze` dostosowane, `test_v5v3_analysis.py` 18 asercji.
Najmocniejszy kontrargument RT: v2 izoluje w praktyce tylko blok LC10a×LC10a, którego miary (wzajemność, trójkąty,
klasteryzacja, asortatywność) zmieniają się razem; efekt zmienia znak z napędem; 57–58 % masy |w| nie jest testowane.

### 2026-10-29 — Mechanizm (DONE, eksploracja) — `v5_mech_strength.py` → `results/v5_mech_strength/`
A (pętla otwarta): nachylenia DATA 496, CUT 196, RAND_CUT 262–276, SCALE 253. B (ziarna dev 1241–1290, n = 50): d vs DATA
CUT +0,73° (0,27; 1,22), RAND_CUT +1,94° (0,99; 2,90), SCALE +2,51° (1,46; 3,58); post hoc CUT − RAND_CUT −1,21° (−1,85; −0,62).
Red Team (własny): RAND/SCALE naruszają rekurencję LC×LC, CUT nie → wynik wskazuje na rekurencję LC×LC, nie przesądza
o nieistotności AOTU; wzmocnienie nie tłumaczy (CUT ma niższe nachylenie, a mniejszy deficyt). PASS_WITH_LIMITATIONS.

### 2026-10-29 — Stabilność (DONE) — `v6_stability.py` → `results/v6_stability/`; Enkoder (DONE) — `results/v7_encoder_distance_20261029.txt`
Liczby w VALIDATION_PLAN (sekcja „Sesja autonomiczna 2026-10-29”).

### 2026-10-29 17:11 — integralność po pracy: Stage 1 28/28; zmiany tylko w flymind/; testy: 12 zestawów + T1–T9 zielone.
2026-10-29T17:12:09 ['FINAL-2026-10-29']
Stage 1 frozen hashes: 28/28; protocol True; manifest 2f061a60b1d34815

### 2026-10-29 20:52–20:55 — V5 v3: zgoda użytkownika, kontrola, zamrożenie, test dymny (FLYMIND-V5v3-r3)
- Zgoda użytkownika na protokół r3 (sha256 a0f098093b707ad9…). Stage 1 28/28. Manifesty V5 v2 i v5v2_topology = bieżący kod;
  manifest V5 v1 różni się w loop.py/visual_path.py/so101.py — znane, opisane wcześniej (dodatki z domyślnym zachowaniem bez zmian).
- Ziarna 3051–3100 i tasowania 203 051–203 100, 403 051–403 100: brak użycia (47 plików JSON + kod).
- Kompletność r3 vs kod: 17 własności, 5 zamian/krawędź, offsety ziaren, SESOI 1,0, perm 100 000 (3401), bootstrap 10 000 (3402),
  H1 bez korekty, H2/H3 Holm(2), warstwy ρ, limit 2 błędów/warunek — zgodne. Poza runnerem: zgodność kodu z manifestem
  (sprawdzana przed/po) i opisowe nachylenia kalibracji (`v5v3_post_slopes.py`).
- Zamrożenie: `validation/v5v3_protocol.md` (= DRAFT r3 bajt w bajt), `validation/v5v3_manifest.json`, `validation/v5v3_frozen_code/` (18 plików).
- Test dymny: ziarna dev 1291–1292 → scratchpad (`v5v3_smoke`), łańcuch działa, wynik nieanalizowany.
- Przed przebiegiem: kod = manifest, kopia = manifest, protokół OK, dane bez zmian, Stage 1 28/28 (`results/v5v3_run_integrity.txt`).
- Przebieg: `.venv/bin/python -I -B flymind/v5v3.py --seeds 3051-3100 --out flymind/results/v5v3 --approved-protocol-sha256 a0f098093b707ad9ccd06a9cc5989031d63f3a88fa1d22438144d4f4220cb2a8` — uruchomiony 20:55.
- Przygotowane przed zobaczeniem wyników: `v5v3_post_slopes.py`, `audit_v5v3_independent.py` (przetestowany na teście dymnym).

### 2026-10-29 21:07 — V5 v3 wynik (DONE)
- Przebieg zakończony (exit 0), 250 prób, 0 błędów symulatora, 0 wykluczeń. Po przebiegu: kod = manifest, protokół i dane bez zmian,
  Stage 1 28/28, zmiany tylko w flymind/ (`results/v5v3_run_integrity.txt`).
- H1 DATA − SWS v2: −0,19° (CI95 −0,58; +0,16; CI90 −0,51; +0,10), p 0,33 → równoważne w granicach SESOI → „Hipoteza nie została potwierdzona.”
  H2 DATA − SHUF_STR −2,40° (−3,43; −1,45), H3 SWS − SHUF_STR −2,21° (−3,07; −1,42), p_Holm 2·10⁻⁵. D1 −1,25°, D2 +5,64°.
  Warstwy H1: +0,53 / −1,02 / −0,47°. Nachylenia: SWS 492–495, SHUF_STR 59–157 Hz/rad. Niezależna reanaliza: te same decyzje.
- Red Team: PASS_WITH_LIMITATIONS (szczegóły w VALIDATION_PLAN). Weryfikacja zarzutu skali (`v5v3_gain_check.py`, dev 1501–1520):
  ~45 % H2 to skala sygnału — POTWIERDZONE.
- Otwarte (PLANNED, wymagają nowej puli ziaren i zgody): TOST per warstwa przy ρ < 0,28 (±0,5°); pętla przy stałym napędzie;
  SHUF_STR z własną kalibracją jako warunek potwierdzający.
2026-10-29T21:24:11 ['V5v3-FINAL']
Stage 1 frozen hashes: 28/28; protocol True; manifest 2f061a60b1d34815

### 2026-10-29 21:50– — V5 v4 (polecenie użytkownika: protokół, Red Team, potwierdzenie po bramkach) — IN_PROGRESS
- Etap A (`V5v4_STAGE_A_AUDIT.md`): Stage 1 28/28; V5 v3 kod = manifest = kopia; reanaliza V5 v3 zgodna; 12 zestawów testów + T1–T9 zielone;
  pule 4001–4450, 5001–5010, 6001–6010 (+ offsety) wolne. Nowe zasady: zakaz ziaren 1001–1999 → nowe pule kalibracyjna 5001–5003 i dev 6001–6010.
- Etap B/C: `v5v4.py` (r1), `test_v5v4.py`, moc `v5v4_power.py`; kalibracja deterministyczna (DATA 492,1, TOY 306,1 Hz/rad).
- Etap D, Red Team r1 (osobna instancja modelu — ograniczona niezależność): NOT READY, 3 MAJOR: M1 błędne uzasadnienie ρ < 0,28
  (POTWIERDZONE moim renderem `results/v7_encoder_distance_az_20261029.txt` — napęd rośnie z |az|); M2 krucha moc; M3 brak ujawnienia
  replikacji dev RT V5 v3 i ryzyka kancelacji w S2. 11 MINOR.
- r2: protokół i runner przepisane (r1 zachowane), n 150/300, `v5v4_power_r2.py`, testy 21 asercji zielone. Red Team r2 — w toku.
- Red Team r2: READY (0 BLOCKER/MAJOR, 9 MINOR); poprawione N1, N2, N6–N9 (runner r2 zachowany), protokół r3. Red Team r3 (wąski, diffy): READY, 3 MINOR
  (M-a/M-b rozwiązane procedurą w §9; M-c kosmetyka). Wszystkie raporty RT: osobna instancja modelu — ograniczona niezależność.
- 22:1x: rejestr ziaren `validation/v5v4_seed_registry.md`; zamrożenie FLYMIND-V5v4-r3: `validation/v5v4_protocol.md` (sha f648c7ea…),
  `validation/v5v4_manifest.json`, `validation/v5v4_frozen_code/` (18 plików). Test dymny 6001–6002 → scratchpad (VALID, łańcuch OK);
  zamrożone artefakty bez zmian przed i po teście. Stage 1 28/28 przed przebiegiem (`results/v5v4_run_integrity.txt`).
- 22:18: start shardów A (4001–4225) i B (4226–4450) w tle. Przygotowane przed wynikami: `v5v4_post_sws_slopes.py`, `audit_v5v4_independent.py`.

### 2026-10-30 07:37 — V5 v4 ZAKOŃCZONE (PASS_WITH_LIMITATIONS) — `V5v4_FINAL_REPORT.md`
2700/2700 prób, 0 błędów, 0 wykluczeń, oba shardy VALID; Stage 1 28/28 po; kod V5 v4 i V5 v3 = manifesty. H1: S1 +0,51° (kontrola lepsza),
S2 −0,52° (DATA lepsza), p_Holm 2·10⁻⁵; H2a −1,38°, H2b +1,41°; P lepszy o 2,68°. Reanaliza niezależna zgodna. Nachylenia SWS 0,988–1,005 × DATA.
Otwarte (PLANNED, wymaga zgody): Red Team wyników V5 v4; kontrola rozdzielająca motywy bloku LC10a×LC10a (np. zachowująca wzajemność).

## Programme V5 v4.1 → V7 (2026-10-30, long autonomous mission; English entries)
Central documents: `program_v5v41/` (SEED_REGISTRY.md, RECON_SUMMARY.md, V5v41_PROTOCOL.md + AMENDMENT_A1, V5v42_PROTOCOL.md, later
V6/V6.1/V7 protocols, FINAL_REPORT). Integrity tool `integrity_v5v41.py` (Stage 1 + manifests + 377 protected files).

### 2026-10-30 08:32–08:50 — reconnaissance, integrity, V5 v4.1 launch
- Baseline integrity: Stage 1 28/28, v5v3/v5v4 manifests 18/18, protected tree dfcabd78f1484c96 (`results/v5v41/integrity_baseline.json`).
- Recon workflow (4 independent read-only auditors) → `results/v5v41/recon/A–D`; my verified corrections in `program_v5v41/RECON_SUMMARY.md`
  (P better 446/450 not 450/450; V5 v4 calibration is a near-saturation large-signal slope; effective membrane noise ≈ 0.32 mV SD;
  "SWS weaker at 6–9 mV" not stated anywhere, ≤ 6-instance artifacts show weaker at 6–7.8 and stronger at 8–10 mV).
- New pools registered before any run (8 41x xxx – 8 70x xxx; collision scan 0 hits).
- V5 v4.1 protocol r1 sha dc569e02…; runner `v5v41.py` (tests 8/8, bit-identical to alif.ALIF); 50 SWS instances: all 17 properties,
  50 distinct W, pairwise changed-edge Jaccard 0.13–0.14, LC×LC reciprocal pairs 511–604 (DATA 2450). Main run started 08:39.
- Amendment A1 (E6 symmetric operating point, sha 59104af9…) written before any main-run result was inspected; E6 run started.
- `block_shuffle.py` (tests 7/7; ALL == SWS bit-exactly) and V5 v4.2 protocol r1 written before v4.1 results.
- `cl_runner.py` (tests 6/6, MuJoCo, smoke seeds): parameter injection into frozen loop.run_trial; DATA calibration with new seeds
  8 601 001–003 = 496.46 Hz/rad (frozen V5 v4: 492.12).

### 2026-10-30 09:12–09:50 — V5 v4.1 DONE (PASS_WITH_LIMITATIONS) — `results/v5v41/REPORT.md`
- E1: SWS DNa02 ipsi −18.0 Hz vs DATA over 6–10 mV (CI −18.8; −17.2), 0/50 instances ≥ DATA; reverses at 10.5–11 mV; thresholds
  +0.09/+0.17 mV; LC10a mean rate equal; noise 0 shrinks the effect (−6.9). E6 small-signal gain DATA higher at 6–7 mV, SWS at 10.
- RT (3 agents): RT2 PASS (bit-exact re-sim, swap dose-response → 0), RT1 PASS_WITH_LIMITATIONS (SD_between noise-level; ρ 0.59
  withdrawn; E6 robust only 6–7 & 10 mV), RT3 FAIL of my "downstream of LC10a" reading → corrected: LC10a synchrony (Fano 38.9 vs
  11.3, verified) is the best correlate; locus unresolved.
- V5 v4.2 analysis amendment A2 (sha d710e3fe…) — synchrony mediators — written before any v4.2 dynamics result was opened.
- V6 protocol sha 4d195e87…; V6 calibration (seeds 8 601 001–003): D0 496.5, BA0 516.0, BA1 176.9, TH6 530.7, TH8 436.1, J015 400.6,
  J025 553.8, SG6 472.2 Hz/rad. V6 closed loop (DATA/SWS/P) started on 2 workers 09:2x; v4.2 dynamics started 09:15.

### 2026-10-30 10:35–12:40 — V5 v4.2 DONE (PASS_WITH_LIMITATIONS), V6 closed loop DATA/SWS done, V5 v4.3 run
- v4.2 (`results/v5v42/REPORT.md`): B1 LC×LC alone gives ~94 % of the SWS open-loop deficit (−16.4 vs −17.4 Hz) and the full LC10a
  synchrony; B2–B4 −0.9…−1.8 Hz ("partial/unresolved"); B5 = SWS. RT1/RT2 PASS_WITH_LIMITATIONS; RT2 pilot: reciprocity-preserving
  LC×LC shuffle still synchronous (reciprocity minor). Wording corrected (value- not bit-identical, additivity unresolved).
- V6 rule → family X = B1. V6 open loop (16 configs × DATA + 50 SWS + 25 B1) running (slow, ~4 h). V6 closed loop DATA/SWS/P 2040
  trials done, 0 errors; B1 closed-loop trials appended (running). V6.1 queued after B1 closed loop.
- V5 v4.3 (new stage, protocol sha 5de36553…): LC10a replay into DATA network, identity replay exact for 11/11 sources; circular-shift
  / Poisson surrogates shrink the B1−DATA DNa02 gap from −19.9 to −1.7 / −2.1 Hz → timing route supported (pre-registered rule).

## 2026-10-30 14:25–14:45 — V6 parameter study analysed; V6.1/V7 queued; new user request → V6m mechanism study
- V6 (parameter study) complete: open loop 15 configs × 76 networks + D0 from v4.1; closed loop 3000 trials, 0 errors. Analysis run
  (`v6_analysis.py`), figures, DRAFT report `results/v6/REPORT.md`; red team (2 agents, workflow wf_62e601b4) launched.
  Key: open-loop SWS deficit near threshold in all non-ceiling configs except σ 6 (Δ own +0.5 Hz, LC10a Fano equal — post hoc);
  closed-loop d small (|d| ≤ 0.66°, none shown > SESOI), sign configuration-dependent; Q8 Spearman S1 −0.12, S2 +0.19 (n = 8).
  b_a = 0 cells hit the 250 Hz ceiling → their interaction contrasts are not interpretable.
- V6.1: restarted from 2 → 8 workers (resumable JSONL, 88 records kept, verified parseable); toy-relay reference (§2) run
  (`v61_toy.py`). Analysis script `v61_v7_analysis.py` written before V6.1/V7 results; V7 protocol hashed (969139e8…) and V7
  queued to start after V6.1.
- User message (14:3x): mechanistic dissection of the DNa02 response to synchronous LC10a input. Named **V6m** (results/v6m/) to
  avoid colliding with results/v6/. Engine facts checked first: DNa02 has no direct LC10a input; DNa02 → 21 intermediates
  (feedback) → DN-only test needs intermediates clamped (Exp 1c); subtractive reset at t_ref 2.2 is a null manipulation
  (v clamped during refractoriness) → Exp 5a paired with t_ref 0. Seed pools 8 440/8 441/8 442/8 498 registered (0 collisions).
  Synthetic-synchrony design pilot on smoke seeds → 10 Hz event grid chosen to reach B1's synchrony. Protocol sha b8cd8935…
  frozen before the smoke run; smoke used rep 1 of the main seeds and B1 8 421 001 (disclosed). Tests T1/T2/T5 OK; T3 (REF ==
  v4.3 V0) exact on smoke. Full run started 14:43; analysis script hashed 14:43 before results.

## 2026-10-30 14:45–15:50 — V6m results, red team falsifies the draft interpretation, V6m2 pre-registered follow-up
- V6m full run 14:43–14:56 (25 jobs, all validations true; T3 REF == v4.3 V0 exact for 11 sources). Analysis (one post-hash
  ordering bug fix, logged). Pre-registered rule outcomes (absolute gap): LCIRC removes most (F 0.94 / rep 0.80); DNa02 t_ref 0
  (intermediates clamped) "contributes" 21 % / 33 %; DNa02 b_a 0 enlarges; intermediate b_a 0 n.s.; intermediate circular shift
  contributes 36 % / 23 %; intermediate t_ref 0 enlarges; subtractive reset n.s. Exp 4: DNa02 falls monotonically with synthetic
  LC10a synchrony at fixed counts. Post-hoc Exp 6 (addendum A1): 10 % rate-weighted excitatory intermediate drive deficit for B1.
- My DRAFT interpretation ("two stages, neither DNa02 refractoriness; DNa02 timing route survives t_ref 0; candidate leak") was
  FALSIFIED by the red team (RT-A PASS_WITH_LIMITATIONS; RT-B, RT-C, RT-D NOT_READY):
  (1) RT-B and RT-D independently simulated the untested combination: with DNa02 t_ref 0, destroying intermediate synchrony
      ENLARGES the gap (interaction +11.1 Hz [+7.5; +14.7] and +14.4 Hz [+10.8; +18.3]);
  (2) removing the leak alone leaves the timing share unchanged (RT-D);
  (3) on the relative gap DNa02 t_ref 0 removes ~60 % ("removes most"); rate-matched check ~75 % (RT-D, exploratory);
  (4) parameter dependence: at b_a 1.0 t_ref 0 removes 76 % (abs), at J0 0.25 it enlarges the gap (RT-C).
- Response: V6m2 pre-registered DNa02-only factorial (protocol V6m2_PROTOCOL.md r2 sha f8faf355…; r2 = exact MASYNC sampler after
  the r1 sampler failed in the smoke run, no data seen): DNa02 dynamics {REF, T0, T0B rate-matched, T1, T6, NOLEAK} × intermediate
  input {M0, MCIRC, MASYNC} × arms {MAIN, BA1, J025}; primary = interaction Δt(REF) − Δt(T0B) on Hz and log-ratio, wider of percentile /
  jackknife-t CI. New seeds 8 443/8 444 registered (0 collisions). Bias calibrated −38 mV (MAIN). Run started ~15:50; analysis
  script hashed before results.
- V6 parameter-study report finalised after RT1/RT2 (27 fixes); V6.1 analysed (DRAFT report: sign of d governed by drive level);
  V7 running (1086/1440).

## 2026-10-30 15:33–17:20 — V6m2 result, V7 done, usage-limit interruption
- Timestamp correction (from file mtimes): V6m2 protocol r1 hashed 15:18:58, r2 15:21:30, analysis script hashed 15:24:37, run
  15:26:05–15:33:01. The "~15:35/~15:45/~15:50" in the previous entry and inside the hashed protocol text were wrong clock estimates
  (protocol file left unchanged to keep its hash); ordering protocol → analysis hash → run is confirmed by the files.
- V6m2 (pre-registered): H-RS SUPPORTED in MAIN on every criterion; interaction Δt(REF) − Δt(T0B) +21.2 Hz (+17.3; +25.0), log +0.55;
  generalises (BA1 +11.3, J025 +22.4, CIs excl. 0); NOLEAK no effect; 1 blocked step suffices (MAIN). Rate-matched t_ref 0 removes ~81 % of
  the gap (not a "refractory share": the synchrony term flips sign). Count route ~60–70 % with timing removed.
- V7 finished (1440 trials, 0 errors): G2 pattern holds both halves; G1 holds formally but loop mostly fails; G3 no difference; G4
  REVERSED. Draft reports for V6.1, V7, V6m2 written; V6m report rewritten after RT-A…D.
- Red-team workflows for V6m2 and V6.1/V7 failed on the session usage limit (no reviews written; partial scratch dirs only);
  relaunched 17:12 after reset.

## 2026-10-30 17:12–17:26 — red-team completion, corrected reports, final report
- V6.1 (RT61) and V7 (RT-7): NOT_READY on drafts (headline over-reach; drive-band claim contradicted by V7's own data; mis-specified drive
  model; provenance: v61_v7_analysis.py hashed 14:31:46, after the V6.1 run started) → reports corrected → PASS_WITH_LIMITATIONS.
- V6m2 (RT-E replication +22.1 Hz with an independent implementation; RT-F alternatives; RT-G statistics): PASS_WITH_LIMITATIONS;
  J025 T0B NOT rate-matched (calibration hit the −60 mV grid edge); operating regime can flip the synchrony sign (bias with block intact);
  gain matching makes the no-block synchrony effect ≈ neutral (I +7.4 n.s.); "1 step suffices" not robust → report corrected.
- V6m report aligned with corrected V6m2. FINAL_REPORT.md (A–K) written in program_v5v41/.
- Final checks 17:25: 6 test suites OK; integrity Stage 1 28/28, manifests 18/18 ×2, protected tree unchanged (377 files, 0 changed).

## 2026-10-30 17:2x–17:3x — V6m3 (user approved "Yes, run it")
- Protocol `V6m3_PROTOCOL.md` sha fbeeb64a… (hashed 17:29:21 with v6m3.py e4422fc4 and test_v6m3.py de438e74); analysis script
  4f1d675a hashed 17:30:19 after a dry run on smoke data (output discarded unseen). Seeds 8 445/8 446/8 499 registered (0 collisions).
- Part A (intermediates free; t_ref 0 with gain- and bias-matched intermediate rates) and Part B (DNa02-only 2×2 count-swap of real
  intermediate trains; REF primary, T0/T0G secondary); MAIN (B1 001–010) + REPLICATION (B1 011–020, new noise) at 8/9 mV.
- Tests V1/V4 OK; smoke OK (calibration within grids). Full run launched.
- 17:3x r1 crashed in REP B1 8 421 017 (count-swap: no ISI ≥ 4 slot); r2 fallback (any free 1-ms slot, counted; 5 spikes total) hashed
  17:33:46; 17 completed r1 jobs kept unopened, 4 rerun (+1 that crashed). 22 jobs OK, Stage 1 28/28.
- Results: H-IR SUPPORTED in MAIN and REP (intermediate refractoriness causes the ~11 % drive / ~8 % count deficit; removed under gain-
  and bias-matched t_ref 0); count-swap (real trains, DNa02 block intact): count −12.2 Hz, timing −10.9 Hz, count share 0.53 (0.46; 0.59),
  order-sensitivity range ~0.4–0.7 (BD needs 12 % added random spikes); DNa02 t_ref 0 removes the timing effect (also gain-matched).
  Red team (RT-H, RT-I) launched.
- 17:4x–17:58 V6m3 red team (RT-H, RT-I; both PASS_WITH_LIMITATIONS): QA net ≈ 0 is a cancellation (block explains the synchrony-dependent
  ≈ 60 %; non-synchrony residual persists); 18/22 r1 jobs (not 17); count share construction-dependent 0.36–0.53 (window mismatch + random
  addition bias the pre-registered 0.53 upward); T0G timing ≈ 0 averages opposite signs → V6m3 report corrected (20 items).
- FINAL_REPORT updated with V6m3; independent cross-check found 19 discrepancies + over-claims (carry-over of corrected stage claims,
  integrity labels not saved, protocol-hash record locations, V6m3 r1/r2, test count) → all fixed; integrity output now saved to
  program_v5v41/integrity_final_20261030.txt (17:56, Stage 1 28/28, 0 changed). Seed-registry timestamp erratum appended.
