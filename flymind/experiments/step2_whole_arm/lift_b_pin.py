"""Krok 2(b): faza podniesienia — staw 1 (shoulder_lift) sterowany siecią muchy T1 L + T2 L. SYMULACJA MuJoCo.

Cel i reguły: LOOP_TARGET_b_r2.md; k, znak, filtr: CALIBRATION_k_SIGNS.md (zatwierdzone). Wspólne moduły tylko importowane:
benchmark object_handling (scena, ewaluator, rusztowanie), sensory_manipulation (LegJaw = szczęka, FlyGrip), reach, safety.
Z FlyGrip skopiowane są tylko tick() i attempt(); zmiany: (1) w fazie „lift” staw 1 dostaje przyrost celu ze sterownika
ramienia (sieć / tasowanie / odruch), pozostałe stawy trzymają pozę chwytu; (2) źródło komendy stawu 1; (3) bezpiecznik
stołu; (4) odcisk trajektorii przed podniesieniem (test identyczności). World dostaje pomiar siły ramię↔blat (podklasa).

Ramiona: N (sieć z danych), S (tasowanie, --shuffle-seed), R (odruch: stałe unoszenie 0,5 rad/s), K (klasyczne IK: P["lift"]),
K0 (object_handling.Controller, w pełni klasyczny). Szczęka N/S/R/K: samodzielny LegJaw T2 L (Glu jak wariant).
Uruchom z katalogu tymczasowego:
  .venv/bin/python -I -B flymind/experiments/step2_whole_arm/lift_b.py --arm N --glu -1 --seed 20101 --poses 1 --tag it1_N_g-1
"""
import argparse
import hashlib
import json
import os
import resource
import sys
import time
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FLY = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, FLY)
import object_handling as oh  # noqa: E402
import sensory_manipulation as sm  # noqa: E402
import visual_path  # noqa: E402
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402
from connectome import load_edges  # noqa: E402
from leg_circuit import select  # noqa: E402
from pick_place import Fail  # noqa: E402
from reach import ReachError, _kin, clearance, plan  # noqa: E402
from safety import Command  # noqa: E402
from snn_interface import DEFAULT_SIGN, NT_COLS, ModelParams, assign_nt, build  # noqa: E402

OUT = os.path.join(FLY, "results", "step2_whole_arm_20261113", "lift_b")
SWING = ("Sternal anterior rotator MN",)
STANCE = ("Pleural remotor/abductor MN", "Sternal posterior rotator MN")
LIFT_SRC = {"N": "snn:legT1L", "S": "snn:legT1L_shuffled", "R": "classical:reflex_lift", "K": "classical:reach"}


@dataclass(frozen=True)
class LiftCfg:
    """Parametry ramienia stawu 1. k, s1, tau_r: CALIBRATION_k_SIGNS.md (zmiana = nowy plik kalibracji)."""
    version: str = "it1"
    k: float = 0.005               # rad/s na Hz
    s1: float = -1.0               # wymach → −q (w górę)
    tau_r: float = 0.05            # s
    J0: float = 0.2
    touch_mV_per_N: float = 40.0   # jak szczęka (FJ1)
    touch_max_mV: float = 40.0
    v_reflex: float = 0.5          # rad/s, odruch R (= v_ref kalibracji)
    lift_max: float = 3.0          # s
    z_min: float = 0.005           # m, bezpiecznik stołu (reach.clearance)
    proprio: str = "none"          # przyszłe iteracje: wejście propriocepcji T1 L (przez receptory)
    net: str = "it1"               # definicja sieci (union): it1 = pierwotna, it2 = + IN przedruchowe MN biodra T1 L


# ---------------------------------------------------------------- sieć T1 L + T2 L -----------------------------------
def t1_premotor_in(t1_sens, fl_mn, t=5):
    """it2 (poprawka błędu it1): IN obwodu T1 L wg definicji leg_circuit (vnc_intrinsic, ≥ t synaps OD receptorów nogi
    ORAZ ≥ t synaps DO jej MN), ale z MN = wszystkie MN podklasy „fl” L, a nie tylko wychodzące nerwem ProLN."""
    import pyarrow.dataset as ds
    a = pd.read_feather(visual_path.ANN, columns=["bodyId", "superclass"])
    intrinsic = set(a.bodyId[a.superclass == "vnc_intrinsic"].astype(int))
    W = ds.dataset(visual_path.WEIGHTS, format="ipc")
    out = W.to_table(filter=ds.field("body_pre").isin([int(b) for b in t1_sens])).to_pandas()
    inn = W.to_table(filter=ds.field("body_post").isin([int(b) for b in fl_mn])).to_pandas()
    s_in, m_out = out.groupby("body_post").weight.sum(), inn.groupby("body_pre").weight.sum()
    return sorted(set(s_in[s_in >= t].index) & set(m_out[m_out >= t].index) & intrinsic)


def union(glu, J0, net="it1"):
    """Podgraf indukowany MaleCNS: obwód T2 L (kolejność jak leg_circuit, więc indeksy padów jak w FlyJaw) + obwód T1 L
    + wszystkie MN podklasy „fl” strony L (MN biodra T1 wychodzą innymi nerwami — leg_data_v1.json).
    net="it2": dodatkowo IN przedruchowe T1 L dla WSZYSTKICH MN „fl” L (t1_premotor_in) — poprawka błędu it1."""
    a = pd.read_feather(visual_path.ANN, columns=["bodyId", "type", "superclass", "subclass", "somaSide"])
    t2, g2, _ = select("T2", "L")
    t1, g1, _ = select("T1", "L")
    fl = a[(a.superclass == "vnc_motor") & (a.subclass == "fl") & (a.somaSide == "L")]
    extra = []
    if net == "it2":
        t1s = [b for v in g1["sensory"].values() for b in v]
        extra = [b for b in t1_premotor_in(t1s, fl.bodyId.astype(int)) if b not in set(t1)]
    elif net != "it1":
        raise ValueError(f"nieznana wersja sieci {net!r}")
    bodies = list(dict.fromkeys([int(b) for b in list(t2) + list(t1) + sorted(fl.bodyId.astype(int)) + list(extra)]))
    edges, erep = load_edges(visual_path.WEIGHTS, bodies=bodies)
    nts = pd.read_feather(visual_path.NTS)
    tab = nts.set_index("body").reindex(bodies)[list(NT_COLS)]
    ov = {b: ("unknown", "brak NT; znak 0") for b, r in tab.iterrows()
          if not any(isinstance(x, str) and x != "unclear" for x in r)}
    signs = {**DEFAULT_SIGN, "glutamate": glu}
    signs.update({n: 0.0 for n in set(assign_nt(bodies, nts, ov).nt) - set(signs)})
    spec = build(edges, bodies, nts, ModelParams(J0=J0, sign_map=signs), nt_overrides=ov)
    pos = {b: i for i, b in enumerate(bodies)}
    br = g2["sensory"]["mechanosensory bristle"]
    ty = fl.set_index("bodyId").type
    pool = lambda names: [pos[int(b)] for b in fl.bodyId if ty[b] in names]  # noqa: E731
    idx = dict(pad_in=([pos[b] for b in br[: len(br) // 2]], [pos[b] for b in br[len(br) // 2:]]),
               swing=pool(SWING), stance=pool(STANCE),
               t1_sensory={k: [pos[b] for b in v] for k, v in g1["sensory"].items()})
    rep = dict(N=len(bodies), T2L=len(t2), T1L=len(set(t1) | set(fl.bodyId.astype(int))), net=net, added_T1_IN=len(extra), edges=erep["loaded"],
               swing=len(idx["swing"]), stance=len(idx["stance"]), W_sha256=spec.report["W_sha256"])
    return spec, idx, rep


class _W:
    def __init__(self, W):
        self.W = W


class LiftNet:
    """Sterownik stawu 1: dotyk padów → szczecinki T2 L → (połączenia z danych) → pule wymach / podpór T1 L."""

    def __init__(self, glu, lc, shuffle_seed=None):
        spec, self.idx, self.rep = union(glu, lc.J0, lc.net)
        if shuffle_seed is not None:
            spec = visual_path.shuffle(spec, shuffle_seed, equal_weight=True)
            self.rep = dict(self.rep, shuffle_seed=shuffle_seed, W_sha256_shuffled=hashlib.sha256(
                np.ascontiguousarray(spec.W).tobytes()).hexdigest())
        self.W, self.N, self.lc = spec.W, spec.W.shape[0], lc
        self.reset()

    def reset(self):
        self.net = SparseALIF(_W(self.W), ALIFParams(), None)      # szum 0
        self.r = np.zeros(2)

    def step(self, touch, q1, qd1, dt=0.01):
        c, X = self.lc, np.zeros(self.N)
        for ix, f in zip(self.idx["pad_in"], touch[:2]):
            X[ix] = min(c.touch_max_mV, c.touch_mV_per_N * max(0.0, float(f)))
        s = self.net.run(X, 10)
        now = np.array([s[:, self.idx["swing"]].mean(), s[:, self.idx["stance"]].mean()]) * 1000.0
        self.r += dt / c.tau_r * (now - self.r)
        return c.s1 * c.k * dt * float(self.r[0] - self.r[1])


class Reflex:
    def __init__(self, lc):
        self.lc, self.r = lc, np.zeros(2)

    def reset(self):
        pass

    def step(self, touch, q1, qd1, dt=0.01):
        return -self.lc.v_reflex * dt


# ---------------------------------------------------------------- świat z pomiarem siły na blat ---------------------
class ForceWorld(oh.World):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._f6 = np.zeros(6)
        self.fmax = {}

    def step(self, q_t, tau):
        obs = super().step(q_t, tau)
        d, m, f = self.sim.d, self.sim.m, 0.0
        for i, (g1, g2) in enumerate(d.contact.geom[:d.ncon]):
            a, b = self.lab[g1], self.lab[g2]
            if "table" in (a, b) and (a in oh.ARMSET or b in oh.ARMSET):
                self.sim.mj.mj_contactForce(m, d, i, self._f6)
                f += abs(float(self._f6[0]))
        if f > self.fmax.get(self.phase, 0.0):
            self.fmax[self.phase] = round(f, 4)
        return obs


# ---------------------------------------------------------------- kontroler -----------------------------------------
class LiftGrip(sm.FlyGrip):
    def __init__(self, world, cfg, driver, src, fc, arm, lift, lc):
        super().__init__(world, cfg, driver, src, fc)
        self.arm, self.lift, self.lc = arm, lift, lc
        self.src1, self.dq1, self.lifting, self.q1 = "classical:reach", 0.0, False, None
        self.h, self.prelift, self.pre_ticks = hashlib.sha256(), None, 0
        self.guard = self.lift_ticks = 0
        self.lift_log = []

    def tick(self, tgt, mode):                                     # = FlyGrip.tick + staw 1 + odcisk + bezpiecznik
        o, g = self.obs, self.grip
        if self.lift is not None:                                  # sieć stawu 1 liczy się w KAŻDYM takcie (te same zmysły)
            self.dq1 = float(self.lift.step(o.touch, float(o.q[1]), float(o.qd[1])))
        if self.lifting:
            q1n = self.q1 + self.dq1
            qc = np.r_[tgt[:5], o.q[5]]
            qc[1] = q1n
            if clearance(self.sim, qc) < self.lc.z_min:            # BEZPIECZNIK (klasyczny), nie decyzja muchy
                self.guard += 1
                q1n = self.q1
            self.q1 = q1n
            tgt = np.array(tgt[:5], float)
            tgt[1] = q1n
            self.lift_ticks += 1
        w0 = time.perf_counter()
        self.tau_fly = float(self.driver.step(o.touch, float(o.q[5]), float(o.qd[5])))
        w1 = time.perf_counter()
        on = self.tau_fly >= self.fc.tau_engage
        self.eng, self.low = (self.eng + 1, 0) if on else (0, self.low + 1)
        if mode in ("fly", "search"):
            if self._touch_t is None and max(o.touch[:2]) > 0.05:
                self._touch_t = o.t
            if self._touch_t is not None and self._close_t is None and self.tau_fly > 0.05:
                self._close_t = o.t
                self.react.append(round((o.t - self._touch_t) * 1e3, 1))
        if mode == "fly":
            tau, src = self.tau_fly, self.src
        elif mode == "search":
            tau, src = self.fc.tau_search, "classical:search"
        else:
            g.mode, src = "open", "classical:open"
            tau = g.cfg.tau_open if o.q[5] < g.cfg.q_open else \
                g.cfg.tau_close if mode == "preshape" and o.q[5] > g.cfg.q_open + 0.05 else 0.0
        srcs = {**{j: "classical:reach" for j in range(5)}, "jaw": src}
        if self.lifting:
            srcs[1] = self.src1
            srcs.update({j: "script:hold_grasp_pose" for j in (0, 2, 3, 4)})
        cmd = Command(o.t, {j: float(tgt[j]) for j in range(5)}, tau, srcs)
        q_t, tau_t, flags, per = self.safety.step(cmd, o.q, o.t, 0.0)
        if flags:
            raise Fail("safety_" + flags[0], str(flags))
        for f in {x for v in per.values() for x in v}:
            self.stats["flags"][f] = self.stats["flags"].get(f, 0) + 1
        w2 = time.perf_counter()
        self.lat.append((*getattr(self.driver, "t", (0, w1 - w0, 0)), w2 - w1))
        self.obs = self.w.step(q_t, tau_t)
        if self.prelift is None:
            if self.w.phase == "lift":
                self.prelift = self.h.hexdigest()
            else:
                self.h.update(np.r_[q_t, tau_t, self.obs.q, self.obs.qd, self.obs.touch].tobytes())
                self.pre_ticks += 1

    def lift_phase(self, P):
        """Staw 1 z ramienia (sieć / tasowanie / odruch), stawy 0, 2–4 trzymają pozę chwytu; koniec: wysokość transportu
        (sukces ruchu) albo lift_max (porażka „no_lift”). Potem transport planowany klasycznie z bieżącej pozy."""
        sim, c = self.sim, self.lc
        cs = lambda q: _kin(sim, q).site("cs_fixed").xpos.copy()  # noqa: E731
        tgt = np.asarray((P["side"] or P["descend"])[-1])[:5].copy()
        z_goal = cs(self.obs.q)[2] + (P["z_carry"] - P["z_grasp"])
        self.lifting, self.q1, self.src1 = True, float(tgt[1]), LIFT_SRC[self.arm]
        t0, g0, ok = self.lift_ticks, self.guard, False
        try:
            for _ in range(int(round(c.lift_max / self.lim.dt))):
                if cs(self.obs.q)[2] >= z_goal:
                    ok = True
                    break
                self.tick(tgt, "fly")
                self.gripping()
            ok = ok or cs(self.obs.q)[2] >= z_goal
        finally:
            self.lifting, self.src1 = False, "classical:reach"
            self.lift_log.append(dict(ticks=self.lift_ticks - t0, guard=self.guard - g0, ok=ok,
                                      dz_mm=round(float(cs(self.obs.q)[2] - (z_goal - (P["z_carry"] - P["z_grasp"]))) * 1e3, 1)))
        if not ok:
            raise Fail("no_lift", f"dz {self.lift_log[-1]['dz_mm']} mm po {c.lift_max} s, bezpiecznik {self.guard - g0}")
        try:
            P["transport"] = plan(sim, self.obs.q.copy(), cs(P["transport"][-1]), point="cs_fixed", cfg=self.rcfg)
        except ReachError as e:
            raise Fail("unreachable_after_lift", str(e)) from e

    def attempt(self, p):                                          # = FlyGrip.attempt, faza „lift” podmieniona
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
            w.phase = "grasp"
            for x in oh.profile(P["side"], self.obs.q, fc.v_side, c.a_max, self.lim.dt) if P["side"] else []:
                self.tick(x, "fly")
            tgt = np.asarray((P["side"] or P["descend"])[-1])[:5]
            if not self.wait(*((fc.hold_max, tgt, "fly") if P["side"] else (fc.search_max, tgt, "search")),
                             until=lambda: self.eng >= fc.engage_ticks):
                raise Fail("no_engage", f"moment sterownika {self.tau_fly:.2f} N·m, touch {np.round(self.obs.touch, 2).tolist()}")
            rec["tau_engage"], rec["q_jaw_grasp"] = round(self.tau_fly, 3), round(float(self.obs.q[5]), 3)
            mark("grasp")
            w.phase = "lift"
            if self.arm == "K":
                self.follow(P["lift"], "fly", self.gripping)
            else:
                self.lift_phase(P)
            rec["lifted"] = True
            mark("lift")
            w.phase = "transport"
            self.follow(P["transport"], "fly", self.gripping)
            rec["tau_carry"] = round(self.tau_fly, 3)
            mark("transport")
            w.phase = "place"
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


# ---------------------------------------------------------------- próba, seria ---------------------------------------
def run_trial(item, seed, arm, jaw, lift, fc, lc):
    made, origC, origW = [], oh.Controller, oh.World
    if jaw is not None:
        jaw.reset()
    if lift is not None:
        lift.reset()
    worlds = []
    oh.World = lambda *a, **kw: worlds.append(ForceWorld(*a, **kw)) or worlds[-1]
    if arm != "K0":
        oh.Controller = lambda world, cfg: made.append(LiftGrip(world, cfg, jaw, "snn:legT2L", fc, arm, lift, lc)) or made[0]
    try:
        r = oh.run([item], seed)
    finally:
        oh.Controller, oh.World = origC, origW
    o = r["objects"][0]
    ctl = made[0] if made else None
    ss = r["safety_stats"]
    return dict(item="/".join(item), seed=seed, truth=o["truth"], success=o["success"], final=o["final"],
                attempts=o["attempts"], reasons=[x["reason"] for x in o["attempt_log"] if not x["ok"]],
                complete=r["complete"], stopped_by=r["stopped_by"], T_sim=round(r["T_sim"], 3), T_wall=round(r["T_wall"], 2),
                fmax_by_phase=worlds[0].fmax, fmax=max(worlds[0].fmax.values(), default=0.0),
                unwanted=r["unwanted"], prelift_sha=ctl.prelift if ctl else None, prelift_ticks=ctl.pre_ticks if ctl else None,
                lift_log=ctl.lift_log if ctl else [], guard=ctl.guard if ctl else 0, lift_ticks=ctl.lift_ticks if ctl else 0,
                safety_stats=ss, pen_mm=o.get("pen_mm"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=("N", "S", "R", "K", "K0"))
    ap.add_argument("--glu", type=float, default=-1.0)
    ap.add_argument("--shuffle-seed", type=int)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--poses", type=int, default=1)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--version", default="it1")
    ap.add_argument("--lift-max", type=float, default=3.0)
    ap.add_argument("--net", default="it1", choices=("it1", "it2"))
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    if a.seed in (20201,) and not os.environ.get("STEP2_FINAL_TEST"):
        sys.exit("ziarna testowe tylko w teście końcowym (STEP2_FINAL_TEST=1)")
    if (a.arm == "S") != (a.shuffle_seed is not None):
        sys.exit("--shuffle-seed wymagane dokładnie dla ramienia S")
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, a.tag + ".json")
    if os.path.exists(path):
        sys.exit(f"istnieje {path}")
    lc = LiftCfg(version=a.version, lift_max=a.lift_max, net=a.net)
    fc = sm.FlyCfg(glu_sign=a.glu, trigger="search")
    w0 = time.perf_counter()
    jaw = None if a.arm == "K0" else sm.LegJaw(fc, touch=True, proprio=False)
    lift = LiftNet(a.glu, lc, a.shuffle_seed) if a.arm in ("N", "S") else Reflex(lc) if a.arm == "R" else None
    build_s = time.perf_counter() - w0
    items, runs = oh.SETS["base"], []
    for it in [x for x in items if not a.only or "/".join(x) in a.only]:
        for k in range(a.poses):
            r = run_trial(it, a.seed * 1000 + items.index(it) * 10 + k, a.arm, jaw, lift, fc, lc)
            runs.append(r)
            print(f"{r['item']:22s} {k}: lift {r['truth']['lift']!s:5} placed {r['success']!s:5} fmax {r['fmax']:6.2f} N "
                  f"guard {r['guard']:4d} {r['reasons']} {r['lift_log']}", flush=True)
    out = dict(tag=a.tag, arm=a.arm, glu=a.glu, shuffle_seed=a.shuffle_seed, seed=a.seed, poses=a.poses, version=a.version,
               lift_cfg=asdict(lc), fly_cfg=asdict(fc), argv=sys.argv, build_s=round(build_s, 1),
               lift_net=getattr(lift, "rep", None), wall_s=round(time.perf_counter() - w0, 1),
               max_rss_MB=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20, 1),
               code_sha256={f: hashlib.sha256(open(p, "rb").read()).hexdigest() for f, p in
                            (("lift_b.py", __file__), ("sensory_manipulation.py", sm.__file__), ("object_handling.py", oh.__file__))},
               runs=runs)
    with open(path, "x") as f:
        json.dump(out, f, indent=1, default=float)
    print("zapisano", path, "| lift", sum(r["truth"]["lift"] for r in runs), "/", len(runs), "| wall", out["wall_s"], "s")


if __name__ == "__main__":
    main()
