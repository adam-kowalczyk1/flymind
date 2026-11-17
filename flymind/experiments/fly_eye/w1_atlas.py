"""W1 — atlas „co widzi każde piętro oka” (flyvis, Lappalainen i in. 2024) dla klatek kamery robota z W0. SYMULACJA.

Cel i kryteria: LOOP_TARGET_W1.md. Uruchamiać w envs/flyvis z FLYVIS_ROOT_DIR=data/flyvis:
  w1_atlas.py W0_DIR MODELS(np. 0-9) OUT_DIR
Optyka [MODEL, jawnie inżynierska]: kolumna flyvis (u, v) → kąt (x, y) = flyxy(u, v) × 5,1° (jak bridge_loom.py; oś x = poziom
kadru, y = pion) → kierunek kamery pinhole → jasność „Rh1” rozmyta Gaussem FWHM 5° → wartość /255. Kolumny poza polem kamery
(70° × 86°) dostają jedną stałą szarość = mediana jasności pierwszej klatki sceny (wariant b z planu 12 XI). Ta sama reguła
dla każdej kolumny i sceny. Krok 20 ms (jak trening flyvis). Modele deterministyczne, bez ziaren.
"""
import math
import os
import sys

import numpy as np
import torch
from flyvis import NetworkView
from scipy.ndimage import gaussian_filter, map_coordinates

DEG_COL, FWHM = 5.1, 5.0
SAVE = ["R1", "L1", "L2", "Mi1", "Tm3", "Tm1", "Tm2"] + [f"T4{s}" for s in "abcd"] + [f"T5{s}" for s in "abcd"]
SCENES = ["S1_spokoj", "S2_bok", "S2r_bok_wstecz", "S3_zblizanie", "S4_ramie"]


def flyxy(u, v):
    return np.c_[1.5 * v, -np.sqrt(3) * (u + v / 2)] / np.sqrt(3)       # jak bridge_loom.flyxy (jednostka = kolumna)


def hex_movie(lum, fovy, xy_deg):
    """lum [T × H × W] uint8 → [T × kolumny] w [0, 1]; maska kolumn w polu kamery."""
    T, H, W = lum.shape
    f = (H / 2) / math.tan(math.radians(fovy) / 2)
    tx, ty = np.tan(np.radians(xy_deg[:, 0])), np.tan(np.radians(xy_deg[:, 1]))
    col, row = W / 2 + f * tx, H / 2 - f * ty
    inside = (np.abs(xy_deg[:, 0]) < 89) & (np.abs(xy_deg[:, 1]) < 89) & (col >= 0) & (col <= W - 1) & (row >= 0) & (row <= H - 1)
    sig = (FWHM / 2.355) / (fovy / H)
    grey = float(np.median(lum[0])) / 255.0
    out = np.full((T, len(xy_deg)), grey, np.float32)
    for t in range(T):
        b = gaussian_filter(lum[t].astype(np.float32), sig, mode="nearest") / 255.0
        out[t, inside] = map_coordinates(b, np.c_[row[inside], col[inside]].T, order=1, mode="nearest")
    return out, inside


def main(w0, models, out):
    os.makedirs(out, exist_ok=True)
    lo, hi = map(int, models.split("-"))
    for k in range(lo, hi + 1):
        path = os.path.join(out, f"model_{k:03d}.npz")
        if os.path.exists(path):
            sys.exit(f"istnieje {path}")
        net = NetworkView(f"flow/0000/{k:03d}").init_network()
        nd = net.connectome.nodes
        t = np.array(nd.type[:]).astype(str); u = np.array(nd.u[:]); v = np.array(nd.v[:])
        r1 = t == "R1"
        xy = flyxy(u[r1], v[r1]) * DEG_COL
        idx = {s: np.where(t == s)[0] for s in SAVE}
        for s in SAVE:
            assert (u[idx[s]] == u[r1]).all() and (v[idx[s]] == v[r1]).all(), s
        types = sorted(set(t))
        centre = int(np.argmin(np.hypot(*xy.T)))
        cidx = np.array([np.where((t == s) & (u == u[r1][centre]) & (v == v[r1][centre]))[0][0] for s in types])
        res = dict(xy_deg=xy, types_all=np.array(types), centre=centre, dt=0.02)
        for sc in SCENES:
            W0 = np.load(os.path.join(w0, f"{sc}.npz"))
            mv, inside = hex_movie(W0["lum"], float(W0["fovy_deg"]), xy)
            with torch.no_grad():
                a = net.simulate(torch.tensor(mv)[None, :, None, :], 0.02).numpy()[0]
            res[f"{sc}__movie"] = mv
            res[f"{sc}__inside"] = inside
            res[f"{sc}__centre_all"] = a[:, cidx].astype(np.float32)          # klatki × 65 typów (kolumna środkowa)
            for s in SAVE:
                res[f"{sc}__{s}"] = a[:, idx[s]].astype(np.float32)            # klatki × 721
        np.savez_compressed(open(path, "xb"), **res)
        print("model", k, "ok", flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:4])
