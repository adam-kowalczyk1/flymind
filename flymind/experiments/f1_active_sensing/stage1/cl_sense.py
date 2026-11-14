"""F1 Stage 1 (ENGINEERING / MODEL): closed-loop trial with a sensing motion (STAGE1_DESIGN.md d3 §3–§5).
The loop is loop.run_trial (V5, frozen) re-composed from the same frozen modules; additions are guarded so that motion 'none',
no pixel noise and 300 ticks reproduce loop.run_trial bit for bit (test F1). Nothing outside stage1/ is modified; mujoco only via
SO101Sim (in-memory cam_quat / ball qpos for the 'virtual' / 'mt' modes, restored every tick)."""
import math
import os
import sys

import numpy as np

FLY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, FLY)
import loop as L  # noqa: E402
from alif import ALIF  # noqa: E402
from decoder import SteerDecoder  # noqa: E402
from encoder import TargetEncoder  # noqa: E402
from latency import DelayLine  # noqa: E402
from safety import Command, Limits, SafetyLayer, ranges_from_mjcf  # noqa: E402
from sensory import Frame, SensoryGate, spot_clip  # noqa: E402
from so101 import UPSTREAM, SO101Sim, integrate_pan  # noqa: E402

DT = L.DT
T_ON = 0.25                           # s, cosine onset ramp (d3.1 A7: a step at t = 0 was rate-clipped into pan_t)
T_MOVE, T_RAMP = 4.75, 5.5            # envelope: 1 until 4.75 s, cosine ramp to 0 at 5.5 s (§3)
B_AMP = math.radians(4.0)             # bearing amplitude of every motion (§3)
TH_TAU_MS, TH_MV = 20.0, 5.93         # TH_LP-ster, fixed from Stage 0 (§4)
GATE_RAMP = 0.25                      # s, gated on/off ramp


def envelope(n):
    t = np.arange(n) * DT
    e = np.ones(n)
    r = (t > T_MOVE) & (t < T_RAMP)
    e[r] = 0.5 * (1 + np.cos(math.pi * (t[r] - T_MOVE) / (T_RAMP - T_MOVE)))
    e[t >= T_RAMP] = 0.0
    on = t < T_ON
    e[on] = 0.5 * (1 - np.cos(math.pi * t[on] / T_ON))
    return e


def jvel(n, f, rng, vel_tol=0.2, max_draws=1000):
    """Unit-bearing-amplitude smooth jitter (Stage 0 J_vel kernel), RMS and velocity RMS matched to sin(·) over 0.75–4.75 s."""
    w = slice(int(0.75 / DT), int(T_MOVE / DT))
    sd = 1 / (2 * math.sqrt(2) * math.pi * f) / DT
    h = int(math.ceil(4 * sd))
    k = np.exp(-0.5 * (np.arange(-h, h + 1) / sd) ** 2)
    target = 2 * math.pi * f / math.sqrt(2)
    for d in range(1, max_draws + 1):
        x = np.convolve(rng.standard_normal(n + 2 * h), k / k.sum(), "valid")
        x = x - x[w].mean()
        x = x / np.sqrt((x[w] ** 2).mean()) / math.sqrt(2)
        v = np.sqrt((np.gradient(x, DT)[w] ** 2).mean())
        if abs(v / target - 1) <= vel_tol:
            return x, d
    raise RuntimeError("jvel: no accepted draw")


def bearing_gain(sim, q, ball_pos):
    """|d bearing / d q_pan| at pose q for a ball at ball_pos (finite difference ±0.5°, FK only, state untouched)."""
    b = sim.m.joint("ball").qposadr[0]
    keep = sim.d.qpos[b:b + 3].copy()
    sim.d.qpos[b:b + 3] = ball_pos
    h = math.radians(0.5)
    qp, qm = q.copy(), q.copy()
    qp[0] += h
    qm[0] -= h
    g = abs(L.bearing(sim, qp) - L.bearing(sim, qm)) / (2 * h)
    sim.d.qpos[b:b + 3] = keep
    return g


def _qmul(a, b):
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return np.array([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                     w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2])


def calibrate_th(shape):
    """slope_TH: loop.calibrate_p procedure (same synthetic spots, offset 0) on the steady-state TH_LP-ster signal u."""
    enc = TargetEncoder(shape, L.ENC)
    az = np.arange(-30, 31, 10)
    imgs = spot_clip(np.radians(az), np.zeros(len(az)), shape, 70.0, 9, (40, 180, 50), (120, 120, 120)).images
    y = np.array([L.ENC.i_max * enc.encode(im)["g"] for im in imgs])
    d = np.maximum(0, y[:, 0] - TH_MV) - np.maximum(0, y[:, 1] - TH_MV)
    x = np.radians(az)
    return float((d * x).sum() / (x * x).sum())


def run(ctrl, spec_idx, seed, calib, tr, motion="none", f=1.0, phase=0.0, noise=None, ticks=L.TICKS, slope=None,
        jit=None, omega_on=0.10, g_b=None):
    """One trial. ctrl: 'snn' | 'th' | 'p'; spec_idx = (spec, idx) for 'snn'; tr = dict(az0_deg, rho) or dict(az0_deg=None) for no
    target; motion: none | sin | jvel | gated | virtual | mt; noise int16 [ticks, H, W, 3] or None; jit: unit-amplitude jvel trace;
    g_b: bearing gain for A_pan = 4°/g_b (pan modes). Returns the loop.run_trial record plus Stage 1 traces."""
    spec, idx = spec_idx
    sim = SO101Sim()
    try:
        target = tr.get("az0_deg") is not None
        ball = L.place_ball(sim, math.radians(tr["az0_deg"]), tr["rho"]) if target else None
        sim.reset(L.Q_POSE, ball_pos=ball)
        H, W = sim.cfg.cam_shape
        gate = SensoryGate((H, W), period=DT, max_age=0.05, reset_after=0.1)
        enc = TargetEncoder((H, W), L.ENC)
        net = ALIF(spec, L.P, seed) if ctrl == "snn" else None
        inL, inR = idx["in_L"], idx["in_R"]
        dec = SteerDecoder({"DNa02_L": idx["DNa02_L"], "DNa02_R": idx["DNa02_R"]}, ("DNa02",), [0.0],
                           [slope or calib["slope_snn"]], L.STEER) if ctrl == "snn" else None
        p_f, y_lp = 0.0, np.zeros(2)
        a_lp = math.exp(-DT * 1000 / TH_TAU_MS)
        safety = SafetyLayer(Limits(ranges=ranges_from_mjcf(UPSTREAM), max_sensor_age=0.05))
        delay = DelayLine(0, None)
        src = {"snn": "snn:DNa02", "p": "classical:P_encoder", "th": "classical:TH_LP", "zero": "script:hold_pose"}[ctrl]

        env = envelope(ticks)
        t = np.arange(ticks) * DT
        unit = {"none": np.zeros(ticks), "jvel": jit if jit is not None else np.zeros(ticks)}.get(
            motion, np.sin(2 * math.pi * f * t + phase))
        shape_t = unit * env                                  # bearing-unit trajectory (×4°)
        pan_mode = motion in ("sin", "jvel", "gated")
        a_pan = B_AMP / g_b if pan_mode else 0.0
        cid, bq = sim.m.camera("eye").id, sim.m.joint("ball").qposadr[0]
        q_local0 = sim.m.cam_quat[cid].copy()
        cam_body = sim.m.cam_bodyid[cid]

        gamp, gtgt, quiet = 1.0, 1.0, 0.0
        pan_t, e, om, flags = 0.0, [], [], {}
        th_s, pan_m, pan_tr, invalid = np.zeros(ticks), np.zeros(ticks), np.zeros(ticks), 0
        q0_tr, ball_dev, last_set = np.zeros(ticks), 0.0, None
        cnt = np.zeros((ticks, 4), np.int16)                  # LC10a L, LC10a R, DNa02 L, DNa02 R spikes per tick
        omega = 0.0
        for k in range(ticks):
            if motion == "gated" and k:                       # amplitude state from the previous tick's omega
                if abs(omega) > omega_on:
                    gtgt, quiet = 0.0, 0.0
                else:
                    quiet += DT
                    if quiet >= 1.0:
                        gtgt = 1.0
                gamp += float(np.clip(gtgt - gamp, -DT / GATE_RAMP, DT / GATE_RAMP))
            th_s[k] = a_pan * shape_t[k] * (gamp if motion == "gated" else 1.0)
            q0_tr[k] = sim.d.qpos[sim.qadr[0]]
            if motion == "mt" and target:                     # ball on the circle around the CURRENT eye, direction + δ
                if last_set is not None:
                    ball_dev = max(ball_dev, float(np.linalg.norm(sim.d.qpos[bq:bq + 3] - last_set)))
                q_now = sim.d.qpos[sim.qadr].copy()
                eye = sim.fk(q_now)["eye"]
                v = np.asarray(ball[:2]) - eye[:2]
                psi = math.atan2(v[1], v[0]) + B_AMP * shape_t[k]
                r = math.hypot(*v)
                sim.d.qpos[bq:bq + 7] = [eye[0] + r * math.cos(psi), eye[1] + r * math.sin(psi), ball[2], 1, 0, 0, 0]
                last_set = sim.d.qpos[bq:bq + 3].copy()
                sim.d.qvel[sim.m.joint("ball").dofadr[0]:][:6] = 0.0
                sim.mj.mj_forward(sim.m, sim.d)
            e.append(L.bearing(sim, sim.d.qpos[sim.qadr].copy()))
            if target:
                qm = sim.d.qpos[sim.qadr].copy()
                qm[0] -= th_s[k]
                pan_m[k] = L.bearing(sim, qm)
            if motion == "virtual":                           # camera yaw about world vertical through the optical centre
                th = B_AMP * shape_t[k]
                qb = sim.d.xquat[cam_body].copy()
                qz = np.array([math.cos(th / 2), 0.0, 0.0, math.sin(th / 2)])
                sim.m.cam_quat[cid] = _qmul(qb * np.array([1, -1, -1, -1]), _qmul(qz, _qmul(qb, q_local0)))
                sim.mj.mj_camlight(sim.m, sim.d)
            obs = sim.observe()
            if motion == "virtual":
                sim.m.cam_quat[cid] = q_local0
                sim.mj.mj_camlight(sim.m, sim.d)
            fr = delay.push(obs.frame)
            if fr is None:
                s_usable, age, img = False, 0.0, None
            else:
                smp = gate.push(fr, now=obs.t)
                s_usable, age, img = smp.usable, smp.age, fr.image if smp.usable else None
            if img is not None and noise is not None:
                img = np.clip(img.astype(np.int16) + noise[k], 0, 255).astype(np.uint8)
            g = enc.encode(img)["g"]
            if ctrl == "zero":                               # diagnostic: motor loop off (F3)
                omega = 0.0
            elif ctrl == "p":
                a = math.exp(-DT / L.STEER.tau_s[0])
                p_f = a * p_f + (1 - a) * float(g @ [1, -1])
                omega = float(np.clip(L.STEER.gain * p_f / calib["slope_p"], -L.STEER.w_max, L.STEER.w_max))
            elif ctrl == "th":
                y_lp = a_lp * y_lp + (1 - a_lp) * L.ENC.i_max * np.asarray(g, float)
                u = max(0.0, y_lp[0] - TH_MV) - max(0.0, y_lp[1] - TH_MV)
                a = math.exp(-DT / L.STEER.tau_s[0])
                p_f = a * p_f + (1 - a) * u
                omega = float(np.clip(L.STEER.gain * p_f / calib["slope_th"], -L.STEER.w_max, L.STEER.w_max))
            else:
                I = enc.currents(g, inL, inR, len(spec.bodies))
                spk = net.run(I, 10)
                omega = dec.step(spk, 1.0)["omega"]
                cnt[k] = (spk[:, inL].sum(), spk[:, inR].sum(), spk[:, idx["DNa02_L"]].sum(), spk[:, idx["DNa02_R"]].sum())
            pan_t = integrate_pan(pan_t, omega, DT)
            cmd = Command(obs.t, {0: pan_t + th_s[k], **{j: L.Q_POSE[j] for j in range(1, 5)}}, None,
                          {0: src, **{j: "script:hold_pose" for j in range(1, 5)}})
            qt, tau, fl, per = safety.step(cmd, obs.q, now=obs.t, sensor_age=age)
            pan_t = qt[0] - th_s[k]                           # command-level efference copy (§3)
            pan_tr[k] = pan_t
            for x in list(fl) + [y for v in per.values() for y in v]:
                flags[x] = flags.get(x, 0) + 1
            if "cmd_timeout" in fl or any("vision_stale" in v for v in per.values()):
                invalid += 1
            sim.act(qt, tau)
            sim.step()
            om.append(omega)
        e = np.degrees(np.array(e))
        az0 = tr["az0_deg"] if target else 0.0
        return dict(ctrl=ctrl, motion=motion, az0_deg=az0, rho=tr.get("rho"), e_deg=e.round(3).tolist(),
                    omega=np.round(om, 4).tolist(), safety_flags=flags, safety_per_source=safety.stats["per_source"],
                    gate=gate.stats, sim_stats={k: v for k, v in sim.stats.items() if k != "released"},
                    theta_s=th_s, pan_t=pan_tr, q0=q0_tr, ball_dev_m=ball_dev, e_motor_deg=np.degrees(pan_m), counts=cnt, invalid_ticks=invalid, a_pan=a_pan)
    finally:
        sim.close()


def lockin(x, f, phase, lo=0.75, hi=T_MOVE):
    """S10 estimator: amplitude of the f-component of x over [lo, hi) s after linear detrend, reference phase = trial phase."""
    k = np.arange(int(lo / DT), int(hi / DT))
    y = np.asarray(x, float)[k]
    t = k * DT
    y = y - np.polyval(np.polyfit(t, y, 1), t)
    return float(2 * abs(np.mean(y * np.exp(-1j * (2 * math.pi * f * t + phase)))))


RANGES = dict(W=dict(rho=(0.22, 0.36), az=(8.0, 16.0)), S=dict(rho=(0.16, 0.24), az=(10.0, 30.0)))


def draw(u, ranges=RANGES):
    """Per-unit stimulus (§10): default_rng([u, 2]) uniforms in the order W(ρ, |az|, side, φ), S(ρ, |az|, side, φ), N(φ), mapped onto
    `ranges` (R1 may re-centre W; the uniforms stay the same)."""
    r = np.random.default_rng([u, 2])
    out = {}
    for g in ("W", "S"):
        a, b, c, d = r.uniform(size=4)
        (r0, r1), (z0, z1) = ranges[g]["rho"], ranges[g]["az"]
        out[g] = dict(rho=r0 + a * (r1 - r0), az=z0 + b * (z1 - z0), side=1 if c < 0.5 else -1, phi=2 * math.pi * d)
    out["N"] = dict(phi=2 * math.pi * r.uniform())
    return out


def pixel_noise(u, sigma=10.0, ticks=600, shape=(96, 128)):
    return np.rint(np.random.default_rng([u, 1]).standard_normal((ticks, *shape, 3)) * sigma).astype(np.int16)


def gain_for(tr):
    """Bearing gain at the start pose for this trial's ball (no target: nominal ρ 0.29 m, |az| 12°)."""
    sim = SO101Sim(render=False)
    try:
        az, rho = (tr["az0_deg"], tr["rho"]) if tr.get("az0_deg") is not None else (12.0, 0.29)
        b = L.place_ball(sim, math.radians(az), rho)
        sim.reset(L.Q_POSE, ball_pos=b)
        return bearing_gain(sim, L.Q_POSE.copy(), b)
    finally:
        sim.close()
