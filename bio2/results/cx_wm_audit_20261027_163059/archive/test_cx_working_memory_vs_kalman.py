#!/usr/bin/env python3
"""
bio2/test_cx_working_memory_vs_kalman.py

Eksperyment 2: Pamięć robocza kompleksu centralnego (CX) vs Filtr Kalmana + PD.
Porównanie zdolności podtrzymania azymutu celu podczas okluzji wzrokowej:
  1. BIO-Static: czysty model biologiczny (kompensacja ruchu własnego przez PEN, bez ekstrapolacji prędkości celu).
  2. BIO-Hybrid: wariant produkcyjny agent.py (ekstrapolacja prędkości celu przez zewnętrzny np.polyfit).
  3. BIO-NoSelf: ablacja kompensacji ruchu własnego (wytrymowany spoczynek u_for(0.0), brak wejścia w_base).
  4. BIO-Shuffle: wariant kontrolny (Within-Projection Weight Shuffle — permutacja wag w obrębie projekcji).
  5. LastObs-PD: klasyczny punkt odniesienia dla BIO-Static (Zero-Order Hold na pozycji w świecie + PD).
  6. Kalman-PD: optymalny estymator liniowo-kwadratowy dla BIO-Hybrid (filtr Kalmana 2D w świecie + PD).

ZASADY METODOLOGICZNE:
  - Izolacja od plików produkcyjnych (plik samodzielny, read-only wobec reszty repozytorium).
  - Determinizm numeryczny przy zadanym generatorze rng(seed).
  - Kontrolowane maskowanie obserwacji (Software Blanking) eliminujące artefakty krawędzi przesłony.
  - Wspólny interfejs obserwacji i ścisły zakaz wycieku informacji o celu w czasie okluzji.
  - Formalny test niegorszości (Non-Inferiority Testing) z marginesem inżynierskim delta_NI = 3.0 deg.
"""

import argparse
import json
import math
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

import mujoco
import numpy as np
import scipy.stats as st

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import scene2
from brain import Brain, B
from snn import ConnectomeSNN
from vision import Vision

# -----------------------------------------------------------------------------
# Konfiguracja globalna protokołu
# -----------------------------------------------------------------------------
CFG = dict(
    w_max=0.6,               # rad/s, maks. prędkość bazy (agent.py: W_MAX)
    windup=0.02,             # rad, strefa martwa przeciwwzbudzeniowa (agent.py: WINDUP)
    dt=0.01,                 # s, krok sterowania 100 Hz (10 ms)
    delta_ni_deg=3.0,        # stopnie, inżynierski margines niegorszości (geometria szczęk)
    alpha_signif=0.05,       # poziom istotności statystycznej
    t_occ_primary=1.0,       # s, główny punkt końcowy (Primary Endpoint)
    t_occ_list=(0.5, 1.0, 1.5, 2.0), # s, badane czasy okluzji
    seeds_tune=tuple(range(100, 130)), # N = 30 ziaren strojeniowych / pilotażowych
    seeds_test=tuple(range(40)),       # N = 40 ziaren testowych potwierdzających
    t_mask_start=0.50,       # s, faza akwizycji wzrokowej przed okluzją
    t_trial_total=3.50,      # s, maksymalny czas trwania próby
)

CX_GROUPS = ["EPG", "PEN_a_L", "PEN_a_R", "PEN_b_L", "PEN_b_R", "Delta7", "PFL3_L", "PFL3_R"]
SLOPE_DEGENERATE_THRESH = 1e-6
VALID_VARIANTS = ("BIO-Static", "BIO-Hybrid", "BIO-NoSelf", "BIO-Shuffle", "LastObs-PD", "Kalman-PD")
DIAGNOSTIC_VARIANTS = ("BIO-Shuffle-DiagFallback",)
ALL_VARIANTS = VALID_VARIANTS + DIAGNOSTIC_VARIANTS


# -----------------------------------------------------------------------------
# Narzędzia matematyczne i obsługa kątów
# -----------------------------------------------------------------------------
def wrap_angle(theta: float) -> float:
    """Zawija kąt do przedziału [-pi, +pi)."""
    return float((theta + np.pi) % (2.0 * np.pi) - np.pi)


def angle_diff(a: float, b: float) -> float:
    """Oblicza najkrótszą różnicę kątową wrap(a - b) w [-pi, +pi)."""
    return wrap_angle(a - b)


def check_calibration_slope(sl: Optional[np.ndarray], thresh: float = SLOPE_DEGENERATE_THRESH) -> Tuple[bool, str]:
    """
    Weryfikuje poprawność nachylenia kalibracji sterowania DNa (widzenie / pamięć).
    Zwraca: (is_valid, reason)
    """
    if sl is None:
        return False, "Brak wektora nachylenia (None)"
    arr = np.asarray(sl, dtype=float)
    if not np.all(np.isfinite(arr)):
        return False, f"Nieskończone lub NaN nachylenie dekodera: {arr}"
    if np.any(np.abs(arr) < thresh):
        return False, f"Zdegenerowane podprogowe nachylenie (|slope| < {thresh}): {arr}"
    return True, ""


# -----------------------------------------------------------------------------
# Warstwa wykonawcza serwomechanizmu SO-101
# -----------------------------------------------------------------------------
def apply_base_velocity(d, m, omega_cmd: float, dt: float = CFG["dt"]) -> float:
    """
    Aplikuje komendę prędkości kątowej bazy do siłownika pozycji STS3215.
    Zgodnie z mechatroniką SO-101 (agent.py:169-171):
      - omega_cmd > 0 oznacza skręt w lewo (wzrost azymutu w świecie);
      - staw 0 qpos[0] maleje przy skręcie w lewo, dlatego: d.ctrl[0] -= w * dt.
    Zwraca rzeczywistą skorygowaną pozycję zadaną d.ctrl[0].
    """
    w = np.clip(omega_cmd, -CFG["w_max"], CFG["w_max"])
    c = np.clip(d.ctrl[0] - w * dt, d.qpos[0] - CFG["windup"], d.qpos[0] + CFG["windup"])
    d.ctrl[0] = np.clip(c, *m.actuator_ctrlrange[0])
    return float(d.ctrl[0])


def get_aim_azimuth(d) -> float:
    """Azymut paszczy (site 'aim' chwytaka) w układzie świata z osi bazy (0, 0)."""
    p = d.site("aim").xpos
    return float(np.arctan2(p[1], p[0]))


def get_ball_azimuth(d) -> float:
    """Azymut środka kulki w układzie świata z osi bazy (0, 0)."""
    b = d.body("ball").xpos
    return float(np.arctan2(b[1], b[0]))


# -----------------------------------------------------------------------------
# Klasyczny estymator: Filtr Kalmana (w układzie świata)
# -----------------------------------------------------------------------------
class LinearKalmanTargetEstimator:
    """
    Dyskretny filtr Kalmana estymujący stan celu w układzie świata:
      x = [theta_w, omega_w]^T
    Model ruchu: stała prędkość kątowa (Constant Angular Velocity).
    W fazie okluzji wykonuje wyłącznie krok predykcji.
    """
    def __init__(self, q_w: float = 0.5, r_v: float = 0.005, dt: float = CFG["dt"]):
        self.dt = dt
        self.F = np.array([[1.0, dt],
                           [0.0, 1.0]], dtype=float)
        self.H = np.array([[1.0, 0.0]], dtype=float)
        dt3 = (dt ** 3) / 3.0
        dt2 = (dt ** 2) / 2.0
        self.Q = np.array([[dt3, dt2],
                           [dt2, dt]], dtype=float) * q_w
        self.R = np.array([[r_v]], dtype=float)
        self.x = np.zeros(2, dtype=float)
        self.P = np.eye(2, dtype=float) * 1.0
        self.initialized = False

    def reset(self, theta_init: float = 0.0, omega_init: float = 0.0):
        self.x = np.array([wrap_angle(theta_init), omega_init], dtype=float)
        self.P = np.diag([0.05, 0.5]).astype(float)
        self.initialized = True

    def predict(self):
        """Krok predykcji a priori (w trakcie widzenia oraz w okluzji)."""
        if not self.initialized:
            return
        self.x = self.F @ self.x
        self.x[0] = wrap_angle(self.x[0])
        self.P = self.F @ self.P @ self.F.T + self.Q

    def update(self, z_theta_w: float):
        """Krok aktualizacji pomiarowej a posteriori (tylko gdy cel widoczny)."""
        if not self.initialized:
            self.reset(theta_init=z_theta_w)
            return
        y = angle_diff(z_theta_w, self.x[0])
        S = float((self.H @ self.P @ self.H.T + self.R)[0, 0])
        K = (self.P @ self.H.T) / S
        self.x = self.x + K.flatten() * y
        self.x[0] = wrap_angle(self.x[0])
        I_KH = np.eye(2) - K @ self.H
        self.P = I_KH @ self.P

    @property
    def theta_world(self) -> float:
        return float(self.x[0])

    @property
    def omega_world(self) -> float:
        return float(self.x[1])


# -----------------------------------------------------------------------------
# Kontrolery śledzenia (Wspólny interfejs)
# -----------------------------------------------------------------------------
class LastObsPDController:
    """
    Baseline naiwny (Zero-Order Hold):
    Zapamiętuje ostatnio widzianą pozycję celu w świecie theta_w*.
    Podczas okluzji kompensuje ruch własny bazy: theta_rel = theta_w* - theta_mouth_w.
    """
    def __init__(self, kp: float = 2.5, kd: float = 0.15):
        self.kp = kp
        self.kd = kd
        self.theta_w_last: Optional[float] = None

    def reset(self):
        self.theta_w_last = None

    def step(self, cue_rel: Optional[float], mouth_az: float, w_base: float) -> float:
        if cue_rel is not None:
            self.theta_w_last = wrap_angle(cue_rel + mouth_az)
            target_rel = cue_rel
        else:
            if self.theta_w_last is None:
                return 0.0
            target_rel = angle_diff(self.theta_w_last, mouth_az)
        omega_cmd = self.kp * target_rel - self.kd * w_base
        return float(np.clip(omega_cmd, -CFG["w_max"], CFG["w_max"]))


class KalmanPDController:
    """
    Baseline klasyczny:
    Filtr Kalmana estymuje kąt i prędkość celu w świecie.
    Regulator PD steruje bazą do estymowanego azymutu z kompensacją prędkości celu.
    """
    def __init__(self, kf: LinearKalmanTargetEstimator, kp: float = 2.8, kd: float = 0.12):
        self.kf = kf
        self.kp = kp
        self.kd = kd

    def reset(self):
        self.kf.initialized = False

    def step(self, cue_rel: Optional[float], mouth_az: float, w_base: float) -> float:
        self.kf.predict()
        if cue_rel is not None:
            z_w = wrap_angle(cue_rel + mouth_az)
            self.kf.update(z_w)
        if not self.kf.initialized:
            return 0.0
        target_rel = angle_diff(self.kf.theta_world, mouth_az)
        omega_cmd = self.kp * target_rel + self.kd * (self.kf.omega_world - w_base)
        return float(np.clip(omega_cmd, -CFG["w_max"], CFG["w_max"]))


# -----------------------------------------------------------------------------
# Kontroler BIO (kompleks centralny CX)
# -----------------------------------------------------------------------------
def make_within_projection_shuffled_brain(seed: int) -> Brain:
    """
    Tworzy model Brain z kontrolą Within-Projection Weight Shuffle:
    W obrębie każdej pary projekcji CX (ga -> gb) permutuje losowo wartości niezerowych wag.
    Zachowuje:
      - multizbiór wag wewnątrz każdej projekcji (osobno pobudzających i hamujących);
      - całkowitą masę synaptyczną per projekcja;
      - architekturę połączeń między typami komórek.
    Niszczy:
      - zależność wag od różnicy faz delta_theta (ring profile), eliminując atraktor.
    """
    b = Brain(seed=seed)
    rng = np.random.default_rng(seed)
    g = b.groups
    W_cx = b.net.W.copy()

    for ga in CX_GROUPS:
        for gb in CX_GROUPS:
            pre, post = g[ga], g[gb]
            sub = W_cx[np.ix_(post, pre)].copy()
            for sign in (1.0, -1.0):
                mask = (sign * sub) > 0.0
                if mask.any():
                    sub[mask] = rng.permutation(sub[mask])
            W_cx[np.ix_(post, pre)] = sub

    b.net.W = W_cx
    b.reset()
    b.calibrate_ring()
    b.calibrate_steer()
    return b


class BioAdaptiveController:
    """
    Kontroler bioniczny integrujący SNN (Brain) z serwomechanizmem bazy SO-101.
    Obsługuje 4 warianty:
      - 'static': PEN otrzymuje u_for(-w_base), prędkość celu = 0.
      - 'hybrid': PEN otrzymuje u_for(tv_poly - w_base), tv_poly z np.polyfit.
      - 'noself': PEN otrzymuje u_for(0.0) (brak kompensacji ruchu bazy, trim spoczynkowy).
      - 'shuffle': Within-Projection Weight Shuffle.
    """
    def __init__(
        self,
        mode: str = "static",
        brain: Optional[Brain] = None,
        seed: int = 0,
        allow_fallback: bool = False,
    ):
        assert mode in ("static", "hybrid", "noself", "shuffle"), f"Nieznany tryb BIO: {mode}"
        self.mode = mode
        self.allow_fallback = allow_fallback
        self.fallback_used = False

        if mode == "shuffle":
            self.brain = brain or make_within_projection_shuffled_brain(seed)
        else:
            self.brain = brain or Brain(seed=seed)
            if self.brain.calib is None:
                self.brain.calibrate_ring()
            if self.brain.steer is None:
                self.brain.calibrate_steer()
        self.seed = seed

        # Weryfikacja jakości kalibracji sterowania DNa
        self.calibration_status = "VALID"
        self.calibration_details = ""
        st_cal = self.brain.steer
        if st_cal is not None:
            mem_valid, mem_reason = check_calibration_slope(st_cal.get("slope_mem"))
            vis_valid, vis_reason = check_calibration_slope(st_cal.get("slope"))
            if not mem_valid:
                self.calibration_status = "DEGENERATE_CALIBRATION"
                self.calibration_details = f"Zdegenerowana kalibracja pamięci roboczej: {mem_reason}"
            elif not vis_valid:
                self.calibration_status = "DEGENERATE_CALIBRATION"
                self.calibration_details = f"Zdegenerowana kalibracja widzenia: {vis_reason}"

        self.reset()

    def reset(self):
        self.brain.reset()
        self.tv = 0.0
        self.tw_hist: List[Tuple[float, float]] = []
        self.dn_f = np.zeros(2)
        self.bump_prev = 0.0

    def step(self, cue_rel: Optional[float], mouth_az: float, w_base: float, t_sim: float) -> Tuple[float, float, float]:
        """
        Zwraca: (omega_cmd, bump_angle, bump_coherence)
        """
        seen = cue_rel is not None
        if seen:
            th_w = wrap_angle(cue_rel + mouth_az)
            self.tw_hist = [h for h in self.tw_hist if t_sim - h[0] < 0.6] + [(t_sim, th_w)]
            if len(self.tw_hist) >= 5 and (self.tw_hist[-1][0] - self.tw_hist[0][0]) >= 0.3:
                t_arr, a_arr = np.array(self.tw_hist).T
                self.tv = float(np.clip(np.polyfit(t_arr, np.unwrap(a_arr), 1)[0], -1.0, 1.0))

        # Obliczenie sygnału sterującego PEN
        if self.mode == "hybrid":
            rel_omega = (self.tv if seen else self.tv) - w_base
            u_in = self.brain.u_for(rel_omega)
        elif self.mode == "static" or self.mode == "shuffle":
            rel_omega = -w_base
            u_in = self.brain.u_for(rel_omega)
        elif self.mode == "noself":
            u_in = self.brain.u_for(0.0)
        else:
            u_in = 0.0

        spk = self.brain.step10(cue=cue_rel, u=u_in, rest=False)
        b_ang, b_skup, _ = self.brain.bump(spk)
        self.bump_prev = b_ang

        # Odczyt z neuronów zstępujących DNa02 i DNa01
        g = self.brain.groups
        rt = self.brain.rate
        raw_dn = np.array([
            rt[g["DNa02_L"]].mean() - rt[g["DNa02_R"]].mean(),
            rt[g["DNa01_L"]].mean() - rt[g["DNa01_R"]].mean()
        ])
        tau_dn = np.array([0.10, 0.40])
        a_filter = np.exp(-0.01 / tau_dn)
        self.dn_f = a_filter * self.dn_f + (1.0 - a_filter) * raw_dn

        st_cal = self.brain.steer
        is_mem = not seen
        if is_mem:
            off = st_cal["offset_mem"]
            sl = st_cal["slope_mem"]
            mem_valid, _ = check_calibration_slope(sl)
            if not mem_valid:
                if self.allow_fallback:
                    sl = st_cal["slope"]
                    self.fallback_used = True
                else:
                    return 0.0, b_ang, b_skup
        else:
            off = st_cal["offset"]
            sl = st_cal["slope"]
            vis_valid, _ = check_calibration_slope(sl)
            if not vis_valid:
                return 0.0, b_ang, b_skup

        g_turn = 2.5
        omega_cmd = g_turn * float(np.mean((self.dn_f - off) / sl))
        omega_cmd = float(np.clip(omega_cmd, -CFG["w_max"], CFG["w_max"]))
        return omega_cmd, b_ang, b_skup


# -----------------------------------------------------------------------------
# Główna pętla wykonawcza symulacji w MuJoCo (Closed-Loop Trial Runner)
# -----------------------------------------------------------------------------
def run_closedloop_trial(
    variant: str,
    seed: int,
    t_occ: float,
    t_mask_start: float = CFG["t_mask_start"],
    t_total: float = CFG["t_trial_total"],
    dt: float = CFG["dt"],
    calib_brain: Optional[Brain] = None,
) -> Dict:
    """
    Wykonuje jedną, w pełni zdefiniowaną próbę w pętli zamkniętej z modelem SO-101.
    Gwarantuje:
      - Niezależny stan symulatora MuJoCo (świeża instancja scene2.load());
      - Deterministyczne warunki początkowe zależne wyłącznie od seeda;
      - Parkowanie fizycznej przesłony (set_mocap PARK) — okluzja jest realizowana
        przez programowe maskowanie obserwacji (Software Blanking), bez artefaktów krawędzi;
      - Ścisłą ochronę przed wyciekiem prawdy o celu w trakcie okluzji (cue = None);
      - Rejestrację metryk wyłonienia, stabilizacji i energii;
      - Bezpieczne zwalnianie renderera offscreen w bloku try...finally.
    """
    assert variant in ALL_VARIANTS, f"Niepoprawny wariant: {variant} (dostępne: {ALL_VARIANTS})"

    # 1. Inicjalizacja sceny MuJoCo
    rng = np.random.default_rng(seed)
    m, d = scene2.load()
    y0 = float(rng.uniform(0.12, 0.16))
    vy = float(-rng.uniform(0.09, 0.12))
    q_catch, _ = scene2.reset_scene(m, d, ball_y0=y0, ball_vy=vy)

    # Zaparkowanie fizycznej przesłony poza polem widzenia (czyste maskowanie programowe)
    scene2.set_mocap(m, d, "occluder", scene2.PARK)
    mujoco.mj_forward(m, d)

    # 2. Inicjalizacja renderera kamery i siatkówki
    r, opt = scene2.eye_renderer(m)
    vision = Vision(scene2.CAM_FOVY, scene2.CAM_W / scene2.CAM_H, efference=True)

    # 3. Inicjalizacja kontrolera
    if variant == "LastObs-PD":
        ctl = LastObsPDController(kp=2.5, kd=0.15)
    elif variant == "Kalman-PD":
        kf = LinearKalmanTargetEstimator(q_w=0.5, r_v=0.005, dt=dt)
        ctl = KalmanPDController(kf=kf, kp=2.8, kd=0.12)
    elif variant == "BIO-Static":
        ctl = BioAdaptiveController(mode="static", brain=calib_brain, seed=seed)
    elif variant == "BIO-Hybrid":
        ctl = BioAdaptiveController(mode="hybrid", brain=calib_brain, seed=seed)
    elif variant == "BIO-NoSelf":
        ctl = BioAdaptiveController(mode="noself", brain=calib_brain, seed=seed)
    elif variant == "BIO-Shuffle":
        ctl = BioAdaptiveController(mode="shuffle", seed=seed, allow_fallback=False)
    elif variant == "BIO-Shuffle-DiagFallback":
        ctl = BioAdaptiveController(mode="shuffle", seed=seed, allow_fallback=True)
    else:
        raise ValueError(f"Nieobsługiwany wariant: {variant}")

    # 4. Pętla symulacji 100 Hz
    n_steps_total = int(round(t_total / dt))
    t_reappear = t_mask_start + t_occ
    q_pan_prev: Optional[float] = None

    e_reappear_deg: Optional[float] = None
    e_ring_deg: Optional[float] = None
    j_ctrl = 0.0
    reacquire_steps = 0
    t_reacquire: Optional[float] = None
    status = "SUCCESS"
    error_reason = ""
    reappear_recorded = False

    # Detekcja zdegenerowanej kalibracji na poziomie kontrolera
    if variant.startswith("BIO-") and hasattr(ctl, "calibration_status"):
        if ctl.calibration_status == "DEGENERATE_CALIBRATION":
            status = "DEGENERATE_CALIBRATION"
            error_reason = ctl.calibration_details

    try:
        for k in range(n_steps_total):
            t_sim = d.time
            q_pan, w_pan = float(d.qpos[0]), float(d.qvel[0])
            dpsi = 0.0 if q_pan_prev is None else -(q_pan - q_pan_prev)
            q_pan_prev = q_pan
            w_base = -w_pan

            # A. Krok percepcji wzrokowej
            r.update_scene(d, camera="eye", scene_option=opt)
            frame = r.render()
            v_out = vision.step(frame, dpsi=dpsi)

            # Ekstrakcja kandydata na cel z promienia kamery przecinającego stół
            R_cam = d.cam("eye").xmat.reshape(3, 3)
            c0 = d.cam("eye").xpos
            aim_az = get_aim_azimuth(d)
            ball_az = get_ball_azimuth(d)
            true_rel_az = angle_diff(ball_az, aim_az)

            bearings = []
            for c in v_out.get("cands", []):
                rw = R_cam @ c["ray"]
                if rw[2] < -1e-3:
                    p = c0 + (scene2.scene.BALL_R - c0[2]) / rw[2] * rw
                    cand_az = float(np.arctan2(p[1], p[0]))
                    bearings.append(float(angle_diff(cand_az, aim_az)))
            detected_cue = bearings[0] if bearings else None

            # B. Programowe maskowanie sygnału w oknie okluzji [t_mask_start, t_reappear)
            is_occluded = (t_sim >= t_mask_start) and (t_sim < t_reappear)
            cue_rel = None if is_occluded else detected_cue

            # C. Krok kontrolera
            b_ang, b_skup = 0.0, 0.0
            if variant.startswith("BIO-"):
                omega_cmd, b_ang, b_skup = ctl.step(cue_rel, aim_az, w_base, t_sim)
            else:
                omega_cmd = ctl.step(cue_rel, aim_az, w_base)

            # Walidacja stabilności numerycznej
            if not np.isfinite(omega_cmd):
                status = "TECHNICAL_FAILURE"
                error_reason = f"Wykryto NaN/Inf w komendzie sterowania w kroku {k} (t = {t_sim:.3f} s)"
                break

            # Rejestracja energii sterowania w fazie okluzji
            if is_occluded:
                j_ctrl += (omega_cmd ** 2) * dt

            # D. Aplikacja sterowania do siłownika STS3215
            apply_base_velocity(d, m, omega_cmd, dt=dt)

            # E. Krok fizyki MuJoCo (10 kroków po 1 ms = 10 ms pętli)
            for _ in range(10):
                mujoco.mj_step(m, d)

            # F. Rejestracja metryk wyłonienia celu (dokładnie w chwili t_reappear)
            if (t_sim >= t_reappear) and not reappear_recorded:
                e_reappear_deg = float(np.degrees(true_rel_az))
                if variant.startswith("BIO-"):
                    e_ring_deg = float(np.degrees(angle_diff(true_rel_az, b_ang)))
                reappear_recorded = True

                # Sprawdzenie kryterium błędu sterowania (tylko gdy próba nie ma wcześniejszej dyskwalifikacji)
                if abs(e_reappear_deg) >= 20.0 and status == "SUCCESS":
                    status = "CONTROL_FAILURE"
                    error_reason = f"Duży błąd celowania przy wyłonieniu (|e| = {abs(e_reappear_deg):.1f}° >= 20°)"

            # G. Pomiar czasu reakwizycji celu po okluzji
            if t_sim >= t_reappear and t_reacquire is None:
                if abs(np.degrees(true_rel_az)) <= 5.0:
                    reacquire_steps += 1
                    if reacquire_steps >= 10:  # Utrzymanie w paśmie przez co najmniej 100 ms
                        t_reacquire = float(t_sim - t_reappear)
                else:
                    reacquire_steps = 0

    except Exception as exc:
        status = "TECHNICAL_FAILURE"
        error_reason = f"Wyjątek symulacji: {repr(exc)}"
    finally:
        r.close()

    # Weryfikacja czy punkt wyłonienia został poprawnie osiągnięty
    if not reappear_recorded and status not in ("TECHNICAL_FAILURE", "DEGENERATE_CALIBRATION"):
        status = "TECHNICAL_FAILURE"
        error_reason = "Symulacja zakończyła się przed nadejściem chwili wyłonienia celu"

    return dict(
        variant=variant,
        seed=seed,
        t_occ=t_occ,
        status=status,
        e_reappear_deg=e_reappear_deg,
        e_ring_deg=e_ring_deg,
        t_reacquire=t_reacquire,
        j_ctrl=float(j_ctrl),
        n_steps=k + 1,
        t_sim_final=float(d.time),
        y0=y0,
        vy=vy,
        error_reason=error_reason,
        fallback_used=bool(getattr(ctl, "fallback_used", False)),
        calibration_status=getattr(ctl, "calibration_status", "VALID"),
    )


# -----------------------------------------------------------------------------
# Testy jednostkowe geometrii, znaków i wrapowania (Fast Unit Tests)
# -----------------------------------------------------------------------------
def run_unit_tests() -> bool:
    """
    Weryfikuje 4 przypadki testowe znaków oraz brak wycieku danych.
    Działa całkowicie w RAM w czasie < 0.1 s, bez uruchamiania symulatora.
    """
    print("=" * 80)
    print("URUCHAMIANIE TESTÓW JEDNOSTKOWYCH GEOMETRII I ZNAKÓW STEROWANIA")
    print("=" * 80)

    # 1. Test wrapowania kąta
    assert abs(wrap_angle(0.0)) < 1e-12
    assert abs(wrap_angle(np.pi) - (-np.pi)) < 1e-12 or abs(wrap_angle(np.pi) - np.pi) < 1e-12
    assert abs(wrap_angle(3.0 * np.pi) - (-np.pi)) < 1e-12 or abs(wrap_angle(3.0 * np.pi) - np.pi) < 1e-12
    assert abs(angle_diff(np.radians(175), np.radians(-175)) - np.radians(-10)) < 1e-7
    print(" [OK] Test 1: Wrapowanie kątów na granicy [-pi, +pi).")

    # 2. Testy znaków regulatora LastObs-PD
    ctl = LastObsPDController(kp=2.0, kd=0.1)

    # Przypadek 1: Cel po lewej (+20 deg), baza spoczywa
    w1 = ctl.step(cue_rel=np.radians(20), mouth_az=0.0, w_base=0.0)
    assert w1 > 0.0, f"Błąd znaku: cel po lewej powinien dawać omega > 0, otrzymano {w1}"
    print(f" [OK] Przypadek 1: Cel po lewej (+20°) -> omega = {w1:+.3f} rad/s (skręt w lewo).")

    # Przypadek 2: Cel po prawej (-20 deg), baza spoczywa
    w2 = ctl.step(cue_rel=np.radians(-20), mouth_az=0.0, w_base=0.0)
    assert w2 < 0.0, f"Błąd znaku: cel po prawej powinien dawać omega < 0, otrzymano {w2}"
    print(f" [OK] Przypadek 2: Cel po prawej (-20°) -> omega = {w2:+.3f} rad/s (skręt w prawo).")

    # Przypadek 3: Skok przez granicę +-pi (cel +175°, paszcza -175°)
    ctl.theta_w_last = np.radians(175)
    w3 = ctl.step(cue_rel=None, mouth_az=np.radians(-175), w_base=0.0)
    assert w3 < 0.0, f"Błąd znaku na granicy +-pi: powinien skręcać w prawo o 10°, otrzymano {w3}"
    print(f" [OK] Przypadek 3: Granica +-pi (+175° vs -175°) -> omega = {w3:+.3f} rad/s (najkrótsza droga).")

    # Przypadek 4: Tłumienie prędkości własnej (cel w osi, baza kręci się w lewo +0.5 rad/s)
    ctl.theta_w_last = 0.0
    w4 = ctl.step(cue_rel=None, mouth_az=0.0, w_base=0.5)
    assert w4 < 0.0, f"Błąd znaku tłumienia: w_base > 0 powinno dawać moment hamujący < 0, otrzymano {w4}"
    print(f" [OK] Przypadek 4: Tłumienie ruchu bazy (w_base = +0.5 rad/s) -> omega = {w4:+.3f} rad/s (hamowanie).")

    # 3. Testy filtru Kalmana
    kf = LinearKalmanTargetEstimator(q_w=0.1, r_v=0.01, dt=0.01)
    kf.reset(theta_init=0.0, omega_init=0.2)
    for _ in range(50):
        kf.predict()
    assert abs(kf.theta_world - 0.1) < 0.02, f"Predykcja Kalmana rozbieżna: {kf.theta_world}"
    print(" [OK] Test 5: Predykcja filtru Kalmana w okluzji zachowuje stan dynamiczny.")

    # 4. Testy walidacji nachylenia kalibracji (slope validation)
    # A: Prawidłowe nachylenie
    v_ok, r_ok = check_calibration_slope(np.array([12.5, 10.2]))
    assert v_ok is True, f"Nieoczekiwana flaga dla poprawnego nachylenia: {r_ok}"
    print(" [OK] Test 6: Prawidłowe nachylenie pamięci poprawnie zweryfikowane.")

    # B: Zerowe nachylenie
    v_zero, r_zero = check_calibration_slope(np.array([0.0, 0.0]))
    assert v_zero is False, "Zerowe nachylenie powinno być odrzucone jako zdegenerowane."
    assert "podprogowe nachylenie" in r_zero or "0." in r_zero
    print(" [OK] Test 7: Zerowe nachylenie pamięci poprawnie wykryte jako zdegenerowane.")

    # C: Nieskończone lub NaN nachylenie
    v_nan, _ = check_calibration_slope(np.array([np.nan, 10.0]))
    assert v_nan is False, "NaN w nachyleniu powinno być odrzucone."
    v_inf, _ = check_calibration_slope(np.array([np.inf, 10.0]))
    assert v_inf is False, "Inf w nachyleniu powinno być odrzucone."
    print(" [OK] Test 8: Nieskończone i NaN nachylenie pamięci poprawnie wykryte.")

    # 5. Testy zachowania BioAdaptiveController przy zdegenerowanej pamięci
    class MockBrain:
        def __init__(self, sl_mem, sl_vis=np.array([15.0, 15.0])):
            self.steer = {
                "offset": np.array([0.0, 0.0]),
                "slope": np.array(sl_vis, dtype=float),
                "offset_mem": np.array([0.0, 0.0]),
                "slope_mem": np.array(sl_mem, dtype=float),
            }
            self.calib = (np.array([-1.0, 1.0]), np.array([-1.0, 1.0]))
            self.groups = {
                "EPG": np.arange(10),
                "DNa02_L": np.array([10]), "DNa02_R": np.array([11]),
                "DNa01_L": np.array([12]), "DNa01_R": np.array([13]),
            }
            self.rate = np.ones(20) * 10.0
        def reset(self): pass
        def u_for(self, w): return 0.0
        def step10(self, **kw): return np.zeros((10, 20), bool)
        def bump(self, spk): return 0.0, 0.5, 10.0

    # D: Prawidłowy kontroler
    b_valid = MockBrain(sl_mem=[12.0, 10.0])
    ctl_valid = BioAdaptiveController(mode="static", brain=b_valid)
    assert ctl_valid.calibration_status == "VALID"
    w_val, _, _ = ctl_valid.step(cue_rel=None, mouth_az=0.0, w_base=0.0, t_sim=0.6)
    assert np.isfinite(w_val)
    print(" [OK] Test 9: BioAdaptiveController z prawidłową pamięcią działa bez przeszkód.")

    # E: Kontroler z zerowym nachyleniem (podstawowy BIO-Shuffle bez fallbacku)
    b_zero = MockBrain(sl_mem=[0.0, 0.0])
    ctl_zero = BioAdaptiveController(mode="shuffle", brain=b_zero, allow_fallback=False)
    assert ctl_zero.calibration_status == "DEGENERATE_CALIBRATION"
    w_zero, _, _ = ctl_zero.step(cue_rel=None, mouth_az=0.0, w_base=0.0, t_sim=0.6)
    assert w_zero == 0.0, f"Oczekiwano omega=0.0 przy zdegenerowanej kalibracji, otrzymano {w_zero}"
    assert ctl_zero.fallback_used is False, "Podstawowy BIO-Shuffle nie może używać ukrytego fallbacku!"
    assert np.isfinite(w_zero)
    print(" [OK] Test 10: Zerowe nachylenie w podstawowym BIO-Shuffle: omega=0.0 bez NaN/Inf i bez ukrytego fallbacku.")

    # F: Kontroler z NaN/Inf w nachyleniu
    b_nan = MockBrain(sl_mem=[np.nan, 0.0])
    ctl_nan = BioAdaptiveController(mode="shuffle", brain=b_nan, allow_fallback=False)
    assert ctl_nan.calibration_status == "DEGENERATE_CALIBRATION"
    w_nan, _, _ = ctl_nan.step(cue_rel=None, mouth_az=0.0, w_base=0.0, t_sim=0.6)
    assert w_nan == 0.0
    assert ctl_nan.fallback_used is False
    assert np.isfinite(w_nan)
    print(" [OK] Test 11: NaN/Inf w nachyleniu pamięci: omega=0.0 bez NaN/Inf i bez ukrytego fallbacku.")

    # G: Jawny tryb awaryjny allow_fallback=True
    ctl_fallback = BioAdaptiveController(mode="shuffle", brain=b_zero, allow_fallback=True)
    w_fb, _, _ = ctl_fallback.step(cue_rel=None, mouth_az=0.0, w_base=0.0, t_sim=0.6)
    assert ctl_fallback.fallback_used is True, "W trybie awaryjnym flaga fallback_used powinna być True."
    assert np.isfinite(w_fb)
    print(" [OK] Test 12: Jawny tryb diagnostyczny allow_fallback=True poprawnie oznacza fallback_used=True.")

    print("=" * 80)
    print("WSZYSTKIE TESTY JEDNOSTKOWE ZAKOŃCZONE POWODZENIEM (PASS)")
    print("=" * 80)
    return True


# -----------------------------------------------------------------------------
# Narzędzia statystyczne: Test niegorszości i przedziały ufności
# -----------------------------------------------------------------------------
def compute_non_inferiority_stats(
    diffs: np.ndarray,
    delta_ni: float = CFG["delta_ni_deg"],
    alpha: float = CFG["alpha_signif"]
) -> Dict[str, float]:
    """
    Oblicza statystyki sparowane dla testu niegorszości:
      H0: mu_diff >= delta_ni (BIO jest gorsze o >= delta_ni)
      H1: mu_diff < delta_ni  (BIO jest nie gorsze w marginesie delta_ni)
    diffs = |e_BIO| - |e_Baseline|
    """
    n = len(diffs)
    m = float(np.mean(diffs))
    s = float(np.std(diffs, ddof=1))
    se = s / math.sqrt(n)

    t_crit = float(st.t.ppf(1.0 - alpha, df=n - 1))
    ci_upper = m + t_crit * se

    t_stat = (m - delta_ni) / se if se > 1e-12 else 0.0
    p_non_inf = float(st.t.cdf(t_stat, df=n - 1))

    pairwise_means = [(diffs[i] + diffs[j]) / 2.0 for i in range(n) for j in range(i, n)]
    hl_median = float(np.median(pairwise_means))

    return dict(
        n=n,
        mean_diff=m,
        std_diff=s,
        se_diff=se,
        ci_upper_95=ci_upper,
        p_non_inferiority=p_non_inf,
        non_inferior_confirmed=bool(ci_upper < delta_ni),
        hodges_lehmann_median=hl_median,
    )


# -----------------------------------------------------------------------------
# Szacowanie mocy statystycznej i wielkości próby
# -----------------------------------------------------------------------------
def estimate_required_sample_size(s_delta: float, delta_ni: float = 3.0, alpha: float = 0.05, power: float = 0.80) -> int:
    """
    Wyznacza minimalną liczebność próby N dla sparowanego testu niegorszości:
      N >= (z_{1-alpha} + z_{power})^2 * s_delta^2 / delta_ni^2
    """
    z_a = float(st.norm.ppf(1.0 - alpha))
    z_b = float(st.norm.ppf(power))
    n_exact = ((z_a + z_b) ** 2) * (s_delta ** 2) / (delta_ni ** 2)
    return int(math.ceil(n_exact))


# -----------------------------------------------------------------------------
# Punkt wejścia CLI
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Eksperyment 2: Pamięć robocza CX vs Kalman + PD")
    parser.add_argument("--test-unit", action="store_true", help="Uruchom szybkie testy jednostkowe w RAM (< 0.1 s)")
    parser.add_argument("--check-calibration", action="store_true", help="Sprawdź tabele kalibracji u_for(0.0) i steer")
    parser.add_argument("--estimate-sample-size", type=float, metavar="S_DELTA", help="Oszacuj N na podstawie odchylenia pilotażowego")
    parser.add_argument("--run-single-trial", action="store_true", help="Uruchom jedną krótką próbę diagnostyczną")
    parser.add_argument("--variant", type=str, default="LastObs-PD", choices=ALL_VARIANTS, help="Wariant kontrolera")
    parser.add_argument("--seed", type=int, default=100, help="Ziarno losowości sceny")
    parser.add_argument("--t-occ", type=float, default=1.0, help="Czas okluzji [s]")
    parser.add_argument("--t-total", type=float, default=2.5, help="Czas całkowity próby diagnostycznej [s]")
    args = parser.parse_args()

    if args.test_unit:
        success = run_unit_tests()
        sys.exit(0 if success else 1)

    if args.estimate_sample_size is not None:
        s_d = args.estimate_sample_size
        n_single = estimate_required_sample_size(s_d, delta_ni=3.0, alpha=0.05, power=0.80)
        n_holm = estimate_required_sample_size(s_d, delta_ni=3.0, alpha=0.0125, power=0.80)
        print("=" * 80)
        print(f"OSZACOWANIE LICZEBNOŚCI PRÓBY DLA S_DELTA = {s_d:.2f}° (Margines Δ_NI = 3.0°)")
        print("=" * 80)
        print(f" 1. Pojedynczy główny punkt końcowy (alpha = 0.05, power = 80%): N >= {n_single}")
        print(f" 2. Korekta dla 4 czasów okluzji (alpha = 0.0125, power = 80%): N >= {n_holm}")
        print("=" * 80)
        sys.exit(0)

    if args.check_calibration:
        print("Sprawdzanie kalibracji Brain(seed=0)...")
        b = Brain(seed=0)
        b.calibrate_ring()
        b.calibrate_steer()
        u0 = b.u_for(0.0)
        print(f"Trim spoczynkowy u_for(0.0): {u0:+.4f} (neutralizacja dryfu konektomu)")
        print(f"Offset DNa02 widzenie: {b.steer['offset'][0]:+.2f} Hz | pamięć: {b.steer['offset_mem'][0]:+.2f} Hz")
        print(f"Nachylenie DNa02 widzenie: {b.steer['slope'][0]:+.2f} Hz/rad | pamięć: {b.steer['slope_mem'][0]:+.2f} Hz/rad")
        sys.exit(0)

    if args.run_single_trial:
        print("=" * 80)
        print(f"POJEDYNCZA PRÓBA DIAGNOSTYCZNA: wariant={args.variant}, seed={args.seed}, t_occ={args.t_occ} s")
        print("=" * 80)
        res = run_closedloop_trial(
            variant=args.variant,
            seed=args.seed,
            t_occ=args.t_occ,
            t_total=args.t_total,
        )
        print(json.dumps(res, indent=2))
        sys.exit(0)

    print("Skrypt testowy Eksperymentu 2. Użyj --test-unit, aby uruchomić bezpieczną weryfikację logiki.")


if __name__ == "__main__":
    main()
