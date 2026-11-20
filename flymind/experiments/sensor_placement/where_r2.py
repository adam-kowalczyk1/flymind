"""Gdzie r2 (TARGET_where_r2.md): gradient MDN / zaciskanie wzdłuż rangi koniec→nasada i losowe grupy."""
import json, os, sys
import numpy as np
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import where_test as W  # noqa: E402
import live_avoid as LA  # noqa: E402

def main():
    bm = json.load(open(os.path.join(HERE, "results/bristle_map_r1.json")))
    net = LA.build(glu=-1, brake="hub")
    q = net._world.sim.d.qpos[net._world.sim.qadr][:5].copy()
    seeds = range(2011210, 2011213)
    # ranga u dla wszystkich (z bristle_map: przelicz z by_type niemożliwe → policz ponownie z SWC)
    import bristle_map as BM, pandas as pd
    mp = json.load(open(os.path.join(HERE, "../step3_wiring/touch_map.json")))
    rows = []
    for b in mp["femur"] + mp["tibia_tarsus"]:
        p = os.path.join(BM.SKEL, f"{b}.swc")
        if os.path.exists(p):
            L = BM.leaves(p)
            if len(L) >= 3:
                rows.append((b, L.mean(0)))
    c = np.median(np.stack([r[1] for r in rows]), 0)
    r = np.array([np.linalg.norm(v - c) for _, v in rows]); ids = np.array([b for b, _ in rows])
    order = ids[np.argsort(r)]
    bins = np.array_split(order, 5)
    def resp(group):
        g = [net.pos[int(b)] for b in group]
        return np.mean([W.trial(net, q, (g, []), s, 1, 0) for s in seeds], 0)
    G = [resp(b) for b in bins]
    mdn, jaw = [g[1] for g in G], [g[7] for g in G]
    rho_m, rho_j = spearmanr(range(5), mdn)[0], spearmanr(range(5), jaw)[0]
    g1 = bool(rho_m <= -0.9 or rho_j >= 0.9)
    allb = list(ids)
    rng = np.random.default_rng(2011216)
    hits, D = 0, []
    for _ in range(200):
        p = rng.permutation(allb)
        a, b = resp(p[:84]), resp(p[84:177])
        dm, dj = a[1] - b[1], b[7] - a[7]
        D.append((float(dm), float(dj)))
        hits += int(dm >= 5.9 and dj >= 0.36)
    frac = hits / 200
    res = dict(bins_MDN=mdn, bins_jaw=jaw, bins_n=[len(b) for b in bins], rho_MDN=float(rho_m), rho_jaw=float(rho_j), G1=g1,
               G2_frac=frac, G2=frac < 0.05, random=D)
    json.dump(res, open(os.path.join(HERE, "results/where_r2.json"), "w"), indent=1)
    print("MDN wg przedziałów (koniec→nasada):", np.round(mdn, 1), "szczęka:", np.round(jaw, 2))
    print(f"G1 ρ_MDN={rho_m:.2f} ρ_szczęka={rho_j:.2f} → {'ZDANE' if g1 else 'NIE ZDANE'} | G2 losowe z takim podziałem ról: {frac:.3f} → {'ZDANE' if frac < 0.05 else 'NIE ZDANE'}")

if __name__ == "__main__":
    main()
