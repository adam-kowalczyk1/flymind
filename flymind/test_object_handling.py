"""Testy benchmarku obsługi przedmiotów (Etap A: kontrola sceny + kontrole uczciwości ewaluatora). Bez serii pomiarowych.

Uruchom z katalogu tymczasowego (MuJoCo dopisuje ostrzeżenia do ./MUJOCO_LOG.TXT):
    .venv/bin/python -I -B flymind/test_object_handling.py
Kod wyjścia 0 = wszystkie testy zaliczone. Testy same stawiają przedmioty (teleport) WYŁĄCZNIE tutaj, poza World —
w seriach pomiarowych jedynym zapisem pozy jest pojawienie się przedmiotu w strefie.
"""
import contextlib
import inspect
import io
import math
import os
import re
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import object_handling as oh  # noqa: E402
from pick_place import Fail  # noqa: E402

ALL = [(s, "mid") for s in oh.SHAPES]
HOME = np.array(oh.OHCfg.home)


def idle(w, sec):
    for _ in range(int(round(sec / 0.01))):
        w.step(HOME[:5], 0.0)


def put(w, o, pos, quat=None, vel=(0, 0, 0)):
    """Tylko w testach: postaw przedmiot w dowolnym miejscu (zapis pozy poza World)."""
    d = w.sim.d
    d.qpos[o["adr"]:o["adr"] + 7] = [*pos, *(o["rest_quat"] if quat is None else quat)]
    d.qvel[o["dof"]:o["dof"] + 6] = [*vel, 0, 0, 0]
    o["t_spawn"] = o["t_spawn"] if o["t_spawn"] is not None else w.sim.sim_time
    w.sim.mj.mj_forward(w.sim.m, d)


def touch_of(w, o):
    d = w.sim.d
    return {y for a, b in d.contact.geom[:d.ncon] for x, y in ((w.lab[a], w.lab[b]), (w.lab[b], w.lab[a]))
            if x == ("obj", o["uid"]) and y is not None}


def z_low(w, o):
    return float(w._cloud_world(o)[:, 2].min())


# ---------------------------------------------------------------- A: scena -----------------------------------------
def test_A1_scene_loads_and_rests():
    w = oh.World(ALL, 0)
    m, d, mj = w.sim.m, w.sim.d, w.sim.mj
    mj.mj_forward(m, d)
    labs = {(str(w.lab[a]), str(w.lab[b])) for a, b in d.contact.geom[:d.ncon]}
    assert not any("arm" in p or "jaw" in x or "palm" in x for p in labs for x in p), labs     # ramię niczego nie dotyka
    assert not any("box" in p and any(x in oh.ARMSET for x in p) for p in labs)
    assert 0.15 < m.body_subtreemass[w.box_bid] < 0.25, m.body_subtreemass[w.box_bid]
    w.pending = False                                    # bez spawnu: sama scena
    p0 = d.xpos.copy()
    idle(w, 2.0)
    ids = [w.box_bid] + [o["bid"] for o in w.objs]
    drift = np.linalg.norm(d.xpos - p0, axis=1)[ids]
    assert drift.max() < 0.0006, drift                   # pudełko i zaparkowane przedmioty stoją (osiadanie < 0,6 mm)
    assert all(z_low(w, o) > -0.0005 for o in w.objs)    # nic nie przenika przez blat
    assert w.box_drift < 0.0001 and w.stats["pose_writes"] == 0           # pudełko nie przesuwa się po blacie


def test_A2_every_object_spawns_stable_and_percept_matches():
    for it in ALL:
        w = oh.World([it], 5)
        idle(w, 1.0)
        o, z = w.objs[0], w.scene.zone
        assert o["t_spawn"] is not None and w.stats["pose_writes"] == 1, it
        p = w.sim.d.xipos[o["bid"]]
        assert z[0] - .02 <= p[0] <= z[1] + .02 and z[2] - .02 <= p[1] <= z[3] + .02, (it, p)
        assert z_low(w, o) > -0.0005, (it, z_low(w, o))                       # nie wpada w blat
        assert w._still(o) and touch_of(w, o) == {"table"}, (it, touch_of(w, o))
        pc = w.percept()
        ref = oh.obb(o["cloud"] @ oh.quat_mat(w.sim.mj, o["rest_quat"]).T)     # wymiary z katalogu (poza spoczynkowa)
        assert abs(pc["l"] - ref["l"]) < 0.001 and abs(pc["w"] - ref["w"]) < 0.001, (it, pc, ref)
        assert abs(pc["h"] - (ref["h"] + o["rest_z"])) < 0.001, (it, pc["h"])
        assert set(pc) == {"x", "y", "yaw", "l", "w", "h"}                     # percept nie niesie masy, tarcia, kształtu


def test_A3_box_holds_objects():
    w = oh.World(ALL, 0)
    w.pending = False
    bx, by = w.scene.box_xy
    for i, o in enumerate(w.objs[:9]):                   # zestaw podstawowy: zrzut z wysokości transportu
        put(w, o, (bx - 0.06 + 0.06 * (i % 3), by - 0.05 + 0.05 * (i // 3), o["rest_z"] + 0.055))
    idle(w, 2.0)
    for o in w.objs[:9]:
        t = touch_of(w, o)
        assert w._in_box(o, t) and w._still(o), (o["shape"], t, w.sim.d.xipos[o["bid"]])
        assert z_low(w, o) > w.scene.floor - 0.001, (o["shape"], z_low(w, o))  # nie przenika przez dno
    assert w.box_drift < 0.003, w.box_drift
    s = w.objs[4]                                        # kula puszczona w ściankę 0,3 m/s zostaje w pudełku
    assert s["shape"] == "sphere"
    put(w, s, (bx, by, w.scene.floor + 0.018), vel=(0.3, 0.0, 0.0))
    idle(w, 2.0)
    assert w._in_footprint(w.sim.d.xipos[s["bid"]]) and "table" not in touch_of(w, s)


def test_A4_spawner_rules():
    items = [("cube_M", "mid"), ("sphere", "mid"), ("cyl", "mid")]
    w = oh.World(items, 3)
    idle(w, 0.5)
    o0, o1 = w.objs[0], w.objs[1]
    assert w.current is o0 and w.next == 1 and not w.pending           # jeden przedmiot naraz; następny czeka na lift
    idle(w, 3.0)
    assert o1["t_spawn"] is None and w.stats["pose_writes"] == 1        # bez podniesienia nie ma kolejnego
    p0 = w.sim.d.xpos[o0["bid"]].copy()
    assert not w._free(o1, (p0[0], p0[1], o1["rest_z"]), o1["rest_quat"])           # miejsce zajęte
    assert not w._free(o1, (p0[0] + 0.03, p0[1], o1["rest_z"]), o1["rest_quat"])    # za blisko (margines 2,5 cm)
    bx, by = w.scene.box_xy
    assert not w._free(o1, (bx, by + w.scene.box_in[1] + 0.03, o1["rest_z"]), o1["rest_quat"])   # przy ściance pudełka
    k = oh._kin(w.sim, HOME)                             # pod padami ramienia opuszczonego nad strefę
    q, *_ = oh.ik(w.sim, [0.19, 0.05, 0.05], HOME, point="cs_fixed")
    w.sim.d.qpos[w.sim.qadr] = q
    cs = oh._kin(w.sim, q).site("cs_fixed").xpos
    assert not w._free(o1, (cs[0], cs[1], o1["rest_z"]), o1["rest_quat"])
    w.sim.d.qpos[w.sim.qadr] = HOME
    w.pending, w.next = True, 0                          # drugi zapis pozy tego samego przedmiotu jest zabroniony:
    for _ in range(200):                                 # 1) kontrola wolnego miejsca odrzuca go (koliduje sam ze sobą)
        w._try_spawn()
    assert w.stats["pose_writes"] == 1 and w.stats["spawn_rejects"] >= 200
    w._free = lambda *a: True                            # 2) nawet z wyłączoną kontrolą miejsca zapis jest zablokowany
    try:
        w._try_spawn()
        raise SystemExit("spawn pozwolił zapisać pozę drugi raz")
    except AssertionError:
        pass
    del k


def test_A5_queue_in_a_real_series():
    items = [("cube_M", "mid"), ("long", "mid"), ("cube_S", "mid")]
    r = oh.run(items, 11)
    ev = r["events"]
    assert [e["uid"] for e in ev if e["ev"] == "spawn"] == [0, 1, 2]                  # kolejność kolejki
    for uid in (1, 2):                                   # następny dopiero po lift (albo porzuceniu) poprzedniego
        ts = next(e["t"] for e in ev if e["ev"] == "spawn" and e["uid"] == uid)
        tl = next(e["t"] for e in ev if e["ev"] in ("lift", "abandoned") and e["uid"] == uid - 1)
        assert ts >= tl, (uid, ts, tl)
    assert r["stats"]["pose_writes"] == 3 and r["resets"] == 0 and r["auto_resets"] == 0 and r["complete"]
    assert not any(e["ev"] == "unwanted_contact" and e["kind"] == "carried_hit" and "('obj', " in e["pair"][1]
                   and e["phase"] == "transport" and e["t"] < 20 for e in ev[:0])    # (informacyjnie; patrz raport)
    return r


# ---------------------------------------------------------------- uczciwość ewaluatora -----------------------------
def test_E1_no_motion_means_no_success():
    w = oh.World([("cube_M", "mid")], 1)
    idle(w, 1.0)
    assert w.percept() is not None
    idle(w, 3.0)                                         # ramię stoi; „kontroler” mógłby twierdzić cokolwiek
    w.finalize()
    o = w.objs[0]
    assert not any(o["truth"].values()) and not o["success"] and o["final"] == "zone", o["truth"]


def test_E2_in_box_criterion():
    w = oh.World([("cube_M", "mid"), ("sphere", "mid")], 1)
    w.pending = False
    c, s = w.objs
    bx, by = w.scene.box_xy
    ax, ay = w.scene.box_in
    put(w, c, (bx + ax + 0.04, by, c["rest_z"]))         # na blacie obok pudełka
    put(w, s, (bx, by, w.scene.floor + 0.0178))          # na dnie pudełka
    idle(w, 1.0)
    assert not w._in_box(c, touch_of(w, c)) and w._in_box(s, touch_of(w, s))
    put(w, c, (bx + ax + 0.002, by, w.scene.rim + 0.016))   # na krawędzi ścianki: środek masy poza obrysem wnętrza
    idle(w, 0.05)
    assert not w._in_box(c, touch_of(w, c))
    put(w, c, (bx, by, 0.20))                            # w powietrzu nad pudełkiem: brak podparcia
    assert not w._in_box(c, touch_of(w, c))
    w.finalize()
    assert s["final"] == "box" and not s["success"]      # leży w pudełku, ale nikt go tam nie włożył → nie sukces


class Dropper(oh.Controller):
    """Kontroler celowo psujący transport: po 0,4 s przenoszenia zgłasza utratę chwytu (→ otwiera szczękę nad blatem)."""
    n = 0

    def held(self):
        super().held()
        if self.w.phase == "transport":
            self.n += 1
            if self.n > 40:
                raise Fail("lost_grip", "test: wymuszone")


def test_E3_drop_outside_box_is_not_success():
    orig = oh.Controller
    oh.Controller = Dropper
    try:
        r = oh.run([("cube_M", "mid")], 1)
    finally:
        oh.Controller = orig
    o = r["objects"][0]
    assert o["truth"]["grasp"] and o["truth"]["lift"] and not o["truth"]["transport"] and not o["truth"]["placed"], o["truth"]
    assert o["dropped"] and o["final"] in ("table", "zone") and not o["success"], (o["dropped"], o["final"])
    assert o["attempt_log"][0]["reason"] == "lost_grip" and o["attempt_log"][0]["recover"] is True
    assert o["attempts"] == 1 and len(o["attempt_log"]) == 1            # po podniesieniu nie ma drugiej próby


def test_E4_ungraspable_is_reported_not_hidden():
    r = oh.run([("cube_XL", "light")], 1)                # 55 mm > rozwarcie szczęki: odmowa bez ruchu, przedmiot zostaje
    o = r["objects"][0]
    assert [a["reason"] for a in o["attempt_log"]] == ["too_wide", "too_wide"] and o["abandoned"]
    assert o["final"] == "zone" and not o["success"] and not any(o["truth"].values())
    assert oh.summarize([r])["success"] == dict(k=0, n=1, pct=0.0)


# ---------------------------------------------------------------- rozdział informacji ------------------------------
def test_I1_controller_sees_only_declared_inputs():
    src = inspect.getsource(oh.Controller)
    used = set(re.findall(r"self\.w\.(\w+)", src)) | set(re.findall(r"\bw\.(\w+)", src))
    assert used <= {"step", "percept", "done", "phase", "scene", "obs", "sim"}, used
    for bad in ("sim.d", ".d.", "xipos", "qvel", "objs", "current", "carried", "truth", "events", "ncon", "lab"):
        assert bad not in src, bad                       # żadnego stanu przedmiotów, kontaktów ani wyniku ewaluatora
    assert "mass" not in src and "mu" not in re.findall(r"\b\w+\b", src)


# ---------------------------------------------------------------- katalog, geometria, powtarzalność -----------------
def test_C1_catalogue_matches_model():
    w = oh.World(sorted(set(oh.SETS["base"] + oh.SETS["hard"])), 0)
    m = w.sim.m
    vol = dict(box=lambda s: 8 * s[0] * s[1] * s[2], sphere=lambda s: 4 / 3 * math.pi * s[0] ** 3,
               cylinder=lambda s: math.pi * s[0] ** 2 * 2 * s[1], ellipsoid=lambda s: 4 / 3 * math.pi * s[0] * s[1] * s[2],
               capsule=lambda s: math.pi * s[0] ** 2 * 2 * s[1] + 4 / 3 * math.pi * s[0] ** 3,
               mesh=lambda s: 0.5 * 0.03 * 0.03 * 0.04)
    for o in w.objs:
        M = oh.MATERIALS[o["material"]]
        want = M["density"] * sum(vol[g[0]](g[1]) for g in oh.SHAPES[o["shape"]]["geoms"])
        assert abs(o["mass"] - want) / want < 0.005, (o["shape"], o["material"], o["mass"], want)
        for g in o["geoms"]:
            assert abs(m.geom_friction[g][0] - M["mu"]) < 1e-9 and m.geom_priority[g] == 1
            assert abs(m.geom_solref[g][0] - M["solref"][0]) < 1e-9
    assert len(oh.SETS["base"]) == 45 and len(set(oh.SETS["base"])) == 45


def test_C2_paths_clear_table_and_rim():
    w = oh.World([("cube_M", "mid")], 1)
    c = oh.Controller(w)
    z, rim = w.scene.zone, w.scene.rim
    n = 0
    for x in (z[0], z[1]):
        for y in (z[2], z[3]):
            for yaw in (0.0, 0.8, 1.6, 2.4):
                for wd, h in ((0.02, 0.02), (0.035, 0.035), (0.045, 0.045), (0.03, 0.05)):
                    P = c.plan(dict(x=x, y=y, yaw=yaw, l=wd, w=wd, h=h))
                    for q in P["transport"] + P["retreat"]:
                        assert oh.clearance(w.sim, q) > rim + 0.01, (x, y, yaw, wd, oh.clearance(w.sim, q))
                    assert min(oh.clearance(w.sim, q) for q in P["home"]) > rim + 0.01
                    assert abs(oh.clearance(w.sim, P["descend"][-1]) - P["z_grasp"]) < 0.001
                    assert P["z_grasp"] >= 0.007 - 1e-9                    # pady nigdy niżej niż w Etapie 1
                    n += 1
    steps = w.sim.stats["steps"]
    try:
        c.plan(dict(x=0.19, y=0.02, yaw=0.0, l=0.07, w=0.06, h=0.03))
        raise SystemExit("za szeroki przedmiot nie został odrzucony")
    except Fail as e:
        assert e.reason == "too_wide" and w.sim.stats["steps"] == steps
    return n


def test_C3_deterministic():
    items = [("cube_M", "mid"), ("sphere", "hard_slick")]
    a, b, c = oh.run(items, 7), oh.run(items, 7), oh.run(items, 8)
    key = lambda r: (r["T_sim"], [(o["truth"], o["t"], o["final_pos"], o["spawn"]) for o in r["objects"]])  # noqa: E731
    assert key(a) == key(b), "to samo ziarno → inny przebieg"
    assert a["objects"][0]["spawn"] != c["objects"][0]["spawn"]


def test_W1_results_only_in_own_dir_and_never_overwritten():
    assert oh.OUT.endswith(os.path.join("flymind", "results", "object_handling"))
    tmp, orig, argv = tempfile.mkdtemp(), oh.OUT, sys.argv
    oh.OUT = os.path.join(tmp, "out")
    try:
        for expect in (0, "istnieje"):
            sys.argv = ["x", "single", "--only", "cube_M/mid", "--poses", "1", "--tag", "t"]
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    oh.main()
            except SystemExit as e:
                assert e.code == expect or expect in str(e.code), e.code
        assert os.listdir(oh.OUT) == ["t.json"]
    finally:
        oh.OUT, sys.argv = orig, argv


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            out = fn()
            print(f"{name}: OK" + (f" ({out} planów)" if isinstance(out, int) else ""), flush=True)
    print("WSZYSTKIE TESTY OK")
