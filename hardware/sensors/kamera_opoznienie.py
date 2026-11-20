"""Prawdziwe opóźnienie kamery (19 XI). Okno Terminala miga czarny ↔ biały (2 razy na sekundę), kamera patrzy na ekran.
Mierzymy czas od polecenia „zmień kolor” do klatki, w której program widzi zmianę. Droga obrazu jest ta sama co w
live_avoid.py (ffmpeg → 160×100 → Python), bo używamy jego klasy Frames.
Wynik OBEJMUJE opóźnienie samego ekranu (zwykle 1–3 odświeżenia, ok. 10–30 ms). Sama kamera z programem są więc szybsze.
Uruchom, WKLEJAJĄC w Terminal (okno duże lub na cały ekran, kamera 5–15 cm od okna, celuje w jego środek):
  cd /Users/admin/so101_fly_project && .venv/bin/python hardware/sensors/kamera_opoznienie.py [--size 640x400 --fps 120 --n 20]
Wynik jest DOPISYWANY do ~/Desktop/kamera_opoznienie.txt (razem ze stanem naświetlania z uvc-util).
  --check = sprawdzian liczenia bez kamery."""
import argparse
import os
import shutil
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../flymind/experiments/step3_wiring"))
UVC = "/Users/admin/tools/uvc-util/src/uvc-util"
OUT = os.path.expanduser("~/Desktop/kamera_opoznienie.txt")


def paint(white):
    """Całe okno Terminala na biało albo na czarno (spacje z kolorem tła)."""
    c, r = shutil.get_terminal_size()
    sys.stdout.write("\033[H" + ("\033[107m" if white else "\033[40m") + " " * (c * r) + "\033[H")
    sys.stdout.flush()


def analyse(rec):
    """rec = [(biały?, [(s od przełączenia, jasność klatki), …]), …] → słownik z opóźnieniami [ms] albo błędem."""
    tail = lambda w: [b for white, fr in rec if white == w for t, b in fr[len(fr) * 2 // 3:]]   # noqa: E731  ustalona jasność
    dark, light = np.median(tail(False)), np.median(tail(True))
    if light - dark < 10:
        return dict(err=f"kamera nie widzi migania (jasność czarny {dark:.0f}, biały {light:.0f}) — przysuń ją do ekranu")
    mid, lat = (dark + light) / 2, {True: [], False: []}
    for white, fr in rec[1:]:                                    # pierwsze przełączenie pomijamy (kamera dopiero się ustawia)
        hit = [t for t, b in fr if (b > mid) == white]
        if hit:
            lat[white].append(1000 * hit[0])
    allv = lat[True] + lat[False]
    return dict(dark=dark, light=light, n=len(allv), med=np.median(allv), lo=min(allv), hi=max(allv),
                to_white=np.median(lat[True]), to_black=np.median(lat[False]))


def _check():
    rng = np.random.default_rng(0)
    rec = []
    for k in range(20):                                          # klatki co 1/120 s, zmiana widoczna 45 ms po przełączeniu
        white = k % 2 == 0
        ts = np.arange(rng.uniform(0, 1 / 120), 0.25, 1 / 120)
        rec.append((white, [(t, (200 if white else 20) if t >= 0.045 else (20 if white else 200)) for t in ts]))
    r = analyse(rec)
    assert 45 <= r["med"] < 45 + 1000 / 120 and r["n"] == 19, r
    assert "err" in analyse([(w, [(t, 100) for t, _ in fr]) for w, fr in rec]), "brak migania musi dać błąd"
    print("kamera_opoznienie _check OK", {k: round(float(v), 1) for k, v in r.items()})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cam", default="USB Camera")
    ap.add_argument("--size", default="640x400")
    ap.add_argument("--fps", type=int, default=120)
    ap.add_argument("--fmt", type=int, help="numer formatu z kamera_mjpg (zamiast ffmpeg)")
    ap.add_argument("--n", type=int, default=20, help="ile mignięć (każde = biały + czarny)")
    ap.add_argument("--half", type=float, default=0.25, help="s jednego koloru (0,25 s = 2 mignięcia/s, bezpieczne dla oczu)")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        return _check()
    from live_avoid import Frames
    fr = Frames(cam=a.cam, fps=a.fps, size=a.size, fmt=a.fmt)
    t_end = time.time() + 10
    while fr.n < 30 and time.time() < t_end:
        time.sleep(0.01)
    if fr.n == 0:
        fr.stop()
        sys.exit("BRAK OBRAZU z kamery — wklej komendę w Terminal (nie z Claude), sprawdź kabel.")
    rec, n0, t0all = [], fr.n, time.perf_counter()
    sys.stdout.write("\033[?25l")
    try:
        paint(False)
        time.sleep(1.0)
        for k in range(2 * a.n):
            white = k % 2 == 0
            t0 = time.perf_counter()
            paint(white)
            seen, got = fr.n, []
            while time.perf_counter() - t0 < a.half:
                if fr.n != seen:
                    seen = fr.n
                    got.append((time.perf_counter() - t0, float(fr.last.mean())))
                time.sleep(0.0005)
            rec.append((white, got))
    finally:
        sys.stdout.write("\033[0m\033[2J\033[H\033[?25h")
        sys.stdout.flush()
    fps = (fr.n - n0) / (time.perf_counter() - t0all)
    fr.stop()
    gaps = np.concatenate([np.diff([t for t, _ in g]) for _, g in rec])
    exp = subprocess.run([UVC, "-I", "0", "-g", "auto-exposure-mode", "-g", "exposure-time-abs", "-g", "gain"],
                         capture_output=True, text=True).stdout.replace("\n", "; ")
    r = analyse(rec)
    head = f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {f'kamera_mjpg format {a.fmt}' if a.fmt is not None else f'ffmpeg {a.size}@{a.fps}'}  kamera {fps:.0f} kl./s  | {exp}"
    body = (r["err"] if "err" in r else
            f"opóźnienie ekran→program: mediana {r['med']:.0f} ms (od {r['lo']:.0f} do {r['hi']:.0f}, {r['n']} pomiarów; "
            f"na biały {r['to_white']:.0f}, na czarny {r['to_black']:.0f}); jasność czarny {r['dark']:.0f}, biały {r['light']:.0f}; "
            f"odstęp klatek mediana {1000 * np.median(gaps):.1f} ms")
    with open(OUT, "a") as f:
        f.write(head + "\n  " + body + "\n")
    print(head + "\n  " + body + f"\n(dopisane do {OUT})")


if __name__ == "__main__":
    main()
