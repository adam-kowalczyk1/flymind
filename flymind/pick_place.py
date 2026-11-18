"""flymind/pick_place.py — Etap 1: KLASYCZNY, powtarzalny cykl pick-and-place kostki między stałymi miejscami A i B.

To NIE jest sterowanie muszki: wszystkie komendy mają źródło "classical:pick_place" i przechodzą przez
safety.SafetyLayer. Etap 1 jest bazą techniczną do późniejszych porównań (Etap 2+), nie wynikiem biologicznym.

Kostka jeździ tam i z powrotem: leży w A → cykl A→B; leży w B → cykl B→A. Środowiska nie resetujemy między cyklami.
Pozycja kostki jest czytana ze stanu symulatora (ground truth, bez kamery) — ograniczenie opisane w dokumentacji.

Warstwy (wszystko poza tym plikiem odziedziczone):
  so101.SO101Sim       scena (stół, kostka, znaczniki A/B), fizyka, aktuatory
  reach.ik/plan/...    IK, odcinki kartezjańskie, kontrola odstępu padów od stołu
  grip.ClassicGrip     automat szczęki (open / close → hold po kontakcie obu padów)
  safety.SafetyLayer   zakresy, prędkość, wyprzedzenie celu, moment szczęki
  ten plik             plan cyklu (liczony raz na kierunek, cache), profil trapezowy v/a, orkiestrator faz,
                       kontrole przejść, obsługa błędów z powrotem do domu, pomiary, seria prób (__main__)

Uruchom serię:  .venv/bin/python -I -B flymind/pick_place.py --seeds 1 2 3 4 5 --cycles 50 --tag main
"""
import argparse
import json
import math
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, replace

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grip import ClassicGrip, GripCfg  # noqa: E402
from reach import ReachCfg, ReachError, _kin, clearance, fixed_pad_target, ik, plan, plan_joint  # noqa: E402
from safety import Command, Limits, SafetyLayer, ranges_from_mjcf  # noqa: E402
from so101 import ROOT, UPSTREAM, SceneCfg, SimError, SO101Sim  # noqa: E402

SRC = "classical:pick_place"
PHASES = ("approach", "grasp", "lift", "transport", "place", "return")
OUT = os.path.join(ROOT, "flymind", "results", "pick_place")
# Co wolno zrobić automatycznie po porażce cyklu (klasy błędów; opis w PICK_PLACE_STAGE1.md §15):
#   1. porażki procesu (cube_pushed, no_contact, slip, …)  → recover() wraca do domu i SPRAWDZA stan
#   2. NO_MOTION: kolizja, zła komenda, zatrzymana fizyka      → recover() nie rusza ramienia; seria resetuje scenę
#   3. zatrzaśnięty błąd SafetyLayer (pomiar poza zakresem, estop) → nic go nie kasuje poza jawnym
#      SafetyLayer.clear(powód); seria się zatrzymuje (reset sceny NIE jest potwierdzeniem bezpieczeństwa)
NO_MOTION = ("table_collision", "bad_command", "sim_error")


class Fail(RuntimeError):
    """Nieudany cykl: reason = krótki kod przyczyny (raportowany), detail = opis."""
    def __init__(self, reason, detail=""):
        super().__init__(f"{reason}: {detail}")
        self.reason, self.detail = reason, detail


@dataclass(frozen=True)
class PPCfg:
    # miejsca [m] i kostka (PLA ok. 1,1 g/cm³ → 3 cm ≈ 30 g; tarcie PLA/guma ok. 0,8 — wybór jawny, nie strojony)
    A: tuple = (0.22, 0.10)
    B: tuple = (0.22, -0.10)
    cube: float = 0.030
    cube_mass: float = 0.030
    cube_friction: float = 0.8
    home: tuple = (0.0, -0.4, 1.0, 0.0, 1.571, 0.93)     # jak test_reach.Q0; szczęka otwarta
    # geometria chwytu [m]
    gap: float = 0.004            # stała szczęka od ściany kostki przy zejściu
    pad_bottom: float = 0.007     # najniższy narożnik padów nad stołem w chwycie (reach z_min = 5 mm)
    h_above: float = 0.06         # zejście / odejście w pionie
    h_transport: float = 0.06     # spód kostki nad stołem w transporcie
    place_drop: float = 0.001     # spód kostki nad stołem w chwili otwarcia szczęki
    # ruch
    v_max: float = 1.0            # rad/s na staw (reach.ReachCfg.v_max; SafetyLayer: 1,5)
    a_max: float = 4.0            # rad/s² na staw (profil trapezowy)
    settle_tol: float = 0.02      # rad, |cel − q| ramienia = osiągnięto
    settle_max: float = 0.5       # s, potem kontynuacja z flagą slow_settle (nie porażka)
    # szczęka (GripCfg z grip.py, moment ≤ Limits.tau_max)
    close_max: float = 2.0        # s do kontaktu obu padów (szczęka zamyka się ok. 0,75 rad/s przy 0,5 N·m)
    hold_settle: float = 0.10     # s narastania siły po kontakcie
    f_grip: float = 1.0           # N na każdym padzie = chwyt potwierdzony
    open_max: float = 1.0         # s
    q_pre: float = 0.93           # rad: rozwarcie szczęki w podejściu i po odłożeniu (GripCfg.q_open; 0,93 jak bio2)
    q_clear: float = 0.55         # rad szczęki: rozwarcie wyraźnie szersze niż kostka (kontakt przy ok. 0,3 rad)
    # kontrola wyników
    slip_tol: float = 0.008       # m, przesunięcie kostki względem stałej szczęki w trakcie trzymania
    zone: float = 0.010           # m, promień dopuszczalnego obszaru wokół A/B
    yaw_tol: float = 10.0         # °, obrót kostki względem nominalnego
    tilt_tol: float = 5.0         # °, przechył kostki
    reuse_tol: float = 0.0015     # m, odchyłka kostki, do której używamy planu z cache (inaczej nowy plan chwytu)
    reuse_yaw: float = 2.0        # °


def cube_pose(sim):
    """(xyz [m], yaw [rad] mod 90°, tilt [rad]) kostki z symulatora."""
    R = sim.d.body("cube").xmat.reshape(3, 3)
    k = int(np.argmax(np.abs(R[2])))                     # oś kostki najbliższa pionu
    tilt = math.acos(min(1.0, abs(R[2, k])))
    h = R[:, (k + 1) % 3]                                 # oś pozioma
    yaw = math.atan2(h[1], h[0])
    return sim.d.body("cube").xpos.copy(), (yaw + math.pi / 4) % (math.pi / 2) - math.pi / 4, tilt


def wrap90(a):
    return (a + math.pi / 4) % (math.pi / 2) - math.pi / 4


def profile(path, q_start, v, a, dt):
    """Cele [5] na takty: ścieżka w stawach parametryzowana długością w normie max (każdy staw ≤ v, ≤ a na
    odcinkach prostych), profil trapezowy start/stop. Gęste punkty z IK → zakręty łagodne."""
    pts = np.array([np.asarray(q_start, float)[:5]] + [np.asarray(p, float)[:5] for p in path])
    s = np.r_[0.0, np.cumsum(np.abs(np.diff(pts, axis=0)).max(1))]
    S = s[-1]
    if S < 1e-9:
        return []
    ta = v / a
    if S < v * ta:                                       # trójkąt: nie osiąga v
        ta, v = math.sqrt(S / a), math.sqrt(S * a)
    T = 2 * ta + (S - v * ta) / v
    t = dt * np.arange(1, int(math.ceil(T / dt)) + 1)
    st = np.where(t < ta, 0.5 * a * t ** 2,
                  np.where(t < T - ta, v * ta / 2 + v * (t - ta), S - 0.5 * a * np.clip(T - t, 0, None) ** 2))
    st = np.clip(st, 0, S)
    return [np.array([np.interp(x, s, pts[:, j]) for j in range(5)]) for x in st]


class Cell:
    """Stanowisko: symulator + warstwa bezpieczeństwa + szczęka + plany. Jedna instancja na serię (bez resetów)."""

    def __init__(self, cfg=PPCfg(), seed=None):
        self.cfg, self.seed = cfg, seed
        rng = np.random.default_rng(seed) if seed is not None else None
        # zmienność per ziarno (oszacowanie realnej rozbieżności, nie strojenie): masa i tarcie ±10 %, start kostki
        # ±2 mm / ±3°. seed None = wartości nominalne.
        mass = cfg.cube_mass * (rng.uniform(0.9, 1.1) if rng else 1.0)
        fric = cfg.cube_friction * (rng.uniform(0.9, 1.1) if rng else 1.0)
        self.scene = SceneCfg(cube_size=cfg.cube, cube_mass=mass, cube_friction=(fric, 0.005, 1e-4),
                              marks=(cfg.A, cfg.B), backdrop=False)
        self.sim = SO101Sim(self.scene, render=False)
        self.lim = Limits(ranges=ranges_from_mjcf(UPSTREAM))
        self.rcfg = ReachCfg(v_max=cfg.v_max)
        self.home = np.array(cfg.home)
        self.sim.reset(self.home)                         # kostka zaparkowana: plany nominalne bez kostki w scenie
        self.plans, self.yaw_nom = {}, {}
        t0 = time.perf_counter()
        for src, dst in (("A", "B"), ("B", "A")):
            self.plans[(src, dst)] = self.plan_cycle(self.place(src), self.place(dst))
        self.plan_wall = time.perf_counter() - t0
        # nominalna orientacja kostki w A = kierunek zamykania szczęk w pozie chwytu nad A (ściana ⟂ szczęce)
        for name in ("A", "B"):
            self.yaw_nom[name] = self.jaw_yaw(self.place(name))
        dx, dy, dyaw = (rng.uniform(-0.002, 0.002), rng.uniform(-0.002, 0.002),
                        math.radians(rng.uniform(-3, 3))) if rng else (0.0, 0.0, 0.0)
        self.sim.reset(self.home, cube_pose=(cfg.A[0] + dx, cfg.A[1] + dy, self.yaw_nom["A"] + dyaw))
        self.safety = SafetyLayer(self.lim)
        self.grip = ClassicGrip(GripCfg(q_open=cfg.q_pre))
        self.obs = self.sim.observe()
        g = self.sim.m
        self.arm_geoms = {i for i in range(g.ngeom)
                          if g.geom(i).name not in ("table", "cube", "ball") and not g.geom(i).name.startswith("mark")}
        self.table_id, self.cube_id = g.geom("table").id, g.geom("cube").id
        self.stats = dict(replans=0, slow_settle=0, flags={}, min_margin=np.inf, max_qd=0.0, max_qdd=0.0)
        self._qd_prev = self.obs.qd[:5].copy()
        self.settle_ticks = 0

    # ---------- geometria ----------
    def place(self, name):
        x, y = getattr(self.cfg, name)
        return np.array([x, y, self.cfg.cube / 2])

    def jaw_dir(self, center):
        q, *_ = ik(self.sim, np.asarray(center) + [0, 0, 0.08], self.home, cfg=self.rcfg)
        k = _kin(self.sim, q)
        n = k.site("cs_fixed").xpos - k.site("cs_moving").xpos
        return q, n

    def jaw_yaw(self, center):
        _, n = self.jaw_dir(center)
        return wrap90(math.atan2(n[1], n[0]))

    def pad_target(self, center, gap, lift=0.0):
        """Cel miejsca cs_fixed: stała szczęka o gap od ściany kostki, najniższy narożnik padów pad_bottom nad
        spodem kostki, + lift w pionie."""
        c = self.cfg
        q_up, _ = self.jaw_dir(center)
        # L = pionowy odstęp miejsca cs_fixed od najniższego narożnika padów (stały przy osi w dół)
        L = _kin(self.sim, q_up).site("cs_fixed").xpos[2] - clearance(self.sim, q_up)
        dz = c.pad_bottom + L - c.cube / 2               # względem środka kostki leżącej na stole
        return fixed_pad_target(self.sim, q_up, center, c.cube / 2, gap=gap, dz=dz) + [0, 0, lift]

    def plan_pick(self, src):
        """Ścieżki (listy q[6]) podejścia i podniesienia dla kostki o środku src, od pozy domowej."""
        c, h, jo, r = self.cfg, self.home, self.cfg.home[5], self.rcfg
        g = self.pad_target(src, c.gap)
        p = {"approach_move": plan_joint(self.sim, h, g + [0, 0, c.h_above], point="cs_fixed", jaw_open=jo, cfg=r)}
        p["approach_descend"] = plan(self.sim, p["approach_move"][-1], g, point="cs_fixed", jaw_open=jo, cfg=r)
        p["lift"] = plan(self.sim, p["approach_descend"][-1], g + [0, 0, c.h_transport], point="cs_fixed", cfg=r)
        return p

    def plan_cycle(self, src, dst):
        """Ścieżki wszystkich faz cyklu src → dst od pozy domowej. ReachError → nieosiągalne."""
        c, h, jo, r = self.cfg, self.home, self.cfg.home[5], self.rcfg
        lift = c.h_transport
        p = self.plan_pick(src)
        # odłożenie: stała szczęka dociśnięta do kostki (gap 0), spód kostki place_drop nad stołem
        gp = self.pad_target(dst, 0.0, lift=c.place_drop)
        p["transport"] = plan(self.sim, p["lift"][-1], gp + [0, 0, lift - c.place_drop], point="cs_fixed", cfg=r)
        p["place_descend"] = plan(self.sim, p["transport"][-1], gp, point="cs_fixed", cfg=r)
        p["retreat"] = plan(self.sim, p["place_descend"][-1], gp + [0, 0, c.h_above], point="cs_fixed",
                            jaw_open=jo, cfg=r)
        p["home"] = [p["retreat"][-1] + (h - p["retreat"][-1]) * i / 20 for i in range(1, 21)]
        for q in p["home"]:
            if min(clearance(self.sim, q), clearance(self.sim, np.r_[q[:5], jo])) < r.z_min:
                raise ReachError("powrót do domu za blisko stołu")
        return p

    # ---------- takt i monitory ----------
    def tick(self, tgt, mode):
        self.grip.mode = mode
        o = self.obs
        tau = self.grip.step(o.q[5], o.touch)
        cmd = Command(o.t, {j: float(tgt[j]) for j in range(5)}, tau, {**{j: SRC for j in range(5)}, "jaw": SRC})
        q_t, tau_t, flags, per = self.safety.step(cmd, o.q, o.t, 0.0)
        if flags:
            raise Fail("safety_" + flags[0], str(flags))
        for f in {x for v in per.values() for x in v}:
            self.stats["flags"][f] = self.stats["flags"].get(f, 0) + 1
        try:
            applied = self.sim.act(q_t, tau_t)
        except SimError as e:                             # komenda łamie kontrakt symulatora: ctrl bez zmian, bez kroku
            raise Fail("bad_command", str(e)) from e
        if not applied:                                   # symulator zatrzymany (po niestabilności): bez kroku
            raise Fail("sim_error", f"symulator zatrzymany: {self.sim.stopped}")
        try:
            self.sim.step()
        except SimError as e:
            raise Fail("sim_error", str(e)) from e
        self.obs = o = self.sim.observe()
        r = self.lim.ranges
        self.stats["min_margin"] = min(self.stats["min_margin"], float(np.min(np.minimum(o.q - r[:, 0], r[:, 1] - o.q))))
        self.stats["max_qd"] = max(self.stats["max_qd"], float(np.abs(o.qd[:5]).max()))
        self.stats["max_qdd"] = max(self.stats["max_qdd"], float(np.abs(o.qd[:5] - self._qd_prev).max() / self.lim.dt))
        self._qd_prev = o.qd[:5].copy()
        hit = self.table_contacts()
        if hit:
            raise Fail("table_collision", ",".join(hit))

    def table_contacts(self, cube_ok=True):
        d, out = self.sim.d, []
        for i in range(d.ncon):
            a, b = int(d.contact.geom[i][0]), int(d.contact.geom[i][1])
            if self.table_id in (a, b):
                other = b if a == self.table_id else a
                if other in self.arm_geoms or (other == self.cube_id and not cube_ok):
                    out.append(self.sim.m.geom(other).name)
        return out

    def cube_contacts(self):
        """Nazwy geomów ramienia dotykających kostki (pady, dłoń, korpus)."""
        d, out = self.sim.d, []
        for i in range(d.ncon):
            a, b = int(d.contact.geom[i][0]), int(d.contact.geom[i][1])
            if self.cube_id in (a, b) and (b if a == self.cube_id else a) in self.arm_geoms:
                out.append(self.sim.m.geom(b if a == self.cube_id else a).name)
        return out

    def cube_on_table(self):
        d = self.sim.d
        return any({int(d.contact.geom[i][0]), int(d.contact.geom[i][1])} == {self.table_id, self.cube_id}
                   for i in range(d.ncon))

    def held_offset(self):
        """Położenie kostki względem stałej szczęki w układzie chwytaka [m] (niezależne od obrotu bazy)."""
        d = self.sim.d
        return d.body("gripper").xmat.reshape(3, 3).T @ (d.body("cube").xpos - d.site("cs_fixed").xpos)

    def follow(self, path, mode, check=None):
        tg = profile(path, self.obs.q, self.cfg.v_max, self.cfg.a_max, self.lim.dt)
        for x in tg:
            self.tick(x, mode)
            if check:
                check()
        self.settle(np.asarray(path[-1])[:5], mode, check)

    def settle(self, tgt, mode, check=None):
        n = int(self.cfg.settle_max / self.lim.dt)
        for _ in range(n):
            if np.abs(self.obs.q[:5] - tgt).max() < self.cfg.settle_tol:
                return
            self.tick(tgt, mode)
            self.settle_ticks += 1
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

    # ---------- cykl ----------
    def where(self):
        """Nazwa miejsca, w którym leży kostka (w strefie zone, płasko, obrót ≤ yaw_tol), albo None."""
        p, yaw, tilt = cube_pose(self.sim)
        c = self.cfg
        for name in ("A", "B"):
            if (np.linalg.norm(p[:2] - getattr(c, name)) <= c.zone and math.degrees(tilt) <= c.tilt_tol
                    and abs(math.degrees(wrap90(yaw - self.yaw_nom[name]))) <= c.yaw_tol and p[2] < c.cube):
                return name
        return None

    def cycle(self):
        """Jeden pełny cykl. Zwraca dict pomiarów; porażka → Fail (po próbie odzyskania pozycji domowej)."""
        c, sim = self.cfg, self.sim
        rec = {"t_sim": {}, "t_wall": {}}
        if self.safety.fault:                             # zatrzaśnięty błąd: żaden cykl nie rusza przed clear()
            raise Fail("safety_fault", self.safety.fault)
        if self.sim.stopped:                              # fizyka zatrzymana: wznowienie tylko przez reset symulatora
            raise Fail("sim_error", f"symulator zatrzymany: {self.sim.stopped}")
        src = self.where()
        if src is None:
            p, yaw, tilt = cube_pose(sim)
            raise Fail("object_lost", f"kostka poza A/B: {np.round(p, 4).tolist()}, tilt {math.degrees(tilt):.1f}°")
        dst = "B" if src == "A" else "A"
        rec["src"], rec["dst"] = src, dst
        p, yaw, _ = cube_pose(sim)
        dev = np.linalg.norm(p[:2] - getattr(c, src))
        dyaw = abs(math.degrees(wrap90(yaw - self.yaw_nom[src])))
        if dev <= c.reuse_tol and dyaw <= c.reuse_yaw:
            P = self.plans[(src, dst)]
        else:   # kostka przesunięta: nowy plan chwytu z faktycznej pozycji; transport/odłożenie/powrót z cache
            self.stats["replans"] += 1
            try:
                P = {**self.plans[(src, dst)], **self.plan_pick(np.array([p[0], p[1], c.cube / 2]))}
            except ReachError as e:
                raise Fail("unreachable", str(e)) from e
        rec["src_dev_mm"], rec["src_dyaw_deg"] = dev * 1e3, dyaw
        clock = [sim.sim_time, time.perf_counter()]      # sim_time: odporny na reset MuJoCo (so101.SO101Sim)

        def mark(ph):
            rec["t_sim"][ph] = sim.sim_time - clock[0]
            rec["t_wall"][ph] = time.perf_counter() - clock[1]
            clock[:] = [sim.sim_time, time.perf_counter()]

        z_table = c.cube / 2
        # 1 podejście: szczęka otwarta, nad kostkę, pionowe zejście
        self.follow(P["approach_move"], "open")
        if self.obs.q[5] < c.q_clear:
            raise Fail("jaw_not_open", f"q szczęki {self.obs.q[5]:.2f} < {c.q_clear}")
        self.follow(P["approach_descend"], "open")
        p0 = cube_pose(sim)[0]
        if np.linalg.norm(p0[:2] - p[:2]) > 0.003:
            raise Fail("cube_pushed", f"kostka przesunięta przy zejściu o {np.linalg.norm(p0[:2] - p[:2]) * 1e3:.1f} mm")
        mark("approach")
        # 2 chwyt: zamykanie do kontaktu obu padów, narastanie siły, potwierdzenie siły
        tgt = np.asarray(P["approach_descend"][-1])[:5]
        if not self.wait(c.close_max, tgt, "close", until=lambda: self.grip.mode == "hold"):
            raise Fail("no_contact", f"touch {np.round(self.obs.touch, 2).tolist()}")
        self.wait(c.hold_settle, tgt, "hold")
        if min(self.obs.touch[:2]) < c.f_grip:
            raise Fail("weak_grip", f"touch {np.round(self.obs.touch, 2).tolist()} N < {c.f_grip}")
        off0 = self.held_offset()
        mark("grasp")

        def held():
            if min(self.obs.touch[:2]) < GripCfg().f_contact:
                raise Fail("slip", f"utrata kontaktu szczęk, touch {np.round(self.obs.touch, 2).tolist()}")
            s = np.linalg.norm(self.held_offset() - off0)
            if s > c.slip_tol:
                raise Fail("slip", f"kostka przesunięta w chwytaku o {s * 1e3:.1f} mm")

        # 3 podniesienie: kostka musi opuścić stół i jechać z chwytakiem
        self.follow(P["lift"], "hold", held)
        z = sim.d.body("cube").xpos[2] - z_table
        if z < 0.5 * c.h_transport or self.cube_on_table():
            raise Fail("lift_failed", f"spód kostki {z * 1e3:.1f} mm nad stołem")
        rec["lift_mm"] = z * 1e3
        mark("lift")

        # 4 transport: bez kontaktu kostki ze stołem
        def carried():
            held()
            if self.cube_on_table():
                raise Fail("cube_hit_table", "kontakt kostki ze stołem w transporcie")

        self.follow(P["transport"], "hold", carried)
        mark("transport")
        # 5 odłożenie: zejście, kontakt ze stołem, otwarcie, zwolnienie
        self.follow(P["place_descend"], "hold", held)
        tgt = np.asarray(P["place_descend"][-1])[:5]
        if not self.wait(0.2, tgt, "hold", until=self.cube_on_table):
            raise Fail("place_no_contact", f"spód kostki {(sim.d.body('cube').xpos[2] - z_table) * 1e3:.1f} mm")
        if not self.wait(c.open_max, tgt, "open", until=lambda: self.obs.q[5] >= c.q_clear):
            raise Fail("jaw_not_open", f"q szczęki {self.obs.q[5]:.2f} < {c.q_clear}")
        if max(self.obs.touch[:2]) > GripCfg().f_contact:
            raise Fail("release_failed", f"touch po otwarciu {np.round(self.obs.touch, 2).tolist()}")
        z_rel = sim.d.body("cube").xpos[2]
        mark("place")
        # 6 powrót: odejście w górę (kostka zostaje), dom
        self.follow(P["retreat"], "open")
        if sim.d.body("cube").xpos[2] - z_rel > 0.003:
            raise Fail("release_failed", "kostka uniesiona przy odejściu chwytaka")
        self.follow(P["home"], "open")
        mark("return")
        p, yaw, tilt = cube_pose(sim)
        err = np.linalg.norm(p[:2] - getattr(c, dst))
        rec.update(place_err_mm=err * 1e3, place_dyaw_deg=math.degrees(wrap90(yaw - self.yaw_nom[dst])),
                   tilt_deg=math.degrees(tilt))
        if self.where() != dst:
            raise Fail("place_out_of_zone", f"błąd {err * 1e3:.1f} mm, obrót {rec['place_dyaw_deg']:.1f}°, "
                                            f"przechył {math.degrees(tilt):.1f}°")
        rec["home_err_rad"] = float(np.abs(self.obs.q[:5] - self.home[:5]).max())
        return rec

    def not_ready(self):
        """Powód, dla którego następny cykl NIE może ruszyć bez ingerencji, albo None. Czyta bieżący stan (ostatnia
        obserwacja, kontakty fizyki, warstwa bezpieczeństwa), nie historię ruchu."""
        o, c = self.obs, self.cfg
        if self.safety.fault:
            return f"safety_latched: {self.safety.fault}"
        if self.sim.stopped:
            return f"sim_stopped: {self.sim.stopped}"
        e = float(np.abs(o.q[:5] - self.home[:5]).max())
        if e >= c.settle_tol:
            return f"arm_not_home: {e:.3f} rad ≥ {c.settle_tol}"
        if o.q[5] < c.q_clear:
            return f"jaw_not_open: {o.q[5]:.2f} < {c.q_clear}"
        if max(o.touch) > GripCfg().f_contact:
            return f"pads_loaded: touch {np.round(o.touch, 2).tolist()} N"
        hit = self.table_contacts() + self.cube_contacts()
        if hit:
            return "contact: " + ",".join(hit)
        if self.where() is None:
            return f"cube_lost: {np.round(cube_pose(self.sim)[0], 4).tolist()}"
        return None

    def recover(self, reason=None):
        """Po porażce cyklu (reason = jej przyczyna): otwórz szczękę, odejdź w górę o h_above, wróć do domu — bez resetu
        symulacji. Zwraca True TYLKO gdy stan po ruchu jest potwierdzony (not_ready() is None: ramię w domu, szczęka
        otwarta, pady i ramię bez kontaktu, kostka w A/B, brak błędu bezpieczeństwa i symulatora); inaczej opis powodu.
        Nie kasuje zatrzaśniętego błędu SafetyLayer i nie rusza ramienia po przyczynach z NO_MOTION."""
        if self.safety.fault:
            return f"safety_latched: {self.safety.fault}"
        if self.sim.stopped or reason in NO_MOTION:
            return f"no_motion: {reason or self.sim.stopped}"
        try:
            self.obs = self.sim.observe()                 # świeży pomiar (ostatni mógł być powodem porażki)
            q = self.obs.q.copy()
            self.wait(0.5, q[:5], "open", until=lambda: self.obs.q[5] >= self.cfg.q_clear)
            up, ep, ea = ik(self.sim, self.sim.d.site("cs_fixed").xpos + [0, 0, self.cfg.h_above], q, cfg=self.rcfg,
                            point="cs_fixed")
            for path in ([q + (up - q) * i / 20 for i in range(1, 21)] if ep < 0.01 else [],
                         [up + (self.home - up) * i / 20 for i in range(1, 21)]):
                if path:
                    tg = profile(path, self.obs.q, 0.5, 2.0, self.lim.dt)
                    for x in tg:
                        self.tick(x, "open")
            self.settle(self.home[:5], "open")
        except Fail as e:
            return f"{e.reason}: {e.detail}"
        return self.not_ready() or True

    def reset_scene(self):
        """Reset SYMULATORA (teleport ramienia do domu i kostki do A) — na prawdziwym stanowisku ręczna ingerencja.
        Nie jest potwierdzeniem bezpieczeństwa: ta sama SafetyLayer, zatrzaśnięty błąd i statystyki zostają."""
        self.sim.reset(self.home, cube_pose=(*self.cfg.A, self.yaw_nom["A"]))
        self.obs = self.sim.observe()
        self.safety.prev = None                           # pierwszy cel po resecie = pomiar (bez skoku)
        self._qd_prev = self.obs.qd[:5].copy()            # bez fałszywego skoku max_qdd po teleportacji


def git_state():
    def g(*a):
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    import hashlib
    files = ("pick_place.py", "so101.py", "reach.py", "grip.py", "safety.py")
    sha = {f: hashlib.sha256(open(os.path.join(ROOT, "flymind", f), "rb").read()).hexdigest()[:16] for f in files}
    return dict(commit=g("rev-parse", "HEAD"), branch=g("branch", "--show-current"), sha256_16=sha,
                dirty_files=g("status", "--porcelain", "--", "flymind/pick_place.py", "flymind/so101.py",
                              "flymind/reach.py", "flymind/grip.py", "flymind/safety.py").splitlines())


def series(cfg, seed, n, cell=None):
    """n kolejnych cykli bez resetu. Po porażce cyklu `outcome` mówi, co się stało — to trzy różne rzeczy:
      "recovered"  recover() wrócił do domu i potwierdził stan; następny cykl rusza BEZ resetu
      "reset"      stanu nie potwierdzono → reset symulatora (liczony w `resets`; na sprzęcie = ręczna ingerencja,
                   której czas NIE jest wliczony — dlatego `continuous` = brak resetów jawnych i samoczynnych MuJoCo)
      "halted"     zatrzaśnięty błąd SafetyLayer → seria staje (bez resetu, bez dalszych cykli) do jawnego clear()
    Nieoczekiwany wyjątek też kończy serię. Seria przerwana ma complete=False i stopped_by=powód (nie jest udana).
    Czas symulacji z sim.sim_time (monotoniczny przez resety). cell: gotowe stanowisko (testy)."""
    import mujoco
    cell = cell or Cell(cfg, seed)
    sim, cfg = cell.sim, cell.cfg
    cycles, resets, auto0, stopped_by = [], 0, sim.stats["auto_resets"], None
    t_sim0, t_wall0 = sim.sim_time, time.perf_counter()
    for i in range(n):
        q_start = cell.obs.q.copy()
        s0, w0, a0 = sim.sim_time, time.perf_counter(), sim.stats["auto_resets"]
        try:
            try:
                rec = cell.cycle()
                rec["ok"], rec["reason"] = True, None
            except Fail as e:
                rec = {"ok": False, "reason": e.reason, "detail": e.detail, "t_to_fail_sim": sim.sim_time - s0}
                rec["recover"] = cell.recover(e.reason)
                if cell.safety.fault:
                    rec["outcome"], stopped_by = "halted", f"safety_latched: {cell.safety.fault}"
                elif rec["recover"] is True:
                    rec["outcome"] = "recovered"
                else:
                    resets += 1
                    rec["reset"], rec["outcome"] = True, "reset"
                    cell.reset_scene()
        except (Exception, KeyboardInterrupt) as e:      # noqa: BLE001 — zapisujemy to, co jest, jako niekompletne
            rec = {"ok": False, "reason": "exception", "detail": repr(e)}
            stopped_by = f"exception: {e!r}"
        rec.update(i=i, cycle_sim=sim.sim_time - s0, cycle_wall=time.perf_counter() - w0,
                   start_drift_rad=float(np.abs(q_start[:5] - cell.home[:5]).max()), start_jaw=float(q_start[5]))
        if sim.stats["auto_resets"] > a0:
            rec["auto_resets"] = sim.stats["auto_resets"] - a0
        cycles.append(rec)
        if stopped_by:
            break
    T_sim, T_wall = sim.sim_time - t_sim0, time.perf_counter() - t_wall0
    ok, auto = sum(r["ok"] for r in cycles), sim.stats["auto_resets"] - auto0
    return dict(seed=seed, n=n, ok=ok, resets=resets, auto_resets=auto, continuous=resets == 0 and auto == 0,
                complete=stopped_by is None, stopped_by=stopped_by,
                T_sim=T_sim, T_wall=T_wall, plan_wall=cell.plan_wall,
                per_h_sim=ok / T_sim * 3600 if T_sim else 0.0, per_h_wall=ok / T_wall * 3600,
                scene=dict(cube_mass=cell.scene.cube_mass, cube_friction=cell.scene.cube_friction[0],
                           cube_size=cell.scene.cube_size, timestep=cell.scene.timestep),
                stats={k: (v if not isinstance(v, float) else round(v, 5)) for k, v in cell.stats.items()},
                safety_stats=cell.safety.stats["per_source"], mujoco=mujoco.__version__, cycles=cycles)


def summarize(runs):
    cyc = [c for r in runs for c in r["cycles"]]
    ok = [c for c in cyc if c["ok"]]
    ts = np.array([c["cycle_sim"] for c in ok]) if ok else np.array([np.nan])
    tw = np.array([c["cycle_wall"] for c in ok]) if ok else np.array([np.nan])
    T_sim, T_wall = sum(r["T_sim"] for r in runs), sum(r["T_wall"] for r in runs)
    reasons = {}
    for c in cyc:
        if not c["ok"]:
            reasons[c["reason"]] = reasons.get(c["reason"], 0) + 1
    q = lambda a: [round(float(x), 3) for x in np.percentile(a, [0, 25, 50, 75, 100])]  # noqa: E731
    return dict(attempts=len(cyc), ok=len(ok), success_rate=len(ok) / len(cyc), fail_reasons=reasons,
                resets=sum(r["resets"] for r in runs), auto_resets=sum(r.get("auto_resets", 0) for r in runs),
                continuous=all(r.get("continuous", r["resets"] == 0) for r in runs),
                complete=all(r.get("complete", True) for r in runs) and len(cyc) == sum(r["n"] for r in runs),
                recovered=sum(c.get("outcome") == "recovered" for c in cyc),
                cycle_sim_s_min_q1_med_q3_max=q(ts), cycle_wall_s_min_q1_med_q3_max=q(tw),
                phase_sim_s_median={p: round(float(np.median([c["t_sim"][p] for c in ok])), 3) for p in PHASES} if ok else {},
                phase_wall_s_median={p: round(float(np.median([c["t_wall"][p] for c in ok])), 4) for p in PHASES} if ok else {},
                T_sim_s=round(T_sim, 2), T_wall_s=round(T_wall, 2),
                ops_per_h_sim=round(len(ok) / T_sim * 3600, 1) if T_sim else 0.0,
                ops_per_h_wall=round(len(ok) / T_wall * 3600, 1),
                place_err_mm_med_max=[round(float(np.median([c["place_err_mm"] for c in ok])), 2),
                                      round(float(max(c["place_err_mm"] for c in ok)), 2)] if ok else None,
                start_drift_rad_max=round(max(c["start_drift_rad"] for c in cyc), 4),
                replans=sum(r["stats"]["replans"] for r in runs),
                max_qd=max(r["stats"]["max_qd"] for r in runs), min_margin=min(r["stats"]["min_margin"] for r in runs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    ap.add_argument("--cycles", type=int, default=50)
    ap.add_argument("--v", type=float, default=PPCfg.v_max)
    ap.add_argument("--a", type=float, default=PPCfg.a_max)
    ap.add_argument("--q-pre", type=float, default=PPCfg.q_pre)
    ap.add_argument("--home", type=float, nargs=6, default=PPCfg.home)
    ap.add_argument("--tag", default="run")
    a = ap.parse_args()
    cfg = replace(PPCfg(), v_max=a.v, a_max=a.a, q_pre=a.q_pre, home=tuple(a.home))
    os.makedirs(OUT, exist_ok=True)
    paths = [os.path.join(OUT, f"{a.tag}{x}.json") for x in ("", ".INCOMPLETE")]
    if any(os.path.exists(p) for p in paths):            # wyników nie nadpisujemy — nowa seria = nowy --tag
        sys.exit(f"istnieje już wynik o tagu {a.tag!r} w {OUT} — wybierz inny --tag")
    runs = []
    for s in a.seeds:
        r = series(cfg, s, a.cycles)
        runs.append(r)
        print(f"seed {s}: {r['ok']}/{r['n']} ok, resets {r['resets']}, T_sim {r['T_sim']:.1f} s, "
              f"T_wall {r['T_wall']:.1f} s, fails {[c['reason'] for c in r['cycles'] if not c['ok']]}", flush=True)
        if not r["complete"]:                             # zatrzaśnięty błąd / wyjątek: kolejnych ziaren nie ruszamy
            print(f"SERIA PRZERWANA: {r['stopped_by']}", flush=True)
            break
    summ = summarize(runs)
    complete = summ["complete"] and len(runs) == len(a.seeds)
    out = dict(tag=a.tag, complete=complete, argv=sys.argv, cfg=asdict(cfg), git=git_state(),
               python=sys.version.split()[0], summary=summ, runs=runs)
    path = paths[0] if complete else paths[1]
    with open(path, "x") as f:
        json.dump(out, f, indent=1, default=float)
    print(json.dumps(summ, indent=1))
    print("zapisano" if complete else "NIEKOMPLETNE — zapisano", path)
    sys.exit(0 if complete else 1)


if __name__ == "__main__":
    main()
