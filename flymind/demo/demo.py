"""flymind/demo/demo.py — pokaz pętli FlyMind V5 w MuJoCo: okno interaktywne, prezentacja i nagrania. Tylko wizualizacja.

Takt sterowania (Demo.tick) jest przepisany 1:1 z loop.run_trial (warunki 'snn' i 'classical_p', bez opóźnienia, max_age
0,05 s) na TYCH SAMYCH obiektach: visual_path.network(J0 0,2), ALIF(loop.P), TargetEncoder(loop.ENC), SteerDecoder(loop.STEER,
slope z kalibracji V4 v2), SensoryGate, SafetyLayer, SO101Sim. test_demo.py sprawdza, że trajektoria jest identyczna
z loop.run_trial i że dodatki wizualne (oświetlenie widoku zewnętrznego, znaczniki, okno) nie zmieniają obrazu kamery robota.
Różnice wobec eksperymentu (jawnie): pętla trwa dłużej niż 3 s, a piłeczkę można przestawiać lub przesuwać.

Co jest czym:
  DATA         połączenia 424 neuronów (LC10a L/R → 147 pośrednich → DNa02 L/R), liczby synaps i przekaźniki z MaleCNS v1.0
  MODEL        dynamika ALIF (parametry ogólne, nie pomiar tych neuronów), J0 = 0,2 mV/synapsę, szum σ = 2 mV
  ENGINEERING  kamera MuJoCo, enkoder koloru (ten sam prąd dla wszystkich LC10a jednej strony), dekoder P na DNa02 L−R,
               warstwa bezpieczeństwa, serwo pozycyjne. Stawy 1–4 trzyma skrypt, chwytak nie jest sterowany.
  Tryb P       regulator P na wyjściu enkodera (gL − gR); SNN nie jest wtedy liczona.
To nie jest mózg muchy, tylko model wycinka połączeń w symulacji.

Uruchom (macOS wymaga mjpython):
  okno interaktywne   .venv/bin/mjpython flymind/demo/demo.py
  prezentacja         .venv/bin/mjpython flymind/demo/demo.py --present
  nagrania + zrzuty   .venv/bin/python -I -B flymind/demo/demo.py --media flymind/demo/media     (bez okna, osobny proces)
"""
import sys

sys.dont_write_bytecode = True          # nie twórz __pycache__ w flymind/ (moduły loop.py itd. tylko importowane)
import argparse  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
import subprocess  # noqa: E402
import time  # noqa: E402
from functools import lru_cache  # noqa: E402

import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FLY = os.path.dirname(HERE)
sys.path.insert(0, FLY)
import loop as L  # noqa: E402
from alif import ALIF  # noqa: E402
from decoder import SteerDecoder  # noqa: E402
from encoder import TargetEncoder  # noqa: E402
from safety import Command, Limits, SafetyLayer, ranges_from_mjcf  # noqa: E402
from sensory import SensoryGate  # noqa: E402
from so101 import UPSTREAM, SceneCfg, SO101Sim, integrate_pan  # noqa: E402
from visual_path import network  # noqa: E402

CALIB = os.path.join(FLY, "results", "v4", "v4_partB_v2_20261028T214641.json")   # ten sam plik co potwierdzenie V5
SEED0 = 9_900_001        # szum ALIF w pokazie; poza wszystkimi pulami z SEED_REGISTRY (pokaz nie jest eksperymentem)
SEED_CMP = 9_900_101     # szum ALIF prób porównawczych (pozycja i → SEED_CMP + i), ten sam w prezentacji i nagraniu
MAX_AGE = 0.05
HIST = 600               # takty historii na wykresach (6 s)
RASTER = 50              # takty w rastrze (500 ms × 1 ms)
AZ_BOX, RHO_BOX = (-30.0, 30.0), (0.16, 0.35)     # losowe położenia: pudełko V5 v2 (dalekie cele = strefa martwa)
V_TH = L.P.v_th - L.P.v_rest                        # 7 mV: stały prąd potrzebny do impulsu (bez szumu i synaps)


def load_calib():
    """Kalibracja jak loop.main: slope SNN z V4 v2 (te same warunki odmowy), slope P z calibrate_p."""
    v4 = json.load(open(CALIB))
    if v4.get("version") != 2 or v4["J0"] != L.J0 or v4["calib"]["offset"] != 0.0 or v4["calib"].get("refused") \
            or not v4["calib"]["slope_hz_per_rad"] > 0:
        sys.exit("kalibracja V4 v2 niezgodna z loop.main")
    return dict(slope_snn=v4["calib"]["slope_hz_per_rad"], slope_p=L.calibrate_p(SceneCfg().cam_shape))


class Demo:
    """Stan pętli. tick() = jeden takt loop.run_trial (10 ms); reszta to sterowanie pokazem."""

    def __init__(self, mode="snn", az_deg=20.0, rho=0.20, seed=SEED0, net=None, calib=None):
        self.spec, self.idx = net or network(L.J0)[:2]
        self.calib = calib or load_calib()
        self.sim = SO101Sim()
        self.cam_shape = self.sim.cfg.cam_shape
        self.seed, self.mode, self.n_reset = seed, mode, 0
        self.reset(az_deg, rho)

    def reset(self, az_deg=None, rho=None, mode=None, noise_seed=None):
        """Nowa próba jak w run_trial: Q_POSE, pan 0, świeża sieć/dekoder/bramka/bezpieczeństwo.
        noise_seed: ziarno ALIF (jak ziarno próby w run_trial); domyślnie nowa realizacja szumu po każdym resecie."""
        self.az, self.rho = az_deg if az_deg is not None else self.az, rho if rho is not None else self.rho
        self.mode = mode or self.mode
        s = self.sim
        s.reset(L.Q_POSE, ball_pos=L.place_ball(s, math.radians(self.az), self.rho))
        H, W = s.cfg.cam_shape
        self.gate = SensoryGate((H, W), period=L.DT, max_age=MAX_AGE, reset_after=max(0.1, MAX_AGE))
        self.enc = TargetEncoder((H, W), L.ENC)
        self.net = ALIF(self.spec, L.P, self.seed + self.n_reset if noise_seed is None else noise_seed)
        self.n_reset += 1
        self.dec = SteerDecoder({"DNa02_L": self.idx["DNa02_L"], "DNa02_R": self.idx["DNa02_R"]}, ("DNa02",), [0.0],
                                [self.calib["slope_snn"]], L.STEER)
        self.safety = SafetyLayer(Limits(ranges=ranges_from_mjcf(UPSTREAM), max_sensor_age=MAX_AGE))
        self.p_f, self.pan_t, self.k = 0.0, 0.0, 0
        self.src = "classical:P_encoder" if self.mode == "classical_p" else "snn:DNa02"
        self.hist = {k: [] for k in ("t", "lcL", "lcR", "mid", "dnL", "dnR", "diff", "omega", "pan", "e")}
        self.raster = np.zeros((RASTER * 10, len(self.spec.bodies)), bool)
        self.last = {}

    def move_ball(self, az_deg, rho):
        """Przestaw piłeczkę (namiar od osi kamery w Q_POSE, jak place_ball); sieć i ramię bez zmian."""
        s, self.az, self.rho = self.sim, az_deg, rho
        j = s.m.joint("ball")
        s.d.qpos[j.qposadr[0]:j.qposadr[0] + 7] = [*L.place_ball(s, math.radians(az_deg), rho), 1, 0, 0, 0]
        s.d.qvel[j.dofadr[0]:j.dofadr[0] + 6] = 0
        s.mj.mj_forward(s.m, s.d)

    def tick(self):
        """Jeden takt — ta sama kolejność i te same wywołania co loop.run_trial (delay_k = 0)."""
        s = self.sim
        e = L.bearing(s, s.d.qpos[s.qadr].copy())                    # prawda symulatora — tylko do oceny i wykresu
        obs = s.observe()
        f = obs.frame
        smp = self.gate.push(f, now=obs.t)
        age, img = smp.age, f.image if smp.usable else None
        g = self.enc.encode(img)["g"]
        spk, diff = None, np.nan
        if self.mode == "classical_p":
            a = math.exp(-L.DT / L.STEER.tau_s[0])
            self.p_f = a * self.p_f + (1 - a) * float(g @ [1, -1])
            omega = float(np.clip(L.STEER.gain * self.p_f / self.calib["slope_p"], -L.STEER.w_max, L.STEER.w_max))
        else:
            I = self.enc.currents(g, self.idx["in_L"], self.idx["in_R"], len(self.spec.bodies))
            spk = self.net.run(I, 10)
            out = self.dec.step(spk, 1.0)
            omega, diff = out["omega"], float(out["diff_hz"][0])
        self.pan_t = integrate_pan(self.pan_t, omega, L.DT)
        cmd = Command(obs.t, {0: self.pan_t, **{j: L.Q_POSE[j] for j in range(1, 5)}}, None,
                      {0: self.src, **{j: "script:hold_pose" for j in range(1, 5)}})
        qt, tau, fl, per = self.safety.step(cmd, obs.q, now=obs.t, sensor_age=age)
        self.pan_t = qt[0]
        s.act(qt, tau)
        s.step()
        self.k += 1
        self._record(obs, img, g, spk, diff, omega, e, fl, per)
        return e

    def _record(self, obs, img, g, spk, diff, omega, e, fl, per):
        h, ix = self.hist, self.idx
        rate = (lambda grp: float(spk[:, ix[grp]].mean() * 1000.0)) if spk is not None else (lambda grp: np.nan)
        if spk is not None:
            self.raster = np.roll(self.raster, -10, axis=0)
            self.raster[-10:] = spk
        dn = self.dec.r if spk is not None else (np.nan, np.nan)   # dec.used = [DNa02_L, DNa02_R] (indeksy rosnące)
        for k, v in (("t", obs.t), ("lcL", rate("in_L")), ("lcR", rate("in_R")), ("mid", rate("mid")),
                     ("dnL", dn[0]), ("dnR", dn[1]), ("diff", diff), ("omega", omega),
                     ("pan", math.degrees(obs.q[0])), ("e", math.degrees(e))):
            h[k].append(v)
            del h[k][:-HIST]
        self.last = dict(img=img if img is not None else obs.frame.image, g=g, omega=omega, e_deg=math.degrees(e),
                         pan_deg=math.degrees(obs.q[0]), safety=list(fl) + [y for v in per.values() for y in v])


# ---------------- rysowanie (matplotlib Agg → obraz RGB; to samo w oknie i w nagraniach) ----------------
def _fig(w, h):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    fig = Figure(figsize=(w / 100, h / 100), dpi=100, facecolor="#101418")
    return fig, FigureCanvasAgg(fig)


def _rgb(canvas, copy=True):
    """RGB z bufora Agg. copy=False: widok bufora — ważny tylko do następnego rysowania (okno i nagranie kopiują od razu)."""
    x = np.asarray(canvas.buffer_rgba())[..., :3]
    return x.copy() if copy else x


def _step(v, steps):
    """Najmniejsza granica osi ze `steps` mieszcząca dane (oś skacze rzadko, zamiast pływać co klatkę)."""
    v = np.asarray(v, float)
    m = float(np.nanmax(np.abs(v))) if np.isfinite(v).any() else 0.0
    return next((s for s in steps if s >= m), steps[-1])


def _ema(x, tau_ticks=5.0):
    """Wygładzenie tylko do wyświetlania (τ 50 ms jak odczyt dekodera); NaN (tryb P) zostaje NaN."""
    from scipy.signal import lfilter
    x = np.asarray(x, float)
    a = math.exp(-1.0 / tau_ticks)
    y = lfilter([1 - a], [1, -a], np.nan_to_num(x))
    y[~np.isfinite(x)] = np.nan
    return y


MODE_TXT = {"snn": ("SNN — komenda obrotu z impulsów DNa02", "#6cc4ff"),
            "classical_p": ("P — klasyczny regulator, SNN nie jest liczona", "#ffd166")}
C_L, C_R, C_MID, C_DN = "#4ea8ff", "#ff9f43", "#c8c8c8", "#ffe066"


class Panel:
    """Panel aktywności (prawa strona). Elementy zmienne rysowane blittingiem na zapamiętanym tle — szybko i stałe osie."""

    def __init__(self, demo, w, h):
        self.d, self.w, self.h = demo, w, h
        self.fig, self.canvas = _fig(w, h)
        u = h / 1080.0
        fs = lambda x: x * u * 1.0                                    # noqa: E731
        f = self.fig
        gs = f.add_gridspec(8, 2, height_ratios=[1.55, 1.75, 0.32, 1, 1, 1, 1, 0.05], hspace=0.62, wspace=0.28,
                            left=0.17, right=0.88, top=0.875, bottom=0.04)
        self.title = f.text(0.03, 0.985, "", fontsize=fs(15), weight="bold", va="top", animated=True)
        self.status = f.text(0.03, 0.950, "", fontsize=fs(11), va="top", family="monospace", color="#c9d1d9", animated=True)
        self.flag = f.text(0.03, 0.924, "", fontsize=fs(11), va="top", weight="bold", color="#ff5c5c", animated=True)
        f.text(0.03, 0.008, "DATA: połączenia MaleCNS v1.0   MODEL: dynamika ALIF   ENGINEERING: kamera, enkoder, "
               "dekoder, serwo", fontsize=fs(8.5), color="#8a96a3")

        def axis(spec, title, bg="#161b22"):
            ax = f.add_subplot(spec, facecolor=bg)
            ax.set_title(title, fontsize=fs(9.5), color="#e6edf3", loc="left", pad=3 * u)
            ax.tick_params(labelsize=fs(8), colors="#9aa7b4", length=2 * u)
            for sp in ax.spines.values():
                sp.set_color("#3a4450")
            return ax

        ax = axis(gs[0, 0], "kamera robota (96×128)", "#000")
        H, W = demo.cam_shape
        self.cam = ax.imshow(np.zeros((H, W, 3), np.uint8), animated=True)
        ax.set_xticks([])
        ax.set_yticks([])
        ax = self.ax_bar = axis(gs[0, 1], "")
        self.bars = ax.bar(["L", "R"], [0, 0], color=[C_L, C_R], width=0.6)
        for b in self.bars:
            b.set_animated(True)
        self.thr, self.fs_title = ax.axhline(V_TH, color="#ff5c5c", lw=1.2 * u, ls="--"), fs(9.5)
        ax.set_ylim(0, L.ENC.i_max)
        self.ax_ras = axis(gs[1, :], "impulsy — ostatnie 500 ms (każdy wiersz = neuron)", "#000")
        ix = demo.idx
        self.order = np.r_[ix["in_L"], ix["in_R"], ix["mid"]]
        self.colors = np.array([[80, 168, 255]] * len(ix["in_L"]) + [[255, 158, 66]] * len(ix["in_R"]) +
                               [[216, 216, 216]] * len(ix["mid"]), np.uint8)
        self.ras = self.ax_ras.imshow(np.zeros((len(self.order), RASTER * 10, 3), np.uint8), aspect="auto",
                                      interpolation="nearest", animated=True)
        b = np.cumsum([0, len(ix["in_L"]), len(ix["in_R"]), len(ix["mid"])])
        self.ax_ras.set_yticks((b[:-1] + b[1:]) / 2, [f"LC10a L ({b[1]})", f"LC10a R ({b[2] - b[1]})",
                                                       f"pośrednie ({b[3] - b[2]})"])
        for y in b[1:-1]:
            self.ax_ras.axhline(y - 0.5, color="#3a4450", lw=0.8 * u)
        self.ax_ras.set_xticks([0, RASTER * 10 - 1], ["−500 ms", "teraz"])
        self.off = self.ax_ras.text(0.5, 0.5, "", transform=self.ax_ras.transAxes, ha="center", va="center",
                                    fontsize=fs(11), color="#ffd166", animated=True)
        ax = axis(gs[2, :], "", "#000")
        self.dnras = ax.imshow(np.zeros((2, RASTER * 10, 3), np.uint8), aspect="auto", interpolation="nearest", animated=True)
        ax.set_yticks([0, 1], ["DNa02 L", "DNa02 R"])
        ax.set_xticks([])
        self.dn = np.r_[ix["DNa02_L"], ix["DNa02_R"]]
        x0 = -(HIST - 1) * L.DT
        self.ax_r = axis(gs[3, :], "częstość populacji [Hz] (wygładzona τ 50 ms)")
        self.ax_dn = axis(gs[4, :], "DNa02 [Hz] — dokładnie to, co czyta dekoder (τ 50 ms)")
        self.ax_d = axis(gs[5, :], "DNa02 L−R [Hz]  →  komenda ω [rad/s] (dekoder P = ENGINEERING)")
        self.ax_p = axis(gs[6, :], "kąt bazy i błąd do celu [°] (błąd = prawda symulatora, sterownik go nie widzi)")
        self.ax_o = self.ax_d.twinx()
        self.ax_o.tick_params(labelsize=fs(8), colors="#ffd166", length=2 * u)
        self.ax_o.set_ylim(-1.15, 1.15)
        for y in (-L.STEER.w_max, L.STEER.w_max):
            self.ax_o.axhline(y, color="#ffd166", lw=0.6 * u, ls=":")
        self.ax_p.axhspan(-5, 5, color="#2ea043", alpha=0.18)
        for ax in (self.ax_r, self.ax_dn, self.ax_d, self.ax_p, self.ax_o):
            ax.set_xlim(x0, 0)
        self.ax_p.set_xlabel("czas [s] względem teraz", fontsize=fs(8), color="#9aa7b4", labelpad=1)
        for ax in (self.ax_r, self.ax_dn, self.ax_d):
            ax.set_xticklabels([])
        lw = 1.4 * u
        mk = lambda ax, c, lab, **kw: ax.plot([], [], color=c, label=lab, lw=lw, animated=True, **kw)[0]   # noqa: E731
        self.l = dict(lcL=mk(self.ax_r, C_L, "LC10a L"), lcR=mk(self.ax_r, C_R, "LC10a R"), mid=mk(self.ax_r, C_MID, "pośrednie"),
                      dnL=mk(self.ax_dn, C_L, "DNa02 L"), dnR=mk(self.ax_dn, C_R, "DNa02 R"),
                      diff=mk(self.ax_d, "#c77dff", "L−R [Hz]"), omega=mk(self.ax_o, "#ffd166", "ω [rad/s]"),
                      pan=mk(self.ax_p, "#7ee787", "baza [°]"), e=mk(self.ax_p, "#ff6b6b", "błąd [°]"))
        leg = dict(loc="upper left", fontsize=fs(7.5), ncol=3, framealpha=0.35, facecolor="#0d1117", edgecolor="#3a4450",
                   labelcolor="#e6edf3", handlelength=1.2, borderpad=0.25)
        self.ax_r.legend(**leg)
        self.ax_dn.legend(**leg)
        self.ax_p.legend(**leg)
        self.ax_d.legend(handles=[self.l["diff"], self.l["omega"]], **leg)
        f.text(0.03, 0.026, f"* prąd stały potrzebny do impulsu pojedynczego neuronu bez szumu i wejść synaptycznych "
               f"(V_th − V_rest = {V_TH:.0f} mV)", fontsize=fs(7), color="#6e7b88")
        self.dyn = [self.title, self.status, self.flag, self.cam, *self.bars, self.ras, self.off, self.dnras,
                    *self.l.values()]
        self.bg, self.lim = None, None

    def render(self, status="", flag=""):
        d, h = self.d, self.d.hist
        snn = d.mode != "classical_p"
        txt, col = MODE_TXT[d.mode]
        self.title.set_text("TRYB " + txt)
        self.title.set_color(col)
        self.status.set_text(status)
        self.flag.set_text(flag)
        if d.last.get("img") is not None:
            self.cam.set_data(d.last["img"])
        for b, v in zip(self.bars, d.last.get("g", (0, 0))):
            b.set_height(L.ENC.i_max * v)
        n = len(self.order)
        self.ras.set_data(d.raster[:, self.order].T[..., None] * self.colors[:, None, :] if snn else
                          np.zeros((n, RASTER * 10, 3), np.uint8))
        self.dnras.set_data(d.raster[:, self.dn].T[..., None] * np.array([255, 224, 102], np.uint8) if snn else
                            np.zeros((2, RASTER * 10, 3), np.uint8))
        self.off.set_text("" if snn else "SNN nie jest liczona w trybie P")
        x = (np.arange(len(h["t"])) - len(h["t"]) + 1) * L.DT
        for k, ln in self.l.items():
            ln.set_data(x, _ema(h[k]) if k in ("lcL", "lcR", "mid") else h[k])
        lim = (d.mode, _step(np.r_[_ema(h["lcL"]), _ema(h["lcR"]), _ema(h["mid"])], (25, 50, 100, 250)),
               _step(np.r_[h["dnL"], h["dnR"]], (50, 100, 250)), _step(h["diff"], (50, 100, 250)),
               _step(np.r_[h["pan"], h["e"]], (40, 80, 120)))
        if lim != self.lim or self.bg is None:                       # osie zmieniły zakres → pełne odrysowanie tła
            self.lim = lim
            self.ax_bar.set_title("prąd → LC10a [mV]  (- - próg*)" if snn else "enkoder ×12 mV → regulator P",
                                  fontsize=self.fs_title, color="#e6edf3", loc="left")
            self.thr.set_visible(snn)
            self.ax_r.set_ylim(0, lim[1])
            self.ax_dn.set_ylim(0, lim[2])
            self.ax_d.set_ylim(-lim[3], lim[3])
            self.ax_p.set_ylim(-lim[4], lim[4])
            self.canvas.draw()
            self.bg = self.canvas.copy_from_bbox(self.fig.bbox)
        else:
            self.canvas.restore_region(self.bg)
        r = self.canvas.get_renderer()
        for a in self.dyn:
            a.draw(r)
        return _rgb(self.canvas, copy=False)


class Snap:
    """Kopia stanu potrzebnego panelowi (dla procesu rysującego): te same pola co Demo, bez symulatora."""

    def __init__(self, d):
        self.mode, self.idx, self.cam_shape = d.mode, d.idx, d.cam_shape
        self.hist = {k: list(v) for k, v in d.hist.items()}
        self.raster = d.raster.copy()
        self.last = {k: d.last[k] for k in ("img", "g") if k in d.last}


def panel_worker(conn, shm_name):
    """Osobny proces: Snap → Panel.render → obraz do pamięci współdzielonej. Symulacja w oknie nie czeka na rysowanie."""
    from multiprocessing import shared_memory
    shm, panels = shared_memory.SharedMemory(name=shm_name), {}
    try:
        while True:
            msg = conn.recv()
            if msg is None:
                break
            snap, w, h, status, flag = msg
            p = panels.get((w, h)) or panels.setdefault((w, h), Panel(snap, w, h))
            p.d = snap
            img = p.render(status, flag)
            np.ndarray(img.shape, np.uint8, buffer=shm.buf)[:] = img
            conn.send(img.shape)
    finally:
        shm.close()


class PanelProc:
    """Klient procesu panelu. request() wysyła stan (gdy proces wolny), poll() zwraca gotowy obraz albo None."""

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

    def request(self, d, w, h, status, flag):
        if self.busy or w * h * 3 > self.shm.size:
            return False
        self.conn.send((Snap(d), w, h, status, flag))
        self.busy = True
        return True

    def poll(self):
        if not (self.busy and self.conn.poll()):
            return None
        self.busy = False
        shape = self.conn.recv()
        return np.ndarray(shape, np.uint8, buffer=self.shm.buf)     # ważny do następnego request()

    def close(self):
        try:
            self.conn.send(None)
            self.p.join(3)
        finally:
            if self.p.is_alive():
                self.p.terminate()
            self.shm.close()
            self.shm.unlink()


@lru_cache(maxsize=64)
def text_image(text, w, h, size=20, fg="#e6edf3", bg="#0d1117", weight="normal", align="left", family="sans-serif"):
    """Pasek tekstu (polskie znaki) jako obraz RGB — podpisy, plakietka trybu, pomoc klawiszy."""
    fig, canvas = _fig(w, h)
    fig.set_facecolor(bg)
    fig.text(0.015 if align == "left" else 0.5, 0.5, text, fontsize=size,
             color=fg, va="center", ha="left" if align == "left" else "center", weight=weight, linespacing=1.35,
             wrap=family != "monospace", family=family)
    canvas.draw()
    return _rgb(canvas)


def status_line(d, tempo=None):
    x = d.last
    if not x:
        return "", ""
    s = f"t {d.k * L.DT:5.2f} s   ω {x['omega']:+.2f} rad/s   baza {x['pan_deg']:+5.1f}°   błąd {x['e_deg']:+5.1f}°"
    if tempo is not None:
        s += f"   tempo {tempo:.2f}×"
    flag = "BRAK RUCHU (|błąd| > 5°, ω ≈ 0)" if abs(x["e_deg"]) > 5 and abs(x["omega"]) < 0.02 else ""
    return s, flag


def random_ball(rng):
    return float(rng.uniform(*AZ_BOX)), float(rng.uniform(*RHO_BOX))


# ---------------- kamera widoku zewnętrznego i znaczniki (tylko rysunek; robot ich nie widzi) ----------------
SHOTS = dict(  # lookat, distance, azimuth, elevation
    wide=((0.27, 0.02, 0.10), 1.05, -35.0, -28.0),     # całe ramię z boku + strefa celu
    behind=((0.33, 0.01, 0.05), 1.0, 0.0, -50.0),      # zza robota: oś kamery i namiar celu
    side=((0.32, 0.03, 0.08), 0.92, 60.0, -32.0),      # z drugiej strony
)


def apply_cam(cam, shot, eye_id, aspect=None, shift_px=0.0, vp_h=None, fovy=45.0):
    """Ujęcia kadrowane dla proporcji ~16:10. aspect < 1,15 → kamera odsuwa się. shift_px: okno rysuje scenę na całą
    szerokość, a panel zasłania prawą część — punkt patrzenia przesuwany w prawo, by obiekt był w środku widocznej części."""
    import mujoco
    if shot == "eye":
        cam.type, cam.fixedcamid = mujoco.mjtCamera.mjCAMERA_FIXED, eye_id
        return
    la, dist, az, el = shot
    dist *= max(1.0, 1.15 / aspect) if aspect else 1.0
    la = np.asarray(la, float)
    if shift_px and vp_h:
        a = math.radians(az)
        la = la + np.array([math.sin(a), -math.cos(a), 0.0]) * shift_px * dist * math.tan(math.radians(fovy) / 2) / (vp_h / 2)
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.lookat[:] = la
    cam.distance, cam.azimuth, cam.elevation = dist, az, el


def _blend(a, b, w):
    w = w * w * (3 - 2 * w)                                           # łagodny start i koniec ruchu kamery
    return (tuple(np.add(np.multiply(a[0], 1 - w), np.multiply(b[0], w))), a[1] + (b[1] - a[1]) * w,
            a[2] + (b[2] - a[2]) * w, a[3] + (b[3] - a[3]) * w)


def add_markers(scn, d):
    """Czerwona linia = oś kamery robota „eye” do stołu; zielona obwódka pod piłeczką dla widoczności. Tylko w scenie
    widoku zewnętrznego / okna (user_scn) — renderer kamery robota ma własną scenę i tych geometrii nie dostaje."""
    import mujoco
    k = d.sim.fk(d.sim.d.qpos[d.sim.qadr].copy())
    p0, f = k["eye"], k["eye_forward"]
    p1 = p0 + f * (p0[2] - d.sim.cfg.ball_r) / max(-f[2], 1e-6)
    b = d.sim.d.qpos[d.sim.m.joint("ball").qposadr[0]:][:3]
    for typ, size, rgba, conn in ((mujoco.mjtGeom.mjGEOM_LINE, None, (1, .2, .2, 1), (p0, p1)),
                                  (mujoco.mjtGeom.mjGEOM_CYLINDER, (0.045, 0.0008, 0), (.2, 1, .35, .35), None)):
        if scn.ngeom >= scn.maxgeom:
            return
        g = scn.geoms[scn.ngeom]
        mujoco.mjv_initGeom(g, typ, np.array(size or (0, 0, 0), float), np.array([b[0], b[1], 0.001]),
                            np.eye(3).ravel(), np.array(rgba, np.float32))
        if conn:
            mujoco.mjv_connector(g, typ, 3, *conn)
        scn.ngeom += 1


def add_fill_light(scn):
    """Dodatkowe miękkie światło w scenie WIDOKU ZEWNĘTRZNEGO (nagrania). Model i kamera robota bez zmian."""
    import mujoco
    if scn.nlight >= len(scn.lights):
        return
    li = scn.lights[scn.nlight]
    li.type, li.headlight, li.castshadow = mujoco.mjtLightType.mjLIGHT_DIRECTIONAL, 0, 0
    li.dir[:] = np.array([-0.5, 0.6, -0.62]) / np.linalg.norm([-0.5, 0.6, -0.62])
    li.pos[:] = (0.6, -0.6, 1.0)
    li.diffuse[:], li.ambient[:], li.specular[:] = (0.32, 0.32, 0.34), (0.10, 0.10, 0.11), (0.05, 0.05, 0.05)
    scn.nlight += 1


# ---------------- prezentacja: scenariusz sterowany TAKTAMI symulacji (okno = nagranie) ----------------
# Położenia ustalone z góry, przed uruchomieniem (nie dobierane pod wynik): blisko z lewej / prawej, mały kąt, daleko.
# Każdy akt z resetem ma stałe ziarno szumu ALIF → prezentacja powtarzalna niezależnie od wcześniejszych resetów.
CMP = ((20.0, 0.20), (-12.0, 0.24), (25.0, 0.30), (-28.0, 0.18))
ACTS = (
    dict(name="intro", s=6, mode="snn", reset=(20.0, 0.20), seed=SEED0 + 10, shots=((0, "wide"),), orbit=3.0,
         cap="FlyMind w MuJoCo: 424 neurony połączone jak w connectomie MaleCNS v1.0 (LC10a → 147 pośrednich → DNa02) "
             "sterują obrotem bazy SO-101.  To model w symulacji, nie mózg muchy."),
    dict(name="jumps", s=12, mode="snn", reset=(15.0, 0.20), seed=SEED0 + 20, jumps=((4, -25.0, 0.18), (8, 5.0, 0.22)),
         shots=((0, "eye"), (4, "behind")),
         cap="Cel przeskakuje w ustalone z góry miejsca (+15°, −25°, +5°). Sieć dostaje wyłącznie obraz z kamery robota "
             "(pierwsze 4 s: widok tej kamery)."),
    dict(name="far", s=6, mode="snn", reset=(22.0, 0.32), seed=SEED0 + 30, shots=((0, "side"),),
         cap="Cel dalej (ρ 0,32 m): mniejszy obraz celu = słabszy prąd do LC10a. Czerwona linia na wykresie prądu = próg impulsu."),
    dict(name="track", s=8, mode="snn", reset=(25.0, 0.20), seed=SEED0 + 40, slide=(25.0, -25.0, 0.20, 0.5, 7.5), shots=((0, "behind"),),
         cap="Cel jedzie ze stałą prędkością z +25° do −25° (zadanie spoza protokołu V5: śledzenie ruchomego celu)."),
    *(dict(name=f"cmp{i}_{m}", s=3, mode=m, reset=(az, rho), seed=SEED_CMP + i, compare=i, shots=((0, "behind"),),
           cap=f"Porównanie {i + 1}/{len(CMP)} — {'SNN' if m == 'snn' else 'P'}: ten sam start (baza 0°), cel {az:+.0f}°, "
               f"ρ {rho:.2f} m, te same ograniczenia; próba 3 s jak w protokole V5.")
      for i, (az, rho) in enumerate(CMP) for m in ("snn", "classical_p")),
    dict(name="summary", s=5, mode=None, hold=True, shots=((0, "wide"),), cap=None),
)


class Show:
    """Scenariusz prezentacji. step(d) wykonuje JEDEN krok zegara pokazu (takt 10 ms): ustawienia aktu, potem d.tick()
    (poza aktem 'summary', gdzie symulacja stoi). Wyniki porównania liczone loop.metrics (ten sam miernik co V5)."""

    def __init__(self, acts=ACTS):
        self.acts, self.start, t = acts, [], 0
        for a in acts:
            self.start.append(t)
            t += int(round(a["s"] * 100))
        self.total, self.k, self.results, self.e_log, self._e = t, 0, [], [], []
        self.i = -1
        self.keys = [(self.start[i] + int(round(ts * 100)), name, a.get("orbit", 0.0), self.start[i])
                     for i, a in enumerate(acts) for ts, name in a["shots"]]          # (takt, ujęcie, orbita °/s, start aktu)

    def act_at(self, k):
        return max(j for j, s in enumerate(self.start) if s <= k)

    @property
    def done(self):
        return self.k >= self.total

    def step(self, d):
        if self.done:
            return None
        i = self.act_at(self.k)
        a, t = self.acts[i], (self.k - self.start[i]) * L.DT
        if i != self.i:
            self._close_act(d)
            self.i, self._e = i, []
            if "reset" in a:
                d.reset(*a["reset"], mode=a["mode"], noise_seed=a.get("seed"))
        for tj, az, rho in a.get("jumps", ()):
            if abs(t - tj) < L.DT / 2:
                d.move_ball(az, rho)
        if "slide" in a:
            a0, a1, rho, t0, t1 = a["slide"]
            if t0 <= t <= t1:
                d.move_ball(a0 + (a1 - a0) * (t - t0) / (t1 - t0), rho)
        self.k += 1
        if a.get("hold"):
            return None
        e = d.tick()
        self._e.append(math.degrees(e))
        self.e_log.append(round(math.degrees(e), 6))
        if self.k == self.total:
            self._close_act(d)
        return e

    def _close_act(self, d):
        if self.i < 0 or "compare" not in self.acts[self.i]:
            return
        a = self.acts[self.i]
        r = L.metrics(dict(e_deg=self._e, az0_deg=a["reset"][0], safety_flags={}))
        self.results.append(dict(pos=a["compare"], mode=a["mode"], az=a["reset"][0], rho=a["reset"][1], seed=a.get("seed"),
                                 final_abs_err=round(r["final_abs_err"], 2), success=r["success"],
                                 overshoot_deg=round(r["overshoot_deg"], 2), t_first_within=r["t_first_within"]))

    def _cam(self, j, k):
        _, name, orbit, a0 = self.keys[j]
        if name == "eye":
            return "eye"
        la, dist, az, el = SHOTS[name]
        return la, dist, az + orbit * (k - a0) * L.DT, el

    def shot(self):
        """Ujęcie dla bieżącego taktu: 'eye' (cięcie) albo kamera swobodna z płynnym przejściem 1 s od poprzedniego ujęcia."""
        k = min(self.k, self.total - 1)
        j = max(i for i, key in enumerate(self.keys) if key[0] <= k)
        cur = self._cam(j, k)
        if j == 0 or cur == "eye":
            return cur
        prev, w = self._cam(j - 1, self.keys[j][0]), (k - self.keys[j][0]) / 100
        return cur if prev == "eye" or w >= 1 else _blend(prev, cur, w)

    def caption(self):
        a = self.acts[self.act_at(min(self.k, self.total - 1))]
        if a["cap"]:
            return a["cap"]
        return "\n".join(["Wyniki tej prezentacji — średni |błąd| w ostatnich 0,5 s próby, ✓ = cały czas < 5° (loop.metrics)", ""]
                         + [f"cel {az:+3.0f}°  ρ {rho:.2f} m      SNN {self._res(i, 'snn'):>8s}      P {self._res(i, 'classical_p'):>8s}"
                            for i, (az, rho) in enumerate(CMP)])

    def cap_height(self):
        """Wysokość paska podpisu w pikselach przy 1080 wierszach: plansza wyników jest wyższa."""
        return 300 if self.acts[self.act_at(min(self.k, self.total - 1))]["cap"] is None else 112

    def _res(self, i, mode):
        r = [x for x in self.results if x["pos"] == i and x["mode"] == mode]
        return f"{r[0]['final_abs_err']:.1f}° {'✓' if r[0]['success'] else '✗'}" if r else "—"


# ---------------- okno MuJoCo ----------------
KEYS = {54: "pause", 55: "reset", 56: "mode", 57: "random", 45: "left", 61: "right"}   # 6 7 8 9 - =
PANEL_LEVELS = ((1, 1.0), (1, 0.6), (2, 1.0), (2, 0.5))      # (podział rozdzielczości panelu, ułamek --panel-fps)
HELP = "6 pauza · 7 reset · 8 SNN ↔ P (restart tej samej sceny) · 9 losowy cel · − / = cel 10° w lewo / prawo · " \
       "[ ] kamera robota · Esc widok swobodny"
HELP_PRESENT = "prezentacja · 6 pauza · 7 od początku · 9 kamera automatyczna wł./wył. (wył. = mysz) · " \
               "[ ] kamera robota"


def handle(action, d, state, rng):
    """Akcja klawisza (tryb interaktywny) → zmiana pokazu. state: dict(paused=bool)."""
    if action == "pause":
        state["paused"] = not state["paused"]
    elif action == "reset":
        d.reset()
    elif action == "mode":
        d.reset(mode="classical_p" if d.mode == "snn" else "snn")
    elif action == "random":
        d.move_ball(*random_ball(rng))
    elif action in ("left", "right"):
        d.move_ball(float(np.clip(d.az + (10 if action == "left" else -10), *AZ_BOX)), d.rho)


def run_viewer(d, a):
    """Okno: symulacja w czasie rzeczywistym (takty doganiają zegar, maks. 6 na klatkę), panel i podpisy jako obrazy."""
    import mujoco
    import mujoco.viewer
    keys, state, rng = [], dict(paused=False, auto=True), np.random.default_rng(a.seed)
    show = Show() if a.present else None
    if show:
        d.reset(*ACTS[0]["reset"], mode="snn")
    v = mujoco.viewer.launch_passive(d.sim.m, d.sim.d, key_callback=keys.append, show_left_ui=False, show_right_ui=False)
    eye = d.sim.m.camera("eye").id
    apply_cam(v.cam, SHOTS["behind"], eye)
    panel = size = None
    wall0, done0, n_tick, t_jump = time.time(), 0, 0, time.time()
    t_start = time.time()
    t_end = t_start + a.seconds if a.seconds else None
    rate_win, frames, t_render, t_panel, lvl, slow_t, panel_sc, sc = [], 0, [], 0.0, 0, None, 0, 1
    tempos, T = [], dict(lock_wait=0.0, sim=0.0, panel=0.0, overlay=0.0, sync=0.0)
    try:
        pp = None if a.panel_inproc else PanelProc()
    except Exception as err:                              # noqa: BLE001 — bez procesu panel rysowany w oknie (wolniej)
        print("proces panelu niedostępny, rysuję w oknie:", err, flush=True)
        pp = None
    t_req = time.time()
    try:
        while v.is_running() and (t_end is None or time.time() < t_end):
            while keys:
                act = KEYS.get(keys.pop(0))
                with v.lock():
                    if show and act == "reset":
                        show = Show()
                    elif show and act == "random":
                        state["auto"] = not state["auto"]
                    elif act and (act == "pause" or not show):
                        handle(act, d, state, rng)
                wall0, done0 = time.time(), n_tick
            if a.jump and not show and not state["paused"] and time.time() - t_jump > a.jump:
                with v.lock():
                    d.move_ball(*random_ball(rng))
                t_jump = time.time()
            tq = time.perf_counter()
            with v.lock():
                tl = time.perf_counter()
                T["lock_wait"] += tl - tq
                n = 0
                while not state["paused"] and n_tick - done0 < (time.time() - wall0) * a.speed * 100 and n < 6:
                    if show:
                        show.step(d)
                        if show.done:
                            if a.once:
                                break
                            show = Show()
                    else:
                        d.tick()
                    n += 1
                    n_tick += 1
                if n_tick - done0 < (time.time() - wall0) * a.speed * 100 - 25:     # > 0,25 s za zegarem: nie doganiaj w nieskończoność
                    wall0, done0 = time.time(), n_tick
                sh = show.shot() if show and state["auto"] else None
                vp0 = v.viewport
                if sh is not None and vp0 is not None and vp0.width > 0 and size:
                    apply_cam(v.cam, sh, eye, aspect=(vp0.width - size[0]) / vp0.height, shift_px=size[0] / 2, vp_h=vp0.height,
                              fovy=d.sim.m.vis.global_.fovy)
                v.user_scn.ngeom = 0
                if sh != "eye":
                    add_markers(v.user_scn, d)
                T["sim"] += time.perf_counter() - tl
            now = time.time()
            rate_win = [x for x in rate_win if now - x[0] < 2.0] + [(now, n_tick)]
            tempo = (rate_win[-1][1] - rate_win[0][1]) / 100 / max(now - rate_win[0][0], 1e-3) if len(rate_win) > 5 else None
            if tempo is not None and not state["paused"] and now - t_start > 5:
                tempos.append(tempo)
            # Symulacja ma pierwszeństwo: gdy przez 3 s idzie wolniej niż zegar, panel tanieje o jeden stopień
            # (pełna rozdzielczość 20 → 12 kl./s, potem połowa pikseli ×2). Sterowanie i tak liczone jest w czasie symulacji.
            if tempo is not None and not state["paused"] and tempo < 0.97 * a.speed and lvl < len(PANEL_LEVELS) - 1:
                slow_t = slow_t or now
                if now - slow_t > 3.0:
                    lvl, slow_t, rate_win = lvl + 1, None, []
            else:
                slow_t = None
            sc, pfps = PANEL_LEVELS[lvl][0], a.panel_fps * PANEL_LEVELS[lvl][1]
            vp = v.viewport
            if vp is not None and vp.width > 0:
                pw = min(int(vp.width * 0.40), int(vp.height * 0.72)) // 2 * 2
                if (pw, vp.height // 2 * 2) != size:
                    size, panel = (pw, vp.height // 2 * 2), None
                s, flag = status_line(d, tempo if not state["paused"] else None)
                if state["paused"]:
                    flag = "PAUZA   " + flag
                due = time.time() - t_panel >= 1 / pfps or state["paused"]
                t0, img = time.perf_counter(), None
                if pp:                                        # panel w osobnym procesie: odbierz gotowy obraz, potem zamów nowy
                    img = pp.poll()
                    if img is not None:
                        t_render = t_render[-999:] + [time.time() - t_req]
                elif due:
                    if panel is None or panel_sc != sc:
                        panel, panel_sc = Panel(d, size[0] // sc, size[1] // sc), sc
                    img, t_panel = panel.render(s, flag), time.time()
                    t_render = t_render[-999:] + [time.perf_counter() - t0]
                if img is not None and img.shape[0] * (size[1] // img.shape[0]) == size[1] and img.shape[0] != size[1]:
                    img = img.repeat(2, 0).repeat(2, 1)
                T["panel"] += time.perf_counter() - t0
                if img is not None and img.shape[:2] == (size[1], size[0]):
                    t1 = time.perf_counter()
                    aw, u = vp.width - size[0], vp.height / 1080
                    ch = int((show.cap_height() if show else 105) * u) // 2 * 2
                    cap = show.caption() if show else HELP
                    bw, bh = int(min(aw, 760 * u)), int(56 * u)
                    imgs = [(mujoco.MjrRect(vp.width - size[0], 0, size[0], size[1]), img),
                            (mujoco.MjrRect(0, 0, aw, ch), text_image(cap, aw, ch, size=13 * u if show else 11 * u,
                                                                     family="monospace" if ch > 200 * u else "sans-serif")),
                            (mujoco.MjrRect(0, vp.height - bh, bw, bh),
                             text_image("TRYB " + MODE_TXT[d.mode][0], bw, bh, size=15 * u, fg=MODE_TXT[d.mode][1], weight="bold"))]
                    if show:
                        hw, hp = int(min(aw, 900 * u)), int(30 * u)
                        imgs.append((mujoco.MjrRect(0, ch, hw, hp),
                                     text_image(HELP_PRESENT + ("" if state["auto"] else "   [kamera ręczna]"), hw, hp, size=9 * u,
                                                fg="#9aa7b4")))
                    # mujoco 3.17 (zmierzone): bez nakładki tekstowej viewer rysuje obrazy tylko w górnym pasie okna (obszar
                    # przycinania zostaje z poprzedniego elementu UI). Pusty tekst pod plakietką trybu resetuje ten obszar.
                    v.set_texts([(mujoco.mjtFont.mjFONT_NORMAL, mujoco.mjtGridPos.mjGRID_TOPLEFT, " ", " ")])
                    v.set_images(imgs)                        # kopiuje obrazy — bufor procesu panelu można nadpisać
                    T["overlay"] += time.perf_counter() - t1
                if pp and due and pp.request(d, size[0] // sc, size[1] // sc, s, flag):
                    t_panel = t_req = time.time()
            t2 = time.perf_counter()
            v.sync()
            T["sync"] += time.perf_counter() - t2
            frames += 1
            if state["paused"]:
                time.sleep(0.03)
            else:
                ahead = (n_tick - done0) / (a.speed * 100) - (time.time() - wall0)
                if ahead > 0:
                    time.sleep(min(ahead, 0.02))
    finally:
        if pp:
            pp.close()
    wall = time.time() - t_start
    info = dict(ticks=n_tick, frames=frames, panel_ms_p50=round(1000 * float(np.median(t_render)), 1) if t_render else None,
                fps=round(frames / wall, 1), sim_s=round(n_tick * L.DT, 2), wall_s=round(wall, 2),
                panel_px=list(size) if size else None, panel_scale=sc, panel_fps=round(pfps, 1), panel_level=lvl,
                tempo_p10_p50=[round(float(np.percentile(tempos, q)), 3) for q in (10, 50)] if tempos else None,
                ms_per_s={k: round(1000 * x / wall, 1) for k, x in T.items()}, panel_process=bool(pp))
    print("koniec:", json.dumps(info), flush=True)
    if a.log:
        with open(a.log, "x") as fh:
            json.dump(dict(info, present=bool(a.present), e_log=show.e_log if show else None), fh)
    v.close()


# ---------------- nagrania i zrzuty (bez okna; osobny proces, nie blokuje okna) ----------------
class Ext:
    """Renderer widoku zewnętrznego (własna scena: światło wypełniające + znaczniki); kamera robota nietknięta."""

    def __init__(self, d, w, h):
        import mujoco
        m = d.sim.m
        m.vis.global_.offwidth = max(m.vis.global_.offwidth, w)
        m.vis.global_.offheight = max(m.vis.global_.offheight, h)
        self.d, self.r, self.cam, self.aspect = d, mujoco.Renderer(m, h, w), mujoco.MjvCamera(), w / h
        self.eye = m.camera("eye").id

    def render(self, shot):
        """Ujęcie 'eye' bez dodatków (bez światła wypełniającego i znaczników) — tak blisko obrazu robota, jak się da;
        robot ma jeszcze wyłączone cienie/odbicia i rozdzielczość 96×128."""
        apply_cam(self.cam, shot, self.eye, aspect=self.aspect)
        self.r.update_scene(self.d.sim.d, camera=self.cam)
        if shot != "eye":
            add_fill_light(self.r.scene)
            add_markers(self.r.scene, self.d)
        return self.r.render()

    def close(self):
        if self.r._gl_context is not None:
            self.r._gl_context.make_current()                       # jak SO101Sim.close (błąd mujoco 3.17 przy zamykaniu)
        self.r.close()


def overlay(frame, img, x, y, alpha=0.86):
    h, w = img.shape[:2]
    roi = frame[y:y + h, x:x + w]
    roi[:] = (alpha * img + (1 - alpha) * roi).astype(np.uint8)


class Video:
    def __init__(self, path, w, h, fps=25):
        self.p = subprocess.Popen(["ffmpeg", "-n", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                                   "-r", str(fps), "-i", "-", "-pix_fmt", "yuv420p", "-vcodec", "libx264", "-crf", "18",
                                   "-preset", "medium", "-movflags", "+faststart", path], stdin=subprocess.PIPE)
        self.path, self.n = path, 0

    def write(self, frame):
        self.p.stdin.write(np.ascontiguousarray(frame).tobytes())
        self.n += 1

    def close(self):
        self.p.stdin.close()
        if self.p.wait():
            raise RuntimeError(f"ffmpeg: błąd zapisu {self.path}")


def compose_main(d, show, ext, panel, W, H):
    """Klatka prezentacji: widok 3D (lewo) z plakietką trybu i podpisem + panel aktywności (prawo)."""
    pw = panel.w
    frame = np.zeros((H, W, 3), np.uint8)
    frame[:, :W - pw] = ext.render(show.shot())
    s, flag = status_line(d)
    frame[:, W - pw:] = panel.render(s, flag)
    u, aw = H / 1080, W - pw
    ch = int(show.cap_height() * u)
    overlay(frame, text_image(show.caption(), aw, ch, size=13.5 * u, family="monospace" if ch > 200 * u else "sans-serif"),
            0, H - ch, 0.92)
    bw, bh = int(min(aw, 780 * u)), int(58 * u)
    overlay(frame, text_image("TRYB " + MODE_TXT[d.mode][0], bw, bh, size=15 * u, fg=MODE_TXT[d.mode][1], weight="bold"),
            0, 0, 0.9)
    return frame


SHOT_AT = {"intro": 4.0, "jumps": 2.5, "far": 5.0, "track": 4.0, "cmp0_snn": 2.5, "cmp0_classical_p": 2.5,
           "cmp2_snn": 2.9, "summary": 1.0}     # zrzuty ekranu: akt → sekunda aktu


def record_main(d, path, shots_dir=None, W=1920, H=1080):
    show = Show()
    d.reset(*ACTS[0]["reset"], mode="snn")
    ext, panel = Ext(d, W - 720, H), Panel(d, 720, H)
    hi = (Ext(d, 1600, 1440), Panel(d, 960, 1440)) if shots_dir else None
    want = {show.start[i] + int(round(SHOT_AT[a["name"]] * 100)): a["name"] for i, a in enumerate(show.acts)
            if a["name"] in SHOT_AT}
    vid, saved = Video(path, W, H), []
    try:
        while not show.done:
            show.step(d)
            if show.k % 4 == 0:
                vid.write(compose_main(d, show, ext, panel, W, H))
            if hi and show.k in want:
                import matplotlib.image as mpimg
                p = os.path.join(shots_dir, f"flymind_{len(saved) + 1:02d}_{want[show.k]}.png")
                mpimg.imsave(p, compose_main(d, show, hi[0], hi[1], 2560, 1440))
                saved.append(p)
    finally:
        vid.close()
        ext.close()
        hi and hi[0].close()
    return show, saved


def record_neurons(d, path, shot_path=None, W=1920, H=1080):
    """Fragment „neurony”: duży panel (lewo) + kamera robota i widok zewnętrzny (prawo); akty SNN: skoki, daleko, śledzenie."""
    show = Show(tuple(a for a in ACTS if a["name"] in ("jumps", "far", "track")))
    pw, rw = 1200, W - 1200
    panel, eye, ext = Panel(d, pw, H), Ext(d, rw, H // 2), Ext(d, rw, H - H // 2)
    vid = Video(path, W, H)
    try:
        while not show.done:
            show.step(d)
            if show.k % 4:
                continue
            frame = np.zeros((H, W, 3), np.uint8)
            s, flag = status_line(d)
            frame[:, :pw] = panel.render(s, flag)
            frame[:H // 2, pw:] = eye.render("eye")
            sh = show.shot()
            frame[H // 2:, pw:] = ext.render(SHOTS["behind"] if sh == "eye" else sh)
            u = H / 1080
            overlay(frame, text_image("kamera robota (widok w pełnej rozdzielczości; sieć dostaje 96×128 z panelu)",
                                      rw, int(34 * u), size=9.5 * u), pw, 0)
            ch = int(120 * u)
            overlay(frame, text_image(show.caption(), rw, ch, size=10.5 * u), pw, H - ch)
            vid.write(frame)
            if shot_path and show.k == show.start[0] + 900:
                import matplotlib.image as mpimg
                mpimg.imsave(shot_path, frame)
    finally:
        vid.close()
        eye.close()
        ext.close()


class CmpPlot:
    """Dolny pasek nagrania porównawczego: błąd i komenda ω obu sterowników na wspólnej osi czasu próby."""

    def __init__(self, w, h):
        self.fig, self.canvas = _fig(w, h)
        u = h / 420
        gs = self.fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.78], wspace=0.28, left=0.05, right=0.985, top=0.83, bottom=0.17)
        self.ax_e, self.ax_o = self.fig.add_subplot(gs[0], facecolor="#161b22"), self.fig.add_subplot(gs[1], facecolor="#161b22")
        self.ax_t = self.fig.add_subplot(gs[2], facecolor="#101418")
        self.ax_t.axis("off")
        for ax, t in ((self.ax_e, "błąd do celu [°] (prawda symulatora)"), (self.ax_o, "komenda ω [rad/s]")):
            ax.set_title(t, fontsize=11 * u, color="#e6edf3", loc="left")
            ax.tick_params(labelsize=9 * u, colors="#9aa7b4")
            ax.set_xlim(0, 3)
            ax.set_xlabel("czas próby [s]", fontsize=9 * u, color="#9aa7b4")
            for sp in ax.spines.values():
                sp.set_color("#3a4450")
        self.ax_e.axhspan(-5, 5, color="#2ea043", alpha=0.18)
        self.ax_e.set_ylim(-32, 32)
        self.ax_o.set_ylim(-1.15, 1.15)
        self.l = {k: ax.plot([], [], color=c, lw=2 * u, label=lab)[0]
                  for k, ax, c, lab in (("e_snn", self.ax_e, "#6cc4ff", "SNN"), ("e_p", self.ax_e, "#ffd166", "P"),
                                        ("o_snn", self.ax_o, "#6cc4ff", "SNN"), ("o_p", self.ax_o, "#ffd166", "P"))}
        for ax in (self.ax_e, self.ax_o):
            ax.legend(loc="upper right", fontsize=9 * u, facecolor="#0d1117", edgecolor="#3a4450", labelcolor="#e6edf3")
        self.txt = self.ax_t.text(0, 1, "", fontsize=10.5 * u, color="#e6edf3", va="top", family="monospace", linespacing=1.5)
        self.u = u

    def render(self, ds, rows):
        for k, d in (("snn", ds[0]), ("p", ds[1])):
            n = min(d.k, HIST)
            x = np.arange(d.k - n + 1, d.k + 1) * L.DT
            self.l["e_" + k].set_data(x, d.hist["e"][-n:])
            self.l["o_" + k].set_data(x, d.hist["omega"][-n:])
        self.txt.set_text("\n".join(rows))
        self.canvas.draw()
        return _rgb(self.canvas)


def record_compare(net, calib, path, shot_path=None, W=1920, H=1080):
    """Porównanie obok siebie: dwie NIEZALEŻNE symulacje (SNN | P) z identycznym startem i celem w każdej próbie."""
    ds = (Demo("snn", *CMP[0], net=net, calib=calib), Demo("classical_p", *CMP[0], net=net, calib=calib))
    vh = 660
    exts = [Ext(d, W // 2, vh) for d in ds]
    plot = CmpPlot(W, H - vh)
    vid, results = Video(path, W, H), []
    u = H / 1080
    try:
        for i, (az, rho) in enumerate(CMP):
            for d in ds:
                d.reset(az, rho, mode=d.mode, noise_seed=SEED_CMP + i)
            assert np.array_equal(ds[0].sim.d.qpos, ds[1].sim.d.qpos) and np.array_equal(ds[0].sim.d.ctrl, ds[1].sim.d.ctrl)
            e = ([], [])
            for k in range(L.TICKS):
                for j, d in enumerate(ds):
                    e[j].append(math.degrees(d.tick()))
                if k % 4 == 3:
                    frame = np.zeros((H, W, 3), np.uint8)
                    for j, (d, x) in enumerate(zip(ds, exts)):
                        frame[:vh, j * W // 2:(j + 1) * W // 2] = x.render(SHOTS["behind"])
                        s, flag = status_line(d)
                        txt, col = MODE_TXT[d.mode]
                        overlay(frame, text_image(("SNN (DNa02)" if j == 0 else "P (klasyczny)") + f"   błąd {d.last['e_deg']:+5.1f}°"
                                                  + ("   BRAK RUCHU" if flag else ""), W // 2, int(54 * u), size=15 * u,
                                                  fg=col, weight="bold"), j * W // 2, 0, 0.9)
                    overlay(frame, text_image(f"próba {i + 1}/{len(CMP)}: cel {az:+.0f}°, ρ {rho:.2f} m — ten sam start, "
                                              "ta sama scena i ograniczenia; obie symulacje liczone równolegle w tym samym takcie",
                                              W, int(36 * u), size=10.5 * u, align="center"), 0, vh - int(36 * u), 0.85)
                    rows = ["wyniki (średni |błąd| ostatnie 0,5 s)", ""] + [
                        f"{r['az']:+4.0f}°/{r['rho']:.2f}  SNN {r['snn']:5.1f}° {'✓' if r['snn_ok'] else '✗'}   "
                        f"P {r['p']:4.1f}° {'✓' if r['p_ok'] else '✗'}" for r in results]
                    frame[vh:] = plot.render(ds, rows)
                    vid.write(frame)
                    if shot_path and i == 0 and k == 239:
                        import matplotlib.image as mpimg
                        mpimg.imsave(shot_path, frame)
            m = [L.metrics(dict(e_deg=x, az0_deg=az, safety_flags={})) for x in e]
            results.append(dict(az=az, rho=rho, seed=SEED_CMP + i, snn=round(m[0]["final_abs_err"], 2), snn_ok=m[0]["success"],
                                p=round(m[1]["final_abs_err"], 2), p_ok=m[1]["success"]))
            print("porównanie:", results[-1], flush=True)
        rows = ["wyniki (średni |błąd| ostatnie 0,5 s)", ""] + [
            f"{r['az']:+4.0f}°/{r['rho']:.2f}  SNN {r['snn']:5.1f}° {'✓' if r['snn_ok'] else '✗'}   "
            f"P {r['p']:4.1f}° {'✓' if r['p_ok'] else '✗'}" for r in results]
        frame[vh:] = plot.render(ds, rows)
        for _ in range(75):                                           # 3 s planszy z kompletem wyników
            vid.write(frame)
    finally:
        vid.close()
        for x in exts:
            x.close()
        for d in ds:
            d.sim.close()
    return results


def make_media(d, out):
    """Wszystkie nagrania i zrzuty do NOWEGO katalogu (istniejące pliki nie są nadpisywane)."""
    if os.path.exists(out) and os.listdir(out):
        sys.exit(f"{out} istnieje i nie jest pusty — nie nadpisuję; podaj nowy katalog")
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    show, shots = record_main(d, os.path.join(out, "flymind_presentation.mp4"), out)
    print(f"prezentacja: {show.total / 100:.0f} s symulacji, {len(shots)} zrzutów, {time.time() - t0:.0f} s", flush=True)
    record_neurons(d, os.path.join(out, "flymind_neurons.mp4"), os.path.join(out, "flymind_neurons.png"))
    print(f"neurony: gotowe, {time.time() - t0:.0f} s", flush=True)
    cmp = record_compare((d.spec, d.idx), d.calib, os.path.join(out, "flymind_snn_vs_p.mp4"), os.path.join(out, "flymind_snn_vs_p.png"))
    with open(os.path.join(out, "results.json"), "x") as fh:
        json.dump(dict(note="Pokaz (4 próby), nie eksperyment. Miernik: loop.metrics (V5). Te same położenia i ziarna w "
                            "prezentacji i w nagraniu porównawczym.", cmp_positions=CMP, presentation_compare=show.results,
                       side_by_side=cmp, seeds=dict(alif_demo=SEED0, alif_compare=[SEED_CMP + i for i in range(len(CMP))])),
                  fh, ensure_ascii=False, indent=1)
    print(f"zapisano w {out} ({time.time() - t0:.0f} s)", flush=True)


def _out_ok(p):
    p = os.path.realpath(p)
    roots = [os.path.realpath(HERE), "/private/tmp", "/tmp"] + ([os.path.realpath(os.environ["TMPDIR"])] if os.environ.get("TMPDIR") else [])
    return any(p == r or p.startswith(r + os.sep) for r in roots)


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--present", action="store_true", help="tryb prezentacji (scenariusz, automatyczna kamera, podpisy)")
    ap.add_argument("--once", action="store_true", help="prezentacja: jeden przebieg zamiast pętli")
    ap.add_argument("--mode", choices=("snn", "p"), default="snn")
    ap.add_argument("--az", type=float, default=20.0, help="początkowy namiar piłeczki [°, + w lewo]")
    ap.add_argument("--rho", type=float, default=0.20, help="początkowa odległość piłeczki od kamery [m]")
    ap.add_argument("--jump", type=float, default=0.0, help="co ile sekund losowo przestawić piłeczkę (0 = nie)")
    ap.add_argument("--speed", type=float, default=1.0, help="tempo względem czasu rzeczywistego (nie zmienia sterowania)")
    ap.add_argument("--seed", type=int, default=SEED0, help="szum ALIF i losowe położenia piłeczki")
    ap.add_argument("--seconds", type=float, default=0.0, help="zamknij okno po tylu sekundach (0 = nigdy)")
    ap.add_argument("--panel-inproc", action="store_true", help="okno: rysuj panel w tym samym procesie (wolniej)")
    ap.add_argument("--panel-fps", type=float, default=20.0, help="okno: odświeżanie panelu [1/s] (symulacja niezależnie)")
    ap.add_argument("--log", help="okno: zapisz statystyki (i e(t) prezentacji) do NOWEGO pliku JSON")
    ap.add_argument("--record", help="bez okna: nagraj prezentację do MP4 (nowy plik)")
    ap.add_argument("--media", help="bez okna: wszystkie nagrania i zrzuty do NOWEGO katalogu")
    a = ap.parse_args()
    for p in (a.record, a.media, a.log):
        if p and not _out_ok(p):
            sys.exit(f"{p}: zapis tylko w flymind/demo/, /tmp albo $TMPDIR")
    if a.record and os.path.exists(a.record):
        sys.exit(f"{a.record} istnieje — nie nadpisuję")
    d = Demo("classical_p" if a.mode == "p" else "snn", a.az, a.rho, a.seed)
    print(f"sieć: {len(d.spec.bodies)} neuronów, slope SNN {d.calib['slope_snn']:.1f} Hz/rad, slope P {d.calib['slope_p']:.3f}",
          flush=True)
    if a.media:
        make_media(d, a.media)
    elif a.record:
        record_main(d, a.record)
        print("zapisano:", a.record)
    else:
        run_viewer(d, a)


if __name__ == "__main__":
    main()
