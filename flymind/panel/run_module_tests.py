"""Uruchamia po kolei istniejące testy modułów FlyMind (zamknięta lista) i wypisuje podsumowanie. Niczego nie zmienia.
Kod wyjścia 0 tylko wtedy, gdy wszystkie przeszły. Używane przez panel (pozycja „Testy modułów”)."""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
FLY = os.path.dirname(HERE)
ROOT = os.path.dirname(FLY)
TESTS = ("connectome snn_interface alif sensory decoder safety latency epg_ring encoder visual_path side_shuffle fly_jaw "
         "vision_leg reach object_handling sensory_manipulation vision_manipulation pick_place pick_place_faults").split()
JOBS = [(t, [os.path.join(FLY, f"test_{t}.py")]) for t in TESTS] + [("so101", [os.path.join(FLY, "test_so101.py"), "--zgoda-sim"])]

bad = []
for i, (name, args) in enumerate(JOBS, 1):
    t0 = time.time()
    r = subprocess.run([sys.executable, "-I", "-B", *args], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    last = (r.stdout.strip().splitlines() or ["(brak wyjścia)"])[-1][:140]
    ok = r.returncode == 0
    print(f"[{i:2d}/{len(JOBS)}] {'OK  ' if ok else 'BŁĄD'} test_{name:22s} {time.time() - t0:5.1f} s   {last}", flush=True)
    if not ok:
        bad.append(name)
        print(r.stdout[-3000:], flush=True)
print(f"\nPODSUMOWANIE: {len(JOBS) - len(bad)}/{len(JOBS)} zestawów OK" + (f"; błędy: {bad}" if bad else ""), flush=True)
sys.exit(1 if bad else 0)
