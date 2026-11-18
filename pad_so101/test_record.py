"""Test nagrywania pokazów bez ramienia i bez kamery: ~/miniforge3/envs/lerobot/bin/python pad_so101/test_record.py

Przechodzi przez Session (pad → Controller → bezpieczeństwo → FakeArm → LeRobotDataset) w tymczasowym katalogu:
zapis, odrzucenie R3, odrzucenie przez STOP, za krótki pokaz; potem czyta nagranie jak lerobot-train."""
import math
import os
import sys
import tempfile

sys.dont_write_bytecode = True
os.environ["HF_LEROBOT_HOME"] = tempfile.mkdtemp(prefix="pad_rec_test_")   # przed importem lerobot

import numpy as np

import record
import run
from control import PadState


class SynthCam:
    height, width = 480, 640

    def __init__(self):
        self.i = 0

    def read_latest(self):
        self.i += 1
        return np.full((480, 640, 3), self.i % 255, np.uint8)

    def disconnect(self):
        pass


def test_session():
    fps = 30
    arm = record.FakeArm()
    arm.dt = 1 / fps
    arm.cams = {"front": SynthCam()}
    arm.observation_features |= {"front": (480, 640, 3)}
    ds = record.open_dataset("local/test", arm, fps, resume=False)
    safety = run.make_safety(arm)
    q5, g, _ = arm.read()
    ctrl = run.Controller(q5, g)
    sess = record.Session(arm, ctrl, safety, ds, "test task", episodes=5, max_s=60, fps=fps)

    def hold(n, **kw):
        for _ in range(n):
            sess.tick(PadState(**kw))

    def press(btn):
        hold(1, buttons=frozenset({btn}))
        hold(1)

    press("START"); hold(45, lx=0.8, rt=0.6); press("START")      # pokaz 1: zapisany
    assert sess.n == 1 and not sess.rec, ctrl.msg
    press("START"); hold(40, ly=0.7); press("RIGHTSTICK")         # R3 = odrzucony
    assert sess.n == 1 and not sess.rec
    press("START"); hold(40); press("BACK")                       # STOP = odrzucony
    assert sess.n == 1 and not sess.rec and ctrl.stopped
    press("START")                                                # Menu po STOP = wznów, nie start pokazu
    assert not ctrl.stopped and not sess.rec
    press("START"); hold(5); press("START")                       # < 1 s = odrzucony
    assert sess.n == 1 and "krótki" in ctrl.msg
    cam = arm.cams["front"]
    real_read = cam.read_latest
    press("START"); hold(20)                                      # kamera gubi obraz w trakcie pokazu (np. telefon)
    cam.read_latest = lambda: (_ for _ in ()).throw(TimeoutError("latest frame is too old"))
    hold(3)
    assert sess.n == 1 and not sess.rec and ctrl.stopped, ctrl.msg
    press("START")                                                # bez obrazu Menu nie wznawia
    assert ctrl.stopped
    cam.read_latest = real_read
    press("START")                                                # obraz wrócił → Menu wznawia
    assert not ctrl.stopped and not sess.rec
    press("START"); hold(60, rx=-0.9, lt=1.0); press("START")     # pokaz 2
    assert sess.n == 2
    ds.finalize()

    from lerobot.datasets import LeRobotDataset
    d = LeRobotDataset("local/test")
    assert d.meta.total_episodes == 2, d.meta.total_episodes
    assert d.num_frames == 47 + 62, d.num_frames                 # start..koniec włącznie z taktem wciśnięcia
    names = d.features["action"]["names"]
    assert names == [f"{m}.pos" for m in record.MOTORS], names
    assert d.features["observation.state"]["names"] == names
    fr = d[10]
    assert tuple(fr["observation.images.front"].shape) == (3, 480, 640), fr["observation.images.front"].shape
    pan = [float(d[i]["action"][0]) for i in range(47)]
    assert pan[-1] - pan[0] > 5, pan                              # lewa gałka w prawo → podstawa się obróciła (stopnie)
    a, o = np.array([d[i]["action"] for i in range(46)]), np.array([d[i + 1]["observation.state"] for i in range(46)])
    assert np.abs(a - o).max() < 1e-3                             # FakeArm wykonuje komendę → następna obserwacja = akcja
    print(f"nagrywanie OK: 2 pokazy, {d.num_frames} klatek, wideo {fr['observation.images.front'].shape}, "
          f"{os.environ['HF_LEROBOT_HOME']}")


def test_stall():
    """Nadgarstek blokuje się na przeszkodzie (2026-11-07): po > 1 s pchania cel wraca do pozycji zmierzonej."""
    class StuckArm(record.FakeArm):
        t = 0.0

        def now(self):
            return self.t

        def write(self, q5, tau, g):
            super().write(q5, tau, g)
            self.q[4] = min(self.q[4], 0.1)                 # wrist_roll nie przejdzie dalej niż 0,1 rad
            self.t += self.dt

    arm = StuckArm()
    arm.dt, arm.cams = 1 / 30, {}
    safety = run.make_safety(arm)
    q5, g, _ = arm.read()
    ctrl = run.Controller(q5, g)
    for _ in range(90):                                     # 3 s prawa gałka w prawo = nadgarstek pcha w przeszkodę
        run.control_tick(arm, ctrl, safety, PadState(rx=1.0))
        assert ctrl.target[4] - arm.q[4] < math.radians(15)
    assert "nie może dojechać" in ctrl.msg, ctrl.msg
    for _ in range(45):                                     # puszczona gałka → w ciągu ~1 s przestaje pchać
        run.control_tick(arm, ctrl, safety, PadState())
    assert abs(ctrl.target[4] - arm.q[4]) < math.radians(3), (ctrl.target[4], arm.q[4])
    ok = arm.q.copy()
    for _ in range(60):                                     # stawy, które jadą normalnie, nie są ruszane
        run.control_tick(arm, ctrl, safety, PadState(lx=0.5))
    assert arm.q[0] > ok[0] + 0.15 and "pan" not in ctrl.msg, (arm.q[0], ok[0], ctrl.msg)
    print("blokada stawu OK")


if __name__ == "__main__":
    test_session()
    test_stall()
