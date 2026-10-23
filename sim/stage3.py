"""Etap 3 — zamknięta pętla MuJoCo ↔ ConnectomeSNN: przechwycenie toczącej się kulki.

Co 10 ms: wzrok (azymut kulki względem osi chwytaka) → LC10a; czujniki dotyku szczęk → neurony
czuciowe nogi; 10 kroków SNN po 1 ms; DNa02 L−R → prędkość obrotu bazy; MN → PWM chwytaka.
Uniesienie po pewnym chwycie to skryptowy program ruchowy (nie część obwodu muchy).

Metryki liczone NIEZALEŻNIE od wejść sterownika (z sił kontaktu MuJoCo, nie z czujników touch):
  sukces  = kulka uniesiona ≥ 3 cm nad stół na końcu próby, w kontakcie z obiema szczękami,
            a siła ściskania (średnia 20 ms) nigdy nie przekroczyła F_CRUSH;
  reakcja = czas od pierwszego kontaktu kulki z chwytakiem do początku pewnego chwytu
            (obie szczęki ≥ F_SECURE nieprzerwanie przez 50 ms).
Uruchom:  python stage3.py  [liczba prób]
"""
import sys
import time

import mujoco
import numpy as np

import scene
from circuit import FlyController

F_CRUSH = 5.0      # N — próg zgniecenia miękkiej piłki (nasza stała)
F_SECURE = 0.3     # N — minimalny nacisk szczęki (2·μ·F > m·g z zapasem; μ=1,2, m=50 g)
SERVO_SPEED = 4.7  # rad/s, ramię (STS3215, ok.)
WINDUP = 0.02      # rad, maks. odjazd celu serwa bazy od zmierzonej pozycji
BASE_LEAK = None   # s, wygasanie przesunięcia celu serwa bazy (None = brak)
REAL_FRICTION = True   # tarcie wg materiałów (scene.build_xml); μ = 1 wszędzie dawało klin przy dłoni
T_TRIAL = 5.0
Q_OPEN = 0.93      # rad, rozwarcie szczęk w oczekiwaniu (szczelina ~8 cm na kulkę 5 cm); 1,2 dawało
                   # 2× dłuższe domykanie przy tym samym bezpiecznym tempie dojazdu
WARMUP = 1.0       # s, robot patrzy na kulkę trzymaną na szczycie równi i obraca się do niej
PADS = ("jaw_fixed", "jaw_moving")


def jaw_forces(m, d, ball_gid, pad_gids):
    """Siły normalne kulka–pad [N] (stała, ruchoma) z mj_contactForce — metryka niezależna."""
    out = np.zeros(2)
    f6 = np.zeros(6)
    for i in range(d.ncon):
        c = d.contact[i]
        for k, pg in enumerate(pad_gids):
            if {c.geom1, c.geom2} == {ball_gid, pg}:
                mujoco.mj_contactForce(m, d, i, f6)
                out[k] += abs(f6[0])
    return out


def bearing(d):
    """Azymut kulki względem kierunku „paszczy”, oba widziane z osi obrotu bazy (jak oko muchy na
    osi obrotu ciała), + = w lewo. Oko na chwytaku (28 cm od osi) dawało wzmocnienie pętli rosnące
    jak 1 + r/odległość i oscylacje ±40° tuż przed złapaniem."""
    b = d.body("ball").xpos[:2]
    g = d.site("aim").xpos[:2]          # środek otwartej paszczy (nie punkt domkniętego chwytu)
    return float(np.angle(np.exp(1j * (np.arctan2(b[1], b[0]) - np.arctan2(g[1], g[0])))))


def base_cmd(m, d, yaw):
    """Prędkość obrotu bazy → cel serwa pozycyjnego: cel = pozycja + przesunięcie, które całkuje −ω·dt
    (dodatni kąt shoulder_pan obraca w prawo), ograniczone do ±WINDUP i (opcjonalnie) wygasające ze
    stałą BASE_LEAK. Bez wygasania przesunięcie zostaje na granicy windupu po skręcie i serwo przy
    ω ≈ 0 dociska stałą szczękę do kulki."""
    w = np.clip(yaw, -SERVO_SPEED, SERVO_SPEED)
    off = d.ctrl[0] - d.qpos[0]
    if BASE_LEAK:
        off *= np.exp(-scene.CONTROL_DT / BASE_LEAK)
    off = np.clip(off - w * scene.CONTROL_DT, -WINDUP, WINDUP)
    d.ctrl[0] = np.clip(d.qpos[0] + off, *m.actuator_ctrlrange[0])


def run_trial(seed, controller, record=False, on_step=None, q_open=None, real_friction=REAL_FRICTION):
    rng = np.random.default_rng(seed)
    ramp = rng.uniform(9, 14)
    m, d = scene.load(ramp_deg=ramp, real_friction=real_friction)
    q_catch, _ = scene.ik_catch_pose(m, d, r=0.28)
    q_lift = q_catch.copy()
    q_lift[1] -= 0.25
    mujoco.mj_resetData(m, d)
    d.qpos[:5] = q_catch
    d.qpos[5] = Q_OPEN if q_open is None else q_open
    d.ctrl[:5] = q_catch
    bj = m.joint("ball").qposadr[0]
    d.qpos[bj + 1] = rng.uniform(-0.06, 0.06)               # przesunięcie boczne startu
    d.qvel[m.joint("ball").dofadr[0] + 1] = rng.uniform(-0.05, 0.05)   # boczna prędkość
    mujoco.mj_forward(m, d)
    q_ball = d.qpos[bj:bj + 7].copy()
    ball_gid = m.geom("ball").id
    pad_gids = [m.geom(n).id for n in PADS]
    grip_gids = set(pad_gids) | {m.geom("palm").id}
    n_sub = round(scene.CONTROL_DT / m.opt.timestep)

    controller.reset()
    # kulka trzymana na szczycie równi (wyłączona grawitacja kulki), robot już się do niej obraca
    bdof = m.joint("ball").dofadr[0]
    v0 = d.qvel[bdof:bdof + 6].copy()
    for _ in range(round(WARMUP / scene.CONTROL_DT)):
        yaw, _, _ = controller.control_step(bearing(d) + np.radians(rng.normal(0, 1.0)), d.sensordata[:3].copy(),
                                            active=True)
        base_cmd(m, d, yaw)
        for _ in range(n_sub):
            mujoco.mj_step(m, d)
            d.qpos[bj:bj + 7] = q_ball
            d.qvel[bdof:bdof + 6] = 0
    d.qvel[bdof:bdof + 6] = v0
    d.time = 0.0
    secure_ctrl, lifting, t_lift = 0, False, None
    log = dict(t=[], force=[], touch=[], yaw=[], torque=[], theta=[], spikes=[], ball=[], q_grip=[], tau_pan=[])
    first_contact = None
    az_err = None
    hist = []
    cpu = 0.0
    for k in range(round(T_TRIAL / scene.CONTROL_DT)):
        th = bearing(d) + np.radians(rng.normal(0, 1.0))     # szum „oka” 1°
        touch = d.sensordata[:3].copy()
        c0 = time.perf_counter()
        yaw, tau, spk = controller.control_step(th, touch, active=True, jaw_vel=d.qvel[5], jaw_q=d.qpos[5])
        cpu += time.perf_counter() - c0
        base_cmd(m, d, yaw)
        d.ctrl[5] = np.clip(-tau / scene.GRIP_TORQUE, -1, 1)  # zamykanie = ujemny PWM
        # program uniesienia: wyzwalany czujnikami sterownika (obie szczęki > F_SECURE przez 100 ms)
        secure_ctrl = secure_ctrl + 1 if min(touch[0], touch[1]) > F_SECURE else 0
        if secure_ctrl >= 10 and not lifting:
            lifting, t_lift = True, d.time
        if lifting:
            step = SERVO_SPEED * scene.CONTROL_DT
            d.ctrl[1] += np.clip(q_lift[1] - d.ctrl[1], -step, step)
        for _ in range(n_sub):
            mujoco.mj_step(m, d)
            f = jaw_forces(m, d, ball_gid, pad_gids)
            hist.append(f)
            if first_contact is None and any({c.geom1, c.geom2} & grip_gids and ball_gid in (c.geom1, c.geom2)
                                             for c in d.contact[:d.ncon]):
                first_contact = d.time
        if az_err is None and np.hypot(*d.body("ball").xpos[:2]) < 0.34:
            az_err = float(np.degrees(bearing(d)))   # błąd celowania tuż przed paszczą
        if on_step:
            on_step(m, d)
        if record:
            log["t"].append(d.time)
            log["force"].append(hist[-1])
            log["touch"].append(touch)
            log["yaw"].append(yaw)
            log["torque"].append(tau)
            log["theta"].append(th)
            log["spikes"].append(spk)
            log["ball"].append(d.body("ball").xpos.copy())
            log["q_grip"].append(d.qpos[5])
            log["tau_pan"].append(d.actuator_force[0])

    F = np.array(hist)                                    # [ms, 2]
    F20 = np.array([np.convolve(F[:, i], np.ones(20) / 20, "same") for i in range(2)]).T
    peak = F20.max()
    both = (F >= F_SECURE).all(1)
    t_secure = None
    if first_contact is not None:
        start = int(first_contact * 1000)
        run = 0
        for i in range(start, len(both)):
            run = run + 1 if both[i] else 0
            if run >= 50:
                t_secure = (i - 49) / 1000
                break
    ball_z = d.body("ball").xpos[2]
    holding = (F[-1] > 0.05).all()
    lifted = ball_z > scene.BALL_R + 0.03
    out = dict(seed=seed, ramp=ramp, success=bool(lifted and holding and peak < F_CRUSH),
               lifted=bool(lifted), holding=bool(holding), crushed=bool(peak >= F_CRUSH), peak_force=float(peak),
               hold_force=float(F[-200:].mean()) if holding else 0.0,
               contact=first_contact, reaction_ms=None if (t_secure is None or first_contact is None)
               else 1000 * (t_secure - first_contact), cpu_ms_per_cycle=1000 * cpu / (k + 1),
               miss=first_contact is None, t_lift=t_lift, az_err_deg=az_err)
    if record:
        out["log"] = {k: np.array(v) for k, v in log.items()}
        out["F"] = F
    return out


def summarize(results, label=""):
    ok = [r for r in results if r["success"]]
    rt = [r["reaction_ms"] for r in ok if r["reaction_ms"] is not None]
    s = dict(n=len(results), success_pct=100 * len(ok) / len(results),
             crushed=sum(r["crushed"] for r in results), missed=sum(r["miss"] for r in results),
             dropped=sum((not r["miss"]) and (not r["crushed"]) and (not r["success"]) for r in results),
             reaction_ms_mean=float(np.mean(rt)) if rt else float("nan"),
             reaction_ms_sd=float(np.std(rt)) if rt else float("nan"),
             peak_force_mean=float(np.mean([r["peak_force"] for r in results if not r["miss"]] or [np.nan])),
             cpu_ms=float(np.mean([r["cpu_ms_per_cycle"] for r in results])))
    print(f"{label} sukces {s['success_pct']:.0f}% ({len(ok)}/{s['n']}), zgniecione {s['crushed']}, "
          f"chybione {s['missed']}, upuszczone {s['dropped']}, reakcja {s['reaction_ms_mean']:.0f}±"
          f"{s['reaction_ms_sd']:.0f} ms, szczyt siły {s['peak_force_mean']:.2f} N, CPU SNN {s['cpu_ms']:.2f} ms/cykl")
    return s


def main(n=10):
    results = []
    for seed in range(n):
        fc = FlyController(seed=seed)
        r = run_trial(seed, fc)
        results.append(r)
        print(f"próba {seed}: {'SUKCES' if r['success'] else 'porażka'}  rampa {r['ramp']:.1f}°  "
              f"kontakt {r['contact'] if r['contact'] is None else round(r['contact'], 3)} s  "
              f"reakcja {r['reaction_ms'] if r['reaction_ms'] is None else round(r['reaction_ms'])} ms  "
              f"szczyt {r['peak_force']:.2f} N  trzyma {r['hold_force']:.2f} N  "
              f"uniesiona {r['lifted']}  zgniecona {r['crushed']}")
    return summarize(results, "RAZEM:")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 10)
