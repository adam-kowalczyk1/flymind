"""FJ2 pilot 2 (eksploracja, bez ziaren, szum 0). Start Q_POSE, piłeczka na wprost w zasięgu kamery (0,30 / 0,34 / 0,38 m).
Stawy 1–2: FlyArm (wzrok → sieć muchy), kierunki przypisania s1, s2 ∈ {+1, −1} (jawnie badane w pilocie).
Szczęka: FlyJaw (sam dotyk, obwód z FJ1), więc wzrok jej nie zamyka. Miara: zbliżenie punktu chwytu do piłeczki.
Uruchom:  .venv/bin/python -I -B flymind/experiments/fj2_fly_arm/pilot_arm2.py [k] [ticks]"""
import itertools
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from fly_arm import FlyArm, FlyArmCfg  # noqa: E402
from fly_jaw import FlyJaw, FlyJawCfg  # noqa: E402
from reach import _kin, grasp_point  # noqa: E402
from safety import Command, Limits, SafetyLayer, ranges_from_mjcf  # noqa: E402
from so101 import UPSTREAM, SO101Sim  # noqa: E402

Q_POSE = np.array([0.0, -0.4, 1.0, 0.0, 1.571, 0.93])
k = float(sys.argv[1]) if len(sys.argv) > 1 else 0.01
TICKS = int(sys.argv[2]) if len(sys.argv) > 2 else 400
sim = SO101Sim(render=True)
for glu in (-1.0, 1.0):
    arm, jaw = FlyArm(sim.cfg.cam_shape, FlyArmCfg(glu_sign=glu, k=k)), FlyJaw(FlyJawCfg(glu_sign=glu))
    for s1, s2 in itertools.product((1, -1), (1, -1)):
        out = []
        for rho in (0.30, 0.34, 0.38):
            arm.net.reset(); arm.r = {kk: np.zeros(2) for kk in arm.r}
            jaw.net.reset(); jaw.r_press = jaw.r_release = 0.0
            ball = np.array([rho, 0.0, 0.025])
            sim.reset(Q_POSE, ball_pos=ball)
            safety = SafetyLayer(Limits(ranges=ranges_from_mjcf(UPSTREAM)))
            obs, tgt = sim.observe(), Q_POSE[:5].copy()
            d0 = np.linalg.norm(grasp_point(_kin(sim, obs.q)) - ball); dmin, seen = d0, 0
            for t in range(TICKS):
                dq, _, diag = arm.step(obs.frame.image, obs.touch)
                tgt[1] += s1 * dq[1]; tgt[2] += s2 * dq[2]
                tau = jaw.step(obs.touch)
                cmd = Command(obs.t, {j: float(tgt[j]) for j in range(5)}, tau, {**{j: "snn:vision_leg" for j in range(5)}, "jaw": "snn:legT2L"})
                q_t, tau_t, flags, _ = safety.step(cmd, obs.q, obs.t, 0.0)
                tgt = q_t.copy()
                sim.act(q_t, tau_t); sim.step(); obs = sim.observe()
                dmin = min(dmin, np.linalg.norm(grasp_point(_kin(sim, obs.q)) - ball)); seen += diag["g"].mean() > 0.05
            d = np.linalg.norm(grasp_point(_kin(sim, obs.q)) - ball)
            out.append(f"rho {rho}: {d0*1000:.0f}→min {dmin*1000:.0f}→end {d*1000:.0f} mm, q1 {obs.q[1]:+.2f} q2 {obs.q[2]:+.2f}, seen {seen}/{TICKS}, touch {np.round(obs.touch[:2],1).tolist()}, ball moved {np.linalg.norm(sim.d.body('ball').xpos-ball)*1000:.0f} mm")
        print(f"Glu {glu:+.0f} s1 {s1:+d} s2 {s2:+d}:\n   " + "\n   ".join(out), flush=True)
