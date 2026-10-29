"""Testy jednostkowe narzędzi opóźnień: sztuczny zegar i dane syntetyczne. Bez mujoco, bez benchmarków, bez zapisu.
Uruchom:  .venv/bin/python -I -B flymind/test_latency.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from latency import DelayLine, LatencyError, StageTimer, env_info, summarize  # noqa: E402


class FakeClock:
    """Zegar [ns], który przesuwa się tylko jawnie."""
    def __init__(self):
        self.t = 0

    def __call__(self):
        return self.t


def raises(fn, *a, **kw):
    try:
        fn(*a, **kw)
    except LatencyError:
        return True
    return False


def main():
    # summarize: 1..100 ms → percentyle liniowe znane analitycznie; przekroczenie ściśle > 10 ms
    s = summarize(np.arange(1, 101) * 1_000_000)
    assert s["n"] == 100 and s["p50_ms"] == 50.5 and np.isclose(s["p99_ms"], 99.01) and s["max_ms"] == 100
    assert s["over_deadline"] == 90 and s["over_frac"] == 0.9
    assert summarize([10_000_000])["over_deadline"] == 0 and summarize([])["n"] == 0

    # StageTimer: takt mierzony bezpośrednio (z narzutem poza etapami), rozgrzewka wykluczona, etap nieobecny zgłoszony
    c = FakeClock()
    t = StageTimer(warmup=2, clock=c)
    t.absent("encoder", "brak enkodera obraz→SNN w flymind/")
    for k in range(5):
        t.begin()
        with t.stage("snn"):
            c.t += (100 if k < 2 else 3) * 1_000_000          # rozgrzewka: 100 ms, potem 3 ms
        with t.stage("physics"):
            c.t += 2_000_000
        c.t += 1_000_000                                       # czas poza etapami (np. logika pętli)
        t.end()
    r = t.report()
    assert r["warmup_ticks"] == 2 and r["measured_ticks"] == 3
    assert r["stages"]["snn"]["max_ms"] == 3 and r["stages"]["physics"]["p50_ms"] == 2
    assert r["tick_total"]["p50_ms"] == 6 and r["tick_total"]["over_deadline"] == 0     # 3 + 2 + 1, nie 3 + 2
    assert r["absent_stages"] == {"encoder": "brak enkodera obraz→SNN w flymind/"} and "encoder" not in r["stages"]

    # błędy użycia: etap poza taktem, podwójne begin, end bez begin, pomiar etapu nieobecnego, absent bez powodu
    t = StageTimer(0, clock=c)
    assert raises(lambda: t.stage("x").__enter__())
    t.begin()
    assert raises(t.begin)
    t.absent("enc", "brak")
    assert raises(lambda: t.stage("enc").__enter__()) and raises(t.absent, "y", "")
    t.end()
    assert raises(t.end) and raises(StageTimer, -1)

    # DelayLine: k = 0 bez opóźnienia; k = 2 → FIFO, pierwsze k wyjść = fill
    d0 = DelayLine(0, fill=None)
    assert [d0.push(x) for x in "abc"] == ["a", "b", "c"]
    d2 = DelayLine(2, fill=None)
    assert [d2.push(x) for x in range(5)] == [None, None, 0, 1, 2]
    assert raises(DelayLine, -1, None) and raises(DelayLine, 1.0, None) and raises(DelayLine, True, None)

    # env_info: tylko odczyt, bez importu mujoco
    e = env_info()
    assert e["cpu_count"] and "numpy" in e["packages"] and "mujoco" not in sys.modules
    print("OK: narzędzia opóźnień (15 asercji)")


if __name__ == "__main__":
    main()
