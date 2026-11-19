"""Kryteria A1–A5 z LOOP_TARGET_avoid_r1.md (liczone automatycznie). Uruchom: analyze_avoid.py KATALOG [--glu -1]"""
import glob
import json
import os
import sys

import numpy as np

DIRS = ("left", "right", "front")


def load(d, glu):
    T = {}
    for p in glob.glob(os.path.join(d, "*.json")):
        r = json.load(open(p))
        if r.get("glu") != glu or "cond" not in r:
            continue
        net = r["net"] + (str(r["shuffle_seed"]) if r.get("shuffle_seed") is not None else "")
        key = (net, r["touch"], r.get("map", "somato") if r["touch"] != "sim3" else "-", r["aim"], r["cond"])
        T.setdefault(key, {})[(r["dir"], r["noise_seed"])] = r["touched_s"]
    return T


def per_dir(a, b, ok):
    """Ile ziaren w każdym kierunku spełnia ok(a, b); zwraca {dir: (k, n)}."""
    out = {}
    for d in DIRS:
        ks = sorted(k for k in a if k[0] == d and k in b)
        out[d] = (sum(ok(a[k], b[k]) for k in ks), len(ks))
    return out


def criteria(T, touch, mp, aim):
    g = lambda net, cond, m=mp: T.get((net, touch, m, aim, cond), {})  # noqa: E731
    full, fro = g("N", "full"), g("N", "frozen")
    res = {}
    for name, cond in (("A1", "full"), ("A2", "numb"), ("A3", "lesion")):
        x = g("N", cond)
        ok = (lambda a, f: a < f - 0.2) if name == "A1" else (lambda a, f: a >= f - 0.2)
        pd = per_dir(x, fro, ok)
        res[name] = dict(per_dir={d: f"{k}/{n}" for d, (k, n) in pd.items()},
                         pass_=bool(pd) and all(n >= 5 and k >= 4 for k, n in pd.values()))
    m_full = np.mean(list(full.values())) if full else np.nan
    shuf = {net: np.mean(list(v.values())) for (net, t, m, a, c), v in T.items()
            if t == touch and m == mp and a == aim and c == "full" and net[0] in "FL" and len(v) == len(full)}
    res["A4"] = dict(data=round(float(m_full), 3), shuffles={k: round(float(v), 3) for k, v in shuf.items()},
                     pass_=bool(shuf) and all(m_full <= v - 0.2 for v in shuf.values()))
    if touch == "hw2-A5":                          # usunięte z celu przed testem (porównanie map)
        a5 = {}
        for other in ("swap", "halves"):
            o = g("N", "full", other)
            ks = [k for k in full if k in o]
            wins = sum(full[k] < o[k] for k in ks)
            dm = float(np.mean([o[k] - full[k] for k in ks])) if ks else np.nan
            a5[other] = dict(wins=f"{wins}/{len(ks)}", mean_gain_s=round(dm, 3), pass_=len(ks) == 15 and wins >= 10 and dm >= 0.1)
        res["A5"] = dict(a5, pass_=all(v["pass_"] for v in a5.values()))
    res["means"] = {c: round(float(np.mean(list(g("N", c).values()))), 3) for c in ("full", "frozen", "numb", "blind", "lesion") if g("N", c)}
    return res


def _check():
    T = {}
    for d in DIRS:
        for s in range(5):
            T.setdefault(("N", "hw2", "somato", "tips", "frozen"), {})[(d, s)] = 1.8
            T.setdefault(("N", "hw2", "somato", "tips", "full"), {})[(d, s)] = 1.0
            T.setdefault(("N", "hw2", "somato", "tips", "numb"), {})[(d, s)] = 1.8
            T.setdefault(("N", "hw2", "somato", "tips", "lesion"), {})[(d, s)] = 1.7 if s else 1.0
            T.setdefault(("F1", "hw2", "somato", "tips", "full"), {})[(d, s)] = 1.6
    r = criteria(T, "hw2", "somato", "tips")
    assert r["A1"]["pass_"] and r["A2"]["pass_"] and r["A3"]["pass_"] and r["A4"]["pass_"], r
    T[("F1", "hw2", "somato", "tips", "full")] = {k: 1.1 for k in T[("F1", "hw2", "somato", "tips", "full")]}
    assert not criteria(T, "hw2", "somato", "tips")["A4"]["pass_"]
    print("analyze_avoid _check OK")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        _check()
        sys.exit(0)
    glu = float(sys.argv[sys.argv.index("--glu") + 1]) if "--glu" in sys.argv else -1.0
    T = load(sys.argv[1], glu)
    out = {k: criteria(T, *m) for k, m in (("hw2p", ("hw2p", "somato", "palm")), ("hw2", ("hw2", "somato", "tips")),
                                            ("sim3", ("sim3", "-", "palm")))}
    j = out["hw2"]["A1"]["per_dir"]
    fro, full = T.get(("N", "hw2", "somato", "tips", "frozen"), {}), T.get(("N", "hw2", "somato", "tips", "full"), {})
    g = per_dir(full, fro, lambda a, f: a >= f - 0.2)
    out["G"] = dict(per_dir={d: f"{k}/{n}" for d, (k, n) in g.items()},
                    pass_=bool(g) and all(n >= 5 and k >= 4 for k, n in g.values()) and out["hw2p"]["A1"]["pass_"])
    out["PASS_unika"] = all(out["hw2p"][c]["pass_"] for c in ("A1", "A2", "A3", "A4"))
    print(json.dumps(out, indent=1, ensure_ascii=False))
