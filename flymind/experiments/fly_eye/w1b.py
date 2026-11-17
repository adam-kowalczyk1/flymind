"""W1b — kierunek ruchu w T4/T5 na obrazie z kamery robota, miara „ten sam podtyp, ruch w jego stronę vs w przeciwną”. Cel: LOOP_TARGET_W1b.md.
envs/flyvis:  w1b.py run MODELS(np. 0-9) W0B_DIR OUT.npz      odpowiedź podtypu = Σ max(0, aktywność − stan w klatce przed ruchem)
                                                              po kolumnach w polu kamery i klatkach od początku ruchu (jak W1)
              w1b.py eval RUN.npz OUT.json
DI = (ΣR w stronę preferowaną − ΣR w przeciwną) / (suma), sumy po obu przedmiotach. Strona preferowana: a = w lewo kadru, b = w prawo,
c = w górę, d = w dół (kierunki T4 modelu 000 z PREREG_BRIDGE.md: a 178°, b −9°, c 59°, d −84°; oś x = poziom kadru)."""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SUB = [f"T4{s}" for s in "abcd"] + [f"T5{s}" for s in "abcd"]
MATS, PREF = ("hard_slick", "mid"), {"a": ("L", "R"), "b": ("R", "L"), "c": ("U", "D"), "d": ("D", "U")}


def run(models, w0, out):
    import torch
    import w2_run as W
    from w1_atlas import DEG_COL, flyxy, hex_movie
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    lo, hi = map(int, models.split("-")); res = {}
    for k in range(lo, hi + 1):
        net, t, u, v, r1, col = W.load(k)
        idx = W.type_idx(t, u, v, r1, SUB); xy = flyxy(u[r1], v[r1]) * DEG_COL
        for mat in MATS:
            for d in "RLUD":
                S = np.load(os.path.join(w0, f"{mat}_{d}.npz")); n0 = int(S["n_pre"])
                mv, ins = hex_movie(S["lum"], float(S["fovy_deg"]), xy)
                with torch.no_grad():
                    a = net.simulate(torch.tensor(mv)[None, :, None, :], 0.02).numpy()[0][:, idx][:, :, ins]
                res[f"m{k}_{mat}_{d}"] = np.clip(a[n0:] - a[n0 - 1], 0, None).sum((0, 2))        # 8 podtypów
        print("model", k, "ok", flush=True)
    np.savez(out, **res)


def evaluate(runf, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    R = np.load(runf)
    models = sorted({int(k[1:].split("_")[0]) for k in R})
    di = lambda m, j, mats: (lambda p, n: float((p - n) / (p + n + 1e-12)))(                       # noqa: E731
        *[sum(R[f"m{m}_{mat}_{PREF[SUB[j][-1]][i]}"][j] for mat in mats) for i in (0, 1)])
    DI = {m: {SUB[j]: di(m, j, MATS) for j in range(8)} for m in models}
    res = dict(models=models, DI=DI, per_object={mat: {s: int(sum(di(m, j, (mat,)) > 0 for m in models)) for j, s in enumerate(SUB)} for mat in MATS})
    for name, subs in (("K2b_horizontal", ["T4a", "T4b", "T5a", "T5b"]), ("K2c_vertical", ["T4c", "T4d", "T5c", "T5d"])):
        n_ok = {s: int(sum(DI[m][s] > 0 for m in models)) for s in subs}
        frac = sum(n_ok.values()) / (len(subs) * len(models))
        res[name] = dict(n_ok=n_ok, frac=frac, median_DI={s: float(np.median([DI[m][s] for m in models])) for s in subs},
                         ok=bool(frac >= 0.8 and min(n_ok.values()) >= 0.6 * len(models)))
    res["W1b_pass"] = res["K2b_horizontal"]["ok"]
    json.dump(res, open(out, "x"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "DI"}, indent=1))


if __name__ == "__main__":
    (run if sys.argv[1] == "run" else evaluate)(*sys.argv[2:])
