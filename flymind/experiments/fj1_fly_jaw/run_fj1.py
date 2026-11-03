"""FJ1 — test potwierdzający: szczęka SO-101 sterowana obwodem dotykowym nogi muchy (protokół: PROTOCOL.md).

Ramiona: A (obwód z danych, Glu −1 i Glu +1), C (ten sam obwód przetasowany z zachowaniem stopni i wag, 10 instancji
na znak Glu), D (trywialny odruch klasyczny: dotyk > próg → moment zamykający), N (moment 0 po dotyku; po red teamie r1). Ramię SO-101 sięga klasycznie
(rusztowanie, źródło "classical:reach"); badane jest WYŁĄCZNIE sterowanie szczęką.
Bez szumu ALIF; jedynym losowaniem jest tasowanie w ramieniu C (ziarna 9 201 001–9 201 020; smoke 9 208 001–002;
SEED_REGISTRY.md).

  --feasibility   tylko IK/planer dla siatki (bez fizyki i bez szczęki): które pozycje są osiągalne
  --smoke         jedna próba każdego typu ramienia w pozycji z pilota (poza siatką), nic nie analizuje
  --run           pełny test → results/fj1_trials.jsonl + manifest
Uruchom z katalogu repozytorium:  .venv/bin/python -I -B flymind/experiments/fj1_fly_jaw/run_fj1.py --run
"""
import hashlib
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FLY = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, FLY)
from fly_jaw import FlyJaw, FlyJawCfg  # noqa: E402
from leg_circuit import network  # noqa: E402
from reach import ReachCfg, ReachError, fixed_pad_target, ik, plan, plan_joint, ticks  # noqa: E402
from safety import Command, Limits, SafetyLayer, ranges_from_mjcf  # noqa: E402
from snn_interface import DEFAULT_SIGN  # noqa: E402
from so101 import UPSTREAM, SO101Sim  # noqa: E402
from visual_path import shuffle  # noqa: E402

Q0 = np.array([0, -0.4, 1.0, 0, 1.571, 0.93])
GRID = [(rho, az) for rho in (0.17, 0.20, 0.23) for az in (-25.0, -10.0, 10.0, 25.0)]   # m, stopnie (+ w lewo = +y)
SMOKE_BALL = (0.25, 0.03)
GAP, SIDE_STEP, V_SIDE = 0.004, 0.008, 0.02         # zamrożone z pilota: m, m, rad/s
HOLD_TICKS, LIFT, LIFT_SETTLE = 150, 0.06, 60
SEEDS = {-1.0: range(9_201_001, 9_201_011), 1.0: range(9_201_011, 9_201_021)}
REFLEX_TAU, REFLEX_F = 0.5, 0.2                     # ramię D: N·m, N (jak grip.GripCfg.tau_close / f_contact)
CODE = ["fly_jaw.py", "leg_circuit.py", "alif_sparse.py", "alif.py", "reach.py", "safety.py", "so101.py", "sensory.py",
        "snn_interface.py", "visual_path.py", "connectome.py", "experiments/fj1_fly_jaw/run_fj1.py",
        "experiments/fj1_fly_jaw/analyze_fj1.py", "experiments/fj1_fly_jaw/PROTOCOL.md",
        "experiments/fj1_fly_jaw/SEED_REGISTRY.md", "../assets/so101_upstream.xml",
        "../data/malecns/body-annotations-male-cns-v1.0-minconf-0.5.feather",
        "../data/malecns/body-neurotransmitters-male-cns-v1.0.feather",
        "../data/malecns/connectome-weights-male-cns-v1.0-minconf-0.5.feather"]


def ball_xyz(rho, az_deg, r=0.025):
    a = math.radians(az_deg)
    return np.array([rho * math.cos(a), rho * math.sin(a), r])


def table_contacts(sim):
    g = np.asarray(sim.d.contact.geom).reshape(-1, 2)[:sim.d.ncon]
    names = [(sim.m.geom(int(a)).name, sim.m.geom(int(b)).name) for a, b in g]
    return sorted({b if a == "table" else a for a, b in names if "table" in (a, b)} - {"ball"})


def approach(sim, ball):
    """Plan rusztowania: nad piłeczką → w dół obok niej → powolny dosuw boczny do dotyku. ReachError = nieosiągalne."""
    qa, *_ = ik(sim, ball + [0, 0, 0.08], Q0)
    tgt = fixed_pad_target(sim, qa, ball, sim.cfg.ball_r, GAP)
    n = tgt - ball - [0, 0, 0.005]
    n[2] = 0.0
    n /= np.linalg.norm(n)
    p1 = plan_joint(sim, Q0, tgt + [0, 0, 0.07], point="cs_fixed", jaw_open=Q0[5])
    p2 = plan(sim, p1[-1], tgt, point="cs_fixed", jaw_open=Q0[5])
    p3 = plan(sim, p2[-1], tgt - n * SIDE_STEP, point="cs_fixed", jaw_open=Q0[5])
    return p1, p2, p3, tgt - n * SIDE_STEP


class Null:
    """Ramię N (kontrola zerowa, dodana po red teamie r1): po dotyku moment 0 — czy rusztowanie samo chwyta?"""
    def step(self, touch):
        return 0.0


class Reflex:
    """Ramię D: klasyczny odruch bez pamięci — dowolny pad > REFLEX_F → REFLEX_TAU zamykania, inaczej 0."""
    def step(self, touch):
        return REFLEX_TAU if max(touch[0], touch[1]) > REFLEX_F else 0.0


def trial(sim, ball, jaw, src):
    sim.reset(Q0, ball_pos=ball)
    safety = SafetyLayer(Limits(ranges=ranges_from_mjcf(UPSTREAM)))
    obs, hits, close_tick, touch_tick = sim.observe(), set(), None, None
    p1, p2, p3, end = approach(sim, ball)

    def go(targets, jaw_fn, settle):
        nonlocal obs, close_tick, touch_tick
        for tgt in list(targets) + [targets[-1]] * settle:
            tau, s = jaw_fn(obs)
            cmd = Command(obs.t, {j: float(tgt[j]) for j in range(5)}, tau,
                          {**{j: "classical:reach" for j in range(5)}, "jaw": s})
            q_t, tau_t, flags, _ = safety.step(cmd, obs.q, obs.t, 0.0)
            if flags:
                raise RuntimeError(f"safety hold {flags}")
            sim.act(q_t, tau_t)
            sim.step()
            obs = sim.observe()
            hits.update(table_contacts(sim))
            if touch_tick is None and s == src and max(obs.touch[:2]) > 0.05:
                touch_tick = safety.stats["ticks"]
            if close_tick is None and s == src and tau_t > 0.05:
                close_tick = safety.stats["ticks"]

    opener = lambda o: (-0.3 if o.q[5] < 0.9 else 0.0, "classical:open")   # noqa: E731 — rusztowanie: szczęka otwarta
    under = lambda o: (jaw.step(o.touch), src)                               # noqa: E731
    go(ticks(p1, obs.q), opener, 20)
    go(ticks(p2, obs.q), opener, 20)
    go(ticks(p3, obs.q, ReachCfg(v_max=V_SIDE)), under, HOLD_TICKS)
    z0 = float(sim.d.body("ball").xpos[2])
    go(ticks(plan(sim, obs.q, end + [0, 0, LIFT], point="cs_fixed"), obs.q), under, LIFT_SETTLE)
    lift = float(sim.d.body("ball").xpos[2]) - z0
    touch = obs.touch[:2].tolist()
    ok = lift >= 0.04 and min(touch) > REFLEX_F and not hits
    jaw_stats = safety.stats["per_source"].get(src, {})
    return dict(lift_mm=round(lift * 1000, 2), end_touch=[round(x, 3) for x in touch], table_hits=sorted(hits),
                first_touch_tick=touch_tick, first_close_tick=close_tick, end_jaw_q=round(float(obs.q[5]), 4),
                jaw_clips={k: v for k, v in jaw_stats.items() if k != "ticks"},
                sources=sorted(safety.stats["per_source"]), success=bool(ok),
                rates=[round(getattr(jaw, "r_press", float("nan")), 1), round(getattr(jaw, "r_release", float("nan")), 1)])


def arms(smoke=False):
    """(nazwa, glu, seed, fabryka sterownika). Bazowe sieci budowane raz na znak Glu; tasowania raz na ziarno."""
    out = []
    for glu in (-1.0, 1.0):
        cfg = FlyJawCfg(glu_sign=glu)
        base, _, _ = network(cfg.J0, cfg.leg, cfg.side, sign_map={**DEFAULT_SIGN, "glutamate": glu})
        out.append((f"A_glu{glu:+.0f}", glu, None, lambda c=cfg: FlyJaw(c)))
        for sd in ([9_208_001 + (glu > 0)] if smoke else SEEDS[glu]):
            sh = shuffle(base, sd, equal_weight=True)
            out.append((f"C_glu{glu:+.0f}", glu, sd, lambda c=cfg, s=sh: FlyJaw(c, spec=s)))
    out.append(("D_reflex", None, None, Reflex))
    out.append(("N_zero", None, None, Null))
    return out


def sha(p):
    return hashlib.sha256(open(os.path.join(FLY, p), "rb").read()).hexdigest()


def main(argv):
    sim = SO101Sim(render=False)
    if "--feasibility" in argv:
        for rho, az in GRID:
            try:
                approach(sim, ball_xyz(rho, az))
                print(f"  rho {rho} az {az:+.0f}: OK")
            except ReachError as e:
                print(f"  rho {rho} az {az:+.0f}: NIEOSIĄGALNE ({e})")
        return
    grid = [SMOKE_BALL] if "--smoke" in argv else GRID
    todo = arms(smoke="--smoke" in argv)          # smoke: A−1, C−1, A+1, C+1, D; ziarna tasowania z puli smoke
    res_dir = os.path.join(HERE, "results")
    os.makedirs(res_dir, exist_ok=True)
    out = os.path.join(res_dir, "fj1_smoke.jsonl" if "--smoke" in argv else "fj1_trials.jsonl")
    if "--run" not in argv and "--smoke" not in argv:
        sys.exit("podaj --run, --smoke albo --feasibility")
    if os.path.exists(out):
        sys.exit(f"{out} istnieje — nie nadpisuję wyników")
    import mujoco, scipy                       # noqa: E401 — wersje bibliotek do manifestu
    manifest = dict(started=time.strftime("%Y-%m-%dT%H:%M:%S"), argv=argv, code_sha256={p: sha(p) for p in CODE},
                    versions=dict(python=sys.version, numpy=np.__version__, scipy=scipy.__version__, mujoco=mujoco.__version__))
    t0 = time.time()
    with open(out, "w") as f:
        for name, glu, sd, make in todo:
            for pos in grid:
                ball = ball_xyz(*pos) if pos != SMOKE_BALL else np.array([*SMOKE_BALL, 0.025])
                jaw = make()
                src = {"D_reflex": "classical:reflex", "N_zero": "classical:null"}.get(name, "snn:legT2L")
                try:
                    r = dict(arm=name, glu=glu, seed=sd, pos=list(pos), status="ok", **trial(sim, ball, jaw, src))
                except Exception as e:  # noqa: BLE001 — próba przerwana jest danymi; analiza odmówi werdyktu
                    r = dict(arm=name, glu=glu, seed=sd, pos=list(pos), status=f"error: {e!r}", success=False)
                f.write(json.dumps(r) + "\n")
                f.flush()
                print(f"{name:10s} seed {sd} pos {pos}: {r['status']} success {r['success']} lift {r.get('lift_mm')} mm "
                      f"touch {r.get('end_touch')}", flush=True)
    manifest.update(finished=time.strftime("%Y-%m-%dT%H:%M:%S"), seconds=round(time.time() - t0),
                    code_sha256_after={p: sha(p) for p in CODE})
    json.dump(manifest, open(out.replace(".jsonl", "_manifest.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
