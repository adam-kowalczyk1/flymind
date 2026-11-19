"""Analiza diag_vision.py (rozwój). Pary full/blind z tym samym szumem → gdzie wzrok zmienia drogę dotyk dłoni → cofnięcie.
Uruchom: analyze_diag.py KATALOG_RAW [--tag N]   (bez argumentów: _check)"""
import glob
import json
import os
import sys

import numpy as np

FROZEN = {"front": 1.63, "left": 1.80, "right": 1.63}      # hw2p, ramię nieruchome (avoid r1, geometria: to samo dla każdego ziarna)
DT, POST = 0.01, 0.3
GROUPS = ("bm", "dnkey", "dnesc", "eyeL", "eyeR", "vpn", "brain", "asc", "dn", "inter", "mn", "feco")


def avoided(r):
    return r["touched_s"] < FROZEN[r["dir"]] - 0.2


def windows(touch):
    on = np.flatnonzero(np.asarray(touch).max(1) > 0.2)
    t0 = int(on[0]) if len(on) else None
    return t0


def rates(sp, a, b):
    """Hz na neuron w taktach [a, b) (sp = spiki/takt 10 ms)."""
    return sp[a:b].sum(0) / ((b - a) * DT)


def load(raw, tag):
    P = {}
    for p in glob.glob(os.path.join(raw, f"{tag}_*.json")):
        r = json.load(open(p))
        z = np.load(p[:-5] + ".npz")
        P.setdefault((r["dir"], r["seed"]), {})[r["cond"]] = (r, z)
    return {k: v for k, v in P.items() if "full" in v and "blind" in v}


def main(raw, tag="N"):
    meta = np.load(os.path.join(raw, "net_meta.npz"), allow_pickle=True)   # własny plik
    reg, ty = meta["reg"], meta["type"]
    P = load(raw, tag)
    print(f"par: {len(P)}")
    out = dict(pairs=[], groups={})
    acc = {k: [] for k in ("full_ok", "full_fail", "blind_ok", "blind_fail")}
    dpre, dpost = [], []
    for (d, s), v in sorted(P.items()):
        (rf, zf), (rb, zb) = v["full"], v["blind"]
        t0 = windows(zb["touch"])                          # dotyk zaczyna się tak samo (ramię przed dotykiem stoi prawie w miejscu)
        a, b = int(0.5 / DT), t0
        row = dict(dir=d, seed=s, full=avoided(rf), blind=avoided(rb), t_full=rf["touched_s"], t_blind=rb["touched_s"],
                   dq1_full=rf["dq_end"][0], dq1_blind=rb["dq_end"][0])
        out["pairs"].append(row)
        for cond, r, z in (("full", rf, zf), ("blind", rb, zb)):
            sp = z["spikes"].astype(np.float32)
            g = {k: [float(rates(sp, a, b)[reg == k].mean()), float(rates(sp, t0, t0 + int(POST / DT))[reg == k].mean())]
                 for k in GROUPS if (reg == k).any()}
            acc[f"{cond}_{'ok' if avoided(r) else 'fail'}"].append(g)
        spf, spb = zf["spikes"].astype(np.float32), zb["spikes"].astype(np.float32)
        dpre.append(rates(spf, a, b) - rates(spb, a, b))
        dpost.append(rates(spf, t0, t0 + int(POST / DT)) - rates(spb, t0, t0 + int(POST / DT)))
    n = {k: len(v) for k, v in acc.items()}
    print("unika: full", sum(p["full"] for p in out["pairs"]), "/", len(P), "| blind", sum(p["blind"] for p in out["pairs"]), "/", len(P), n)
    print(f"{'grupa':8}" + "".join(f"{k:>22}" for k in acc))
    for k in GROUPS:
        cells = []
        for c, L in acc.items():
            vals = np.array([g[k] for g in L if k in g]) if L else np.zeros((0, 2))
            cells.append(f"{vals[:, 0].mean():9.1f}/{vals[:, 1].mean():9.1f}   " if len(vals) else f"{'—':>22}")
        out["groups"][k] = cells
        print(f"{k:8}" + "".join(cells))
    print("(Hz przed dotykiem / 0,3 s po dotyku)")
    dpre, dpost = np.mean(dpre, 0), np.mean(dpost, 0)
    for name, dd in (("PRZED dotykiem", dpre), ("PO dotyku", dpost)):
        print(f"\nnajwiększe różnice full − blind {name} (Hz, średnio po parach):")
        for i in np.argsort(-np.abs(dd))[:25]:
            print(f"  {i:6d} {reg[i]:7} {ty[i]:14} {dd[i]:+8.1f}")
    # obszarowo: suma różnic po dotyku
    print("\nsuma |różnic| po dotyku wg obszaru:", {k: round(float(np.abs(dpost[reg == k]).sum()), 1) for k in GROUPS if (reg == k).any()})
    np.savez_compressed(os.path.join(raw, f"{tag}_diff.npz"), dpre=dpre, dpost=dpost)
    with open(os.path.join(raw, "..", f"analysis_{tag}.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)


def brake(R):
    """Kryteria B1–B4 z LOOP_TARGET_brake_r1.md. R = {(tag, cond): [wynik próby (dict z dir, touched_s)]}."""
    def per_dir(L, want):
        return {d: (sum(avoided(r) == want for r in L if r["dir"] == d), sum(r["dir"] == d for r in L)) for d in FROZEN}
    mean = lambda L: float(np.mean([r["touched_s"] for r in L])) if L else np.nan  # noqa: E731
    S, Sn, N = R.get(("S", "full"), []), R.get(("S", "numb"), []), R.get(("N", "full"), [])
    b1, b2 = per_dir(S, True), per_dir(Sn, False)
    ok = lambda pd: all(n >= 5 and k >= 4 for k, n in pd.values())  # noqa: E731
    ctrl = {t: mean(L) for (t, c), L in R.items() if t.startswith("C") and c == "full" and len(L) == len(S)}
    out = dict(B1=dict(per_dir=b1, pass_=ok(b1)), B2=dict(per_dir=b2, pass_=ok(b2)),
               B3=dict(S=mean(S), N=mean(N), pass_=bool(S and N) and mean(S) <= mean(N) - 0.3),
               B4=dict(S=mean(S), ctrl=ctrl, pass_=len(ctrl) == 3 and all(v >= mean(S) + 0.3 for v in ctrl.values())))
    out["PASS"] = all(out[k]["pass_"] for k in ("B1", "B2", "B3", "B4"))
    return out


def sweep(raws):
    """Przegląd ręki: dla każdego ustawienia (prędkość, promień) i grupy (N, S) — ile unika i średni czas dotyku.
    Czas ramienia nieruchomego z warunku frozen tego samego ustawienia (dla ustawienia bazowego: FROZEN)."""
    R = {}
    for raw in raws:
        for (tag, cond), L in load_results(raw).items():
            grp, _, setting = tag.partition("_")
            grp = {"S9870": "S"}.get(grp, grp)
            for r in L:
                if r["seed"] <= 21950005:
                    R.setdefault((setting or "v0.3_r0.04", grp, cond), []).append(r)
    out = {}
    for (setting, grp, cond), L in sorted(R.items()):
        if cond == "frozen":
            continue
        fro = {r["dir"]: r["touched_s"] for r in R.get((setting, "N", "frozen"), [])} or FROZEN
        ok = [r["touched_s"] < fro[r["dir"]] - 0.2 for r in L]
        out[f"{setting} {grp} {cond}"] = dict(unika=f"{sum(ok)}/{len(ok)}", dotyk_s=round(float(np.mean([r["touched_s"] for r in L])), 2),
                                             nieruchome_s=round(float(np.mean([fro[r['dir']] for r in L])), 2),
                                             staw1=round(float(np.mean([r["dq_end"][0] for r in L])), 2))
    return out


def load_results(raw):
    R = {}
    for p in glob.glob(os.path.join(raw, "*.json")):
        r = json.load(open(p))
        if "touched_s" in r:
            R.setdefault((r["tag"], r["cond"]), []).append(r)
    return R


def _check():
    mk = lambda tag, cond, t: [dict(tag=tag, cond=cond, dir=d, touched_s=t) for d in FROZEN for _ in range(5)]  # noqa: E731
    R = {("S", "full"): mk("S", "full", 0.5), ("S", "numb"): mk("S", "numb", 1.7), ("N", "full"): mk("N", "full", 1.2),
         ("C1", "full"): mk("C1", "full", 1.2), ("C2", "full"): mk("C2", "full", 1.1), ("C3", "full"): mk("C3", "full", 1.3)}
    assert brake(R)["PASS"], brake(R)
    R[("C2", "full")] = mk("C2", "full", 0.7)
    assert not brake(R)["B4"]["pass_"] and not brake(R)["PASS"]
    R[("S", "numb")] = mk("S", "numb", 0.5)
    assert not brake(R)["B2"]["pass_"]
    assert windows(np.array([[0, 0, 0], [0.1, 0, 0], [0.3, 0, 0]])) == 2
    assert avoided(dict(dir="left", touched_s=1.5)) and not avoided(dict(dir="left", touched_s=1.7))
    sp = np.zeros((10, 3))
    sp[2:4, 1] = 1
    assert np.allclose(rates(sp, 0, 10), [0, 20, 0])
    print("analyze_diag _check OK")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        _check()
    elif "--sweep" in sys.argv:                     # analyze_diag.py RAW1 [RAW2 ...] --sweep
        for k, v in sweep([p for p in sys.argv[1:] if p != "--sweep"]).items():
            print(f"{k:28} {v}")
    elif "--brake" in sys.argv:                     # analyze_diag.py KATALOG_RAW --brake
        print(json.dumps(brake(load_results(sys.argv[1])), indent=1, ensure_ascii=False))
    else:
        main(sys.argv[1], sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "N")
