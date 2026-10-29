import sys, gc
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
exec(open(sys.argv[1]).read().split("a = SO101Sim()")[0])          # funkcja probe() i importy z dbg_renderer.py
sim = SO101Sim(); h0 = probe(sim, "rep0")
sim = SO101Sim(); gc.collect(); h1 = probe(sim, "rep1 (nowy sim, stary usunięty PO utworzeniu nowego)")
print("rep1 == rep0:", h1 == h0)
sim = SO101Sim(); gc.collect(); h2 = probe(sim, "rep2")
# długi przebieg: czy wielokrotne make_current (CGLLockContext) nie blokuje i nie spowalnia
import time
t = time.perf_counter()
for k in range(3000):
    sim.observe(); sim.step()
print(f"3000 × observe+step po poprawce: {time.perf_counter()-t:.1f} s")
sim.close(); print("close() ok, renderer:", sim.renderer)
