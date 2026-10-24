"""Agent bio2: pętla 100 Hz kamera → siatkówka → mózg (CX, DN) + czucie → rdzeń brzuszny → serwa SO-101.

Kierunek celu względem osi bazy (nie kamery): kamera siedzi na chwytaku ~25 cm od osi obrotu, więc kierunek do
bliskiej piłeczki zmienia się przy obrocie bazy ~2,3× szybciej niż kąt bazy — kompensacja PEN „−prędkość bazy”
była przez to za słaba, a pętla wzrokowa za silna. Promień z kamery (środek plamki na siatkówce) przecinam
z płaszczyzną stołu (piłeczka leży na stole, robot zna swoją kinematykę) → azymut z osi bazy względem paszczy.
Pamięć obiektu (wariant `memory`):
  "pred"  — widoczny cel ustawia wzgórze EPG (wejście wzrokowe); PEN dostaje prędkość kątową celu względem
            ramienia = (ostatnia zmierzona prędkość celu w świecie) − (prędkość bazy z propriocepcji serwa ID 1).
            Podczas zasłonięcia wzgórze przesuwa się z przewidywanym celem. Przewidywanie ruchu celu to założenie
            MODELOWE (w kompleksie centralnym muchy nie jest opisane).
  "static"— PEN dostaje tylko −prędkość bazy: wzgórze pamięta kierunek, w którym cel zniknął (w świecie).
  "none"  — bez pamięci: gdy celu nie widać, baza stoi.
Neuromodulacja (OA-VUM, model): stan „polowanie” (wysokie wzmocnienie ruchu) włącza się po ACQ_N kolejnych spójnych
wykryciach celu i trwa HUNT_HOLD po jego ostatnim widzeniu; w spoczynku DNa02/DNa01 nie poruszają bazą (bez tego
spontaniczne wzgórze EPG z szumu obracało ramię, zanim cel w ogóle się pojawił).
Uwaga odgórna (model): w polowaniu wykrycie celu liczy się tylko w ±GATE od kierunku wzgórza EPG — inaczej krawędzie
bliskiej przesłony, przesuwające się przy własnym obrocie (paralaksa), były brane za cel.
Ucieczka: spike DNp01 (Giant Fiber, wszystko-albo-nic) uruchamia program „wyrzut w tył” (bark + łokieć,
maksymalna prędkość serw), jak skok muchy. Dotyk szczęk wstrzymuje skręt bazy (v4).
"""
import mujoco
import numpy as np

import scene2
from brain import Brain
from vision import Vision
from vnc import vnc_controller

SERVO_SPEED = 4.7          # rad/s (STS3215, ok.)
WINDUP = 0.02              # rad
# --- nasze stałe ---
G_TURN = 2.5               # 1/s: ω bazy = G_TURN · kąt odczytany z DN (mucha: 2–3,3 (°/s)/°)
TAU_DNA02, TAU_DNA01 = 0.10, 0.40   # s, filtry odczytu: DNa02 szybki, DNa01 wolny (precyzyjny)
TV_WIN, TV_MIN = 0.6, 0.3  # s: prędkość celu = nachylenie regresji kierunku (świat) z ostatnich 0,6 s widzenia, min. 0,3 s
TV_MAX = 1.0               # rad/s, ograniczenie estymaty
# (różniczkowanie klatka po klatce z filtrem 0,25 s: szum kierunku ±5° → SD estymaty ~1 rad/s, prędkość piłeczki ~0,23)
ESCAPE_T = 0.6             # s, czas programu ucieczki
F_SECURE = 0.3             # N, warunek pewnego chwytu (obie szczęki przez 100 ms) → uniesienie
HUNT_HOLD = 3.0            # s, czas stanu „polowanie” po ostatnim widzeniu celu (OA-VUM)
ACQ_N, ACQ_TOL = 5, np.radians(8)   # start polowania: 5 kolejnych spójnych wykryć (rozrzut < 8°)
GATE = np.radians(25)      # w polowaniu wykrycie liczy się tylko blisko kierunku wzgórza EPG (uwaga odgórna, model)
W_MAX = 1.0                # rad/s, maks. prędkość obrotu bazy z DNa02/DNa01
W_SELF = 0.05             # rad/s, powyżej: obrót własny → wejście HS wygaszone (kopia eferentna)
LOCK = np.radians(20)      # wzgórze w ±20° od celu → start ruchu bazy


class Agent:
    def __init__(self, m, d, seed=0, memory="pred", efference=True, q_catch=None, brain=None, calib=None, vnc=None):
        self.m, self.d = m, d
        self.brain = brain or Brain(seed=seed)
        if calib is not None:
            self.brain.calib = calib
        elif self.brain.calib is None:
            self.brain.calibrate_ring()
        if self.brain.steer is None:
            self.brain.calibrate_steer()
        self.vnc = vnc if vnc is not None else vnc_controller(seed=seed)
        self.vision = Vision(scene2.CAM_FOVY, scene2.CAM_W / scene2.CAM_H, efference=efference)
        self.r, self.opt = scene2.eye_renderer(m)
        self.memory = memory
        self.q_catch = q_catch
        self.q_lift = q_catch.copy()
        self.q_lift[1] -= 0.25
        self.q_escape = q_catch.copy()
        self.q_escape[1] -= 1.1                       # bark w górę/w tył
        self.q_escape[2] += 0.4                       # łokieć
        self.reset()

    def reset(self):
        self.brain.reset()
        self.vnc.reset()
        self.vision.reset()
        self.q_pan_prev = None
        self.tv = 0.0                                 # prędkość kątowa celu w świecie [rad/s]
        self.tw_hist = []                             # (t, kierunek celu w świecie) z klatek z widzeniem
        self.seen = False
        self.hunt_until = -1.0
        self.acq = []
        self.locked = False
        self.dn_f = np.zeros(2)                       # przefiltrowane różnice L−P: DNa02, DNa01
        self.escape_t = None
        self.secure, self.lifting = 0, False
        self.bump_prev = 0.0
        self.log = dict(t=[], target=[], bump=[], skup=[], omega=[], loom=[], dnp01=[], tau=[], wedges=[], seen=[])

    def close(self):
        self.r.close()

    def _aim_az(self):
        """Azymut paszczy (punkt „aim” chwytaka) z osi bazy [rad] — z kinematyki."""
        p = self.d.site("aim").xpos
        return float(np.arctan2(p[1], p[0]))

    def step(self):
        m, d = self.m, self.d
        q_pan, w_pan = d.qpos[0], d.qvel[0]
        dpsi = 0.0 if self.q_pan_prev is None else -(q_pan - self.q_pan_prev)   # + w lewo
        self.q_pan_prev = q_pan
        self.r.update_scene(d, camera="eye", scene_option=self.opt)
        v = self.vision.step(self.r.render(), dpsi=dpsi)
        w_base = -w_pan
        touch = d.sensordata[:3].copy()
        contact = touch.max() > F_SECURE

        # --- kierunek celu z osi bazy: promień kamery ∩ płaszczyzna stołu (z = promień piłeczki) ---
        R, c0, aim = d.cam("eye").xmat.reshape(3, 3), d.cam("eye").xpos, self._aim_az()
        bearings = []
        for c in v["cands"]:
            rw = R @ c["ray"]
            if rw[2] < -1e-3:
                p = c0 + (scene2.scene.BALL_R - c0[2]) / rw[2] * rw
                bearings.append(float(np.angle(np.exp(1j * (np.arctan2(p[1], p[0]) - aim)))))
        hunting = d.time < self.hunt_until
        # uwaga odgórna (model): w polowaniu wybierz kandydata najbliższego kierunkowi wzgórza EPG, poza tym najsilniejszego
        if hunting and bearings:
            cue = min(bearings, key=lambda x: abs(np.angle(np.exp(1j * (x - self.bump_prev)))))
        else:
            cue = bearings[0] if bearings else None
        target_base = cue
        if cue is not None and not hunting:
            self.acq = (self.acq + [cue])[-ACQ_N:]
            if len(self.acq) == ACQ_N and np.ptp(self.acq) < ACQ_TOL:
                self.hunt_until = d.time + HUNT_HOLD
            else:
                cue = None if len(self.acq) < ACQ_N else cue
        elif cue is not None and abs(np.angle(np.exp(1j * (cue - self.bump_prev)))) > GATE:
            cue = None                                   # poza oczekiwaniem pierścienia
        if cue is None and not hunting:
            self.acq = [] if target_base is None else self.acq
        self.seen = cue is not None
        if self.seen:
            self.hunt_until = d.time + HUNT_HOLD
            th_w = cue + self._aim_az()
            self.tw_hist = [h for h in self.tw_hist if d.time - h[0] < TV_WIN] + [(d.time, th_w)]
            t_h, a_h = np.array(self.tw_hist).T
            if t_h[-1] - t_h[0] >= TV_MIN:
                self.tv = float(np.clip(np.polyfit(t_h, np.unwrap(a_h), 1)[0], -TV_MAX, TV_MAX))
        rel = (self.tv if self.memory == "pred" else 0.0) - w_base
        hunting = d.time < self.hunt_until
        # HS: kopia eferentna przy obrocie własnym — u muchy sygnał ruchowy kasuje odpowiedź HS podczas skrętów
        # dobrowolnych (Kim i in. 2015, 2017). Odejmowanie przewidywanego przepływu nie wystarcza (paralaksa bliskiej
        # przesłony przy kamerze 25 cm od osi) — resztka przez HS→DNa02 dawała skręty o złym znaku do 3–4 rad/s.
        flow_in = 0.0 if abs(w_base) > W_SELF else v["flow"]
        spk = self.brain.step10(cue=cue, u=self.brain.u_for(rel), loom=v["loom"], flow=flow_in,
                                rest=not hunting)
        g = self.brain.groups
        b_ang, b_skup, _ = self.brain.bump(spk)
        self.bump_prev = b_ang

        # --- skręt bazy: DNa02 (szybki filtr) + DNa01 (wolny), przeliczone na kąt kalibracją trymu i nachylenia ---
        rt = self.brain.rate
        raw = np.array([rt[g["DNa02_L"]].mean() - rt[g["DNa02_R"]].mean(), rt[g["DNa01_L"]].mean() - rt[g["DNa01_R"]].mean()])
        a = np.exp(-0.01 / np.array([TAU_DNA02, TAU_DNA01]))
        self.dn_f = a * self.dn_f + (1 - a) * raw
        st = self.brain.steer
        off, sl = (st["offset"], st["slope"]) if self.seen else (st["offset_mem"], st["slope_mem"])
        omega = G_TURN * float(np.mean((self.dn_f - off) / sl))
        if hunting and not self.locked and cue is not None and abs(np.angle(np.exp(1j * (cue - b_ang)))) < LOCK:
            self.locked = True                           # wzgórze zatrzaśnięte na celu → można ruszać bazą
        if not hunting:
            self.locked = False
        if not (hunting and self.locked) or (self.memory == "none" and not self.seen) or contact or self.escape_t is not None:
            omega = 0.0
        w = np.clip(omega, -W_MAX, W_MAX)
        c = np.clip(d.ctrl[0] - w * 0.01, d.qpos[0] - WINDUP, d.qpos[0] + WINDUP)
        d.ctrl[0] = np.clip(c, *m.actuator_ctrlrange[0])

        # --- ucieczka (Giant Fiber) ---
        gf = spk[:, np.concatenate([g["DNp01_L"], g["DNp01_R"]])].any()
        if gf and self.escape_t is None:
            self.escape_t = d.time
        step = SERVO_SPEED * 0.01
        if self.escape_t is not None:
            for j in (1, 2):
                d.ctrl[j] += np.clip(self.q_escape[j] - d.ctrl[j], -step, step)

        # --- chwyt (rdzeń brzuszny) ---
        _, tau, _ = self.vnc.control_step(None, touch, active=hunting, jaw_vel=d.qvel[5], jaw_q=d.qpos[5])
        d.ctrl[5] = np.clip(-tau / scene2.scene.GRIP_TORQUE, -1, 1)
        self.secure = self.secure + 1 if min(touch[0], touch[1]) > F_SECURE else 0
        if self.secure >= 10:
            self.lifting = True
        if self.lifting and self.escape_t is None:
            d.ctrl[1] += np.clip(self.q_lift[1] - d.ctrl[1], -step, step)

        L = self.log
        L["t"].append(d.time)
        L["target"].append(np.nan if cue is None else cue)
        L["bump"].append(b_ang)
        L["skup"].append(b_skup)
        L["omega"].append(omega)
        L["loom"].append(max(v["loom"]))
        L["dnp01"].append(bool(gf))
        L["tau"].append(tau)
        L["wedges"].append(self.brain.wedges(spk))
        L["seen"].append(self.seen)
        L.setdefault("strength", []).append(v["target_strength"])
        L.setdefault("n_blob", []).append(v["n_blob"])
        return v
