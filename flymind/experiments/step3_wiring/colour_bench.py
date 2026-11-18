"""Benchmark „kolor × położenie × czas pętli” (16 XI 2026). SYMULACJA. Cel i kryteria: LOOP_TARGET_colour_r1.md.

Trzy moduły w każdym takcie (100 Hz czasu symulacji):
  1. PERCEPCJA  kamera „eye” na chwytaku → maska przedmiotu → prąd LC10a L/P (sieć) albo sylwetka do pomiaru (klasyczne)
  2. DECYZJA    sieć z MaleCNS (E: DNa02 → obrót bazy, obwód nogi T2 L → szczęka) albo kontroler klasyczny (A)
  3. WYKONANIE  klasyczne rusztowanie (dojazd, podniesienie, transport, puszczenie) + warstwa bezpieczeństwa → komendy stawów

Percepcja w dwóch wersjach (wszystko inne bez zmian, `vision_manipulation.py` importowany bez zmian, podmiany tylko w pamięci):
  green   — jak dotąd: detektor ZIELENI (encoder.TargetEncoder, sylwetka „odcień zielony”)
  chroma  — NOWA, niezależna od odcienia: piksel przedmiotu = nasycony kolor ((max − min) względem jasności), bez pikseli
            własnego chwytaka (maska z kilku położeń szczęki) i bez pikseli rzutujących się na pudełko (własna kinematyka).
            Nadal NIE jest to oko muchy: to sztuczne pobudzanie LC10a (decyzja Adama 12 XI). Szare/białe przedmioty są dla niej
            niewidoczne (stół jest szary) — zapisane z góry jako ograniczenie.
Czas pętli: dla każdego taktu czas zegarowy od klatki do komendy (cały takt kontrolera BEZ kroku fizyki).

Uruchom: colour_bench.py --arm A_cam|E_vis_touch --perc green|chroma --colour NAZWA --seed S --tag TAG --out DIR
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FLY = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, FLY)
import object_handling as oh  # noqa: E402
import sensory_manipulation as sm  # noqa: E402
import vision_manipulation as vm  # noqa: E402
from encoder import TargetEncoder  # noqa: E402

COLOURS = {"zielony": (40, 180, 50), "czerwony": (200, 45, 40), "niebieski": (45, 70, 210), "zolty": (225, 200, 40),
           "bialy": (235, 235, 235)}
SAT_SIL = 0.25          # sylwetka: (max − min)/max > SAT_SIL i max > 20 — „kolor nasycony, dowolny odcień”
JAW_STEPS = 7           # położenia szczęki do maski własnego chwytaka


def sat(x):
    """Nasycenie względem jasności piksela (0 = szary)."""
    mx, mn = x.max(-1), x.min(-1)
    return (mx - mn) / np.maximum(mx, 1.0), mx


class ChromaEncoder(TargetEncoder):
    """Jak TargetEncoder, ale kontrast c = (max − min)/średnia jasność obrazu zamiast (G − (R+B)/2)/jasność."""

    def encode(self, image):
        if image is None:
            return dict(g=np.zeros(2), n_px=0, az_centroid=None, usable=False)
        x = image.astype(np.float32)
        if self.p.blur_px > 1:
            from scipy.ndimage import uniform_filter
            x = uniform_filter(x, size=(self.p.blur_px, self.p.blur_px, 1), mode="nearest")
        lum = float(x.mean())
        if lum < 1.0:
            return dict(g=np.zeros(2), n_px=0, az_centroid=None, usable=True)
        c = (x.max(-1) - x.min(-1)) / lum
        c = np.where(c > self.p.c_min, c, 0.0)
        col = c.sum(0)
        g = 1 - np.exp(-(self.S @ col) / self.p.e0)
        n = int((c > 0).sum())
        return dict(g=g, n_px=n, az_centroid=float((col * self.az).sum() / col.sum()) if n else None, usable=True)


def make_eye(colour, perc):
    rgba = (*[v / 255 for v in COLOURS[colour]], 1.0)

    class Eye2(vm.Eye):
        def __init__(self, world, vc=vm.VisCfg()):
            super().__init__(world, vc)
            m = self.sim.m
            for o in world.objs:                                   # kolor przedmiotu — tylko wygląd, fizyka bez zmian
                m.geom_rgba[m.body_geomadr[o["bid"]]:m.body_geomadr[o["bid"]] + m.body_geomnum[o["bid"]]] = rgba
            self.perc = perc
            if perc == "chroma":
                self.own_lo, self.own_hi = self._own_masks()
                H, W = vm.LO
                t = math.tan(math.radians(vm.ENC.fovy_deg) / 2)
                jj, ii = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
                self.rays_lo = np.stack([(2 * jj / W - 1) * t * W / H, (1 - 2 * ii / H) * t, -np.ones((H, W))], -1)

        def _own_masks(self):
            """Piksele własnego chwytaka (nasycone: czerwone pady, złote śruby) przy JAW_STEPS położeniach szczęki,
            na OSOBNYM MjData (stan symulacji nietknięty), poza patrzenia, zanim pojawi się przedmiot."""
            import mujoco
            from scipy.ndimage import binary_dilation
            m, d = self.sim.m, self.sim.d
            k = mujoco.MjData(m)
            k.qpos[:], jid = d.qpos, m.joint("gripper").id
            lo, hi = m.jnt_range[jid] if m.jnt_limited[jid] else (-0.2, 1.8)
            out = {}
            for s in (vm.LO, vm.HI):
                acc = np.zeros(s, bool)
                for a in np.linspace(lo, hi, JAW_STEPS):
                    k.qpos[self.sim.qadr[5]] = a
                    mujoco.mj_forward(m, k)
                    self.r[s].update_scene(k, camera="eye")
                    sv, mx = sat(self.r[s].render().astype(np.float32))
                    acc |= (sv > 0.15) & (mx > 20)
                out[s] = binary_dilation(acc, iterations=2)
            return out[vm.LO], out[vm.HI]

        def see(self):
            if self.perc != "chroma":
                return super().see()
            t0 = time.perf_counter()
            img = self.frame(vm.LO)
            t1 = time.perf_counter()
            img = img.copy()
            kk = self.sim.fk(self.sim.d.qpos[self.sim.qadr].copy())
            ray = self.rays_lo @ kk["eye_R"].T
            E, b = kk["eye"], self.box
            down = ray[..., 2] < -0.05
            P = E[:2] + ray[..., :2] * (E[2] / np.where(down, -ray[..., 2], 1.0))[..., None]
            inbox = (P[..., 0] > b[0]) & (P[..., 0] < b[1]) & (P[..., 1] > b[2]) & (P[..., 1] < b[3])
            img[self.own_lo | inbox | ~down] = int(img.mean())
            e = self.enc.encode(img)
            self.t[:] = t1 - t0, time.perf_counter() - t1
            return img, e

        def silhouette(self, img, q):
            if self.perc != "chroma":
                return super().silhouette(img, q)
            k = self.sim.fk(np.asarray(q, float))
            E, R = k["eye"], k["eye_R"]
            sv, mx = sat(img.astype(np.float32))
            c = (sv > SAT_SIL) & (mx > 20) & ~self.own_hi
            ray = self.rays[c] @ R.T
            ray = ray[ray[:, 2] < -0.05]
            P = E[:2] + ray[:, :2] * (E[2] / -ray[:, 2:3])
            b = self.box
            return P[~((P[:, 0] > b[0]) & (P[:, 0] < b[1]) & (P[:, 1] > b[2]) & (P[:, 1] < b[3]))], E.copy()

    return Eye2


CTRL = []


def timed(factory):
    """Czas pętli: takt kontrolera (klatka → percepcja → decyzja → bezpieczeństwo → komenda) BEZ kroku fizyki."""
    def f(w, cfg):
        c = factory(w, cfg)
        c.tl, phys, step0, tick0 = [], [0.0], w.step, c.tick

        def step(*a, **k):
            t = time.perf_counter()
            r = step0(*a, **k)
            phys[0] += time.perf_counter() - t
            return r

        def tick(*a, **k):
            phys[0] = 0.0
            t = time.perf_counter()
            r = tick0(*a, **k)
            c.tl.append(time.perf_counter() - t - phys[0])
            return r

        w.step, c.tick = step, tick
        CTRL.append(c)
        return c
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=("A_cam", "E_vis_touch"))
    ap.add_argument("--perc", required=True, choices=("green", "chroma"))
    ap.add_argument("--colour", required=True, choices=sorted(COLOURS))
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    path = os.path.join(a.out, a.tag + ".json")
    if os.path.exists(path):
        sys.exit(f"istnieje {path}")
    vm.Eye = make_eye(a.colour, a.perc)
    if a.perc == "chroma":
        vm.TargetEncoder = ChromaEncoder                           # też kalibracje skrętu (calibrate, calibrate_p)
    fc, vc = sm.FlyCfg(trigger="search"), vm.VisCfg()
    w0 = time.perf_counter()
    factory, drv, cal = vm.make(a.arm, fc, vc)
    items, runs, loop, lat = oh.SETS["base"], [], [], []
    jobs = [([it], a.seed * 1000 + items.index(it) * 10) for it in items if not a.only or "/".join(it) in a.only]
    for its, seed in jobs:
        CTRL.clear()
        r = vm.run_series(its, seed, timed(factory), drv)
        loop += CTRL[0].tl
        lat.append(r.pop("lat"))
        runs.append(r)
        o = r["objects"][0]
        print(f"{o['shape'] + '/' + o['material']:22s} {seed}: {'OK ' if o['success'] else '-- '}"
              f"{''.join('GLTRP'[j] if o['truth'][s] else '.' for j, s in enumerate(oh.STAGES))} → {o['final']}", flush=True)
    L = np.asarray(loop) * 1e3
    summ = oh.summarize(runs)
    summ["loop_ms"] = dict(vm.pct(L), p999=round(float(np.percentile(L, 99.9)), 3), over_50=int((L > 50).sum()), n=int(len(L)))
    summ["compute_ms_per_tick_vm"] = vm.pct(np.vstack(lat).sum(1) * 1e3)
    V = [v for r in runs for v in r["vision"]]
    E = [vm.perr(v) for v in V]
    summ["vision"] = dict(percepts=len(V), pos_mm=vm.pct([abs(e["pos_mm"]) for e in E if e["pos_mm"] is not None]))
    out = dict(tag=a.tag, arm=a.arm, perc=a.perc, colour=a.colour, rgb=COLOURS[a.colour], seed=a.seed, argv=sys.argv,
               calibration=cal, network=getattr(drv, "sizes", None), wall_s=round(time.perf_counter() - w0, 1),
               code_sha256={f: __import__("hashlib").sha256(open(p, "rb").read()).hexdigest() for f, p in
                            (("colour_bench.py", __file__), ("vision_manipulation.py", vm.__file__), ("encoder.py", sys.modules["encoder"].__file__))},
               summary=summ, runs=runs)
    with open(path, "x") as f:
        json.dump(out, f, indent=1, default=float)
    s = summ["success"]
    print(f"\n{a.arm}/{a.perc}/{a.colour}: {s['k']}/{s['n']} | pętla ms {summ['loop_ms']}")


if __name__ == "__main__":
    main()
