"""flymind/demo/test_demo_arm.py — odbiór demo_arm.py bez okna i bez renderowania.
Uruchom: .venv/bin/python -I -B flymind/demo/test_demo_arm.py     (ok. 2–3 minuty: trzy próby cube_S/hard_grip, ziarno 20951)

T1: próba przez ścieżkę pokazu (przechwytywanie impulsów + haki) = joint_net.run_trial na zwykłych ArmNet/LegJaw: identyczny wynik
    (prawda, lift_log, T_sim, safety_stats, fmax, odcisk prelift_sha itd. — wszystko poza zegarem ściennym).
T2: przechwytywanie niczego nie zmienia: SHA CAŁEJ trajektorii (q_t, tau, obserwacje każdego kroku) ze ścieżki z przechwytywaniem
    = ze ścieżki bez niego (zwykłe klasy, same haki trajektorii).
T3: przechwycone impulsy są prawdziwe: (a) odtworzone z nich filtrowane częstości pul = ArmNet.r (dokładnie), (b) raster 500 ms =
    ostatnie 500 wierszy wszystkich impulsów, (c) liczba neuronów w grupach = ArmNet.N + LegJaw.N, MN pul leżą w grupach MN.
T4: panel rysuje dane z Live (obraz, liczba neuronów na ekranie), tekst stawów zawiera źródła komend z SafetyLayer.
T5: zakaz ziaren testowych w CLI."""
import hashlib
import os
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

import demo_arm as DA  # noqa: E402

JN = DA.JN
ITEM, IDX = DA.find_item("cube_S/hard_grip")
SEED = 20951 * 1000 + IDX * 10 + 0            # joint_net.main: seed·1000 + indeks·10 + pose; --poses 1 → tylko pose 0
AC = JN.ArmCfg(version="test", joints=(1, 2, 3), roll=True, inputs=("padsT2", "padsT1"), in_rule="fl")
GLU = -1.0
SKIP = {"T_wall"}


def strip(r):
    return {k: v for k, v in r.items() if k not in SKIP}


# --- referencja: dokładnie jak joint_net.main (zwykłe obiekty, bez haków)
fc, jaw, drv, _ = DA.make_nets(GLU, AC, capture=False)
ref = JN.run_trial(ITEM, SEED, "N", jaw, drv, fc, AC)
print(f"ref: lift {ref['truth']['lift']} placed {ref['success']} T_sim {ref['T_sim']} act_ticks {ref['act_ticks']} lift_log {ref['lift_log']}")

# --- ścieżka pokazu z przechwytywaniem (keep=True: pełny zapis impulsów do testu)
r1, live, sha1, _ = DA.run_demo(ITEM, SEED, GLU, AC, capture=True, keep=True)
assert strip(r1) == strip(ref), {k: (r1[k], ref[k]) for k in ref if k not in SKIP and r1[k] != ref[k]}
print(f"T1 OK: wynik pokazu = joint_net.run_trial ({len(strip(ref))} pól identycznych, prelift_sha {ref['prelift_sha'][:12]}…)")

# --- ścieżka bez przechwytywania, same haki trajektorii
r2, _, sha2, _ = DA.run_demo(ITEM, SEED, GLU, AC, capture=False)
assert strip(r2) == strip(ref) and sha1 == sha2, (sha1, sha2)
print(f"T2 OK: SHA całej trajektorii z przechwytywaniem = bez niego ({sha1[:16]}…), {live.n_ticks} taktów")

# --- T3
kept = np.vstack(live.kept)
assert kept.shape == (live.n_ticks * 10, live.N) and kept.sum() == live.n_spikes > 0
ring = np.roll(live.ring, -live.ptr, axis=0)
assert np.array_equal(ring, kept[-DA.RASTER:][:, live.order])
assert np.allclose(live.r_chk, live.drv.r, rtol=0, atol=1e-9), (live.r_chk, live.drv.r)
assert sum(g["n"] for g in live.groups) == live.N == live.Na + live.Nj
mn = {(g["net"], g["leg"]): set(g["idx"].tolist()) for g in live.groups if g["kind"] == "MN"}
armMN = set().union(*[v for (n, _), v in mn.items() if n == "ArmNet"])
for j, (p, n) in live.drv.idx["pools"].items():
    assert set(p) | set(n) <= armMN
assert set(live.jaw.press) | set(live.jaw.release) <= {i - live.Na for i in mn[("LegJaw", "T2 L")]}
assert live.drv.ac.dt_ms == 1.0 and live.drv.nsteps == 10 and len(live.kept[0]) == 10
print(f"T3 OK: {live.n_spikes} impulsów przechwyconych, r z impulsów = ArmNet.r, raster 500 ms = ostatnie 500 wierszy; "
      f"neurony {live.Na} + {live.Nj} = {live.N}; grupy: " + "; ".join(g["label"] for g in live.groups))

# --- T4
snap = live.snapshot()
p = DA.Panel(720, 900, snap["static"])
img = p.render(snap).copy()
assert img.shape == (900, 720, 3) and img.std() > 5 and f"= {live.N}" in snap["count"]
assert "snn:legT1L" in live.seen and "snn:legT2L" in live.seen and "script:hold_grasp_pose" in live.seen, live.seen
assert live.seen <= set(ref["safety_stats"]), (live.seen, list(ref["safety_stats"]))
assert "5 gripper" in snap["joints"] and "shoulder_lift" in snap["joints"] and "POS" in snap["joints"]
print("T4 OK: panel 720×900 narysowany z danych symulacji; źródła komend widziane przez SafetyLayer ⊂ safety_stats:", sorted(live.seen))

# --- T5
out = subprocess.run([sys.executable, "-I", "-B", os.path.join(HERE, "demo_arm.py"), "--seed", "20901"], capture_output=True, text=True)
assert out.returncode != 0 and "zabronione" in (out.stdout + out.stderr)
print("T5 OK: ziarno testowe odrzucone")
print("WSZYSTKIE TESTY OK; sha256 trajektorii", sha1)
