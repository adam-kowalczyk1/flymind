"""flymind/v5_ablation.py — skąd przewaga topologii z danych w V5 v2? EKSPLORACJA (ziarna rozwojowe), protokół zapisany
2026-10-29 PRZED uruchomieniem. Nic tu nie jest potwierdzeniem (pula 2001–2100 wyczerpana).

Mapa ścieżek (obliczona przed protokołem): wpływ 2-skokowy LC10a → pośrednie → DNa02 idzie prawie wyłącznie przez AOTU —
pobudzenie ipsilateralne przez 49 pobudzających AOTU (+63/+66 ×10³), hamowanie kontralateralne przez 2 × AOTU019 (GABA,
ground truth; −70/−82 ×10³); LAL +11/+15 ×10³; LLPC1 (43 neurony) ≈ 0. Tasowanie equal_weight niszczy pobudzenie
ipsilateralne (75 ×10³ → −1…12 ×10³), a częściowo zachowuje hamowanie kontralateralne (wagi hamujące są rzadkie).

Warianty (sieć z danych J0 0,2; ablacja = wyzerowanie wierszy i kolumn neuronów w W_data; dekoder sieci z danych):
  data, abl_AOTU_exc (pobudzające AOTU*), abl_AOTU019 (2 neurony), abl_LAL (LAL*), abl_LLPC1, abl_other (reszta pośrednich),
  no_mid_mid (bez krawędzi pośrednie → pośrednie), no_LC_LC (bez krawędzi LC10a → LC10a),
  eqshuffle (visual_path.shuffle equal_weight, ziarna 1301–1303), toy_relay (loop_v2.toy_relay, własna kalibracja).
Część A (pętla otwarta, spot_clip, enkoder V4 v2, ziarna 1001–1003): indeks skrętu S(r) = [L−P(az +20°) − L−P(az −20°)]/2
  [Hz] dla promienia plamki r ∈ {9, 6, 5, 4} px (mniejsza plamka = dalsza piłeczka = słabszy napęd).
Część B (pętla zamknięta, ziarna 1201–1220): cele na granicy czułości — |az0| ~ U[15°, 30°] (znak losowy),
  ρ ~ U[0,24; 0,30]; sukces jak V5 (|e| < 5° w 2,5–3,0 s). Warianty: data, eqshuffle (ziarno + 100 000),
  abl_AOTU_exc, abl_AOTU019, abl_LAL, abl_LLPC1, no_mid_mid, toy_relay.
Przewidywania (zapisane teraz): abl_AOTU_exc obniża S(5) o > 50 % i zachowanie do poziomu eqshuffle lub niżej;
  abl_AOTU019 — umiarkowany spadek (traci się push-pull); abl_LLPC1 i abl_other — bez istotnej zmiany;
  no_mid_mid — mała zmiana. Liczebności małe (n = 20) — wynik wskazuje kierunek dalszych badań, nie rozstrzyga.
Uruchom: .venv/bin/python -I -B flymind/v5_ablation.py --part {A,B} --out KATALOG
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np
import pandas as pd

if __name__ == "__main__" and not sys.flags.dont_write_bytecode:
    sys.exit("uruchom z python -B")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import loop as L  # noqa: E402
import loop_v2 as L2  # noqa: E402
import v4_open_loop as V4  # noqa: E402
from sensory import spot_clip  # noqa: E402
from snn_interface import SNNSpec  # noqa: E402
from visual_path import ANN, network, shuffle  # noqa: E402

RADII = (9, 6, 5, 4)


def variants(spec, idx):
    t = pd.read_feather(ANN, columns=["bodyId", "type"]).set_index("bodyId").type.reindex(spec.bodies).astype(str).to_numpy()
    mid = idx["mid"]
    lc = np.r_[idx["in_L"], idx["in_R"]]
    fam = lambda f: mid[np.array([f(x) for x in t[mid]])]
    groups = dict(abl_AOTU_exc=fam(lambda x: x.startswith("AOTU") and x != "AOTU019"), abl_AOTU019=fam(lambda x: x == "AOTU019"),
                  abl_LAL=fam(lambda x: x.startswith("LAL")), abl_LLPC1=fam(lambda x: x == "LLPC1"))
    groups["abl_other"] = np.setdiff1d(mid, np.concatenate(list(groups.values())))

    def ablate(cols):
        W = spec.W_data.copy()
        W[cols, :] = 0
        W[:, cols] = 0
        return SNNSpec(spec.bodies, spec.nt, spec.sign, W, spec.W_model.copy(), {})

    def cut(rows, cols):
        W = spec.W_data.copy()
        W[np.ix_(rows, cols)] = 0
        return SNNSpec(spec.bodies, spec.nt, spec.sign, W, spec.W_model.copy(), {})

    out = {"data": spec, **{k: ablate(v) for k, v in groups.items()}, "no_mid_mid": cut(mid, mid), "no_LC_LC": cut(lc, lc)}
    return out, {k: int(len(v)) for k, v in groups.items()}


def steer_index(spec, idx, r, seeds=V4.CAL_SEEDS):
    img = lambda a: spot_clip(np.radians([a]), [0.0], V4.SHAPE, V4.FOVY, r, V4.FG, V4.BG).images[0]
    d = [(V4.static_diff(spec, idx, s, img(20)) - V4.static_diff(spec, idx, s, img(-20))) / 2 for s in seeds]
    return round(float(np.mean(d)), 1)


def part_a():
    V4.V.update(V4.VERSION[2])
    spec, idx, _ = network(L.J0)
    var, sizes = variants(spec, idx)
    for s in (1301, 1302, 1303):
        var[f"eqshuffle_{s}"] = shuffle(spec, s, equal_weight=True)
    toy, tidx, _ = L2.toy_relay(spec, idx)
    res = {k: {r: steer_index(v, idx, r) for r in RADII} for k, v in var.items()}
    res["toy_relay"] = {r: steer_index(toy, tidx, r) for r in RADII}
    return dict(steer_index_hz=res, group_sizes=sizes)


def part_b():
    spec, idx, _ = network(L.J0)
    var, sizes = variants(spec, idx)
    toy, tidx, _ = L2.toy_relay(spec, idx)
    cal = dict(slope_snn=json.load(open(os.path.join(HERE, "results", "v4", "v4_partB_v2_20261028T214641.json")))["calib"]["slope_hz_per_rad"],
               slope_p=L.calibrate_p((96, 128)))
    toy_slope = L2.calibrate_v4v2(toy, tidx)["slope"]
    runs = []
    for c in ("data", "eqshuffle", "abl_AOTU_exc", "abl_AOTU019", "abl_LAL", "abl_LLPC1", "no_mid_mid", "toy_relay"):
        for s in range(1201, 1221):
            rng = np.random.default_rng(s)
            tr = dict(seed=s, az0_deg=float(rng.choice([-1, 1]) * rng.uniform(15, 30)), rho=float(rng.uniform(0.24, 0.30)))
            base, kw = (var.get(c), idx), dict(tr=tr)
            if c == "eqshuffle":
                base = (shuffle(spec, s + 100_000, equal_weight=True), idx)
            elif c == "toy_relay":
                base, kw["slope"] = (toy, tidx), toy_slope
            r = L.run_trial("snn", s, base, cal, **kw)
            r.update(L.metrics(r))
            runs.append(dict(cond=c, seed=s, az0=tr["az0_deg"], rho=tr["rho"], success=r["success"],
                             final_abs_err=r["final_abs_err"]))
            print(f"{c:13s} {s}: az0 {tr['az0_deg']:+5.1f} ρ {tr['rho']:.3f} → |e| {r['final_abs_err']:5.2f} {r['success']}", flush=True)
    summ = {c: f"{sum(x['success'] for x in runs if x['cond'] == c)}/20" for c in dict.fromkeys(x["cond"] for x in runs)}
    return dict(summary=summ, runs=runs, toy_slope=toy_slope, group_sizes=sizes)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--part", choices=("A", "B"), required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if not L._allowed(a.out):
        sys.exit("--out poza flymind/ i $TMPDIR")
    pre = L.stage1_hashes()
    if pre["mismatched"]:
        sys.exit(f"Stage 1 niezgodny: {pre['mismatched']}")
    t0 = time.perf_counter()
    res = part_a() if a.part == "A" else part_b()
    res.update(protocol=__doc__, wall_s=time.perf_counter() - t0, stage1_post=L.stage1_hashes())
    path = os.path.join(a.out, f"v5_ablation_{a.part}_{time.strftime('%Y%m%dT%H%M%S')}.json")
    with open(path, "x") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: v for k, v in res.items() if k not in ("protocol", "runs")}, indent=1, default=str))
    print("zapisano:", path)
