"""Nowa podstawa i bark w pętli, scena 45 s (plan: PLAN_PODSTAWA_BARK.md). base_shoulder.py PULE.json DIR_OUT [--selftest]"""
import json
import os
import sys
import time
import zlib

import numpy as np

sys.dont_write_bytecode = True
import one_run as O  # noqa: E402

P, T, S0 = O.P, O.T, O.S0
JS = (0, 1, 2, 3)
T.J = JS                                                                # aktywne stawy: świat, ArmCfg, qc
T.JN.SIGN.update({0: 1.0, 1: -1.0})                                     # znaki z geometrii (plan)
KEEP = [11.9, 12.5, 19.9, 22.5, 29.5, 35.9, 36.3, 36.6, 40.0]           # chwile klatek kamery do pokazania
RUNS = dict(nowa={}, zablokowane=dict(block=True), mikro=dict(block=True, eps=1e-6))


def trial(net, feco, cam, block=False, eps=0.0):
    w, ctl, last, tgt = P.start()
    drv, eye, feel = P.Drv(net, feco, O.SEED), S0.EYES["v2"](), T.TM.Feel(level="ideal", seed=O.SEED)
    ctl.drv, net_step = drv, drv.step

    def step(touch, q, qd):
        q = q.copy()
        q[2] += eps
        drv.out = net_step(touch, q, qd)
        dq = drv.out.copy()
        if block:
            dq[:2] = 0.0
        return dq
    drv.step = step
    log, fr = {k: [] for k in ("t", "q_all", "qd_all", "dq_net", "dq_sent", "qc", "qt", "r", "loom", "raw", "feco", "felt", "ball", "gap", "cam", "rot", "flag", "guard", "ncon", "cnt", "real_touch", "fcrc")}, []
    q0 = ctl.obs.q.copy()
    for i in range(O.N):
        t = i * O.DT
        side, dist = O.ball(t)
        f, rot = cam.look(ctl.obs.q, side, dist)
        cp = cam.k.cam_xpos[cam.cid].copy()
        gap = np.linalg.norm(cam.E0 + cam.R0[:, 0] * side + cam.f0 * dist - cp) - S0.R_BALL
        if any(abs(t - k) < 1e-6 for k in KEEP):
            fr.append(f.copy())
        eye.see(f, O.DT, t)
        drv.loom, drv.felt, g0 = dict(eye.loom), feel.step(O.forces(t)), ctl.guard
        ctl.tick(tgt, "open")
        o = ctl.obs
        for k, x in (("t", t), ("q_all", o.q), ("qd_all", o.qd), ("dq_net", drv.out), ("dq_sent", ctl.dq), ("qc", [ctl.qc[j] for j in JS]), ("qt", last["out"][:5]), ("r", drv.r.copy()), ("loom", (eye.loom["L"], eye.loom["R"])),
                     ("raw", [T.A_MV * v / eye.out_full for v in eye.out]), ("feco", (drv.q[2], drv.qd[2])), ("felt", drv.felt), ("ball", (side, dist)), ("gap", gap), ("cam", cp), ("rot", rot),
                     ("flag", [sum(T.BIT[b] for b in last["per"].get(j, ())) for j in JS]), ("guard", ctl.guard - g0), ("ncon", sum(w.unwanted.values())),
                     ("cnt", [int(drv.spk[:, m].sum()) for m in net._grp.values()]), ("real_touch", o.touch), ("fcrc", zlib.crc32(f.tobytes()))):
            log[k].append(np.array(x, float))
    return dict({k: np.array(v) for k, v in log.items()}, q0=q0, klatki=np.array(fr))


def selftest():
    """Bez sieci: sztuczny przyrost podstawy/barku tą samą drogą (ArmGrip, SafetyLayer, MuJoCo) daje ruch zgodny z geometrią."""
    for j, s in ((0, 1), (0, -1), (1, 1), (1, -1)):
        w, ctl, last, tgt = P.start()
        dq = np.zeros(5)
        dq[j] = s * 0.001
        ctl.drv = T.Const(dq)
        p0 = T.JN._kin(ctl.sim, ctl.obs.q).site("cs_fixed").xpos.copy()
        for _ in range(100):
            ctl.tick(tgt, "open")
        p = T.JN._kin(ctl.sim, ctl.obs.q).site("cs_fixed").xpos - p0
        ok = (s * p[1] < -0.01) if j == 0 else (s * p[2] < -0.005)
        print("staw", j, "znak", s, "Δq", (ctl.obs.q - np.array(T.oh.OHCfg().home))[j].round(4), "Δchwytak mm", (p * 1e3).round(1).tolist(), "OK" if ok else "BŁĄD")
        assert ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit()
    src, out = sys.argv[1:3]
    os.makedirs(out)
    T.A_MV = S0.O.MV
    cam, (net, feco) = O.Cam(), O.build()
    U = json.load(open(src))
    inv = {i: b for b, i in net.pos.items()}
    G = {f"{ax}|{k}": list(map(int, v)) for ax, d in U.items() for k, v in d.items()}
    G["szczęka T2|zaciskanie (Ti extensor)"], G["szczęka T2|zwalnianie (Ti flexor + Acc)"] = [[int(inv[i]) for i in ix] for ix in (net.press, net.release)]
    old = {j: net.pools[j] for j in (2, 3)}
    ix = lambda *ks: [net.pos[b] for k in ks for b in G[k]]             # noqa: E731
    net.pools = {0: (ix("1 podstawa|+ promotor"), ix("1 podstawa|- remotor")),
                 1: (ix("2 bark|Tr flexor", "2 bark|Acc. tr flexor"), ix("2 bark|Tr extensor", "2 bark|Sternotroch.", "2 bark|Tergotr.")), **old}
    assert [len(x) for p in net.pools.values() for x in p] == [4, 2, 11, 8, 15, 2, 2, 5]
    ids = [b for v in G.values() for b in v]
    assert len(ids) == len(set(ids)) == 76
    n0 = len(net._grp)
    for b in ids:
        m = np.zeros(net.N, bool)
        m[net.pos[b]] = True
        net._grp[f"id{b}"] = m
    json.dump(dict(grupy=G, kolumny_cnt=["(dawne)"] * n0 + ids), open(os.path.join(out, "neurony.json"), "w"), indent=1, ensure_ascii=False)
    for name, kw in RUNS.items():
        t0 = time.time()
        g = trial(net, feco, cam, **kw)
        np.savez_compressed(os.path.join(out, name + ".npz"), **g)
        print(name, f"{time.time() - t0:.0f} s | flagi", (g["flag"] > 0).sum(0).tolist(), "strażnik", int(g["guard"].sum()), "kontakty", int(g["ncon"].max()),
              "| zmiana kątów °", np.degrees(g["q_all"][-1] - g["q0"]).round(2).tolist(), "min przerwa kula–kamera mm", round(float(g["gap"].min() * 1e3), 1), flush=True)
