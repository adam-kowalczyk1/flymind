# Diagnoza: czy drugi SO101Sim (drugi mujoco.Renderer) w tym samym procesie renderuje poprawnie?
import sys, time, hashlib
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import numpy as np
from so101 import SO101Sim
Q = np.array([0, 0, 0, 0, 0, 0.93])
def probe(sim, label):
    sim.reset(Q)
    hs, ts, means = [], [], []
    for k in range(40):
        t = time.perf_counter(); img = sim.observe().frame.image; ts.append(time.perf_counter() - t)
        hs.append(hashlib.sha256(img.tobytes()).hexdigest()[:8]); means.append(img.mean())
        sim.act(np.r_[0.02 * k, Q[1:5]], 0.0); sim.step()
    print(f"{label}: unikalnych klatek {len(set(hs))}/40, observe mediana {np.median(ts)*1e3:.3f} ms, "
          f"jasność {min(means):.1f}…{max(means):.1f}, ctx={getattr(sim.renderer, '_gl_context', None)!r}")
    return hs
a = SO101Sim(); ha = probe(a, "sim A (pierwszy)")
b = SO101Sim(); hb = probe(b, "sim B (drugi, A żyje)")
print("A i B identyczne sekwencje:", ha == hb)
ha2 = probe(a, "sim A ponownie (po utworzeniu B)")
b.renderer.close(); a.renderer.close(); del a, b
c = SO101Sim(); hc = probe(c, "sim C (po close() A i B)")
print("C == A:", hc == ha)
