"""Weryfikacja kroku 2, temat 5 (miernik siły ramię↔blat). Diagnostyka, nie test. Nic nie zmienia w plikach projektu:
pomiar niezależny jest dopinany W PAMIĘCI (opakowanie mujoco.mj_step + podklasa ForceWorld tylko w tym procesie).

Pytanie: czy „0 N” z testów może być skutkiem tego, że lift_b.ForceWorld mierzy siłę tylko raz na takt 10 ms (po 10 krokach
fizyki) i tylko dla par ramię↔blat?

Niezależny pomiar w KAŻDYM kroku fizyki (1 ms):
  f_arm_table   suma |siły normalnej| kontaktów ramię(+pady)↔blat           (to samo, co ForceWorld, ale 10× gęściej)
  f_obj_table   suma dla kontaktów przedmiot↔blat w czasie, gdy przedmiot dotyka padów (docisk przez trzymany przedmiot)
Część P (kontrola pozytywna, bez sieci, bez ziaren): ramię celowo opuszczane na blat jak w force_probe.py.
Część T (próby): całe ramię z sieci z danych (N), Glu ±1, ziarno 20954 (wpisane do SEED_REGISTRY przed uruchomieniem).

Uruchom:  .venv/bin/python -I -B .../v05_force_substep.py OUT.json   (OUT nie może istnieć)"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FLY = os.path.dirname(os.path.dirname(HERE))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(FLY, "experiments", "step2_whole_arm"))
sys.path.insert(0, FLY)
import mujoco  # noqa: E402

import joint_net as JN  # noqa: E402
import object_handling as oh  # noqa: E402
import sensory_manipulation as sm  # noqa: E402

SEED = 20954
ITEMS = ["cube_S/hard_grip", "cube_S/light", "cyl/hard_grip", "sphere/hard_grip", "long/heavy", "flat/hard_grip", "cube_L/heavy", "wedge/mid"]
CUR = {"w": None}
M = dict(arm=0.0, obj=0.0, n_sub=0, n_sub_arm=0)
_f6 = np.zeros(6)
_orig = mujoco.mj_step


def _probe(m, d, *a, **k):
    r = _orig(m, d, *a, **k)
    w = CUR["w"]
    if w is None or d is not w.sim.d:
        return r
    fa = fo = 0.0
    pad_obj = set()
    pairs = []
    for i in range(d.ncon):
        g1, g2 = d.contact.geom[i]
        a_, b_ = w.lab[g1], w.lab[g2]
        pairs.append((i, a_, b_))
        for x, y in ((a_, b_), (b_, a_)):
            if x in oh.PADS and y not in oh.ARMSET and y not in ("table", "box"):
                pad_obj.add(y)
    for i, a_, b_ in pairs:
        if "table" not in (a_, b_):
            continue
        other = b_ if a_ == "table" else a_
        if other in oh.ARMSET:
            mujoco.mj_contactForce(m, d, i, _f6)
            fa += abs(float(_f6[0]))
        elif other in pad_obj:
            mujoco.mj_contactForce(m, d, i, _f6)
            fo += abs(float(_f6[0]))
    M["n_sub"] += 1
    M["n_sub_arm"] += int(fa > 0)
    M["arm"], M["obj"] = max(M["arm"], fa), max(M["obj"], fo)
    return r


class ProbeWorld(JN.ForceWorld):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        CUR["w"] = self


def reset_m():
    M.update(arm=0.0, obj=0.0, n_sub=0, n_sub_arm=0)


def main(out_path):
    if os.path.exists(out_path):
        sys.exit(f"istnieje {out_path}")
    mujoco.mj_step = _probe
    out = dict(seed=SEED, items=ITEMS, positive_control=[], trials=[])
    # P: kontrola pozytywna jak force_probe.py (bez sieci, bez bezpiecznika)
    w = ProbeWorld([oh.SETS["base"][0]], 1)
    assert w.sim.mj.mj_step is _probe, "symulator nie używa opakowanego mj_step — pomiar niezależny nie działa"
    w.phase = "probe"
    q = np.array(oh.OHCfg.home, float)
    for dq in np.arange(0.0, 1.21, 0.1):
        w.fmax = {}
        reset_m()
        for _ in range(100):
            w.step(np.r_[q[:1], q[1] + dq, q[2:5]], 0.0)
        rec = dict(dq1=round(float(dq), 2), tick_fmax_N=w.fmax.get("probe", 0.0), substep_fmax_N=round(M["arm"], 4),
                   substeps=M["n_sub"], substeps_with_contact=M["n_sub_arm"])
        out["positive_control"].append(rec)
        print("P", rec, flush=True)
    # T: próby całego ramienia z siecią z danych
    JN.ForceWorld = ProbeWorld
    items = oh.SETS["base"]
    names = ["/".join(x) for x in items]
    missing = [x for x in ITEMS if x not in names]
    if missing:
        print("brak w zestawie (pomijam):", missing, "; dostępne np.:", names[:12], flush=True)
    for glu in (-1.0, 1.0):
        ac = JN.ArmCfg(version="v05", joints=(1, 2, 3), roll=True, inputs=("padsT2", "padsT1"), in_rule="fl")
        fc = sm.FlyCfg(glu_sign=glu, trigger="search")
        jaw = sm.LegJaw(fc, touch=True, proprio=False)
        drv = JN.ArmNet(glu, ac)
        for it in [x for x in items if "/".join(x) in ITEMS]:
            reset_m()
            r = JN.run_trial(it, SEED * 1000 + items.index(it) * 10, "N", jaw, drv, fc, ac)
            rec = dict(glu=glu, item=r["item"], seed=r["seed"], lift=bool(r["truth"]["lift"]), placed=bool(r["success"]),
                       reasons=r["reasons"], guard=r["guard"], tick_fmax_N=r["fmax"], tick_fmax_by_phase=r["fmax_by_phase"],
                       unwanted_arm_table=r["unwanted"]["arm_table"], substep_arm_table_fmax_N=round(M["arm"], 4),
                       substeps=M["n_sub"], substeps_with_arm_table_contact=M["n_sub_arm"],
                       substep_heldobj_table_fmax_N=round(M["obj"], 3))
            out["trials"].append(rec)
            print("T", rec, flush=True)
    with open(out_path, "x") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1])
