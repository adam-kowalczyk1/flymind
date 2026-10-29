"""Testy T1–T8 interfejsu SO-101 w MuJoCo — PRZYGOTOWANE, NIEURUCHOMIONE (wymagają osobnej zgody).
Importują mujoco, kompilują model i wykonują krótką symulację headless (bez okien, bez zapisu plików, bez bio2).
Bez flagi zgody skrypt nic nie importuje z mujoco i kończy się kodem 2.
Uruchom (po zgodzie):  .venv/bin/python -I -B flymind/test_so101.py --zgoda-sim"""
import hashlib
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from safety import Command, Limits, SafetyLayer, ranges_from_mjcf  # noqa: E402
from sensory import SensoryGate  # noqa: E402
from so101 import JOINTS, ROOT, UPSTREAM, SO101Sim, integrate_pan  # noqa: E402

STAGE1 = ["bio2/test_cx_causal_memory.py", "bio2/analyze_cx_causal_confirmation.py",
          "bio2/test_analyze_cx_causal_confirmation.py", "bio2/test_cx_causal_runner_safety.py",
          "bio2/results/cx_causal_phase2_20261027_174754/confirmatory_protocol_v4.md", "bio2/brain.py", "bio2/snn.py",
          "bio2/scene2.py", "bio2/so101_base.py", "bio2/vision.py", "bio2/retina.py",
          "bio2/test_cx_working_memory_vs_kalman.py", "bio2/circuit_bio2.json", "assets/so101_upstream.xml"]
Q_OPEN = np.array([0, 0, 0, 0, 0, 0.93])        # poza zerowa ramienia, szczęka rozwarta jak bio2 (q_open 0,93)


def snapshot():
    """T8: hashe Stage 1, git status, zawartość bio2/__pycache__ — porównywane przed i po."""
    h = {p: hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest() for p in STAGE1}
    git = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout
    pc = os.path.join(ROOT, "bio2", "__pycache__")
    return h, git, sorted((f, os.stat(os.path.join(pc, f)).st_mtime) for f in os.listdir(pc))


def contacts(sim):
    """Pary nazw geomów w kontakcie. API pola mjContact (geom vs geom1/geom2) zależy od wersji — niezweryfikowane."""
    c, n = sim.d.contact, sim.d.ncon
    g = np.asarray(c.geom).reshape(-1, 2) if hasattr(c, "geom") else np.c_[c.geom1, c.geom2]
    return [(sim.m.geom(int(a)).name, sim.m.geom(int(b)).name) for a, b in g[:n]]


def i(x):
    """Skalar int z pola akcesora mujoco (pola skalarne bywają tablicami (1,)) albo z enum."""
    return int(np.ravel(x)[0]) if not hasattr(x, "value") else int(x.value)


def azimuth(p):
    return np.arctan2(p[1], p[0])


def t1():
    """Model: kompilacja, krok 1 ms, stawy i zakresy = plik producenta, aktuatory, siatki."""
    sim = SO101Sim(render=False)
    m, mj = sim.m, sim.mj
    assert m.opt.timestep == 0.001 and i(m.opt.integrator) == int(mj.mjtIntegrator.mjINT_IMPLICITFAST)
    assert m.njnt == 7 and [m.joint(i).name for i in range(6)] == list(JOINTS)          # 6 stawów + piłeczka
    assert np.allclose(sim.jrange, ranges_from_mjcf(UPSTREAM))
    assert (sim.crange[:5, 0] >= sim.jrange[:5, 0] - 1e-5).all() and (sim.crange[:5, 1] <= sim.jrange[:5, 1] + 1e-5).all()
    g = m.actuator("gripper")
    assert i(g.trntype) == int(mj.mjtTrn.mjTRN_JOINT) and np.isclose(g.gear[0], 3.35) and np.allclose(g.ctrlrange, [-1, 1])
    assert i(g.biastype) == int(mj.mjtBias.mjBIAS_NONE)                                      # silnik, nie serwo
    assert all(i(m.actuator(n).biastype) == int(mj.mjtBias.mjBIAS_AFFINE) for n in JOINTS[:5])  # serwa pozycyjne
    assert m.nmesh == 13 and m.nsensor == 3
    return "T1 ok"


def t2():
    """Znak bazy: −q pan (PAN_LEFT) obraca chwytak w lewo (+y); to samo dynamicznie z integrate_pan(+ω)."""
    sim = SO101Sim(render=False)
    a_l, a_r = (azimuth(sim.fk(np.r_[p, Q_OPEN[1:]])["gripperframe"]) for p in (-0.3, 0.3))
    assert a_l > a_r
    sim.reset(Q_OPEN)
    a0, tgt = azimuth(sim.fk(sim.observe().q)["gripperframe"]), 0.0
    for _ in range(50):                                           # 0,5 s przy ω = +0,5 rad/s (w lewo)
        tgt = integrate_pan(tgt, 0.5, 0.01)
        sim.act(np.r_[tgt, Q_OPEN[1:5]], 0.0)
        sim.step()
    o = sim.observe()
    assert o.q[0] < -0.15 and azimuth(sim.fk(o.q)["gripperframe"]) > a0 + 0.15
    return f"T2 ok: q_pan {o.q[0]:+.3f} rad po 0,5 s"


def t3():
    """Kontrakt klatki z renderu + orientacja obrazu względem układu kamery (piłeczka w znanym kierunku)."""
    sim = SO101Sim()
    sim.reset(Q_OPEN)
    gate, H, W = SensoryGate(sim.cfg.cam_shape, 0.01, 0.03, 0.05), *sim.cfg.cam_shape
    for k in range(5):
        o = sim.observe()
        assert o.frame.image.dtype == np.uint8 and o.frame.image.shape == (H, W, 3) and o.frame.seq == k
        assert np.isclose(o.frame.t_capture, 0.01 * k) and gate.push(o.frame, o.frame.t_receive).usable
        sim.act(Q_OPEN[:5], 0.0)
        sim.step()
    tanY = np.tan(np.radians(sim.cfg.cam_fovy) / 2)
    res = []
    for dx, dy in ((0, 0), (-0.04, 0), (0, 0.04)):                 # środek, w lewo (−x kamery), w górę (+y kamery)
        k = sim.fk(Q_OPEN)
        R = k["eye_R"]
        sim.reset(Q_OPEN, ball_pos=k["eye"] + 0.25 * k["eye_forward"] + dx * R[:, 0] + dy * R[:, 1])
        img = sim.observe().frame.image.astype(int)
        mask = (img[..., 1] > img[..., 0] + 60) & (img[..., 1] > img[..., 2] + 60)     # zielona piłeczka
        rr, cc = np.nonzero(mask)
        assert rr.size, "piłeczka niewidoczna"
        u_pred = W / 2 * (1 + dx / 0.25 / (tanY * W / H))
        v_pred = H / 2 * (1 - dy / 0.25 / tanY)
        res.append((cc.mean() + 0.5, rr.mean() + 0.5, u_pred, v_pred))
    # środek: ±3 px; przesunięcia względem piłeczki środkowej: ±1,5 px. Maska łapie głównie oświetloną stronę
    # kuli (zmierzone: stałe przesunięcie ok. −2,4 px), różnice centroidów to znoszą.
    (u0, v0, *_), (u1, v1, pu1, pv1), (u2, v2, pu2, pv2) = res
    assert abs(u0 - W / 2) < 3 and abs(v0 - H / 2) < 3
    assert abs((u1 - u0) - (pu1 - W / 2)) < 1.5 and abs(v1 - v0) < 1.5
    assert abs((v2 - v0) - (pv2 - H / 2)) < 1.5 and abs(u2 - u0) < 1.5
    res = [(round(float(a), 1), round(float(b), 1)) for a, b, *_ in res]
    up = sim.fk(Q_OPEN)["eye_R"][:, 1]
    return f"T3 ok: centroidy {res}; oś „góra” kamery w świecie {up.round(2).tolist()} (tylko log)"


def t4():
    """Powtarzalność: te same komendy → bajtowo identyczny qpos."""
    out = []
    for _ in range(2):
        sim = SO101Sim(render=False)
        sim.reset(Q_OPEN)
        for k in range(100):
            sim.act(Q_OPEN[:5] + 0.2 * np.sin(0.05 * k) * np.array([1, 0.5, -0.5, 0.3, 0]), 0.3 * np.sin(0.1 * k))
            sim.step()
        out.append(sim.d.qpos.tobytes())
    assert out[0] == out[1]
    return "T4 ok"


def t5():
    """Warstwa bezpieczeństwa w pętli z fizyką: skok celu → rate; zablokowany łokieć → lead; siła ≤ forcerange."""
    sim = SO101Sim(render=False)
    sim.reset(Q_OPEN)
    sim.m.dof_damping[sim.vadr[2]] = 1e4                          # tylko w tym teście: „zablokowany” łokieć
    safe, flags = SafetyLayer(Limits(ranges_from_mjcf(UPSTREAM))), set()
    for k in range(100):
        o = sim.observe()
        out, tau, fl, per = safe.step(Command(o.t, {1: 1.0, 2: 0.5}, None, {1: "script:t5", 2: "script:t5"}),
                                      o.q, o.t, 0.0)
        flags |= {f for v in per.values() for f in v}
        sim.act(out, tau)
        sim.step()
        assert abs(out[2] - o.q[2]) <= 0.3 + 1e-9
        assert np.abs(sim.d.actuator_force[sim.aid[:5]]).max() <= 3.35 + 1e-6
    assert {"rate", "lead"} <= flags
    return f"T5 ok: flagi {sorted(flags)}"


def t6():
    """Szczęka: τ > 0 zmniejsza q (zamyka), τ < 0 otwiera; piłeczka między padami → nacisk > 0. Grawitacja 0 tylko tu."""
    sim = SO101Sim(render=False)
    sim.reset(Q_OPEN)
    q0 = sim.observe().q[5]
    for _ in range(20):
        sim.act(Q_OPEN[:5], 0.5)
        sim.step()
    q1 = sim.observe().q[5]
    for _ in range(20):
        sim.act(Q_OPEN[:5], -0.5)
        sim.step()
    q2 = sim.observe().q[5]
    assert q1 < q0 and q2 > q1
    sim.m.opt.gravity[:] = 0
    k = sim.fk(Q_OPEN)
    sim.reset(Q_OPEN, ball_pos=(k["cs_fixed"] + k["cs_moving"]) / 2)
    touch = 0.0
    for _ in range(50):
        sim.act(Q_OPEN[:5], 0.5)
        sim.step()
        touch = max(touch, sim.observe().touch.sum())
    assert touch > 0
    return f"T6 ok: q {q0:.3f} → {q1:.3f} (τ+) → {q2:.3f} (τ−); max nacisk {touch:.2f} N (położenie piłeczki do strojenia)"


def t7():
    """Kontakt ramię–stół wykrywany: poza z chwytakiem poniżej stołu wg fk → kontakt z 'table' po kilku krokach."""
    sim = SO101Sim(render=False)
    low = None
    for lift in np.linspace(-1.6, 1.6, 33):
        for elbow in np.linspace(-1.6, 1.6, 33):
            q = np.r_[0, lift, elbow, 0, 0, 0.93]
            if sim.fk(q)["gripperframe"][2] < -0.02:
                low = q
                break
        if low is not None:
            break
    assert low is not None, "brak pozy z chwytakiem pod stołem w siatce"
    sim.reset(Q_OPEN)
    seen = set()
    for _ in range(200):                                         # powolne opuszczanie przez SafetyLayer-free cel
        sim.act(np.clip(low[:5], sim.crange[:5, 0], sim.crange[:5, 1]), 0.0)
        sim.step()
        seen |= {p for p in contacts(sim) if "table" in p and "ball" not in p}   # piłeczka na parkingu się nie liczy
    assert seen
    return f"T7 ok: kontakty ze stołem {sorted(seen)} (tylko pomiar; reakcja warstwy bezpieczeństwa — osobna decyzja)"


def t9():
    """Regresja: zwolnienie starego SO101Sim po utworzeniu nowego nie psuje renderu nowego (błąd mujoco 3.17
    Renderer.close() — zwalnia bufory w bieżącym, cudzym kontekście GL; poprawka w SO101Sim.close)."""
    import gc
    a = SO101Sim()
    a.reset(Q_OPEN)
    ref = a.observe().frame.image
    b = SO101Sim()
    del a
    gc.collect()
    b.reset(Q_OPEN)
    assert np.array_equal(b.observe().frame.image, ref)
    b.close()
    assert b.renderer is None
    return "T9 ok: render po zwolnieniu innego symulatora bez zmian"


def main():
    if "--zgoda-sim" not in sys.argv:
        print("test_so101: NIE uruchomiono — wymaga osobnej zgody i flagi --zgoda-sim (importuje mujoco, symuluje).")
        sys.exit(2)
    before = snapshot()
    for t in (t1, t2, t3, t4, t5, t6, t7, t9):
        print(t())
    assert snapshot() == before, "T8: zmiana w Stage 1 / git status / bio2/__pycache__"
    print("T8 ok: Stage 1, git status i bio2/__pycache__ bez zmian")


if __name__ == "__main__":
    main()
