"""Krok 0: samo oko na kamerze nadgarstka w MuJoCo (plan: PREREG_KROK0.md). Bez sieci i bez sprzętu.
  step0_eye.py --settings OUT.json   zapis ustawień oka (przed przebiegiem)
  step0_eye.py --check               klatki i adaptacja, bez oceny sygnału oka na scenach próby
  step0_eye.py --out DIR             próba"""
import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
FLY = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path[:0] = [os.path.join(FLY, "experiments", "step3_wiring"), FLY]
import object_handling as oh  # noqa: E402
import oko_mucha as O  # noqa: E402

DT, T_AD, T_TRIAL, FPS = 0.01, 2.0, 3.5, 100
R_BALL, D0, D1, V, T_STOP = 0.02, 0.25, 0.06, 0.30, 2.0
N_AD, N = int(T_AD / DT), int(T_TRIAL / DT)
GRAY = np.array([0.299, 0.587, 0.114])
TRAJ = sorted(glob.glob(os.path.join(FLY, "results/step3_20261115/avoid_r1/test/N_g-1_palm_numb_*.npz")))
SEEDS = range(27400001, 27400011)
W_P1, W_P2 = (1.367, 2.1), (1.1, 2.5)
EYES = {"v2": lambda: O.FlyEye(out_full=O.OUT_FULL2, vshs=True, g0=O.G0), "v3": lambda: O.FlyEye3()}


class Cam:
    """Kamera „eye” w świecie object_handling; kula tylko w rendererze. Stan symulacji nietknięty (osobny MjData)."""
    def __init__(self):
        import mujoco
        self.mj, self.w = mujoco, oh.World([], 1)
        self.sim = self.w.sim
        m = self.m = self.sim.m
        m.geom_rgba[m.geom("mark_zone").id] = 0
        m.vis.headlight.ambient[:], m.vis.headlight.diffuse[:] = 0.6, 0.4
        self.r = mujoco.Renderer(m, 400, 640)
        for f in (mujoco.mjtRndFlag.mjRND_SHADOW, mujoco.mjtRndFlag.mjRND_REFLECTION, mujoco.mjtRndFlag.mjRND_SKYBOX):
            self.r.scene.flags[f] = False
        self.k, self.cid = mujoco.MjData(m), m.camera("eye").id
        self.home = np.array(oh.OHCfg().home)
        self.place(self.home[1:4])
        self.E0, R = self.k.cam_xpos[self.cid].copy(), self.k.cam_xmat[self.cid].reshape(3, 3).copy()
        self.R0, self.f0 = R, -R[:, 2]

    def place(self, q3):
        q = self.home.copy()
        q[1:4] = q3
        self.k.qpos[:] = self.sim.d.qpos
        self.k.qpos[self.sim.qadr] = q
        self.mj.mj_forward(self.m, self.k)

    def ball(self, t, moves):
        return self.E0 + self.f0 * (D1 + V * np.clip(T_STOP - t, 0.0, (D0 - D1) / V) if moves else D0)

    def frame(self, q3, ball):
        """Szara klatka 100×160 (float, przed szumem i uint8)."""
        self.place(q3)
        self.r.update_scene(self.k, camera="eye")
        s = self.r.scene
        self.mj.mjv_initGeom(s.geoms[s.ngeom], self.mj.mjtGeom.mjGEOM_SPHERE, np.array([R_BALL, 0, 0]), ball, np.eye(3).ravel(), np.array([.1, .1, .1, 1], np.float32))
        s.ngeom += 1
        g = self.r.render().astype(float) @ GRAY
        return g.reshape(100, 4, 160, 4).mean((1, 3))

    def rot_deg(self):
        R = self.k.cam_xmat[self.cid].reshape(3, 3)
        return float(np.degrees(np.arccos(np.clip((np.trace(self.R0.T @ R) - 1) / 2, -1, 1))))


def traj(path, scale=1.0):
    q = np.load(path)["q"]
    return q[0] + scale * (q - q[0])                                    # q[i] = kąty po takcie i


def frames(cam, q, ball_moves):
    """N klatek próby: klatka i widzi stan PRZED taktem i (kąty po takcie i−1)."""
    out, rot, gap = [], [], []
    for i in range(N):
        b = cam.ball(i * DT, ball_moves)
        out.append(cam.frame(cam.home[1:4] if q is None or i == 0 else q[i - 1], b))
        rot.append(cam.rot_deg())
        gap.append(float(np.linalg.norm(b - cam.k.cam_xpos[cam.cid])) - R_BALL)
    return np.array(out), np.array(rot), np.array(gap)


def see(F0, F, make, seed=None):
    """2 s adaptacji na klatce F0, potem próba. Zwraca loom [N, 2] mV (do neuronów) i raw [N, 2] (nieobcięty)."""
    eye, rng, out = make(), None if seed is None else np.random.default_rng(seed), []
    for j in range(N_AD + N):
        f = F0 if j < N_AD else F[j - N_AD]
        if rng is not None:
            f = f + O.SIGMA * rng.standard_normal(f.shape)
        eye.see(np.clip(np.round(f), 0, 255).astype(np.uint8), DT, (j - N_AD) * DT)
        if j >= N_AD:
            out.append((eye.loom["L"], eye.loom["R"], *(O.MV * x / eye.out_full for x in eye.out)))
    return np.array(out)


def settings(path):
    sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()  # noqa: E731
    git = lambda *a: subprocess.run(["git", "-C", FLY, *a], capture_output=True, text=True).stdout.strip()  # noqa: E731
    d = dict(zapisano=subprocess.run(["date"], capture_output=True, text=True).stdout.strip(), git_HEAD=git("rev-parse", "HEAD"),
             oko_mucha_commit=git("log", "-1", "--format=%h %s", "--", "experiments/step3_wiring/oko_mucha.py"),
             oko_mucha_zmiany_lokalne=git("status", "--short", "experiments/step3_wiring/oko_mucha.py"),
             v2=dict(klasa="FlyEye", out_full=O.OUT_FULL2, vshs=True, g0=O.G0, flip=False, blok_px=O.BLK, TAU_HP=O.TAU_HP, TAU_LP=O.TAU_LP, MV=O.MV, L_FULL=O.L_FULL, jednostki=len(O.LEFT)),
             v3=dict(klasa="FlyEye3", out_full=O.OUT_FULL3, g0=O.G3, blok_px=O.BLK3, TAU_LP=O.TAU_LP3, CGC=O.CGC3, jednostki=len(O.LEFT3)),
             obraz=dict(render="640x400", oko="160x100", gray=GRAY.tolist(), fps=FPS, fovy=70.0, szum_sigma=O.SIGMA), kula=dict(r=R_BALL, d0=D0, d1=D1, v=V, t_stop=T_STOP),
             adaptacja_s=T_AD, proba_s=T_TRIAL, trajektorie=[os.path.basename(x) for x in TRAJ],
             sha256={os.path.basename(p): sha(p) for p in (O.__file__, __file__, os.path.join(HERE, "PREREG_KROK0.md"), os.path.join(FLY, "so101.py"), oh.__file__,
                                                           os.path.join(FLY, "experiments/step3_wiring/live_avoid.py"))})
    with open(path, "x") as f:
        json.dump(d, f, indent=1, ensure_ascii=False)
    print(json.dumps(d, indent=1, ensure_ascii=False))


def check():
    cam = Cam()
    assert len(TRAJ) == 15 and all(np.allclose(np.load(t)["q"][0], cam.home[1:4]) and len(np.load(t)["q"]) == N for t in TRAJ)
    a, b = cam.frame(cam.home[1:4], cam.ball(0, True)), cam.frame(cam.home[1:4], cam.ball(0, True))
    assert (a == b).all(), "render niedeterministyczny"
    assert np.allclose(cam.ball(0, True), cam.ball(0, False)) and abs(np.linalg.norm(cam.ball(2.0, True) - cam.E0) - D1) < 1e-9
    dark = lambda t: (cam.frame(cam.home[1:4], cam.ball(t, True)) < 70).sum()  # noqa: E731
    n = [int(dark(t)) for t in (0.0, 1.3, 1.5, 1.7, 1.9, 2.0, 3.0)]
    assert n[0] == n[1] < n[2] < n[3] < n[4] < n[5] == n[6], n
    S = see(a, np.repeat(a[None], N, 0), EYES["v2"])
    assert S.max() < 1e-9, "nieruchomy obraz daje sygnał"
    o = O.run("loom", 24100900, EYES["v2"]())
    print("check OK; ciemne piksele kuli w czasie:", n, "| oko v2 na scenie kalibracyjnej (θ 37°):", round(O._at37(o, o[:, 1:3].max(axis=1)) / O.OUT_FULL2, 3))


def main(out):
    os.makedirs(out, exist_ok=True)
    cam = Cam()
    F0 = cam.frame(cam.home[1:4], cam.ball(0, False))
    scen = {"S": (None, False), "K": (None, True)}
    for k, t in enumerate(TRAJ):
        for sc in (1, 5, 20):
            for kula in (False, True):
                scen[f"{'KR' if kula else 'R'}_{sc}_{k:02d}"] = (traj(t, sc), kula)
    data = {}
    for name, (q, kula) in scen.items():
        F, rot, gap = frames(cam, q, kula)
        assert (F[0] == F0).all(), "klatka 0 ≠ klatka adaptacji"
        data[f"{name}/rot"], data[f"{name}/gap"] = rot, gap
        for v, mk in EYES.items():
            data[f"{name}/{v}"] = see(F0, F, mk)
        if name in ("S", "K") or "_1_" in name:
            data[f"{name}/v2_szum"] = np.array([see(F0, F, EYES["v2"], s) for s in SEEDS])
        print(name, "obrót kamery maks", round(rot.max(), 3), "° | odstęp kuli min", round(100 * gap.min(), 2), "cm", flush=True)
    np.savez_compressed(os.path.join(out, "sygnaly.npz"), **{k.replace("/", "__"): v for k, v in data.items()})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    settings(a.settings) if a.settings else check() if a.check else main(a.out)
