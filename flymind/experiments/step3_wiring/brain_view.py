"""Podgląd mózgu z ramieniem (19 XI, prośba Adama): jedna próba „nie dać się dotknąć” (hw2p: A0 szczęka stała + P dłoń)
→ (1) spiki KAŻDEGO neuronu w każdym takcie 10 ms, (2) film ramienia z ręką (1 klatka = 1 takt, 25 kl./s = zwolnione 4×),
(3) dane dla strony: przynależność neuronów do obszarów i schematyczne położenia. Ilustracja, nie test (ziarno rozwojowe).
Położenia neuronów są SCHEMATYCZNE (w danych nie ma współrzędnych): neuron leży w obszarze swojej grupy, w losowym miejscu.
Uruchom: brain_view.py --dir left --seed 21948002 --out DIR"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import avoid as A  # noqa: E402
import brainleg as B  # noqa: E402
import head  # noqa: E402
import nets  # noqa: E402
import touch_map as TM  # noqa: E402

W, H = 720, 600
# obszary schematu (środek x, y, promienie rx, ry) w układzie 1000 × 1000; podpis
REG = {
    "eyeL": ((150, 250, 115, 150), "oko lewe (LPLC2, LC4, LPLC1, LC6, LC16)"),
    "eyeR": ((850, 250, 115, 150), "oko prawe"),
    "vpn": ((500, 175, 230, 55), "mózg: neurony wzrokowe → mózg"),
    "brain": ((500, 285, 250, 80), "mózg: neurony wewnętrzne"),
    "bm": ((500, 75, 120, 30), "szczecinki głowy (czujnik P „dłoń”)"),
    "asc": ((500, 385, 160, 30), "neurony wstępujące (z ciała do mózgu)"),
    "dn": ((500, 470, 70, 45), "neurony zstępujące (mózg → ciało)"),
    "dnkey": ((380, 470, 38, 26), "DNg15 + DNge078 (droga głowa → noga)"),
    "dnesc": ((620, 470, 38, 26), "DN ucieczki (DNp01/02/04/11)"),
    "inter": ((500, 690, 150, 150), "noga: interneurony"),
    "femur": ((265, 640, 60, 50), "szczecinki nogi „udo” (czujnik A0)"),
    "tibia": ((265, 760, 50, 40), "szczecinki nogi „goleń” (bez czujnika w hw2p)"),
    "feco": ((265, 860, 40, 28), "czucie łokcia (FeCO)"),
    "mn": ((735, 700, 70, 150), "noga: motoneurony (ruch ramienia)"),
    "other": ((500, 905, 130, 40), "inne"),
}
ESC = ("DNp01", "DNp02", "DNp04", "DNp11")


def regions(net):
    """Obszar dla każdego neuronu sieci (indeks → klucz REG)."""
    import pandas as pd
    a = pd.read_feather(nets.visual_path.ANN, columns=["bodyId", "type", "superclass"]).set_index("bodyId")
    body = [None] * net.N
    for b, i in net.pos.items():
        body[i] = b
    sc = a.superclass.reindex(body).astype(str).values
    ty = a.type.reindex(body).astype(str).values
    reg = np.array(["other"] * net.N, object)
    reg[np.isin(sc, ["cb_intrinsic", "cb_sensory", "cb_motor", "cb_endocrine", "ol_intrinsic"])] = "brain"
    reg[np.isin(sc, ["visual_projection", "visual_centrifugal"])] = "vpn"
    reg[np.isin(sc, ["ascending_neuron", "sensory_ascending"])] = "asc"
    reg[np.isin(sc, ["descending_neuron", "sensory_descending"])] = "dn"
    reg[np.isin(sc, ["vnc_intrinsic", "vnc_sensory"])] = "inter"
    reg[sc == "vnc_motor"] = "mn"
    reg[np.isin(ty, ESC)] = "dnesc"
    _, d78, d15 = B.route_ids()
    reg[[net.pos[b] for b in d78 + d15]] = "dnkey"
    for k, ix in (("eyeL", net._eyes["L"]), ("eyeR", net._eyes["R"]), ("bm", net.palm),
                  ("femur", net.pads[0]), ("tibia", net.pads[1])):
        reg[list(ix)] = k
    for j, (p, n) in net.pools.items():
        reg[list(p) + list(n)] = "mn"
    reg[net.press + net.release] = "mn"
    fe = A.alive.feco_idx(net.glu) if hasattr(net, "glu") else None
    if fe:
        reg[[i for v in fe.values() for i in v]] = "feco"
    return reg, ty


def layout(reg, seed=7):
    rng = np.random.default_rng(seed)
    xy = np.zeros((len(reg), 2))
    for k, ((cx, cy, rx, ry), _) in REG.items():
        ix = np.flatnonzero(reg == k)
        r, t = np.sqrt(rng.uniform(0, 1, len(ix))), rng.uniform(0, 2 * np.pi, len(ix))
        xy[ix] = np.c_[cx + rx * r * np.cos(t), cy + ry * r * np.sin(t)]
    return np.round(xy).astype(int)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="left")
    ap.add_argument("--seed", type=int, default=21948002)
    ap.add_argument("--glu", type=float, default=-1.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    net = head.HeadLife(a.glu, "N", None, eyes=True)
    net.glu = a.glu
    net._eyes = A.eye_idx(net)
    net.pads = TM.pads_for(net, "somato")
    feel = TM.Feel(level="typ", seed=a.seed)
    feel.discs = ("A0", "P")
    spikes = []
    base = A.R.SparseALIF

    class RecALIF(base):                            # tylko zapis: które neurony dały spike w takcie (10 kroków po 1 ms)
        def run(self, X, n):
            s = super().run(X, n)
            spikes.append(np.flatnonzero(np.asarray(s).sum(0) > 0).astype(np.int32))
            return s
    A.R.SparseALIF = RecALIF
    res, log = A.trial(net, a.dir, 2.0, a.seed, feco=A.alive.feco_idx(a.glu), aim="palm", feel=feel)
    A.R.SparseALIF = base
    print(json.dumps(res))
    reg, ty = regions(net)
    xy = layout(reg)
    # film: ta sama kinematyka co w próbie, ręka = kula
    import mujoco
    w = A.JN.ForceWorld([("cyl", A.JN.oh.BASE_MATS[0])], 1)
    sim = w.sim
    q6 = sim.d.qpos[sim.qadr].copy()
    target = A.JN._kin(sim, q6).site("cs_palm").xpos.copy()
    u = np.array(A.DIRS[a.dir], float)
    u /= np.linalg.norm(u)
    m = sim.m
    m.vis.global_.offwidth, m.vis.global_.offheight = max(m.vis.global_.offwidth, W), max(m.vis.global_.offheight, H)
    r, cam = mujoco.Renderer(m, H, W), mujoco.MjvCamera()
    cam.type, cam.lookat[:], cam.distance, cam.azimuth, cam.elevation = mujoco.mjtCamera.mjCAMERA_FREE, target + [0.0, 0.03, 0.03], 0.45, 150.0, -20.0
    vid = os.path.join(a.out, "ramie.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "25",
                           "-i", "-", "-pix_fmt", "yuv420p", "-vcodec", "libx264", "-crf", "23", "-movflags", "+faststart", vid],
                          stdin=subprocess.PIPE)
    hands = []
    for i, (t, q) in enumerate(zip(log["t"], log["q"])):
        h = target + u * (A.D0 - A.V_HAND * min(max(0.0, t - A.T_PRE), A.D0 / A.V_HAND))
        hands.append(h.tolist())
        qq = q6.copy()
        qq[1:4] = q
        sim.d.qpos[sim.qadr] = qq
        mujoco.mj_forward(m, sim.d)
        r.update_scene(sim.d, camera=cam)
        scn = r.scene
        if scn.ngeom < scn.maxgeom:
            mujoco.mjv_initGeom(scn.geoms[scn.ngeom], mujoco.mjtGeom.mjGEOM_SPHERE, np.array([A.R_HAND, 0, 0]), h,
                                np.eye(3).ravel(), np.array([0.95, 0.75, 0.6, 0.55], np.float32))
            scn.ngeom += 1
        ff.stdin.write(np.ascontiguousarray(r.render()).tobytes())
    ff.stdin.close()
    if ff.wait():
        raise RuntimeError("ffmpeg")
    touch = np.array(log["touch"])
    data = dict(
        info=dict(res, dir=a.dir, seed=a.seed, glu=a.glu, dt_ms=10, fps=25, n=int(net.N),
                  note="Ilustracja, nie test. Położenia neuronów schematyczne (dane nie mają współrzędnych)."),
        regions={k: dict(xy=v[0], label=v[1], n=int((reg == k).sum())) for k, v in REG.items()},
        reg=[list(REG).index(k) for k in reg], xy=xy.ravel().tolist(),
        spikes=[s.tolist() for s in spikes],
        series=dict(t=log["t"], touch=np.round(touch.max(1), 2).tolist(), touch3=np.round(touch, 2).tolist(),
                    loom=np.round(log["loom"], 2).tolist(), q=np.round(log["q"], 3).tolist()))
    assert len(spikes) == len(log["t"]), (len(spikes), len(log["t"]))
    with open(os.path.join(a.out, "mozg.json"), "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print("zapisano", a.out, "spiki/takt średnio", round(float(np.mean([len(s) for s in spikes])), 1))


if __name__ == "__main__":
    main()
