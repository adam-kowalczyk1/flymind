# FlyMind — Etap 1: powtarzalny cykl pick-and-place SO-101 (MuJoCo)

Data: 2026-11-09 · Branch `flymind/fly-first-control` · commit bazowy `54155d4` · MuJoCo 3.17.0, NumPy 2.5.4, Python z `.venv`

**Werdykt: UKOŃCZONY w zakresie symulacji** (szczegóły ograniczeń w §8). To jest **klasyczny kontroler**, nie sterowanie
muszki: wszystkie komendy mają źródło `classical:pick_place`. Wyniki dotyczą wyłącznie symulacji, nie fizycznego robota.

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
| D. Monitory symulacji | `pick_place.py::Cell.tick` | **nowe** — kontakt ramienia ze stołem, flagi warstwy, niestabilność fizyki, zapas do krańców, max prędkość |
| E. Orkiestrator | `pick_place.py::Cell.cycle`, `recover` | **nowe** |
| F. Pomiar i seria | `pick_place.py::series`, `summarize`, `main` | **nowe** |
| Testy | `flymind/test_pick_place.py` | **nowe** |

## 3. Scena i obiekt (`PPCfg` w `pick_place.py`)
- Kostka 30 mm, 30 g (≈ PLA 1,1 g/cm³), tarcie 0,8 (PLA/guma), condim 4. Pady szczęk z `so101.py`: tarcie 1,2 (odziedziczone).
- A = (0,22; 0,10) m, B = (0,22; −0,10) m — 20 cm transportu. Znaczniki: płaskie krążki bez kolizji (tylko wizualne).
- Orientacja startowa kostki: ściany prostopadłe do kierunku zamykania szczęk w pozie chwytu nad A.
- Ziarno (seed) losuje raz na serię: masa i tarcie kostki ×U(0,9; 1,1), start kostki ±2 mm / ±3°. Fizyka sama w sobie
  jest deterministyczna (ten sam seed → identyczne czasy; potwierdzone dwoma przebiegami S0).
- Pozycja kostki jest czytana **ze stanu symulatora** (bez kamery) — patrz ograniczenia.

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
| każdy takt | warstwa bezpieczeństwa + monitory | `table_collision`, `safety_*`, `sim_error` |

Po porażce `recover()` otwiera szczękę, odchodzi w górę i wraca do domu bez resetu. Jeśli kostki nie ma w A ani w B,
seria resetuje środowisko i **liczy to jako reset** (pole `resets`). Porażki nigdy nie są liczone jako sukces.

**Plany liczone raz:** przy starcie `Cell` liczy pełne plany A→B i B→A (≈ 22 ms). Gdy kostka odbiega od nominału
> 1,5 mm lub > 2°, liczony jest od nowa tylko plan chwytu (≈ 3,4 ms; zmierzone), a transport/odłożenie/powrót są z cache.
W praktyce kostka po odłożeniu leży 1,5–3 mm od nominału, więc nowy plan chwytu był liczony w każdym cyklu.

## 5. Metryki
- `cycle_sim` — czas cyklu w **sekundach symulacji** (to odpowiada czasowi pracy robota w modelu).
- `cycle_wall` — czas cyklu w **sekundach zegarowych** tego Maca, bez renderowania. To jest szybkość obliczeń, nie robota.
- Czasy faz (sym. i zegarowe), `place_err_mm`, `tilt_deg`, `home_err_rad`, `start_drift_rad`, przyczyny porażek.
- Przepustowość = udane przeniesienia / łączny czas serii × 3600, osobno dla czasu symulacji i zegarowego.
- Statystyki serii: min / Q1 / mediana / Q3 / max, nie najlepszy cykl.

## 6. Uruchomienie

```bash
.venv/bin/python -I -B flymind/test_pick_place.py
```

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

| Wariant | Sukces | Cykl min / med / max | op/h (czas sym.) | op/h (czas zegarowy) | Błąd odłożenia med / max | Interwencje warstwy bezp. |
|---|---|---|---|---|---|---|
| S0 bazowy (v 1,0; a 4; szczęka 0,93; dom z `test_reach`) | 250/250 | 9,07 / 9,15 / 9,19 | 393,4 | 20 725 | 1,82 / 2,09 mm | 0 |
| S1 v 1,45; a 8 | 250/250 | 6,84 / 6,92 / 6,95 | 520,4 | 26 604 | 2,52 / 3,12 mm | 0 |
| S2 = S1 + szczęka 0,65 | 250/250 | 6,52 / 6,55 / 6,86 | 549,7 | 27 896 | 2,51 / 3,12 mm | 0 |
| **S3 = S2 + dom nad środkiem A–B** | **250/250** | **5,12 / 5,17 / 5,46** | **697,8** | 33 784 | 2,56 / 3,10 mm | 0 |
| S4 = S3 przy v 1,0; a 4 | 250/250 | 6,70 / 6,77 / 7,05 | 533,2 | 26 120 | 1,80 / 2,07 mm | 0 |
| S3, ciągłość 500 cykli (seed 6) | 500/500 | 5,12 / 5,165 / 5,43 | 699,6 | 35 718 | 2,61 / 2,68 mm | 0 |

Mediany faz S0 → S3 [s]: podejście 2,39 → 0,985; chwyt 1,17 → 0,79; podniesienie 0,64 → 0,45; transport 1,305 → 0,92;
odłożenie 1,21 → 1,02; powrót 2,43 → 0,985.

Ciągłość: we wszystkich seriach 0 resetów; odchyłka ramienia na starcie cyklu ≤ 0,0005 rad (taka sama w cyklu 1 i 500);
błąd odłożenia się nie kumuluje (mediana pierwszych/ostatnich 100 cykli: 2,61 / 2,52 mm). Najmniejszy zapas do krańca
stawu: 0,115 rad. Max zmierzona prędkość stawu: 0,89 rad/s (v 1,0) i 1,36 rad/s (v 1,45) — poniżej limitu 1,5 warstwy.

Wykres: `flymind/results/pick_place/variants.png`.

**Wnioski z optymalizacji.** Największy zysk dała poza domowa bliżej miejsc pracy (S2 → S3: −1,4 s), potem prędkość
(S0 → S1: −2,2 s) i mniejsze rozwarcie szczęki (−0,4 s). Szybszy ruch ma koszt: błąd odłożenia rośnie z ~1,8 do ~2,6 mm
(max 3,1 mm), wciąż w strefie 10 mm. Skuteczność nie spadła w żadnym wariancie. Wariant do dalszych prac: **S3**; S0
pozostaje domyślną konfiguracją kodu (testy jej używają).

**1500 op/h nie osiągnięto.** Najlepszy zmierzony wynik: ok. 698 op/h czasu symulacji (5,17 s/cykl). 1500 op/h wymagałoby
cyklu 2,4 s. Wartości „op/h czasu zegarowego” (20–36 tys.) mówią tylko, jak szybko liczy komputer — nie są wydajnością robota.

## 8. Testy (`flymind/test_pick_place.py`, ok. 2 s)
T1 profil (koniec, |Δq| ≤ v·dt, |Δ²q| ≤ a·dt²) · T2 scena (wymiary, masa, znaczniki bez kontaktu) · T3 jeden cykl faza po
fazie · T4 6 cykli bez resetu, przełączanie kierunku, brak dryfu · T5 kostka 6 mm od A → nowy plan chwytu, sukces ·
T6 kostka „niewidoczna” dla szczęk → `no_contact` · T7 śliska kostka (tarcie 0,05) → porażka chwytu/podniesienia ·
T8 kostka obrócona 30° → `object_lost` bez ruchu. W T6–T8 sprawdzane jest też, że `recover()` wraca do domu.
Bez regresji: `test_reach.py`, `test_safety.py`, `test_so101.py --zgoda-sim` (T1–T9) przechodzą.

## 9. Ograniczenia i znane problemy
1. **Pozycja kostki ze stanu symulatora**, nie z kamery — w fizycznym robocie potrzebna percepcja (Etap 2+).
2. **Skuteczność 100 % dotyczy idealnego modelu**: brak szumu czujników, luzów, błędów kalibracji, opóźnień serw.
   Losowość per seed jest tylko w masie/tarciu (±10 %) i ustawieniu startowym (±2 mm/±3°). Na prawdziwym SO-101 należy
   spodziewać się gorszych wyników.
3. Ścieżki obsługi błędów zostały sprawdzone tylko na awariach wstrzykniętych w testach (T6–T8); w seriach żadna porażka
   nie wystąpiła. `object_lost` wymaga resetu (automatycznego w serii, liczonego).
4. Kolizje ze stołem wykrywane są kontaktami w symulatorze (wyrocznia niedostępna w realnym robocie) i kontrolą odstępu
   padów w planie; warstwa bezpieczeństwa nadal nie ma geometrii kartezjańskiej (jak w `safety.py`).
5. Przyspieszenie jest ograniczone w **komendach** (a_max 4–8 rad/s²). Zmierzone przyspieszenia stawów z różnic prędkości
   co 10 ms sięgają 62–102 rad/s² — to stany przejściowe serw pozycyjnych i kontaktów, nie komenda.
6. Kostka kładzie się 1,5–3 mm od nominału (szczęka dociska ją do stałego padu, kostka lekko się przechyla ~3,5° w chwycie),
   więc plan chwytu liczony jest w każdym cyklu (3,4 ms); transport/odłożenie/powrót są z cache.
7. Tylko kostka 30 mm. Kula nie była testowana w cyklu (istniejący `test_reach.py` podnosi kulę).
8. Chwyt trwa 0,8–1,2 s głównie przez prędkość zamykania szczęki przy momencie 0,5 N·m (`GripCfg`, nie zmieniane).
9. Poza domowa S3 (`--home`) została wyznaczona IK raz (cs_fixed nad (0,22; 0; 0,10) m) i wpisana do `run_sweep.sh`.

## 10. Decyzje techniczne
- Kostka zamiast kuli (stabilna, nie toczy się). Prowadzenie **stałej** szczęki (jak `test_reach`), bo ruchoma obraca się.
- Nowy kod w jednym pliku `pick_place.py`; scena rozszerzona w `so101.py` polami opcjonalnymi zamiast kopii sceny.
- Kontrola poślizgu w **układzie chwytaka** (pierwsza wersja w układzie świata dawała fałszywy „slip” przy obrocie bazy).
- Zwolnienie = oba pady bez kontaktu i szczęka ≥ 0,55 rad, a nie pełne otwarcie (oszczędza ok. 1 s, bez wpływu na sukces).
- Ograniczeń bezpieczeństwa nie zmieniano; v_max 1,45 < 1,5 limitu warstwy, by komenda nie była przycinana.

## 11. Gotowość do Etapu 2
Baza jest stabilna i deterministyczna: 1 750 prób bez porażki w 6 seriach, bez dryfu, z pełnym zapisem konfiguracji.
Nadaje się do porównań wariantów sterowania (w tym podmiany pojedynczych decyzji na sygnał z sieci muszki) i dalszej
optymalizacji czasu. Przed przeniesieniem na sprzęt potrzebne są: percepcja kostki, szum/opóźnienia w symulacji i test
na prawdziwym ramieniu (osobna zgoda).

## 12. Integralność
- Zmienione: `flymind/so101.py` (+22/−2 linii). Nowe: `flymind/pick_place.py`, `flymind/test_pick_place.py`,
  `flymind/PICK_PLACE_STAGE1.md`, katalog `flymind/results/pick_place/`.
- Stan przed zmianami: `flymind/results/pick_place/files_sha256_before.txt`, `so101_default_xml_sha256_before.txt`.
  Przywrócenie `so101.py`: `git checkout -- flymind/so101.py` (plik śledzony, commit `54155d4`).
- Nic nie usunięto, nie wykonano `git clean`, commitów ani `push`. Istniejące pliki nieśledzone nietknięte.
