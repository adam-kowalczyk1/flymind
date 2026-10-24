"""Etap 3, scenariusz B2 „chwyt” (bio2): piłeczka stacza się z równi w stronę paszczy; agent (agent.py) śledzi ją
wzrokiem (siatkówka → EPG → DNa02/DNa01 skręcają bazę), przy dotyku rdzeń brzuszny (VNC) zamyka szczęki,
potem uniesienie. Wszystkie miary liczone z prawdy MuJoCo (siły kontaktu mj_contactForce, pozycje ciał, segmentacja
obrazu kamery), nie z czujników ani sygnałów wewnętrznych sterownika.

Miary:
  sukces      = środek piłeczki ≥ 3 cm nad położeniem na stole i obie szczęki w kontakcie przez ≥ 1 s
                (okno 1 s: wysokość spełniona przez cały czas, kontakt z obiema szczękami w ≥ 99 % kroków 1 ms);
  zgniecenie  = maks. siła normalna kontaktu szczęka–piłeczka (pojedyncza szczęka, średnia 20 ms jak w v1: pojedynczy
                krok 1 ms z uderzenia 50 g piłeczki daje szpilki 5–10 N bez ściskania) > F_CRUSH; szczyt 1 ms raportowany obok;
  reakcja (i) = od pierwszej widoczności piłeczki (segmentacja ≥ 20 px, jak stage3._ball_visible) do startu ruchu
                bazy (|ω| > 0,05 rad/s przez ≥ 30 ms, z qvel[0]);
  reakcja (ii)= od pierwszego dotyku piłeczki z ramieniem do pewnego chwytu (obie szczęki ≥ F_SECURE przez 50 ms);
  stabilność  = średnia i współczynnik zmienności (σ/μ) sumarycznej siły szczęk w oknie trzymania, poślizg =
                przesunięcie piłeczki względem chwytaka (układ ciała `gripper`) w oknie trzymania [mm].
Klasyfikacja porażek (kolejność reguł): chybienie (piłeczka nigdy nie dotknęła ramienia) → zgniecenie (szczyt siły
> F_CRUSH) → upuszczenie (był pewny chwyt, a okna trzymania brak) → przepchnięcie (bez pewnego chwytu, piłeczkę
odepchnęła poruszająca się baza/chwytak: prędkość punktu `aim` > V_PUSH w czasie kontaktu) → wytoczenie (bez
pewnego chwytu, piłeczka wytoczyła się z paszczy własnym pędem).

Uruchom:  python stage3_b2.py tune 100 120 | val 120 140 | report   (patrz __main__)
"""
import hashlib
import os
import sys
import time
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

import scene2
import so101_base as sb
import agent as agent_mod
from agent import Agent
from stage3 import _seg, _ball_visible

HERE = os.path.dirname(os.path.abspath(__file__))
F_CRUSH = 5.0          # N
F_SECURE = agent_mod.F_SECURE
LIFT_H = 0.03          # m
HOLD_T = 1.0           # s
V_PUSH = 0.03          # m/s, prędkość `aim` w kontakcie uznawana za „pchanie”
N_REP = 10

# --- parametry sceny B2 (nasze, strojone na seedach 100–119) ---
P0 = dict(
    ramp=12.0,                  # stopnie (równia z v1; ramp_deg=12)
    ramp_L=0.16,                # długość równi [m] (v1: 0,16)
    s0=0.85,                    # start wzdłuż równi (ułamek długości) jak w v1
    y_range=(-0.01, 0.09),      # boczne przesunięcie startu piłeczki [m]: ±5 cm wokół środka okna chwytu bez skrętu (+4 cm)
    vy_range=(0.0, 0.0),        # boczna prędkość początkowa [m/s]
    T=5.0,                      # s
    q_open=0.93,                # rozwarcie szczęk w oczekiwaniu [rad] (scene2.reset_scene)
    W_MAX=0.6,                  # rad/s, maks. prędkość obrotu bazy (agent.W_MAX; domyślnie 1,0 — przy 1,0 baza spychała piłeczkę)
    no_turn=False,              # kontrola: baza zablokowana (pokazuje, że zadanie wymaga skrętu)
    dn_ref=False,               # poprawka startu odczytu DNa02/DNa01 (B2Agent); False = agent.py bez zmian
)

P_FINAL = dict(P0)             # konfiguracja raportu (po strojeniu na seedach 100–119 i walidacji 120–139)


class B2Agent(Agent):
    """Agent z opcjonalną poprawką startu odczytu skrętu (`dn_ref`). W agent.py filtry DNa02/DNa01 startują od zera,
    a kalibracja trymu (offset) dotyczy stanu aktywnego (wzgórze na celu) — po rozpoczęciu polowania wolny filtr DNa01
    (τ 0,4 s) przez ~0,4 s pokazuje „kąt = −offset/slope”, czyli stały skręt w lewo (zmierzone: offset ≈ −3…−5 Hz,
    slope ≈ 15 Hz/rad → ~+0,2 rad). Poprawka: poza polowaniem filtr stoi na offsecie (odczyt = 0°)."""

    def __init__(self, *a, dn_ref=False, **kw):
        self.dn_ref = dn_ref
        super().__init__(*a, **kw)

    def step(self):
        if self.dn_ref and self.d.time >= self.hunt_until:
            self.dn_f = self.brain.steer["offset"].copy()
        return super().step()


def load_scene(ramp_deg, L):
    """scene2.load(ramp_deg) z równią o długości L (v1: 0,16 m); dolny koniec równi nadal przy x = 0,45."""
    root = ET.fromstring(scene2.build_xml(ramp_deg=ramp_deg))
    g = next(g for g in root.iter("geom") if g.get("name") == "ramp")
    a = np.radians(ramp_deg)
    g.set("size", f"{L / 2} 0.12 0.004")
    g.set("pos", f"{0.45 + 0.5 * L * np.cos(a)} 0 {0.5 * L * np.sin(a) - 0.004 * np.cos(a)}")
    m = mujoco.MjModel.from_xml_string(ET.tostring(root, encoding="unicode"))
    m.vis.global_.offwidth, m.vis.global_.offheight = max(scene2.CAM_W, 1280), max(scene2.CAM_H, 720)
    return m, mujoco.MjData(m)


def _robot_geoms(m):
    bid = m.body("ball").id
    return np.array([g for g in range(m.ngeom) if m.geom_bodyid[g] != 0 and m.geom_bodyid[g] != bid])


def _forces(m, d, ball, pads, palm, robot):
    """Siły normalne kulka–pad (stała, ruchoma), kulka–dłoń i liczba kontaktów kulka–ramię, z mj_contactForce."""
    out = np.zeros(3)
    n_rob = 0
    f6 = np.zeros(6)
    for i in range(d.ncon):
        c = d.contact[i]
        if ball not in (c.geom1, c.geom2):
            continue
        o = c.geom2 if c.geom1 == ball else c.geom1
        if o in robot:
            n_rob += 1
        for k, pg in enumerate((*pads, palm)):
            if o == pg:
                mujoco.mj_contactForce(m, d, i, f6)
                out[k] += abs(f6[0])
    return out, n_rob


def run_trial(seed, P=None, record=False, calib=None):
    P = dict(P0, **(P or {}))
    rng = np.random.default_rng(seed)
    if P["W_MAX"] is not None:
        agent_mod.W_MAX = P["W_MAX"]
    m, d = load_scene(P["ramp"], P["ramp_L"])
    q, _ = scene2.reset_scene(m, d, q_open=P["q_open"])
    a, L = np.radians(P["ramp"]), P["ramp_L"]
    y0 = float(rng.uniform(*P["y_range"]))
    vy0 = float(rng.uniform(*P["vy_range"]))
    bj, bv = m.joint("ball").qposadr[0], m.joint("ball").dofadr[0]
    s = P["s0"]
    d.qpos[bj:bj + 7] = [0.45 + s * L * np.cos(a), y0, s * L * np.sin(a) + sb.BALL_R / np.cos(a) + 0.001, 1, 0, 0, 0]
    d.qvel[bv:bv + 6] = [0, vy0, 0, -vy0 / sb.BALL_R, 0, 0]
    mujoco.mj_forward(m, d)
    ag = B2Agent(m, d, seed=seed, q_catch=q, calib=calib, dn_ref=P["dn_ref"])
    sr, opt = _seg(m)
    ball = m.geom("ball").id
    pads = (m.geom("jaw_fixed").id, m.geom("jaw_moving").id)
    palm = m.geom("palm").id
    robot = set(_robot_geoms(m).tolist())
    q_base0 = d.qpos[0]
    n_ctl = int(P["T"] / 0.01)
    # --- zapisy: co 1 ms (siły, pozycje), co 10 ms (widoczność, baza) ---
    F = np.zeros((n_ctl * 10, 3))
    NR = np.zeros(n_ctl * 10, int)
    BZ = np.zeros(n_ctl * 10)
    REL = np.zeros((n_ctl * 10, 3))
    VAIM = np.zeros(n_ctl * 10)
    px = np.zeros(n_ctl)
    wpan = np.zeros(n_ctl)
    qpan = np.zeros(n_ctl)
    az_ball = np.zeros(n_ctl)
    az_aim = np.zeros(n_ctl)
    tauj = np.zeros(n_ctl)
    dnf = np.zeros((n_ctl, 2))
    qj = np.zeros(n_ctl)
    prev_aim = d.site("aim").xpos.copy()
    for k in range(n_ctl):
        px[k] = _ball_visible(m, d, sr, opt)
        ag.step()
        if P["no_turn"]:
            d.ctrl[0] = q_base0
        for j in range(10):
            mujoco.mj_step(m, d)
            i = 10 * k + j
            F[i], NR[i] = _forces(m, d, ball, pads, palm, robot)
            bp = d.body("ball").xpos
            BZ[i] = bp[2]
            R = d.body("gripper").xmat.reshape(3, 3)
            REL[i] = R.T @ (bp - d.body("gripper").xpos)
            aim = d.site("aim").xpos
            VAIM[i] = np.linalg.norm(aim - prev_aim) / m.opt.timestep
            prev_aim = aim.copy()
        wpan[k] = d.qvel[0]
        qpan[k] = d.qpos[0]
        b = d.body("ball").xpos
        az_ball[k] = np.arctan2(b[1], b[0])
        az_aim[k] = ag._aim_az()
        tauj[k] = ag.log["tau"][-1]
        dnf[k] = ag.dn_f
        qj[k] = d.qpos[5]
    ag.close()
    sr.close()
    out = analyse(seed, P, y0, F, NR, BZ, REL, VAIM, px, wpan, qpan)
    out["peak_ball_x"] = float(d.body("ball").xpos[0])
    if record:
        out["log"] = {k: np.array(v) for k, v in ag.log.items()}
        out.update(F=F, px=px, wpan=wpan, qpan=qpan, az_ball=az_ball, az_aim=az_aim, tau=tauj, qj=qj, BZ=BZ, REL=REL, dnf=dnf)
    return out


def _runs(mask):
    """Początki i długości odcinków True."""
    x = np.concatenate([[0], mask.astype(int), [0]])
    dx = np.diff(x)
    st, en = np.where(dx == 1)[0], np.where(dx == -1)[0]
    return st, en - st


def analyse(seed, P, y0, F, NR, BZ, REL, VAIM, px, wpan, qpan):
    n = len(F)
    Ff, Fm = F[:, 0], F[:, 1]
    Fs = Ff + Fm
    peak = float(max(Ff.max(), Fm.max()))
    peak20 = float(max(np.convolve(f, np.ones(20) / 20, "same").max() for f in (Ff, Fm)))
    contact_any = NR > 0
    first_touch = int(np.argmax(contact_any)) if contact_any.any() else None
    both = (np.minimum(Ff, Fm) > 0.05)
    lifted = (BZ - sb.BALL_R) >= LIFT_H
    # okno trzymania 1 s: wysokość przez cały czas, kontakt obiema szczękami w ≥ 99 % kroków
    W = int(HOLD_T * 1000)
    cl, cb = np.concatenate([[0], np.cumsum(~lifted)]), np.concatenate([[0], np.cumsum(both)])
    t_hold = None
    for i in range(0, n - W + 1):
        if cl[i + W] - cl[i] == 0 and cb[i + W] - cb[i] >= 0.99 * W:
            t_hold = i
            break
    # pewny chwyt (obie szczęki ≥ F_SECURE przez 50 ms) po pierwszym dotyku
    sec = np.minimum(Ff, Fm) >= F_SECURE
    t_secure = None
    if first_touch is not None:
        st, ln = _runs(sec)
        ok = [(a, l) for a, l in zip(st, ln) if a + l > first_touch and l >= 50]
        if ok:
            t_secure = max(ok[0][0], first_touch)
    # reakcja (i): widoczność → ruch bazy
    vis = np.where(px > 20)[0]
    t_vis = int(vis[0]) * 0.01 if len(vis) else None
    mv = np.abs(wpan) > 0.05
    st, ln = _runs(mv)
    t_move = None
    if t_vis is not None:
        c = [a for a, l in zip(st, ln) if l >= 3 and a * 0.01 >= t_vis]
        t_move = c[0] * 0.01 if c else None
    out = dict(seed=seed, y0_cm=100 * y0, peak=peak, peak20=peak20, t_touch=None if first_touch is None else first_touch / 1000,
               t_vis=t_vis, t_move=t_move,
               react_move_ms=None if (t_vis is None or t_move is None) else 1000 * (t_move - t_vis),
               react_grip_ms=None if (t_secure is None or first_touch is None) else float(t_secure - first_touch),
               base_turn_deg=float(np.degrees(qpan.max() - qpan.min())), base_net_deg=float(np.degrees(qpan[-1] - qpan[0])),
               crushed=peak20 > F_CRUSH, success=t_hold is not None, secured=t_secure is not None)
    if t_hold is not None:
        w = slice(t_hold, t_hold + W)
        fs = Fs[w]
        rel = REL[w] * 1000
        out.update(f_mean=float(fs.mean()), f_cv=float(fs.std() / fs.mean()), slip_mm=float(np.linalg.norm(rel[-1] - rel[0])),
                   slip_max_mm=float(np.linalg.norm(rel - rel.mean(0), axis=1).max()), t_hold=t_hold / 1000)
    # klasyfikacja
    if t_hold is not None:
        cls = "zgniecenie*" if out["crushed"] else "sukces"      # * = uniesiona, ale szczyt siły > F_CRUSH
    elif first_touch is None:
        cls = "chybienie"
    elif out["crushed"]:
        cls = "zgniecenie"
    elif t_secure is not None:
        cls = "upuszczenie"
    else:
        pushing = contact_any & (VAIM > V_PUSH) & (F.max(1) > 0.05)
        cls = "przepchnięcie" if pushing.sum() >= 20 else "wytoczenie"
    out["cls"] = cls
    return out


def _fmt(r):
    f = lambda v, p=0: "  -  " if v is None else f"{v:.{p}f}"
    return (f"{r['seed']:4d} y0={r['y0_cm']:+5.1f}cm  {r['cls']:<13s} szczyt={r['peak']:5.2f}N (20ms {r['peak20']:4.2f})  "
            f"reakcja_ruch={f(r['react_move_ms'])}ms  reakcja_chwyt={f(r['react_grip_ms'])}ms  "
            f"baza={r['base_turn_deg']:.1f}°  F={f(r.get('f_mean'), 2)}N CV={f(r.get('f_cv'), 2)} poślizg={f(r.get('slip_mm'), 1)}mm")


def _one(a):
    seed, P = a
    return run_trial(seed, P)


def _meta():
    """md5 używanych plików (inni zmieniają je w trakcie pracy)."""
    return ", ".join(f"{f} {hashlib.md5(open(os.path.join(HERE, f), 'rb').read()).hexdigest()[:10]}"
                     for f in ("agent.py", "brain.py", "vision.py", "retina.py", "vnc.py", "snn.py", "scene2.py",
                               "so101_base.py", "stage3.py", "stage3_b2.py"))


def run_set(seeds, P=None, procs=3, verbose=True):
    from multiprocessing import Pool
    t0 = time.time()
    with Pool(procs) as pool:
        rs = pool.map(_one, [(s, P) for s in seeds])
    if verbose:
        for r in rs:
            print(_fmt(r))
        print(summary(rs), f"[{time.time() - t0:.0f} s]", _meta())
    return rs


def summary(rs):
    n = len(rs)
    ok = [r for r in rs if r["success"]]
    clean = [r for r in ok if not r["crushed"]]
    c = {}
    for r in rs:
        c[r["cls"]] = c.get(r["cls"], 0) + 1
    return f"n={n} sukces {len(ok)}/{n} (bez zgniecenia {len(clean)}/{n}) klasy {c}"


# ------------------------------------------------------------------ raport (seedy 0–9, JEDEN przebieg)
CLS_COLOR = {"sukces": "tab:green", "zgniecenie*": "tab:olive", "zgniecenie": "tab:red", "chybienie": "tab:gray",
             "wytoczenie": "tab:blue", "przepchnięcie": "tab:orange", "upuszczenie": "tab:purple"}


def _rec(a):
    seed, P = a
    return run_trial(seed, P, record=True)


def _ms(rs, key, fmt="{:.0f}"):
    v = [r[key] for r in rs if r.get(key) is not None and np.isfinite(r[key])]
    return "brak danych" if not v else f"{fmt.format(np.mean(v))} ± {fmt.format(np.std(v))} (n={len(v)})"


def _classes(rs):
    c = {}
    for r in rs:
        c[r["cls"]] = c.get(r["cls"], 0) + 1
    return ", ".join(f"{k} {v}" for k, v in sorted(c.items(), key=lambda kv: -kv[1]))


def _counts(rs):
    n = len(rs)
    ok = sum(r["success"] for r in rs)
    c_inst = sum(r["peak"] > F_CRUSH for r in rs)
    c_20 = sum(r["peak20"] > F_CRUSH for r in rs)
    clean = sum(r["success"] and not r["crushed"] for r in rs)
    return f"sukces {ok}/{n} ({100 * ok / n:.0f} %), sukces bez zgniecenia {clean}/{n}, szczyt > {F_CRUSH:g} N: {c_inst}/{n} (chwilowy, 1 ms), {c_20}/{n} (średnia 20 ms = miara zgniecenia)"


def report(seeds=range(N_REP), procs=3, outdir=os.path.join(HERE, "results")):
    from multiprocessing import Pool
    seeds = list(seeds)
    t0 = time.time()
    with Pool(procs) as pool:
        out = pool.map(_rec, [(s, P_FINAL) for s in seeds] + [(s, dict(P_FINAL, no_turn=True)) for s in seeds])
    main, ctrl = out[:len(seeds)], out[len(seeds):]
    L = ["Etap 3, scenariusz B2 „chwyt” (bio2) — piłeczka z równi do paszczy, śledzenie wzrokiem, chwyt VNC, uniesienie",
         f"seedy {seeds[0]}–{seeds[-1]} ({len(seeds)} prób), jeden przebieg; md5 plików: {_meta()}",
         f"parametry sceny: {P_FINAL}", "",
         "Miary (z prawdy MuJoCo: mj_contactForce, pozycje ciał, segmentacja kamery; niezależne od czujników sterownika):",
         f"  sukces = środek piłeczki ≥ {LIFT_H * 100:g} cm nad stołem przez cały czas okna {HOLD_T:g} s, obie szczęki w kontakcie w ≥ 99 % kroków 1 ms",
         f"  zgniecenie = maks. średniej 20 ms siły normalnej szczęka–piłeczka (miara v1) > {F_CRUSH:g} N; podaję też szczyt chwilowy (1 ms)",
         "  reakcja (i) = pierwsza widoczność (≥ 20 px) → start ruchu bazy (|ω| > 0,05 rad/s przez ≥ 30 ms)",
         f"  reakcja (ii) = pierwszy dotyk piłeczki z ramieniem → pewny chwyt (obie szczęki ≥ {F_SECURE:g} N przez 50 ms)",
         "  siła trzymania: średnia sumy sił obu szczęk w oknie trzymania; CV = σ/μ (krok 1 ms); poślizg = przesunięcie piłeczki w układzie chwytaka (okno trzymania)",
         "  porażki: chybienie / zgniecenie / upuszczenie (był pewny chwyt) / przepchnięcie (kontakt z ruchem `aim` > "
         f"{V_PUSH * 100:g} cm/s) / wytoczenie (reszta). * = uniesiona, ale szczyt siły > {F_CRUSH:g} N", "",
         "WYNIKI (agent z siatkówką → EPG → DNa02/DNa01 → VNC):"]
    L += [_fmt(r) for r in main]
    L += ["", "PODSUMOWANIE: " + _counts(main), "  klasy: " + _classes(main),
          f"  reakcja (i) widoczność → ruch bazy [ms]: {_ms(main, 'react_move_ms')}",
          f"  reakcja (ii) dotyk → pewny chwyt [ms] (tylko próby z pewnym chwytem): {_ms(main, 'react_grip_ms')}",
          f"  siła trzymania [N]: {_ms([r for r in main if r['success']], 'f_mean', '{:.2f}')}; CV: {_ms([r for r in main if r['success']], 'f_cv', '{:.2f}')}",
          f"  poślizg w oknie trzymania [mm]: {_ms([r for r in main if r['success']], 'slip_mm', '{:.1f}')} (maks. odchylenie {_ms([r for r in main if r['success']], 'slip_max_mm', '{:.1f}')})",
          f"  szczyt siły chwilowy [N]: {_ms([r for r in main if r['peak'] > 0], 'peak', '{:.1f}')}, średnia 20 ms: {_ms([r for r in main if r['peak'] > 0], 'peak20', '{:.1f}')}",
          "", "KONTROLA — te same seedy z zablokowaną bazą (bez skrętu): " + _counts(ctrl), "  klasy: " + _classes(ctrl),
          "  (zakres bocznego startu piłeczki wybrany tak, że tylko część położeń trafia w paszczę bez skrętu bazy)"]
    L += [_fmt(r) for r in ctrl]
    L += ["", f"czas obliczeń: {time.time() - t0:.0f} s"]
    txt = "\n".join(L)
    open(os.path.join(outdir, "stage3_b2.txt"), "w").write(txt + "\n")
    print(txt)
    _plot(main, ctrl, outdir)
    return main, ctrl


def _plot(main, ctrl, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ex = next((r for r in main if r["success"]), main[0])
    t10 = np.arange(len(ex["qpan"])) * 0.01
    t1 = np.arange(len(ex["F"])) / 1000
    fig = plt.figure(figsize=(15, 10))
    gs = fig.add_gridspec(4, 2, width_ratios=[1.35, 1], hspace=0.45, wspace=0.28)
    ax = [fig.add_subplot(gs[i, 0]) for i in range(4)]
    d = np.degrees
    ax[0].plot(t10, d(ex["az_ball"]), "g", label="azymut piłeczki (z osi bazy)")
    ax[0].plot(t10, d(ex["az_aim"]), "k", label="azymut paszczy (`aim`)")
    ax[0].plot(t10, -d(ex["qpan"] - ex["qpan"][0]), "r--", lw=1, label="kąt bazy −Δq_pan (+ = w lewo)")
    ax[0].set_ylabel("kąt [°]")
    ax[0].set_ylim(-35, 35)
    ax[0].legend(fontsize=7, loc="upper right")
    ax[0].set_title(f"przykładowa próba: seed {ex['seed']}, y0 = {ex['y0_cm']:+.1f} cm, wynik: {ex['cls']}", fontsize=10)
    ax[1].plot(t10, ex["dnf"][:, 0], label="DNa02 L−R (filtr 0,1 s)")
    ax[1].plot(t10, ex["dnf"][:, 1], label="DNa01 L−R (filtr 0,4 s)")
    ax[1].set_ylabel("L−R [Hz]")
    ax[1].legend(fontsize=7, loc="upper right")
    ax[2].plot(t1, ex["F"][:, 0], label="szczęka stała", lw=0.8)
    ax[2].plot(t1, ex["F"][:, 1], label="szczęka ruchoma", lw=0.8)
    ax[2].axhline(F_CRUSH, color="r", ls=":", lw=1, label=f"F_CRUSH {F_CRUSH:g} N")
    ax[2].set_ylabel("siła kontaktu [N]\n(mj_contactForce)")
    ax[2].legend(fontsize=7, loc="upper right")
    ax[3].plot(t10, ex["tau"], "m", label="τ chwytaka z VNC [N·m] (+ = zamykanie)")
    ax[3].set_ylabel("τ [N·m]")
    a2 = ax[3].twinx()
    a2.plot(t1, 100 * (ex["BZ"] - sb.BALL_R), "c", lw=1, label="wysokość piłeczki nad stołem [cm]")
    a2.axhline(100 * LIFT_H, color="c", ls=":", lw=1)
    a2.set_ylabel("wysokość [cm]")
    ax[3].set_xlabel("czas [s]")
    ax[3].legend(fontsize=7, loc="upper left")
    a2.legend(fontsize=7, loc="upper right")
    for a in ax:
        a.grid(alpha=0.3)
        a.set_xlim(0, t10[-1])
    # podsumowanie 10 prób
    b1 = fig.add_subplot(gs[0:2, 1])
    for rs, mk, lab in ((main, "o", "agent"), (ctrl, "x", "kontrola: baza zablokowana")):
        for r in rs:
            b1.scatter(r["y0_cm"], r["peak"], c=CLS_COLOR[r["cls"]], marker=mk, s=60 if mk == "o" else 45, linewidths=1.5)
    b1.axhline(F_CRUSH, color="r", ls=":", lw=1)
    b1.set_xlabel("start boczny piłeczki y0 [cm]")
    b1.set_ylabel("szczyt siły szczęka–piłeczka [N]")
    b1.set_title("10 prób: kółko = agent, krzyżyk = kontrola bez skrętu bazy", fontsize=9)
    from matplotlib.lines import Line2D
    b1.legend([Line2D([], [], marker="o", ls="", color=c) for c in CLS_COLOR.values()], list(CLS_COLOR), fontsize=7, ncol=2)
    b1.grid(alpha=0.3)
    b2 = fig.add_subplot(gs[2, 1])
    x = np.arange(len(main))
    b2.bar(x - 0.2, [r["react_move_ms"] or 0 for r in main], 0.4, label="(i) widoczność → ruch bazy")
    b2.bar(x + 0.2, [r["react_grip_ms"] or 0 for r in main], 0.4, label="(ii) dotyk → pewny chwyt")
    b2.set_xticks(x, [str(r["seed"]) for r in main])
    b2.set_ylabel("reakcja [ms]")
    b2.set_xlabel("seed")
    b2.legend(fontsize=7)
    b3 = fig.add_subplot(gs[3, 1])
    ok = [r for r in main if r["success"]]
    if ok:
        xx = np.arange(len(ok))
        b3.bar(xx, [r["f_mean"] for r in ok], 0.5, yerr=[r["f_mean"] * r["f_cv"] for r in ok], color="tab:green", capsize=3)
        for i, r in enumerate(ok):
            b3.text(i, 0.1, f"{r['slip_mm']:.1f} mm", ha="center", fontsize=7, color="w", rotation=90)
        b3.set_xticks(xx, [str(r["seed"]) for r in ok])
    b3.set_ylabel("siła trzymania [N] ± σ\n(w słupku: poślizg)")
    b3.set_xlabel("seed (próby z sukcesem)")
    fig.suptitle(f"bio2 Etap 3, B2 „chwyt”: sukces {sum(r['success'] for r in main)}/{len(main)} (kontrola bez skrętu bazy: "
                 f"{sum(r['success'] for r in ctrl)}/{len(ctrl)})", fontsize=12)
    fig.savefig(os.path.join(outdir, "stage3_b2.png"), dpi=110, bbox_inches="tight")




if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "one":
        print(_fmt(run_trial(int(sys.argv[2]))))
    elif mode == "report":          # seedy 0–9, JEDEN przebieg → results/stage3_b2.txt/png
        report(range(N_REP))
    else:                           # tune 100 120 | val 120 140 [słownik zmian parametrów]
        run_set(range(int(sys.argv[2]), int(sys.argv[3])), eval(sys.argv[4]) if len(sys.argv) > 4 else None)
