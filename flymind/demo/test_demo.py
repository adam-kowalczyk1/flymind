"""flymind/demo/test_demo.py — odbiór pokazu bez okna. Uruchom: .venv/bin/python -I -B flymind/demo/test_demo.py [LOG_OKNA.json]
T1/T2: takt pokazu = loop.run_trial (snn / classical_p): identyczne e(t) i ω(t) przez 300 taktów.
T3: przestawienie piłeczki zmienia wejście sieci. T4: w trybie SNN ruch pochodzi z impulsów DNa02 (wyciszone DNa02 → ω = 0).
T5: tryb P nie liczy SNN. T6: panel rysuje dane z symulacji. T7: reset / pauza / przełącznik trybu.
T8: dodatki wizualne nagrań (renderer zewnętrzny, światło, znaczniki, panel) nie zmieniają obrazu kamery robota ani sterowania.
T9: próby porównawcze prezentacji = loop.run_trial (te same e(t)), wyniki = loop.metrics; start SNN i P identyczny.
T10: scenariusz deterministyczny; parametry modelu i sieć niezmienione po wszystkich testach.
T11 (opcjonalny, z plikiem --log okna --present): e(t) z okna na żywo = odtworzenie scenariusza bez okna."""
import hashlib
import json
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

import demo as D  # noqa: E402
from decoder import SteerDecoder  # noqa: E402

SEED, AZ, RHO = D.SEED0 + 500, 18.0, 0.21


def fingerprint(d):
    return (repr(D.L.P), repr(D.L.ENC), repr(D.L.STEER), D.L.J0, D.L.Q_POSE.tolist(), D.L.TICKS, D.L.DT,
            hashlib.sha256(np.ascontiguousarray(d.spec.W).tobytes()).hexdigest(), json.dumps(d.calib, sort_keys=True))


d = D.Demo("snn", AZ, RHO, SEED)
fp0 = fingerprint(d)
net, cal = (d.spec, d.idx), d.calib
tr = dict(seed=SEED, az0_deg=AZ, rho=RHO)

for i, cond in enumerate(("snn", "classical_p"), 1):
    ref = D.L.run_trial(cond, SEED, net, cal, tr=tr)
    d.reset(AZ, RHO, mode=cond, noise_seed=SEED)               # ta sama realizacja szumu co run_trial (seed próby)
    e, om = [], []
    for _ in range(D.L.TICKS):
        e.append(d.tick())
        om.append(d.last["omega"])
    e = np.degrees(np.array(e)).round(3).tolist()
    assert e == ref["e_deg"], f"T{i} {cond}: e(t) różni się od loop.run_trial"
    assert np.round(om, 4).tolist() == ref["omega"], f"T{i} {cond}: ω(t) różni się"
    print(f"T{i} OK {cond}: 300 taktów identycznych z loop.run_trial, końcowy |e| {abs(e[-1]):.2f}°")

# T3: wejście sieci zależy od położenia piłeczki
d.reset(20.0, RHO, mode="snn")
d.tick()
gl = d.last["g"].copy()
d.move_ball(-20.0, RHO)
d.tick()
gr = d.last["g"].copy()
assert gl[0] > gl[1] and gr[1] > gr[0], (gl, gr)
print(f"T3 OK: piłeczka +20° → g {gl.round(3)}, −20° → g {gr.round(3)}")

# T4: ruch w trybie SNN pochodzi z DNa02 — (a) ω odtwarza świeży dekoder z zapisanych impulsów, (b) bez impulsów DNa02 brak ruchu
d.reset(20.0, RHO, mode="snn")
dec2 = SteerDecoder({"DNa02_L": d.idx["DNa02_L"], "DNa02_R": d.idx["DNa02_R"]}, ("DNa02",), [0.0], [d.calib["slope_snn"]], D.L.STEER)
run0 = d.net.run
cap = []
d.net.run = lambda I, n: cap.append(run0(I, n)) or cap[-1]
for _ in range(100):
    d.tick()
    assert dec2.step(cap[-1], 1.0)["omega"] == d.last["omega"]
moved = abs(d.last["pan_deg"])
dn = np.r_[d.idx["DNa02_L"], d.idx["DNa02_R"]]


def silenced(I, n):
    s = run0(I, n)
    s[:, dn] = False
    return s


d.reset(20.0, RHO, mode="snn")
d.net.run, run0 = silenced, d.net.run
for _ in range(100):
    d.tick()
    assert d.last["omega"] == 0.0
assert moved > 5 and abs(d.last["pan_deg"]) < 0.05, (moved, d.last["pan_deg"])
print(f"T4 OK: ω = dekoder(impulsy DNa02); po 1 s baza {moved:.1f}°, z wyciszonym DNa02 {d.last['pan_deg']:.3f}°")

# T5: tryb P działa bez SNN
d.reset(20.0, RHO, mode="classical_p")
for _ in range(100):
    d.tick()
assert d.net.t == 0 and abs(d.last["pan_deg"]) > 5 and not d.raster.any()
print(f"T5 OK: P bez SNN (kroki ALIF {d.net.t}), baza {d.last['pan_deg']:.1f}°")

# T6: panel pokazuje dane z symulacji
d.reset(20.0, RHO, mode="snn")
for _ in range(60):
    d.tick()
p = D.Panel(d, 720, 1080)
img = p.render(*D.status_line(d)).copy()
ras = np.asarray(p.ras.get_array())
assert img.shape == (1080, 720, 3) and ras.any(axis=-1).sum() == d.raster[:, p.order].sum() > 0
assert np.asarray(p.dnras.get_array()).any(axis=-1).sum() == d.raster[:, dn].sum()
lc = d.raster[-10:][:, d.idx["in_L"]].mean() * 1000
assert abs(d.hist["lcL"][-1] - lc) < 1e-9 and np.allclose(p.l["pan"].get_ydata(), d.hist["pan"])
assert np.allclose(p.l["dnL"].get_ydata(), d.hist["dnL"]) and p.l["dnL"].get_ydata()[-1] == d.dec.r[0]
assert [b.get_height() for b in p.bars] == [D.L.ENC.i_max * x for x in d.last["g"]]
print(f"T6 OK: raster panelu = {int(d.raster.sum())} impulsów z symulacji, DNa02 L na wykresie = dec.r ({d.dec.r[0]:.1f} Hz)")

# T7: reset, pauza, przełącznik trybu (ta sama funkcja handle co w oknie)
st, rng = dict(paused=False), np.random.default_rng(1)
D.handle("pause", d, st, rng)
assert st["paused"]
D.handle("pause", d, st, rng)
assert not st["paused"]
D.handle("reset", d, st, rng)
assert d.k == 0 and abs(d.sim.d.qpos[d.sim.qadr[0]]) < 1e-12 and d.mode == "snn"
D.handle("mode", d, st, rng)
assert d.mode == "classical_p" and d.k == 0
D.handle("left", d, st, rng)
assert d.az == 30.0
print("T7 OK: pauza przełącza stan, reset zeruje czas i bazę, 8 przełącza tryb, '-' przesuwa piłeczkę")

# T8: dodatki wizualne nie wpływają na kamerę robota ani na sterowanie
a, b = D.Demo("snn", AZ, RHO, SEED, net=net, calib=cal), D.Demo("snn", AZ, RHO, SEED, net=net, calib=cal)
ext, ext_eye, pb = D.Ext(b, 1600, 1440), D.Ext(b, 800, 600), D.Panel(b, 960, 1440)
show = D.Show()
for k in range(150):
    ea, eb = a.tick(), b.tick()
    ext.render(show.shot() if k % 2 else D.SHOTS["wide"])
    ext_eye.render("eye")
    pb.render(*D.status_line(b))
    assert ea == eb and np.array_equal(a.last["img"], b.last["img"]), f"T8: rozjazd w takcie {k}"
ext.close()
ext_eye.close()
print("T8 OK: 150 taktów z renderowaniem nagrań (światło, znaczniki, 1600×1440, panel) — obraz robota i e(t) identyczne")

# T9: próby porównawcze prezentacji = loop.run_trial; start SNN i P identyczny
cmp_acts = tuple(x for x in D.ACTS if x.get("compare") in (0, 2))
s9 = D.Show(cmp_acts)
c = D.Demo("snn", *D.CMP[0], net=net, calib=cal)
while not s9.done:
    s9.step(c)
off = 0
for act, r in zip(cmp_acts, s9.results):
    az, rho = act["reset"]
    ref = D.L.run_trial(act["mode"], act["seed"], net, cal, tr=dict(seed=act["seed"], az0_deg=az, rho=rho))
    seg = np.round(s9.e_log[off:off + D.L.TICKS], 3).tolist()
    off += D.L.TICKS
    assert seg == ref["e_deg"], f"T9 {act['name']}: e(t) ≠ run_trial"
    m = D.L.metrics(ref)
    assert r["final_abs_err"] == round(m["final_abs_err"], 2) and r["success"] == m["success"]
    print(f"   {act['name']:16s} cel {az:+.0f}°/{rho:.2f}: |e| końcowy {r['final_abs_err']:5.2f}°  sukces {r['success']}")
x, y = D.Demo("snn", 0, 0.2, net=net, calib=cal), D.Demo("classical_p", 0, 0.2, net=net, calib=cal)
for q in (x, y):
    q.tick()
    q.reset(*D.CMP[1], mode=q.mode, noise_seed=D.SEED_CMP + 1)
assert np.array_equal(x.sim.d.qpos, y.sim.d.qpos) and np.array_equal(x.sim.d.ctrl, y.sim.d.ctrl) and x.sim.d.time == y.sim.d.time
print("T9 OK: próby porównawcze prezentacji identyczne z loop.run_trial; start SNN i P bit w bit ten sam")

# T10: determinizm scenariusza i brak zmian modelu
s1, s2 = D.Show(), D.Show()
d1, d2 = D.Demo("snn", 0, 0.2, net=net, calib=cal), D.Demo("snn", 0, 0.2, net=net, calib=cal)
for _ in range(400):
    s1.step(d1)
    s2.step(d2)
assert s1.e_log == s2.e_log and len(s1.e_log) == 400
assert fingerprint(d) == fp0 == fingerprint(d1), "T10: parametry modelu/sieci zmienione"
assert [x["reset"] for x in D.ACTS if "compare" in x] == [p for p in D.CMP for _ in (0, 1)]
print(f"T10 OK: scenariusz deterministyczny; ALIF/enkoder/dekoder/J0/W/kalibracja bez zmian (W sha {fp0[7][:12]})")

# T11: okno na żywo = odtworzenie bez okna (log z: mjpython demo.py --present --seconds N --log PLIK)
if len(sys.argv) > 1:
    live = json.load(open(sys.argv[1]))
    assert live["present"] and live["e_log"], "T11: log bez prezentacji"
    s = D.Show()
    r = D.Demo("snn", D.ACTS[0]["reset"][0], D.ACTS[0]["reset"][1], net=net, calib=cal)
    while len(s.e_log) < len(live["e_log"]):
        s.step(r)
    assert s.e_log == live["e_log"], "T11: okno ≠ odtworzenie"
    print(f"T11 OK: {len(live['e_log'])} taktów z okna MuJoCo identycznych z odtworzeniem bez okna "
          f"(tempo {live['sim_s'] / live['wall_s']:.2f}× wliczając start, panel {live['panel_ms_p50']} ms, {live['fps']} kl./s)")
for q in (d, a, b, c, x, y, d1, d2):
    q.sim.close()
print("WSZYSTKIE TESTY OK")
