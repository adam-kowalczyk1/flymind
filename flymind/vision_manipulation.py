"""flymind/vision_manipulation.py — etap „wzrok w pętli”: kamera na chwytaku zamiast położenia z symulatora. SYMULACJA.

Uruchamiaj z katalogu tymczasowego (MuJoCo dopisuje MUJOCO_LOG.TXT do bieżącego katalogu):
  .venv/bin/python -I -B flymind/vision_manipulation.py bench --arm E_vis_touch --tag E_vis_touch_v1

Co jest NOWE względem sensory_manipulation.py (tamten plik i object_handling.py są importowane bez zmian):
  1. Percept nie pochodzi z symulatora. Kontroler dostaje wyłącznie klatki kamery „eye” (na chwytaku) i własne enkodery.
  2. Jedna sieć z danych MaleCNS = droga wzrokowa LC10a → pośrednie → DNa02 (visual_path) ∪ obwód nogi T2 L (leg_circuit),
     wszystkie krawędzie z danych między tymi neuronami (podgraf indukowany). W danych DNa02 L ma 1190 synaps do 30
     neuronów obwodu T2 L (27 interneuronów, 3 MN) — to jedyne bezpośrednie połączenie wzroku z dotykiem w tej sieci [DATA].
  3. Sieć steruje DWIEMA rzeczami: obrotem bazy na przedmiot (DNa02 L−P, jak zweryfikowana pętla V5) i szczęką (MN goleni).

Przepływ informacji (rozdzielony):
  kamera „eye” na chwytaku
    → [MODEL] klatka 96×128 w każdym takcie (100 Hz czasu symulacji) → enkoder koloru encoder.TargetEncoder → prąd LC10a L/R
    → [DATA] sieć → DNa02 L/R → dekoder SteerDecoder → prędkość obrotu bazy           (źródło „snn:DNa02”)
    → [KLASYCZNE, jawnie] geometria obrazu na klatce 480×640 (2 klatki na przedmiot): sylwetka przedmiotu rzutowana na blat z własnej kinematyki; wysokość z paralaksy
      ruchu (dwa widoki po obrocie bazy o `peer`); z tego prostokąt z góry + wysokość dla klasycznego planu dojazdu
  dotyk padów → szczecinki nogi, kąt/prędkość szczęki → FeCO (jak w poprzednim etapie) → MN goleni → moment szczęki
  stan symulatora: TYLKO ewaluator (object_handling.World) i dziennik błędu percepcji; nie trafia do sterowania
  (test V2: podmiana wartości wyroczni na NaN nie zmienia przebiegu).

Czego sieć NIE robi: odległość, kształt, orientacja i wysokość przedmiotu liczy klasyczna geometria obrazu; dojazd, podniesienie,
transport i puszczenie to to samo klasyczne rusztowanie co wcześniej. Enkoder to detektor koloru (przedmioty są zielone),
nie model oka muchy. Przypisanie „obrót bazy ≙ skręt muchy” to analogia z V5 [MODEL].
"""
import argparse
import json
import math
import os
import resource
import sys
import time
from dataclasses import asdict, dataclass, replace

import numpy as np
import pandas as pd
from scipy.ndimage import binary_dilation

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import object_handling as oh  # noqa: E402
import sensory_manipulation as sm  # noqa: E402
import visual_path  # noqa: E402
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402
from connectome import load_edges  # noqa: E402
from decoder import SteerDecoder, SteerParams  # noqa: E402
from encoder import EncoderParams, TargetEncoder  # noqa: E402
from leg_circuit import select as leg_select  # noqa: E402
from object_handling import Fail  # noqa: E402
from safety import Command  # noqa: E402
from sensory import spot_clip  # noqa: E402
from snn_interface import DEFAULT_SIGN, NT_COLS, ModelParams, assign_nt, build  # noqa: E402
from so101 import integrate_pan  # noqa: E402

OUT = os.path.join(oh.ROOT, "flymind", "results", "vision_manipulation")
# Poza „patrzenia”: znaleziona przeszukaniem własnej kinematyki (kamera 16,0 cm nad blatem, patrzy niemal pionowo w dół na
# środek strefy; najniższy punkt chwytaka 8,4 cm nad blatem, czyli nad najwyższym przedmiotem zestawu + zapas podajnika).
# v3: staw 3 = 1,60 rad (w v1/v2 było 1,65 — o 0,04 rad ZA marginesem warstwy bezpieczeństwa 1,608, która przycinała cel
# w każdym takcie; skutek: po nieudanej próbie „ramię nie w domu” → brak drugiego podejścia i przerwane serie).
Q_SURVEY = (0.105, -0.91, 0.68, 1.60, 1.586, 0.93)
GREEN = (40 / 255, 180 / 255, 50 / 255, 1.0)       # kolor bodźca kalibracyjnego V4 — tylko wygląd, fizyka bez zmian
ENC = EncoderParams(blur_px=3)                     # jak V4 v2 / V5
STEER = SteerParams(tau_s=(0.10,), gain=2.5, w_max=1.0)   # jak V5 (loop.py)
LO, HI = (96, 128), (480, 640)
NOISE_VIS = 2.0                                    # mV: szum prądu neuronów drogi wzrokowej, jak w V5 (ALIFParams(noise=2.0));
                                                   # obwód nogi bez szumu, jak w poprzednim etapie. Każdy podobwód w swoim
                                                   # zweryfikowanym reżimie [MODEL].
SEED_NOISE, SEED_CAL = 18_000_000, 18_190_000      # ziarno szumu = SEED_NOISE + ziarno sceny; kalibracja: SEED_CAL + i
TH = np.radians(np.arange(0, 360, 0.5))
U = np.c_[np.cos(TH), np.sin(TH)]
ARMS = {  # nazwa: (szczęka, obrót bazy przy patrzeniu, opis)
    "A_cam": ("classical:object_handling", "classical:P_encoder", "klasyczny kontroler + percept z kamery"),
    "B_cam": ("snn:legT2L", "classical:P_encoder", "sieć nogi (sam dotyk) steruje szczęką; wzrok poza siecią"),
    "D_vis": ("snn:vis+legT2L", "snn:DNa02", "sieć wspólna, kanał dotyku odcięty (sam wzrok)"),
    "E_vis_touch": ("snn:vis+legT2L", "snn:DNa02", "sieć wspólna: wzrok + dotyk"),
    "E_blind_grasp": ("snn:vis+legT2L", "snn:DNa02", "E, ale wejście wzrokowe wyłączone poza patrzeniem (czy wzrok zmienia chwyt)"),
    "F_vis_touch_feco": ("snn:vis+legT2L+FeCO", "snn:DNa02", "sieć wspólna: wzrok + dotyk + propriocepcja FeCO"),
}


@dataclass(frozen=True)
class VisCfg:
    n_min: int = 12                # px (96×128) powyżej progu kontrastu: „coś widać”
    om_still: float = 0.10         # rad/s: obrót uznany za ustalony, gdy |średnia ω z ostatnich still_ticks taktów| poniżej
    still_ticks: int = 30          # (wyjście DNa02 to pojedyncze impulsy: chwilowa ω skacze, liczy się średnia)
    orient_max: float = 2.5        # s na ustawienie się od pierwszego zobaczenia (potem pomiar mimo wszystko)
    peer: float = 0.25             # rad: obrót bazy między dwoma widokami (paralaksa ruchu); kierunek, przy którym przedmiot
                                   # odsuwa się w kadrze od szczęki
    peer_settle: int = 8           # taktów po obrocie przed drugim widokiem
    min_px: int = 150              # px (480×640) sylwetki, poniżej — brak perceptu
    k_max: float = 2.0             # ograniczenie skali paralaksy (wysokość ≤ połowa wysokości kamery)
    h_margin: float = 0.005        # m dodawane do wysokości dla planu (niepewność paralaksy; ustalone przed benchmarkiem)
    box_margin: float = 0.02       # m: piksele rzutujące się na pudełko + tyle są pomijane (robot wie, gdzie ma pudełko)
    pan_lim: float = 1.2           # rad


# ---------------------------------------------------------------- kamera i geometria obrazu ------------------------
class Eye:
    """Kamera „eye” na chwytaku: klatki + klasyczna geometria. Nie czyta położeń przedmiotów z symulatora."""

    def __init__(self, world, vc=VisCfg()):
        import mujoco
        self.vc, self.sim, sc = vc, world.sim, world.scene
        m = self.sim.m
        m.geom_rgba[m.geom("mark_zone").id] = 0                    # znacznik strefy niewidoczny (był żółty: myliłby enkoder)
        for o in world.objs:                                       # wszystkie przedmioty zielone — tylko wygląd
            m.geom_rgba[m.body_geomadr[o["bid"]]:m.body_geomadr[o["bid"]] + m.body_geomnum[o["bid"]]] = GREEN
        m.vis.headlight.ambient[:], m.vis.headlight.diffuse[:] = 0.6, 0.4   # światło rozproszone: boki brył nie są czarne
        self.r = {s: mujoco.Renderer(m, *s) for s in (LO, HI)}     # LO: co takt dla sieci; HI: tylko do pomiaru geometrii
        for r in self.r.values():
            for f in (mujoco.mjtRndFlag.mjRND_SHADOW, mujoco.mjtRndFlag.mjRND_REFLECTION, mujoco.mjtRndFlag.mjRND_SKYBOX):
                r.scene.flags[f] = False                           # jak so101.SO101Sim: bez cieni/odbić/nieba
        self.enc = TargetEncoder(LO, ENC)
        x = self.frame(LO).astype(np.float32)                      # ramię w pozie patrzenia, przedmiotów jeszcze nie ma w kadrze:
        own = (x[..., 1] - (x[..., 0] + x[..., 2]) / 2) / max(1.0, float(x.mean())) > 0.05
        self.own = binary_dilation(own, iterations=2)              # maska WŁASNEGO chwytaka (złote śruby pobudzały enkoder
        H, W = HI                                                  # i baza dryfowała bez bodźca — test śledzenia v1, S0)
        t = math.tan(math.radians(ENC.fovy_deg) / 2)
        jj, ii = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
        self.rays = np.stack([(2 * jj / W - 1) * t * W / H, (1 - 2 * ii / H) * t, -np.ones((H, W))], -1)   # układ kamery
        (ax, ay), g = sc.box_in, sc.wall + vc.box_margin
        self.box = (sc.box_xy[0] - ax - g, sc.box_xy[0] + ax + g, sc.box_xy[1] - ay - g, sc.box_xy[1] + ay + g)
        self.t = np.zeros(2)                                       # czas zegarowy: render, siatkówka+enkoder

    def close(self):
        """Jak SO101Sim.close: każdy renderer zwalniany we WŁASNYM kontekście GL (inaczej psuje bufory następnego)."""
        for r in self.r.values():
            if r._gl_context is not None:
                r._gl_context.make_current()
            r.close()
        self.r = {}

    def frame(self, shape=HI):
        self.r[shape].update_scene(self.sim.d, camera="eye")
        return self.r[shape].render()

    def see(self):
        """Klatka 96×128 → wyjście enkodera. Wywoływane w każdym takcie (kamera 100 Hz czasu symulacji)."""
        t0 = time.perf_counter()
        img = self.frame(LO)
        t1 = time.perf_counter()
        img = img.copy()
        img[self.own] = int(img.mean())
        e = self.enc.encode(img)
        self.t[:] = t1 - t0, time.perf_counter() - t1
        return img, e

    def silhouette(self, img, q):
        """Punkty blatu [K, 2], na które rzutują się piksele przedmiotu, i położenie kamery — z klatki i WŁASNYCH enkoderów q."""
        k = self.sim.fk(np.asarray(q, float))
        E, R = k["eye"], k["eye_R"]
        x = img.astype(np.float32)
        c = (x[..., 1] > 1.4 * np.maximum(x[..., 0], x[..., 2])) & (x[..., 1] > 20)     # odcień zielony, niezależnie od jasności
        ray = self.rays[c] @ R.T
        ray = ray[ray[:, 2] < -0.05]
        P = E[:2] + ray[:, :2] * (E[2] / -ray[:, 2:3])
        b = self.box
        return P[~((P[:, 0] > b[0]) & (P[:, 0] < b[1]) & (P[:, 1] > b[2]) & (P[:, 1] < b[3]))], E.copy()


def measure(S1, E1, S2, E2, vc=VisCfg()):
    """Prostokąt z góry + wysokość z dwóch sylwetek na blacie (kamera w E1, potem w E2). Klasyczna geometria:
    punkt na wysokości h rzutuje się z kamery na blat w E + (p − E)·k, k = Z/(Z − h). Dla kierunku u = (E1 − E2)/b skrajny
    punkt sylwetki przesuwa się między widokami o (k − 1)·b → k, h. Potem w każdym kierunku cofamy rzut górnej ściany."""
    b = float(np.hypot(*(E1 - E2)[:2]))
    u = (E1 - E2)[:2] / b
    k = float(np.clip(1 + ((S2 @ u).max() - (S1 @ u).max()) / b, 1.0, vc.k_max))
    sS, Eu = (S1 @ U.T).max(0), E1[:2] @ U.T
    s = np.where(sS <= Eu, sS, (sS + (k - 1) * Eu) / k)            # funkcja podparcia prawdziwego obrysu
    ext = s[:360] + s[360:]
    j = int(np.argmin(ext[:180] * ext[180:]))
    mid = lambda i: (s[i] - s[i + 360]) / 2  # noqa: E731
    c = U[j] * mid(j) + U[j + 180] * mid(j + 180)
    a, d = float(ext[j]), float(ext[j + 180])
    l, w, yaw = (a, d, TH[j]) if a >= d else (d, a, TH[j + 180])
    return dict(x=float(c[0]), y=float(c[1]), yaw=float(yaw % math.pi), l=l, w=w, h=float(E1[2] * (k - 1) / k), k=k, baseline=b)


# ---------------------------------------------------------------- sieć wspólna: wzrok + noga ------------------------
def union_spec(fc):
    """Podgraf indukowany MaleCNS: ciała obwodu nogi (w kolejności leg_circuit, więc indeksy LegJaw pozostają ważne)
    + ciała drogi wzrokowej. Znaki jak w leg_circuit.network (glutaminian jawny)."""
    c = sm.FlyJawCfg(glu_sign=fc.glu_sign)
    leg, _, _ = leg_select(c.leg, c.side)
    vb, vg, vrep = visual_path.select()
    if set(leg) & set(vb):
        raise ValueError("obwód nogi i droga wzrokowa mają wspólne ciała — indeksy trzeba by przeliczyć")
    bodies = list(leg) + list(vb)
    edges, erep = load_edges(visual_path.WEIGHTS, bodies=bodies)
    nts = pd.read_feather(visual_path.NTS)
    tab = nts.set_index("body").reindex(bodies)[list(NT_COLS)]
    ov = {b: ("unknown", "brak przekaźnika; znak 0") for b, r in tab.iterrows()
          if not any(isinstance(x, str) and x != "unclear" for x in r)}
    signs = {**DEFAULT_SIGN, "glutamate": fc.glu_sign}
    signs.update({n: 0.0 for n in set(assign_nt(bodies, nts, ov).nt) - set(signs)})
    spec = build(edges, bodies, nts, ModelParams(J0=c.J0, sign_map=signs), nt_overrides=ov)
    pos = {b: i for i, b in enumerate(bodies)}
    idx = {k: np.array([pos[b] for b in v]) for k, v in vg.items()}
    L = len(leg)
    cross = dict(vis_to_leg=int(np.count_nonzero(spec.W[:L, L:])), leg_to_vis=int(np.count_nonzero(spec.W[L:, :L])),
                 dna02L_to_leg=int(np.count_nonzero(spec.W[:L, idx["DNa02_L"][0]])),
                 dna02R_to_leg=int(np.count_nonzero(spec.W[:L, idx["DNa02_R"][0]])))
    return spec, idx, dict(N=len(bodies), leg=L, visual=vrep["sizes"], edges=erep["loaded"], cross_edges=cross)


class VisJaw(sm.LegJaw):
    """Sieć wspólna. Wejścia: g (enkoder obrazu → LC10a L/R), dotyk (szczecinki), opcjonalnie FeCO. Wyjścia: moment szczęki
    (MN goleni, jak LegJaw) i prędkość obrotu bazy omega (DNa02 L−P)."""

    def __init__(self, fc, touch=True, proprio=False, vision=True, slope=None, noise=NOISE_VIS):
        super().__init__(fc, touch, proprio)
        spec, self.vis, self.rep = union_spec(fc)
        self.spec, self.N, self.use_vision = spec.W, spec.W.shape[0], vision
        self.sizes = dict(self.sizes, **self.rep, noise_visual_mV=noise)
        self.g, self.omega, self.slope = np.zeros(2), 0.0, slope
        self.nz = np.r_[np.zeros(self.rep["leg"]), np.full(self.N - self.rep["leg"], float(noise))]
        self.reset()

    def reset(self, seed=None):
        """seed: ziarno szumu drogi wzrokowej (None → 0, tylko do prac pomocniczych)."""
        super().reset()
        self.rng = np.random.default_rng(seed or 0)
        if getattr(self, "slope", None):
            self.dec = SteerDecoder({k: self.vis[k] for k in ("DNa02_L", "DNa02_R")}, ("DNa02",), [0.0], [self.slope], STEER)
        self.dn = np.zeros(2)

    def step(self, touch, q, qd, dt=0.01):
        c, f = self.c, self.fc
        t0 = time.perf_counter()
        X = np.zeros(self.N)
        if self.use_touch:
            for ix, x in zip(self.pad_in, touch[:2]):
                X[ix] = min(c.max_mV, c.gain_mV_per_N * max(0.0, float(x)))
        if self.use_proprio:
            X[self.feco["claw_ext"]] = f.feco_mV * min(1.0, max(0.0, (f.q_mid - q) / f.q_span))
            X[self.feco["claw_flex"]] = f.feco_mV * min(1.0, max(0.0, (q - f.q_mid) / f.q_span))
            X[self.feco["hook_ext"]] = f.feco_mV * min(1.0, max(0.0, -qd / f.qd_ref))
            X[self.feco["hook_flex"]] = f.feco_mV * min(1.0, max(0.0, qd / f.qd_ref))
        if self.use_vision:
            X[self.vis["in_L"]], X[self.vis["in_R"]] = ENC.i_max * self.g[0], ENC.i_max * self.g[1]
        t1 = time.perf_counter()
        if self.nz.any():                                          # szum co 1 ms tylko w drodze wzrokowej (jak V5)
            s = np.vstack([self.net.run(X + self.nz * self.rng.standard_normal(self.N), 1) for _ in range(c.steps)])
        else:
            s = self.net.run(X, c.steps)
        t2 = time.perf_counter()
        a = dt / c.rate_tau
        self.r_press += a * (s[:, self.press].mean() * 1000 - self.r_press)
        self.r_release += a * (s[:, self.release].mean() * 1000 - self.r_release)
        self.dn = np.array([s[:, self.vis["DNa02_L"]].mean(), s[:, self.vis["DNa02_R"]].mean()]) * 1000
        if self.slope:
            self.omega = float(self.dec.step(np.asarray(s, bool), 1.0)["omega"])
        self.t[:] = t1 - t0, t2 - t1, time.perf_counter() - t2
        return c.k * (self.r_press - self.r_release)


def calibrate(driver, ticks=60):
    """Nachylenie dekodera skrętu [Hz/rad] TEJ sieci na bodźcach syntetycznych V4 (plamka 9 px, azymut −30…30° co 10°),
    offset 0 — ta sama procedura co V4/V5, bez szumu. Zwraca nachylenie i surowe różnice DNa02 L−P."""
    enc, az = TargetEncoder(LO, ENC), np.arange(-30, 31, 10)
    imgs = spot_clip(np.radians(az), np.zeros(len(az)), LO, ENC.fovy_deg, 9, (40, 180, 50), (120, 120, 120)).images
    d = []
    for i, im in enumerate(imgs):
        driver.reset(SEED_CAL + i)
        driver.g = enc.encode(im)["g"]
        r = []
        for _ in range(ticks):
            driver.step(np.zeros(3), 0.9, 0.0)
            r.append(driver.dn[0] - driver.dn[1])
        d.append(float(np.mean(r[ticks // 2:])))
    driver.g = np.zeros(2)
    driver.reset()
    x, d = np.radians(az), np.array(d)
    return float((d * x).sum() / (x * x).sum()), d.round(2).tolist()


def calibrate_p():
    """Regulator P na wyjściu enkodera (gL − gP), te same bodźce (jak loop.calibrate_p)."""
    enc, az = TargetEncoder(LO, ENC), np.arange(-30, 31, 10)
    imgs = spot_clip(np.radians(az), np.zeros(len(az)), LO, ENC.fovy_deg, 9, (40, 180, 50), (120, 120, 120)).images
    d, x = np.array([enc.encode(im)["g"] @ [1, -1] for im in imgs]), np.radians(az)
    return float((d * x).sum() / (x * x).sum())


# ---------------------------------------------------------------- kontrolery z kamerą --------------------------------
class Cam:
    """Wspólne dla wszystkich ramion: patrzenie (obrót bazy na przedmiot), pomiar z kamery, rejestracja błędu percepcji."""

    def cam_init(self, vc, pan_by, slope_p):
        self.vc, self.pan_by, self.slope_p = vc, pan_by, slope_p
        self.eye = Eye(self.w, vc)
        self.pan_t, self.p_f, self.om = float(self.home[0]), 0.0, 0.0
        self.g, self.n_px, self.img = np.zeros(2), 0, None
        self.pan_src, self.blank, self.swap = "classical:reach", False, False
        self.vlog, self.clat = [], []

    def see(self):
        self.img, e = self.eye.see()
        if self.blank:                                             # test: brak klatki (zasłonięcie / awaria kamery)
            e = self.eye.enc.encode(None)
        self.g, self.n_px = (e["g"][::-1] if self.swap else e["g"]), e["n_px"]
        a = math.exp(-0.01 / STEER.tau_s[0])                       # regulator P (porównanie klasyczne), ten sam filtr co V5
        self.p_f = a * self.p_f + (1 - a) * float(self.g @ [1, -1])
        self.clat.append(tuple(self.eye.t))

    def omega(self):
        if self.pan_by.startswith("snn"):
            return self.driver.omega
        return float(np.clip(STEER.gain * self.p_f / self.slope_p, -STEER.w_max, STEER.w_max))

    def gaze(self):
        """Jeden takt patrzenia: stawy 1–4 w pozie patrzenia, baza według wyjścia sieci (albo regulatora P)."""
        tgt = self.home[:5].copy()
        tgt[0] = self.pan_t
        self.pan_src = self.pan_by
        try:
            self.tick(tgt, "open")
        finally:
            self.pan_src = "classical:reach"
        self.om = self.omega()
        self.pan_t = float(np.clip(integrate_pan(self.pan_t, self.om, self.lim.dt), -self.vc.pan_lim, self.vc.pan_lim))

    def look(self):
        """Dwa widoki (przed i po obrocie bazy o `peer`) → percept z samej kamery i enkoderów. None = nic nie zmierzono."""
        vc = self.vc
        S1, E1 = self.eye.silhouette(self.eye.frame(), self.obs.q)
        if len(S1) < vc.min_px:
            return None
        tgt = np.r_[self.home[:5], self.home[5]]
        tgt[0] = self.pan_t + vc.peer
        self.pan_src = "classical:peer"
        try:
            self.follow([tgt], "open")
            self.wait(vc.peer_settle * self.lim.dt, tgt[:5], "open")
        finally:
            self.pan_src = "classical:reach"
        self.pan_t = float(tgt[0])
        S2, E2 = self.eye.silhouette(self.eye.frame(), self.obs.q)
        if len(S2) < vc.min_px:
            return None
        p = measure(S1, E1, S2, E2, vc)
        p["h_est"], p["h"] = p["h"], p["h"] + vc.h_margin
        return p

    def wait_percept(self):
        vc, t0, oms, t_seen = self.vc, self.obs.t, [], None
        self.pan_t = float(self.obs.q[0])
        while True:
            if self.w.done():
                return None
            if self.obs.t - t0 > self.cfg.idle_max:
                self.stop = "no_object: kamera nie widzi przedmiotu (albo strefa zablokowana)"
                return None
            self.gaze()
            seen = self.n_px >= vc.n_min
            oms = oms[1 - vc.still_ticks:] + [self.om] if seen else []
            t_seen = self.obs.t if seen and t_seen is None else t_seen
            still = len(oms) == vc.still_ticks and abs(float(np.mean(oms))) < vc.om_still
            if not still and not (t_seen is not None and self.obs.t - t_seen > vc.orient_max):
                continue
            rec = dict(t_wait=self.obs.t - t0, t_orient=self.obs.t - t_seen, converged=bool(still), pan=self.pan_t)
            p = self.look()
            oms, t_seen = [], None
            if p is None:
                continue
            truth = self.w.percept()        # rejestruje próbę w świecie; wartości wyroczni idą TYLKO do dziennika błędu
            if truth is None:
                continue
            self.vlog.append(dict(rec, cam=p, truth=truth))
            return p


class ClassicCam(Cam, oh.Controller):
    def __init__(self, world, cfg, vc, slope_p):
        super().__init__(world, cfg)
        self.cam_init(vc, "classical:P_encoder", slope_p)

    def tick(self, tgt, mode):
        self.see()
        super().tick(tgt, mode)


class VisGrip(Cam, sm.FlyGrip):
    """FlyGrip z kamerą: klatka w każdym takcie; sieć dostaje wyjście enkodera (jeśli ma kanał wzrokowy)."""

    def __init__(self, world, cfg, driver, src, fc, vc, pan_by, slope_p, grasp_vision=True):
        super().__init__(world, cfg, driver, src, fc)
        self.cam_init(vc, pan_by, slope_p)
        self.grasp_vision = grasp_vision

    def tick(self, tgt, mode):                                     # jak FlyGrip.tick + kamera i źródło komendy bazy
        o, g = self.obs, self.grip
        self.see()
        w0 = time.perf_counter()
        if hasattr(self.driver, "g"):
            self.driver.g = self.g if self.grasp_vision or self.pan_src == self.pan_by else np.zeros(2)
        self.tau_fly = float(self.driver.step(o.touch, float(o.q[5]), float(o.qd[5])))
        w1 = time.perf_counter()
        on = self.tau_fly >= self.fc.tau_engage
        self.eng, self.low = (self.eng + 1, 0) if on else (0, self.low + 1)
        if mode in ("fly", "search"):
            if self._touch_t is None and max(o.touch[:2]) > 0.05:
                self._touch_t = o.t
            if self._touch_t is not None and self._close_t is None and self.tau_fly > 0.05:
                self._close_t = o.t
                self.react.append(round((o.t - self._touch_t) * 1e3, 1))
        if mode == "fly":
            tau, src = self.tau_fly, self.src
        elif mode == "search":
            tau, src = self.fc.tau_search, "classical:search"
        else:
            g.mode, src = "open", "classical:open"
            tau = g.cfg.tau_open if o.q[5] < g.cfg.q_open else \
                g.cfg.tau_close if mode == "preshape" and o.q[5] > g.cfg.q_open + 0.05 else 0.0
        cmd = Command(o.t, {j: float(tgt[j]) for j in range(5)}, tau,
                      {0: self.pan_src, **{j: "classical:reach" for j in range(1, 5)}, "jaw": src})
        q_t, tau_t, flags, per = self.safety.step(cmd, o.q, o.t, 0.0)
        if flags:
            raise Fail("safety_" + flags[0], str(flags))
        for f in {x for v in per.values() for x in v}:
            self.stats["flags"][f] = self.stats["flags"].get(f, 0) + 1
        w2 = time.perf_counter()
        self.lat.append((*self.eye.t, *getattr(self.driver, "t", (0, w1 - w0, 0)), w2 - w1))
        self.obs = self.w.step(q_t, tau_t)


# ---------------------------------------------------------------- uruchamianie -------------------------------------
CFG = replace(oh.OHCfg(), home=Q_SURVEY)


def make(arm, fc=sm.FlyCfg(trigger="search"), vc=VisCfg()):
    """Zwraca (fabryka kontrolera, sterownik sieci albo None, kalibracja)."""
    cal = dict(slope_p=calibrate_p())
    jaw, pan, _ = ARMS[arm]
    if arm == "A_cam":
        return (lambda w, cfg: ClassicCam(w, cfg, vc, cal["slope_p"])), None, cal
    if arm == "B_cam":
        drv = sm.LegJaw(fc)
    else:
        drv = VisJaw(fc, touch=arm != "D_vis", proprio=arm.startswith("F_"))
        cal["slope_snn"], cal["dna02_diff_hz"] = calibrate(drv)
        if not cal["slope_snn"] > 0:
            raise SystemExit(f"kalibracja skrętu: nachylenie {cal['slope_snn']} ≤ 0 (znak ustalony z góry) — odmowa")
        drv.slope = cal["slope_snn"]
    return (lambda w, cfg: VisGrip(w, cfg, drv, jaw, fc, vc, pan, cal["slope_p"], arm != "E_blind_grasp")), drv, cal


def run_series(items, seed, factory, drv, record=None):
    made, orig = [], oh.Controller
    if isinstance(drv, VisJaw):
        drv.reset(SEED_NOISE + seed)
    elif drv is not None:
        drv.reset()
    oh.Controller = lambda w, cfg: made.append(factory(w, cfg)) or made[0]
    try:
        r = oh.run(items, seed, cfg=CFG, record=record)
    finally:
        oh.Controller = orig
        for x in made:
            x.eye.close()
    c = made[0]
    r["vision"] = c.vlog
    r["lat"] = np.array(c.lat) if getattr(c, "lat", None) else np.c_[np.array(c.clat), np.zeros((len(c.clat), 4))]
    r["react_ms"] = getattr(c, "react", [])
    return r


def perr(v):
    """Błąd perceptu kamery względem wyroczni (prawda symulatora) — liczony PO fakcie, tylko do raportu."""
    c, t = v["cam"], v["truth"]
    dy = (c["yaw"] - t["yaw"] + math.pi / 2) % math.pi - math.pi / 2
    return dict(pos_mm=1e3 * math.hypot(c["x"] - t["x"], c["y"] - t["y"]), w_mm=1e3 * (c["w"] - t["w"]), l_mm=1e3 * (c["l"] - t["l"]),
                h_mm=1e3 * (c["h_est"] - t["h"]), yaw_deg=math.degrees(dy) if t["l"] - t["w"] > 0.005 else None)


def pct(a):
    a = np.asarray(a, float)
    return dict(median=round(float(np.median(a)), 4), p95=round(float(np.percentile(a, 95)), 4),
                p99=round(float(np.percentile(a, 99)), 4), max=round(float(a.max()), 4), n=int(len(a))) if len(a) else None


def wilson(k, n, z=1.96):
    if not n:
        return None
    p, d = k / n, 1 + z * z / n
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round((p + z * z / (2 * n)) / d - h, 3), round((p + z * z / (2 * n)) / d + h, 3)]


def code_vision():
    import hashlib
    return {f: hashlib.sha256(open(os.path.join(HERE, f), "rb").read()).hexdigest()
            for f in ("vision_manipulation.py", "sensory_manipulation.py", "visual_path.py", "leg_circuit.py", "fly_jaw.py",
                      "encoder.py", "decoder.py", "alif.py", "alif_sparse.py", "snn_interface.py")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("bench", "series"))
    ap.add_argument("--arm", required=True, choices=sorted(ARMS))
    ap.add_argument("--set", default="base", choices=sorted(oh.SETS))
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--poses", type=int, default=3)
    ap.add_argument("--seed", type=int, default=100, help="bench: ziarno położeń (100 = te same co wcześniejsze ramiona)")
    ap.add_argument("--perm", type=int, nargs="+", default=[1], help="series: ziarna permutacji")
    ap.add_argument("--n", type=int, default=9)
    ap.add_argument("--record")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", default=OUT, help="katalog wyników (prace rozwojowe: katalog tymczasowy)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, a.tag + ".json")
    if os.path.exists(path) or os.path.exists(path.replace(".json", ".INCOMPLETE.json")):
        sys.exit(f"istnieje już wynik o tagu {a.tag!r} w {a.out} — wybierz inny --tag")
    fc, vc = sm.FlyCfg(trigger="search"), VisCfg()
    w0, c0 = time.perf_counter(), time.process_time()
    factory, drv, cal = make(a.arm, fc, vc)
    items, runs, lat, react = oh.SETS[a.set], [], [], []
    if a.mode == "bench":
        jobs = [([it], a.seed * 1000 + items.index(it) * 10 + k) for it in items if not a.only or "/".join(it) in a.only
                for k in range(a.poses)]
    else:
        jobs = []
        for ps in a.perm:
            order = [items[i] for i in np.random.default_rng(ps).permutation(len(items))]
            jobs += [(order[j:j + a.n], ps * 100 + j // a.n) for j in range(0, len(order), a.n)]
    for its, seed in jobs:
        r = run_series(its, seed, factory, drv, record=a.record if not runs else None)
        lat.append(r.pop("lat"))
        react += r["react_ms"]
        runs.append(r)
        for o in r["objects"]:
            print(f"{o['shape'] + '/' + o['material']:22s} {seed}: {'OK ' if o['success'] else '-- '}"
                  f"{''.join('GLTRP'[j] if o['truth'][s] else '.' for j, s in enumerate(oh.STAGES))} "
                  f"próby {o['attempts']} {[x['reason'] for x in o['attempt_log'] if not x['ok']]} → {o['final']}", flush=True)
    L = np.vstack(lat) * 1e3
    wall, cpu = time.perf_counter() - w0, time.process_time() - c0
    summ = oh.summarize(runs)
    s = summ["success"]
    s["ci95_wilson"] = wilson(s["k"], s["n"])
    summ["compute_ms_per_tick"] = dict(camera_render=pct(L[:, 0]), retina_encoder=pct(L[:, 1]), sensory_currents=pct(L[:, 2]),
                                       snn_10_steps=pct(L[:, 3]), decoding=pct(L[:, 4]), safety_and_command=pct(L[:, 5]),
                                       camera_to_command_total=pct(L.sum(1)))
    summ["contact_to_close_command_sim_ms"] = pct(react)
    V = [v for r in runs for v in r["vision"]]
    E = [perr(v) for v in V]
    summ["vision"] = dict(percepts=len(V), converged=sum(v["converged"] for v in V), t_orient_s=pct([v["t_orient"] for v in V]),
                          **{k: pct([abs(e[k]) for e in E if e[k] is not None]) for k in ("pos_mm", "w_mm", "l_mm", "h_mm", "yaw_deg")},
                          bias_mm={k: round(float(np.mean([e[k] for e in E])), 2) for k in ("w_mm", "l_mm", "h_mm")} if E else None)
    summ["process"] = dict(wall_s=round(wall, 1), cpu_s=round(cpu, 1), cpu_load=round(cpu / wall, 2),
                           max_rss_MB=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20, 1),
                           ticks=int(len(L)), sim_tick_ms=10.0, gpu="tylko render kamery (OpenGL)")
    complete = all(r["complete"] for r in runs)
    out = dict(tag=a.tag, mode=a.mode, arm=a.arm, jaw_source=ARMS[a.arm][0], pan_source=ARMS[a.arm][1], arm_desc=ARMS[a.arm][2],
               complete=complete, argv=sys.argv, fly_cfg=asdict(fc), vis_cfg=asdict(vc), q_survey=Q_SURVEY, calibration=cal,
               encoder=asdict(ENC), steer=asdict(STEER), network=getattr(drv, "sizes", None), cfg=asdict(CFG),
               scene=asdict(oh.Scene()), crit=asdict(oh.Crit()), code=oh.code_state(), code_vision=code_vision(), python=sys.version.split()[0],
               summary=summ, runs=runs)
    path = path if complete or a.mode == "bench" else path.replace(".json", ".INCOMPLETE.json")
    with open(path, "x") as f:
        json.dump(out, f, indent=1, default=float)
    print(f"\n{a.arm}: w pudełku {s['k']}/{s['n']} (95 % CI {s['ci95_wilson']}); percepcja: {summ['vision']}")
    print("czas obliczeń [ms/takt]:", {k: (v or {}).get("median") for k, v in summ["compute_ms_per_tick"].items()})
    print("zapisano", path)


if __name__ == "__main__":
    main()
