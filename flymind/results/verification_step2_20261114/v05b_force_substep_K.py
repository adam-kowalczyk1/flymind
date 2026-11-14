"""Temat 5, dopełnienie: te same sceny co v05 (ziarno 20954), ale ramię K (klasyczne podniesienie; szczęka = ta sama sieć T2 L).
Cel: czy siła przedmiot↔blat przy trzymaniu (v05: do 27 N) pochodzi od sieci ramienia, czy występuje też bez niej.
Uruchom: .venv/bin/python -I -B .../v05b_force_substep_K.py OUT.json"""
import json
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v05_force_substep as V  # noqa: E402

JN, oh, sm, M = V.JN, V.oh, V.sm, V.M


def main(out_path):
    if os.path.exists(out_path):
        sys.exit(f"istnieje {out_path}")
    V.mujoco.mj_step = V._probe
    JN.ForceWorld = V.ProbeWorld
    items, out = oh.SETS["base"], []
    ac = JN.ArmCfg(version="v05b", joints=(1, 2, 3), roll=True, inputs=("padsT2", "padsT1"), in_rule="fl")
    fc = sm.FlyCfg(glu_sign=-1.0, trigger="search")
    jaw = sm.LegJaw(fc, touch=True, proprio=False)
    for it in [x for x in items if "/".join(x) in V.ITEMS]:
        V.reset_m()
        r = JN.run_trial(it, V.SEED * 1000 + items.index(it) * 10, "K", jaw, None, fc, ac)
        rec = dict(arm="K", glu=-1.0, item=r["item"], seed=r["seed"], lift=bool(r["truth"]["lift"]), placed=bool(r["success"]),
                   reasons=r["reasons"], tick_fmax_N=r["fmax"], substep_arm_table_fmax_N=round(M["arm"], 4),
                   substeps=M["n_sub"], substep_heldobj_table_fmax_N=round(M["obj"], 3))
        out.append(rec)
        print("K", rec, flush=True)
    with open(out_path, "x") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1])
