"""T2 — bodźce na 721 kolumnach flyvis (PREREG_T2.md). Wartości 0 (ciemno) … 1 (jasno), tło 0,5 lub faktura 0/1.
stimuli(X) → dict nazwa → (klatki × 721, etykieta 1 = zbliżanie / 0 = nie, zbiór 'train' | 'test')."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../v1_camera_input"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../fly_eye"))
from bridge_loom import CENTERS, DEG_COL, DT, HOLD, PRE, R0, R1  # noqa: E402
from d_ideal import texture  # noqa: E402

TRAIN_SEEDS, TEST_SEEDS = (24104001, 24104002), (24104101, 24104102)


def radius(lv):
    a0, a1 = np.radians(R0 * DEG_COL), np.radians(R1 * DEG_COL)
    tc = np.arange(lv / np.tan(a0), lv / np.tan(a1), -DT)
    return np.degrees(np.arctan(lv / tc)) / DEG_COL


def pad(fr):
    return np.array([fr[0]] * int(PRE / DT) + list(fr) + [fr[-1]] * int(HOLD / DT), np.float32)


def disc(X, c, r):
    return np.hypot(X[:, 0] - c[0], X[:, 1] - c[1]) <= r


def moving_bg(X, seed, mv, n):
    f = texture(seed, X)
    out = []
    for k in range(n):
        x = k / max(n - 1, 1)
        if mv.startswith("tr"):
            a = np.radians(int(mv[2:]))
            P = X - np.array([np.cos(a), np.sin(a)]) * (-8 + 16 * x)
        elif mv.startswith("roll"):
            th = (1 if mv == "roll+" else -1) * 2.0 * x
            cs, sn = np.cos(-th), np.sin(-th)
            P = X @ np.array([[cs, sn], [-sn, cs]])
        else:                                                      # "still"
            P = X
        out.append(f(P))
    return out


def stimuli(X):
    S = {}
    r = radius(0.04)
    n = len(r)
    for pol in (0, 1):
        for ci in range(7):
            c = CENTERS[ci]
            S[f"loom_p{pol}_c{ci}"] = (pad([np.where(disc(X, c, rr), pol, 0.5) for rr in r]), 1, "train")
            S[f"recede_p{pol}_c{ci}"] = (pad([np.where(disc(X, c, rr), pol, 0.5) for rr in r[::-1]]), 0, "train")
        for ci in (0, 2, 5):
            for a in (0, 90, 180, 270):
                e = np.array([np.cos(np.radians(a)), np.sin(np.radians(a))])
                fr = [np.where(disc(X, CENTERS[ci] + e * (-8 + 16 * k / (n - 1)), 4.0), pol, 0.5) for k in range(n)]
                S[f"trans_p{pol}_c{ci}_{a}"] = (pad(fr), 0, "train")
        S[f"flash_p{pol}"] = (pad([np.full(len(X), 0.5)] * 5 + [np.full(len(X), float(pol))] * (n - 5)), 0, "train")
    for s in TRAIN_SEEDS:
        for mv in ("tr0", "tr90", "tr180", "tr270", "roll+", "roll-"):
            S[f"self_{mv}_s{s}"] = (pad(moving_bg(X, s, mv, n)), 0, "train")
    # --- test (nic z tego nie widzi trening)
    for lv in (0.02, 0.08):
        rl = radius(lv)
        for pol in (0, 1):
            for ci in (1, 3, 6):
                S[f"Tloom_lv{lv}_p{pol}_c{ci}"] = (pad([np.where(disc(X, CENTERS[ci], rr), pol, 0.5) for rr in rl]), 1, "test")
        rl = radius(lv)
        for ci in (1, 4):
            S[f"Trecede_lv{lv}_c{ci}"] = (pad([np.where(disc(X, CENTERS[ci], rr), 0, 0.5) for rr in rl[::-1]]), 0, "test")
    for s in TEST_SEEDS:
        for mv in ("tr0", "tr90", "tr180", "tr270", "roll+", "roll-"):
            S[f"Tself_{mv}_s{s}"] = (pad(moving_bg(X, s, mv, n)), 0, "test")
        for ci in (0, 4):                                          # ciemny dysk zbliża się na nieruchomej fakturze
            bg = moving_bg(X, s, "still", n)
            S[f"Tloomtex_c{ci}_s{s}"] = (pad([np.where(disc(X, CENTERS[ci], rr), 0, b) for rr, b in zip(r, bg)]), 1, "test")
        for mv in ("tr0", "tr90"):                                 # zbliżanie W CZASIE ruchu kamery
            bg = moving_bg(X, s, mv, n)
            S[f"Tloomself_{mv}_s{s}"] = (pad([np.where(disc(X, CENTERS[0], rr), 0, b) for rr, b in zip(r, bg)]), 1, "test")
        for a in (0, 90, 180, 270):                                # większy przesuwany dysk na fakturze
            e = np.array([np.cos(np.radians(a)), np.sin(np.radians(a))])
            bg = moving_bg(X, s, "still", n)
            fr = [np.where(disc(X, e * (-8 + 16 * k / (n - 1)), 6.0), 0, b) for k, b in enumerate(bg)]
            S[f"Ttrans6_{a}_s{s}"] = (pad(fr), 0, "test")
    return S


if __name__ == "__main__":
    from bridge_loom import flyxy
    u, v = np.meshgrid(np.arange(-15, 16), np.arange(-15, 16))
    m = np.abs(u + v) <= 15
    X = flyxy(u[m], v[m])
    S = stimuli(X)
    tr = [k for k, (_, _, sp) in S.items() if sp == "train"]
    te = [k for k, (_, _, sp) in S.items() if sp == "test"]
    print(len(X), "kolumn;", len(tr), "trening (", sum(S[k][1] for k in tr), "zbliżań),", len(te), "test (", sum(S[k][1] for k in te), "zbliżań)")
    print({k: S[k][0].shape for k in list(S)[:3]})
