"""flymind/v5v3_control_check.py — techniczna walidacja kontroli SHUF_WITHIN_SIDE v2 (warstwa × strona) przed protokołem V5 v3
(bez pętli, bez MuJoCo). Cel ustalony przed uruchomieniem: (1) czy kontrola zachowuje lateralizację strukturalną
i funkcjonalną; (2) co poza tym zmienia (rekurencja, wartość własna, architektura warstw); (3) gdzie leży ewentualna różnica
dynamiczna (dekompozycja bloku LC10a×LC10a). Nie służy do strojenia: J0, próg synaps, enkoder i sceny V5 v3 są ustalone.
Napęd: 12 mV·g do LC10a jednej strony, 300 ms, g ∈ {0,50; 0,55; 0,60; 0,70; 1,00}; ziarna ALIF 1001–1015 (dev; zalecenie RT).
Sieci: DATA; SWS v2 ziarna 1401–1403; dekompozycja (ziarno 1401): DATA z blokiem LC×LC z SWS i SWS z blokiem LC×LC z DATA.
Uruchom: .venv/bin/python -I -B flymind/v5v3_control_check.py --out flymind/results/v5v3_prep
"""
import argparse
import json
import os
import sys
import time

import numpy as np

if __name__ == "__main__" and not sys.flags.dont_write_bytecode:
    sys.exit("uruchom z python -B")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from alif import ALIF, ALIFParams, rates  # noqa: E402
from loop import _allowed, stage1_hashes  # noqa: E402
from side_shuffle import KEYS, layer_side_labels, properties, shuffle_within_side  # noqa: E402
from snn_interface import SNNSpec  # noqa: E402
from v5v2_topology import lateralization  # noqa: E402
from visual_path import network  # noqa: E402

P = ALIFParams(noise=2.0)
AMPS, SEEDS = (0.50, 0.55, 0.60, 0.70, 1.00), tuple(range(1001, 1016))


def curve(spec, W, idx):
    sp = SNNSpec(spec.bodies, spec.nt, spec.sign, W, spec.W_model, {})
    out = {}
    for amp in AMPS:
        ipsi, contra = [], []
        for s, o in (("L", "R"), ("R", "L")):
            I = np.zeros((300, len(spec.bodies)))
            I[:, idx[f"in_{s}"]] = 12.0 * amp
            for seed in SEEDS:
                r = rates(ALIF(sp, P, seed).run(I, 300), P.dt)
                ipsi.append(r[idx[f"DNa02_{s}"]].mean())
                contra.append(r[idx[f"DNa02_{o}"]].mean())
        out[str(amp)] = dict(ipsi=round(float(np.mean(ipsi)), 1), ipsi_sem=round(float(np.std(ipsi, ddof=1) / np.sqrt(len(ipsi))), 1),
                             contra=round(float(np.mean(contra)), 1))
    return out


def structure(W, idx):
    lc, dn, mid = np.r_[idx["in_L"], idx["in_R"]], np.r_[idx["DNa02_L"], idx["DNa02_R"]], idx["mid"]
    nz = W != 0
    rec = lambda a, b: int((nz[np.ix_(a, b)] & nz[np.ix_(b, a)].T).sum() // (2 if a is b else 1))
    return dict(lambda_max_re=round(float(np.max(np.linalg.eigvals(W).real)), 2), recip_LC_LC=rec(lc, lc), recip_mid_mid=rec(mid, mid),
                LC_to_DN=int(nz[np.ix_(dn, lc)].sum()), mid_to_DN=int(nz[np.ix_(dn, mid)].sum()), mid_to_LC=int(nz[np.ix_(lc, mid)].sum()),
                LC_to_LC=int(nz[np.ix_(lc, lc)].sum()), LC_to_mid=int(nz[np.ix_(mid, lc)].sum()), mid_to_mid=int(nz[np.ix_(mid, mid)].sum()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if not _allowed(a.out) or stage1_hashes()["mismatched"]:
        sys.exit("odmowa: --out poza flymind/$TMPDIR albo Stage 1 niezgodny")
    t0 = time.perf_counter()
    spec, idx, _ = network(0.2)
    gr, grep_ = layer_side_labels(spec, idx)
    W = spec.W_data
    li0 = lateralization(W, idx)
    lc = np.r_[idx["in_L"], idx["in_R"]]
    res = dict(groups=grep_, DATA=dict(structure=structure(W, idx), curve=curve(spec, W, idx)), SWS=[])
    first = None
    for s in (1401, 1402, 1403):
        sh = shuffle_within_side(spec, gr, s)
        p = properties(spec, sh, gr)
        first = first if first is not None else sh.W_data
        res["SWS"].append(dict(seed=s, all_properties=all(p[k] for k in KEYS), changed_frac=p["changed_frac"],
                               li_rel=round(lateralization(sh.W_data, idx) / li0, 4), structure=structure(sh.W_data, idx),
                               curve=curve(spec, sh.W_data, idx)))
    H = W.copy()
    H[np.ix_(lc, lc)] = first[np.ix_(lc, lc)]
    G = first.copy()
    G[np.ix_(lc, lc)] = W[np.ix_(lc, lc)]
    res["decomposition_seed1401"] = {"DATA+LCxLC_SWS": curve(spec, H, idx), "SWS+LCxLC_DATA": curve(spec, G, idx)}
    res.update(protocol=__doc__, wall_s=round(time.perf_counter() - t0, 1), stage1_post=stage1_hashes())
    path = os.path.join(a.out, f"v5v3_control_check_v2_{time.strftime('%Y%m%dT%H%M%S')}.json")
    with open(path, "x") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    fmt = lambda c: "  ".join(f"g{k}: {v['ipsi']:5.1f}±{v['ipsi_sem']:4.1f}/{v['contra']:4.1f}" for k, v in c.items())
    print("DATA                ", fmt(res["DATA"]["curve"]), res["DATA"]["structure"])
    for x in res["SWS"]:
        print(f"SWS {x['seed']} prop={x['all_properties']} LI={x['li_rel']}", fmt(x["curve"]), x["structure"])
    for k, v in res["decomposition_seed1401"].items():
        print(f"{k:20s}", fmt(v))
    print("zapisano:", path)
