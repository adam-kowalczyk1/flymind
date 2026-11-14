"""Weryfikacja kroku 2, temat 7 („przyczyna w danych, nie w kodzie”) — niezależna analiza, BEZ robota i bez ziaren.
Uruchom:  .venv/bin/python -I -B flymind/results/verification_step2_20261114/v07_data_paths.py OUT.json   (OUT nie może istnieć)

Część A (same dane MaleCNS, bez symulacji), dla każdej puli MN stawów 1–4:
  - ile synaps wejściowych ma pula w CAŁYCH danych i jaka część pochodzi od neuronów obecnych w sieci kroku 2;
  - ile bezpośrednio od pobudzanych receptorów (szczecinki padów T2 L + T1 L);
  - ile od neuronów sieci, które same dostają ≥ 5 synaps od pobudzanych receptorów („1 krok od dotyku”), z podziałem na znak;
  - najkrótsza droga (liczba kroków, krawędzie ≥ 5 synaps) od pobudzanych receptorów do puli: w sieci i w całych danych.
Część B (ten sam kod sieci co w eksperymencie, szum 0, bez MuJoCo): dotyk 1 N na oba pady przez 0,5 s → częstości pul.
Część C (odczyt plików testu): średnie częstości pul w próbach — sieć z danych kontra tasowania (czy TEN SAM kod potrafi
  pobudzić te pule przy innych połączeniach)."""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

HERE = os.path.dirname(os.path.abspath(__file__))
FLY = os.path.dirname(os.path.dirname(HERE))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(FLY, "experiments", "step2_whole_arm"))
sys.path.insert(0, FLY)
import joint_net as JN  # noqa: E402
import visual_path  # noqa: E402

NAMES = {1: ("j1+ wymach", "j1- podpór"), 2: ("j2+ Ti flex", "j2- Ti ext"), 3: ("j3+ Ta lev", "j3- Ta dep"),
         4: ("j4+ Tr flex", "j4- Tr ext")}
T = 5


def bfs(adj, src, targets, maxhop=6):
    seen, front, hop, reached = set(src), set(src), 0, {}
    while front and hop < maxhop:
        hop += 1
        nxt = set()
        for u in front:
            nxt |= adj.get(u, set())
        nxt -= seen
        seen |= nxt
        for name, tg in targets.items():
            if name not in reached and nxt & tg:
                reached[name] = dict(hops=hop, n_mn_reached=len(nxt & tg))
        front = nxt
    return reached


def main(out_path):
    if os.path.exists(out_path):
        sys.exit(f"istnieje {out_path}")
    out = {}
    W = ds.dataset(visual_path.WEIGHTS, format="ipc")
    for glu in (-1.0, 1.0):
        spec, idx, rep = JN.build_net(glu, 0.2, "fl")
        bodies = [int(b) for b in spec.bodies]
        inb = set(bodies)
        sign = dict(zip(bodies, np.asarray(spec.sign, float)))
        stim = {bodies[i] for name in ("padsT2", "padsT1") for half in idx[name] for i in half}
        pools = {NAMES[j][k]: {bodies[i] for i in idx["pools"][j][k]} for j in NAMES for k in (0, 1)}
        allmn = sorted({b for v in pools.values() for b in v})
        res = dict(N=rep["N"], W_sha256=rep["W_sha256"], n_stim=len(stim), pools={})
        if glu == -1.0:                                            # część A nie zależy od znaku poza kolumnami znaków
            inn = W.to_table(filter=ds.field("body_post").isin(allmn)).to_pandas()
            s_out = W.to_table(filter=ds.field("body_pre").isin(sorted(stim))).to_pandas()
            hop1 = s_out.groupby("body_post").weight.sum()
            hop1 = set(int(b) for b in hop1[hop1 >= T].index)
            # graf w sieci (krawędzie ≥ T) i w całych danych (BFS warstwami, zapytania do pliku)
            e_in = W.to_table(filter=ds.field("body_pre").isin(bodies) & ds.field("body_post").isin(bodies)
                              & (ds.field("weight") >= T)).to_pandas()
            adj = {}
            for u, v in zip(e_in.body_pre.astype(int), e_in.body_post.astype(int)):
                adj.setdefault(u, set()).add(v)
            net_reach = bfs(adj, stim, pools)
            full_reach, seen, front = {}, set(stim), set(stim)
            for hop in range(1, 5):
                t = W.to_table(filter=ds.field("body_pre").isin(sorted(front)) & (ds.field("weight") >= T)).to_pandas()
                nxt = set(t.body_post.astype(int)) - seen
                seen |= nxt
                for name, tg in pools.items():
                    if name not in full_reach and nxt & tg:
                        full_reach[name] = dict(hops=hop, n_mn_reached=len(nxt & tg))
                front = nxt
                if len(full_reach) == len(pools):
                    break
            out["A_structure"] = dict(threshold_syn=T, n_hop1_all=len(hop1), n_hop1_in_net=len(hop1 & inb), pools={})
        for name, mn in pools.items():
            d = inn[inn.body_post.isin(mn)]
            pre = d.body_pre.astype(int)
            tot = int(d.weight.sum())
            w_net = d[pre.isin(inb)]
            w_h1 = d[pre.isin(hop1 & inb)]
            sg = w_h1.body_pre.astype(int).map(sign)
            rec = dict(n_mn=len(mn), syn_total_data=tot,
                       syn_from_net=int(w_net.weight.sum()), frac_from_net=round(float(w_net.weight.sum()) / max(tot, 1), 3),
                       syn_direct_from_stim=int(d[pre.isin(stim)].weight.sum()),
                       syn_from_hop1_in_net=int(w_h1.weight.sum()),
                       frac_hop1_of_total=round(float(w_h1.weight.sum()) / max(tot, 1), 3),
                       hop1_exc=int(w_h1.weight[sg > 0].sum()), hop1_inh=int(w_h1.weight[sg < 0].sum()),
                       hop1_zero_sign=int(w_h1.weight[sg == 0].sum()),
                       syn_from_hop1_outside_net=int(d[pre.isin(hop1 - inb)].weight.sum()))
            if glu == -1.0:
                rec.update(path_in_net=net_reach.get(name), path_full_data=full_reach.get(name))
                out["A_structure"]["pools"][name] = rec
            res["pools"][name] = dict(hop1_exc=rec["hop1_exc"], hop1_inh=rec["hop1_inh"], hop1_zero=rec["hop1_zero_sign"])
        # część B: ten sam kod sieci, dotyk 1 N na oba pady, 0,5 s, szum 0
        ac = JN.ArmCfg(version="v07", joints=(1, 2, 3), roll=True, inputs=("padsT2", "padsT1"), in_rule="fl")
        net = JN.ArmNet(glu, ac)
        assert net.rep["W_sha256"] == rep["W_sha256"]
        for _ in range(50):
            net.step(np.array([1.0, 1.0, 0.0]), np.zeros(6), np.zeros(6))
        res["B_rates_Hz_after_0.5s_touch"] = {NAMES[j][k]: round(float(net.r[j, k]), 2) for j in NAMES for k in (0, 1)}
        out[f"glu{glu:+.0f}"] = res
        print("Glu", glu, json.dumps(res["B_rates_Hz_after_0.5s_touch"], ensure_ascii=False))
    # część C: częstości pul w próbach testowych (tylko odczyt)
    R = os.path.join(FLY, "results", "step2_whole_arm_20261113")
    C = {}
    for sub, pre in (("lift_b", None), ("elbow_c", "c_test_"), ("wrist_d", "d_test_"), ("whole_arm_5", "arm_test_")):
        if pre is None:
            continue
        for p in sorted(glob.glob(os.path.join(R, sub, "test", pre + "[NS]*_g*.json"))):
            runs = json.load(open(p))["runs"]
            m = [r["mean_rates_active"] for r in runs if r.get("mean_rates_active")]
            if m:
                a = np.mean(np.array(m, float), axis=0).round(1)
                C[os.path.basename(p)[:-5]] = {NAMES[j][k]: float(a[j, k]) for j in NAMES for k in (0, 1)}
    out["C_mean_pool_rates_in_test_trials_Hz"] = C
    with open(out_path, "x") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    for name, r in out["A_structure"]["pools"].items():
        print(f"{name:13s}", {k: v for k, v in r.items()})


if __name__ == "__main__":
    main(sys.argv[1])
