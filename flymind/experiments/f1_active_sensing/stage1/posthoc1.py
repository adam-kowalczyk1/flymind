"""F1 Stage 1 — post-hoc, EXPLORATORY (not pre-registered). Reads results/confirm only, writes results/posthoc_confirm.json.
  A. onset phase: DATA sin vs none success in W, split by direction of the first 0.3 s of θ_s (toward / away from the target).
     Pan toward the target = −side (checked on DATA none S: sign(pan_end)·side = −1 in 400/400 units, red team).
  B. physical camera motion: lock-in amplitude of q0 = pan_t + θ_s at f, W vs S (does the tracker cancel the dither?).
  C. gated arm: S10-type lock-in on pan_t vs none in S (descriptive; S10 was frozen for sin only).
Run: .venv/bin/python -I -B flymind/experiments/f1_active_sensing/stage1/posthoc1.py"""
import glob
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cl_sense as CS  # noqa: E402

D = os.path.join(HERE, "results", "confirm")
OUT = os.path.join(HERE, "results", "posthoc_confirm.json")
rng = np.random.default_rng(9115003)  # analysis RNG pool 9 115 001–003 (§10)


def boot(a, b=None, n=4000):
    """Unit-resampled CI95 of mean(a) or mean(a) − mean(b) (b may differ in length)."""
    a = np.asarray(a, float)
    m = lambda: a[rng.integers(0, len(a), len(a))].mean() - (0 if b is None else np.asarray(b, float)[rng.integers(0, len(b), len(b))].mean())
    bs = np.array([m() for _ in range(n)])
    return [float(x) for x in np.percentile(bs, [2.5, 97.5])]


rows = {"toward": [], "away": []}
q0amp = {"W": [], "S": []}
gated = {"W": [], "S": []}
for j in sorted(glob.glob(os.path.join(D, "u*.json"))):
    r = {(x["fam"], x["motion"], x["rng"]): x for x in json.load(open(j))}
    z = np.load(j[:-4] + "npz")
    x = r[("DATA", "sin", "W")]
    th = z["DATA|sin|W|th"]
    early = th[:30].mean() * -x["side"]                       # > 0: first motion turns the camera toward the target
    rows["toward" if early > 0 else "away"].append((r[("DATA", "none", "W")]["success"], x["success"]))
    f, phi = x["f"], x["phi"]
    for g in ("W", "S"):
        q0 = z[f"DATA|sin|{g}|pan"].astype(float) + z[f"DATA|sin|{g}|th"]
        q0amp[g].append((math.degrees(CS.lockin(q0, f, phi)), math.degrees(CS.lockin(z[f"DATA|sin|{g}|th"].astype(float), f, phi))))
        gated[g].append(math.degrees(CS.lockin(z[f"DATA|gated|{g}|pan"].astype(float), f, phi))
                        - math.degrees(CS.lockin(z[f"DATA|none|{g}|pan"].astype(float), f, phi)))

out = dict(label="EXPLORATORY post hoc — not part of the frozen decision rules", n_units=sum(map(len, rows.values())))
A = {}
for k, v in rows.items():
    v = np.array(v, float)
    d = v[:, 1] - v[:, 0]
    A[k] = dict(n=len(v), none=float(v[:, 0].mean()), sin=float(v[:, 1].mean()), delta=float(d.mean()), ci95=boot(d))
dt, da = (np.array(rows[k], float) for k in ("toward", "away"))
A["toward_minus_away"] = dict(est=float((dt[:, 1] - dt[:, 0]).mean() - (da[:, 1] - da[:, 0]).mean()),
                              ci95=boot(dt[:, 1] - dt[:, 0], da[:, 1] - da[:, 0]))
out["A_onset_direction"] = A
out["B_camera_motion_deg"] = {g: dict(q0_lockin=float(np.mean([a for a, _ in v])), theta_s_lockin=float(np.mean([b for _, b in v])),
                                      fraction_kept=float(np.mean([a for a, _ in v]) / np.mean([b for _, b in v])))
                              for g, v in q0amp.items()}
out["C_gated_s10_deg"] = {g: dict(est=float(np.mean(v)), ci95=boot(v)) for g, v in gated.items()}
with open(OUT, "w") as fh:
    json.dump(out, fh, indent=1)
print(json.dumps(out, indent=1))

if __name__ == "__main__":
    assert out["n_units"] == 400, out["n_units"]
