"""flymind/loop.py — V5: pętla zamknięta w MuJoCo. obraz (kamera „eye”) → SensoryGate → TargetEncoder → LC10a →
sieć z danych (visual_path) → DNa02 L/R → SteerDecoder → integrate_pan → SafetyLayer → SO101Sim → nowa klatka.
Bez bio2; mujoco tylko przez so101.SO101Sim. Zapis tylko do --out (nowy plik, tryb „x”).

Zadanie (orientacja bazy na piłeczkę): poza bazą ramię stoi w pozie Q_POSE (kamera poziomo, pochylona ~34° w dół).
Piłeczka (r 2,5 cm) leży na stole w namiarze az0 od osi kamery (|az0| ~ U[10°, 30°], znak losowy) i odległości
ρ ~ U[0,16; 0,24] m od kamery (rzut poziomy). Pan startuje z 0. Czas 3 s (300 taktów po 10 ms, SNN 10 × 1 ms na takt).
Błąd e(t) = namiar piłeczki względem poziomego rzutu osi kamery z fk() i pozycji piłeczki w symulatorze — TYLKO do oceny;
sterownik dostaje wyłącznie obraz (i propriocepcję warstwy bezpieczeństwa).

Warunki (ten sam enkoder, bramka, warstwa bezpieczeństwa, symulator, takt):
  snn            sieć z danych, dekoder skalibrowany w V4 v2 (offset 0, slope z pliku wyników V4) — znak ustalony z góry
  snn_shuffle    ta sama sieć po tasowaniu krawędzi (ziarno = ziarno próby + 100 000), TEN SAM dekoder
  snn_swap       zamiana stron wejścia LC10a (przewidywanie: odwracanie się od celu)
  no_vision      klatki bez obrazu (image None) — enkoder dostaje brak bodźca
  classical_p    regulator P na wyjściu enkodera (gL − gR), skalibrowany na tych samych bodźcach syntetycznych co SNN,
                 ten sam filtr τ 0,1 s, gain i w_max — omija SNN (źródło „classical:”)
Dodatkowo (eksploracyjnie): delay_k — opóźnienie klatek o k taktów (DelayLine) dla snn.

Ziarna: --seeds; zakresy 0–39 i 300–399 odrzucane. Stage 1: hashe manifestu sprawdzane przed i po — niezgodność = przerwanie.
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time
from contextlib import nullcontext

import numpy as np

if __name__ == "__main__" and not sys.flags.dont_write_bytecode:
    sys.exit("uruchom z python -B")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from alif import ALIF, ALIFParams  # noqa: E402
from decoder import SteerDecoder, SteerParams  # noqa: E402
from encoder import EncoderParams, TargetEncoder  # noqa: E402
from latency import DelayLine, StageTimer, env_info  # noqa: E402
from safety import Command, Limits, SafetyLayer, ranges_from_mjcf  # noqa: E402
from sensory import Frame, SensoryGate, spot_clip  # noqa: E402
from so101 import UPSTREAM, SceneCfg, SimError, SO101Sim, integrate_pan  # noqa: E402
from visual_path import network, shuffle  # noqa: E402

FORBIDDEN = set(range(0, 40)) | set(range(300, 400))
MANIFEST = os.path.join(ROOT, "bio2", "results", "cx_causal_phase2_20261027_174754", "frozen_manifest_v4.json")
Q_POSE = np.array([0.0, -0.4, 1.0, 0.0, 1.571, 0.5])
P = ALIFParams(noise=2.0)
J0 = 0.2                                # z reguły V4 v2 (część A v1), nie strojone na pętli
ENC = EncoderParams(blur_px=3)          # V4 v2
STEER = SteerParams(tau_s=(0.10,), gain=2.5, w_max=1.0)
TICKS, DT = 300, 0.01
CONDS = ("snn", "snn_shuffle", "snn_swap", "no_vision", "classical_p")


def stage1_hashes():
    m = json.load(open(MANIFEST))
    files = dict(m["deps_sha256"], **{m[k]: m[k + "_sha256"] for k in ("runner", "analysis", "analysis_selftest",
                                                                         "runner_safety_test")})
    bad = [p for p, h in files.items() if hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest() != h]
    return dict(n=len(files), mismatched=bad, manifest_sha256=hashlib.sha256(open(MANIFEST, "rb").read()).hexdigest())


def trial_spec(seed):
    rng = np.random.default_rng(seed)
    return dict(seed=seed, az0_deg=float(rng.choice([-1, 1]) * rng.uniform(10, 30)), rho=float(rng.uniform(0.16, 0.24)))


def bearing(sim, q):
    """Namiar piłeczki [rad, + w lewo] względem poziomego rzutu osi kamery (prawda symulatora, tylko ocena)."""
    k = sim.fk(q)
    b = sim.d.qpos[sim.m.joint("ball").qposadr[0]:][:3]
    f = k["eye_forward"]
    v = b[:2] - k["eye"][:2]
    return math.atan2(f[0] * v[1] - f[1] * v[0], f[0] * v[0] + f[1] * v[1])


def place_ball(sim, az0, rho):
    k = sim.fk(Q_POSE)
    psi = math.atan2(k["eye_forward"][1], k["eye_forward"][0]) + az0
    return (k["eye"][0] + rho * math.cos(psi), k["eye"][1] + rho * math.sin(psi), sim.cfg.ball_r)


def calibrate_p(shape):
    """Kalibracja regulatora P na bodźcach syntetycznych V4 (azymuty −30…30° co 10°), offset 0 (pusty obraz)."""
    enc = TargetEncoder(shape, ENC)
    az = np.arange(-30, 31, 10)
    imgs = spot_clip(np.radians(az), np.zeros(len(az)), shape, 70.0, 9, (40, 180, 50), (120, 120, 120)).images
    d = np.array([enc.encode(im)["g"] @ [1, -1] for im in imgs])
    x = np.radians(az)
    return float((d * x).sum() / (x * x).sum())


def run_trial(cond, seed, base, calib, delay_k=0, timer=None, max_age=0.05, tr=None, slope=None, cfg=None, distractor=None):
    """tr/slope/cfg/distractor: rozszerzenia V5 v2 (loop_v2.py); domyślne None = zachowanie zamrożone V5 v1."""
    spec, idx = base
    if cond == "snn_shuffle":
        spec = shuffle(spec, seed + 100_000)
    sim = SO101Sim(cfg) if cfg else SO101Sim()
    try:
        tr = tr or trial_spec(seed)
        sim.reset(Q_POSE, ball_pos=place_ball(sim, math.radians(tr["az0_deg"]), tr["rho"]),
                  distractor_pos=distractor)
        H, W = sim.cfg.cam_shape
        gate = SensoryGate((H, W), period=DT, max_age=max_age, reset_after=max(0.1, max_age))
        enc = TargetEncoder((H, W), ENC)
        net = ALIF(spec, P, seed)
        inL, inR = (idx["in_R"], idx["in_L"]) if cond == "snn_swap" else (idx["in_L"], idx["in_R"])
        dec = SteerDecoder({"DNa02_L": idx["DNa02_L"], "DNa02_R": idx["DNa02_R"]}, ("DNa02",), [0.0], [slope or calib["slope_snn"]], STEER)
        p_f = 0.0
        safety = SafetyLayer(Limits(ranges=ranges_from_mjcf(UPSTREAM), max_sensor_age=max_age))
        delay = DelayLine(delay_k, None)
        pan_t, e, om, flags, src = 0.0, [], [], {}, "classical:P_encoder" if cond == "classical_p" else "snn:DNa02"
        for k in range(TICKS):
            st = timer.stage if timer else (lambda _n: nullcontext())
            e.append(bearing(sim, sim.d.qpos[sim.qadr].copy()))     # ocena — poza pomiarem czasu
            if timer:
                timer.begin()
            with st("observe"):
                obs = sim.observe()
            f = obs.frame if cond != "no_vision" else Frame(obs.frame.seq, obs.frame.t_capture, obs.frame.t_receive, None,
                                                            obs.frame.proprio, "sim:blank")
            f = delay.push(f)
            if f is None:
                s_usable, age, img = False, 0.0, None
            else:
                smp = gate.push(f, now=obs.t)
                s_usable, age, img = smp.usable, smp.age, f.image if smp.usable else None
            with st("encoder"):
                g = enc.encode(img)["g"]
            if cond == "classical_p":
                a = math.exp(-DT / STEER.tau_s[0])
                p_f = a * p_f + (1 - a) * float(g @ [1, -1])
                omega = float(np.clip(STEER.gain * p_f / calib["slope_p"], -STEER.w_max, STEER.w_max))
                net_spk = None
            else:
                I = enc.currents(g, inL, inR, len(spec.bodies))
                with st("snn"):
                    net_spk = net.run(I, 10)
                with st("decoder"):
                    omega = dec.step(net_spk, 1.0)["omega"]
            pan_t = integrate_pan(pan_t, omega, DT)
            cmd = Command(obs.t, {0: pan_t, **{j: Q_POSE[j] for j in range(1, 5)}}, None,
                          {0: src, **{j: "script:hold_pose" for j in range(1, 5)}})
            with st("safety"):
                qt, tau, fl, per = safety.step(cmd, obs.q, now=obs.t, sensor_age=age)
            pan_t = qt[0]                                   # integracja od celu po ograniczeniach (bez wind-up)
            for x in list(fl) + [y for v in per.values() for y in v]:
                flags[x] = flags.get(x, 0) + 1
            with st("act+physics"):
                sim.act(qt, tau)
                sim.step()
            om.append(omega)
            if timer:
                timer.end()
        e = np.degrees(np.array(e))
        return dict(cond=cond, delay_k=delay_k, **tr, e_deg=e.round(3).tolist(), omega=np.round(om, 4).tolist(),
                    safety_flags=flags, safety_per_source=safety.stats["per_source"], gate=gate.stats,
                    sim_stats={k: v for k, v in sim.stats.items() if k != "released"})
    finally:
        sim.close()


def metrics(r, tol=5.0, hold_s=0.5):
    e = np.array(r["e_deg"])
    n_hold = int(hold_s / DT)
    inside = np.abs(e) < tol
    t_in = int(np.argmax(inside)) * DT if inside.any() else None
    s0 = math.copysign(1, r["az0_deg"])
    return dict(success=bool(inside[-n_hold:].all()), final_abs_err=float(abs(e[-n_hold:]).mean()),
                t_first_within=t_in, overshoot_deg=float(max(0.0, (-s0 * e).max())),
                safety_ticks_flagged=int(sum(r["safety_flags"].values())))


def _allowed(out):
    roots = [os.path.realpath(HERE)] + ([os.path.realpath(os.environ["TMPDIR"])] if os.environ.get("TMPDIR") else [])
    p = os.path.realpath(out)
    return os.path.isdir(p) and any(p == r or p.startswith(r + os.sep) for r in roots)


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--conds", default=",".join(CONDS))
    ap.add_argument("--seeds", required=True, help="a-b (włącznie)")
    ap.add_argument("--delays", default="0", help="opóźnienia klatek [takty] dla snn, np. 0,5,10")
    ap.add_argument("--calib", required=True, help="plik JSON wyników V4 v2 (slope SNN)")
    ap.add_argument("--label", required=True)
    ap.add_argument("--max-age", type=float, default=0.05, help="[s] klatka starsza = nieaktualna (bramka i bezpieczeństwo); zamrożone V5: 0,05")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    lo, hi = map(int, a.seeds.split("-"))
    seeds = list(range(lo, hi + 1))
    conds = a.conds.split(",")
    if set(seeds) & FORBIDDEN or set(conds) - set(CONDS) or not _allowed(a.out):
        sys.exit("odmowa: ziarna z zakresu 0–39/300–399, nieznany warunek albo --out poza flymind/ i $TMPDIR")
    pre = stage1_hashes()
    if pre["mismatched"]:
        sys.exit(f"Stage 1 niezgodny PRZED przebiegiem: {pre['mismatched']}")
    v4 = json.load(open(a.calib))
    if v4.get("version") != 2 or v4["J0"] != J0 or v4["calib"]["offset"] != 0.0:
        sys.exit("--calib: oczekiwano wyników V4 v2 z J0 = 0,2 i offsetem 0")
    if v4["calib"].get("refused") or not v4["calib"]["slope_hz_per_rad"] > 0:
        sys.exit("--calib: kalibracja odrzucona albo slope ≤ 0 (znak ustalony z góry)")
    calib = dict(slope_snn=v4["calib"]["slope_hz_per_rad"], slope_p=calibrate_p(SceneCfg().cam_shape), calib_file=a.calib)
    spec, idx, rep = network(J0)
    t0 = time.perf_counter()
    timer = StageTimer(warmup=0)
    runs = []
    for c in conds:
        for dk in ([int(x) for x in a.delays.split(",")] if c in ("snn", "classical_p") else [0]):
            for s in seeds:
                try:
                    r = run_trial(c, s, (spec, idx), calib, dk, timer if (c == "snn" and dk == 0) else None, a.max_age)
                    r.update(metrics(r))
                except SimError as err:                 # protokół: porażka, raportowana osobno
                    r = dict(cond=c, delay_k=dk, **trial_spec(s), error=str(err), success=False, final_abs_err=float("nan"),
                             t_first_within=None, overshoot_deg=float("nan"), safety_ticks_flagged=0, safety_flags={},
                             e_deg=[float("nan")])
                runs.append(r)
                print(f"{c:12s} d{dk:<2d} seed {s}: az0 {r['az0_deg']:+6.1f}° → final |e| {r['final_abs_err']:5.2f}° "
                      f"success {r['success']} t_in {r['t_first_within']} overshoot {r['overshoot_deg']:.1f}° flags {r['safety_flags']}",
                      flush=True)
    post = stage1_hashes()
    res = dict(label=a.label, argv=sys.argv, max_age=a.max_age, conds=conds, seeds=[lo, hi], calib=calib, network=rep, J0=J0,
               encoder=ENC.__dict__, steer=STEER.__dict__, q_pose=Q_POSE.tolist(), stage1_pre=pre, stage1_post=post,
               env=env_info(), wall_s=time.perf_counter() - t0, loop_timing_snn=timer.report(), runs=runs,
               code_sha256={f: hashlib.sha256(open(os.path.join(HERE, f), "rb").read()).hexdigest()
                            for f in ("loop.py", "encoder.py", "visual_path.py", "alif.py", "decoder.py", "safety.py",
                                      "so101.py", "sensory.py", "snn_interface.py", "connectome.py")})
    path = os.path.join(a.out, f"v5_{a.label}_{time.strftime('%Y%m%dT%H%M%S')}.json")
    with open(path, "x") as f:
        json.dump(res, f, ensure_ascii=False, default=str)
    print("zapisano:", path, "| Stage 1 po:", "OK" if not post["mismatched"] else post["mismatched"])
    return res


if __name__ == "__main__":
    main()
