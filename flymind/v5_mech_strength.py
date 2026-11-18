"""flymind/v5_mech_strength.py — Etap 5: czy efekt ablacji LC10a → AOTU wynika z BLOKU połączeń, czy z ilości usuniętego sygnału?
EKSPLORACJA (ziarna rozwojowe), protokół zapisany 2026-10-29 PRZED uruchomieniem. Bez nowych połączeń biologicznych.

Dane (DATA): wyjścia LC10a w sieci 94 310 synaps: do 51 neuronów AOTU* 58 458 (62 %, 3234 krawędzie), do LC10a 25 244 (27 %),
do innych pośrednich 10 608 (11 %). Kontrola „to samo poza AOTU” jest niewykonalna (poza AOTU tylko 35 852 synaps).
Warianty (wspólny dekoder DATA jak w V5 v2; dodatkowo raport własnego nachylenia kalibracji = skala sygnału):
  DATA
  CUT_LC10a_AOTU   (MODEL, ablacja jak V5 v2) krawędzie LC10a → AOTU* = 0
  RAND_CUT         (CONTROL) dla każdej strony osobno: losowa kolejność krawędzi wyjściowych LC10a tej strony (do
                   dowolnych celów), usuwane do osiągnięcia liczby synaps usuniętych przez CUT po tej stronie; ziarna 1501–1503
                   (pętla otwarta) i ziarno próby + 500 000 (pętla zamknięta)
  SCALE            (CONTROL, zmiana wag jako kontrola — nie biologia) wszystkie wyjścia LC10a × (1 − frakcja CUT po stronie)
Część A (pętla otwarta): krzywa DNa02 ipsi/kontra dla napędu 12 mV·g, g ∈ {0,50; 0,55; 0,60; 0,70; 1,00}, ziarna ALIF
  1001–1015; nachylenie kalibracji V4 v2 (loop_v2.calibrate_v4v2).
Część B (pętla zamknięta, MuJoCo): zadanie V5 v2 (trial_spec_v2), ziarna 1241–1290 (n = 50), warunki DATA, CUT, RAND_CUT,
  SCALE; miara główna: błąd końcowy; różnice w parach wobec DATA (d = wariant − DATA); średnia, bootstrap 95 % CI (ziarno 1601),
  test permutacyjny zmiany znaku (v5v3.perm_test), Holm na 3 porównaniach.
Pytania i interpretacja ustalone teraz:
  Q1 istnienie w danych — liczby powyżej (DATA).
  Q2 wpływ na dynamikę — krzywe i nachylenia w części A.
  Q3 wpływ na zachowanie — część B. Jeśli d(CUT) ≈ d(RAND_CUT) ≈ d(SCALE) (CI nakładające się) → efekt CUT tłumaczy ilość
  usuniętego sygnału, NIE specyfika bloku AOTU. Jeśli d(CUT) wyraźnie różni się od obu kontroli → specyfika bloku.
  Wynik jest eksploracyjny; nie potwierdza mechanizmu.
Uruchom: .venv/bin/python -I -B flymind/v5_mech_strength.py --part {A,B} --out flymind/results/v5_mech_strength
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
import loop as L  # noqa: E402
import loop_v2 as L2  # noqa: E402
from snn_interface import SNNSpec  # noqa: E402
from v5v2_topology import cut_lc_aotu  # noqa: E402
from v5v3 import boot_ci, holm, perm_test  # noqa: E402
from v5v3_control_check import curve  # noqa: E402
from visual_path import network  # noqa: E402


def cut_amount(spec, idx, cut):
    return {s: float(spec.W_data[:, idx[f"in_{s}"]].sum() - cut.W_data[:, idx[f"in_{s}"]].sum()) for s in "LR"}


def rand_cut(spec, idx, target, seed):
    rng = np.random.default_rng(seed)
    W = spec.W_data.copy()
    rep = {}
    for s in "LR":
        lcs = idx[f"in_{s}"]
        post, col = np.nonzero(W[:, lcs])
        order = rng.permutation(len(post))
        removed, k = 0.0, 0
        while removed < target[s] - 1e-9:
            i = order[k]
            removed += W[post[i], lcs[col[i]]]
            W[post[i], lcs[col[i]]] = 0.0
            k += 1
        rep[s] = dict(edges_removed=k, mv_removed=round(removed, 2), mv_target=round(target[s], 2))
    return SNNSpec(spec.bodies, spec.nt, spec.sign, W, spec.W_model.copy(), {}), rep


def scale(spec, idx, target):
    W = spec.W_data.copy()
    fr = {}
    for s in "LR":
        lcs = idx[f"in_{s}"]
        fr[s] = 1 - target[s] / W[:, lcs].sum()
        W[:, lcs] *= fr[s]
    return SNNSpec(spec.bodies, spec.nt, spec.sign, W, spec.W_model.copy(), {}), {s: round(v, 4) for s, v in fr.items()}


def part_a():
    spec, idx, _ = network(L.J0)
    cut = cut_lc_aotu(spec, idx)[0]
    tgt = cut_amount(spec, idx, cut)
    out = dict(target_mv_removed=tgt)
    nets = {"DATA": spec, "CUT_LC10a_AOTU": cut}
    for s in (1501, 1502, 1503):
        nets[f"RAND_CUT_{s}"], out[f"RAND_CUT_{s}_rep"] = rand_cut(spec, idx, tgt, s)
    nets["SCALE"], out["SCALE_factors"] = scale(spec, idx, tgt)
    for k, n in nets.items():
        out[k] = dict(curve=curve(spec, n.W_data, idx), calib=L2.calibrate_v4v2(n, idx))
        print(k, out[k]["calib"]["slope"], {a: v["ipsi"] for a, v in out[k]["curve"].items()}, flush=True)
    return out


def part_b(seeds):
    spec, idx, _ = network(L.J0)
    cut = cut_lc_aotu(spec, idx)[0]
    tgt = cut_amount(spec, idx, cut)
    sc = scale(spec, idx, tgt)[0]
    cal = dict(slope_snn=json.load(open(os.path.join(HERE, "results", "v4", "v4_partB_v2_20261028T214641.json")))["calib"]["slope_hz_per_rad"],
               slope_p=L.calibrate_p((96, 128)))
    runs = []
    for c in ("DATA", "CUT_LC10a_AOTU", "RAND_CUT", "SCALE"):
        for s in seeds:
            tr = {k: v for k, v in L2.trial_spec_v2(s).items() if k in ("seed", "az0_deg", "rho")}
            net = {"DATA": spec, "CUT_LC10a_AOTU": cut, "SCALE": sc}.get(c) or rand_cut(spec, idx, tgt, s + 500_000)[0]
            r = L.run_trial("snn", s, (net, idx), cal, tr=tr)
            r.update(L.metrics(r))
            runs.append(dict(cond=c, **tr, success=r["success"], final_abs_err=r["final_abs_err"]))
            print(f"{c:15s} {s}: |e| {r['final_abs_err']:6.2f}", flush=True)
    E = {(r["cond"], r["seed"]): r["final_abs_err"] for r in runs}
    comps, ps, out = ("CUT_LC10a_AOTU", "RAND_CUT", "SCALE"), [], dict(runs=runs, tests={})
    for c in comps:
        d = np.array([E[(c, s)] - E[("DATA", s)] for s in seeds])
        ps.append(perm_test(d, seed=1602))
        out["tests"][c] = dict(mean_d=round(float(d.mean()), 3), ci95=[round(x, 3) for x in boot_ci(d, 0.95, seed=1601)],
                               median_d=round(float(np.median(d)), 3), zeros=int((d == 0).sum()), p_perm=ps[-1],
                               success=int(sum(r["success"] for r in runs if r["cond"] == c)))
    for c, ph in zip(comps, holm(ps)):
        out["tests"][c]["p_holm"] = float(ph)
    out["DATA_success"] = int(sum(r["success"] for r in runs if r["cond"] == "DATA"))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--part", choices=("A", "B"), required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if not L._allowed(a.out) or L.stage1_hashes()["mismatched"]:
        sys.exit("odmowa: --out poza flymind/$TMPDIR albo Stage 1 niezgodny")
    t0 = time.perf_counter()
    res = part_a() if a.part == "A" else part_b(list(range(1241, 1291)))
    res.update(protocol=__doc__, wall_s=round(time.perf_counter() - t0, 1), stage1_post=L.stage1_hashes())
    path = os.path.join(a.out, f"v5_mech_strength_{a.part}_{time.strftime('%Y%m%dT%H%M%S')}.json")
    with open(path, "x") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: v for k, v in res.items() if k not in ("protocol", "runs") and not k.startswith(("DATA", "CUT", "RAND", "SCALE"))} |
                     ({"tests": res["tests"], "DATA_success": res["DATA_success"]} if a.part == "B" else {}), indent=1, default=str))
    print("zapisano:", path)
