"""F1 Stage 1 analysis (STAGE1_DESIGN.md d3 §2, §6, §8, §9). Commands: pilot-rules | confirm | describe <stage>.
Frozen before the pilot (hashed in manifest_pilot.json). Writes results/analysis_<stage>.json and stage1_confirm_params.json (mode x)."""
import glob
import json
import math
import os
import sys
import zlib

import numpy as np
from scipy.stats import beta, norm

HERE = os.path.dirname(os.path.abspath(__file__))
SESOI, EPS, N_BOOT = 0.10, 1e-9, 10_000
MEAS = (0.1, 0.9)
RNG = dict(pilot=9115001, confirm=9115002)
HOLM = ("S1", "S2", "S3", "S4", "S7", "S8", "S9")


def load(stage):
    rows = [r for f in sorted(glob.glob(os.path.join(HERE, "results", stage, "u*.json"))) for r in json.load(open(f))]
    units = sorted({r["unit"] for r in rows})
    bad = sorted({r["unit"] for r in rows if r["invalid_ticks"] > 0})
    keep = [u for u in units if u not in bad]                     # listwise exclusion (§3)
    by = {(r["unit"], r["fam"], r["motion"], r["rng"]): r for r in rows}
    return keep, bad, by


def col(by, units, fam, motion, rng, field="success"):
    return np.array([np.nan if by[(u, fam, motion, rng)][field] is None else float(by[(u, fam, motion, rng)][field]) for u in units])


def inst(by, units, fam):
    return np.array([by[(u, fam, "none", "W")]["inst"] for u in units])


def boot_idx(rng, n, groups=None):
    """Unit indices for one paired bootstrap replicate; hierarchical (instances, then units within them) when groups given."""
    if groups is None:
        return rng.integers(0, n, n)
    ids = np.unique(groups)
    pick = rng.choice(ids, len(ids))
    pools = [np.flatnonzero(groups == g) for g in pick]
    return np.concatenate([rng.choice(p, len(p)) for p in pools])


def stat_boot(fn, n, seed, groups=None, key=""):
    rng = np.random.default_rng([seed, zlib.crc32(key.encode())])     # registered seed + named stream
    return np.array([fn(boot_idx(rng, n, groups)) for _ in range(N_BOOT)])


def classify(est, bs, sesoi=SESOI, measurable=True):
    lo95, hi95 = np.percentile(bs, [2.5, 97.5])
    lo90, hi90 = np.percentile(bs, [5, 95])
    p = 1.0 if (np.ptp(bs) == 0 and est == 0) else float(min(1.0, max(1 / len(bs), 2 * min((bs <= 0).mean(), (bs >= 0).mean()))))
    if lo95 > 0 and est >= sesoi - EPS:
        c = "SUPPORTED"
    elif hi95 < 0 and est <= -sesoi + EPS:
        c = "HARMFUL"
    elif -sesoi + EPS < lo90 and hi90 < sesoi - EPS and measurable:
        c = "EQUIVALENT"
    elif lo95 > 0 or hi95 < 0:
        c = "DETECTABLE-BELOW-SESOI"
    elif not measurable:
        c = "UNMEASURABLE"
    else:
        c = "INCONCLUSIVE"
    return dict(est=float(est), ci95=[float(lo95), float(hi95)], ci90=[float(lo90), float(hi90)], p=p, cls=c)


def meas(*arms):
    return all(MEAS[0] <= np.nanmean(a) <= MEAS[1] for a in arms)


def harm(est, bs, margin):
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return dict(est=float(est), ci95=[float(lo), float(hi)], margin=margin,
                cls="HARMFUL" if (lo > 0 and est >= margin - EPS) else "NOT-HARMFUL" if hi < margin else "UNDETERMINED")


def holm(ps):
    order = np.argsort(ps)
    adj, run = np.empty(len(ps)), 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - r) * ps[i]))
        adj[i] = run
    return adj


def s6(b_ft, n_ft):
    """False turns, DATA sin vs none on N: harm = (b − c)/n, exact conditional CI (Clopper–Pearson on b of b + c)."""
    n = len(b_ft)
    b, c = int((b_ft & ~n_ft).sum()), int((~b_ft & n_ft).sum())
    if b + c == 0:
        lo, hi = 0.0, 1 - 0.025 ** (1 / n)
    else:
        pl = beta.ppf(0.025, b, c + 1) if b else 0.0
        ph = beta.ppf(0.975, b + 1, c) if c else 1.0
        lo, hi = (b + c) / n * (2 * pl - 1), (b + c) / n * (2 * ph - 1)
    est = (b - c) / n
    return dict(b=b, c=c, n=n, est=est, ci95=[lo, hi], margin=0.05,
                cls="HARMFUL" if (lo > 0 and est >= 0.05) else "NOT-HARMFUL" if hi < 0.05 else "UNDETERMINED")


def tests(stage, units, by, seed):
    n = len(units)
    S = lambda fam, m, g="W", fld="success": col(by, units, fam, m, g, fld)  # noqa: E731
    dD = S("DATA", "sin") - S("DATA", "none")
    out = {}

    def run(name, d, arms, groups=None):
        bs = stat_boot(lambda i: np.nanmean(d[i]), n, seed, groups, name)
        out[name] = dict(classify(np.nanmean(d), bs, measurable=meas(*arms)), arms={f"arm{k}": float(np.nanmean(a)) for k, a in enumerate(arms)})

    run("H1", dD, (S("DATA", "sin"), S("DATA", "none")))
    out["H1"]["rho50_shift_m"] = out["H1"]["est"] * 0.14 if stage == "confirm" else None
    run("S1", S("DATA", "sin") - S("DATA", "jvel"), (S("DATA", "sin"), S("DATA", "jvel")))
    for name, fam in (("S2", "B1"), ("S3", "SWS")):
        run(name, dD - (S(fam, "sin") - S(fam, "none")), (S("DATA", "none"), S("DATA", "sin"), S(fam, "none"), S(fam, "sin")),
            groups=inst(by, units, fam))
    th_none = np.nanmean(S("TH", "none"))
    if MEAS[0] <= th_none <= MEAS[1]:
        run("S4", dD - (S("TH", "sin") - S("TH", "none")), (S("DATA", "none"), S("DATA", "sin"), S("TH", "none"), S("TH", "sin")))
    else:
        out["S4"] = dict(cls="NOT TESTED", p=1.0, reason=f"TH_LP-ster none success in W = {th_none:.3f} outside {MEAS}")
    for name, m in (("S7", "gated"), ("S8", "virtual"), ("S9", "mt")):
        run(name, S("DATA", m) - S("DATA", "sin"), (S("DATA", m), S("DATA", "sin")))
    adj = holm(np.array([out[k]["p"] for k in HOLM]))
    for k, a in zip(HOLM, adj):
        out[k]["p_holm"] = float(a)
    # harm tests (no Holm, §2)
    hs = S("DATA", "none", "S") - S("DATA", "sin", "S")
    he = S("DATA", "sin", "S", "final_abs_err") - S("DATA", "none", "S", "final_abs_err")
    r5s = harm(np.nanmean(hs), stat_boot(lambda i: np.nanmean(hs[i]), n, seed, key="S5s"), 0.05)
    r5e = harm(np.nanmean(he), stat_boot(lambda i: np.nanmean(he[i]), n, seed, key="S5e"), 1.0)
    out["S5"] = dict(success=r5s, final_err_deg=r5e,
                     cls="HARMFUL" if "HARMFUL" in (r5s["cls"], r5e["cls"]) else
                     "NOT-HARMFUL" if r5s["cls"] == r5e["cls"] == "NOT-HARMFUL" else "UNDETERMINED")
    ft = lambda m: col(by, units, "DATA", m, "N", "false_turn").astype(bool)  # noqa: E731
    out["S6"] = s6(ft("sin"), ft("none"))
    s10 = {}
    for g in ("W", "S"):
        d = S("DATA", "sin", g, "s10_deg") - S("DATA", "none", g, "s10_deg")
        s10[g] = harm(np.nanmean(d), stat_boot(lambda i: np.nanmean(d[i]), n, seed, key="S10" + g), 1.0)
    out["S10"] = dict(s10, cls="HARMFUL" if "HARMFUL" in (s10["W"]["cls"], s10["S"]["cls"]) else
                      "NOT-HARMFUL" if s10["W"]["cls"] == s10["S"]["cls"] == "NOT-HARMFUL" else "UNDETERMINED")
    return out


def describe(units, by):
    fams = sorted({k[1:] for k in by})
    tab = {}
    for fam, m, g in fams:
        rows = [by[(u, fam, m, g)] for u in units]
        f = lambda k: [r[k] for r in rows if r[k] is not None]  # noqa: E731
        tab[f"{fam}|{m}|{g}"] = dict(n=len(rows), success=float(np.mean(f("success"))) if g != "N" else None,
                                     final_err=float(np.mean(f("final_abs_err"))) if g != "N" else None,
                                     track_cost=float(np.mean(f("track_cost"))) if g != "N" else None,
                                     latency_med_s=float(np.median(f("latency_s"))) if f("latency_s") else None,
                                     latency_found=len(f("latency_s")), s10_deg=float(np.mean(f("s10_deg"))),
                                     false_turn=float(np.mean(f("false_turn"))) if g == "N" else None,
                                     lc_ipsi=float(np.mean(f("lc_ipsi"))), dn=float(np.mean([r["dn_L"] + r["dn_R"] for r in rows])),
                                     a_pan_deg=float(np.degrees(np.mean(f("a_pan")))), lead_flags=float(np.mean(
                                         [r["flags"].get("lead", 0) for r in rows])), rate_flags=float(np.mean([r["flags"].get("rate", 0) for r in rows])))
    rho = np.array([by[(u, "DATA", "none", "W")]["rho"] for u in units])
    d = col(by, units, "DATA", "sin", "W") - col(by, units, "DATA", "none", "W")
    q = np.quantile(rho, [1 / 3, 2 / 3])
    terc = [float(d[(rho >= a) & (rho < b)].mean()) for a, b in ((-1, q[0]), (q[0], q[1]), (q[1], 9))]
    return dict(arms=tab, delta_by_rho_tercile=terc)


def failure(t, d):
    return {"G-a H1 not SUPPORTED": t["H1"]["cls"] != "SUPPORTED",
            "G-b harm (S5/S6/S10)": "HARMFUL" in (t["S5"]["cls"], t["S6"]["cls"], t["S10"]["cls"]),
            "G-c S4 EQUIVALENT (threshold, not SNN)": t["S4"]["cls"] == "EQUIVALENT",
            "G-e S8 SUPPORTED (virtual > physical)": t["S8"]["cls"] == "SUPPORTED",
            "G-f DATA none success in W > 0.9": d["arms"]["DATA|none|W"]["success"] > 0.9}


def write(name, obj):
    p = os.path.join(HERE, "results", name)
    with open(p, "x") as fh:
        json.dump(obj, fh, indent=1, default=float)
    print("wrote", p)


def pilot_rules():
    units, bad, by = load("pilot")
    P = json.load(open(os.path.join(HERE, "stage1_params.json")))
    t = tests("pilot", units, by, RNG["pilot"])
    d = describe(units, by)
    # R1 range
    p0 = d["arms"]["DATA|none|W"]["success"]
    (a, b) = P["ranges"]["W"]["rho"]
    ranges = json.loads(json.dumps(P["ranges"]))
    r1 = dict(p0=p0, changed=False)
    if not 0.15 <= p0 <= 0.6:
        r50 = a + p0 * (b - a)
        ranges["W"]["rho"] = [r50 - 0.07, r50 + 0.07]
        r1.update(changed=True, rho50=r50)
    # R3 omega_on
    om = np.concatenate([np.abs(np.load(os.path.join(HERE, "results", "pilot", f"u{u}.npz"))["DATA|sin|N|om"]) for u in units])
    r3 = max(0.10, math.ceil(np.percentile(om, 99) * 100) / 100)
    # R2 n by simulation (normal-approximation CI per simulated data set; ponytail: no nested bootstrap, 2000 sims × 5 n)
    S = lambda fam, m, g="W": col(by, units, fam, m, g)  # noqa: E731
    dD = S("DATA", "sin") - S("DATA", "none")
    diffs = dict(H1=dD, S1=S("DATA", "sin") - S("DATA", "jvel"),
                 S2=dD - (S("B1", "sin") - S("B1", "none")), S3=dD - (S("SWS", "sin") - S("SWS", "none")),
                 S4=dD - (S("TH", "sin") - S("TH", "none")), S7=S("DATA", "gated") - S("DATA", "sin"),
                 S8=S("DATA", "virtual") - S("DATA", "sin"), S9=S("DATA", "mt") - S("DATA", "sin"))
    groups = dict(S2=inst(by, units, "B1"), S3=inst(by, units, "SWS"))
    shift = max(0.0, SESOI - np.nanmean(dD))
    rng = np.random.default_rng([RNG["pilot"], zlib.crc32(b"R2")])
    power = {}
    for n in (200, 250, 300, 350, 400):
        res = {k: [] for k in diffs}
        for _ in range(2000):
            for k, x in diffs.items():
                idx = boot_idx(rng, len(x), groups.get(k))
                idx = idx[rng.integers(0, len(idx), n)]
                y = x[idx] + (shift if k == "H1" else 0.0)
                m, se = np.nanmean(y), np.nanstd(y, ddof=1) / math.sqrt(n)
                lo95, hi95, lo90, hi90 = m - 1.96 * se, m + 1.96 * se, m - 1.645 * se, m + 1.645 * se
                if k == "H1":
                    res[k].append(lo95 > 0 and m >= SESOI)
                else:                                       # decisive = SUPPORTED/HARMFUL at Holm-worst α/7, or EQUIVALENT (TOST)
                    z = norm.ppf(1 - 0.025 / 7)
                    res[k].append(abs(m) - z * se > 0 and abs(m) >= SESOI or (lo90 > -SESOI and hi90 < SESOI))
        power[n] = {k: float(np.mean(v)) for k, v in res.items()}
    n_sel = next((n for n in (200, 250, 300, 350, 400) if power[n]["H1"] >= 0.8), 400)
    conf = dict(n_units=n_sel, omega_on=r3, ranges=ranges, f_hz=P["f_hz"], r1=r1, r2_power=power, r2_h1_shift=shift,
                pilot_units=len(units), pilot_excluded=bad)
    write("analysis_pilot.json", dict(tests=t, describe=d, failure=failure(t, d), rules=conf))
    with open(os.path.join(HERE, "stage1_confirm_params.json"), "x") as fh:
        json.dump(conf, fh, indent=1)
    print(json.dumps(dict(n=n_sel, omega_on=r3, r1=r1, power=power[n_sel]), indent=1))


def confirm():
    units, bad, by = load("confirm")
    C = json.load(open(os.path.join(HERE, "stage1_confirm_params.json")))
    if len(units) + len(bad) != C["n_units"]:
        sys.exit(f"expected {C['n_units']} units, found {len(units) + len(bad)}")
    t = tests("confirm", units, by, RNG["confirm"])
    d = describe(units, by)
    write("analysis_confirm.json", dict(n_units=len(units), excluded=bad, tests=t, describe=d, failure=failure(t, d), params=C))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "pilot-rules":
        pilot_rules()
    elif cmd == "confirm":
        confirm()
    elif cmd == "describe":
        u, b, by = load(sys.argv[2])
        print(json.dumps(describe(u, by), indent=1, default=float))
