"""P1 (21 XI): oko muchy (oko_mucha.FlyEye z VS/HS, test 2 PASS) na PRAWDZIWYM nagraniu z kamery (PREREG_OKO_KAMERA.md).
  .venv/bin/python oko_kamera.py ~/Desktop/oko_r1.mkv ~/Desktop/oko_r1_plan.json OUT.json
  .venv/bin/python oko_kamera.py --check     (sceny syntetyczne zszyte w jedno nagranie → musi wyjść PASS)
Klatki: ffmpeg skaluje do 160×100 szarości, jak live_avoid.Frames; czas = znaczniki klatek (zegar komputera)."""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import oko_mucha as O  # noqa: E402

FF, FP = "/Users/admin/miniforge3/bin/ffmpeg", "/Users/admin/miniforge3/bin/ffprobe"
LOOM, NON = ("loom_c", "loom_l", "loom_r"), ("side", "recede", "pan", "tilt")
PAD = 0.5                                                  # okno = [t0, t1 + 0,5 s]


def frames(path):
    pts = np.array(subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-show_entries", "frame=pts_time", "-of", "csv=p=0", path],
                                  capture_output=True, text=True, check=True).stdout.split(), float)
    raw = subprocess.run([FF, "-v", "error", "-i", path, "-vf", f"scale={O.W_PX}:{O.H_PX},format=gray", "-fps_mode", "passthrough",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    F = np.frombuffer(raw, np.uint8).reshape(-1, O.H_PX, O.W_PX)
    assert len(F) == len(pts), (len(F), len(pts))
    return pts, F


def run_eye(pts, F):
    eye = O.FlyEye(out_full=O.OUT_FULL2, vshs=True, g0=O.G0)
    out = np.zeros((len(F), 2))
    for k, (t, f) in enumerate(zip(pts, F)):
        eye.see(f.astype(float), None, t)
        out[k] = eye.out
    return out / O.OUT_FULL2                                # 1 = pełny napęd zbliżania (40 mV) w mózgu


def evaluate(pts, F, plan):
    e = run_eye(pts, F)
    lum = F.reshape(len(F), -1).mean(1)
    W = []
    for w in plan["windows"]:
        m = (pts >= w["t0"]) & (pts <= w["t1"] + PAD)
        if not m.any():
            W.append(dict(kind=w["kind"], peak=None))
            continue
        k = np.where(m)[0][e[m].max(1).argmax()]
        W.append(dict(kind=w["kind"], peak=float(e[k].max()), side=float(e[k, 0] - e[k, 1]), lum_min=float(lum[m].min())))
    peaks = lambda ks: [w["peak"] for w in W if w["kind"] in ks and w["peak"] is not None]   # noqa: E731
    lp = peaks(LOOM)
    med = float(np.median(lp)) if lp else 0.0
    non = peaks(NON)
    rest = [w for w in W if w["kind"] == "rest"]
    sync = [w for w in W if w["kind"] == "sync"]
    sides = [np.sign(w["side"]) for w in W if w["kind"] == "loom_l"], [np.sign(w["side"]) for w in W if w["kind"] == "loom_r"]
    k3 = max(sum(a > 0 for a in sides[0]) + sum(b < 0 for b in sides[1]), sum(a < 0 for a in sides[0]) + sum(b > 0 for b in sides[1]))
    K = dict(K1=sum(p <= 0.25 * med for p in non) >= int(np.ceil(0.8 * len(non))) and len(non) > 0,
             K2=sum(p >= 0.5 for p in lp) >= int(np.ceil(0.8 * len(lp))) and len(lp) > 0,
             K3=k3 == len(sides[0]) + len(sides[1]) and k3 > 0,
             K4=all(p >= 0.5 * med for p in peaks(("loompan",))) and len(peaks(("loompan",))) > 0,
             K5=all(w["peak"] is not None and w["peak"] <= 0.1 for w in rest) and len(rest) > 0)
    rw = [w for w in plan["windows"] if w["kind"] == "rest"]
    base = float(np.median(lum[(pts >= rw[0]["t0"]) & (pts <= rw[0]["t1"])])) if rw else float(np.median(lum))   # jasność „nic nie rób”
    return dict(PASS=all(K.values()), K=K, median_loom=med, nonloom_ratio=[p / med if med else None for p in non],
                side_mapping="L=lewa" if k3 and sides[0] and sides[0][0] > 0 else "zamienione (użyj --flip)",
                sync_dark=[w["lum_min"] / max(base, 1e-9) for w in sync if w["peak"] is not None],
                light_ratio=[p / med if med else None for p in peaks(("light",))],
                fps=float(1 / np.median(np.diff(pts))), n_frames=int(len(F)), windows=W)


def _check():
    """Sceny testu 2 (oko_mucha.scene, ziarna 24 101 001–) zszyte w jedno nagranie 640×400 z planem → oczekuję PASS."""
    order = [("sync", None), ("rest", "static"), *[("loom_c", "loom")] * 3, *[("loom_l", "loom_L")] * 2, *[("loom_r", "loom_R")] * 2,
             *[("side", "side")] * 3, *[("recede", "recede")] * 3, *[("pan", "pan_h")] * 3, *[("tilt", "pan_v")] * 3,
             *[("loompan", "loom_pan")] * 2, *[("light", "light")] * 2]
    d = tempfile.mkdtemp()
    vid, fr, plan, t = os.path.join(d, "v.mkv"), [], {"windows": []}, 0.0
    for i, (kind, sc) in enumerate(order):
        S = O.scene(sc, 24101001 + i) if sc else [(k / O.FPS, np.full((O.H_PX, O.W_PX), 10, np.uint8)) for k in range(240)]
        if kind == "rest":                                   # „nic nie rób”: stała scena bez dysku
            S = [(tt, S[0][1]) for tt, _ in S]
        hold = [S[0][1]] * O.FPS                             # 1 s bez ruchu: skok między scenami wygasa przed oknem
        plan["windows"].append(dict(kind=kind, t0=t + 1.0 + 0.4, t1=t + 1.0 + len(S) / O.FPS - PAD))
        fr += hold + [f for _, f in S]
        t += 1.0 + len(S) / O.FPS
    p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{4 * O.W_PX}x{4 * O.H_PX}",
                          "-r", str(O.FPS), "-i", "-", "-c:v", "ffv1", vid], stdin=subprocess.PIPE)
    for f in fr:
        p.stdin.write(np.kron(f, np.ones((4, 4), np.uint8)).tobytes())
    p.stdin.close()
    p.wait()
    res = evaluate(*frames(vid), plan)
    print(json.dumps({k: v for k, v in res.items() if k != "windows"}, default=float))
    assert res["PASS"], "syntetyczne sceny testu 2 nie przechodzą przez ścieżkę nagrania"
    assert res["sync_dark"][0] < 0.3, "znacznik zasłonięcia niewidoczny"
    print("oko_kamera _check OK")


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        _check()
    else:
        vid, plan, out = sys.argv[1:4]
        plan = json.load(open(os.path.expanduser(plan)))
        pts, F = frames(os.path.expanduser(vid))
        ft = np.array(plan["frame_t"])
        # 21 XI: wyjście do skryptu było stałe 120 kl./s (ffmpeg dublował klatki), plik ma prawdziwe ~78 kl./s ze zmiennym odstępem.
        # Obie drogi zaczynają od tej samej pierwszej klatki → czas klatki k = czas przyjścia pierwszej + (pts_k − pts_0).
        t = ft[0] + pts - pts[0]
        r = evaluate(t, F, plan)
        r["clock"] = dict(method="ft0 + pts", span_file=float(pts[-1] - pts[0]), span_pipe=float(ft[-1] - ft[0]))
        lum = F.reshape(len(F), -1).mean(1)
        sw = [w for w in plan["windows"] if w["kind"] == "sync"][0]
        m = (t >= sw["t0"] - 2) & (t <= sw["t1"] + 2)
        dark = t[m][lum[m] < 0.3 * np.median(lum[m])]
        r["clock"]["dark_from_sync_t0_s"] = float(dark[0] - sw["t0"]) if len(dark) else None   # oczekuję 0–3 s (reakcja Adama)
        json.dump(r, open(out, "w"), indent=1, default=float)
        print(json.dumps({k: v for k, v in r.items() if k != "windows"}, default=float))
