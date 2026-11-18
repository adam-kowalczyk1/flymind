"""Sprawa 2 — analiza testu dawki (zapisana PRZED testem; reguły LOOP_TARGET_dose_r1.md).
Uruchom: analyze_dose.py KATALOG OUT.json"""
import glob
import json
import os
import sys

from scipy.stats import spearmanr

TAU_ENGAGE = 0.10   # N·m — próg „sieć zaciska” z sensory_manipulation.FlyCfg


def metrics(curve):
    last = curve[-1]
    p, r = last["press_Hz"], last["release_Hz"]
    taus = [c["tau"] for c in curve]
    rho = spearmanr([c["mV"] for c in curve], taus).statistic if len(set(taus)) > 1 else 0.0
    return dict(tau40=last["tau"], rec40=round((p - r) / (p + r), 4) if p + r > 0 else 0.0, rho=round(float(rho), 4))


def main(d, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    rows = {}
    for p in sorted(glob.glob(os.path.join(d, "dose_g*_*.json"))):
        j = json.load(open(p))
        g = f"{j['glu']:+.0f}"
        for k, v in j["rows"].items():
            rows.setdefault(g, {}).setdefault(j["family"], {})[k] = metrics(v["curve"])
    res = {}
    for g, fams in sorted(rows.items()):
        N = fams["data"]["N"]
        rep = dict(N=N, precondition=bool(N["rho"] >= 0.9 and N["tau40"] >= TAU_ENGAGE))
        for fam in "FLG":
            S = fams.get(fam, {})
            if not S:
                continue
            t = [v["tau40"] for v in S.values()]
            c = [v["rec40"] for v in S.values()]
            hs = bool(len(S) == 20 and N["tau40"] > max(t))
            hr = bool(len(S) == 20 and N["rec40"] > max(c))
            rep[fam] = dict(n=len(S), tau40_min=min(t), tau40_med=sorted(t)[len(t) // 2], tau40_max=max(t), n_tau_ge=sum(x >= N["tau40"] for x in t),
                            rec40_min=min(c), rec40_med=sorted(c)[len(c) // 2], rec40_max=max(c), n_rec_ge=sum(x >= N["rec40"] for x in c),
                            rho_med=sorted(v["rho"] for v in S.values())[len(S) // 2], H_S=hs, H_Rec=hr, H_D=bool(hs and hr))
        res[f"glu{g}"] = rep
        print(f"Glu {g}: N {N} warunek {rep['precondition']}")
        for fam in "FLG":
            if fam in rep:
                print(f"   {fam}: {rep[fam]}")
    ok = all(res.get(f"glu{g}", {}).get("precondition") and all(res[f"glu{g}"].get(f, {}).get("H_D") for f in "FL") for g in ("+1", "-1"))
    res["verdict_FL_both_glu"] = bool(ok)
    print("Werdykt (F i L, oba Glu):", ok)
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(*sys.argv[1:3])
