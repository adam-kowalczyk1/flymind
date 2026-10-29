import sys
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import numpy as np, PIL.Image as I
from so101 import SO101Sim
S = "/private/tmp/claude-501/-Users-admin-so101-fly-project/6454b16d-a7f4-423a-a824-4d37dc6a0832/scratchpad/"
Q = np.array([0, 0, 0, 0, 0, 0.93]); sim = SO101Sim(); H, W = 96, 128
tanY = np.tan(np.radians(70) / 2)
for n, (dx, dy) in enumerate(((0, 0), (-0.04, 0), (0, 0.04))):
    k = sim.fk(Q); R = k["eye_R"]
    sim.reset(Q, ball_pos=k["eye"] + 0.25 * k["eye_forward"] + dx * R[:, 0] + dy * R[:, 1])
    img = sim.observe().frame.image; g = img.astype(int)
    rr, cc = np.nonzero((g[..., 1] > g[..., 0] + 60) & (g[..., 1] > g[..., 2] + 60))
    print((dx, dy), "n", rr.size, "centroid u,v", cc.mean() + .5, rr.mean() + .5, "pred",
          W / 2 * (1 + dx / 0.25 / (tanY * W / H)), H / 2 * (1 - dy / 0.25 / tanY))
    I.fromarray(np.kron(img, np.ones((4, 4, 1), np.uint8))).save(S + f"t3_{n}.png")
