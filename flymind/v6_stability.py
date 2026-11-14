"""flymind/v6_stability.py — Etap 6: czy różnica DATA vs SHUF_WITHIN_SIDE v2 (przesunięcie progu odpowiedzi DNa02) zależy od
arbitralnych założeń ALIF? EKSPLORACJA (pętla otwarta, ziarna dev), protokół zapisany 2026-10-29 PRZED uruchomieniem.
Nie służy do wyboru parametrów V5 v3 (te są ustalone: J0 0,2, noise 2, b_a 0,5, delay 1,8 ms).

Siatka (MODEL): J0 ∈ {0,15; 0,20; 0,25} × noise ∈ {1; 2; 3} mV × b_a ∈ {0; 0,5}; dodatkowo delay_ms ∈ {1,0; 3,0} przy wartościach
  domyślnych. Sieci: DATA i SWS v2 (ziarno 1401, ta sama instancja dla wszystkich ustawień, przebudowana dla każdego J0).
Miary (ziarna ALIF 1001–1010, obie strony): próg g30 = najmniejsze g z siatki 0,40…1,00 co 0,025, przy którym średnia DNa02
  ipsi ≥ 30 Hz (interpolacja liniowa między punktami siatki); Δg30 = g30(SWS) − g30(DATA) (> 0 ⇔ DATA czulsza); odpowiedź
  kontralateralna przy g = 1; spontaniczna częstość sieci bez bodźca (300 ms); odsetek nasyconych neuronów (≥ 0,9 r_max) przy g = 1.
Interpretacja ustalona teraz: znak Δg30 stały w ≥ 90 % ustawień → kierunek efektu odporny na te założenia; zmiana znaku →
  efekt zależny od parametrów (ograniczenie). Wielkość Δg30 raportowana, nie interpretowana jako biologiczna.
Uruchom: .venv/bin/python -I -B flymind/v6_stability.py --out flymind/results/v6_stability
"""
import argparse
import itertools
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
from side_shuffle import layer_side_labels, shuffle_within_side  # noqa: E402
from snn_interface import SNNSpec  # noqa: E402
from visual_path import network  # noqa: E402

AMPS = np.round(np.arange(0.40, 1.0001, 0.025), 3)
SEEDS = tuple(range(1001, 1011))


def measure(spec, idx, P):
    ipsi = []
    contra1 = sat1 = None
    for amp in AMPS:
        v = []
        for s, o in (("L", "R"), ("R", "L")):
            I = np.zeros((300, len(spec.bodies)))
            I[:, idx[f"in_{s}"]] = 12.0 * amp
            for seed in SEEDS:
                r = rates(ALIF(spec, P, seed).run(I, 300), P.dt)
                v.append((r[idx[f"DNa02_{s}"]].mean(), r[idx[f"DNa02_{o}"]].mean(), (r >= 0.9 * P.r_max).mean()))
        v = np.array(v)
        ipsi.append(v[:, 0].mean())
        if amp == 1.0:
            contra1, sat1 = float(v[:, 1].mean()), float(v[:, 2].mean())
    ipsi = np.array(ipsi)
    k = np.flatnonzero(ipsi >= 30)
    if not len(k):
        g30 = None
    elif k[0] == 0:
        g30 = float(AMPS[0])
    else:
        i = k[0]
        g30 = float(AMPS[i - 1] + (30 - ipsi[i - 1]) / (ipsi[i] - ipsi[i - 1]) * (AMPS[i] - AMPS[i - 1]))
    spont = float(np.mean([rates(ALIF(spec, P, s).run(np.zeros((300, len(spec.bodies))), 300), P.dt).mean() for s in SEEDS[:3]]))
    return dict(g30=g30, contra_g1=contra1, sat_g1=sat1, spont_hz=spont, ipsi_curve=np.round(ipsi, 1).tolist())


if __name__ == "__main__":
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if not _allowed(a.out) or stage1_hashes()["mismatched"]:
        sys.exit("odmowa")
    t0 = time.perf_counter()
    grid = [dict(J0=j, noise=n, b_a=b, delay_ms=1.8) for j, n, b in itertools.product((0.15, 0.20, 0.25), (1.0, 2.0, 3.0), (0.0, 0.5))]
    grid += [dict(J0=0.20, noise=2.0, b_a=0.5, delay_ms=d) for d in (1.0, 3.0)]
    rows = []
    for g in grid:
        spec, idx, _ = network(g["J0"])
        gr, _ = layer_side_labels(spec, idx)
        sws = shuffle_within_side(spec, gr, 1401)
        P = ALIFParams(noise=g["noise"], b_a=g["b_a"], delay_ms=g["delay_ms"])
        md, ms = measure(spec, idx, P), measure(SNNSpec(spec.bodies, spec.nt, spec.sign, sws.W_data, spec.W_model, {}), idx, P)
        dg = None if md["g30"] is None or ms["g30"] is None else round(ms["g30"] - md["g30"], 4)
        rows.append(dict(**g, DATA=md, SWS=ms, delta_g30=dg))
        print(g, "g30 DATA", md["g30"] and round(md["g30"], 3), "SWS", ms["g30"] and round(ms["g30"], 3), "Δ", dg,
              "| kontra", md["contra_g1"], ms["contra_g1"], "| spont", round(md["spont_hz"], 2), round(ms["spont_hz"], 2),
              "| sat", round(md["sat_g1"], 3), flush=True)
    d = [r["delta_g30"] for r in rows if r["delta_g30"] is not None]
    summ = dict(n_settings=len(rows), n_defined=len(d), frac_positive=round(float(np.mean(np.array(d) > 0)), 3) if d else None,
                delta_range=[min(d), max(d)] if d else None)
    res = dict(rows=rows, summary=summ, protocol=__doc__, wall_s=round(time.perf_counter() - t0, 1), stage1_post=stage1_hashes())
    path = os.path.join(a.out, f"v6_stability_{time.strftime('%Y%m%dT%H%M%S')}.json")
    with open(path, "x") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    print(summ, "\nzapisano:", path)
