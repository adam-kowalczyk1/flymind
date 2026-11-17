"""W2 — analiza PO FAKCIE (opisowa, bez wpływu na werdykt; napisana po obejrzeniu w2_result.json).
envs/flyvis: w2_posthoc.py MAP.npz W2_DIR
(1) układ 2×2: ciemny/jasny × zbliżanie/oddalanie — czy LC4 z modelu reaguje na „jaśnieje”, czy na „zbliża się”;
(2) wkład typów wejściowych do LC4 (ciemny dysk w środku oka) w modelach 000 i 004."""
import glob
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "v1_camera_input"))
import w2_run as W  # noqa: E402
from bridge_loom import DT, PRE, flyxy, movies  # noqa: E402

M = np.load(sys.argv[1]); D = {}
for f in sorted(glob.glob(os.path.join(sys.argv[2], "discs_*.npz"))):
    D.update(np.load(f))
print("model  c.zbliż  c.oddal  j.zbliż  j.oddal | jaśnieje/ciemnieje  zbliżanie/oddalanie   (średnia po 55 LC4 i 7 środkach, układ prawdziwy)")
rb, ra = [], []
for m in range(10):
    g = lambda pol, name: np.mean([D[f"m{m}_p{pol}_{name}_{c}"][0].mean() for c in range(7)])  # noqa: E731
    dl, dr, bl, br = g(0, "loom"), g(0, "recede"), g(1, "loom"), g(1, "recede")
    rb.append((dr + bl) / (dl + br)); ra.append((dl + bl) / (dr + br))
    print(f"{m:03d}  {dl:8.1f} {dr:8.1f} {bl:8.1f} {br:8.1f} | {rb[-1]:8.2f} {ra[-1]:8.2f}")
print(f"mediana: jaśnieje/ciemnieje {np.median(rb):.2f} (> 1 w {sum(x > 1 for x in rb)}/10 modeli); zbliżanie/oddalanie {np.median(ra):.2f}")
for k in (0, 4):
    net, t, u, v, r1, col = W.load(k)
    types, mats = W.readout_mats(M, col); idx = W.type_idx(t, u, v, r1, types)
    mv = movies(flyxy(u[r1], v[r1]), 0); n0 = int(PRE / DT)
    m0 = mats[0].toarray().reshape(len(M["post"]), len(types), 721); out = {}
    for name in ("loom_0", "recede_0"):
        with torch.no_grad():
            a = net.simulate(torch.tensor(mv[name], dtype=torch.float32)[None, :, None, :], DT).numpy()[0]
        rel = np.clip(a[:, idx][n0:] - a[:, idx][n0 - 1][None], 0, None)
        out[name] = np.einsum("ctk,ftk->ft", m0, rel).max(0) / len(M["post"])
    print(f"model {k:03d}: szczyt wkładu typu do LC4 (ciemny dysk, środek) — typ, zbliżanie, oddalanie")
    for i in np.argsort(-(out["loom_0"] + out["recede_0"]))[:6]:
        print(f"   {types[i]:6s} {out['loom_0'][i]:8.1f} {out['recede_0'][i]:8.1f}")
