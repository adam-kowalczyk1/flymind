"""W1 — kryteria K1/K2 (LOOP_TARGET_W1.md), opisowe D1–D3 i obrazy atlasu. .venv: w1_analysis.py W1_DIR W0_DIR"""
import glob
import json
import os
import sys

import numpy as np

T4 = [f"T4{s}" for s in "abcd"]; T5 = [f"T5{s}" for s in "abcd"]
PARTNER = {"a": "b", "b": "a", "c": "d", "d": "c"}
EXPECT = {"L1": -1, "L2": -1, "Mi1": 1, "Tm3": 1, "Tm1": -1, "Tm2": -1}
PD_000 = {"a": 178.0, "b": -9.0, "c": 59.0, "d": -84.0}   # kierunki T4 modelu 000 (PREREG_BRIDGE.md, inna sesja) — tylko D2
N0 = 50                                                   # pierwsza klatka ruchu; stan odniesienia = klatka 49


def rect(D, sc, s, ins):
    a = D[f"{sc}__{s}"][:, ins]
    return np.clip(a[N0:] - a[N0 - 1], 0, None)


def k1(D):
    sc = "S2_bok"; ins = D[f"{sc}__inside"]; mv = D[f"{sc}__movie"][:, ins]
    x = np.stack([mv[t] - mv[t - 10:t].mean(0) for t in range(N0, len(mv))]).ravel()
    r = {}
    for s in EXPECT:
        a = D[f"{sc}__{s}"][:, ins]
        y = (a[N0:] - a[N0 - 1]).ravel()
        r[s] = float(np.corrcoef(x, y)[0, 1])
    ok = sum(np.sign(r[s]) == e for s, e in EXPECT.items())
    return dict(r=r, n_ok=int(ok), ok=bool(ok >= 5))


def sums(D, sc):
    ins = D[f"{sc}__inside"]
    return {s: float(rect(D, sc, s, ins).sum()) for s in T4 + T5}


def k2(D):
    f, b = sums(D, "S2_bok"), sums(D, "S2r_bok_wstecz")
    out = {}
    for grp in (T4, T5):
        wf = max(grp, key=f.get)[-1]; wb = max(grp, key=b.get)[-1]
        out[grp[0][:2]] = dict(forward=wf, reverse=wb, ok=bool(wf in "ab" and wb == PARTNER[wf]))
    out["ok"] = bool(out["T4"]["ok"] and out["T5"]["ok"])
    out["sums_forward"], out["sums_reverse"] = f, b
    return out


def d2_outward(D):
    """Zbliżanie: ważona aktywnością średnia cos(kąt PD podtypu − kierunek od środka kadru). 1 = „na zewnątrz”."""
    sc = "S3_zblizanie"; ins = D[f"{sc}__inside"]; xy = D["xy_deg"][ins]
    rad = np.degrees(np.arctan2(xy[:, 1], xy[:, 0]))
    out = {}
    for grp in (T4, T5):
        num = den = 0.0
        for s in grp:
            w = rect(D, sc, s, ins).sum(0)
            num += (w * np.cos(np.radians(PD_000[s[-1]] - rad))).sum(); den += w.sum()
        out[grp[0][:2]] = float(num / den) if den > 0 else None
    return out


def figures(D, w0, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    xy = D["xy_deg"]
    hue = {"a": (0.85, 0.2, 0.2), "b": (0.2, 0.45, 0.9), "c": (0.2, 0.7, 0.25), "d": (0.9, 0.6, 0.1)}

    def dir_rgb(sc, grp, t):
        A = np.stack([np.clip(D[f"{sc}__{s}"][t] - D[f"{sc}__{s}"][N0 - 1], 0, None) for s in grp])
        k = A.argmax(0); m = A.max(0)
        m = m / max(np.percentile(np.stack([np.clip(D[f"{sc}__{s}"][N0:] - D[f"{sc}__{s}"][N0 - 1], 0, None) for s in grp]), 99.5), 1e-6)
        c = np.array([hue[grp[i][-1]] for i in k]) * np.clip(m, 0, 1)[:, None] + 0.12 * (1 - np.clip(m, 0, 1))[:, None]
        return c

    def panel(ax, sc, t, what):
        ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal")
        ins = D[f"{sc}__inside"]
        if what == "kamera":
            ax.imshow(np.load(os.path.join(w0, f"{sc}.npz"))["rgb"][t]); return
        if what == "oko":
            c = D[f"{sc}__movie"][t]; ax.scatter(*xy.T, c=np.where(ins, c, np.nan), cmap="gray", vmin=0, vmax=1, s=9, marker="h")
            ax.scatter(*xy[~ins].T, c="#ddd", s=9, marker="h"); return
        if what in ("T4", "T5"):
            ax.scatter(*xy.T, c=dir_rgb(sc, T4 if what == "T4" else T5, t), s=9, marker="h"); return
        a = D[f"{sc}__{what}"]; d = a[t] - a[N0 - 1]; v = np.percentile(np.abs(a[N0:] - a[N0 - 1]), 99.5) + 1e-6
        ax.scatter(*xy.T, c=d, cmap="coolwarm", vmin=-v, vmax=v, s=9, marker="h")

    cols = ["kamera", "oko", "R1", "L1", "L2", "Mi1", "Tm1", "T4", "T5"]
    names = {"kamera": "kamera robota", "oko": "oko (omatidia)", "R1": "fotoreceptor R1", "L1": "L1", "L2": "L2",
             "Mi1": "Mi1 (ON)", "Tm1": "Tm1 (OFF)", "T4": "T4 kierunek (ON)", "T5": "T5 kierunek (OFF)"}
    scen = ["S1_spokoj", "S2_bok", "S2r_bok_wstecz", "S3_zblizanie", "S4_ramie"]
    times = [49, 60, 75, 90, 105]
    for sc in scen:
        f, ax = plt.subplots(len(times), len(cols), figsize=(2.0 * len(cols), 1.7 * len(times)))
        for i, t in enumerate(times):
            for j, w in enumerate(cols):
                panel(ax[i, j], sc, t, w)
                if i == 0: ax[i, j].set_title(names[w], fontsize=8)
            ax[i, 0].set_ylabel(f"{(t - N0) * 20} ms", fontsize=8)
        f.suptitle(f"{sc} — model flyvis 000. Kolor: czerwony/niebieski = wzrost/spadek względem chwili przed ruchem; "
                   "T4/T5: barwa = zwycięski podtyp (a czerw., b nieb., c ziel., d pomar.)", fontsize=8)
        plt.tight_layout(); f.savefig(os.path.join(out, f"atlas_{sc}.png"), dpi=90); plt.close(f)
    for sc in ("S2_bok", "S3_zblizanie", "S4_ramie"):
        sub = ["kamera", "oko", "L1", "Mi1", "T4", "T5"]
        f, ax = plt.subplots(1, len(sub), figsize=(2.3 * len(sub), 2.4))
        def draw(t):
            for j, w in enumerate(sub):
                ax[j].cla(); panel(ax[j], sc, t, w); ax[j].set_title(names[w], fontsize=8)
            f.suptitle(f"{sc}  t = {(t - N0) * 20} ms", fontsize=9)
        FuncAnimation(f, draw, frames=range(40, 125, 2)).save(os.path.join(out, f"film_{sc}.gif"), writer=PillowWriter(fps=12))
        plt.close(f)


def main(d, w0):
    files = sorted(glob.glob(os.path.join(d, "model_0*.npz")))
    rows = {}
    for p in files:
        D = np.load(p)
        S1, S2 = sums(D, "S1_spokoj"), sums(D, "S2_bok")
        rows[os.path.basename(p)[6:9]] = dict(K1=k1(D), K2=k2(D),
                                              D1_static_over_motion=float(sum(S1.values()) / max(sum(S2.values()), 1e-9)),
                                              D2_outward=d2_outward(D), D3_pan=k2_like(D))
    n1 = sum(r["K1"]["ok"] for r in rows.values()); n2 = sum(r["K2"]["ok"] for r in rows.values())
    res = dict(n_models=len(rows), K1_models_ok=n1, K2_models_ok=n2, K1=bool(n1 >= 8), K2=bool(n2 >= 8),
               W1=bool(n1 >= 8 and n2 >= 8), models=rows)
    out = os.path.join(d, "w1_result.json")
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    json.dump(res, open(out, "x"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "models"}, indent=1))
    for k, r in rows.items():
        print(k, "K1", r["K1"]["n_ok"], {s: round(x, 2) for s, x in r["K1"]["r"].items()}, "| K2 T4", r["K2"]["T4"]["forward"],
              r["K2"]["T4"]["reverse"], "T5", r["K2"]["T5"]["forward"], r["K2"]["T5"]["reverse"],
              "| D1", round(r["D1_static_over_motion"], 3), "D2", r["D2_outward"], "D3", r["D3_pan"])
    figures(np.load(os.path.join(d, "model_000.npz")), w0, d)


def k2_like(D):
    s = sums(D, "S4_ramie")
    return {g: max(grp, key=s.get)[-1] for g, grp in (("T4", T4), ("T5", T5))}


if __name__ == "__main__":
    main(*sys.argv[1:3])
