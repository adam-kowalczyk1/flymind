import json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "s3_stats.py")).read().split("# ---------- 1.")[0])
s = json.load(open(os.path.join(HERE, "stratified.json")))
c = {n: i for i, n in enumerate(s["cells"])}
Y = np.array([r["Y"] for r in s["res"]])[:, 0]          # REF
def f(Z):
    sh = lambda v: 0.5 * ((Z[f"DB_{v}"] - Z["DD"]) + (Z["BB"] - Z[f"BD_{v}"])) / (Z["BB"] - Z["DD"])  # noqa: E731
    th = 1 - (Z["BBm2"] - Z["DDm2"]) / (Z["BB"] - Z["DD"])
    return dict(U_minus_U2=sh("U") - sh("U2"), U_minus_CT2=sh("U") - sh("CT2"), U_minus_THIN2=sh("U") - th)
show("[REF paired share differences, stratified sim]", ci(f, {n: Y[:, i] for n, i in c.items()}), keys=("U_minus_U2", "U_minus_CT2", "U_minus_THIN2"))
# per level/side of the stratified CT2 share
Yj = np.array([r["Y"] for r in s["res"]])[:, 0]
lv = np.array([r["li"] for r in s["res"]]); sd_ = np.array([r["si"] for r in s["res"]])
for li in range(2):
    for si in range(2):
        m = (lv == li) & (sd_ == si)
        o = ci(dec, dict(DD=Yj[m, c["DD"]], BB=Yj[m, c["BB"]], DB=Yj[m, c["DB_CT2"]], BD=Yj[m, c["BD_CT2"]]), nboot=1000)
        o2 = ci(dec, dict(DD=Yj[m, c["DD"]], BB=Yj[m, c["BB"]], DB=Yj[m, c["DB_U"]], BD=Yj[m, c["BD_U"]]), nboot=1000)
        print(f"   lv {8+li} {'LR'[si]}: share U {o2['share']['est']:.3f}  CT2 {o['share']['est']:.3f} [{o['share']['jt'][0]:.3f};{o['share']['jt'][1]:.3f}]")
