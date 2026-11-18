"""R0 — pierwszy kontakt z prawdziwym SO-101: TYLKO ODCZYT. Nic nie jest wysyłane do serw (bez włączania momentu, bez ruchu,
bez konfiguracji). Czyta przez 15 s: położenie [°], obciążenie, prąd, napięcie, temperaturę 6 serw; zapisuje CSV.
Potem robi po jednym zdjęciu z każdej kamery (indeksy 0–3) i zapisuje PNG. Uruchom (w środowisku lerobot):
  ~/miniforge3/envs/lerobot/bin/python hardware/real_arm/r0_odczyt.py            (port wykrywany sam)
  ~/miniforge3/envs/lerobot/bin/python hardware/real_arm/r0_odczyt.py --port /dev/tty.usbmodemXXXX
W trakcie odczytu możesz poruszać ramieniem ręką (silniki są luźne) — zobaczymy, czy położenia się zmieniają."""
import argparse
import csv
import glob
import os
import sys
import time

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "r0_" + time.strftime("%Y%m%d_%H%M%S"))
REGS = ("Present_Position", "Present_Load", "Present_Current", "Present_Voltage", "Present_Temperature")


def arm(port):
    from lerobot.robots.so_follower import SOFollower, SOFollowerRobotConfig
    r = SOFollower(SOFollowerRobotConfig(port=port, id="so101_follower", use_degrees=True))
    r.bus.connect()                     # tylko otwarcie portu + sprawdzenie, że 6 serw odpowiada (bez configure/torque)
    rows, t0 = [], time.monotonic()
    while time.monotonic() - t0 < 15.0:
        row = dict(t=round(time.monotonic() - t0, 3))
        for reg in REGS:
            v = r.bus.sync_read(reg, normalize=(reg == "Present_Position"))
            row.update({f"{m}.{reg}": round(float(x), 2) for m, x in v.items()})
        rows.append(row)
        time.sleep(0.05)
    r.bus.port_handler.closePort()      # zamknięcie portu bez disconnect() (ten wyłącza moment = zapis do serw)
    with open(os.path.join(OUT, "serwa.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"serwa: {len(rows)} odczytów w 15 s")
    for m in r.bus.motors:
        pos = [x[f"{m}.Present_Position"] for x in rows]
        print(f"  {m:14s} położenie {pos[0]:+7.1f}° → {pos[-1]:+7.1f}° (zakres {min(pos):+.1f}…{max(pos):+.1f}) | "
              f"obciążenie {rows[-1][f'{m}.Present_Load']:.0f} | prąd {rows[-1][f'{m}.Present_Current']:.0f} | "
              f"napięcie {rows[-1][f'{m}.Present_Voltage'] / 10:.1f} V | {rows[-1][f'{m}.Present_Temperature']:.0f} °C")


def cameras():
    import cv2
    for i in range(4):
        c = cv2.VideoCapture(i)
        ok, img = c.read() if c.isOpened() else (False, None)
        if ok:
            p = os.path.join(OUT, f"kamera_{i}.png")
            cv2.imwrite(p, img)
            print(f"kamera {i}: {img.shape[1]}×{img.shape[0]} → {p}")
        else:
            print(f"kamera {i}: brak")
        c.release()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port")
    ap.add_argument("--bez-ramienia", action="store_true", help="tylko kamery")
    a = ap.parse_args()
    os.makedirs(OUT)
    if not a.bez_ramienia:
        ports = [a.port] if a.port else sorted(glob.glob("/dev/tty.usbmodem*"))
        if len(ports) != 1:
            sys.exit(f"znalezione porty: {ports or 'żadnego'} — podłącz ramię kablem USB (i zasilacz) albo podaj --port")
        arm(ports[0])
    cameras()
    print("zapisano w", OUT)
