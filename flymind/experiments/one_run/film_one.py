"""Film pełnego przebiegu (tempo rzeczywiste, 25 kl./s, bez wyolbrzymiania ruchu). film_one.py DIR_RAW OUT.mp4"""
import subprocess, sys
import numpy as np
sys.dont_write_bytecode = True
import one_run as R  # noqa: E402
import plot_one as PL  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import mujoco  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

z, FF = PL.z, "/Users/admin/miniforge3/bin/ffmpeg"
W, H = 1280, 900
TOP = 470
fig, ax = plt.subplots(4, 1, figsize=(W / 100, (H - TOP) / 100), dpi=100, sharex=True, facecolor="#fcfcfb", gridspec_kw=dict(height_ratios=[0.8, 0.8, 1, 1.3], hspace=0.18))


tmp = plt.figure().add_subplot()                                            # wiersz „dotyk” nie mieści się w filmie (jest na wykresie i na pasku bodźców)
PL.rows(fig, [ax[0], ax[1], tmp, ax[2], ax[3]])
ax[3].set_xlabel("czas próby [s]")
fig.subplots_adjust(left=0.085, right=0.925, top=0.97, bottom=0.11)
fig.canvas.draw()
base = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
x0, x1 = (ax[3].transData.transform((v, 0))[0] for v in (0, 45))
y0, y1 = base.shape[0] - ax[0].get_window_extent().y1, base.shape[0] - ax[3].get_window_extent().y0
cam = R.Cam()
m = cam.m
ref = cam.look(z['q_all'][2100], *z['ball'][2100])[0].copy()
m.geom_rgba[m.geom('ball').id, 3] = 0.0                                     # zielona piłka z modelu (zaparkowana) — tylko w filmie ukryta
assert (cam.look(z['q_all'][2100], *z['ball'][2100])[0] == ref).all(), 'piłka była w kadrze nadgarstka'
m.vis.global_.offwidth, m.vis.global_.offheight = 800, 480
r = mujoco.Renderer(m, TOP, 780)
ext = mujoco.MjvCamera()
ext.type, ext.lookat[:], ext.distance, ext.azimuth, ext.elevation = mujoco.mjtCamera.mjCAMERA_FREE, [0.16, 0.0, 0.14], 0.72, 118, -14
font, big = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 17), ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 22)
ff = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "25", "-i", "-", "-pix_fmt", "yuv420p", "-vcodec", "libx264", "-crf", "21", "-movflags", "+faststart", sys.argv[2]], stdin=subprocess.PIPE)
still = np.degrees(np.abs(z["dq"])).max(1) / .01 < 0.05
for i in range(0, R.N, 4):
    q6, (side, dist) = z["q_all"][i], z["ball"][i]
    wrist, _ = cam.look(q6, side, dist)
    pos = cam.E0 + cam.R0[:, 0] * side + cam.f0 * dist
    m.vis.headlight.ambient[:], m.vis.headlight.diffuse[:] = 0.25, 0.3             # widok zewnętrzny ciemniej; obraz nadgarstka już zrobiony
    r.update_scene(cam.k, camera=ext)
    s = r.scene
    items = [(pos, R.S0.R_BALL, (.1, .1, .1, 1))]
    for k, site in enumerate(("cs_fixed", "cs_moving")):
        if z["felt"][i, k] > 0.2:
            items.append((cam.k.site(site).xpos.copy(), 0.014, (.16, .47, .84, .9) if k == 0 else (.92, .41, .2, .9)))
    for p, rad, c in items:
        mujoco.mjv_initGeom(s.geoms[s.ngeom], mujoco.mjtGeom.mjGEOM_SPHERE, np.array([rad, 0, 0]), p, np.eye(3).ravel(), np.array(c, np.float32))
        s.ngeom += 1
    f = np.full((H, W, 3), 252, np.uint8)
    v = r.render().copy()
    m.vis.headlight.ambient[:], m.vis.headlight.diffuse[:] = 0.6, 0.4
    v[(v == 0).all(-1)] = (226, 229, 233)
    f[:TOP, :780] = v
    im = Image.fromarray(f)
    im.paste(Image.fromarray(wrist).resize((460, 288), Image.NEAREST).convert("RGB"), (800, 34))
    dr = ImageDraw.Draw(im)
    dr.text((800, 8), "obraz z kamery nadgarstka (wejście oka)", font=font, fill=(82, 81, 78))
    a = np.degrees(q6[1:4] - z["q0"][1:4])
    dr.text((800, 334), f"t = {i * .01:4.1f} s".replace(".", ","), font=big, fill=(11, 11, 11))
    dr.text((930, 334), "ruch z sieci" if not still[i:i + 4].all() else "bezruch", font=big, fill=(11, 11, 11) if not still[i:i + 4].all() else (130, 128, 122))
    dr.text((800, 372), f"bark {a[0]:+.2f}°   łokieć {a[1]:+.2f}°   nadgarstek {a[2] + 0.0:+.2f}°".replace(".", ","), font=font, fill=(11, 11, 11))
    dr.text((800, 400), f"oko L/P {z['loom'][i, 0]:.0f}/{z['loom'][i, 1]:.0f} mV    dotyk A0 {z['felt'][i, 0]:.1f} N  A1 {z['felt'][i, 1]:.1f} N".replace(".", ","), font=font, fill=(11, 11, 11))
    dr.text((800, 430), "podstawa, obrót i szczęka: trzymane klasycznie", font=font, fill=(82, 81, 78))
    g = base.copy()
    c = int(round(x0 + (x1 - x0) * i * .01 / 45))
    g[int(y0):int(y1), max(0, c - 1):c + 1] = (11, 11, 11)
    f = np.asarray(im).copy()
    f[TOP:] = g[:H - TOP, :W]
    ff.stdin.write(f.tobytes())
    if i in (700, 1250, 2100, 3650):
        Image.fromarray(f).save(sys.argv[2].replace(".mp4", f"_{i // 100}s.png"))
ff.stdin.close()
print("ffmpeg", ff.wait())
