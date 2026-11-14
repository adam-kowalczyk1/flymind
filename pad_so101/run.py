"""pad_so101/run.py — sterowanie SO-101 padem Xbox. Mapa przycisków i instrukcja: PLAN.md.

  .venv/bin/python pad_so101/run.py                                  # symulacja MuJoCo (flymind/so101.py)
  ~/miniforge3/envs/lerobot/bin/python pad_so101/run.py --real /dev/tty.usbmodemX   # prawdziwe ramię (NIESPRAWDZONE)

Pliki flymind/ są tylko importowane (so101.py, safety.py), nigdy zmieniane. Komendy mają źródło `classical:pad`.
"""
import argparse
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True                  # nic nie zapisujemy w flymind/ (nawet __pycache__)
sys.path[:0] = [HERE, os.path.join(os.path.dirname(HERE), "flymind")]

import dataclasses

import numpy as np
import pygame

import control
import settings
from control import ARM, Controller, PadState
from pad import Pad
from safety import Command, Limits, SafetyLayer

POSES = os.path.join(HERE, "poses.json")
RECS = os.path.join(HERE, "recordings")
SRC = "classical:pad"
RUMBLE = {"stop": (1.0, 600), "saved": (0.6, 150), "rec_saved": (0.6, 150), "tick": (0.3, 80), "limit": (0.15, 60)}
W, H, PANEL = 640, 480, 330

# --- symulacja ---
HOME_Q = (0.0, -1.0, 1.0, 0.6, 0.0, 0.6)    # chwytak ok. 11 cm nad stołem, 25 cm przed podstawą
BALL = (0.30, -0.08, 0.025)                  # na stole, obok chwytaka (do ćwiczenia chwytania)
GRIP_OPEN_Q = 1.745                          # q chwytaka [rad] dla g = 1 (górny zakres stawu)
KP_GRIP, KD_GRIP = 3.0, 0.05                 # N·m/rad, N·m·s/rad: pozycja chwytaka → moment (sim ma silnik momentowy)
# --- prawdziwe ramię: pokrętła kalibracji, sprawdzić przy pierwszym uruchomieniu na biegu 1 ---
REAL_SIGN = (1, 1, 1, 1, 1)                  # znak lerobot-stopnie → kierunek jak w symulacji; zły kierunek → −1
REAL_GRIP_OPEN = 100.0                       # gripper.pos dla g = 1 (lerobot RANGE_0_100); jeśli 0 = otwarty → 0.0


class SimArm:
    kind, dt = "sim", 0.01

    def __init__(self):
        import mujoco
        from so101 import SO101Sim
        self.mj, self.sim = mujoco, SO101Sim()
        self.ranges = self.sim.jrange.copy()
        self.reset()
        m = self.sim.m
        self._d, self._sid, self._sh = mujoco.MjData(m), m.site("gripperframe").id, m.body("shoulder").id
        self._u = np.array([1.0, 0, 0])
        self.view = mujoco.Renderer(m, H, W)
        self.cam = mujoco.MjvCamera()                   # za ramieniem (lekko z boku, żeby nie zasłaniało piłeczki): prawo ekranu = prawo ramienia
        self.cam.lookat[:], self.cam.distance, self.cam.azimuth, self.cam.elevation = (0.22, -0.03, 0.05), 0.8, 20, -42

    def reset(self):
        self.sim.reset(HOME_Q, ball_pos=BALL)

    def read(self):
        q = self.sim.d.qpos[self.sim.qadr]
        return q[:5].copy(), q[5] / GRIP_OPEN_Q, q.copy()

    def now(self):
        return float(self.sim.d.time)

    def jaw_torque(self, g):
        d, s = self.sim.d, self.sim
        return KP_GRIP * (d.qpos[s.qadr[5]] - g * GRIP_OPEN_Q) + KD_GRIP * d.qvel[s.vadr[5]]   # + = zamykanie

    def write(self, q5, tau, g):
        self.sim.act(q5, tau)
        self.sim.step()

    def jac(self, q5):
        """J[3,3]: (promień, wysokość, pochylenie nosa w górę) chwytaka względem (lift, elbow, wrist_flex)."""
        mj, m, d, s = self.mj, self.sim.m, self._d, self.sim
        d.qpos[:] = s.d.qpos
        d.qpos[s.qadr[:5]] = q5
        mj.mj_kinematics(m, d)
        mj.mj_comPos(m, d)
        jp, jr = np.zeros((3, m.nv)), np.zeros((3, m.nv))
        mj.mj_jacSite(m, d, jp, jr, self._sid)
        r = d.site_xpos[self._sid] - d.xpos[self._sh]
        if np.hypot(r[0], r[1]) > 0.02:                 # chwytak nad osią podstawy: zostaw poprzedni kierunek
            self._u = np.array([r[0], r[1], 0]) / np.hypot(r[0], r[1])
        ez = np.array([0, 0, 1.0])
        cols = s.vadr[1:4]
        return np.array([self._u @ jp[:, cols], ez @ jp[:, cols], np.cross(self._u, ez) @ jr[:, cols]])

    def frame(self):
        self.view.update_scene(self.sim.d, camera=self.cam)
        eye = self.sim.observe().frame.image
        return self.view.render(), eye

    def close(self):
        self.view.close()
        self.sim.close()


class RealArm:
    kind, dt = "real", 0.02
    jac = None                                          # tryb KART wyłączony: model ↔ ramię niesprawdzony

    def __init__(self, port, robot_id, cameras=None):
        from lerobot.robots.so_follower import SOFollower, SOFollowerRobotConfig
        cfg = SOFollowerRobotConfig(port=port, id=robot_id, use_degrees=True, max_relative_target=5.0, cameras=cameras or {},
                                    disable_torque_on_disconnect=False)   # po wyjściu ramię trzyma pozycję, nie opada
        self.robot = SOFollower(cfg)
        self.robot.connect()
        c = self.robot.calibration
        half = [math.radians((c[n].range_max - c[n].range_min) / 2 * 360 / 4095) for n in ARM]   # lerobot: 0° = środek
        self.ranges = np.array([[-h, h] for h in half] + [[0.0, 1.0]])
        # bez zasilania bark opada do ~100°, za kraniec z kalibracji (94°); do 15° poza: zakres poszerzony do pomiaru,
        # inaczej warstwa bezpieczeństwa odmawia startu. Serwo i tak nie pojedzie za swój limit z kalibracji.
        q5 = self.read()[0]
        for j, x in enumerate(q5):
            lo, hi = self.ranges[j]
            if lo - math.radians(15) <= x < lo or hi < x <= hi + math.radians(15):
                self.ranges[j] = (min(lo, x - 0.01), max(hi, x + 0.01))
                print(f"{ARM[j]}: {math.degrees(x):+.0f}° poza zakresem ±{math.degrees(hi):.0f}° — zakres poszerzony do pomiaru")
        self.t0 = time.monotonic()

    def read(self):
        o = self.obs = self.robot.get_observation()     # record.py zapisuje to jako obserwację (stawy + kamery)
        q5 = np.array([s * math.radians(o[f"{n}.pos"]) for s, n in zip(REAL_SIGN, ARM)])
        g = abs(o["gripper.pos"] - (100.0 - REAL_GRIP_OPEN)) / 100.0
        return q5, g, np.append(q5, g)

    def now(self):
        return time.monotonic() - self.t0

    def jaw_torque(self, g):
        return None

    def write(self, q5, tau, g):
        a = {f"{n}.pos": s * math.degrees(x) for s, n, x in zip(REAL_SIGN, ARM, q5)}
        a["gripper.pos"] = abs((100.0 - REAL_GRIP_OPEN) - float(np.clip(g, 0, 1)) * 100.0)
        self.sent = self.robot.send_action(a)           # to, co naprawdę poszło do serw (po przycięciu) = akcja w nagraniu

    def frame(self):
        return None, None

    def close(self):
        self.robot.disconnect()


def load_slots(kind):
    try:
        with open(POSES) as f:
            return {int(k): tuple(v) for k, v in json.load(f).get(kind, {}).items()}
    except FileNotFoundError:
        return {}


def save_slots(kind, slots):
    data = {}
    if os.path.exists(POSES):
        with open(POSES) as f:
            data = json.load(f)
    data[kind] = {str(k): list(v) for k, v in slots.items()}
    with open(POSES, "w") as f:
        json.dump(data, f, indent=1)


def save_rec(kind, rec, dt):
    os.makedirs(RECS, exist_ok=True)
    p = os.path.join(RECS, time.strftime(f"trasa_%Y%m%d_%H%M%S_{kind}.npz"))
    np.savez(p, q=np.array([r[0] for r in rec]), g=np.array([r[1] for r in rec]), dt=dt, joints=np.array(ARM))
    return p


def control_tick(arm, ctrl, safety, ps):
    """Pad → Controller → SafetyLayer (flymind/safety.py) → ramię. Zwraca (q6 zmierzone, flagi stawów)."""
    q5, g, q6 = arm.read()
    target, g_cmd = ctrl.tick(ps, q5, arm.dt)
    if ctrl.stopped and not safety.fault:
        safety.estop(ctrl.stopped)
    elif safety.fault and not ctrl.stopped:
        safety.clear("pad: wznowienie Menu")
    t = arm.now()
    srcs = {i: SRC for i in range(5)} | {"jaw": SRC}
    out, tau, flags, per = safety.step(Command(t, dict(enumerate(target)), arm.jaw_torque(g_cmd), srcs), q6, t, 0.0)
    if "fault" in flags and not ctrl.stopped:
        ctrl.stop(safety.fault)
    if arm.kind == "real":
        out = release_stalls(arm, ctrl, safety, out, q5, t)
    ctrl.target = out                                   # całka pada nie ucieka za ograniczenia
    arm.write(out, tau, g_cmd)
    return q6, per


STALL_ERR, STALL_MOVE, STALL_S = math.radians(3), math.radians(1), 1.0


def release_stalls(arm, ctrl, safety, out, q5, t):
    """Staw stoi (ruszył się < 1°) przez > 1 s, a cel jest > 3° dalej: przeszkoda, kraniec albo za ciężko. Cel = pozycja
    zmierzona, żeby serwo nie pchało w miejscu (grzanie, spadek napięcia → zgubione pakiety, 2026-11-07).
    Jednorazowo na zdarzenie, więc zwykłe ugięcie pod ciężarem (< 3°) nie powoduje osuwania."""
    if not hasattr(arm, "stall_t"):
        arm.stall_t, arm.stall_q = np.full(5, np.inf), q5.copy()
    over = np.abs(out - q5) > STALL_ERR
    restart = over & (np.isinf(arm.stall_t) | (np.abs(q5 - arm.stall_q) > STALL_MOVE))   # zegar od nowa, gdy staw jedzie
    arm.stall_t[restart], arm.stall_q[restart] = t, q5[restart]
    arm.stall_t[~over] = np.inf
    hit = t - arm.stall_t > STALL_S
    if hit.any():
        arm.stall_t[hit] = np.inf
        ctrl.msg = "staw nie może dojechać: " + ", ".join(ARM[i] for i in np.flatnonzero(hit)) + " — przestaję pchać"
        ctrl.events.append("limit")
        out = safety.prev = np.where(hit, q5, out)      # też w warstwie bezpieczeństwa, inaczej jej ogranicznik prędkości cofa zmianę
    return out


def make_safety(arm, max_lead=settings.DEFAULTS["max_lead"]):
    return SafetyLayer(Limits(ranges=arm.ranges, dt=arm.dt, max_lead=(max_lead,) * 5, vision_joints=(), cmd_timeout=1.0))


LABEL = {"BACK": "View", "START": "Menu", "LEFTSTICK": "L3", "RIGHTSTICK": "R3", "DPAD_UP": "D-pad ↑",
         "DPAD_DOWN": "D-pad ↓", "DPAD_LEFT": "D-pad ←", "DPAD_RIGHT": "D-pad →"}


def apply_settings(s, pad, safety):
    """settings.json → stałe control.py, pad (mapa przycisków), warstwa bezpieczeństwa, pokrętła ramienia."""
    global KP_GRIP, REAL_SIGN, REAL_GRIP_OPEN
    control.DEADZONE, control.EXPO, control.GRIP_SPEED = s["deadzone"], s["expo"], s["grip_speed"]
    control.GEARS = tuple((n, r, m) for (n, *_), (r, m) in zip(control.GEARS, s["gears"]))
    control.START_GEAR = s["start_gear"] - 1
    b = s["buttons"]
    control.KEYS = {"BACK": LABEL.get(b["stop"], b["stop"]), "START": LABEL.get(b["play"], b["play"]),
                    "RIGHTSTICK": LABEL.get(b["record"], b["record"]), "B": LABEL.get(b["save"], b["save"])}
    KP_GRIP, REAL_SIGN, REAL_GRIP_OPEN = s["grip_kp"], tuple(s["real_sign"]), float(s["real_grip_open"])
    pad.configure(s)
    safety.lim = dataclasses.replace(safety.lim, max_lead=(s["max_lead"],) * 5)


def legend(ctrl, real, s, demo=False):
    k, b = ctrl.mode == "KART", {a: LABEL.get(v, v) for a, v in s["buttons"].items()}
    trig = "LT / RT" if s["swap_triggers"] else "RT / LT"
    return [
        ("LEWA GAŁKA", ""), ("  ←→", "obrót podstawy"), ("  ↑↓", "chwytak bliżej/dalej" if k else "bark przód/tył"),
        ("PRAWA GAŁKA", ""), ("  ↑↓", "chwytak góra/dół" if k else "łokieć góra/dół"), ("  ←→", "obrót nadgarstka"),
        (f"{b['pitch_up']} / {b['pitch_down']}", "nos chwytaka góra/dół"), (trig, "zamknij / otwórz chwytak"), ("", ""),
        (b["mode"], "tryb STAWY/KART" + (" (tylko sim)" if real else "")), (b["home"], "pozycja startowa"),
        (f"{b['goto']} / {b['save']}", "jedź do slotu / zapisz slot"), (f"{b['gear_up']} {b['gear_down']}", "bieg"),
        (f"{b['slot_prev']} {b['slot_next']}", "slot 1–4"),
        (b["record"], "odrzuć pokaz" if demo else "nagrywanie trasy"),
        (b["play"], "start / koniec pokazu" if demo else "odtwórz trasę / wznów"), (b["stop"], "STOP"),
        ("", ""), ("klawiatura", "Esc wyjście" + ("" if real else ", R reset sceny")),
    ]


def draw(screen, fonts, arm, ctrl, pad, img, eye, q6, s=settings.DEFAULTS, banner=None):
    """banner = (tekst, kolor RGB) — pasek pod górną belką (record.py: stan nagrywania pokazów)."""
    f, big = fonts
    screen.fill((24, 26, 30))
    if img is not None:
        screen.blit(pygame.image.frombuffer(img.tobytes(), (W, H), "RGB"), (0, 0))
    else:   # prawdziwe ramię: zamiast obrazu wartości stawów
        for i, n in enumerate(ARM + ("gripper",)):
            v = f"{math.degrees(q6[i]):7.1f}°" if i < 5 else f"{q6[5] * 100:5.0f} %"
            screen.blit(big.render(f"{n:14s} {v}", True, (220, 220, 220)), (30, 120 + 36 * i))
    rec = "   ● NAGRYWANIE" if ctrl.rec is not None else ""
    top = f"TRYB {ctrl.mode}   BIEG {ctrl.gear + 1}/3 {control.GEARS[ctrl.gear][0]}   SLOT {ctrl.slot}{rec}"
    screen.fill((0, 0, 0), (0, 0, W, 26))
    screen.blit(f.render(top, True, (255, 90, 90) if ctrl.rec is not None else (240, 240, 240)), (8, 4))
    screen.fill((0, 0, 0), (0, H - 26, W, 26))
    screen.blit(f.render(ctrl.msg, True, (255, 210, 90)), (8, H - 22))
    if ctrl.stopped:
        s = pygame.Surface((W, 80), pygame.SRCALPHA)
        s.fill((180, 0, 0, 200))
        screen.blit(s, (0, H // 2 - 40))
        t = big.render(f"STOP — {control.KEYS['START']} wznawia", True, (255, 255, 255))
        screen.blit(t, ((W - t.get_width()) // 2, H // 2 - 14))
    x0 = W + 12
    screen.blit(f.render(f"pad: {pad.name or 'BRAK — połącz przez Bluetooth'}", True,
                         (140, 220, 140) if pad.name else (255, 120, 120)), (x0, 8))
    if banner:
        screen.fill(banner[1], (0, 26, W, 30))
        screen.blit(big.render(banner[0], True, (255, 255, 255)), (8, 27))
    for i, (a, b) in enumerate(legend(ctrl, arm.kind == "real", s, demo=banner is not None)):
        screen.blit(f.render(a, True, (150, 200, 255)), (x0, 34 + 18 * i))
        screen.blit(f.render(b, True, (220, 220, 220)), (x0 + 120, 34 + 18 * i))
    if eye is not None:
        e = pygame.transform.scale(pygame.image.frombuffer(eye.tobytes(), (eye.shape[1], eye.shape[0]), "RGB"), (192, 144))
        screen.blit(e, (W - 200, H - 26 - 152))
        screen.blit(f.render("kamera w chwytaku", True, (60, 60, 60)), (W - 200, H - 26 - 172))
    pygame.display.flip()


def main():
    ap = argparse.ArgumentParser(description="SO-101 + pad Xbox")
    ap.add_argument("--real", metavar="PORT", help="port prawdziwego ramienia (lerobot); bez tego: symulacja")
    ap.add_argument("--id", default="so101_follower", help="id kalibracji lerobot")
    a = ap.parse_args()

    pygame.init()
    screen = pygame.display.set_mode((W + PANEL, H))
    pygame.display.set_caption("SO-101 — pad Xbox")
    fonts = (pygame.font.SysFont("arialunicode,helveticaneue", 15), pygame.font.SysFont("arialunicode,helveticaneue", 26, bold=True))
    pad = Pad()
    try:
        s = settings.load()
    except (ValueError, json.JSONDecodeError) as e:
        print(f"settings.json niepoprawny ({e}) — używam domyślnych")
        s = settings.DEFAULTS
    s_mtime = os.path.getmtime(settings.PATH) if os.path.exists(settings.PATH) else None
    arm = RealArm(a.real, a.id) if a.real else SimArm()
    safety = make_safety(arm)
    apply_settings(s, pad, safety)
    q5, g, q6 = arm.read()
    bad = [f"{n}: {math.degrees(x):+.0f}° (zakres ±{math.degrees(hi):.0f}°)"
           for n, x, (lo, hi) in zip(ARM, q5, arm.ranges) if not lo <= x <= hi]
    if bad:                                             # warstwa bezpieczeństwa i tak odmówi startu — powiedz po ludzku
        arm.close()
        sys.exit("Staw poza zakresem z kalibracji: " + "; ".join(bad) + ".\nWyłącz zasilanie ramienia, przesuń ten staw "
                 "ręką trochę w stronę środka, włącz zasilanie i uruchom ponownie. Jeśli się powtarza: ponowna kalibracja.")
    ctrl = Controller(q5, g, jac=arm.jac, slots=load_slots(arm.kind))
    t_check = 0.0
    clock, acc, t_last, last_limit, quitting = pygame.time.Clock(), 0.0, time.monotonic(), 0.0, False
    try:
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    if arm.kind == "sim" or ctrl.stopped or quitting:
                        return
                    quitting, ctrl.goto = True, ctrl.home          # prawdziwe ramię: najpierw płynnie do startu
                    ctrl.msg = "wracam do startu i kończę (Esc jeszcze raz = od razu)"
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_r and arm.kind == "sim":
                    arm.reset()
                    ctrl.target, ctrl.goto, ctrl.play = arm.read()[0], None, None
                    safety.prev = None                     # warstwa bezpieczeństwa startuje od nowego pomiaru
                    ctrl.msg = "reset sceny"
            if time.monotonic() - t_check > 1.0:          # strona ustawień zapisała nowy plik → zastosuj w locie
                t_check = time.monotonic()
                m = os.path.getmtime(settings.PATH) if os.path.exists(settings.PATH) else None
                if m != s_mtime:
                    s_mtime = m
                    try:
                        s = settings.load()
                        ctrl.msg = "wczytano nowe ustawienia"
                        old = (list(REAL_SIGN), REAL_GRIP_OPEN)
                        if arm.kind == "real" and (s["real_sign"], s["real_grip_open"]) != old:
                            # zmiana znaku w locie = cel w lustrzanym kącie = skok ramienia; tylko po restarcie
                            s = {**s, "real_sign": old[0], "real_grip_open": old[1]}
                            ctrl.msg = "kierunki stawów/chwytaka zmienią się po ponownym uruchomieniu"
                        apply_settings(s, pad, safety)
                    except (ValueError, json.JSONDecodeError) as e:
                        ctrl.msg = f"błędne ustawienia, zostają stare: {e}"
            ps = pad.poll()
            if ps is None:
                ctrl.stop("brak pada")
                ps = PadState()
            if quitting:
                ps = PadState()
                if ctrl.goto is None:
                    return
            now = time.monotonic()
            acc, t_last = min(acc + now - t_last, 5 * arm.dt), now
            while acc >= arm.dt or arm.kind == "real":
                acc -= arm.dt
                try:
                    q6, per = control_tick(arm, ctrl, safety, ps)
                except ConnectionError as e:          # zgubiony pakiet z serw (spadek napięcia, kabel): STOP zamiast wywalenia
                    ctrl.stop("brak odczytu serw")
                    ctrl.msg = f"STOP: brak odczytu serw ({str(e)[-40:]}) — sprawdź zasilanie, Menu wznawia"
                    per = {}
                if any("range" in v for k, v in per.items() if k != "jaw") and now - last_limit > 0.5:
                    last_limit = now
                    ctrl.events.append("limit")
                    ctrl.msg = "kraniec: " + ", ".join(ARM[k] for k, v in per.items() if k != "jaw" and "range" in v)
                if arm.kind == "real":
                    break
            for ev in ctrl.events:
                pad.rumble(*RUMBLE[ev])
                if ev == "saved":
                    save_slots(arm.kind, ctrl.slots)
                elif ev == "rec_saved":
                    ctrl.msg += " → " + os.path.relpath(save_rec(arm.kind, ctrl.last_rec, arm.dt), HERE)
            ctrl.events.clear()
            img, eye = arm.frame()
            draw(screen, fonts, arm, ctrl, pad, img, eye, q6, s)
            clock.tick(60 if arm.kind == "sim" else round(1 / arm.dt))
    finally:
        arm.close()
        pygame.quit()


if __name__ == "__main__":
    main()
