"""Krok 4 — „dwa czucia, dwa odruchy”: JEDNA sieć (reguła „pre”) steruje naraz szczęką i stawami 1–3 ramienia.
Kanały czuciowe (tylko receptory):  pady chwytaka → szczecinki nogi środkowej T2 L (jak FlyJaw: pad stały / ruchomy = połowy)
                                    czujnik dłoni (cs_palm) → szczecinki nogi przedniej T1 L (wszystkie)
Wyjścia:  moment szczęki = 0,005 N·m/Hz · (Ti extensor − Ti flexor/Acc. ti flexor nogi T2 L)      (jak LegJaw)
          stawy 1–3: przyrost celu = znak · 0,005 · dt · (pula POS − pula NEG nogi T1 L)           (jak krok 2/3)
Próby (podjazd klasyczny, identyczny dla każdej sieci; potem 2 s sterowania siecią):
  W „wycofanie”: otwarty chwytak schodzi nad wysokim przedmiotem, aż dłoń go dotknie (≥ F_ON).  Oczekiwane: ramię odciąża
                 dłoń i NIE zaciska szczęki.
  C „chwyt”:     standardowy dosuw; szczęka domykana klasycznie do zaciśnięcia przez sieć (jak w etapie dotyku), potem sieć
                 trzyma 2 s.  Oczekiwane: sieć zaciska i trzyma, ramię nie wciska przedmiotu w stół.
Niczego nie zmienia w modułach wspólnych ani w kroku 2 (podklasa joint_net.ArmGrip, sieć z nets.py).
Uruchom: reflex.py --net N|F|L|G [--shuffle-seed S] --glu ±1 --seed SEED --poses P --tag TAG --out DIR"""
import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import explore_specificity as ES  # noqa: E402
import nets  # noqa: E402
import side_shuffle  # noqa: E402
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402

JN = nets.JN
oh, sm = JN.oh, JN.sm
TEST4 = {21501}
ITEMS = {"W": [("cyl_thin", m) for m in oh.BASE_MATS],   # wysoki cienki walec (60 mm): jedyny kształt katalogu, na którym dłoń
         "C": [("cyl", m) for m in oh.BASE_MATS]}        # (51 mm nad końcem padów) może usiąść; chwyt: walec podstawowy
F_ON = 1.0            # N: nacisk dłoni kończący zejście (przy 40 mV/N = pełne pobudzenie receptorów)
T_NET = 2.0           # s sterowania siecią
Z_LOW = 0.006         # m: najniższe zejście padów (strażnik ramienia ma 5 mm); dłoń dotyka walca 60 mm przy ok. 9 mm
V_PRESS = 0.10        # rad/s: wolne zejście do kontaktu


class TwoNet:
    def __init__(self, glu, kind="N", shuffle_seed=None, rule="pre"):
        bodies, m = nets.bodies_for(rule)
        spec, idx, rep, layer = nets.build_rule(glu, 0.2, rule)
        t2, t1 = ES.mn_sets(bodies, m)
        self.rep = dict(rep, kind=kind, shuffle_seed=shuffle_seed)
        if kind != "N":
            g = np.array(layer, object)
            if kind == "G":
                pos0 = {b: i for i, b in enumerate(bodies)}
                for b in m["sens2"]:
                    g[pos0[b]] = "S_T2"
                for b in m["sens1"]:
                    g[pos0[b]] = "S_T1"
                g[t2], g[t1] = "M_T2", "M_T1"
            spec = JN.visual_path.shuffle(spec, shuffle_seed, equal_weight=True) if kind == "F" else \
                side_shuffle.shuffle_within_side(spec, np.array(g, str), shuffle_seed)
            self.rep["W_sha256_shuffled"] = hashlib.sha256(np.ascontiguousarray(spec.W).tobytes()).hexdigest()
        pos = {b: i for i, b in enumerate(bodies)}
        mn2 = m["g2"]["MN"]
        self.press = [pos[int(b)] for b in mn2.get("Ti extensor MN", [])]
        self.release = [pos[int(b)] for k in ("Ti flexor MN", "Acc. ti flexor MN") for b in mn2.get(k, [])]
        self.pads, self.palm = idx["padsT2"], [i for h in idx["padsT1"] for i in h]
        self.pools = {j: idx["pools"][j] for j in (1, 2, 3)}
        self.W, self.N = spec.W, spec.W.shape[0]
        self.rep.update(press_MN=len(self.press), release_MN=len(self.release), palm_receptors=len(self.palm),
                        pad_receptors=[len(x) for x in self.pads])
        self.reset()

    def reset(self):
        self.net = SparseALIF(JN.LB._W(self.W), ALIFParams(), None)       # szum 0
        self.r, self.rj, self.tau = np.zeros((5, 2)), np.zeros(2), 0.0

    def step(self, touch, q, qd, dt=0.01, tau_r=0.05):                     # wołane przez ArmGrip.tick jako „drv”
        X = np.zeros(self.N)
        for ix, f in zip(self.pads, touch[:2]):
            X[ix] = min(40.0, 40.0 * max(0.0, float(f)))
        X[self.palm] = min(40.0, 40.0 * max(0.0, float(touch[2])))
        s = self.net.run(X, 10)
        dq = np.zeros(5)
        for j, (p, n) in self.pools.items():
            now = np.array([s[:, p].mean(), s[:, n].mean()]) * 1000.0
            self.r[j] += dt / tau_r * (now - self.r[j])
            dq[j] = JN.SIGN[j] * 0.005 * dt * float(self.r[j, 0] - self.r[j, 1])
        now = np.array([s[:, self.press].mean(), s[:, self.release].mean()]) * 1000.0
        self.rj += dt / tau_r * (now - self.rj)
        self.tau = 0.005 * float(self.rj[0] - self.rj[1])
        return dq


class JawView:                                                             # „driver” szczęki: moment z tej samej sieci
    def __init__(self, net):
        self.net, self.t = net, (0.0, 0.0, 0.0)

    def reset(self):
        pass

    def step(self, touch, qj, qdj):
        return self.net.tau


def trial(item, seed, kind, net, fc, ac):
    net.reset()
    w = JN.ForceWorld([item], seed)
    ctl = JN.ArmGrip(w, oh.OHCfg(), JawView(net), "snn:legT2L", fc, "N", net, ac)
    sim, c = ctl.sim, ctl.cfg
    cs = lambda q: JN._kin(sim, q).site("cs_fixed").xpos.copy()  # noqa: E731
    rec = dict(item="/".join(item), seed=seed, kind=kind, valid=False, success=False)
    try:
        p = ctl.wait_percept()
        if p is None:
            return dict(rec, reason="no_percept")
        P = ctl.plan(p)
        ctl.grip = oh.ClassicGrip(oh.GripCfg(q_open=P["q_pre"]))
        w.phase = "approach"
        ctl.follow(P["move"], "preshape")
        ctl.wait(c.open_max, np.asarray(P["move"][-1])[:5], "preshape", until=lambda: ctl.obs.q[5] >= P["q_pre"] - c.jaw_tol)
        ctl.follow(P["descend"], "open")
        tgt = np.asarray(P["descend"][-1])[:5].copy()
        log = dict(palm=[], pads=[], tau=[], z=[])
        if kind == "W":
            w.phase = "press"
            q_g = P["descend"][-1]
            path = JN.plan(sim, q_g, cs(q_g) - [0, 0, JN.clearance(sim, q_g) - Z_LOW], point="cs_fixed", jaw_open=P["q_pre"], cfg=ctl.rcfg)
            for x in oh.profile(path, ctl.obs.q, V_PRESS, c.a_max, ctl.lim.dt):
                ctl.tick(x, "open")
                tgt = np.asarray(x)[:5].copy()
                if ctl.obs.touch[2] >= F_ON:
                    break
            rec.update(palm_at_handover=round(float(ctl.obs.touch[2]), 3), pads_at_handover=np.round(ctl.obs.touch[:2], 3).tolist())
            if ctl.obs.touch[2] < F_ON:
                return dict(rec, reason="no_palm_contact")
        else:
            w.phase = "grasp"
        rec["valid"] = True
        w.phase = "net"
        ctl.active, ctl.qc = {1, 2, 3}, {j: float(tgt[j]) for j in (1, 2, 3)}
        z0, g0, a0, engaged = float(cs(ctl.obs.q)[2]), ctl.guard, ctl.act_ticks, kind == "W"
        ctl.eng = 0
        max_eng = 0
        if kind == "C":                                              # domykanie klasyczne do zaciśnięcia przez sieć
            engaged = ctl.wait(fc.search_max, tgt, "search", until=lambda: ctl.eng >= fc.engage_ticks)
            rec["engaged"] = bool(engaged)
        if engaged:
            for _ in range(int(round(T_NET / ctl.lim.dt))):
                ctl.tick(tgt, "fly")
                max_eng = max(max_eng, ctl.eng)
                o = ctl.obs
                log["palm"].append(float(o.touch[2]))
                log["pads"].append(float(max(o.touch[:2])))
                log["tau"].append(float(ctl.tau_fly))
                log["z"].append(float(cs(o.q)[2]))
        ctl.active = set()
        n_act = max(ctl.act_ticks - a0, 1)
        gfrac = (ctl.guard - g0) / n_act
        fmax = max(w.fmax.values(), default=0.0)
        rec.update(guard_frac=round(gfrac, 4), fmax=fmax, max_eng=max_eng,
                   mean_rates=(ctl.rsum / max(ctl.act_ticks, 1)).round(2).tolist())
        if engaged and log["z"]:
            end = slice(-20, None)
            rec.update(dz_mm=round((log["z"][-1] - z0) * 1e3, 2), palm_end=round(float(np.mean(log["palm"][end])), 3),
                       pads_end=round(float(np.mean(log["pads"][end])), 3), tau_max=round(max(log["tau"]), 3),
                       tau_end=round(float(np.mean(log["tau"][end])), 3), tau_min=round(min(log["tau"]), 3))
            safe = gfrac <= 0.10 and fmax <= 5.0
            if kind == "W":
                rec["success"] = bool(rec["palm_end"] < 0.05 and rec["dz_mm"] >= 0.0 and max_eng < fc.engage_ticks and safe)
            else:
                rec["success"] = bool(rec["tau_end"] >= fc.tau_engage and rec["pads_end"] > 0.05 and rec["dz_mm"] >= -2.0 and safe)
        return rec
    except (JN.Fail, JN.ReachError) as e:
        return dict(rec, reason=f"{type(e).__name__}: {getattr(e, 'reason', '')} {e}"[:200])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", required=True, choices=("N", "F", "L", "G"))
    ap.add_argument("--shuffle-seed", type=int)
    ap.add_argument("--glu", type=float, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--poses", type=int, default=6)
    ap.add_argument("--kinds", default="W,C")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.seed in TEST4 and not os.environ.get("STEP4_FINAL_TEST"):
        sys.exit("ziarna testowe kroku 4 tylko w teście końcowym (STEP4_FINAL_TEST=1)")
    if (a.net == "N") != (a.shuffle_seed is None):
        sys.exit("--shuffle-seed wymagane dokładnie dla sieci F/L/G")
    if not 1 <= a.poses <= 9:
        sys.exit("--poses 1…9")
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, a.tag + ".json")
    if os.path.exists(path):
        sys.exit(f"istnieje {path}")
    t0 = time.time()
    net = TwoNet(a.glu, a.net, a.shuffle_seed)
    fc = sm.FlyCfg(glu_sign=a.glu, trigger="search")
    ac = JN.ArmCfg(version="reflex", joints=(1, 2, 3), roll=False, inputs=(), in_rule="fl")
    runs = []
    for mi in range(len(oh.BASE_MATS)):
        for k in range(a.poses):
            for kind in a.kinds.split(","):                          # ziarna sceny: W = seed·1000 + mat·10 + poza; C = to samo + 100
                it = ITEMS[kind][mi]
                r = trial(it, a.seed * 1000 + (100 if kind == "C" else 0) + mi * 10 + k, kind, net, fc, ac)
                runs.append(r)
                print(f"{r['item']:14s} {k} {kind}: valid {r['valid']!s:5} OK {r['success']!s:5} "
                      + " ".join(f"{x}={r[x]}" for x in ("dz_mm", "palm_end", "pads_end", "tau_max", "tau_end", "max_eng", "guard_frac", "fmax", "reason", "palm_at_handover") if x in r), flush=True)
    out = dict(tag=a.tag, net=a.net, glu=a.glu, shuffle_seed=a.shuffle_seed, seed=a.seed, poses=a.poses, rep=net.rep, argv=sys.argv,
               params=dict(F_ON=F_ON, T_NET=T_NET, Z_LOW=Z_LOW, V_PRESS=V_PRESS), wall_s=round(time.time() - t0, 1),
               code_sha256={f: hashlib.sha256(open(os.path.join(HERE, f), "rb").read()).hexdigest() for f in ("reflex.py", "nets.py")},
               runs=runs)
    with open(path, "x") as f:
        json.dump(out, f, indent=1, ensure_ascii=False, default=float)
    print(f"zapisano {path} | W {sum(r['success'] for r in runs if r['kind'] == 'W')}/{sum(r['valid'] for r in runs if r['kind'] == 'W')} "
          f"| C {sum(r['success'] for r in runs if r['kind'] == 'C')}/{sum(r['valid'] for r in runs if r['kind'] == 'C')}")


if __name__ == "__main__":
    main()
