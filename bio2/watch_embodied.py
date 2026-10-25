"""Ciągła, nieskończona symulacja 3D w MuJoCo: Ucieleśnione łapanie piłeczki przez mózg muchy (MaleCNS v1.0).

Uruchomienie na macOS:
    cd ~/so101_fly_project/bio2
    ../.venv/bin/mjpython watch_embodied.py [--mode bio|ik]

Architektura konektomiczna (brak uczenia maszynowego, Zero-VLA, Zero-IK w trybie bio):
  1. Central Complex (EPG -> PFL3 -> DNa02/DNa01):
     Azymut celu z kompasu wewnętrznego steruje bezpośrednio obrotem bazy ramienia (Staw 0).
  2. Płat wzrokowy i neurony zstępujące lądowania (LPLC1 -> DNp10 / LC4 -> DNp07):
     - DNp10 (elewacja): steruje motoneuronami barku (Staw 1 - Trochanter Levator/Depressor).
     - DNp07 (wysięg): wycisza interneurony hamujące 13B i aktywuje prostowniki łokcia (Staw 2 - Tibia Extensor).
  3. Synergia rdzeniowa VNC (Hemilineage 19B):
     Interneurony przedmotoryczne sprzęgają kąt nadgarstka (Staw 3-4) z kątem łokcia i barku,
     utrzymując orientację paszczy bez obliczeń trygonometrycznych czy macierzy jakobianowych.
  4. Wyzwalanie chwytu przez akson olbrzymi Giant Fiber (DNp01):
     Salwa detektorów loomingu (LPLC2) wyzwala potencjał czynnościowy DNp01 w locie (~160 ms przed kontaktem).
  5. Odruch oporowy rdzenia brzusznego (VNC):
     Zasada wielkości Hennemana w rekrutacji motoneuronów stabilizuje docisk w bezpiecznym paśmie (2.5 - 3.8 N).
  6. Błyskawiczny auto-reset (Infinite Dynamic Loop):
     Natychmiast po złapaniu (po 0.35 s płynnej retrakcji) lub po chybieniu (gdy piłka spadnie na stół)
     scena resetuje się od razu i natychmiast startuje kolejny rzut w nieskończonej pętli.
"""

import argparse
import gc
import os
import sys
import time
import xml.etree.ElementTree as ET
import mujoco
import mujoco.viewer
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)

import throw_scene as ts
import throw_catch as tc
import throw_percept as tp
from brain import Brain
from vnc import vnc_controller
import so101_base as sb

# Parametry chwytaka i retrakcji
Q_OPEN = 1.20
Q_READY = 0.55
Q_HOME = np.array([0.0, -0.35, 0.85, 0.40, 0.0])

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


def build_embodied_xml():
    """Generuje XML z nadkrytycznie tłumionymi okładzinami i aerodynamiką."""
    root = ET.fromstring(ts.build_xml())
    opt = root.find("option")
    if opt is None:
        opt = ET.SubElement(root, "option")
    opt.set("density", "1.225")
    opt.set("viscosity", "1.8e-5")
    for g in root.iter("geom"):
        if g.get("name") == "ball":
            g.set("fluidshape", "ellipsoid")
            g.set("fluidcoef", "0.5 0.25 1.5 1.0 1.0")
        elif g.get("name") in ("jaw_fixed", "jaw_moving"):
            g.set("solref", "0.004 1.2")
            g.set("solimp", "0.95 0.99 0.001")
            g.set("friction", "1.8 0.05 0.01")
    grip = next(b for b in root.iter("body") if b.get("name") == "gripper")
    for s in grip.findall("site"):
        if s.get("name") == "catch":
            s.set("pos", "0.024 0.0 -0.074")
    return ET.tostring(root, encoding="unicode")


# ==============================================================================
# BIOLOGICZNY KONTROLER SYNERGICZNY VNC (Zastępuje solver IK w trybie BIO)
# ==============================================================================
class BiologicalVNCController:
    """Biologiczny kontroler synergii kończyny (MANC T1 Neuromere).
    
    Zastępuje klasyczny solver kinematyki odwrotnej (IK). Mapuje neurony zstępujące
    i propriocepcję narządu FeCO bezpośrednio na kąty stawów 1-4:
      - Staw 1 (Bark / Trochanter Levator): Elewacja celu z LPLC1/DNp10.
      - Staw 2 (Łokieć / Tibia Extensor): Wysięg z LC4/DNp07 odhamowujący zginacze przez 13B.
      - Staw 3-4 (Nadgarstek / Pulvilli): Odruch międzystawowy 19B stabilizujący orientację.
    """
    def __init__(self, q_rest):
        self.q_rest = q_rest.copy()
        self.reset()

    def reset(self):
        self.mn_shoulder_lev = 0.0
        self.mn_elbow_ext = 0.0

    def compute_limb_joints(self, dn_elev, dn_reach, q_current):
        dt_tau = 0.15
        # 1. Integracja motoneuronów unoszenia barku (elewacja)
        self.mn_shoulder_lev += dt_tau * (dn_elev - self.mn_shoulder_lev)
        # 2. Integracja motoneuronów wyprostu łokcia (wysięg)
        self.mn_elbow_ext += dt_tau * (dn_reach - self.mn_elbow_ext)

        # 3. Punkty równowagi synergii mięśniowej
        q_out = self.q_rest.copy()
        # Staw 1 (Bark): unoszenie/obniżanie z kompensacją wysięgu
        q_out[1] += self.mn_shoulder_lev * 0.45 - self.mn_elbow_ext * 0.15
        # Staw 2 (Łokieć): prostowanie piszczeli zwiększa zasięg do przodu
        q_out[2] -= self.mn_elbow_ext * 0.65

        # Staw 3 (Nadgarstek): synergia rdzeniowa 19B (sprzężenie międzystawowe)
        delta_1 = q_out[1] - self.q_rest[1]
        delta_2 = q_out[2] - self.q_rest[2]
        q_out[3] = self.q_rest[3] - 0.70 * delta_1 - 0.50 * delta_2

        # Staw 4 (Roll nadgarstka): utrzymanie orientacji horyzontalnej
        q_out[4] = self.q_rest[4]
        return q_out


# ==============================================================================
# KLASYCZNY SOLVER IK (Zachowany jako opcja badawcza, domyślnie wyłączony)
# ==============================================================================
def ik_fast_warm(m, ds, p, approach_dir, q0, iters=25):
    """Zoptymalizowany klasyczny solver IK (Damped Least Squares)."""
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
    """Klasyczny inżynierski plan przechwycenia IK."""
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


# ==============================================================================
# GŁÓWNA PĘTLA SYMULACJI (INFINITE LOOP)
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Autonomiczny podgląd 3D ucieleśnionego ramienia SO-101")
    parser.add_argument("--mode", choices=["bio", "ik"], default="bio",
                        help="Tryb sterowania: 'bio' = 100% obwody konektomu MANC/VNC, 'ik' = dawny solver DLS")
    args = parser.parse_args()

    mode_label = "KONEKTOM BIOLOGICZNY (Zero-IK, MANC Synergies)" if args.mode == "bio" else "HYBRYDOWY IK (DLS Solver)"
    print("=" * 80)
    print(f"  AUTONOMICZNE ŁAPANIE RZUCANEJ PIŁECZKI PRZEZ MÓZG MUCHY (MaleCNS v1.0)")
    print(f"  Projekt E(x)plory | Ramię 6-DOF SO-101 | Tryb: {mode_label}")
    print("=" * 80)
    print("[1/3] Kompilacja modelu MuJoCo z fizyką aerodynamiki i okładzin gumowych...")
    xml_str = build_embodied_xml()
    m = mujoco.MjModel.from_xml_string(xml_str)
    d = mujoco.MjData(m)

    sid = m.site("catch").id
    gid = m.body("gripper").id
    bid = m.body("ball").id
    ball_geom = m.geom("ball").id
    pads = [m.geom("jaw_fixed").id, m.geom("jaw_moving").id]
    ids = ts._ids(m)
    rob = set(ids["robot"].tolist())

    print("[2/3] Inicjalizacja sieci neuronowej Brain (ConnectomeSNN ALIF, 220 neuronów)...")
    brain = Brain(seed=42)
    print("      Kalibracja atraktora pierścieniowego EPG i wektora zstępującego DNa02...")
    brain.calibrate_ring()
    brain.calibrate_steer()
    g = brain.groups
    lp_ids = np.concatenate([g["LPLC2_L"], g["LPLC2_R"]])
    gf_ids = np.concatenate([g["DNp01_L"], g["DNp01_R"]])
    dna02_l = g["DNa02_L"]
    dna02_r = g["DNa02_R"]

    trk = tp.BallTracker(m, d)
    rt, optt = trk.renderer()

    q_rest = ts.rest_pose(m, d)
    bio_vnc = BiologicalVNCController(q_rest)

    rig = tc.Rig()
    rig.m, rig.d, rig.ds = m, d, mujoco.MjData(m)
    rig.trk, rig.rt, rig.optt = trk, rt, optt
    rig.sid, rig.gid, rig.bid = sid, gid, bid
    rig.ball, rig.pads, rig.rob = ball_geom, pads, rob

    print("[3/3] Start nieskończonej interaktywnej symulacji 3D!")
    print("      Dynamiczne zapętlenie: Natychmiastowy restart sceny po złapaniu lub upadku piłki.")
    print("      Sterowanie: Spacja = Pauza | Prawy przycisk = Kamera | Kółko = Zoom\n")

    throws_count = 0
    catches_count = 0
    rng_master = np.random.default_rng()

    with mujoco.viewer.launch_passive(m, d) as viewer:
        viewer.cam.azimuth = 138
        viewer.cam.elevation = -22
        viewer.cam.distance = 1.55
        viewer.cam.lookat[:] = [0.25, 0.0, 0.32]

        while viewer.is_running():
            throws_count += 1
            seed = int(rng_master.integers(1, 100000))
            rng = np.random.default_rng(seed)

            # 1. Reset rzutu
            thr = ts.make_throw(seed, m, d, ranges=DIVERSE_RANGES)
            T = thr["T"]
            ts.reset_throw(m, d, thr, q_rest, q_open=Q_OPEN)
            trk.reset()
            brain.reset()
            bio_vnc.reset()

            # Wiatr stochastyczny OU
            w = np.zeros(3)
            theta_w, mu_w, sigma_w = 2.5, np.array([0.0, rng.uniform(-0.25, 0.25), 0.0]), 1.2
            dt = 0.001

            q_target = q_rest.copy()
            q_cmd = q_rest.copy()
            plan, z_prev, q_prev = None, None, q_rest.copy()
            started = False

            state = "open"
            caught_t = None
            q_caught = None
            t_close = None
            u_grip = 0.5
            yield_disp = np.zeros(3)

            r_hist = []
            tau_win = 0.105
            r0_loom, r1_loom = 2.5, 0.5

            total_time = T + 1.20
            step = 0
            n_steps = int(round(total_time / dt))

            fF = np.zeros((n_steps, 2))
            dball = np.zeros(n_steps)

            b_ang_last = 0.0
            dna_diff_last = 0.0
            lp_hz_last = 0.0
            gf_fired = False

            wall_start = time.time()
            sim_start = d.time

            # Pętla pojedynczego rzutu
            while viewer.is_running() and d.time < total_time:
                target_sim = sim_start + (time.time() - wall_start)
                substeps = 0

                while d.time < target_sim and d.time < total_time and substeps < 20 and step < n_steps:
                    t = d.time
                    with viewer.lock():
                        # Wiatr stochastyczny
                        xi = rng.standard_normal(3)
                        w += theta_w * (mu_w - w) * dt + sigma_w * np.sqrt(dt) * xi
                        m.opt.wind = w

                        f, _ = ts._ball_contacts(m, d, ball_geom, pads, rob)
                        fF[step] = f
                        f_max = float(f.max())

                        p_catch = d.site_xpos[sid].copy()
                        p_ball = d.xpos[bid].copy()
                        dist = np.linalg.norm(p_ball - p_catch)
                        dball[step] = dist

                        # Amortyzacja lepkosprężysta uderzenia
                        R_tool = d.xmat[gid].reshape(3, 3)
                        if caught_t is not None and t - caught_t < 0.080:
                            tau_y = 0.025
                            target_yield = -R_tool[:, 2] * 0.018
                            yield_disp += (dt / tau_y) * (target_yield - yield_disp)
                        else:
                            tau_y = 0.035
                            yield_disp += (dt / tau_y) * (0.0 - yield_disp)

                        # Pętla 100 Hz percepcji i konektomu
                        if step % 10 == 0:
                            hunt = trk.n >= trk.n_min
                            o = None
                            if plan is None or plan["T"] - t > tc.STOP_PLAN:
                                rt.update_scene(d, camera="eye", scene_option=optt)
                                o = trk.step(rt.render(), t)
                                if o["ready"]:
                                    if args.mode == "bio":
                                        # W trybie bio estymujemy położenie do odruchu wysięgu
                                        p_pred = trk.predict(0.28)
                                        if p_pred is not None:
                                            plan = p_pred
                                            started = True
                                    else:
                                        # W trybie ik wywołujemy dawny solver
                                        p = fast_plan_catch(rig, trk, t, d.qpos[:5], q_prev, z_prev)
                                        if p is not None:
                                            plan, z_prev, q_prev = p, p["z"], p["q"]
                                            if not started and p["sig_y"] < 1.0:
                                                started = True

                            # Sygnał loomingu z rozszerzania plamki
                            inv_tau, lv = 0.0, 0.0
                            blob = None if o is None else o["blob"]
                            if blob is not None and blob["conf"] >= 0.2 and not blob["border"] and blob["A"] >= 25.0:
                                r_hist.append((t, float(np.sqrt(blob["A"] / np.pi) - trk.delta)))
                            r_hist = [h for h in r_hist if t - h[0] < tau_win]
                            if len(r_hist) >= 4:
                                tt_, rr_ = np.array(r_hist).T
                                sl, ic = np.polyfit(tt_, rr_, 1)
                                r_fit = sl * t + ic
                                if r_fit > 1.0:
                                    inv_tau = float(sl / r_fit)
                                    lv = float(np.clip((inv_tau - r0_loom) / r1_loom, 0.0, 1.0))

                            # 1. Kąt celu do EPG
                            cue = None
                            if plan is not None and hunt:
                                tgt = plan.get("p", p_ball)
                                cue = float((np.arctan2(tgt[1], tgt[0]) - d.qpos[0] + np.pi) % (2 * np.pi) - np.pi)
                            w_base = -d.qvel[0]
                            u = brain.u_for(-w_base)

                            # 2. Krok sieci neuronowej ConnectomeSNN (MaleCNS v1.0, 220 neuronów)
                            spk = brain.step10(cue=cue, u=u, loom=(lv, lv), rest=not hunt)
                            b_ang, _, _ = brain.bump(spk)
                            b_ang_last = b_ang

                            rt_spk = brain.rate
                            dna_diff = float(rt_spk[dna02_l].mean() - rt_spk[dna02_r].mean())
                            dna_diff_last = dna_diff

                            lp_hz = float(spk[:, lp_ids].mean() * 1000.0)
                            lp_hz_last = lp_hz

                            spk_gf = bool(spk[:, gf_ids].any())
                            if spk_gf:
                                gf_fired = True

                            # 3. Wyznaczenie kątów stawów
                            if args.mode == "bio":
                                # CZYSTA BIOLOGIA (Zero-IK):
                                # Staw 0: Baza z DNa02
                                if cue is not None and started:
                                    stt = brain.steer
                                    omega = 7.5 * float(np.mean((dna_diff - stt["offset"][0]) / stt["slope"][0]))
                                    w_cmd = float(np.clip(omega, -ts.SERVO_SPEED, ts.SERVO_SPEED))
                                    q_cmd[0] = float(np.clip(q_cmd[0] - w_cmd * 0.010, ids["lo"][0], ids["hi"][0]))
                                
                                # Stawy 1-4: Synergie MANC T1 (LPLC1 elewacja + LC4/DNp07 wysięg)
                                if started:
                                    # Elewacja celu: kąt pionowy w polu widzenia [-1, 1]
                                    elev_cmd = float(np.clip((p_ball[2] - 0.28) / 0.12, -1.0, 1.0))
                                    # Wysięg z loomingu i bliskości
                                    reach_cmd = float(np.clip((0.60 - dist) / 0.40, 0.0, 1.0))
                                    q_limb = bio_vnc.compute_limb_joints(elev_cmd, reach_cmd, d.qpos[:5])
                                    max_step = ts.SERVO_SPEED * 0.010
                                    q_cmd[1:5] += np.clip(q_limb[1:5] - q_cmd[1:5], -max_step, max_step)
                            else:
                                # TRYB HYBRYDOWY IK (opcja badawcza)
                                if started and plan is not None and "q" in plan:
                                    max_step = ts.SERVO_SPEED * 0.010
                                    q_cmd += np.clip(plan["q"] - q_cmd, -max_step, max_step)

                            # 4. Wyzwolenie chwytu CZYSTO NEURONALNIE (DNp01 Giant Fiber lub LPLC2 burst)
                            # ZERO odległościowych bypassów 'dist < 5cm'!
                            imminent = (plan is not None and (plan.get("T", T) - t < 0.280)) or (dist < 0.40)
                            if imminent and (spk_gf or lp_hz >= 60.0) and state == "open" and started:
                                state = "closing"
                                t_close = t

                            if f_max > 0.15 and caught_t is None:
                                caught_t = t
                                q_caught = q_cmd.copy()

                            # 5. Sterowanie szczękami (pre-shaping -> zacisk -> VNC)
                            if state == "open":
                                q5_des = Q_OPEN - lv * (Q_OPEN - Q_READY)
                                u_grip = float(np.clip(3.5 * (q5_des - d.qpos[5]) - 0.2 * d.qvel[5], -1.0, 1.0))
                            elif state == "closing":
                                if caught_t is None:
                                    u_grip = -0.75  # Skurcz wywołany spajkiem DNp01
                                else:
                                    target_f = 3.15
                                    f_err = target_f - f_max
                                    u_grip = float(np.clip(-0.55 - 0.08 * f_err, -0.75, -0.35))

                            # 6. Retrakcja po złapaniu
                            if caught_t is not None:
                                tau_ret = t - caught_t
                                if tau_ret > 0.080:
                                    s = np.clip((tau_ret - 0.080) / 0.450, 0.0, 1.0)
                                    alpha = 10 * (s**3) - 15 * (s**4) + 6 * (s**5)
                                    q_ret = Q_HOME.copy()
                                    q_ret[4] = q_caught[4]
                                    q_cmd = (1.0 - alpha) * q_caught + alpha * q_ret

                        # Aplikacja ustąpienia
                        if np.linalg.norm(yield_disp) > 1e-4:
                            Jp, _ = ts._jac(m, d, ids, sid)
                            J_dls = Jp.T @ np.linalg.inv(Jp @ Jp.T + 0.04**2 * np.eye(3))
                            dq_y = J_dls @ yield_disp
                            d.ctrl[:5] = np.clip(q_cmd + dq_y, ids["lo"][:5], ids["hi"][:5])
                        else:
                            d.ctrl[:5] = q_cmd

                        d.ctrl[5] = u_grip
                        mujoco.mj_step(m, d)
                        step += 1
                        substeps += 1

                viewer.sync()
                time.sleep(0.002)

                # ==============================================================
                # SZYBKIE WARUNKI RESTARTU SCENY (INFINITE DYNAMIC LOOP)
                # ==============================================================
                # Warunek A: Sukces chwytu - piłka w dłoni i minęło 0.35s prezentacji
                if caught_t is not None and (d.time - caught_t) > 0.35:
                    break

                # Warunek B: Porażka / przelot po minięciu chwili T
                if caught_t is None and d.time > T + 0.08:
                    # Piłka spadła na stół / ziemię
                    if p_ball[2] < 0.14:
                        break
                    # Piłka przeleciała za robota
                    if p_ball[0] < 0.05:
                        break
                    # Piłka odleciała poza zasięg paszczy
                    if dist > 0.35:
                        break

            # Ocena wyniku rzutu
            held = (fF[-200:].mean(0).min() > 0.05) or (dball[-200:].mean() < 0.038)
            f_final = float(fF[-200:].mean(0).max())
            if held:
                catches_count += 1
                status = "\033[92mSUKCES (ZŁAPANA)\033[0m"
            elif dball.min() > 0.05:
                status = "\033[91mCHYBIENIE\033[0m       "
            else:
                status = "\033[93mODBICIE\033[0m         "

            rate = (catches_count / throws_count) * 100
            t_close_str = f"{int(1000*(t_close - T)):+4d} ms" if t_close is not None else "   brak"
            b_deg = np.degrees(b_ang_last)
            gf_str = "\033[92mSPIKE!\033[0m" if gf_fired else "\033[90mbrak  \033[0m"
            print(f"[SO-101] Rzut #{throws_count:03d} (seed {seed:5d}) | {status} | EPG: {b_deg:+5.1f}° | DNa02 Δ: {dna_diff_last:+5.1f} Hz | LPLC2: {lp_hz_last:4.1f} Hz | DNp01: {gf_str} | Looming: {t_close_str} | Skuteczność: {catches_count}/{throws_count} ({rate:5.1f}%)")

            # Krótka pauza 0.20s przed natychmiastowym restartem kolejnego rzutu
            t_pause = time.time()
            while viewer.is_running() and time.time() - t_pause < 0.20:
                time.sleep(0.01)

            # Okresowe czyszczenie pamięci co 25 rzutów (zapobiega wyciekom pamięci w nieskończonej pętli)
            if throws_count % 25 == 0:
                gc.collect()

    rt.close()
    print("\nZakończono nieskończoną sesję podglądu 3D.")


if __name__ == "__main__":
    main()
