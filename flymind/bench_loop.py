"""flymind/bench_loop.py — SZKIELET pomiarów B1–B3 (krok 10). Nie uruchamia się bez jawnej flagi zgody.

  B1  czas zegarowy etapów jednej pętli: observe (render + stan) → bramka → [enkoder: BRAK] → bodziec PFL3 (zastępczy)
      → SNN 10 × 1 ms → dekoder → warstwa bezpieczeństwa → act → fizyka 10 × 1 ms; cały takt mierzony bezpośrednio.
      Render osobno (poza pętlą), bo SO101Sim.observe() nie rozdziela renderu od odczytu stanu.
  B2  skalowanie kroku ALIF z GĘSTĄ macierzą W (alif.py: self.W @ buf) — sieci SYNTETYCZNE, nie connectome.
  B3  test KOMPONENTU (nie pętli zamkniętej): skok prądu do PFL3 → zdarzenia DNa02 / dekoder / q_pan w czasie symulacji.
      Bodziec nie jest obrazem: brak enkodera obraz→SNN (zapisane w metadanych).

Uruchomienie (po osobnej zgodzie użytkownika; katalog --out musi istnieć i leżeć w flymind/ albo w $TMPDIR):
  TMPDIR=<scratchpad> .venv/bin/python -I -B flymind/bench_loop.py --zgoda-bench --which b1,b2,b3 --out <katalog>
Zapis: jeden nowy plik JSON na pomiar (tryb „x” — nigdy nie nadpisuje). Ziarna 1001–1013; 0–39 i 300–399 zabronione.
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FORBIDDEN_SEEDS = set(range(0, 40)) | set(range(300, 400))         # HELDOUT bio2 + zakres protokołu Stage 1
SEEDS = tuple(range(1001, 1011))                                    # B3: powtórzenia
CALIB_SEEDS = (1011, 1012, 1013)                                    # kalibracja dekodera (rozłączne z SEEDS)
B1_SEED, B2_SEED = 1001, 1001
WHICH = ("b1", "b2", "b3")
OPTS = ("--zgoda-bench", "--which", "--out", "--max-mem-gb", "--b1-ticks", "--b1-reps", "--warmup")


def parse(argv):
    ap = argparse.ArgumentParser(allow_abbrev=False, description=__doc__.split("\n")[0])
    ap.add_argument("--zgoda-bench", action="store_true", help="jawna zgoda użytkownika na benchmark")
    ap.add_argument("--which", default="b1,b2,b3")
    ap.add_argument("--out", required=True, help="istniejący katalog w flymind/ albo w $TMPDIR")
    ap.add_argument("--max-mem-gb", type=float, default=2.0, help="B2: limit szacowanej pamięci jednej sieci")
    ap.add_argument("--b1-ticks", type=int, default=3000)
    ap.add_argument("--b1-reps", type=int, default=3)
    ap.add_argument("--warmup", type=int, default=100)
    return ap.parse_args(argv)


def validate(a, argv):
    """Błędy blokujące — sprawdzane PRZED importem numpy, flymind i mujoco."""
    err = []
    if not a.zgoda_bench:
        err.append("brak --zgoda-bench (benchmark wymaga osobnej zgody użytkownika)")
    if not sys.flags.dont_write_bytecode:
        err.append("uruchom z python -B (inaczej powstałby flymind/__pycache__)")
    rep = [o for o in OPTS if sum(t == o or t.startswith(o + "=") for t in argv) > 1]
    if rep:
        err.append(f"powtórzone opcje {rep} (argparse wziąłby ostatnią po cichu)")
    which = a.which.split(",")
    if not which or set(which) - set(WHICH):
        err.append(f"--which: dozwolone {WHICH}")
    out = os.path.realpath(a.out)
    roots = [os.path.realpath(HERE)] + ([os.path.realpath(os.environ["TMPDIR"])] if os.environ.get("TMPDIR") else [])
    if not os.path.isdir(out):
        err.append(f"--out {out}: katalog nie istnieje (skrypt go nie tworzy)")
    elif not any(out == r or out.startswith(r + os.sep) for r in roots):
        err.append(f"--out {out}: poza dozwolonymi {roots}")
    if not (0 < a.max_mem_gb <= 8) or a.b1_ticks < 1 or a.b1_reps < 1 or a.warmup < 0:
        err.append("parametry liczbowe poza zakresem (max-mem-gb ∈ (0, 8], ticks/reps ≥ 1, warmup ≥ 0)")
    bad = sorted(FORBIDDEN_SEEDS & set(SEEDS + CALIB_SEEDS + (B1_SEED, B2_SEED)))
    if bad:
        err.append(f"ziarna zabronione: {bad}")
    return err, which, out


# ---------------------------------------------------------------- wspólne (importy po walidacji)

def _ctx():
    """Moduły ładowane dopiero po walidacji argumentów."""
    sys.path.insert(0, HERE)
    import numpy as np
    import pandas as pd
    from alif import ALIF, ALIFParams
    from connectome import load_edges, map_populations
    from decoder import DecoderError, SteerDecoder, SteerParams, fit_steer
    from latency import StageTimer, env_info, summarize
    from safety import Command, Limits, SafetyLayer
    from sensory import SensoryGate
    from snn_interface import ModelEdge, ModelParams, build
    return {k: v for k, v in locals().items()}


DATA = os.path.join(ROOT, "data", "malecns")
WEIGHTS = os.path.join(DATA, "connectome-weights-male-cns-v1.0-minconf-0.5.feather")
NTS = os.path.join(DATA, "body-neurotransmitters-male-cns-v1.0.feather")
CIRCUIT = os.path.join(ROOT, "bio2", "circuit_bio2.json")          # tylko odczyt listy neuronów (bez importu bio2)
J0, NOISE = 0.3, 2.0                                                  # jak kroki 5–8 (bio2 J0_RAW, noise)
Q0 = (0.0, 0.0, 0.0, 0.0, 0.0, 0.93)                                  # poza startowa jak T2–T6


def brain(c):
    """Mózg bio2 (moduły cx, dn, loom, hs) z danych + krawędzie modelowe DNa01 (kopia PFL3→DNa02, bio2 brain.py:111).
    Zwraca (spec dane+model, spec tylko dane, indeksy populacji, metadane)."""
    np, pd = c["np"], c["pd"]
    ann = pd.DataFrame([n for n in json.load(open(CIRCUIT))["neurons"] if n["module"] in ("cx", "dn", "loom", "hs")])
    ids = ann.bodyId.tolist()
    pops, prep = c["map_populations"](ann, {f"{t}_{s}": dict(type=t, side=s)
                                            for t in ("PFL3", "DNa02", "DNa01") for s in "LR"})
    e, erep = c["load_edges"](WEIGHTS, bodies=ids)
    nt = pd.read_feather(NTS)
    me = []
    for sp, so in (("L", "R"), ("R", "L")):
        post02, post01 = pops[f"DNa02_{so}"], pops[f"DNa01_{so}"]
        for p in pops[f"PFL3_{sp}"]:
            w = int(e.weight[(e.body_pre == p) & e.body_post.isin(post02)].sum())
            if w:
                me += [c["ModelEdge"](int(p), int(b), float(w), "bio2 brain.py:111 kopia PFL3→DNa02 (brak w danych)")
                       for b in post01]
    mp = c["ModelParams"](J0=J0)
    full = c["build"](e, ids, nt, mp, model_edges=me)
    data = c["build"](e, ids, nt, mp, model_edges=me, include_model=False)
    pos = {b: i for i, b in enumerate(ids)}
    idx = {k: [pos[int(b)] for b in v] for k, v in pops.items()}
    meta = dict(neurons=len(ids), populations=prep["sizes"], edges=erep["loaded"], model_edges=len(me),
                J0=J0, noise_mV=NOISE, W_sha256_full=full.report["W_sha256"], W_sha256_data=data.report["W_sha256"])
    return full, data, idx, meta


def pfl3_proxy(np, n, idx, x):
    """BODZIEC ZASTĘPCZY (nie obraz, nie kąt celu): prąd PFL3_L = 8 + 4x, PFL3_R = 8 − 4x [mV], x ∈ [−1, 1]."""
    I = np.zeros(n)
    I[idx["PFL3_L"]], I[idx["PFL3_R"]] = 8 + 4 * x, 8 - 4 * x
    return I


def calibrate(c, spec, idx, channels):
    """offset/slope dekodera z ziaren CALIB_SEEDS: x ∈ {−1, −0,5, 0, 0,5, 1}, 1 s, średnia L−P z ostatnich 500 ms."""
    np = c["np"]
    X, Y = [], []
    for x in (-1.0, -0.5, 0.0, 0.5, 1.0):
        for s in CALIB_SEEDS:
            net = c["ALIF"](spec, c["ALIFParams"](noise=NOISE), s)
            dec = c["SteerDecoder"](idx, channels, [0.0] * len(channels), [1.0] * len(channels), c["SteerParams"]())
            I, acc = pfl3_proxy(np, len(spec.bodies), idx, x), []
            for k in range(100):
                o = dec.step(net.run(I, 10), 1.0)
                if k >= 50:
                    acc.append(o["diff_hz"])
            X.append(x)
            Y.append(np.mean(acc, 0))
    return c["fit_steer"](np.array(X), np.array(Y), min_slope=2.0)


def check_timing(sim, lim, P):
    """Spójność okresów: takt fizyki = takt bezpieczeństwa = 10 kroków SNN."""
    tick = sim.cfg.n_sub * sim.cfg.timestep
    if not (abs(tick - lim.dt) < 1e-12 and abs(10 * P.dt / 1000 - tick) < 1e-12):
        raise RuntimeError(f"niespójne okresy: fizyka {tick} s, bezpieczeństwo {lim.dt} s, SNN 10×{P.dt} ms")
    return tick


# ---------------------------------------------------------------- B1

def b1(c, a):
    from so101 import SO101Sim, integrate_pan
    np = c["np"]
    full, _, idx, meta = brain(c)
    off, sl = calibrate(c, full, idx, ("DNa02",))
    P = c["ALIFParams"](noise=NOISE)
    reps = []
    for r in range(a.b1_reps):
        sim = SO101Sim()
        sim.reset(np.array(Q0))
        lim = c["Limits"](sim.jrange)
        dt = check_timing(sim, lim, P)
        net, safe = c["ALIF"](full, P, B1_SEED + r), c["SafetyLayer"](lim)
        dec = c["SteerDecoder"](idx, ("DNa02",), off, sl, c["SteerParams"]())
        gate = c["SensoryGate"](sim.cfg.cam_shape, dt, 0.03, 0.05)
        T = c["StageTimer"](warmup=a.warmup)
        T.absent("encoder", "brak enkodera obraz→SNN w flymind/ — bodziec PFL3 jest zastępczy")
        tgt, last_img, wall0 = Q0[0], -1.0, time.perf_counter()
        for k in range(a.warmup + a.b1_ticks):
            x = 1.0 if (k // 100) % 2 == 0 else -1.0
            T.begin()
            with T.stage("observe(render+stan)"):
                obs = sim.observe()
            with T.stage("gate"):
                if gate.push(obs.frame, obs.t).usable:
                    last_img = obs.frame.t_capture
            with T.stage("stimulus_pfl3_proxy"):
                I = pfl3_proxy(np, len(full.bodies), idx, x)
            with T.stage("snn_10x1ms"):
                spk = net.run(I, 10)
            with T.stage("decoder"):
                o = dec.step(spk, 1.0)
            with T.stage("safety"):
                tgt = integrate_pan(tgt, o["omega"], dt)
                out, tau, _, _ = safe.step(c["Command"](obs.t, {0: tgt}, None, {0: "snn:DNa02"}), obs.q, obs.t,
                                           obs.t - last_img)
                tgt = out[0]
            with T.stage("act"):
                sim.act(out, tau)
            with T.stage("physics_10x1ms"):
                sim.step()
            T.end()
        wall = time.perf_counter() - wall0
        rep = T.report()
        rep.update(sim_seconds=sim.d.time, wall_seconds=wall, realtime_factor=sim.d.time / wall,
                   safety_interventions=safe.stats["per_source"], gate=gate.stats, sim_stats=sim.stats)
        # render osobno: ta sama scena, poza pętlą — NIE dodawany do kosztu taktu
        R = c["StageTimer"](warmup=50)
        for _ in range(550):
            R.begin()
            with R.stage("render_only"):
                sim.renderer.update_scene(sim.d, camera="eye", scene_option=sim.opt)
                sim.renderer.render()
            R.end()
        rep["render_only_separate"] = R.report()["stages"]["render_only"]
        sim.close()                    # jawnie, we własnym kontekście GL (patrz SO101Sim.close)
        reps.append(rep)
    return dict(kind="B1 czas zegarowy etapów", network=meta, calibration=dict(offset=off.tolist(), slope=sl.tolist(),
                seeds=CALIB_SEEDS), stimulus="PFL3 zastępczy, x = ±1 przełączany co 100 taktów", repetitions=reps)


# ---------------------------------------------------------------- B2

B2_N = (272, 1000, 3000, 10000)
B2_STEPS = {272: 2000, 1000: 1000, 3000: 300, 10000: 60}
B2_GEN = dict(density=9252 / 272 ** 2, exc_frac=0.8, weight_mV="0,3 · U{1..19}", seed=B2_SEED,
              note="gęstość jak circuit_bio2 (9252 krawędzi / 272²); sieć losowa, NIE connectome")


def b2_estimate(N, density):
    """Szacunek szczytu pamięci [B]: W float64 (N²) + wektory generatora i stanu (O(N), z zapasem)."""
    return 8 * N * N + 256 * N


def b2(c, a):
    import resource
    import tracemalloc
    from types import SimpleNamespace
    np = c["np"]
    ram = c["env_info"]()["ram_bytes"] or 0
    res = []
    for N in B2_N:
        est = b2_estimate(N, B2_GEN["density"])
        if est > a.max_mem_gb * 2 ** 30 or (ram and est > 0.25 * ram):
            res.append(dict(N=N, skipped=f"szacunek {est / 2**30:.2f} GiB > limit {a.max_mem_gb} GiB lub 25 % RAM"))
            continue
        tracemalloc.start()
        t0 = time.perf_counter_ns()
        rng = np.random.default_rng(B2_SEED)
        W = np.zeros((N, N))
        sign = np.where(rng.random(N) < B2_GEN["exc_frac"], 1.0, -1.0)       # znak per neuron presynaptyczny
        for i in range(N):                                                  # wiersz po wierszu: pamięć O(N)
            cols = np.flatnonzero(rng.random(N) < B2_GEN["density"])
            W[i, cols] = 0.3 * rng.integers(1, 20, cols.size) * sign[cols]
        np.fill_diagonal(W, 0.0)
        net = c["ALIF"](SimpleNamespace(W=W), c["ALIFParams"](noise=NOISE), B2_SEED)
        init_ns = time.perf_counter_ns() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        T, I = c["StageTimer"](warmup=10), np.zeros(N)
        for _ in range(10 + B2_STEPS[N]):
            T.begin()
            with T.stage("alif_step_1ms"):
                net.step(I)
            T.end()
        res.append(dict(N=N, init_ms=init_ns / 1e6, W_bytes=int(W.nbytes), estimate_bytes=est,
                        tracemalloc_peak_bytes=int(peak), ru_maxrss_after=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                        step_1ms=T.report()["stages"]["alif_step_1ms"],
                        note="krok = W@buf (gęsty) + aktualizacja stanu; takt 10 ms ≈ 10 kroków (nie mierzony tu)"))
        del W, net
    return dict(kind="B2 skalowanie kroku ALIF (sieci syntetyczne)", generator=B2_GEN, results=res,
                init_includes="generacja W wiersz po wierszu (Bernoulli) + ALIF.__init__",
                ru_maxrss_units="bajty na macOS, KiB na Linuksie")


# ---------------------------------------------------------------- B3

PRE_TICKS, POST_TICKS = 100, 200          # 1 s x = −1, potem 2 s x = +1 (skok w chwili t_on = 1,0 s czasu symulacji)


def b3_trial(c, sim_cls, integrate_pan, spec, idx, channels, off, sl, seed):
    """Jedna próba. Stan początkowy: sim.reset(Q0), nowa sieć ALIF(seed), nowy dekoder/bramka/bezpieczeństwo."""
    np = c["np"]
    sim = sim_cls()
    sim.reset(np.array(Q0))
    lim = c["Limits"](sim.jrange)
    P = c["ALIFParams"](noise=NOISE)
    dt = check_timing(sim, lim, P)
    net, safe = c["ALIF"](spec, P, seed), c["SafetyLayer"](lim)
    dec = c["SteerDecoder"](idx, channels, off, sl, c["SteerParams"]())
    gate = c["SensoryGate"](sim.cfg.cam_shape, dt, 0.03, 0.05)
    L, R = idx["DNa02_L"], idx["DNa02_R"]
    tgt, last_img, rec, w0 = Q0[0], -1.0, dict(diff=[], omega=[], q=[], spL=[], spR=[]), time.perf_counter()
    t_on = PRE_TICKS * dt
    for k in range(PRE_TICKS + POST_TICKS):
        obs = sim.observe()
        if gate.push(obs.frame, obs.t).usable:
            last_img = obs.frame.t_capture
        spk = net.run(pfl3_proxy(np, len(spec.bodies), idx, -1.0 if k < PRE_TICKS else 1.0), 10)
        o = dec.step(spk, 1.0)
        tgt = integrate_pan(tgt, o["omega"], dt)
        out, tau, _, _ = safe.step(c["Command"](obs.t, {0: tgt}, None, {0: "snn:DNa02"}), obs.q, obs.t, obs.t - last_img)
        tgt = out[0]
        sim.act(out, tau)
        sim.step()
        rec["diff"].append(float(o["diff_hz"][0]))
        rec["omega"].append(o["omega"])
        rec["q"].append(float(sim.d.qpos[sim.qadr[0]]))                    # q_pan po fizyce tego taktu
        rec["spL"].append(spk[:, L].any(1))
        rec["spR"].append(spk[:, R].any(1))
    sim.close()
    return b3_events(np, rec, t_on, dt), time.perf_counter() - w0


def b3_events(np, rec, t_on, dt):
    """Definicje operacyjne (czas względem t_on; wartość taktu k odpowiada końcowi taktu, czyli (k − k_on + 1)·dt):
    E1 pierwszy spike DNa02 strony zyskującej (większa średnia po bodźcu); niezdefiniowane, jeśli ta strona miała
       spike w ostatnich 200 ms przed bodźcem.
    E2 różnica L−P (DNa02, wyjście dekodera) przekracza połowę drogi między średnią przed (ostatnie 200 ms) a średnią
       po (ostatnie 500 ms okna); brak odpowiedzi, jeśli |zmiana| < 3·σ_przed + 1 Hz.
    E3 ω > 0 (oczekiwany znak dla skoku x −1 → +1) przez 3 kolejne takty; niezdefiniowane, jeśli ω > 0 już przed bodźcem.
    E4 odwrócenie ruchu bazy: q_pan spada o > 1 mrad poniżej swojego maksimum od t_on (ruch w lewo = −q).
    Brak zdarzenia do końca okna (2 s) → None (cenzurowane), liczone osobno, nigdy nie pomijane po cichu."""
    k_on = PRE_TICKS
    d, om, q = (np.array(rec[k]) for k in ("diff", "omega", "q"))
    spL, spR = np.concatenate(rec["spL"]), np.concatenate(rec["spR"])     # [ms]
    ms_on = k_on * 10
    gain_R = spR[ms_on + 1500:].mean() - spR[ms_on - 200:ms_on].mean() > spL[ms_on + 1500:].mean() - spL[ms_on - 200:ms_on].mean()
    sp = spR if gain_R else spL
    ev = {}
    if sp[ms_on - 200:ms_on].any():
        ev["E1_first_spike_ms"] = "niezdefiniowane: strona zyskująca aktywna przed bodźcem"
    else:
        hit = np.flatnonzero(sp[ms_on:])
        ev["E1_first_spike_ms"] = float(hit[0] + 1) if hit.size else None    # spike w kroku j → koniec kroku j
    pre, post = d[k_on - 20:k_on], d[-50:]
    if abs(post.mean() - pre.mean()) < 3 * pre.std() + 1.0:
        ev["E2_diff_half_ms"] = None
    else:
        mid, up = (pre.mean() + post.mean()) / 2, post.mean() > pre.mean()
        hit = np.flatnonzero((d[k_on:] >= mid) if up else (d[k_on:] <= mid))
        ev["E2_diff_half_ms"] = float((hit[0] + 1) * dt * 1000) if hit.size else None
    if (om[k_on - 3:k_on] > 0).all():
        ev["E3_omega_sign_ms"] = "niezdefiniowane: ω > 0 przed bodźcem"
    else:
        pos = om[k_on:] > 0
        hit = [i for i in range(len(pos) - 2) if pos[i:i + 3].all()]
        ev["E3_omega_sign_ms"] = float((hit[0] + 1) * dt * 1000) if hit else None
    qa = q[k_on:]
    hit = np.flatnonzero(np.maximum.accumulate(qa) - qa > 1e-3)
    ev["E4_pan_reversal_ms"] = float((hit[0] + 1) * dt * 1000) if hit.size else None
    ev["gaining_side"] = "R" if gain_R else "L"
    return ev


def b3(c, a):
    from so101 import SO101Sim, integrate_pan
    np = c["np"]
    full, _, idx, meta = brain(c)
    try:
        off, sl = calibrate(c, full, idx, ("DNa02", "DNa01"))
    except c["DecoderError"] as e:
        return dict(kind="B3", error=f"kalibracja odrzucona: {e}")
    out = dict(kind="B3 test komponentu (skok prądu PFL3) — NIE pętla zamknięta, NIE reakcja na obraz",
               network=meta, calibration=dict(offset=off.tolist(), slope=sl.tolist(), seeds=CALIB_SEEDS),
               protocol=dict(t_on_s=PRE_TICKS * 0.01, pre_x=-1.0, post_x=1.0, window_s=POST_TICKS * 0.01, seeds=SEEDS,
                             q0=Q0, definitions=b3_events.__doc__,
                             same_network_both_variants="tak — sieć dane+model; różni się tylko zestaw kanałów dekodera"),
               intrinsic=dict(tick_quantization_ms=10, synaptic_delay_ms_per_hop=2,
                              filter_half_rise_ms={"rate_50ms": 50 * np.log(2), "DNa02_0.10s": 100 * np.log(2),
                                                   "DNa01_0.40s": 400 * np.log(2)}),
               variants={})
    for name, ch in (("DNa02", (0,)), ("DNa02+DNa01", (0, 1))):
        chans = tuple(("DNa02", "DNa01")[i] for i in ch)
        trials = [b3_trial(c, SO101Sim, integrate_pan, full, idx, chans, off[list(ch)], sl[list(ch)], s) for s in SEEDS]
        agg = {}
        for key in trials[0][0]:
            if key == "gaining_side":
                continue
            v = [t[0][key] for t in trials]
            num = np.array([x for x in v if isinstance(x, float)])
            agg[key] = dict(n=len(v), n_censored=sum(x is None for x in v), n_undefined=sum(isinstance(x, str) for x in v),
                            median_ms=float(np.median(num)) if num.size else None,
                            iqr_ms=[float(x) for x in np.percentile(num, [25, 75])] if num.size else None,
                            min_ms=float(num.min()) if num.size else None, max_ms=float(num.max()) if num.size else None)
        out["variants"][name] = dict(trials=[t[0] for t in trials], aggregate=agg,
                                     wall_seconds_per_trial=[t[1] for t in trials])
    out["note"] = ("porównanie wariantów opisuje dekoder w tym modelu; nie dowodzi biologicznej poprawności DNa01 "
                   "(wejście DNa01 to w 92–96 % krawędzie modelowe)")
    return out


# ----------------------------------------------------------------

def main(argv):
    a = parse(argv)
    err, which, out = validate(a, argv)
    if err:
        print("bench_loop: NIE uruchomiono:\n  " + "\n  ".join(err))
        return 2
    c = _ctx()
    for w in which:
        t0 = time.perf_counter()
        res = dict(bench=w, started=time.strftime("%Y-%m-%dT%H:%M:%S"), env=c["env_info"](), argv=argv,
                   result={"b1": b1, "b2": b2, "b3": b3}[w](c, a), wall_seconds_total=time.perf_counter() - t0,
                   caveat="wynik z jednej maszyny; nie dowodzi czasu rzeczywistego na innym sprzęcie")
        path = os.path.join(out, f"bench_{w}_{time.strftime('%Y%m%dT%H%M%S')}.json")
        with open(path, "x") as f:
            json.dump(res, f, ensure_ascii=False, indent=1, default=str)
        print(f"{w}: zapisano {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
