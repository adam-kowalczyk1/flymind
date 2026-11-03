"""FJ2 pilot (eksploracja, bez ziaren, szum 0): czy sam wzrok przez sieć muchy przybliża chwytak do piłeczki?
Piłeczka na wprost (azymut 0), podstawa nieruchoma. Komendy stawów 1–2 i szczęki tylko z FlyArm (źródło snn:vision_leg).
Uruchom:  .venv/bin/python -I -B flymind/experiments/fj2_fly_arm/pilot_arm.py <k> [ticks]"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from fly_arm import FlyArm, FlyArmCfg  # noqa: E402
from reach import _kin, grasp_point  # noqa: E402
from safety import Command, Limits, SafetyLayer, ranges_from_mjcf  # noqa: E402
from so101 import UPSTREAM, SO101Sim  # noqa: E402

Q_POSE = np.array([0.0, -0.4, 1.0, 0.0, 1.571, 0.93])
k = float(sys.argv[1]) if len(sys.argv) > 1 else 0.01
TICKS = int(sys.argv[2]) if len(sys.argv) > 2 else 400
sim = SO101Sim(render=True)
for glu in (-1.0, 1.0):
    arm = None
    for rho in (0.20, 0.27, 0.34):
        arm = FlyArm(sim.cfg.cam_shape, FlyArmCfg(glu_sign=glu, k=k)) if arm is None else arm
        arm.net.reset(); arm.r = {kk: np.zeros(2) for kk in arm.r}
        ball = np.array([rho, 0.0, 0.025])
        sim.reset(Q_POSE, ball_pos=ball)
        safety = SafetyLayer(Limits(ranges=ranges_from_mjcf(UPSTREAM)))
        obs, tgt = sim.observe(), Q_POSE[:5].copy()
        d0 = np.linalg.norm(grasp_point(_kin(sim, obs.q)) - ball); dmin, log = d0, []
        for t in range(TICKS):
            dq, tau, diag = arm.step(obs.frame.image, obs.touch)
            for j, v in dq.items():
                tgt[j] += v
            cmd = Command(obs.t, {j: float(tgt[j]) for j in range(5)}, tau, {**{j: "snn:vision_leg" for j in range(5)}, "jaw": "snn:vision_leg"})
            q_t, tau_t, flags, per = safety.step(cmd, obs.q, obs.t, 0.0)
            tgt = q_t.copy()                                  # cel po ograniczeniach (bez narastania poza zakresem)
            sim.act(q_t, tau_t); sim.step(); obs = sim.observe()
            d = np.linalg.norm(grasp_point(_kin(sim, obs.q)) - ball); dmin = min(dmin, d)
            if t % 100 == 0 or t == TICKS - 1:
                log.append(f"t{t}: q1 {obs.q[1]:+.2f} q2 {obs.q[2]:+.2f} d {d*1000:.0f}mm g {np.round(diag['g'],2).tolist()} DNp09 {np.round(diag['dnp09']).tolist()} r {diag['rates']}")
        print(f"\nGlu {glu:+.0f} rho {rho}: start {d0*1000:.0f} mm, min {dmin*1000:.0f} mm, end {d*1000:.0f} mm, touch {obs.touch.round(2).tolist()}, ball moved {np.linalg.norm(sim.d.body('ball').xpos - ball)*1000:.0f} mm, safety per_source {safety.stats['per_source']}")
        for l in log: print("   ", l)
