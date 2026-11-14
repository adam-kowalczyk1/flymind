"""F1 blocking tests (PROTOCOL r3 §10), assert-style, no framework. Smoke-pool seeds 9 108 0xx only. Passing them does NOT prove
scientific validity. Run: .venv/bin/python -I -B flymind/experiments/f1_active_sensing/tests/test_f1.py"""
import hashlib
import json
import math
import os
import subprocess
import sys

import numpy as np

if not sys.flags.dont_write_bytecode:
    sys.exit("run with python -B")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
import analysis_core as AC  # noqa: E402
import stimulus as ST  # noqa: E402
import systems as SY  # noqa: E402

PR = json.load(open(os.path.join(HERE, "protocol.json")))
U = 9108001
sc = ST.Scene()
N = SY.Networks([9108002], [9108003], U)
I_MAX = SY.L.ENC.i_max
W_SHA = hashlib.sha256(N.spec.W_data.tobytes()).hexdigest()
ok = []


def check(name, cond, info=""):
    print(("PASS " if cond else "FAIL ") + name, info, flush=True)
    ok.append(bool(cond))


def stream(st, theta, unit=U, sigma=10.0, mode="camera"):
    sc.set_target(**st) if st else sc.set_target()
    imgs, rec = sc.frames(theta, mode)
    g, lin = SY.encode(imgs, SY.pixel_noise(unit, sigma))
    return imgs, rec, g, lin


T1 = dict(az_deg=10.0, rho=0.26, k=1.0, r=0.025)
stat, _ = ST.motion("stat", 0, 0, 0)
th, _ = ST.motion("sin", 2.0, 4.0, 0.3)
# T1 zero amplitude == stationary (images, g, SNN bit-identical)
zero, _ = ST.motion("sin", 2.0, 0.0, 0.3)
i0, _, g0, _ = stream(T1, stat)
i1, _, g1, _ = stream(T1, zero)
o0, o1 = (SY.run_snn(N.spec, N.idx, g, U, I_MAX) for g in (g0, g1))
check("T1 zero amplitude reproduces stationary", (i0 == i1).all() and (g0 == g1).all() and o0 == o1, f"D {o0['D']}")

# T2 mirror: flipped image swaps g exactly; mirrored scene sign; asymmetry reported
e = SY.ENC.encode(i0[150])["g"]
ef = SY.ENC.encode(np.ascontiguousarray(i0[150, :, ::-1]))["g"]
check("T2 flipped image swaps g_L/g_R", np.allclose(e, ef[::-1], rtol=1e-6, atol=1e-9), f"{e.round(6)} vs {ef.round(6)}")
_, _, gL, _ = stream(T1, th)
_, _, gR, _ = stream(dict(T1, az_deg=-10.0), -th)
oL, oR = SY.run_snn(N.spec, N.idx, gL, U, I_MAX), SY.run_snn(N.spec, N.idx, gR, U, I_MAX)
sw = SY.run_snn(N.spec, N.idx, gL[:, ::-1], U, I_MAX)
check("T2 mirrored scene: encoder ipsi > contra on both sides", gL[100:, 0].mean() > gL[100:, 1].mean() and gR[100:, 1].mean() > gR[100:, 0].mean(),
      f"ipsi g L-target {gL[100:, 0].mean():.4f} vs R-target {gR[100:, 1].mean():.4f} (scene asymmetry ratio {gL[100:, 0].mean() / gR[100:, 1].mean():.3f})")
check("T2/T11 readout sign: D>0 left target, D<0 right target, swapped g flips sign", oL["D"] > 0 and oR["D"] < 0 and sw["D"] < 0,
      f"D_L {oL['D']} D_R {oR['D']} D_swapped {sw['D']}")

# T3/T12 no target: SNN silent, P = 0, over smoke units and phases
Ds, Ps = [], []
for u in range(9108010, 9108018):
    t_, _ = ST.motion("sin", 2.0, 4.0, math.pi / 2 * (u % 4))
    _, _, gn, ln = stream(None, t_, unit=u)
    Ds.append(SY.run_snn(N.spec, N.idx, gn, u, I_MAX)["D"])
    Ps.append(SY.controls(gn, ln, 6.0, 6.0, 0.1, 20.0, I_MAX)["P"])
check("T3/T12 no target: SNN D = 0 and |P| < 1e-3 (spontaneous directional activity)", all(d == 0 for d in Ds) and max(map(abs, Ps)) < 1e-3,
      f"D {Ds} |P|max {max(map(abs, Ps)):.1e}")

# T4 phase: no-target drive 0; window-mean drive of a target varies < 2 % across 4 phases (whole cycles)
gp = []
for r in range(4):
    sc.set_target(**dict(T1, rho=0.30))
    t_, _ = ST.motion("sin", 2.0, 4.0, math.pi / 2 * r)
    imgs, _ = sc.frames(t_)
    gp.append(np.array([SY.ENC.encode(f)["g"] for f in imgs])[100:].mean(0))
gp = np.array(gp)
check("T4 phase: window-mean target drive varies < 2 % across phases", np.ptp(gp, 0).max() / gp.mean(0).max() < 0.02, str(gp.round(4).tolist()))

# T5 jitter statistics (+ T14 draws)
for f, A in ((0.5, 1.0), (2.0, 2.0), (4.0, 4.0)):
    s, _ = ST.motion("sin", f, A, 0.7)
    sh, _ = ST.motion("jshuf", f, A, 0.7, np.random.default_rng([U, 3, 0]))
    check(f"T5 jshuf f{f} A{A}: same θ multiset (window and pre-window)",
          np.array_equal(np.sort(s[100:]), np.sort(sh[100:])) and np.array_equal(np.sort(s[:100]), np.sort(sh[:100])))
    for kind in ("jrms", "jvel"):
        x, n = ST.motion(kind, f, A, 0.0, np.random.default_rng([U, 3, 1]))
        v = np.sqrt((ST.derivs(x)[0][100:] ** 2).mean()) / (2 * math.pi * f * math.radians(A) / math.sqrt(2))
        good = abs(np.sqrt((x[100:] ** 2).mean()) - math.radians(A) / math.sqrt(2)) < 1e-12 and abs(x[100:].mean()) < 1e-12 \
            and (kind == "jrms" or abs(v - 1) <= 0.2)
        check(f"T5 {kind} f{f} A{A}: window RMS exact, window mean 0" + ("" if kind == "jrms" else ", RMS velocity ±20 %"), good,
              f"vel ratio {v:.2f} draws {n} peak/A {np.abs(x[100:]).max() / math.radians(A):.2f}")
v_sin = np.sqrt((ST.derivs(th)[0][100:] ** 2).mean())
check("T5 sinusoid velocity = 2πfA/√2 (central differences, 2 %)", abs(v_sin / (2 * math.pi * 2 * math.radians(4) / math.sqrt(2)) - 1) < 0.02)

# T6 target world position, bearing, camera position
w = sc.set_target(**T1)
_, rec = sc.frames(th)
check("T6 ball does not move", np.ptp(rec["ball"], 0).max() == 0 and np.allclose(rec["ball"][0], w))
check("T6 bearing = az0 − θ", np.abs(rec["bearing"] - (math.radians(10) - th)).max() < 1e-9,
      f"max err {np.abs(rec['bearing'] - (math.radians(10) - th)).max():.1e} rad")
check("T6 camera position constant", np.ptp(rec["cam_pos"], 0).max() < 1e-12)
# MT: static camera, ball moved to bearing az0 − θ, z = r
_, mt = sc.frames(th, "mt")
check("MT bearing = az0 − θ, camera static, ball z = r", np.abs(mt["bearing"] - (math.radians(10) - th)).max() < 1e-9
      and np.ptp(mt["cam_R"], 0).max() < 1e-12 and np.allclose(mt["ball"][:, 2], 0.025))
ic, _ = sc.frames(th)
im, _ = sc.frames(th, "mt")


def blob(img):
    x = img.astype(float)
    c = (x[..., 1] - (x[..., 0] + x[..., 2]) / 2) / x.mean()
    ys, xs = np.nonzero(c > 0.15)
    return xs.mean(), len(xs)


dc = [abs(blob(a)[0] - blob(b)[0]) for a, b in zip(ic[::30], im[::30])]
da = [abs(blob(a)[1] - blob(b)[1]) for a, b in zip(ic[::30], im[::30])]
check("MT vs camera rotation: ball column centroid < 1 px apart (area difference reported)", max(dc) < 1.0,
      f"max centroid diff {max(dc):.2f} px, max area diff {max(da)} px")

# r3.1 A1 render cache: cached frames are bit-identical to fresh renders, across conditions sharing θ values (sin → jshuf)
sc.set_target(**T1)
shf, _ = ST.motion("jshuf", 2.0, 4.0, 0.3, np.random.default_rng([U, 3, 5]))
c1, _ = sc.frames(th)
c2, _ = sc.frames(shf)
n_cached = len(sc.cache)
f1, _ = sc.frames(th, cache=False)
f2, _ = sc.frames(shf, cache=False)
cm, _ = sc.frames(th, "mt")
fm, _ = sc.frames(th, "mt", cache=False)
check("A1 cache: cached == fresh renders (camera and MT), sin and J_shuf share renders", (c1 == f1).all() and (c2 == f2).all()
      and (cm == fm).all() and n_cached == len(np.unique(np.round(th, 12))),
      f"{n_cached} distinct renders for 300 frames; parts {(c1 == f1).all()} {(c2 == f2).all()} {(cm == fm).all()} {len(np.unique(np.round(th, 12)))}")
_, mrec = sc.frames(th, "mt")
_, rec2 = sc.frames(stat)
check("A1 MT leaves the ball at its static position", np.allclose(rec2["ball"][0], sc.set_target(**T1)))

# T7 renderer pose == recorded pose; projected ball column ≈ rendered centroid
sc.set_target(**T1)
errs, cen = [], []
for t in (0.0, math.radians(3.0), math.radians(-4.0)):
    p, R = sc.pose(t)
    img = sc.sim.observe().frame.image
    cams = sc.sim.renderer.scene.camera                   # [0]/[1] = stereo eyes at ±ipd/2; mono rendering uses their average
    cpos = (np.array(cams[0].pos) + np.array(cams[1].pos)) / 2
    errs.append(max(np.abs(cpos - p).max(), np.abs(np.array(cams[0].forward) + R[:, 2]).max(), np.abs(np.array(cams[0].up) - R[:, 1]).max()))
    b = sc.sim.d.qpos[sc.bq:sc.bq + 3]
    v = R.T @ (b - p)
    H, Wd = img.shape[:2]
    tanx = math.tan(math.radians(35)) * Wd / H
    cen.append(abs(blob(img)[0] + 0.5 - Wd / 2 * (1 + v[0] / (-v[2]) / tanx)))
check("T7 renderer camera = recorded pose", max(errs) < 1e-5, f"max {max(errs):.1e}")
check("T7 projected ball column ≈ rendered centroid (< 1.5 px)", max(cen) < 1.5, str(np.round(cen, 2).tolist()))

# T8 baseline network unmodified; controls differ
check("T8 DATA W unchanged, no model edges", hashlib.sha256(N.spec.W_data.tobytes()).hexdigest() == W_SHA and not N.spec.W_model.any())
lc = np.r_[N.idx["in_L"], N.idx["in_R"]]
blk = np.zeros(N.spec.W_data.shape, bool)
blk[np.ix_(lc, lc)] = True
dif = N.nets["B1"][0].W_data != N.spec.W_data
check("T8 B1 differs from DATA only inside the LC10a×LC10a block (full mask)", dif.any() and not dif[~blk].any(), f"{dif.sum()} entries differ")

# T9 integrity (protected files, Stage 1) — the F1 pre-snapshot comparison is run by the runner wrapper
r = subprocess.run([sys.executable, "-I", "-B", os.path.join(ROOT, "flymind", "integrity_v5v41.py"), "--compare",
                    os.path.join(ROOT, "flymind", "results", "v5v41", "integrity_baseline.json"), "--label", "f1_tests"],
                   capture_output=True, text=True)
check("T9 integrity_v5v41 --compare", r.returncode == 0, r.stdout.strip()[-120:])
r = subprocess.run([sys.executable, "-I", "-B", os.path.join(HERE, "integrity_f1.py")], capture_output=True, text=True)
check("T9 F1 pre-snapshot unchanged (flymind/ outside experiments, bio2/, data/, assets/)", r.returncode == 0, r.stdout.strip())

# T10 determinism
_, _, g2, _ = stream(T1, stat)
check("T10 repeated run bit-identical", (g2 == g0).all() and SY.run_snn(N.spec, N.idx, g0, U, I_MAX) == o0)

# CRN: same unit → same noise sequence across networks; N equal
a1, a2 = SY.ALIF(N.spec, SY.L.P, U), SY.ALIF(N.nets["SWS"][0], SY.L.P, U)
check("CRN noise identical across networks", (a1.rng.standard_normal(5000) == a2.rng.standard_normal(5000)).all()
      and len(N.spec.bodies) == len(N.nets["B1"][0].bodies) == len(N.nets["SWS"][0].bodies) == 424)

# controls: TH_LP extrema property; P is a window mean of g_L − g_R up to a start transient
gg = np.abs(np.random.default_rng(U).standard_normal((300, 2))) * 0.6
x = SY.lowpass_drive(gg, I_MAX, 20.0)
fine = SY.ema(np.repeat(I_MAX * gg, 10, 0), math.exp(-1 / 20))
check("TH_LP frame-end sampling = 1 ms low-pass at frame ends", np.allclose(x, fine[9::10]))
c = SY.controls(gg, np.zeros(300), 6.0, 6.0, 0.1, 20.0, I_MAX)
check("P ≈ window mean of g_L − g_R", abs(c["P"] - (gg[100:, 0] - gg[100:, 1]).mean()) < 0.02, f"{c['P']:.4f}")
check("no bio2 module imported", not any(k.startswith("bio2") for k in sys.modules))
r = subprocess.run([sys.executable, "-I", "-B", os.path.join(HERE, "analysis_core.py")], capture_output=True, text=True)
check("analysis_core self-check", r.returncode == 0, r.stdout.strip())
sc.close()
print(f"{sum(ok)}/{len(ok)} passed")
sys.exit(0 if all(ok) else 1)
