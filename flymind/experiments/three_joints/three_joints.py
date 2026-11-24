"""Trzy stawy (bark, łokieć, nadgarstek) z sieci muchy w MuJoCo, bez sekwencji zadania. Plan: PREREG_THREE_JOINTS.md. Tylko symulacja.
  three_joints.py --selftest                                   autotest bez sieci (ruch stawów, wykrywanie ograniczeń)
  three_joints.py --glu -1 --seeds 27301001,... --out DIR      próby (sieć budowana raz)"""
import argparse
import os
import sys

import numpy as np

FLY = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(FLY, "experiments", "step3_wiring"))
import alive  # noqa: E402
import head  # noqa: E402
import live_avoid as LA  # noqa: E402
import reflex as R  # noqa: E402
import touch_map as TM  # noqa: E402

JN, oh, sm = R.JN, R.oh, R.sm
DT, T_SETTLE, T_PRE, T_PRESS, T_POST, F_N, SIGMA = 0.01, 1.0, 3.0, 2.0, 3.0, 3.0, 2.0
J = (1, 2, 3)
CONDS = ("spokoj", "palec1", "palec2", "palec1_92")
BIT = dict(range=1, rate=2, lead=4, vision_stale=8)


class Drv:
    """Sieć jako „drv” ArmGrip: dotyk z harmonogramu (nie z kontaktów sceny), czucie łokcia z prawdziwego q/qd MuJoCo."""
    def __init__(self, net, feco, seed):
        net.net = R.SparseALIF(net._spec, R.ALIFParams(noise=SIGMA), seed)
        net.net.step = LA.fast_step(net.net, net._Wc)
        net.r, net.rj, net.tau = np.zeros((5, 2)), np.zeros(2), 0.0
        self.net, self.felt, run0 = net, np.zeros(2), net.net.run
        self.q, self.qd = np.zeros(6), np.zeros(6)

        def run(X, n):
            X, e, v = X.copy(), self.q[2] / alive.Q_LIM, self.qd[2]
            for k, x in (("claw_flex", e), ("claw_ext", -e), ("hook_flex", v), ("hook_ext", -v)):
                X[feco[k]] = 40.0 * min(1.0, max(0.0, x))
            return run0(X, n)
        net.net.run = run

    @property
    def r(self):
        return self.net.r

    def step(self, touch, q, qd):
        self.q, self.qd = q, qd
        return self.net.step(np.array([*self.felt, 0.0]), q[:5], qd[:5], DT)


class Const:
    """Sztuczna komenda (autotest)."""
    def __init__(self, dq):
        self.dq, self.r, self.felt = np.array(dq, float), np.zeros((5, 2)), np.zeros(2)

    def step(self, *a):
        return self.dq.copy()


class Still:
    def step(self, *a):
        return 0.0


def world():
    w = JN.ForceWorld([], 1)
    ac = JN.ArmCfg(version="three_joints", joints=J, roll=False, inputs=(), in_rule="fl")
    ctl = JN.ArmGrip(w, oh.OHCfg(), Still(), "snn:legT2L", sm.FlyCfg(glu_sign=-1.0, trigger="search"), "N", None, ac)
    last, step0 = {}, ctl.safety.step

    def step(cmd, q, now, age):                         # podsłuch: wejście i wyjście SafetyLayer (wynik bez zmian)
        out = step0(cmd, q, now, age)
        last.update(cmd=dict(cmd.q_target), out=out[0], per=out[3])
        return out
    ctl.safety.step = step
    return w, ctl, last


def simulate(drv, felt_at, n, active=True):
    """n taktów; felt_at(i) → siła odczuta [A0, A1] w takcie i. Zwraca log (klucz → tablica [takt, …])."""
    w, ctl, last = world()
    tgt = np.array(oh.OHCfg().home[:5])
    w.phase = "settle"
    for _ in range(int(round(T_SETTLE / DT))):
        ctl.tick(tgt, "open")
    w.phase, ctl.drv = "net", drv
    ctl.active, ctl.qc = set(J), {j: float(tgt[j]) for j in J}
    log = {k: [] for k in ("t", "q", "qc", "dq", "qt", "flag", "guard", "r", "felt", "real_touch", "q_all", "f_table", "ncon")}
    q0 = ctl.obs.q.copy()
    for i in range(n):
        drv.felt = np.asarray(felt_at(i), float)
        g0 = ctl.guard
        ctl.tick(tgt, "open")
        o = ctl.obs
        for k, x in (("t", (i + 1) * DT), ("q", o.q[1:4]), ("qc", [ctl.qc[j] for j in J]), ("dq", ctl.dq[1:4]), ("qt", last["out"][1:4]),
                     ("flag", [sum(BIT[f] for f in last["per"].get(j, ())) for j in J]), ("guard", ctl.guard - g0), ("r", drv.r[1:4].copy()),
                     ("felt", drv.felt), ("real_touch", o.touch), ("q_all", o.q), ("f_table", w.fmax.get("net", 0.0)),
                     ("ncon", sum(w.unwanted.values()))):
            log[k].append(np.array(x, float))
    return dict({k: np.array(v) for k, v in log.items()}, q0=q0)


def selftest():
    n = 100
    base = simulate(Const(np.zeros(5)), lambda i: (0, 0), n)
    assert np.abs(base["q"] - base["q"][0]).max() < 0.005 and not base["flag"].any() and not base["guard"].any()
    for k, j in enumerate(J):
        for s in (1, -1):
            dq = np.zeros(5)
            dq[j] = s * 0.001
            g = simulate(Const(dq), lambda i: (0, 0), n)
            mv = g["q"][-1] - base["q"][-1]
            assert s * mv[k] > 0.08 and np.abs(np.delete(mv, k)).max() < 0.02, (j, s, mv)
    g = simulate(Const([0, 0, 0, 0.005, 0]), lambda i: (0, 0), 200)
    assert (g["flag"][:, 2].astype(int) & 1).any() and g["q"][-1, 2] < 1.66, "zakres nadgarstka niewykryty"
    g = simulate(Const([0, 0.02, 0, 0, 0]), lambda i: (0, 0), 100)
    assert (g["flag"][:, 0].astype(int) & 2).any(), "limit prędkości niewykryty"
    g = simulate(Const([0, 0.012, 0, 0, 0]), lambda i: (0, 0), 400)
    print("strażnik stołu: takty", int(g["guard"].sum()), "| flagi barku", sorted(set(g["flag"][:, 0].astype(int))), "| siła na stół", g["f_table"].max())
    assert g["guard"].any() or g["flag"].any(), "zejście w stół niewykryte"
    print("selftest OK; dryf w spoczynku [rad]:", np.abs(base["q"] - base["q"][0]).max(0).round(5).tolist())


def build(glu):
    net = head.HeadLife(glu, "N", eyes=True)
    net.pads = TM.pads_for(net, "somato")
    net._full = list(net.pads)
    net._spec = JN.LB._W(net.W)
    net._Wc = R.SparseALIF(net._spec, R.ALIFParams(), None).W.tocsc()
    rng = np.random.default_rng(27301900)
    net._sub = sorted(int(x) for x in rng.choice(net.pads[0], len(net.pads[1]), replace=False))
    return net


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--glu", type=float)
    ap.add_argument("--seeds")
    ap.add_argument("--out")
    ap.add_argument("--conds", default=",".join(CONDS))
    a = ap.parse_args()
    if a.selftest:
        selftest()
        sys.exit(0)
    os.makedirs(a.out, exist_ok=True)
    net, feco = build(a.glu), alive.feco_idx(a.glu)
    print("sieć", net.N, "neuronów; receptory A0/A1:", [len(x) for x in net._full], flush=True)
    i0, i1 = int(round(T_PRE / DT)), int(round((T_PRE + T_PRESS) / DT))
    n = i1 + int(round(T_POST / DT))
    for s in map(int, a.seeds.split(",")):
        for c in a.conds.split(","):
            path = os.path.join(a.out, f"g{a.glu:+.0f}_{s}_{c}.npz")
            if os.path.exists(path):
                sys.exit(f"istnieje {path}")
            net.pads = [net._sub, net._full[1]] if c == "palec1_92" else net._full
            feel, k = TM.Feel(level="ideal", seed=s), {"palec1": 0, "palec1_92": 0, "palec2": 1}.get(c)

            def felt(i):
                f = np.zeros(2)
                if k is not None and i0 <= i < i1:
                    f[k] = F_N
                return feel.step(f)
            g = simulate(Drv(net, feco, s), felt, n)
            np.savez_compressed(path, **g)
            print(s, c, "Δq 0–3/3–5/5–8 s:", [(g["q"][b - 1] - (g["q"][a_ - 1] if a_ else g["q0"][1:4])).round(3).tolist() for a_, b in ((0, i0), (i0, i1), (i1, n))],
                  "flagi", int((g["flag"] > 0).sum()), "strażnik", int(g["guard"].sum()), "kontakty", int(g["ncon"][-1]), flush=True)
