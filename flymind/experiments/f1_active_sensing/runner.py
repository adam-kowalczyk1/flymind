"""F1 Stage 0 runner (open loop, PROTOCOL r2). One job = one unit u: draw its stimulus (rho, |az|, k, φ), then for every condition
render left / right / no-target on range D and left / right on range C, add the unit's pixel noise, run the frozen encoder, store the
g and LIN streams (controls are computed in analysis), and run the SNN networks of that condition on range D + no target.
Output per unit: u<id>.feather (SNN rows) and u<id>.npz (streams, motion records), mode "x", under results/<stage>/.
Run: .venv/bin/python -I -B flymind/experiments/f1_active_sensing/runner.py --stage {pilot1|pilot2|confirm|robust} --manifest M.json
     --manifest-sha256 <sha of M.json> [--workers 4]   (rendering is GL-bound at ~240 frames/s in total; more workers do not help)
"""
import argparse
import hashlib
import json
import math
import multiprocessing as mp
import os
import sys
import time
import zlib

import numpy as np
import pandas as pd

if __name__ == "__main__" and not sys.flags.dont_write_bytecode:
    sys.exit("run with python -B")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stimulus as ST  # noqa: E402
import systems as SY  # noqa: E402

PROTO = json.load(open(os.path.join(HERE, "protocol.json")))
FS, AS = PROTO["sin_f_hz"], PROTO["sin_A_deg"]
NETS = ("DATA", "B1", "SWS")


def cname(c):
    k, f, A = c
    return {"stat": "stat", "jshuf": f"jshuf_A{A:g}", "jrms": f"jrms_A{A:g}"}.get(k, f"{k}_f{f:g}_A{A:g}")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def plan(stage):
    """Returns (conditions → networks, conditions rendered on range C, units, b1 seeds, sws seeds, variants {name: overrides}, file tag).
    PROTOCOL r3.1: pilot in two parts (pilot1: stat + 16 sin → R1; pilot2: J_shuf, J_rms, J_vel at (f*, A*)); range C only where needed."""
    key = lambda f, A: [("stat", 0.0, 0.0), ("sin", f, A), ("jshuf", f, A), ("jrms", 0.0, A), ("jvel", f, A)]
    if stage in ("pilot1", "pilot2"):
        P = PROTO["pilot"]
        if stage == "pilot1":
            conds, tag = [("stat", 0.0, 0.0)] + [("sin", f, A) for f in FS for A in AS], ""
        else:
            r1 = json.load(open(os.path.join(HERE, "pilot_r1.json")))
            conds, tag = key(r1["f_star"], r1["A_star"])[2:], "p2"
        return {c: NETS for c in conds}, set(conds), list(range(P["units"][0], P["units"][1] + 1)), \
            list(range(P["b1_instances"][0], P["b1_instances"][1] + 1)), \
            list(range(P["sws_instances"][0], P["sws_instances"][1] + 1)), {tag: {}}
    cp = json.load(open(os.path.join(HERE, "confirm_params.json")))
    f, A = cp["f_star"], cp["A_star"]
    k = key(f, A)
    C = PROTO[stage]
    b1, sws = (list(range(C[x][0], C[x][1] + 1)) for x in ("b1_instances", "sws_instances"))
    if stage == "confirm":
        conds = {c: NETS if c in k else ("DATA",) for c in k[:1] + [("sin", g, a) for g in FS for a in AS] + k[2:]}
        conds[("mt", f, A)] = ("DATA",)
        return conds, set(k) | {("mt", f, A)}, list(range(C["units_first"], C["units_first"] + cp["n_units"])), b1, sws, {"": {}}
    if stage == "robust":
        return {c: NETS for c in k[:3]}, set(), list(range(C["units_first"], C["units_first"] + C["n"])), b1, sws, C["variants"]
    raise ValueError(stage)


def draw_stimulus(u, over, stage):
    """Unit stimulus (PROTOCOL §2): uniforms drawn in a fixed order; confirm/robust use the R3/R3D ranges of confirm_params.json,
    pilot and smoke always the protocol ranges (so pilot1 and pilot2 draw identical stimuli)."""
    D, C = PROTO["range_D"], PROTO["range_C"]
    p = json.load(open(os.path.join(HERE, "confirm_params.json"))) if stage in ("confirm", "robust") else {}
    rng = np.random.default_rng([u, 2])
    rD = p.get("range_D_rho", D["rho_m"])
    rho = rng.uniform(*([0.72 * rD[0], 0.72 * rD[1]] if "ball_r_m" in over else rD))      # small_ball: range × 0.72
    az = rng.uniform(*over.get("abs_az_deg", D["abs_az_deg"]))
    k = rng.uniform(*p.get("range_C_k", C["k"]))
    phi = rng.uniform(0, 2 * math.pi)
    return dict(rho=rho, az=az, k=k, phi=phi)


_W = {}


def _init(b1, sws, first):
    _W["nets"] = SY.Networks(b1, sws, first)
    _W["scene"] = ST.Scene()


def job(args):
    stage, u, conds, rangeC, variant, over, out, man_sha = args
    sc, N = _W["scene"], _W["nets"]
    t0 = time.perf_counter()
    st = draw_stimulus(u, over, stage)
    sigma = over.get("pixel_noise_sigma", PROTO["pixel_noise_sigma"])
    r_ball = over.get("ball_r_m", PROTO["range_D"]["ball_r_m"])
    noise = SY.pixel_noise(u, sigma)
    rc = PROTO["range_C"]
    stims = [("D", "L", dict(az_deg=st["az"], rho=st["rho"], k=1.0, r=r_ball)),
             ("D", "R", dict(az_deg=-st["az"], rho=st["rho"], k=1.0, r=r_ball)), ("N", "N", None),
             ("C", "L", dict(az_deg=st["az"], rho=rc["rho_m"], k=st["k"], r=rc["ball_r_m"])),
             ("C", "R", dict(az_deg=-st["az"], rho=rc["rho_m"], k=st["k"], r=rc["ball_r_m"]))]
    traj = {}
    for c in conds:                                   # jitter rng index = crc32 of the condition name (order-independent)
        kind, f, A = c
        rng = np.random.default_rng([u, 3, zlib.crc32(cname(c).encode())]) if kind in ("jshuf", "jrms", "jvel") else None
        traj[c] = ST.motion(kind, f, A, st["phi"], rng, PROTO["jvel_vel_tolerance"], PROTO["jvel_max_draws"])
    rows, arr = [], {f"{cname(c)}|theta": th for c, (th, _) in traj.items()}
    arr.update({f"{cname(c)}|draws": np.array(n) for c, (_, n) in traj.items()})
    checks = []
    for lad, side, s in stims:                        # stimulus outer loop: the render cache is shared across conditions
        sc.set_target(**s) if s else sc.set_target()
        for c, nets in conds.items():
            if lad == "C" and c not in rangeC:
                continue
            kind, f, A = c
            theta, draws = traj[c]
            cn = cname(c)
            imgs, rec = sc.frames(theta, "mt" if kind == "mt" else "camera")
            if s and kind != "mt" and np.ptp(rec["ball"], 0).max() > 0:
                raise RuntimeError("ball moved")
            g, lin = SY.encode(imgs, noise)
            arr[f"{cn}|{lad}{side}|g"], arr[f"{cn}|{lad}{side}|lin"] = g.astype(np.float32), lin.astype(np.float32)
            if lad == "D" and side == "L":
                arr[f"{cn}|bearing"], arr[f"{cn}|cam_R"], arr[f"{cn}|ball"] = rec["bearing"], rec["cam_R"], rec["ball"]
            if c == ("stat", 0.0, 0.0) or kind == "jvel":   # runtime determinism check: fresh render == cached/first render
                fresh, _ = sc.frames(theta[:2], "camera", cache=False)
                checks.append(bool((fresh == imgs[:2]).all()))
            if lad == "C":
                continue
            for net in nets:
                o = SY.run_snn(N.pick(net, u), N.idx, g, u, SY.L.ENC.i_max, f if kind in ("sin", "jvel", "mt") else None, theta)
                rows.append(dict(stage=stage, variant=variant, unit=u, cond=cn, kind=kind, f=f, A=A, ladder=lad, side=side,
                                 system=net, jit_draws=draws, manifest_sha256=man_sha, **st, **o))
    arr["render_checks"] = np.array(checks)
    if not all(checks):
        raise RuntimeError(f"render determinism check failed {checks.count(False)}/{len(checks)}")
    arr["manifest_sha256"] = np.array(man_sha)
    tag = f"{variant + '_' if variant else ''}u{u}"
    for ext, write in (("feather", lambda fh: pd.DataFrame(rows).to_feather(fh)), ("npz", lambda fh: np.savez_compressed(fh, **arr))):
        final, part = os.path.join(out, f"{tag}.{ext}"), os.path.join(out, f".{tag}.{ext}.part")
        if os.path.exists(final):
            raise FileExistsError(final)
        with open(part, "wb") as fh:                  # write fully, then rename: a crash leaves no half file under the final name
            write(fh)
        os.rename(part, final)
    return tag, len(rows), round(time.perf_counter() - t0, 1), len(sc.cache)


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--stage", choices=("pilot1", "pilot2", "confirm", "robust", "smoke"), required=True)
    ap.add_argument("--manifest", required=True, help="manifest file name in this directory (from manifest.py)")
    ap.add_argument("--manifest-sha256", required=True)
    ap.add_argument("--workers", type=int, default=9)
    ap.add_argument("--units", help="smoke only: a-b inside the smoke pool")
    ap.add_argument("--plan", default="pilot1", help="smoke only: which stage's conditions to use")
    a = ap.parse_args()
    man = os.path.join(HERE, os.path.basename(a.manifest))
    if sha(man) != a.manifest_sha256:
        sys.exit("manifest.json hash mismatch")
    m = json.load(open(man))
    root = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
    bad = [p for p, h in m["sha256"].items() if sha(os.path.join(HERE, p)) != h] + \
          [p for p, h in m["deps_sha256"].items() if sha(os.path.join(root, "flymind", p)) != h] + \
          [p for p, h in m["data_sha256"].items() if sha(os.path.join(root, "data", "malecns", p)) != h]
    if bad:
        sys.exit(f"files differ from manifest: {bad}")
    if a.stage in ("confirm", "robust") and "confirm_params.json" not in m["sha256"]:
        sys.exit("confirm/robust need a manifest that includes confirm_params.json")
    if a.stage == "pilot2" and "pilot_r1.json" not in m["sha256"]:
        sys.exit("pilot2 needs a manifest that includes pilot_r1.json")
    if any(k.startswith("bio2") for k in sys.modules):
        sys.exit("bio2 imported")
    stage = a.stage
    conds, rangeC, units, b1, sws, variants = plan(a.plan if stage == "smoke" else stage)
    if stage == "smoke":
        lo, hi = map(int, a.units.split("-"))
        if not (PROTO["smoke_units"][0] <= lo <= hi <= PROTO["smoke_units"][1]):
            sys.exit("--units only inside the smoke pool")
        units = list(range(lo, hi + 1))
    elif a.units:
        sys.exit("--units is for smoke runs only")
    out = os.path.join(HERE, "results", "pilot" if stage.startswith("pilot") else stage)
    os.makedirs(out, exist_ok=True)                    # resumable: finished unit files are skipped, never overwritten
    pre = SY.L.stage1_hashes()
    if pre["mismatched"]:
        sys.exit(f"Stage 1 mismatch: {pre['mismatched']}")
    done = lambda v, u: all(os.path.exists(os.path.join(out, f"{v + '_' if v else ''}u{u}.{e}")) for e in ("feather", "npz"))
    jobs = [(stage, u, conds, rangeC, v, over, out, a.manifest_sha256) for v, over in variants.items() for u in units if not done(v, u)]
    print(f"{len(jobs)} unit jobs to run", flush=True)
    t0, errors = time.perf_counter(), []
    with mp.get_context("spawn").Pool(a.workers, _init, (b1, sws, units[0])) as pool:
        for res in pool.imap_unordered(_safe, jobs):
            if res[0] == "ERROR":
                errors.append(res[1:])
            print(*res, flush=True)
    post = SY.L.stage1_hashes()
    meta = dict(stage=stage, argv=sys.argv, units=[units[0], units[-1], len(units)], variants=list(variants),
                conds={cname(c): list(n) for c, n in conds.items()}, b1=b1, sws=sws, manifest_sha256=a.manifest_sha256,
                errors=errors, stage1_pre=pre, stage1_post=post, wall_s=time.perf_counter() - t0, time=time.strftime("%Y-%m-%dT%H:%M:%S"))
    with open(os.path.join(out, f"run_meta_{time.strftime('%Y%m%dT%H%M%S')}.json"), "x") as fh:
        json.dump(meta, fh, indent=1, default=str)
    print(f"errors {len(errors)}; Stage 1 after:", "OK" if not post["mismatched"] else post["mismatched"])
    if len(errors) > 0.01 * len(jobs) or post["mismatched"]:
        sys.exit("STOP: > 1 % of units failed or Stage 1 changed (PROTOCOL §10) — no analysis")


def _safe(args):
    try:
        return job(args)
    except Exception as e:  # noqa: BLE001 — a failed unit is recorded and excluded (PROTOCOL §10)
        return ("ERROR", args[1], repr(e))


if __name__ == "__main__":
    main()
