"""F1 analysis (PROTOCOL r3 §5, §7–9). Reads results/<stage>/ (feather + npz per unit), never writes outside this directory.
  pilot-r1    : R1 → pilot_r1.json (after pilot part 1)
  pilot-rules : R2–R4, R3D, power → confirm_params.json (after pilot part 2; mode "x")
  confirm     : H1, S1–S6 (Holm), validity checks, grid, SDT, neural measures, failure conditions → results/analysis_confirm.json
  robust      : 0D variants → results/analysis_robust.json
Run: .venv/bin/python -I -B flymind/experiments/f1_active_sensing/analysis.py {pilot-r1|pilot-rules|confirm|robust} [smoke]
"""
import glob
import json
import math
import os
import sys
import zlib

import numpy as np
import pandas as pd
from scipy.stats import norm

if __name__ == "__main__" and not sys.flags.dont_write_bytecode:
    sys.exit("run with python -B")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analysis_core as AC  # noqa: E402
import systems as SY  # noqa: E402

PR = json.load(open(os.path.join(HERE, "protocol.json")))
SESOI, FA = PR["sesoi_bsc"], PR["fa_max"]
EPS = 1e-9                                            # float-safe comparisons against SESOI / gates (code red team m1)
I_MAX = SY.L.ENC.i_max
TH_GRID = np.round(np.arange(PR["th_grid_mV"][0], PR["th_grid_mV"][1] + 1e-9, PR["th_grid_mV"][2]), 2)


# ---------------- loading ----------------
def load(stage, variant=""):
    """Returns (snn DataFrame, streams {unit: dict}, unit table). For the pilot, part-1 (u*) and part-2 (p2_u*) files are merged."""
    d = os.path.join(HERE, "results", stage)
    tags = ["", "p2"] if stage in ("pilot", "smoke") else [variant]
    snn, streams = [], {}
    for t in tags:
        pre = f"{t}_" if t else ""
        for f in sorted(glob.glob(os.path.join(d, f"{pre}u*.feather"))):
            if not os.path.basename(f).startswith(pre + "u"):
                continue
            u = int(os.path.basename(f)[len(pre) + 1:].split(".")[0])
            snn.append(pd.read_feather(f))
            with np.load(f[:-8] + ".npz") as z:
                streams.setdefault(u, {}).update({k: z[k] for k in z.files})
    snn = pd.concat(snn, ignore_index=True)
    units = snn.drop_duplicates("unit").set_index("unit")[["rho", "az", "k", "phi"]].sort_index()
    return snn, streams, units


class Data:
    """D arrays per (system, cond, range): DL, DR, DN aligned on the sorted unit list."""

    def __init__(self, stage, variant="", th=None, th_lp=None):
        self.snn, self.streams, self.units = load(stage, variant)
        self.u = self.units.index.to_numpy()
        self.th, self.th_lp = th, th_lp
        self.cache = {}

    def D(self, system, cond, rng="D"):
        key = (system, cond, rng)
        if key in self.cache:
            return self.cache[key]
        if system in ("DATA", "B1", "SWS"):
            t = self.snn[(self.snn.system == system) & (self.snn.cond == cond)].set_index(["side", "unit"]).D
            out = tuple(t.loc[s].reindex(self.u).to_numpy(float) for s in ("L", "R", "N"))
        else:
            out = tuple(np.array([self._ctrl(system, self.streams[u], cond, f"{rng}{s}" if s != "N" else "NN") for u in self.u])
                        for s in ("L", "R", "N"))
        if any(np.isnan(x).any() for x in out):
            raise ValueError(f"missing trials for {key}")
        self.cache[key] = out
        return out

    def _ctrl(self, system, z, cond, stim, th=None):
        g, lin = z[f"{cond}|{stim}|g"].astype(float), z[f"{cond}|{stim}|lin"].astype(float)
        if system == "P":
            return float(SY.ema(g @ [1.0, -1.0], math.exp(-0.01 / PR["p_tau_s"]))[SY.W].mean())
        if system == "LIN":
            return float(lin[SY.W].mean())
        if system == "TH":
            return float(SY.thresh_D(I_MAX * g, self.th if th is None else th)[0])
        if system == "TH_LP":
            return float(SY.thresh_D(SY.lowpass_drive(g, I_MAX, PR["th_lp_tau_ms"]), self.th_lp if th is None else th)[0])
        raise ValueError(system)

    def th_curve(self, system, cond="stat"):
        """BSC on range D for every θ of the grid (R4). c = 0 is exact here: no-target drive is 0 ⇒ D = 0 (checked)."""
        out = []
        for s in ("DL", "DR", "NN"):
            rows = []
            for u in self.u:
                z = self.streams[u]
                g = z[f"{cond}|{s}|g"].astype(float)
                dr = I_MAX * g if system == "TH" else SY.lowpass_drive(g, I_MAX, PR["th_lp_tau_ms"])
                rows.append(SY.thresh_D(dr, TH_GRID))
            out.append(np.array(rows))
        L, R, Nn = out
        assert not Nn.any(), "TH no-target D ≠ 0: criterion would not be 0"
        return 0.5 * ((L > 0).mean(0) + (R < 0).mean(0))


def bsc(D3, idx):
    L, R, Nn = D3
    b, _ = AC.bsc(L[idx][:, None], R[idx][:, None], Nn[idx], FA)
    return float(b[0])


def unit_hits(D3):
    L, R, Nn = D3
    c = AC.criterion(Nn, FA)
    return 0.5 * ((L > c).astype(float) + (R < -c).astype(float))


def sk_valid(D3, x, lo, hi, increasing=False):
    """PROTOCOL §5: edge hit rates and 7-bin monotonicity. x = rho (range D, hit falls) or k (range C, hit rises)."""
    h = unit_hits(D3)
    if increasing:
        x, lo, hi = -x, -hi, -lo
    e = PR["sk_edge_frac"] * (hi - lo)
    near, far = h[x < lo + e], h[x > hi - e]
    edges = bool(near.size and far.size and near.mean() >= PR["sk_edge_hit"][0] and far.mean() <= PR["sk_edge_hit"][1])
    b = np.minimum((PR["sk_bins"] * (x - lo) / (hi - lo)).astype(int), PR["sk_bins"] - 1)
    rates = [float(h[b == i].mean()) if (b == i).any() else np.nan for i in range(PR["sk_bins"])]
    r = np.array(rates)
    mono = bool(np.nanmax(np.diff(r[~np.isnan(r)]), initial=-1) <= PR["sk_monotone_tol"])
    return dict(valid=edges and mono, edges=edges, monotone=mono, near=float(near.mean()) if near.size else None,
                far=float(far.mean()) if far.size else None, bins=rates)


def ranges(stage):
    cp = os.path.join(HERE, "confirm_params.json")
    p = json.load(open(cp)) if stage != "pilot" and os.path.exists(cp) else {}
    return p.get("range_D_rho", PR["range_D"]["rho_m"]), p.get("range_C_k", PR["range_C"]["k"])


def sk_threshold(b, lo, hi, increasing=False):
    return (lo + (1 - b) * (hi - lo)) if increasing else (lo + b * (hi - lo))


# ---------------- bootstrap ----------------
def hier_idx(rng, inst, n_units):
    """Instances with replacement, then units within each drawn instance with replacement (PROTOCOL §8)."""
    groups = [np.flatnonzero(inst == i) for i in np.unique(inst)]
    pick = rng.integers(len(groups), size=len(groups))
    return np.concatenate([rng.choice(groups[g], size=len(groups[g])) for g in pick])


def boot_stat(stat, n, n_boot, seed, inst=None):
    rng = np.random.default_rng(seed)
    full = stat(np.arange(n))
    bs = np.array([stat(hier_idx(rng, inst, n) if inst is not None else rng.integers(n, size=n)) for _ in range(n_boot)])
    return full, bs


def classify(full, bs, measurable=True, sk=True):
    lo95, hi95 = np.percentile(bs, [2.5, 97.5])
    lo90, hi90 = np.percentile(bs, [5, 95])
    if np.ptp(bs) == 0 and full == 0:
        p = 1.0
    else:
        p = float(min(1.0, max(1 / len(bs), 2 * min((bs <= 0).mean(), (bs >= 0).mean()))))
    if lo95 > 0 and full >= SESOI - EPS:
        cls = "SUPPORTED"
    elif hi95 < 0 and full <= -SESOI + EPS:
        cls = "HARMFUL"
    elif -SESOI + EPS < lo90 and hi90 < SESOI - EPS and measurable and sk:
        cls = "EQUIVALENT"
    elif lo95 > 0 or hi95 < 0:
        cls = "DETECTABLE-BELOW-SESOI"
    elif not (measurable and sk):
        cls = "UNMEASURABLE"
    else:
        cls = "INCONCLUSIVE"
    return dict(est=float(full), ci95=[float(lo95), float(hi95)], ci90=[float(lo90), float(hi90)], p=p, cls=cls,
                negative=bool(full < 0 and hi95 < 0))


def meas(b):
    return PR["measurable_bsc"][0] - EPS <= b <= PR["measurable_bsc"][1] + EPS


# ---------------- pilot rules ----------------
def pilot_rules(stage="pilot", part=2):
    """part 1: R1 → pilot_r1.json (after pilot1). part 2: R2–R4, R3D → confirm_params.json (after pilot2).
    stage 'smoke' = dry run on smoke units: prints, writes nothing."""
    out_p = os.path.join(HERE, "confirm_params.json")
    if stage == "pilot" and os.path.exists(out_p if part == 2 else os.path.join(HERE, "pilot_r1.json")):
        sys.exit("rules are applied once — output exists")
    X = Data(stage)
    n = len(X.u)
    rho, k = X.units.rho.to_numpy(), X.units.k.to_numpy()
    (a, b), (ka, kb) = PR["range_D"]["rho_m"], PR["range_C"]["k"]
    allidx = np.arange(n)
    stat = {s: bsc(X.D(s, "stat"), allidx) for s in ("DATA", "B1", "SWS")}
    cells = [(f, A) for f in PR["sin_f_hz"] for A in PR["sin_A_deg"]]
    grid = {}
    for f, A in cells:
        c = f"sin_f{f:g}_A{A:g}"
        grid[c] = {s: bsc(X.D(s, c), allidx) - stat[s] for s in ("DATA", "B1", "SWS")}
    pooled = {c: float(np.mean(list(v.values()))) for c, v in grid.items()}

    def pick(score):
        best = max(score.values())
        tied = [(f, A) for f, A in cells if score[f"sin_f{f:g}_A{A:g}"] >= best - 0.01 - EPS]
        return sorted(tied, key=lambda t: (-t[1], t[0]))[0]
    f_s, A_s = pick(pooled)
    f_d, A_d = pick({c: v["DATA"] for c, v in grid.items()})
    r1p = os.path.join(HERE, "pilot_r1.json")
    if part == 1:
        r1 = dict(rule="R1 (PROTOCOL r3.1)", f_star=f_s, A_star=A_s, data_only_argmax=dict(f=f_d, A=A_d, agrees=(f_d, A_d) == (f_s, A_s)),
                  pilot_stat_bsc=stat, pilot_grid_delta=grid, pilot_pooled_delta=pooled, n_pilot_units=n)
        print(json.dumps(r1, indent=1))
        if stage == "pilot":
            with open(r1p, "x") as fh:
                json.dump(r1, fh, indent=1)
        return
    r1 = json.load(open(r1p)) if stage == "pilot" else dict(f_star=f_s, A_star=A_s)
    f_s, A_s = r1["f_star"], r1["A_star"]
    sin = f"sin_f{f_s:g}_A{A_s:g}"
    # R4: matched thresholds
    target = stat["DATA"]
    th = {}
    for s in ("TH", "TH_LP"):
        curve = X.th_curve(s)
        i = int(np.argmin(np.abs(curve - target)))
        th[s] = dict(theta_mV=float(TH_GRID[i]), bsc_stat=float(curve[i]), match_err=float(abs(curve[i] - target)),
                     matched=bool(abs(curve[i] - target) <= PR["th_match_max"]))
    X.th, X.th_lp = th["TH"]["theta_mV"], th["TH_LP"]["theta_mV"]
    # R3 range C (P), R3D range D (DATA)
    bP = bsc(X.D("P", "stat", "C"), allidx)
    rC = [ka, kb]
    if not (0.2 <= bP <= 0.8):
        kt = sk_threshold(bP, ka, kb, increasing=True)
        rC = [max(0.01, kt - PR["r3_halfwidth_k"]), kt + PR["r3_halfwidth_k"]]
    skD = {c: sk_valid(X.D("DATA", c), rho, a, b) for c in ("stat", sin)}
    rD = [a, b]
    if not all(v["valid"] for v in skD.values()):
        rc = float(np.mean([sk_threshold(bsc(X.D("DATA", c), allidx), a, b) for c in ("stat", sin)]))
        rD = [rc - PR["r3d_halfwidth_rho"], rc + PR["r3d_halfwidth_rho"]]
    # R2 sample size from per-unit paired differences
    jsh, jvl = f"jshuf_A{A_s:g}", f"jvel_f{f_s:g}_A{A_s:g}"
    h = lambda s, c, r="D": unit_hits(X.D(s, c, r))
    diffs = {"H1": h("DATA", sin) - h("DATA", "stat"), "S1": h("DATA", sin) - h("DATA", jsh), "S2": h("DATA", sin) - h("DATA", jvl),
             "S3": (h("DATA", sin) - h("DATA", "stat")) - (h("B1", sin) - h("B1", "stat")),
             "S4": (h("DATA", sin) - h("DATA", "stat")) - (h("SWS", sin) - h("SWS", "stat")),
             "S5": h("P", sin, "C") - h("P", "stat", "C"),
             "S6": (h("DATA", sin) - h("DATA", "stat")) - (h("TH_LP", sin) - h("TH_LP", "stat"))}
    if not th["TH_LP"]["matched"]:
        diffs.pop("S6")                               # S6 would not be tested (code red team M4)
    power = {}
    for kk, d in diffs.items():
        al, pw = (PR["alpha"], PR["power_h1"]) if kk == "H1" else (PR["alpha"] / 6, PR["power_secondary"])
        sd = float(d.std(ddof=1))
        za = norm.ppf(1 - al / 2)
        need = math.ceil(1.2 * ((za + norm.ppf(pw)) * sd / SESOI) ** 2) if sd > 0 else 0
        power[kk] = dict(sd=sd, n_required=need, alpha=al, target_power=pw)
    n_units = int(min(PR["confirm"]["n_max"], max(PR["confirm"]["n_min"], max(v["n_required"] for v in power.values()))))
    for kk, v in power.items():
        v["achieved_power_at_n"] = float(norm.cdf(math.sqrt(n_units / 1.2) * SESOI / v["sd"] - norm.ppf(1 - v["alpha"] / 2))) if v["sd"] > 0 else 1.0
        v["expected_inconclusive"] = v["achieved_power_at_n"] < 0.5
    res = dict(rule_version=PR["protocol"], f_star=f_s, A_star=A_s, r1=r1, n_units=n_units, power=power,
               theta_TH_mV=th["TH"]["theta_mV"], theta_TH_LP_mV=th["TH_LP"]["theta_mV"], threshold_match=th,
               range_C_k=rC, range_C_rule=dict(pilot_P_stat_bsc=bP, changed=rC != [ka, kb]),
               range_D_rho=rD, range_D_rule=dict(sk=skD, changed=rD != [a, b]), n_pilot_units=n,
               note="R1–R4 applied mechanically; pilot data are not used in confirmatory estimates")
    if stage == "pilot":
        with open(out_p, "x") as fh:
            json.dump(res, fh, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ("pilot_grid_delta",)}, indent=1))


# ---------------- confirm / robust ----------------
def neural_table(X, nets, conds):
    """Descriptive neural measures: mean over target trials (ipsi = target side), Δ vs stat with unit-bootstrap CI95."""
    S = X.snn[X.snn.side != "N"].copy()
    ipsi = lambda r, a, b: np.where(S.side == "L", S[a], S[b])
    S["lc_ipsi"], S["lc_contra"] = ipsi(S, "n_in_L", "n_in_R"), ipsi(S, "n_in_R", "n_in_L")
    S["dn_ipsi"], S["dn_contra"] = ipsi(S, "n_DNa02_L", "n_DNa02_R"), ipsi(S, "n_DNa02_R", "n_DNa02_L")
    S["sync_lc_ipsi"] = ipsi(S, "sync_in_L", "sync_in_R")
    S["lat_lc_ipsi"], S["lat_dn_ipsi"] = ipsi(S, "lat_in_L_ms", "lat_in_R_ms"), ipsi(S, "lat_DNa02_L_ms", "lat_DNa02_R_ms")
    S["sD"] = np.where(S.side == "L", S.D, -S.D)
    cols = ["lc_ipsi", "lc_contra", "n_mid", "dn_ipsi", "dn_contra", "sD", "sync_lc_ipsi", "sync_mid", "lat_lc_ipsi", "lat_dn_ipsi",
            "lat_decision_ms"]
    rng = np.random.default_rng(PR["analysis_rng"]["confirm"] + 7)
    out = {}
    for net in nets:
        base = S[(S.system == net) & (S.cond == "stat")].groupby("unit")[cols].mean()
        for c in conds:
            t = S[(S.system == net) & (S.cond == c)]
            if t.empty:
                continue
            m = t.groupby("unit")[cols].mean()
            row = {}
            for col in cols:
                x = m[col].to_numpy(float)
                d = (m[col] - base[col].reindex(m.index)).to_numpy(float)
                ok = ~np.isnan(d)
                bs = [np.nanmean(d[ok][rng.integers(ok.sum(), size=ok.sum())]) for _ in range(2000)] if ok.sum() > 1 else [np.nan]
                row[col] = dict(mean=float(np.nanmean(x)) if (~np.isnan(x)).any() else None,
                                delta_vs_stat=float(np.nanmean(d)) if ok.any() else None,
                                ci95=[float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))] if ok.sum() > 1 else None)
            sd = t.groupby("unit").apply(lambda q: float(q.D[q.side == "L"].iloc[0]) if (q.side == "L").any() else np.nan)
            row["fano_D_left"] = float(sd.var() / sd.mean()) if sd.mean() else None
            if "F_dn_amp_hz" in t:
                for fc in ("F_in_L_amp_hz", "F_in_R_amp_hz", "F_dn_amp_hz", "F_dn_phase"):
                    if fc in t and t[fc].notna().any():
                        row[fc] = float(t[fc].mean()) if "amp" in fc else float(np.angle(np.exp(1j * t[fc].dropna()).mean()))
            out[f"{net}|{c}"] = row
    return out


def sdt(D3, idx=None):
    L, R, Nn = D3
    c = AC.criterion(Nn, FA)
    n = len(L)
    a = AC.auc(L, R)
    ad = AC.auc(np.r_[np.abs(L), np.abs(R)], np.abs(Nn))
    side = np.r_[np.ones(n), -np.ones(n)]
    resp = np.r_[AC.responses(L, c), AC.responses(R, c)]
    return dict(criterion=c, fa=float((np.abs(Nn) > c).mean()), hit_L=float((L > c).mean()), hit_R=float((R < -c).mean()),
                bsc=float(0.5 * ((L > c).mean() + (R < -c).mean())), dprime_LR=AC.dprime_from_auc(a, n), auc_LR=a,
                dprime_det=AC.dprime_from_auc(ad, n), mi_bits=AC.mi_bits(side, resp),
                frac_D0=float(np.mean(np.r_[L, R] == 0)), side_failure=bool(min((L > c).mean(), (R < -c).mean()) < 0.1 and
                                                                             max((L > c).mean(), (R < -c).mean()) > 0.5))


def confirm(stage="confirm"):
    cp = json.load(open(os.path.join(HERE, "confirm_params.json")))
    X = Data(stage, th=cp["theta_TH_mV"], th_lp=cp["theta_TH_LP_mV"])
    n = len(X.u)
    if n != cp["n_units"]:
        sys.exit(f"confirm has {n} units, protocol requires {cp['n_units']} — STOP")
    rho, kk = X.units.rho.to_numpy(), X.units.k.to_numpy()
    (a, b), (ka, kb) = ranges(stage)
    f, A = cp["f_star"], cp["A_star"]
    sin, jsh, jrm, jvl, mt = f"sin_f{f:g}_A{A:g}", f"jshuf_A{A:g}", f"jrms_A{A:g}", f"jvel_f{f:g}_A{A:g}", f"mt_f{f:g}_A{A:g}"
    first = PR["confirm"]["units_first"]
    inst = {"B1": (X.u - first) % 10, "SWS": (X.u - first) % 10}
    NB, seed = PR["n_boot"], PR["analysis_rng"]["confirm"]
    allidx = np.arange(n)
    sk = lambda s, c, r="D": sk_valid(X.D(s, c, r), rho if r == "D" else kk, *((a, b) if r == "D" else (ka, kb)), increasing=r == "C")
    B = lambda s, c, r="D": (lambda idx: bsc(X.D(s, c, r), idx))
    res = dict(n_units=n, f_star=f, A_star=A, range_D=[a, b], range_C=[ka, kb], theta_TH=X.th, theta_TH_LP=X.th_lp)

    def test(name, terms, inst_=None, arms=()):
        stat = lambda idx: sum(w * B(*t)(idx) for w, t in terms)
        full, bs = boot_stat(stat, n, NB, seed + zlib.crc32(name.encode()) % 1000, inst_)
        armv = {f"{t[0]}|{t[1]}|{t[2] if len(t) > 2 else 'D'}": B(*t)(allidx) for t in arms}
        skv = {k_: sk(*t)["valid"] for k_, t in zip(armv, arms)}
        r = classify(full, bs, all(meas(v) for v in armv.values()), all(skv.values()))
        r.update(arms=armv, sk_valid=skv, threshold_shift_m=float(full * (b - a)) if all(skv.values()) and arms and arms[0][-1] != "C" else None)
        return r

    res["H1"] = test("H1", [(1, ("DATA", sin)), (-1, ("DATA", "stat"))], arms=[("DATA", sin), ("DATA", "stat")])
    fam = {"S1": test("S1", [(1, ("DATA", sin)), (-1, ("DATA", jsh))], arms=[("DATA", sin), ("DATA", jsh)]),
           "S2": test("S2", [(1, ("DATA", sin)), (-1, ("DATA", jvl))], arms=[("DATA", sin), ("DATA", jvl)])}
    for s, key in (("B1", "S3"), ("SWS", "S4")):
        fam[key] = test(key, [(1, ("DATA", sin)), (-1, ("DATA", "stat")), (-1, (s, sin)), (1, (s, "stat"))], inst[s],
                        arms=[("DATA", sin), ("DATA", "stat"), (s, sin), (s, "stat")])
    fam["S5"] = test("S5", [(1, ("P", sin, "C")), (-1, ("P", "stat", "C"))], arms=[("P", sin, "C"), ("P", "stat", "C")])
    lp_err = abs(bsc(X.D("TH_LP", "stat"), allidx) - bsc(X.D("DATA", "stat"), allidx))
    res["TH_LP_match_on_confirm"] = dict(err=lp_err, pilot=cp["threshold_match"]["TH_LP"])
    lp_ok = cp["threshold_match"]["TH_LP"]["matched"] and lp_err <= PR["th_match_max"] + EPS     # r3.2: gate on the confirm range too
    if lp_ok:
        fam["S6"] = test("S6", [(1, ("DATA", sin)), (-1, ("DATA", "stat")), (-1, ("TH_LP", sin)), (1, ("TH_LP", "stat"))],
                         arms=[("DATA", sin), ("DATA", "stat"), ("TH_LP", sin), ("TH_LP", "stat")])
    ps = [v["p"] for v in fam.values()] + ([] if lp_ok else [1.0])          # Holm family is always the pre-registered 6
    adj, rej = AC.holm(ps)
    for (k_, v), p_, r_ in zip(fam.items(), adj, rej):
        v.update(p_holm=p_, holm_reject=r_)
    if not lp_ok:
        fam["S6"] = dict(cls="NOT TESTED (TH_LP unmatched)", p=1.0, p_holm=adj[-1], holm_reject=False,
                         match=res["TH_LP_match_on_confirm"])
    res["secondary"] = fam
    # validity and exploratory
    res["validity"] = {"DATA sin − MT": test("V1", [(1, ("DATA", sin)), (-1, ("DATA", mt))], arms=[("DATA", sin), ("DATA", mt)]),
                       "P sin − J_shuf (C)": test("V2", [(1, ("P", sin, "C")), (-1, ("P", jsh, "C"))], arms=[("P", sin, "C"), ("P", jsh, "C")]),
                       "TH sin − J_shuf (D)": test("V3", [(1, ("TH", sin)), (-1, ("TH", jsh))], arms=[("TH", sin), ("TH", jsh)])}
    grid = {}
    for g_f in PR["sin_f_hz"]:
        for g_A in PR["sin_A_deg"]:
            c = f"sin_f{g_f:g}_A{g_A:g}"
            grid[c] = test(c, [(1, ("DATA", c)), (-1, ("DATA", "stat"))], arms=[("DATA", c), ("DATA", "stat")])
    adj, _ = AC.holm([v["p"] for v in grid.values()])
    for v, p_ in zip(grid.values(), adj):
        v["p_holm16"] = p_
    res["grid_DATA"] = grid
    expl = {}
    for s in ("DATA", "B1", "SWS", "P", "TH", "TH_LP", "LIN"):
        for c in ("stat", sin, jsh, jrm, jvl) + ((mt,) if s not in ("B1", "SWS") else ()):
            for r in ("D", "C") if s not in ("DATA", "B1", "SWS") else ("D",):
                expl[f"{s}|{c}|{r}"] = dict(sdt(X.D(s, c, r)), sk=sk(s, c, r))
    res["sdt"] = expl
    res["rho_bins_hits"] = {k_: v["sk"]["bins"] for k_, v in expl.items()}
    # per-instance table and DATA rank
    per = {}
    dD = bsc(X.D("DATA", sin), allidx) - bsc(X.D("DATA", "stat"), allidx)
    for s in ("B1", "SWS"):
        per[s] = []
        for i in range(10):
            idx = np.flatnonzero(inst[s] == i)
            per[s].append(dict(instance=i, n=len(idx), delta=bsc(X.D(s, sin), idx) - bsc(X.D(s, "stat"), idx),
                               data_delta_same_units=bsc(X.D("DATA", sin), idx) - bsc(X.D("DATA", "stat"), idx)))
    allc = [x["delta"] for s in per for x in per[s]]
    res["per_instance"] = dict(table=per, data_delta=dD, data_rank_from_top=int(1 + sum(v > dD for v in allc)), n_controls=len(allc))
    res["neural"] = neural_table(X, ("DATA", "B1", "SWS"), ("stat", sin, jsh, jrm, jvl, mt))
    # failure conditions (descriptive)
    g_pos = sum(1 for v in grid.values() if v["p_holm16"] < 0.05 and v["est"] > 0)
    lc = res["neural"].get(f"DATA|{sin}", {}).get("lc_ipsi", {})
    res["failure_conditions"] = {
        "F-a H1 not SUPPORTED": res["H1"]["cls"] != "SUPPORTED",
        "F-b no sinusoid specificity": any(fam[k_]["cls"] == "EQUIVALENT" or fam[k_]["negative"] for k_ in ("S1", "S2")),
        "F-c not SNN-specific": fam["S5"]["cls"] == "SUPPORTED" or ("negative" in fam["S6"] and (fam["S6"]["cls"] == "EQUIVALENT" or fam["S6"]["negative"])),
        "F-d no wiring specificity": all(fam[k_]["cls"] == "EQUIVALENT" or fam[k_]["negative"] for k_ in ("S3", "S4")),
        "F-e narrow (≤ 1 grid cell)": g_pos <= 1,
        "F-f firing without information": bool(lc.get("ci95") and lc["ci95"][0] > 0 and res["H1"]["cls"] != "SUPPORTED"),
        "F-h side failure": expl[f"DATA|{sin}|D"]["side_failure"],
        "grid_cells_positive_holm": g_pos}
    return res


def robust_range(v, over, rD):
    """0D rho range: small_ball scales the (possibly R3D re-centred) range D by 0.72 (code red team m6); others use range D."""
    if v == "small_ball":
        return [0.72 * rD[0], 0.72 * rD[1]]
    return rD


def robust():
    cp = json.load(open(os.path.join(HERE, "confirm_params.json")))
    f, A = cp["f_star"], cp["A_star"]
    sin, jsh = f"sin_f{f:g}_A{A:g}", f"jshuf_A{A:g}"
    out = {}
    rD = ranges("robust")[0]
    for v, over in PR["robust"]["variants"].items():
        X = Data("robust", v, th=cp["theta_TH_mV"], th_lp=cp["theta_TH_LP_mV"])
        n = len(X.u)
        a, b = robust_range(v, over, rD)
        r = {}
        for s in ("DATA", "B1", "SWS", "P", "TH", "TH_LP", "LIN"):
            for c2, lab in ((sin, "sin−stat"), (jsh, "jshuf−stat")):
                st = lambda idx, s=s, c2=c2: bsc(X.D(s, c2), idx) - bsc(X.D(s, "stat"), idx)
                full, bs = boot_stat(st, n, PR["n_boot"], PR["analysis_rng"]["robust"])
                r[f"{s}|{lab}"] = dict(classify(full, bs, meas(bsc(X.D(s, "stat"), np.arange(n))) and meas(bsc(X.D(s, c2), np.arange(n)))),
                                       stat=sdt(X.D(s, "stat")), moved=sdt(X.D(s, c2)),
                                       sk_stat=sk_valid(X.D(s, "stat"), X.units.rho.to_numpy(), a, b)["valid"])
        out[v] = r
    pos = sum(out[v]["DATA|sin−stat"]["ci95"][0] > 0 for v in out)
    out["F-g fewer than 3 of 4 variants with CI95 > 0 (DATA)"] = pos < 3
    out["variants_with_DATA_benefit"] = pos
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd in ("pilot-r1", "pilot-rules"):
        pilot_rules(sys.argv[2] if len(sys.argv) > 2 else "pilot", 1 if cmd == "pilot-r1" else 2)
    elif cmd in ("confirm", "robust"):
        r = confirm() if cmd == "confirm" else robust()
        path = os.path.join(HERE, "results", f"analysis_{cmd}.json")
        with open(path, "x") as fh:
            json.dump(r, fh, indent=1, default=float)
        print("written", path)
    else:
        sys.exit(__doc__)
