"""Ilustracja (nie test): „jak widzi prawdziwa mucha” vs „co dostaje nasza mucha”. Scena rozwojowa --seed 21990, 1 przedmiot.
Panele: (1) kamera robota 640×480; (2) PRZYBLIŻENIE oka muchy: ta sama klatka próbkowana na siatce heksagonalnej co ~5°
(omatidia), jasność szerokopasmowa jak R1–R6, rozmycie gaussowskie ~5° (kąt akceptacji) — model, nie pomiar;
(3) maska „chroma” 96×128, którą widzi nasz enkoder; (4) dwie liczby g_L, g_P podawane do LC10a — CAŁE wejście wzrokowe sieci.
Uruchom: fly_view_figure.py KOLOR OUT.png"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import colour_bench as cb  # noqa: E402

vm, oh = cb.vm, cb.oh
SHOT = {}


def main(colour, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import RegularPolygon
    from scipy.ndimage import gaussian_filter

    vm.Eye = cb.make_eye(colour, "chroma")
    vm.TargetEncoder = cb.ChromaEncoder
    see0 = vm.Cam.see

    def see(self):                                     # pierwsza klatka, w której „coś widać” (przedmiot jeszcze z boku)
        see0(self)
        if "hi" not in SHOT and self.n_px >= vm.VisCfg().n_min:
            SHOT.update(hi=self.eye.frame(vm.HI).copy(), lo=self.img.copy(), g=self.g.copy(), n=self.n_px)
    vm.Cam.see = see
    factory, drv, cal = vm.make("A_cam")
    vm.run_series([("cube_M", "hard_grip")], 21990 * 1000 + oh.SETS["base"].index(("cube_M", "hard_grip")) * 10, factory, drv)

    hi, lo, g = SHOT["hi"], SHOT["lo"], SHOT["g"]
    H, W = hi.shape[:2]
    fov_v = vm.ENC.fovy_deg
    deg_px = fov_v / H                                  # stopnie na piksel (w przybliżeniu, środek kadru)
    lum = hi.astype(np.float32).mean(-1)                # R1–R6: jeden szerokopasmowy pigment → sama jasność
    dphi = 5.0                                          # ° między omatidiami (literatura: ok. 4,5–5° u Drosophila)
    blur = gaussian_filter(lum, sigma=(dphi / 2.355) / deg_px)
    step = dphi / deg_px
    fig, ax = plt.subplots(1, 4, figsize=(22, 5.6), gridspec_kw=dict(width_ratios=[1.33, 1.33, 1.33, 0.7]))
    ax[0].imshow(hi)
    ax[0].set_title("1. Kamera robota (640×480, kolor)", fontsize=13)
    ax[1].set_xlim(0, W), ax[1].set_ylim(H, 0), ax[1].set_aspect("equal"), ax[1].set_facecolor("black")
    n_hex = 0
    for j, y in enumerate(np.arange(step / 2, H, step * math.sqrt(3) / 2)):
        for x in np.arange(step / 2 + (step / 2 if j % 2 else 0), W, step):
            v = float(blur[int(y), int(min(x, W - 1))]) / 255
            ax[1].add_patch(RegularPolygon((x, y), 6, radius=step / math.sqrt(3), orientation=0, facecolor=(v, v, v), edgecolor="none"))
            n_hex += 1
    ax[1].set_title(f"2. Prawdziwa mucha (przybliżenie): ~{n_hex} omatidiów\nna tym wycinku 70°, co ~5°, sama jasność (R1–R6)", fontsize=13)
    ax[2].imshow(lo)
    m = np.zeros(lo.shape[:2], bool)
    x = lo.astype(np.float32)
    c = (x.max(-1) - x.min(-1)) / max(1.0, float(x.mean()))
    m = c > vm.ENC.c_min
    ov = lo.copy()
    ov[m] = (255, 0, 255)
    ax[2].imshow(ov)
    ax[2].set_title(f"3. Nasza mucha: obraz 96×128 → maska koloru\n(różowe = „przedmiot”, {int(m.sum())} pikseli)", fontsize=13)
    ax[3].bar(["lewe\nLC10a", "prawe\nLC10a"], [g[0] * vm.ENC.i_max, g[1] * vm.ENC.i_max], color=["#3b6fb6", "#d0703a"])
    ax[3].set_ylim(0, vm.ENC.i_max)
    ax[3].set_ylabel("prąd [mV]")
    ax[3].set_title("4. Tyle dostaje sieć:\nDWIE liczby", fontsize=13)
    for a in ax[:3]:
        a.set_xticks([]), a.set_yticks([])
    fig.suptitle(f"Ta sama chwila w symulacji (przedmiot {colour}, scena rozwojowa 21990) — ILUSTRACJA, nie wynik testu", fontsize=14)
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print("zapisano", out, "| omatidiów:", n_hex, "| g:", g.round(3), "| px maski:", int(m.sum()))


if __name__ == "__main__":
    main(*sys.argv[1:3])
