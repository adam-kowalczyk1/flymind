"""flymind/latency.py — narzędzia pomiaru opóźnień (krok 10). Czysta biblioteka standardowa + numpy; bez mujoco,
bez bio2, nic nie zapisuje i nie zmienia środowiska.

StageTimer   czas zegarowy etapów taktu i CAŁEGO taktu mierzony bezpośrednio (begin → end), nie jako suma etapów
summarize    p50/p95/p99/max i przekroczenia terminu; percentyle liczone osobno dla każdego szeregu (nie sumować!)
DelayLine    opóźnienie o k taktów (FIFO); k = 0 → wartość z tego samego taktu
env_info     opis maszyny i bibliotek (odczyt; wersje z metadanych pakietów, bez importu mujoco)
"""
import gc
import importlib.metadata
import os
import platform
import sys
import time
from collections import deque
from contextlib import contextmanager

import numpy as np

PCT_METHOD = "linear"                  # numpy.percentile, interpolacja liniowa między próbkami


class LatencyError(ValueError):
    pass


def summarize(ns, deadline_ms=10.0):
    """Statystyki szeregu czasów [ns] → ms. Przekroczenie: wartość > deadline_ms (ściśle)."""
    x = np.asarray(ns, dtype=np.float64) / 1e6
    if x.size == 0:
        return dict(n=0)
    p50, p95, p99 = np.percentile(x, [50, 95, 99], method=PCT_METHOD)
    over = int((x > deadline_ms).sum())
    return dict(n=int(x.size), p50_ms=float(p50), p95_ms=float(p95), p99_ms=float(p99), max_ms=float(x.max()),
                mean_ms=float(x.mean()), over_deadline=over, over_frac=over / x.size, deadline_ms=deadline_ms)


class StageTimer:
    """Użycie:  t.begin(); with t.stage("snn"): ...; t.end()  — jeden takt.
    Pierwsze `warmup` taktów jest zapisywanych, ale wykluczanych ze statystyk (raport podaje ich liczbę).
    absent(nazwa, powód): etap, którego pętla NIE wykonuje (np. brak enkodera) — w raporcie jako brak, nie jako 0."""

    def __init__(self, warmup, clock=time.perf_counter_ns, deadline_ms=10.0):
        if warmup < 0:
            raise LatencyError("warmup ≥ 0")
        self.warmup, self.clock, self.deadline = int(warmup), clock, deadline_ms
        self.ticks, self.stages, self.missing = [], {}, {}
        self._t0, self._k = None, 0

    def begin(self):
        if self._t0 is not None:
            raise LatencyError("begin() bez end() poprzedniego taktu")
        self._t0 = self.clock()

    @contextmanager
    def stage(self, name):
        if self._t0 is None:
            raise LatencyError(f"etap {name!r} poza taktem")
        if name in self.missing:
            raise LatencyError(f"etap {name!r} oznaczony jako nieobecny")
        s = self.clock()
        try:
            yield
        finally:
            self.stages.setdefault(name, []).append((self._k, self.clock() - s))

    def end(self):
        if self._t0 is None:
            raise LatencyError("end() bez begin()")
        self.ticks.append(self.clock() - self._t0)
        self._t0 = None
        self._k += 1

    def absent(self, name, reason):
        if not reason or name in self.stages:
            raise LatencyError(f"absent({name!r}): wymagany powód i etap nie może mieć pomiarów")
        self.missing[name] = reason

    def report(self):
        w = self.warmup
        return dict(
            warmup_ticks=min(w, len(self.ticks)), measured_ticks=max(len(self.ticks) - w, 0),
            clock="time.perf_counter_ns (monotoniczny)", percentile_method=PCT_METHOD,
            tick_total=summarize(self.ticks[w:], self.deadline),
            stages={k: summarize([d for i, d in v if i >= w], self.deadline) for k, v in self.stages.items()},
            absent_stages=dict(self.missing),
            note="tick_total mierzony bezpośrednio; percentyle etapów NIE sumują się do percentyli taktu")


class DelayLine:
    """Opóźnienie o k taktów. push(x) zwraca wartość podaną k wywołań wcześniej; przez pierwsze k wywołań — `fill`
    (jawna wartość początkowa, np. None = „brak danych”). k = 0: push(x) zwraca x (bez opóźnienia)."""

    def __init__(self, k, fill):
        if not isinstance(k, int) or isinstance(k, bool) or k < 0:
            raise LatencyError(f"k musi być int ≥ 0, jest {k!r}")
        self.k = k
        self.q = deque([fill] * k)

    def push(self, x):
        if self.k == 0:
            return x
        self.q.append(x)
        return self.q.popleft()


def env_info():
    """Opis środowiska (tylko odczyt). Wynik z jednej maszyny nie przenosi się na inny sprzęt."""
    def ver(p):
        try:
            return importlib.metadata.version(p)
        except importlib.metadata.PackageNotFoundError:
            return None
    try:
        ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (ValueError, OSError, AttributeError):
        ram = None
    return dict(
        python=sys.version.split()[0], implementation=platform.python_implementation(),
        platform=platform.platform(), machine=platform.machine(), processor=platform.processor(),
        cpu_count=os.cpu_count(), ram_bytes=ram,
        packages={p: ver(p) for p in ("numpy", "mujoco", "pandas", "pyarrow")},
        blas_threads_env={k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                                                          "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")},
        gc_enabled=gc.isenabled(), gc_counts=gc.get_count(), dont_write_bytecode=sys.flags.dont_write_bytecode,
        clock_info=dict(vars(time.get_clock_info("perf_counter"))))
