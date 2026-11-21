"""P1 (21 XI): nagranie z kamery nadgarstka do testu oka muchy NA PRAWDZIWYM OBRAZIE (PREREG_OKO_KAMERA.md).
Tylko kamera, nic nie idzie do ramienia. Uruchom w Terminal.app (tylko on ma dostęp do kamery):
  python3 hardware/sensors/nagraj_oko.py            → ~/Desktop/oko_r1.mkv + ~/Desktop/oko_r1_plan.json
Głos (Zosia) mówi, co robić; patrz na kamerę, nie na ekran. Około 4 minut.
  python3 hardware/sensors/nagraj_oko.py --check    (bez kamery: sprawdza tylko plan)
  python3 hardware/sensors/nagraj_oko.py --fake --out /ścieżka/x   (bez kamery i głosu: obraz testowy, 4 pierwsze kroki)"""
import json
import os
import subprocess
import sys
import threading
import time

FF = "/Users/admin/miniforge3/bin/ffmpeg"
OUT = os.path.expanduser(sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "~/Desktop/oko_r1")
# (rodzaj, polecenie przygotowania albo None, polecenie „teraz”, długość okna [s])
PLAN = ([("prep", None, "Połóż kamerę nieruchomo, obiektywem do siebie. Zaczynamy za chwilę.", 6),
         ("sync", None, "Zasłoń obiektyw dłonią", 3), ("prep", None, "Odsłoń", 2),
         ("rest", None, "Nic nie rób", 5)]
        + [("loom_c", "Dłoń daleko, na środku obrazu", "Teraz szybko zbliż dłoń prosto do kamery", 4)] * 3
        + [("loom_l", "Dłoń daleko, po twojej lewej", "Teraz zbliż dłoń do kamery", 4)] * 2
        + [("loom_r", "Dłoń daleko, po twojej prawej", "Teraz zbliż dłoń do kamery", 4)] * 2
        + [("side", "Dłoń z boku, około pół metra od kamery", "Teraz przesuń dłoń w poprzek, w tej samej odległości", 4)] * 3
        + [("recede", "Dłoń blisko kamery", "Teraz szybko odsuń dłoń", 4)] * 3
        + [("prep", None, "Weź kamerę do ręki. Druga ręka nic nie robi.", 5)]
        + [("pan", "Trzymaj kamerę", "Teraz obróć kamerę w lewo i w prawo", 4)] * 3
        + [("tilt", "Trzymaj kamerę", "Teraz pochyl kamerę w górę i w dół", 4)] * 3
        + [("loompan", "Trzymaj kamerę, druga dłoń daleko", "Teraz obracaj powoli kamerę i jednocześnie zbliż dłoń", 4)] * 2
        + [("prep", None, "Odłóż kamerę nieruchomo.", 4)]
        + [("light", "Przygotuj się przy świetle", "Teraz zgaś i zapal światło, albo zasłoń i odsłoń lampę", 4)] * 2
        + [("prep", None, "Koniec. Dziękuję.", 2)])


def say(txt):
    print(f"  >>> {txt}", flush=True)
    if "--fake" not in sys.argv:
        subprocess.run(["say", "-v", "Zosia", "-r", "200", txt])


def main():
    if "--check" in sys.argv:
        n = sum(1 for k, *_ in PLAN if k not in ("prep", "sync"))
        print(f"plan OK: {len(PLAN)} kroków, {n} okien, ~{sum(d + 3 for *_, d in PLAN) / 60:.1f} min")
        return
    src = (["-re", "-f", "lavfi", "-i", "testsrc=size=640x400:rate=80"] if "--fake" in sys.argv else   # --fake: próba bez kamery
           ["-f", "avfoundation", "-framerate", "120", "-video_size", "640x400", "-i", "USB Camera"])
    # te same klatki idą do pliku (pełne) i do tego skryptu (16×10), który zapisuje czas przyjścia każdej → zegar komputera
    ff = subprocess.Popen([FF, "-y", "-nostdin", "-loglevel", "error", *src, "-filter_complex", "[0:v]format=gray,split=2[a][b];[b]scale=16:10[c]",
                           "-map", "[a]", "-c:v", "ffv1", OUT + ".mkv", "-map", "[c]", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                          stdin=subprocess.DEVNULL, stdout=subprocess.PIPE)
    ft = []
    threading.Thread(target=lambda: [ft.append(time.time()) for _ in iter(lambda: ff.stdout.read(160), b"")], daemon=True).start()
    time.sleep(3)                                         # kamera się rozkręca
    if ff.poll() is not None or not ft:
        sys.exit("ffmpeg nie ruszył — czy kamera jest podłączona i to jest Terminal.app?")
    log = []
    try:
        for kind, prep, now, dur in (PLAN[:4] if "--fake" in sys.argv else PLAN):
            if prep:
                say(prep)
                time.sleep(1.5)
            t0 = time.time()                                # okno od początku polecenia „teraz” (Adam może ruszyć w trakcie)
            say(now)
            time.sleep(dur)
            log.append(dict(kind=kind, t0=t0, t1=time.time()))
            json.dump(dict(windows=log, frame_t=ft[:]), open(OUT + "_plan.json", "w"))
    finally:
        ff.terminate()
        ff.wait()
        time.sleep(0.5)
        json.dump(dict(windows=log, frame_t=ft), open(OUT + "_plan.json", "w"))
    print(f"zapisane: {OUT}.mkv i {OUT}_plan.json — daj znać Claude'owi.")


if __name__ == "__main__":
    main()
