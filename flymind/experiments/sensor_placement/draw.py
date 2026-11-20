"""Rysunek: chwytak (prawdziwe siatki) + wybrane miejsca FSR402 (pole czynne Ø12,7 pełną linią, folia Ø18,3 przerywaną)."""
import json, os, sys
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placement as PL

def draw(layouts, path, title):
    G = PL.Gripper(); P, N = G.points(0.0)
    d = json.load(open(os.path.join(PL.OUT, "placement_r1b.json")))
    C = d["cand"]
    fig, ax = plt.subplots(1, 2, figsize=(13, 8))
    s = np.arange(len(P))[::10]
    for a, (i, j, t) in zip(ax, [(0, 2, "z boku (szczęka stała po lewej, ruchoma po prawej, q = 0)"), (1, 2, "od strony szczęki ruchomej (widok na ścianę +x)")]):
        a.scatter(P[s, i], P[s, j], s=0.2, c=np.where(G.mov[s], "#9aa", "#ccc"))
        for (name, ids, col) in layouts:
            for k in ids:
                c, n = np.array(C[k]["p"]), np.array(C[k]["n"])
                for r, ls in ((PL.R_ACT, "-"), (PL.R_FOIL, "--")):
                    u = np.cross(n, [0, 0, 1.0] if abs(n[2]) < 0.9 else [1.0, 0, 0]); u /= np.linalg.norm(u); w = np.cross(n, u)
                    th = np.linspace(0, 2 * np.pi, 80)
                    ring = c + r * (np.cos(th)[:, None] * u + np.sin(th)[:, None] * w)
                    a.plot(ring[:, i], ring[:, j], ls, c=col, lw=1.6 if ls == "-" else 0.8)
                a.text(c[i], c[j], name, color=col, fontsize=9, ha="center", va="center", weight="bold")
        a.axhline(-104.4, c="k", lw=0.5); a.text(a.get_xlim()[0], -103, " czubek z = −104,4", fontsize=8)
        a.set_aspect("equal"); a.set_title(t, fontsize=10); a.set_xlabel("mm"); a.set_ylabel("mm")
    fig.suptitle(title, fontsize=11)
    fig.savefig(path, dpi=90, bbox_inches="tight")

if __name__ == "__main__":
    d = json.load(open(os.path.join(PL.OUT, "placement_r1b.json")))
    b = d["baseline"]; s0, s1 = d["score"]["0.45"], d["score"]["1.45"]
    draw([("teraz", [b["fsr1"], b["palm"]], "tab:gray"),
          ("A", s0["top"][0]["pair"], "tab:red"),
          ("B", s1["top"][0]["pair"], "tab:blue")],
         os.path.join(PL.OUT, "miejsca_r1b.png"),
         "FSR402 (pełne koło = pole czynne Ø12,7 mm, przerywane = folia Ø18,3): szary = obecne (szczęka stała + dłoń), "
         "czerwony A = najlepsza para (folia 0,45 mm), niebieski B = najlepsza para z krążkiem 1,45 mm")
