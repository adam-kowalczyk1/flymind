"""flymind/experiments/bio_advantage/d0_analysis.py — Stage D0: spatial sensorimotor maps in MaleCNS wiring (DATA ONLY).

No simulation, no neuron dynamics, no robot. Reads the three MaleCNS files, writes only to a NEW output directory.
Definitions, thresholds and seeds are fixed in D0_PREREG.md; the script refuses to run if that file's hash differs
from the one given on the command line.

Run (from anywhere):
  .venv/bin/python -I -B flymind/experiments/bio_advantage/d0_analysis.py \
      --prereg-sha256 <sha> --out flymind/results/bio_advantage/d0_v1
"""
import argparse
import hashlib
import itertools
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather
from scipy.stats import rankdata

HERE = os.path.dirname(os.path.abspath(__file__))
FLYMIND = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, FLYMIND)                      # python -I does not add it; imports below are read-only project code

import leg_circuit  # noqa: E402
import visual_path  # noqa: E402
from connectome import load_edges  # noqa: E402
from snn_interface import SNNSpec  # noqa: E402
from visual_path import ANN, WEIGHTS  # noqa: E402

NPERM, MIN_SYN, COVER = 10_000, 20, 0.8
SEED0 = 19_100_001                               # D0-a/b permutation tests: default_rng([SEED0, running test index])
SHUF_SEEDS = list(range(19_100_101, 19_100_201))  # D0-c edge-swap shuffles
LABEL_SEED = 19_100_090                          # D0-c label permutation
VPN_DN = {"LPLC2": ["DNp04", "DNp06", "DNp01"], "LPLC1": ["DNp03", "DNp06", "DNp11"],
          "LC4": ["DNp01", "DNp02", "DNp04", "DNp11"]}
CONFIRM = [("LPLC2", "DNp04"), ("LPLC2", "DNp06"), ("LPLC1", "DNp03"), ("LPLC1", "DNp06"), ("LPLC1", "DNp11")]
PRESS, RELEASE = ("Ti extensor MN",), ("Ti flexor MN", "Acc. ti flexor MN")   # same pools as fly_jaw.py
ALPHA = 0.01
LOG = []


def log(s=""):
    print(s, flush=True)
    LOG.append(s)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


class Edges:
    """Whole edge list in memory once (Arrow), filtered by pre / post id sets."""

    def __init__(self):
        self.t = feather.read_table(WEIGHTS)

    def _f(self, col, ids):
        return self.t.filter(pc.is_in(self.t[col], pa.array(np.asarray(ids, dtype=np.int64)))).to_pandas()

    def into(self, ids):
        return self._f("body_post", ids)

    def outof(self, ids):
        return self._f("body_pre", ids)


def _wmean(inp, pos):
    """Synapse-weighted mean position of each post neuron over its positioned presynaptic partners."""
    d = inp[inp.body_pre.isin(pos.index)]
    w = d.weight.to_numpy(float)
    g = pd.DataFrame({"post": d.body_post.to_numpy(), "w": w,
                      "h1w": w * pos.h1.reindex(d.body_pre).to_numpy(),
                      "h2w": w * pos.h2.reindex(d.body_pre).to_numpy()}).groupby("post").sum()
    return pd.DataFrame({"h1": g.h1w / g.w, "h2": g.h2w / g.w, "nsyn": g.w})


def positions(ids, E, hexa, min_syn=MIN_SYN):
    """PREREG §2: method A (direct hex-annotated inputs) if ≥ 80 % of ids have ≥ min_syn such synapses, else method B."""
    inp = E.into(ids)
    A = _wmean(inp, hexa)
    cover = float((A.nsyn.reindex(ids).fillna(0) >= min_syn).mean())
    if cover >= COVER:
        return A[A.nsyn >= min_syn], "A", cover
    PA = _wmean(E.into(inp.body_pre.unique()), hexa)
    B = _wmean(inp, PA[PA.nsyn >= min_syn])
    return B[B.nsyn >= min_syn], "B", cover


def grad_test(y, H, rng, nperm=NPERM):
    """R = multiple correlation of rank(y) with the plane a·h1 + b·h2 + c; permutation p (PREREG §2)."""
    y, H = np.asarray(y, float), np.asarray(H, float)
    r = rankdata(y)
    r = r - r.mean()
    ss = float(r @ r)
    if len(y) < 10 or ss == 0:
        return dict(n=len(y), R=None, p=1.0, angle_deg=None, null_p95=None)
    Hc = H - H.mean(0)
    Q, _ = np.linalg.qr(Hc)
    R = float(np.sqrt(((Q.T @ r) ** 2).sum() / ss))
    a, b = np.linalg.lstsq(Hc, r, rcond=None)[0]
    Rn = np.sqrt(((rng.permuted(np.tile(r, (nperm, 1)), axis=1) @ Q) ** 2).sum(1) / ss)
    return dict(n=len(y), R=round(R, 4), p=float((1 + (Rn >= R - 1e-12).sum()) / (nperm + 1)),
                angle_deg=round(float(np.degrees(np.arctan2(b, a))), 1), null_p95=round(float(np.quantile(Rn, 0.95)), 4))


def spear_perm(x, y, rng, nperm=NPERM):
    rx, ry = rankdata(x) - (len(x) + 1) / 2, rankdata(y) - (len(y) + 1) / 2
    den = np.sqrt((rx @ rx) * (ry @ ry))
    if den == 0:
        return dict(n=len(x), rho=None, p=1.0)
    rho = float(rx @ ry / den)
    rn = rng.permuted(np.tile(ry, (nperm, 1)), axis=1) @ rx / den
    return dict(n=len(x), rho=round(rho, 4), p=float((1 + (np.abs(rn) >= abs(rho) - 1e-12).sum()) / (nperm + 1)))


def selftest():
    rng = np.random.default_rng(0)
    H = rng.normal(size=(120, 2))
    planted = grad_test(H @ [1.0, -2.0] + 0.3 * rng.normal(size=120), H, rng, 2000)
    none = [grad_test(rng.normal(size=120), H, rng, 500)["p"] for _ in range(200)]
    assert planted["R"] > 0.9 and planted["p"] < 0.001, planted
    assert abs(planted["angle_deg"] - np.degrees(np.arctan2(-2, 1))) < 10, planted
    assert 0.01 < np.mean(np.array(none) < 0.05) < 0.12, np.mean(np.array(none) < 0.05)   # null is calibrated
    s = spear_perm(H[:, 0], -H[:, 0] + 0.1 * rng.normal(size=120), rng, 2000)
    assert s["rho"] < -0.9 and s["p"] < 0.001, s
    P = np.array([[1.0, 0], [0, 1.0]])
    assert abs(mean_jsd(P) - 1.0) < 1e-9 and mean_jsd(np.array([[.5, .5], [.5, .5]])) < 1e-12


# ---------------------------------------------------------------- D0-a
def d0a(E, ann, hexa, min_syn=MIN_SYN, frac=False, k0=0):
    res, k = [], k0
    ty, side_of = ann.set_index("bodyId").type, ann.set_index("bodyId").somaSide
    for vpn, dns in VPN_DN.items():
        for side in "LR":
            ids = ann.bodyId[(ann.type == vpn) & (ann.somaSide == side)].astype(int).tolist()
            pos, method, cover = positions(ids, E, hexa, min_syn)
            out = E.outof(ids)
            tot = out.groupby("body_pre").weight.sum().reindex(ids).fillna(0)
            counts = {}
            for dn in dns:
                o = out[out.body_post.map(ty) == dn]
                by_body = o.groupby("body_post").weight.sum()
                target = int(by_body.idxmax())
                y = o[o.body_post == target].groupby("body_pre").weight.sum().reindex(ids).fillna(0)
                counts[dn] = y
                yy = (y / tot.replace(0, np.nan)).fillna(0) if frac else y
                ok = [b for b in ids if b in pos.index]
                t = grad_test(yy.loc[ok], pos.loc[ok, ["h1", "h2"]], np.random.default_rng([SEED0, k]))
                k += 1
                res.append(dict(vpn=vpn, dn=dn, side=side, target_body=target, target_side=side_of.get(target),
                                n_pop=len(ids), method=method, cover_A=round(cover, 3), synapses=int(y.sum()),
                                connected=int((y > 0).sum()), confirmatory=(vpn, dn) in CONFIRM, **t))
            for d1, d2 in itertools.combinations(dns, 2):
                s = spear_perm(counts[d1], counts[d2], np.random.default_rng([SEED0, k]))
                k += 1
                res.append(dict(vpn=vpn, pair=f"{d1}|{d2}", side=side, kind="opposite", **s))
    return res, k


# ---------------------------------------------------------------- D0-b
def d0b(E, hexa, k0):
    spec, idx, rep = visual_path.network(J0=1.0)
    W = np.asarray(spec.W_data, float)
    W2, A2 = W @ W, np.abs(W) @ np.abs(W)
    bodies = np.asarray(spec.bodies)
    res, k = [], k0
    for side, other in (("L", "R"), ("R", "L")):
        lc = np.asarray(idx["in_" + side])
        ip, co = int(idx["DNa02_" + side][0]), int(idx["DNa02_" + other][0])
        ids = bodies[lc].astype(int).tolist()
        pos, method, cover = positions(ids, E, hexa)
        ok = np.array([b in pos.index for b in ids])
        H = pos.loc[[b for b in ids if b in pos.index], ["h1", "h2"]]
        ys = {"signed_ipsi_minus_contra": W2[ip, lc] - W2[co, lc], "unsigned_ipsi_minus_contra": A2[ip, lc] - A2[co, lc],
              "unsigned_ipsi": A2[ip, lc], "signed_ipsi": W2[ip, lc]}
        for name, y in ys.items():
            t = grad_test(y[ok], H, np.random.default_rng([SEED0, k]))
            k += 1
            res.append(dict(side=side, y=name, primary=name == "signed_ipsi_minus_contra", method=method,
                            cover_A=round(cover, 3), n_pop=len(ids), mean=float(np.mean(y)),
                            cv=float(np.std(y) / abs(np.mean(y))) if np.mean(y) else None,
                            frac_positive=float(np.mean(y > 0)), **t))
    meta = dict(sizes=rep["sizes"], zero_sign_neurons=int((np.asarray(spec.sign) == 0).sum()), N=len(bodies))
    return res, meta, k


# ---------------------------------------------------------------- D0-c
def mean_jsd(D):
    """Mean pairwise Jensen–Shannon divergence (base 2) between the rows of D (each row a distribution)."""
    def H(p):
        p = p[p > 0]
        return float(-(p * np.log2(p)).sum())
    js = [H((p + q) / 2) - (H(p) + H(q)) / 2 for p, q in itertools.combinations(D, 2)]
    return float(np.mean(js)) if js else float("nan")


_CIRC = {}


def circuit(side):
    """T2 leg circuit as an unsigned count matrix N[post, pre] + bristle types and motor pools (cached per process)."""
    if side not in _CIRC:
        bodies, groups, rep = leg_circuit.select("T2", side)
        edges, _ = load_edges(WEIGHTS, bodies=bodies)
        pos = {b: i for i, b in enumerate(bodies)}
        N = np.zeros((len(bodies), len(bodies)))
        N[edges.body_post.map(pos).to_numpy(), edges.body_pre.map(pos).to_numpy()] = edges.weight.to_numpy(float)
        np.fill_diagonal(N, 0.0)
        ty = pd.read_feather(ANN, columns=["bodyId", "type"]).set_index("bodyId").type
        br = groups["sensory"]["mechanosensory bristle"]
        tcount = pd.Series([ty.get(b) for b in br]).value_counts()
        keep = sorted(t for t, n in tcount.items() if n >= 8)
        br = [b for b in br if ty.get(b) in keep]
        lab = np.array([keep.index(ty.get(b)) for b in br])
        pools = sorted(groups["MN"])
        mn = [b for p in pools for b in groups["MN"][p]]
        mlab = np.array([i for i, p in enumerate(pools) for _ in groups["MN"][p]])
        _CIRC[side] = dict(bodies=np.asarray(bodies), N=N, br=np.array([pos[b] for b in br]), lab=lab, types=keep,
                           mn=np.array([pos[b] for b in mn]), mlab=mlab, pools=pools, sizes=rep["sizes"],
                           type_n={t: int(tcount[t]) for t in keep}, edges=int(len(edges)))
    return _CIRC[side]


def per_bristle(N, c):
    """V[bristle, pool] = direct + two-hop unsigned path weight from each bristle to each motor pool."""
    P = N[np.ix_(c["mn"], c["br"])] + N[c["mn"], :] @ N[:, c["br"]]
    return np.stack([P[c["mlab"] == i].sum(0) for i in range(len(c["pools"]))], 1)


def type_dist(V, lab, n_types):
    D = np.stack([V[lab == t].sum(0) for t in range(n_types)])
    s = D.sum(1, keepdims=True)
    return (D / np.where(s == 0, 1, s))[s[:, 0] > 0]


def S_of(N, c):
    return mean_jsd(type_dist(per_bristle(N, c), c["lab"], len(c["types"])))


def shuffled_S(args):
    side, seed = args
    c = circuit(side)
    z = np.zeros_like(c["N"])
    spec = SNNSpec(bodies=c["bodies"], nt=None, sign=None, W_data=c["N"], W_model=z, report={})
    sh = visual_path.shuffle(spec, seed, equal_weight=False)          # the project's own degree-preserving shuffle
    return seed, S_of(sh.W_data, c), int(sh.report["shuffle"]["swaps"])


def d0c():
    res = {}
    for side in "LR":
        c = circuit(side)
        V = per_bristle(c["N"], c)
        D = type_dist(V, c["lab"], len(c["types"]))
        S = mean_jsd(D)
        t0 = time.perf_counter()
        first = shuffled_S((side, SHUF_SEEDS[0]))
        dt = time.perf_counter() - t0
        seeds = SHUF_SEEDS[1:] if dt <= 60 else SHUF_SEEDS[1:20]
        with ProcessPoolExecutor(8) as ex:
            rest = list(ex.map(shuffled_S, [(side, s) for s in seeds]))
        null = np.array([first[1]] + [r[1] for r in rest])
        rng = np.random.default_rng(LABEL_SEED + (side == "R"))
        lab_null = np.array([mean_jsd(type_dist(V, rng.permutation(c["lab"]), len(c["types"]))) for _ in range(NPERM)])
        pi = {p: i for i, p in enumerate(c["pools"])}
        pr = D[:, [pi[p] for p in PRESS if p in pi]].sum(1)
        rl = D[:, [pi[p] for p in RELEASE if p in pi]].sum(1)
        index = (pr - rl) / np.where(pr + rl == 0, 1, pr + rl)
        res[side] = dict(sizes=c["sizes"], edges=c["edges"], n_bristles=int(len(c["br"])), types=c["type_n"],
                         pools=c["pools"], S_data=S, shuffle_seconds_first=round(dt, 1), n_shuffles=int(len(null)),
                         shuffle_seeds=[SHUF_SEEDS[0]] + list(seeds), S_null=[round(float(x), 6) for x in null],
                         S_null_max=float(null.max()), S_null_mean=float(null.mean()), S_null_sd=float(null.std(ddof=1)),
                         z=float((S - null.mean()) / null.std(ddof=1)), n_null_ge_data=int((null >= S).sum()),
                         swaps_first=first[2], label_perm_p=float((1 + (lab_null >= S).sum()) / (NPERM + 1)),
                         label_null_mean=float(lab_null.mean()),
                         press_release_index={t: round(float(x), 3) for t, x in zip(c["types"], index)},
                         dist={t: {p: round(float(v), 4) for p, v in zip(c["pools"], row)} for t, row in zip(c["types"], D)})
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg-sha256", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    prereg = os.path.join(HERE, "D0_PREREG.md")
    if sha(prereg) != a.prereg_sha256:
        sys.exit("D0_PREREG.md hash differs from --prereg-sha256: refusing to run")
    selftest()
    os.makedirs(a.out, exist_ok=False)            # never overwrite an earlier result
    t0 = time.time()
    data = {os.path.basename(p): sha(p) for p in (ANN, visual_path.NTS, WEIGHTS)}
    frozen = open(os.path.join(FLYMIND, "results", "vision_manipulation", "FREEZE_v3.txt")).read()
    if not all(h in frozen for h in data.values()):
        sys.exit(f"data hashes differ from FREEZE_v3.txt: {data}")
    log(f"D0 start {time.strftime('%Y-%m-%d %H:%M:%S %z')}; prereg {a.prereg_sha256}; script {sha(os.path.abspath(__file__))}")
    log("data hashes equal FREEZE_v3.txt: " + json.dumps(data))
    ann = pd.read_feather(ANN, columns=["bodyId", "type", "somaSide", "assignedOlHex1", "assignedOlHex2"])
    hx = ann.dropna(subset=["assignedOlHex1", "assignedOlHex2"])
    hexa = pd.DataFrame({"h1": hx.assignedOlHex1.astype(float).to_numpy(), "h2": hx.assignedOlHex2.astype(float).to_numpy()},
                        index=hx.bodyId.astype(int).to_numpy())
    E = Edges()
    log(f"edges {E.t.num_rows}; hex-annotated bodies {len(hexa)}")

    A, k = d0a(E, ann, hexa)
    log("\n== D0-a gradients (y = synapse count; R, permutation p; * = confirmatory)")
    for r in A:
        if "R" in r:
            log(f"{'*' if r['confirmatory'] else ' '} {r['vpn']:6s}->{r['dn']:6s} {r['side']} n={r['n']:3d}/{r['n_pop']:3d} "
                f"pos={r['method']} syn={r['synapses']:5d} R={r['R']} null95={r['null_p95']} p={r['p']:.5f} angle={r['angle_deg']}")
    log("\n== D0-a opposite gradients (Spearman between counts onto two targets)")
    for r in A:
        if r.get("kind") == "opposite":
            log(f"  {r['vpn']:6s} {r['pair']:14s} {r['side']} n={r['n']} rho={r['rho']} p={r['p']:.5f}")
    A_frac, k = d0a(E, ann, hexa, frac=True, k0=k)
    A_50, k = d0a(E, ann, hexa, min_syn=50, k0=k)
    verdict_a = {}
    for vpn, dn in CONFIRM:
        ps = {r["side"]: r["p"] for r in A if r.get("dn") == dn and r["vpn"] == vpn and "R" in r}
        verdict_a[f"{vpn}->{dn}"] = dict(p=ps, PASS=bool(ps["L"] < ALPHA and ps["R"] < ALPHA),
                                         sens_frac={r["side"]: r["p"] for r in A_frac if r.get("dn") == dn and r["vpn"] == vpn},
                                         sens_min50={r["side"]: r["p"] for r in A_50 if r.get("dn") == dn and r["vpn"] == vpn})
    Ha = any(v["PASS"] for v in verdict_a.values())
    log("\n== D0-a verdict (PASS = p < 0.01 in both hemispheres)")
    for kx, v in verdict_a.items():
        log(f"  {kx}: {'PASS' if v['PASS'] else 'fail'} p={v['p']} | frac {v['sens_frac']} | min50 {v['sens_min50']}")
    log(f"  H-a (≥ 1 confirmatory pair passes): {'PASS' if Ha else 'FAIL — kill criterion met'}")

    B, metaB, k = d0b(E, hexa, k)
    log(f"\n== D0-b LC10a → DNa02 two-hop path vs position; network {metaB}")
    for r in B:
        log(f"{'*' if r['primary'] else ' '} {r['side']} {r['y']:28s} n={r['n']}/{r['n_pop']} pos={r['method']} "
            f"(coverA {r['cover_A']}) R={r['R']} null95={r['null_p95']} p={r['p']:.5f} angle={r['angle_deg']} "
            f"cv={None if r['cv'] is None else round(r['cv'], 2)} frac>0={r['frac_positive']:.2f}")
    pb = {r["side"]: r["p"] for r in B if r["primary"]}
    Hb = bool(pb["L"] < ALPHA and pb["R"] < ALPHA)
    log(f"  H-b: {'PASS' if Hb else 'FAIL'} p={pb}")

    C = d0c()
    log("\n== D0-c bristle types → motor pools (S = mean pairwise JSD, unsigned direct + two-hop paths)")
    for side, r in C.items():
        log(f"  T2 {side}: circuit {r['sizes']} edges={r['edges']} bristles={r['n_bristles']} types={len(r['types'])} "
            f"pools={len(r['pools'])} | S_data={r['S_data']:.4f} null mean={r['S_null_mean']:.4f} max={r['S_null_max']:.4f} "
            f"(n={r['n_shuffles']}, first shuffle {r['shuffle_seconds_first']} s, swaps {r['swaps_first']}) z={r['z']:.1f} "
            f"null≥data={r['n_null_ge_data']} | label-perm p={r['label_perm_p']:.5f}")
        log(f"     press/release index by type: {r['press_release_index']}")
    Hc = all(r["n_null_ge_data"] == 0 for r in C.values())
    log(f"  H-c (data > every shuffle on both sides): {'PASS' if Hc else 'FAIL'}")

    log(f"\nD0 done in {time.time() - t0:.0f} s")
    out = dict(prereg_sha256=a.prereg_sha256, script_sha256=sha(os.path.abspath(__file__)), data_sha256=data,
               params=dict(NPERM=NPERM, MIN_SYN=MIN_SYN, COVER=COVER, ALPHA=ALPHA, SEED0=SEED0, LABEL_SEED=LABEL_SEED),
               d0a=A, d0a_sens_frac=A_frac, d0a_sens_min50=A_50, d0a_verdict=verdict_a, H_a=Ha,
               d0b=B, d0b_meta=metaB, H_b=Hb, d0c=C, H_c=Hc)
    with open(os.path.join(a.out, "d0_results.json"), "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False, default=str)
    with open(os.path.join(a.out, "d0_stdout.txt"), "w") as f:
        f.write("\n".join(LOG) + "\n")


if __name__ == "__main__":
    main()
