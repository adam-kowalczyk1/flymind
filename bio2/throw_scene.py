"""Etap 5 (bio2): scena „rzucana piłeczka” — piłeczka (5 cm) leci swobodnie po paraboli (bez oporu powietrza), ramię
SO-101 z kamerą „eye” ma ją złapać. Ten plik: scena, generator rzutów, IK pozycyjne i WYROCZNIA (górna granica
wykonalności: sterowanie znające prawdę, bez mózgu). Weryfikacja pod `__main__` (patrz niżej).

Scena = scene2 bez równi i bez przesłony (przesłona, „drapieżnik” i sonda usunięte z XML, tło odsunięte na x = 3,2 m,
żeby rzut z 2 m go nie przebijał). Piłeczka (ciało swobodne „ball”) koliduje ze stołem i ramieniem jak w scene2.

Geometria chwytu (zmierzona, patrz so101_base.py): oś narzędzia = −z ciała `gripper` (od dłoni do czubków szczęk),
piłeczka wlatuje w paszczę WZDŁUŻ +z_gripper (od czubków ku dłoni, kierunek lotu = −oś narzędzia). Ruchoma szczęka
jest palcem na zawiasie, a paszcza jest otwarta na boki (pady mają 1,6 cm szerokości w y): piłeczka uderzająca w dłoń
ukośnie ucieka wzdłuż y, zanim szczęki (serwo STS3215 w trybie PWM: stała czasowa ~50 ms, 0,75 rad w ~0,2 s) się zamkną.
Dlatego w locie szczęki stoją w „lejku” Q_OPEN (0,6 rad, szczelina ~6–7 cm na piłeczkę 5 cm), a zamykanie (T − 30 ms)
tylko dociska piłeczkę. Zamykanie z pełnego rozwarcia (1,2 rad) wymaga startu ~200 ms przed T (patrz wyniki strojenia).
Punkt przechwycenia p* to środek piłeczki w chwili T; do p* doprowadzam punkt `CATCH_LOCAL` (współrzędne w układzie
`gripper`) = środek paszczy tuż nad dłonią (site „grasp” z so101_base leży przy stałej szczęce, patrz niżej).

Ograniczenie kinematyki (ważne): ramię ma 5 stawów — bark (pan) obraca całą płaszczyznę ramienia, a wszystkie pozostałe
stawy leżą w tej płaszczyźnie (rolka nadgarstka obraca tylko wokół osi narzędzia). Oś narzędzia leży więc (z dokładnością
do 1,5 cm przesunięcia punktu chwytu od osi) w pionowej płaszczyźnie przez oś bazy i p*. Kierunek lotu można dopasować
w pionie (nadgarstek), a w poziomie tylko do kierunku radialnego — stąd limit kąta podejścia ANG_MAX w generatorze.
"""
import os
import sys
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

import scene2
import so101_base as sb

HERE = os.path.dirname(os.path.abspath(__file__))
G = 9.81
R_BALL = sb.BALL_R
SERVO_SPEED = 4.7            # rad/s (jak agent.SERVO_SPEED; nie importuję agent.py — ciągnie siatkówkę i SNN)
D_PERCEPT = 0.25             # s, opóźnienie percepcji wyroczni
CLOSE_LEAD = 0.03            # s, szczęki zaczynają się zamykać T − CLOSE_LEAD
Q_OPEN = 0.6                 # rad, rozwarcie szczęk (lejek) w oczekiwaniu i podczas lotu; dobrane eksperymentalnie, patrz RAPORT
U_CLOSE = 0.8                # PWM zamykania (moment −3,35·U N·m; stała siła)

# zakresy losowania (opis i uzasadnienie: patrz RAPORT w results/stage5_throw_scene.txt)
RANGES = dict(
    az_star=np.radians((-30.0, 30.0)),   # azymut p* od osi bazy [rad]
    r_star=(0.20, 0.36),                 # odległość pozioma p* od osi bazy [m]
    z_star=(0.22, 0.34),                 # wysokość p* [m] (poniżej 0,22 oś narzędzia nie wyprowadza się stromo w górę, patrz mapa)
    d0=(1.0, 2.0),                       # odległość pozioma p0 od bazy [m]
    az0=np.radians((-45.0, 45.0)),       # azymut p0 [rad]
    z0=(0.2, 0.8),                       # wysokość p0 [m]
    T=(0.6, 1.0),                        # czas lotu [s]
    ang_max=np.radians(20.0),            # maks. kąt między osią narzędzia a −kierunkiem lotu w p* [rad]
)

# punkt chwytu w układzie `gripper` doprowadzany do p*: środek paszczy (x między stałą szczęką a ruchomą), tuż nad dłonią
# (dłoń: powierzchnia z = −0,043, środek piłeczki przy dłoni z = −0,068; −0,074 = 6 mm „w głąb” — piłeczka trafia w dłoń
# ułamek ms przed T). Site „grasp” z so101_base leży przy stałej szczęce (po domknięciu), a nie w środku otwartej paszczy.
CATCH_LOCAL = np.array([0.032, 0.0, -0.074])


# --------------------------------------------------------------------------------------------- scena
def build_xml():
    root = ET.fromstring(scene2.build_xml(ramp_deg=None))
    world = root.find("worldbody")
    for b in list(world):
        if b.tag == "body" and b.get("name") in ("occluder", "predator", "probe"):
            world.remove(b)
    for g in world.iter("geom"):
        if g.get("name") == "backdrop":
            g.set("pos", "3.2 0 1.0")
    grip = next(b for b in root.iter("body") if b.get("name") == "gripper")
    ET.SubElement(grip, "site", dict(name="catch", pos=" ".join(map(str, CATCH_LOCAL)), size="0.004", rgba="1 0 1 1"))
    return ET.tostring(root, encoding="unicode")


def load():
    m = mujoco.MjModel.from_xml_string(build_xml())
    m.vis.global_.offwidth, m.vis.global_.offheight = max(scene2.CAM_W, 1280), max(scene2.CAM_H, 720)
    return m, mujoco.MjData(m)


_IDS = {}


def _ids(m):
    """Indeksy stawów ramienia, zakresy, geomy ramienia (cache per model)."""
    k = id(m)
    if k not in _IDS:
        jid = [m.joint(j).id for j in sb.ARM]
        bid = m.body("ball").id
        robot = np.array([g for g in range(m.ngeom) if m.geom_bodyid[g] != 0 and m.geom_bodyid[g] != bid
                          and m.geom_contype[g] + m.geom_conaffinity[g] > 0])
        _IDS[k] = dict(qa=[m.joint(j).qposadr[0] for j in sb.ARM], da=[m.joint(j).dofadr[0] for j in sb.ARM],
                       lo=m.jnt_range[jid, 0].copy(), hi=m.jnt_range[jid, 1].copy(), robot=robot,
                       table=m.geom("table").id, grip=m.body("gripper").id)
    return _IDS[k]


def place_ball(m, d, p0, v0):
    """Piłeczka w p0 z prędkością liniową v0 (świat), bez obrotu."""
    scene2.place_free(m, d, "ball", p0)
    v = m.joint("ball").dofadr[0]
    d.qvel[v:v + 3] = v0


def reset_throw(m, d, thr, q_rest, q_open=Q_OPEN):
    """Ramię w pozie spoczynkowej, szczęki otwarte, piłeczka w p0 z v0."""
    mujoco.mj_resetData(m, d)
    d.qpos[:5] = q_rest
    d.qpos[5] = q_open
    d.ctrl[:5] = q_rest
    place_ball(m, d, thr["p0"], thr["v0"])
    mujoco.mj_forward(m, d)


DT = 0.001   # krok fizyki (so101_base.TIMESTEP)


def ball_pos(thr, t):
    """Położenie piłeczki wg DYSKRETNEJ paraboli integratora MuJoCo (zmierzone: pierwszy krok po ustawieniu qvel nie przesuwa
    ciała, potem pozycja idzie ze starą prędkością): x(t) = p0 + v0 (t − DT) + ½ g t (t − DT) dla t ≥ DT, zgodne co do 1e-4 mm.
    Wzór ciągły p0 + v0 t + ½ g t² różni się od tego o v0·DT (do 5 mm) i ½ g t DT (do 5 mm)."""
    t = max(t, DT)
    return thr["p0"] + thr["v0"] * (t - DT) + 0.5 * np.array([0, 0, -G]) * t * (t - DT)


def ball_vel(thr, t):
    return thr["v0"] + np.array([0, 0, -G]) * t


# --------------------------------------------------------------------------------------------- IK
def _desired_frame(approach_dir):
    """Żądany układ osi `gripper` (kolumny x, y, z): z = −oś narzędzia = kierunek lotu, y „w dół” (kamera na górze),
    x = y × z. Zwraca None gdy approach_dir None."""
    zd = np.asarray(approach_dir, float)
    zd = zd / np.linalg.norm(zd)                       # z_gripper = kierunek lotu (oś narzędzia = −z = przeciwna)
    down = np.array([0.0, 0.0, -1.0])
    yd = down - (down @ zd) * zd
    if np.linalg.norm(yd) < 1e-3:                      # lot pionowy: wybierz y poziomo
        yd = np.array([1.0, 0.0, 0.0])
        yd = yd - (yd @ zd) * zd
    yd /= np.linalg.norm(yd)
    xd = np.cross(yd, zd)
    return np.stack([xd, yd, zd], axis=1)


def _fk(m, d, ids, q):
    d.qpos[ids["qa"]] = q
    mujoco.mj_fwdPosition(m, d)


def _jac(m, d, ids, site):
    """Jakobian site'a (pozycja 3×5, obrót 3×5) po stawach ramienia — mj_jacSite."""
    jp, jr = np.zeros((3, m.nv)), np.zeros((3, m.nv))
    mujoco.mj_jacSite(m, d, jp, jr, site)
    return jp[:, ids["da"]], jr[:, ids["da"]]


def ik_reach(m, d, p, approach_dir=None, q0=None, site="catch", iters=150, lam=0.01, q_grip=Q_OPEN):
    """IK pozycyjne: damped least squares na jakobianie MuJoCo (mj_jacSite), 5 stawów ramienia
    (szczęka osobno, ustawiona na q_grip), z limitami stawów (obcięcie po kroku).

    Priorytety zadań (pochodna po przestrzeni zerowej): 1) pozycja site'a `site` (domyślnie „catch” = środek paszczy,
    CATCH_LOCAL; „grasp” = site chwytaka z so101_base) = p; 2) w przestrzeni zerowej pozycji: oś narzędzia przeciwna do `approach_dir` (kierunku lotu piłeczki
    w p*) i rolka tak, by kamera była na górze (y chwytaka w dół). Rolka nie zmienia osi, więc po spełnieniu pozycji
    zostają 2 stopnie swobody (nachylenie osi i rolka).
    Zwraca (q[5], err_pos [m], err_ang [rad] = kąt między osią narzędzia a −approach_dir; 0 gdy approach_dir=None).
    Stan d: qpos ramienia jest nadpisywany (przywracam przed wyjściem)."""
    ids = _ids(m)
    site = m.site(site).id
    save = d.qpos.copy()
    d.qpos[5] = q_grip
    p = np.asarray(p, float)
    Rd = None if approach_dir is None else _desired_frame(approach_dir)
    az = np.arctan2(p[1], p[0])
    starts = [] if q0 is None else [np.asarray(q0, float)]
    for dz in (0.0, 1.0, -1.0):          # zimne starty: łokieć w górę, różne nachylenia nadgarstka
        starts.append(np.array([az, 0.5 + 0.4 * dz, 0.9 - 0.3 * dz, -0.6 + 0.8 * dz, 1.5]))
    best = None
    n = len(ids["qa"])
    for qs in starts:
        q = np.clip(qs, ids["lo"], ids["hi"])
        for it in range(iters):
            _fk(m, d, ids, q)
            ep = p - d.site_xpos[site]
            Jp, Jr = _jac(m, d, ids, site)
            R = d.xmat[ids["grip"]].reshape(3, 3)
            eo = None if Rd is None or it >= iters - 30 else 0.5 * sum(np.cross(R[:, i], Rd[:, i]) for i in range(3))
            free = np.ones(n, bool)                  # zbiór aktywny: stawy na limicie, które krok wypychałby dalej, zamrażam
            for _ in range(4):
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
            if nm > 0.2:
                dq *= 0.2 / nm
            q = np.clip(q + dq, ids["lo"], ids["hi"])
            if nm < 1e-6 and it > 10:
                break
        _fk(m, d, ids, q)
        err = float(np.linalg.norm(p - d.site_xpos[site]))
        ang = 0.0
        if approach_dir is not None:
            tool = -d.xmat[ids["grip"]].reshape(3, 3)[:, 2]
            a = np.asarray(approach_dir, float)
            ang = float(np.arccos(np.clip(tool @ (-a / np.linalg.norm(a)), -1, 1)))
            up = float(d.xmat[ids["grip"]].reshape(3, 3)[2, 1])      # z świata osi y chwytaka (<0: kamera na górze)
        else:
            up = -1.0
        cost = err * 100 + ang + (1.0 if up > 0.2 else 0.0)
        if best is None or cost < best[0]:
            best = (cost, q.copy(), err, ang)
        if err < 1e-3 and ang < np.radians(5):
            break
    d.qpos[:] = save
    mujoco.mj_forward(m, d)
    return best[1], best[2], best[3]


def arm_clearance(m, d, q, q_grip=Q_OPEN):
    """Odstęp ramienia od stołu [m] (min. mj_geomDistance geomów ramienia do stołu, obcięty do 0,3 m) i liczba
    samokolizji (kontakty geom–geom ramienia w tej pozie)."""
    ids = _ids(m)
    save = d.qpos.copy()
    d.qpos[ids["qa"]] = q
    d.qpos[5] = q_grip
    bj = m.joint("ball").qposadr[0]
    d.qpos[bj:bj + 3] = (0, 5, 5)
    mujoco.mj_forward(m, d)
    rob = set(ids["robot"].tolist())
    clr = min(mujoco.mj_geomDistance(m, d, int(g), ids["table"], 0.3, None) for g in ids["robot"]
              if m.body(m.geom_bodyid[g]).name != "shoulder")     # bark obraca się tylko wokół pionu: odstęp stały
    n_self = sum(1 for i in range(d.ncon) if d.contact[i].geom1 in rob and d.contact[i].geom2 in rob)
    d.qpos[:] = save
    mujoco.mj_forward(m, d)
    return float(clr), n_self


# --------------------------------------------------------------------------------------------- generator rzutów
def make_throw(seed, m=None, d=None, ranges=None, max_tries=5000):
    """Rzut dla danego seeda (deterministyczny). Losuje p* (zakresy RANGES) i p0, T; v0 liczone tak, by dyskretny integrator
    MuJoCo trafił w p* dokładnie w chwili T (T zaokrąglone do 1 ms; dyskretna parabola, patrz ball_pos; poprawka względem
    wzoru ciągłego v0 = (p* − p0 − ½gT²)/T wynosi ok. 1,5–5 mm w pozycji). Odrzucam losowania, dla których (i) pozioma składowa lotu odbiega od kierunku radialnego
    do bazy o > ang_max (oś narzędzia nie ma jak jej śledzić, patrz docstring modułu), (ii) IK nie dociera do p* z błędem
    < 1 mm z osią narzędzia w ang_max od −kierunku lotu i kamerą na górze, (iii) poza ramienia ma kolizję ze stołem (odstęp < 5 mm)
    lub samokolizję.
    Zwraca dict: p0, v0, p_star, T, approach (wersor lotu w p*), speed (|v| w p*), el_deg (nachylenie toru w p*, < 0 = opada),
    az_off_deg (odchylenie poziomej składowej lotu od kierunku do bazy), ang_deg (kąt osi narzędzia z IK względem −approach),
    q_star (5 stawów, IK dla site „catch”), tries (liczba losowań do akceptacji), rej (liczniki odrzuceń: az / z / ik / ang / kol)."""
    rg = dict(RANGES, **(ranges or {}))
    if m is None:
        m, d = load()
    rng = np.random.default_rng(seed)
    gv = np.array([0, 0, -G])
    rej = dict(az=0, z=0, ik=0, ang=0, kol=0)
    for tries in range(1, max_tries + 1):
        az, r, z = rng.uniform(*rg["az_star"]), rng.uniform(*rg["r_star"]), rng.uniform(*rg["z_star"])
        ps = np.array([r * np.cos(az), r * np.sin(az), z])
        dd, a0, z0 = rng.uniform(*rg["d0"]), rng.uniform(*rg["az0"]), rng.uniform(*rg["z0"])
        p0 = np.array([dd * np.cos(a0), dd * np.sin(a0), z0])
        T = round(rng.uniform(*rg["T"]) / DT) * DT
        v0 = (ps - p0 - 0.5 * gv * T * (T - DT)) / (T - DT)
        vT = v0 + gv * T
        a = vT / np.linalg.norm(vT)
        ah = a[:2] / np.linalg.norm(a[:2])
        rad = ps[:2] / np.linalg.norm(ps[:2])
        az_off = float(np.arccos(np.clip(-ah @ rad, -1, 1)))     # 0 = lot dokładnie ku bazie
        if az_off > rg["ang_max"]:
            rej["az"] += 1
            continue
        if ps[2] < R_BALL + 0.02:
            rej["z"] += 1
            continue
        q, err, ang = ik_reach(m, d, ps, a)
        if err >= 1e-3:
            rej["ik"] += 1
        elif ang > rg["ang_max"]:
            rej["ang"] += 1
        else:
            clr, nself = arm_clearance(m, d, q)
            if clr > 0.005 and nself == 0:
                return dict(seed=seed, p0=p0, v0=v0, p_star=ps, T=float(T), approach=a, speed=float(np.linalg.norm(vT)),
                            el_deg=float(np.degrees(np.arcsin(a[2]))), az_off_deg=float(np.degrees(az_off)),
                            ang_deg=float(np.degrees(ang)), q_star=q, tries=tries, rej=rej, clearance_mm=1000 * clr)
            rej["kol"] += 1
    raise RuntimeError(f"make_throw({seed}): brak akceptowalnego rzutu po {max_tries} losowaniach")


# --------------------------------------------------------------------------------------------- poza spoczynkowa, widoczność
REST = dict(p=(0.25, 0.0, 0.30), el_deg=40.0)       # środek paszczy [m] i nachylenie osi narzędzia (+ = w górę)


def rest_pose(m, d, p=None, el_deg=None):
    """Poza spoczynkowa: środek paszczy w p, oś narzędzia (poziomo na zewnątrz) uniesiona o el_deg. Zwraca q[5]."""
    p = REST["p"] if p is None else p
    e = np.radians(REST["el_deg"] if el_deg is None else el_deg)
    q, err, ang = ik_reach(m, d, np.array(p, float), np.array([-np.cos(e), 0.0, -np.sin(e)]))
    assert err < 1e-3, f"poza spoczynkowa nieosiągalna ({err * 1000:.1f} mm)"
    return q


def seg_renderer(m):
    r, opt = scene2.eye_renderer(m)
    r.enable_segmentation_rendering()
    return r, opt


def ball_px(m, d, r, opt):
    """Liczba pikseli piłeczki w obrazie kamery „eye” (segmentacja, jak stage3._ball_visible)."""
    r.update_scene(d, camera="eye", scene_option=opt)
    s = r.render()
    return int(((s[..., 0] == m.geom("ball").id) & (s[..., 1] == mujoco.mjtObj.mjOBJ_GEOM)).sum())


def rest_visibility(m, d, thr, q_rest, r, opt, dt=0.01):
    """Piksele piłeczki wzdłuż toru swobodnego (ramię nieruchome w q_rest, piłeczka ustawiana kinematycznie)."""
    reset_throw(m, d, thr, q_rest)
    out = []
    for t in np.arange(0, thr["T"] + 1e-9, dt):
        place_ball(m, d, ball_pos(thr, t), ball_vel(thr, t))
        mujoco.mj_forward(m, d)
        out.append(ball_px(m, d, r, opt))
    return np.array(out)


# --------------------------------------------------------------------------------------------- WYROCZNIA
HOLD_T = 1.0         # s, okno trzymania
F_CONTACT = 0.05     # N, kontakt szczęka–piłeczka (jak stage3_b2.analyse: both > 0,05 N)


def _ball_contacts(m, d, ball, pads, rob):
    """Siły normalne kulka–pad (stała, ruchoma) z mj_contactForce i lista (geom) innych kontaktów kulka–ramię."""
    f = np.zeros(2)
    other = []
    f6 = np.zeros(6)
    for i in range(d.ncon):
        c = d.contact[i]
        if ball not in (c.geom1, c.geom2):
            continue
        o = c.geom2 if c.geom1 == ball else c.geom1
        if o in pads:
            mujoco.mj_contactForce(m, d, i, f6)
            f[pads.index(o)] += abs(f6[0])
        elif o in rob:
            other.append(o)
    return f, other


def oracle_trial(seed, thr=None, m=None, d=None, P=None, rest=None, render=True, record=False):
    """Wyrocznia: zna p*, T i q* (prawdę). Ramię stoi w pozie spoczynkowej do t = D_PERCEPT, potem każdy staw jedzie do q*
    z prędkością ograniczoną do SERVO_SPEED (rampa wartości zadanej `ctrl`, serwo pozycyjne MuJoCo ją goni). Szczęki:
    do t = T − CLOSE_LEAD trzymane na Q_OPEN prostym regulatorem P na PWM, potem stała siła zamykania −U_CLOSE (moment
    −3,35·U N·m, bez mózgu i bez VNC). Symulacja do T + 0,5 + HOLD_T. Zwraca dict z miarami i klasą wyniku."""
    P = dict(D=D_PERCEPT, lead=CLOSE_LEAD, u_close=U_CLOSE, q_open=Q_OPEN, speed=SERVO_SPEED, t_after=0.5), P or {}
    P = {**P[0], **P[1]}
    own = m is None
    if own:
        m, d = load()
    thr = thr or make_throw(seed, m, d)
    q_rest = rest_pose(m, d) if rest is None else rest
    if "catch" in P:                                   # inny punkt chwytu w układzie `gripper` -> nowe IK
        m.site_pos[m.site("catch").id] = P["catch"]
        qs, err, _ = ik_reach(m, d, thr["p_star"], thr["approach"], q0=thr["q_star"])
        if err > 1e-3:
            return dict(seed=seed, success=False, cls="IK nieosiągalne", T=thr["T"], arm_err_T_mm=np.nan)
    else:
        qs = thr["q_star"]
    reset_throw(m, d, thr, q_rest, P["q_open"])
    T = thr["T"]
    ball = m.geom("ball").id
    pads = [m.geom("jaw_fixed").id, m.geom("jaw_moving").id]
    palm = m.geom("palm").id
    ids = _ids(m)
    rob = set(ids["robot"].tolist())
    sid = m.site("catch").id
    r, opt = seg_renderer(m) if render else (None, None)
    n = int(round((T + P["t_after"] + HOLD_T) * 1000))
    dt = m.opt.timestep
    step = P["speed"] * dt
    px, fF, first = [], np.zeros((n, 2)), None
    err_arm = np.zeros(n)
    dball = np.zeros(n)
    contact_t, contact_g = None, None
    tab, tab_hit = ids["table"], False
    trace = np.zeros((n, 3))
    for k in range(n):
        t = d.time
        if render and k % 10 == 0 and t <= T:
            px.append(ball_px(m, d, r, opt))
        if t >= P["D"]:
            d.ctrl[:5] += np.clip(qs - d.ctrl[:5], -step, step)
        if t < T - P["lead"]:
            d.ctrl[5] = np.clip(3.0 * (P["q_open"] - d.qpos[5]) - 0.3 * d.qvel[5], -1, 1)
        else:
            d.ctrl[5] = -P["u_close"]
        mujoco.mj_step(m, d)
        f, other = _ball_contacts(m, d, ball, pads, rob)
        tab_hit |= any(tab in (c.geom1, c.geom2) and (c.geom1 in rob or c.geom2 in rob) for c in d.contact[:d.ncon])
        fF[k] = f
        if contact_t is None and (f.any() or other):
            contact_t = d.time
            g = pads[int(np.argmax(f))] if f.any() else other[0]
            contact_g = m.body(m.geom_bodyid[g]).name + ("/" + m.geom(g).name if m.geom(g).name else "")
        err_arm[k] = np.linalg.norm(d.site_xpos[sid] - thr["p_star"])
        dball[k] = np.linalg.norm(d.body("ball").xpos - d.site_xpos[sid])
        trace[k] = d.body("ball").xpos
    if r is not None:
        r.close()
    m.site_pos[sid] = CATCH_LOCAL
    # --- miary
    both = fF.min(1) > F_CONTACT
    close = dball < 0.04                                   # piłeczka w paszczy (środek < 4 cm od środka paszczy)
    W = int(HOLD_T * 1000)
    ok = both & close
    cs = np.concatenate([[0], np.cumsum(ok)])
    t_hold = next((i for i in range(0, n - W + 1) if cs[i + W] - cs[i] >= 0.99 * W), None)
    kT = int(round(T * 1000)) - 1
    arm_err_T = float(err_arm[kT])
    out = dict(seed=seed, T=T, success=t_hold is not None, arm_err_T_mm=1000 * arm_err_T, t_contact=contact_t,
               first_geom=contact_g, table_hit=tab_hit, early_hit=contact_t is not None and contact_t < T - 0.02, t_hold=None if t_hold is None else t_hold / 1000,
               ball_err_T_mm=1000 * float(np.linalg.norm(trace[kT] - thr["p_star"])),
               px=np.array(px) if render else None, speed=thr["speed"], el_deg=thr["el_deg"], az_off_deg=thr["az_off_deg"])
    if out["success"]:
        cls = "sukces"
    elif arm_err_T > 0.02:
        cls = "nie zdążył"
    elif contact_t is None:
        cls = "chybienie"
    elif not both.any():
        cls = "odbicie od szczęki/dłoni" if contact_g and ("gripper" in contact_g or "moving_jaw" in contact_g) else "odbicie od ramienia"
    else:
        cls = "wypadła"
    out["cls"] = cls
    if record:
        out.update(F=fF, dball=dball, trace=trace, err_arm=err_arm)
    return out


# --------------------------------------------------------------------------------------------- weryfikacja (python throw_scene.py)
def _stat(x, unit="", f=".2f"):
    x = np.asarray(x, float)
    return (f"min {x.min():{f}} | p50 {np.percentile(x, 50):{f}} | p95 {np.percentile(x, 95):{f}} | "
            f"max {x.max():{f}} {unit}").strip()


def check_a(m, d, thrs, out):
    """(a) IK: błąd pozycji site'ów „catch” i „grasp”, odstęp od stołu, test statyczny w fizyce (serwa + grawitacja)."""
    out.append("== (a) IK i osiągalność, %d rzutów ==" % len(thrs))
    for site in ("catch", "grasp"):
        e = np.array([ik_reach(m, d, t["p_star"], t["approach"], site=site)[1] for t in thrs]) * 1000
        out.append(f"IK site '{site}': błąd pozycji < 5 mm: {100 * (e < 5).mean():.0f} %; {_stat(e, 'mm', '.3f')}")
    ang = np.array([t["ang_deg"] for t in thrs])
    out.append(f"kąt osi narzędzia względem −kierunku lotu (ang, po IK): {_stat(ang, '°', '.1f')}")
    out.append(f"odstęp ramienia od stołu w pozie p*: {_stat([t['clearance_mm'] for t in thrs], 'mm', '.1f')}")
    # fizyka: serwa trzymają q* (start z q*, ctrl = q*), 0,5 s, pomiar błędu site'a „catch” (ugięcie od grawitacji) i kontaktów ze stołem
    ids = _ids(m)
    sid, tab = m.site("catch").id, ids["table"]
    rob = set(ids["robot"].tolist())
    sag, ntab = [], 0
    for t in thrs:
        mujoco.mj_resetData(m, d)
        d.qpos[:5], d.qpos[5], d.ctrl[:5] = t["q_star"], Q_OPEN, t["q_star"]
        d.ctrl[5] = 0
        place_ball(m, d, (0, 5, 5), (0, 0, 0))
        hit = False
        for _ in range(500):
            mujoco.mj_step(m, d)
            hit |= any(tab in (c.geom1, c.geom2) and (c.geom1 in rob or c.geom2 in rob) for c in d.contact[:d.ncon])
        sag.append(1000 * np.linalg.norm(d.site_xpos[sid] - t["p_star"]))
        ntab += hit
    out.append(f"w fizyce (serwa + grawitacja, 0,5 s) błąd site'a 'catch' względem p*: < 5 mm: {100 * (np.array(sag) < 5).mean():.0f} %; "
               f"{_stat(sag, 'mm', '.2f')}; rzutów z kontaktem ramię–stół: {ntab}/{len(thrs)}")
    tries = np.array([t["tries"] for t in thrs])
    rej = {k: sum(t["rej"][k] for t in thrs) for k in thrs[0]["rej"]}
    out.append(f"generator: akceptowane losowania (p*, p0, T) = {100 * len(thrs) / tries.sum():.1f} % ({tries.sum()} losowań na {len(thrs)} rzutów); "
               f"odrzucenia: poziomy kąt lotu > ang_max {rej['az']}, IK nie dociera {rej['ik']}, kąt osi > ang_max {rej['ang']}, "
               f"kolizja {rej['kol']}")
    return sag


def reach_map(m, d, n=1500, seed=12345):
    """Osiągalność w całym pudle losowania p*: dla n losowań (p*, p0, T) — (i) sama pozycja (IK bez orientacji, < 5 mm),
    (ii) pełne kryteria generatora. Zwraca tablice (r, z, az, ok_pos, ok_full)."""
    rg = RANGES
    rng = np.random.default_rng(seed)
    gv = np.array([0, 0, -G])
    rows = []
    for _ in range(n):
        az, r, z = rng.uniform(*rg["az_star"]), rng.uniform(*rg["r_star"]), rng.uniform(*rg["z_star"])
        ps = np.array([r * np.cos(az), r * np.sin(az), z])
        dd, a0, z0 = rng.uniform(*rg["d0"]), rng.uniform(*rg["az0"]), rng.uniform(*rg["z0"])
        p0 = np.array([dd * np.cos(a0), dd * np.sin(a0), z0])
        T = round(rng.uniform(*rg["T"]) / DT) * DT
        vT = (ps - p0 - 0.5 * gv * T * (T - DT)) / (T - DT) + gv * T
        a = vT / np.linalg.norm(vT)
        ah = a[:2] / np.linalg.norm(a[:2])
        az_off = np.arccos(np.clip(-ah @ ps[:2] / np.linalg.norm(ps[:2]), -1, 1))
        _, e0, _ = ik_reach(m, d, ps, None)
        q, e1, ang = ik_reach(m, d, ps, a)
        clr, ns = arm_clearance(m, d, q)
        full = az_off <= rg["ang_max"] and e1 < 1e-3 and ang <= rg["ang_max"] and clr > 0.005 and ns == 0
        rows.append((r, z, az, e0 < 5e-3, full))
    return np.array(rows, float).T


def check_b(thrs, out):
    """(b) piłeczka bez ramienia (kolizje geomów ramienia wyłączone): odchyłka od p* w chwili T."""
    m2, d2 = load()
    ids = _ids(m2)
    m2.geom_contype[ids["robot"]] = 0
    m2.geom_conaffinity[ids["robot"]] = 0
    dev, dev_naive, zmin = [], [], []
    gv = np.array([0, 0, -G])
    for t in thrs:
        n = int(round(t["T"] / DT))
        for v0, store in ((t["v0"], dev), ((t["p_star"] - t["p0"] - 0.5 * gv * t["T"] ** 2) / t["T"], dev_naive)):
            mujoco.mj_resetData(m2, d2)
            place_ball(m2, d2, t["p0"], v0)
            lo = 9.0
            for _ in range(n):
                mujoco.mj_step(m2, d2)
                lo = min(lo, d2.body("ball").xpos[2])
            store.append(1000 * np.linalg.norm(d2.body("ball").xpos - t["p_star"]))
            if store is dev:
                zmin.append(lo)
    out.append("== (b) tor swobodny bez ramienia, odchyłka od p* w chwili T ==")
    out.append(f"v0 z poprawką dyskretną (półjawny Euler, krok 1 ms): {_stat(dev, 'mm', '.4f')}")
    out.append(f"v0 ze wzoru ciągłego (p* − p0 − ½gT²)/T:            {_stat(dev_naive, 'mm', '.2f')}   "
               f"(różnica = opóźnienie o 1 krok + ½·g·T·dt integratora, nie fizyka)")
    out.append(f"min. wysokość środka piłeczki w locie: {min(zmin):.3f} m (promień {R_BALL} m) — tor nie dotyka stołu")


def run_c(m, d, thrs, rest, label, out, P=None, render=True):
    rs = [oracle_trial(t["seed"], thr=t, m=m, d=d, rest=rest, render=render, P=P) for t in thrs]
    n = len(rs)
    cl = {}
    for r in rs:
        cl[r["cls"]] = cl.get(r["cls"], 0) + 1
    ns = sum(r["success"] for r in rs)
    out.append(f"{label}: sukces {ns}/{n} = {100 * ns / n:.0f} %   klasy: " + ", ".join(f"{k} {v}" for k, v in sorted(cl.items(), key=lambda kv: -kv[1])))
    return rs


def scan_rest(m, d, seeds, out):
    """Wybór pozy spoczynkowej: % klatek lotu (ramię nieruchome), w których piłeczka ma ≥ 1 px / > 20 px (stage3)."""
    thrs = [make_throw(s, m, d) for s in seeds]
    r, opt = seg_renderer(m)
    out.append(f"== wybór pozy spoczynkowej (ramię nieruchome, {len(thrs)} rzutów, % klatek lotu z piłeczką w obrazie) ==")
    out.append("środek paszczy [m]            nachylenie osi   ≥1 px   >20 px")
    for p in [(0.15, 0, 0.30), (0.20, 0, 0.26), (0.25, 0, 0.30), (0.20, 0, 0.35)]:
        for el in (0, 20, 40, 60):
            try:
                q = rest_pose(m, d, p, el)
            except AssertionError:
                out.append(f"{str(p):28s} {el:3d}°            nieosiągalna")
                continue
            a = np.concatenate([rest_visibility(m, d, t, q, r, opt) for t in thrs])
            out.append(f"{str(p):28s} {el:3d}°          {100 * (a >= 1).mean():5.0f}   {100 * (a > 20).mean():5.0f}"
                       + ("   <- wybrana" if (p, el) == (REST["p"], REST["el_deg"]) else ""))
    r.close()


def figure(m, d, thrs, rs, rmap, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(15, 10.5))
    ax = fig.add_subplot(2, 2, 1, projection="3d")
    ok = np.array([r["success"] for r in rs])
    tt = np.linspace(0, 1, 40)
    for t, o in zip(thrs, ok):
        P = np.array([ball_pos(t, x * t["T"]) for x in tt])
        ax.plot(P[:, 0], P[:, 1], P[:, 2], color="tab:green" if o else "tab:red", lw=0.9, alpha=0.8)
        ax.scatter(*t["p_star"], color="k", s=8)
    ax.scatter(0, 0, 0, marker="^", color="tab:blue", s=60, label="baza")
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]"); ax.set_zlabel("z [m]")
    ax.set_title("tory 3D (zielony: wyrocznia złapała, czerwony: nie); czarne = p*")
    ax.set_zlim(0, 1.0); ax.view_init(24, -150)
    ax = fig.add_subplot(2, 2, 2)
    th = np.radians(np.linspace(-45, 45, 50))
    for rr in (1.0, 2.0):
        ax.plot(rr * np.cos(th), rr * np.sin(th), "0.7", lw=0.8)
    for t, o in zip(thrs, ok):
        ax.plot([t["p0"][0], t["p_star"][0]], [t["p0"][1], t["p_star"][1]], color="tab:green" if o else "tab:red", lw=0.5, alpha=0.6)
        ax.scatter(*t["p_star"][:2], color="tab:green" if o else "tab:red", s=14, zorder=3)
    ax.plot(0, 0, "^", color="tab:blue"); ax.set_aspect("equal")
    ax.set_xlim(-0.1, 2.1); ax.set_ylim(-1.5, 1.5)
    ax.set_title("widok z góry: rzuty (p0 → p*), łuki = 1 m i 2 m od bazy")
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
    ax = fig.add_subplot(2, 2, 3)
    rr, zz, az, okp, okf = rmap
    re, ze = np.linspace(*RANGES["r_star"], 9), np.linspace(*RANGES["z_star"], 9)
    hit, _, _ = np.histogram2d(rr[okf > 0], zz[okf > 0], bins=(re, ze))
    tot, _, _ = np.histogram2d(rr, zz, bins=(re, ze))
    im = ax.imshow(100 * hit.T / np.maximum(tot.T, 1), origin="lower", extent=(re[0], re[-1], ze[0], ze[-1]), aspect="auto",
                   cmap="Greys", vmin=0, vmax=40)
    fig.colorbar(im, ax=ax, label="% losowań (p*, p0, T) akceptowanych przez generator")
    for t, o in zip(thrs, ok):
        ax.scatter(np.hypot(*t["p_star"][:2]), t["p_star"][2], color="tab:green" if o else "tab:red", s=22, edgecolor="k", zorder=3)
    ax.set_xlabel("odległość pozioma p* od osi bazy [m]"); ax.set_ylabel("z [m]")
    ax.set_title("przekrój (r, z): obszar przechwyceń (tło) i wyniki wyroczni (kropki)")
    ax = fig.add_subplot(2, 2, 4)
    f1 = [np.mean(r["px"] >= 1) for r in rs]
    f20 = [np.mean(r["px"] > 20) for r in rs]
    ax.hist([100 * np.array(f1), 100 * np.array(f20)], bins=np.linspace(0, 100, 11), label=["≥ 1 px", "> 20 px (stage3)"])
    ax.set_xlabel("% klatek lotu z piłeczką w polu widzenia kamery „eye”"); ax.set_ylabel("liczba rzutów")
    ax.set_title("widoczność w locie (ramię rusza po D = 0,25 s)"); ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main(only_fig=False):
    import time
    t0 = time.time()
    m, d = load()
    if only_fig:
        thrs = [make_throw(s, m, d) for s in range(50)]
        rs = run_c(m, d, thrs, rest_pose(m, d), "fig", [])
        figure(m, d, thrs, rs, reach_map(m, d), os.path.join(HERE, "results", "stage5_throw_scene.png"))
        return
    out = ["Etap 5 — scena „rzucana piłeczka” (throw_scene.py), wyrocznia (górna granica wykonalności)", ""]
    out.append("== parametry ==")
    out.append("zakresy losowania: " + ", ".join(
        f"{k}={tuple(np.round(np.degrees(v) if k in ('az_star', 'az0', 'ang_max') else v, 3).tolist()) if k != 'ang_max' else round(float(np.degrees(v)), 1)}"
        + ("°" if k in ("az_star", "az0", "ang_max") else "") for k, v in RANGES.items()))
    out.append(f"wyrocznia: D = {D_PERCEPT} s, serwa {SERVO_SPEED} rad/s, szczęki: lejek Q_OPEN = {Q_OPEN} rad (regulator P na PWM), "
               f"zamykanie stałym PWM −{U_CLOSE} (moment {U_CLOSE * sb.GRIP_TORQUE:.2f} N·m) od T − {CLOSE_LEAD * 1000:.0f} ms, "
               f"punkt chwytu 'catch' = {CATCH_LOCAL.tolist()} w układzie gripper; poza spoczynkowa: paszcza w {REST['p']}, oś +{REST['el_deg']:.0f}° w górę")
    out += ["", "== wybór zakresów (uzasadnienie; liczby w sekcjach poniżej) ==",
            "p0 (1–2 m, ±45°, 0,2–0,8 m) i T (0,6–1,0 s) wg specyfikacji, bez zmian. Piłeczka wlatuje stromo (lot opada pod −55…−80°, 3,6–5,5 m/s,",
            "bo spadek z 0,2–0,8 m w 0,6–1,0 s daje v_z ≈ −½gT), więc oś narzędzia musi iść w górę pod +55…+80°: SO-101 osiąga to tylko dla",
            "z_star ≥ ~0,22 m (pomiar: tabela nachyleń osi z 300 tys. losowych póz; poniżej mapa akceptacji w png), stąd z_star 0,22–0,34 m i",
            "r_star 0,20–0,36 m (dalej/wyżej łokieć i nadgarstek na limitach). az_star ±30° (pan ±110°, ale kamera i p0 ±45°).",
            "ang_max = 20°: oś narzędzia może śledzić lot tylko w płaszczyźnie przez oś bazy (5 stawów), a pad ma 1,6 cm w y — przy większym",
            "skosie piłeczka ucieka z paszczy bokiem (ang_max 30° daje już tylko ~80 %, 12° niewiele poprawia, a odrzuca więcej losowań).",
            "Rozwarcie szczęk w locie Q_OPEN = 0,6 rad (lejek) zamiast pełnego: SO-101 zamyka się ~0,75 rad w ~0,2 s, a zamykanie z 30 ms",
            "przed T z pełnego rozwarcia praktycznie zawsze zawodzi (tabela strojenia).", ""]
    scan_rest(m, d, range(100, 110), out)
    out.append("")
    seeds = list(range(100))
    thrs = [make_throw(s, m, d) for s in seeds]
    sag = check_a(m, d, thrs, out)
    rmap = reach_map(m, d)
    okp, okf = rmap[3], rmap[4]
    out.append(f"osiągalność w całym pudle p* ({len(okp)} losowań): sama pozycja (IK < 5 mm, bez orientacji) {100 * okp.mean():.0f} %; "
               f"pełne kryteria generatora (pozycja + oś w ang_max + poziomy kąt lotu + brak kolizji) {100 * okf.mean():.0f} %")
    out.append("")
    check_b(thrs, out)
    out.append("")
    out.append("== (c) wyrocznia ==")
    rest = rest_pose(m, d)
    ths_rep = thrs[:50]
    rs = run_c(m, d, ths_rep, rest, "RAPORT seedy 0–49 (D = 0,25 s)", out)
    px1 = np.concatenate([r["px"] >= 1 for r in rs])
    px20 = np.concatenate([r["px"] > 20 for r in rs])
    out.append(f"widoczność piłeczki w locie (ramię rusza po D): ≥ 1 px {100 * px1.mean():.0f} % klatek, > 20 px (stage3) {100 * px20.mean():.0f} % klatek "
               f"(50 rzutów, {len(px1)} klatek 100 Hz); piłeczka widoczna (≥ 1 px) od klatki pierwszej u {100 * np.mean([r['px'][0] >= 1 for r in rs]):.0f} % rzutów")
    bad = [r for r in rs if not r["success"]]
    for r in bad:
        out.append(f"  porażka seed {r['seed']}: {r['cls']}, T = {r['T']:.2f} s, błąd ramienia w T = {r['arm_err_T_mm']:.1f} mm, "
                   f"1. kontakt: {r['first_geom']}, v = {r['speed']:.1f} m/s, nachylenie toru {r['el_deg']:.0f}°, odchylenie poziome {r['az_off_deg']:.0f}°")
    out.append(f"kontakt ramię–stół w trakcie jazdy ramienia: {sum(r['table_hit'] for r in rs)}/{len(rs)} rzutów; piłeczka dotknęła ramienia > 20 ms przed T: "
               f"{sum(r['early_hit'] for r in rs)}/{len(rs)}")
    out.append(f"błąd położenia 'catch' w chwili T: {_stat([r['arm_err_T_mm'] for r in rs], 'mm', '.1f')}")
    out.append(f"prędkość piłeczki w p*: {_stat([r['speed'] for r in rs], 'm/s', '.1f')}; czas lotu T: {_stat([r['T'] for r in rs], 's', '.2f')}")
    out.append("")
    out.append("-- strojenie na seedach 100–149 (render wyłączony) --")
    thr_t = [make_throw(s, m, d) for s in range(100, 150)]
    run_c(m, d, thr_t, rest, "seedy 100–149, konfiguracja końcowa", out, render=False)
    for amax in (12, 30):
        tt = [make_throw(s, m, d, ranges=dict(ang_max=np.radians(amax))) for s in range(100, 150)]
        run_c(m, d, tt, rest, f"seedy 100–149, ang_max = {amax}° (szerzej/węziej niż końcowe 20°)", out, render=False)
    for qo, lead in ((1.2, 0.03), (1.2, 0.2), (0.9, 0.03), (0.8, 0.03), (0.4, 0.03), (0.6, 0.0), (0.6, 0.10)):
        run_c(m, d, thr_t, rest, f"seedy 100–149, Q_open = {qo}, zamykanie od T − {lead * 1000:.0f} ms", out, render=False,
              P=dict(q_open=qo, lead=lead))
    out.append("")
    out.append("-- czułość (seedy 0–49, konfiguracja końcowa) --")
    for D in (0.35, 0.45, 0.55, 0.7):
        run_c(m, d, ths_rep, rest, f"opóźnienie percepcji D = {D} s", out, render=False, P=dict(D=D))
    for ax_i, ax_n in enumerate(("x (rozwieranie szczęk)", "y (poprzecznie do szczęk)", "z (głębokość w paszczy)")):
        for off in (-0.02, -0.01, -0.005, 0.005, 0.01, 0.02):
            c = CATCH_LOCAL.copy()
            c[ax_i] += off
            run_c(m, d, ths_rep, rest, f"celowanie z przesunięciem {1000 * off:+.0f} mm wzdłuż {ax_n}", out, render=False, P=dict(catch=c))
    out.append("")
    out.append(f"[czas {time.time() - t0:.0f} s]")
    txt = "\n".join(out)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "stage5_throw_scene.txt"), "w").write(txt + "\n")
    figure(m, d, ths_rep, rs, rmap, os.path.join(HERE, "results", "stage5_throw_scene.png"))
    print(txt)


if __name__ == "__main__":
    main(only_fig=len(sys.argv) > 1 and sys.argv[1] == "fig")
