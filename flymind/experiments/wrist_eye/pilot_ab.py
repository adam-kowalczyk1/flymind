"""Pilotaż A/B (plan: PREREG_PILOT_AB.md): FlyEye v2 + HeadLife + ArmGrip w MuJoCo; obraz na żywo vs nagranie z nieruchomej kamery.
  pilot_ab.py --glu -1 --seeds 27501001,... --out DIR"""
import argparse
import os
import sys
import time
import zlib

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "three_joints")]
import step0_eye as S0  # noqa: E402
import three_joints as T  # noqa: E402
import avoid as A  # noqa: E402

DT, N, N_AD = 0.01, 700, 200
LEG = (S0.D0 - S0.D1) / S0.V                                           # 0,633 s
T1, HOLD, T2 = 1.0, 0.5, 4.27                                          # T2 na siatce taktów: klatki obu zbliżeń w tych samych fazach
CONDS = ("A", "B", "B1", "C")


def ball_dist(t):
    """Odległość kuli od startowego położenia kamery [m] — dwa jednakowe zbliżenia."""
    for t0 in (T2, T1):
        if t >= t0:
            u = t - t0
            return S0.D0 - S0.V * (np.clip(u, 0, LEG) - np.clip(u - LEG - HOLD, 0, LEG))
    return S0.D0


class Cam(S0.Cam):
    def shot(self, q6, dist):
        """Klatka 100×160 uint8 dla pełnej pozy q6 (osobny MjData) i kuli w `dist` m po startowej osi kamery; + obrót kamery [°]."""
        self.k.qpos[:] = self.sim.d.qpos
        self.k.qpos[self.sim.qadr] = q6
        self.mj.mj_forward(self.m, self.k)
        self.r.update_scene(self.k, camera="eye")
        s = self.r.scene
        self.mj.mjv_initGeom(s.geoms[s.ngeom], self.mj.mjtGeom.mjGEOM_SPHERE, np.array([S0.R_BALL, 0, 0]), self.E0 + self.f0 * dist, np.eye(3).ravel(), np.array([.1, .1, .1, 1], np.float32))
        s.ngeom += 1
        g = (self.r.render().astype(float) @ S0.GRAY).reshape(100, 4, 160, 4).mean((1, 3))
        return np.clip(np.round(g), 0, 255).astype(np.uint8), self.rot_deg()


class Drv(T.Drv):
    """T.Drv (czucie łokcia, szybki krok) + prąd oka na komórki zbliżania + zapis impulsów grup."""
    def __init__(self, net, feco, seed):
        super().__init__(net, feco, seed)
        self.loom, self.spk, run1 = {"L": 0.0, "R": 0.0}, None, net.net.run

        def run(X, n):
            X = X.copy()
            for s, ix in net._eyes.items():
                X[ix] = self.loom[s]
            self.spk = run1(X, n)
            return self.spk
        net.net.run = run


class Freeze:
    """Bez sieci (nagranie): komenda zero."""
    r = np.zeros((5, 2))

    def step(self, *a):
        return np.zeros(5)


def start():
    w, ctl, last = T.world()
    tgt = np.array(T.oh.OHCfg().home[:5])
    w.phase = "settle"
    for _ in range(100):
        ctl.tick(tgt, "open")
    w.phase = "net"
    ctl.active, ctl.qc = set(T.J), {j: float(tgt[j]) for j in T.J}
    return w, ctl, last, tgt


def record(cam):
    """Nagranie: ramię trzymane tą samą drogą, komendy zero."""
    w, ctl, last, tgt = start()
    ctl.drv, F = Freeze(), []
    f0 = cam.shot(ctl.obs.q, S0.D0)[0]
    for i in range(N):
        F.append(cam.shot(ctl.obs.q, ball_dist(i * DT))[0])
        ctl.tick(tgt, "open")
    return f0, np.array(F)


def trial(net, feco, cam, rec, seed, cond):
    f0, F = rec
    w, ctl, last, tgt = start()
    drv, eye = Drv(net, feco, seed), S0.EYES["v2"]()
    ctl.drv = drv
    rng = np.random.default_rng(27502000 + seed % 1000)
    for j in range(N_AD):
        eye.see(f0, DT, (j - N_AD) * DT)
    keys = ("loom", "raw", "dq", "qc", "qt", "q", "q_all", "r", "flag", "guard", "ncon", "rot", "fdiff", "cnt", "crc", "fcrc", "real_touch")
    log, q0 = {k: [] for k in keys}, ctl.obs.q.copy()
    for i in range(N):
        live = cond in ("A", "C")
        if live:
            f, rot = cam.shot(ctl.obs.q, S0.D0 if cond == "C" else ball_dist(i * DT))
        else:
            f, rot = F[i], cam.shot(ctl.obs.q, S0.D0)[1]
            if cond == "B1":
                f = np.clip(np.round(f + rng.standard_normal(f.shape)), 0, 255).astype(np.uint8)
        eye.see(f, DT, i * DT)
        drv.loom = dict(eye.loom)
        g0 = ctl.guard
        ctl.tick(tgt, "open")
        o, s = ctl.obs, drv.spk
        n = s.sum(0)
        for k, x in (("loom", (eye.loom["L"], eye.loom["R"])), ("raw", [T.A_MV * v / eye.out_full for v in eye.out]), ("dq", ctl.dq[1:4]), ("qc", [ctl.qc[j] for j in T.J]),
                     ("qt", last["out"][1:4]), ("q", o.q[1:4]), ("q_all", o.q), ("r", drv.r[1:4].copy()), ("flag", [sum(T.BIT[b] for b in last["per"].get(j, ())) for j in T.J]),
                     ("guard", ctl.guard - g0), ("ncon", sum(w.unwanted.values())), ("rot", rot), ("fdiff", np.abs(f.astype(float) - F[i]).mean()),
                     ("cnt", [int(n[m].sum()) for m in net._grp.values()]), ("crc", [zlib.crc32(s[:, m].tobytes()) for m in net._grp.values()]), ("fcrc", zlib.crc32(f.tobytes())), ("real_touch", o.touch)):
            log[k].append(np.array(x))
    return dict({k: np.array(v) for k, v in log.items()}, q0=q0)


def groups(net):
    """Grupy neuronów do śledzenia sygnału (adnotacje MaleCNS)."""
    import pandas as pd
    inv = {i: b for b, i in net.pos.items()}
    sc = pd.read_feather(T.JN.visual_path.ANN, columns=["bodyId", "superclass"]).set_index("bodyId").superclass.reindex([inv[i] for i in range(net.N)]).fillna("NA").to_numpy().astype(str)
    eye = np.zeros(net.N, bool)
    eye[[i for v in net._eyes.values() for i in v]] = True
    mn = np.zeros(net.N, bool)
    mn[[i for p, n in net.pools.values() for i in list(p) + list(n)]] = True
    dn = sc == "descending_neuron"
    return dict(oko=eye, mozg=~eye & ~dn & np.isin(sc, ["cb_intrinsic", "visual_projection", "ascending_neuron", "cb_sensory"]), DN=dn, rdzen=sc == "vnc_intrinsic", MN_stawy=mn)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--glu", type=float, required=True)
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--conds", default=",".join(CONDS))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    T.A_MV = S0.O.MV
    cam = Cam()
    rec = record(cam)
    assert (record(cam)[1] == rec[1]).all(), "nagranie niedeterministyczne"
    assert (rec[1][0] == rec[0]).all() and np.abs(rec[1][100].astype(int) - rec[0]).max() <= 1 and np.abs(rec[1][160].astype(int) - rec[0]).max() > 50   # szczęka osiada: ≤ 1 poziom
    i1, i2 = int(round(T1 / DT)), int(round(T2 / DT))
    print("drugie zbliżenie w nagraniu = pierwsze (różnica klatek, maks poziomów):", max(int(np.abs(rec[1][i1 + k].astype(int) - rec[1][i2 + k]).max()) for k in range(60)), "| T2 =", round(T2, 3), flush=True)
    net, feco = T.build(a.glu), T.alive.feco_idx(a.glu)
    net._eyes = A.eye_idx(net)
    net._grp = groups(net)
    net.W = None
    print({k: int(v.sum()) for k, v in net._grp.items()}, flush=True)
    for s in map(int, a.seeds.split(",")):
        for c in a.conds.split(","):
            path = os.path.join(a.out, f"g{a.glu:+.0f}_{s}_{c}.npz")
            if os.path.exists(path):
                sys.exit(f"istnieje {path}")
            t0 = time.time()
            g = trial(net, feco, cam, rec, s, c)
            np.savez_compressed(path, **g)
            print(s, c, f"{time.time() - t0:.0f} s | flagi", int((g["flag"] > 0).sum()), "strażnik", int(g["guard"].sum()), "kontakty", int(g["ncon"][-1]), flush=True)
