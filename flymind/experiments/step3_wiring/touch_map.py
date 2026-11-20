"""JEDNA wspólna droga czujnik → mózg dla symulacji i prawdziwego sprzętu (19 XI).
  świat/FSR402 (A0 szczęka stała, A1 szczęka ruchoma) → siła na aktywnym polu → ADC (dzielnik 5 V, FSR, r_fix do GND) → zliczenia
  → counts_to_force → N → `net.step([A0, A1, palm], ...)` (TwoNet.step robi 40 mV/N); receptory: A0 → grupa „udo”, A1 → „goleń+stopa”
  (analogia: staw szczęki = staw udo–goleń; podział z touch_map.json, status = patrz tam: dziś HIPOTEZA, nie literatura).
Użycie:  net.pads = touch_map.pads_for(net, "somato");  felt = Feel(5100).step(forces_AB);  net.step([*felt, palm_N], q, qd, dt)
Prawdziwy Arduino: felt = touch_map.from_counts(a0, a1, 5100)  — ta sama funkcja co w symulacji."""
import json
import os
import sys
from collections import deque

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nerves as NV  # noqa: E402

R_DISC, R_FOIL = 6.35e-3, 9.15e-3        # m: aktywne pole FSR402 Ø12,7 mm, folia Ø18,3 mm (tylko aktywne czuje)
R_FIX = 5100.0                           # Ω opornik dzielnika (właściciel ma klasę 5 kΩ: 4,7 lub 5,1 k)
# Pozycje w układach ciał (m, normalna ku drugiej szczęce). Policzone z siatek producenta przez hardware/gripper_sensors/export_gripper.py
# (szczęka ruchoma otwarta 0,6 rad; środek i normalna z największej płaskiej ściany) i przeliczone na układ ciała ruchomej szczęki
# wzorem R_j^T (R_g c + p_g - p_j) — `_derive()` robi to samo i `_check` porównuje.
FSR = {"A0": ("gripper", np.array([-0.011655, -0.000218, -0.074425]), np.array([1.0, 0.0, -0.00057])),
       "A1": ("moving_jaw_so101_v1", np.array([-0.01232, -0.05925, 0.01889]), np.array([-1.0, -0.0025, -0.0001]))}
# Wariant „dłoń” (19 XI): drugi czujnik na spodzie serwa między nasadami szczęk — płaska ściana 40×32 mm na z = −36 mm
# w układzie 'gripper' (siatka sts3215_03a_v1, export_gripper.py), środek x ≈ 7 mm; +0,5 mm na grubość folii; normalna ku czubkom.
FSR_PALM = {"P": ("gripper", np.array([0.007, 0.0, -0.0365]), np.array([0.0, 0.0, -1.0]))}


def _derive(angle=0.6):
    """Przelicza FSR z gripper_mm.json (układ 'gripper') na układy ciał; wymaga assets/ i hardware/ projektu."""
    import mujoco
    root = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    xml = open(os.path.join(root, "assets/so101_upstream.xml")).read().replace('meshdir="assets"', f'meshdir="{root}/assets/so101_meshes"')
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    d.qpos[m.joint("gripper").qposadr[0]] = angle
    mujoco.mj_forward(m, d)
    S = json.load(open(os.path.join(root, "hardware/gripper_sensors/gripper_mm.json")))["_sensors"]
    g, j = m.body("gripper").id, m.body("moving_jaw_so101_v1").id
    Rg, Rj = d.xmat[g].reshape(3, 3), d.xmat[j].reshape(3, 3)
    c1, n1, _ = S["FSR1_A0_szczeka_stala"]
    c2, n2, _ = S["FSR2_A1_szczeka_ruchoma"]
    return {"A0": ("gripper", np.array(c1) / 1000, np.array(n1)),
            "A1": ("moving_jaw_so101_v1", Rj.T @ (Rg @ (np.array(c2) / 1000) + d.xpos[g] - d.xpos[j]), Rj.T @ (Rg @ np.array(n2)))}


def fsr_world(m, d):
    """Środki i normalne obu dysków w świecie. m = MjModel, d = MjData po kinematyce (np. reach._kin(sim, q), sim.m)."""
    out = {}
    for k, (body, c, n) in {**FSR, **FSR_PALM}.items():
        b = m.body(body).id
        R = d.xmat[b].reshape(3, 3)
        out[k] = (R @ c + d.xpos[b], R @ n)
    return out


def sphere_force(centre, radius, disc_c, disc_n, k=300.0):
    """Siła [N] kuli na płaskim AKTYWNYM dysku (Ø12,7 mm): k · max(0, radius − odległość od najbliższego punktu dysku).
    Kula za dyskiem (po stronie szczęki) nie działa. Folia poza aktywnym polem nie czuje."""
    v = np.asarray(centre, float) - disc_c
    t = float(v @ disc_n)
    if t < 0:
        return 0.0
    p = v - t * disc_n
    r = np.linalg.norm(p)
    if r > R_DISC:
        p *= R_DISC / r
    return float(k * max(0.0, radius - np.linalg.norm(v - p)))


def from_counts(a0, a1, r_fix=R_FIX):
    """Zliczenia ADC z Arduino (lub z symulacji) → siła odczuta [N] (A0, A1). Jedna funkcja dla symulacji i sprzętu."""
    return np.array([NV.counts_to_force(float(min(max(c, 0), NV.ADC)), r_fix) for c in (a0, a1)])


class Feel:
    """Symulowany tor: siły prawdziwe (A0, A1) → odczyt jak z Arduino. level: typ = gain 0,7–1,1 na czujnik, szum ADC 1,5, opóźnienie 1 takt;
    ideal = g 1, bez szumu i opóźnienia (kwantyzacja ADC i krzywa FSR zostają). Losowość tylko z ziarna."""
    def __init__(self, r_fix=R_FIX, level="typ", seed=0):
        self.r_fix = r_fix
        p = NV.LEVELS["typ"] if level == "typ" else dict(g=(1.0, 1.0), adc_sd=0.0, d_s=0)
        rng = np.random.default_rng([int(seed), 19112026])
        self.g, self.sd, self.rng = rng.uniform(*p["g"], size=2), p["adc_sd"], rng
        self.buf = deque([np.zeros(2)] * (p["d_s"] + 1), maxlen=p["d_s"] + 1)

    def counts(self, forces):
        return [round(min(max(NV.fsr_counts(float(f) * g, self.r_fix) + self.rng.normal(0, self.sd), 0.0), NV.ADC)) for f, g in zip(forces, self.g)]

    def step(self, forces):
        self.buf.append(from_counts(*self.counts(forces), self.r_fix))
        return self.buf[0]

    from_counts = staticmethod(from_counts)


def _map():
    return json.load(open(os.path.join(HERE, "touch_map.json")))


def pads_for(net, mapping="somato"):
    """(indeksy A0, indeksy A1) w kolejności neuronów sieci. somato = (udo, goleń+stopa); swap = odwrotnie; halves = stary podział po bodyId."""
    if not hasattr(net, "_pads0"):
        net._pads0 = tuple(net.pads)
    if mapping == "halves":
        return net._pads0
    if getattr(net, "pos", None) is None:               # BrainNet nie ma .pos; kolejność jak w head.py / nets2.build_ext
        import brainleg as B
        import nets
        bm, d78, d15 = B.route_ids()
        order = list(dict.fromkeys(nets.bodies_for("pre")[0] + bm + d78 + d15))
        assert len(order) == net.N
        net.pos = {b: i for i, b in enumerate(order)}
    if mapping == "elabbady":                           # 20 XI: (A0 = środek szczęki → szczecinki „środkowe”, A1 = czubek → „koniec nogi”)
        bm = json.load(open(os.path.join(HERE, "../sensor_placement/results/bristle_map_r1.json")))   # reguła Elabbady 2026, wyprowadzone
        return [net.pos[b] for b in bm["A0"]], [net.pos[b] for b in bm["tip"]]
    mp = _map()
    f, t = ([net.pos[b] for b in mp[k]] for k in ("femur", "tibia_tarsus"))
    return {"somato": (f, t), "swap": (t, f)}[mapping]


def _check():
    for k, (b, c, n) in _derive().items():
        assert FSR[k][0] == b and np.abs(FSR[k][1] - c).max() < 5e-5 and np.abs(FSR[k][2] - n).max() < 5e-3, (k, c, n)
    c, n, r = np.zeros(3), np.array([0, 0, 1.0]), 0.04
    assert abs(sphere_force([0, 0, r - 0.002], r, c, n) - 0.6) < 1e-9                                  # wcisk 2 mm → 0,6 N
    assert sphere_force([0, 0, r], r, c, n) == 0 and sphere_force([0, 0, -0.001], r, c, n) == 0
    assert sphere_force([R_FOIL, 0, 0.004], 0.004, c, n) == 0                                          # dotyk folii, nie pola
    assert sphere_force([R_DISC + 0.001, 0, 0.003], 0.004, c, n) > 0                                  # rąb aktywnego pola
    assert from_counts(0, 0).tolist() == [0.0, 0.0] and Feel(5100, "ideal").step([0, 0]).tolist() == [0.0, 0.0]
    for rf in (5100, 10000):
        for f in (0.5, 1, 3, 10):
            assert abs(NV.counts_to_force(NV.fsr_counts(f, rf), rf) - f) / f < 0.02, (rf, f)
    assert NV.fsr_counts(1.0, 5100) < NV.fsr_counts(1.0, 10000) and NV.fsr_counts(1.0) == NV.fsr_counts(1.0, 10000)
    fe = Feel(5100, "ideal")
    assert abs(fe.step([2.0, 0.0])[0] - 2.0) / 2.0 < 0.03
    mp = _map()
    f, t = set(mp["femur"]), set(mp["tibia_tarsus"])
    assert not f & t and len(f) + len(t) + len(mp["unassigned"]) == 322 and mp["status"] in ("literature", "hypothesis")
    print("touch_map _check OK; femur/tibia_tarsus:", len(f), len(t), "status", mp["status"])


if __name__ == "__main__":
    _check()
