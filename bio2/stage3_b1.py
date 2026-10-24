"""Etap 3, scenariusz B1 „ucieczka” (bio2): czarna kula (r 8 cm) leci na kamerę → looming (LC4/LPLC2) → DNp01 → wyrzut ramienia.

Próba drapieżnika: Agent w pozie chwytu, piłeczka odstawiona poza pole widzenia, kula startuje 1,2 m od kamery
(kierunek: oś kamery ±15° w azymucie, na wysokości kamery), po 0,5 s ciszy leci po prostej na punkt, w którym stała kamera
na starcie, ze stałą prędkością U(1,0; 2,0) m/s (losowane z ziarna). Miary liczone z prawdy MuJoCo (pozycje ciał i kamery w tym
samym stanie), sterownik dostarcza tylko chwilę spike'a DNp01 (escape_t) i, dla drugiej definicji opóźnienia, pierwszą klatkę loom > 0:
  sukces = pierwszy spike DNp01 po starcie kuli i zanim środek kuli zbliżył się do kamery na ≤ 0,10 m;
  opóźnienie od chwili 0,30 m (oraz od pierwszego loom > 0); odległość kuli przy spike'u;
  czas od spike'a do odsunięcia chwytaka (punkt „aim”) o 2 cm od jego położenia w chwili spike'a [ms] i odległość kuli wtedy;
  to samo wg położenia z chwili startu kuli (t_ret0 — może wyprzedzać spike, gdy baza śledzi kulę).
Rozdzielczość czasu: 10 ms (okno kroku sterownika; spike w oknie [t, t+10 ms) liczony jako t).
Kontrole fałszywych ucieczek (3 s): (a) obrót własny bazy ±1,8 rad/s (a′ — okres 0,75 s, ok. ±3 rad/s) (d.ctrl[0] nadpisane po ag.step(); obwiednia 0,6 s: start sin(ωt) bez niej daje skok prędkości 0→2,8 rad/s) z kopią eferentną i bez;
(b) piłeczka wtacza się w paszczę (b1 równia 9–14°, b2 toczenie w poprzek bez przesłony); (c) sama scena (w (a) i (c) przesłona stoi w polu widzenia jak w vision_calib). Miara: % prób z jakimkolwiek
spike'em DNp01.
Użycie (z pliku, bo multiprocessing): python stage3_b1.py tune|val|final [klucz=wartość ...]; final zapisuje results/stage3_b1.{txt,png}.
Strojenie tylko na ziarnach 100–119, walidacja 120–139, raport końcowy 0–9 (jeden przebieg).
Strojony jeden parametr: G_LOOM0 (próg przyrostu obszaru OFF w vision.py) 15 → 20 przez nadpisanie vision.G_LOOM0 w tym pliku (vision.py
nietknięty). Przy 15 piłeczka stoczona w paszczę dawała fałszywą ucieczkę (10 % na 100–119, 40 % na 120–139); przy 20 — 0 %, a spike
drapieżnika przychodzi ~2 cm później. Po poprawce pierwszych klatek w vision.py sprawdzone ponownie na bieżących plikach: przy 15 równia 8/40 (100–139) → zostaje 20.
Ceną jest utrata rozstrzygającej roli kopii eferentnej w kontroli (a), stąd kontrola (a′) z silniejszym obrotem.
"""
import os
import sys
from multiprocessing import Pool

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mujoco
import numpy as np

import scene2
import vision
from agent import Agent
from brain import Brain

HERE = os.path.dirname(os.path.abspath(__file__))
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]

# --- nasze stałe sceny B1 ---
D_START = 1.2               # m, start kuli od kamery
YAW_MAX = np.radians(15)    # kierunek lotu względem osi kamery
V_RANGE = (1.0, 2.0)        # m/s
T_QUIET = 0.5               # s, kula stoi przed startem (siatkówka się ustala)
T_PRED = 2.5                # s, długość próby drapieżnika
T_CTRL = 3.0                # s, długość prób kontrolnych (po T_QUIET)
N_PRE = 30                  # klatek siatkówki bez mózgu przed próbą (czujnik już działa; bez tego pierwsze klatki dają przejściowy OFF)
D_ESC = 0.10                # m, „za późno”: środek kuli (powierzchnia 2 cm od kamery)
D_REF = 0.30                # m, chwila odniesienia opóźnienia
RETREAT = 0.02              # m, odsunięcie chwytaka
ROT_A, ROT_T = 0.39, 1.2    # rad, s: q0 ± 0,39 rad (zmierzone na qvel ±1,8 rad/s; vision_calib: 0,35); obwiednia 0,6 s na starcie
ROT2_T = 0.75              # s, kontrola (a′): ta sama amplituda, okres 0,75 s → ok. ±3 rad/s
VARIANTS = ["pred", "rot_eff", "rot_noeff", "rot2_eff", "rot2_noeff", "ramp", "cross", "bare"]
V0 = dict(g0=vision.G_LOOM0, g1=vision.G_LOOM1, t_l2=vision.T_L2)
PAR = dict(g0=20)           # strojone na ziarnach 100–119: G_LOOM0 vision.py 15 → 20 (patrz niżej); reszta domyślna
_calib = None


def _calib_ring():
    global _calib
    if _calib is None:
        b = Brain(seed=0)
        b.calibrate_ring()
        _calib = b.calib
    return _calib


def _first(t, mask):
    i = np.flatnonzero(mask)
    return (t[i[0]], int(i[0])) if len(i) else (np.nan, None)


def run_trial(args):
    kind, seed, par, record = args
    par = dict(PAR, **(par or {}))
    vision.G_LOOM0, vision.G_LOOM1 = par.get("g0", V0["g0"]), par.get("g1", V0["g1"])
    rng = np.random.default_rng(seed)
    ramp = rng.uniform(9, 14) if kind == "ramp" else None
    m, d = scene2.load(ramp_deg=ramp)
    if kind == "ramp":                                   # jak vision_calib / v1: piłeczka na szczycie równi
        q, _ = scene2.scene.ik_catch_pose(m, d, r=0.28)
        mujoco.mj_resetData(m, d)
        d.qpos[:5], d.qpos[5], d.ctrl[:5] = q, 0.93, q
        bj = m.joint("ball").qposadr[0]
        d.qpos[bj + 1] = rng.uniform(-0.06, 0.06)
        d.qvel[m.joint("ball").dofadr[0] + 1] = rng.uniform(-0.05, 0.05)
    elif kind == "cross":                                # jak scenariusz A, ale bez przesłony
        q, _ = scene2.reset_scene(m, d, ball_y0=rng.uniform(0.12, 0.16), ball_vy=-rng.uniform(0.09, 0.12))
    else:                                                # piłeczka daleko poza polem widzenia
        q, _ = scene2.reset_scene(m, d, ball_y0=3.0, ball_vy=0.0)
    if kind.startswith("rot") or kind == "bare":         # nieruchoma przesłona w polu widzenia: krawędzie dają fałszywy looming przy obrocie
        scene2.set_mocap(m, d, "occluder", (scene2.OCC_X, 0.0, 0.05))
    mujoco.mj_forward(m, d)
    brain = Brain(seed=seed, params={k: par[k] for k in ("loom_gain", "bias_dn_other") if k in par})
    ag = Agent(m, d, seed=seed, memory="pred", efference=not kind.endswith("noeff"), q_catch=q, calib=_calib_ring(), brain=brain)
    if kind == "pred":
        cam0 = d.cam("eye").xpos.copy()
        fwd = -d.cam("eye").xmat.reshape(3, 3)[:, 2]
        yaw = rng.uniform(-YAW_MAX, YAW_MAX)
        c, s = np.cos(yaw), np.sin(yaw)
        u = np.array([c * fwd[0] - s * fwd[1], s * fwd[0] + c * fwd[1], 0.0])
        u /= np.linalg.norm(u)
        p0 = cam0 + D_START * u
        speed = rng.uniform(*V_RANGE)
        T = T_PRED
    else:
        T = T_QUIET + T_CTRL
        if kind in ("ramp", "cross"):
            bj, bv = m.joint("ball").qposadr[0], m.joint("ball").dofadr[0]
            q_ball, v_ball = d.qpos[bj:bj + 7].copy(), d.qvel[bv:bv + 6].copy()
    for _ in range(N_PRE):                               # rozgrzewka samej siatkówki/widzenia (kula i piłeczka stoją)
        if kind == "pred":
            scene2.set_mocap(m, d, "predator", p0)
            mujoco.mj_forward(m, d)
        ag.r.update_scene(d, camera="eye", scene_option=ag.opt)
        ag.vision.step(ag.r.render())
    dn = np.concatenate([ag.brain.groups["DNp01_L"], ag.brain.groups["DNp01_R"]])
    rec = dict(loomL=[], loomP=[], dnrate=[], spk=[], grow=[], dball=[])
    if record:
        orig = ag.brain.step10

        def wrapped(**kw):
            s = orig(**kw)
            rec["spk"].append(s[:, dn].copy())
            rec["dnrate"].append(float(ag.brain.rate[dn].mean()))
            return s
        ag.brain.step10 = wrapped
    n = int(T * 100)
    t_, dist, aim, wmax = np.zeros(n), np.full(n, np.nan), np.zeros((n, 3)), 0.0
    for k in range(n):
        t = k * 0.01
        if kind == "pred":
            tt = max(t - T_QUIET, 0.0)
            scene2.set_mocap(m, d, "predator", p0 + (cam0 - p0) / D_START * speed * tt)
            mujoco.mj_forward(m, d)
            dist[k] = np.linalg.norm(d.body("predator").xpos - d.cam("eye").xpos)
        if kind in ("ramp", "cross"):                    # piłeczka trzymana do T_QUIET, potem puszczona
            if t < T_QUIET:
                d.qpos[bj:bj + 7], d.qvel[bv:bv + 6] = q_ball, 0.0
            elif k == int(T_QUIET * 100):
                d.qvel[bv:bv + 6] = v_ball
        t_[k], aim[k] = d.time, d.site("aim").xpos
        v = ag.step()
        rec["loomL"].append(v["loom"][0])
        rec["loomP"].append(v["loom"][1])
        rec["grow"].append(max(v["grow"]))
        rec["dball"].append(float(np.linalg.norm(d.body("ball").xpos - d.cam("eye").xpos)))
        if kind.startswith("rot"):
            if t >= T_QUIET:
                tau = t - T_QUIET                    # sinus ±A wokół q0 z obwiednią 0,6 s (bez skoku prędkości na starcie)
                d.ctrl[0] = q[0] + ROT_A * np.sin(2 * np.pi * tau / (ROT2_T if kind.startswith("rot2") else ROT_T)) * min(1.0, tau / 0.6) ** 2 * (3 - 2 * min(1.0, tau / 0.6))
                wmax = max(wmax, abs(d.qvel[0]))
        for _ in range(10):
            mujoco.mj_step(m, d)
    loom = np.array(rec["loomL"] + [0.0])[:n], np.array(rec["loomP"] + [0.0])[:n]
    lmax = np.maximum(*loom)
    t_esc = ag.escape_t if ag.escape_t is not None else np.nan
    out = dict(kind=kind, seed=seed, esc=ag.escape_t is not None and t_esc >= T_QUIET, pre=ag.escape_t is not None and t_esc < T_QUIET, t_esc=t_esc, loom_max=float(lmax.max()), wbase_max=wmax)
    if kind == "pred":
        t_d10, _ = _first(t_, dist <= D_ESC)
        t_d30, _ = _first(t_, dist <= D_REF)
        t_l0, _ = _first(t_, (lmax > 0) & (t_ >= T_QUIET))
        ks = int(round(t_esc * 100)) if ag.escape_t is not None else None
        ok = ag.escape_t is not None and t_esc >= T_QUIET and dist[ks] > D_ESC
        out.update(speed=speed, yaw=np.degrees(yaw), ok=bool(ok),
                   t_d10=t_d10, t_d30=t_d30, t_loom0=t_l0, lat30=(t_esc - t_d30) * 1e3, lat_loom=(t_esc - t_l0) * 1e3,
                   dist_spk=float(dist[ks]) if ks is not None else np.nan)
        # odsunięcie chwytaka o 2 cm: od położenia w chwili spike'a i od położenia w chwili startu kuli
        k0 = int(T_QUIET * 100)
        t_r0, kr0 = _first(t_, (np.linalg.norm(aim - aim[k0], axis=1) >= RETREAT) & (t_ >= T_QUIET))
        out.update(t_ret0_ms=(t_r0 - t_esc) * 1e3 if ks is not None else np.nan, dist_ret0=float(dist[kr0]) if kr0 is not None else np.nan)
        out["ret_from_loom_ms"] = np.nan
        if ks is not None:
            t_r, kr = _first(t_, (np.linalg.norm(aim - aim[ks], axis=1) >= RETREAT) & (t_ >= t_esc))
            out.update(ret_from_loom_ms=(t_r - t_l0) * 1e3, t_ret_ms=(t_r - t_esc) * 1e3, dist_ret=float(dist[kr]) if kr is not None else np.nan)
        else:
            out.update(t_ret_ms=np.nan, dist_ret=np.nan)
    ag.r.close()                                         # bez tego kolejny Renderer w tym procesie zwraca zepsute klatki (zmierzone)
    if record:
        out["log"] = dict(t=t_, dist=dist, grow=np.array(rec["grow"]), dball=np.array(rec["dball"]), loomL=loom[0], loomP=loom[1], aim=aim, dnrate=np.array(rec["dnrate"]),
                          spk=np.concatenate(rec["spk"]) if rec["spk"] else None)
    return out


# ------------------------------------------------------------------ zbiorcze
def run_all(seeds, par=None, record_first=False, procs=3):
    tasks = [(k, s, par, False) for k in VARIANTS for s in seeds]
    with Pool(procs) as p:
        res = p.map(run_trial, tasks, chunksize=1)
    return {k: [r for r in res if r["kind"] == k] for k in VARIANTS}


def _ms(x, fmt="{:.0f}"):
    x = np.asarray(x, float)
    ok = x[np.isfinite(x)]
    if not len(ok):
        return "NaN (0/%d)" % len(x)
    f = fmt.format
    return f"{f(ok.mean())} ± {f(ok.std())} [{f(ok.min())}…{f(ok.max())}] n={len(ok)}/{len(x)}"


def report(R, label=""):
    P = R["pred"]
    import hashlib
    h = ", ".join(f"{f}:{hashlib.md5(open(os.path.join(HERE, f), 'rb').read()).hexdigest()[:8]}" for f in ("agent.py", "brain.py", "vision.py", "scene2.py", "vnc.py"))
    L = [f"B1 ucieczka — {label}", f"(wersje plików współdzielonych, md5: {h})", ""]
    ok = [r for r in P if r["ok"]]
    L.append(f"Drapieżnik (n={len(P)}): sukces (spike DNp01 po starcie i przed 0,10 m) {len(ok)}/{len(P)} = {100 * len(ok) / len(P):.0f} %; "
             f"spike przed startem kuli {sum(r['pre'] for r in P)}; brak spike'a {sum(not r['esc'] and not r['pre'] for r in P)}; spike za późno "
             f"{sum(r['esc'] and not r['ok'] for r in P)}")
    L.append("seed  v[m/s] yaw[°]  spike[s]  d@spike[m]  opóźn.od0,30m[ms]  opóźn.odloom[ms]  odsunięcie2cm od spike[ms]  d@odsun[m]  odsun.od startu[ms]  d@(od startu)")
    for r in P:
        L.append(f"{r['seed']:4d}  {r['speed']:5.2f}  {r['yaw']:+6.1f}  {r['t_esc']:7.2f}  {r['dist_spk']:9.3f}  {r['lat30']:16.0f}  {r['lat_loom']:15.0f}  "
                 f"{r['t_ret_ms']:24.0f}  {r['dist_ret']:9.3f}  {r['t_ret0_ms']:17.0f}  {r['dist_ret0']:11.3f}  {'OK' if r['ok'] else ('PRZED' if r['pre'] else ('ZA PÓŹNO' if r['esc'] else 'BRAK'))}")
    L.append("")
    L.append(f"opóźnienie od 0,30 m [ms]: {_ms([r['lat30'] for r in P])}")
    L.append(f"opóźnienie od 1. loom>0 [ms]: {_ms([r['lat_loom'] for r in P])}")
    L.append(f"odległość kuli przy spike'u [m]: {_ms([r['dist_spk'] for r in P], '{:.3f}')}")
    L.append(f"spike → odsunięcie 2 cm [ms]: {_ms([r['t_ret_ms'] for r in P])}; odległość kuli wtedy [m]: {_ms([r['dist_ret'] for r in P], '{:.3f}')}")
    L.append(f"1. loom>0 → odsunięcie 2 cm [ms]: {_ms([r['ret_from_loom_ms'] for r in P])}")
    L.append(f"położenie sprzed startu kuli → odsunięcie 2 cm, od spike'a [ms]: {_ms([r['t_ret0_ms'] for r in P])} (ujemne = chwytak ruszył przed spike'em)")
    nr = sum(np.isfinite(r['dist_ret']) and r['dist_ret'] > D_ESC for r in P)
    L.append(f"odsunięcie o 2 cm zdążyło przed 0,10 m: {nr}/{len(P)} = {100 * nr / len(P):.0f} % (tylko raport, bez strojenia)")
    L.append("")
    L.append("Kontrole fałszywych ucieczek (3 s po 0,5 s ciszy, spike DNp01 kiedykolwiek):")
    names = dict(rot_eff="(a) obrót własny ±1,8 rad/s, kopia eferentna TAK", rot_noeff="(a) obrót własny ±1,8 rad/s, kopia eferentna NIE",
                 rot2_eff="(a′) obrót własny ±3 rad/s, kopia eferentna TAK", rot2_noeff="(a′) obrót własny ±3 rad/s, kopia eferentna NIE",
                 ramp="(b1) piłeczka z równi do paszczy", cross="(b2) piłeczka w poprzek bez przesłony", bare="(c) sama scena, bez bodźca")
    for k in VARIANTS[1:]:
        rs = R[k]
        e = sum(r["esc"] for r in rs)
        extra = f", maks. |ω| bazy {max(r['wbase_max'] for r in rs):.2f} rad/s" if k.startswith("rot") else ""
        L.append(f"  {names[k]}: {e}/{len(rs)} = {100 * e / len(rs):.0f} %, spike w ciszy przed bodźcem {sum(r['pre'] for r in rs)}  (maks. looming {max(r['loom_max'] for r in rs):.2f}{extra})")
    return "\n".join(L)


def plot(R, rec, path, R0=None):
    log, r = rec["log"], rec
    fig = plt.figure(figsize=(13, 8.5))
    gs = fig.add_gridspec(4, 2, width_ratios=[1.5, 1], hspace=0.5, wspace=0.28)
    t = log["t"]
    ax = [fig.add_subplot(gs[i, 0]) for i in range(4)]
    ax[0].plot(t, log["dist"], color=CAT[0], lw=1.6)
    ax[0].axhline(D_REF, color=INK2, ls=":", lw=1)
    ax[0].axhline(D_ESC, color=CAT[7], ls=":", lw=1)
    ax[0].set_ylabel("kula–kamera [m]")
    ax[0].set_title(f"przykładowa próba (ziarno {r['seed']}, {r['speed']:.2f} m/s, {r['yaw']:+.0f}°): prawda MuJoCo", fontsize=10, loc="left")
    ax[1].plot(t, log["loomL"], color=CAT[1], lw=1.2, label="L")
    ax[1].plot(t, log["loomP"], color=CAT[2], lw=1.2, label="P")
    ax[1].set_ylabel("looming 0–1")
    ax[1].legend(frameon=False, ncol=2, fontsize=8, loc="upper left")
    if log["spk"] is not None:
        sp = log["spk"]
        ti, ni = np.nonzero(sp)
        ax[2].scatter(ti * 1e-3, ni, s=3, color=INK)
        ax[2].set_ylabel("DNp01 raster (nr)")
        a2 = ax[2].twinx()
        a2.plot(t, log["dnrate"], color=CAT[3], lw=1.2)
        a2.set_ylabel("szybkość [Hz]", color=CAT[3])
    ax[3].plot(t, np.linalg.norm(log["aim"] - log["aim"][int(T_QUIET * 100)], axis=1) * 100, color=CAT[5], lw=1.6)
    ax[3].axhline(RETREAT * 100, color=INK2, ls=":", lw=1)
    ax[3].set_ylabel("przesunięcie chwytaka [cm]")
    ax[3].set_xlabel("czas [s]")
    for a in ax:
        a.axvline(r["t_esc"], color=CAT[7], lw=1, ls="--")
        a.axvline(r["t_d30"], color=INK2, lw=0.8, ls=":")
        a.grid(color=GRID)
        a.set_xlim(0, t[-1])
    ax[0].text(r["t_esc"], ax[0].get_ylim()[1], " spike DNp01", color=CAT[7], fontsize=8, va="top")
    bx = fig.add_subplot(gs[:, 1])
    labs = ["±1,8 +kopia", "±1,8 bez kopii", "±3 +kopia", "±3 bez kopii", "równia", "w poprzek", "bez bodźca"]
    pct = lambda RR: [100 * sum(x["esc"] for x in RR[k]) / len(RR[k]) for k in VARIANTS[1:]]
    pc, x = pct(R), np.arange(len(VARIANTS) - 1)
    w = 0.38 if R0 else 0.7
    bx.bar(x - (w / 2 if R0 else 0), pc, w, color=CAT[0], label=f"G_LOOM0 = {V0['g0'] if R0 is None else PAR['g0']} (strojony)")
    for i, v in enumerate(pc):
        bx.text(i - (w / 2 if R0 else 0), v + 1.5, f"{v:.0f}", ha="center", fontsize=9)
    if R0:
        p0 = pct(R0)
        bx.bar(x + w / 2, p0, w, color=CAT[1], label=f"G_LOOM0 = {V0['g0']} (vision.py)")
        for i, v in enumerate(p0):
            bx.text(i + w / 2, v + 1.5, f"{v:.0f}", ha="center", fontsize=9)
    bx.legend(frameon=False, fontsize=8, loc="upper center")
    bx.set_xticks(x, labs)
    ok = 100 * sum(x["ok"] for x in R["pred"]) / len(R["pred"])
    bx.set_ylim(0, 110)
    bx.set_ylabel("próby z ucieczką [%]")
    bx.set_title(f"kontrole (n={len(R['rot_eff'])} po 3 s); drapieżnik: ucieczka na czas {ok:.0f} %", fontsize=10, loc="left")
    bx.tick_params(axis="x", rotation=25)
    bx.grid(axis="y", color=GRID)
    fig.savefig(path, dpi=130, bbox_inches="tight")


def parse(argv):
    par = {}
    for a in argv:
        k, v = a.split("=")
        par[k] = float(v)
    return par


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "val"
    par = dict(PAR, **parse(sys.argv[2:]))
    seeds = {"tune": range(100, 120), "val": range(120, 140), "final": range(10)}[mode]
    R = run_all(seeds, par)
    if os.environ.get("B1_DUMP"):
        import pickle
        pickle.dump(R, open(os.environ["B1_DUMP"], "wb"))
    txt = report(R, f"{mode}, ziarna {seeds[0]}–{seeds[-1]}, parametry {par or 'domyślne'}")
    print(txt)
    if mode == "final":
        ref = {"g0": V0["g0"]}                           # odniesienie w tym samym przebiegu: nieprzestrojony próg vision.py
        R0 = run_all(seeds, ref)
        txt += "\n\n" + "=" * 100 + "\n" + report(R0, f"ODNIESIENIE bez strojenia (G_LOOM0 = {V0['g0']}), ziarna {seeds[0]}–{seeds[-1]}")
        print("\n" + txt.split("=" * 100)[1])
        os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
        open(os.path.join(HERE, "results", "stage3_b1.txt"), "w").write(txt + "\n")
        pick = next((r for r in R["pred"] if r["ok"]), R["pred"][0])
        rec = run_trial(("pred", pick["seed"], par, True))
        plot(R, rec, os.path.join(HERE, "results", "stage3_b1.png"), R0)
