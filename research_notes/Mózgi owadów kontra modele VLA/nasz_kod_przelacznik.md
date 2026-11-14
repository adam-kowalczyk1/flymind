# Nasz kod i maszyna: co istnieje pod przełącznik sterowników na JEDNYM prawdziwym SO-101 (SNN muchy vs pi0 vs regulator P vs SNN przetasowana)

Metoda: wyłącznie pliki lokalne i polecenia tylko-do-odczytu (grep, ls, sysctl, system_profiler, import pakietów). Nic nie zainstalowano, do żadnego portu szeregowego nic nie wysłano. Źródła podane jako ścieżki (bez URL, bo nic nie jest z internetu). Data stanu: 2026-11-03.

## 1. Czy w repo jest jakikolwiek kod rozmawiający z prawdziwym SO-101 / serwami Feetech?

### Takeaway
NIE. W `/Users/admin/so101_fly_project` nie ma żadnego sterownika sprzętowego (lerobot, scservo, feetech, pyserial, /dev/tty — zero trafień w kodzie). Wszystko jest symulacją MuJoCo; sprzęt jest jawnie "poza zakresem bez osobnej zgody". Sama maszyna ma jednak zainstalowany LeRobot 0.6.2 z klasą `SO101Follower` (poza repo projektu).

### Cited Findings
- grep po `lerobot|feetech|scservo|/dev/tty|pyserial|import serial|openpi|pi0` w repo (bez .venv/.git/results) trafia TYLKO w: notatki `research_notes/...` (3 pliki .md), `reports/Projekt mózgu muchy dla inwestorów.md`, `flymind/experiments/f1_active_sensing/stage1/RAPORT_ETAP1_PL.md`, `bio2/audit_and_validate.py` (tekst o serwie STS3215, nie sterownik), `assets/so101_upstream.xml` l. 24 (komentarz producenta o wzmocnieniach pozycji "Lerobot", nie sterownik). Żaden plik `.py` z `import lerobot/serial/scservo`. — wynik grep wykonany lokalnie
- Notatka własna: "W kodzie grep po lerobot|scservo|feetech|serial nie znalazł sterownika sprzętowego" i "Demo na prawdziwym ramieniu nie jest możliwe z obecnego kodu" — `research_notes/Projekt mózgu muchy dla inwestorów/nasze_wyniki.md` l. 44, 140
- Pamięć projektu: "ALL results are MuJoCo simulation (no hardware driver in repo) ... novelty only if it runs on real SO-101" — `/Users/admin/.claude/projects/-Users-admin-so101-fly-project/memory/explory-2026-competition.md`
- Raport końcowy V5v4: "brak fizycznego ramienia" — `flymind/V5v4_FINAL_REPORT.md` l. 19
- Zgoda: "sprzęt — tylko za osobną zgodą" (`flymind/VALIDATION_PLAN.md` l. 10, 536); "Walidacja na fizycznym SO-101 (po kalibracji kamery i serw)" jest w sekcji "Poza zakresem" (`flymind/VALIDATION_PLAN.md` l. 557); pamięć: "hardware still needs separate consent" (`memory/flymind-closed-loop-2026-10-28.md` l. 11) oraz "#1 priority = net on real SO-101 ..., needs Adam's explicit hardware go-ahead" (`memory/explory-2026-competition.md`).
- Pamięć "wait for explicit approval before Stage 1/commits/hardware" — `memory/flymind-f1-active-sensing-2026-11-01.md` l. 17
- Poza repo, na maszynie: LeRobot 0.6.2 zainstalowany edytowalnie z `/Users/admin/lerobot` (commit e624f3f7, 2026-09-24) w Pythonie miniforge; `feetech-servo-sdk 1.0.0`, `pyserial 3.5`, `opencv-python-headless 4.13.0.92`, `torchvision 0.26.0`, `av 15.1.0`, `datasets 4.8.5` — `/Users/admin/miniforge3/bin/pip3 list`
- LeRobot ma gotowy `SO101Follower = SOFollower` z `connect()`, `calibrate()`, `get_observation()`, `send_action()`, kamerami przez `make_cameras_from_configs`, opcją `max_relative_target` i `disable_torque_on_disconnect=True`; silniki `Motor(1..5,"sts3215")` — `/Users/admin/lerobot/src/lerobot/robots/so_follower/so_follower.py` l. 75-79, 114, 137, 204, 229, 266; `config_so_follower.py`. Są też polecenia `lerobot-find-port`, `lerobot-calibrate`, `lerobot-find-cameras`, `lerobot-find-joint-limits`, `lerobot-eval` w `/Users/admin/miniforge3/bin/`.

### Inferences
- Pod przełącznik na prawdziwym ramieniu jest do napisania cały "most sprzętowy" (host Mac -> LeRobot `SO101Follower`), ale kawałki biblioteczne (sterownik serw, kalibracja, kamery, ograniczenie `max_relative_target`) już leżą na dysku.

### Gaps
- Nie sprawdzałem, czy `/Users/admin/Robot_Sim_To_Real` (projekt Unity) lub `/Users/admin/Projects/hades_voice` zawierają coś o ramieniu (poza zakresem; to nie jest ten projekt).

## 2. Interfejs sterownika w symulacji: wejścia, wyjścia, gdzie jest P, gdzie tasowanie

### Takeaway
Pętla zamknięta jest jedna: `flymind/loop.py::run_trial(cond, ...)` z warunkami `snn`, `snn_shuffle`, `snn_swap`, `no_vision`, `classical_p`. To jest de facto już "przełącznik sterowników" (tylko w symulacji): wspólny enkoder, bramka czujnika, warstwa bezpieczeństwa i symulator; różni się tylko gałąź generująca `omega`. Sterowany jest tylko obrót podstawy (shoulder_pan), pozostałe stawy trzyma skrypt. Drugi tor (FlyArm, stawy 1-2 + szczęka) jest osobną klasą bez wspólnego interfejsu.

### Cited Findings
- Warunki: `CONDS = ("snn", "snn_shuffle", "snn_swap", "no_vision", "classical_p")` — `flymind/loop.py` l. ok. 66; opis warunków w nagłówku l. 17-27.
- Takt 10 ms (`TICKS, DT = 300, 0.01`), 3 s próby; SNN 10 x 1 ms na takt. Obserwacja: `sim.observe()` -> `SensoryGate` -> `TargetEncoder.encode(img)["g"]` (g = odpowiedź lewa/prawa z obrazu kamery "eye" 96x128) — `flymind/loop.py` l. 130-150; `flymind/so101.py` l. 73 (`cam_shape=(96,128)`, fovy 70).
- Gałąź SNN: `enc.currents(g, inL, inR, N)` -> `ALIF.run(I, 10)` -> `SteerDecoder.step(spikes)["omega"]` (DNa02 L-R, gain 2.5, w_max 1.0, tau 0.1 s) — `flymind/loop.py` l. 154-160, STEER l. 62.
- Gałąź regulator P (`classical_p`): `p_f` = filtr 1. rzędu na `g @ [1,-1]`, `omega = clip(gain * p_f / calib["slope_p"], +-w_max)`, SNN omijana, źródło `"classical:P_encoder"`; kalibracja `calibrate_p()` na tych samych bodźcach syntetycznych — `flymind/loop.py` l. 80-86 (calibrate_p), 150-153.
- Tasowanie połączeń: `snn_shuffle` = `visual_path.shuffle(spec, seed+100_000)` (podwójne zamiany krawędzi, `equal_weight` opcjonalnie) — `flymind/loop.py` l. ok. 107; `flymind/visual_path.py` l. 71-93. Inne warianty kontroli: `flymind/side_shuffle.py::shuffle_within_side`, `flymind/block_shuffle.py`, `flymind/experiments/fj2_fly_arm/shuffle_six_legs.py` (wyniki: `.../results/shuffle_six_legs.jsonl`).
- Wyjście -> ruch: `omega` -> `integrate_pan(pan_t, omega, DT)` (`PAN_LEFT=-1`) -> `Command(t, q_target{0..4}, jaw_torque, sources)` z etykietą źródła (`snn:`, `classical:`, `script:`) -> `SafetyLayer.step(cmd, q, now, sensor_age)` -> `sim.act(qt, tau)` — `flymind/loop.py` l. 161-170; `flymind/so101.py` l. 51-54.
- Warstwa bezpieczeństwa (`flymind/safety.py`, 154 l.): kolejność ograniczeń zakres-margines 0,05 rad -> prędkość `v_max=1.5 rad/s` -> wyprzedzenie `max_lead=(0.02,0.3,0.3,0.3,0.3)` rad względem pomiaru -> zakres; watchdog komendy 50 ms (`cmd_timeout`), `vision_stale` (max_sensor_age 50 ms) dla stawów wzrokowych, zatrzaśnięty `estop`/błąd czujnika, moment szczęki `tau_max` 1 N·m + odcięcie na krańcu, obowiązkowa etykieta źródła i liczniki interwencji per źródło; ZAKRESY czytane z MJCF (`ranges_from_mjcf`). Czego NIE ma: kolizji ze stołem i przestrzeni roboczej kartezjańskiej — `flymind/safety.py` l. 1-14, 40-56.
- Dokładny kontrakt wyjścia symulatora = wyjście safety: `act(q_target[5] rad, jaw_torque N*m)`; symulator odrzuca komendy łamiące kontrakt (`SimError`) — `flymind/so101.py` l. 10-13, 247-265. Kolejność stawów: shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper.
- Stałe, które trzeba by dopasować do prawdziwych serw: `v_max` "serwo STS3215 ok. 4,7 rad/s wg bio2" (`safety.py` l. 46, `bio2/agent.py` l. 30 `SERVO_SPEED=4.7`); chwytak symulowany jako silnik momentowy 3,35 N*m (PWM, tryb 2) (`so101.py` l. 66; `bio2/so101_base.py` l. 107), a prawdziwy LeRobot sterowałby POZYCJĄ — niezgodność trybu.
- FlyArm (`flymind/fly_arm.py`, 70 l.): wejścia = obraz (-> LC9 L/R) + dotyk padów (-> receptory szczecinkowe T2 L); wyjście = przyrosty celów stawów 1-2 (`shoulder_lift`, `elbow_flex`) i moment szczęki; etykieta źródła `"snn:vision_leg"`; sieć 5643 neurony, `SparseALIF` (CSR), J0 0,275, Glu -1; `FlyArm.step(image, touch, dt)` zwraca `(dq, tau, diag)` — `flymind/fly_arm.py` l. 1-70; opis mapowania `flymind/experiments/fj2_fly_arm/DESIGN.md`. Sieć z pilota dotyku T2L->T2R ma 10 036 neuronów — `.../PILOT_NOTES.md`.
- Pętla w demo przepisana 1:1 z `loop.run_trial` dla `snn` i `classical_p` (test równości trajektorii: `flymind/demo/test_demo.py`) — `flymind/demo/demo.py` l. 1-12. Zawiera też tryb "w czasie rzeczywistym" (takty doganiają zegar, max 6 na klatkę) — `demo.py` l. 620-675.
- Zasada nadrzędna: o zachowaniu decyduje wyjście SNN ("snn:..."), klasyczny kod tylko jako (a) warstwa bezpieczeństwa, (b) baseline/oracle, (c) jawne rusztowanie; "even at a cost in quality" — `memory/fly-must-control.md`. To wprost pasuje do ułożenia: SNN muchy = sterownik "of record", P i pi0 = ramiona porównawcze, safety = wspólna i niezależna.
- Wyniki symulacyjne istotne dla porównania: regulator P jest dokładniejszy i gładszy niż SNN (SNN oscyluje +-2 stopnie), SNN znacznie bardziej wrażliwa na opóźnienie (50 ms: 17/40 sukcesów, 100 ms: 7/20 vs 20/20 dla P), tasowanie testowało lateralizację siły wejścia, nie szczegółową topologię — `flymind/VALIDATION_PLAN.md` l. ok. 495-510 (V4/V5), `memory/explory-2026-competition.md`.

### Inferences
- Kontrakt `Command`/`SafetyLayer` jest już neutralny względem sterownika (etykiety `snn:`, `classical:`, `script:`). pi0 dałby się wpiąć jako kolejny sterownik ze źródłem `classical:`/nowym prefiksem (np. `vla:`) — ale `SOURCES` w `safety.py` l. 15 akceptuje tylko 3 prefiksy, więc dodanie czwartego wymaga zmiany tej stałej (zmiana pliku, nie robiona).
- pi0 wypuszcza akcje 6-D (stawy + chwytak) na obraz+stan+język; SNN/P sterują tylko `shoulder_pan` (ewentualnie lift/elbow w FlyArm). Uczciwe porównanie wymaga wspólnego zadania i ograniczenia pi0 do tego samego stawu albo jawnego opisu różnicy zakresu swobody.
- Wejście obrazu w obecnym kodzie to obraz 96x128 z kamery symulowanej na chwytaku ("oko-w-dłoni"). Prawdziwa kamera będzie miała inny rozmiar, ekspozycję, opóźnienie i kolor piłeczki; enkoder jest koloru (zielona piłeczka) i kalibrowany pod symulację.

### Gaps
- Nie znalazłem kodu mapującego prawdziwy obraz z kamery USB na `Frame` (jest tylko kontrakt `Frame` w `flymind/sensory.py` z uwagą "sprzęt: time.monotonic po stronie hosta i znacznik sterownika kamery"). Kalibracja enkodera dla prawdziwej kamery: brak.
- Nie ma kodu obsługującego brak odpowiedzi serwa/utratę komunikacji szeregowej (to by dodał mostek).

## 3. Środowisko Pythona i zainstalowane pakiety (LeRobot, torch, MPS, pi0)

### Takeaway
Dwa rozłączne środowiska. Projektowy `.venv` (Python 3.12.13: mujoco 3.17.0, numpy 2.5.4, scipy, pandas, matplotlib, glfw, brak pip) NIE ma lerobota ani torcha. Miniforge `python3` (3.14.7) MA lerobot 0.6.2, torch 2.11.0 z MPS dostępnym (`True`), ale NIE ma mujoco ani transformers (więc pi0 nie ruszy bez doinstalowania `lerobot[pi]`). Wagi pi0 nie są pobrane.

### Cited Findings
- `.venv/bin/python -c "import lerobot"` -> `ModuleNotFoundError`; `import torch` -> `ModuleNotFoundError`; `python -m pip` -> "No module named pip". Pakiety z `.venv/lib/python3.12/site-packages`: mujoco-3.17.0, numpy-2.5.4, scipy-1.18.1, pandas-3.1.0, pyarrow-26.0.0, matplotlib-3.11.2, glfw-2.11.0, pyopengl-3.1.10, websockets-17.3, pillow-13.0.0, etils, absl-py (BRAK opencv, BRAK torch, BRAK lerobot).
- `/Users/admin/miniforge3/bin/python3`: Python 3.14.7; `import lerobot, torch` -> lerobot `0.6.2` (`/Users/admin/lerobot/src/lerobot/__init__.py`), torch `2.11.0`, `torch.backends.mps.is_available()` = `True`; `import mujoco` -> ModuleNotFoundError; `import transformers` -> ModuleNotFoundError; cv2 4.13.0 działa. Pakiety: gymnasium 1.3.0, draccus 0.11.6, safetensors 0.8.0, huggingface_hub 1.33.0, rerun-sdk 0.33.1, pynput 1.8.2, fastapi 0.143.0, numpy 2.2.6, pandas 2.3.3, datasets 4.8.5, av 15.1.0, torchvision 0.26.0, torchcodec 0.11.1.
- Polityka pi w LeRobot: `pi = ["lerobot[transformers-dep]", "lerobot[scipy-dep]"]`, `transformers-dep = ["transformers>=5.4.0,<5.6.0"]` — `/Users/admin/lerobot/pyproject.toml` l. 160, 223. Politycy w drzewie: `pi0`, `pi05`, `pi0_fast`, `smolvla`, `act`, `diffusion`, `groot`, `xvla` itd. — `/Users/admin/lerobot/src/lerobot/policies/`. `modeling_pi0.py` importuje `transformers` warunkowo (`_transformers_available`).
- Cache HF: `~/.cache/huggingface/hub` ma 12 KB (puste, same pliki wersji) = żadne wagi pi0/paligemma nie są pobrane. `~/.cache/huggingface/lerobot/hub` zawiera jedynie zbiór `datasets--TaeJun123123--so101_lego_drop_real_50` (cudzy, pobrany 15 paź 2026; 50 epizodów, 30 fps, kamery `front` i `wrist` po 480x640x3, stan 6 stawów) — `.../meta/info.json`. To NIE dowodzi, że to nasz sprzęt.
- Inne środowiska: `/Users/admin/venv` Python 3.9.6 (pyvenv.cfg), zawiera m.in. sounddevice, pytest, coloredlogs (z projektem `hades_voice`, nie ten projekt); `uv` jest w `/Users/admin/.local/bin/uv` i miniforge.
- Wolne miejsce na dysku danych: 77 GiB wolne z 926 GiB (92 % zajęte) — `df -h /Users/admin`.
- Projektowe zasady uruchamiania: `python -I -B` (bez __pycache__), `--zgoda-sim` przy symulatorze, zakazane ziarna 0-39 i 300-399, nigdy import bio2 w `flymind/` — `flymind/NEXT_SESSION.md`, `flymind/loop.py` l. 28-33, `memory/flymind-audit-2026-10-28.md`.

### Inferences
- Przełącznik na prawdziwym ramieniu będzie musiał połączyć dwa środowiska: kod SNN (ALIF nie wymaga mujoco) z LeRobotem+torch (miniforge). Miniforge ma numpy 2.2.6 i pandas 2.3.3, ale NIE ma scipy (`import scipy` -> ModuleNotFoundError), a `alif_sparse.py` importuje `scipy.sparse`; `.venv` ma scipy 1.18.1, ale nie ma lerobota. Opcje: osobny proces SNN w `.venv` + gniazdo do procesu z lerobotem, albo doinstalowanie scipy w miniforge (zgoda). To decyzja do podjęcia, nic nie zmieniono.
- pi0 na Macu: MPS jest dostępny, ale pobranie wag (wiele GB) + `transformers` wymaga instalacji (zgoda), a 77 GiB wolnego miejsca jest wystarczające, lecz niezbyt komfortowe.

### Gaps
- Nie testowałem importu modułów flymind w miniforge (to byłoby wykonanie kodu projektu); wiadomo tylko, że scipy tam brakuje.
- Nie znam wersji pi0 w cache/na dysku (brak), ani wagi `lerobot/pi0_base` / `pi05_base` — pobranie nie było wykonywane.
- Czy pi0 działa płynnie na MPS (czas inferencji, brak operacji nieobsługiwanych) — nie mierzone; `grep mps` w `policies/pi0/*.py` nic nie znalazł.

## 4. Zmierzone prędkości pętli SNN i kosztowne etapy

### Takeaway
Pętla V5 (SNN 424 neurony, render 96x128) ma w symulacji takt p50 4,3 ms, p99 6,2 ms (cel 10 ms) na tym Macu; dominuje render. Dla większych sieci (FlyArm, 5-10 tys. neuronów) w plikach NIE ma zmierzonego czasu taktu na prawdziwej pętli — jest tylko syntetyczny pomiar gęstego ALIF i sam fakt użycia macierzy rzadkiej.

### Cited Findings
- Maszyna pomiaru: "macOS arm64, 10 rdzeni" — `flymind/VALIDATION_PLAN.md` l. 507; ta sama maszyna: Apple M1 Max, `MacBookPro18,4`, `hw.memsize` = 34 359 738 368 B (32 GiB) — `sysctl hw.memsize`, `sysctl -n machdep.cpu.brand_string`, `sysctl -n hw.model`.
- B1 (3 x 3000 taktów, cały takt mierzony): p50 ~4,1 ms, p99 ~8,2-8,5 ms, 1-7 taktów > 10 ms; render (`observe`) p50 ~3,5 ms; cel p99 < 7 ms i 0 przekroczeń NIE spełniony — `flymind/VALIDATION_PLAN.md` l. 512-513.
- B2 gęsty ALIF, krok 1 ms: 0,02 ms (N=272), 0,11 (1000), 3,2 (3000), 14,4 ms (10 000); N=10 000 wymaga macierzy rzadkiej — `VALIDATION_PLAN.md` l. 514-515; `flymind/bench_loop.py` l. 240-265.
- Pętla V5 potwierdzająca (40 prób x 300 taktów, warunek snn): takt p50 4,3 ms, p99 6,2 ms, max 16,4 ms, 50/12 000 taktów > 10 ms (0,4 %). Etapy (przy równoległym agencie, zawyżone): observe/render p50 8,1 ms, enkoder 0,26 ms, SNN 424 n x 10 kroków 0,43 ms, dekoder 0,06 ms, safety 0,02 ms, fizyka 0,14 ms — `VALIDATION_PLAN.md` l. 516-522.
- B3 (opóźnienia komponentowe, skok prądu PFL3, nie obraz): pierwszy spike DNa02 12 ms, połowa zmiany L-R 30 ms, znak omega 80 ms (DNa02); reakcja omega na bodziec ~40 ms przy 2 Hz (V4) — `VALIDATION_PLAN.md` l. 516-522.
- Czułość na opóźnienie (z ostrzeżeniem, że przy 50 ms safety częściowo kształtuje zachowanie): 50 ms 17/40 sukcesów SNN; 100 ms 7/20 vs P 20/20 — `VALIDATION_PLAN.md` l. ok. 495-503. Cykl graniczny SNN (próg ALIF -> quasi-dwustan, filtry odczytu) wskazany jako źródło wrażliwości na opóźnienie, zadanie otwarte — l. 540.
- Kod do pomiaru opóźnień: `flymind/latency.py` (`StageTimer`, `summarize` p50/p95/p99, `DelayLine`, `env_info`), `flymind/bench_loop.py` B1-B3 (bramki `--zgoda-bench`).
- Demo zapisuje `fps`, `ms_per_s` per etap w JSON (`demo.py` l. 757-762) — nie znalazłem zapisanego wyniku dla FlyArm.

### Inferences
- Dla ruchu na prawdziwym ramieniu 100 Hz (takt 10 ms) SNN-owi z 424 neuronami wystarcza z zapasem; budżet czasu zajmie kamera USB (opóźnienie ekspozycji + transfer, nie mierzone) i serwo (STS3215 po magistrali szeregowej). Dla pi0 inferencja na MPS to osobna nieznana (zwykle jednostki-dziesiątki Hz; brak własnych pomiarów, nie podaję liczby).
- Dla przełącznika "uczciwie czasowo": SNN (takt 10 ms) i P mogą działać w 100 Hz, pi0 w niższej częstotliwości z kolejką akcji (action chunk) — porównanie wymaga wspólnego zegara i rejestrowania opóźnienia end-to-end dla każdego sterownika.

### Gaps
- Brak pomiaru czasu taktu dla FlyArm (5-10 tys. neuronów, SparseALIF) w pętli — tylko opis konstrukcji (`alif_sparse.py`).
- Brak pomiaru opóźnienia prawdziwej kamery i magistrali serw; brak pomiaru czasu inferencji pi0 na tym Macu.

## 5. Sprzęt, którego używamy (tylko z dowodów w plikach / poleceniach tylko-do-odczytu)

### Takeaway
Fizyczny SO-101 NIE jest udokumentowany w plikach projektu jako posiadany. Są dowody MODELU (SO-101 z serwami STS3215 w pliku producenta MJCF) i dowody, że w przeszłości (1 paź 2026) na tym Macu skalibrowano follower SO-101 przez LeRobot, ale bez portu, kamer ani leadera w konfiguracji. Aktualnie do Maca nie jest podłączone żadne urządzenie USB-szeregowe, a jedyną kamerą jest wbudowana FaceTime HD. Czujniki dotyku/siły istnieją TYLKO w modelu MuJoCo.

### Cited Findings
Legenda: [FIZ] = dowód na fizyczny element; [SYM] = tylko w modelu MuJoCo / założenie; [?] = NIEZNANE.

Komputer (fizyczny, zmierzony teraz)
- [FIZ] Apple MacBook Pro `MacBookPro18,4`, chip Apple M1 Max, 32 GiB RAM, macOS Darwin 27.2.0, 10 rdzeni — `sysctl -n hw.model`, `sysctl -n machdep.cpu.brand_string`, `sysctl hw.memsize`; "10 rdzeni" z `flymind/VALIDATION_PLAN.md` l. 507.
- [FIZ] Kamera wbudowana: `FaceTime HD Camera` (jedyna kamera, `Model ID: FaceTime HD Camera`) — `system_profiler SPCameraDataType` (liczba "Model ID" = 1). Rozdzielczość i tryb: NIEZNANE — nie znaleziono w plikach (nie uruchamiałem `lerobot-find-cameras`, bo otwiera kamerę).
- [FIZ] Brak podłączonych urządzeń USB w chwili pomiaru: `system_profiler SPUSBDataType` zwraca puste drzewo (0 wierszy treści); `ls /dev/tty.* /dev/cu.*` pokazuje tylko `Bluetooth-Incoming-Port` i `debug-console` — czyli żadnej magistrali serw Feetech (zwykle `/dev/tty.usbmodem*`/`usbserial*`) ani adaptera nie widać. Wniosek: ramię nie jest teraz podłączone.

Ramię i serwa
- [SYM] Model ramienia: oficjalny SO-101 (TheRobotStudio, onshape-to-robot) w MJCF — `assets/so101_upstream.xml`; komentarz `bio2/so101_base.py` l. 1-3; `flymind/so101.py` (UPSTREAM). Siatki STL zawierają części: `sts3215_03a_v1.stl`, `sts3215_03a_no_horn_v1.stl`, `waveshare_mounting_plate_so101_v2.stl`, `wrist_camera_so101_v1.stl`, `wrist_camera_mount_so101_v1.stl` — `assets/so101_meshes/` (modele CAD producenta; sama obecność STL NIE dowodzi, że kupiono te części).
- [SYM/specyfikacja] Serwa: 6 x Feetech STS3215 (shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper) — `RESULTS.md` l. 3; `assets/so101_upstream.xml` l. 156-163 (`class="sts3215"`, forcerange +-3,35 N*m); `/Users/admin/lerobot/src/lerobot/robots/so_follower/so_follower.py` l. 75-79 (ID 1-6, `sts3215`). Napięcie zasilania, wersja przełożenia (np. 1/345 vs 1/191 vs 1/147), liczba i rodzaj kontrolerów (np. Waveshare Bus Servo Adapter): NIEZNANE — nie znaleziono w plikach.
- [FIZ, pośredni] Kalibracja follower SO-101 istnieje na tej maszynie: `~/.cache/huggingface/lerobot/calibration/robots/so_follower/so101_follower.json` (zmodyfikowany 1 paź 2026, 917 B), ID serw 1-6, np. `shoulder_pan` homing_offset -1933, range 646-3403 (surowe kroki 0-4095); `wrist_roll` range 0-4095, `gripper` 2028-3530. To znaczy, że kiedyś ramię było podłączone i skalibrowane przez LeRobot na tym Macu, ale: czy to TO ramię i czy nadal jest u autora — NIEZNANE — nie znaleziono w plikach projektu.
- [FIZ, pośredni] Profil robota LeRobot `~/.cache/huggingface/lerobot/robots/so-101.json` (20 cze 2026) ma PUSTE pola: `leader_port: ""`, `follower_port: ""`, `cameras: []` — brak zapisanego portu i kamer.
- [?] Ramię leader (teleoperacja): NIEZNANE — nie znaleziono w plikach (brak pliku kalibracji `so_leader`).
- [?] Port szeregowy ramienia, baudrate, ID kontrolera: NIEZNANE — nie znaleziono w plikach (LeRobot domyślnie ma 1 Mbps wg biblioteki Feetech, ale nie sprawdzałem konfiguracji tutaj).
- [?] Notatka o zakupie/dostępności fizycznego SO-101 u autora: "Nie znalazłem notatek o zakupie/dostępności fizycznego SO-101 u autora" — `research_notes/Projekt mózgu muchy dla inwestorów/nasze_wyniki.md` l. 144. Cena "~130 USD" dotyczy ogólnie SO-101 (rynek), nie dowód zakupu — `.../rynek_inwestorzy.md` l. 156.

Kamera(y) ramienia
- [SYM] Kamera "eye" w MuJoCo: zamocowana na ciele `gripper` (oko w dłoni), `cam_pos=(0.016,-0.03,-0.03)` m, `cam_quat=(0,0,0,1)`, `fovy=70`, obraz 96x128 (H x W), kolory kontrastowe, bez cieni — `flymind/so101.py` l. 69-74 (SceneCfg). Wprost: "orientacja obrazu niezweryfikowana statycznie". Pochodzi z `bio2/scene2.py` (commit `f2ffcf1` 2026-10-23: "kamera oko-w-dłoni").
- [?] Kamera na PRAWDZIWYM ramieniu (model, rozdzielczość, mocowanie nadgarstek/przód): NIEZNANE — nie znaleziono w plikach. Jedyne sugestie to STL `wrist_camera_so101_v1.stl` / `wrist_camera_mount_so101_v1.stl` (element CAD producenta) i obcy zbiór `TaeJun123123/so101_lego_drop_real_50` z kamerami `front`+`wrist` 640x480 — to cudzy dataset, nie dowód naszej konfiguracji.
- [FIZ] W razie braku zewnętrznej kamery dostępna jest tylko wbudowana FaceTime HD (patrz wyżej).

Czujniki dotyku / siły / inne
- [SYM] Czujniki dotyku `cs_fixed`, `cs_moving`, `cs_palm` (MuJoCo `touch`, jednostka N) na wewnętrznych powierzchniach szczęk i dłoni — TYLKO w modelu symulacji: `bio2/so101_base.py` l. 29, 88, 117; `flymind/so101.py` l. 8-9 (`touch[3]`, TOUCH), odczyt `d.sensor(s).data[0]`. Komentarz: "jaw grip on ball gives only ~0.28 N touch (pad placement untuned)" (`memory/flymind-audit-2026-10-28.md`). Żaden fizyczny czujnik siły/dotyku (FSR, tensometr, taktylny) nie jest opisany w plikach: NIEZNANE — nie znaleziono w plikach.
- [FIZ, wewnętrzne] Odczyt pozycji stawów (enkodery magnetyczne w STS3215) przejdzie przez `get_observation()` LeRobota (klucze `*.pos`); w pętli projektowej to "propriocepcja" `obs.q[6]` — potwierdzone tylko jako część API LeRobota, nie testowane na sprzęcie.
- [SYM] Stosowane w FlyArm "dotyk -> receptory szczecinkowe T2 L" bierze wejście z symulowanych padów `cs_*` (`flymind/fly_arm.py` l. 45-52, 60-63). Odczyt prądu/obciążenia serw (STS3215 raportuje obciążenie/temperaturę) — jako zamiennik czujnika dotyku nie jest nigdzie użyty: NIEZNANE/niezaimplementowane.
- [?] IMU, czujniki odległości, enkodery zewnętrzne: NIEZNANE — nie znaleziono w plikach.

Stół, piłeczka, oświetlenie (scena)
- [SYM] Piłeczka r = 2,5 cm (średnica 5 cm), 50 g, zielona; stół z=0; tło za stołem — `flymind/so101.py` SceneCfg l. 75-81. Fizyczna piłeczka (kolor, średnica) i stół: NIEZNANE — nie znaleziono w plikach.

### Inferences
- Wszystkie WYNIKI w projekcie pochodzą z symulowanego sprzętu: kamera, dotyk i piłeczka są modelem. Przeniesienie na prawdziwe ramię wymaga co najmniej: realnej kamery (innej niż symulowana 96x128), kalibracji enkodera pod jej kolor/ekspozycję, mapowania prawdziwych pozycji serw (kroki -> radiany; kalibracja LeRobot daje przesunięcia i zakresy), braku odpowiednika "touch" (więc FlyArm z dotykiem nie przenosi się 1:1).
- Fakt, że kalibracja `so101_follower.json` istnieje (1 paź 2026), jest przesłanką, że jakieś ramię SO-101 kiedyś było podłączone do tego Maca; ale wymaga potwierdzenia od autora (czy jest u niego, czy jest w pełni sprawne, jaka kamera, jakie zasilanie).

### Gaps
- Pytanie do właściciela (jedyne źródło prawdy): czy ma fizyczne ramię SO-101 (follower + ewentualnie leader), jaką kamerę (model, USB, czy na nadgarstku), jaki zasilacz i adapter Feetech, gdzie je ma, i zgoda na użycie sprzętu.
- Nie sprawdzałem repozytorium git pod kątem dawnych plików z konfiguracją sprzętu (tylko `git log --oneline` z grepem po słowach kluczowych: trafienie wyłącznie symulacyjne).

## 6. Czego brakuje do porównania na prawdziwym ramieniu: sterownik SNN muchy vs pi0 vs regulator P vs SNN przetasowana

### Takeaway
Do mostu brakuje (a) kodu I/O sprzętu, (b) przetwarzania prawdziwej kamery, (c) adaptera pi0 (pakiety, wagi, polityka, ewentualny fine-tuning), (d) warstwy bezpieczeństwa dla prawdziwego robota i (e) wspólnego protokołu/ziaren. Sam przełącznik na poziomie `Command` jest już prawie gotowy dzięki `loop.py` + `safety.py`.

### Cited Findings (stan zastany) i lista braków
Co jest (można użyć):
- Wspólny kontrakt `Frame -> encoder -> sterownik -> Command(źródło) -> SafetyLayer -> act()` w `flymind/` (patrz sekcja 2); warunki snn / snn_shuffle / classical_p już zaimplementowane w `loop.py`; tasowania w `visual_path.py`, `side_shuffle.py`, `block_shuffle.py`.
- Biblioteka LeRobot z `SO101Follower` (poza repo, miniforge), `feetech-servo-sdk`, `pyserial`, `opencv`, torch+MPS.
- Rejestr ziaren i integralność kodu (`SEED_REGISTRY.md`, hashe manifestu, `integrity_*.py`) — metodologia, którą trzeba zachować dla prawdziwych prób.

Czego brakuje (każdy punkt zweryfikowany brakiem w plikach/na dysku):
1. Sterownik sprzętu: brak `RealSO101` zgodnego z `SO101Sim` (`reset/observe/act/step/close`) — nic w repo nie importuje lerobot/feetech/serial. Trzeba napisać adapter: `get_observation()` -> `Obs(frame, q[6] rad, qd, touch)`, `send_action()` z konwersją rad <-> jednostki LeRobota (kalibracja jest w `so101_follower.json`). Musi zachować kontrakt `SimError`-podobnych odrzuceń.
2. Wykrycie/mapowanie sprzętu: port ramienia i kamery nie są zapisane (`so-101.json` ma puste pola); `/dev/tty.*` nie pokazuje żadnego urządzenia szeregowego (ramię nie jest teraz podłączone); trzeba `lerobot-find-port` / `lerobot-find-cameras` (wymaga zgody i fizycznego podłączenia).
3. Kamera: kod mapujący prawdziwy obraz na `Frame` z zegarem monotonicznym i znacznikiem czasu; enkoder (`encoder.py`) skalibrowany dla symulacji (zielona piłeczka, 96x128, blur_px=3) — brak kalibracji na prawdziwych obrazach, brak pomiaru opóźnienia kamery; kamera "eye" jest w symulacji na chwytaku, realne mocowanie nieznane.
4. Różnice tryb/sprzęt: symulowany chwytak to silnik momentowy PWM (3,35 N*m), prawdziwy LeRobot steruje pozycją; `safety.jaw_torque` nie ma odpowiednika; stałe `v_max`, `max_lead`, `tau_max`, `margin` to wybory projektu/symulacji, nie zmierzone na serwach; brak kolizji ze stołem i przestrzeni roboczej w safety (`safety.py` l. 13) — to istotny brak przy prawdziwym ramieniu. LeRobot ma `max_relative_target` jako drugą, niezależną barierę (rekomendowana).
5. Warstwa bezpieczeństwa sprzętowa: potrzebny przycisk/skrót E-stop (`safety.estop()` jest, ale nic go nie wywołuje z zewnątrz), obsługa utraty komunikacji szeregowej, wyłączanie momentu przy rozłączeniu (`disable_torque_on_disconnect=True` w LeRobocie), limity prądu/temperatury serw. Brak testów na sprzęcie (`test_safety.py` używa zastępczego serwa, "nie jest modelem fizyki").
6. pi0: brak `transformers` w miniforge i w `.venv`; brak wag (`~/.cache/huggingface/hub` puste); brak adaptera polityki (LeRobot `policies/pi0` istnieje, ale wymaga instalacji `lerobot[pi]` i pobrania checkpointu, np. bazowego, oraz zwykle fine-tuningu na danych tego zadania — brak naszych danych demonstracyjnych: `~/.cache/huggingface/lerobot/outputs/train` puste; tylko cudzy zbiór `so101_lego_drop_real_50`). Brak definicji zadania w języku dla pi0 i brak ograniczenia akcji do `shoulder_pan` (SNN steruje tylko podstawą). Brak pomiaru czasu inferencji na MPS.
7. Źródło sterownika w safety: `SOURCES = ("snn:","classical:","script:")` — brak etykiety dla pi0 (np. `vla:`); zmiana pliku z historią zamrożonych hashy (Stage 1/manifesty), więc wymaga jawnej decyzji i nowego manifestu.
8. Przełącznik: brak jednego wejściowego CLI/obiektu wybierającego sterownik w czasie pracy na sprzęcie (w `loop.py` jest `cond`, w `fly_arm.py` osobna klasa); brak jednolitej abstrakcji `Controller.step(obs)->Command` (każdy tor ma własny kod w `run_trial`).
9. Protokół: brak zarejestrowanego protokołu/ziaren dla prób na sprzęcie, brak definicji metryki w świecie rzeczywistym (jak mierzyć namiar piłeczki bez prawdy z symulatora: `bearing()` używa pozycji piłeczki z symulatora "TYLKO do oceny"), brak systemu śledzenia (np. znacznik/AprilTag lub drugi widok) do pomiaru błędu na prawdziwej scenie; brak zgody użytkownika na sprzęt ("tylko za osobną zgodą").
10. Wyniki symulacji przemawiają za ostrożnością: P > SNN pod względem dokładności, SNN wrażliwa na opóźnienie (50 ms: 17/40 sukcesów), tasowanie nie zawsze niszczy zachowanie — przed prawdziwą pętlą trzeba zmierzyć łączne opóźnienie kamera+USB+serwo i porównać z progiem (`VALIDATION_PLAN.md`).

### Inferences
- Minimalna ścieżka bez zmiany zamrożonego kodu: nowy plik (np. adapter `RealSO101` + skrypt przełącznika) w `flymind/`, importujący `loop`, `safety`, `encoder`, `visual_path` bez edycji, z jawnym nowym prefiksem źródła tylko w nowym kodzie (lub opakowaniem `Command` z etykietą `classical:vla_pi0`), co omija konieczność zmiany `safety.SOURCES` ale mniej uczciwie etykietuje. To decyzja, nie rekomendacja zmiany.
- Reguła nadrzędna "mucha musi sterować" oznacza, że pi0 i P to ramiona porównawcze, a safety to wspólna warstwa; w raporcie trzeba pokazać interwencje safety per źródło (już liczone w `safety.stats["per_source"]`).

### Gaps
- Czy autor chce uruchamiać pi0 lokalnie na M1 Max (32 GiB) czy zdalnie; jaki rozmiar/wariant pi0 (np. pi0_base, pi05, pi0_fast, smolvla jako lżejszy) — brak decyzji w plikach.
- Czy istnieje zbiór demonstracji tego zadania (obrót podstawy do piłeczki) — nie znaleziono.
