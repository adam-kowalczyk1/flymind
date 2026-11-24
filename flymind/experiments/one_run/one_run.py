"""Jedna ciągła próba (plan: PLAN_JEDEN_PRZEBIEG.md): kamera nadgarstka + A0/A1 + czucie łokcia → sieć → bark, łokieć, nadgarstek. Tylko MuJoCo.
  one_run.py --out DIR        pełny przebieg + kontrole przyczyn (a)–(d)"""
import argparse
import os
import sys
import time

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "..", "wrist_eye"), os.path.join(HERE, "..", "three_joints")]
import pilot_ab as P  # noqa: E402

T, S0, A = P.T, P.S0, P.A
DT, N, SEED = 0.01, 4500, 27601001
D_FAR, D_NEAR, V, SIDE = 0.22, 0.06, 0.30, 0.375
RUNS = dict(pelny={}, siec_odcieta=dict(cut=True), bez_wzroku=dict(blind=True), bez_dotyku=dict(numb=True), bez_obu=dict(blind=True, numb=True))
LEG = (D_FAR - D_NEAR) / V
# punkty toru kuli: (czas, bok [m, + = prawo kadru], odległość [m]); między nimi ruch jednostajny
PATH = [(0.0, -SIDE, D_FAR), (6.0, -SIDE, D_FAR), (8.5, SIDE, D_FAR), (10.0, SIDE, D_FAR), (11.25, 0.0, D_FAR), (12.0, 0.0, D_FAR), (12.0 + LEG, 0.0, D_NEAR), (13.2, 0.0, D_NEAR),
        (13.2 + LEG, 0.0, D_FAR), (14.5, 0.0, D_FAR), (15.75, SIDE, D_FAR), (34.0, SIDE, D_FAR), (35.25, 0.0, D_FAR), (36.0, 0.0, D_FAR), (36.0 + LEG, 0.0, D_NEAR), (38.5, 0.0, D_NEAR),
        (38.5 + LEG, 0.0, D_FAR), (40.0, 0.0, D_FAR), (41.25, SIDE, D_FAR), (45.0, SIDE, D_FAR)]
PRESS = [(20.0, 22.0, 0), (27.0, 29.0, 1), (36.0, 38.0, 1)]


def ball(t):
    p = np.array(PATH)
    return np.interp(t, p[:, 0], p[:, 1]), np.interp(t, p[:, 0], p[:, 2])


def forces(t):
    f = np.zeros(2)
    for a, b, k in PRESS:
        if a <= t < b:
            f[k] = T.F_N * min(1.0, (t - a) / 0.1)
    return f


class Cam(P.Cam):
    """Klatka kamery nadgarstka z kulą w punkcie (bok, odległość) względem startowej osi kamery."""
    def look(self, q6, side, dist):
        e, self.E0 = self.E0, self.E0 + self.R0[:, 0] * side
        f, rot = self.shot(q6, dist)
        self.E0 = e
        return f, rot


def trial(net, feco, cam, cut=False, blind=False, numb=False):
    w, ctl, last, tgt = P.start()
    drv, eye, feel = P.Drv(net, feco, SEED), S0.EYES["v2"](), T.TM.Feel(level="ideal", seed=SEED)
    ctl.drv = drv
    if cut:
        net_step = drv.step
        drv.step = lambda *a: 0.0 * net_step(*a)                        # kontrola (a): sieć liczy, komenda do stawów = 0
    log = {k: [] for k in ("t", "q_all", "dq", "qc", "qt", "r", "loom", "felt", "ball", "rot", "flag", "guard", "ncon", "cnt", "real_touch")}
    q0 = ctl.obs.q.copy()
    for i in range(N):                                                  # jedna pętla, bez warunków zależnych od bodźca
        t = i * DT
        side, dist = ball(t)
        f, rot = cam.look(ctl.obs.q, side, dist)
        eye.see(f, DT, t)
        drv.loom = dict(eye.loom) if not blind else {"L": 0.0, "R": 0.0}
        drv.felt = feel.step(forces(t)) * (0.0 if numb else 1.0)
        g0 = ctl.guard
        ctl.tick(tgt, "open")
        o = ctl.obs
        for k, x in (("t", t), ("q_all", o.q), ("dq", ctl.dq[1:4]), ("qc", [ctl.qc[j] for j in T.J]), ("qt", last["out"][1:4]), ("r", drv.r[1:4].copy()), ("loom", (eye.loom["L"], eye.loom["R"])),
                     ("felt", drv.felt), ("ball", (side, dist)), ("rot", rot), ("flag", [sum(T.BIT[b] for b in last["per"].get(j, ())) for j in T.J]), ("guard", ctl.guard - g0),
                     ("ncon", sum(w.unwanted.values())), ("cnt", [int(drv.spk[:, m].sum()) for m in net._grp.values()]), ("real_touch", o.touch)):
            log[k].append(np.array(x, float))
    return dict({k: np.array(v) for k, v in log.items()}, q0=q0)


def build():
    net, feco = T.build(-1.0), T.alive.feco_idx(-1.0)
    net._eyes = A.eye_idx(net)
    net._grp = P.groups(net)
    net.W, net.pads = None, net._full
    return net, feco


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    T.A_MV = S0.O.MV
    cam, (net, feco) = Cam(), build()
    for name, kw in RUNS.items():
        path = os.path.join(a.out, name + ".npz")
        if os.path.exists(path):
            sys.exit(f"istnieje {path}")
        t0 = time.time()
        g = trial(net, feco, cam, **kw)
        np.savez_compressed(path, **g)
        print(name, f"{time.time() - t0:.0f} s obliczeń na 45 s próby | flagi", int((g["flag"] > 0).sum()), "strażnik", int(g["guard"].sum()), "kontakty", int(g["ncon"][-1]),
              "| zmiana kątów °", np.degrees(g["q_all"][-1] - g["q0"])[1:4].round(2).tolist(), flush=True)
