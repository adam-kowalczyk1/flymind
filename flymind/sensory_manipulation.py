"""flymind/sensory_manipulation.py — etap „czucie i manipulacja”: szczęką SO-101 steruje obwód nogi muchy (MaleCNS, T2 L)
w benchmarku różnych przedmiotów (scena, kolejka i ewaluator z object_handling.py — importowane, bez zmian).

CO TU DECYDUJE SIEĆ, A CO NIE (uczciwy podział; opis: SENSORY_MANIPULATION_STAGE.md):
  sieć (źródło "snn:…")        kiedy zacisnąć szczękę (po dotyku), jak mocno (moment ciągły), czy chwyt „jest” (bramka
                               podniesienia) i czy trwa (przerwanie transportu, gdy sieć przestaje zaciskać).
  rusztowanie klasyczne        trajektorie ramienia (IK), dosuw boczny do dotyku, otwarcie szczęki przed chwytem i nad
  ("classical:…")              pudełkiem (sieć NIE ma sygnału puszczenia — NOT IMPLEMENTED), harmonogram faz.
  percept                      wyrocznia z symulatora (prostokąt z góry), NIE kamera — wzrok sieci nie jest tu włączony.

Wejścia sieci są wyłącznie czuciowe: dotyk padów → receptory szczecinkowe; (wariant C) kąt i prędkość szczęki → FeCO.
Neuronów ruchowych nie pobudza się sztucznie. Mapowanie wyjścia (prostownik goleni → zaciskanie) to ANALOGIA z FJ1.

Uruchom (z katalogu tymczasowego):
  .venv/bin/python -I -B flymind/sensory_manipulation.py --arm B_fly --tag B_fly_glu-1_v1
"""
import argparse
import json
import os
import resource
import sys
import time
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import object_handling as oh  # noqa: E402
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402
from fly_jaw import FlyJaw, FlyJawCfg  # noqa: E402
from leg_circuit import network, select  # noqa: E402
from pick_place import Fail  # noqa: E402
from reach import ReachError, _kin, plan  # noqa: E402
from safety import Command  # noqa: E402
from snn_interface import DEFAULT_SIGN  # noqa: E402
from visual_path import ANN, shuffle  # noqa: E402

OUT = os.path.join(oh.ROOT, "flymind", "results", "sensory_manipulation")
# FeCO z adnotacji MaleCNS (synonyms „FeCO claw/hook”) + reguła Lee i in. 2024; przypisanie flex/ext: INFERRED (raport
# danych 2026-11-05). Zamykanie szczęki ≙ prostowanie goleni (mapowanie FJ1), więc: szczęka domknięta → claw-EXT,
# rozwarta → claw-FLEX, ruch zamykania → hook-EXT, otwierania → hook-FLEX. Club (drgania) pominięty: 0 % wejścia do MN.
FECO = dict(claw_ext="SNpp51", claw_flex="SNpp50", hook_ext="SNpp39", hook_flex="SNpp41")
ARMS = {  # nazwa: (źródło komendy szczęki, opis)
    "D_reflex": ("classical:reflex", "trywialny odruch: dotyk > 0,2 N → 0,5 N·m (punkt odniesienia)"),
    "N_null": ("classical:null", "moment 0 (kontrola zerowa)"),
    "B_fly": ("snn:legT2L", "istniejący FlyJaw: dotyk → szczecinki → obwód nogi z danych"),
    "C_fly_feco": ("snn:legT2L+FeCO", "B + propriocepcja: kąt/prędkość szczęki → FeCO claw/hook"),
    "C_no_touch": ("snn:legT2L+FeCO", "ablacja: sama propriocepcja, dotyk odcięty"),
    "S_shuffle": ("snn:legT2L_shuffled", "kontrola: ten sam obwód przetasowany z zachowaniem stopni i wag (wymaga --shuffle-seed)"),
}


@dataclass(frozen=True)
class FlyCfg:
    glu_sign: float = -1.0
    trigger: str = "push"          # co doprowadza do pierwszego dotyku (rusztowanie, to samo dla wszystkich ramion):
                                   #   "push"   dosuw boczny stałego padu jak w FJ1 (siła = tarcie przedmiotu o blat)
                                   #   "search" słaby moment zamykający „szukania” do chwili, gdy sterownik sam zaciska
    tau_search: float = 0.30       # N·m. Zmierzone: staw szczęki ma tłumienie 0,6 N·m·s/rad i tarcie 0,052 N·m, więc przy
                                   # 0,1 N·m zamyka się 0,08 rad/s (5–15 s do dotyku), przy 0,3 N·m — 0,42 rad/s.
                                   # Po przejęciu przez sterownik moment szukania znika: trzymać musi sam sterownik.
    search_max: float = 4.0        # s (pełny zakres 1,5 rad przy 0,42 rad/s)
    push: float = 0.004            # m dosuwu stałego padu ZA ścianę przedmiotu (FJ1: GAP 4 + 4 mm)
    v_side: float = 0.02           # rad/s dosuwu (FJ1, zamrożone z pilota: szybciej = przedmiot ucieka)
    tau_engage: float = 0.10       # N·m: sieć „zaciska”, gdy jej moment ≥ tyle …
    engage_ticks: int = 10         # … przez tyle taktów z rzędu (0,1 s)
    loss_ticks: int = 5            # tyle taktów poniżej progu w transporcie = sieć puściła
    hold_max: float = 1.5          # s czekania na zaciśnięcie po dosuwie (FJ1: 150 taktów)
    # propriocepcja [MODEL]: liniowe kodowanie, ten sam prąd maksymalny co dotyk (40 mV); wartości nie były strojone
    q_mid: float = 0.80            # rad: środek zakresu szczęki (−0,12…1,70)
    q_span: float = 0.90           # rad do nasycenia claw
    qd_ref: float = 1.0            # rad/s do nasycenia hook
    feco_mV: float = 40.0


class Reflex:
    def step(self, touch, q, qd):
        return 0.5 if max(touch[0], touch[1]) > 0.2 else 0.0

    def reset(self):
        pass


class Null(Reflex):
    def step(self, touch, q, qd):
        return 0.0


class LegJaw:
    """Obwód nogi T2 L jako sterownik szczęki. touch/proprio włączają kanały czuciowe; spec = przetasowana kontrola."""

    def __init__(self, fc=FlyCfg(), touch=True, proprio=False, shuffle_seed=None):
        self.fc, self.use_touch, self.use_proprio = fc, touch, proprio
        cfg, spec = FlyJawCfg(glu_sign=fc.glu_sign), None
        if shuffle_seed is not None:                               # jak ramię C w FJ1: tasowanie zachowuje stopnie i wagi
            base, _, _ = network(cfg.J0, cfg.leg, cfg.side, sign_map={**DEFAULT_SIGN, "glutamate": cfg.glu_sign})
            spec = shuffle(base, shuffle_seed, equal_weight=True)
        fj = FlyJaw(cfg, spec)
        self.c, self.spec = fj.cfg, fj.net.W
        self.pad_in, self.press, self.release, self.N = fj.pad_in, fj.press, fj.release, fj.N
        bodies, groups, _ = select(self.c.leg, self.c.side)
        ty = pd.read_feather(ANN, columns=["bodyId", "type"]).set_index("bodyId").type
        sens = [b for v in groups["sensory"].values() for b in v]
        pos = {b: i for i, b in enumerate(bodies)}
        self.feco = {k: [pos[b] for b in sens if ty.get(b) == t] for k, t in FECO.items()}
        if proprio and not all(self.feco.values()):
            raise ValueError(f"brak receptorów FeCO w obwodzie: { {k: len(v) for k, v in self.feco.items()} }")
        self.sizes = dict(N=self.N, bristle=sum(map(len, self.pad_in)), press_MN=len(self.press),
                          release_MN=len(self.release), **{k: len(v) for k, v in self.feco.items()})
        self.t = np.zeros(3)
        self.reset()

    def reset(self):
        self.net = SparseALIF(_W(self.spec), ALIFParams(), None)   # szum 0
        self.r_press = self.r_release = 0.0

    def step(self, touch, q, qd, dt=0.01):
        c, f = self.c, self.fc
        t0 = time.perf_counter()
        X = np.zeros(self.N)
        if self.use_touch:
            for ix, x in zip(self.pad_in, touch[:2]):
                X[ix] = min(c.max_mV, c.gain_mV_per_N * max(0.0, float(x)))
        if self.use_proprio:
            X[self.feco["claw_ext"]] = f.feco_mV * min(1.0, max(0.0, (f.q_mid - q) / f.q_span))
            X[self.feco["claw_flex"]] = f.feco_mV * min(1.0, max(0.0, (q - f.q_mid) / f.q_span))
            X[self.feco["hook_ext"]] = f.feco_mV * min(1.0, max(0.0, -qd / f.qd_ref))
            X[self.feco["hook_flex"]] = f.feco_mV * min(1.0, max(0.0, qd / f.qd_ref))
        t1 = time.perf_counter()
        s = self.net.run(X, c.steps)
        t2 = time.perf_counter()
        a = dt / c.rate_tau
        self.r_press += a * (s[:, self.press].mean() * 1000 - self.r_press)
        self.r_release += a * (s[:, self.release].mean() * 1000 - self.r_release)
        tau = c.k * (self.r_press - self.r_release)
        self.t[:] = t1 - t0, t2 - t1, time.perf_counter() - t2
        return tau


class _W:
    def __init__(self, W):
        self.W = W


class FlyGrip(oh.Controller):
    """Kontroler z object_handling, w którym o szczęce w chwycie i transporcie decyduje `driver` (sieć albo kontrola)."""

    def __init__(self, world, cfg, driver, src, fc):
        super().__init__(world, cfg)
        self.driver, self.src, self.fc = driver, src, fc
        self.tau_fly, self.eng, self.low = 0.0, 0, 0
        self.lat, self.react = [], []
        self._touch_t = self._close_t = None

    def tick(self, tgt, mode):
        o, g = self.obs, self.grip
        w0 = time.perf_counter()
        self.tau_fly = float(self.driver.step(o.touch, float(o.q[5]), float(o.qd[5])))   # czucie → sieć w KAŻDYM takcie
        w1 = time.perf_counter()
        on = self.tau_fly >= self.fc.tau_engage
        self.eng, self.low = (self.eng + 1, 0) if on else (0, self.low + 1)
        if mode in ("fly", "search"):                              # czas: pierwszy dotyk → pierwsza komenda zaciskania sterownika
            if self._touch_t is None and max(o.touch[:2]) > 0.05:
                self._touch_t = o.t
            if self._touch_t is not None and self._close_t is None and self.tau_fly > 0.05:
                self._close_t = o.t
                self.react.append(round((o.t - self._touch_t) * 1e3, 1))
        if mode == "fly":
            tau, src = self.tau_fly, self.src
        elif mode == "search":                                     # rusztowanie: słabe domykanie aż do dotyku
            tau, src = self.fc.tau_search, "classical:search"
        else:                                                      # rusztowanie: szczęka otwierana klasycznie
            g.mode, src = "open", "classical:open"
            tau = g.cfg.tau_open if o.q[5] < g.cfg.q_open else \
                g.cfg.tau_close if mode == "preshape" and o.q[5] > g.cfg.q_open + 0.05 else 0.0
        cmd = Command(o.t, {j: float(tgt[j]) for j in range(5)}, tau, {**{j: "classical:reach" for j in range(5)}, "jaw": src})
        q_t, tau_t, flags, per = self.safety.step(cmd, o.q, o.t, 0.0)
        if flags:
            raise Fail("safety_" + flags[0], str(flags))
        for f in {x for v in per.values() for x in v}:
            self.stats["flags"][f] = self.stats["flags"].get(f, 0) + 1
        w2 = time.perf_counter()
        self.lat.append((*getattr(self.driver, "t", (0, w1 - w0, 0)), w2 - w1))   # kodowanie, sieć, dekodowanie, komenda
        self.obs = self.w.step(q_t, tau_t)

    def plan(self, p):
        P, sim, r = super().plan(p), self.sim, self.rcfg
        if self.fc.trigger != "push":
            return {**P, "side": []}
        cs = lambda q: _kin(sim, q).site("cs_fixed").xpos.copy()  # noqa: E731
        try:                                                        # dosuw stałego padu do przedmiotu i dalej o `push`
            q_g = P["descend"][-1]
            n = oh.jaw_dir(_kin(sim, q_g))
            P["side"] = plan(sim, q_g, cs(q_g) - n * (self.cfg.gap + self.fc.push), point="cs_fixed", jaw_open=P["q_pre"], cfg=r)
            drop = cs(P["transport"][-1])
            P["lift"] = plan(sim, P["side"][-1], cs(P["side"][-1]) + [0, 0, P["z_carry"] - P["z_grasp"]], point="cs_fixed", cfg=r)
            P["transport"] = plan(sim, P["lift"][-1], drop, point="cs_fixed", cfg=r)
        except ReachError as e:
            raise Fail("unreachable", str(e)) from e
        return P

    def gripping(self):
        if self.low >= self.fc.loss_ticks:
            raise Fail("snn_released", f"moment sterownika {self.tau_fly:.2f} N·m < {self.fc.tau_engage}")

    def attempt(self, p):
        c, w, fc = self.cfg, self.w, self.fc
        rec = dict(percept=p, t_sim={}, t_wall={}, ok=False, reason=None, lifted=False)
        t0, clock = self.obs.t, [self.obs.t, time.perf_counter()]
        self._touch_t = self._close_t = None

        def mark(ph):
            rec["t_sim"][ph] = self.obs.t - clock[0]
            rec["t_wall"][ph] = time.perf_counter() - clock[1]
            clock[:] = [self.obs.t, time.perf_counter()]

        try:
            w.phase = "plan"
            P = self.plan(p)
            rec.update(plan_wall=time.perf_counter() - clock[1], q_pre=P["q_pre"], z_grasp=P["z_grasp"], drop=P["drop"])
            clock[1] = time.perf_counter()
            self.grip = oh.ClassicGrip(oh.GripCfg(q_open=P["q_pre"]))
            w.phase = "approach"
            self.follow(P["move"], "preshape")
            if not self.wait(c.open_max, np.asarray(P["move"][-1])[:5], "preshape",
                             until=lambda: self.obs.q[5] >= P["q_pre"] - c.jaw_tol):
                raise Fail("jaw_not_open", f"q szczęki {self.obs.q[5]:.2f}, cel {P['q_pre']:.2f}")
            self.follow(P["descend"], "open")
            mark("approach")
            w.phase = "grasp"                                       # od teraz o szczęce decyduje sterownik (sieć)
            for x in oh.profile(P["side"], self.obs.q, fc.v_side, c.a_max, self.lim.dt) if P["side"] else []:
                self.tick(x, "fly")
            tgt = np.asarray((P["side"] or P["descend"])[-1])[:5]
            if not self.wait(*((fc.hold_max, tgt, "fly") if P["side"] else (fc.search_max, tgt, "search")),
                             until=lambda: self.eng >= fc.engage_ticks):
                raise Fail("no_engage", f"moment sterownika {self.tau_fly:.2f} N·m, touch {np.round(self.obs.touch, 2).tolist()}")
            rec["tau_engage"], rec["q_jaw_grasp"] = round(self.tau_fly, 3), round(float(self.obs.q[5]), 3)
            mark("grasp")
            w.phase = "lift"
            self.follow(P["lift"], "fly", self.gripping)
            rec["lifted"] = True
            mark("lift")
            w.phase = "transport"
            self.follow(P["transport"], "fly", self.gripping)
            rec["tau_carry"] = round(self.tau_fly, 3)
            mark("transport")
            w.phase = "place"                                       # puszczenie: rusztowanie (sieć nie ma sygnału otwarcia)
            tgt = np.asarray(P["transport"][-1])[:5]
            self.n_drop = P["drop"] + 1
            q_rel = min(self.obs.q[5] + c.jaw_release, P["q_pre"] - c.jaw_tol)
            if not self.wait(c.open_max, tgt, "open", until=lambda: max(self.obs.touch[:2]) < self.grip.cfg.f_contact
                             and self.obs.q[5] >= q_rel):
                raise Fail("release_failed", f"touch {np.round(self.obs.touch, 2).tolist()}, q szczęki {self.obs.q[5]:.2f}")
            mark("place")
            w.phase = "return"
            if P["retreat"]:
                self.follow(P["retreat"], "open")
            self.follow(P["home"], "open")
            mark("return")
            rec["ok"] = True
        except Fail as e:
            rec.update(reason=e.reason, detail=e.detail, fail_phase=w.phase, t_to_fail_sim=self.obs.t - t0)
            rec["recover"] = self.recover()
            if rec["recover"] is not True:
                self.stop = f"recover: {rec['recover']}"
        w.phase = "idle"
        rec["op_sim"] = self.obs.t - t0
        return rec


def make_driver(arm, fc, shuffle_seed=None):
    if arm == "D_reflex":
        return Reflex()
    if arm == "N_null":
        return Null()
    if arm == "S_shuffle" and shuffle_seed is None:
        raise SystemExit("S_shuffle wymaga --shuffle-seed")
    return LegJaw(fc, touch=arm != "C_no_touch", proprio=arm.startswith("C_"),
                  shuffle_seed=shuffle_seed if arm == "S_shuffle" else None)


def run_trial(item, seed, driver, src, fc):
    """Jedna próba: świeża scena z jednym przedmiotem, ten sam przebieg co object_handling.run, inny sterownik szczęki."""
    made, orig = [], oh.Controller
    driver.reset()
    oh.Controller = lambda world, cfg: made.append(FlyGrip(world, cfg, driver, src, fc)) or made[0]
    try:
        r = oh.run([item], seed)
    finally:
        oh.Controller = orig
    r["lat"], r["react_ms"] = np.array(made[0].lat), made[0].react
    return r


def pct(a):
    return dict(median=round(float(np.median(a)), 4), p95=round(float(np.percentile(a, 95)), 4),
                p99=round(float(np.percentile(a, 99)), 4), max=round(float(a.max()), 4), n=int(len(a)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=sorted(ARMS))
    ap.add_argument("--glu", type=float, default=-1.0)
    ap.add_argument("--trigger", default="push", choices=("push", "search"))
    ap.add_argument("--shuffle-seed", type=int)
    ap.add_argument("--set", default="base", choices=sorted(oh.SETS))
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--poses", type=int, default=3)
    ap.add_argument("--seed", type=int, default=100, help="ziarno położeń — domyślnie to samo co B_base bazy klasycznej")
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, a.tag + ".json")
    if os.path.exists(path) or os.path.exists(path.replace(".json", ".INCOMPLETE.json")):
        sys.exit(f"istnieje już wynik o tagu {a.tag!r} w {OUT} — wybierz inny --tag")
    fc, src = FlyCfg(glu_sign=a.glu, trigger=a.trigger), ARMS[a.arm][0]
    w0, c0 = time.perf_counter(), time.process_time()
    driver = make_driver(a.arm, fc, a.shuffle_seed)
    build_s, items, runs, lat, react = time.perf_counter() - w0, oh.SETS[a.set], [], [], []
    for it in [x for x in items if not a.only or "/".join(x) in a.only]:
        for k in range(a.poses):
            r = run_trial(it, a.seed * 1000 + items.index(it) * 10 + k, driver, src, fc)
            lat.append(r.pop("lat"))
            react += r["react_ms"]
            runs.append(r)
            o = r["objects"][0]
            print(f"{'/'.join(it):22s} poza {k}: {'OK ' if o['success'] else '-- '}"
                  f"{''.join('GLTRP'[j] if o['truth'][s] else '.' for j, s in enumerate(oh.STAGES))} "
                  f"próby {o['attempts']} {[x['reason'] for x in o['attempt_log'] if not x['ok']]} → {o['final']}", flush=True)
    L = np.vstack(lat) * 1e3                                        # ms, czas ZEGAROWY komputera na takt
    wall, cpu = time.perf_counter() - w0, time.process_time() - c0
    summ = oh.summarize(runs)
    summ["compute_ms_per_tick"] = dict(sensory_encoding=pct(L[:, 0]), snn_10_steps=pct(L[:, 1]), decoding=pct(L[:, 2]),
                                       safety_and_command=pct(L[:, 3]), sensor_to_command_total=pct(L.sum(1)))
    summ["contact_to_close_command_sim_ms"] = pct(np.array(react)) if react else None
    summ["process"] = dict(wall_s=round(wall, 1), cpu_s=round(cpu, 1), cpu_load=round(cpu / wall, 2),
                           max_rss_MB=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20, 1),
                           driver_build_s=round(build_s, 2), ticks=int(len(L)), sim_tick_ms=10.0, gpu="nieużywany")
    complete = all(r["complete"] for r in runs)
    out = dict(tag=a.tag, arm=a.arm, arm_desc=ARMS[a.arm][1], jaw_source=src, shuffle_seed=a.shuffle_seed, complete=complete,
               argv=sys.argv, fly_cfg=asdict(fc), fly_jaw_cfg=asdict(FlyJawCfg(glu_sign=a.glu)), feco_types=FECO,
               network=getattr(driver, "sizes", None), cfg=asdict(oh.OHCfg()), scene=asdict(oh.Scene()),
               crit=asdict(oh.Crit()), code=oh.code_state(), python=sys.version.split()[0], summary=summ, runs=runs)
    with open(path if complete else path.replace(".json", ".INCOMPLETE.json"), "x") as f:
        json.dump(out, f, indent=1, default=float)
    print(json.dumps({k: v for k, v in summ.items() if not k.startswith("by_")}, indent=1, ensure_ascii=False))
    print("zapisano" if complete else "NIEKOMPLETNE — zapisano", path)


if __name__ == "__main__":
    main()
