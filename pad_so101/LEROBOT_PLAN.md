# Pad → LeRobot: uczenie ramienia przez pokazywanie (plan)

Stan: 2026-11-07. **Aktualizacja tego samego dnia:** zgodnie z decyzją — od razu prawdziwe ramię, bez symulacji.
Zrobione: `record.py` (zamiast wtyczki z kroku 3 — własny skrypt nagrywania z naszym STOP i warstwą bezpieczeństwa),
środowisko `~/miniforge3/envs/lerobot` (Python 3.12), test zapisu i próbna nauka ACT (2 kroki) przechodzą.
Instrukcja: `NAGRYWANIE.md`. Kroki 1–2 (symulacja) pominięte. Dalej: podłączyć ramię i kamerę.

Pierwotny plan poniżej. Źródła sprawdzone tego dnia (kod lerobot na dysku, GitHub API, dokumentacja LeRobot).

## Odpowiedź w skrócie

**Tak, da się.** Pomysł nazywa się *uczenie przez naśladowanie*:
1. sterujesz ramieniem padem i robisz zadanie (np. „podnieś klocek i odłóż do pudełka") ok. 50 razy;
2. komputer nagrywa każdy pokaz: obraz z kamer i pozycje stawów;
3. sieć neuronowa (ACT albo SmolVLA) uczy się na tych nagraniach, co robić, gdy widzi daną scenę;
4. potem ramię robi zadanie samo, a Ty trzymasz pad tylko do STOP.

Nasz pad jest do tego dobrze przygotowany. Już daje to, czego potrzebuje LeRobot: cel każdego stawu i chwytaka.
Prawdziwe ramię też obsługujemy tą samą klasą co LeRobot (`SOFollower`). Brakuje trzech rzeczy:
- **kamer** (sieci uczą się z obrazu);
- **zapisu nagrań w formacie LeRobot**;
- **wtyczki**, dzięki której gotowe komendy LeRobot widzą nasz pad.

**Ważne (zasada projektu):** ramię nauczone z pokazów to **nie jest mucha**. To klasyczna linia bazowa (`classical:`).
Może się przydać do uczciwego porównania z mózgiem muchy, ale nigdy nie jest wynikiem muchy.

## Co sprawdziłem

| Fakt | Gdzie |
|---|---|
| Na komputerze jest lerobot 0.6.2 (`/Users/admin/lerobot`, środowisko `~/miniforge3`) | `pyproject.toml`, git e624f3f7 |
| Ramię SO-101 w LeRobot przyjmuje komendy `shoulder_pan.pos` … `wrist_roll.pos` w **stopniach**, a `gripper.pos` w skali 0–100 | `robots/so_follower/so_follower.py:71-80, 88` |
| Wbudowany pad LeRobot (`gamepad`) daje tylko przesunięcia końcówki x/y/z + chwytak otwórz/zamknij. Wymaga modelu URDF i biblioteki `placo` (kinematyka odwrotna). Nasz pad jest bogatszy: 5 stawów, biegi, sloty, STOP | `teleoperators/gamepad/teleop_gamepad.py:104-130`, `model/kinematics.py` |
| Własne urządzenia podłącza się jako pakiet o nazwie `lerobot_teleoperator_…`; LeRobot sam go znajduje | `utils/import_utils.py:244-256` |
| Klasa pada musi mieć: `action_features`, `feedback_features`, `is_connected`, `is_calibrated`, `connect`, `calibrate`, `configure`, `get_action`, `send_feedback`, `disconnect` | `teleoperators/teleoperator.py` |
| Nagrywanie: `lerobot-record`. Uruchamianie nauczonej sieci: `lerobot-rollout` | `scripts/` |
| Danych potrzeba: „co najmniej 50 pokazów, po 10 na każde miejsce". Dla SmolVLA 25 pokazów „nie wystarczyło" | dokumentacja LeRobot: il_robots, smolvla |
| Kamery w przykładach SO-101: dwie (`wrist` na chwytaku + `top` z góry), 640×480, 30 kl./s | il_robots |
| Czas nauki ACT, 50 pokazów, 5 epok: Mac M1–M3 **Max** ok. 6–14 h. RTX 4090: 30–60 min. W chmurze HF Jobs: `--job.target=…` (płatne) | hardware_guide |

## Podobne projekty na GitHubie

| Repo | ★ | Ostatnio | Licencja | Co z niego weźmiemy |
|---|---|---|---|---|
| [johnsutor/so101-nexus](https://github.com/johnsutor/so101-nexus) | 51 | 2026-11-02 | Apache-2.0 | **Najbliżej celu.** SO-101 w MuJoCo + gotowe zadania (podnieś, przenieś), nagrywanie w formacie LeRobot, uczenie i RL. Steruje się tam ramieniem-prowadzącym (którego nie mamy), więc nasz pad byłby nowym źródłem sterowania |
| [maskjp/lerobot_teleoperator_gamepad](https://github.com/maskjp/lerobot_teleoperator_gamepad) | 0 | 2026-08-14 | **brak** | Gotowy wzór wtyczki pada (pygame, tryb stawów). Brak licencji = wolno tylko podejrzeć, nie kopiować kodu |
| [TheRobotStudio/SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100) | 8028 | 2026-10-06 | Apache-2.0 | Oficjalne modele SO-101 (URDF/MuJoCo) — do sprawdzenia, czy nasz model w `flymind/so101.py` się zgadza |
| [huggingface/gym-hil](https://github.com/huggingface/gym-hil) | 237 | 2026-09-24 | Apache-2.0 | Wzór „człowiek z padem poprawia robota w symulacji" (ramię Franka, nie SO-101) |
| [SinfonIAUniandes/lerobot_robot_so101_mujoco](https://github.com/SinfonIAUniandes/lerobot_robot_so101_mujoco) | 3 | 2026-05-27 | brak | Symulacja SO-101 udająca prawdziwe ramię w LeRobot — tylko do podejrzenia |

Nie znalazłem gotowego repo „SO-101 + pad Xbox w stawach". Nasz pad wypełnia tę lukę.

## Plan krok po kroku

Każdy krok ma warunek „gotowe, gdy…". Kroki 1–2 nie wymagają żadnego sprzętu.

**Krok 1 — nagrywanie w symulacji.** Do `run.py` dochodzi tryb nagrywania pokazów:
- na symulacji renderują się 2 kamery (chwytak + z góry);
- każdy pokaz zapisuje się jako LeRobotDataset, lokalnie, bez wysyłania do internetu;
- przyciskami pada: start/koniec pokazu, „powtórz ten pokaz".

Gotowe, gdy przeglądarka nagrań LeRobot (`lerobot-dataset-viz`) otwiera nagrany pokaz z obrazem i ruchem stawów.

Do sprawdzenia przy tym kroku: lerobot jest w `~/miniforge3` (Python 3.14), a symulacja w `.venv`. Trzeba ustalić, w którym środowisku to uruchamiać.

**Krok 2 — pierwsza nauczona sieć (symulacja).**
- 50 pokazów prostego zadania, np. „przesuń piłeczkę do celu";
- nauka ACT na Macu przez noc;
- test: 20 prób w symulacji, liczymy, ile się udało.

Gotowe, gdy znamy ten wynik. Nawet słaby wynik jest cenny, bo cała droga będzie już przetarta.

**Krok 3 — wtyczka `lerobot_teleoperator_xboxpad`.** Mały pakiet w `pad_so101/`, który owija nasz `Controller`:
- `get_action()` zwraca stopnie dla 5 stawów i 0–100 dla chwytaka;
- można wtedy używać zwykłych komend: `lerobot-record --robot.type=so101_follower --teleop.type=xboxpad …`.

Otwarta kwestia: pad musi znać pozycję ramienia na starcie (inaczej pierwszy ruch byłby skokiem). Do rozwiązania: start z pozycji domowej z wolnym dojazdem albo przez `send_feedback`.

Gotowe, gdy `lerobot-teleoperate` steruje prawdziwym ramieniem z pada.

**Krok 4 — prawdziwe ramię.**
- 2 kamery (zgodnie z wyborem kamer: OV9281 + druga);
- 50 pokazów na stole;
- nauka;
- `lerobot-rollout` z padem w ręce do STOP, na biegu 1, przy wyłączniku zasilania.

Gotowe, gdy znamy wynik na prawdziwym stole (np. 10 prób).

## Czego nie wiadomo (uczciwie)

- Czy ACT da radę bez kamer. Dokumentacja tego nie opisuje, więc zakładam, że kamery są potrzebne.
- Jaki procesor ma ten Mac. Czasy 6–14 h podano dla M1–M3 Max; na słabszym Macu nauka potrwa dłużej.
- Czy model symulacji zgadza się z prawdziwym ramieniem na tyle, żeby nagrania z symulacji pomagały na prawdziwym stole. Bezpieczniej założyć, że na prawdziwym ramieniu trzeba nagrać od nowa.
- Wtyczka pada w `lerobot-rollout` (przejęcie sterowania w trakcie) — widziana w kodzie, nie sprawdzona w działaniu.
