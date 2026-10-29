#!/usr/bin/env python3
"""
bio2/test_cx_causal_memory.py — Faza 2: przyczynowa walidacja pamięci CX (eksperyment-only).

Pytanie: czy trwały stan sieci CX przyczynowo poprawia zachowanie skierowane na cel podczas okluzji, ponad
dopasowaną nie-neuronalną pamięć z identyczną informacją?

Projekt (szczegóły: results/cx_causal_phase2_*/causal_protocol.md):
  * Wspólny tor widzenia dla WSZYSTKICH ramion: omega = K * cue_rel (cue z widzenia, None przy braku detekcji -> 0).
    Faza widoczna jest więc bit-identyczna we wszystkich ramionach danego ziarna (sieć CX tylko „słucha”).
  * Okluzja startuje po zbieżności śledzenia (kryterium numeryczne CONV), piłeczka zatrzymywana w chwili okluzji
    (Eksp. A; cel stacjonarny w okluzji) albo jedzie dalej (Eksp. B).
  * Bierny obrót bazy (eksperymentator) w oknie PASSIVE: ramiona dostają tylko w_base (propriocepcja).
  * Po oknie: omega = K * theta_hat, theta_hat z pamięci danego ramienia:
      cx_bump   — kąt wektora populacji EPG (PEN napędzane u_for(-w_base) lub u_for(0) dla 'noself');
      cx_dn     — odczyt DNa02/DNa01 L−R jedną kalibracją pamięci (offset_mem/slope_mem), bez przełączania;
      scalar    — ostatni cue minus całka w_base dt (ta sama informacja, bez sieci);
      cv        — filtr stałej prędkości (Eksp. B) na tym samym cue + w_base;
      freeze    — omega = 0.
  * Interwencje w okluzji: impuls EPG (prąd jak bodziec wzrokowy) w bump+delta (delta=0 = sham), reset pierścienia
    (hamowanie rest=True), przesunięcie skalarne (scalar_shift).
Brak dostępu do prawdziwego położenia celu przez sterowniki (tylko metryki). Ziarna 0–39 zabronione.
"""
import argparse
import copy
import hashlib
import json
import os
import shutil
import sys
import time

import mujoco
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import scene2
from brain import Brain
from test_cx_working_memory_vs_kalman import angle_diff, get_aim_azimuth, get_ball_azimuth, wrap_angle
from vision import Vision

PROTOCOL_VERSION = "v4"   # results/cx_causal_phase2_*/confirmatory_protocol_v4.md

# Parametry zamrażane po fazie rozwojowej (seeds DEV); zmiany tylko z wpisem w progress_log.
CFG = dict(dt=0.01, w_max=0.6, windup=0.02, K=2.5,
           conv_t_min=1.0, conv_t_max=2.2, conv_win=30, conv_seen_min=27, conv_rate_max_deg_s=4.0,
           t_occ=2.0, passive_start=0.0, passive_dur=0.6, int_start=0.7, pulse_dur=0.2, reset_start=0.0, reset_dur=0.1,
           y0_range=(0.12, 0.16), v_range=(0.07, 0.12), coh_min=0.2, shuffle_frac=0.2,
           # zamrożone po DEV (seeds 200–209): lambda_self — wspólna skala kinematyczna w_base -> zmiana namiaru
           # (wszystkie pamięci); lambda_cx — dodatkowy trym wejścia PEN, część kalibracji ramienia CX
           lambda_self=1.105, lambda_cx=0.65,
           # v2 (po red-team): skok celu tuż przed okluzją poszerza zapamiętywany namiar (zamrożone w protokole v4)
           jump_range=(10.0, 20.0), jump_vis=0.2)
HELDOUT = set(range(40))
MEMORIES = ("cx_bump", "cx_dn", "scalar", "cv", "freeze", "selfonly")


def apply_velocity(d, m, w):
    """Jak agent.py/phase 1: komenda prędkości -> cel pozycyjny serwa z ogranicznikiem windup."""
    w = float(np.clip(w, -CFG["w_max"], CFG["w_max"]))
    c = np.clip(d.ctrl[0] - w * CFG["dt"], d.qpos[0] - CFG["windup"], d.qpos[0] + CFG["windup"])
    d.ctrl[0] = np.clip(c, *m.actuator_ctrlrange[0])


def scene_params(seed):
    """Losowy kierunek (±), położenie i prędkość; cel startuje po stronie przeciwnej do kierunku ruchu."""
    rng = np.random.default_rng(seed)
    s = 1.0 if rng.random() < 0.5 else -1.0
    y0 = s * rng.uniform(*CFG["y0_range"])
    vy = -s * rng.uniform(*CFG["v_range"])
    return y0, vy


def calibrated_brain(seed, shuffle_frac=0.0):
    """shuffle_frac > 0: częściowa permutacja wag CX w obrębie projekcji i znaku (bez kompensacji wzmocnień);
    kalibracje u_for/steer są własne dla sieci (część definicji kontroli)."""
    b = Brain(seed=seed)
    if shuffle_frac > 0:
        rng = np.random.default_rng(10_000 + seed)
        g, W = b.groups, b.net.W.copy()
        cxg = ["EPG", "PEN_a_L", "PEN_a_R", "PEN_b_L", "PEN_b_R", "Delta7", "PFL3_L", "PFL3_R"]
        for ga in cxg:
            for gb in cxg:
                sub = W[np.ix_(g[gb], g[ga])].copy()
                for sign in (1.0, -1.0):
                    idx = np.flatnonzero((sign * sub) > 0)
                    pick = idx[rng.random(len(idx)) < shuffle_frac]
                    sub.flat[pick] = sub.flat[rng.permutation(pick)]
                W[np.ix_(g[gb], g[ga])] = sub
        b.net.W = W
        b.reset()
    b.calibrate_ring()
    b.calibrate_steer()
    return b


class ScalarMemory:
    """theta_hat = ostatni widziany cue, potem theta_hat -= w_base*dt (cel stacjonarny w świecie)."""
    def __init__(self):
        self.th = None

    def step(self, cue, w_base, dt):
        if cue is not None:
            self.th = cue
        elif self.th is not None:
            self.th = wrap_angle(self.th - w_base * dt)
        return self.th


class SelfOnlyMemory:
    """Integrator bez celu (kontrola): zakłada cel na wprost w chwili utraty widzenia, potem tylko -∫w dt.
    Mierzy, ile wyniku daje sama kompensacja ruchu własnego, bez pamięci namiaru celu."""
    def __init__(self):
        self.th = None

    def step(self, cue, w_base, dt):
        if cue is not None:
            self.th = 0.0
        elif self.th is not None:
            self.th = wrap_angle(self.th - w_base * dt)
        return self.th


class CVMemory:
    """Filtr alfa-beta stałej prędkości kątowej celu w układzie egocentrycznym z kompensacją w_base
    (ta sama informacja co CX: cue + w_base; bez aim_az). Prędkość własna celu v_t = d(cue)/dt + w_base."""
    def __init__(self, alpha=0.5, beta=0.1, v_max=1.0):
        self.alpha, self.beta, self.v_max = alpha, beta, v_max
        self.th, self.v = None, 0.0

    def step(self, cue, w_base, dt):
        if self.th is None:
            self.th = cue
            return self.th
        pred = wrap_angle(self.th + (self.v - w_base) * dt)
        if cue is not None:
            r = angle_diff(cue, pred)
            self.th = wrap_angle(pred + self.alpha * r)
            self.v = float(np.clip(self.v + self.beta * r / dt, -self.v_max, self.v_max))
        else:
            self.th = pred
        return self.th


def dn_readout(brain, dn_f):
    st = brain.steer
    return float(np.mean((dn_f - st["offset_mem"]) / st["slope_mem"]))


def run_trial(seed, memory, pen="self", passive_deg=0.0, intervention=None, int_delta_deg=0.0, ball_stop=True,
              brain0=None, K=None, t_occ=None, cv_params=None, jump=False):
    """Jedna próba. memory ∈ MEMORIES; pen ∈ {'self','none'}; intervention ∈ {None,'pulse','reset','scalar_shift'}."""
    assert seed not in HELDOUT, "ziarna 0–39 są zarezerwowane (held-out)"
    assert memory in MEMORIES
    K = CFG["K"] if K is None else K
    t_occ = CFG["t_occ"] if t_occ is None else t_occ
    dt = CFG["dt"]
    y0, vy = scene_params(seed)
    m, d = scene2.load()
    scene2.reset_scene(m, d, ball_y0=y0, ball_vy=vy)
    scene2.set_mocap(m, d, "occluder", scene2.PARK)
    mujoco.mj_forward(m, d)
    r, opt = scene2.eye_renderer(m)
    vis = Vision(scene2.CAM_FOVY, scene2.CAM_W / scene2.CAM_H, efference=True)
    bv = m.joint("ball").dofadr[0]

    uses_cx = memory in ("cx_bump", "cx_dn")
    brain = copy.deepcopy(brain0) if uses_cx else None
    if uses_cx:
        brain.reset()
    g = brain.groups if uses_cx else None
    mem = (ScalarMemory() if memory == "scalar" else CVMemory(**(cv_params or {})) if memory == "cv" else
           SelfOnlyMemory() if memory == "selfonly" else None)
    jr = np.random.default_rng(77_777 + seed)                 # skok zależy tylko od ziarna (wspólny dla ramion)
    jump_deg = float((1.0 if jr.random() < 0.5 else -1.0) * jr.uniform(*CFG["jump_range"]))
    t_conv = None
    dn_f = np.zeros(2)
    a_dn = np.exp(-dt / np.array([0.10, 0.40]))

    rec = dict(seed=seed, memory=memory, pen=pen, passive_deg=passive_deg, intervention=intervention,
               int_delta_deg=int_delta_deg, ball_stop=ball_stop, K=K, t_occ=t_occ, y0=y0, vy=vy,
               jump=jump, jump_deg=jump_deg if jump else 0.0,
               status="OK", reason="", lambda_self=CFG["lambda_self"], lambda_cx=CFG["lambda_cx"])
    hist_cue = []
    t_on = None
    q_prev = None
    th_hat = None
    snaps = {}
    log = []
    k = -1
    try:
        n_max = int(round((CFG["conv_t_max"] + t_occ + 0.05) / dt))
        for k in range(n_max):
            t = d.time
            q, wq = float(d.qpos[0]), float(d.qvel[0])
            dpsi = 0.0 if q_prev is None else -(q - q_prev)
            q_prev = q
            w_base = -wq
            w_mem = CFG["lambda_self"] * w_base          # to samo dla wszystkich pamięci
            r.update_scene(d, camera="eye", scene_option=opt)
            vo = vis.step(r.render(), dpsi=dpsi)
            R = d.cam("eye").xmat.reshape(3, 3)
            c0 = d.cam("eye").xpos
            aim = get_aim_azimuth(d)
            cue = None
            for c in vo.get("cands", []):
                rw = R @ c["ray"]
                if rw[2] < -1e-3:
                    p = c0 + (scene2.scene.BALL_R - c0[2]) / rw[2] * rw
                    cue = angle_diff(float(np.arctan2(p[1], p[0])), aim)
                    break
            true_rel = angle_diff(get_ball_azimuth(d), aim)

            # --- kryterium zbieżności i start okluzji (identyczne dla wszystkich ramion — faza widoczna wspólna)
            if t_on is None:
                hist_cue.append(cue)
                win = hist_cue[-CFG["conv_win"]:]
                seen = [c for c in win if c is not None]
                if t >= CFG["conv_t_min"] - 1e-9 and len(win) == CFG["conv_win"] and len(seen) >= CFG["conv_seen_min"]:
                    idx = [i for i, c in enumerate(win) if c is not None]
                    rate = abs(np.polyfit(np.array(idx) * dt, np.degrees(seen), 1)[0])
                    if rate <= CFG["conv_rate_max_deg_s"] and t_conv is None:
                        t_conv = t
                        rec.update(conv_rate_deg_s=float(rate), conv_seen=len(seen), t_conv=float(t))
                        if jump:                                   # teleport w azymucie, prędkość bez zmian
                            bj = m.joint("ball").qposadr[0]
                            bx, by_ = d.qpos[bj], d.qpos[bj + 1]
                            az = np.arctan2(by_, bx) + np.radians(jump_deg)
                            d.qpos[bj + 1] = bx * np.tan(az)
                if t_conv is not None and t_on is None and t >= t_conv + (CFG["jump_vis"] if jump else 0.0) - 1e-9:
                    t_on = t
                if t_conv is None and t >= CFG["conv_t_max"] - 1e-9:
                    rec.update(status="NOT_CONVERGED", reason=f"brak zbieżności do t={t:.2f}")
                    break
            occluded = t_on is not None and t < t_on + t_occ - 1e-9
            if t_on is not None and not occluded:
                rec.update(e_end_deg=float(np.degrees(true_rel)), t_end=float(t),
                           th_hat_end_deg=None if th_hat is None else float(np.degrees(th_hat)),
                           mem_err_end_deg=None if th_hat is None else float(np.degrees(angle_diff(th_hat, true_rel))))
                break
            rel = None if t_on is None else t - t_on
            if rel is not None and abs(rel) < 1e-9 and ball_stop:
                d.qvel[bv:bv + 6] = 0.0
            cue_in = None if occluded else cue
            passive = rel is not None and CFG["passive_start"] - 1e-9 <= rel < CFG["passive_start"] + CFG["passive_dur"] - 1e-9
            t_i0 = CFG["int_start"] if intervention == "pulse" else CFG["reset_start"]
            t_i1 = t_i0 + (CFG["pulse_dur"] if intervention == "pulse" else CFG["reset_dur"])
            in_int = rel is not None and intervention in ("pulse", "reset") and t_i0 - 1e-9 <= rel < t_i1 - 1e-9

            # --- krok pamięci
            if uses_cx:
                u = brain.u_for(-CFG["lambda_cx"] * w_mem) if pen == "self" else brain.u_for(0.0)
                if in_int and intervention == "pulse":
                    if "bump_pre_int" not in snaps:
                        snaps["bump_pre_int"] = snaps.get("_last_bump", 0.0)
                    spk = brain.step10(cue=snaps["bump_pre_int"] + np.radians(int_delta_deg), u=u)
                elif in_int and intervention == "reset":
                    spk = brain.step10(u=u, rest=True)
                else:
                    spk = brain.step10(cue=cue_in, u=u)
                b_ang, b_coh, b_epg = brain.bump(spk)
                snaps["_last_bump"] = b_ang
                rt = brain.rate
                raw = np.array([rt[g["DNa02_L"]].mean() - rt[g["DNa02_R"]].mean(),
                                rt[g["DNa01_L"]].mean() - rt[g["DNa01_R"]].mean()])
                dn_f = a_dn * dn_f + (1 - a_dn) * raw
                # jawna reguła odczytu (wszystkie ramiona CX): brak spójnego wzgórza -> brak estymaty (omega = 0)
                th_hat = (None if b_coh < CFG["coh_min"] else b_ang) if memory == "cx_bump" else dn_readout(brain, dn_f)
                cx_state = dict(bump_deg=float(np.degrees(b_ang)), coh=float(b_coh), epg_hz=float(b_epg),
                                pfl3_hz=float(rt[np.r_[g["PFL3_L"], g["PFL3_R"]]].mean()), dna02_lr=float(raw[0]),
                                dn_hat_deg=float(np.degrees(dn_readout(brain, dn_f))))
            else:
                cx_state = {}
                if mem is not None:
                    th_hat = mem.step(cue_in, w_mem, dt)
                if intervention == "scalar_shift" and rel is not None and abs(rel - CFG["int_start"]) < 1e-6 and th_hat is not None:
                    mem.th = wrap_angle(mem.th + np.radians(int_delta_deg))
                    th_hat = mem.th

            # --- polecenie
            if not occluded:
                omega = 0.0 if cue is None else K * cue              # wspólny tor widzenia
            elif passive:
                omega = np.radians(passive_deg) / CFG["passive_dur"]  # bierny obrót (eksperymentator)
            elif memory == "freeze" or th_hat is None:
                omega = 0.0
            else:
                omega = K * th_hat
            if not np.isfinite(omega):
                rec.update(status="TECHNICAL_FAILURE", reason=f"nie-skończona komenda w kroku {k}")
                break

            # --- migawki
            def snap(name):
                snaps[name] = dict(t=float(t), true_rel_deg=float(np.degrees(true_rel)), aim_deg=float(np.degrees(aim)),
                                   w_base=float(w_base), omega=float(omega),
                                   th_hat_deg=None if th_hat is None else float(np.degrees(th_hat)), **cx_state)
            if rel is not None and abs(rel) < 1e-9:
                snap("onset")
            if rel is not None and abs(rel - (CFG["passive_start"] + CFG["passive_dur"])) < 1e-6:
                snap("post_passive")
            if rel is not None and abs(rel - CFG["int_start"]) < 1e-6:
                snap("pre_int")
            if rel is not None and abs(rel - (CFG["int_start"] + CFG["pulse_dur"] + 0.05)) < 1e-6:
                snap("post_int")
            if rel is not None:
                log.append((round(rel, 3), round(float(np.degrees(true_rel)), 3), round(float(omega), 4),
                            None if th_hat is None else round(float(np.degrees(th_hat)), 3), cx_state.get("coh")))

            apply_velocity(d, m, omega)
            for _ in range(10):
                mujoco.mj_step(m, d)
    except Exception as exc:
        rec.update(status="TECHNICAL_FAILURE", reason=repr(exc))
    finally:
        r.close()
    snaps.pop("_last_bump", None)
    if "bump_pre_int" in snaps:
        snaps["bump_pre_int"] = float(np.degrees(snaps["bump_pre_int"]))
    if rec["status"] == "OK" and "e_end_deg" not in rec:
        rec.update(status="TECHNICAL_FAILURE", reason="koniec bez chwili wyłonienia")
    rec.update(t_on=t_on, n_steps=k + 1, snaps=snaps, log=log,
               steer_calib=({kk: np.asarray(v).tolist() for kk, v in brain0.steer.items()} if uses_cx else None))
    if "onset" in snaps and "post_passive" in snaps:
        rec["passive_realised_deg"] = snaps["post_passive"]["aim_deg"] - snaps["onset"]["aim_deg"]
    return rec


# ----------------------------------------------------------------------------- testy jednostkowe (bez MuJoCo)
def run_unit_tests():
    sm = ScalarMemory()
    assert sm.step(None, 0.0, 0.01) is None
    assert abs(sm.step(0.2, 0.0, 0.01) - 0.2) < 1e-12
    for _ in range(100):
        sm.step(None, 0.1, 0.01)                       # baza w lewo 0.1 rad/s przez 1 s -> cel 0.1 rad bardziej w prawo
    assert abs(sm.th - 0.1) < 1e-9, sm.th
    sm.th = np.radians(179.0)
    sm.step(None, -np.radians(2.0) / 0.01, 0.01)       # zawijanie przez ±pi
    assert abs(np.degrees(sm.th) - (-179.0)) < 1e-6, np.degrees(sm.th)
    cv = CVMemory(alpha=0.5, beta=0.1)
    cv.step(0.0, 0.0, 0.01)
    for k in range(1, 300):                            # cel w świecie 0.2 rad/s, baza stoi
        cv.step(0.2 * k * 0.01, 0.0, 0.01)
    assert abs(cv.v - 0.2) < 0.02, cv.v
    th0 = cv.th
    for _ in range(100):
        cv.step(None, 0.0, 0.01)
    assert abs((cv.th - th0) - 0.2) < 0.03, cv.th - th0  # ekstrapolacja przez 1 s
    cv2 = CVMemory()
    cv2.step(0.0, 0.0, 0.01)
    for _ in range(300):                               # cel stoi, baza w lewo 0.3 rad/s: cue maleje, v celu ~0
        cv2.step(wrap_angle(cv2.th - 0.3 * 0.01), 0.3, 0.01)
    assert abs(cv2.v) < 0.02, cv2.v
    so = SelfOnlyMemory()
    so.step(0.3, 0.0, 0.01)
    assert so.th == 0.0                                # ignoruje namiar celu
    for _ in range(100):
        so.step(None, 0.1, 0.01)
    assert abs(so.th + 0.1) < 1e-9, so.th
    y_signs = {np.sign(scene_params(s)[0]) for s in range(200, 240)}
    assert y_signs == {1.0, -1.0}
    assert all(np.sign(scene_params(s)[0]) == -np.sign(scene_params(s)[1]) for s in range(200, 240))
    try:
        run_trial(5, "freeze")
        raise RuntimeError("held-out guard failed")
    except AssertionError:
        pass
    print("UNIT TESTS PASS (ScalarMemory integration/wrap, CVMemory velocity/extrapolation/self-motion, "
          "scene randomisation both directions, held-out guard)")
    return True


ARMS = {  # nazwa -> kwargs run_trial (Eksp. A, C, D)
    "CX-Bump": dict(memory="cx_bump"),
    "CX-Bump-NoSelf": dict(memory="cx_bump", pen="none"),
    "CX-DN": dict(memory="cx_dn"),
    "Scalar": dict(memory="scalar"),
    "Freeze": dict(memory="freeze"),
    "CX-Reset": dict(memory="cx_bump", intervention="reset"),
    "CX-Pulse+30": dict(memory="cx_bump", intervention="pulse", int_delta_deg=30.0),
    "CX-Pulse-30": dict(memory="cx_bump", intervention="pulse", int_delta_deg=-30.0),
    "CX-Sham": dict(memory="cx_bump", intervention="pulse", int_delta_deg=0.0),
    "Scalar-Shift+30": dict(memory="scalar", intervention="scalar_shift", int_delta_deg=30.0),
    "Scalar-Shift-30": dict(memory="scalar", intervention="scalar_shift", int_delta_deg=-30.0),
    "CV": dict(memory="cv"),
    "CX-Shuffle20": dict(memory="cx_bump", net="shuffle"),
    "SelfOnly": dict(memory="selfonly"),
    "CX-DN-Sham": dict(memory="cx_dn", intervention="pulse", int_delta_deg=0.0),
    "CX-DN-Pulse+30": dict(memory="cx_dn", intervention="pulse", int_delta_deg=30.0),
    "CX-DN-Pulse-30": dict(memory="cx_dn", intervention="pulse", int_delta_deg=-30.0),
}


def runner_sha256():
    with open(os.path.abspath(__file__), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def cfg_sha256(cfg):
    return hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()


class DatasetError(RuntimeError):
    pass


class Dataset:
    """Plik JSONL + manifest <out>.manifest.json (niezmienny) + dziennik uruchomień <out>.runs.jsonl + blokada <out>.lock.
    Wznowienie tylko przy identycznej konfiguracji; uszkodzony ostatni rekord -> odmowa (albo jawna naprawa z kopią)."""
    IDENTITY = ("dataset_id", "protocol_version", "runner_sha256", "cfg_sha256", "jump", "moving", "arms", "passive", "no_log")

    def __init__(self, out, identity, repair_truncated=False):
        self.out = os.path.abspath(out)
        self.man_path = self.out + ".manifest.json"
        self.lock_path = self.out + ".lock"
        self.identity = identity
        self.repair = repair_truncated
        self.lock_fd = None

    def __enter__(self):
        d = os.path.dirname(self.out)
        os.makedirs(d, exist_ok=True)
        if not os.access(d, os.W_OK):
            raise DatasetError(f"katalog wyjściowy niezapisywalny: {d}")
        try:
            self.lock_fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise DatasetError(f"zbiór zablokowany (inny proces lub porzucona blokada): {self.lock_path} — "
                               "usuń ręcznie tylko po upewnieniu się, że żaden proces nie pisze")
        os.write(self.lock_fd, f"pid={os.getpid()} {time.strftime('%Y-%m-%dT%H:%M:%S')}\n".encode())
        try:
            self._check_manifest()
            self.done = self._load_records()
        except Exception:
            self._unlock()
            raise
        return self

    def __exit__(self, *exc):
        self._unlock()

    def _unlock(self):
        if self.lock_fd is not None:
            os.close(self.lock_fd)
            os.remove(self.lock_path)
            self.lock_fd = None

    def _check_manifest(self):
        if os.path.exists(self.man_path):
            man = json.load(open(self.man_path))
            diff = {k: (man.get(k), self.identity[k]) for k in self.IDENTITY if man.get(k) != self.identity[k]}
            if diff:
                raise DatasetError(f"konfiguracja różni się od manifestu {self.man_path}: {diff}")
        else:
            if os.path.exists(self.out):
                raise DatasetError(f"plik danych bez manifestu: {self.out} (odmowa dopisywania)")
            man = dict(self.identity, cfg=copy.deepcopy(CFG), created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
                       versions=dict(python=sys.version.split()[0], mujoco=mujoco.__version__, numpy=np.__version__))
            tmp = self.man_path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(man, f, indent=1)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.man_path)

    def _load_records(self):
        done = set()
        if not os.path.exists(self.out):
            return done
        raw = open(self.out, "rb").read()
        lines = raw.split(b"\n")
        bad_tail = lines.pop() or None          # fragment bez końcowego '\n' = niepełny ostatni zapis
        for n, ln in enumerate(lines, 1):
            try:
                x = json.loads(ln)
            except ValueError:
                raise DatasetError(f"uszkodzony rekord w linii {n} — odmowa; plik bez zmian")
            for k in ("dataset_id", "protocol_version", "runner_sha256", "cfg_sha256"):
                if x.get(k) != self.identity[k]:
                    raise DatasetError(f"rekord w linii {n}: {k}={x.get(k)!r} ≠ {self.identity[k]!r}")
            key = (x["arm"], x["seed"], x["passive_deg"])
            if key in done:
                raise DatasetError(f"zduplikowany rekord {key} w linii {n}")
            done.add(key)
        if bad_tail is not None:
            if not self.repair:
                raise DatasetError("niepełny ostatni rekord JSONL — odmowa wznowienia; użyj --repair-truncated "
                                   "(kopia oryginału + raport) po sprawdzeniu pliku")
            ts = time.strftime("%Y%m%d_%H%M%S")
            orig = f"{self.out}.orig-{ts}"
            shutil.copy2(self.out, orig)
            good = b"".join(ln + b"\n" for ln in lines)
            rep = dict(action="removed incomplete last record", original_copy=orig, removed_bytes=len(bad_tail),
                       removed_repr=repr(bad_tail[:200]), kept_records=len(done), at=ts)
            with open(f"{self.out}.repair-{ts}.json", "w") as f:
                json.dump(rep, f, indent=1)
            tmp = self.out + ".tmp"
            with open(tmp, "wb") as f:
                f.write(good)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.out)
            print(f"NAPRAWA: usunięto niepełny ostatni rekord; oryginał {orig}", flush=True)
        return done

    def log_run(self, argv, seeds):
        with open(self.out + ".runs.jsonl", "a") as f:
            f.write(json.dumps(dict(argv=argv, seeds=seeds, pid=os.getpid(), at=time.strftime("%Y-%m-%dT%H:%M:%S"))) + "\n")

    def append(self, rec):
        key = (rec["arm"], rec["seed"], rec["passive_deg"])
        if key in self.done:
            raise DatasetError(f"próba dopisania duplikatu {key}")
        with open(self.out, "a") as f:
            f.write(json.dumps(rec) + "\n")
            f.flush()
            os.fsync(f.fileno())
        self.done.add(key)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Faza 2: przyczynowa walidacja pamięci CX")
    ap.add_argument("--test-unit", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--seeds", default="200-205")
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--passive", default="-20,20", help="bierne obroty [deg], po przecinku")
    ap.add_argument("--moving", action="store_true", help="Eksp. B: piłeczka nie jest zatrzymywana")
    ap.add_argument("--jump", action="store_true", help="v2: skok celu ±U(jump_range) na jump_vis s przed okluzją")
    ap.add_argument("--out", help="JSONL (dopisywany, wznawialny; manifest <out>.manifest.json)")
    ap.add_argument("--dataset-id", help="jawny identyfikator zbioru (wymagany z --run)")
    ap.add_argument("--repair-truncated", action="store_true",
                    help="usuń niepełny OSTATNI rekord (kopia oryginału + raport); inaczej odmowa")
    ap.add_argument("--lambda-self", type=float, default=CFG["lambda_self"])
    ap.add_argument("--lambda-cx", type=float, default=CFG["lambda_cx"])
    ap.add_argument("--no-log", action="store_true", help="nie zapisuj przebiegów czasowych")
    a = ap.parse_args(argv)
    CFG["lambda_self"] = a.lambda_self
    CFG["lambda_cx"] = a.lambda_cx
    if a.test_unit:
        sys.exit(0 if run_unit_tests() else 1)
    if not a.run:
        ap.print_help()
        return
    if not a.out or not a.dataset_id:
        sys.exit("Odmowa: --run wymaga --out i --dataset-id")
    lo, _, hi = a.seeds.partition("-")
    seeds = list(range(int(lo), int(hi) + 1)) if hi else [int(s) for s in a.seeds.split(",")]
    if set(seeds) & HELDOUT:
        sys.exit("Odmowa: ziarna 0–39 są held-out")
    arms = a.arms.split(",")
    unknown = [x for x in arms if x not in ARMS]
    if unknown or len(set(arms)) != len(arms):
        sys.exit(f"Odmowa: nieznane lub powtórzone ramiona {unknown or arms}")
    passives = [float(x) for x in a.passive.split(",")]
    rsha, csha = runner_sha256(), cfg_sha256(CFG)
    identity = dict(dataset_id=a.dataset_id, protocol_version=PROTOCOL_VERSION, runner_sha256=rsha, cfg_sha256=csha,
                    jump=a.jump, moving=a.moving, arms=arms, passive=passives, no_log=a.no_log)
    prov = dict(dataset_id=a.dataset_id, protocol_version=PROTOCOL_VERSION, runner_sha256=rsha, cfg_sha256=csha)
    try:
        ds = Dataset(a.out, identity, a.repair_truncated).__enter__()
    except DatasetError as e:
        sys.exit(f"Odmowa: {e}")
    try:
        ds.log_run(sys.argv if argv is None else argv, seeds)
        for s in seeds:
            brains = {}
            for arm in arms:
                for pd in passives:
                    if (arm, s, pd) in ds.done:
                        continue
                    kw = dict(ARMS[arm])
                    net = kw.pop("net", "intact")
                    t0 = time.time()
                    if kw["memory"].startswith("cx") and net not in brains:
                        try:
                            brains[net] = calibrated_brain(s, CFG["shuffle_frac"] if net == "shuffle" else 0.0)
                        except Exception as exc:          # trwały zapis zamiast utraty informacji
                            brains[net] = exc
                    brain0 = brains.get(net) if kw["memory"].startswith("cx") else None   # tylko ramiona CX używają sieci
                    if isinstance(brain0, Exception):
                        res = dict(seed=s, passive_deg=pd, ball_stop=not a.moving, jump=a.jump, status="TECHNICAL_FAILURE",
                                   reason=f"kalibracja sieci ({net}) nieudana: {brain0!r}")
                    else:
                        try:
                            res = run_trial(s, passive_deg=pd, ball_stop=not a.moving, brain0=brain0, jump=a.jump, **kw)
                        except Exception as exc:
                            res = dict(seed=s, passive_deg=pd, ball_stop=not a.moving, jump=a.jump,
                                       status="TECHNICAL_FAILURE", reason=f"infrastruktura: {exc!r}")
                    res.update(arm=arm, wall_s=round(time.time() - t0, 2),
                               finished_at=time.strftime("%Y-%m-%dT%H:%M:%S"), **prov)
                    if a.no_log:
                        res.pop("log", None)
                    ds.append(res)
                    print(f"{arm:16s} seed={s} passive={pd:+.0f} status={res['status']} e_end={res.get('e_end_deg')} "
                          f"t_on={res.get('t_on')} wall={res['wall_s']}s", flush=True)
    finally:
        ds.__exit__(None, None, None)


if __name__ == "__main__":
    main()
