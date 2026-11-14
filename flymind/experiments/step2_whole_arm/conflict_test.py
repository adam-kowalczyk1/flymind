"""Krok 7: konflikt bodźców na sieci wspólnej (wzrok + dotyk). SYMULACJA MuJoCo.

Pytanie: czy bodziec wzrokowy pokazany W TRAKCIE trzymania przedmiotu zmienia zachowanie chwytu, gdy wzrok NIE jest ręcznie
bramkowany (kanał wzrokowy sieci jest włączony przez cały czas)?
Sieć: `vision_manipulation.VisJaw` (moduł wspólny, importowany bez zmian) — podgraf indukowany MaleCNS: droga wzrokowa
LC10a → pośrednie → DNa02 ∪ obwód nogi T2 L; w danych DNa02 L ma 1190 synaps do 30 neuronów obwodu T2 L [DATA].
Szczęka = moment z MN goleni tej sieci (jak LegJaw); wejścia: dotyk padów → szczecinki T2 L, kamera „eye” na chwytaku →
enkoder koloru → LC10a L/R (każdy takt). Ramię: klasyczne rusztowanie (jak B_fly_search), percept-wyrocznia (jak etap czucia).
Przedmioty w kolorach materiałów (--colors native; pilot 1 z zielonymi: enkoder nasycony g≈1 — patrz log).
Bodziec: zielona kula (geom „ball” sceny, bez kolizji, ustawiana kinematycznie w układzie kamery) od początku fazy
podniesienia do początku odkładania; po stronie LEWEJ kadru. Sham: ta sama kula w tym samym miejscu, kolor szary (enkoder
koloru jej nie widzi; tak samo zasłania tło). Tasowania S: `block_shuffle` tylko krawędzi wzrok → noga (cele przetasowane
w obrębie obwodu nogi przy zachowanych stopniach i wagach); oba obwody poza tym bez zmian.
  .venv/bin/python -I -B conflict_test.py --arm N --glu -1 --stim on --seed 20961 --poses 1 --tag … --out DIR
"""
import argparse
import hashlib
import json
import os
import resource
import sys
import time
from dataclasses import asdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lift_b_pin as LB  # noqa: E402,F401  (ustawia ścieżkę do flymind/)
import object_handling as oh  # noqa: E402
import sensory_manipulation as sm  # noqa: E402
import vision_manipulation as vm  # noqa: E402
from block_shuffle import block_shuffle  # noqa: E402

TEST_SEEDS = {20971}
NOISE0 = {20961: 20_990_500, 20971: 20_990_000}     # ziarno szumu drogi wzrokowej = NOISE0[seed] + nr próby (SEED_REGISTRY)
OFFSET = (-0.045, 0.0, -0.10)   # m, układ kamery (x w prawo, y w górę, −z = oś widzenia); ustalone w pilocie z OBRAZU (g), nie z zachowania
GREEN, GREY = (0.1, 0.7, 0.2, 1.0), (0.5, 0.5, 0.5, 1.0)
WIN = 100                       # takty okna pomiaru po włączeniu bodźca (1 s)


class ShufVisJaw(vm.VisJaw):
    """VisJaw z przetasowanym blokiem wzrok → noga (block_shuffle 'LC2MID' przy etykietach: wzrok = 'in', noga = 'mid')."""

    def __init__(self, fc, seed, **kw):
        super().__init__(fc, **kw)
        spec, _, _ = vm.union_spec(fc)
        L = self.rep["leg"]
        groups = ["mid_leg"] * L + ["in_vis"] * (spec.W.shape[0] - L)
        sh = block_shuffle(spec, groups, seed, "LC2MID")
        self.shuf_rep = sh.report["block_shuffle"]
        self.spec = sh.W
        self.shuf_sha = hashlib.sha256(np.ascontiguousarray(sh.W).tobytes()).hexdigest()
        self.reset()


class ConflictGrip(sm.FlyGrip):
    def __init__(self, world, cfg, driver, src, fc, stim, colors="native"):
        super().__init__(world, cfg, driver, src, fc)
        import mujoco
        self.mj = mujoco
        m = self.sim.m
        rgba0 = m.geom_rgba.copy()
        self.eye = vm.Eye(world)
        if colors == "native":          # pilot 1: zielone przedmioty nasycały enkoder (g≈1 po obu stronach) → kolory materiałów
            for o in world.objs:
                sl = slice(m.body_geomadr[o["bid"]], m.body_geomadr[o["bid"]] + m.body_geomnum[o["bid"]])
                m.geom_rgba[sl] = rgba0[sl]
        self.bg = m.geom("ball").id
        m.geom_contype[self.bg] = m.geom_conaffinity[self.bg] = 0           # bodziec bez fizyki kontaktu
        m.geom_rgba[self.bg] = GREEN if stim == "on" else GREY
        self.bq = int(m.jnt_qposadr[m.joint("ball").id])
        self.bv = int(m.jnt_dofadr[m.joint("ball").id])
        self.cam = m.camera("eye").id
        self.park = m.qpos0[self.bq:self.bq + 7].copy()
        self.win, self.wins, self.on = None, [], False
        self.own_px = int(self.eye.own.sum())

    def _place(self, active):
        d = self.sim.d
        if active:
            p = d.cam_xpos[self.cam] + d.cam_xmat[self.cam].reshape(3, 3) @ np.array(OFFSET)
            d.qpos[self.bq:self.bq + 7] = [*p, 1, 0, 0, 0]
        else:
            d.qpos[self.bq:self.bq + 7] = self.park
        d.qvel[self.bv:self.bv + 6] = 0
        self.mj.mj_kinematics(self.sim.m, d)

    def tick(self, tgt, mode):
        active = self.w.phase in ("lift", "transport")
        if active and not self.on:                                  # początek okna
            self.win = dict(t0=self.obs.t, tau=[], g=[], dn=[], n_px=[])
            self.wins.append(self.win)
        self.on = active
        self._place(active)
        _, e = self.eye.see()
        self.driver.g = e["g"]                                      # wzrok zawsze włączony (bez bramkowania)
        super().tick(tgt, mode)
        if active and len(self.win["tau"]) < WIN:
            self.win["tau"].append(self.tau_fly)
            self.win["g"].append(e["g"].tolist())
            self.win["n_px"].append(e["n_px"])
            self.win["dn"].append(self.driver.dn.tolist())


def summarize_win(w):
    if not w or not w["tau"]:
        return None
    return dict(n=len(w["tau"]), tau_mean=round(float(np.mean(w["tau"])), 4), tau_min=round(float(np.min(w["tau"])), 4),
                g_mean=np.round(np.mean(w["g"], 0), 4).tolist(), dn_mean=np.round(np.mean(w["dn"], 0), 2).tolist(),
                n_px_mean=round(float(np.mean(w["n_px"])), 1))


def run_trial(item, seed, drv, fc, stim, noise_seed, colors="native"):
    made, orig = [], oh.Controller
    drv.reset(noise_seed)
    oh.Controller = lambda w, cfg: made.append(ConflictGrip(w, cfg, drv, "snn:vis+legT2L", fc, stim, colors)) or made[0]
    try:
        r = oh.run([item], seed)
    finally:
        oh.Controller = orig
        for x in made:
            x.eye.close()
    o, c = r["objects"][0], made[0]
    return dict(item="/".join(item), seed=seed, noise_seed=noise_seed, truth=o["truth"], success=o["success"],
                reasons=[x["reason"] for x in o["attempt_log"] if not x["ok"]], attempts=o["attempts"],
                win_first=summarize_win(c.wins[0] if c.wins else None), n_windows=len(c.wins),
                windows=[summarize_win(w) for w in c.wins], own_px=c.own_px, complete=r["complete"],
                stopped_by=r["stopped_by"], T_sim=round(r["T_sim"], 3), T_wall=round(r["T_wall"], 2),
                safety_stats=r["safety_stats"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=("N", "S"))
    ap.add_argument("--shuffle-seed", type=int)
    ap.add_argument("--glu", type=float, required=True)
    ap.add_argument("--stim", required=True, choices=("on", "sham"))
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--poses", type=int, default=1)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--colors", default="native", choices=("native", "green"))
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.seed in TEST_SEEDS and not os.environ.get("STEP2_FINAL_TEST"):
        sys.exit("ziarna testowe tylko w teście końcowym (STEP2_FINAL_TEST=1)")
    if a.seed not in NOISE0:
        sys.exit("ziarno spoza rejestru kroku 7")
    if (a.arm == "S") != (a.shuffle_seed is not None):
        sys.exit("--shuffle-seed wymagane dokładnie dla S")
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, a.tag + ".json")
    if os.path.exists(path):
        sys.exit(f"istnieje {path}")
    fc = sm.FlyCfg(glu_sign=a.glu, trigger="search")
    w0 = time.perf_counter()
    drv = vm.VisJaw(fc) if a.arm == "N" else ShufVisJaw(fc, a.shuffle_seed)
    build_s = time.perf_counter() - w0
    items, runs, t = oh.SETS["base"], [], 0
    for it in [x for x in items if not a.only or "/".join(x) in a.only]:
        for k in range(a.poses):
            r = run_trial(it, a.seed * 1000 + items.index(it) * 10 + k, drv, fc, a.stim, NOISE0[a.seed] + t, a.colors)
            t += 1
            runs.append(r)
            print(f"{r['item']:22s} {k}: grasp {r['truth']['grasp']!s:5} lift {r['truth']['lift']!s:5} placed {r['success']!s:5} "
                  f"{r['reasons']} win {r['win_first']}", flush=True)
    out = dict(tag=a.tag, arm=a.arm, glu=a.glu, stim=a.stim, shuffle_seed=a.shuffle_seed, seed=a.seed, poses=a.poses,
               offset=OFFSET, win_ticks=WIN, colors=a.colors, fly_cfg=asdict(fc), argv=sys.argv, build_s=round(build_s, 1),
               net=dict(drv.rep, W_sha256=hashlib.sha256(np.ascontiguousarray(drv.spec).tobytes()).hexdigest(),
                        shuffle=getattr(drv, "shuf_rep", None)),
               wall_s=round(time.perf_counter() - w0, 1),
               max_rss_MB=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20, 1),
               code_sha256={f: hashlib.sha256(open(p, "rb").read()).hexdigest() for f, p in
                            (("conflict_test.py", __file__), ("vision_manipulation.py", vm.__file__),
                             ("sensory_manipulation.py", sm.__file__), ("object_handling.py", oh.__file__))},
               runs=runs)
    with open(path, "x") as f:
        json.dump(out, f, indent=1, default=float)
    print("zapisano", path)


if __name__ == "__main__":
    main()
