"""„Oko jak u muchy” (wariant b, 20 XI) — plan i kryteria: PREREG_OKO_EMD.md (spisane przed uruchomieniem, df85e57).
Kod (nie neurony z konektomu), ale każdy etap naśladuje znany typ komórki oka muchy:
  bloki 4×4 = ommatidia → log + adaptacja (R1–R6, L1/L2) → ON/OFF (T4/T5) → detektor ruchu Hassensteina–Reichardta
  w 4 kierunkach → LPLC2: 4 ramiona „na zewnątrz” naraz (średnia geometryczna), ruch do środka hamuje (LPi).
Wyjście = napęd [mV] komórek zbliżania lewej/prawej strony mózgu (te same co dziś w live_avoid, avoid.eye_idx).
  oko_mucha.py --test     test z planu (10 scen syntetycznych × 10 ziaren) → flymind/results/oko_emd_20261120/
  oko_mucha.py --calib    wylicza OUT_FULL ze sceny kalibracyjnej (ziarno 24 100 900)
  oko_mucha.py --check    szybki sprawdzian znaków (bez sprzętu)"""
import json
import os
import sys
import time

import numpy as np
from scipy import ndimage

W_PX, H_PX, BLK = 160, 100, 4                 # kadr jak w live_avoid; bloki 4×4 → siatka 40×25 „ommatidiów”
GW, GH = W_PX // BLK, H_PX // BLK
TAU_HP, TAU_LP = 0.25, 0.05                   # adaptacja fotoreceptora/laminy, opóźnienie w detektorze ruchu [s]
MV, L_FULL = 40.0, 2.0                        # jak avoid.py: 40 mV = pełny napęd, osiągany przy L = 2 rad/s
OUT_FULL = 0.0537                             # z --calib 20 XI (0,05368; scena kalibracyjna, ziarno 24 100 900, przed testem)
FOV_H, FPS, SIGMA = 100.0, 80, 3.0            # scen syntetycznych: kąt widzenia (niezmierzony), kl./s (zmierzone), szum
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../results/oko_emd_20261120")


def _units():
    """32 jednostki LPLC2: środki x = 6,10,…,34, y = 6,10,14,18, promień 10 pól. Zwraca wagi ramion (prawe, lewe, dolne,
    górne) na sygnałach H (między polami w poziomie, 25×39) i V (w pionie, 24×40) oraz stronę jednostki (True = lewa)."""
    hy, hx = np.mgrid[:GH, :GW - 1] + np.array([0.0, 0.5])[:, None, None]
    vy, vx = np.mgrid[:GH - 1, :GW] + np.array([0.5, 0.0])[:, None, None]
    arms, left = [[], [], [], []], []
    for cy in range(6, 19, 4):
        for cx in range(6, 35, 4):
            inh, inv = np.hypot(hx - cx, hy - cy) <= 10, np.hypot(vx - cx, vy - cy) <= 10
            for k, m in enumerate((inh & (hx > cx), inh & (hx < cx), inv & (vy > cy), inv & (vy < cy))):
                arms[k].append(m.ravel() / m.sum())
            left.append(cx < GW / 2)
    return [np.array(a) for a in arms], np.array(left)


ARMS, LEFT = _units()


def hr(s, d, ax):
    """Detektor Reichardta między sąsiadami wzdłuż osi ax: opóźnione A × B − A × opóźnione B; > 0 = ruch od A do B."""
    a, b = (s[:, :-1], s[:, 1:]) if ax else (s[:-1], s[1:])
    da, db = (d[:, :-1], d[:, 1:]) if ax else (d[:-1], d[1:])
    return da * b - a * db


class FlyEye:
    """Interfejs jak live_avoid.Eye: see(f, dt, t) → L (tu: „równoważne” L = L_FULL · wyjście / OUT_FULL), do tego
    .loom = napęd stron {"L","R"} [mV], .m = maska zmian (pokazywana na stronie), .th = 0 (oko nie mierzy kąta plamy)."""
    def __init__(self, flip=False, out_full=None):
        self.flip, self.out_full = flip, out_full or OUT_FULL
        self.x = self.don = self.doff = self.t_last = None
        self.L, self.th, self.sa, self.out = 0.0, 0.0, 0.0, (0.0, 0.0)
        self.loom = {"L": 0.0, "R": 0.0}

    def see(self, f, dt, t):
        x = np.log(f.reshape(GH, BLK, GW, BLK).mean((1, 3)) + 8.0)
        if self.x is None:
            self.x, self.don, self.doff, self.t_last = x, np.zeros_like(x), np.zeros_like(x), t
            return 0.0
        dt, self.t_last = max(t - self.t_last, 1e-3), t
        self.x += (1 - np.exp(-dt / TAU_HP)) * (x - self.x)
        hp = x - self.x
        on, off = np.maximum(hp, 0), np.maximum(-hp, 0)
        H = hr(on, self.don, 1) + hr(off, self.doff, 1)          # > 0 = w prawo
        V = hr(on, self.don, 0) + hr(off, self.doff, 0)          # > 0 = w dół
        a = 1 - np.exp(-dt / TAU_LP)
        self.don += a * (on - self.don)
        self.doff += a * (off - self.doff)
        h, v = H.ravel(), V.ravel()
        arm = np.maximum(0, np.stack([ARMS[0] @ h, -(ARMS[1] @ h), ARMS[2] @ v, -(ARMS[3] @ v)]))
        lplc2 = np.prod(arm, axis=0) ** 0.25
        oL, oR = lplc2[LEFT].max(), lplc2[~LEFT].max()
        self.out = (oR, oL) if self.flip else (oL, oR)
        self.m = np.kron(np.abs(hp) > 0.1, np.ones((BLK, BLK), bool))
        if self.out_full:
            self.loom = {s: MV * min(1.0, o / self.out_full) for s, o in zip("LR", self.out)}
            self.L = L_FULL * max(self.out) / self.out_full
            self.sa = float((self.out[0] - self.out[1]) / (sum(self.out) + 1e-12))
        return self.L


# ---------------------------------------------------------------- sceny syntetyczne (plan, sekcja „Sceny”)
def scene(kind, seed, T=3.0):
    """Lista (t, klatka uint8 100×160). Render 2× i uśrednienie 2×2 (gładki ruch), potem szum σ = SIGMA na kadrze oka."""
    rng = np.random.default_rng(seed)
    S, pd = 2, 2 * W_PX / FOV_H                                  # piksele renderu na stopień
    tex = ndimage.gaussian_filter(rng.standard_normal((3 * H_PX * S, 3 * W_PX * S)), 3 * S)
    tex = 140 + 25 * tex / tex.std()
    yy, xx = np.mgrid[:H_PX * S, :W_PX * S].astype(float)
    cy0, cx0 = H_PX * S / 2, W_PX * S / 2
    loom_th = lambda t: np.degrees(2 * np.arctan(0.1 / max(2.0 - t, 0.1 / np.tan(np.radians(40)))))  # noqa: E731  ≤ 80°
    out = []
    for k in range(int(T * FPS)):
        t = k / FPS
        u = max(0.0, t - 0.5)                                     # ruch / zdarzenie od t = 0,5 s
        dx = dy = rot = 0.0
        if kind == "pan_h":
            dx = 50 * u * pd
        elif kind == "pan_v":
            dy = 50 * u * pd
        elif kind == "roll":
            rot = np.radians(90 * u)
        c, s_ = np.cos(rot), np.sin(rot)
        X, Y = xx - cx0, yy - cy0
        img = ndimage.map_coordinates(tex, [c * Y + s_ * X + 1.5 * H_PX * S + dy, -s_ * Y + c * X + 1.5 * W_PX * S + dx], order=1)
        disc = None                                               # (środek x w ułamku szerokości, średnica [°])
        if kind.startswith("loom") and t >= 0.5:
            disc = ({"loom": 0.5, "loom_L": 0.25, "loom_R": 0.75}[kind], loom_th(t))
        elif kind == "recede" and 3.0 - t - 1 / FPS >= 0.5:      # scena 1 odwrócona w czasie
            disc = (0.5, loom_th(3.0 - t - 1 / FPS))
        elif kind == "side" and t >= 0.5:
            disc = ((-15 + 100 * u) / FOV_H, 30.0)
        elif kind == "static" and t >= 0.5:
            disc = (0.5, 40.0)
        if disc:
            img[np.hypot(xx - disc[0] * W_PX * S, yy - cy0) <= disc[1] / 2 * pd] = 40.0
        if kind == "light" and t >= 1.0:
            img = img * 1.5
        f = img.reshape(H_PX, S, W_PX, S).mean((1, 3)) + SIGMA * rng.standard_normal((H_PX, W_PX))
        out.append((t, np.clip(np.round(f), 0, 255).astype(np.uint8)))
    return out


KINDS = ["loom", "loom_L", "loom_R", "side", "pan_h", "pan_v", "roll", "recede", "static", "light"]


def run(kind, seed, eye):
    o = []
    for t, f in scene(kind, seed):
        eye.see(f, 1 / FPS, t)
        o.append((t, *getattr(eye, "out", (0.0, 0.0)), eye.L))
    return np.array(o)                                            # kolumny: t, out_L, out_R, L (stare oko: tylko L ma sens)


def calib():
    o = run("loom", 24100900, FlyEye(out_full=1.0))
    t37 = 2.0 - 0.1 / np.tan(np.radians(36.87 / 2))               # θ = 36,87° ⇔ L = 2 rad/s (t ≈ 1,70 s)
    sel = np.abs(o[:, 0] - t37) <= 2.5 / FPS
    return float(o[sel, 1:3].max(axis=1).mean())


def test():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from live_avoid import Eye
    t0, R = time.time(), {}
    for seed in range(24100001, 24100011):
        r = {k: run(k, seed, FlyEye()) for k in KINDS}
        old = {k: run(k, seed, Eye(FOV_H))[:, 3] for k in KINDS}
        pk = {k: float(r[k][:, 1:3].max()) for k in KINDS}
        side = {}
        for k, i in (("loom_L", 1), ("loom_R", 2)):
            o, j = r[k], int(r[k][:, 1:3].max(axis=1).argmax())
            big = o[:, 1:3].max(axis=1) > 0.5 * o[:, 1:3].max()
            side[k] = bool(o[j, i] > o[j, 3 - i] and o[big, i].mean() > o[big, 3 - i].mean())
        st = r["static"]
        late = float(st[st[:, 0] >= 2.0, 1:3].max(axis=1).mean())
        lo = r["loom"]
        j50 = int(np.argmax(lo[:, 1:3].max(axis=1) > 0.5 * pk["loom"]))
        R[seed] = dict(peak=pk, ratio={k: pk[k] / pk["loom"] for k in KINDS[3:]},
                       K1=all(pk[k] <= 0.25 * pk["loom"] for k in KINDS[3:]), K2=side["loom_L"] and side["loom_R"],
                       K3=late <= 0.05 * pk["loom"], static_late=late / pk["loom"],
                       fire_theta=float(np.degrees(2 * np.arctan(0.1 / max(2.0 - lo[j50, 0], 1e-3)))),
                       old_peak_L={k: float(old[k].max()) for k in KINDS})
        print(seed, "K1", R[seed]["K1"], "K2", R[seed]["K2"], "K3", R[seed]["K3"],
              "| max stosunek", max(R[seed]["ratio"], key=R[seed]["ratio"].get), round(max(R[seed]["ratio"].values()), 3), flush=True)
    n = {k: sum(R[s][k] for s in R) for k in ("K1", "K2", "K3")}
    verdict = "PASS" if all(v >= 9 for v in n.values()) else "FAILED"
    os.makedirs(RES, exist_ok=True)
    json.dump(dict(verdict=verdict, n=n, seeds=R, OUT_FULL=OUT_FULL, seconds=time.time() - t0), open(f"{RES}/test_syntetyczny.json", "w"), indent=1)
    print("WYNIK:", verdict, n, f"({time.time() - t0:.0f} s)")
    return R, verdict


def _check():
    lo = run("loom", 1, FlyEye(out_full=1.0))[:, 1:3].max()       # zbliżanie: 4 ramiona naraz; kamera w bok: 2 ramiona < 0
    pan = run("pan_h", 1, FlyEye(out_full=1.0))[:, 1:3].max()
    assert lo > 4 * pan, (lo, pan)
    print("oko_mucha _check OK: zbliżanie", round(lo, 4), "kamera w bok", round(pan, 4))


if __name__ == "__main__":
    if "--calib" in sys.argv:
        print("OUT_FULL =", calib())
    elif "--test" in sys.argv:
        test()
    else:
        _check()
