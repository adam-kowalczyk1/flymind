"""Krok 2, przed (b): koszt czasu jednego taktu sterowania (10 ms symulacji) dla sieci T1 L + T2 L + droga wzrokowa,
przy dt 1 ms (10 kroków ALIF) i dt 0,1 ms (100 kroków). Tylko pomiar; nic poza plikiem wyniku nie jest zapisywane.

Sieć (podgraf indukowany MaleCNS, jak vision_manipulation.union_spec, plus T1 L):
  T2 L = leg_circuit.select("T2","L");  T1 L = leg_circuit.select("T1","L") ∪ MN podklasy "fl" strony L (MN biodra T1
  wychodzą innymi nerwami — leg_data_v1.json);  wzrok = visual_path.select(). Ciała wspólne liczone raz.
Wejścia jak w VisJaw: dotyk 40 mV na połowę szczecinek T2 L, wzrok 12 mV·g (g = 0,5/0,3) na LC10a, szum σ 2 mV tylko w drodze
wzrokowej (generator co krok), Glu −1, J0 0,2. Ziarno szumu: 20 000 010 (SEED_REGISTRY.md).
  .venv/bin/python -I -B flymind/experiments/step2_whole_arm/tick_cost.py OUT.json
"""
import json
import os
import platform
import sys
import time

import numpy as np
import pandas as pd

FLY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, FLY)
import visual_path  # noqa: E402
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402
from connectome import load_edges  # noqa: E402
from leg_circuit import select  # noqa: E402
from snn_interface import DEFAULT_SIGN, NT_COLS, ModelParams, assign_nt, build  # noqa: E402

SEED = 20_000_010
TICKS, WARM = 300, 20


def union(glu=-1.0, J0=0.2):
    a = pd.read_feather(visual_path.ANN, columns=["bodyId", "superclass", "subclass", "somaSide"])
    t2, g2, _ = select("T2", "L")
    t1, g1, _ = select("T1", "L")
    t1mn = sorted(a.bodyId[(a.superclass == "vnc_motor") & (a.subclass == "fl") & (a.somaSide == "L")].astype(int))
    vb, vg, _ = visual_path.select()
    bodies = list(dict.fromkeys([int(b) for b in list(t2) + list(t1) + t1mn + list(vb)]))
    edges, erep = load_edges(visual_path.WEIGHTS, bodies=bodies)
    nts = pd.read_feather(visual_path.NTS)
    tab = nts.set_index("body").reindex(bodies)[list(NT_COLS)]
    ov = {b: ("unknown", "brak NT; znak 0") for b, r in tab.iterrows()
          if not any(isinstance(x, str) and x != "unclear" for x in r)}
    signs = {**DEFAULT_SIGN, "glutamate": glu}
    signs.update({n: 0.0 for n in set(assign_nt(bodies, nts, ov).nt) - set(signs)})
    spec = build(edges, bodies, nts, ModelParams(J0=J0, sign_map=signs), nt_overrides=ov)
    pos = {b: i for i, b in enumerate(bodies)}
    br = g2["sensory"]["mechanosensory bristle"]
    idx = dict(touch=[pos[b] for b in br[: len(br) // 2]] + [pos[b] for b in br[len(br) // 2:]],
               in_L=[pos[b] for b in vg["in_L"]], in_R=[pos[b] for b in vg["in_R"]],
               visual=[pos[b] for b in vb])
    sizes = dict(N=len(bodies), T2L=len(t2), T1L=len(set(t1) | set(t1mn)), visual=len(vb),
                 shared_T1_T2=len(set(t2) & (set(t1) | set(t1mn))), edges=int(erep["loaded"]["edges"]),
                 nnz_W=int(np.count_nonzero(spec.W)))
    return spec, idx, sizes


def measure(spec, idx, dt, noise):
    p = ALIFParams(dt=dt)
    net = SparseALIF(spec, p, None)
    N, steps = spec.W.shape[0], int(round(10 / dt))
    X = np.zeros(N)
    X[idx["touch"]] = 40.0
    X[idx["in_L"]], X[idx["in_R"]] = 12 * 0.5, 12 * 0.3
    nz = np.zeros(N)
    nz[idx["visual"]] = 2.0 if noise else 0.0
    rng = np.random.default_rng(SEED)
    ts, n_spk = [], 0
    for k in range(TICKS + WARM):
        t0 = time.perf_counter()
        if noise:
            s = np.vstack([net.run(X + nz * rng.standard_normal(N), 1) for _ in range(steps)])
        else:
            s = net.run(X, steps)
        dtw = time.perf_counter() - t0
        if k >= WARM:
            ts.append(dtw * 1e3)
            n_spk += int(s.sum())
    ts = np.array(ts)
    return dict(dt_ms=dt, steps_per_tick=steps, noise=noise, median_ms=round(float(np.median(ts)), 3),
                p95_ms=round(float(np.percentile(ts, 95)), 3), max_ms=round(float(ts.max()), 3),
                realtime_factor=round(10.0 / float(np.median(ts)), 2), mean_rate_hz=round(n_spk / TICKS / N / 0.01, 2))


def main(out):
    t0 = time.perf_counter()
    spec, idx, sizes = union()
    build_s = time.perf_counter() - t0
    res = dict(sizes=sizes, build_s=round(build_s, 1), seed=SEED, ticks=TICKS, warmup=WARM,
               machine=dict(platform=platform.platform(), processor=platform.processor(), python=sys.version.split()[0]),
               runs=[measure(spec, idx, dt, nz) for dt in (1.0, 0.1) for nz in (False, True)])
    with open(out, "x") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
