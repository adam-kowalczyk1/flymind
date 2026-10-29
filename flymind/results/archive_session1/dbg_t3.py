import sys
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import numpy as np
from so101 import SO101Sim
S = "/private/tmp/claude-501/-Users-admin-so101-fly-project/6454b16d-a7f4-423a-a824-4d37dc6a0832/scratchpad/"
Q = np.array([0, 0, 0, 0, 0, 0.93])
sim = SO101Sim()
k = sim.fk(Q)
print("eye", k["eye"].round(3), "fwd", k["eye_forward"].round(3), "R", k["eye_R"].round(2).tolist())
print("gripperframe", k["gripperframe"].round(3))
b = k["eye"] + 0.25 * k["eye_forward"]
sim.reset(Q, ball_pos=b)
print("ball", b.round(3), "ball qpos", sim.d.qpos[sim.m.joint("ball").qposadr[0]:][:3].round(3))
img = sim.observe().frame.image
print("img mean", img.mean((0, 1)).round(1), "min", img.min(), "max", img.max())
g = img.astype(int)
print("max G-R", (g[..., 1] - g[..., 0]).max(), "max G-B", (g[..., 1] - g[..., 2]).max())
import PIL.Image as I
I.fromarray(np.kron(img, np.ones((4, 4, 1), np.uint8))).save(S + "t3_center.png")
