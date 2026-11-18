"""Testy etapu „wzrok w pętli” (vision_manipulation.py). Uruchom z katalogu tymczasowego:
    .venv/bin/python -I -B flymind/test_vision_manipulation.py
Ziarna: tylko pula rozwojowa 101 xxx (nie pokrywa się z benchmarkiem 100 xxx)."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import object_handling as oh  # noqa: E402
import sensory_manipulation as sm  # noqa: E402
import vision_manipulation as vm  # noqa: E402

FC = sm.FlyCfg(trigger="search")
MADE = {}


def arm(name):
    if name not in MADE:
        MADE[name] = vm.make(name, FC)
    return MADE[name]


def trial(name, item, seed, **patch):
    f, drv, _ = arm(name)

    def factory(w, cfg):
        c = f(w, cfg)
        for k, v in patch.items():
            setattr(c, k, v)
        return c
    r = vm.run_series([item], seed, factory, drv)
    r.pop("lat")
    return r


def strip(x):
    if isinstance(x, dict):
        return {k: strip(v) for k, v in x.items() if "wall" not in k and k not in ("vision", "lat")}
    return [strip(v) for v in x] if isinstance(x, list) else x


def test_V1_camera_percept_matches_truth_on_prisms():
    for it, seed in ((("cube_M", "mid"), 101090), (("long", "heavy"), 101320), (("flat", "mid"), 101290)):
        r = trial("A_cam", it, seed)
        e = vm.perr(r["vision"][0])
        assert e["pos_mm"] < 1.5 and abs(e["w_mm"]) < 1.5 and abs(e["l_mm"]) < 1.5 and abs(e["h_mm"]) < 3, (it, e)


def test_V2_oracle_values_do_not_reach_control():
    """Wartości wyroczni podmienione na NaN: przebieg (ruch, wynik, czasy symulacji) musi być identyczny."""
    a = trial("E_vis_touch", ("cube_M", "mid"), 101090)
    orig = oh.World.percept
    oh.World.percept = lambda self: (lambda p: p and {k: float("nan") for k in p})(orig(self))
    try:
        b = trial("E_vis_touch", ("cube_M", "mid"), 101090)
    finally:
        oh.World.percept = orig
    for r in (a, b):
        for o in r["objects"]:
            for x in o["attempt_log"]:
                x.pop("percept", None)
            o.pop("events", None)
    sa, sb = strip(a), strip(b)
    assert all(math.isnan(v) for v in b["vision"][0]["truth"].values())
    assert sa["T_sim"] == sb["T_sim"] and [o["truth"] for o in sa["objects"]] == [o["truth"] for o in sb["objects"]]
    assert sa["objects"][0]["attempt_log"] == sb["objects"][0]["attempt_log"]


def test_V3_union_without_vision_equals_leg_circuit():
    u, l = vm.VisJaw(FC, noise=0.0), sm.LegJaw(FC)
    u.reset(), l.reset()
    for i in range(80):
        t = np.array([0.6, 0.4, 0.0]) if i > 20 else np.zeros(3)
        assert u.step(t, 0.5, 0.0) == l.step(t, 0.5, 0.0)
    c = u.rep["cross_edges"]
    assert c["dna02L_to_leg"] > 0 and c["vis_to_leg"] >= c["dna02L_to_leg"], c     # połączenie wzrok → noga jest w danych


def test_V4_blank_camera_means_no_percept_and_no_success():
    r = trial("E_vis_touch", ("cube_M", "mid"), 101090, blank=True)
    assert not r["vision"] and not any(o["success"] for o in r["objects"]) and "no_object" in (r["stopped_by"] or "")


def test_V5_network_turns_towards_object_and_swap_turns_away():
    """Przedmiot po lewej (y > kamery): sieć obraca kamerę w jego stronę; zamiana stron wejścia LC10a — w przeciwną."""
    f, drv, _ = arm("E_vis_touch")
    out = {}
    for swap in (False, True):
        drv.reset(vm.SEED_NOISE + 101090)
        w = oh.World([("cube_M", "mid")], 101090, home=vm.Q_SURVEY)
        c = f(w, vm.CFG)
        c.swap = swap
        while w.objs[0]["t_spawn"] is None:
            c.gaze()
        c.gaze()                                                    # położenie ciała aktualne dopiero po kroku fizyki
        y_obj = float(w.sim.d.xipos[w.objs[0]["bid"]][1])           # prawda — tylko ocena testu
        e0 = abs(w.sim.fk(c.obs.q)["eye"][1] - y_obj)
        for _ in range(100):
            c.gaze()
        out[swap] = (e0, abs(w.sim.fk(c.obs.q)["eye"][1] - y_obj))
        c.eye.close()
    assert out[False][0] > 0.015, f"scena testu: przedmiot za blisko osi ({out})"
    assert out[False][1] < 0.012 and out[True][1] > out[True][0], out


def test_V6_results_dir_and_no_overwrite():
    assert vm.OUT.endswith(os.path.join("flymind", "results", "vision_manipulation"))
    src = open(vm.__file__).read()
    assert 'open(path, "x")' in src and "os.path.exists(path)" in src


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v()
            print(f"{k}: OK", flush=True)
    print("WSZYSTKIE TESTY OK")
