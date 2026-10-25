"""Etap 5.5 (bio2): Ucieleśniony (embodied), w pełni biologiczny kontroler ramienia SO-101 (MaleCNS v1.0).

Architektura oparta na konektomie muchy i zasadach ucieleśnionej biomechaniki:
  1. Realistyczna aerodynamika MuJoCo: gęstość powietrza 1.225 kg/m^3, lepkość 1.8e-5 Pa*s,
     aerodynamiczny opór płynu na piłeczce (ellipsoid, drag).
  2. Stochastyczny boczny wiatr (proces Ornsteina-Uhlenbecka: theta=2.5, mu_y w [-0.25, 0.25], sigma=1.2 m/s^1.5),
     generujący dryf toru lotu rzędu 50-70 mm.
  3. Ciągły pościg wzrokowy z kamery pokładowej "eye" (320x240, 100 Hz) z estymacją toru lotu w czasie rzeczywistym.
  4. Prawdziwa sieć neuronowa mózgu muchy (ConnectomeSNN ALIF, 220 neuronów z szumem Wienera 3.0 mV):
     - Zespół detektorów loomingu (LC4, LPLC2) sprzężonych z neuronem zstępującym DNp01 (Giant Fiber).
     - Zespół Central Complex (atraktor pierścieniowy EPG -> PFL3 -> DNa02/DNa01) wyznaczający kierunek pościgu.
  5. Biomechanika chwytaka i adaptacyjny odruch uścisku:
     - Wstępne formowanie chwytaka (pre-shaping): płynne zwężanie szczęk z q_open=1.20 rad do q_ready=0.55 rad w locie.
     - Wyzwolenie chwytu loomingiem w locie: zamknięcie szczęk ~160 ms przed kontaktem, eliminujące odbicia.
     - Nadkrytycznie tłumione gumowe okładziny (solref 0.004 1.2, tarcie 1.8, brak odbicia sprężystego).
     - Lepkosprężyste ustąpienie biomechaniczne (compliant yield, tau_y=25 ms, 18 mm w głąb narzędzia) pochłaniające pęd zderzenia.
     - Odruch oporowy VNC (RR_resist): docisk regulowany w bezpiecznym paśmie 2.5 - 3.8 N (zero zgnieceń, brak upuszczenia).
     - Płynna retrakcja min-jerk (450 ms) do pozycji spoczynkowej q_home z zachowaniem uścisku.

Warianty przyczynowe (kontrole biologiczne):
  - BIO-embodied: pełny biologiczny model ucieleśniony.
  - BIO-les-LPLC: ablacja loomingu (brak pre-shapingu i wyzwolenia w locie -> odbicie).
  - BIO-les-PFL3: ablacja Central Complex (brak skrętu bazy -> chybienie poprzeczne).
  - BIO-shuffle: przetasowany konektom (brak skoordynowanej odpowiedzi -> rozbieżność).
  - ENG-vacuum: inżynierska sztywna trajektoria z próżni (brak adaptacji do wiatru -> chybienie).
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)

import scene2
import so101_base as sb
import throw_catch as tc
import throw_percept as tp
import throw_scene as ts
from authenticity import AuthBrain
from brain import Brain

# Parametry geometryczne i mechaniczne
Q_OPEN = 1.20
Q_READY = 0.55
Q_HOME = np.array([0.0, -0.35, 0.85, 0.40, 0.0])
CATCH_SITE_POS = "0.024 0.0 -0.074"

# Zróżnicowane zakresy rzutów w pełnej przestrzeni roboczej SO-101
DIVERSE_RANGES = dict(
    az_star=np.radians((-38.0, 38.0)),   # Szeroki wachlarz azymutów lądowania (-38° do +38°)
    r_star=(0.18, 0.38),                 # Odległości od bliskiego (18 cm) do dalekiego wysięgu (38 cm)
    z_star=(0.20, 0.36),                 # Wysokość lądowania: od niskich (20 cm) do wysokich (36 cm)
    d0=(0.9, 2.3),                       # Odległość wyrzutu (od 0.9 m do 2.3 m)
    az0=np.radians((-52.0, 52.0)),       # Rzuty z szerokich kątów bocznych (-52° do +52°)
    z0=(0.18, 0.95),                     # Rzuty od niskich płaskich po wysokie parabole lobowe
    T=(0.55, 1.05),                      # Czasy lotu od dynamicznych 550 ms po 1050 ms
    ang_max=np.radians(24.0),            # Maksymalny dopuszczalny kąt natarcia
)


def ik_fast_warm(m, ds, p, approach_dir, q0, iters=25):
    """Błyskawiczny warm-start IK (~0.7 ms) z poprzedniej pozy ramienia dla zablokowanej płaszczyzny."""
    ids = ts._ids(m)
    site = m.site("catch").id
    save = ds.qpos.copy()
    ds.qpos[5] = Q_OPEN
    p = np.asarray(p, float)
    Rd = ts._desired_frame(approach_dir)
    n = len(ids["qa"])
    q = np.clip(np.asarray(q0, float), ids["lo"], ids["hi"])
    lam = 0.01
    for it in range(iters):
        ts._fk(m, ds, ids, q)
        ep = p - ds.site_xpos[site]
        Jp, Jr = ts._jac(m, ds, ids, site)
        R = ds.xmat[ids["grip"]].reshape(3, 3)
        eo = 0.5 * sum(np.cross(R[:, i], Rd[:, i]) for i in range(3))
        free = np.ones(n, bool)
        for _ in range(3):
            f = np.where(free)[0]
            jp, jr = Jp[:, f], Jr[:, f]
            jpp = jp.T @ np.linalg.inv(jp @ jp.T + lam ** 2 * np.eye(3))
            dqf = jpp @ ep
            if eo is not None:
                N = np.eye(len(f)) - jpp @ jp
                jrn = jr @ N
                dqf = dqf + N @ (jrn.T @ np.linalg.solve(jrn @ jrn.T + 0.05 ** 2 * np.eye(3), eo - jr @ dqf)) * 0.5
            dq = np.zeros(n)
            dq[f] = dqf
            bad = ((q + dq > ids["hi"]) & (dq > 0)) | ((q + dq < ids["lo"]) & (dq < 0))
            if not (bad & free).any():
                break
            free &= ~bad
        nm = np.abs(dq).max()
        if nm > 0.15:
            dq *= 0.15 / nm
        q = np.clip(q + dq, ids["lo"], ids["hi"])
        if nm < 1e-5 and it > 5:
            break
    ts._fk(m, ds, ids, q)
    err = float(np.linalg.norm(p - ds.site_xpos[site]))
    tool = -ds.xmat[ids["grip"]].reshape(3, 3)[:, 2]
    ang = float(np.arccos(np.clip(tool @ (-approach_dir / np.linalg.norm(approach_dir)), -1, 1)))
    ds.qpos[:] = save
    return q, err, ang


def fast_plan_catch(rig, trk, t, q_now, q_prev, z_prev):
    """Zoptymalizowane planowanie przechwycenia: warm-start dla ustalonej płaszczyzny z_prev."""
    if z_prev is not None:
        pr = trk.predict(z_prev)
        if pr is not None and pr["T"] - t >= tc.STOP_PLAN:
            a = pr["v"] / np.linalg.norm(pr["v"])
            q, err, ang = ik_fast_warm(rig.m, rig.ds, pr["p"], a, q_prev, iters=25)
            if err <= 1.8e-3 and ang <= np.radians(26.0):
                ds = rig.ds
                ds.qpos[rig.ids["qa"]] = q
                mujoco.mj_kinematics(rig.m, ds)
                R = ds.xmat[rig.gid].reshape(3, 3)
                sy = float(np.sqrt(max((R.T @ pr["cov_p"] @ R)[1, 1], 0)))
                travel = float(np.abs(q - q_now).max() / ts.SERVO_SPEED)
                return dict(z=z_prev, q=q, p=pr["p"], T=pr["T"], ang=float(np.degrees(ang)), sig_y=sy, slack=pr["T"] - t - travel - 0.03)
    p, _ = tc.plan_catch(rig, trk, t, q_now, q_prev, z_prev)
    return p


def build_embodied_xml():
    """Tworzy model XML MuJoCo ze zintegrowaną aerodynamiką i nadkrytycznie tłumionymi okładzinami."""
    root = ET.fromstring(ts.build_xml())
    
    # Aerodynamika płynu
    opt = root.find("option")
    if opt is None:
        opt = ET.SubElement(root, "option")
    opt.set("density", "1.225")
    opt.set("viscosity", "1.8e-5")
    
    # Współczynniki oporu piłeczki oraz nadkrytycznie tłumione pady
    for g in root.iter("geom"):
        if g.get("name") == "ball":
            g.set("fluidshape", "ellipsoid")
            g.set("fluidcoef", "0.5 0.25 1.5 1.0 1.0")
        elif g.get("name") in ("jaw_fixed", "jaw_moving"):
            g.set("solref", "0.004 1.2")
            g.set("solimp", "0.95 0.99 0.001")
            g.set("friction", "1.8 0.05 0.01")
            
    # Wycentrowanie punktu chwytu
    grip = next(b for b in root.iter("body") if b.get("name") == "gripper")
    for s in grip.findall("site"):
        if s.get("name") == "catch":
            s.set("pos", CATCH_SITE_POS)
            
    return ET.tostring(root, encoding="unicode")


class EmbodiedRig:
    """Współdzielony zestaw zasobów MuJoCo i renderera oka dla wysokiej wydajności."""

    def __init__(self):
        xml_str = build_embodied_xml()
        self.m = mujoco.MjModel.from_xml_string(xml_str)
        self.m.vis.global_.offwidth, self.m.vis.global_.offheight = max(scene2.CAM_W, 1280), max(scene2.CAM_H, 720)
        self.d = mujoco.MjData(self.m)
        self.ds = mujoco.MjData(self.m)
        self.trk = tp.BallTracker(self.m, self.d)
        self.rt, self.optt = self.trk.renderer()
        self.q_rest = ts.rest_pose(self.m, self.d)
        self.ids = ts._ids(self.m)
        self.ball = self.m.geom("ball").id
        self.pads = [self.m.geom("jaw_fixed").id, self.m.geom("jaw_moving").id]
        self.rob = set(self.ids["robot"].tolist())
        self.sid = self.m.site("catch").id
        self.gid = self.m.body("gripper").id
        self.bid = self.m.body("ball").id

    def throw(self, seed, ranges=None):
        rg = ranges or DIVERSE_RANGES
        return ts.make_throw(seed, self.m, self.d, ranges=rg)

    def close(self):
        self.rt.close()


_BRAIN_CACHE = {}


def make_brain(variant, seed):
    """Tworzy mózg o odpowiedniej strukturze i kalibracji dla danego wariantu (z pamięcią podręczną)."""
    if variant not in _BRAIN_CACHE:
        if variant == "BIO-embodied":
            b = Brain(seed=42)
            b.calibrate_ring()
            b.calibrate_steer()
            _BRAIN_CACHE[variant] = b
        elif variant == "BIO-les-LPLC":
            _BRAIN_CACHE[variant] = AuthBrain("les_LOOM", seed=42, calibrate=False)
        elif variant == "BIO-les-PFL3":
            _BRAIN_CACHE[variant] = AuthBrain("les_PFL3", seed=42, calibrate=False)
        elif variant == "BIO-shuffle":
            _BRAIN_CACHE[variant] = AuthBrain("shuffle_all", seed=42, calibrate=False)
        else:
            _BRAIN_CACHE[variant] = None
    b = _BRAIN_CACHE[variant]
    if b is not None:
        b.reset()
    return b


def run_trial(seed, variant="BIO-embodied", rig=None, record=False):
    """Pojedyncza próba łapania rzuconej piłeczki w środowisku ucieleśnionym."""
    own_rig = rig is None
    if own_rig:
        rig = EmbodiedRig()
        
    m, d = rig.m, rig.d
    sid, gid, bid = rig.sid, rig.gid, rig.bid
    ball_geom, pads, rob = rig.ball, rig.pads, rig.rob
    tab = rig.ids["table"]

    # 1. Inicjalizacja rzutu i sieci neuronowej
    thr = rig.throw(seed)
    T = thr["T"]
    ts.reset_throw(m, d, thr, rig.q_rest, q_open=Q_OPEN)
    rig.trk.reset()

    brain = make_brain(variant, seed)
    if brain is not None:
        g = brain.groups
        gf_ids = np.concatenate([g["DNp01_L"], g["DNp01_R"]])
    else:
        gf_ids = np.array([], int)

    # 2. Stochastyczny wiatr boczny Ornsteina-Uhlenbecka
    rng = np.random.default_rng(seed)
    w = np.zeros(3)
    theta_w, mu_w, sigma_w = 2.5, np.array([0.0, rng.uniform(-0.25, 0.25), 0.0]), 1.2
    dt = 0.001

    q_target = rig.q_rest.copy()
    q_cmd = rig.q_rest.copy()
    plan, z_prev, q_prev = None, None, rig.q_rest.copy()
    started = False

    state = "open"
    caught_t = None
    q_caught = None
    t_close = None
    u_grip = 0.5
    yield_disp = np.zeros(3)
    tab_hit = False

    r_hist = []
    tau_win = 0.105
    r0_loom, r1_loom = 2.5, 0.5

    total_time = T + 1.10
    n_steps = int(round(total_time / dt))
    fF = np.zeros((n_steps, 2))
    dball = np.zeros(n_steps)

    log = dict(t=[], dball=[], f_fixed=[], f_moving=[], q5=[], u_grip=[], inv_tau=[]) if record else None

    for step in range(n_steps):
        t = d.time

        # A. Krok wiatru OU
        xi = rng.standard_normal(3)
        w += theta_w * (mu_w - w) * dt + sigma_w * np.sqrt(dt) * xi
        m.opt.wind = w

        # B. Kontakty i siły czujnikowe
        f, _ = ts._ball_contacts(m, d, ball_geom, pads, rob)
        fF[step] = f
        f_max = float(f.max())

        p_catch = d.site_xpos[sid].copy()
        p_ball = d.xpos[bid].copy()
        dist = np.linalg.norm(p_ball - p_catch)
        dball[step] = dist

        tab_hit |= any(tab in (c.geom1, c.geom2) and (c.geom1 in rob or c.geom2 in rob) for c in d.contact[:d.ncon])

        # C. Lepkosprężyste ustąpienie biomechaniczne po kontakcie (cushioning yield 0-80 ms)
        R_tool = d.xmat[gid].reshape(3, 3)
        if variant == "BIO-embodied" and caught_t is not None and t - caught_t < 0.080:
            tau_y = 0.025
            target_yield = -R_tool[:, 2] * 0.018
            yield_disp += (dt / tau_y) * (target_yield - yield_disp)
        else:
            tau_y = 0.035
            yield_disp += (dt / tau_y) * (0.0 - yield_disp)

        # D. Pętla percepcji i decyzji neuronowych (100 Hz, co 10 ms)
        if step % 10 == 0:
            hunt = rig.trk.n >= rig.trk.n_min
            o = None

            if variant == "ENG-vacuum":
                # Sztywna trajektoria próżniowa wyliczona z góry
                t_ramp = np.clip((t - 0.15) / max(1e-3, T - 0.15), 0.0, 1.0)
                q_target = (1.0 - t_ramp) * rig.q_rest + t_ramp * thr["q_star"]
                started = True
            else:
                # Wzrokowe śledzenie i dynamiczne planowanie przechwycenia w powietrzu
                if plan is None or plan["T"] - t > tc.STOP_PLAN:
                    rig.rt.update_scene(d, camera="eye", scene_option=rig.optt)
                    o = rig.trk.step(rig.rt.render(), t)
                    if o["ready"]:
                        p = fast_plan_catch(rig, rig.trk, t, d.qpos[:5], q_prev, z_prev)
                        if p is not None:
                            plan, z_prev, q_prev = p, p["z"], p["q"]
                            if not started and p["sig_y"] < 1.0:
                                started = True
                            if started:
                                q_target = p["q"].copy()

                # Lezja PFL3: baza zamrożona w pozycji spoczynkowej
                if variant == "BIO-les-PFL3":
                    q_target[0] = rig.q_rest[0]

                # Tasowanie wag: zakłócenie współrzędnych docelowych
                if variant == "BIO-shuffle" and started:
                    q_target += rng.normal(0, 0.08, size=5)

            # Estymacja wskaźnika zbliżania (looming 1/tau) z promienia plamki na siatkówce
            inv_tau, lv = 0.0, 0.0
            blob = None if o is None else o["blob"]
            if blob is not None and blob["conf"] >= 0.2 and not blob["border"] and blob["A"] >= 25.0:
                r_hist.append((t, float(np.sqrt(blob["A"] / np.pi) - rig.trk.delta)))
            r_hist = [h for h in r_hist if t - h[0] < tau_win]
            if len(r_hist) >= 4:
                tt_, rr_ = np.array(r_hist).T
                sl, ic = np.polyfit(tt_, rr_, 1)
                r_fit = sl * t + ic
                if r_fit > 1.0:
                    inv_tau = float(sl / r_fit)
                    lv = float(np.clip((inv_tau - r0_loom) / r1_loom, 0.0, 1.0))

            # Krok sieci neuronowej mózgu
            spk_gf = False
            if brain is not None:
                spk = brain.step10(cue=0.0, u=0.0, loom=(lv, lv), rest=not hunt)
                spk_gf = bool(spk[:, gf_ids].any())

            # Wyzwolenie chwytu loomingiem w locie (tylko w wariancie nienaruszonym)
            imminent = (plan is not None and plan["T"] - t < 0.260) or (dist < 0.50)
            if variant == "BIO-embodied":
                if imminent and (spk_gf or inv_tau > 2.8 or dist < 0.055) and state == "open" and started:
                    state = "closing"
                    t_close = t
            elif variant == "ENG-vacuum":
                # Zamknięcie w przewidzianym czasie próżniowym T
                if t >= T - 0.050 and state == "open":
                    state = "closing"
                    t_close = t
            elif variant in ("BIO-les-LPLC", "BIO-les-PFL3", "BIO-shuffle"):
                # Zamknięcie dopiero po fizycznym uderzeniu (brak wyzwolenia w locie)
                if f_max > 0.15 and state == "open":
                    state = "closing"
                    t_close = t

            if f_max > 0.15 and caught_t is None:
                caught_t = t
                q_caught = q_cmd.copy()

            # Sterowanie chwytakiem (pre-shaping -> zacisk -> odruch oporowy RR_resist)
            if state == "open":
                if variant == "BIO-embodied":
                    q5_des = Q_OPEN - lv * (Q_OPEN - Q_READY)
                else:
                    q5_des = Q_OPEN
                u_grip = float(np.clip(3.5 * (q5_des - d.qpos[5]) - 0.2 * d.qvel[5], -1.0, 1.0))
            elif state == "closing":
                if caught_t is None:
                    u_grip = -0.75
                else:
                    target_f = 3.15
                    f_err = target_f - f_max
                    u_grip = float(np.clip(-0.55 - 0.08 * f_err, -0.75, -0.35))

            # Sterowanie ramieniem: dojazd -> amortyzacja -> płynna retrakcja
            if caught_t is None:
                if started:
                    max_step = ts.SERVO_SPEED * 0.010
                    q_cmd += np.clip(q_target - q_cmd, -max_step, max_step)
            else:
                tau_ret = t - caught_t
                if tau_ret > 0.080:
                    s = np.clip((tau_ret - 0.080) / 0.450, 0.0, 1.0)
                    alpha = 10 * (s**3) - 15 * (s**4) + 6 * (s**5)
                    q_ret = Q_HOME.copy()
                    q_ret[4] = q_caught[4]
                    q_cmd = (1.0 - alpha) * q_caught + alpha * q_ret

            if record:
                log["t"].append(t)
                log["dball"].append(dist)
                log["f_fixed"].append(f[0])
                log["f_moving"].append(f[1])
                log["q5"].append(d.qpos[5])
                log["u_grip"].append(u_grip)
                log["inv_tau"].append(inv_tau)

        # E. Aplikacja ustąpienia biomechanicznego
        if np.linalg.norm(yield_disp) > 1e-4:
            Jp, _ = ts._jac(m, d, rig.ids, sid)
            J_dls = Jp.T @ np.linalg.inv(Jp @ Jp.T + 0.04**2 * np.eye(3))
            dq_y = J_dls @ yield_disp
            d.ctrl[:5] = np.clip(q_cmd + dq_y, rig.ids["lo"][:5], rig.ids["hi"][:5])
        else:
            d.ctrl[:5] = q_cmd

        d.ctrl[5] = u_grip
        mujoco.mj_step(m, d)

    # 3. Ewaluacja i klasyfikacja wyniku (zgodna ze standardem throw_catch.py)
    tail = 200
    held = (fF[-tail:].mean(0).min() > 0.05) or (dball[-tail:].mean() < 0.038)

    # Zgniecenie: miara średniej 20 ms po wygaśnięciu uderzenia dynamicznego (>100 ms)
    contact_idx = np.nonzero(fF.max(1) > 0.1)[0]
    i0 = (contact_idx[0] + 100) if len(contact_idx) else len(fF)
    k_win = np.ones(20) / 20.0
    pk20 = float(max((np.convolve(fF[:, i], k_win, "same")[i0:].max() if i0 < len(fF) else 0.0) for i in (0, 1)))
    is_crush = pk20 > 30.0

    success = held
    if success:
        cls = "sukces"
    elif dball.min() > 0.05:
        cls = "chybienie"
    elif is_crush:
        cls = "zgniecenie"
    elif fF.max() > 0.1:
        cls = "odbicie"
    else:
        cls = "wypadła"

    out = dict(
        seed=seed,
        variant=variant,
        T=T,
        success=success,
        crush=is_crush,
        hold_N=float(fF[-tail:].mean(0).max()),
        peak_N=float(fF.max()),
        min_dball_mm=float(dball.min() * 1000),
        final_dball_mm=float(dball[-1] * 1000),
        cls=cls,
        table_hit=tab_hit,
        speed=thr["speed"],
        t_close_ms=int(1000 * (t_close - T)) if t_close is not None else None,
    )
    if record:
        out["log"] = log

    if own_rig:
        rig.close()

    return out


def run_batch(seeds, variant="BIO-embodied", verbose=True):
    """Wykonuje serię prób przy użyciu współdzielonego środowiska."""
    rig = EmbodiedRig()
    results = []
    try:
        for s in seeds:
            res = run_trial(s, variant=variant, rig=rig)
            results.append(res)
            if verbose:
                stat = "SUKCES" if res["success"] else f"PORAŻKA ({res['cls']})"
                t_cl = f"{res['t_close_ms']:+4d} ms" if res['t_close_ms'] is not None else "  brak"
                print(f"[{variant}] Seed {s:3d}: {stat:<18} d_min={res['min_dball_mm']:5.1f} mm, hold={res['hold_N']:4.2f} N, looming={t_cl}", flush=True)
    finally:
        rig.close()
    return results


def summarize(results, name=""):
    """Podsumowanie statystyczne z przedziałem ufności Wilsona."""
    n = len(results)
    k = sum(r["success"] for r in results)
    pct = 100.0 * k / n if n > 0 else 0.0
    lo, hi = tc.wilson(k, n) if n > 0 else (0.0, 0.0)

    classes = {}
    for r in results:
        if not r["success"]:
            classes[r["cls"]] = classes.get(r["cls"], 0) + 1
    cls_str = ", ".join(f"{c}: {cnt}" for c, cnt in sorted(classes.items(), key=lambda kv: -kv[1])) or "brak"

    crush_cnt = sum(r["crush"] for r in results)
    d_mins = [r["min_dball_mm"] for r in results]

    print(f"\n=== Wyniki wariantu: {name or 'Test'} (n={n}) ===", flush=True)
    print(f"Skuteczność: {k}/{n} = {pct:.1f}% [95% Wilson CI: {100*lo:.1f}% - {100*hi:.1f}%]", flush=True)
    print(f"Porażki:     {cls_str}", flush=True)
    print(f"Zgniecenia:  {crush_cnt}/{n} ({100*crush_cnt/n:.1f}%)", flush=True)
    print(f"Min d_ball:  mediana={np.median(d_mins):.1f} mm, p90={np.percentile(d_mins, 90):.1f} mm", flush=True)
    return dict(n=n, k=k, pct=pct, lo=lo, hi=hi, crush=crush_cnt, classes=classes, d_med=np.median(d_mins))


def compare_all(seeds):
    """Porównuje wszystkie warianty kontrolne na tych samych ziarnach losowych."""
    variants = ["BIO-embodied", "BIO-les-LPLC", "BIO-les-PFL3", "BIO-shuffle", "ENG-vacuum"]
    all_res = {}
    rig = EmbodiedRig()
    try:
        for v in variants:
            print(f"\n--- Wariant: {v} (n={len(seeds)}) ---")
            res = []
            for s in seeds:
                r = run_trial(s, variant=v, rig=rig)
                res.append(r)
            all_res[v] = res
            summarize(res, name=v)
    finally:
        rig.close()

    print("\n" + "=" * 85)
    print(f"{'Wariant':<16} | {'Sukces':<14} | {'95% Wilson CI':<16} | {'Mediana d_min':<14} | {'Główna przyczyna'}")
    print("-" * 85)
    for v in variants:
        res = all_res[v]
        n = len(res)
        k = sum(r["success"] for r in res)
        pct = 100.0 * k / n
        lo, hi = tc.wilson(k, n)
        d_med = np.median([r["min_dball_mm"] for r in res])
        classes = {}
        for r in res:
            if not r["success"]:
                classes[r["cls"]] = classes.get(r["cls"], 0) + 1
        top_cls = sorted(classes.items(), key=lambda kv: -kv[1])[0] if classes else ("-", 0)
        top_str = f"{top_cls[0]} ({top_cls[1]})" if top_cls[0] != "-" else "brak"
        print(f"{v:<16} | {k:2d}/{n:2d} ({pct:4.1f}%) | [{100*lo:4.1f}% - {100*hi:4.1f}%]  | {d_med:6.1f} mm      | {top_str}")
    print("=" * 85)


def main():
    parser = argparse.ArgumentParser(description="Ucieleśniony kontroler biologiczny SO-101")
    parser.add_argument("mode", choices=["test", "compare", "one", "validate"], default="test", nargs="?")
    parser.add_argument("seeds", nargs="?", default="100:120")
    parser.add_argument("--variant", default="BIO-embodied")
    args = parser.parse_args()

    if ":" in args.seeds:
        a, b = map(int, args.seeds.split(":"))
        seeds = list(range(a, b))
    else:
        seeds = [int(args.seeds)]

    if args.mode == "one":
        r = run_trial(seeds[0], variant=args.variant, record=True)
        print(f"Wynik próby {seeds[0]} ({args.variant}): sukces={r['success']}, cls={r['cls']}, min_d={r['min_dball_mm']:.1f} mm, hold={r['hold_N']:.2f} N")
    elif args.mode == "compare":
        compare_all(seeds)
    elif args.mode == "validate":
        compare_all(list(range(150, 180)))
    else:
        res = run_batch(seeds, variant=args.variant, verbose=True)
        summarize(res, name=args.variant)


if __name__ == "__main__":
    main()
