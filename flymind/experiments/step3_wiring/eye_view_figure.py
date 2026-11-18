"""Ilustracja (nie test): co odbiera nasza „mucha” z modelem oka złożonego (eye_bench). Scena rozwojowa 21990, cube_M.
Dla każdego koloru jeden wiersz: kamera | 296 omatidiów (jasność dla Rh1) | które omatidia „widzą przedmiot” (kontrast > próg)
| dwie liczby do LC10a. Klatka z chwili t = T_SHOT s (przedmiot już na stole, ramię jeszcze się nie obróciło).
Uruchom: eye_view_figure.py OUT.png KOLOR [KOLOR ...]"""
import dataclasses
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import eye_bench as eb  # noqa: E402

vm, oh = eb.vm, eb.oh
T_SHOT = 0.30


def shoot(colour):
    vm.Eye = eb.make_eye(colour, "eye")
    vm.TargetEncoder, vm.spot_clip = eb.EyeEncoder, eb.eye_spot_clip
    shot, see0 = {}, vm.Cam.see

    def see(self):
        see0(self)
        if "lo" not in shot and self.obs.t >= T_SHOT:
            shot.update(hi=self.eye.frame(vm.HI).copy(), lo=self.img.copy(), g=self.g.copy())
    vm.Cam.see = see
    f, d, _ = vm.make("A_cam")
    vm.CFG = dataclasses.replace(vm.CFG, idle_max=1.0)
    it = ("cube_M", "hard_grip")
    vm.run_series([it], 21990 * 1000 + oh.SETS["base"].index(it) * 10, f, d)
    vm.Cam.see = see0
    return shot


def main(out, *colours):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import RegularPolygon
    enc = eb.EyeEncoder(vm.LO)
    r = eb.STEP / math.sqrt(3)
    fig, ax = plt.subplots(len(colours), 4, figsize=(21, 5.2 * len(colours)), gridspec_kw=dict(width_ratios=[1.33, 1.33, 1.33, 0.6]))
    ax = np.atleast_2d(ax)
    for i, col in enumerate(colours):
        s = shoot(col)
        v = enc.sample(s["lo"])
        bg = float(np.median(v))
        c = np.abs(v - bg) / bg
        on = c > eb.C_MIN
        ax[i, 0].imshow(s["hi"])
        ax[i, 0].set_title(f"{col}: kamera robota (kolor, 640×480)", fontsize=12)
        for k, a in enumerate((ax[i, 1], ax[i, 2])):
            a.set_xlim(0, eb.W), a.set_ylim(eb.H, 0), a.set_aspect("equal"), a.set_facecolor("black")
            for (y, x), val, o, cc in zip(enc.C, v, on, c):
                if k == 0:
                    g = min(1.0, val / 255)
                    a.add_patch(RegularPolygon((x, y), 6, radius=r, facecolor=(g, g, g), edgecolor="none"))
                else:
                    a.add_patch(RegularPolygon((x, y), 6, radius=r, facecolor=(1, 0.1, 0.6) if o else (0.25, 0.25, 0.25),
                                               edgecolor="black", lw=0.3))
            a.set_xticks([]), a.set_yticks([])
        ax[i, 1].set_title("296 omatidiów: jasność, jak widzą ją R1–R6\n(bez koloru, prawie ślepe na czerwień)", fontsize=12)
        ax[i, 2].set_title(f"które omatidia „widzą przedmiot”\n(kontrast > {eb.C_MIN:.2f}: {int(on.sum())} z {len(on)}; maks. {c.max():.2f})", fontsize=12)
        ax[i, 3].bar(["lewe", "prawe"], s["g"] * vm.ENC.i_max, color=["#3b6fb6", "#d0703a"])
        ax[i, 3].set_ylim(0, vm.ENC.i_max), ax[i, 3].set_ylabel("prąd LC10a [mV]")
        ax[i, 3].set_title("to dostaje sieć", fontsize=12)
        ax[i, 0].set_xticks([]), ax[i, 0].set_yticks([])
    fig.suptitle("Co odbiera nasza „mucha” z modelem oka złożonego — ta sama chwila, scena rozwojowa 21990 (ILUSTRACJA, nie wynik)", fontsize=14)
    fig.tight_layout()
    fig.savefig(out, dpi=100)
    print("zapisano", out)


if __name__ == "__main__":
    main(*sys.argv[1:])
