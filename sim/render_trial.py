"""Klatki z próby Etapu 3:  python render_trial.py seed t1,t2,... plik.png  (lub .mp4 z ffmpeg)"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mujoco
import numpy as np

from circuit import FlyController
from stage3 import run_trial

seed = int(sys.argv[1])
times = [float(x) for x in sys.argv[2].split(",")]
out = sys.argv[3]
frames, R = [], {}


def cb(m, d):
    if "r" not in R:
        R["r"] = mujoco.Renderer(m, 360, 480)
        R["cam"] = mujoco.MjvCamera()
        R["opt"] = mujoco.MjvOption()
        R["opt"].sitegroup[:] = 1
    if times and d.time >= times[0] - 1e-9:
        times.pop(0)
        cam = R["cam"]
        cam.lookat[:] = d.site("grasp").xpos
        cam.distance, cam.azimuth, cam.elevation = 0.35, 160, -35
        R["r"].update_scene(d, camera=cam, scene_option=R["opt"])
        frames.append((d.time, R["r"].render().copy()))


run_trial(seed, FlyController(seed=seed), on_step=cb)
fig, ax = plt.subplots(1, len(frames), figsize=(4 * len(frames), 3.4))
for a, (t, im) in zip(np.atleast_1d(ax), frames):
    a.imshow(im)
    a.set_title(f"t = {t:.2f} s")
    a.axis("off")
fig.tight_layout()
fig.savefig(out, dpi=100)
print(out)
