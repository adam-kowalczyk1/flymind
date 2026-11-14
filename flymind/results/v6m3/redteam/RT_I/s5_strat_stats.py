import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = ["x"]
src = open(os.path.join(HERE, "s3_stats.py")).read().split("# ---------- 1.")[0]
exec(src)  # reuse dec / ci / show
s = json.load(open(os.path.join(HERE, "stratified.json")))
C, D = s["cells"], s["dyn"]
Y = np.array([r["Y"] for r in s["res"]]); DR = np.array([r["DR"] for r in s["res"]])
c = {n: i for i, n in enumerate(C)}
print("DNa02-weighted exc drive 500-1000:", {n: round(float(DR[:, c[n]].mean()), 1) for n in C})
for di, dyn in enumerate(D):
    print(dyn, "means", {n: round(float(Y[:, di, c[n]].mean()), 2) for n in C})
    for v in ("U", "U2", "CT2"):
        o = ci(dec, dict(DD=Y[:, di, c["DD"]], BB=Y[:, di, c["BB"]], DB=Y[:, di, c[f"DB_{v}"]], BD=Y[:, di, c[f"BD_{v}"]]))
        show(f"[{dyn} swap {v}]", o, keys=("C", "T", "share", "inter", "T_Dcnt", "T_Bcnt"))
    f = lambda Z: dict(T_thin=Z["BBm2"] - Z["DDm2"], Cshare_thin=1 - (Z["BBm2"] - Z["DDm2"]) / (Z["BB"] - Z["DD"]))  # noqa: E731
    show(f"[{dyn} MTHIN stratified]", ci(f, {n: Y[:, di, c[n]] for n in ("DD", "BB", "DDm2", "BBm2")}), keys=("T_thin", "Cshare_thin"))
