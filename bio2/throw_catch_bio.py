"""Etap 5b (bio2): REALNA rola mózgu muchy w łapaniu rzuconej piłeczki — i test, czy jest realna (kontrole przyczynowości).

Dwie role (reszta — tracker 320×240, predykcja toru, IK, serwa — to inżynieria z throw_catch.py, bez zmian):
  τ   (warunek B: szczęki szeroko 1,2 rad, zamknięcie potrzebuje ~200 ms): CHWILĘ ZAMKNIĘCIA wyznacza looming 1/τ = θ̇/θ plamki piłeczki
      w obrazie 320×240 (kąt θ z promienia plamki w pikselach, bez trackera 3D; θ̇ z regresji po 5 klatkach) → wejście loom do
      LC4/LPLC2 (Brain.step10; MODEL: przetwarzanie 1/τ poza obwodem, rozdzielczość robota, nie siatkówka 32×24) → LPLC2 → (krawędzie konektomu
      LPLC2→DNp01) → odczyt: spike DNp01 („DN”) albo populacja LPLC2 ≥ próg („LP”) → „zamknij”. Zamknięcie wychodzi z impulsów neuronów, nie z T_pred.
  yaw SKRĘT BAZY: azymut p_pred (przewidywanego punktu przechwycenia) względem paszczy (jak w agent.py) → cue do EPG → PFL3 → DNa02/DNa01 →
      ω bazy dekoderem z agent.py (G_TURN, W_MAX, trym i nachylenie z calibrate_steer, bramka „zatrzaśnięte” LOCK); pozostałe 4 stawy liczy IK
      do p_pred przy kącie bazy narzuconym przez mózg (IK z zablokowanym stawem 0, rolka pochłania do ~6° błędu). Decyzja: cel PRZYSZŁY (azymut
      p_pred), nie bieżący azymut piłeczki — piłeczka zmienia azymut względem osi bazy w locie, a chwytak ma być tam, gdzie piłeczka BĘDZIE.
Warianty (nazwy w VARIANTS), kontrole: te same z mózgiem uszkodzonym jak w authenticity.py (rewire_all, shuffle_all, shuffle_cx, les_LOOM, les_PFL3).
Miary jak w throw_catch.py (sukces = trzymana 1 s). Dodatkowo: chwila zamknięcia względem prawdziwego T, 1. spike DNp01, błąd azymutu bazy
względem planu IK (wolny staw 0) w T − 30 ms.

Użycie (z bio2):  python throw_catch_bio.py grid WARIANT a:b TAG [klucz=wart,wart ...] | validate a:b | report a:b | predictions-check
"""
import os
import sys
import time

import mujoco
import numpy as np

import scene2
import so101_base as sb
import throw_scene as ts
import throw_catch as tc
import throw_percept as tp
from authenticity import AuthBrain
from vnc import vnc_controller

HERE = os.path.dirname(os.path.abspath(__file__))
G_TURN0, W_MAX, WINDUP = 2.5, 1.0, 0.02          # agent.py
TAU_DNA02, TAU_DNA01 = 0.10, 0.40                # agent.py
LOCK = np.radians(20)                            # agent.py

P0 = dict(
    tc.P0,
    r0=2.5,              # 1/s: MODEL: 1/τ, od którego rośnie wejście loom (rozjazd ≈ moment zamknięcia)
    r1=0.5,              # 1/s: MODEL: szerokość rampy wejścia (loom = 1 przy r0 + r1)
    tau_win=0.105,       # s: MODEL: okno regresji θ̇ (dłuższe = mniej szumu, większe opóźnienie)
    a_min=25.0,          # px: min. pole plamki do liczenia θ̇/θ
    lp_thr=60.0,         # Hz: MODEL: próg populacji LPLC2 (24 neurony, okno 10 ms) dla odczytu „LP”
    g_turn=G_TURN0,      # 1/s: MODEL (dekoder): ω = g_turn · kąt z DN
    sig_y_start=1.0, lead=0.03,
)

# nazwa → konfiguracja. yaw: 'ik' (IK wolny staw 0 = ENG), 'frozen' (staw 0 zamrożony), 'brain'; close: 'tpred' | 'tau_dn' | 'tau_lp'
VARIANTS = {
    "ENG": dict(yaw="ik", close="tpred", hold="pwm", escape=None, struct="control"),
    "NO-YAW": dict(yaw="frozen", close="tpred", hold="pwm", escape=None, struct="control"),
    "BIO-yaw": dict(yaw="brain", close="tpred", hold="pwm", escape=None, struct="control"),
    "BIO-τ(DN)": dict(yaw="ik", close="tau_dn", hold="pwm", escape="gated", struct="control"),
    "BIO-τ(LP)": dict(yaw="ik", close="tau_lp", hold="pwm", escape="gated", struct="control"),
    "BIO-τ-ucieczka": dict(yaw="ik", close="tau_dn", hold="pwm", escape="free", struct="control"),
    "BIO-full": dict(yaw="brain", close="tau_dn", hold="vnc", escape="gated", struct="control"),
}
WIDE = dict(q_open=1.2, lead=0.2)


def _ik_fixed(m, d, p, approach_dir, q_pan, q0, site="catch", iters=60, lam=0.01):
    """IK z zablokowanym stawem 0 (kąt bazy q_pan): DLS po stawach 1–4, pozycja z priorytetem, orientacja w przestrzeni zerowej
    (kopia logiki ts.ik_reach). Zwraca (q[5], err_pos [m], err_ang [rad])."""
    ids = ts._ids(m)
    site = m.site(site).id
    save = d.qpos.copy()
    d.qpos[5] = ts.Q_OPEN
    Rd = ts._desired_frame(approach_dir)
    az = np.arctan2(p[1], p[0])
    starts = [np.asarray(q0, float), np.array([az, 0.5, 0.9, -0.6, 1.5]), np.array([az, -0.5, 0.9, -1.2, 1.5])]
    best = None
    for qs in starts:
        q = np.clip(qs, ids["lo"], ids["hi"])
        q[0] = q_pan
        for it in range(iters):
            ts._fk(m, d, ids, q)
            ep = p - d.site_xpos[site]
            Jp, Jr = (a[:, 1:] for a in ts._jac(m, d, ids, site))
            R = d.xmat[ids["grip"]].reshape(3, 3)
            eo = None if it >= iters - 15 else 0.5 * sum(np.cross(R[:, i], Rd[:, i]) for i in range(3))
            free = np.ones(4, bool)
            for _ in range(4):
                f = np.where(free)[0]
                jp, jr = Jp[:, f], Jr[:, f]
                jpp = jp.T @ np.linalg.inv(jp @ jp.T + lam ** 2 * np.eye(3))
                dqf = jpp @ ep
                if eo is not None:
                    N = np.eye(len(f)) - jpp @ jp
                    jrn = jr @ N
                    dqf = dqf + N @ (jrn.T @ np.linalg.solve(jrn @ jrn.T + 0.05 ** 2 * np.eye(3), eo - jr @ dqf)) * 0.5
                dq = np.zeros(4)
                dq[f] = dqf
                bad = ((q[1:] + dq > ids["hi"][1:]) & (dq > 0)) | ((q[1:] + dq < ids["lo"][1:]) & (dq < 0))
                if not (bad & free).any():
                    break
                free &= ~bad
            nm = np.abs(dq).max()
            if nm > 0.2:
                dq *= 0.2 / nm
            q[1:] = np.clip(q[1:] + dq, ids["lo"][1:], ids["hi"][1:])
            if nm < 1e-6 and it > 10:
                break
        ts._fk(m, d, ids, q)
        err = float(np.linalg.norm(p - d.site_xpos[site]))
        tool = -d.xmat[ids["grip"]].reshape(3, 3)[:, 2]
        ang = float(np.arccos(np.clip(tool @ (-approach_dir / np.linalg.norm(approach_dir)), -1, 1)))
        up = float(d.xmat[ids["grip"]].reshape(3, 3)[2, 1])
        cost = err * 100 + ang + (1.0 if up > 0.2 else 0.0)
        if best is None or cost < best[0]:
            best = (cost, q.copy(), err, ang)
        if err < 1e-3 and ang < np.radians(5):
            break
    d.qpos[:] = save
    mujoco.mj_forward(m, d)
    return best[1], best[2], best[3]


# --------------------------------------------------------------------------------------------- mózg (z kontrolami)
_CAL = {}


def make_brain(key, seed, need_cal):
    """Mózg-kontrola `key` (authenticity.COND) o strukturze z ziarna seed % 3 (3 różne przetasowania); szum SNN z ziarna próby.
    Kalibracja odczytu (calibrate_ring/steer) raz na (key, struktura) na proces — jak po lezji w authenticity (kalibracja dekodera, nie sieci)."""
    st = 0 if key == "control" else seed % 3
    b = AuthBrain(key, seed=st, calibrate=False)
    if need_cal:
        if (key, st) not in _CAL:
            b.calibrate_ring()
            b.calibrate_steer()
            _CAL[(key, st)] = (b.calib, b.steer)
        b.calib, b.steer = _CAL[(key, st)]
    b.net.rng = np.random.default_rng(1000 + seed)
    b.reset()
    return b


# --------------------------------------------------------------------------------------------- jeden rzut
def run_trial(seed, name, P=None, rig=None, record=False, struct=None):
    own = rig is None
    rig = rig or tc.Rig()
    try:
        return _run(seed, name, P, rig, record, struct)
    finally:
        if own:
            rig.close()


def _wrap(a):
    return float(np.angle(np.exp(1j * a)))


def _run(seed, name, P, rig, record, struct):
    cfg = dict(P0)
    cfg.update(VARIANTS[name])
    if P:
        cfg.update(P)
    if struct:
        cfg["struct"] = struct
    m, d, ds = rig.m, rig.d, rig.ds
    thr = rig.throw(seed)
    T = thr["T"]
    ts.reset_throw(m, d, thr, rig.q_rest, cfg["q_open"])
    trk = rig.trk
    trk.reset()
    yaw, close = cfg["yaw"], cfg["close"]
    tau_mode = close.startswith("tau")
    need_brain = tau_mode or yaw == "brain"
    if need_brain:
        brain = make_brain(cfg["struct"], seed, yaw == "brain")
        g = brain.groups
        lp_ids = np.concatenate([g["LPLC2_L"], g["LPLC2_R"]])
        gf_ids = np.concatenate([g["DNp01_L"], g["DNp01_R"]])
        dna02 = np.concatenate([g["DNa02_L"], g["DNa02_R"]])
    vnc = vnc_controller(seed=seed) if cfg["hold"] == "vnc" else None
    n_fr = int(round((T + tc.TAIL + ts.HOLD_T) * 100))
    n = n_fr * 10
    q_target = rig.q_rest.copy()
    started, z_prev, plan, q_prev = False, None, None, rig.q_rest.copy()
    state, t_close, t_touch, close_pending = "open", None, None, False
    vnc_on, tau_cmd = False, 0.0
    esc_t, gf_t, gf_n, t_start = None, None, 0, None
    lp_hz, lv, inv_tau = 0.0, 0.0, 0.0
    r_hist = []
    pan0 = rig.q_rest[0]
    q_pan_prev = None
    dn_f = np.zeros(2)
    locked = False
    b_ang = 0.0
    omega = 0.0
    fF = np.zeros((n, 2))
    dball = np.zeros(n)
    site_tr = np.zeros((n, 3))
    yax_tr = np.zeros((n, 3))
    lag, yaw_err = 0.0, np.nan
    tab_hit = False
    tab = rig.ids["table"]
    k_T = int(round(T * 1000)) - 1
    log = dict(t=[], lp=[], lv=[], inv_tau=[], gf=[], omega=[], cue=[], bump=[], q0=[], q0_ref=[], q5=[], cmd5=[], dtrue=[], spk_lp=[], spk_dna=[], dn=[]) if record else None
    q0_ref = np.nan
    for fr in range(n_fr):
        t = d.time
        hunt = trk.n >= trk.n_min
        fire, close_pending = close_pending, False
        o = None
        # ---- percepcja + plan
        if esc_t is None and (plan is None or plan["T"] - t > tc.STOP_PLAN) and t < T + 0.1:
            trk_ = trk
            rig.rt.update_scene(d, camera="eye", scene_option=rig.optt)
            o = trk_.step(rig.rt.render(), t)
            if o["ready"]:
                p, plans = tc.plan_catch(rig, trk_, t, d.qpos[:5], q_prev, z_prev)
                if p is not None:
                    plan, z_prev, q_prev = p, p["z"], p["q"]
                    q0_ref = p["q"][0]
                    if not started and p["sig_y"] < cfg["sig_y_start"]:
                        started, t_start = True, t
                    if started:
                        q_target = p["q"].copy()
                        if yaw != "ik":      # skręt bazy narzucony (zamrożony / z mózgu): IK 4 stawów do p_pred przy bieżącym kącie bazy
                            q_pan = pan0 if yaw == "frozen" else d.ctrl[0]
                            a = trk_.predict(p["z"])["v"]
                            ql, err, ang = _ik_fixed(m, ds, p["p"], a / np.linalg.norm(a), q_pan, q_target)
                            q_target = ql
        # ---- τ: kąt plamki 320×240 → 1/τ → loom
        if tau_mode:
            blob = None if o is None else o["blob"]
            if blob is not None and blob["conf"] >= 0.2 and not blob["border"] and blob["A"] >= cfg["a_min"]:
                r_hist.append((t, float(np.sqrt(blob["A"] / np.pi) - trk.delta)))
            r_hist = [h for h in r_hist if t - h[0] < cfg["tau_win"]]
            inv_tau, lv = 0.0, 0.0
            if len(r_hist) >= max(4, int(0.7 * cfg["tau_win"] / 0.01)):
                tt_, rr_ = np.array(r_hist).T
                sl, ic = np.polyfit(tt_, rr_, 1)
                r_fit = sl * t + ic
                if r_fit > 1:
                    inv_tau = float(sl / r_fit)
                    lv = float(np.clip((inv_tau - cfg["r0"]) / cfg["r1"], 0, 1))
        # ---- mózg: loom (τ) i/lub cue (yaw)
        spk_gf = False
        spk = None
        if need_brain and t <= T + tc.BRAIN_UNTIL:
            cue = None
            if yaw == "brain" and plan is not None and hunt:
                aim = d.site("aim").xpos
                tgt = plan["p"]
                cue = _wrap(np.arctan2(tgt[1], tgt[0]) - np.arctan2(aim[1], aim[0]))
            w_base = -d.qvel[0]
            u = brain.u_for(-w_base) if yaw == "brain" else 0.0
            spk = brain.step10(cue=cue, u=u, loom=(lv, lv), flow=0.0, rest=not hunt)
            lp_hz = float(spk[:, lp_ids].mean() * 1000.0)
            spk_gf = bool(spk[:, gf_ids].any())
            if spk_gf:
                gf_n += 1
                if gf_t is None:
                    gf_t = t
                if esc_t is None and cfg["escape"] == "free":
                    esc_t = t
                    q_esc = d.ctrl[:5].copy()
                    q_esc[1] -= 1.1
                    q_esc[2] += 0.4
                    q_target = np.clip(q_esc, rig.ids["lo"], rig.ids["hi"])
            if state == "open" and hunt and started:
                if (close == "tau_dn" and spk_gf) or (close == "tau_lp" and lp_hz >= cfg["lp_thr"]):
                    close_pending = True
            if yaw == "brain":      # dekoder skrętu jak w agent.py (stan aktywny)
                b_ang, _, _ = brain.bump(spk)
                rt = brain.rate
                gg = brain.groups
                raw = np.array([rt[gg["DNa02_L"]].mean() - rt[gg["DNa02_R"]].mean(), rt[gg["DNa01_L"]].mean() - rt[gg["DNa01_R"]].mean()])
                a_ = np.exp(-0.01 / np.array([TAU_DNA02, TAU_DNA01]))
                dn_f = a_ * dn_f + (1 - a_) * raw
                stt = brain.steer
                off, sl_ = stt["offset"], stt["slope"]
                omega = cfg["g_turn"] * float(np.mean((dn_f - off) / sl_))
                if cue is not None and not locked and abs(_wrap(cue - b_ang)) < LOCK:
                    locked = True
                if cue is None:
                    locked = False
                if not locked:
                    dn_f = np.array(off, float)
                if not locked or esc_t is not None or d.sensordata[:3].max() > tc.F_TOUCH:
                    omega = 0.0
                w = float(np.clip(omega, -W_MAX, W_MAX))
                c = np.clip(d.ctrl[0] - w * 0.01, d.qpos[0] - WINDUP, d.qpos[0] + WINDUP)
                d.ctrl[0] = float(np.clip(c, *m.actuator_ctrlrange[0]))
        # ---- czucie, VNC
        touch = d.sensordata[:3].copy()
        touched = touch.max() > tc.F_TOUCH
        if touched and t_touch is None:
            t_touch = t
        if vnc is not None:
            _, tau, _ = vnc.control_step(None, touch, active=hunt, jaw_vel=d.qvel[5], jaw_q=d.qpos[5])
            tau_cmd = float(np.clip(-tau / sb.GRIP_TORQUE, -1, 1))
        if state == "closing" and cfg["hold"] == "vnc" and touched:
            vnc_on = True
        # ---- 10 ms fizyki
        for j in range(10):
            tt = d.time
            k = fr * 10 + j
            if started or esc_t is not None:
                if yaw == "brain" and esc_t is None:
                    d.ctrl[1:5] += np.clip(q_target[1:] - d.ctrl[1:5], -tc.SERVO_STEP, tc.SERVO_STEP)
                else:
                    d.ctrl[:5] += np.clip(q_target - d.ctrl[:5], -tc.SERVO_STEP, tc.SERVO_STEP)
            elif yaw == "frozen":
                pass
            if state == "open":
                if close == "tpred" and plan is not None and tt >= plan["T"] - cfg["lead"] and started:
                    state, t_close = "closing", tt
                elif fire and j == 0:
                    state, t_close = "closing", tt
            if state == "open":
                d.ctrl[5] = np.clip(3.0 * (cfg["q_open"] - d.qpos[5]) - 0.3 * d.qvel[5], -1, 1)
            else:
                d.ctrl[5] = tau_cmd if vnc_on else -cfg["u_close"]
            mujoco.mj_step(m, d)
            f, _other = ts._ball_contacts(m, d, rig.ball, rig.pads, rig.rob)
            fF[k] = f
            tab_hit |= any(tab in (c.geom1, c.geom2) and (c.geom1 in rig.rob or c.geom2 in rig.rob) for c in d.contact[:d.ncon])
            site_tr[k] = d.site_xpos[rig.sid]
            yax_tr[k] = d.xmat[rig.gid].reshape(3, 3)[:, 1]
            dball[k] = np.linalg.norm(d.body("ball").xpos - d.site_xpos[rig.sid])
            if k == k_T - tc.PRE_MS:
                lag = float(np.abs(d.qpos[1:5] - q_target[1:]).max()) if started else 9.9
                yaw_err = float(np.degrees(d.qpos[0] - q0_ref)) if np.isfinite(q0_ref) else np.nan
        if record:
            log["t"].append(t); log["lp"].append(lp_hz); log["lv"].append(lv); log["inv_tau"].append(inv_tau); log["gf"].append(spk_gf)
            log["omega"].append(omega); log["q0"].append(d.qpos[0]); log["q0_ref"].append(q0_ref); log["q5"].append(d.qpos[5]); log["cmd5"].append(d.ctrl[5])
            log["dtrue"].append(np.linalg.norm(d.body("ball").xpos - d.site_xpos[rig.sid]))
            log["dn"].append(dn_f.copy()); log["bump"].append(b_ang)
            log["spk_lp"].append(np.zeros((10, len(lp_ids)), bool) if spk is None else spk[:, lp_ids])
            log["spk_dna"].append(np.zeros((10, len(dna02)), bool) if spk is None else spk[:, dna02])
    out = tc._score(seed, name, thr, cfg, fF, dball, (site_tr, yax_tr, lag), tab_hit, t_close, t_start, t_touch, esc_t, gf_t, gf_n, started, log, plan)
    out["yaw_err_deg"] = yaw_err
    out["struct"] = cfg["struct"]
    if not out["success"] and yaw != "ik" and np.isfinite(yaw_err) and abs(yaw_err) > 5 and out["cls"] not in ("ucieczka", "nie zdążył"):
        out["cls"] = "zły azymut"
    return out


# --------------------------------------------------------------------------------------------- równoległość i raport
_RIG = None


def _work(a):
    global _RIG
    seed, name, P = a
    if _RIG is None:
        _RIG = tc.Rig()
    return run_trial(seed, name, P, rig=_RIG)


def run_set(seeds, name, P=None, procs=3):
    from multiprocessing import Pool
    with Pool(procs) as pool:
        return pool.map(_work, [(s, name, P) for s in seeds], chunksize=1)


def _line(rs):
    n = len(rs)
    k = sum(r["success"] for r in rs)
    lo, hi = tc.wilson(k, n)
    cl = {}
    for r in rs:
        if not r["success"]:
            cl[r["cls"]] = cl.get(r["cls"], 0) + 1
    tcl = [r["t_close_ms"] for r in rs if r["t_close_ms"] is not None]
    ye = [abs(r["yaw_err_deg"]) for r in rs if np.isfinite(r["yaw_err_deg"])]
    gf = sum(r["dnp01"] for r in rs)
    s = f"sukces {k:2d}/{n} = {100 * k / n:3.0f} % [{100 * lo:.0f}–{100 * hi:.0f}]  " + (", ".join(f"{a} {b}" for a, b in sorted(cl.items(), key=lambda kv: -kv[1])) or "-")
    s += f"  | DNp01 {gf}/{n}"
    if tcl:
        s += f"  zamk.−T med {np.median(tcl):.0f} (p10 {np.percentile(tcl, 10):.0f}, p90 {np.percentile(tcl, 90):.0f}) n={len(tcl)}"
    if ye:
        s += f"  |błąd azymutu bazy| med {np.median(ye):.1f}° p90 {np.percentile(ye, 90):.1f}°"
    return s


def _grid(variant, seeds, spec, tag, struct=None):
    import itertools
    keys = [k.split("=")[0] for k in spec]
    vals = [[float(v) for v in k.split("=")[1].split(",")] for k in spec]
    path = os.path.join(HERE, "results", "stage5b_tuning.txt")
    for combo in itertools.product(*vals):
        P = dict(zip(keys, combo))
        t0 = time.time()
        rs = [r for r in run_set(seeds, variant, dict(P, **({"struct": struct} if struct else {})))]
        line = f"[{tag} seedy {seeds[0]}–{seeds[-1]}] {variant}{'/' + struct if struct else ''} {P}: " + _line(rs) + f"  ({time.time() - t0:.0f} s)"
        print(line, flush=True)
        open(path, "a").write(line + "\n")


def _parse(x):
    a, b = x.split(":")
    return list(range(int(a), int(b)))


VALIDATION_ROWS = [
    ("ENG A", "ENG", {}),
    ("ENG B", "ENG", WIDE),
    ("NO-YAW A", "NO-YAW", {}),
    ("NO-YAW B", "NO-YAW", WIDE),
    ("BIO-yaw A (G 2.5)", "BIO-yaw", dict(g_turn=2.5)),
    ("BIO-yaw+G A", "BIO-yaw", dict(g_turn=5.0)),
    ("BIO-yaw+G B", "BIO-yaw", dict(WIDE, g_turn=5.0)),
    ("BIO-τ(DN) B", "BIO-τ(DN)", WIDE),
    ("BIO-τ(LP) B", "BIO-τ(LP)", WIDE),
    ("BIO-τ-ucieczka B", "BIO-τ-ucieczka", WIDE),
    ("BIO-full B", "BIO-full", dict(WIDE, g_turn=5.0)),
]

TEST_ROWS = VALIDATION_ROWS + [
    ("BIO-τ(DN) + rewire_all", "BIO-τ(DN)", dict(WIDE, struct="rewire_all")),
    ("BIO-τ(DN) + shuffle_all", "BIO-τ(DN)", dict(WIDE, struct="shuffle_all")),
    ("BIO-τ(DN) + les_LOOM", "BIO-τ(DN)", dict(WIDE, struct="les_LOOM")),
    ("BIO-τ(LP) + rewire_all", "BIO-τ(LP)", dict(WIDE, struct="rewire_all")),
    ("BIO-τ(LP) + shuffle_all", "BIO-τ(LP)", dict(WIDE, struct="shuffle_all")),
    ("BIO-τ(LP) + les_LOOM", "BIO-τ(LP)", dict(WIDE, struct="les_LOOM")),
    ("BIO-yaw + les_PFL3 A", "BIO-yaw", dict(g_turn=2.5, struct="les_PFL3")),
    ("BIO-yaw + shuffle_cx A", "BIO-yaw", dict(g_turn=2.5, struct="shuffle_cx")),
    ("BIO-yaw+G + les_PFL3 A", "BIO-yaw", dict(g_turn=5.0, struct="les_PFL3")),
    ("BIO-full + les_PFL3 B", "BIO-full", dict(WIDE, g_turn=5.0, struct="les_PFL3")),
    ("BIO-full + les_LOOM B", "BIO-full", dict(WIDE, g_turn=5.0, struct="les_LOOM")),
]


def run_suite(seeds, rows, out_file, tag):
    path = os.path.join(HERE, "results", out_file)
    print(f"\n=== URUCHAMIANIE ZESTAWU [{tag}] (seedy {seeds[0]}–{seeds[-1]}, N={len(seeds)}, wariantów={len(rows)}) ===", flush=True)
    existing = set()
    if os.path.exists(path):
        with open(path) as f:
            content = f.read()
            for lb, _, _ in rows:
                if f" {lb} " in content or f" {lb:<26s}" in content:
                    existing.add(lb)
    with open(path, "a") as f:
        f.write(f"\n# --- {tag} seedy {seeds[0]}–{seeds[-1]} (data: {time.strftime('%Y-%m-%d %H:%M:%S')}) ---\n")
    for label, variant, P in rows:
        if label in existing:
            print(f"[{tag} {seeds[0]}–{seeds[-1]}] {label:<26s} (pominięto - już obliczone)", flush=True)
            continue
        t0 = time.time()
        rs = run_set(seeds, variant, P)
        struct_tag = f"/{P['struct']}" if "struct" in P else ""
        line = f"[{tag} {seeds[0]}–{seeds[-1]}] {label:<26s} ({variant}{struct_tag}): " + _line(rs) + f"  ({time.time() - t0:.0f} s)"
        print(line, flush=True)
        with open(path, "a") as f:
            f.write(line + "\n")
    print(f"=== ZAKOŃCZONO [{tag}] -> zapisano do {path} ===\n", flush=True)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "one":
        name, seed = sys.argv[2], int(sys.argv[3])
        P = dict(q_open=1.2, lead=0.2) if len(sys.argv) > 4 and sys.argv[4] == "B" else {}
        t0 = time.time()
        r = run_trial(seed, name, P)
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items() if k not in ("log",)}, f"{time.time() - t0:.1f} s")
    elif mode == "grid":
        # grid WARIANT a:b TAG [struct=KLUCZ] [klucz=wart,...]
        spec = sys.argv[5:]
        struct = next((s.split("=")[1] for s in spec if s.startswith("struct=")), None)
        _grid(sys.argv[2], _parse(sys.argv[3]), [s for s in spec if not s.startswith("struct=")], sys.argv[4], struct)
    elif mode == "validate":
        seeds = _parse(sys.argv[2]) if len(sys.argv) > 2 else list(range(150, 200))
        run_suite(seeds, VALIDATION_ROWS, "stage5b_validation.txt", "VAL")
    elif mode == "test":
        seeds = _parse(sys.argv[2]) if len(sys.argv) > 2 else list(range(0, 50))
        run_suite(seeds, TEST_ROWS, "stage5b_final_test.txt", "TEST")

