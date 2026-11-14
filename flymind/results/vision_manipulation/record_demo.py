"""Nagranie: CIĄGŁA seria 8 przedmiotów z kolejką, percept z kamery na chwytaku, wybrane ramię (np. sieć wzrok + dotyk).
Te same przedmioty i ziarno (4242) co pokaz etapu dotyku. Uruchom z katalogu tymczasowego:
  .venv/bin/python -I -B flymind/results/vision_manipulation/record_demo.py E_vis_touch 4242 demo_E_vis_touch_v2"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import object_handling as oh  # noqa: E402
import vision_manipulation as vm  # noqa: E402
from PIL import Image  # noqa: E402

ITEMS = [("cube_M", "mid"), ("sphere", "hard_slick"), ("long", "heavy"), ("cyl", "hard_grip"), ("cube_S", "light"),
         ("flat", "mid"), ("wedge", "mid"), ("cube_L", "light")]
arm, seed, tag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
out = os.path.join(vm.OUT, "media", tag)
os.makedirs(os.path.dirname(out), exist_ok=True)
if any(os.path.exists(out + e) for e in (".json", ".mp4", "_sheet.png")):
    sys.exit(f"istnieje już {out}.* — wybierz inny tag")
factory, drv, cal = vm.make(arm)
frames = tempfile.mkdtemp()
r = vm.run_series(ITEMS, seed, factory, drv, record=frames)
r.pop("lat")
fs = sorted(os.listdir(frames))
subprocess.run(["/Users/admin/miniforge3/bin/ffmpeg", "-loglevel", "error", "-framerate", "25", "-i",
                os.path.join(frames, "f%05d.png"), "-pix_fmt", "yuv420p", out + ".mp4"], check=True)
im = [Image.open(os.path.join(frames, fs[int(len(fs) * k / 9)])) for k in range(9)]
W, H = im[0].size
sheet = Image.new("RGB", (3 * W, 3 * H))
for k, x in enumerate(im):
    sheet.paste(x, ((k % 3) * W, (k // 3) * H))
sheet.resize((3 * W // 2, 3 * H // 2)).save(out + "_sheet.png")
summ = oh.summarize([r])
with open(out + ".json", "x") as f:
    json.dump(dict(tag=tag, arm=arm, jaw_source=vm.ARMS[arm][0], pan_source=vm.ARMS[arm][1], seed=seed, items=ITEMS, frames=len(fs),
                   calibration=cal, code=oh.code_state(), code_vision=vm.code_vision(), summary=summ, run=r), f, indent=1, default=float)
print(f"{arm}: {summ['success']} w pudełku, T_sim {r['T_sim']:.1f} s, stop {r['stopped_by']}, percepty {len(r['vision'])}, "
      f"losy {[(o['shape'] + '/' + o['material'], o['final']) for o in r['objects']]}")
print("źródła komend:", {k: v["ticks"] for k, v in r["safety_stats"].items()})
