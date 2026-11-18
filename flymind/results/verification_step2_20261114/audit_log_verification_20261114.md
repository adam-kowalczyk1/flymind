# Niezależna weryfikacja raportu końcowego kroku 2 — log audytu (14 XI 2026)

Sesja weryfikująca: jedna (ta). Tryb: tylko odczyt i ponowne przeliczenia. Żadnych przebiegów symulacji do tej pory.
Nic nie zostało nadpisane; wszystkie pliki tej weryfikacji są w `flymind/results/verification_step2_20261114/`.
Bez commitów, bez zmian modułów wspólnych, bez robota, bez kodu Artificial Brains.

**STAN: ZATRZYMANE na warunku STOP nr 1 („ziarno testowe użyte więcej niż raz”) — patrz sekcja S. Tematy 3–11 NIE zostały
jeszcze sprawdzone.**

Oznaczenia: VERIFIED / PARTIALLY VERIFIED / REPORTED / INFERRED / HYPOTHESIS / NOT VERIFIED / FAILED / NOT IMPLEMENTED.

---

## Log kroków

| # | Co i dlaczego | Komenda / plik | Wynik |
|---|---|---|---|
| 1 | Przeczytać raport i logi źródłowe w całości | `reports/step2_final_report_20261114.md`, `step2_log_2026-11-13.md` (502 linie), `step2_log_2026-11-13_part5.md`, `SEED_REGISTRY.md`, `LOOP_TARGET_b_r2.md`, `lift_b.py` (cały) | przeczytane; `REPORT_b`, logi kroków 6–7, cele c/d/e/arm, `joint_net.py` — jeszcze nie w całości |
| 2 | Stan gita (zasada „bez commitów” i punkt odniesienia) | `git log -6`, `git show --stat HEAD`, `git status --short` | HEAD = `19db7eb` z 14 XI 09:01:59 (lokalny, gałąź 1 commit przed `origin`, bez push): commit kroku 2 + zaległych etapów. Raport (05:12) pisze „nic nie zostało zacommitowane” — prawdziwe w chwili pisania, nieaktualne od 09:01. Brak zmian w plikach śledzonych po commicie |
| 3 | Hashe plików celu, kalibracji, rejestru i skryptów kontra hashe w logach | `shasum -a 256 …`, `stat -f '%SB %Sm'` | Zgodne z logami: `LOOP_TARGET_b_r2` 17428a12…, `c_r1` 39814eb1…, `d_r1` eb0e983c…, `e_r1` 5c7cb5dd…, `arm_r1` e4d6d4b3…, `CONFLICT_TARGET_r1` e1746e72…, `CALIBRATION_k_SIGNS` a2a3fa41…, `joint_net.py` ad332dce…, `lift_b.py` 182f1467…, `lift_b_pin.py` 2e6e0698…, `demo_arm.py` 4312db6a… — VERIFIED. Czas utworzenia = czas modyfikacji dla wszystkich plików celu (nie były zmieniane po utworzeniu) |
| 4 | Inwentarz wszystkich plików wyników (ziarna, tasowania, liczba prób, hash W, hashe kodu, czasy) | `v01_inventory.py` → `inventory.json` | 274 pliki JSON, w tym 228 z listą prób; każda seria ma ziarna prób = ziarno·1000 + indeks·10 + poza, bez powtórzeń wewnątrz pliku |
| 5 | Użycie ziaren: serie na katalog, ziarna tasowań, duplikaty konfiguracji, pliki niepełne | `v02_seed_use.py` | wyniki w sekcji S |
| 6 | Zachowane katalogi robocze obu sesji (skrypty uruchomień, logi przerwanych przebiegów) | `/private/tmp/claude-501/…2phfos/369d1f0a…/scratchpad` (sesja B, staw b), `…vu2mUR/e68121d3…/scratchpad` (sesja A, c–e/ramię) | Znalezione: `run_test.sh`, `run_dt01.sh`, `run_dt01_chunks.sh`, `test_dt01_single_killed/*.log`, `launch_arm0.sh`, `launch_test.sh`, `launch_conflict.sh`, `run_b_it1.out`, `jn_test/` |
| 7 | Niezależna oś czasu: znaczniki czasu wywołań narzędzi w zapisach obu sesji (`~/.claude/projects/-Users-admin-so101-fly-project/369d1f0a….jsonl`, `e68121d3….jsonl`) | `v03_transcript_timeline.py` (z różnymi wzorcami) | czasy w sekcjach S i P. Ograniczenie: to zapisy tych samych sesji (niezależne od treści logów, ale nie zewnętrzny notariusz) |
| 8 | Odtworzenie rejestru ziaren z 18:13:59 przez cofnięcie jedynej późniejszej edycji (19:26:48) | skrypt w linii (hashlib) | sha256 = `f303f742a341a3e5b812c5c2f5288e5deee55afd9351ba078e2f79feafd0f772` = hash z logu §5.2.8 — VERIFIED |
| 9 | Czy sesje używały nawzajem swoich ziaren | `v03_transcript_timeline.py 'seed 20[12]01…'` itd. | sekcja S, pkt 4 |
| 10 | Co mówi zatwierdzony plan o dt 0,1 ms i „raz” | `grep` w plikach celu i `REPORT_b` | `LOOP_TARGET_b_r2` §8.4: „test końcowy (20201, 135 prób, raz) dla najlepszej wersji + sprawdzenie dt 0,1 ms (tylko N, oba Glu)”; `LOOP_TARGET_c_r1` l. 5: „0,1 ms raz na końcu: tylko N, oba Glu”. Plan NIE mówi, na jakich ziarnach ma być sprawdzenie dt 0,1 ms |

---

## S. Temat 1 — ziarna testowe (ZAKOŃCZONY; tu zadziałał warunek STOP)

### S1. Testy główne — każdy zakres użyty raz — VERIFIED
`inventory.json` / `v02_seed_use.py`: katalogi `lift_b/test` (20201), `elbow_c/test` (20401), `wrist_d/test` (20601),
`roll_e/test` (20801), `whole_arm_5/test` (20901) mają po 17 plików × 135 prób (N, S1–S5, R, K × Glu ±1 + K0), jeden plik na
konfigurację, 135 różnych ziaren prób w każdym. Ziarna tasowań testowych (20 x10 001–005) występują wyłącznie w katalogach
`test` swojego stawu. `conflict_7/test` (20971): 4 pliki N × 135 prób + 20 plików S × 45 prób (tasowania 20 980 001–005).

### S2. Te same sceny testowe użyte ponownie w sprawdzeniu dt 0,1 ms — STWIERDZONE (pliki)
| Staw | Katalog | Ziarno | Próby | Kiedy |
|---|---|---|---|---|
| (b) | `lift_b/test_dt01/` (18 kawałków po 5 prób) | 20201, poza 0 | 45 na Glu, tylko N | 14 XI 01:37–03:44 |
| (c) | `elbow_c/dt01/` | 20401, poza 0 | 45 na Glu, tylko N | 13 XI 22:36 – 14 XI 03:58 |
| (d) | `wrist_d/dt01/` | 20601, poza 0 | 45 na Glu, tylko N | do 14 XI 02:50 |
| (e) | `roll_e/dt01/` | 20801, poza 0 | 45 na Glu, tylko N | do 14 XI 03:31 |

Było to zapowiedziane przed testem: (b) log T.4 (wpis 21:06:12, `run_test.sh` 21:02:40, pierwszy plik testu 21:11:34) i
`run_dt01.sh` („sceny testowe poza 0”); (c–e) log §5.12 (wpis 20:37:00). Ujawnione w `REPORT_b` (§5) i w logach.
W raporcie końcowym jest tylko „45 scen” / „45 scen, poza 0” — bez słowa, że to ziarna testowe. Sformułowanie raportu §2
„ziarna testowe użyte raz” jest więc **za mocne**: raz w teście głównym, drugi raz (ramię N, poza 0) w sprawdzeniu dt 0,1 ms.

### S3. (b): część scen testowych przy dt 0,1 ms policzona DWA razy — STWIERDZONE (pliki + zapis sesji)
`run_dt01.sh` uruchomiony 13 XI 23:23:50 (jeden proces na Glu), zabity 14 XI 01:37:34 (`dt01_run.out`, zapis sesji B),
potem ten sam zakres uruchomiony od nowa w 18 kawałkach (`run_dt01_chunks.sh`). Zachowane logi przerwanego przebiegu
(`…/scratchpad/test_dt01_single_killed/`): Glu −1 — 4 próby, Glu +1 — 6 prób (wszystkie 6: lift True, Δz 33–45 mm).
Te 10 scen testowych zostało więc policzone przy dt 0,1 ms dwukrotnie. Wyniki przerwanego przebiegu NIE wchodzą do
`compare_g±1.json` (skrypt `compare_dt01.py` czyta tylko `lift_b/test_dt01/*.json`), ale zostały użyte do porównania
„kawałki = pojedynczy przebieg” (log T.10) — czyli były oglądane. Rozbieżność w logu: T.8 podaje „2 i 5 prób”, T.10 i pliki: 4 i 6.

### S4. Incydent S1 / ziarno 20 910 001 — skutek: brak — VERIFIED
Zapis sesji A: `launch_arm0.sh` z `--shuffle-seed 20910001` uruchomiony 19:26:36, `pkill -f "shuffle-seed 20910001"` 19:26:48
(12 s później; budowa sieci tasowanej trwa ≥ 50 s). Logi w `whole_arm_5/it0_killed_testshuffleseed/` mają 0 bajtów, pliku JSON
nie ma. W tej samej komendzie (19:26:48) dopisano 20 952 001 do rejestru i uruchomiono powtórkę. `arm_it0_S1_g±1.json` mają
`shuffle_seed` 20952001 i inne hashe W (ff9f1fe2…, 0ae71acd…) niż S1 testu (0c971370…, d7b6cfe5…). Formalnie ziarno
tasowania testowego zostało „dotknięte” dwa razy (12 s przerwanego startu + test), bez żadnego wyniku z pierwszego razu.

### S5. Rejestr przed użyciem — VERIFIED (z zastrzeżeniem z kroku 7)
- (b): wiersze 20101/20201/tasowania wpisane 17:56:31 (ta sama komenda co `LOOP_TARGET_b_r2.md`); pierwszy przebieg (b) 17:59.
- (c–e), ramię, konflikt: wpisane 18:13:59 (hash odtworzony, krok 8); pierwsze przebiegi: (c) it1 18:16:03, (d) it1 18:17:04,
  piloty konfliktu 18:22, (e) it1 (pliki wyników 18:58–19:17; godziny startu nie sprawdzałem), ramię it0 19:26.
- 20 952 001: wpisane 19:26:48, przed powtórką (ta sama komenda).

### S6. Czy sesje dotknęły tych samych ziaren — ziarna testowe: NIE; treningowe (b): TAK — VERIFIED
Sesja A (c–e, ramię) użyła ziaren TRENINGOWYCH stawu (b) (20101 / 20 110 001–002) trzy razy: duplikat it1 (18:08:36, zabity
18:10:38), test równoważności i testy dymne `joint_net.py` (18:13:39, wyniki tylko w jej katalogu roboczym `jn_test/`), własna
iteracja 2 stawu (b) (18:16:03, zabita 18:21:59). Ziaren testowych (b) 20201 sesja A nie użyła ani razu; sesja B nie użyła
żadnego ziarna c–e, ramienia ani konfliktu.

### S7. Przerwane przebiegi (`*_killed`) — nie zostawiły wyników użytych w analizie — VERIFIED
`lift_b/it1_dup_killed/`, `lift_b/it2_session100bd1_killed/`, `whole_arm_5/it0_killed_testshuffleseed/` zawierają wyłącznie
pliki `.log` (10, 6, 2), żadnego JSON. Skrypty analizy (`analyze_b.py`, `analyze_joint.py`, `analyze_conflict.py`,
`compare_dt01.py`, `dt01_cmp.py`) czytają tylko `*.json` ze wskazanego katalogu. Pliki JSON `lift_b/it1/` powstały 18:07–18:15,
czyli z uruchomienia sesji B (18:02:19); duplikaty R/K sesji A zakończyły się od razu komunikatem „istnieje …” (logi 106–107
bajtów), duplikaty N/S zabito przed zapisem. Wyjątek opisany w S3 (log przerwanego dt 0,1 użyty do porównania zgodności).
`roll_e/test_analysis_PARTIAL_13of17files_*` to analiza zrobiona 22:35:53 na niepełnym teście (serie wstrzymane SIGSTOP, potem
wznowione) — nie przerwany przebieg; czy raport używa wersji pełnej — do sprawdzenia w temacie 3.

---

## P. Temat 2 — rejestracja przed testem (CZĘŚCIOWO; reszta nie sprawdzona)

Czasy zapisu z zapisów sesji (zgodne z czasami plików): `LOOP_TARGET_b_r2` 17:56:31 → (b) it0 17:59; `c_r1` 18:15:24 → (c) it1
18:16:03; `d_r1` i `e_r1` 18:16:52 → (d) it1 18:17:04; `arm_r1` 18:23:56 → ramię it0 19:26:36; `CONFLICT_TARGET_r1` 18:25:27 →
test konfliktu po 21:52. Hashe = hashe w logach. **PARTIALLY VERIFIED** (kolejność potwierdzona; treść reguł i dozwolone
zmiany — jeszcze nie oceniane).
Uwagi do sprawdzenia później: (1) piloty konfliktu (18:22–18:24) są sprzed pliku celu (ujawnione); (2) test dymny stawu 2
sesji A skończył się 18:14:18, a `LOOP_TARGET_c_r1.md` zapisano 18:15:24 — log §5.2.7 twierdzi, że wynik przeczytano po
zapisaniu celu: NOT VERIFIED; (3) log §5.18 podaje „ok. 01:55”, faktyczny wpis 01:36:43, start testu ramienia 01:38:36
(kolejność zgodna, godzina w logu błędna).

---

## Nie sprawdzone (tematy 3–11)
Przeliczenie liczb z surowych prób, spójność wyników, czujnik siły i kontrola pozytywna (nowe ziarna), 2593 vs 2916 vs 4100,
wniosek „dane, nie kod”, dt 0,1 vs 1 ms, reguła kroku 7, zasady (diff modułów wspólnych, stymulacja, etykiety), interfejs.
Obserwacje wstępne z czytania kodu, BEZ werdyktu: `ForceWorld` (`lift_b.py` l. 157–173) liczy tylko kontakty ramię↔blat
(etykiety z `oh.ARMSET`), raz na takt 10 ms, i raportuje `worlds[0]`; we wszystkich obejrzanych plikach `fmax_by_phase` = `{}`.
Wymaga sprawdzenia w temacie 5.
