"""flymind/so101.py — interfejs SO-101 w MuJoCo (krok 9). Bez bio2; plik producenta tylko czytany.

Dwie warstwy:
  build_mjcf(cfg) → str   czysty XML (stdlib ElementTree), BEZ mujoco: plik producenta + zmiany w pamięci
  SO101Sim(cfg)           jedyne miejsce z `import mujoco` (import leniwy) — reszta flymind działa bez tej zależności

Kolejność i jednostki (zawsze po NAZWACH stawów/aktuatorów/czujników, nigdy po indeksach qpos):
  q[6]      [rad]   shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper
  qd[6]     [rad/s] jw.
  touch[3]  [N]     cs_fixed, cs_moving, cs_palm (czujniki touch na padach szczęk i dłoni)
  act(q_target[5] [rad], jaw_torque [N·m, + = zamykanie]) — dokładnie wyjście flymind/safety.py; symulator NIE
            powtarza ograniczeń warstwy bezpieczeństwa, tylko odrzuca komendy łamiące kontrakt (SimError).

Mapowania (weryfikacja statyczna — patrz komentarze przy stałych; dynamicznie: T2 i T6 w test_so101.py):
  baza:     PAN_LEFT = −1: obrót „w lewo” (+ω dekodera) = malejące q shoulder_pan
  szczęka:  ctrl_gripper = JAW_CLOSE · τ / grip_torque, JAW_CLOSE = −1 (ctrl > 0 → +q → otwieranie)
"""
import math
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import numpy as np

from sensory import Frame

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPSTREAM = os.path.join(ROOT, "assets", "so101_upstream.xml")
MESHDIR = os.path.join(ROOT, "assets", "so101_meshes")      # XML producenta ma meshdir="assets" → assets/assets (nie istnieje)
ARM = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll")
JOINTS = ARM + ("gripper",)
TOUCH = ("cs_fixed", "cs_moving", "cs_palm")
SITES = ("gripperframe",) + TOUCH

# Staw shoulder_pan: oś z ciała `shoulder`, którego quat (0, 0, −1, 0) = obrót 180° wokół y → oś = −z świata.
# +q obraca więc zgodnie z ruchem wskazówek zegara patrząc z góry: od +x (przód) w stronę −y (prawo). Lewo = −q.
# Zgodne z bio2 agent.py: dpsi = −(q_pan − q_prev) „+ w lewo” i ctrl[0] − ω·dt.
PAN_LEFT = -1.0
# Staw gripper: oś z ciała szczęki; ciało obrócone o 90° wokół x względem `gripper`, więc oś = y chwytaka.
# Środek padu ruchomej szczęki (pos szczęki 0,0202 + obrót punktu (−0,0077; −0,0526)) ma w układzie `gripper`
# x(q) = 0,0202 − 0,0077·cos q + 0,0526·sin q — rośnie z q, czyli oddala się od stałej szczęki (x = −0,0115).
# +q = otwieranie; zakres [−0,175; 1,745] (q≈0 domknięte) jest z tym zgodny. Silnik MuJoCo: moment = gear·ctrl
# wzdłuż osi stawu, więc ctrl > 0 otwiera. Zamykanie (τ > 0 w dekoderze) → ctrl < 0.
JAW_CLOSE = -1.0


class SimError(RuntimeError):
    pass


def integrate_pan(target_prev, omega_left, dt):
    """Cel bazy [rad] z prędkości dekodera (+ w lewo) — całkowanie jak bio2 (ctrl[0] − ω·dt)."""
    return target_prev + PAN_LEFT * omega_left * dt


@dataclass(frozen=True)
class SceneCfg:
    upstream: str = UPSTREAM
    meshdir: str = MESHDIR
    # fizyka: 1 ms = krok SNN (pętla 10 ms = 10 kroków); implicitfast/elliptic/impratio jak bio2 so101_base.py
    timestep: float = 0.001
    n_sub: int = 10
    integrator: str = "implicitfast"
    cone: str = "elliptic"
    impratio: float = 10.0
    # chwytak w trybie PWM STS3215 (bio2 so101_base.py): silnik, gear = forcerange producenta 3,35 N·m, ctrl ∈ [−1, 1]
    grip_torque: float = 3.35
    # kamera „eye” w układzie ciała `gripper` (bio2 scene2.py; orientacja obrazu niezweryfikowana statycznie → T3)
    cam_pos: tuple = (0.016, -0.03, -0.03)
    cam_quat: tuple = (0.0, 0.0, 0.0, 1.0)
    cam_fovy: float = 70.0
    cam_shape: tuple = (96, 128)       # (H, W)
    # scena (bio2 so101_base.py/scene2.py): stół z = 0, piłeczka 5 cm / 50 g, tło za stołem dla kontrastu obrazu
    table_friction: tuple = (0.8, 0.005, 1e-5)
    ball_r: float = 0.025
    ball_mass: float = 0.050
    ball_friction: tuple = (0.3, 0.005, 1e-5)
    ball_park: tuple = (0.0, 0.9, 0.025)   # domyślnie poza przestrzenią roboczą: brak ukrytego zadania
    backdrop: bool = True
    distractor_r: float = 0.0          # > 0: druga zielona kula „distractor” (V5 v2), parkowana jak piłeczka; 0 = XML bez zmian


def _sub(parent, tag, **attrs):
    return ET.SubElement(parent, tag, {k: " ".join(map(str, v)) if isinstance(v, tuple) else str(v)
                                       for k, v in attrs.items()})


def build_mjcf(cfg=SceneCfg()):
    """XML sceny jako string. Plik producenta tylko czytany; brak oczekiwanych elementów → SimError."""
    for p in (cfg.upstream, cfg.meshdir):
        if not os.path.exists(p):
            raise SimError(f"brak {p}")
    root = ET.parse(cfg.upstream).getroot()
    joints = {j.get("name"): j for j in root.find("worldbody").iter("joint")}   # bez szablonów z <default>
    acts = {a.get("name"): a for a in root.find("actuator")}
    bodies = {b.get("name"): b for b in root.iter("body")}
    miss = [n for n in JOINTS if n not in joints or n not in acts] + \
           [b for b in ("gripper", "moving_jaw_so101_v1") if b not in bodies]
    if miss or set(joints) != set(JOINTS):
        raise SimError(f"model producenta niezgodny: brak {miss}, stawy {sorted(joints)}")
    meshes = [m.get("file") for m in root.iter("mesh")]
    absent = [f for f in meshes if not os.path.isfile(os.path.join(cfg.meshdir, f))]
    if absent:
        raise SimError(f"brak siatek w {cfg.meshdir}: {absent}")

    root.find("compiler").set("meshdir", cfg.meshdir)
    _sub(root, "option", timestep=cfg.timestep, integrator=cfg.integrator, cone=cfg.cone, impratio=cfg.impratio)
    asset, world = root.find("asset"), root.find("worldbody")
    _sub(asset, "texture", name="grid", type="2d", builtin="checker", width=512, height=512,
         rgb1=".85 .85 .85", rgb2=".75 .75 .75")
    _sub(asset, "material", name="table", texture="grid", texrepeat="8 8")
    _sub(asset, "material", name="pad", rgba=".9 .2 .2 1")
    _sub(world, "light", pos="0.3 -0.5 1.2", dir="0 0.4 -1", directional="true")
    _sub(world, "geom", name="table", type="plane", size="1 1 0.01", material="table", friction=cfg.table_friction)
    if cfg.backdrop:
        _sub(world, "geom", name="backdrop", type="box", size="0.01 3 1.5", pos="1.8 0 1.0",
             rgba="0.75 0.75 0.75 1", contype=0, conaffinity=0)
    ball = _sub(world, "body", name="ball", pos=cfg.ball_park)
    _sub(ball, "freejoint", name="ball")
    _sub(ball, "geom", name="ball", type="sphere", size=cfg.ball_r, mass=cfg.ball_mass, rgba=".1 .7 .2 1",
         condim=6, solref="0.01 1", friction=cfg.ball_friction)
    if cfg.distractor_r > 0:
        dis = _sub(world, "body", name="distractor", pos=(0.0, -0.9, cfg.distractor_r))
        _sub(dis, "freejoint", name="distractor")
        _sub(dis, "geom", name="distractor", type="sphere", size=cfg.distractor_r, mass=cfg.ball_mass, rgba=".1 .7 .2 1",
             condim=6, solref="0.01 1", friction=cfg.ball_friction)

    # chwytak (bio2 so101_base.py): siatki szczęk tylko wizualne, kontakt przez pudełka-pady z czujnikami touch
    for g in root.iter("geom"):
        if g.get("class") == "collision" and g.get("mesh") in ("wrist_roll_follower_so101_v1", "moving_jaw_so101_v1"):
            g.set("contype", "0")
            g.set("conaffinity", "0")
    grip, jaw = bodies["gripper"], bodies["moving_jaw_so101_v1"]
    pad = dict(type="box", material="pad", friction="1.2 0.005 0.0001", condim=4, group=1)
    # (ciało, geom, site, rozmiar padu, rozmiar objętości czujnika, pozycja) — wartości 1:1 z bio2 so101_base.py
    for body, geom, site, size, ssize, pos, extra in (
            (grip, "jaw_fixed", "cs_fixed", "0.003 0.008 0.024", "0.0045 0.009 0.025", "-0.0115 0 -0.076", {}),
            (grip, "palm", "cs_palm", "0.016 0.010 0.003", "0.017 0.011 0.0045", "0.006 0 -0.046",
             dict(friction="0.35 0.005 0.0001")),
            (jaw, "jaw_moving", "cs_moving", "0.003 0.024 0.008", "0.0045 0.025 0.009", "-0.0077 -0.0526 0.0188", {})):
        _sub(body, "geom", name=geom, size=size, pos=pos, **{**pad, **extra})
        _sub(body, "site", name=site, type="box", size=ssize, pos=pos, rgba="1 0 0 0.2")
    _sub(grip, "camera", name="eye", pos=cfg.cam_pos, quat=cfg.cam_quat, fovy=cfg.cam_fovy)

    act = root.find("actuator")
    act.remove(acts["gripper"])        # pozycyjny aktuator producenta → silnik momentowy (tylko w pamięci)
    _sub(act, "motor", name="gripper", joint="gripper", gear=cfg.grip_torque, ctrlrange="-1 1")
    sens = _sub(root, "sensor")
    for s in TOUCH:
        _sub(sens, "touch", name=s, site=s)
    return ET.tostring(root, encoding="unicode")


@dataclass(frozen=True)
class Obs:
    frame: Frame                       # obraz z kamery „eye” (image None, jeśli render zawiódł)
    q: np.ndarray                      # [6] rad, kolejność JOINTS
    qd: np.ndarray                     # [6] rad/s
    touch: np.ndarray                  # [3] N, kolejność TOUCH
    t: float                           # s, czas symulacji


@dataclass
class SO101Sim:
    cfg: SceneCfg = SceneCfg()
    render: bool = True
    stats: dict = field(default_factory=dict)

    def __post_init__(self):
        import mujoco                  # leniwie: konfiguracja i kontrakty importują się bez mujoco
        self.mj = mujoco
        self.m = mujoco.MjModel.from_xml_string(build_mjcf(self.cfg))
        self.d = mujoco.MjData(self.m)
        self._kin = mujoco.MjData(self.m)                       # osobne dane do fk(): nie rusza stanu symulacji
        m = self.m
        self.qadr = np.array([m.joint(n).qposadr[0] for n in JOINTS])
        self.vadr = np.array([m.joint(n).dofadr[0] for n in JOINTS])
        self.aid = np.array([m.actuator(n).id for n in JOINTS])
        self.jrange = np.array([m.joint(n).range for n in JOINTS])
        self.crange = np.array([m.actuator(n).ctrlrange for n in JOINTS])
        self.renderer = self.opt = None
        if self.render:
            H, W = self.cfg.cam_shape
            self.renderer = mujoco.Renderer(m, H, W)
            for f in (mujoco.mjtRndFlag.mjRND_SHADOW, mujoco.mjtRndFlag.mjRND_REFLECTION, mujoco.mjtRndFlag.mjRND_SKYBOX):
                self.renderer.scene.flags[f] = False                # bez cieni/odbić/nieba (jak bio2: ruchomy cień myli siatkówkę)
            self.opt = mujoco.MjvOption()
            self.opt.sitegroup[:] = 0                               # siatkówka nie widzi znaczników pomocniczych
        self.stats = dict(steps=0, frames=0, render_fail=0, rejected=0, ignored_stopped=0)
        self.last_error = None
        self.stopped = None
        self.seq = 0

    # ---------------- stan ----------------
    def reset(self, q0, ball_pos=None, distractor_pos=None):
        """Ustaw pozycje stawów q0[6] (w zakresach) i piłeczkę (x, y, z) albo parking; prędkości 0; cele = q0."""
        q0 = np.asarray(q0, float)
        if q0.shape != (6,) or not np.isfinite(q0).all() or \
                ((q0 < self.jrange[:, 0]) | (q0 > self.jrange[:, 1])).any():
            raise SimError(f"q0 poza zakresem lub zły kształt: {q0}")
        mj, m, d = self.mj, self.m, self.d
        mj.mj_resetData(m, d)
        d.qpos[self.qadr] = q0
        b = m.joint("ball").qposadr[0]
        d.qpos[b:b + 7] = [*(self.cfg.ball_park if ball_pos is None else ball_pos), 1, 0, 0, 0]
        if distractor_pos is not None:
            if self.cfg.distractor_r <= 0:
                raise SimError("distractor_pos bez distractor_r > 0 w SceneCfg")
            b = m.joint("distractor").qposadr[0]
            d.qpos[b:b + 7] = [*distractor_pos, 1, 0, 0, 0]
        d.ctrl[self.aid[:5]] = np.clip(q0[:5], self.crange[:5, 0], self.crange[:5, 1])
        d.ctrl[self.aid[5]] = 0.0
        mj.mj_forward(m, d)
        self.stopped, self.seq = None, 0

    def observe(self):
        """Obserwacja w chwili d.time. Render zawodzi → image None (bramka sensoryczna oznaczy no_image)."""
        d, img = self.d, None
        if self.renderer is not None:
            try:
                self.renderer.update_scene(d, camera="eye", scene_option=self.opt)
                img = self.renderer.render().copy()
            except Exception as e:     # noqa: BLE001 — utrata obrazu jest danymi, nie awarią pętli; powód zapisany
                self.stats["render_fail"] += 1
                self.last_error = f"render: {e!r}"
        q = d.qpos[self.qadr].copy()
        self.stats["frames"] += 1
        f = Frame(self.seq, float(d.time), float(d.time), img, proprio=q.copy(), source="sim")
        self.seq += 1
        return Obs(f, q, d.qvel[self.vadr].copy(), np.array([d.sensor(s).data[0] for s in TOUCH]), float(d.time))

    def close(self):
        """Zwolnienie renderera we WŁASNYM kontekście GL. mujoco 3.17 Renderer.close() zwalnia MjrContext w bieżącym
        kontekście, nie swoim: przy kilku rendererach kasuje bufory innego, który potem po cichu zwraca śmieci
        (zmierzone: 0,03 ms zamiast ok. 3,5 ms na klatkę, inna jasność, bez wyjątku). _gl_context to prywatne API."""
        r = getattr(self, "renderer", None)
        if r is not None:
            if r._gl_context is not None:
                r._gl_context.make_current()
            r.close()
            self.renderer = None

    def __del__(self):
        self.close()                   # także przy zwolnieniu przez GC (np. nadpisanie zmiennej nowym SO101Sim)

    # ---------------- komendy ----------------
    def act(self, q_target, jaw_torque):
        """Zastosuj wyjście warstwy bezpieczeństwa. Zwraca True, jeśli zastosowano; False w stanie stop.
        Komenda łamiąca kontrakt (kształt, NaN, poza ctrlrange, |τ| > grip_torque) → SimError, ctrl bez zmian."""
        q_target = np.asarray(q_target, float)
        lo, hi = self.crange[:5, 0], self.crange[:5, 1]
        why = ("kształt" if q_target.shape != (5,) else
               "NaN/inf" if not (np.isfinite(q_target).all() and math.isfinite(jaw_torque)) else
               f"cel poza ctrlrange {q_target.round(4).tolist()}" if ((q_target < lo) | (q_target > hi)).any() else
               f"|τ| {jaw_torque} > {self.cfg.grip_torque}" if abs(jaw_torque) > self.cfg.grip_torque else None)
        if why:
            self.stats["rejected"] += 1
            raise SimError("komenda odrzucona: " + why)
        if self.stopped:
            self.stats["ignored_stopped"] += 1
            return False
        self.d.ctrl[self.aid[:5]] = q_target
        self.d.ctrl[self.aid[5]] = JAW_CLOSE * jaw_torque / self.cfg.grip_torque
        return True

    def stop(self, reason):
        """Żądanie zatrzymania (zatrzaśnięte): cele = bieżące pozycje (w ctrlrange), szczęka 0 N·m; act() ignorowane."""
        q = self.d.qpos[self.qadr[:5]]
        self.d.ctrl[self.aid[:5]] = np.clip(q, self.crange[:5, 0], self.crange[:5, 1])
        self.d.ctrl[self.aid[5]] = 0.0
        self.stopped = reason

    def release(self, reason):
        self.stats.setdefault("released", []).append((self.stopped, reason))
        self.stopped = None

    def step(self):
        """Jeden takt sterowania = n_sub kroków fizyki. Niestabilność (NaN, ostrzeżenie BADQACC) → stop + SimError."""
        mj, m, d = self.mj, self.m, self.d
        for _ in range(self.cfg.n_sub):
            mj.mj_step(m, d)
        self.stats["steps"] += 1
        bad = d.warning[mj.mjtWarning.mjWARN_BADQACC].number
        if bad or not (np.isfinite(d.qpos).all() and np.isfinite(d.qvel).all()):
            self.last_error = f"fizyka niestabilna (BADQACC={bad}) w t={d.time:.3f}"
            self.stop(self.last_error)
            raise SimError(self.last_error)

    # ---------------- kinematyka ----------------
    def fk(self, q):
        """Kinematyka prosta dla q[6] na osobnym MjData (stan symulacji nietknięty): pozycje miejsc SITES [m]
        oraz kamery (pozycja, macierz obrotu eye_R, oś widzenia eye_forward = −z kamery) w układzie świata."""
        k, mj = self._kin, self.mj
        q = np.asarray(q, float)
        if q.shape != (6,) or not np.isfinite(q).all():
            raise SimError(f"fk: zły q {q}")
        k.qpos[:] = self.d.qpos
        k.qpos[self.qadr] = q
        mj.mj_kinematics(self.m, k)
        mj.mj_camlight(self.m, k)      # pozy kamer liczy mj_camlight, nie mj_kinematics (bez tego eye = 0)
        out = {s: k.site(s).xpos.copy() for s in SITES}
        R = k.cam("eye").xmat.reshape(3, 3).copy()       # kolumny: x (prawo obrazu), y (góra obrazu), z (do tyłu)
        out["eye"], out["eye_R"], out["eye_forward"] = k.cam("eye").xpos.copy(), R, -R[:, 2]
        return out
