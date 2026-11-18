"""RT-F analysis of rtf_raw.npz (no simulation). Unit for CI = noise rep (n = 4), jackknife-t (as V6m2). B1 = mean of 3 instances.
Run: .venv/bin/python -I -B flymind/results/v6m2/redteam/RT_F/rtf_analysis.py"""
import json
import os

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
Z = np.load(os.path.join(HERE, "rtf_raw.npz"))
A, conds = Z["A"], list(Z["conds"])                    # [src, cond, input(M0, MASYNC, MTHIN, MTHIN_DATA), li, si, r]
x = np.nanmean(A, (4, 5))                                 # mean over levels, sides -> [src, cond, inp, r]  (keep li? no)
x = A.mean(4).mean(3)                                     # [src, cond, inp, r]
D, B = x[0], x[1:]                                        # D [cond, inp, r]; B [k, cond, inp, r]
R = x.shape[-1]
tq = stats.t.ppf(0.975, R - 1)


def stat(f):
    est = f(np.arange(R))
    jk = np.array([f(np.delete(np.arange(R), i)) for i in range(R)])
    se = np.sqrt((R - 1) / R * ((jk - jk.mean(0)) ** 2).sum(0))
    return est, est - tq * se, est + tq * se


def S(c):
    i = conds.index(c)
    out = {}
    out["DATA_M0"] = stat(lambda m: D[i, 0, m].mean())
    out["B1_M0"] = stat(lambda m: B[:, i, 0][:, m].mean())
    out["gap_M0"] = stat(lambda m: B[:, i, 0][:, m].mean() - D[i, 0, m].mean())
    out["dt"] = stat(lambda m: (B[:, i, 1][:, m].mean() - D[i, 1, m].mean()) - (B[:, i, 0][:, m].mean() - D[i, 0, m].mean()))
    out["dD_async"] = stat(lambda m: D[i, 1, m].mean() - D[i, 0, m].mean())
    out["dB_async"] = stat(lambda m: B[:, i, 1][:, m].mean() - B[:, i, 0][:, m].mean())
    out["gap_thin"] = stat(lambda m: (B[:, i, 2][:, m] - B[:, i, 3][:, m]).mean())   # B1 thinned - DATA thinned (paired per k)
    out["thin_DATA"] = stat(lambda m: B[:, i, 3][:, m].mean())
    j = conds.index("REF")
    out["I"] = stat(lambda m: ((B[:, j, 1][:, m].mean() - D[j, 1, m].mean()) - (B[:, j, 0][:, m].mean() - D[j, 0, m].mean()))
                    - ((B[:, i, 1][:, m].mean() - D[i, 1, m].mean()) - (B[:, i, 0][:, m].mean() - D[i, 0, m].mean())))
    out["Fmatch"] = stat(lambda m: 1 - (B[:, i, 0][:, m].mean() - D[i, 0, m].mean()) / (B[:, j, 0][:, m].mean() - D[j, 0, m].mean()))
    return out


res = {c: {k: [float(v) for v in t] for k, t in S(c).items()} for c in conds}
ref_rate = res["REF"]["DATA_M0"][0]
gains = [c for c in conds if c.startswith("T0_g")]
gstar = min(gains, key=lambda c: abs(res[c]["DATA_M0"][0] - ref_rate))
biases = [c for c in conds if c.startswith("T0_b")] + ["T0"]
bstar = min(biases, key=lambda c: abs(res[c]["DATA_M0"][0] - ref_rate))
f = lambda t: f"{t[0]:+7.1f} ({t[1]:+.1f}; {t[2]:+.1f})"  # noqa: E731
print(f"rate-matched (post hoc, this data): gain {gstar}, bias {bstar}; REF DATA rate {ref_rate:.1f}")
print(f"{'cond':14s} {'DATA M0':>7s} {'B1 M0':>7s} | {'gap M0':^22s} | {'dt=gapASYNC-gapM0':^22s} | {'gap THIN (counts eq)':^22s} | "
      f"{'I vs REF':^22s} | dDATA_async dB1_async | Fmatch")
for c in conds:
    r = res[c]
    print(f"{c:14s} {r['DATA_M0'][0]:7.1f} {r['B1_M0'][0]:7.1f} | {f(r['gap_M0'])} | {f(r['dt'])} | {f(r['gap_thin'])} | {f(r['I'])} | "
          f"{r['dD_async'][0]:+6.1f} {r['dB_async'][0]:+6.1f} | {r['Fmatch'][0]:+.2f}")
aux = json.load(open(os.path.join(HERE, "rtf_aux.json")))
print("ISI histogram (M0, bins 0..11 ms; summed over cells) DATA / B1 8421001")
for cn in aux["isi"]["DATA"]:
    print(f"  {cn:10s} DATA {aux['isi']['DATA'][cn][1:8]}  B1 {aux['isi']['8421001'][cn][1:8]}")
# (d) per-neuron intermediate counts 300-1000 ms, B1 vs DATA, paired cells
c = aux["counts"]
dif, rd, rb = [], [], []
for key, v in c.items():
    k, li, si, r = key.split("|")
    if k != "DATA":
        dd = np.array(c[f"DATA|{li}|{si}|{r}"])
        dif.append(np.array(v) - dd)
        rd.append(dd)
        rb.append(np.array(v))
dif, rd, rb = np.array(dif), np.array(rd), np.array(rb)
print(f"intermediate counts 300-1000 ms: DATA total {rd.sum(1).mean():.0f}, B1 {rb.sum(1).mean():.0f} ({rb.sum() / rd.sum() - 1:+.1%});"
      f" neurons with B1<DATA {np.mean(dif < 0):.2f}, = {np.mean(dif == 0):.2f}, > {np.mean(dif > 0):.2f};"
      f" silent in both {np.mean((rd == 0) & (rb == 0)):.2f}; max count {rd.max()} / {rb.max()} (cap 175)")
act = rd.mean(0) > 0
print(f"  mean |diff| per active neuron {np.abs(dif[:, act]).mean():.1f} spikes; share of total |diff| from top-10 neurons "
      f"{np.sort(np.abs(dif).sum(0))[::-1][:10].sum() / np.abs(dif).sum():.2f}")
json.dump(dict(stats=res, gain_star=gstar, bias_star=bstar), open(os.path.join(HERE, "rtf_analysis.json"), "w"), indent=1)
