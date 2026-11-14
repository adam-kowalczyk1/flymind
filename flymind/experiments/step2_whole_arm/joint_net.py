"""Krok 2 (stawy b–e i całe ramię): uogólnienie lift_b.py (lift_b.py bez zmian, tylko importowany). SYMULACJA MuJoCo.

Zadania (cele: LOOP_TARGET_*.md):
  --joints 1|2|3|1,2,3   faza „podniesienie”: wskazane stawy z sieci, pozostałe trzymają pozę chwytu; koniec jak w lift_b
                         (cs_fixed na wysokości transportu = sukces ruchu, inaczej po lift_max „no_lift”)
  --roll                 staw 4 (wrist_roll) z sieci od zaciśnięcia do zwolnienia (podniesienie, transport, odkładanie);
                         stawy 0–3 jak w rusztowaniu (IK); bez --joints podnoszenie klasyczne (IK)
Komenda stawu j (CALIBRATION_k_SIGNS.md): cel_j += s_j · k · dt · (r_POS_j − r_NEG_j), filtr τ_r 50 ms.
Wejścia sieci (tylko receptory; MN i interneuronów nie pobudza się):
  padsT2   dotyk padów → szczecinki T2 L (jak szczęka i lift_b)                                   [jak FJ1]
  padsT1   ten sam dotyk → szczecinki stopy T1 L (klasa „mechanosensory bristle”, połowa na pad)  [MODEL]
  fecoT1   kąt/prędkość łokcia (staw 2) → FeCO T1 L (claw/hook, typy jak sensory_manipulation.FECO) [MODEL]
Sieć: T2 L + T1 L (+ MN „fl” L) jak lift_b.union; --in-rule fl dodaje interneurony T1 wybrane względem WSZYSTKICH MN „fl” L
(≥ 5 synaps z receptorów T1 L i ≥ 5 do MN „fl” L) — poprawka D3 z logu (lift_b brał IN tylko względem MN nerwu ProLN).
Ramiona: N, S (tasowanie), R (odruch: stawy podnoszenia stale „w górę” 0,5 rad/s; staw 4 trzymany), K (klasyczne IK),
K0 (object_handling.Controller). Szczęka N/S/R/K: samodzielny LegJaw T2 L.
  .venv/bin/python -I -B joint_net.py --arm N --glu -1 --seed 20301 --joints 2 --inputs padsT2,padsT1 --in-rule fl \
      --version c_it1 --tag c_it1_N_g-1 --out DIR
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
import pyarrow.dataset as ds

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lift_b_pin as LB  # noqa: E402  (przypięta kopia lift_b.py, sha 2e6e0698…; ścieżki i moduły wspólne)
from lift_b_pin import Fail, ForceWorld, ReachError, _kin, clearance, oh, plan, sm, visual_path  # noqa: E402
from alif import ALIFParams  # noqa: E402
from alif_sparse import SparseALIF  # noqa: E402
from connectome import load_edges  # noqa: E402
from leg_circuit import select  # noqa: E402
from safety import Command  # noqa: E402
from snn_interface import DEFAULT_SIGN, NT_COLS, ModelParams, assign_nt, build  # noqa: E402

TEST_SEEDS = {20201, 20401, 20601, 20801, 20901}
# pule i znaki: CALIBRATION_k_SIGNS.md, tabela sekcji 3 (bez zmian)
POOLS = {1: (LB.SWING, LB.STANCE),
         2: (("Ti flexor MN", "Acc. ti flexor MN"), ("Ti extensor MN",)),
         3: (("Ta levator MN",), ("Ta depressor MN",)),
         4: (("Tr flexor MN",), ("Tr extensor MN", "Sternotrochanter MN", "Tergotr. MN"))}
SIGN = {1: -1.0, 2: 1.0, 3: -1.0, 4: 1.0}
UP = {1: -1.0, 2: -1.0, 3: -1.0}          # kierunek q, który unosi chwytak (CALIBRATION sekcja 3) — tylko odruch R
SRC = {"N": "snn:legT1L", "S": "snn:legT1L_shuffled", "R": "classical:reflex", "K": "classical:reach"}
FECO_T1 = dict(claw_ext="SNpp51", claw_flex="SNpp50", hook_ext="SNpp39", hook_flex="SNpp41")


@dataclass(frozen=True)
class ArmCfg:
    version: str = "x"
    joints: tuple = (1,)           # stawy z sieci w fazie podniesienia
    roll: bool = False             # staw 4 z sieci od zaciśnięcia do zwolnienia
    inputs: tuple = ("padsT2",)
    in_rule: str = "nerve"         # "nerve" = lift_b.union; "fl" = poprawka D3
    k: float = 0.005
    tau_r: float = 0.05
    J0: float = 0.2
    touch_mV_per_N: float = 40.0
    touch_max_mV: float = 40.0
    feco_mV: float = 40.0          # [MODEL] jak szczęka (sensory_manipulation.FlyCfg)
    q2_mid: float = 0.0            # środek zakresu łokcia (ctrlrange ±1,69)
    q2_span: float = 1.69
    qd_ref: float = 1.0
    v_reflex: float = 0.5
    lift_max: float = 3.0
    z_min: float = 0.005
    dt_ms: float = 1.0             # krok ALIF sieci ramienia (szczęka zawsze jak w module wspólnym)


def build_net(glu, J0, in_rule):
    a = pd.read_feather(visual_path.ANN, columns=["bodyId", "type", "superclass", "subclass", "somaSide"])
    t2, g2, _ = select("T2", "L")
    t1, g1, _ = select("T1", "L")
    fl = a[(a.superclass == "vnc_motor") & (a.subclass == "fl") & (a.somaSide == "L")]
    flb = sorted(fl.bodyId.astype(int))
    extra = []
    if in_rule == "fl":
        sens1 = sorted({int(b) for v in g1["sensory"].values() for b in v})
        intr = set(a.bodyId[a.superclass == "vnc_intrinsic"].astype(int))
        W = ds.dataset(visual_path.WEIGHTS, format="ipc")
        s_in = W.to_table(filter=ds.field("body_pre").isin(sens1)).to_pandas().groupby("body_post").weight.sum()
        m_out = W.to_table(filter=ds.field("body_post").isin(flb)).to_pandas().groupby("body_pre").weight.sum()
        extra = sorted(set(s_in[s_in >= 5].index) & set(m_out[m_out >= 5].index) & intr)
    elif in_rule != "nerve":
        raise ValueError(in_rule)
    bodies = list(dict.fromkeys([int(b) for b in list(t2) + list(t1) + flb + list(extra)]))
    edges, erep = load_edges(visual_path.WEIGHTS, bodies=bodies)
    nts = pd.read_feather(visual_path.NTS)
    tab = nts.set_index("body").reindex(bodies)[list(NT_COLS)]
    ov = {b: ("unknown", "brak NT; znak 0") for b, r in tab.iterrows() if not any(isinstance(x, str) and x != "unclear" for x in r)}
    signs = {**DEFAULT_SIGN, "glutamate": glu}
    signs.update({n: 0.0 for n in set(assign_nt(bodies, nts, ov).nt) - set(signs)})
    spec = build(edges, bodies, nts, ModelParams(J0=J0, sign_map=signs), nt_overrides=ov)
    pos = {b: i for i, b in enumerate(bodies)}
    ty = a.set_index("bodyId").type
    pool = lambda names: [pos[b] for b in flb if ty[b] in names]  # noqa: E731
    half = lambda v: ([pos[b] for b in v[: len(v) // 2]], [pos[b] for b in v[len(v) // 2:]])  # noqa: E731
    sens1all = [b for v in g1["sensory"].values() for b in v]
    idx = dict(padsT2=half(g2["sensory"]["mechanosensory bristle"]), padsT1=half(g1["sensory"]["mechanosensory bristle"]),
               feco={k: [pos[b] for b in sens1all if str(ty.get(b)) == t] for k, t in FECO_T1.items()},
               pools={j: (pool(p), pool(n)) for j, (p, n) in POOLS.items()})
    rep = dict(N=len(bodies), T2L=len(t2), T1L=len(set(t1) | set(flb)), extra_IN=len(extra), in_rule=in_rule,
               edges=erep["loaded"], pools={j: [len(p), len(n)] for j, (p, n) in idx["pools"].items()},
               padsT1=[len(x) for x in idx["padsT1"]], feco={k: len(v) for k, v in idx["feco"].items()},
               W_sha256=spec.report["W_sha256"])
    return spec, idx, rep


class ArmNet:
    """Sieć T1 L + T2 L jako sterownik stawów 1–4 (wyjście: przyrosty celów; które trafiają do robota — decyduje kontroler)."""

    def __init__(self, glu, ac, shuffle_seed=None):
        spec, self.idx, self.rep = build_net(glu, ac.J0, ac.in_rule)
        if shuffle_seed is not None:
            spec = visual_path.shuffle(spec, shuffle_seed, equal_weight=True)
            self.rep = dict(self.rep, shuffle_seed=shuffle_seed,
                            W_sha256_shuffled=hashlib.sha256(np.ascontiguousarray(spec.W).tobytes()).hexdigest())
        self.W, self.N, self.ac = spec.W, spec.W.shape[0], ac
        self.nsteps = int(round(10.0 / ac.dt_ms))
        self.reset()

    def reset(self):
        self.net = SparseALIF(LB._W(self.W), ALIFParams(dt=self.ac.dt_ms), None)    # szum 0
        self.r = np.zeros((5, 2))

    def step(self, touch, q, qd, dt=0.01):
        c, X = self.ac, np.zeros(self.N)
        for name in ("padsT2", "padsT1"):
            if name in c.inputs:
                for ix, f in zip(self.idx[name], touch[:2]):
                    X[ix] = min(c.touch_max_mV, c.touch_mV_per_N * max(0.0, float(f)))
        if "fecoT1" in c.inputs:                                # łokieć ↔ staw udo–goleń (zgięcie = +q2)
            e = (float(q[2]) - c.q2_mid) / c.q2_span
            X[self.idx["feco"]["claw_flex"]] = c.feco_mV * min(1.0, max(0.0, e))
            X[self.idx["feco"]["claw_ext"]] = c.feco_mV * min(1.0, max(0.0, -e))
            X[self.idx["feco"]["hook_flex"]] = c.feco_mV * min(1.0, max(0.0, float(qd[2]) / c.qd_ref))
            X[self.idx["feco"]["hook_ext"]] = c.feco_mV * min(1.0, max(0.0, -float(qd[2]) / c.qd_ref))
        s = self.net.run(X, self.nsteps)
        dq = np.zeros(5)
        for j, (p, n) in self.idx["pools"].items():
            now = np.array([s[:, p].mean(), s[:, n].mean()]) * 1000.0 / c.dt_ms
            self.r[j] += dt / c.tau_r * (now - self.r[j])
            dq[j] = SIGN[j] * c.k * dt * float(self.r[j, 0] - self.r[j, 1])
        return dq


class ArmReflex:
    def __init__(self, ac):
        self.ac = ac

    def reset(self):
        pass

    def step(self, touch, q, qd, dt=0.01):
        dq = np.zeros(5)
        for j in self.ac.joints:
            dq[j] = UP[j] * self.ac.v_reflex * dt
        return dq                                               # staw 4: trzymany (0)


class ArmGrip(sm.FlyGrip):
    def __init__(self, world, cfg, jaw, src, fc, arm, drv, ac):
        super().__init__(world, cfg, jaw, src, fc)
        self.arm, self.drv, self.ac = arm, drv, ac
        self.dq, self.active, self.qc, self.lifting = np.zeros(5), set(), {}, False
        self.h, self.prelift, self.pre_ticks = hashlib.sha256(), None, 0
        self.guard = self.lift_ticks = self.act_ticks = 0
        self.lift_log, self.roll_dev, self.rsum = [], 0.0, np.zeros((5, 2))

    def tick(self, tgt, mode):
        o, g = self.obs, self.grip
        if self.drv is not None:                                   # sieć liczy się w KAŻDYM takcie (te same zmysły)
            self.dq = self.drv.step(o.touch, o.q, o.qd)
        tgt = np.array(tgt[:5], float)
        if self.active:
            qn = {j: self.qc[j] + float(self.dq[j]) for j in self.active}
            qc = np.r_[tgt, o.q[5]]
            for j, v in qn.items():
                qc[j] = v
            if clearance(self.sim, qc) < self.ac.z_min:            # BEZPIECZNIK (klasyczny), nie decyzja muchy
                self.guard += 1
                qn = {j: self.qc[j] for j in self.active}
            self.qc.update(qn)
            for j, v in qn.items():
                tgt[j] = v
            self.act_ticks += 1
            self.lift_ticks += int(self.lifting)
            if 4 in self.active:
                self.roll_dev = max(self.roll_dev, abs(self.qc[4] - self.q4_0))
            if hasattr(self.drv, "r"):
                self.rsum += self.drv.r
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
            srcs.update({j: "script:hold_grasp_pose" for j in range(5)})
        for j in self.active:
            srcs[j] = SRC[self.arm]
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
        sim, c = self.sim, self.ac
        cs = lambda q: _kin(sim, q).site("cs_fixed").xpos.copy()  # noqa: E731
        tgt = np.asarray((P["side"] or P["descend"])[-1])[:5].copy()
        z_goal = cs(self.obs.q)[2] + (P["z_carry"] - P["z_grasp"])
        self.active = set(c.joints) | ({4} if c.roll else set())
        self.qc = {j: float(tgt[j]) for j in self.active}
        self.lifting, t0, g0, ok = True, self.lift_ticks, self.guard, False
        try:
            for _ in range(int(round(c.lift_max / self.lim.dt))):
                if cs(self.obs.q)[2] >= z_goal:
                    ok = True
                    break
                self.tick(tgt, "fly")
                self.gripping()
            ok = bool(ok or cs(self.obs.q)[2] >= z_goal)
        finally:
            self.lifting = False
            self.active = {4} if c.roll else set()
            self.lift_log.append(dict(ticks=self.lift_ticks - t0, guard=self.guard - g0, ok=ok,
                                      dz_mm=round(float(cs(self.obs.q)[2] - (z_goal - (P["z_carry"] - P["z_grasp"]))) * 1e3, 1)))
        if not ok:
            raise Fail("no_lift", f"dz {self.lift_log[-1]['dz_mm']} mm po {c.lift_max} s, bezpiecznik {self.guard - g0}")
        try:
            P["transport"] = plan(sim, self.obs.q.copy(), cs(P["transport"][-1]), point="cs_fixed", cfg=self.rcfg)
        except ReachError as e:
            raise Fail("unreachable_after_lift", str(e)) from e

    def attempt(self, p):                                          # = lift_b.LiftGrip.attempt + staw 4 + wiele stawów
        c, w, fc, ac = self.cfg, self.w, self.fc, self.ac
        rec = dict(percept=p, t_sim={}, t_wall={}, ok=False, reason=None, lifted=False)
        t0, clock = self.obs.t, [self.obs.t, time.perf_counter()]
        self._touch_t = self._close_t = None
        net_arm = self.arm in ("N", "S", "R")

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
            self.q4_0 = float(tgt[4])
            if net_arm and ac.joints:
                self.lift_phase(P)
            else:
                if net_arm and ac.roll:
                    self.active, self.qc = {4}, {4: float(tgt[4])}
                self.follow(P["lift"], "fly", self.gripping)
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
            self.active = set()
            w.phase = "return"
            if P["retreat"]:
                self.follow(P["retreat"], "open")
            self.follow(P["home"], "open")
            mark("return")
            rec["ok"] = True
        except Fail as e:
            self.active, self.lifting = set(), False
            rec.update(reason=e.reason, detail=e.detail, fail_phase=w.phase, t_to_fail_sim=self.obs.t - t0)
            rec["recover"] = self.recover()
            if rec["recover"] is not True:
                self.stop = f"recover: {rec['recover']}"
        w.phase = "idle"
        rec["op_sim"] = self.obs.t - t0
        return rec


def run_trial(item, seed, arm, jaw, drv, fc, ac):
    made, origC, origW, worlds = [], oh.Controller, oh.World, []
    if jaw is not None:
        jaw.reset()
    if drv is not None:
        drv.reset()
    oh.World = lambda *a, **kw: worlds.append(ForceWorld(*a, **kw)) or worlds[-1]
    if arm != "K0":
        oh.Controller = lambda world, cfg: made.append(ArmGrip(world, cfg, jaw, "snn:legT2L", fc, arm, drv, ac)) or made[0]
    try:
        r = oh.run([item], seed)
    finally:
        oh.Controller, oh.World = origC, origW
    o, ctl = r["objects"][0], (made[0] if made else None)
    at = ctl.act_ticks if ctl else 0
    return dict(item="/".join(item), seed=seed, truth=o["truth"], success=o["success"], final=o["final"],
                attempts=o["attempts"], reasons=[x["reason"] for x in o["attempt_log"] if not x["ok"]],
                complete=r["complete"], stopped_by=r["stopped_by"], T_sim=round(r["T_sim"], 3), T_wall=round(r["T_wall"], 2),
                fmax_by_phase=worlds[0].fmax, fmax=max(worlds[0].fmax.values(), default=0.0), unwanted=r["unwanted"],
                prelift_sha=ctl.prelift if ctl else None, prelift_ticks=ctl.pre_ticks if ctl else None,
                lift_log=ctl.lift_log if ctl else [], guard=ctl.guard if ctl else 0, lift_ticks=ctl.lift_ticks if ctl else 0,
                act_ticks=at, roll_dev=round(ctl.roll_dev, 4) if ctl else 0.0,
                mean_rates_active=(ctl.rsum / at).round(2).tolist() if ctl and at else None,
                safety_stats=r["safety_stats"], pen_mm=o.get("pen_mm"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=("N", "S", "R", "K", "K0"))
    ap.add_argument("--glu", type=float, default=-1.0)
    ap.add_argument("--shuffle-seed", type=int)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--poses", type=int, default=1)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--joints", default="")
    ap.add_argument("--roll", action="store_true")
    ap.add_argument("--inputs", default="padsT2")
    ap.add_argument("--in-rule", default="nerve", choices=("nerve", "fl"))
    ap.add_argument("--dt-ms", type=float, default=1.0)
    ap.add_argument("--lift-max", type=float, default=3.0)
    ap.add_argument("--version", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.seed in TEST_SEEDS and not os.environ.get("STEP2_FINAL_TEST"):
        sys.exit("ziarna testowe tylko w teście końcowym (STEP2_FINAL_TEST=1)")
    if (a.arm == "S") != (a.shuffle_seed is not None):
        sys.exit("--shuffle-seed wymagane dokładnie dla ramienia S")
    joints = tuple(int(x) for x in a.joints.split(",") if x)
    if not set(joints) <= {1, 2, 3} or not (joints or a.roll):
        sys.exit("--joints ⊂ {1,2,3} i/lub --roll")
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, a.tag + ".json")
    if os.path.exists(path):
        sys.exit(f"istnieje {path}")
    ac = ArmCfg(version=a.version, joints=joints, roll=a.roll, inputs=tuple(a.inputs.split(",")), in_rule=a.in_rule,
                dt_ms=a.dt_ms, lift_max=a.lift_max)
    fc = sm.FlyCfg(glu_sign=a.glu, trigger="search")
    w0 = time.perf_counter()
    jaw = None if a.arm == "K0" else sm.LegJaw(fc, touch=True, proprio=False)
    drv = ArmNet(a.glu, ac, a.shuffle_seed) if a.arm in ("N", "S") else ArmReflex(ac) if a.arm == "R" else None
    build_s = time.perf_counter() - w0
    items, runs = oh.SETS["base"], []
    for it in [x for x in items if not a.only or "/".join(x) in a.only]:
        for k in range(a.poses):
            r = run_trial(it, a.seed * 1000 + items.index(it) * 10 + k, a.arm, jaw, drv, fc, ac)
            runs.append(r)
            print(f"{r['item']:22s} {k}: lift {r['truth']['lift']!s:5} placed {r['success']!s:5} fmax {r['fmax']:6.2f} N "
                  f"guard {r['guard']:4d} roll {r['roll_dev']:.3f} {r['reasons']} {r['lift_log']}", flush=True)
    out = dict(tag=a.tag, arm=a.arm, glu=a.glu, shuffle_seed=a.shuffle_seed, seed=a.seed, poses=a.poses, version=a.version,
               arm_cfg=asdict(ac), fly_cfg=asdict(fc), argv=sys.argv, build_s=round(build_s, 1),
               lift_net=getattr(drv, "rep", None), wall_s=round(time.perf_counter() - w0, 1),
               max_rss_MB=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20, 1),
               code_sha256={f: hashlib.sha256(open(p, "rb").read()).hexdigest() for f, p in
                            (("joint_net.py", __file__), ("lift_b.py", LB.__file__), ("sensory_manipulation.py", sm.__file__),
                             ("object_handling.py", oh.__file__))},
               runs=runs)
    with open(path, "x") as f:
        json.dump(out, f, indent=1, default=float)
    print("zapisano", path, "| lift", sum(r["truth"]["lift"] for r in runs), "| placed", sum(r["success"] for r in runs),
          "/", len(runs), "| wall", out["wall_s"], "s")


if __name__ == "__main__":
    main()
