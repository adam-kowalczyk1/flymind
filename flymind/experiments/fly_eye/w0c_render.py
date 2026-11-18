"""W0c — nowe sceny do powtórzenia W7-kamera (LOOP_TARGET_W8.md). Te same 5 typów co W0 (spokój, bok, bok wstecz, zbliżanie,
obrót ramienia), ale: przedmiot jasny (hard_slick) albo brązowy (mid) zamiast czarnego, tor przesunięty o (+2 cm, +2 cm) w kadrze.
Kamera, poza, światło, czas, długości ruchów i zapis jak w0_render.py. SYMULACJA, ruch kinematyczny. w0c_render.py OUT_DIR
Zapis: OUT_DIR/{hard_slick|mid}/{S1_spokoj,S2_bok,S2r_bok_wstecz,S3_zblizanie,S4_ramie}.npz"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from w0_render import HI, N_MOV, N_POST, N_PRE, OUT, RH1, SEED, oh, vm  # noqa: E402


def render(out, mat):
    import mujoco
    os.makedirs(out, exist_ok=True)
    w = oh.World([("cube_L", mat)], SEED)
    sim, o = w.sim, w.objs[0]
    m, d = sim.m, sim.d
    m.geom_rgba[m.geom("mark_zone").id] = 0
    m.vis.headlight.ambient[:], m.vis.headlight.diffuse[:] = 0.6, 0.4
    r = mujoco.Renderer(m, *HI)
    for f in (mujoco.mjtRndFlag.mjRND_SHADOW, mujoco.mjtRndFlag.mjRND_REFLECTION, mujoco.mjtRndFlag.mjRND_SKYBOX):
        r.scene.flags[f] = False
    q0 = np.array(vm.Q_SURVEY)
    sim.reset(q0)
    k = sim.fk(q0)
    E, R = k["eye"], k["eye_R"]
    fwd = R @ [0, 0, -1.0]
    hit = E + fwd * (E[2] / -fwd[2])
    unit = lambda a: a / np.linalg.norm(a)  # noqa: E731
    right = unit(np.r_[R[:2, 0], 0]); up = unit(np.r_[R[:2, 1], 0])
    c = np.array([hit[0], hit[1], o["rest_z"]]) + 0.02 * right + 0.02 * up
    goal = E + fwd * 0.06 + 0.02 * R[:, 0] + 0.02 * R[:, 1]     # 6 cm przed kamerą, przesunięte tak samo w kadrze

    def shoot(q, p):
        d.qpos[sim.qadr] = q
        d.qpos[o["adr"]:o["adr"] + 7] = [*p, *o["rest_quat"]]
        mujoco.mj_forward(m, d)
        r.update_scene(d, camera="eye")
        sm = r.render().reshape(OUT[0], HI[0] // OUT[0], OUT[1], HI[1] // OUT[1], 3).mean((1, 3))
        return np.clip(sm @ RH1, 0, 255).astype(np.uint8), sm.astype(np.uint8)

    s = np.r_[np.zeros(N_PRE), np.linspace(0, 1, N_MOV), np.ones(N_POST)]
    scenes = {
        "S1_spokoj": [(q0, c) for _ in s],
        "S2_bok": [(q0, c + right * (-0.05 + 0.10 * x)) for x in s],
        "S2r_bok_wstecz": [(q0, c + right * (0.05 - 0.10 * x)) for x in s],
        "S3_zblizanie": [(q0, c + (goal - c) * x) for x in s],
        "S4_ramie": [(q0 + np.r_[0.3 * x, np.zeros(5)], c) for x in s],
    }
    for name, seq in scenes.items():
        L, C = zip(*[shoot(q, p) for q, p in seq])
        np.savez_compressed(os.path.join(out, f"{name}.npz"), lum=np.array(L), rgb=np.array(C), dt=0.02, n_pre=N_PRE, n_mov=N_MOV,
                            fovy_deg=vm.ENC.fovy_deg, seed=SEED)
        print(mat, name, np.array(L).shape, int(np.min(L)), int(np.max(L)))
    r.close()


if __name__ == "__main__":
    for mat in ("hard_slick", "mid"):
        render(os.path.join(sys.argv[1], mat), mat)
