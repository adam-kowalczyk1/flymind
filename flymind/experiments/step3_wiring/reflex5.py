"""Krok 5 — nadgarstek: „dotyk przy głowie → cofnij dłoń nadgarstkiem”. Wariant próby z reflex.py (ten plik go nie zmienia).
Różnice względem kroku 4:
  - sieć = „pre” + 69 neuronów BM (szczecinki mechanosensoryczne głowy, cb_sensory) + 2 neurony zstępujące DNge078
    (droga znaleziona w danych: BM → DNge078 → Ta levator MN nogi T1 L; `wrist_screen.py`, `wrist_dn_inputs.py`);
  - czujnik dłoni robota (cs_palm, obok kamery) → neurony BM (40 mV/N, maks. 40 mV) ZAMIAST szczecinek nogi T1;
  - pady → szczecinki nogi T2 jak dotąd. Wyjścia bez zmian: szczęka z pul T2, stawy 1–3 z pul T1 (staw 3 = pule stępu).
Tasowania: F = swobodne (równa waga); L = zachowujące warstwy (receptory w tym BM / interneurony w tym DN / MN);
           B = jak L, ale BM i DN jako osobne grupy (zachowuje sumy połączeń BM → DN → reszta).
Uruchom jak reflex.py: reflex5.py --net N|F|L|B [--shuffle-seed S] --glu ±1 --seed SEED --poses P --tag TAG --out DIR"""
import hashlib
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import explore_specificity as ES  # noqa: E402
import nets  # noqa: E402
import nets2  # noqa: E402
import reflex as R  # noqa: E402
import side_shuffle  # noqa: E402

JN = nets.JN
TEST5 = {21701}


def head_route():
    a = pd.read_feather(nets.visual_path.ANN, columns=["bodyId", "type", "superclass"])
    bm = [int(b) for b in a.bodyId[(a.type == "BM") & (a.superclass == "cb_sensory")]]
    dn = [int(b) for b in a.bodyId[a.type == "DNge078"]]
    return bm, dn


class HeadNet(R.TwoNet):
    def __init__(self, glu, kind="N", shuffle_seed=None, rule="pre"):
        bm, dn = head_route()
        spec, idx, rep, layer, pos, m = nets2.build_ext(glu, bm + dn)
        bodies = [None] * len(pos)
        for b, i in pos.items():
            bodies[i] = b
        t2, t1 = ES.mn_sets(bodies, m)
        layer = np.array(layer, object)
        for b in dn:
            layer[pos[b]] = "I"
        self.rep = dict(rep, kind=kind, shuffle_seed=shuffle_seed, n_BM=len(bm), n_DNge078=len(dn))
        if kind != "N":
            g = layer.copy()
            if kind == "B":
                for b in bm:
                    g[pos[b]] = "S_BM"
                for b in dn:
                    g[pos[b]] = "I_DN"
            spec = JN.visual_path.shuffle(spec, shuffle_seed, equal_weight=True) if kind == "F" else \
                side_shuffle.shuffle_within_side(spec, np.array(g, str), shuffle_seed)
            self.rep["W_sha256_shuffled"] = hashlib.sha256(np.ascontiguousarray(spec.W).tobytes()).hexdigest()
        mn2 = m["g2"]["MN"]
        self.press = [pos[int(b)] for b in mn2.get("Ti extensor MN", [])]
        self.release = [pos[int(b)] for k in ("Ti flexor MN", "Acc. ti flexor MN") for b in mn2.get(k, [])]
        self.pads, self.palm = idx["padsT2"], [pos[b] for b in bm]          # dłoń → szczecinki głowy
        self.pools = {j: idx["pools"][j] for j in (1, 2, 3)}
        self.W, self.N = spec.W, spec.W.shape[0]
        self.rep.update(press_MN=len(self.press), release_MN=len(self.release), palm_receptors=len(self.palm),
                        pad_receptors=[len(x) for x in self.pads])
        self.reset()


T_W5 = 0.5            # s sterowania siecią w próbie dłoni (krótko: odruch jest „w stronę dotyku” i zwiększa nacisk)
DQ_MOVE = 0.02        # rad: minimalny ruch nadgarstka w kierunku unoszenia
DQ_STILL = 0.01       # rad: maksymalny ruch stawu, który ma pozostać w spoczynku


def trial5(item, seed, kind, net, fc, ac):
    """W5: dotyk dłoni → rusza się nadgarstek (staw 3, kierunek unoszenia), bark i łokieć stoją, szczęka nie zaciska.
    C5: dotyk palców → szczęka zaciska i trzyma 2 s (jak próba C kroku 4), nadgarstek stoi."""
    oh = R.oh
    net.reset()
    w = JN.ForceWorld([item], seed)
    ctl = JN.ArmGrip(w, oh.OHCfg(), R.JawView(net), "snn:legT2L", fc, "N", net, ac)
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
        if kind == "W":
            w.phase = "press"
            q_g = P["descend"][-1]
            path = JN.plan(sim, q_g, cs(q_g) - [0, 0, JN.clearance(sim, q_g) - R.Z_LOW], point="cs_fixed", jaw_open=P["q_pre"], cfg=ctl.rcfg)
            for x in oh.profile(path, ctl.obs.q, R.V_PRESS, c.a_max, ctl.lim.dt):
                ctl.tick(x, "open")
                tgt = np.asarray(x)[:5].copy()
                if ctl.obs.touch[2] >= R.F_ON:
                    break
            rec["palm_at_handover"] = round(float(ctl.obs.touch[2]), 3)
            if ctl.obs.touch[2] < R.F_ON:
                return dict(rec, reason="no_palm_contact")
        else:
            w.phase = "grasp"
        rec["valid"] = True
        w.phase = "net"
        ctl.active, ctl.qc = {1, 2, 3}, {j: float(tgt[j]) for j in (1, 2, 3)}
        q0, z0, g0, a0 = dict(ctl.qc), float(cs(ctl.obs.q)[2]), ctl.guard, ctl.act_ticks
        ctl.eng, max_eng, engaged = 0, 0, kind == "W"
        palm, pads, tau = [], [], []
        if kind == "C":
            engaged = ctl.wait(fc.search_max, tgt, "search", until=lambda: ctl.eng >= fc.engage_ticks)
            rec["engaged"] = bool(engaged)
        if engaged:
            for _ in range(int(round((T_W5 if kind == "W" else R.T_NET) / ctl.lim.dt))):
                ctl.tick(tgt, "fly")
                max_eng = max(max_eng, ctl.eng)
                palm.append(float(ctl.obs.touch[2]))
                pads.append(float(max(ctl.obs.touch[:2])))
                tau.append(float(ctl.tau_fly))
        dq = {j: ctl.qc[j] - q0[j] for j in (1, 2, 3)}
        ctl.active = set()
        gfrac = (ctl.guard - g0) / max(ctl.act_ticks - a0, 1)
        fmax = max(w.fmax.values(), default=0.0)
        lev = float(JN.UP[3] * dq[3])                                # > 0 = kierunek unoszenia końcówki (jak w kroku 2)
        rec.update(dq1=round(dq[1], 4), dq2=round(dq[2], 4), dq3_lev=round(lev, 4), max_eng=max_eng, guard_frac=round(gfrac, 4), fmax=fmax,
                   mean_rates=(ctl.rsum / max(ctl.act_ticks, 1)).round(2).tolist())
        if engaged and tau:
            safe = gfrac <= 0.10 and fmax <= 5.0
            rec.update(palm_max=round(max(palm), 2), tau_max=round(max(tau), 3), tau_end=round(float(np.mean(tau[-20:])), 3),
                       pads_end=round(float(np.mean(pads[-20:])), 3), dz_mm=round((float(cs(ctl.obs.q)[2]) - z0) * 1e3, 2))
            if kind == "W":
                rec["success"] = bool(lev >= DQ_MOVE and abs(dq[1]) <= DQ_STILL and abs(dq[2]) <= DQ_STILL and max_eng < fc.engage_ticks and safe)
            else:
                rec["success"] = bool(rec["tau_end"] >= fc.tau_engage and rec["pads_end"] > 0.05 and rec["dz_mm"] >= -2.0
                                      and abs(dq[3]) <= DQ_STILL and safe)
        return rec
    except (JN.Fail, JN.ReachError) as e:
        return dict(rec, reason=f"{type(e).__name__}: {getattr(e, 'reason', '')} {e}"[:200])


if __name__ == "__main__":
    if "--seed" in sys.argv and int(sys.argv[sys.argv.index("--seed") + 1]) in TEST5 and not os.environ.get("STEP5_FINAL_TEST"):
        sys.exit("ziarna testowe kroku 5 tylko w teście końcowym (STEP5_FINAL_TEST=1)")
    for i, x in enumerate(sys.argv):                          # rodzina B: reflex.py zna tylko N/F/L/G → przekaż jako „G” i podmień
        if x == "--net" and sys.argv[i + 1] == "B":
            sys.argv[i + 1] = "G"
            _orig = HeadNet.__init__
            HeadNet.__init__ = lambda self, glu, kind="N", shuffle_seed=None, rule="pre", _o=_orig: _o(self, glu, "B" if kind == "G" else kind, shuffle_seed, rule)
    R.TwoNet = HeadNet
    R.trial = trial5
    R.main()
