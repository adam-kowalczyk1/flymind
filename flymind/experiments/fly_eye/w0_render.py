"""W0 — klatki z kamery nadgarstka SO-101 (MuJoCo) dla atlasu W1. SYMULACJA, ruch kinematyczny (bez fizyki).

Scena: istniejący świat object_handling (blat 0,75 szarości), jeden przedmiot cube_L z materiału hard_grip (ciemny, 0,15),
ramię w pozie patrzenia vision_manipulation.Q_SURVEY. Kamera „eye” 70° (pion), światło jak vision_manipulation.Eye.
Każda scena: 50 klatek bez ruchu (adaptacja), 50 klatek ruchu, 25 bez ruchu; krok 20 ms (jak trening flyvis).
  S1 spokoj     — przedmiot stoi w środku kadru;
  S2 bok        — przedmiot jedzie w prawo w kadrze, 10 cm w 1 s;  S2r bok_wstecz — to samo w lewo (kontrola);
  S3 zblizanie  — przedmiot unosi się wzdłuż osi kamery od blatu do 6 cm pod kamerą (bodziec zbliżania, nienaturalny);
  S4 ramie      — przedmiot stoi, obraca się podstawa ramienia o 0,3 rad (ruch całego obrazu).
Zapis: jasność „jak Rh1” (wagi R,G,B z step3_wiring/eye_bench.py) 120×160 uint8 + RGB 120×160 uint8.
Uruchomienie z katalogu tymczasowego (MuJoCo pisze MUJOCO_LOG.TXT): w0_render.py OUT_DIR
"""
import os
import sys

import numpy as np

FM = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, FM)
import object_handling as oh  # noqa: E402
import vision_manipulation as vm  # noqa: E402

RH1 = np.array([0.05, 0.55, 0.40])          # jak eye_bench.RH1
SEED = 23504001                              # World wymaga ziarna; przedmiot stawiam ręcznie, generator nieużywany
N_PRE, N_MOV, N_POST = 50, 50, 25
HI, OUT = (480, 640), (120, 160)


def main(out):
    import mujoco
    os.makedirs(out, exist_ok=True)
    w = oh.World([("cube_L", "hard_grip")], SEED)
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
    hit = E + fwd * (E[2] / -fwd[2])                       # gdzie oś kamery trafia w blat
    right = R[:, 0].copy(); right[2] = 0; right /= np.linalg.norm(right)
    z0 = o["rest_z"]
    quat = o["rest_quat"]

    def pose(p):
        d.qpos[o["adr"]:o["adr"] + 7] = [*p, *quat]

    def shoot(q, p):
        d.qpos[sim.qadr] = q
        pose(p)
        mujoco.mj_forward(m, d)
        r.update_scene(d, camera="eye")
        img = r.render()
        sm = img.reshape(OUT[0], HI[0] // OUT[0], OUT[1], HI[1] // OUT[1], 3).mean((1, 3))
        return np.clip(sm @ RH1, 0, 255).astype(np.uint8), sm.astype(np.uint8)

    c = np.array([hit[0], hit[1], z0])
    s = np.r_[np.zeros(N_PRE), np.linspace(0, 1, N_MOV), np.ones(N_POST)]
    top = E - fwd * 0.0                                      # docelowo 6 cm przed kamerą wzdłuż osi
    scenes = {
        "S1_spokoj": [(q0, c) for _ in s],
        "S2_bok": [(q0, c + right * (-0.05 + 0.10 * x)) for x in s],
        "S2r_bok_wstecz": [(q0, c + right * (0.05 - 0.10 * x)) for x in s],
        "S3_zblizanie": [(q0, c + (top + fwd * 0.06 - c) * x) for x in s],
        "S4_ramie": [(q0 + np.r_[0.3 * x, np.zeros(5)], c) for x in s],
    }
    for name, seq in scenes.items():
        L, C = zip(*[shoot(q, p) for q, p in seq])
        np.savez_compressed(os.path.join(out, f"{name}.npz"), lum=np.array(L), rgb=np.array(C), dt=0.02,
                            n_pre=N_PRE, n_mov=N_MOV, fovy_deg=vm.ENC.fovy_deg, seed=SEED)
        print(name, np.array(L).shape, "jasność min/max", int(np.min(L)), int(np.max(L)))
    r.close()


if __name__ == "__main__":
    main(sys.argv[1])
