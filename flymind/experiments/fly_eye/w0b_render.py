"""W0b — nowe sceny dla W1b (LOOP_TARGET_W1b.md): przedmiot cube_L JASNY (materiał hard_slick .95) albo BRĄZOWY (mid .7 .45 .2),
przesunięty z osi kamery, ruch w 4 strony kadru (pliki {materiał}_{R|L|U|D}.npz). Ta sama kamera, poza, światło, czas (50 + 50 + 25 klatek co 20 ms) i zapis co w0_render.py. SYMULACJA, ruch kinematyczny.
  R w prawo kadru, L w lewo, U w górę kadru, D w dół kadru; droga 10 cm (R/L) i 8 cm (U/D) w 1 s; środek toru przesunięty o (+2 cm, +2 cm).
w0b_render.py OUT_DIR"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from w0_render import HI, N_MOV, N_POST, N_PRE, OUT, RH1, SEED, oh, vm  # noqa: E402


def main(out):
    os.makedirs(out, exist_ok=True)
    for mat in ("hard_slick", "mid"):
        render(out, mat)


def render(out, mat):
    import mujoco
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

    def shoot(p):
        d.qpos[sim.qadr] = q0
        d.qpos[o["adr"]:o["adr"] + 7] = [*p, *o["rest_quat"]]
        mujoco.mj_forward(m, d)
        r.update_scene(d, camera="eye")
        sm = r.render().reshape(OUT[0], HI[0] // OUT[0], OUT[1], HI[1] // OUT[1], 3).mean((1, 3))
        return np.clip(sm @ RH1, 0, 255).astype(np.uint8), sm.astype(np.uint8)

    s = np.r_[np.zeros(N_PRE), np.linspace(0, 1, N_MOV), np.ones(N_POST)]
    for name, ax, half in (("R", right, 0.05), ("L", -right, 0.05), ("U", up, 0.04), ("D", -up, 0.04)):
        L, C = zip(*[shoot(c + ax * (-half + 2 * half * x)) for x in s])
        np.savez_compressed(os.path.join(out, f"{mat}_{name}.npz"), lum=np.array(L), rgb=np.array(C), dt=0.02, n_pre=N_PRE, n_mov=N_MOV,
                            fovy_deg=vm.ENC.fovy_deg, seed=SEED)
        print(mat, name, np.array(L).shape, "jasność min/max", int(np.min(L)), int(np.max(L)))
    r.close()


if __name__ == "__main__":
    main(sys.argv[1])
