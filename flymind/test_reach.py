"""Testy klasycznego sięgania i chwytu (reach.py, grip.py) w MuJoCo, headless, bez bio2, bez losowości i ziaren.
T1 IK w obie strony, T2 cel nieosiągalny, T3 cel pod stołem, T4 automat szczęki, T5 podniesienie piłeczki w 3 miejscach:
sięgnięcie z góry → zejście → chwyt do kontaktu obu szczęk → uniesienie o 6 cm, bez dotknięcia stołu ramieniem. To test INŻYNIERII (źródła "classical:*"), nie biologii.
Uruchom:  .venv/bin/python -I -B flymind/test_reach.py"""
import itertools
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grip import ClassicGrip, GripCfg  # noqa: E402
from reach import ReachError, _kin, fixed_pad_target, grasp_point, ik, plan, plan_joint, ticks  # noqa: E402
from safety import Command, Limits, SafetyLayer, ranges_from_mjcf  # noqa: E402
from so101 import UPSTREAM, SO101Sim  # noqa: E402

Q0 = np.array([0, -0.4, 1.0, 0, 1.571, 0.93])
BALLS = [np.array([0.25, 0.03, 0.025]), np.array([0.20, -0.10, 0.025]), np.array([0.22, 0.10, 0.025])]
ARM_GEOMS_OK_ON_TABLE = {"ball"}


def table_contacts(sim):
    c, n = sim.d.contact, sim.d.ncon
    g = np.asarray(c.geom).reshape(-1, 2)[:n]
    names = [(sim.m.geom(int(a)).name, sim.m.geom(int(b)).name) for a, b in g]
    return sorted({b if a == "table" else a for a, b in names if "table" in (a, b)} - ARM_GEOMS_OK_ON_TABLE)


def run(sim, safety, grip, targets, jaw_mode, obs, settle=30, log=None):
    """Wykonaj cele [5] przez SafetyLayer; szczęka z ClassicGrip. Zwraca ostatnią obserwację."""
    grip.mode = jaw_mode
    for tgt in list(targets) + [targets[-1]] * settle:
        tau = grip.step(obs.q[5], obs.touch)
        cmd = Command(obs.t, {j: float(tgt[j]) for j in range(5)}, tau,
                      {**{j: "classical:reach" for j in range(5)}, "jaw": "classical:grip"})
        q_t, tau_t, flags, _ = safety.step(cmd, obs.q, obs.t, 0.0)
        assert not flags, flags
        sim.act(q_t, tau_t)
        sim.step()
        obs = sim.observe()
        if log is not None:
            log.append(table_contacts(sim))
    return obs


def pick(sim, ball, gap=0.004):
    """Chwyt z góry: stała szczęka obok piłeczki → zamknięcie do kontaktu obu → uniesienie o 6 cm.
    Zwraca (błąd padu [m], uniesienie [m], touch po uniesieniu, dotknięcia stołu, źródła komend)."""
    sim.reset(Q0, ball_pos=ball)
    safety = SafetyLayer(Limits(ranges=ranges_from_mjcf(UPSTREAM)))
    grip, obs, log = ClassicGrip(), sim.observe(), []
    q_above, *_ = ik(sim, ball + [0, 0, 0.08], Q0)
    tgt = fixed_pad_target(sim, q_above, ball, sim.cfg.ball_r, gap)
    p1 = plan_joint(sim, Q0, tgt + [0, 0, 0.07], point="cs_fixed", jaw_open=Q0[5])
    p2 = plan(sim, p1[-1], tgt, point="cs_fixed", jaw_open=Q0[5])
    obs = run(sim, safety, grip, ticks(p1, obs.q), "open", obs, log=log)
    obs = run(sim, safety, grip, ticks(p2, obs.q), "open", obs, log=log)
    err = float(np.linalg.norm(sim.d.site("cs_fixed").xpos - tgt))
    obs = run(sim, safety, grip, [obs.q[:5]] * 80, "close", obs, log=log)
    assert grip.mode == "hold", f"brak kontaktu obu szczęk: touch {obs.touch.round(2)}"
    z0 = sim.d.body("ball").xpos[2]
    obs = run(sim, safety, grip, ticks(plan(sim, obs.q, tgt + [0, 0, 0.06], point="cs_fixed"), obs.q), "hold", obs,
              settle=50, log=log)
    return err, sim.d.body("ball").xpos[2] - z0, obs.touch, sorted({x for c in log for x in c}), set(safety.stats["per_source"])


def main():
    sim = SO101Sim(render=False)

    # T1: q → punkt chwytu → IK z innego startu → ten sam punkt (siatka deterministyczna, bez losowania)
    worst = 0.0
    for pan, lift, elb, wf in itertools.product((-0.6, 0.0, 0.6), (-0.3, 0.2), (0.4, 0.9), (0.6, 1.1)):
        q = np.array([pan, lift, elb, wf, 1.571, 0.6])
        p = grasp_point(_kin(sim, q))
        a = _kin(sim, q).site("gripperframe").xmat.reshape(3, 3)[:, 0].copy()
        qs, ep, ea = ik(sim, p, np.r_[Q0[:5], 0.6], axis=a)
        worst = max(worst, ep)
    assert worst < 0.002, f"IK: najgorszy błąd {worst * 1000:.2f} mm"

    # T2, T3: odmowa zamiast cichego obcięcia (cel poza zasięgiem, cel pod stołem)
    for bad in ([0.55, 0.0, 0.10], [0.25, 0.0, -0.02]):
        try:
            plan(sim, Q0, bad)
            raise AssertionError(f"plan przyjął {bad}")
        except ReachError:
            pass

    # T4: automat szczęki (bez fizyki)
    g = ClassicGrip(GripCfg())
    g.mode = "close"
    assert g.step(0.6, [0.0, 0.0, 0.0]) > 0 and g.mode == "close"
    assert g.step(0.6, [1.0, 0.0, 0.0]) > 0 and g.mode == "close"       # jedna szczęka to nie chwyt
    assert g.step(0.6, [1.0, 1.0, 0.0]) == GripCfg().tau_hold and g.mode == "hold"
    g.mode = "open"
    assert g.step(0.5, [0, 0, 0]) < 0 and g.step(0.95, [0, 0, 0]) == 0.0

    # T5: podniesienie piłeczki w kilku miejscach stołu
    res = [pick(sim, b) for b in BALLS]
    for b, (err, lift, touch, hit, srcs) in zip(BALLS, res):
        tag = np.round(b[:2], 2).tolist()
        assert err < 0.003, f"{tag}: pad {err * 1000:.1f} mm od celu"
        assert lift > 0.04, f"{tag}: piłeczka uniesiona tylko o {lift * 1000:.1f} mm"
        assert min(touch[:2]) > GripCfg().f_contact, f"{tag}: brak kontaktu obu szczęk po uniesieniu {touch}"
        assert not hit, f"{tag}: ramię dotknęło stołu: {hit}"
        assert srcs == {"classical:reach", "classical:grip"}, srcs
    print(f"OK: sięganie i chwyt (IK najgorzej {worst * 1000:.2f} mm; "
          + "; ".join(f"{np.round(b[:2], 2).tolist()}: uniesienie {r[1] * 1000:.0f} mm, touch {np.round(r[2][:2], 1).tolist()} N"
                      for b, r in zip(BALLS, res)) + ")")


if __name__ == "__main__":
    main()
