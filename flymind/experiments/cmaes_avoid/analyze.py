"""Kryteria C1–C5 z PREREG_CMAES.md, liczone z plików testu results/test_*.json. Uruchom: analyze.py → results/analysis.json"""
import json
import os

import numpy as np

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
T0 = {"left": 1.80, "right": 1.63, "front": 1.63}             # ramię nieruchome (sprawdzane warunkiem frozen w test_N0)


def rows(name, cond):
    return [r for r in json.load(open(os.path.join(R, f"test_{name}.json")))["rows"] if r["cond"] == cond]


def summ(rs):
    t = np.array([r["touched_s"] for r in rs])
    av = sum(r["touched_s"] < T0[r["dir"]] - 0.2 for r in rs)
    return dict(n=len(rs), mean_touched=round(float(t.mean()), 3), avoids=int(av))


def main():
    fr = rows("N0", "frozen")
    assert all(abs(r["touched_s"] - T0[r["dir"]]) < 1e-6 for r in fr), [(r["dir"], r["touched_s"]) for r in fr]
    S = {k: summ(rows(*k.split(":"))) for k in ("N:full", "N:numb", "N:lesion", "N0:full", "LA:full", "LA:numb",
                                                 "LB:full", "LB:numb", "D:full", "D:numb")}
    m = lambda k: S[k]["mean_touched"]  # noqa: E731
    C = dict(C1=S["N:full"]["avoids"] >= 13 and m("N:full") <= m("N0:full") - 0.3,
             C2=S["N:numb"]["avoids"] <= 2,
             C3=S["N:lesion"]["avoids"] <= 2,
             C4=m("N:full") < m("LA:full") - 0.2 and m("N:full") < m("LB:full") - 0.2,
             C5=abs(m("LA:full") - m("LB:full")) < min(m("LA:full"), m("LB:full")) - m("N:full"))
    out = dict(summary=S, criteria=C, PASS=all(C.values()))
    json.dump(out, open(os.path.join(R, "analysis.json"), "w"), indent=1, default=bool)
    print(json.dumps(out, indent=1, default=bool))


if __name__ == "__main__":
    main()
