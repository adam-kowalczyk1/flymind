# pad_so101 — sterowanie SO-101 padem Xbox (Series S)

Osobny folder. **Nie zmienia żadnego pliku w `flymind/`** — tylko czyta (importuje) dwa z nich:
`flymind/so101.py` (symulacja MuJoCo) i `flymind/safety.py` (warstwa bezpieczeństwa: zakresy, prędkość, STOP).

To jest **ręczne sterowanie człowieka** (narzędzie: demo, testy ramienia, nagrywanie tras), a nie mózg muchy.
Wyniki z pada nigdy nie są wynikami „muchy" — źródło komend jest oznaczone `classical:pad`.

## Jak patrzysz na ramię

Kamera w oknie stoi **za ramieniem** i patrzy tam, gdzie ramię sięga. Dzięki temu:
gałka w prawo = ramię w prawo na ekranie, gałka do przodu = ramię do przodu.

## Mapa przycisków

| Element pada | Tryb STAWY (domyślny) | Tryb KARTEZJAŃSKI (tylko symulacja) |
|---|---|---|
| Lewa gałka ←→ | obrót podstawy (lewo/prawo) | obrót podstawy (lewo/prawo) |
| Lewa gałka ↑↓ | bark: pochyl ramię do przodu / do tyłu | chwytak bliżej / dalej (poziomo) |
| Prawa gałka ↑↓ | łokieć: chwytak w górę / w dół | chwytak w górę / w dół (pionowo) |
| Prawa gałka ←→ | obrót nadgarstka | obrót nadgarstka |
| RB / LB | nadgarstek: nos chwytaka w górę / w dół | to samo; bez RB/LB chwytak **trzyma swój kąt** |
| RT (prawy spust) | zamykaj chwytak — im mocniej, tym szybciej | to samo |
| LT (lewy spust) | otwieraj chwytak | to samo |
| **X** | przełącz tryb STAWY ↔ KARTEZJAŃSKI | |
| **Y** | wróć do pozycji startowej (płynnie) | |
| **A** | jedź do pozycji zapisanej w bieżącym slocie | |
| **B** | zapisz bieżącą pozycję w bieżącym slocie (wibracja = zapisano) | |
| D-pad ↑ / ↓ | bieg: wolno / normalnie / szybko | |
| D-pad ← / → | slot 1–4 | |
| R3 (wciśnij prawą gałkę) | nagrywanie trasy: start / stop (zapis do `recordings/`) | |
| **≡ Menu** | odtwórz nagraną trasę / przerwij; po STOP — **wznów** | |
| **⧉ View** | **STOP** (zatrzaśnięty: ramię trzyma pozycję, nic nie rusza) | |
| Xbox, Share, L3 | wolne (macOS przechwytuje przycisk Xbox) | |

Zasady, żeby było intuicyjnie i bezpiecznie:
- Ruch gałką **zawsze przerywa** automatyczny ruch (Y, A, odtwarzanie) — człowiek ma pierwszeństwo.
- Gałki mają martwą strefę i łagodny start (mały wychył = bardzo precyzyjny ruch).
- Krótka wibracja: zapisano / zmiana trybu. Długa: STOP. Słaba: staw doszedł do krańca.
- Pad się rozłączył → automatyczny STOP. Po ponownym połączeniu wznowienie tylko przez ≡ Menu.
- Klawiatura: `Esc` wyjście, `R` reset sceny (piłeczka wraca na stół).

## Uruchomienie

Symulacja (działa od razu):

```bash
.venv/bin/python pad_so101/run.py
```

Prawdziwe ramię (NIESPRAWDZONE — ramię nie było podłączone przy pisaniu kodu): środowisko `~/miniforge3/envs/lerobot`
(Python 3.12 + lerobot + pygame-ce; w głównym `~/miniforge3` z Pythonem 3.14 komendy lerobot nie działają). Pierwsze uruchomienie: bieg 1 (wolno), ręka przy wyłączniku zasilania,
każdy staw ruszyć osobno i sprawdzić kierunek. Zły kierunek → strona ustawień, sekcja „Prawdziwe ramię".

```bash
~/miniforge3/envs/lerobot/bin/python pad_so101/run.py --real /dev/tty.usbmodemXXXX
```

Na prawdziwym ramieniu: tryb KARTEZJAŃSKI wyłączony (brak sprawdzonego dopasowania modelu do ramienia),
`Esc` najpierw płynnie wraca do pozycji startowej, potem rozłącza. Serwa zostają pod momentem (ramię nie opada) —
po skończeniu odłóż ramię i wyłącz zasilanie.
STOP z pada to STOP programowy; prawdziwy wyłącznik awaryjny = wyłącznik zasilania.

## Strona ustawień

```bash
.venv/bin/python pad_so101/settings.py
```

Otwiera w przeglądarce stronę z ustawieniami: czułość gałek (martwa strefa, krzywa precyzji), odwracanie osi,
prędkości trzech biegów, zmiana przycisków („Naucz" → wciśnij przycisk na padzie), wibracje, kierunki stawów
prawdziwego ramienia. Na górze realistyczny pad na żywo: każdy przycisk ma opis, co zrobi ramię (opisy zmieniają się razem z mapą przycisków), mapki gałek ze śladem ruchu i martwą strefą, przycisk „Sprawdź wibracje". **Zapisz** → `settings.json`; działający `run.py` wczytuje zmiany
w ciągu 1 s, bez restartu. Złe wartości są odrzucane (np. jeden przycisk dla dwóch akcji, prędkość ponad 1,5 rad/s).

## Pliki

- `control.py` — logika pada → cele stawów (bez pygame, bez mujoco; testowalna)
- `pad.py` — odczyt pada przez SDL GameController (nazwy przycisków standardowe, nie zgadywane indeksy)
- `run.py` — okno: symulacja MuJoCo + podgląd + legenda; albo prawdziwe ramię (`--real`)
- `settings.py` — wartości domyślne, sprawdzanie poprawności, mały serwer strony (tylko na tym komputerze)
- `settings.html` — strona ustawień
- `test_control.py` — testy logiki i kierunków w symulacji
- `record.py` — nagrywanie pokazów padem na prawdziwym ramieniu do formatu LeRobot (instrukcja: `NAGRYWANIE.md`)
- `test_record.py` — test nagrywania bez ramienia
- `NAGRYWANIE.md` — krok po kroku: port, kierunki, kamera, nagrywanie, nauka ACT, uruchomienie
- `LEROBOT_PLAN.md` — plan: nagrywanie pokazów padem i uczenie ramienia w LeRobot (research, repozytoria, kroki)
