"""Test „widzenie jak oko złożone muchy” (16 XI 2026). SYMULACJA. Cel i kryteria: LOOP_TARGET_eye_r1.md.

Percepcja „eye” (NOWA) — wejście wzrokowe sieci przechodzi przez model OPTYKI oka złożonego:
  klatka kamery 96×128 → jasność widziana przez R1–R6 (jeden pigment Rh1, szczyt ok. 480 nm, BEZ koloru; wagi R,G,B =
  0,05 / 0,55 / 0,40 — przybliżenie, prawie ślepe na czerwień) → rozmycie gaussowskie o FWHM = 5° (kąt
  akceptacji) → próbkowanie na siatce heksagonalnej co 5° (omatidia; ok. 300 na polu kamery 70°) → kontrast Webera względem
  mediany wszystkich omatidiów (tło) → |kontrast| > C_MIN → napęd LC10a L/P tą samą regułą co dotąd (strefa obuoczna, nasycenie).
Czego to NIE jest: modelu neuronów płata wzrokowego (lamina → medulla → lobula). Między omatidiami a LC10a nadal jest prosty
detektor kontrastu = sztuczne pobudzanie LC10a (decyzja Adama 12 XI). Droga z danych (oko → LC10a) czeka na sesję „Oko muchy”
(bramka G2 FAILED 16 XI). Klasyczny pomiar położenia do chwytu (rusztowanie) bez zmian: sylwetka „chroma” z klatki 480×640.
Parametry ustalone PRZED testem (eksploracja na scenach rozwojowych 21 990 xxx, opis w LOOP_TARGET_eye_r1.md):
  Δφ = 5°, FWHM = 5° (literatura); C_MIN = 0,17 = 1,5 × największy kontrast pustej sceny (0,113);
  kalibracja skrętu ciemną plamką (60,60,60) na szarym (120) zamiast zielonej (zielona jest dla Rh1 tak jasna jak tło);
  E0 dobrane tak, by plamka kalibracyjna na wprost dawała ten sam napęd co dotychczasowy enkoder koloru dla swojej plamki (g = 0,916).

Uruchom: eye_bench.py --arm A_cam|E_vis_touch --perc chroma|eye --colour NAZWA --seed S --tag TAG --out DIR [--only ...]
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time

import numpy as np
from scipy.ndimage import binary_dilation, gaussian_filter, map_coordinates

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import colour_bench as cb  # noqa: E402

vm, oh, sm = cb.vm, cb.oh, cb.sm
DPHI, FWHM, C_MIN = 5.0, 5.0, 0.17
RH1 = np.array([0.05, 0.55, 0.40])               # wagi R, G, B jasności widzianej przez R1–R6
CAL_SPOT, CAL_BG, G_REF = (60, 60, 60), (120, 120, 120), 0.916
H, W = vm.LO
DEG_PX = vm.ENC.fovy_deg / H                     # ° na piksel klatki 96×128
STEP = DPHI / DEG_PX                             # odstęp omatidiów w pikselach
PX_PER_OM = STEP * STEP * math.sqrt(3) / 2       # pole jednego omatidium w pikselach (ok. 41)


def hex_centres():
    pts = []
    for j, y in enumerate(np.arange(STEP / 2, H, STEP * math.sqrt(3) / 2)):
        for x in np.arange(STEP / 2 + (STEP / 2 if j % 2 else 0), W, STEP):
            pts.append((y, x))
    return np.array(pts)


class EyeEncoder(cb.TargetEncoder):
    """Oko złożone (model optyki) → g L/P. n_px zwracane w pikselach-ekwiwalentach (omatidia × PX_PER_OM), żeby próg
    „coś widać” (VisCfg.n_min = 12 px) znaczył „co najmniej jedno omatidium”."""

    def __init__(self, shape, params=vm.ENC):
        super().__init__(shape, params)
        self.C = hex_centres()
        tanx = math.tan(math.radians(params.fovy_deg) / 2) * W / H
        self.az_om = -np.arctan((2 * self.C[:, 1] / W - 1) * tanx)
        sL = 1 / (1 + np.exp(-self.az_om / math.radians(params.w_deg)))
        self.S_om = np.stack([sL, 1 - sL])

    def sample(self, image):
        lum = image.astype(np.float32) @ RH1
        b = gaussian_filter(lum, sigma=(FWHM / 2.355) / DEG_PX, mode="nearest")
        return map_coordinates(b, self.C.T, order=1, mode="nearest")

    def encode(self, image):
        if image is None:
            return dict(g=np.zeros(2), n_px=0, az_centroid=None, usable=False)
        v = self.sample(image)
        bg = float(np.median(v))
        if bg < 1.0:
            return dict(g=np.zeros(2), n_px=0, az_centroid=None, usable=True)
        c = np.abs(v - bg) / bg
        c = np.where(c > C_MIN, c, 0.0)
        g = 1 - np.exp(-(self.S_om @ c) / E0)
        n = int((c > 0).sum())
        return dict(g=g, n_px=int(round(n * PX_PER_OM)), n_om=n, az_centroid=float((c * self.az_om).sum() / c.sum()) if n else None,
                    usable=True)


def _e0():
    """E0 tak, by plamka kalibracyjna (ciemna, 9 px, na wprost) dała g = G_REF po obu stronach — jak enkoder koloru dla swojej."""
    from sensory import spot_clip
    im = spot_clip(np.radians([0.0]), np.zeros(1), vm.LO, vm.ENC.fovy_deg, 9, CAL_SPOT, CAL_BG).images[0]
    e = EyeEncoder.__new__(EyeEncoder)
    EyeEncoder.__init__(e, vm.LO)
    v = e.sample(im)
    c = np.abs(v - np.median(v)) / np.median(v)
    c = np.where(c > C_MIN, c, 0.0)
    return float((e.S_om @ c)[0] / -math.log(1 - G_REF))


E0 = _e0()


def eye_spot_clip(az, el, shape, fovy, size, colour, bg):
    """Kalibracja skrętu w trybie „eye”: ta sama procedura, ale plamka widoczna dla Rh1 (ciemna na szarym)."""
    from sensory import spot_clip
    return spot_clip(az, el, shape, fovy, size, CAL_SPOT, CAL_BG)


def make_eye(colour, perc):
    Base = cb.make_eye(colour, "chroma")
    if perc == "chroma":
        return Base

    class EyeEye(Base):
        def _own_masks(self):
            """Maska własnego chwytaka: suma kryterium koloru (jak chroma) i kontrastu jasności względem tła (oko bez koloru
            widzi też szare/czarne części chwytaka)."""
            import mujoco
            lo_c, hi_c = super()._own_masks()
            m, d = self.sim.m, self.sim.d
            k = mujoco.MjData(m)
            k.qpos[:], jid = d.qpos, m.joint("gripper").id
            lo, hi = m.jnt_range[jid] if m.jnt_limited[jid] else (-0.2, 1.8)
            acc = {s: np.zeros(s, bool) for s in (vm.LO, vm.HI)}
            for a in np.linspace(lo, hi, cb.JAW_STEPS):
                k.qpos[self.sim.qadr[5]] = a
                mujoco.mj_forward(m, k)
                for s in acc:
                    self.r[s].update_scene(k, camera="eye")
                    lum = self.r[s].render().astype(np.float32) @ RH1
                    acc[s] |= np.abs(lum - np.median(lum)) / max(1.0, float(np.median(lum))) > C_MIN
            return lo_c | binary_dilation(acc[vm.LO], iterations=3), hi_c | binary_dilation(acc[vm.HI], iterations=3)

    return EyeEye


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=("A_cam", "E_vis_touch"))
    ap.add_argument("--perc", required=True, choices=("chroma", "eye"))
    ap.add_argument("--colour", required=True, choices=sorted(cb.COLOURS))
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    path = os.path.join(a.out, a.tag + ".json")
    if os.path.exists(path):
        sys.exit(f"istnieje {path}")
    vm.Eye = make_eye(a.colour, a.perc)
    vm.TargetEncoder = EyeEncoder if a.perc == "eye" else cb.ChromaEncoder      # też kalibracje skrętu
    if a.perc == "eye":
        vm.spot_clip = eye_spot_clip
    fc, vc = sm.FlyCfg(trigger="search"), vm.VisCfg()
    w0 = time.perf_counter()
    factory, drv, cal = vm.make(a.arm, fc, vc)
    items, runs, loop = oh.SETS["base"], [], []
    jobs = [([it], a.seed * 1000 + items.index(it) * 10) for it in items if not a.only or "/".join(it) in a.only]
    for its, seed in jobs:
        cb.CTRL.clear()
        r = vm.run_series(its, seed, cb.timed(factory), drv)
        loop += cb.CTRL[0].tl
        r.pop("lat")
        runs.append(r)
        o = r["objects"][0]
        print(f"{o['shape'] + '/' + o['material']:22s} {seed}: {'OK ' if o['success'] else '-- '}"
              f"{''.join('GLTRP'[j] if o['truth'][s] else '.' for j, s in enumerate(oh.STAGES))} → {o['final']}", flush=True)
    L = np.asarray(loop) * 1e3
    summ = oh.summarize(runs)
    summ["loop_ms"] = dict(vm.pct(L), n=int(len(L)))
    V = [v for r in runs for v in r["vision"]]
    summ["vision"] = dict(percepts=len(V), t_orient_s=vm.pct([v["t_orient"] for v in V]),
                          pos_mm=vm.pct([abs(e["pos_mm"]) for e in map(vm.perr, V) if e["pos_mm"] is not None]))
    out = dict(tag=a.tag, arm=a.arm, perc=a.perc, colour=a.colour, rgb=cb.COLOURS[a.colour], seed=a.seed, argv=sys.argv,
               eye=dict(dphi_deg=DPHI, fwhm_deg=FWHM, c_min=C_MIN, e0=E0, rh1_rgb=RH1.tolist(), cal_spot=CAL_SPOT, n_ommatidia=len(hex_centres()), px_per_om=PX_PER_OM),
               calibration=cal, network=getattr(drv, "sizes", None), wall_s=round(time.perf_counter() - w0, 1),
               code_sha256={f: hashlib.sha256(open(p, "rb").read()).hexdigest() for f, p in
                            (("eye_bench.py", __file__), ("colour_bench.py", cb.__file__), ("vision_manipulation.py", vm.__file__))},
               summary=summ, runs=runs)
    with open(path, "x") as f:
        json.dump(out, f, indent=1, default=float)
    s = summ["success"]
    print(f"\n{a.arm}/{a.perc}/{a.colour}: {s['k']}/{s['n']} | kalibracja {cal} | percepty {summ['vision']}")


if __name__ == "__main__":
    main()
