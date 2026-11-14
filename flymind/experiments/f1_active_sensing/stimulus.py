"""F1 stimulus (ENGINEERING): virtual-camera motion trajectories and MuJoCo rendering of a static scene (PROTOCOL r2 §2–3).
Robot static at loop.Q_POSE, physics never stepped. Camera rotated about the WORLD VERTICAL through its optical centre (position
unchanged) by writing cam_quat of the in-memory model; no file is modified. θ > 0 = camera turned left ⇒ true bearing = az0 − θ.
MT control: camera static, ball moved on the horizontal circle around the camera to bearing az0 − θ.
"""
import math
import os
import sys

import numpy as np

FLY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, FLY)
import loop as L  # noqa: E402
from so101 import SO101Sim  # noqa: E402

T, FR, W0 = 300, 0.01, 100           # frames, s per frame, first window frame
GREY = 0.75                          # table rgb (so101.build_mjcf)


def _window_norm(x, A):
    """Remove the window mean and scale the whole trace so the window RMS is A/√2."""
    x = x - x[W0:].mean()
    return x / np.sqrt((x[W0:] ** 2).mean()) * A / math.sqrt(2)


def derivs(th):
    """θ̇ [rad/s], θ̈ [rad/s²] by central differences."""
    v = np.gradient(th, FR)
    return v, np.gradient(v, FR)


def motion(kind, f, A_deg, phase, rng=None, vel_tol=0.2, max_draws=1000):
    """θ[k] [rad]. kind: stat | sin | mt (same trajectory as sin) | jshuf | jrms | jvel. Returns (θ, draws)."""
    t = np.arange(T) * FR
    A = math.radians(A_deg)
    if kind == "stat" or A == 0:
        return np.zeros(T), 0
    s = A * np.sin(2 * math.pi * f * t + phase)
    if kind in ("sin", "mt"):
        return s, 0
    if kind == "jshuf":
        return np.r_[rng.permutation(s[:W0]), rng.permutation(s[W0:])], 1
    if kind == "jrms":
        return _window_norm(rng.standard_normal(T), A), 1
    if kind == "jvel":
        sd = 1 / (2 * math.sqrt(2) * math.pi * f) / FR
        h = int(math.ceil(4 * sd))
        k = np.exp(-0.5 * (np.arange(-h, h + 1) / sd) ** 2)
        target = 2 * math.pi * f * A / math.sqrt(2)
        for n in range(1, max_draws + 1):
            x = _window_norm(np.convolve(rng.standard_normal(T + 2 * h), k / k.sum(), "valid"), A)
            v = np.sqrt((derivs(x)[0][W0:] ** 2).mean())
            if abs(v / target - 1) <= vel_tol:
                return x, n
        raise RuntimeError("jvel: no accepted draw")
    raise ValueError(kind)


def _qmul(a, b):
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return np.array([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                     w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2])


class Scene:
    """One SO101Sim used as a static renderer: set_target() then frames(θ, mode)."""

    def __init__(self):
        self.sim = s = SO101Sim()
        m = s.m
        self.cid, self.gid = m.camera("eye").id, m.geom("ball").id
        self.bq = m.joint("ball").qposadr[0]
        self.q_local0 = m.cam_quat[self.cid].copy()
        self.rgba0, self.size0, self.rbound0 = m.geom_rgba[self.gid].copy(), m.geom_size[self.gid].copy(), float(m.geom_rbound[self.gid])
        s.reset(L.Q_POSE)
        self.q_body = s.d.xquat[m.cam_bodyid[self.cid]].copy()
        k = s.fk(L.Q_POSE)
        self.eye, self.psi0 = k["eye"].copy(), math.atan2(k["eye_forward"][1], k["eye_forward"][0])
        self.tgt = None
        self.cache = {}                                # (mode, round(θ, 12)) → image for the current target (PROTOCOL r3.1 A1)

    def set_target(self, az_deg=None, rho=None, k=1.0, r=0.025):
        """az_deg None = no target (ball parked, default colour and size). Returns the ball world position or None."""
        s, m, g = self.sim, self.sim.m, self.gid
        m.cam_quat[self.cid] = self.q_local0
        self.cache = {}
        if az_deg is None:
            m.geom_rgba[g], m.geom_size[g], m.geom_rbound[g] = self.rgba0, self.size0, self.rbound0
            s.reset(L.Q_POSE)
            self.tgt = None
            return None
        m.geom_rgba[g, :3] = GREY + k * (self.rgba0[:3] - GREY)
        m.geom_size[g, 0], m.geom_rbound[g] = r, r
        x, y, _ = L.place_ball(s, math.radians(az_deg), rho)
        s.reset(L.Q_POSE, ball_pos=(x, y, r))
        self.tgt = (math.radians(az_deg), rho, r)
        return np.array([x, y, r])

    def pose(self, theta):
        """Camera world-yaw θ about its optical centre; returns (cam_xpos, cam_xmat) that the renderer will use."""
        s, m = self.sim, self.sim.m
        qz = np.array([math.cos(theta / 2), 0.0, 0.0, math.sin(theta / 2)])
        qb_inv = self.q_body * np.array([1, -1, -1, -1])
        m.cam_quat[self.cid] = _qmul(qb_inv, _qmul(qz, _qmul(self.q_body, self.q_local0)))
        s.mj.mj_forward(m, s.d)
        return s.d.cam_xpos[self.cid].copy(), s.d.cam_xmat[self.cid].reshape(3, 3).copy()

    def _move_ball(self, bearing):
        az0, rho, r = self.tgt
        psi = self.psi0 + bearing
        self.sim.d.qpos[self.bq:self.bq + 7] = [self.eye[0] + rho * math.cos(psi), self.eye[1] + rho * math.sin(psi), r, 1, 0, 0, 0]

    def frames(self, theta, mode="camera", cache=True):
        """mode 'camera': rotate the camera by θ; 'mt': static camera, ball at bearing az0 − θ. Returns images [T,H,W,3], record.
        cache: an image already rendered for the same target, mode and θ (rounded to 1e-12 rad) is reused (scene is static)."""
        H, W = self.sim.cfg.cam_shape
        n = len(theta)
        imgs = np.empty((n, H, W, 3), np.uint8)
        rec = dict(cam_pos=np.empty((n, 3)), cam_R=np.empty((n, 3, 3)), bearing=np.full(n, np.nan), ball=np.full((n, 3), np.nan))
        for k, th in enumerate(theta):
            if mode == "mt":
                if self.tgt is not None:
                    self._move_ball(self.tgt[0] - th)
                rec["cam_pos"][k], rec["cam_R"][k] = self.pose(0.0)
            else:
                rec["cam_pos"][k], rec["cam_R"][k] = self.pose(th)
            key = (mode, round(float(th), 12))
            img = self.cache.get(key) if cache else None
            if img is None:
                img = self.sim.observe().frame.image
                if img is None:
                    raise RuntimeError(f"render failed: {self.sim.last_error}")
                if cache:
                    self.cache[key] = img
            imgs[k] = img
            rec["ball"][k] = self.sim.d.qpos[self.bq:self.bq + 3]
            if self.tgt is not None:
                rec["bearing"][k] = L.bearing(self.sim, L.Q_POSE)
        self.sim.m.cam_quat[self.cid] = self.q_local0
        if mode == "mt" and self.tgt is not None:        # put the ball back at its static position
            self._move_ball(self.tgt[0])
            self.sim.mj.mj_forward(self.sim.m, self.sim.d)
        return imgs, rec

    def close(self):
        self.sim.close()
