# Uczenie prawdziwego ramienia padem — instrukcja krok po kroku

Pokazujesz zadanie padem około 50 razy → komputer się uczy (ACT, przez noc na Macu) → ramię robi zadanie samo.
Ramię nauczone z pokazów to **linia porównawcza (classical)**, nie mucha. Nigdy nie podajemy tego jako wyniku muchy.

Wszystkie komendy uruchamiasz z folderu `so101_fly_project`. Środowisko Pythona do tego to `~/miniforge3/envs/lerobot`:
Python 3.12 z lerobot i padem. W głównym `~/miniforge3` (Python 3.14) komendy `lerobot-*` nie działają, bo
biblioteka draccus nie obsługuje Pythona 3.14.

```bash
export LR=~/miniforge3/envs/lerobot/bin
```

## 1. Podłącz ramię i znajdź port

Zasilanie ramienia + kabel USB. Potem:

```bash
$LR/lerobot-find-port
```

Program poprosi o odłączenie kabla i poda port, np. `/dev/tty.usbmodem5A7A0185001`. Kalibracja ramienia jest już zrobiona
(1 października, nazwa `so101_follower`). Robisz ją od nowa tylko po rozkręcaniu ramienia:
`$LR/lerobot-calibrate --robot.type=so101_follower --robot.port=PORT --robot.id=so101_follower`.

## 2. Pierwsze uruchomienie: sprawdź kierunki (bez nagrywania)

```bash
$LR/python pad_so101/run.py --real PORT
```

- **D-pad ↓ do biegu 1 (wolno).** Ręka przy wyłączniku zasilania.
- Rusz każdy staw osobno. Jeśli któryś jedzie w złą stronę, przełącz go na stronie ustawień (sekcja „Prawdziwe ramię"):
  `.venv/bin/python pad_so101/settings.py`. Zmiana kierunku działa po ponownym uruchomieniu programu (w locie ramię by skoczyło).
- RT ma zamykać chwytak. Jeśli otwiera, przełącz „Chwytak otwarty przy" na 0.
- View = STOP. Prawdziwy wyłącznik awaryjny to wyłącznik zasilania.

## 3. Kamera

Sieć uczy się z obrazu, więc kamera jest konieczna. Najlepsze, co mamy teraz, to **iPhone jako kamera** (Continuity Camera).
Postaw go na statywie z boku albo z przodu, tak żeby widział cały stół i chwytak. **Między pokazami kamera nie może się ruszać.**

```bash
$LR/lerobot-find-cameras opencv
```

**iPhone jako kamera (Kamera w ciągłości):**
- warunki: ten sam Apple ID na Macu i iPhonie, Wi-Fi i Bluetooth włączone na obu, a na iPhonie
  Ustawienia → Ogólne → AirPlay i ciągłość → Kamera w ciągłości włączona;
- iPhone zablokowany, nieruchomo na statywie, poziomo, tylną kamerą na stół, blisko Maca. Kabel USB do Maca jest
  stabilniejszy i ładuje telefon;
- na Macu w Centrum sterowania → Efekty wideo **wyłącz Centrum uwagi (Center Stage), Portret i Oświetlenie studyjne**.
  One same przesuwają i zmieniają kadr, a kadr musi być stały;
- połączenie telefoniczne przerywa obraz. Program wtedy sam robi STOP i odrzuca bieżący pokaz; zapisane pokazy zostają.
  Po rozmowie odłóż telefon **dokładnie w to samo miejsce** (najlepiej statyw z uchwytem) i wciśnij Menu.
  Żeby nic nie przerywało, możesz włączyć „Nie przeszkadzać" z wyjątkiem ważnych osób;
- numer kamery może się zmienić po rozłączeniu iPhone'a. Sprawdzaj go przed każdą sesją i używaj tego samego numeru
  przy uruchamianiu nauczonej sieci (krok 8);
- jeśli program zgłosi, że kamera nie obsługuje 640×480, spróbuj `--cam front=1@1280x720`.

Program wypisze kamery z numerami i zapisze zdjęcie z każdej w `outputs/captured_images`, żeby było widać, który numer to iPhone.
Za pierwszym razem macOS zapyta, czy Terminal może używać kamery — trzeba się zgodzić.
Druga kamera (na chwytaku) poprawia wyniki, ale na razie jej nie mamy.

## 4. Ćwiczenie bez ramienia (zalecane)

Wszystko działa jak naprawdę, tylko „ramię" jest udawane: kamera, pad, zapis. Pozwala nauczyć się przycisków.

```bash
$LR/python pad_so101/record.py --fake --cam front=1 --task "test" --name proba --episodes 3
```

(`front=1` to numer kamery z kroku 3.) Potem usuń próbę: `rm -rf ~/.cache/huggingface/lerobot/local/proba`.

## 5. Nagrywanie pokazów

```bash
$LR/python pad_so101/record.py --port PORT --cam front=1 --name klocek --task "Pick up the cube and put it in the box"
```

| Przycisk | Co robi podczas nagrywania |
|---|---|
| **Menu** | start pokazu → zrób zadanie → **Menu** = koniec i zapis |
| **R3** (wciśnij prawą gałkę) | odrzuć bieżący pokaz (coś poszło źle) |
| **View** | STOP — bieżący pokaz jest odrzucany; Menu wznawia |
| **Y** | wróć do pozycji startowej (rób to przed każdym pokazem) |
| reszta | jak zwykle (gałki, spusty, biegi, sloty) |
| Esc (klawiatura) | koniec: ramię wraca do startu, nagranie się zamyka |

Na górze okna widać czerwony pasek „● NAGRYWAM pokaz 7/50" i czas. Pokaz krótszy niż 1 s jest odrzucany,
a dłuższy niż 60 s zapisuje się sam (`--max-s`). Przerwane nagrywanie dokończysz później, dodając `--resume`.

**Jak nagrywać dobre pokazy** (od tego zależy wynik):
- 50 pokazów: 5 różnych miejsc klocka × 10 pokazów;
- przed każdym pokazem Y (start) i otwarty chwytak;
- ruchy płynne, spokojne i zawsze w podobny sposób; lepiej wolno niż szarpanie;
- to samo światło, nic obcego w kadrze, ręce człowieka poza kadrem w trakcie pokazu;
- opis zadania (`--task`) po angielsku i taki sam przez całe nagranie.

Jeśli pasek pokazuje „⚠ tylko N kl./s", komputer nie nadąża. Zamknij inne programy albo zmniejsz obraz (`--cam front=1@640x480`).

## 6. Obejrzyj nagranie

```bash
$LR/lerobot-dataset-viz --repo-id local/klocek --episode-index 0
```

## 7. Nauka (ACT na karcie graficznej Maca)

```bash
$LR/lerobot-train --dataset.repo_id=local/klocek --policy.type=act --policy.device=mps \
  --policy.push_to_hub=false --wandb.enable=false --batch_size=4 --steps=50000 --save_freq=10000 \
  --output_dir=outputs/act_klocek --job_name=act_klocek
```

Według dokumentacji LeRobot nauka trwa na M1 Max około 6–14 h (zostaw Maca włączonego na noc, podłączonego do prądu).
Szybciej w chmurze (HF Jobs, płatne), ale to wymaga konta Hugging Face — na razie nie.

## 8. Ramię robi zadanie samo

```bash
$LR/lerobot-rollout --strategy.type=base \
  --policy.path=outputs/act_klocek/checkpoints/last/pretrained_model \
  --robot.type=so101_follower --robot.port=PORT --robot.id=so101_follower --robot.max_relative_target=5 \
  --robot.cameras="{ front: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30}}" \
  --task="Pick up the cube and put it in the box" --duration=30
```

Kamera musi mieć **tę samą nazwę (`front`), ustawienie i rozmiar** co przy nagrywaniu.
Tu **nie działa** nasza warstwa bezpieczeństwa ani STOP z pada, steruje sam LeRobot. Dlatego: ręka na wyłączniku zasilania,
krótkie próby (`--duration=30`), pusty stół poza zadaniem.
Liczymy próby udane / wszystkie (np. 10 prób) — to jest wynik.

## Co sprawdziłem, a czego nie

- Sprawdzone bez ramienia (`pad_so101/test_record.py`): nagrywanie, odrzucanie (R3, STOP, za krótki), zapis wideo
  i format zgodny z LeRobot (nazwy stawów, stopnie, obraz 640×480). Nagranie czyta się tak, jak czyta je nauka.
- **Niesprawdzone:** prawdziwe ramię (nie było podłączone), prawdziwa kamera w `record.py`, kierunki stawów,
  pełna nauka i `lerobot-rollout`.
