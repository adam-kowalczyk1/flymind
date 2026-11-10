"""flymind/object_handling.py — benchmark obsługi RÓŻNYCH przedmiotów: chwyt w strefie centralnej → pudełko, w kółko.

Osobny eksperyment (nie Etap 1): własna scena, własne wyniki w results/object_handling/. Wspólny kod (so101, reach,
grip, safety, pick_place) jest tylko importowany — żaden z tych plików nie jest zmieniany. To NIE jest sterowanie
muszki: komendy mają źródło "classical:object_handling" i przechodzą przez safety.SafetyLayer.

Trzy rozdzielone role (opis: OBJECT_HANDLING_BENCHMARK.md):
  Controller  widzi TYLKO: enkodery q/qd, dotyk 3 padów, czas, percept-wyrocznię (prostokąt z góry + wysokość) przy
              starcie próby oraz własny model kinematyczny ramienia. Nie zna masy, tarcia, kształtu ani losu przedmiotu.
  World       symulator + podajnik przedmiotów (kolejka, spawn) + ewaluator na stanie prawdziwym (kontakty, pozycje).
              Jedyny zapis pozy przedmiotu w całej serii to jego pojawienie się w strefie (raz na przedmiot).
  summarize   analiza po próbie.

Uruchom:  .venv/bin/python -I -B flymind/object_handling.py single --set base --poses 3 --tag B_base
          .venv/bin/python -I -B flymind/object_handling.py series --set base --perm 1 --tag C_perm1
"""
import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, replace

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import so101  # noqa: E402
from grip import ClassicGrip, GripCfg  # noqa: E402
from pick_place import Fail, profile  # noqa: E402
from reach import ReachCfg, ReachError, _kin, clearance, ik, plan  # noqa: E402
from safety import Command, Limits, SafetyLayer, ranges_from_mjcf  # noqa: E402
from so101 import ROOT, UPSTREAM, SceneCfg, SimError, SO101Sim  # noqa: E402

SRC = "classical:object_handling"
PHASES = ("approach", "grasp", "lift", "transport", "place", "return")
STAGES = ("grasp", "lift", "transport", "release", "placed")
OUT = os.path.join(ROOT, "flymind", "results", "object_handling")
PAD_HALF = 0.003                                       # połowa grubości padu (so101.build_mjcf)
PADS = ("jaw_fixed", "jaw_moving", "palm")
ARMSET = set(PADS) | {"arm"}

# ---------------------------------------------------------------- katalog (zamrożony przed pomiarami) -------------
# Wszystkie przedmioty są SZTYWNE. „Materiał” = gęstość + tarcie + stała czasowa kontaktu (solref); nazwy w komentarzu
# mówią tylko, jakiemu rzeczywistemu materiałowi odpowiada rząd wielkości parametrów. Geomy przedmiotów mają
# priority=1, więc w każdym kontakcie (pad, blat, pudełko) obowiązuje tarcie i solref PRZEDMIOTU.
MATERIALS = {
    "hard_grip":  dict(density=1150, mu=1.00, solref=(0.004, 1), rgba=".15 .15 .15 1"),   # twarda guma / ebonit
    "hard_slick": dict(density=1410, mu=0.20, solref=(0.004, 1), rgba=".95 .95 .9 1"),    # gładkie tworzywo typu POM
    "heavy":      dict(density=7850, mu=0.50, solref=(0.004, 1), rgba=".55 .6 .65 1"),    # stal
    # katalog v2: solref 0,020 → 0,004. Przy v1 (0,020) i masie kilku gramów pady PRZENIKAŁY przez przedmiot (szczęka
    # dochodziła do krańca), bo sztywność kontaktu MuJoCo skaluje się z masą — artefakt symulatora, nie cecha materiału.
    "light":      dict(density=120,  mu=0.60, solref=(0.004, 1), rgba=".95 .8 .3 1"),     # balsa / sztywna pianka
    "mid":        dict(density=700,  mu=0.50, solref=(0.010, 1), rgba=".7 .45 .2 1"),     # drewno
    # tylko zestaw trudny (Etap D)
    "ice":        dict(density=920,  mu=0.05, solref=(0.004, 1), rgba=".6 .85 .95 1"),    # prawie bez tarcia
    "tungsten":   dict(density=19300, mu=0.50, solref=(0.004, 1), rgba=".3 .3 .35 1"),    # bardzo ciężki
}
LY = (0.7071068, 0.0, 0.7071068, 0.0)                  # obrót 90° wokół y: oś z bryły leży poziomo
WEDGE = "-.015 -.02 0  -.015 .02 0  .015 -.02 0  .015 .02 0  -.015 -.02 .03  -.015 .02 .03"
# geoms: (typ, połówki wymiarów [m], opcjonalnie pozycja w ciele); rest: orientacja spoczynkowa; condim 6 = z tarciem toczenia
SHAPES = {
    "cube_S": dict(cat="małe", geoms=[("box", (.010, .010, .010))]),
    "cube_M": dict(cat="średnie", geoms=[("box", (.015, .015, .015))]),
    "cube_L": dict(cat="duże", geoms=[("box", (.0225, .0225, .0225))]),
    "cyl":    dict(cat="wąskie (walec stojący)", geoms=[("cylinder", (.015, .025))], condim=6),
    "sphere": dict(cat="okrągłe", geoms=[("sphere", (.0175,))], condim=6),
    "flat":   dict(cat="płaskie", geoms=[("box", (.025, .0175, .005))]),
    "long":   dict(cat="wydłużone", geoms=[("box", (.040, .010, .010))]),
    "L":      dict(cat="nieregularne", geoms=[("box", (.0225, .0075, .010)), ("box", (.0075, .010, .010), (.015, .0175, 0))]),
    "wedge":  dict(cat="nieregularne", geoms=[("mesh", WEDGE)]),
    # zestaw trudny (Etap D) — nieużywany przy pracy nad kontrolerem
    "cube_XS":    dict(cat="bardzo małe", geoms=[("box", (.006, .006, .006))]),
    "plate_thin": dict(cat="bardzo płaskie", geoms=[("box", (.025, .0175, .003))]),
    "cube_XL":    dict(cat="za duże", geoms=[("box", (.0275, .0275, .0275))]),
    "cyl_lying":  dict(cat="walec leżący", geoms=[("cylinder", (.015, .025))], rest=LY, condim=6),
    "cyl_thin":   dict(cat="wysoki cienki walec", geoms=[("cylinder", (.008, .030))], condim=6),
    "capsule":    dict(cat="kapsuła leżąca", geoms=[("capsule", (.0125, .020))], rest=LY, condim=6),
    "egg":        dict(cat="elipsoida", geoms=[("ellipsoid", (.0225, .016, .016))], condim=6),
    "hammer":     dict(cat="środek masy poza środkiem", geoms=[("box", (.035, .006, .006)), ("box", (.010, .0175, .010), (.035, 0, .004))]),
    "bar_long":   dict(cat="bardzo długie", geoms=[("box", (.060, .010, .010))]),
}
BASE_SHAPES = ("cube_S", "cube_M", "cube_L", "cyl", "sphere", "flat", "long", "L", "wedge")
BASE_MATS = ("hard_grip", "hard_slick", "heavy", "light", "mid")
SETS = {
    "base": [(s, m) for s in BASE_SHAPES for m in BASE_MATS],
    "hard": [("cube_XS", "mid"), ("cube_XS", "hard_slick"), ("plate_thin", "mid"), ("cube_XL", "light"),
             ("cyl_lying", "mid"), ("cyl_lying", "hard_slick"), ("cyl_thin", "mid"), ("capsule", "hard_grip"),
             ("egg", "mid"), ("egg", "hard_slick"), ("hammer", "mid"), ("bar_long", "heavy"), ("sphere", "ice"),
             ("cube_M", "ice"), ("cube_M", "tungsten")],
}


@dataclass(frozen=True)
class Scene:
    """Geometria stanowiska [m]. Kontroler zna z niej tylko nominalne miejsca (strefa, pudełko, punkty zrzutu)."""
    zone: tuple = (0.165, 0.215, -0.03, 0.07)          # x0, x1, y0, y1: gdzie może się pojawić środek przedmiotu
    zone_exit: float = 0.06                            # przenoszony przedmiot musi tyle wyjechać poza strefę przed spawnem
    box_xy: tuple = (0.10, -0.17)                      # środek pudełka
    box_in: tuple = (0.09, 0.08)                       # połówki wnętrza (18 × 16 cm)
    wall: float = 0.004
    floor: float = 0.003
    rim: float = 0.035                                 # górna krawędź ścianek nad blatem
    box_density: float = 1050.0                        # tworzywo typu ABS → ok. 0,19 kg; pudełko NIE jest przymocowane
    box_mu: float = 0.8
    drops: tuple = ((-.04, .025), (0, .025), (.04, .025), (-.04, -.015), (0, -.015), (.04, -.015))   # względem środka
    spawn_margin: float = 0.025                        # minimalny odstęp nowego przedmiotu od wszystkiego (ramię, pudełko, inne)


@dataclass(frozen=True)
class Crit:
    """Kryteria ewaluatora — ustalone przed pomiarami, takie same dla wszystkich przedmiotów."""
    grasp_ticks: int = 10          # ×10 ms ciągłego kontaktu z OBU padami szczęk = chwyt
    lift_dz: float = 0.02          # m: środek masy tyle nad pozycją spoczynkową, bez kontaktu z blatem/pudełkiem/innymi
    lost_ticks: int = 5            # ×10 ms bez żadnego kontaktu z ramieniem przed komendą otwarcia = upuszczony
    release_ticks: int = 5         # ×10 ms bez kontaktu z ramieniem po komendzie otwarcia = zwolniony
    settle_s: float = 1.5          # s po komendzie otwarcia: ocena umieszczenia
    v_tol: float = 0.02            # m/s
    w_tol: float = 1.0             # rad/s
    percept_delay: float = 0.3     # s po pojawieniu się, zanim kontroler dostanie percept
    max_attempts: int = 2          # prób chwytu na przedmiot; potem zostaje tam, gdzie leży („porzucony”)
    final_idle: float = 2.0        # s bezczynności przed końcowym spisem


@dataclass(frozen=True)
class OHCfg:
    """Kontroler. Wartości ruchu i szczęki jak bazowy Etap 1 (PPCfg/GripCfg); nowe: dobór rozwarcia i obrotu nadgarstka."""
    home: tuple = (-0.1, -0.8, 0.4, 1.3, 1.571, 0.93)   # pady ok. 15 cm nad blatem: ponad każdym przedmiotem w strefie
    gap: float = 0.004             # stała szczęka od ściany przedmiotu przy zejściu
    jaw_clear: float = 0.006       # zapas po stronie ruchomej szczęki
    pad_bottom: float = 0.007      # najniższy narożnik padów nad blatem w chwycie (reach z_min = 5 mm)
    palm_clear: float = 0.044      # przedmiot wyższy niż to: pady wyżej, żeby dłoń nie siadła na przedmiocie
    h_above: float = 0.02          # pady tyle nad wierzchem przedmiotu przed zejściem
    carry_clear: float = 0.020     # spód przedmiotu nad krawędzią pudełka w transporcie i przy zrzucie (5,5 cm nad blatem)
    v_max: float = 1.0
    a_max: float = 4.0
    settle_tol: float = 0.02
    settle_max: float = 0.5
    close_max: float = 2.0
    hold_settle: float = 0.10
    f_grip: float = 1.0
    open_max: float = 1.0
    jaw_tol: float = 0.08          # rad: rozwarcie uznane za osiągnięte
    jaw_release: float = 0.15      # rad ponad kąt trzymania = szczęka puściła
    idle_max: float = 12.0         # s czekania na przedmiot, potem koniec serii


# ---------------------------------------------------------------- scena -------------------------------------------
def scene_xml(base, items, sc):
    """XML sceny Etapu 1 (so101.build_mjcf, w pamięci) + pudełko, przedmioty, kamera poglądowa, znacznik strefy."""
    root = ET.fromstring(base)
    world, asset, sub = root.find("worldbody"), root.find("asset"), so101._sub
    C, T = np.array([0.66, -0.50, 0.46]), np.array([0.13, -0.07, 0.02])
    f = (T - C) / np.linalg.norm(T - C)
    r = np.cross(f, [0, 0, 1.0])
    r /= np.linalg.norm(r)
    sub(world, "camera", name="overview", pos=tuple(C), xyaxes=tuple(np.r_[r, np.cross(r, f)]))
    z = sc.zone
    sub(world, "geom", name="mark_zone", type="box", size=((z[1] - z[0]) / 2, (z[3] - z[2]) / 2, 0.0002),
        pos=((z[0] + z[1]) / 2, (z[2] + z[3]) / 2, 0.0002), rgba=".95 .75 .1 .5", contype=0, conaffinity=0)
    bx = sub(world, "body", name="box", pos=(*sc.box_xy, 0.0002))
    sub(bx, "freejoint", name="box")
    (ax, ay), t, hw = sc.box_in, sc.wall, (sc.rim - sc.floor) / 2
    for name, size, pos in (("floor", (ax + t, ay + t, sc.floor / 2), (0, 0, sc.floor / 2)),
                            ("wall_xp", (t / 2, ay + t, hw), (ax + t / 2, 0, sc.floor + hw)),
                            ("wall_xm", (t / 2, ay + t, hw), (-ax - t / 2, 0, sc.floor + hw)),
                            ("wall_yp", (ax, t / 2, hw), (0, ay + t / 2, sc.floor + hw)),
                            ("wall_ym", (ax, t / 2, hw), (0, -ay - t / 2, sc.floor + hw))):
        sub(bx, "geom", name="box_" + name, type="box", size=size, pos=pos, density=sc.box_density,
            friction=(sc.box_mu, 0.005, 1e-4), condim=4, rgba=".35 .5 .75 .6")
    for i, (shape, mat) in enumerate(items):
        S, M = SHAPES[shape], MATERIALS[mat]
        b = sub(world, "body", name=f"o{i}", pos=(-0.45 - 0.12 * (i // 8), -0.42 + 0.12 * (i % 8), 0.05),
                quat=S.get("rest", (1, 0, 0, 0)))                      # parking poza zasięgiem; z poprawiane po kompilacji
        sub(b, "freejoint", name=f"o{i}")
        for j, (typ, size, *pos) in enumerate(S["geoms"]):
            a = dict(name=f"o{i}_{j}", density=M["density"], friction=(M["mu"], 0.005, 1e-4), priority=1,
                     condim=S.get("condim", 4), solref=M["solref"], rgba=M["rgba"], pos=pos[0] if pos else (0, 0, 0))
            if typ == "mesh":
                if asset.find(f"mesh[@name='{shape}']") is None:
                    sub(asset, "mesh", name=shape, vertex=size)
                sub(b, "geom", type="mesh", mesh=shape, **a)
            else:
                sub(b, "geom", type=typ, size=size, **a)
    return ET.tostring(root, encoding="unicode")


def make_sim(xml_fn):
    """SO101Sim z rozszerzonym XML, bez zmiany so101.py: build_mjcf podmieniony tylko na czas konstrukcji."""
    orig = so101.build_mjcf
    so101.build_mjcf = lambda cfg: xml_fn(orig(cfg))
    try:
        return SO101Sim(SceneCfg(backdrop=False), render=False)
    finally:
        so101.build_mjcf = orig


def _unit_sphere(n_lat=13, n_lon=48):
    p = [(0, 0, 1.0), (0, 0, -1.0)]
    for a in np.linspace(-math.pi / 2, math.pi / 2, n_lat)[1:-1]:
        p += [(math.cos(a) * math.cos(b), math.cos(a) * math.sin(b), math.sin(a))
              for b in np.linspace(0, 2 * math.pi, n_lon, endpoint=False)]
    return np.array(p)


US = _unit_sphere()
CORNERS = np.array([(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], float)
CIRC = np.array([(math.cos(b), math.sin(b), 0) for b in np.linspace(0, 2 * math.pi, 48, endpoint=False)])


def quat_mat(mj, q):
    R = np.zeros(9)
    mj.mju_quat2Mat(R, np.asarray(q, float))
    return R.reshape(3, 3)


def cloud(mj, m, bid):
    """Punkty powierzchni bryły w układzie ciała — ze SKOMPILOWANEGO modelu (te same geomy, które liczy fizyka)."""
    G, out = mj.mjtGeom, []
    for g in range(m.body_geomadr[bid], m.body_geomadr[bid] + m.body_geomnum[bid]):
        t, s = m.geom_type[g], m.geom_size[g]
        if t == G.mjGEOM_BOX:
            P = CORNERS * s
        elif t == G.mjGEOM_SPHERE:
            P = US * s[0]
        elif t == G.mjGEOM_ELLIPSOID:
            P = US * s
        elif t == G.mjGEOM_CYLINDER:
            P = np.vstack([CIRC * s[0] + [0, 0, s[1]], CIRC * s[0] - [0, 0, s[1]]])
        elif t == G.mjGEOM_CAPSULE:
            P = np.vstack([US * s[0] + [0, 0, s[1]], US * s[0] - [0, 0, s[1]]])
        elif t == G.mjGEOM_MESH:
            i = m.geom_dataid[g]
            P = m.mesh_vert[m.mesh_vertadr[i]:m.mesh_vertadr[i] + m.mesh_vertnum[i]]
        else:
            raise SimError(f"nieobsługiwany geom {t}")
        out.append(P @ quat_mat(mj, m.geom_quat[g]).T + m.geom_pos[g])
    return np.vstack(out)


def obb(P):
    """Percept-wyrocznia z chmury punktów w świecie: najmniejszy prostokąt widziany z góry + wysokość. l ≥ w [m],
    yaw = kierunek dłuższego boku [rad]. Tyle dałby idealny czujnik głębi nad stołem; NIE jest to wynik kamery."""
    th = np.radians(np.arange(0, 180, 0.5))
    u = np.c_[np.cos(th), np.sin(th)]
    pr = P[:, :2] @ u.T
    lo, hi = pr.min(0), pr.max(0)
    k = int(np.argmin((hi - lo)[:180] * (hi - lo)[180:]))
    a, b = hi[k] - lo[k], hi[k + 180] - lo[k + 180]
    c = u[k] * (hi[k] + lo[k]) / 2 + u[k + 180] * (hi[k + 180] + lo[k + 180]) / 2
    l, w, yaw = (a, b, th[k]) if a >= b else (b, a, th[k + 180])
    return dict(x=float(c[0]), y=float(c[1]), yaw=float(yaw % math.pi), l=float(l), w=float(w), h=float(P[:, 2].max()))


# ---------------------------------------------------------------- świat: fizyka + podajnik + ewaluator -------------
class World:
    def __init__(self, items, seed, scene=Scene(), crit=Crit(), home=OHCfg.home, record=None, record_every=4):
        self.scene, self.crit, self.seed = scene, crit, seed
        self.rng = np.random.default_rng(seed)
        self.sim = make_sim(lambda base: scene_xml(base, items, scene))
        mj, m = self.sim.mj, self.sim.m
        self.objs = []
        for i, (shape, mat) in enumerate(items):
            bid = m.body(f"o{i}").id
            j = m.body_jntadr[bid]
            o = dict(uid=i, shape=shape, material=mat, cat=SHAPES[shape]["cat"], bid=bid, adr=int(m.jnt_qposadr[j]),
                     dof=int(m.jnt_dofadr[j]), cloud=cloud(mj, m, bid), mass=float(m.body_mass[bid]),
                     mu=MATERIALS[mat]["mu"], density=MATERIALS[mat]["density"],
                     geoms=list(range(m.body_geomadr[bid], m.body_geomadr[bid] + m.body_geomnum[bid])),
                     t_spawn=None, attempts=0, pen_mm=0.0, pad_ticks=0, free_ticks=0, both_prev=False, bumped=[],
                     t={}, truth={k: False for k in STAGES}, dropped=None, abandoned=False, evaluated=False)
            o["rest_quat"] = m.qpos0[o["adr"] + 3:o["adr"] + 7].copy()
            o["rest_z"] = float(-(o["cloud"] @ quat_mat(mj, o["rest_quat"]).T)[:, 2].min()) + 0.0003
            m.qpos0[o["adr"] + 2] = o["rest_z"]                          # parking: leży na blacie, nie spada
            self.objs.append(o)
        self.sim.reset(np.array(home))
        self.box_bid = m.body("box").id
        self.box0 = self.sim.d.xpos[self.box_bid].copy()
        self.box_drift = 0.0
        self.lab = []
        for g in range(m.ngeom):
            name, body = m.geom(g).name, m.body(m.geom_bodyid[g]).name
            self.lab.append("table" if name == "table" else "box" if body == "box" else
                            ("obj", int(body[1:])) if body[:1] == "o" and body[1:].isdigit() else
                            name if name in PADS else
                            None if name in ("ball", "backdrop") or name.startswith("mark") else "arm")
        self.solid = [g for g in range(m.ngeom) if self.lab[g] not in (None, "table")
                      and (m.geom_contype[g] or m.geom_conaffinity[g])]
        self.scratch = mj.MjData(m)
        self.next, self.pending, self.t_request = 0, True, 0.0
        self.current = self.carried = self.releasing = None
        self.phase = "idle"
        self.events, self.pairs = [], set()
        self.unwanted = dict(arm_table=0, arm_box=0, armlink_object=0, pad_other_object=0, carried_hit=0)
        self.stats = dict(max_qd=0.0, max_qdd=0.0, v_exceed_ticks=0, spawn_rejects=0, spawn_wait_ticks=0, pose_writes=0)
        self._qd_prev = np.zeros(5)
        self.obs = self.sim.observe()
        self.record, self.record_every, self.nframe = record, record_every, 0
        if record:
            os.makedirs(record, exist_ok=True)
            self.renderer = mj.Renderer(m, 480, 640)

    # ---- interfejs kontrolera: tylko step(), percept(), done(), phase ----
    def step(self, q_t, tau):
        try:
            if not self.sim.act(q_t, tau):
                raise Fail("sim_error", f"symulator zatrzymany: {self.sim.stopped}")
            self.sim.step()
        except SimError as e:
            raise Fail("sim_error", str(e)) from e
        self.obs = self.sim.observe()
        self._evaluate(tau)
        return self.obs

    def percept(self):
        o, t = self.current, self.sim.sim_time
        if o is None or t < o["t_spawn"] + self.crit.percept_delay:
            return None
        if o["attempts"] >= self.crit.max_attempts:              # wyczerpane próby: zostaje, gdzie leży
            o["abandoned"] = True
            self.current = None
            self._log("abandoned", o)
            self._request()
            return None
        if not o["attempts"]:
            o["z0"] = float(self.sim.d.xipos[o["bid"]][2])
        o["attempts"] += 1
        p = obb(self._cloud_world(o))
        self._log("percept", o, attempt=o["attempts"], **{k: round(v, 5) for k, v in p.items()})
        return p

    def done(self):
        return self.current is None and (not self.pending or self.next >= len(self.objs))

    # ---- podajnik ----
    def _request(self):
        if self.next < len(self.objs) and not self.pending:
            self.pending, self.t_request = True, self.sim.sim_time

    def _free(self, o, pos, quat):
        """Czy przedmiot o postawiony w (pos, quat) ma ≥ spawn_margin do ramienia, pudełka i wszystkich wprowadzonych
        przedmiotów. Liczone na kopii stanu (scratch) — symulacja nietknięta."""
        mj, m, k = self.sim.mj, self.sim.m, self.scratch
        k.qpos[:] = self.sim.d.qpos
        k.qpos[o["adr"]:o["adr"] + 7] = [*pos, *quat]
        mj.mj_kinematics(m, k)
        live = {x["uid"] for x in self.objs if x["t_spawn"] is not None}
        mg = self.scene.spawn_margin
        for h in self.solid:
            lab = self.lab[h]
            if isinstance(lab, tuple) and lab[1] not in live:
                continue
            if any(mj.mj_geomDistance(m, k, g, h, mg, None) < mg for g in o["geoms"]):
                return False
        return True

    def _try_spawn(self):
        o, z, d, mj = self.objs[self.next], self.scene.zone, self.sim.d, self.sim.mj
        if self.carried is not None:                               # przenoszony przedmiot jeszcze nad strefą: czekaj
            c, e = d.xipos[self.carried["bid"]], self.scene.zone_exit
            if z[0] - e <= c[0] <= z[1] + e and z[2] - e <= c[1] <= z[3] + e:
                self.stats["spawn_wait_ticks"] += 1
                return
        x, y, yaw = self.rng.uniform(z[0], z[1]), self.rng.uniform(z[2], z[3]), self.rng.uniform(0, math.pi)
        quat = np.zeros(4)
        mj.mju_mulQuat(quat, np.array([math.cos(yaw / 2), 0, 0, math.sin(yaw / 2)]), o["rest_quat"])
        if not self._free(o, (x, y, o["rest_z"]), quat):
            self.stats["spawn_rejects"] += 1
            return
        assert o["t_spawn"] is None, "pozę przedmiotu wolno zapisać tylko raz (pojawienie się)"
        d.qpos[o["adr"]:o["adr"] + 7] = [x, y, o["rest_z"], *quat]
        d.qvel[o["dof"]:o["dof"] + 6] = 0
        self.stats["pose_writes"] += 1
        o["t_spawn"] = self.sim.sim_time
        o["spawn"] = dict(x=float(x), y=float(y), yaw=float(yaw), wait_s=self.sim.sim_time - self.t_request)
        self.current, self.pending, self.next = o, False, self.next + 1
        self._log("spawn", o, **{k: round(v, 4) for k, v in o["spawn"].items()})

    # ---- ewaluator (stan prawdziwy) ----
    def _log(self, ev, o=None, **kw):
        self.events.append(dict(t=round(self.sim.sim_time, 3), ev=ev, phase=self.phase,
                                **({"uid": o["uid"], "obj": f"{o['shape']}/{o['material']}"} if o else {}), **kw))

    def _cloud_world(self, o):
        d = self.sim.d
        return o["cloud"] @ d.xmat[o["bid"]].reshape(3, 3).T + d.xpos[o["bid"]]

    def _in_footprint(self, p):
        d = self.sim.d
        loc = d.xmat[self.box_bid].reshape(3, 3).T @ (p - d.xpos[self.box_bid])
        return bool(abs(loc[0]) <= self.scene.box_in[0] and abs(loc[1]) <= self.scene.box_in[1])

    def _in_box(self, o, touch):
        """W pudełku: środek masy w obrysie wnętrza, brak kontaktu z blatem, podparcie przez pudełko lub inny przedmiot."""
        return self._in_footprint(self.sim.d.xipos[o["bid"]]) and "table" not in touch and \
            ("box" in touch or any(isinstance(x, tuple) for x in touch))

    def _still(self, o):
        v = self.sim.d.qvel[o["dof"]:o["dof"] + 6]
        return bool(np.linalg.norm(v[:3]) < self.crit.v_tol and np.linalg.norm(v[3:]) < self.crit.w_tol)

    def _evaluate(self, tau):
        d, c, now, o_ = self.sim.d, self.crit, self.sim.sim_time, self.obs
        self.stats["max_qd"] = max(self.stats["max_qd"], float(np.abs(o_.qd[:5]).max()))
        self.stats["max_qdd"] = max(self.stats["max_qdd"], float(np.abs(o_.qd[:5] - self._qd_prev).max() / 0.01))
        self.stats["v_exceed_ticks"] += int(np.abs(o_.qd[:5]).max() > 1.5)
        self._qd_prev = o_.qd[:5].copy()
        self.box_drift = max(self.box_drift, float(np.linalg.norm((d.xpos[self.box_bid] - self.box0)[:2])))   # poziomo
        touch, pairs = {o["uid"]: set() for o in self.objs}, set()
        for i, (a, b) in enumerate(d.contact.geom[:d.ncon]):
            la, lb = self.lab[a], self.lab[b]
            if la is None or lb is None or la == lb:
                continue
            for x, y in ((la, lb), (lb, la)):                      # kontrola wiarygodności fizyki: głębokość wnikania padu
                if isinstance(x, tuple) and y in PADS:
                    o = self.objs[x[1]]
                    o["pen_mm"] = max(o["pen_mm"], round(-float(d.contact.dist[i]) * 1e3, 2))
            pairs.add((la, lb) if str(la) < str(lb) else (lb, la))
            for x, y in ((la, lb), (lb, la)):
                if isinstance(x, tuple):
                    touch[x[1]].add(y)
        target = (self.current or self.carried or self.releasing or {}).get("uid")
        for a, b in pairs - self.pairs:                           # początki kontaktów niepożądanych
            arm = [x for x in (a, b) if x in ARMSET]
            ob = [x for x in (a, b) if isinstance(x, tuple)]
            kind = ("arm_table" if arm and "table" in (a, b) else "arm_box" if arm and "box" in (a, b) else
                    "armlink_object" if "arm" in (a, b) and ob else
                    "pad_other_object" if arm and ob and ob[0][1] != target else
                    "carried_hit" if ob and not arm and self.carried and any(x[1] == self.carried["uid"] for x in ob)
                    else None)
            if kind:
                self.unwanted[kind] += 1
                self._log("unwanted_contact", kind=kind, pair=[str(a), str(b)])
        self.pairs = pairs
        for o in self.objs:
            if o["t_spawn"] is None:
                continue
            t = touch[o["uid"]]
            both = "jaw_fixed" in t and "jaw_moving" in t
            o["pad_ticks"] = o["pad_ticks"] + 1 if both else 0
            o["free_ticks"] = 0 if t & ARMSET else o["free_ticks"] + 1
            com = d.xipos[o["bid"]]
            if o is self.current and o["attempts"]:
                if o["pad_ticks"] >= c.grasp_ticks and not o["truth"]["grasp"]:
                    o["truth"]["grasp"], o["t"]["grasp"] = True, now
                    self._log("grasp", o)
                if both and not (t - set(PADS)) and com[2] >= o["z0"] + c.lift_dz:
                    o["truth"]["grasp"] = o["truth"]["lift"] = True
                    o["t"]["lift"] = now
                    self.current, self.carried = None, o
                    self._log("lift", o, dz_mm=round(float(com[2] - o["z0"]) * 1e3, 1))
                    self._request()                                # ← następny przedmiot dopiero po potwierdzonym podniesieniu
            elif o is self.carried:
                hit = t - set(PADS)
                if hit and not o["bumped"]:
                    o["bumped"] = sorted(map(str, hit))
                if tau < 0:                                        # kontroler kazał otworzyć szczękę
                    over = self._in_footprint(com)
                    o["t"]["release_cmd"], self.carried, self.releasing = now, None, o
                    o["truth"]["transport"] = bool(o["both_prev"] and over and not o["bumped"])
                    if not over:
                        o["dropped"] = "release_outside_box:" + self.phase
                    self._log("release_cmd", o, over_box=over, held=o["both_prev"], bumped=o["bumped"])
                elif o["free_ticks"] >= c.lost_ticks:
                    o["dropped"], self.carried = "lost:" + self.phase, None
                    o["t"]["dropped"] = now
                    self._log("dropped", o)
            elif "release_cmd" in o["t"] and not o["evaluated"]:
                if o["free_ticks"] >= c.release_ticks and not o["truth"]["release"]:
                    o["truth"]["release"], o["t"]["released"] = True, now
                    self.releasing = None                          # od teraz każdy kontakt padu z nim jest niepożądany
                if now >= o["t"]["release_cmd"] + c.settle_s:
                    o["evaluated"] = True
                    self.releasing = None if self.releasing is o else self.releasing
                    chk = dict(released=o["truth"]["release"], in_box=self._in_box(o, t), still=self._still(o),
                               no_arm_contact=not (t & ARMSET))
                    o["truth"]["placed"], o["place_check"] = all(chk.values()), chk
                    o["above_rim"] = bool(com[2] > self.scene.rim)
                    self._log("placed" if o["truth"]["placed"] else "not_placed", o, **chk)
            o["both_prev"] = both
        if self.pending and self.next < len(self.objs):
            self._try_spawn()
        if self.record and self.sim.stats["steps"] % self.record_every == 0:
            from PIL import Image
            self.renderer.update_scene(d, camera="overview")
            Image.fromarray(self.renderer.render()).save(os.path.join(self.record, f"f{self.nframe:05d}.png"))
            self.nframe += 1

    def finalize(self):
        """Końcowy spis: gdzie naprawdę jest każdy wprowadzony przedmiot."""
        d, z = self.sim.d, self.scene.zone
        touch = {o["uid"]: set() for o in self.objs}
        for a, b in d.contact.geom[:d.ncon]:
            for x, y in ((self.lab[a], self.lab[b]), (self.lab[b], self.lab[a])):
                if isinstance(x, tuple) and y is not None:
                    touch[x[1]].add(y)
        for o in self.objs:
            if o["t_spawn"] is None:
                o["final"], o["success"], o["fell_out"] = "not_introduced", False, False
                continue
            p, t = d.xipos[o["bid"]], touch[o["uid"]]
            o["final"] = ("gripper" if t & ARMSET else "box" if self._in_box(o, t) and self._still(o) else
                          "zone" if z[0] - .03 <= p[0] <= z[1] + .03 and z[2] - .03 <= p[1] <= z[3] + .03 else "table")
            o["final_pos"] = [round(float(x), 4) for x in p]
            o["success"] = bool(o["truth"]["placed"] and o["final"] == "box")
            o["fell_out"] = bool("release_cmd" in o["t"] and o["dropped"] is None and o["final"] != "box")
            o["z_low_mm"] = round(float(self._cloud_world(o)[:, 2].min()) * 1e3, 2)

    def report(self):
        keep = ("uid", "shape", "material", "cat", "mass", "mu", "density", "spawn", "attempts", "truth", "t", "dropped",
                "abandoned", "bumped", "pen_mm", "place_check", "above_rim", "final", "final_pos", "success", "fell_out", "z_low_mm")
        return dict(objects=[{k: o[k] for k in keep if k in o} for o in self.objs], events=self.events,
                    unwanted=self.unwanted, box_drift_mm=round(self.box_drift * 1e3, 3),
                    stats={k: round(v, 4) if isinstance(v, float) else v for k, v in self.stats.items()})


# ---------------------------------------------------------------- kontroler ---------------------------------------
def pad_corners(k, sim, name):
    g = k.geom(name)
    return g.xpos + (CORNERS * sim.m.geom(name).size) @ g.xmat.reshape(3, 3).T


def jaw_dir(k):
    n = k.site("cs_fixed").xpos - k.site("cs_moving").xpos
    n[2] = 0.0
    return n / np.linalg.norm(n)


def jaw_gap(sim, q):
    """Wolna szerokość między padami [m] wzdłuż kierunku zamykania (najbliższy punkt ruchomego padu)."""
    k = _kin(sim, q)
    n = jaw_dir(k)
    return float((pad_corners(k, sim, "jaw_fixed") @ n).min() - (pad_corners(k, sim, "jaw_moving") @ n).max())


class Controller:
    """Klasyczny kontroler. Wejścia: Obs (q, qd, touch, t), percept z World.percept(), własna kinematyka (reach.*)."""

    def __init__(self, world, cfg=OHCfg()):
        self.w, self.cfg, self.sim = world, cfg, world.sim         # sim służy WYŁĄCZNIE do kinematyki ramienia
        self.lim = Limits(ranges=ranges_from_mjcf(UPSTREAM))
        self.rcfg = ReachCfg(v_max=cfg.v_max)
        self.home = np.array(cfg.home)
        self.safety = SafetyLayer(self.lim)
        self.grip = ClassicGrip(GripCfg(q_open=cfg.home[5]))
        self.obs = world.obs
        q_ref, *_ = ik(self.sim, [0.2, 0.0, 0.06], self.home, cfg=self.rcfg, point="cs_fixed")
        self.qs = np.linspace(-0.12, 1.69, 60)                     # tabela rozwarcia szczęki z własnej kinematyki
        self.gaps = np.maximum.accumulate([jaw_gap(self.sim, np.r_[q_ref[:5], q]) for q in self.qs])
        yaw = lambda q: math.atan2(*jaw_dir(_kin(self.sim, q))[1::-1])  # noqa: E731
        self.roll_sign = math.copysign(1.0, math.sin(yaw(q_ref + [0, 0, 0, 0, 0.2, 0]) - yaw(q_ref)))
        self.n_drop, self.stop = 0, None
        self.stats = dict(flags={}, slow_settle=0, plan_wall=0.0)

    # ---------- takt ----------
    def tick(self, tgt, mode):
        o, g = self.obs, self.grip
        if mode == "preshape":                                     # ustaw rozwarcie z obu stron (ClassicGrip tylko otwiera)
            g.mode = "open"
            tau = g.cfg.tau_open if o.q[5] < g.cfg.q_open else g.cfg.tau_close if o.q[5] > g.cfg.q_open + 0.05 else 0.0
        else:
            g.mode = mode
            tau = g.step(o.q[5], o.touch)
        cmd = Command(o.t, {j: float(tgt[j]) for j in range(5)}, tau, {**{j: SRC for j in range(5)}, "jaw": SRC})
        q_t, tau_t, flags, per = self.safety.step(cmd, o.q, o.t, 0.0)
        if flags:
            raise Fail("safety_" + flags[0], str(flags))
        for f in {x for v in per.values() for x in v}:
            self.stats["flags"][f] = self.stats["flags"].get(f, 0) + 1
        self.obs = self.w.step(q_t, tau_t)

    def follow(self, path, mode, check=None):
        for x in profile(path, self.obs.q, self.cfg.v_max, self.cfg.a_max, self.lim.dt):
            self.tick(x, mode)
            if check:
                check()
        self.settle(np.asarray(path[-1])[:5], mode, check)

    def settle(self, tgt, mode, check=None):
        for _ in range(int(self.cfg.settle_max / self.lim.dt)):
            if np.abs(self.obs.q[:5] - tgt).max() < self.cfg.settle_tol:
                return
            self.tick(tgt, mode)
            if check:
                check()
        self.stats["slow_settle"] += 1

    def wait(self, sec, tgt, mode, until=None, check=None):
        for _ in range(int(round(sec / self.lim.dt))):
            if until and until():
                return True
            self.tick(tgt, mode)
            if check:
                check()
        return bool(until and until())

    def held(self):
        if min(self.obs.touch[:2]) < self.grip.cfg.f_contact:
            raise Fail("lost_grip", f"touch {np.round(self.obs.touch, 2).tolist()}")

    # ---------- plan ----------
    def joint_path(self, q0, q1, jaw, n=20):
        path = [q0 + (q1 - q0) * i / n for i in range(1, n + 1)]
        for q in path:
            if min(clearance(self.sim, q), clearance(self.sim, np.r_[q[:5], jaw])) < self.rcfg.z_min:
                raise ReachError("przejście za blisko blatu")
        return path

    def pose_over(self, xy, n_yaw, w, z_pad, q_pre, gap):
        """Poza z osią chwytaka w dół: kierunek zamykania szczęk = n_yaw (mod 180°), stała szczęka o gap od ściany
        przedmiotu szerokości w ze środkiem w xy, najniższy narożnik padów na wysokości z_pad."""
        sim, r = self.sim, self.rcfg
        q = self.home.copy()
        q[5] = q_pre
        lo, hi = sim.jrange[4, 0] + r.margin, sim.jrange[4, 1] - r.margin
        ep = ea = err = 9.0
        for _ in range(8):
            k = _kin(sim, q)
            n = jaw_dir(k)
            err = (n_yaw - math.atan2(n[1], n[0]) + math.pi / 2) % math.pi - math.pi / 2
            roll = q[4] + self.roll_sign * err
            roll += math.pi if roll < lo else -math.pi if roll > hi else 0.0
            q[4] = roll
            a = math.atan2(n[1], n[0]) + err
            L = k.site("cs_fixed").xpos[2] - clearance(sim, q)
            tgt = np.array([xy[0] + math.cos(a) * (w / 2 + PAD_HALF + gap), xy[1] + math.sin(a) * (w / 2 + PAD_HALF + gap),
                            z_pad + L])
            q, ep, ea = ik(sim, tgt, q, cfg=r, point="cs_fixed")
        if ep > r.tol_pos or ea > r.tol_axis or abs(err) > 0.03 or abs(clearance(sim, q) - z_pad) > 0.002:
            raise ReachError(f"poza nieosiągalna nad {np.round(xy, 3).tolist()}, z {z_pad:.3f} "
                             f"(błąd {ep * 1e3:.1f} mm, oś {math.degrees(ea):.1f}°, obrót {math.degrees(err):.1f}°)")
        return q

    def plan(self, p):
        c, sim, r, sc = self.cfg, self.sim, self.rcfg, self.w.scene
        need = p["w"] + c.gap + c.jaw_clear
        if need > self.gaps[-1]:
            raise Fail("too_wide", f"szerokość {p['w'] * 1e3:.1f} mm + zapas > rozwarcie {self.gaps[-1] * 1e3:.1f} mm")
        q_pre = float(np.interp(need, self.gaps, self.qs))
        z_grasp = max(c.pad_bottom, p["h"] - c.palm_clear)
        z_carry = z_grasp + sc.rim + c.carry_clear
        n_yaw, xy = p["yaw"] + math.pi / 2, (p["x"], p["y"])
        try:
            q_above = self.pose_over(xy, n_yaw, p["w"], p["h"] + c.h_above, q_pre, c.gap)
            cs = lambda q: _kin(sim, q).site("cs_fixed").xpos.copy()  # noqa: E731
            P = dict(q_pre=q_pre, z_grasp=z_grasp, z_carry=z_carry,
                     move=self.joint_path(self.home, q_above, q_pre))
            P["descend"] = plan(sim, q_above, cs(q_above) - [0, 0, p["h"] + c.h_above - z_grasp], point="cs_fixed",
                                jaw_open=q_pre, cfg=r)
            q_g = P["descend"][-1]                                 # IK ma tolerancję 2 mm: dociągnij wysokość padów
            for _ in range(3):
                q_g, *_ = ik(sim, cs(q_g) - [0, 0, clearance(sim, q_g) - z_grasp], q_g, cfg=replace(r, tol_pos=0.0002),
                             point="cs_fixed")
            if abs(clearance(sim, q_g) - z_grasp) > 0.001:
                raise ReachError(f"wysokość chwytu nieosiągalna ({clearance(sim, q_g) * 1e3:.1f} mm)")
            P["descend"].append(q_g)
            P["lift"] = plan(sim, P["descend"][-1], cs(P["descend"][-1]) + [0, 0, z_carry - z_grasp], point="cs_fixed", cfg=r)
            err = None
            for i in range(len(sc.drops)):                         # kolejny punkt zrzutu; nieosiągalny → następny
                dx, dy = sc.drops[(self.n_drop + i) % len(sc.drops)]
                try:
                    q_d = P["lift"][-1]
                    for _ in range(2):                             # środek przedmiotu (nie pad) nad punktem zrzutu
                        n = jaw_dir(_kin(sim, q_d))
                        tgt = np.r_[sc.box_xy[0] + dx + n[0] * (p["w"] / 2 + PAD_HALF),
                                    sc.box_xy[1] + dy + n[1] * (p["w"] / 2 + PAD_HALF), cs(P["lift"][-1])[2]]
                        q_d, ep, ea = ik(sim, tgt, q_d, cfg=r, point="cs_fixed")
                    P["transport"] = plan(sim, P["lift"][-1], tgt, point="cs_fixed", cfg=r)
                    P["retreat"] = []
                    for up in (0.02, 0.01):                        # po zwolnieniu najpierw w górę, o ile zasięg pozwala
                        try:
                            P["retreat"] = plan(sim, P["transport"][-1], tgt + [0, 0, up], point="cs_fixed",
                                                jaw_open=q_pre, cfg=r)
                            break
                        except ReachError:
                            pass
                    P["home"] = self.joint_path((P["retreat"] or P["transport"])[-1], self.home, q_pre)
                    P["drop"] = (self.n_drop + i) % len(sc.drops)
                    break
                except ReachError as e:
                    err = e
            else:
                raise err
        except ReachError as e:
            raise Fail("unreachable", str(e)) from e
        return P

    # ---------- jedna próba ----------
    def attempt(self, p):
        c, w = self.cfg, self.w
        rec = dict(percept=p, t_sim={}, t_wall={}, ok=False, reason=None, lifted=False)
        t0, clock = self.obs.t, [self.obs.t, time.perf_counter()]

        def mark(ph):
            rec["t_sim"][ph] = self.obs.t - clock[0]
            rec["t_wall"][ph] = time.perf_counter() - clock[1]
            clock[:] = [self.obs.t, time.perf_counter()]

        try:
            w.phase = "plan"
            P = self.plan(p)
            rec.update(plan_wall=time.perf_counter() - clock[1], q_pre=P["q_pre"], z_grasp=P["z_grasp"], drop=P["drop"])
            self.stats["plan_wall"] += rec["plan_wall"]
            clock[1] = time.perf_counter()
            self.grip = ClassicGrip(GripCfg(q_open=P["q_pre"]))
            opened = lambda: self.obs.q[5] >= P["q_pre"] - c.jaw_tol  # noqa: E731 — szerzej niż trzeba nie szkodzi
            w.phase = "approach"
            self.follow(P["move"], "preshape")
            tgt = np.asarray(P["move"][-1])[:5]
            if not self.wait(c.open_max, tgt, "preshape", until=opened):
                raise Fail("jaw_not_open", f"q szczęki {self.obs.q[5]:.2f}, cel {P['q_pre']:.2f}")
            self.follow(P["descend"], "open")
            mark("approach")
            w.phase = "grasp"
            tgt = np.asarray(P["descend"][-1])[:5]
            if not self.wait(c.close_max, tgt, "close", until=lambda: self.grip.mode == "hold"):
                raise Fail("no_contact", f"touch {np.round(self.obs.touch, 2).tolist()}, q szczęki {self.obs.q[5]:.2f}")
            self.wait(c.hold_settle, tgt, "hold")
            if min(self.obs.touch[:2]) < c.f_grip:
                raise Fail("weak_grip", f"touch {np.round(self.obs.touch, 2).tolist()} N < {c.f_grip}")
            mark("grasp")
            w.phase = "lift"
            self.follow(P["lift"], "hold", self.held)
            rec["lifted"] = True                                   # przekonanie kontrolera (dotyk), nie stan prawdziwy
            mark("lift")
            w.phase = "transport"
            self.follow(P["transport"], "hold", self.held)
            mark("transport")
            w.phase = "place"
            tgt = np.asarray(P["transport"][-1])[:5]
            self.n_drop = P["drop"] + 1
            q_rel = min(self.obs.q[5] + c.jaw_release, P["q_pre"] - c.jaw_tol)   # wyraźnie szerzej niż w chwycie
            if not self.wait(c.open_max, tgt, "open", until=lambda: max(self.obs.touch[:2]) < self.grip.cfg.f_contact
                             and self.obs.q[5] >= q_rel):
                raise Fail("release_failed", f"touch {np.round(self.obs.touch, 2).tolist()}, q szczęki {self.obs.q[5]:.2f}")
            mark("place")
            w.phase = "return"
            if P["retreat"]:
                self.follow(P["retreat"], "open")
            self.follow(P["home"], "open")
            mark("return")
            rec["ok"] = True
        except Fail as e:
            rec.update(reason=e.reason, detail=e.detail, fail_phase=w.phase, t_to_fail_sim=self.obs.t - t0)
            rec["recover"] = self.recover()
            if rec["recover"] is not True:
                self.stop = f"recover: {rec['recover']}"
        w.phase = "idle"
        rec["op_sim"] = self.obs.t - t0
        return rec

    def not_ready(self):
        """Kontrola po powrocie — tylko z enkoderów i dotyku (kontroler nie widzi kontaktów ani przedmiotów)."""
        o, c = self.obs, self.cfg
        if self.safety.fault:
            return f"safety_latched: {self.safety.fault}"
        e = float(np.abs(o.q[:5] - self.home[:5]).max())
        if e >= c.settle_tol:
            return f"arm_not_home: {e:.3f} rad"
        if max(o.touch) > self.grip.cfg.f_contact:
            return f"pads_loaded: {np.round(o.touch, 2).tolist()} N"
        return None

    def recover(self):
        """Po nieudanej próbie: otwórz szczękę, podnieś pady na wysokość transportu, wróć do domu. Bez resetu."""
        if self.safety.fault:
            return f"safety_latched: {self.safety.fault}"
        try:
            self.w.phase = "recover"
            q, sim = self.obs.q.copy(), self.sim
            self.wait(0.5, q[:5], "open", until=lambda: max(self.obs.touch[:2]) < self.grip.cfg.f_contact
                      and self.obs.q[5] >= self.grip.cfg.q_open - self.cfg.jaw_tol)
            q = self.obs.q.copy()
            path, up = [], self.w.scene.rim + self.cfg.carry_clear + self.cfg.pad_bottom - clearance(sim, q)
            if up > 0.002:
                try:
                    path = plan(sim, q, _kin(sim, q).site("cs_fixed").xpos + [0, 0, up], point="cs_fixed", cfg=self.rcfg)
                except ReachError:
                    path = []
            q1 = np.asarray(path[-1] if path else q)
            path = list(path) + [q1 + (self.home - q1) * i / 20 for i in range(1, 21)]
            for x in profile(path, self.obs.q, 0.5, 2.0, self.lim.dt):
                self.tick(x, "open")
            self.settle(self.home[:5], "open")
        except Fail as e:
            return f"{e.reason}: {e.detail}"
        return self.not_ready() or True

    def wait_percept(self):
        t0 = self.obs.t
        while True:
            p = self.w.percept()
            if p is not None or self.w.done():
                return p
            if self.obs.t - t0 > self.cfg.idle_max:
                self.stop = "no_object: strefa zablokowana lub brak przedmiotu"
                return None
            self.tick(self.home[:5], "open")


# ---------------------------------------------------------------- seria, podsumowanie, zapis ----------------------
def run(items, seed, cfg=OHCfg(), scene=Scene(), crit=Crit(), record=None):
    """Jedna ciągła seria: kolejka `items` [(kształt, materiał), …] bez żadnego resetu. Zwraca raport serii."""
    import mujoco
    w0 = time.perf_counter()
    world = World(items, seed, scene, crit, cfg.home, record)
    ctl = Controller(world, cfg)
    build_wall, w1, attempts, stopped = time.perf_counter() - w0, time.perf_counter(), [], None
    try:
        while not ctl.stop:
            p = ctl.wait_percept()
            if p is None:
                break
            uid = world.current["uid"]
            attempts.append(dict(uid=uid, n=world.current["attempts"], **ctl.attempt(p)))
        stopped = ctl.stop
        if not stopped:
            ctl.wait(crit.final_idle, ctl.home[:5], "open")
    except Fail as e:                                              # błąd bezpieczeństwa / fizyki poza próbą: seria staje
        stopped = f"{e.reason}: {e.detail}"
    world.finalize()
    rep = world.report()
    for o in rep["objects"]:
        o["attempt_log"] = [a for a in attempts if a["uid"] == o["uid"]]
    sim = world.sim
    rep.update(seed=seed, queue=[f"{s}/{m}" for s, m in items], complete=stopped is None, stopped_by=stopped,
               T_sim=sim.sim_time, T_wall=time.perf_counter() - w1, build_wall=build_wall,
               resets=sim.stats["resets"] - 1, auto_resets=sim.stats["auto_resets"],
               controller=dict(flags=ctl.stats["flags"], slow_settle=ctl.stats["slow_settle"],
                               plan_wall=round(ctl.stats["plan_wall"], 3)),
               safety_stats=ctl.safety.stats["per_source"], mujoco=mujoco.__version__)
    return rep


def rate(objs, key=None):
    n = len(objs)
    k = sum(bool(o["truth"][key]) if key in STAGES else bool(o.get(key)) for o in objs)
    return dict(k=k, n=n, pct=round(100 * k / n, 1) if n else None)


def summarize(runs):
    objs = [o for r in runs for o in r["objects"] if o["final"] != "not_introduced"]
    att = [a for o in objs for a in o["attempt_log"]]
    ok_ops = [a for o in objs if o["success"] for a in o["attempt_log"] if a["ok"]]
    med = lambda v: round(float(np.median(v)), 3) if len(v) else None  # noqa: E731
    reasons = {}
    for a in att:
        if not a["ok"]:
            reasons[a["reason"]] = reasons.get(a["reason"], 0) + 1

    def group(f):
        out = {}
        for o in objs:
            out.setdefault(f(o), []).append(o)
        return {str(k): dict(n=len(v), **{s: sum(o["truth"][s] for o in v) for s in STAGES},
                             success=sum(o["success"] for o in v),
                             op_sim_med=med([a["op_sim"] for o in v if o["success"] for a in o["attempt_log"] if a["ok"]]))
                for k, v in sorted(out.items(), key=lambda kv: str(kv[0]))}

    mass_bin = lambda o: next(lab for lim, lab in ((0.01, "a <10 g"), (0.03, "b 10–30 g"), (0.1, "c 30–100 g"),  # noqa: E731
                                                   (0.3, "d 100–300 g"), (9, "e >300 g")) if o["mass"] < lim)
    return dict(
        introduced=len(objs), not_introduced=sum(o["final"] == "not_introduced" for r in runs for o in r["objects"]),
        **{s: rate(objs, s) for s in STAGES}, success=rate(objs, "success"),
        dropped=sum(o["dropped"] is not None for o in objs), fell_out=sum(o["fell_out"] for o in objs),
        abandoned=sum(o["abandoned"] for o in objs), pad_penetration_gt2mm=sum(o["pen_mm"] > 2.0 for o in objs),
        final_loc={k: sum(o["final"] == k for o in objs)
                                                                for k in ("box", "zone", "table", "gripper")},
        attempts=len(att), controller_fails=reasons,
        false_belief=sum(a["ok"] for o in objs if not o["success"] for a in o["attempt_log"]),
        op_sim_s=dict(n=len(ok_ops), mean=round(float(np.mean([a["op_sim"] for a in ok_ops])), 3) if ok_ops else None,
                      median=med([a["op_sim"] for a in ok_ops]),
                      min=round(min((a["op_sim"] for a in ok_ops), default=0), 3),
                      max=round(max((a["op_sim"] for a in ok_ops), default=0), 3)),
        phase_sim_s_median={p: med([a["t_sim"][p] for a in ok_ops]) for p in PHASES},
        phase_wall_s_median={p: med([a["t_wall"][p] for a in ok_ops]) for p in PHASES},
        T_sim_s=round(sum(r["T_sim"] for r in runs), 2), T_wall_s=round(sum(r["T_wall"] for r in runs), 2),
        max_qd=max(r["stats"]["max_qd"] for r in runs), max_qdd=max(r["stats"]["max_qdd"] for r in runs),
        v_exceed_ticks=sum(r["stats"]["v_exceed_ticks"] for r in runs),
        safety_flags={k: sum(r["controller"]["flags"].get(k, 0) for r in runs)
                      for k in sorted({k for r in runs for k in r["controller"]["flags"]})},
        unwanted_contacts={k: sum(r["unwanted"][k] for r in runs) for k in runs[0]["unwanted"]},
        resets=sum(r["resets"] for r in runs), auto_resets=sum(r["auto_resets"] for r in runs),
        interrupted_series=sum(not r["complete"] for r in runs),
        box_drift_mm_max=max(r["box_drift_mm"] for r in runs),
        by_shape=group(lambda o: o["shape"]), by_material=group(lambda o: o["material"]),
        by_category=group(lambda o: o["cat"]), by_mass=group(mass_bin), by_mu=group(lambda o: o["mu"]),
        by_object=group(lambda o: f"{o['shape']}/{o['material']}"))


def code_state():
    g = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()  # noqa: E731
    files = ("object_handling.py", "pick_place.py", "so101.py", "reach.py", "grip.py", "safety.py")
    return dict(commit=g("rev-parse", "HEAD"), branch=g("branch", "--show-current"),
                sha256={f: hashlib.sha256(open(os.path.join(ROOT, "flymind", f), "rb").read()).hexdigest() for f in files})


def catalogue(items):
    """Rzeczywiste parametry z modelu (masa policzona przez MuJoCo z gęstości i geometrii)."""
    w = World(sorted(set(items)), 0)
    out = {}
    for o in w.objs:
        p = obb(o["cloud"] @ quat_mat(w.sim.mj, o["rest_quat"]).T)
        M = MATERIALS[o["material"]]
        out[f"{o['shape']}/{o['material']}"] = dict(
            cat=o["cat"], geoms=[[g[0], list(g[1]) if g[0] != "mesh" else "klin 30×40×30 mm", *map(list, g[2:])]
                                 for g in SHAPES[o["shape"]]["geoms"]],
            footprint_mm=[round(p["l"] * 1e3, 1), round(p["w"] * 1e3, 1)], height_mm=round((o["rest_z"] + p["h"]) * 1e3, 1),
            mass_g=round(o["mass"] * 1e3, 2), density=M["density"], friction=[M["mu"], 0.005, 1e-4],
            solref=list(M["solref"]), condim=SHAPES[o["shape"]].get("condim", 4), priority=1, rigid=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("single", "series"))
    ap.add_argument("--set", default="base", choices=sorted(SETS))
    ap.add_argument("--only", nargs="*", help="single: tylko te „kształt/materiał”")
    ap.add_argument("--poses", type=int, default=3, help="single: losowych położeń na przedmiot")
    ap.add_argument("--seed", type=int, default=100, help="single: ziarno bazowe położeń")
    ap.add_argument("--perm", type=int, nargs="+", default=[1], help="series: ziarna permutacji zestawu")
    ap.add_argument("--n", type=int, default=9, help="series: przedmiotów w jednej serii (jedno pudełko)")
    ap.add_argument("--record", help="katalog na klatki PNG z pierwszej serii")
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    paths = [os.path.join(OUT, f"{a.tag}{x}.json") for x in ("", ".INCOMPLETE")]
    if any(os.path.exists(p) for p in paths):
        sys.exit(f"istnieje już wynik o tagu {a.tag!r} w {OUT} — wybierz inny --tag")
    items, runs = SETS[a.set], []
    if a.mode == "single":                                          # każda próba = świeża scena z JEDNYM przedmiotem
        todo = [it for it in items if not a.only or "/".join(it) in a.only]
        for i, it in enumerate(todo):
            for k in range(a.poses):
                r = run([it], a.seed * 1000 + items.index(it) * 10 + k, record=a.record if not runs else None)
                runs.append(r)
                o = r["objects"][0]
                print(f"{'/'.join(it):22s} poza {k}: {'OK ' if o['success'] else '-- '}"
                      f"{''.join('GLTRP'[j] if o['truth'][s] else '.' for j, s in enumerate(STAGES))} "
                      f"próby {o['attempts']} {[x['reason'] for x in o['attempt_log'] if not x['ok']]} → {o['final']}",
                      flush=True)
    else:                                                           # permutacja całego zestawu pocięta na serie po n
        for ps in a.perm:
            order = [items[i] for i in np.random.default_rng(ps).permutation(len(items))]
            for j in range(0, len(order), a.n):
                r = run(order[j:j + a.n], ps * 100 + j // a.n, record=a.record if not runs else None)
                runs.append(r)
                print(f"perm {ps} seria {j // a.n}: {sum(o['success'] for o in r['objects'])}/{len(r['objects'])} w pudełku, "
                      f"T_sim {r['T_sim']:.1f} s, T_wall {r['T_wall']:.1f} s, stop {r['stopped_by']}, "
                      f"losy {[o['final'] for o in r['objects']]}", flush=True)
    summ = summarize(runs)
    complete = all(r["complete"] for r in runs)
    out = dict(tag=a.tag, mode=a.mode, set=a.set, complete=complete, argv=sys.argv, cfg=asdict(OHCfg()),
               scene=asdict(Scene()), crit=asdict(Crit()), code=code_state(), python=sys.version.split()[0],
               catalogue=catalogue(items), summary=summ, runs=runs)
    with open(paths[0] if complete else paths[1], "x") as f:
        json.dump(out, f, indent=1, default=float)
    print(json.dumps({k: v for k, v in summ.items() if not k.startswith("by_object")}, indent=1, ensure_ascii=False))
    print("zapisano" if complete else "NIEKOMPLETNE — zapisano", paths[0] if complete else paths[1])
    sys.exit(0 if complete else 1)


if __name__ == "__main__":
    main()
