"""Żywy odczyt 2 × FSR402 (Arduino `ms,A0,A1`, 100 Hz) albo plik CSV → touch_map.from_counts → BrainNet (somato) → częstości grup. BEZ ramienia.
Co 100 ms: siła odczuta A0/A1 [N], częstość [Hz] receptorów „udo” i „goleń+stopa”, DNg15, DNge078 i różnica pul P−N stawów 1–3.
Uruchom: fsr_live.py --csv plik.csv --out wynik.csv [--glu -1] [--mapping somato|swap|halves] [--r-fix 5100]
         fsr_live.py --port /dev/cu.usbmodemXXXX   (pyserial tylko w ~/miniforge3/envs/lerobot; Arduino tylko ODCZYT)"""
import argparse
import csv
import sys

import numpy as np

import touch_map as TM


def lines_csv(path):
    for r in csv.reader(open(path)):
        if len(r) == 3 and r[0].strip().isdigit():
            yield int(r[0]), int(r[1]), int(r[2])


def lines_serial(port):
    import serial                                   # lazily: tylko przy --port
    s = serial.Serial(port, 115200, timeout=1)
    while True:
        r = s.readline().decode(errors="ignore").strip().split(",")
        if len(r) == 3 and all(x.isdigit() for x in r):
            yield tuple(int(x) for x in r)


class Live:
    """Opakowanie sieci: ustawia pady wg mapowania i zbiera grupy częstości z ostatniego taktu (10 × 1 ms)."""
    def __init__(self, net, mapping="somato", noise=None, seed=None):
        import brainleg as B
        import reflex as R
        self.net = net
        net.pads = TM.pads_for(net, mapping)
        if noise is not None:                       # szum prądu jak avoid.py / brainleg_noise.py
            net.net = R.SparseALIF(R.JN.LB._W(net.W), R.ALIFParams(noise=noise), seed)
        _, d78, d15 = B.route_ids()
        self.grp = {"udo": net.pads[0], "golen": net.pads[1], "DNg15": [net.pos[b] for b in d15], "DNge078": [net.pos[b] for b in d78],
                    "press": net.press, "release": net.release}
        self.last, run0 = None, net.net.run

        def run(X, n):
            self.last = run0(X, n)
            return self.last
        net.net.run = run

    def tick(self, felt, palm=0.0, dt=0.01):
        """felt = (A0, A1) w N; zwraca słownik częstości [Hz] z tego taktu."""
        self.net.step([felt[0], felt[1], palm], np.zeros(5), np.zeros(5), dt)
        s = self.last * 1000.0
        out = {k: float(s[:, ix].mean()) if len(ix) else 0.0 for k, ix in self.grp.items()}
        for j, (p, n) in self.net.pools.items():
            out[f"j{j}"] = float(s[:, p].mean() - s[:, n].mean())
        return out


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--csv")
    g.add_argument("--port")
    ap.add_argument("--out")
    ap.add_argument("--glu", type=float, default=-1)
    ap.add_argument("--mapping", default="somato")
    ap.add_argument("--r-fix", type=float, default=TM.R_FIX)
    a = ap.parse_args()
    import brainleg as B
    net = B.BrainNet(a.glu)
    live = Live(net, a.mapping)
    keys = ["t_ms", "A0_N", "A1_N", "udo", "golen", "DNg15", "DNge078", "j1", "j2", "j3", "press", "release"]
    rows, acc = [], []
    src = lines_csv(a.csv) if a.csv else lines_serial(a.port)
    try:
        for i, (ms, c0, c1) in enumerate(src):
            felt = TM.from_counts(c0, c1, a.r_fix)
            r = live.tick(felt)
            acc.append((felt[0], felt[1], *(r[k] for k in keys[3:])))
            if len(acc) == 10:                                  # 100 ms
                m = np.mean(acc, axis=0)
                rows.append([ms, *np.round(m, 3)])
                print(" ".join(f"{k}={v:g}" for k, v in zip(keys, rows[-1])), flush=True)
                acc = []
    except KeyboardInterrupt:
        pass
    if a.out:
        csv.writer(open(a.out, "w")).writerows([keys, *rows])


if __name__ == "__main__":
    main()
