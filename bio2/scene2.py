"""Scena v2 (Explory, „bio2”): SO-101 z czujnikami nacisku w szczękach (z sim/scene.py, sprawdzone w v1–v3)
+ kamera „oko w dłoni” + piłeczka tocząca się w poprzek pola widzenia + ruchoma przesłona (mocap)
+ sonda kalibracyjna czujników (mocap, kulka 5 cm na sztywnym uchwycie).

Układ (metry, baza ramienia w (0, 0)): ramię w pozie „bramkarza” (IK z sim/scene.py, paszcza przy x ≈ 0,28),
tor piłeczki x = BALL_X, przesłona przy x = OCC_X między kamerą a torem.
"""
import os
import sys
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sim"))
import scene  # noqa: E402  (model SO-101 + pady + czujniki touch)

# --- nasze stałe sceny ---
BALL_X = 0.44          # tor piłeczki
OCC_X = 0.37           # płaszczyzna przesłony
OCC_SIZE = (0.005, 0.07, 0.05)   # pół-wymiary: grubość, szerokość 14 cm, wysokość 10 cm
CAM_W, CAM_H = 128, 96           # obraz z kamery (FlyRetinaFilter w Etapie 2 zredukuje do 32×24)
CAM_FOVY = 70.0
PARK = (0.0, 0.8, 0.05)          # pozycja przesłony poza sceną
ROLL_MU = 1e-5                   # opór toczenia kulka/stół [m] (nasza stała)


def build_xml(real_friction=True):
    root = ET.fromstring(scene.build_xml(real_friction=real_friction))
    world = root.find("worldbody")
    world.remove(next(g for g in world.iter("geom") if g.get("name") == "ramp"))   # równia z v1 — tu zbędna
    # opór toczenia 1e-5 m (nasza stała; z v1 było 2e-4 m → kulka 0,1 m/s stawała po ~2 s)
    for g in root.iter("geom"):
        if g.get("name") in ("ball", "table"):
            mu = g.get("friction").split()
            g.set("friction", f"{mu[0]} {mu[1]} {ROLL_MU}")
    grip = next(b for b in root.iter("body") if b.get("name") == "gripper")
    # kamera w układzie `gripper`: oś narzędzia = −z (kamera MuJoCo patrzy wzdłuż swojego −z),
    # lokalne +y chwytaka wskazuje w dół, więc obrót o 180° wokół z daje obraz „głową do góry”
    ET.SubElement(grip, "camera", dict(name="eye", pos="0.016 -0.03 -0.03", quat="0 0 0 1", fovy=str(CAM_FOVY)))
    occ = ET.SubElement(world, "body", dict(name="occluder", mocap="true", pos=" ".join(map(str, PARK))))
    ET.SubElement(occ, "geom", dict(name="occluder", type="box", size=" ".join(map(str, OCC_SIZE)),
                                    rgba="0.35 0.25 0.2 1"))
    # sonda: swobodna kulka jak piłeczka (stawiana między szczękami w teście czujników)
    probe = ET.SubElement(world, "body", dict(name="probe", pos=f"0 0.9 {scene.BALL_R}"))
    ET.SubElement(probe, "freejoint", dict(name="probe"))
    ET.SubElement(probe, "geom", dict(name="probe", type="sphere", size=str(scene.BALL_R), mass=str(scene.BALL_MASS),
                                      condim="6", solref="0.01 1", friction=f"0.3 0.005 {ROLL_MU}",
                                      rgba="0.9 0.9 0.2 1"))
    return ET.tostring(root, encoding="unicode")


def load(real_friction=True):
    m = mujoco.MjModel.from_xml_string(build_xml(real_friction))
    d = mujoco.MjData(m)
    m.vis.global_.offwidth, m.vis.global_.offheight = max(CAM_W, 1280), max(CAM_H, 720)
    return m, d


def eye_renderer(m):
    """Renderer kamery „eye” bez znaczników pomocniczych (siatkówka widzi tylko scenę). Bez cieni, odbić
    i nieba: sama mapa cieni kosztowała 4,4 ms z 7,7 ms renderu (zmierzone), a ruchomy cień zakłócałby
    filtr ruchu siatkówki."""
    r = mujoco.Renderer(m, CAM_H, CAM_W)
    for f in (mujoco.mjtRndFlag.mjRND_SHADOW, mujoco.mjtRndFlag.mjRND_REFLECTION, mujoco.mjtRndFlag.mjRND_SKYBOX):
        r.scene.flags[f] = False
    opt = mujoco.MjvOption()
    opt.sitegroup[:] = 0
    return r, opt


def place_free(m, d, joint, pos):
    """Postaw swobodne ciało (freejoint) w pos, w spoczynku."""
    a, v = m.joint(joint).qposadr[0], m.joint(joint).dofadr[0]
    d.qpos[a:a + 7] = [*pos, 1, 0, 0, 0]
    d.qvel[v:v + 6] = 0


def set_mocap(m, d, body, pos):
    d.mocap_pos[m.body(body).mocapid[0]] = pos


def reset_scene(m, d, ball_y0=0.22, ball_vy=-0.10, q_open=0.93):
    """Ramię w pozie chwytu, szczęki otwarte, piłeczka na torze z prędkością toczenia (ω = v/R)."""
    q, err = scene.ik_catch_pose(m, d, r=0.28)
    mujoco.mj_resetData(m, d)
    d.qpos[:5] = q
    d.qpos[5] = q_open
    d.ctrl[:5] = q
    bj, bv = m.joint("ball").qposadr[0], m.joint("ball").dofadr[0]
    d.qpos[bj:bj + 7] = [BALL_X, ball_y0, scene.BALL_R, 1, 0, 0, 0]
    d.qvel[bv:bv + 6] = [0, ball_vy, 0, -ball_vy / scene.BALL_R, 0, 0]   # toczenie bez poślizgu
    set_mocap(m, d, "occluder", PARK)
    mujoco.mj_forward(m, d)
    return q, err
