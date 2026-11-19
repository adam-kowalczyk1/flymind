"""Tryb „nie dać się dotknąć” (18 XI, Adam: „na podstawie swoich wszystkich zmysłów próbuje nie zostać dotknięta; kodem tylko
wykrywanie ręki; ścisła integracja w mózgu”). Sieć: noga + głowa + pełne typy zbliżania (head.HeadLife(eyes=True)).
Kod klasyczny = TYLKO czujniki ręki:
  wzrok  — z punktu gripperframe szybkość rośnięcia dłoni L = max(0, dθ/dt), θ = 2·asin(r/d) → wszystkie komórki LPLC2, LC4,
           LPLC1, LC6, LC16 oka lewego/prawego (somaSide), waga strony (1 ± sin az)/2, 40 mV przy 2 rad/s;
  dotyk  — wcisk dłoni-kuli w punkty cs_palm (dłoń → szczecinki BM) i cs_fixed / cs_moving (pady → receptory T2 L),
           siła 300 N/m · wcisk (3 N/cm), dalej jak dotąd 40 mV/N (TwoNet.step);
  czucie nogi — FeCO T1 L z kąta/prędkości łokcia (jak alive.py).
Ruch: pule stawów 1–3 → przyrost celu (jak cały krok 3/4), kinematyka SO-101 bez fizyki. Żadnej reguły „uciekaj”.
Dłoń: kula r 4 cm leci 0,3 m/s z kierunku left/right/front ku POCZĄTKOWEMU położeniu cs_palm i zostaje tam 1,5 s
(nieruchome ramię = dotknięte). Zmysły można wyłączyć: --blind (bez wzroku), --numb (bez dotyku), --frozen (ramię stoi).
Uruchom: avoid.py --glu ±1 --net N|F|L [--shuffle-seed S] [--lesion both] --dir left|right|front --noise σ --noise-seed K --out P.json"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alive  # noqa: E402
import head  # noqa: E402
import nets  # noqa: E402
import reflex as R  # noqa: E402

JN = nets.JN
R_HAND, V_HAND, D0, K_TOUCH = 0.04, 0.30, 0.45, 300.0
L_FULL, MV, DT, T_PRE, T_HOLD = 2.0, 40.0, 0.01, 0.5, 1.5
DIRS = {"left": (0, 1, 0), "right": (0, -1, 0), "front": (0.7, 0, 0.7)}
PTS = ("cs_fixed", "cs_moving", "cs_palm")                       # kolejność jak touch[0:3]


def eye_idx(net):
    import pandas as pd
    a = pd.read_feather(nets.visual_path.ANN, columns=["bodyId", "type", "somaSide"])
    a = a[a.type.isin(head.LOOM_TYPES) & a.bodyId.isin(list(net.pos))]
    return {s: [net.pos[int(b)] for b in a.bodyId[a.somaSide == s]] for s in ("L", "R")}


def trial(net, direction, sigma, seed, blind=False, numb=False, frozen=False, feco=None, aim="palm", feel=None):
    """feel=None → dotyk „sim3” (siła w środkach padów i dłoni, jak 18 XI); feel=touch_map.Feel → „hw2”: czuje tylko
    2 krążki FSR (A0 szczęka stała, A1 ruchoma) przez model czujnika; dłoń bez czujnika. Miara dotknięcia zawsze ta sama
    (geometria 3 punktów), więc sim3 i hw2 są porównywalne."""
    w = JN.ForceWorld([("cyl", JN.oh.BASE_MATS[0])], 1)
    sim = w.sim
    q6 = sim.d.qpos[sim.qadr].copy()
    q_lo, q_hi = sim.m.jnt_range[1:4, 0], sim.m.jnt_range[1:4, 1]
    sites = lambda q: (lambda k: {p: k.site(p).xpos.copy() for p in PTS + ("gripperframe",)})(JN._kin(sim, q))  # noqa: E731
    S0 = sites(q6)
    target = S0["cs_palm"] if aim == "palm" else 0.5 * (S0["cs_fixed"] + S0["cs_moving"])   # „tips” = między szczękami
    u = np.array(DIRS[direction], float)
    u /= np.linalg.norm(u)
    t_move = D0 / V_HAND
    if not hasattr(net, "_eyes"):
        net._eyes = eye_idx(net)
    eyes = net._eyes
    net.net = R.SparseALIF(R.JN.LB._W(net.W), R.ALIFParams(noise=sigma), seed)
    net.r, net.rj, net.tau = np.zeros((5, 2)), np.zeros(2), 0.0
    st = dict(loom={"L": 0.0, "R": 0.0}, q=q6, qd=np.zeros(6))
    run0 = net.net.run

    def run_senses(X, n):
        X = X.copy()
        for s, ix in eyes.items():
            X[ix] = st["loom"][s]
        if feco:
            e, v = st["q"][2] / alive.Q_LIM, st["qd"][2]
            for k, x in (("claw_flex", e), ("claw_ext", -e), ("hook_flex", v), ("hook_ext", -v)):
                X[feco[k]] = 40.0 * min(1.0, max(0.0, x))
        return run0(X, n)
    net.net.run = run_senses
    th_prev, log = None, dict(t=[], touch=[], loom=[], q=[], dmin=[])
    for i in range(int(round((T_PRE + t_move + T_HOLD) / DT))):
        t = i * DT
        h = target + u * (D0 - V_HAND * min(max(0.0, t - T_PRE), t_move))
        S = sites(q6)
        dist = {p: float(np.linalg.norm(h - x)) for p, x in S.items()}
        real = np.array([K_TOUCH * max(0.0, R_HAND - dist[p]) for p in PTS])      # prawdziwy dotyk (miara)
        if feel is None:
            touch = real.copy()
        else:
            import touch_map as TM
            fw = TM.fsr_world(sim.m, JN._kin(sim, q6))
            f2 = np.array([TM.sphere_force(h, R_HAND, *fw[k]) for k in feel.discs])
            f = feel.step(f2)
            touch = np.array([f[0], f[1], 0.0]) if feel.discs[1] == "A1" else np.array([f[0], 0.0, f[1]])   # P → receptory dłoni (BM)
        if numb:
            touch = np.zeros(3)                                                   # to, co czuje mózg
        v = h - S["gripperframe"]
        d = dist["gripperframe"]
        th = 2 * np.arcsin(min(1.0, R_HAND / d))
        L = 0.0 if th_prev is None else max(0.0, (th - th_prev) / DT)
        th_prev = th
        sa = float(v[1] / np.linalg.norm(v[:2])) if np.linalg.norm(v[:2]) > 1e-6 else 0.0
        drive = 0.0 if blind else MV * min(1.0, L / L_FULL)
        st["loom"] = {"L": drive * (1 + sa) / 2, "R": drive * (1 - sa) / 2}
        dq = net.step(touch, q6[:5], st["qd"][:5], DT)
        if not frozen:
            q1 = np.clip(q6[1:4] + dq[1:4], q_lo, q_hi)
            st["qd"][1:4] = (q1 - q6[1:4]) / DT
            q6[1:4] = q1
        for k, x in (("t", t), ("touch", real.tolist()), ("loom", L), ("q", q6[1:4].tolist()),
                     ("dmin", min(dist[p] for p in PTS) - R_HAND)):
            log[k].append(x)
    Tch = np.array(log["touch"])
    touched = (Tch.max(axis=1) > 0.2)                                  # próg FSR 0,2 N
    return dict(touched_s=round(float(touched.sum() * DT), 2), t_first_touch=next((round(t, 2) for t, x in zip(log["t"], touched) if x), None),
                max_force_N=round(float(Tch.max()), 2), end_gap_cm=round(100 * log["dmin"][-1], 2),
                dq_end=np.round(np.array(log["q"][-1]) - np.array(log["q"][0]), 3).tolist(),
                loom_max=round(float(max(log["loom"])), 2), n_eye=[len(eyes["L"]), len(eyes["R"])]), log


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--glu", type=float, required=True)
    ap.add_argument("--net", default="N")
    ap.add_argument("--shuffle-seed", type=int)
    ap.add_argument("--lesion", default="none", choices=["none", "both"])
    ap.add_argument("--dir", choices=list(DIRS))
    ap.add_argument("--noise", type=float, default=2.0)
    ap.add_argument("--noise-seed", type=int)
    for f in ("blind", "numb", "frozen"):
        ap.add_argument(f"--{f}", action="store_true")
    ap.add_argument("--aim", default="palm", choices=["palm", "tips"])
    ap.add_argument("--touch", default="sim3", choices=["sim3", "hw2", "hw2p"])
    ap.add_argument("--map", default="somato", choices=["somato", "swap", "halves"])
    ap.add_argument("--r-fix", type=float, default=5100.0)
    ap.add_argument("--nerves", default="typ")
    ap.add_argument("--out")
    # tryb wsadowy: sieć budowana RAZ, potem kierunki × ziarna × warunki (wycięcie zawsze na końcu, bo zmienia W)
    ap.add_argument("--out-dir")
    ap.add_argument("--dirs", default="left,right,front")
    ap.add_argument("--noise-seeds", default="")
    ap.add_argument("--conds", default="full,frozen,blind,numb,lesion")
    ap.add_argument("--modes", help="np. sim3:palm:-,hw2:tips:somato,hw2:tips:swap (domyślnie z --touch/--aim/--map)")
    a = ap.parse_args()
    net = head.HeadLife(a.glu, a.net, a.shuffle_seed, eyes=True)
    pads0 = net.pads                               # stary podział (sim3)
    feco = alive.feco_idx(a.glu)
    mk_feel = lambda s: None  # noqa: E731
    if a.touch != "sim3" and a.out_dir is None:
        sys.exit("dotyk przez czujniki tylko w trybie wsadowym (--out-dir --modes)")

    def lesion():                                  # jak touch_natural.lesion_init: zerowane wyjścia DNg15 + DNge078
        import brainleg as B
        _, d78, d15 = B.route_ids()
        mask = np.ones(net.N)
        mask[[net.pos[b] for b in d78 + d15]] = 0.0
        import scipy.sparse as sp
        net.W = sp.csr_matrix(net.W.multiply(mask[None, :])) if sp.issparse(net.W) else net.W * mask[None, :]
        net.rep.update(lesion="both")

    def save(res, log, out):
        np.savez_compressed(out.replace(".json", ".npz"), **{k: np.array(v) for k, v in log.items()})
        with open(out, "x") as f:
            json.dump(res, f, indent=1)
        print(json.dumps(res), flush=True)

    if a.out_dir is None:                          # pojedynczy przebieg — jak 18 XI
        if a.noise_seed is None or a.dir is None or a.out is None:
            sys.exit("pojedynczy przebieg wymaga --dir --noise-seed --out")
        if os.path.exists(a.out):
            sys.exit(f"istnieje {a.out}")
        if a.lesion == "both":
            lesion()
        res, log = trial(net, a.dir, a.noise, a.noise_seed, a.blind, a.numb, a.frozen, feco=feco, aim=a.aim,
                         feel=mk_feel(a.noise_seed))
        save(dict(vars(a), **res), log, a.out)
        sys.exit(0)
    os.makedirs(a.out_dir, exist_ok=True)
    modes = [m.split(":") for m in (a.modes or f"{a.touch}:{a.aim}:{a.map}").split(",")]   # dotyk:cel:mapa

    def use(touch, mp):                            # ta sama zbudowana sieć, inny dotyk / mapa miejsc
        if touch in ("hw2", "hw2p"):               # hw2: A0 szczęka stała + A1 ruchoma; hw2p: A0 szczęka stała + P dłoń
            import touch_map as TM
            net.pads = TM.pads_for(net, mp)
            discs = ("A0", "A1") if touch == "hw2" else ("A0", "P")

            def mk(s):
                f = TM.Feel(r_fix=a.r_fix, level=a.nerves, seed=s)     # ziarno nerwów = ziarno szumu
                f.discs = discs
                return f
            return mk
        net.pads = pads0
        return lambda s: None  # noqa: E731

    base = a.net + (str(a.shuffle_seed) if a.shuffle_seed is not None else "")
    conds = a.conds.split(",")
    for cond in [c for c in conds if c != "lesion"] + (["lesion"] if "lesion" in conds else []):
        if cond == "lesion":
            lesion()
        for touch, aim, mp in modes:
            mk = use(touch, mp)
            for d in a.dirs.split(","):
                for s in map(int, a.noise_seeds.split(",")):
                    tag = base + ("" if touch == "sim3" else f"_{touch}{mp}")
                    out = os.path.join(a.out_dir, f"{tag}_g{a.glu:+.0f}_{aim}_{cond}_{d}_{s}.json")
                    if os.path.exists(out):
                        continue                   # wznowienie po przerwie
                    fl = dict(blind=cond == "blind", numb=cond == "numb", frozen=cond == "frozen")
                    res, log = trial(net, d, a.noise, s, feco=feco, aim=aim, feel=mk(s), **fl)
                    save(dict(vars(a), touch=touch, aim=aim, map=mp, cond=cond, dir=d, noise_seed=s, **fl, **res), log, out)
