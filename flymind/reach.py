"""flymind/reach.py — KLASYCZNE sięganie ramienia SO-101: IK, trajektoria kartezjańska, odstęp od stołu. Bez bio2.

To NIE jest model biologiczny. Muszka nie ma ramienia, więc geometria ruchu jest inżynierią: każda komenda stąd ma
źródło "classical:reach" i przechodzi przez safety.SafetyLayer jak wszystko inne.

  ik(sim, p, q0)         → (q[6], błąd pozycji [m], błąd osi [rad]) — tłumione najmniejsze kwadraty na stawach 0–3,
                           cel: punkt chwytu (środek między padami szczęk) w p, oś podejścia (x ramki gripperframe) = axis
  clearance(sim, q)      → najniższy punkt padów/dłoni nad stołem [m] (dokładne narożniki pudełek, nie środki)
  plan(sim, q0, p_goal)  → punkty q na odcinku prostym w przestrzeni kartezjańskiej; odmowa (ReachError) zamiast
                           cichego obcięcia, gdy cel nieosiągalny, poza zakresem stawów albo za blisko stołu
  ticks(path, ...)       → cele na takty 10 ms z prędkością ≤ v_max (SafetyLayer i tak to egzekwuje)
"""
import math
from dataclasses import dataclass

import numpy as np

DOWN = (0.0, 0.0, -1.0)
PADS = ("jaw_fixed", "jaw_moving", "palm")          # pudełka kontaktowe z so101.build_mjcf
IK_JOINTS = 4                                        # pan, lift, elbow, wrist_flex; wrist_roll i szczęka stałe


class ReachError(ValueError):
    pass


@dataclass(frozen=True)
class ReachCfg:
    z_min: float = 0.005        # m: najniższy narożnik padu nad stołem (z = 0); wybór projektu
    tol_pos: float = 0.002      # m
    tol_axis: float = 0.05      # rad
    iters: int = 300
    damping: float = 0.02       # λ w DLS
    w_axis: float = 0.05        # m/rad: waga błędu osi względem pozycji
    margin: float = 0.05        # rad od krańca zakresu (jak safety.Limits.margin)
    step_m: float = 0.005       # m między punktami trajektorii
    v_max: float = 1.0          # rad/s na staw (SafetyLayer: 1,5)
    dt: float = 0.01            # s, takt sterowania


def _kin(sim, q):
    """Kinematyka q[6] na osobnym MjData (stan symulacji nietknięty), z mj_comPos dla jakobianów."""
    k = sim._kin
    k.qpos[:] = sim.d.qpos
    k.qpos[sim.qadr] = q
    sim.mj.mj_kinematics(sim.m, k)
    sim.mj.mj_comPos(sim.m, k)
    return k


def point_of(k, point):
    """Punkt prowadzony przez IK: "grasp" = środek między padami albo nazwa miejsca (np. "cs_fixed")."""
    return grasp_point(k) if point == "grasp" else k.site(point).xpos


def grasp_point(k):
    """Środek między padami szczęk [m] przy bieżącym kącie szczęki. Ruchoma szczęka obraca się, więc punkt zależy od
    q[5]; do chwytu kuli lepiej prowadzić stałą szczękę (fixed_pad_target, point="cs_fixed")."""
    return 0.5 * (k.site("cs_fixed").xpos + k.site("cs_moving").xpos)


def ik(sim, p, q0, axis=DOWN, cfg=ReachCfg(), point="grasp"):
    p, a_des = np.asarray(p, float), np.asarray(axis, float) / np.linalg.norm(axis)
    q = np.asarray(q0, float).copy()
    lo, hi = sim.jrange[:IK_JOINTS, 0] + cfg.margin, sim.jrange[:IK_JOINTS, 1] - cfg.margin
    cols = sim.vadr[:IK_JOINTS]
    jp, jr = np.zeros((3, sim.m.nv)), np.zeros((3, sim.m.nv))
    sid = sim.m.site("gripperframe").id
    for _ in range(cfg.iters):
        k = _kin(sim, q)
        gp, a = point_of(k, point), k.site("gripperframe").xmat.reshape(3, 3)[:, 0]
        e_p, e_a = p - gp, np.cross(a, a_des)
        if np.linalg.norm(e_p) < cfg.tol_pos and np.linalg.norm(e_a) < math.sin(cfg.tol_axis):
            break
        # jakobian punktu chwytu ≈ jakobian gripperframe przesunięty o ramię (gp − gf): v = v_gf + ω × (gp − gf)
        sim.mj.mj_jacSite(sim.m, k, jp, jr, sid)
        r = gp - k.site("gripperframe").xpos
        Jp = jp[:, cols] - np.cross(r, jr[:, cols].T).T
        Ja = jr[:, cols]
        J = np.vstack([Jp, cfg.w_axis * Ja])
        e = np.concatenate([e_p, cfg.w_axis * e_a])
        dq = J.T @ np.linalg.solve(J @ J.T + cfg.damping ** 2 * np.eye(6), e)
        q[:IK_JOINTS] = np.clip(q[:IK_JOINTS] + dq, lo, hi)
    k = _kin(sim, q)
    a = k.site("gripperframe").xmat.reshape(3, 3)[:, 0]
    return q, float(np.linalg.norm(p - point_of(k, point))), float(math.acos(np.clip(a @ a_des, -1, 1)))


def clearance(sim, q):
    """Najniższe z narożników pudełek PADS nad stołem [m] — kontakt ze stołem zaczyna się przy 0."""
    k = _kin(sim, q)
    zs = []
    for g in PADS:
        geom = k.geom(g)
        R, c, h = geom.xmat.reshape(3, 3), geom.xpos, sim.m.geom(g).size
        zs.append(c[2] - np.abs(R[2] * h).sum())   # najniższy narożnik pudełka: z środka − Σ|R_zi · h_i|
    return float(min(zs))


def plan(sim, q0, p_goal, axis=DOWN, cfg=ReachCfg(), jaw_open=None, point="grasp"):
    """Prosty odcinek od bieżącego punktu chwytu do p_goal; każdy punkt sprawdzony (IK, zakres, stół).
    IK przy kącie szczęki q0[5]; jaw_open: odstęp od stołu sprawdzany też przy tym rozwarciu."""
    q0 = np.asarray(q0, float)
    p0 = point_of(_kin(sim, q0), point)
    n = max(1, int(math.ceil(np.linalg.norm(np.asarray(p_goal) - p0) / cfg.step_m)))
    path, q = [], q0.copy()
    for i in range(1, n + 1):
        p = p0 + (np.asarray(p_goal, float) - p0) * i / n
        q, ep, ea = ik(sim, p, q, axis, cfg, point)
        if ep > cfg.tol_pos or ea > cfg.tol_axis:
            raise ReachError(f"nieosiągalny punkt {np.round(p, 3).tolist()} (błąd {ep * 1000:.1f} mm, {math.degrees(ea):.1f}°)")
        cz = clearance(sim, q) if jaw_open is None else min(clearance(sim, q), clearance(sim, np.r_[q[:5], jaw_open]))
        if cz < cfg.z_min:
            raise ReachError(f"za blisko stołu w {np.round(p, 3).tolist()}: {cz * 1000:.1f} mm < {cfg.z_min * 1000:.1f} mm")
        path.append(q.copy())
    return path


def fixed_pad_target(sim, q, center, radius, gap=0.008, dz=0.005, pad_half=0.003):
    """Cel miejsca cs_fixed przy chwycie obiektu kulistego: stała szczęka o `gap` od powierzchni, po stronie wyznaczonej
    przez kierunek ruchoma → stała w pozie q (poziomo), środek padu dz nad środkiem obiektu. Ruchoma szczęka obraca
    się przy zamykaniu, więc prowadzimy stałą: zamykanie dopycha obiekt do niej."""
    k = _kin(sim, q)
    n = k.site("cs_fixed").xpos - k.site("cs_moving").xpos
    n[2] = 0.0
    n /= np.linalg.norm(n)
    return np.asarray(center, float) + n * (radius + pad_half + gap) + [0.0, 0.0, dz]


def plan_joint(sim, q0, p_goal, axis=DOWN, cfg=ReachCfg(), jaw_open=None, n=20, point="grasp"):
    """Przejście do pozy nad celem interpolacją w stawach (orientacja może się zmieniać po drodze), z kontrolą stołu
    w n punktach. Do dużych zmian orientacji; schodzenie do obiektu — plan() po prostej."""
    q0 = np.asarray(q0, float)
    q1, ep, ea = ik(sim, p_goal, q0, axis, cfg, point)
    if ep > cfg.tol_pos or ea > cfg.tol_axis:
        raise ReachError(f"nieosiągalny {np.round(p_goal, 3).tolist()} (błąd {ep * 1000:.1f} mm, {math.degrees(ea):.1f}°)")
    path = [q0 + (q1 - q0) * i / n for i in range(1, n + 1)]
    for q in path:
        cz = clearance(sim, q) if jaw_open is None else min(clearance(sim, q), clearance(sim, np.r_[q[:5], jaw_open]))
        if cz < cfg.z_min:
            raise ReachError(f"przejście za blisko stołu: {cz * 1000:.1f} mm")
    return path


def ticks(path, q_start, cfg=ReachCfg()):
    """Cele [5] na kolejne takty: między punktami liniowo, |Δq| na takt ≤ v_max·dt."""
    out, prev = [], np.asarray(q_start, float)[:5]
    for q in path:
        q = np.asarray(q, float)[:5]
        n = max(1, int(math.ceil(np.abs(q - prev).max() / (cfg.v_max * cfg.dt))))
        out += [prev + (q - prev) * i / n for i in range(1, n + 1)]
        prev = q
    return out
