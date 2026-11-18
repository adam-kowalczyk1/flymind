"""flymind/test_stage0_dt.py — testy Etapu 0 (infrastruktura wielu dt). Protokół: program_stage0/STAGE0_PROTOCOL.md.
Bez mujoco, bez bio2. Sieci syntetyczne; jedyna sieć z danych to DATA przy dt = 1 w T1c (odtworzenie zapisanego przebiegu,
ziarna NOISE_SEEDS[0:2] z v5v41 — nic nowego nie jest liczone). Ziarna testowe 1001–1009. Zapis: --out (nowy plik JSON, tryb „x”).
Uruchom:  .venv/bin/python -I -B flymind/test_stage0_dt.py --out flymind/results/stage0
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time
from types import SimpleNamespace

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from alif import ALIF, ALIFParams  # noqa: E402
from alif_dt import ALIFdt, isi_continuous_ms, isi_steps, to_steps  # noqa: E402
from connectome import ConnectomeError  # noqa: E402
from decoder import SteerDecoder  # noqa: E402
import v5v41 as V  # noqa: E402
from v5v41_dt import BIN_MS, fano, simulate_dt  # noqa: E402

LADDER = (1.0, 0.2, 0.1, 0.05)
FINE = LADDER[1:]
NOP = dict(b_a=0.0, noise=0.0)
R = {}                                               # wyniki do JSON


def P(dt=1.0, **kw):
    return ALIFParams(**{**ALIFParams(noise=2.0).__dict__, "dt": dt, **kw})


def timing_for(dt):
    return "legacy" if dt == 1.0 else "exact"


def sha(p):
    return hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()


def synth_net(seed=1001, n_in=20, n_mid=15):
    """Mała sieć o strukturze ścieżki LC10a → pośrednie → DNa02 (bez danych). W[post, pre] w mV."""
    rng = np.random.default_rng(seed)
    N = 4 * 0 + 2 * n_in + 2 * n_mid + 2
    iL, iR = np.arange(n_in), np.arange(n_in, 2 * n_in)
    mL, mR = np.arange(2 * n_in, 2 * n_in + n_mid), np.arange(2 * n_in + n_mid, 2 * n_in + 2 * n_mid)
    dL, dR = np.array([N - 2]), np.array([N - 1])
    W = np.zeros((N, N))
    for src, dst in ((iL, mL), (iR, mR), (iL, mR), (iR, mL)):
        W[np.ix_(dst, src)] = rng.uniform(0.0, 30.0, (len(dst), len(src))) * (rng.random((len(dst), len(src))) < 0.5)
    W[np.ix_(mR, iL)] *= -0.5
    W[np.ix_(mL, iR)] *= -0.5
    W[np.ix_(iL, iL)] = rng.uniform(0, 0.4, (n_in, n_in)) * (rng.random((n_in, n_in)) < 0.2)
    W[np.ix_(dL, mL)], W[np.ix_(dR, mR)] = 12.0, 12.0
    W[np.ix_(dL, mR)], W[np.ix_(dR, mL)] = -1.0, -1.0
    np.fill_diagonal(W, 0)
    idx = dict(in_L=iL, in_R=iR, mid_L=mL, mid_R=mR, DNa02_L=dL, DNa02_R=dR)
    return SimpleNamespace(W=W), idx


def same(a, b):
    return all(np.array_equal(a[k], b[k]) for k in ("counts", "adapt", "angle", "ss")) and a["first_dn"] == b["first_dn"]


# ---------------------------------------------------------------- T1 regresja przy dt = 1
def t1a():
    spec, idx = synth_net()
    cfgs = {"step": dict(I=8.0, step_ms=1000), "noise0": dict(I=9.0, step_ms=300),
            "contra": dict(I=8.0, step_ms=300, contra_frac=0.5),
            "pre_ipsi": dict(I=8.0, step_ms=600, pre_ms=500, pre_side="ipsi", pre_mV=10.0),
            "pre_contra": dict(I=8.0, step_ms=600, pre_ms=500, pre_side="contra", pre_mV=10.0),
            "ramp": dict(I=None, ramp=(4.0, 12.0, 200)), "init_v": dict(I=8.0, step_ms=300, init_v=True)}
    out = {}
    for name, c in cfgs.items():
        p = P(noise=0.0) if name == "noise0" else P()
        for side in "LR":
            old = V.simulate(spec, idx, side, c, 1003, p, 1004)
            new = simulate_dt(spec, idx, side, c, 1003, p, 1004, timing="legacy")
            out[f"{name}_{side}"] = dict(identical=bool(same(old, new)), dn_spikes=int(old["counts"][:, 4:].sum()))
    assert all(v["identical"] for v in out.values()), out
    assert sum(v["dn_spikes"] for v in out.values()) > 0, "test pusty: DN nie strzela"
    R["T1a_synthetic_old_vs_new_harness_dt1"] = out


def t1b():
    spec, idx = synth_net(1002)
    N = spec.W.shape[0]
    I = np.random.default_rng(1005).uniform(0, 14, (2000, N))
    res = {}
    for name, p in (("noise2", P()), ("noise0", P(noise=0.0)), ("adapt0", P(b_a=0.0)), ("delay3", P(delay_ms=3.0))):
        a, b = ALIF(spec, p, 1006), ALIFdt(spec, p, 1006, timing="legacy")
        sa, sb = a.run(I, 2000), b.run(I, 2000)
        ok = np.array_equal(sa, sb) and all(np.array_equal(getattr(a, x), getattr(b, x)) for x in ("v", "g", "a"))
        res[name] = dict(identical=bool(ok), spikes=int(sa.sum()))
    assert all(v["identical"] for v in res.values()), res
    R["T1b_ALIFdt_vs_ALIF_dt1"] = res


def t1c():
    """DATA przy dt = 1: nowy harness vs zapisany results/v5v41/raw/DATA.npz (1 poziom, 2 strony, 2 powtórzenia; E1 i E3)."""
    d = np.load(os.path.join(HERE, "results", "v5v41", "raw", "DATA.npz"))
    spec, idx, _, _ = V.make_net("DATA", None)
    p = ALIFParams(noise=2.0)
    out = {}
    for ename, levels, cfg in (("E1", d["E1_levels"], dict(I=8.0, step_ms=1000)),
                               ("E3", d["E3_levels"], dict(I=8.0, step_ms=1000, pre_ms=500, pre_side="ipsi", pre_mV=10.0))):
        li = int(np.flatnonzero(levels == 8.0)[0])
        for si, side in enumerate("LR"):
            for r in range(2):
                x = simulate_dt(spec, idx, side, cfg, V.NOISE_SEEDS[r], p, V.INITV_SEEDS[r], timing="legacy")
                ok = (np.array_equal(x["counts"], d[f"{ename}_counts"][li, si, r]) and np.array_equal(x["adapt"], d[f"{ename}_adapt"][li, si, r])
                      and np.array_equal(x["angle"], d[f"{ename}_angle"][li, si, r]) and x["first_dn"] == d[f"{ename}_first_dn"][li, si, r])
                out[f"{ename}_8mV_{side}_rep{r}"] = dict(identical=bool(ok), dn_hz_ss=float(x["counts"][50:100, 4 + si].mean() * 100))
    assert all(v["identical"] for v in out.values()), out
    R["T1c_DATA_dt1_vs_stored_npz"] = out


# ---------------------------------------------------------------- T2 / T6b / T7b: raster o zadanych czasach fizycznych
class Raster:
    """Atrapa sieci: emituje spike'i w zadanych czasach [ms] (indeks = round(t/dt)); stan a = 0. Do testu harnessu."""
    def __init__(self, times, N, dt):
        self.N, self.k = N, 0
        self.v, self.g, self.a = np.zeros(N), np.zeros(N), np.zeros(N)
        self.ev = {}
        for n, ts in times.items():
            for t in ts:
                self.ev.setdefault(to_steps(t, dt, "exact"), []).append(n)

    def step(self, I):
        s = np.zeros(self.N, bool)
        s[self.ev.get(self.k, [])] = True
        self.k += 1
        return s


def t2():
    spec, idx = synth_net()
    N = spec.W.shape[0]
    rng = np.random.default_rng(1007)
    T = 1500
    times = {}
    for n in range(N):                                    # czasy na siatce 1 ms → reprezentowalne przy każdym dt
        rate = 20 if n < 40 else 60
        times[n] = sorted(set(rng.choice(np.arange(T), rng.poisson(rate * T / 1000), replace=False).tolist()))
    times[N - 2] = [507.0] + [t for t in times[N - 2] if t > 507]      # pierwszy DN_L po początku skoku: 7 ms
    cfg = dict(I=8.0, step_ms=1000, pre_ms=500, pre_side="ipsi", pre_mV=10.0)
    res = {dt: simulate_dt(spec, idx, "L", cfg, 0, P(dt), make=lambda s, p, sd, timing, dt=dt: Raster(times, N, dt))
           for dt in LADDER}
    ref = res[1.0]
    tab = {}
    for dt, x in res.items():
        assert x["T_ms"] == 1500 and x["steps"] * dt == 1500 and x["counts"].shape == ref["counts"].shape
        f = fano(x["counts"][50:100, :1])[0]
        tab[dt] = dict(steps=x["steps"], k_bin=x["k_bin"], T_ms=x["T_ms"], counts_equal=bool(np.array_equal(x["counts"], ref["counts"])),
                       ss_equal=bool(np.array_equal(x["ss"], ref["ss"])), first_dn_ms=x["first_dn"],
                       lc_ipsi_hz_ss=float(x["counts"][50:100, 0].mean() * 100), fano_lc_ipsi=float(f),
                       angle_max_abs_diff_vs_dt1=float(np.abs(x["angle"] - ref["angle"]).max()),
                       angle_max_abs_diff_vs_dt005=float(np.abs(x["angle"] - res[0.05]["angle"]).max()),
                       angle_absmax=float(np.abs(ref["angle"]).max()))
        assert tab[dt]["counts_equal"] and tab[dt]["ss_equal"] and abs(x["first_dn"] - 7.0) < 1e-9
        assert tab[dt]["fano_lc_ipsi"] == tab[1.0]["fano_lc_ipsi"]
    # spike'i między węzłami 1 ms (tylko dt < 1): 10 − dt → bin 0; 10,0 ms → bin 1; 20 − dt → bin 1
    sub = {}
    for dt in FINE:
        x = simulate_dt(spec, idx, "L", dict(I=8.0, step_ms=30), 0, P(dt),
                        make=lambda s, p, sd, timing, dt=dt: Raster({0: [10 - dt, 10.0, 20 - dt]}, N, dt))
        sub[dt] = x["counts"][:, 0].tolist()
        assert sub[dt] == [1, 2, 0], sub
    R["T2_same_spike_times_all_dt"] = dict(table={str(k): v for k, v in tab.items()}, subms_bins=sub)


# ---------------------------------------------------------------- T3 liczniki kroków
def t3():
    one = SimpleNamespace(W=np.zeros((1, 1)))
    tab = {}
    for dt in LADDER:
        net = ALIFdt(one, P(dt), 1001, timing=timing_for(dt))
        tab[str(dt)] = net.timing_report()
        if dt != 1.0:
            assert abs(net.n_ref * dt - 2.2) < 1e-12 and abs(net.n_delay * dt - 1.8) < 1e-12, tab[str(dt)]
    assert tab["1.0"]["n_ref"] == 3 and tab["1.0"]["n_delay"] == 2                  # stary model: 3,0 / 2,0 ms
    refused = {}
    for dt in (1.0, 0.5, 0.25, 0.3):
        try:
            ALIFdt(one, P(dt), 1001, timing="exact")
            refused[str(dt)] = False
        except ConnectomeError:
            refused[str(dt)] = True
    try:
        ALIFdt(one, P(0.1), 1001, timing="legacy")
        refused["legacy_at_0.1"] = False
    except ConnectomeError:
        refused["legacy_at_0.1"] = True
    assert all(refused.values()), refused
    # stary alif.ALIF (float ref -= dt): ile kroków faktycznie blokuje i jakie opóźnienie, dla porównania
    old = {}
    for dt in (1.0, 0.5, 0.25, 0.2, 0.1, 0.05):
        n = ALIF(one, P(dt, **NOP), 1001)
        s = np.flatnonzero(n.run(1e5, int(round(40 / dt)))[:, 0])
        isi = int(np.median(np.diff(s)))
        old[str(dt)] = dict(blocked_steps=isi - 1, t_ref_eff_ms=round((isi - 1) * dt, 6), delay_steps=n.p.delay_steps,
                            delay_eff_ms=round(n.p.delay_steps * dt, 6), r_max_formula_hz=round(float(n.p.r_max), 3),
                            r_max_measured_hz=round(1000 / (isi * dt), 3))
    R["T3_step_counters"] = dict(new=tab, exact_refuses_nonmultiples=refused, old_alif=old)


# ---------------------------------------------------------------- T4 f–I: symulacja = wzór dyskretny; wzór vs ciągły
def t4():
    D = np.arange(10.0, 100.001, 1.0) + 0.37             # +0,37 omija przypadki graniczne (D·(1−(1−h)^j) = Δ)
    sim_vs_formula, err = {}, {}
    for dt in LADDER:
        p = P(dt, **NOP)
        n_ref = ALIFdt(SimpleNamespace(W=np.zeros((1, 1))), p, 1, timing=timing_for(dt)).n_ref
        net = ALIFdt(SimpleNamespace(W=np.zeros((len(D), len(D)))), p, 1, timing=timing_for(dt))
        s = net.run(D, to_steps(600, dt, "exact"))
        mism = []
        for i, d in enumerate(D):
            t = np.flatnonzero(s[:, i])
            isi = np.unique(np.diff(t))
            want = isi_steps(d, dt, n_ref)
            if not (len(isi) == 1 and isi[0] == want and t[0] == want - n_ref - 1):
                mism.append((float(d), isi.tolist(), want))
        sim_vs_formula[str(dt)] = dict(n=len(D), mismatches=mism)
        rel = np.array([1000 / (isi_steps(d, dt, n_ref) * dt) / (1000 / isi_continuous_ms(d)) - 1 for d in D])
        err[str(dt)] = dict(max_abs_rel=float(np.abs(rel).max()), D_at_max=float(D[np.abs(rel).argmax()]), mean_rel=float(rel.mean()),
                            min_rel=float(rel.min()), max_rel=float(rel.max()))
    assert all(not v["mismatches"] for v in sim_vs_formula.values()), sim_vs_formula
    # tabela w punktach z rundy 3
    pts = {}
    for d in (10.0, 20.0, 30.0, 50.0, 100.0, 140.0):
        row = dict(continuous_hz=round(1000 / isi_continuous_ms(d), 2))
        for dt in LADDER:
            n_ref = 3 if dt == 1.0 else to_steps(2.2, dt, "exact")
            row[str(dt)] = round(1000 / (isi_steps(d, dt, n_ref) * dt), 2)
        pts[str(d)] = row
    crit4 = err["0.1"]["max_abs_rel"] <= 0.02
    R["T4_fI"] = dict(sim_equals_formula=sim_vs_formula, rel_err_vs_continuous_D10_100=err, points_hz=pts,
                      criterion4_dt01_within_2pct=bool(crit4))


# ---------------------------------------------------------------- T5 wariancja szumu
def t5():
    Nn, sigma, tau = 400, 2.0, 20.0
    one = SimpleNamespace(W=np.zeros((Nn, Nn)))
    out = {}
    for dt in LADDER:
        for label, ref_dt in (("scaled", 1.0), ("per_step_old", None)):
            if label == "per_step_old" and dt not in (1.0, 0.1):
                continue
            p = P(dt, b_a=0.0, v_th=1e6)
            net = ALIFdt(one, p, 1008, timing=timing_for(dt), noise_ref_dt=ref_dt)
            burn, meas = to_steps(200, dt, "exact"), to_steps(4000, dt, "exact")
            I0 = np.zeros(Nn)
            for _ in range(burn):
                net.step(I0)
            s1 = s2 = 0.0
            stride = max(1, to_steps(1.0, dt, "exact"))  # próbka co 1 ms (ta sama liczba próbek przy każdym dt)
            n = 0
            for k in range(meas):
                net.step(I0)
                if k % stride == 0:
                    x = net.v - p.v_rest
                    s1 += x.sum()
                    s2 += (x * x).sum()
                    n += Nn
            var = s2 / n - (s1 / n) ** 2
            h = dt / tau
            disc = sigma ** 2 / (tau * (2 - h)) if ref_dt else h * sigma ** 2 / (2 - h)
            cont = sigma ** 2 / (2 * tau)
            out[f"{dt}_{label}"] = dict(var=var, analytic_continuous=cont, analytic_discrete=disc,
                                        rel_vs_continuous=var / cont - 1, rel_vs_discrete=var / disc - 1)
    assert all(abs(v["rel_vs_continuous"]) <= 0.05 for k, v in out.items() if k.endswith("scaled")), out
    assert all(abs(v["rel_vs_discrete"]) <= 0.03 for v in out.values()), out
    R["T5_noise_variance"] = out


# ---------------------------------------------------------------- T6 opóźnienie, refrakcja, zapis czasu spike'u
def t6():
    spec = SimpleNamespace(W=np.array([[0.0, 0.0], [3.0, 0.0]]))      # 0 → 1, 3 mV
    out = {}
    for dt in LADDER:
        p = P(dt, **NOP)
        net = ALIFdt(spec, p, 1, timing=timing_for(dt))
        n = to_steps(20, dt, "exact")
        spk, g1, v1 = [], [], []
        for k in range(n):
            s = net.step(np.array([1e5 if k == 3 else 0.0, 0.0]))       # jeden impuls w kroku 3
            spk.append(bool(s[0]))
            g1.append(net.g[1])
            v1.append(net.v[1])
        k_spk = spk.index(True)
        k_g = next(i for i, x in enumerate(g1) if x > 0)
        k_v = next(i for i, x in enumerate(v1) if x != p.v_rest)
        out[str(dt)] = dict(pre_spike_step=k_spk, post_g_step=k_g, post_v_step=k_v, delay_steps=k_g - k_spk,
                            delay_ms=(k_g - k_spk) * dt, n_spikes=sum(spk), expected_steps=net.n_delay)
        assert k_spk == 3 and k_g - k_spk == net.n_delay and k_v == k_g and sum(spk) == 1, out[str(dt)]
        # refrakcja: bardzo silny napęd → spike co n_ref + 1 kroków; v = V_reset w n_ref krokach po wykryciu
        r = ALIFdt(SimpleNamespace(W=np.zeros((1, 1))), p, 1, timing=timing_for(dt))
        vs, ss = [], []
        for _ in range(to_steps(20, dt, "exact")):
            ss.append(bool(r.step(np.array([1e5]))[0]))
            vs.append(r.v[0])
        t = np.flatnonzero(ss)
        clamped = all(vs[i + j] == p.v_reset for i in t[:-1] for j in range(1, r.n_ref + 1))
        out[str(dt)].update(isi_steps=np.unique(np.diff(t)).tolist(), blocked_ms=r.n_ref * dt, min_isi_ms=(r.n_ref + 1) * dt,
                            r_max_hz=r.r_max_hz, clamped_during_ref=bool(clamped))
        assert np.unique(np.diff(t)).tolist() == [r.n_ref + 1] and clamped
    # pierwszy spike: znacznik k·dt, przekroczenie ciągłe w (k·dt, (k+1)·dt] + błąd Eulera → zbieżność do wzoru ciągłego
    fs = {}
    for dt in LADDER:
        D = 20.37
        net = ALIFdt(SimpleNamespace(W=np.zeros((1, 1))), P(dt, **NOP), 1, timing=timing_for(dt))
        k = int(np.flatnonzero(net.run(D, to_steps(30, dt, "exact"))[:, 0])[0])
        t_cont = 20.0 * math.log(D / (D - 7.0))
        fs[str(dt)] = dict(stamp_ms=k * dt, step_end_ms=(k + 1) * dt, continuous_ms=t_cont, stamp_minus_cont_ms=k * dt - t_cont)
    assert abs(fs["0.05"]["stamp_minus_cont_ms"]) <= 0.1, fs
    R["T6_delay_refractory_spike_time"] = dict(pulse=out, first_spike=fs)


# ---------------------------------------------------------------- T7 dekoder: τ 50 ms przy każdym dt
def t7():
    idx = {"DNa02_L": np.array([0]), "DNa02_R": np.array([1])}
    out = {}
    for dt in LADDER:
        dec = SteerDecoder(idx, ("DNa02",), [0.0], [V.DEC_SLOPE], V.STEER)
        k_bin = to_steps(BIN_MS, dt, "exact")
        n = to_steps(500, dt, "exact")
        sp = np.zeros((n, 2), bool)
        sp[0, 0] = True
        rs = []
        for b in range(n // k_bin):                      # dt przekazane jawnie; r nie zależy od podziału na chunki
            for row in sp[b * k_bin:(b + 1) * k_bin]:
                dec.step(row[None, :], dt)
                rs.append(dec.r[0])
        rs = np.array(rs)
        t = np.arange(n) * dt
        tau_fit = -1 / np.polyfit(t[1:400], np.log(rs[1:400]), 1)[0]
        area = float(rs.sum() * dt / 1000)
        out[str(dt)] = dict(tau_ms_fit=float(tau_fit), impulse_area_spikes=area, peak_hz=float(rs[0]),
                            ratio_at_50ms=float(rs[to_steps(50, dt, "exact")] / rs[0]))
        assert abs(tau_fit - 50) < 1e-6 and abs(area - 1) < 1e-3 and abs(out[str(dt)]["ratio_at_50ms"] - math.exp(-1)) < 1e-9
    # wywołanie z dt = 1 przy dt = 0,1 (błąd, który harness usuwa): stała czasowa i amplituda byłyby złe
    dec = SteerDecoder(idx, ("DNa02",), [0.0], [V.DEC_SLOPE], V.STEER)
    sp = np.zeros((1000, 2), bool)
    sp[0, 0] = True
    rs = []
    for row in sp:
        dec.step(row[None, :], 1.0)
        rs.append(dec.r[0])
    out["wrong_dt1_at_dt01"] = dict(tau_ms_effective=float(-1 / np.polyfit(np.arange(1, 400) * 0.1, np.log(rs[1:400]), 1)[0]),
                                    impulse_area_spikes=float(np.sum(rs) * 0.1 / 1000))
    R["T7_decoder_ema"] = out


# ---------------------------------------------------------------- T8 benchmark (sieć syntetyczna 424 neurony)
def t8():
    rng = np.random.default_rng(1009)
    N = 424
    W = rng.uniform(-1, 1, (N, N)) * (rng.random((N, N)) < 0.05)
    n_in = 135
    idx = dict(in_L=np.arange(n_in), in_R=np.arange(n_in, 2 * n_in), mid_L=np.arange(270, 345), mid_R=np.arange(345, 422),
               DNa02_L=np.array([422]), DNa02_R=np.array([423]))
    spec = SimpleNamespace(W=W)
    cfg = dict(I=8.0, step_ms=1000)
    tm = {}
    for dt in (1.0, 0.1):
        t0 = time.perf_counter()
        simulate_dt(spec, idx, "L", cfg, 1009, P(dt), timing=timing_for(dt))
        tm[str(dt)] = time.perf_counter() - t0
    forecast = 10 * tm["1.0"]
    R["T8_benchmark_synthetic"] = dict(wall_s_per_1s_sim=tm, forecast_dt01_s=forecast, ratio_vs_forecast=tm["0.1"] / forecast,
                                       within_3x=bool(tm["0.1"] <= 3 * forecast))


# ---------------------------------------------------------------- T9 nienaruszone pliki zamrożone
def t9(t_start):
    cfg = json.load(open(os.path.join(HERE, "results", "v5v41", "config.json")))["code_sha256"]
    base = json.load(open(os.path.join(HERE, "results", "v5v41", "integrity_baseline.json")))["protected"]
    frozen = {f: dict(now=sha(f), recorded=cfg[f]) for f in ("alif.py", "v5v41.py", "decoder.py", "snn_interface.py", "connectome.py")}
    frozen["loop.py"] = dict(now=sha("loop.py"), recorded=base["flymind/loop.py"])
    assert all(v["now"] == v["recorded"] for v in frozen.values()), frozen
    proto = os.path.join(HERE, "program_stage0", "STAGE0_PROTOCOL.md")
    R["T9_integrity"] = dict(frozen=frozen, new_modules={f: sha(f) for f in ("alif_dt.py", "v5v41_dt.py", "test_stage0_dt.py")},
                             protocol_sha256=sha("program_stage0/STAGE0_PROTOCOL.md"),
                             protocol_written_before_tests=bool(os.path.getmtime(proto) < t_start))
    assert R["T9_integrity"]["protocol_written_before_tests"]


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--out")
    ap.add_argument("--skip-data", action="store_true", help="pomiń T1c (sieć DATA przy dt = 1)")
    a = ap.parse_args()
    t_start = time.time()
    tests = [t9, t1a, t1b] + ([] if a.skip_data else [t1c]) + [t2, t3, t4, t5, t6, t7, t8]
    status = {}
    for fn in tests:
        t0 = time.perf_counter()
        try:
            fn(t_start) if fn is t9 else fn()
            status[fn.__name__] = "PASS"
        except AssertionError as e:
            status[fn.__name__] = f"FAIL: {str(e)[:2000]}"
        print(f"{fn.__name__:4s} {status[fn.__name__][:300]}  ({time.perf_counter() - t0:.1f} s)", flush=True)
    R["status"] = status
    R["env"] = dict(numpy=np.__version__, python=sys.version.split()[0], time=time.strftime("%Y-%m-%dT%H:%M:%S"))
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        path = os.path.join(a.out, f"stage0_tests_{time.strftime('%Y%m%dT%H%M%S')}.json")
        with open(path, "x") as f:
            json.dump(R, f, indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))
        print("zapisano:", path)
    sys.exit(0 if all(v == "PASS" for v in status.values()) else 1)


if __name__ == "__main__":
    main()
