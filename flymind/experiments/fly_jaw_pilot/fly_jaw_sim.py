"""Pilot (exploratory, no seeds): classical reach (scaffold) brings the fixed pad onto the ball; the FLY circuit drives the jaw."""
import sys
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import numpy as np
from fly_jaw import FlyJaw, FlyJawCfg
from reach import ReachCfg, fixed_pad_target, ik, plan, plan_joint, ticks
from safety import Command, Limits, SafetyLayer, ranges_from_mjcf
from so101 import UPSTREAM, SO101Sim
from test_reach import Q0, table_contacts

def go(sim, safety, jaw_fn, targets, obs, settle, log):
    for tgt in list(targets) + [targets[-1]] * settle:
        tau, src = jaw_fn(obs)
        cmd = Command(obs.t, {j: float(tgt[j]) for j in range(5)}, tau, {**{j: "classical:reach" for j in range(5)}, "jaw": src})
        q_t, tau_t, flags, _ = safety.step(cmd, obs.q, obs.t, 0.0)
        sim.act(q_t, tau_t); sim.step(); obs = sim.observe(); log.append((obs.t, obs.q[5], *obs.touch, tau_t, table_contacts(sim)))
    return obs

sim = SO101Sim(render=False)
BALLS = [np.array(b) for b in ([0.25, 0.03, 0.025], [0.20, -0.10, 0.025], [0.22, 0.10, 0.025])]
GAIN = float(sys.argv[1]); VSIDE = float(sys.argv[2])
for ball in BALLS:
  for glu in (-1.0, 1.0):
      fj = FlyJaw(FlyJawCfg(glu_sign=glu, gain_mV_per_N=GAIN))
      sim.reset(Q0, ball_pos=ball)
      safety = SafetyLayer(Limits(ranges=ranges_from_mjcf(UPSTREAM)))
      obs, log = sim.observe(), []
      hold_open = lambda o: (-0.3 if o.q[5] < 0.9 else 0.0, "classical:open")       # scaffold: approach with jaw open
      fly = lambda o: (fj.step(o.touch), "snn:legT2L")
      qa, *_ = ik(sim, ball + [0, 0, 0.08], Q0)
      tgt = fixed_pad_target(sim, qa, ball, sim.cfg.ball_r, gap=0.004)
      n = tgt - ball - [0, 0, 0.005]; n[2] = 0; n /= np.linalg.norm(n)
      p1 = plan_joint(sim, Q0, tgt + [0, 0, 0.07], point="cs_fixed", jaw_open=Q0[5]); p2 = plan(sim, p1[-1], tgt, point="cs_fixed", jaw_open=Q0[5])
      obs = go(sim, safety, hold_open, ticks(p1, obs.q), obs, 20, log)
      obs = go(sim, safety, hold_open, ticks(p2, obs.q), obs, 20, log)
      n0 = len(log)
      d = sim.d; print('  after descent: ball', d.body('ball').xpos.round(4), 'fixed', d.site('cs_fixed').xpos.round(4), 'moving', d.site('cs_moving').xpos.round(4), 'n', n.round(2), 'touch', obs.touch.round(2))
      touch_at = tgt - n * 0.008
      obs = go(sim, safety, fly, ticks(plan(sim, obs.q, touch_at, point="cs_fixed", jaw_open=Q0[5]), obs.q, ReachCfg(v_max=VSIDE)), obs, 150, log)
      tgt = touch_at
      print('  after side-step+fly: ball', d.body('ball').xpos.round(4), 'fixed', d.site('cs_fixed').xpos.round(4), 'moving', d.site('cs_moving').xpos.round(4))
      grip = log[-1]
      z0 = sim.d.body("ball").xpos[2]
      obs = go(sim, safety, fly, ticks(plan(sim, obs.q, tgt + [0, 0, 0.06], point="cs_fixed"), obs.q), obs, 60, log)
      lift = sim.d.body("ball").xpos[2] - z0
      fl = [r for r in log[n0:]]
      first = next((i for i, r in enumerate(fl) if r[5] > 0.05), None)
      print(f"ball {ball[:2].tolist()} Glu {glu:+.0f}: touch at start {np.round(fl[0][2:4], 2)}, first close torque at tick {first}, after 1.5 s jaw q {grip[1]:.3f} "
            f"touch {np.round(grip[2:4], 2)} tau {grip[5]:.2f} | lift {lift*1000:.0f} mm, end touch {np.round(obs.touch[:2], 2)}, "
            f"rates press/release {fj.r_press:.0f}/{fj.r_release:.0f} Hz, table hits {sorted({x for r in log for x in r[6]})}, sources {sorted(safety.stats['per_source'])}")
