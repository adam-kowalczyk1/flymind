"""pad_so101/record.py — nagrywanie pokazów padem na PRAWDZIWYM SO-101 do formatu LeRobot (nauka ACT / SmolVLA).

  ~/miniforge3/envs/lerobot/bin/python pad_so101/record.py --port /dev/tty.usbmodemXXXX --task "Pick up the cube and put it in the box"
  ~/miniforge3/envs/lerobot/bin/python pad_so101/record.py --fake --task "test"     # bez ramienia: ćwiczenie i sprawdzenie zapisu

Sterowanie jak w run.py (PLAN.md). Na czas nagrywania dwie akcje zmieniają znaczenie:
  Menu (akcja „play")   = start pokazu / koniec i zapis pokazu   (po STOP: wznów, jak zawsze)
  R3   (akcja „record") = odrzuć bieżący pokaz
STOP w trakcie pokazu = pokaz odrzucony. Zapisuje się: obraz z kamer + zmierzone stawy (obserwacja) i komenda wysłana do serw
(akcja) — w tym samym formacie co lerobot-record, więc dalej działa zwykłe lerobot-train / lerobot-rollout. Instrukcja: NAGRYWANIE.md.
Źródło komend: classical:pad — to pokazy człowieka, nie mucha.
"""
import sys

sys.dont_write_bytecode = True
import argparse
import dataclasses
import json
import math
import os
import time

import numpy as np
import pygame

import run
import settings
from control import ARM, Controller, PadState
from pad import Pad

MOTORS = ARM + ("gripper",)


class FakeArm:
    """Bez ramienia: „serwa" wykonują komendę od razu. Kamery są prawdziwe. Do ćwiczeń i testu zapisu."""
    kind, dt, jac = "real", 1 / 30, None

    def __init__(self, cameras=None):
        from lerobot.cameras import make_cameras_from_configs
        self.cams = make_cameras_from_configs(cameras or {})
        for c in self.cams.values():
            c.connect()
        self.ranges = np.array([[-2.0, 2.0]] * 5 + [[0.0, 1.0]])
        self.q = np.array(run.HOME_Q[:5] + (0.5,))
        self.action_features = {f"{m}.pos": float for m in MOTORS}
        self.observation_features = self.action_features | {k: (c.height, c.width, 3) for k, c in self.cams.items()}
        self.t0 = time.monotonic()

    def read(self):
        self.obs = self._deg(self.q[:5], self.q[5]) | {k: c.read_latest() for k, c in self.cams.items()}
        return self.q[:5].copy(), self.q[5], self.q.copy()

    def write(self, q5, tau, g):
        self.q = np.append(q5, np.clip(g, 0, 1))
        self.sent = self._deg(self.q[:5], self.q[5])

    @staticmethod
    def _deg(q5, g):
        return {f"{n}.pos": math.degrees(x) for n, x in zip(ARM, q5)} | {"gripper.pos": float(g) * 100}

    def now(self):
        return time.monotonic() - self.t0

    def jaw_torque(self, g):
        return None

    def close(self):
        for c in self.cams.values():
            c.disconnect()


class Session:
    """Pad → ramię (run.control_tick: Controller + warstwa bezpieczeństwa) + nagrywanie pokazów do LeRobotDataset."""

    def __init__(self, arm, ctrl, safety, ds, task, episodes, max_s, fps, busy=lambda msg: None):
        self.arm, self.ctrl, self.safety, self.ds, self.task = arm, ctrl, safety, ds, task
        self.episodes, self.max_frames, self.fps, self.busy = episodes, int(max_s * fps), fps, busy
        self.n = ds.meta.total_episodes          # przy --resume liczymy od tego, co już jest
        self.rec, self.frames, self.prev, self.q6 = False, 0, frozenset(), np.zeros(6)

    def tick(self, ps):
        b = ps.buttons
        pressed, self.prev = b - self.prev, b
        mine = {"RIGHTSTICK"} | (set() if self.ctrl.stopped else {"START"})   # po STOP Menu wznawia, jak w run.py
        if not self.ctrl.stopped:
            if "START" in pressed:
                self.save() if self.rec else self.start()
            if "RIGHTSTICK" in pressed and self.rec:
                self.discard("pokaz odrzucony")
        try:
            q6, per = run.control_tick(self.arm, self.ctrl, self.safety, dataclasses.replace(ps, buttons=b - mine))
        except (TimeoutError, RuntimeError, ConnectionError) as e:
            # kamera bez nowej klatki > 0,5 s (np. połączenie na iPhonie) albo błąd odczytu serw: nic nie wysyłamy
            # (serwa trzymają ostatni cel), STOP; Menu wznawia dopiero, gdy odczyt znowu działa
            if self.rec:
                self.discard("brak odczytu — pokaz odrzucony")
            self.ctrl.stop("brak obrazu/odczytu")
            self.ctrl.msg = f"STOP: {str(e)[:70]} — Menu wznawia"
            return self.q6, {}
        self.q6 = q6
        if self.rec:
            if self.ctrl.stopped:
                self.discard("STOP — pokaz odrzucony")
            else:
                self.add_frame()
                if self.frames >= self.max_frames:
                    self.save()
        return q6, per

    def add_frame(self):
        from lerobot.utils.feature_utils import build_dataset_frame
        f = self.ds.features
        self.ds.add_frame(build_dataset_frame(f, self.arm.obs, "observation") | build_dataset_frame(f, self.arm.sent, "action")
                          | {"task": self.task})
        self.frames += 1

    def start(self):
        if self.n >= self.episodes:
            self.ctrl._say(f"masz już {self.n} pokazów — Esc kończy")
            return
        self.rec, self.frames = True, 0
        self.ctrl._say(f"● nagrywam pokaz {self.n + 1} — Menu kończy i zapisuje, R3 odrzuca", "tick")

    def save(self):
        if self.frames < self.fps:               # krótszy niż 1 s = przypadkowe wciśnięcie
            return self.discard("za krótki (< 1 s) — odrzucony")
        self.busy(f"zapisuję pokaz {self.n + 1}…")
        self.ds.save_episode()
        self.n, self.rec, self.frames = self.n + 1, False, 0
        self.ctrl._say(f"zapisano pokaz {self.n}/{self.episodes} — ułóż scenę i Menu = następny", "rec_saved")

    def discard(self, why):
        self.ds.clear_episode_buffer()
        self.rec, self.frames = False, 0
        self.ctrl._say(why, "tick")

    def banner(self, real_fps):
        slow = f"   ⚠ tylko {real_fps:.0f} kl./s" if real_fps < 0.9 * self.fps else ""
        if self.rec:
            return f"● NAGRYWAM pokaz {self.n + 1}/{self.episodes}   {self.frames / self.fps:4.1f} s{slow}", (190, 30, 30)
        return f"pokazy: {self.n}/{self.episodes} zapisane   ·   Menu = start pokazu{slow}", (40, 70, 130)


def parse_cam(spec, fps):
    """'front=0' albo 'front=1@1280x720' → (nazwa, konfiguracja kamery OpenCV lerobot)."""
    from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
    name, _, rest = spec.partition("=")
    idx, _, size = rest.partition("@")
    w, h = map(int, size.split("x")) if size else (640, 480)
    return name, OpenCVCameraConfig(index_or_path=int(idx), fps=fps, width=w, height=h)


def open_dataset(repo_id, arm, fps, resume):
    from lerobot.datasets import LeRobotDataset
    from lerobot.utils.constants import HF_LEROBOT_HOME
    from lerobot.utils.feature_utils import hw_to_dataset_features
    src = getattr(arm, "robot", arm)
    feats = hw_to_dataset_features(src.action_features, "action") | hw_to_dataset_features(src.observation_features, "observation")
    ncam = sum(isinstance(v, tuple) for v in src.observation_features.values())
    root = HF_LEROBOT_HOME / repo_id
    if resume:
        ds = LeRobotDataset.resume(repo_id, image_writer_threads=4 * ncam)
        if {k: v["shape"] for k, v in feats.items()} != {k: tuple(ds.features[k]["shape"]) for k in feats if k in ds.features}:
            sys.exit(f"Nagranie {root} ma inne kamery/stawy niż teraz — użyj innej nazwy (--name).")
        return ds
    if root.exists():
        sys.exit(f"Nagranie {root} już istnieje: dopisz pokazy z --resume albo podaj inną --name.")
    return LeRobotDataset.create(repo_id, fps, features=feats, robot_type="so101_follower", use_videos=True,
                                 image_writer_threads=4 * ncam)


def main():
    ap = argparse.ArgumentParser(description="Nagrywanie pokazów padem na SO-101 (format LeRobot)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--port", help="port ramienia, np. /dev/tty.usbmodem5A7A0185001 (lerobot-find-port)")
    g.add_argument("--fake", action="store_true", help="bez ramienia (ćwiczenie, test zapisu)")
    ap.add_argument("--id", default="so101_follower", help="id kalibracji lerobot")
    ap.add_argument("--task", required=True, help="opis zadania, najlepiej po angielsku (SmolVLA czyta ten tekst)")
    ap.add_argument("--name", default="so101_pad", help="nazwa nagrania → ~/.cache/huggingface/lerobot/local/<name>")
    ap.add_argument("--resume", action="store_true", help="dopisz pokazy do istniejącego nagrania")
    ap.add_argument("--episodes", type=int, default=50)
    ap.add_argument("--max-s", type=float, default=60, help="pokaz dłuższy niż tyle sekund zapisze się sam")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--cam", action="append", help="kamera: nazwa=indeks[@SZERxWYS], np. front=0 (można kilka razy; "
                                                    "indeksy: lerobot-find-cameras opencv). Domyślnie front=0")
    ap.add_argument("--no-cam", action="store_true", help="bez kamer (tylko test; ACT/SmolVLA potrzebują obrazu)")
    a = ap.parse_args()

    cams = {} if a.no_cam else dict(parse_cam(c, a.fps) for c in (a.cam or ["front=0"]))
    pygame.init()
    screen = pygame.display.set_mode((run.W + run.PANEL, run.H))
    pygame.display.set_caption("SO-101 — nagrywanie pokazów padem")
    fonts = (pygame.font.SysFont("arialunicode,helveticaneue", 15), pygame.font.SysFont("arialunicode,helveticaneue", 22, bold=True))
    pad = Pad()
    try:
        s = settings.load()
    except (ValueError, json.JSONDecodeError) as e:
        print(f"settings.json niepoprawny ({e}) — używam domyślnych")
        s = settings.DEFAULTS
    arm = FakeArm(cams) if a.fake else run.RealArm(a.port, a.id, cams)
    arm.dt = 1 / a.fps                           # sterowanie w takt nagrania
    sess = None
    try:
        ds = open_dataset(f"local/{a.name}", arm, a.fps, a.resume)
        safety = run.make_safety(arm)
        run.apply_settings(s, pad, safety)
        q5, g, q6 = arm.read()
        ctrl = Controller(q5, g, jac=None, slots=run.load_slots("real"))
        ctrl.msg = "gotowe — Menu zaczyna pokaz"
        img = None

        def frame(banner):
            nonlocal img
            if arm.obs.get(next(iter(cams), None)) is not None:
                import cv2
                img = cv2.resize(arm.obs[next(iter(cams))], (run.W, run.H))
            run.draw(screen, fonts, arm, ctrl, pad, img, None, q6, s, banner=banner)

        sess = Session(arm, ctrl, safety, ds, a.task, a.episodes, a.max_s, a.fps,
                       busy=lambda m: frame((m, (120, 90, 20))))
        clock, quitting, t_last, real_fps = pygame.time.Clock(), False, time.monotonic(), float(a.fps)
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    if sess.rec:
                        sess.discard("wyjście — pokaz odrzucony")
                    if a.fake or ctrl.stopped or quitting:
                        return
                    quitting, ctrl.goto = True, ctrl.home          # najpierw płynnie do startu
                    ctrl.msg = "wracam do startu i kończę (Esc jeszcze raz = od razu)"
            ps = pad.poll()
            if ps is None:
                ctrl.stop("brak pada")
                ps = PadState()
            if quitting:
                ps = PadState()
                if ctrl.goto is None:
                    return
            q6, per = sess.tick(ps)
            for ev in ctrl.events:
                pad.rumble(*run.RUMBLE[ev])
                if ev == "saved":
                    run.save_slots("real", ctrl.slots)
            ctrl.events.clear()
            now = time.monotonic()
            real_fps, t_last = 0.9 * real_fps + 0.1 / max(now - t_last, 1e-3), now
            frame(sess.banner(real_fps))
            clock.tick(a.fps)
    finally:
        if sess is not None:
            if sess.rec:
                sess.ds.clear_episode_buffer()
            sess.ds.finalize()
            print(f"\nZapisanych pokazów: {sess.n}. Nagranie: ~/.cache/huggingface/lerobot/local/{a.name}\n"
                  f"Podgląd:  lerobot-dataset-viz --repo-id local/{a.name} --episode-index 0\n"
                  f"Nauka:    zobacz pad_so101/NAGRYWANIE.md")
        arm.close()
        pygame.quit()


if __name__ == "__main__":
    main()
