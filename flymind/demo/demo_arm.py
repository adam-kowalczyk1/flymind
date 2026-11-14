"""flymind/demo/demo_arm.py — pokaz „sieć z konektomu muchy steruje ramieniem SO-101” (krok 6). SYMULACJA MuJoCo. Tylko wizualizacja.

Scena i sterowanie to benchmark czuciowej manipulacji (object_handling.World + joint_net.ArmGrip, ramię „N”): jeden przedmiot
z SETS["base"], stawy 1–3 (+ staw 4 przy --roll) z sieci T1 L + T2 L (ArmNet), szczęka z osobnej sieci T2 L (LegJaw).
Pokaz NIE liczy niczego po swojemu: woła joint_net.run_trial na tych samych obiektach (ArmNet, LegJaw, ArmGrip, ForceWorld);
dołożone są tylko haki, które PODGLĄDAJĄ (podklasy w tym pliku: odczyt impulsów z SparseALIF.run, odczyt komendy z SafetyLayer.step,
synchronizacja okna po World.step). test_demo_arm.py sprawdza, że wynik i trajektoria są identyczne co do bitu z joint_net.run_trial
oraz że przechwytywanie impulsów niczego nie zmienia.

Co jest czym (ta sama linia jest na panelu):
  DANE         połączenia i przekaźniki neuronów T1 L / T2 L z MaleCNS v1.0 (liczba neuronów jest liczona z sieci i pokazana na panelu)
  MODEL        dynamika ALIF (parametry ogólne), J0, znak Glu, kodowanie dotyku 40 mV/N, podział szczecinek T1 L na pady
  INŻYNIERIA   enkodery, dekoder Δcel = s·k·Δr (filtr 50 ms), bezpiecznik stołu, SafetyLayer, rusztowanie klasyczne
               (planowanie IK, fazy, otwarcie szczęki przed chwytem i nad pudełkiem)
Sieć dostaje wyłącznie sygnały z receptorów (dotyk padów); żadnego neuronu nie pobudza się sztucznie. To nie żywa mucha.

Uruchom (macOS, okno interaktywne wymaga mjpython; klawisz 6 = pauza):
  .venv/bin/mjpython flymind/demo/demo_arm.py --item cube_S/hard_grip --seed 20951
  .venv/bin/python -I -B flymind/demo/demo_arm.py --media flymind/demo/media_arm_20261113 --seed 20951   (bez okna, NOWY katalog)
  .venv/bin/python -I -B flymind/demo/demo_arm.py --bench --seed 20951                                  (pomiar wydajności)
Ziarno próby = seed·1000 + indeks_przedmiotu·10 + pose (jak joint_net.main).

Wydajność (zmierzone 2026-11-13, M-seria, maszyna obciążona innymi procesami; cube_S/hard_grip, ziarno 20951, 1 próba):
  bez panelu (przechwytywanie impulsów, bez okna): 1791 taktów w 33,8 s = 53 takty/s, współczynnik czasu rzeczywistego 0,53×
  z panelem w osobnym procesie (20 kl./s, bez okna): 1791 taktów w 38,0 s = 47 taktów/s, 0,47×
  (pierwsze, zakłócone powtórzenie: 11 i 48 taktów/s, 0,11× i 0,48× — średnia obciążenia maszyny ≈ 200; takt 10 ms = 100 taktów/s
  to 1,0×). Okno interaktywne NIE było mierzone (brak podglądu); nagranie --media: 447 klatek w 172 s.
  Sieci: ArmNet 2593 + LegJaw 1507 = 4100 neuronów (liczone z konektomu, nie ~2900).
"""
import sys

sys.dont_write_bytecode = True
import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
import time  # noqa: E402
from contextlib import contextmanager  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FLY = os.path.dirname(HERE)
STEP2 = os.path.join(FLY, "experiments", "step2_whole_arm")
sys.path.insert(0, FLY)
sys.path.insert(0, HERE)                      # `demo` = demo.py, nie pakiet przestrzeni nazw flymind/demo
sys.path.insert(0, STEP2)
import joint_net as JN  # noqa: E402
import object_handling as oh  # noqa: E402
import sensory_manipulation as sm  # noqa: E402
import visual_path  # noqa: E402
from fly_jaw import PRESS, RELEASE  # noqa: E402
from leg_circuit import SENSORY, select  # noqa: E402

import demo as D  # noqa: E402  (tylko pomocnicze: _fig, _rgb, text_image, Video, overlay, add_fill_light, _out_ok; demo.py bez zmian)

RASTER = 500                                    # kolumny rastra = ostatnie 500 ms po 1 ms
JNAME = {0: "shoulder_pan", 1: "shoulder_lift", 2: "elbow_flex", 3: "wrist_flex", 4: "wrist_roll", 5: "gripper"}
KIND_COL = {"rec": (78, 168, 255), "IN": (210, 210, 210), "MN": (255, 159, 67), "?": (255, 80, 80)}
KIND_TXT = {"rec": "receptory", "IN": "interneurony", "MN": "MN", "?": "inne"}
SHOT = ((0.20, 0.0, 0.09), 0.72, -40.0, -30.0)  # kamera swobodna: lookat, odległość, azymut, elewacja (jak D.SHOTS)
HONEST = ("DANE: połączenia i przekaźniki neuronów T1 L i T2 L z MaleCNS v1.0.\n"
          "MODEL: dynamika ALIF (parametry ogólne), J0, znak Glu, kodowanie dotyku, podział szczecinek na pady.\n"
          "INŻYNIERIA: enkodery, dekoder Δcel = s·k·Δr (filtr 50 ms), bezpiecznik stołu, SafetyLayer,\n"
          "rusztowanie klasyczne (IK, fazy, otwarcie szczęki). Symulacja — nie żywa mucha.")


class Quit(Exception):
    """Okno zamknięte przez użytkownika — przerwanie próby."""


# ---------------------------------------------------------------- przechwytywanie (tylko odczyt) ---------------------
def _tap(net, sink):
    """Opakowuje net.run: zwraca TO SAMO co oryginał, kopię impulsów oddaje sink."""
    run0 = net.run

    def run(X, n):
        s = run0(X, n)
        sink(s)
        return s

    net.run = run


class CapArmNet(JN.ArmNet):
    sink = None

    def reset(self):
        super().reset()
        _tap(self.net, lambda s: self.sink and self.sink(s))


class CapLegJaw(sm.LegJaw):
    sink = None

    def reset(self):
        super().reset()
        _tap(self.net, lambda s: self.sink and self.sink(s))


_ARMGRIP = JN.ArmGrip


class HookGrip(_ARMGRIP):
    """ArmGrip bez zmian w sterowaniu: po każdym takcie oddaje stan do Live; komendę czyta z SafetyLayer.step (opakowanie)."""
    live = None

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.last_cmd = None
        s0 = self.safety.step

        def step(cmd, *args, **kwargs):
            self.last_cmd = cmd
            return s0(cmd, *args, **kwargs)

        self.safety.step = step

    def tick(self, tgt, mode):
        super().tick(tgt, mode)
        self.ticks_seen = getattr(self, "ticks_seen", 0) + 1
        if HookGrip.live is not None:
            HookGrip.live.on_tick(self, mode)


class HookWorld(JN.ForceWorld):
    """ForceWorld + wyjście (okno / nagranie) po każdym kroku; skrót SHA całej trajektorii (q_t, tau, obserwacje)."""
    out = None
    hasher = None

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        if HookWorld.out is not None:
            HookWorld.out.on_world(self)

    def step(self, q_t, tau):
        out = HookWorld.out
        with (out.lock() if out is not None else _nolock()):
            obs = super().step(q_t, tau)
        if HookWorld.hasher is not None:
            HookWorld.hasher.update(np.r_[q_t, tau, obs.q, obs.qd, obs.touch].tobytes())
        if out is not None:
            out.after_step(self)
        return obs


@contextmanager
def _nolock():
    yield


@contextmanager
def patched(live=None, out=None):
    """Na czas jednej próby podmienia ForceWorld i ArmGrip w joint_net (wywołania run_trial zostają bez zmian)."""
    o = (JN.ForceWorld, JN.ArmGrip, HookGrip.live, HookWorld.out, HookWorld.hasher)
    JN.ForceWorld, JN.ArmGrip, HookGrip.live, HookWorld.out, HookWorld.hasher = HookWorld, HookGrip, live, out, hashlib.sha256()
    try:
        yield HookWorld.hasher
    finally:
        JN.ForceWorld, JN.ArmGrip, HookGrip.live, HookWorld.out, HookWorld.hasher = o


# ---------------------------------------------------------------- konstrukcja sieci ---------------------------------
def make_nets(glu, ac, capture=True):
    """(jaw, drv, bodies_arm). capture=False → zwykłe LegJaw i ArmNet (referencja), bodies_arm=None."""
    fc = sm.FlyCfg(glu_sign=glu, trigger="search")
    if not capture:
        return fc, sm.LegJaw(fc, touch=True, proprio=False), JN.ArmNet(glu, ac), None
    cap, build0 = {}, JN.build

    def build(*a, **k):
        spec = build0(*a, **k)
        cap["bodies"] = [int(b) for b in spec.bodies]
        return spec

    JN.build = build
    try:
        drv = CapArmNet(glu, ac)
    finally:
        JN.build = build0
    return fc, CapLegJaw(fc, touch=True, proprio=False), drv, cap["bodies"]


class Live:
    """Stan pokazu: grupy neuronów, raster 500 ms (kolumny w kolejności grup), filtrowane częstości pul, tekst panelu."""

    def __init__(self, drv, jaw, ac, bodies_arm, label, keep=False):
        ann = pd.read_feather(visual_path.ANN, columns=["bodyId", "type", "superclass"]).set_index("bodyId")
        ty, sc = ann.type, ann.superclass
        bodies_jaw = select(jaw.c.leg, jaw.c.side)[0]
        t2 = set(select("T2", "L")[0])
        self.Na, self.Nj = drv.N, jaw.N
        if len(bodies_arm) != self.Na or len(bodies_jaw) != self.Nj:
            raise ValueError("liczba ciał ≠ liczba neuronów sieci")
        self.N, self.drv, self.jaw, self.ac, self.label = self.Na + self.Nj, drv, jaw, ac, label
        kind = lambda b: "rec" if sc[b] in SENSORY else "IN" if sc[b] == "vnc_intrinsic" else "MN" if sc[b] == "vnc_motor" else "?"  # noqa: E731
        groups = {}
        for i, b in enumerate(bodies_arm):
            groups.setdefault(("ArmNet", "T2 L" if b in t2 else "T1 L", kind(b)), []).append(i)
        for i, b in enumerate(bodies_jaw):
            groups.setdefault(("LegJaw", "T2 L", kind(b)), []).append(self.Na + i)
        rank = {"rec": 0, "IN": 1, "MN": 2, "?": 3}
        keys = sorted(groups, key=lambda k: (k[0] != "ArmNet", k[1] != "T2 L" if k[0] == "ArmNet" else 0, rank[k[2]]))
        self.groups = [dict(net=k[0], leg=k[1], kind=k[2], n=len(groups[k]), idx=np.array(groups[k])) for k in keys]
        self.order = np.concatenate([g["idx"] for g in self.groups])
        if sorted(self.order.tolist()) != list(range(self.N)):
            raise ValueError("grupy nie pokrywają sieci")
        for g in self.groups:
            g["label"] = f"{g['net']} · {g['leg']} {KIND_TXT[g['kind']]} ({g['n']})"
        self.ty_arm, self.ty_jaw = [ty[b] for b in bodies_arm], [ty[b] for b in bodies_jaw]
        # pule per typ MN (POS/NEG) — ta sama pula indeksów co w ArmNet.idx['pools'], rozbita po typie (tylko do wyświetlania)
        self.pool = {}
        for j, (p, n) in drv.idx["pools"].items():
            self.pool[j] = [[(nm, [i for i in ix if self.ty_arm[i] == nm]) for nm in names] for names, ix in zip(JN.POOLS[j], (p, n))]
            for side, ix in zip(self.pool[j], (p, n)):
                if sorted(i for _, v in side for i in v) != sorted(ix):
                    raise ValueError(f"pula stawu {j}: typy nie pokrywają indeksów")
        self.pool[5] = [[(nm, [i for i in ix if self.ty_jaw[i] == nm]) for nm in names] for names, ix in
                        ((PRESS, jaw.press), (RELEASE, jaw.release))]
        self.rt = {(j, s, nm): 0.0 for j, sides in self.pool.items() for s, side in enumerate(sides) for nm, _ in side}
        self.r_chk = np.zeros((5, 2))                           # niezależne odtworzenie ArmNet.r z przechwyconych impulsów
        self.ring, self.ptr, self.n_ticks, self.n_spikes = np.zeros((RASTER, self.N), bool), 0, 0, 0
        self.keep, self.kept = keep, []
        self.s_arm = self.s_jaw = None
        self.state, self.seen = {}, set()
        self.t0 = time.perf_counter()
        drv.sink, jaw.sink = self._arm, self._jaw

    # --- hak impulsów
    def _arm(self, s):
        self.s_arm = s.copy()

    def _jaw(self, s):
        self.s_jaw = s.copy()

    def on_tick(self, ctl, mode):
        sa, sj = self.s_arm, self.s_jaw
        self.s_arm = self.s_jaw = None
        if sa is None or sj is None:
            raise RuntimeError("takt bez impulsów obu sieci")
        c = self.ac
        both = np.concatenate([sa, sj], axis=1)
        k = len(both)
        self.ring[(self.ptr + np.arange(k)) % RASTER] = both[:, self.order]
        self.ptr, self.n_ticks, self.n_spikes = (self.ptr + k) % RASTER, self.n_ticks + 1, self.n_spikes + int(both.sum())
        if self.keep:
            self.kept.append(both)
        a = 0.01 / c.tau_r
        for j, sides in self.pool.items():                      # filtr τ_r jak ArmNet i LegJaw (tylko podgląd per typ)
            s = sa if j != 5 else sj
            for si, side in enumerate(sides):
                for nm, ix in side:
                    now = float(s[:, ix].mean()) * 1000.0 / (c.dt_ms if j != 5 else 1.0) if ix else 0.0
                    self.rt[(j, si, nm)] += a * (now - self.rt[(j, si, nm)])
        for j, (p, n) in self.drv.idx["pools"].items():
            now = np.array([sa[:, p].mean(), sa[:, n].mean()]) * 1000.0 / c.dt_ms
            self.r_chk[j] += a * (now - self.r_chk[j])
        cmd, o = ctl.last_cmd, ctl.obs
        self.seen |= set(cmd.sources.values()) if cmd else set()
        self.state = dict(dq=ctl.dq.copy(), r=self.drv.r.copy(), r_jaw=(self.jaw.r_press, self.jaw.r_release),
                          tau_fly=float(ctl.tau_fly), cmd_tau=None if cmd is None else cmd.jaw_torque,
                          src=dict(cmd.sources) if cmd else {}, active=sorted(ctl.active), lifting=ctl.lifting, mode=mode,
                          phase=ctl.w.phase, t=o.t, touch=np.asarray(o.touch)[:2].copy(), q5=float(o.q[5]),
                          guard=ctl.guard, flags=dict(ctl.stats["flags"]))

    # --- panel
    def lines(self):
        s, c = self.state, self.ac
        if not s:
            return "", ""
        L = [f"0 {JNAME[0]:<13s} klasyczny (IK rusztowania), poza siecią"]
        for j in range(1, 6):
            if j < 5:
                dq, applied = s["dq"][j], j in s["active"]
                src = s["src"].get(j, "?")
                head = f"{j} {JNAME[j]:<13s} Δcel {dq:+.5f} rad/takt  [{src}]" + ("" if applied else "  (wyjście sieci nieużywane w tej fazie)")
                rp, rn = s["r"][j]
            else:
                head = (f"{j} {JNAME[j]:<13s} moment sieci {s['tau_fly']:+.3f} N·m  (rozkaz "
                        f"{0.0 if s['cmd_tau'] is None else s['cmd_tau']:+.3f})  [{s['src'].get('jaw', '?')}]")
                rp, rn = s["r_jaw"]
            L.append(head)
            for si, (lab, r) in enumerate((("POS", rp), ("NEG", rn))):
                parts = " + ".join(f"{nm} {self.rt[(j, si, nm)]:.1f}" for nm, _ in self.pool[j][si])
                L.append(f"   {lab} {r:6.1f} Hz | {parts}")
        c1 = "\n".join(L)
        d = [f"faza: {s['phase']:<10s} tryb szczęki: {s['mode']:<8s} t_sym {s['t']:6.2f} s   takt {self.n_ticks}",
             f"dotyk padów [N]: stały {s['touch'][0]:.2f}, ruchomy {s['touch'][1]:.2f}  → szczecinki T2 L"
             f"{' i T1 L' if 'padsT1' in c.inputs else ''} ({c.touch_mV_per_N:.0f} mV/N, max {c.touch_max_mV:.0f} mV)",
             f"bezpiecznik stołu: {s['guard']} interwencji; flagi SafetyLayer: {s['flags'] or 'brak'}"]
        return c1, "\n".join(d)

    def snapshot(self):
        c1, c2 = self.lines()
        return dict(raster=np.roll(self.ring, -self.ptr, axis=0), joints=c1, decoder=c2,
                    head=f"{self.label}", count=f"neurony: ArmNet {self.Na} + LegJaw {self.Nj} = {self.N}   "
                    f"impulsów w ostatnim takcie: {int(self.ring[(self.ptr - 10 + np.arange(10)) % RASTER].sum()) if self.n_ticks else 0}",
                    static=[(g["label"], g["kind"], g["net"], g["n"]) for g in self.groups])


# ---------------------------------------------------------------- panel (matplotlib Agg) ----------------------------
class Panel:
    """Panel (prawa strona): raster wszystkich neuronów (max-pooling wierszy w obrębie grupy, by pojedyncze impulsy nie znikały),
    tabela stawów, dekoder, linia uczciwości."""

    def __init__(self, w, h, static):
        self.w, self.h = w, h
        self.fig, self.canvas = D._fig(w, h)
        u = h / 900.0
        f = self.fig
        N = sum(g[3] for g in static)
        self.R = max(120, int(h * 0.35))
        self.rows = [min(n, max(3, round(n / N * self.R))) for _, _, _, n in static]
        self.starts, self.rowcol, y0, self.mid, off = [], [], 0, [], 0
        for (lab, kind, net, n), r in zip(static, self.rows):
            b = np.linspace(0, n, r + 1).astype(int)[:-1]
            self.starts += (b + off).tolist()
            off += n
            self.rowcol += [KIND_COL[kind]] * r
            self.mid.append(y0 + r / 2)
            y0 += r
        self.rowcol, self.nrow, self.bounds = np.array(self.rowcol, np.uint8), y0, np.cumsum([0] + self.rows)
        f.text(0.02, 0.985, "FlyMind: sieć z konektomu muchy steruje ramieniem SO-101 (MuJoCo)", fontsize=10.5 * u,
               weight="bold", va="top", color="#e6edf3")
        self.head = f.text(0.02, 0.958, "", fontsize=7.0 * u, va="top", family="monospace", color="#c9d1d9", linespacing=1.25)
        self.count = f.text(0.02, 0.918, "", fontsize=9.5 * u, va="top", weight="bold", color="#ffd166")
        ax = self.ax = f.add_axes([0.235, 0.535, 0.745, 0.35], facecolor="#000")
        self.ras = ax.imshow(np.zeros((self.nrow, RASTER, 3), np.uint8), aspect="auto", interpolation="nearest")
        ax.set_yticks(self.mid, [g[0] for g in static], fontsize=6.4 * u, color="#c9d1d9")
        ax.set_xticks([0, RASTER - 1], ["−500 ms", "teraz"], fontsize=7 * u, color="#9aa7b4")
        ax.tick_params(length=2 * u)
        for sp in ax.spines.values():
            sp.set_color("#3a4450")
        for i, (g, y) in enumerate(zip(static, self.bounds[1:-1])):
            ax.axhline(y - 0.5, color="#8a96a3" if static[i][2] != static[i + 1][2] else "#3a4450",
                       lw=(1.6 if static[i][2] != static[i + 1][2] else 0.7) * u)
        ax.set_title("impulsy wszystkich neuronów (1 kolumna = 1 ms; wiersz = grupa wierszy neuronów, jasny = ≥1 impuls)",
                     fontsize=7.4 * u, color="#e6edf3", loc="left", pad=3 * u)
        f.text(0.02, 0.490, "stawy: wyjście sieci (częstości pul POS/NEG po filtrze 50 ms, [Hz]) → Δcel na takt 10 ms",
               fontsize=8.4 * u, weight="bold", color="#e6edf3", va="top")
        self.joints = f.text(0.02, 0.466, "", fontsize=6.9 * u, va="top", family="monospace", color="#d0d7de", linespacing=1.28)
        f.text(0.02, 0.240, "dekoder, źródła komend i faza benchmarku", fontsize=8.4 * u, weight="bold", color="#e6edf3", va="top")
        self.dec = f.text(0.02, 0.216, "", fontsize=6.9 * u, va="top", family="monospace", color="#d0d7de", linespacing=1.3)
        f.text(0.02, 0.105, HONEST, fontsize=6.9 * u, va="top", color="#8fbf8f", linespacing=1.35)
        self.cache = None

    def render(self, snap):
        R = snap["raster"]                                       # (500, N) kolumny w kolejności grup
        pooled = np.maximum.reduceat(R, self.starts, axis=1).T     # (nrow, 500)
        self.ras.set_data(pooled[..., None] * self.rowcol[:, None, :])
        self.head.set_text(snap["head"])
        self.count.set_text(snap["count"])
        self.joints.set_text(snap["joints"])
        self.dec.set_text(snap["decoder"])
        self.canvas.draw()
        return D._rgb(self.canvas, copy=False)


def panel_worker(conn, shm_name):
    """Osobny proces: snap → Panel.render → obraz do pamięci współdzielonej (symulacja nie czeka na rysowanie)."""
    from multiprocessing import shared_memory
    shm, panels = shared_memory.SharedMemory(name=shm_name), {}
    try:
        while True:
            msg = conn.recv()
            if msg is None:
                break
            snap, w, h = msg
            p = panels.get((w, h)) or panels.setdefault((w, h), Panel(w, h, snap["static"]))
            img = p.render(snap)
            np.ndarray(img.shape, np.uint8, buffer=shm.buf)[:] = img
            conn.send(img.shape)
    finally:
        shm.close()


class PanelProc:
    def __init__(self, nbytes=48 << 20):
        import multiprocessing as mp
        from multiprocessing import shared_memory
        os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
        self.shm = shared_memory.SharedMemory(create=True, size=nbytes)
        ctx = mp.get_context("spawn")
        self.conn, child = ctx.Pipe()
        self.p = ctx.Process(target=panel_worker, args=(child, self.shm.name), daemon=True)
        self.p.start()
        self.busy = False

    def request(self, snap, w, h):
        if self.busy or w * h * 3 > self.shm.size:
            return False
        self.conn.send((snap, w, h))
        self.busy = True
        return True

    def poll(self):
        if not (self.busy and self.conn.poll()):
            return None
        self.busy = False
        shape = self.conn.recv()
        return np.ndarray(shape, np.uint8, buffer=self.shm.buf)

    def close(self):
        try:
            self.conn.send(None)
            self.p.join(3)
        finally:
            if self.p.is_alive():
                self.p.terminate()
            self.shm.close()
            self.shm.unlink()


# ---------------------------------------------------------------- wyjścia: okno, nagranie, pomiar ---------------------
def set_cam(cam, w=None, shift_px=0.0, vp_h=None, fovy=45.0):
    D.apply_cam(cam, SHOT, None, shift_px=shift_px, vp_h=vp_h, fovy=fovy)


class WindowOut:
    """Okno interaktywne (mjpython): scena MuJoCo po lewej, panel jako nakładka po prawej (jak demo.py). Czas rzeczywisty × speed."""

    def __init__(self, live, speed=1.0, seconds=0.0, panel_fps=20.0):
        self.live, self.speed, self.seconds, self.panel_fps = live, speed, seconds, panel_fps
        self.keys, self.paused, self.v, self.img, self.size = [], False, None, None, None
        self.pp, self.n, self.t_panel, self.frames = PanelProc(), 0, 0.0, 0
        self.stat = dict(ticks=0)

    def on_world(self, w):
        import mujoco.viewer
        self.v = mujoco.viewer.launch_passive(w.sim.m, w.sim.d, key_callback=self.keys.append, show_left_ui=False, show_right_ui=False)
        set_cam(self.v.cam)
        self.t_start = self.wall0 = time.time()

    def lock(self):
        return self.v.lock()

    def after_step(self, w):
        v = self.v
        self.n += 1
        while self.keys:
            if self.keys.pop(0) == 54:
                self.paused = not self.paused
                self.wall0 = time.time() - w.sim.sim_time / self.speed
        if self.seconds and time.time() - self.t_start > self.seconds:
            raise Quit
        while True:
            if not v.is_running():
                raise Quit
            if self.n % 4 == 0 or self.paused:
                self.frame()
            if not self.paused:
                break
            time.sleep(0.03)
            self.wall0 = time.time() - w.sim.sim_time / self.speed
            while self.keys:
                if self.keys.pop(0) == 54:
                    self.paused = False
        ahead = w.sim.sim_time / self.speed - (time.time() - self.wall0)
        if ahead > 0:
            time.sleep(min(ahead, 0.05))

    def frame(self, label=""):
        import mujoco
        v = self.v
        vp = v.viewport
        if vp is not None and vp.width > 0:
            size = (min(int(vp.width * 0.5), int(vp.height * 0.9)) // 2 * 2, vp.height // 2 * 2)
            if size != self.size:
                self.size, self.img = size, None
                set_cam(v.cam, shift_px=size[0] / 2, vp_h=vp.height, fovy=45.0)
            img = self.pp.poll()
            if img is not None and img.shape[:2] == (size[1], size[0]):
                self.img = img
            if self.img is not None:
                v.set_texts([(mujoco.mjtFont.mjFONT_NORMAL, mujoco.mjtGridPos.mjGRID_TOPLEFT, " ", " ")])   # obejście z demo.py
                v.set_images([(mujoco.MjrRect(vp.width - size[0], 0, size[0], size[1]), self.img)])
            if time.time() - self.t_panel >= 1 / self.panel_fps and self.live.state:
                if self.pp.request(self.live.snapshot(), *size):
                    self.t_panel = time.time()
        v.sync()
        self.frames += 1

    def finish(self, result_line):
        """Po próbie okno zostaje (ostatni panel), do zamknięcia lub --seconds."""
        self.live.label += f"\nKONIEC PRÓBY: {result_line}"
        t0 = time.time()
        try:
            while self.v.is_running() and not (self.seconds and time.time() - self.t_start > self.seconds):
                self.frame()
                time.sleep(0.05)
                if time.time() - t0 > 3600:
                    break
        finally:
            self.close()

    def close(self):
        self.pp.close()
        try:
            self.v.close()
        except Exception:  # noqa: BLE001
            pass


class FileOut:
    """Nagranie bez okna: scena (mujoco.Renderer) + panel w tym samym procesie → MP4 25 kl./s + zrzuty."""

    def __init__(self, live, out_dir, W=1600, H=900):
        os.makedirs(out_dir)
        self.live, self.dir, self.W, self.H, self.pw = live, out_dir, W, H, int(H * 0.9) // 2 * 2
        self.vid = D.Video(os.path.join(out_dir, "demo_arm.mp4"), W, H)
        self.panel, self.n, self.shots, self.phase_t = None, 0, [], {}
        self.stat = {}

    def on_world(self, w):
        import mujoco
        m = w.sim.m
        m.vis.global_.offwidth, m.vis.global_.offheight = max(m.vis.global_.offwidth, self.W), max(m.vis.global_.offheight, self.H)
        self.r, self.cam = mujoco.Renderer(m, self.H, self.W - self.pw), mujoco.MjvCamera()
        set_cam(self.cam)

    def lock(self):
        return _nolock()

    def compose(self):
        live = self.live
        snap = live.snapshot()
        if self.panel is None:
            self.panel = Panel(self.pw, self.H, snap["static"])
        frame = np.zeros((self.H, self.W, 3), np.uint8)
        self.r.update_scene(self.w.sim.d, camera=self.cam)
        D.add_fill_light(self.r.scene)
        frame[:, :self.W - self.pw] = self.r.render()
        frame[:, self.W - self.pw:] = self.panel.render(snap)
        s = live.state
        D.overlay(frame, D.text_image(f"faza: {s['phase']}   t_sym {s['t']:.2f} s", 520, 40, size=13, weight="bold"), 0, 0, 0.8)
        return frame

    def after_step(self, w):
        self.w = w
        self.n += 1
        s = self.live.state
        if not s:
            return
        ph = s["phase"]
        self.phase_t.setdefault(ph, s["t"])
        if self.n % 4 == 0:
            fr = self.compose()
            self.vid.write(fr)
            for name, dt in (("grasp", 1.2), ("lift", 0.8), ("transport", 1.0), ("place", 0.6)):
                if ph == name and name not in self.stat and s["t"] - self.phase_t[ph] >= dt:
                    self.stat[name] = 1
                    self.save(fr, name)
            self.last = fr

    def save(self, fr, name):
        import matplotlib.image as mpimg
        p = os.path.join(self.dir, f"demo_arm_{len(self.shots) + 1:02d}_{name}.png")
        mpimg.imsave(p, fr)
        self.shots.append(p)

    def finish(self, result_line):
        if hasattr(self, "last"):
            self.save(self.last, "koniec")
        self.vid.close()
        if getattr(self, "r", None) is not None:
            if self.r._gl_context is not None:
                self.r._gl_context.make_current()
            self.r.close()


class BenchOut:
    """Pomiar: bez okna; panel=False → tylko przechwytywanie; panel=True → panel w osobnym procesie jak w oknie (20 kl./s)."""

    def __init__(self, live, panel, fps=20.0):
        self.live, self.fps, self.pp, self.n, self.t_panel, self.done = live, fps, PanelProc() if panel else None, 0, 0.0, 0
        self.stat = {}

    def on_world(self, w):
        pass

    def lock(self):
        return _nolock()

    def after_step(self, w):
        if self.pp is None or not self.live.state:
            return
        self.pp.poll() is not None and setattr(self, "done", self.done + 1)
        if time.time() - self.t_panel >= 1 / self.fps and self.pp.request(self.live.snapshot(), 720, 900):
            self.t_panel = time.time()

    def finish(self, result_line):
        self.pp and self.pp.close()


# ---------------------------------------------------------------- przebieg ------------------------------------------
def make_cfg(a):
    joints = tuple(int(x) for x in a.joints.split(",") if x)
    if not set(joints) <= {1, 2, 3} or not (joints or a.roll):
        sys.exit("--joints ⊂ {1,2,3} i/lub --roll")
    return JN.ArmCfg(version="demo_arm", joints=joints, roll=a.roll, inputs=tuple(a.inputs.split(",")), in_rule=a.in_rule)


def find_item(name):
    items = oh.SETS["base"]
    for i, it in enumerate(items):
        if "/".join(it) == name:
            return it, i
    sys.exit(f"nieznany przedmiot {name!r}; dostępne: {', '.join('/'.join(x) for x in items)}")


def run_demo(item, seed, glu, ac, out_factory=None, capture=True, keep=False):
    """Jedna próba przez ścieżkę pokazu. Zwraca (wynik run_trial, Live lub None, SHA trajektorii, out)."""
    fc, jaw, drv, bodies = make_nets(glu, ac, capture)
    live = Live(drv, jaw, ac, bodies, f"{'/'.join(item)}  ziarno {seed}  Glu {glu:+g}  stawy sieci {list(ac.joints)}"
                f"{'+4' if ac.roll else ''}  wejścia {','.join(ac.inputs)}  reguła IN {ac.in_rule}  \nALIF dt {ac.dt_ms:g} ms, {drv.nsteps} kroków / takt 10 ms",
                keep) if capture else None
    out = out_factory(live) if out_factory else None
    with patched(live, out) as hasher:
        try:
            r = JN.run_trial(item, seed, "N", jaw, drv, fc, ac)
        except Quit:
            if out:
                out.close()
            return None, live, hasher.hexdigest(), out
    if out:
        out.finish(f"{'sukces' if r['success'] else 'porażka'}; podniesienie {r['truth']['lift']}; {r['reasons'] or 'bez błędów'}")
    return r, live, hasher.hexdigest(), out


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--item", default="cube_S/hard_grip", help="kształt/materiał z object_handling.SETS['base']")
    ap.add_argument("--seed", type=int, required=True, help="jak joint_net --seed (ziarno próby = seed·1000 + indeks·10 + pose)")
    ap.add_argument("--pose", type=int, default=0)
    ap.add_argument("--glu", type=float, default=-1.0)
    ap.add_argument("--joints", default="1,2,3")
    ap.add_argument("--roll", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--inputs", default="padsT2,padsT1")
    ap.add_argument("--in-rule", default="fl", choices=("nerve", "fl"))
    ap.add_argument("--speed", type=float, default=1.0, help="okno: tempo względem czasu rzeczywistego")
    ap.add_argument("--seconds", type=float, default=0.0, help="okno: zamknij po tylu sekundach (0 = do zamknięcia)")
    ap.add_argument("--media", help="bez okna: MP4 + zrzuty do NOWEGO katalogu (odmowa, gdy istnieje)")
    ap.add_argument("--bench", action="store_true", help="bez okna: pomiar wydajności (bez / z panelem w osobnym procesie)")
    a = ap.parse_args()
    if a.seed in JN.TEST_SEEDS or a.seed == 20971:
        sys.exit("ziarna testowe zabronione")
    item, idx = find_item(a.item)
    seed, ac = a.seed * 1000 + idx * 10 + a.pose, make_cfg(a)
    if a.media:
        if not D._out_ok(a.media):
            sys.exit(f"{a.media}: zapis tylko w flymind/demo/, /tmp albo $TMPDIR")
        if os.path.exists(a.media):
            sys.exit(f"{a.media} istnieje — nie nadpisuję; podaj nowy katalog")
        t0 = time.time()
        r, live, sha, out = run_demo(item, seed, a.glu, ac, lambda lv: FileOut(lv, a.media))
        info = dict(item=a.item, trial_seed=seed, argv=sys.argv, neurons=dict(ArmNet=live.Na, LegJaw=live.Nj, total=live.N),
                    groups=[(g["label"], g["n"]) for g in live.groups], success=r["success"], truth=r["truth"], T_sim=r["T_sim"],
                    reasons=r["reasons"], lift_log=r["lift_log"], ticks=live.n_ticks, frames=out.vid.n, trajectory_sha256=sha,
                    shots=out.shots, wall_s=round(time.time() - t0, 1))
        with open(os.path.join(a.media, "info.json"), "x") as f:
            json.dump(info, f, indent=1, ensure_ascii=False, default=float)
        print(json.dumps(info, ensure_ascii=False, default=float))
    elif a.bench:
        rows = []
        for name, panel in (("bez panelu (przechwytywanie impulsów)", False), ("z panelem w osobnym procesie, 20 kl./s", True)):
            t0 = time.perf_counter()
            r, live, sha, out = run_demo(item, seed, a.glu, ac, lambda lv, p=panel: BenchOut(lv, p))
            wall = time.perf_counter() - t0 - 0.0
            rows.append(dict(wariant=name, ticks=live.n_ticks, T_sim=r["T_sim"], T_wall_trial=r["T_wall"], wall_total=round(wall, 2),
                             ticks_per_s=round(live.n_ticks / r["T_wall"], 1), rtf=round(r["T_sim"] / r["T_wall"], 2),
                             panels_done=getattr(out, "done", 0), sha=sha[:16]))
            print(json.dumps(rows[-1], ensure_ascii=False), flush=True)
    else:
        def mk(lv):
            return WindowOut(lv, a.speed, a.seconds)
        r, live, sha, out = run_demo(item, seed, a.glu, ac, mk)
        print(f"sieć: {live.Na} + {live.Nj} = {live.N} neuronów; koniec próby:", None if r is None else
              dict(success=r["success"], truth=r["truth"], T_sim=r["T_sim"], reasons=r["reasons"]), flush=True)


if __name__ == "__main__":
    main()
