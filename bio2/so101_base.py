"""[bio2: kopia zamrożona z sim/scene.py @ a6922bc, żeby bio2 nie zależało od zmian w sim/]
Scena MuJoCo: oficjalny model SO-101 (TheRobotStudio, onshape-to-robot) + czujniki
w szczękach (odpowiednik campaniform sensilla) + kulka staczająca się z równi.

Kinematyka i serwa STS3215 zostają z pliku producenta (assets/so101_upstream.xml).
Zmieniamy tylko kolizje chwytaka: MuJoCo koliduje meshe jako otoczki wypukłe, a otoczka
nieruchomej szczęki wypełnia całą „paszczę” — kulka nie weszłaby między szczęki.
Dlatego meshe szczęk są tylko wizualne, a kolizję robią pudełka zmierzone z wierzchołków
meshy (sim/probe w historii: wewnętrzna ściana stałej szczęki x≈-0,008…-0,012 m,
ruchomej przy q=0 x≈+0,010…+0,012 m, z = -0,06…-0,10 m w układzie ciała `gripper`).
"""
import os
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPSTREAM = os.path.join(ROOT, "assets", "so101_upstream.xml")
MESHDIR = os.path.join(ROOT, "assets", "so101_meshes")

# --- nasze stałe (nie producenta) ---
BALL_R = 0.025        # kulka 5 cm (miękka piłka gumowa/piankowa)
BALL_MASS = 0.050     # 50 g
TIMESTEP = 0.001      # fizyka 1 ms = krok SNN; pętla sterowania 10 ms
CONTROL_DT = 0.010
GRIP_TORQUE = 3.35    # N·m — forcerange serwa z modelu producenta

SENSORS = ["cs_fixed", "cs_moving", "cs_palm"]   # touch [N] na wewnętrznych powierzchniach


def _sub(parent, tag, **attrs):
    return ET.SubElement(parent, tag, {k: str(v) for k, v in attrs.items()})


def build_xml(ramp_deg=12.0, real_friction=True):
    """real_friction: tarcie wg materiałów (kulka 0,3, pady gumowe 1,2, dłoń PLA 0,35, stół 0,8 —
    MuJoCo bierze maksimum pary). False: wszystkie kontakty kulki μ = 1,0 (priority=1)."""
    tree = ET.parse(UPSTREAM)
    root = tree.getroot()
    root.find("compiler").set("meshdir", MESHDIR)
    _sub(root, "option", timestep=TIMESTEP, integrator="implicitfast", cone="elliptic",
         impratio=10)
    vis = _sub(root, "visual")
    _sub(vis, "global", offwidth=1280, offheight=720)

    asset = root.find("asset")
    _sub(asset, "texture", name="grid", type="2d", builtin="checker", width=512, height=512,
         rgb1=".85 .85 .85", rgb2=".75 .75 .75")
    _sub(asset, "material", name="table", texture="grid", texrepeat="8 8")
    _sub(asset, "material", name="pad", rgba=".9 .2 .2 1")

    world = root.find("worldbody")
    _sub(world, "light", pos="0.3 -0.5 1.2", dir="0 0.4 -1", directional="true")
    _sub(world, "camera", name="overview", pos="0.75 -0.55 0.45", xyaxes="0.6 0.8 0 -0.3 0.2 0.93")
    _sub(world, "geom", name="table", type="plane", size="1 1 0.01", material="table",
         friction="0.8 0.005 0.0001")

    # Równia: zaczyna się 0,62 m od bazy, opada w stronę robota (-x) i kończy na stole przy x=0,45.
    L = 0.16
    a = np.radians(ramp_deg)
    cx = 0.45 + 0.5 * L * np.cos(a)
    cz = 0.5 * L * np.sin(a) - 0.004 * np.cos(a)
    quat = [np.cos(a / 2), 0, -np.sin(a / 2), 0]  # obrót wokół y o -a: wyżej na +x
    _sub(world, "geom", name="ramp", type="box", size=f"{L/2} 0.12 0.004",
         pos=f"{cx} 0 {cz}", quat=" ".join(f"{q:.6f}" for q in quat), rgba=".4 .5 .8 1",
         friction="0.8 0.005 0.0001")
    ball = _sub(world, "body", name="ball",
                pos=f"{0.45 + 0.85*L*np.cos(a)} 0 {0.85*L*np.sin(a) + BALL_R/np.cos(a) + 0.001}")
    _sub(ball, "freejoint", name="ball")
    _sub(ball, "geom", name="ball", type="sphere", size=BALL_R, mass=BALL_MASS, rgba=".1 .7 .2 1",
         condim=6, solref="0.01 1",                                    # miękka piankowa
         **(dict(friction="0.3 0.005 0.0002") if real_friction else dict(friction="1.0 0.005 0.0002", priority=1)))
    # priority=1: wszystkie kontakty kulki używają JEJ tarcia (μ = 1,0) — tarcie padów/dłoni nie gra
    # roli. Próba z μ kulki 0,35 (dłoń śliska, pady gumowe) pogorszyła chwyt (kulka wyciskana z „V”).

    # --- chwytak: meshe szczęk tylko wizualne, kolizja pudełkami ---
    for g in root.iter("geom"):
        if g.get("class") == "collision" and g.get("mesh") in (
                "wrist_roll_follower_so101_v1", "moving_jaw_so101_v1"):
            g.set("contype", "0")
            g.set("conaffinity", "0")
    bodies = {b.get("name"): b for b in root.iter("body")}
    grip, jaw = bodies["gripper"], bodies["moving_jaw_so101_v1"]
    pad = dict(type="box", material="pad", friction="1.2 0.005 0.0001", condim=4, group=1)
    # stała szczęka (układ `gripper`, oś narzędzia = -z): wewnętrzna ściana x = -0,0085
    _sub(grip, "geom", name="jaw_fixed", size="0.003 0.008 0.024", pos="-0.0115 0 -0.076", **pad)
    _sub(grip, "site", name="cs_fixed", type="box", size="0.0045 0.009 0.025",
         pos="-0.0115 0 -0.076", rgba="1 0 0 0.2")
    # „dłoń” w głębi paszczy
    _sub(grip, "geom", name="palm", size="0.016 0.010 0.003", pos="0.006 0 -0.046",
         **dict(pad, friction="0.35 0.005 0.0001") if real_friction else pad)
    _sub(grip, "site", name="cs_palm", type="box", size="0.017 0.011 0.0045",
         pos="0.006 0 -0.046", rgba="1 0 0 0.2")
    # ruchoma szczęka: przy q=0 wewnętrzna ściana x = +0,0095 w układzie `gripper`;
    # przeliczone do układu szczęki (pos 0.0202 0.0188 -0.0234, obrót 90° wokół x)
    _sub(jaw, "geom", name="jaw_moving", size="0.003 0.024 0.008", pos="-0.0077 -0.0526 0.0188", **pad)
    _sub(jaw, "site", name="cs_moving", type="box", size="0.0045 0.025 0.009",
         pos="-0.0077 -0.0526 0.0188", rgba="1 0 0 0.2")
    # punkt celowania: środek paszczy przy rozwarciu 1,2 rad (ściany x = −0,0085 i ≈ +0,093); przy
    # obecnym rozwarciu 0,93 środek leży przy x ≈ 0,032, czyli celujemy ~1 cm w stronę ruchomej szczęki
    # (strojenie robione z tym punktem — nie przesuwać bez ponownego strojenia)
    _sub(grip, "site", name="aim", pos=f"0.042 0 {-0.0490 - BALL_R}", size="0.004", rgba="0 1 1 1")
    # punkt środka chwytu (kulka oparta o dłoń i stałą szczękę po domknięciu)
    _sub(grip, "site", name="grasp", pos=f"0.0155 0 {-0.0490 - BALL_R}", size="0.004", rgba="0 0 1 1")

    # Chwytak w trybie PWM STS3215 (tryb 2, otwarta pętla): moment = 3,35 N·m · u, u ∈ [−1, 1],
    # + = otwieranie (rośnie kąt). Tłumienie stawu 0,6 N·m·s z modelu producenta działa jak SEM.
    act = root.find("actuator")
    for a in list(act):
        if a.get("name") == "gripper":
            act.remove(a)
    _sub(act, "motor", name="gripper", joint="gripper", gear=GRIP_TORQUE, ctrlrange="-1 1")

    sens = _sub(root, "sensor")
    for s in SENSORS:
        _sub(sens, "touch", name=s, site=s)
    return ET.tostring(root, encoding="unicode")


def load(ramp_deg=12.0, real_friction=True):
    m = mujoco.MjModel.from_xml_string(build_xml(ramp_deg, real_friction))
    return m, mujoco.MjData(m)


ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]


def tool_axis(d):
    """Oś narzędzia (od dłoni do czubków szczęk) w świecie = -z ciała `gripper`."""
    return -d.body("gripper").xmat.reshape(3, 3)[:, 2]


def jaw_spread_axis(d):
    """Kierunek rozwierania szczęk = x ciała `gripper`."""
    return d.body("gripper").xmat.reshape(3, 3)[:, 0]


def ik_catch_pose(m, d, r=0.24, h=BALL_R + 0.001, pan=0.0, q0=None):
    """IK dla pozy „bramkarza”: środek chwytu na (r, h) w kierunku `pan`, narzędzie poziomo
    na zewnątrz, szczęki rozwierane poziomo. Zwraca q ramienia (5)."""
    from scipy.optimize import least_squares
    out = np.array([np.cos(pan), np.sin(pan), 0])
    side = np.array([-np.sin(pan), np.cos(pan), 0])
    target = np.array([r * np.cos(pan), r * np.sin(pan), h])
    ids = [m.joint(j).qposadr[0] for j in ARM]

    def res(q):
        d.qpos[ids] = q
        mujoco.mj_kinematics(m, d)
        e = d.site("grasp").xpos - target
        return np.concatenate([e * 10, (tool_axis(d) - out) * 0.5, [abs(jaw_spread_axis(d) @ side) - 1]])

    lo = m.jnt_range[[m.joint(j).id for j in ARM], 0]
    hi = m.jnt_range[[m.joint(j).id for j in ARM], 1]
    q0 = np.array([pan, 0.0, 0.0, 0.0, np.pi / 2]) if q0 is None else q0
    sol = least_squares(res, q0, bounds=(lo, hi))
    return sol.x, np.linalg.norm(res(sol.x)[:3]) / 10
