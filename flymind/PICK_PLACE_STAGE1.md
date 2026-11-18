# FlyMind — Etap 1: powtarzalny cykl pick-and-place SO-101 (MuJoCo)

Data: 2026-11-09 · Branch `flymind/fly-first-control` · MuJoCo 3.17.0, NumPy 2.5.4, Python 3.12.13 z `.venv`
· pomiary historyczne (§7) wykonane na stanie roboczym nad commitem `54155d4`, kod zapisany w commicie `f0b6927`;
poprawki po dwóch audytach (§13, §15, §16) i powtórzone serie `*_postfix_v1` — w commicie następującym bezpośrednio po
`f0b6927` (jego skrót: `git log -1 -- flymind/pick_place.py`).

**Status: ZAMKNIĘTY WARUNKOWO jako baza symulacyjna** (nie „ukończony”). Rozbicie:
- dane benchmarkowe i klasyczny cykl w symulacji nominalnej — potwierdzone, także poprawionym kodem (§16);
- obsługa błędów — odzyskanie bez resetu, reset i zatrzymanie po błędzie bezpieczeństwa rozdzielone i przetestowane
  w symulacji (§15); część ścieżek nadal bez testu (§15.5);
- bezpieczeństwo — tylko programowe i tylko w symulacji; lista zabezpieczeń aktywnych / nieaktywnych / brakujących: §15.4;
- fizyczny SO-101 — nic nie zostało sprawdzone (§14); integracja z siecią muszki (SNN) — nie istnieje.

To jest **klasyczny kontroler**, nie sterowanie muszki: wszystkie komendy mają źródło `classical:pick_place`, a sieć
SNN nie bierze udziału w żadnej decyzji cyklu (wybór celu, IK, trajektorie, szczęka, potwierdzenie chwytu, przejścia
faz, recovery — wszystko w `pick_place.py`, `reach.py`, `grip.py`). Wyniki dotyczą wyłącznie symulacji MuJoCo.

## 1. Cel
Kompletny, powtarzalny cykl przeniesienia kostki między stałymi miejscami A i B, bez resetu symulacji między cyklami,
z pomiarem czasu, skuteczności i przyczyn porażek — baza techniczna dla Etapu 2.

## 2. Architektura (co nowe, co odziedziczone)

| Warstwa | Plik | Status |
|---|---|---|
| A. Scena: stół, kostka, znaczniki A/B | `flymind/so101.py` (`SceneCfg.cube_*`, `marks`, `reset(cube_pose=…)`) | **zmienione** — nowe pola opcjonalne; domyślny XML bez zmian (ten sam SHA-256 `13e65e9d…` przed i po) |
| B. Kinematyka i trajektorie | `flymind/reach.py` (`ik`, `plan`, `plan_joint`, `clearance`, `fixed_pad_target`) | odziedziczone, bez zmian |
| B. Profil prędkości/przyspieszenia | `flymind/pick_place.py::profile` | **nowe** — trapez v_max/a_max na staw |
| C. Szczęka | `flymind/grip.py::ClassicGrip` | odziedziczone, bez zmian (używane z `GripCfg(q_open=q_pre)`) |
| D. Bezpieczeństwo | `flymind/safety.py::SafetyLayer` | odziedziczone, bez zmian; każda komenda przez nie przechodzi |
| D. Monitory symulacji | `pick_place.py::Cell.tick` | **nowe** — kontakt ramienia ze stołem, flagi warstwy, zła komenda, niestabilność fizyki, zapas do krańców, max prędkość |
| E. Orkiestrator | `pick_place.py::Cell.cycle`, `recover`, `not_ready`, `reset_scene` | **nowe** |
| F. Pomiar i seria | `pick_place.py::series`, `summarize`, `main` | **nowe** |
| Testy | `flymind/test_pick_place.py`, `flymind/test_pick_place_faults.py` | **nowe** |
| Dowody | `flymind/results/pick_place/validation/` (logi, manifesty, skrypty: §16) | **nowe** |

## 3. Scena i obiekt (`PPCfg` w `pick_place.py`)
- Kostka 30 mm, 30 g (≈ PLA 1,1 g/cm³), tarcie 0,8 (PLA/guma), condim 4. Pady szczęk z `so101.py`: tarcie 1,2 (odziedziczone).
- A = (0,22; 0,10) m, B = (0,22; −0,10) m — 20 cm transportu. Znaczniki: płaskie krążki bez kolizji (tylko wizualne).
- Orientacja startowa kostki: ściany prostopadłe do kierunku zamykania szczęk w pozie chwytu nad A.
- Ziarno (seed) losuje raz na serię: masa i tarcie kostki ×U(0,9; 1,1), start kostki ±2 mm / ±3°. Fizyka sama w sobie
  jest deterministyczna (ten sam seed → identyczne czasy). **Sprostowanie:** wcześniejsze zdanie „potwierdzone dwoma
  przebiegami S0” nie ma dowodu w repozytorium — pliki pierwszego przebiegu `baseline_v1.0*` zostały usunięte (§12), więc
  porównania obu przebiegów nie da się dziś sprawdzić. Częściowy dowód z 2026-11-09: test P1.2
  (`test_pick_place_faults.py`) odtwarza pierwsze 2 cykle S0 dla seed 1 bit w bit z `S0_baseline.json`.
- Pozycja kostki jest czytana **ze stanu symulatora** (bez kamery) — patrz ograniczenia i §14.

## 4. Cykl (fazy i warunki przejścia)
Kostka jeździ tam i z powrotem: leży w A → cykl A→B, leży w B → cykl B→A. Każdy cykl startuje i kończy w pozie domowej.

| Faza | Co się dzieje | Warunek przejścia (inaczej `Fail(przyczyna)`) |
|---|---|---|
| start | rozpoznanie miejsca kostki (strefa 10 mm, obrót ≤ 10°, przechył ≤ 5°) | `object_lost` |
| approach | szczęka otwarta, ruch nad kostkę (6 cm), zejście pionowe; stała szczęka 4 mm od ściany, pady 7 mm nad stołem | `jaw_not_open`, `cube_pushed` (> 3 mm), `unreachable` |
| grasp | zamykanie do kontaktu obu padów (≤ 2 s), 0,1 s narastania siły | `no_contact`, `weak_grip` (< 1 N na padzie) |
| lift | podniesienie o 6 cm, nadzór chwytu co takt | `slip` (utrata kontaktu lub przesunięcie > 8 mm w układzie chwytaka), `lift_failed` |
| transport | prosta kartezjańska na stałej wysokości do nad B | `slip`, `cube_hit_table` |
| place | zejście (spód kostki 1 mm nad stołem), kontakt ze stołem, otwarcie do 0,55 rad | `place_no_contact`, `jaw_not_open`, `release_failed` |
| return | odejście 6 cm w górę, powrót do domu, sprawdzenie kostki w B | `release_failed` (kostka uniesiona), `place_out_of_zone` |
| każdy takt | warstwa bezpieczeństwa + monitory | `table_collision`, `safety_*`, `bad_command` (komenda odrzucona przez symulator), `sim_error` (NaN albo ostrzeżenie MuJoCo BADQPOS/BADQVEL/BADQACC, po którym MuJoCo samo resetuje stan) |

Po porażce cyklu możliwe są **trzy różne skutki** (pole `outcome`, szczegóły i klasy błędów w §15): `recovered` —
`recover()` wrócił do domu i stan został sprawdzony, następny cykl rusza bez resetu; `reset` — stanu nie potwierdzono,
seria teleportuje scenę i liczy to w `resets`; `halted` — zatrzaśnięty błąd bezpieczeństwa, seria staje.
Porażki nigdy nie są liczone jako sukces, a reset nie jest „odzyskaniem”.

**Plany liczone raz:** przy starcie `Cell` liczy pełne plany A→B i B→A (≈ 22 ms). Gdy kostka odbiega od nominału
> 1,5 mm lub > 2°, liczony jest od nowa tylko plan chwytu (≈ 3,4 ms; zmierzone), a transport/odłożenie/powrót są z cache.
W praktyce kostka po odłożeniu leży 1,5–3 mm od nominału, więc nowy plan chwytu był liczony w każdym cyklu.

## 5. Metryki
- `cycle_sim` — czas cyklu w **sekundach symulacji** (to odpowiada czasowi pracy robota w modelu). Liczony z
  `SO101Sim.sim_time` (od poprawki po audycie, §13): licznik narastający przez resety, bo `mj_resetData` zeruje `d.time`.
  Bez resetów `sim_time == d.time` bit w bit, więc wyniki z §7 się nie zmieniają.
- `cycle_wall` — czas cyklu w **sekundach zegarowych** tego Maca, bez renderowania. To jest szybkość obliczeń, nie robota.
- Czasy faz (sym. i zegarowe), `place_err_mm`, `tilt_deg`, `home_err_rad`, `start_drift_rad`, przyczyny porażek.
- Cykl nieudany: `t_to_fail_sim` (od startu cyklu do wykrycia błędu), `cycle_sim` (z ruchem `recover()`; sam reset
  trwa 0 s), `recover` (True albo powód niepotwierdzenia stanu) i `outcome` (`recovered` / `reset` / `halted`).
- Seria przerwana (zatrzaśnięty błąd bezpieczeństwa albo nieoczekiwany wyjątek): `complete = false`, `stopped_by` =
  powód; `main()` zapisuje ją jako `<tag>.INCOMPLETE.json` z kodem wyjścia 1 — nie jest serią udaną. Istniejącego
  pliku wyniku `main()` nie nadpisuje (nowa seria = nowy `--tag`).
- **Operacja** = jeden cykl: dom → chwyt kostki w miejscu, gdzie leży → przeniesienie na drugie miejsce → dom. Ta sama
  kostka kursuje A→B, B→A, …, a następny cykl zaczyna się tam, gdzie poprzedni ją odłożył. To **nie** jest ruch A→B
  z pustym powrotem po nową część ani podawanie nowych części; przepustowości nie wolno tak interpretować.
- Nieciągłość: `resets` (reset sceny przez serię), `auto_resets` (samoczynny reset MuJoCo), `continuous` = brak obu.
  Reset w symulacji trwa 0 s; czas ręcznej ingerencji na prawdziwym stanowisku **nie jest wliczany**, więc przepustowość
  serii z `continuous = false` jest zawyżona względem rzeczywistości.
- **Przepustowość (op/h) — dwie różne miary:**
  - raportowana w JSON i w §7: `udane operacje / łączny czas serii × 3600` (`ops_per_h_sim`, `ops_per_h_wall`). To jest
    przepustowość całej serii = 3600 / **średni** czas cyklu (gdy wszystkie cykle udane);
  - `3600 / mediana czasu cyklu` — przepustowość „typowego” cyklu; nie jest zapisywana w JSON, podana w §7 dla porównania.
  Obie liczone osobno dla czasu symulacji i zegarowego; czas zegarowy to szybkość komputera, **nie robota**.
- Statystyki serii: min / Q1 / mediana / Q3 / max, nie najlepszy cykl.

## 6. Uruchomienie

```bash
.venv/bin/python -I -B flymind/test_pick_place.py
```

```bash
flymind/results/pick_place/validation/run_validation.sh
```
(testy Etapu 1 z zapisem logu, ok. 15 s; `run_validation.sh regression` — inni użytkownicy `SO101Sim`, ok. 2 min;
`run_validation.sh mutation` — testy mutacyjne, ok. 2 min; to nie są benchmarki)

```bash
flymind/results/pick_place/validation/run_postfix.sh postfix_v2
```
(powtórzenie serii S0–S4 i S3×500 pod nowymi nazwami + porównanie ze starymi; sufiks musi być nieużyty)

```bash
.venv/bin/python -I -B flymind/pick_place.py --seeds 1 2 3 4 5 --cycles 50 --tag S0_baseline
```

```bash
flymind/results/pick_place/run_sweep.sh
```

```bash
.venv/bin/python -I flymind/results/pick_place/plot_variants.py
```

Opcje: `--v` (rad/s), `--a` (rad/s²), `--q-pre` (rozwarcie szczęki), `--home` (6 kątów), `--tag`. Wynik:
`flymind/results/pick_place/<tag>.json` (konfiguracja, git commit, SHA-256 plików kodu, wersja MuJoCo, parametry
fizyczne na seed, każdy cykl) + `<tag>_stdout.txt`.

## 7. Wyniki (źródło: `flymind/results/pick_place/*.json`)

Ziarna 1–5 × 50 cykli = 250 prób na wariant, te same warunki. Czas: s symulacji, chyba że napisano inaczej.

Kolumny przepustowości (§5): **„op/h seria”** = udane / łączny czas serii × 3600 = 3600 / średni cykl — to liczba
zapisana w JSON (`ops_per_h_sim`); **„3600/med”** = przepustowość typowego cyklu z mediany (przeliczone z tych samych JSON).
„op/h zegar” = szybkość komputera liczącego fizykę bez obrazu, nie robota.

| Wariant | Sukces | Cykl min / med / max | Średni cykl | op/h seria (czas sym.) | 3600/med (czas sym.) | op/h zegar | Błąd odłożenia med / max | Interwencje warstwy bezp. |
|---|---|---|---|---|---|---|---|---|
| S0 bazowy (v 1,0; a 4; szczęka 0,93; dom z `test_reach`) | 250/250 | 9,07 / 9,15 / 9,19 | 9,150 | 393,4 | 393,4 | 20 725 | 1,82 / 2,09 mm | 0 |
| S1 v 1,45; a 8 | 250/250 | 6,84 / 6,92 / 6,95 | 6,918 | 520,4 | 520,2 | 26 604 | 2,52 / 3,12 mm | 0 |
| S2 = S1 + szczęka 0,65 | 250/250 | 6,52 / 6,55 / 6,86 | 6,549 | 549,7 | 549,6 | 27 896 | 2,51 / 3,12 mm | 0 |
| **S3 = S2 + dom nad środkiem A–B** | **250/250** | **5,12 / 5,17 / 5,46** | 5,159 | **697,8** | 696,3 | 33 784 | 2,56 / 3,10 mm | 0 |
| S4 = S3 przy v 1,0; a 4 | 250/250 | 6,70 / 6,77 / 7,05 | 6,751 | 533,2 | 531,8 | 26 120 | 1,78 / 2,07 mm | 0 |
| S3, ciągłość 500 cykli (seed 6) | 500/500 | 5,12 / 5,165 / 5,43 | 5,146 | 699,6 | 697,0 | 35 718 | 2,61 / 2,68 mm | 0 |

(Sprostowanie: mediana błędu odłożenia S4 to 1,78 mm — `S4_v1.0_jaw0.65_homemid.json`; wcześniej wpisano 1,80.)
Serie powtórzone poprawionym kodem (`*_postfix_v1.json`, §16) dają **te same liczby co do bitu** we wszystkich 1 750
cyklach, więc tabela dotyczy obu wersji kodu. „op/h” liczy operacje zdefiniowane w §5 (kostka kursuje A↔B).

„0 interwencji” znaczy: warstwa bezpieczeństwa nie musiała niczego przycinać, bo planer z założenia mieści się w limitach;
kontrole `cmd_timeout` i `vision_stale` są w tym cyklu nieaktywne konstrukcyjnie (znacznik czasu komendy = chwila
sprawdzenia, wiek obrazu 0). To nie jest dowód, że system jest bezpieczny.

Mediany faz S0 → S3 [s]: podejście 2,39 → 0,985; chwyt 1,17 → 0,79; podniesienie 0,64 → 0,45; transport 1,305 → 0,92;
odłożenie 1,21 → 1,02; powrót 2,43 → 0,985.

Ciągłość: we wszystkich seriach 0 resetów; odchyłka ramienia na starcie cyklu ≤ 0,0005 rad (taka sama w cyklu 1 i 500);
błąd odłożenia się nie kumuluje (mediana pierwszych/ostatnich 100 cykli: 2,61 / 2,52 mm). Najmniejszy zapas do krańca
stawu: 0,115 rad. Max zmierzona prędkość stawu: 0,89 rad/s (v 1,0) i **1,371 rad/s** (v 1,45; seria 500 cykli; w seriach
250 prób 1,345–1,356). To prędkość **zmierzona** pięciu stawów ramienia (bez szczęki), próbkowana co 10 ms; limit 1,5
rad/s warstwy bezpieczeństwa dotyczy **komend** (przyrostu celu na takt), nie zmierzonego ruchu. (Sprostowanie:
wcześniej podano 1,36 rad/s — zaniżone.)

Wykres: `flymind/results/pick_place/variants.png`.

**Wnioski z optymalizacji.** Największy zysk dała poza domowa bliżej miejsc pracy (S2 → S3: −1,4 s), potem prędkość
(S0 → S1: −2,2 s) i mniejsze rozwarcie szczęki (−0,4 s). Szybszy ruch ma koszt: błąd odłożenia rośnie z ~1,8 do ~2,6 mm
(max 3,1 mm), wciąż w strefie 10 mm. Skuteczność nie spadła w żadnym wariancie. Wariant do dalszych prac: **S3**; S0
pozostaje domyślną konfiguracją kodu (testy jej używają).

**1500 op/h nie osiągnięto.** Najlepszy zmierzony wynik: 697,8 op/h czasu symulacji z łącznego czasu serii S3 (średni
cykl 5,159 s; seria 500 cykli: 699,6 op/h, średni cykl 5,146 s). Z mediany (5,17 s) wychodzi 696,3 op/h. 1500 op/h
wymagałoby cyklu 2,4 s. Wartości „op/h czasu zegarowego” (20–36 tys.) mówią tylko, jak szybko liczy komputer — nie są
wydajnością robota.

## 8. Testy (`flymind/test_pick_place.py`, ok. 2 s)
T1 profil (koniec, |Δq| ≤ v·dt, |Δ²q| ≤ a·dt²) · T2 scena (wymiary, masa, znaczniki bez kontaktu) · T3 jeden cykl faza po
fazie · T4 6 cykli bez resetu, przełączanie kierunku, brak dryfu · T5 kostka 6 mm od A → nowy plan chwytu, sukces ·
T6 kostka „niewidoczna” dla szczęk → `no_contact` · T7 śliska kostka (tarcie 0,05) → porażka chwytu/podniesienia ·
T8 kostka obrócona 30° → `object_lost` bez ruchu. W T6–T7 `recover()` ma zwrócić True (stan potwierdzony), w T8 ma
zgłosić zgubioną kostkę (`cube_lost`, nie True); we wszystkich trzech ramię ma stać w domu (< 0,02 rad).

Po audycie dodano `flymind/test_pick_place_faults.py` (P1.1–P1.4: pomiar czasu przy resetach; P5: siedem ścieżek
błędów) — opis w §13. **Trwały log** wszystkich testów (T1–T8, nowe testy, `test_reach.py`, `test_safety.py`,
`test_so101.py --zgoda-sim`): `flymind/results/pick_place/validation/validation_*.log`, tworzony przez
`flymind/results/pick_place/validation/run_validation.sh`. Wcześniejsza deklaracja „8 testów i stare testy przechodzą”
(sprzed audytu) nie miała zapisanego logu — jej dowodem jest dopiero log z 2026-11-09 (po poprawkach kodu).

Logi referencyjne po poprawkach P1 (HEAD `f0b6927` + zmiany niezacommitowane w chwili testu; skróty kodu w logach,
zgodne z plikami w commicie — §16): `validation/validation_20261109_210553.log`, `regression_20261109_210604.log`,
`mutation_20261109_210817.log`. Testy są skryptami z asercjami: plik kończy się przy pierwszej niezaliczonej asercji (kod wyjścia ≠ 0),
więc kod 0 oznacza wykonanie wszystkich; pojedyncze testy `test_pick_place.py`, `test_reach.py` i `test_safety.py`
nie mają własnych linii w logu (jedna linia „OK” na plik).

| Plik | Testy nazwane | Wynik w logu |
|---|---|---|
| `test_pick_place.py` | T1–T8 (8) | zaliczone, kod 0 |
| `test_pick_place_faults.py` | P1.1–P1.5 (5), ścieżki błędów P5 (9), R1, S1–S4 (4), W1–W2 (2) = 21 | zaliczone, kod 0 |
| `test_reach.py` | T1–T5 (5) | zaliczone, kod 0 |
| `test_safety.py` | 1 plik, 21 asercji | zaliczone, kod 0 |
| `test_so101.py --zgoda-sim` | T1–T9 (9) | zaliczone, kod 0 |
| **razem (walidacja)** | 5 plików: 43 testy nazwane + 1 plik asercji; niezaliczone 0; pominięte 0 | |
| regresja: `test_cl_runner.py` (6), `demo/test_demo.py` (T1–T10) | każdy 2×: z bieżącym i z zamrożonym `so101.py` | 4/4 kod 0, wyjścia identyczne (§16) |
| mutacje: `validation/mutate.py` | 20 mutacji jednej zmiany kodu | 20 wykrytych, 0 niewykrytych |

Wcześniejsze logi (`validation_20261109_193810.log`, `validation_20261109_194124.log`) dotyczą kodu sprzed poprawek P1
(34 = 33 testy nazwane + 1 plik) i zostają jako historia.

## 9. Ograniczenia i znane problemy
1. **Pozycja kostki ze stanu symulatora**, nie z kamery — w fizycznym robocie potrzebna percepcja (Etap 2+). Pełne
   zestawienie kontroli korzystających z danych tylko symulacyjnych: §14.
2. **Skuteczność 100 % dotyczy idealnego modelu**: brak szumu czujników, luzów, błędów kalibracji, opóźnień serw.
   Losowość per seed jest tylko w masie/tarciu (±10 %) i ustawieniu startowym (±2 mm/±3°). Na prawdziwym SO-101 należy
   spodziewać się gorszych wyników.
3. Ścieżki obsługi błędów zostały sprawdzone tylko na awariach wywołanych w testach (T6–T8 oraz
   `test_pick_place_faults.py`, §13 i §15); w seriach żadna porażka nie wystąpiła. `object_lost` wymaga resetu
   (automatycznego w serii, liczonego). Po `table_collision` `recover()` celowo nie rusza ramienia — seria robi jawny
   reset (na sprzęcie: ręczna ingerencja).
4. Kolizje ze stołem wykrywane są kontaktami w symulatorze (wyrocznia niedostępna w realnym robocie) i kontrolą odstępu
   padów w planie; warstwa bezpieczeństwa nadal nie ma geometrii kartezjańskiej (jak w `safety.py`). Kolizje siatek
   chwytaka i ruchomej szczęki są wyłączone (`so101.py`, kontakt tylko przez pady), więc monitor nie widzi korpusu
   chwytaka — czy przenikał stół lub kostkę: NOT VERIFIED. (Siatka silnika w chwytaku i pozostałe człony ramienia
   mają kolizje włączone.) Monitor cyklu sprawdza tylko kontakt ramienia ze stołem i tylko raz na takt 10 ms; kontakt
   ramienia z kostką jest sprawdzany dopiero przy potwierdzaniu stanu po porażce (`not_ready()`), a samokolizji ramienia
   nikt nie śledzi.
5. Przyspieszenie jest ograniczone tylko w **komendach** i tylko na prostych odcinkach ścieżki w stawach (a_max 4–8
   rad/s², test T1 sprawdza jeden odcinek prosty); na załamaniach ścieżki ograniczenie nie jest gwarantowane ani
   zmierzone. **Zmierzone** przyspieszenia stawów (różnice prędkości co 10 ms) sięgają 62–102 rad/s². Przyczyna
   jest **niepotwierdzona**: przypuszczalnie stany przejściowe serw pozycyjnych i kontaktów, ale nie ma pomiaru, w której
   fazie i na którym stawie występują szczyty. Nie istnieje żaden limit ani kryterium porażki dla przyspieszenia
   rzeczywistego; warstwa bezpieczeństwa go nie ogranicza.
6. Kostka kładzie się 1,5–3 mm od nominału (szczęka dociska ją do stałego padu, kostka lekko się przechyla ~3,5° w chwycie),
   więc plan chwytu liczony jest w każdym cyklu (3,4 ms); transport/odłożenie/powrót są z cache.
7. Tylko kostka 30 mm. Kula nie była testowana w cyklu (istniejący `test_reach.py` podnosi kulę).
8. Chwyt trwa 0,8–1,2 s głównie przez prędkość zamykania szczęki przy momencie 0,5 N·m (`GripCfg`, nie zmieniane).
   **Szczęka w modelu jest silnikiem momentowym**: `so101.py` zastępuje pozycyjny aktuator producenta silnikiem
   (`gear` 3,35 N·m, `ctrl` ∈ [−1, 1]), a `grip.py` zadaje stały moment: zamykanie +0,5 N·m, trzymanie +0,4 N·m,
   otwieranie −0,5 N·m do kąta `q_open`, potem 0 (limit warstwy 1,0 N·m). Prawdziwe serwo STS3215 nie daje
   skalibrowanego sterowania momentem w N·m — siła chwytu z symulacji nie przenosi się na sprzęt (§14).
9. Poza domowa S3 (`--home`) została wyznaczona IK raz (cs_fixed nad (0,22; 0; 0,10) m) i wpisana do `run_sweep.sh`.

## 10. Decyzje techniczne
- Kostka zamiast kuli (stabilna, nie toczy się). Prowadzenie **stałej** szczęki (jak `test_reach`), bo ruchoma obraca się.
- Nowy kod w jednym pliku `pick_place.py`; scena rozszerzona w `so101.py` polami opcjonalnymi zamiast kopii sceny.
- Kontrola poślizgu w **układzie chwytaka** (pierwsza wersja w układzie świata dawała fałszywy „slip” przy obrocie bazy).
- Zwolnienie = oba pady bez kontaktu i szczęka ≥ 0,55 rad, a nie pełne otwarcie (oszczędza ok. 1 s, bez wpływu na sukces).
- Ograniczeń bezpieczeństwa nie zmieniano; v_max 1,45 < 1,5 limitu warstwy, by komenda nie była przycinana.

## 11. Gotowość do Etapu 2
Baza jest stabilna: 1 750 prób bez porażki w 6 seriach, bez dryfu, z pełnym zapisem konfiguracji (determinizm: §3),
odtworzona co do bitu poprawionym kodem (§16). Jako baza porównawcza nadaje się do porównań **czasu i skuteczności
udanych cykli** w symulacji; porównania odporności na błędy mają oparcie tylko w scenariuszach z §15.
Nadaje się do porównań wariantów sterowania (w tym podmiany pojedynczych decyzji na sygnał z sieci muszki) i dalszej
optymalizacji czasu. Przed przeniesieniem na sprzęt potrzebne są: zastępniki kontroli tylko symulacyjnych (§14), percepcja
kostki, szum/opóźnienia w symulacji i test
na prawdziwym ramieniu (osobna zgoda).

## 12. Integralność
(Sekcja poprawiona po niezależnym audycie 2026-11-09 — poprzednia wersja zawierała dwa nieprawdziwe zdania, patrz niżej.)
- Etap 1 zmienił `flymind/so101.py` (+22/−2 linii). Nowe: `flymind/pick_place.py`, `flymind/test_pick_place.py`,
  `flymind/PICK_PLACE_STAGE1.md`, katalog `flymind/results/pick_place/`. Stan przed zmianami:
  `flymind/results/pick_place/files_sha256_before.txt`, `so101_default_xml_sha256_before.txt`.
- **Usunięte pliki (sprostowanie zdania „nic nie usunięto”).** Pliki pierwszego przebiegu S0 `baseline_v1.0*` (w
  `flymind/results/pick_place/`) zostały usunięte poleceniem `rm -f flymind/results/pick_place/baseline_v1.0*`, wykonanym
  w sesji agenta (Claude), który realizował Etap 1, w tym samym poleceniu, które uruchomiło serię porównawczą
  `run_sweep.sh`. Plików nie ma w repozytorium ani w historii Git, nie zostały odtworzone. Dlatego **bezpośrednie
  porównanie pierwszego i powtórnego przebiegu S0 nie jest możliwe**, a twierdzenie o identycznych czasach obu przebiegów
  jest NOT VERIFIED (częściowy dowód determinizmu: §3).
- **Historia Git (sprostowanie zdania „nie wykonano commitów”).**
  - W chwili pomiarów (wszystkie 6 plików JSON) kod był niezacommitowany: każdy JSON zapisuje `commit` = `54155d4` oraz
    `dirty_files` = `M flymind/so101.py`, `?? flymind/pick_place.py`.
  - Później, na polecenie właściciela projektu, kod, dokumentacja i wyniki zostały zapisane w commicie `f0b6927`.
  - Zgodność: skróty SHA-256 zapisane w każdym JSON (`pick_place.py` `a7b6e4572b1c9b7a…`, `so101.py` `071b4918ff40fd34…`)
    są identyczne z wersjami w `f0b6927`, więc wyniki powstały z kodu, który jest w tym commicie.
  - Poprawki po audycie (§13) są **niezacommitowane** i zmieniają `pick_place.py` i `so101.py` — ich skróty różnią się
    od zapisanych w JSON; wyniki §7 pochodzą z wersji z `f0b6927`.
- Nie wykonano `git clean` ani `push`. Istniejące pliki nieśledzone nietknięte — z jednym wyjątkiem ujawnionym niżej.
- **`MUJOCO_LOG.TXT` (plik nieśledzony w katalogu głównym) był w trakcie prac zapisywany.** Dwa wpisy z 19:04 pochodzą
  z dwóch nieudanych próbnych uruchomień wczesnej wersji testu T7 w sesji budującej Etap 1. 2026-11-09 o 19:32:01–02
  diagnostyka uruchomiona z katalogu repo w sesji pierwszych poprawek dopisała dwa kolejne wpisy; o 19:32:18 ta sama
  sesja przycięła plik z powrotem do pierwotnych 240 bajtów. Treść jest więc taka jak przed poprawkami (sha256
  `27b1dd74…`), ale zdanie „plik bez zmian” było prawdziwe tylko dla treści i dla przebiegów walidacji, nie dla całej
  sesji. Od tego czasu wszystkie testy i serie uruchamiane są z katalogu tymczasowego.
- **Determinizm S0 — częściowy dowód spoza repo.** Zapis sesji budującej Etap 1 zachował wyjście usuniętego przebiegu
  `baseline_v1.0`: wszystkie metryki symulacyjne podsumowania (T_sim 2287,46 s; kwartyle cyklu; mediany faz; 393,4
  op/h; błąd odłożenia) są identyczne z `S0_baseline`. Mocniejszy dowód jest w repo: §16 (1 750 cykli co do bitu).
- **Manifesty wcześniejszych eksperymentów V5** (`flymind/validation/v5*_manifest.json`) zapisują skrót `so101.py`
  sprzed Etapu 1 (`3ad95d38…`; `v5_confirm`: `835e32bf…`). Bieżący plik ma inny skrót już od `f0b6927`. Manifestów nie
  zmieniano; zamrożone kopie kodu w `flymind/validation/*_frozen_code/` są nietknięte i to one służą do odtwarzania
  tamtych przebiegów (`REPRODUCE.md`). Wpływ zmiany na innych użytkowników `SO101Sim`: §16.
- Manifest 17 historycznych plików wynikowych: `validation/historical_sha256.txt` (sprawdzany przed i po każdej nowej
  serii; wynik w `validation/benchmarks_postfix_v1.log`).

## 13. Poprawki po niezależnym audycie (2026-11-09)
Zakres: wiarygodność pomiarów, dokumentacja, ścieżki błędów. Nie zmieniono fizyki, parametrów sterowania, trajektorii,
definicji sukcesu ani surowych wyników (`flymind/results/pick_place/*.json`, `*_stdout.txt` — skróty bez zmian).

**Pomiar czasu przy resetach (błąd ukryty, w danych nie wystąpił).** `mj_resetData` zeruje `d.time`, a czas cyklu i serii
był liczony jako różnica `d.time`. Reset w ścieżce błędu `series()` dawał więc czas cyklu równy minus czasowi od
poprzedniego resetu (≤ 0) i zaniżony łączny czas serii (przy samych resetach 0 s, czyli dzielenie przez zero).
(Sprostowanie: podane wcześniej liczby `[0,0; −16,45; −32,9] s` „z kopii starego kodu” pochodziły z **mutacji jednej
linii nowego kodu** — koniec cyklu liczony z `d.time`, start z `sim_time`; to mutacja M4b w `validation/mutate.py`,
nie przebieg kodu z `f0b6927`.) Dodatkowo samoczynny reset MuJoCo
po ostrzeżeniu BADQPOS/BADQVEL **nie był wykrywany** (`SO101Sim.step` sprawdzał tylko BADQACC): stan był po cichu
teleportowany do pozycji początkowej, a pomiar czasu cofał się.
- `so101.py`: `SO101Sim.sim_time = t_offset + d.time`; `reset()` dolicza do `t_offset` czas sprzed resetu, `step()`
  wykrywa cofnięcie `d.time` w każdym kroku fizyki i dolicza utracony czas; wykonany krok liczy się raz. `step()` zgłasza
  `SimError` przy BADQPOS, BADQVEL, BADQACC lub samoczynnym resecie. Nowe liczniki `stats["resets"]`, `stats["auto_resets"]`.
  Bez resetów `t_offset = 0.0`, więc `sim_time == d.time` bit w bit. `d.time` i `Obs.t` (używane przez warstwę
  bezpieczeństwa i inne eksperymenty) bez zmian.
- `pick_place.py`: `cycle()` i `series()` mierzą czas z `sim_time`; nieudany cykl zapisuje `t_to_fail_sim`; seria
  zapisuje `auto_resets` i `continuous`; reset także po `sim_error` i po nieudanym `recover()`; statystyki warstwy
  bezpieczeństwa przechodzą przez reset; `series(..., cell=None)` przyjmuje gotowe stanowisko (testy).

**Testy (`flymind/test_pick_place_faults.py`).** Niezależna miara czasu: liczba taktów `sim.step` × 10 ms.
- P1.1 `sim_time` ciągły przez `reset()` i przez samoczynny reset MuJoCo (NaN w prędkości kostki → BADQVEL → `SimError`).
- P1.2 zwykłe cykle bez resetu: 2 pierwsze cykle S0 (seed 1) identyczne bit w bit z `S0_baseline.json`.
- P1.3 trzy resety z rzędu w ścieżce błędu (`place_out_of_zone` → kostka poza A/B → reset): brak ujemnych czasów,
  suma cykli = `T_sim` = takty × dt.
- P1.4 dwa samoczynne resety MuJoCo w trakcie cyklu (NaN prędkości → BADQVEL; siła 1e300 → BADQACC) → `sim_error`,
  reset serii, kolejne cykle udane; czas do błędu = 3,00 s (takt 300), bez podwójnego liczenia.
- P5: ścieżki błędów wywołane w symulacji — tabela niżej. Nie wszystkie są zdarzeniem fizycznym: `release_failed`,
  `place_out_of_zone` i `unreachable` wywołano zmianą progu kontroli, strefy albo ustawień planera, `bad_command`
  podmianą wyniku warstwy bezpieczeństwa.
- Skuteczność testów sprawdzona mutacjami: skrypt `validation/mutate.py` (kopie kodu w katalogu tymczasowym), log
  `validation/mutation_*.log` — 20 mutacji, 20 wykrytych. Pierwszy przebieg (9/9, 2026-11-09 19:37) nie zostawił
  artefaktu w repo; 8 z jego 9 mutacji jest w obecnym skrypcie, dziewiątą („brak resetu po nieudanym recover”)
  zastąpiły M10–M16 po zmianie logiki odzyskiwania.

| Ścieżka | Jak wywołana w teście | Wynik (`outcome`) |
|---|---|---|
| `table_collision` | zejście zaplanowane 10 mm za nisko (błąd kalibracji wysokości stołu) | `reset` — `recover()` nie rusza ramienia (`no_motion`) |
| `cube_hit_table` | trasa transportu zaplanowana w dół do stołu przy B | `reset` — po otwarciu szczęki kostka poza A/B (`cube_lost`) |
| `release_failed` (dotyk po otwarciu) | próg zwolnienia `q_clear` 0,2 rad < kąt kontaktu z kostką (zmiana progu) | `recovered` |
| `release_failed` (kostka uniesiona przy odejściu) | — | NOT VERIFIED: wymaga przywierania kostki do szczęki, którego model nie ma |
| `place_out_of_zone` | strefa B przesunięta o 15 mm względem miejsca, w które celuje plan (zmiana strefy) | `reset` (`cube_lost`) |
| `place_no_contact` | zejście przy odkładaniu kończy się 15 mm za wysoko | `recovered` — kostka upuszczona z 15 mm, ląduje w strefie B |
| `cube_pushed` | stała szczęka schodzi 4 mm „w ścianę” kostki | `recovered`; w teście R1 potem 3 udane cykle bez resetu |
| `unreachable` | kostka 6 mm od A + planer z odstępem 20 mm odrzuca plan (zmiana planera); porażka przed ruchem | `recovered`; geometryczna nieosiągalność w strefie 10 mm przy obecnych A/B nie występuje |
| `jaw_not_open` (odłożenie) | serwo szczęki po chwycie nie daje momentu otwierającego | `reset` — stan niepotwierdzony (szczęka zamknięta) |
| `jaw_not_open` (podejście) | szczęka startuje przymknięta (0,2 rad) i nie otwiera się | `reset` |
| `bad_command` | cel poza `ctrlrange` (podmieniony wynik warstwy bezpieczeństwa) | `reset` — komenda niezastosowana, zero taktów |
| `sim_error` | NaN prędkości / siła 1e300 → samoczynny reset MuJoCo (także w 1. i 2. kroku po resecie) | `reset` (P1.1, P1.4, P1.5, S3) |
| `safety_fault` | jednorazowy zły odczyt enkodera; `estop()` | `halted` (S1, S2; §15) |

Kolumna „wynik” to `outcome` sprawdzany asercją w teście; po każdej ścieżce (poza `halted`) test sprawdza też wprost
w symulatorze stan gotowości: ramię w domu, szczęka otwarta, brak kontaktów, kostka w A/B, brak błędów.

## 14. Dane z symulatora a prawdziwy SO-101
Cykl działa w MuJoCo. Część kontroli sukcesu korzysta z informacji, których prawdziwy SO-101 w obecnej konfiguracji
**nie ma**: zweryfikowany sprzęt to jedno ramię SO-101 (enkodery serw) i kamera FaceTime laptopa; czujniki dotyku na
padach i kamera na nadgarstku istnieją tylko w modelu. To nie podważa wyników symulacji — ogranicza ich przenoszenie na
robota. Oznaczenia: **VERIFIED (sym.)** = działa i przetestowane w symulacji; **NOT IMPLEMENTED (sprzęt)** = brak na
robocie; **POTENTIAL HARDWARE EQUIVALENT** = możliwy przyszły odpowiednik, tylko propozycja (nic nie kupiono ani nie
zaimplementowano).

| Kontrola (przyczyna porażki) | Co jest mierzone | Źródło w kodzie | Dlaczego dostępne w symulatorze | Sprzęt dziś | POTENTIAL HARDWARE EQUIVALENT |
|---|---|---|---|---|---|
| start cyklu `object_lost`, wybór A/B, nowy plan chwytu | dokładna poza kostki (pozycja, obrót, przechył) | `cube_pose()`, `where()` | stan ciała `cube` (`xpos`, `xmat`) | NOT IMPLEMENTED | kamera nad stołem lub na nadgarstku + rozpoznanie kostki (np. znacznik / kolor) z kalibracją — propozycja |
| `cube_pushed` | przesunięcie kostki przy zejściu | `cube_pose()` przed i po | jw. | NOT IMPLEMENTED | jw. (kamera) — propozycja |
| `no_contact`, `weak_grip` | siła na padach obu szczęk ≥ 1 N | `obs.touch` (czujniki touch MuJoCo na padach) | wirtualne czujniki siły na padach | NOT IMPLEMENTED (brak czujników na szczękach) | czujniki FSR na padach i/lub prąd/obciążenie serwa szczęki STS3215 — propozycja (wariant „4 FSR + serwo” z 2026-11-05, tylko symulacja planowana) |
| `slip` (utrata kontaktu) | spadek siły na padach | `obs.touch` | jw. | NOT IMPLEMENTED | jw. — propozycja |
| `slip` (przesunięcie > 8 mm) | położenie kostki względem chwytaka | `held_offset()` | pozy ciał `cube` i `gripper` | NOT IMPLEMENTED | kamera na nadgarstku śledząca kostkę — propozycja |
| `lift_failed` | wysokość kostki, brak kontaktu kostka–stół | `xpos` kostki, `cube_on_table()` | lista kontaktów fizyki | NOT IMPLEMENTED | kamera; ewentualnie zmiana obciążenia serwa (kostka 30 g — rozdzielczość wątpliwa, niezweryfikowane) — propozycja |
| `cube_hit_table` | kontakt kostka–stół w transporcie | `cube_on_table()` | lista kontaktów fizyki | NOT IMPLEMENTED | czujniki FSR (zmiana siły) lub kamera — propozycja |
| `place_no_contact` | kontakt kostka–stół przed otwarciem | `cube_on_table()` | lista kontaktów fizyki | NOT IMPLEMENTED | czujniki FSR / obciążenie serw ramienia — propozycja |
| `release_failed` | siła na padach po otwarciu; wysokość kostki przy odejściu | `obs.touch`, `xpos` kostki | czujniki touch, stan ciała | NOT IMPLEMENTED | FSR (siła), kamera (wysokość) — propozycja |
| `place_out_of_zone`, `place_err_mm`, `tilt_deg` | poza kostki względem B | `cube_pose()`, `where()` | stan ciała `cube` | NOT IMPLEMENTED | kamera z kalibracją — propozycja |
| `table_collision` | kontakt ramienia/padów ze stołem | `table_contacts()` | lista kontaktów fizyki | NOT IMPLEMENTED | wykrywanie kolizji z błędu nadążania / prądu serw — propozycja; odstęp padów w planie (`reach.z_min`) działa tylko przy poprawnie skalibrowanej wysokości stołu |
| `sim_error` | niestabilność fizyki | `SO101Sim.step` | stan numeryczny MuJoCo | nie dotyczy (zjawisko tylko symulacyjne) | — |
| `jaw_not_open`, `home_err_rad`, `start_drift_rad`, `safety_*` | kąty stawów i szczęki | `obs.q` | enkodery w modelu | **dostępne co do zasady** (enkodery serw STS3215); integracja z tym kodem NOT IMPLEMENTED | — |
| potwierdzenie stanu po porażce (`not_ready()`) | dom, szczęka, nacisk na padach, kontakty ramię–stół i ramię–kostka, kostka w A/B | `obs.q`, `obs.touch`, lista kontaktów, `where()` | jw. | tylko część „kąty stawów” dostępna co do zasady; reszta NOT IMPLEMENTED | kamera + FSR — propozycja |
| siła chwytu (to nie kontrola, tylko **sterowanie**) | moment szczęki 0,5 / 0,4 N·m | `grip.py`, silnik momentowy w `so101.py` | aktuator `motor` w modelu zamiast serwa pozycyjnego | NOT IMPLEMENTED: STS3215 nie ma skalibrowanego sterowania momentem w N·m | limit prądu / tryb PWM serwa z kalibracją siły na padach — propozycja, niezweryfikowana |
| reset sceny po porażce (`reset_scene()`) | — | `SO101Sim.reset` | teleportacja ramienia i kostki | nie istnieje — na stanowisku to ręczna ingerencja człowieka | — |
| zatrzask błędu / `estop()` | — | `safety.SafetyLayer` | zmienna w programie | **tylko logika programu**; fizycznego wyłącznika awaryjnego ani odcięcia zasilania serw w projekcie nie ma | sprzętowy e-stop odcinający zasilanie serw — propozycja |

Status w symulacji: wszystkie kontrole działały w 1 750 udanych cyklach §7 (warunek spełniony). Porażkę wywołano w
testach dla: `object_lost` (T8), `no_contact` (T6), jednej z `lift_failed`/`slip`/`weak_grip` (T7 — test nie rozróżnia,
która), oraz ścieżek z §13 (w tym `jaw_not_open` i `safety_fault`) — te są **VERIFIED (sym.)**. Bez testu porażki
(NOT VERIFIED): `release_failed` przy odejściu oraz pozycje z §15.5.

## 15. Porażka cyklu: odzyskanie, reset, zatrzymanie (po poprawkach P1)
Wszystko poniżej to logika programu sprawdzona **w symulacji**. Nic z tego nie jest zabezpieczeniem sprzętowym.

### 15.1 Trzy różne skutki (pole `outcome` nieudanego cyklu)
- **`recovered` — prawdziwe odzyskanie.** `recover()` wykonał ruch i stan został sprawdzony; następny cykl rusza bez
  resetu, z miejsca, w którym faktycznie leży kostka. Licznik: `summary.recovered`.
- **`reset` — przerwanie cyklu i reset symulatora.** Stanu nie potwierdzono (albo ruch był niedozwolony), więc
  `reset_scene()` teleportuje ramię do domu i kostkę do A. Liczone w `resets`; `continuous = false`. Na prawdziwym
  stanowisku odpowiada temu ręczna ingerencja, której czas **nie** jest wliczony. To nie jest odzyskanie.
- **`halted` — zatrzymanie serii.** Zatrzaśnięty błąd bezpieczeństwa: bez ruchu, bez resetu, bez kolejnych cykli;
  seria ma `complete = false`. Wznowienie tylko po jawnym potwierdzeniu (15.3, klasa 3).

Udany cykl po resecie dowodzi tylko, że symulator da się ustawić od nowa — nie, że robot sam wrócił do pracy.

### 15.2 `recover()` i potwierdzenie stanu
`recover(przyczyna)` otwiera szczękę, odchodzi 6 cm w górę i wraca do domu (0,5 rad/s), po czym wywołuje `not_ready()`.
Zwraca **True tylko wtedy**, gdy `not_ready()` nie znajduje przeszkody; inaczej zwraca jej opis. `not_ready()` czyta
bieżący stan, nie historię ruchu:

| Warunek | Źródło | Zgłaszany powód |
|---|---|---|
| brak zatrzaśniętego błędu warstwy bezpieczeństwa | `SafetyLayer.fault` | `safety_latched` |
| symulator nie jest zatrzymany | `SO101Sim.stopped` | `sim_stopped` |
| 5 stawów ramienia w domu, tolerancja `settle_tol` = 0,02 rad | `obs.q` | `arm_not_home` |
| szczęka otwarta ≥ `q_clear` = 0,55 rad | `obs.q[5]` | `jaw_not_open` |
| żaden pad ani dłoń nie jest dociśnięty (> 0,2 N) | `obs.touch` | `pads_loaded` |
| ramię nie dotyka stołu ani kostki | lista kontaktów fizyki | `contact` |
| kostka leży w A albo B (strefa, obrót, przechył) — następny cykl ma skąd ją wziąć | `where()` | `cube_lost` |

`recover()` **nie kasuje** błędu bezpieczeństwa i **nie rusza ramienia**, gdy błąd jest zatrzaśnięty, symulator
zatrzymany albo przyczyna należy do klasy 2 (zwraca `safety_latched…` / `no_motion…`).

Test R1 (`test_pick_place_faults.py`): jeden błędny plan podejścia (stała szczęka 4 mm w ścianę kostki) → `cube_pushed`
→ `recover()` → stan sprawdzony wprost w symulatorze (dom 0,0004 rad, szczęka 0,93 rad, brak kontaktów, kostka 5,0 mm
od A — tam, gdzie ją zepchnięto) → trzy kolejne cykle udane (A→B, B→A, A→B), `resets = 0`, licznik resetów symulatora
bez zmian, czas ciągły. Nic nie jest ustawiane ręcznie między porażką a następnym cyklem. To **jeden** scenariusz
przejściowego błędu; inne nie były sprawdzane (15.5).

### 15.3 Klasy błędów
| Klasa | Przyczyny | Ruch po błędzie | Dalszy ciąg serii | Co może wznowić pracę |
|---|---|---|---|---|
| 1. porażka procesu (odzyskiwalna automatycznie) | `object_lost`, `unreachable`, `jaw_not_open`, `cube_pushed`, `no_contact`, `weak_grip`, `slip`, `lift_failed`, `cube_hit_table`, `place_no_contact`, `release_failed`, `place_out_of_zone`; niezatrzaśnięte flagi warstwy (`safety_bad_command`) | `recover()`: szczęka, 6 cm w górę, dom | `recovered`, jeśli stan potwierdzony; inaczej `reset` | automat |
| 2. błąd wymagający zatrzymania ruchu | `table_collision` (kontakt ramienia ze stołem), `bad_command` (komenda odrzucona przez symulator) | żaden | `reset` | w symulacji reset (liczony); na sprzęcie człowiek |
| 3. zatrzaśnięty błąd bezpieczeństwa | `safety_fault`: pomiar stawu poza zakresem o > 0,05 rad albo NaN; programowy `estop()` | żaden — `cycle()`, `tick()` i `recover()` kończą się przed wysłaniem komendy i przed krokiem fizyki | `halted` | **tylko** jawne `SafetyLayer.clear(powód)`, zapisywane w `safety.stats["cleared"]`; nie robi tego `recover()`, `series()` ani `reset_scene()` |
| 4. błąd krytyczny symulatora | `sim_error`: niestabilna fizyka, MuJoCo samo teleportuje stan | żaden — `SO101Sim` ignoruje komendy do czasu `reset()` | `reset` | tylko reset symulatora; zjawisko czysto symulacyjne, bez odpowiednika sprzętowego |

W kodzie klasy 2 i 4 łączy jedna stała `NO_MOTION` (`pick_place.py`): po tych przyczynach `recover()` nie wysyła komend.
Reset symulatora **nie jest potwierdzeniem bezpieczeństwa**: `reset_scene()` zostawia tę samą warstwę z zatrzaśniętym
błędem (test S2). „Operator” oznacza tu wywołanie `clear()` w kodzie — nie ma uwierzytelnienia ani fizycznego przycisku.
Po zatrzaśnięciu w symulatorze zostaje ostatnia wysłana komenda (ramię trzyma cel, szczęka ostatni moment); nowa nie
jest wysyłana.

### 15.4 Zabezpieczenia — stan faktyczny
| Stan | Mechanizm |
|---|---|
| **aktywne w cyklu (symulacja)** | zakres stawów z marginesem, limit prędkości **komendy** 1,5 rad/s, limit wyprzedzenia celu względem pomiaru, limit momentu szczęki 1,0 N·m i kraniec szczęki (`safety.py`); zatrzask przy pomiarze poza zakresem / NaN i blokada ruchu do `clear()`; odstęp padów od stołu w planie (`reach.z_min` 5 mm); monitor kontaktu ramię–stół co 10 ms i wykrywanie niestabilności fizyki (dane symulatora); odrzucenie komendy poza kontraktem |
| **nieaktywne konstrukcyjnie** | `cmd_timeout` i `vision_stale`: znacznik czasu komendy = chwila sprawdzenia, wiek obrazu = 0 (`Cell.tick`); działają tylko w izolowanym `test_safety.py` |
| **niezaimplementowane** | limit i kontrola przyspieszenia rzeczywistego; geometria kartezjańska i kolizje w warstwie bezpieczeństwa; kolizje korpusu chwytaka i ruchomej szczęki (wyłączone w modelu); samokolizje ramienia; monitor kontaktu ramię–kostka w trakcie cyklu; sprzętowy e-stop i odcięcie zasilania; nadzór komunikacji z serwami; jakikolwiek z powyższych mechanizmów na fizycznym SO-101 |

„Brak interwencji warstwy” ani zaliczone testy nie są dowodem bezpieczeństwa ruchu.

### 15.5 Czego nadal nie sprawdzono
- `release_failed` przy odejściu; `weak_grip`, `slip`, `lift_failed` osobno (T7 wywołuje jedną z trzech);
  `safety_bad_command` (NaN z planera).
- Odzyskanie po innych przejściowych błędach niż `cube_pushed`; odzyskanie, gdy ramię nie dojeżdża do domu
  (`arm_not_home` nie ma scenariusza — warunek sprawdzany tylko pośrednio).
- Przerwanie z klawiatury (ta sama gałąź kodu co wyjątek z testu W1, osobno nieuruchamiana).
- Zachowanie przy szumie czujników, opóźnieniach, luzach — model ich nie ma (§9.2).

## 16. Poprawki P1 po drugim audycie (2026-11-09)
Zakres: pięć priorytetów P1. Nie zmieniono fizyki, parametrów sterowania, trajektorii, limitów, definicji sukcesu ani
metryk; `reach.py`, `grip.py`, `safety.py` bez zmian (te same skróty co w `files_sha256_before.txt`).

**P1.1 odzyskanie bez resetu** — `pick_place.py`: `not_ready()`, `recover()` z potwierdzeniem stanu, `cube_contacts()`,
`outcome` w `series()`; test R1 (§15.2).
**P1.2 błędy bezpieczeństwa** — `pick_place.py`: `recover()` nie kasuje zatrzasku, klasa `NO_MOTION`, `cycle()` odmawia
startu przy zatrzasku / zatrzymanym symulatorze, `series()` staje (`halted`), `reset_scene()` zachowuje warstwę;
osobna przyczyna `bad_command`; testy `jaw_not_open` ×2, S1–S4 (§15.3). `safety.py` bez zmian.
**P1.3 inni użytkownicy `so101.SO101Sim`** — zmiana `step()` jest wspólna dla całego środowiska:
- nowe zachowanie dotyczy tylko niestabilnej fizyki: BADQPOS / BADQVEL / samoczynny reset MuJoCo kończą takt
  wyjątkiem `SimError` (wcześniej tylko BADQACC; stan był po cichu teleportowany). `loop.py` traktuje `SimError` jako
  nieudaną próbę, `cl_runner.py` zapisuje błąd; `bench_loop.py`, `cl_sense.py`, `run_fj1.py`, `demo.py` i skrypty
  pilotażowe nie łapią wyjątku — przy niestabilności zatrzymają się zamiast liczyć dalej na teleportowanym stanie;
- `sim.stats` ma dwa nowe liczniki (`resets`, `auto_resets`); trafią do pola `sim_stats` nowych wyników `loop.py`,
  `cl_sense.py`, `bench_loop.py`. Żaden kod w repo ich nie czyta;
- `d.time`, `Obs.t`, przebieg zwykłego kroku i domyślna scena (SHA-256 `13e65e9d…`) bez zmian;
- **regresja uruchomiona** (`validation/regression_20261109_210604.log`): `test_cl_runner.py` (6 testów) i
  `demo/test_demo.py` (T1–T10) zaliczone z bieżącym `so101.py` oraz z zamrożonym sprzed Etapu 1
  (`validation/v5v4_frozen_code/so101.py`, sha `3ad95d38…`, podmiana tylko w pamięci procesu przez
  `validation/with_so101.py`); wyjścia obu wariantów **identyczne** (poza czasem zegarowym);
- **nieuruchomione** (NOT VERIFIED wykonaniem): `bench_loop.py`, `cl_sense.py`, `run_fj1.py`, `v61_v7.py`,
  `v7_encoder_distance.py`, skrypty pilotażowe i same przebiegi V5 — zapisują wyniki lub trwają długo. Zamrożone kopie
  V5 używają własnego `so101.py`, więc odtwarzanie tamtych przebiegów nie zależy od tej zmiany.

**P1.4 powtórzenie benchmarków** — `validation/run_postfix.sh` uruchomił te same polecenia, ziarna i parametry co
`run_sweep.sh` i seria 500 cykli, pod nowymi nazwami `<tag>_postfix_v1`. Porównanie (`validation/compare_postfix.py`,
pełne liczby w `validation/benchmarks_postfix_v1.log`): każde pole symulacyjne każdego z 1 750 cykli porównane co do
bitu (czasy zegarowe pominięte — zależą od obciążenia komputera).

| Seria | Próby / sukcesy / porażki / resety / przerwania | T_sim [s] | Mediana [s] | 3600/med | ok/T×3600 | max v [rad/s] | max a [rad/s²] | Błąd odłożenia med / max [mm] | Takty | Różnic stare → nowe |
|---|---|---|---|---|---|---|---|---|---|---|
| S0 | 250 / 250 / 0 / 0 / 0 | 2287,46 | 9,150 | 393,44 | 393,45 | 0,88936 | 61,846 | 1,8169 / 2,0903 | 228 746 | 0 |
| S1 | 250 / 250 / 0 / 0 / 0 | 1729,49 | 6,920 | 520,23 | 520,38 | 1,35587 | 77,371 | 2,5150 / 3,1161 | 172 949 | 0 |
| S2 | 250 / 250 / 0 / 0 / 0 | 1637,17 | 6,550 | 549,62 | 549,73 | 1,35466 | 77,371 | 2,5141 / 3,1223 | 163 717 | 0 |
| S3 | 250 / 250 / 0 / 0 / 0 | 1289,74 | 5,170 | 696,32 | 697,82 | 1,34510 | 102,107 | 2,5601 / 3,1029 | 128 974 | 0 |
| S4 | 250 / 250 / 0 / 0 / 0 | 1687,81 | 6,770 | 531,76 | 533,24 | 0,89096 | 71,830 | 1,7793 / 2,0746 | 168 781 | 0 |
| S3 ×500 | 500 / 500 / 0 / 0 / 0 | 2572,81 | 5,165 | 697,00 | 699,62 | 1,37127 | 95,595 | 2,6144 / 2,6795 | 257 281 | 0 |

Wartości w tabeli są takie same dla serii historycznej i powtórzonej (różnica dokładnie 0 w każdej metryce i każdym
cyklu; suma czasów faz = T_sim). Nowe serie: `auto_resets` 0, `continuous` i `complete` true. Wniosek ograniczony do
tego, co zmierzono: poprawki nie zmieniły przebiegu nominalnego cyklu w tych sześciu seriach. Skróty kodu, którym
powstały nowe wyniki (zapisane w każdym JSON i w logu): `so101.py` `1246c409b51ec3ff…`, `pick_place.py`
`91ad5b512a5ef2db…` — te same pliki są w commicie z poprawkami.

**P1.5 dokumentacja i dowody** — ten plik; w `flymind/results/pick_place/validation/`:

| Plik | Co zawiera |
|---|---|
| `historical_sha256.txt` | skróty 17 historycznych plików wynikowych (przed pracami; sprawdzane po) |
| `integrity_p1.txt` | commit bazowy, kontrola historycznych wyników po pracach, skróty wszystkich plików commitu z poprawkami |
| `validation_20261109_210553.log` | log testów Etapu 1 (5 plików) |
| `regression_20261109_210604.log` | log regresji innych użytkowników `SO101Sim` (bieżący i zamrożony `so101.py`) |
| `mutation_20261109_210817.log`, `mutate.py` | testy mutacyjne i ich wynik |
| `benchmarks_postfix_v1.log` | polecenia, kody wyjścia, skróty nowych wyników, kontrola historycznych, pełne porównanie |
| `run_validation.sh`, `run_postfix.sh`, `compare_postfix.py`, `with_so101.py` | skrypty odtwarzające powyższe |

Pozostałe zmiany z tej tury: wykrywanie samoczynnego resetu MuJoCo także w 1. i 2. kroku po resecie (`so101.py`,
test P1.5); `_qd_prev` odświeżany po resecie; `main()` nie nadpisuje wyników i oznacza serię przerwaną
(`*.INCOMPLETE.json`); dzielenie przez zero przy `T_sim = 0` usunięte.
