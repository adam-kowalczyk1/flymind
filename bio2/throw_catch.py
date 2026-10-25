"""Etap 5 (bio2): sterownik łapania rzuconej piłeczki (throw_scene.py) — warianty, żeby było widać, co wnosi mózg muchy, a co inżynieria.

WARSTWA POŁOŻENIA (wspólna dla wszystkich wariantów poza ORACLE; INŻYNIERIA, nie biologia): throw_percept.BallTracker (kamera „eye”
320×240, detekcja po kolorze, parabola balistyczna) → predict(z_c) dla kilku płaszczyzn z_c z zakresu z_star → ik_reach (oś narzędzia
przeciwna do lotu) → serwa z limitem prędkości SERVO_SPEED, z przeplanowaniem co 10 ms. Ruch rusza, gdy jest wykonalny plan, a σ_y
(niepewność toru poprzecznie do paszczy, w układzie chwytaka w pozie docelowej) < SIG_Y_START. Po T_plan − 30 ms plan zamarza.

Warianty (różnią się WYŁĄCZNIE tym, co zamyka szczęki i kto trzyma siłę, oraz tym, co robi spike DNp01):
  ORACLE      throw_scene.oracle_trial (zna prawdę: q*, T), odniesienie.
  ENG         zamknięcie w T_pred − LEAD (stały PWM −U_CLOSE) — bez mózgu.
  ENG+VNC     jw., ale po dotyku siłę trzyma rdzeń brzuszny (VNC) — izoluje wkład VNC.
  LOOM+PWM    zamknięcie wyzwala looming z siatkówki muchy (poniżej), siła stałym PWM — izoluje wkład loomingu.
  BIO-ucieczka    looming → zamknięcie + VNC trzyma siłę; spike DNp01 (Giant Fiber) uruchamia ucieczkę jak w agent.py (= porażka chwytu).
  BIO-polowanie   jw., ale ucieczka gaszona w stanie „polowanie” (MODEL: w pościgu ucieczka jest stłumiona, np. oktopamina/OA;
                  w konektomie tego nie sprawdzono). Polowanie = tracker ma tor.
  BIO-dotyk   kontrola: zamknięcie TYLKO po dotyku (czujniki szczęk → VNC jak v1–v3), bez loomingu i bez T_pred.

Ścieżka looming (BIO): kamera „eye” 128×96 (scene2.eye_renderer) → vision.Vision (FlyRetinaFilter, loom L/P z przyrostu obszaru OFF,
kopia eferentna obrotu bazy dpsi) → Brain.step10(loom=(L, P)) (wejście do LC4/LPLC2, brain.py/agent.py bez zmian) → ODCZYT
(MODEL, wszystkie stałe poniżej): częstość populacji LPLC2 (obie strony, 24 neurony) w ostatnim oknie 10 ms ≥ LPLC2_THR [Hz] →
„zamknij” (odruch lądowania: looming → wysunięcie nóg). SNN całkuje okno 10 ms po obrazie, więc komenda działa od następnej klatki
(+10 ms). Dotyk: max z czujników szczęk/dłoni > F_TOUCH (0,3 N = F_SECURE z agent.py) → przejście z PWM zamykania na VNC.
Miary z prawdy MuJoCo (jak oracle_trial i stage3_b2): sukces = piłeczka w paszczy ≥ 1 s (obie szczęki > 0,05 N, środek < 4 cm od środka
paszczy), zgniecenie = średnia 20 ms siły szczęka–piłeczka > 5 N (raportowane osobno jako flaga; klasa „zgniecenie” tylko przy porażce).

Uruchom:  python throw_catch.py explore | tune ... | report   (patrz __main__)
"""
import os
import sys
import time

import mujoco
import numpy as np

import scene2
import so101_base as sb
import throw_scene as ts
import throw_percept as tp
from brain import Brain
from vision import Vision
from vnc import vnc_controller

HERE = os.path.dirname(os.path.abspath(__file__))
DT = ts.DT
SERVO_STEP = ts.SERVO_SPEED * DT
F_CRUSH = 5.0
F_TOUCH = 0.3            # N (agent.F_SECURE)
Z_CANDS = (0.34, 0.30, 0.26, 0.22)       # płaszczyzny przechwycenia zapytywane u trackera (zakres z_star)
ANG_OK = float(ts.RANGES["ang_max"])
PRE_MS = 30              # błąd paszczy względem toru mierzę 30 ms przed T (przed uderzeniem piłeczki: od ~T−10 ms impuls 0,25 N·s ugina ramię o 2–5 cm)
STOP_PLAN = 0.03         # s: w ostatnich 30 ms przed T_plan plan jest zamrożony (piłeczka za blisko kamery na pomiar)
TAIL = 0.5               # s po T symulacji (jak w oracle_trial) + HOLD
BRAIN_UNTIL = 0.3        # s po T: do tej chwili liczę siatkówkę/mózg (DNp01)

# --- parametry (strojone na seedach 100–149; zob. results/stage5_catch.txt) ---
P0 = dict(
    sig_y_start=1.0,     # m: start ruchu, gdy σ_y planu < tyle (dobrane: 1,0 = bez bramki, patrz strojenie)
    lead=0.03,           # s: ENG zamyka w T_pred − lead
    loom_thr=60.0,       # Hz: MODEL, próg populacji LPLC2 (24 neurony) w oknie 10 ms
    u_close=ts.U_CLOSE,  # PWM zamykania (przed dotykiem; w wariantach z VNC potem siłę daje VNC)
    q_open=ts.Q_OPEN,
    t_on=0.10, g_on0=10.0, g_on1=24.0,   # MODEL: odczyt loomingu JASNEGO (ON) z L1: próg komórki, przyrost obszaru ON w 50 ms: od g_on0 sygnał rośnie, przy g_on0+g_on1 = 1
    loom_mask=True,      # MODEL: wyciszenie WEJŚCIA loomingu do mózgu, gdy ramię jedzie (kopia eferentna, jak HS w agent.py)
    v_self=0.3,          # rad/s: próg „ramię jedzie” dla maski (model)
)

VARIANTS = {
    "NO-CLOSE": dict(trigger="none", hold="pwm", fly=False, escape=None),
    "ORACLE": dict(kind="oracle"),
    "ENG": dict(trigger="tpred", hold="pwm", fly=False, escape=None),
    "ENG+VNC": dict(trigger="tpred", hold="vnc", fly=False, escape=None),
    "LOOM+PWM": dict(trigger="loom", hold="pwm", fly=True, escape=None, src="on"),
    "BIO-ucieczka": dict(trigger="loom", hold="vnc", fly=True, escape="free", src="vision"),
    "BIO-polowanie": dict(trigger="loom", hold="vnc", fly=True, escape="gated", src="vision"),
    "BIO-ON-ucieczka": dict(trigger="loom", hold="vnc", fly=True, escape="free", src="on"),
    "BIO-ON-polowanie": dict(trigger="loom", hold="vnc", fly=True, escape="gated", src="on"),
    "BIO-dotyk": dict(trigger="touch", hold="vnc", fly=False, escape=None),
}


# --------------------------------------------------------------------------------------------- stanowisko (per proces)
class Rig:
    """Model, dane, tracker i renderery (tworzone raz na proces; `close()` zamyka renderery)."""

    def __init__(self):
        self.m, self.d = ts.load()
        self.ds = mujoco.MjData(self.m)                 # dane robocze IK
        self.trk = tp.BallTracker(self.m, self.d)
        self.rt, self.optt = self.trk.renderer()
        self.rf, self.optf = scene2.eye_renderer(self.m)  # 128×96: siatkówka muchy
        self.rs, self.opts = ts.seg_renderer(self.m)    # tylko eksploracja (widoczność)
        self.q_rest = ts.rest_pose(self.m, self.d)
        self.ids = ts._ids(self.m)
        self.ball = self.m.geom("ball").id
        self.pads = [self.m.geom("jaw_fixed").id, self.m.geom("jaw_moving").id]
        self.rob = set(self.ids["robot"].tolist())
        self.sid = self.m.site("catch").id
        self.gid = self.ids["grip"]
        self._thr = {}

    def throw(self, seed):
        if seed not in self._thr:
            self._thr[seed] = ts.make_throw(seed, self.m, self.d)
        return self._thr[seed]

    def close(self):
        for r in (self.rt, self.rf, self.rs):
            r.close()


# --------------------------------------------------------------------------------------------- warstwa położenia
def plan_catch(rig, trk, t, q_now, q_prev, z_prev):
    """Dla płaszczyzn Z_CANDS: predict → IK. Zwraca (najlepszy plan albo None, lista planów). Plan: dict(z, q, p, T, ang, sig_y,
    slack). Wybór: zachowuję poprzednią płaszczyznę (histereza, bez skakania celu), dopóki jest wykonalna; inaczej minimalny
    ang + 2·σ_y [mm] wśród tych z zapasem czasu ≥ 0, a jak brak — z największym zapasem."""
    m, ds, ids = rig.m, rig.ds, rig.ids
    plans = []
    for z in Z_CANDS:
        pr = trk.predict(z)
        if pr is None or pr["T"] - t < STOP_PLAN:
            continue
        a = pr["v"] / np.linalg.norm(pr["v"])
        q, err, ang = ts.ik_reach(m, ds, pr["p"], a, q0=q_prev, iters=60)
        if err > 1.5e-3 or ang > ANG_OK:
            continue
        clr, nself = ts.arm_clearance(m, ds, q)
        if clr < 0.005 or nself:
            continue
        ds.qpos[ids["qa"]] = q
        mujoco.mj_kinematics(m, ds)
        R = ds.xmat[rig.gid].reshape(3, 3)
        sy = float(np.sqrt(max((R.T @ pr["cov_p"] @ R)[1, 1], 0)))
        travel = float(np.abs(q - q_now).max() / ts.SERVO_SPEED)
        plans.append(dict(z=z, q=q, p=pr["p"], T=pr["T"], ang=float(np.degrees(ang)), sig_y=sy, slack=pr["T"] - t - travel - 0.03))
    if not plans:
        return None, plans
    keep = [p for p in plans if z_prev is not None and p["z"] == z_prev]
    if keep:
        return keep[0], plans
    ok = [p for p in plans if p["slack"] >= 0]
    if ok:
        return min(ok, key=lambda p: p["ang"] + 2000 * p["sig_y"]), plans
    return max(plans, key=lambda p: p["slack"]), plans


# --------------------------------------------------------------------------------------------- jeden rzut
def run_trial(seed, name, P=None, rig=None, record=False):
    own = rig is None
    rig = rig or Rig()
    try:
        return _run(seed, name, P, rig, record)
    finally:
        if own:
            rig.close()


def _run(seed, name, P, rig, record):
    cfg = dict(P0, **(P or {}), **VARIANTS[name])
    m, d = rig.m, rig.d
    thr = rig.throw(seed)
    T = thr["T"]
    if cfg.get("kind") == "oracle":
        o = ts.oracle_trial(seed, thr=thr, m=m, d=d, rest=rig.q_rest, render=False, record=True,
                            P=dict(q_open=cfg["q_open"], u_close=cfg["u_close"], lead=cfg["lead"]))
        return _oracle_result(o, thr, name, cfg)
    ts.reset_throw(m, d, thr, rig.q_rest, cfg["q_open"])
    trk = rig.trk
    trk.reset()
    fly = cfg["fly"]
    if fly:
        vis = Vision(scene2.CAM_FOVY, scene2.CAM_W / scene2.CAM_H)
        brain = Brain(seed=seed)
        g = brain.groups
        lp_ids = np.concatenate([g["LPLC2_L"], g["LPLC2_R"]])
        gf_ids = np.concatenate([g["DNp01_L"], g["DNp01_R"]])
    vnc = vnc_controller(seed=seed) if cfg["hold"] == "vnc" else None
    n_fr = int(round((T + TAIL + ts.HOLD_T) * 100))
    q_target = rig.q_rest.copy()
    started, z_prev, plan, q_prev = False, None, None, rig.q_rest.copy()
    state, t_close, t_touch, loom_pending = "open", None, None, False
    vnc_on, tau_cmd = False, 0.0
    esc_t, q_esc, gf_t, gf_n = None, None, None, 0
    t_start = None
    lp_hz, loom_lr, q_pan_prev = 0.0, (0.0, 0.0), None
    grow_lr, off_lr = (0, 0), (0, 0)
    on_hist = []
    n = n_fr * 10
    fF = np.zeros((n, 2))
    dball = np.zeros(n)
    site_tr = np.zeros((n, 3))
    yax_tr = np.zeros((n, 3))
    lag = 0.0
    tab_hit = False
    log = dict(t=[], growL=[], growR=[], offL=[], offR=[], lp=[], loomL=[], loomR=[], gf=[], sig_y=[], plan_T=[], q5=[], cmd5=[], dtrue=[], px=[]) if record else None
    tab = rig.ids["table"]
    k_T = int(round(T * 1000)) - 1
    pos_T = None
    for fr in range(n_fr):
        t = d.time
        hunt = trk.n >= trk.n_min
        # ---- percepcja + plan (co 10 ms)
        loom_fire, loom_pending = loom_pending, False     # komenda z poprzedniej klatki (SNN całkuje okno 10 ms)
        if esc_t is None and (plan is None or plan["T"] - t > STOP_PLAN) and t < T + 0.1:
            rig.rt.update_scene(d, camera="eye", scene_option=rig.optt)
            o = trk.step(rig.rt.render(), t)
            if o["ready"]:
                p, plans = plan_catch(rig, trk, t, d.qpos[:5], q_prev, z_prev)
                if p is not None:
                    plan, z_prev, q_prev = p, p["z"], p["q"]
                    if not started and p["sig_y"] < cfg["sig_y_start"]:
                        started, t_start = True, t
                    if started:
                        q_target = p["q"]
        # ---- siatkówka + mózg (BIO)
        spk_gf = False
        if fly and t <= T + BRAIN_UNTIL:
            dpsi = 0.0 if q_pan_prev is None else -(d.qpos[0] - q_pan_prev)
            q_pan_prev = d.qpos[0]
            rig.rf.update_scene(d, camera="eye", scene_option=rig.optf)
            v = vis.step(rig.rf.render(), dpsi=dpsi)
            loom_lr = v["loom"]
            grow_lr, off_lr = v["grow"], v["off_area"]
            if cfg["src"] == "on":      # MODEL: looming jasnego obiektu z komórek ON (L1) — Vision.loom liczy tylko OFF (obiekty ciemne)
                on = v["retina"]["L1"] > cfg["t_on"]
                on_hist.append((int(on[:, :on.shape[1] // 2].sum()), int(on[:, on.shape[1] // 2:].sum())))
                old = on_hist[-6] if len(on_hist) > 5 else on_hist[0]
                grow_lr = tuple(a - b for a, b in zip(on_hist[-1], old))
                off_lr = on_hist[-1]
                loom_lr = tuple(float(np.clip((g - cfg["g_on0"]) / cfg["g_on1"], 0, 1)) for g in grow_lr)
            moving = cfg["loom_mask"] and float(np.abs(d.qvel[:5]).max()) > cfg["v_self"]
            if moving:                  # MODEL: kopia eferentna wycisza detektory loomingu podczas własnego ruchu ramienia
                loom_lr = (0.0, 0.0)
            spk = brain.step10(cue=None, loom=loom_lr, flow=0.0, rest=not hunt)
            lp_hz = float(spk[:, lp_ids].mean() * 1000.0)
            spk_gf = bool(spk[:, gf_ids].any())
            if lp_hz >= cfg["loom_thr"] and state == "open" and hunt:
                loom_pending = True
            if spk_gf:
                gf_n += 1
                if gf_t is None:
                    gf_t = t
                if esc_t is None and (cfg["escape"] == "free" or (cfg["escape"] == "gated" and not hunt)):
                    esc_t = t
                    q_esc = d.ctrl[:5].copy()
                    q_esc[1] -= 1.1
                    q_esc[2] += 0.4
                    q_esc = np.clip(q_esc, rig.ids["lo"], rig.ids["hi"])
                    q_target = q_esc
        # ---- czucie, VNC
        touch = d.sensordata[:3].copy()
        touched = touch.max() > F_TOUCH
        if touched and t_touch is None:
            t_touch = t
        if vnc is not None:
            _, tau, _ = vnc.control_step(None, touch, active=hunt, jaw_vel=d.qvel[5], jaw_q=d.qpos[5])
            tau_cmd = float(np.clip(-tau / sb.GRIP_TORQUE, -1, 1))
        if touched and state == "open" and (cfg["trigger"] == "touch" or (cfg["trigger"] == "loom" and cfg["hold"] == "vnc")):
            state, t_close, vnc_on = "closing", t, True
        if state == "closing" and cfg["hold"] == "vnc" and touched:
            vnc_on = True
        # ---- 10 ms fizyki
        for j in range(10):
            tt = d.time
            k = fr * 10 + j
            if started or esc_t is not None:
                d.ctrl[:5] += np.clip(q_target - d.ctrl[:5], -SERVO_STEP, SERVO_STEP)
            if state == "open":
                if cfg["trigger"] == "tpred" and plan is not None and tt >= plan["T"] - cfg["lead"] and started:
                    state, t_close = "closing", tt
                elif loom_fire and j == 0:
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
            if k == k_T - PRE_MS:
                lag = float(np.abs(d.qpos[:5] - q_target).max()) if started else 9.9
        if record:
            log["t"].append(t); log["growL"].append(grow_lr[0]); log["growR"].append(grow_lr[1]); log["offL"].append(off_lr[0]); log["offR"].append(off_lr[1]); log["lp"].append(lp_hz); log["loomL"].append(loom_lr[0]); log["loomR"].append(loom_lr[1])
            log["gf"].append(spk_gf); log["sig_y"].append(np.nan if plan is None else plan["sig_y"])
            log["plan_T"].append(np.nan if plan is None else plan["T"]); log["q5"].append(d.qpos[5]); log["cmd5"].append(d.ctrl[5])
            log["dtrue"].append(np.linalg.norm(d.body("ball").xpos - d.site_xpos[rig.sid]))
    return _score(seed, name, thr, cfg, fF, dball, (site_tr, yax_tr, lag), tab_hit, t_close, t_start, t_touch, esc_t, gf_t, gf_n, started, log, plan)


def _crushed(fF, t_skip=100):
    """(zgniecenie, szczyt 1 ms [N], szczyt średniej 20 ms po przejściowym uderzeniu [N]). Uderzenie piłeczki 4–5 m/s daje ~40–60 N
    szczytu w każdym wariancie (także wyroczni), więc zgniecenie liczę od t_skip ms po pierwszym kontakcie (utrzymywany uścisk)."""
    k = np.ones(20) / 20
    c = np.nonzero(fF.max(1) > 0)[0]
    i0 = (c[0] + t_skip) if len(c) else len(fF)
    pk = float(max((np.convolve(fF[:, i], k, "same")[i0:].max() if i0 < len(fF) else 0.0) for i in (0, 1)))
    return pk > F_CRUSH, float(max(fF[:, 0].max(), fF[:, 1].max())), pk


def _hold_window(fF, dball):
    n = len(fF)
    ok = (fF.min(1) > ts.F_CONTACT) & (dball < 0.04)
    W = int(ts.HOLD_T * 1000)
    cs = np.concatenate([[0], np.cumsum(ok)])
    return next((i for i in range(0, n - W + 1) if cs[i + W] - cs[i] >= 0.99 * W), None), ok


def path_error(thr, site_tr, yax_tr):
    """Błąd paszczy względem toru: min_k |site(t_k) − ball_pos(t_k)| dla t_k ∈ [T−60 ms, T+10 ms] (tor analityczny, bez zaburzeń po
    uderzeniu) i jego składowa y w układzie chwytaka [mm]."""
    T = thr["T"]
    k0, k1 = int(round(T * 1000)) - 60, int(round(T * 1000)) + 10
    ks = np.arange(k0, k1)
    e = np.array([site_tr[k] - ts.ball_pos(thr, (k + 1) * ts.DT) for k in ks])
    i = int(np.argmin(np.linalg.norm(e, axis=1)))
    return float(1000 * np.linalg.norm(e[i])), float(1000 * e[i] @ yax_tr[ks[i]]), float((ks[i] + 1) * ts.DT - T) * 1000


def _score(seed, name, thr, cfg, fF, dball, arm, tab_hit, t_close, t_start, t_touch, esc_t, gf_t, gf_n, started, log, plan):
    T = thr["T"]
    kT = int(round(T * 1000)) - 1
    t_hold, _ = _hold_window(fF, dball)
    crush, peak, pk20 = _crushed(fF)
    both = fF.min(1) > ts.F_CONTACT
    contact = fF.max(1) > 0.0
    arm_err, e_y, _ = path_error(thr, arm[0], arm[1])
    lag = arm[2]
    out = dict(seed=seed, variant=name, T=T, success=t_hold is not None, crush=crush, peak_N=peak, hold_N=pk20, arm_err_mm=arm_err, arm_lag_rad=lag, e_y_mm=e_y,
               t_close_ms=None if t_close is None else 1000 * (t_close - T), started=started,
               tau_start_ms=None if t_start is None else 1000 * (T - t_start), t_touch_ms=None if t_touch is None else 1000 * (t_touch - T),
               dnp01=gf_t is not None, dnp01_ms=None if gf_t is None else 1000 * (gf_t - T), dnp01_n=gf_n,
               escape=esc_t is not None, esc_ms=None if esc_t is None else 1000 * (esc_t - T), table_hit=tab_hit,
               speed=thr["speed"], el_deg=thr["el_deg"], az_off_deg=thr["az_off_deg"])
    if out["success"]:
        cls = "sukces"
    elif esc_t is not None:
        cls = "ucieczka"
    elif lag > 0.03:
        cls = "nie zdążył"
    elif not contact.any():
        cls = "chybienie"
    elif crush:
        cls = "zgniecenie"
    elif not both.any():
        cls = "odbicie"
    else:
        cls = "wypadła"
    out["cls"] = cls
    if log is not None:
        out["log"] = {k: np.array(v) for k, v in log.items()}
        out.update(fF=fF, dball=dball, plan=plan, thr=thr, site=arm[0])
    return out


def _oracle_result(o, thr, name, cfg):
    T = thr["T"]
    F = o["F"]
    crush, peak, pk20 = _crushed(F)
    cls = {"odbicie od szczęki/dłoni": "odbicie", "odbicie od ramienia": "odbicie"}.get(o["cls"], o["cls"])
    return dict(seed=o["seed"], variant=name, T=T, success=o["success"], crush=crush, peak_N=peak, hold_N=pk20, arm_err_mm=float(1000 * o["err_arm"][int(round(T * 1000)) - 60:int(round(T * 1000)) + 10].min()), arm_lag_rad=0.0, e_y_mm=np.nan,
                t_close_ms=-1000 * cfg["lead"], started=True, tau_start_ms=1000 * (T - ts.D_PERCEPT), t_touch_ms=None, dnp01=False,
                dnp01_ms=None, dnp01_n=0, escape=False, esc_ms=None, table_hit=o["table_hit"], speed=thr["speed"], el_deg=thr["el_deg"],
                az_off_deg=thr["az_off_deg"], cls=cls)


# --------------------------------------------------------------------------------------------- statystyka, równoległość
def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


_RIG = None


def _work(a):
    global _RIG
    seed, name, P = a
    if _RIG is None:
        _RIG = Rig()
    r = run_trial(seed, name, P, rig=_RIG)
    return r


def run_set(seeds, name, P=None, procs=3):
    from multiprocessing import Pool
    with Pool(procs) as pool:
        return pool.map(_work, [(s, name, P) for s in seeds], chunksize=1)


def summarize(rs, label=""):
    n = len(rs)
    k = sum(r["success"] for r in rs)
    lo, hi = wilson(k, n)
    cl = {}
    for r in rs:
        cl[r["cls"]] = cl.get(r["cls"], 0) + 1
    ks = sum(r["success"] and not r["crush"] for r in rs)
    gf = sum(r["dnp01"] for r in rs)
    return (f"{label:<14s} sukces {k:2d}/{n} = {100 * k / n:3.0f} % [{100 * lo:.0f}–{100 * hi:.0f}]  bez zgniecenia {ks:2d}  "
            + ", ".join(f"{a} {b}" for a, b in sorted(cl.items(), key=lambda kv: -kv[1])) + f"  | DNp01 {gf}/{n}")


# --------------------------------------------------------------------------------------------- zestawy wariantów do raportu
WIDE = dict(q_open=1.2, lead=0.2)       # warunek B: szczęki szeroko otwarte w locie (zamykanie z T − 200 ms, dobrane na 100–149)
SETS = {
    "A (lejek Q_OPEN = 0,6 rad, zamykanie od T − 30 ms)": [
        ("ORACLE", "ORACLE", {}), ("NO-CLOSE", "NO-CLOSE", {}), ("ENG", "ENG", {}), ("ENG+VNC", "ENG+VNC", {}),
        ("LOOM+PWM", "LOOM+PWM", {}), ("BIO-ucieczka", "BIO-ucieczka", {}), ("BIO-polowanie", "BIO-polowanie", {}),
        ("BIO-ON-ucieczka", "BIO-ON-ucieczka", {}), ("BIO-ON-polowanie", "BIO-ON-polowanie", {}),
        ("BIO-ON-pol. bez maski", "BIO-ON-polowanie", dict(loom_mask=False)), ("BIO-dotyk", "BIO-dotyk", {})],
    "B (szczęki szeroko 1,2 rad w locie)": [
        ("ORACLE", "ORACLE", WIDE), ("NO-CLOSE", "NO-CLOSE", WIDE), ("ENG", "ENG", WIDE), ("LOOM+PWM", "LOOM+PWM", WIDE),
        ("BIO-ON-polowanie", "BIO-ON-polowanie", WIDE), ("BIO-dotyk", "BIO-dotyk", WIDE)],
}


def run_all(seeds, procs=3):
    out = {}
    for sname, rows in SETS.items():
        for label, v, P in rows:
            t0 = time.time()
            out[(sname, label)] = run_set(seeds, v, P, procs)
            print(f"  {sname[:1]} {label}: {time.time() - t0:.0f} s", flush=True)
    return out


def _med(x, f=".0f"):
    x = [v for v in x if v is not None and np.isfinite(v)]
    return "  -  " if not x else f"{np.median(x):{f}}"


def table(res, sname):
    lines = [f"{'wariant':<22s} {'sukces':>8s} {'%':>4s} {'Wilson 95 %':>11s}  {'klasy porażek':<44s} DNp01  zamk.−T [ms] med (p10…p90)  błąd paszczy [mm] med/p90  |e_y| med  siła 20 ms [N]"]
    for (sn, label), rs in res.items():
        if sn != sname:
            continue
        n = len(rs)
        k = sum(r["success"] for r in rs)
        lo, hi = wilson(k, n)
        cl = {}
        for r in rs:
            if not r["success"]:
                cl[r["cls"]] = cl.get(r["cls"], 0) + 1
        tc = [r["t_close_ms"] for r in rs if r["t_close_ms"] is not None]
        ae = [r["arm_err_mm"] for r in rs]
        ey = [abs(r["e_y_mm"]) for r in rs if np.isfinite(r["e_y_mm"])]
        gf = sum(r["dnp01"] for r in rs)
        tcs = "  -  " if not tc else f"{np.median(tc):5.0f} ({np.percentile(tc, 10):.0f}…{np.percentile(tc, 90):.0f})"
        lines.append(f"{label:<22s} {k:3d}/{n:<4d} {100 * k / n:4.0f} {100 * lo:4.0f}–{100 * hi:<4.0f}  "
                     f"{', '.join(f'{a} {b}' for a, b in sorted(cl.items(), key=lambda kv: -kv[1])) or '-':<44s} {gf:2d}/{n:<3d} "
                     f"{tcs:<26s} {np.median(ae):5.1f} / {np.percentile(ae, 90):5.1f}        {_med(ey, '.1f'):>6s}     {_med([r['hold_N'] for r in rs], '.0f')}")
    return lines


def gf_stats(res):
    lines = []
    for (sn, label), rs in res.items():
        if "BIO" not in label or "dotyk" in label:
            continue
        n = len(rs)
        ms = [r["dnp01_ms"] for r in rs if r["dnp01"]]
        nsp = [r["dnp01_n"] for r in rs if r["dnp01"]]
        esc = sum(r["escape"] for r in rs)
        if ms:
            lines.append(f"  [{sn[:1]}] {label}: DNp01 odpala w {len(ms)}/{n} rzutów ({100 * len(ms) / n:.0f} %), 1. spike względem T: med {np.median(ms):.0f} ms "
                         f"(p10 {np.percentile(ms, 10):.0f}, p90 {np.percentile(ms, 90):.0f}); odpalenia przed T − 100 ms: {sum(m < -100 for m in ms)}, "
                         f"w oknie ±30 ms wokół T: {sum(abs(m) <= 30 for m in ms)}; spike'ów/rzut med {np.median(nsp):.0f}; ucieczek wykonanych {esc}")
        else:
            lines.append(f"  [{sn[:1]}] {label}: DNp01 nie odpala (0/{n}); ucieczek {esc}")
    return lines


def figure(res, rig, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(17, 11))
    gs = fig.add_gridspec(4, 2, width_ratios=[1.0, 1.15], hspace=0.35, wspace=0.18)
    cols = {"ORACLE": "0.35", "NO-CLOSE": "0.6", "ENG": "tab:blue", "ENG+VNC": "tab:cyan", "LOOM+PWM": "tab:olive", "BIO-ucieczka": "tab:red",
            "BIO-polowanie": "tab:orange", "BIO-ON-ucieczka": "tab:pink", "BIO-ON-polowanie": "tab:green", "BIO-ON-pol. bez maski": "tab:brown", "BIO-dotyk": "tab:purple"}
    for gi, sname in enumerate(SETS):
        ax = fig.add_subplot(gs[2 * gi:2 * gi + 2, 0])
        labs = [l for (sn, l) in res if sn == sname]
        for i, l in enumerate(labs):
            rs = res[(sname, l)]
            k, n = sum(r["success"] for r in rs), len(rs)
            lo, hi = wilson(k, n)
            ax.bar(i, 100 * k / n, color=cols.get(l, "k"), yerr=[[max(0.0, 100 * k / n - 100 * lo)], [max(0.0, 100 * hi - 100 * k / n)]], capsize=3)
            ax.text(i, 3, f"{k}/{n}", ha="center", fontsize=8, color="w", rotation=90)
        ax.set_xticks(range(len(labs)))
        ax.set_xticklabels(labs, rotation=35, ha="right", fontsize=8)
        ax.set_ylim(0, 105)
        ax.set_ylabel("sukces [%] (Wilson 95 %)")
        ax.set_title(f"warunek {sname}", fontsize=10)
    # przykładowa próba BIO-ON-polowanie: pierwszy sukces z DNp01
    rs = res[(list(SETS)[0], "BIO-ON-polowanie")]
    pick = next((r for r in rs if r["success"] and r["dnp01"]), rs[0])
    r = run_trial(pick["seed"], "BIO-ON-polowanie", rig=rig, record=True)
    L, T = r["log"], r["T"]
    t = (L["t"] - T) * 1000
    tk = (np.arange(len(r["fF"])) * 1e-3 - T) * 1000
    ax1 = fig.add_subplot(gs[0, 1])
    ax1.plot(t, 1000 * L["dtrue"], "k", label="odległość piłeczki od środka paszczy [mm]")
    ax1.set_ylim(0, 500)
    ax1.set_ylabel("mm")
    ax1b = ax1.twinx()
    ax1b.plot(t, L["q5"], "tab:blue", label="kąt szczęki q [rad]")
    ax1b.plot(t, L["cmd5"], "tab:red", lw=0.8, label="komenda PWM szczęki")
    ax1b.set_ylabel("rad / PWM")
    ax1.set_title(f"przykładowa próba BIO-ON-polowanie, seed {pick['seed']} (T = {T:.2f} s, v = {r['speed']:.1f} m/s): {r['cls']}", fontsize=10)
    h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax1b.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, fontsize=7, loc="upper right")
    ax2 = fig.add_subplot(gs[1, 1], sharex=ax1)
    ax2.plot(t, L["lp"], "tab:green", label="LPLC2: populacja w oknie 10 ms [Hz]")
    ax2.axhline(P0["loom_thr"], color="tab:green", ls=":", lw=0.8)
    ax2.plot(t, 100 * np.maximum(L["loomL"], L["loomR"]), "tab:gray", lw=0.8, label="wejście loom (ON, maks. L/P) × 100")
    ax2.set_ylabel("Hz"); ax2.legend(fontsize=7, loc="upper left")
    ax3 = fig.add_subplot(gs[2, 1], sharex=ax1)
    ax3.eventplot([t[L["gf"]]], colors="tab:red", lineoffsets=1, linelengths=0.8)
    ax3.set_ylim(0, 2); ax3.set_yticks([]); ax3.set_ylabel("DNp01")
    ax3.text(0.01, 0.8, "spike'i DNp01 (Giant Fiber); ucieczka wygaszona stanem „polowanie” (model)", transform=ax3.transAxes, fontsize=8)
    ax4 = fig.add_subplot(gs[3, 1], sharex=ax1)
    ax4.plot(tk, r["fF"][:, 0], label="szczęka stała [N]")
    ax4.plot(tk, r["fF"][:, 1], label="szczęka ruchoma [N]")
    ax4.set_ylabel("siła normalna [N]"); ax4.set_xlabel("czas względem prawdziwego T [ms]"); ax4.legend(fontsize=7)
    for a in (ax1, ax2, ax3, ax4):
        a.axvline(0, color="k", lw=0.6)
        if r["t_close_ms"] is not None:
            a.axvline(r["t_close_ms"], color="tab:red", ls="--", lw=0.8)
    ax4.set_xlim(-150, 150)
    fig.suptitle("Etap 5: łapanie rzuconej piłeczki — warianty (seedy 0–49, jeden przebieg). Przerywana czerwona: chwila zamknięcia, ciągła czarna: prawdziwe T", fontsize=11)
    fig.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)


def _params_line():
    return (f"parametry (strojone na seedach 100–149): sig_y_start = {P0['sig_y_start']} m (1,0 = bez bramki), lead ENG = {P0['lead']} s (warunek B: {WIDE['lead']} s), "
            f"loom_thr = {P0['loom_thr']} Hz (MODEL), próg ON t_on = {P0['t_on']}, g_on0 = {P0['g_on0']}, g_on1 = {P0['g_on1']} (MODEL), maska eferentna "
            f"v_self = {P0['v_self']} rad/s (MODEL), U_CLOSE = {P0['u_close']}, Q_OPEN = {P0['q_open']} (B: {WIDE['q_open']}), F_TOUCH = {F_TOUCH} N")


def report(seeds):
    t0 = time.time()
    res = run_all(seeds)
    out = ["Etap 5 — sterowniki łapania rzuconej piłeczki (throw_catch.py), seedy %d–%d, jeden przebieg" % (seeds[0], seeds[-1]), "",
           _params_line(), ""]
    for sname in SETS:
        out += [f"== warunek {sname} ==", *table(res, sname), ""]
    out += ["== DNp01 (Giant Fiber) w wariantach z mózgiem ==", *gf_stats(res), ""]
    tun = os.path.join(HERE, "results", "stage5_catch_tuning.txt")
    if os.path.exists(tun):
        out += ["== strojenie i walidacja (log z `grid` / `validate`) ==", open(tun).read().rstrip(), ""]
    out.append(f"[czas {time.time() - t0:.0f} s]")
    txt = "\n".join(out)
    open(os.path.join(HERE, "results", "stage5_catch.txt"), "w").write(txt + "\n")
    rig = Rig()
    try:
        figure(res, rig, os.path.join(HERE, "results", "stage5_catch.png"))
    finally:
        rig.close()
    print(txt)


def _parse_seeds(x):
    a, b = x.split(":")
    return list(range(int(a), int(b)))


def _grid(variant, seeds, spec, tag):
    """grid VARIANT a:b TAG key=v1,v2 [key2=...]: iloczyn kartezjański wartości P; wyniki dopisuję do results/stage5_catch_tuning.txt."""
    import itertools
    keys = [k.split("=")[0] for k in spec]
    vals = [[float(v) for v in k.split("=")[1].split(",")] for k in spec]
    path = os.path.join(HERE, "results", "stage5_catch_tuning.txt")
    for combo in itertools.product(*vals):
        P = dict(zip(keys, combo))
        t0 = time.time()
        rs = run_set(seeds, variant, P)
        tc = [r["t_close_ms"] for r in rs if r["t_close_ms"] is not None]
        ts_ = [r["tau_start_ms"] for r in rs if r["tau_start_ms"] is not None]
        extra = (f"  zamk.−T med {np.median(tc):.0f} ms" if tc else "") + (f"  start ruchu T−{np.median(ts_):.0f} ms" if ts_ else "")
        line = f"[{tag} seedy {seeds[0]}–{seeds[-1]}] {variant} {P}: " + summarize(rs).split(" ", 1)[1].lstrip() + extra + f"  ({time.time() - t0:.0f} s)"
        print(line, flush=True)
        open(path, "a").write(line + "\n")


def validate(seeds):
    res = run_all(seeds)
    path = os.path.join(HERE, "results", "stage5_catch_tuning.txt")
    lines = [f"--- walidacja, seedy {seeds[0]}–{seeds[-1]} (parametry zamrożone po strojeniu na 100–149) ---"]
    for sname in SETS:
        lines += [f"  warunek {sname}", *["  " + l for l in table(res, sname)]]
    txt = "\n".join(lines)
    open(path, "a").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "report"
    if mode == "one":
        name, seed = sys.argv[2], int(sys.argv[3])
        t0 = time.time()
        r = run_trial(seed, name, record=False)
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items() if k not in ("log",)}, f"{time.time() - t0:.1f} s")
    elif mode == "grid":
        _grid(sys.argv[2], _parse_seeds(sys.argv[3]), sys.argv[5:], sys.argv[4])
    elif mode == "validate":
        validate(_parse_seeds(sys.argv[2]))
    elif mode == "report":
        report(_parse_seeds(sys.argv[2]) if len(sys.argv) > 2 else list(range(50)))
