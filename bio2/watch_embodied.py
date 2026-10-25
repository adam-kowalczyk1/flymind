"""Podgląd na żywo łapania wcielonego (embodied) w oknie 3D MuJoCo.

Uruchomienie na macOS:
    cd ~/so101_fly_project/bio2
    ../.venv/bin/mjpython watch_embodied.py [seed] [variant]

Dostępne warianty:
    BIO-embodied   (domyślny - pełny biologiczny: pościg PN, looming pre-shaping, ustąpienie, odruch VNC)
    BIO-les-LPLC   (kontrola: brak loomingu, otwarte szczęki)
    BIO-les-PFL3   (kontrola: brak pościgu azymutalnego)
    BIO-shuffle    (kontrola: przetasowany konektom)
    ENG-vacuum     (kontrola: sztywna inżynieria próżniowa)

Spacja w oknie przeglądarki = pauza/wznowienie.
R = reset.
"""
import sys
import time
import mujoco
import mujoco.viewer
import numpy as np

import throw_catch_embodied as tce
import throw_scene as ts

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 100
variant = sys.argv[2] if len(sys.argv) > 2 else "BIO-embodied"

print(f"=== Oglądanie próby łapania wcielonego ===")
print(f"Seed: {seed}, Wariant: {variant}")
print("Otwieranie okna 3D MuJoCo... (naciśnij Spację, aby zatrzymać/wznowić)")

m, d = tce.make_embodied_model()
sid = m.site("catch").id
ids = ts._ids(m)
gid = ids["grip"]
bid = m.body("ball").id
ball_geom = m.geom("ball").id
pads = [m.geom("jaw_fixed").id, m.geom("jaw_moving").id]
rob = set(ids["robot"].tolist())

thr = ts.make_throw(seed, m, d)
T = thr["T"]
q_rest = ts.rest_pose(m, d)
ts.reset_throw(m, d, thr, q_rest, q_open=tce.Q_OPEN)

# Stochastyczny wiatr OU
w = np.zeros(3)
theta = 2.5
mu = np.array([0.0, 0.2, 0.0])
sigma = 1.2
dt = 0.001
rng = np.random.default_rng(seed)

q_cmd = d.qpos[:5].copy()
p_prev_ball = d.xpos[bid].copy()
p_prev_catch = d.site_xpos[sid].copy()

total_time = T + 1.20
caught_t = None
q_caught = None
yield_disp = np.zeros(3)

with mujoco.viewer.launch_passive(m, d) as v:
    t_start = time.time()
    step = 0
    while v.is_running() and d.time < total_time:
        step_t0 = time.time()
        
        with v.lock():
            t = d.time
            # Wiatr
            xi = rng.standard_normal(3)
            w += theta * (mu - w) * dt + sigma * np.sqrt(dt) * xi
            m.opt.wind = w
            
            # Kontakty
            f, _ = ts._ball_contacts(m, d, ball_geom, pads, rob)
            f_contact = float(f.max())
            
            p_ball = d.xpos[bid].copy()
            p_catch = d.site_xpos[sid].copy()
            r_rel = p_ball - p_catch
            R_dist = np.linalg.norm(r_rel)
            
            v_ball = (p_ball - p_prev_ball) / dt
            v_catch = (p_catch - p_prev_catch) / dt
            v_rel = v_ball - v_catch
            
            p_prev_ball[:] = p_ball
            p_prev_catch[:] = p_catch
            
            if f_contact > 0.15 and caught_t is None:
                caught_t = t
                q_caught = d.qpos[:5].copy()
                
            # Logika sterowania
            if caught_t is None:
                v_clos = -np.dot(r_rel, v_rel) / max(R_dist, 1e-4)
                inv_tau = max(0.0, v_clos) / max(R_dist, 1e-4)
                
                if variant == "BIO-les-LPLC":
                    q5_target = tce.Q_OPEN
                else:
                    loom_act = float(np.clip((inv_tau - 1.5) / 6.0, 0.0, 1.0))
                    q5_target = tce.Q_OPEN - (tce.Q_OPEN - tce.Q_READY) * loom_act
                d.ctrl[5] = np.clip(3.0 * (q5_target - d.qpos[5]) - 0.2 * d.qvel[5], -1.0, 1.0)
                
                if variant == "ENG-vacuum":
                    plan_alpha = np.clip((t - 0.15) / max(T - 0.25, 0.05), 0.0, 1.0)
                    q_des = (1.0 - plan_alpha) * q_rest + plan_alpha * thr["q_star"]
                    dq = q_des - q_cmd
                else:
                    u_los = r_rel / max(R_dist, 1e-4)
                    omega_los = np.cross(r_rel, v_rel) / max(R_dist**2, 1e-4)
                    
                    e_ret = p_ball - p_catch
                    v_task = tce.N_PN * np.cross(omega_los, v_rel) + tce.K_FIX * e_ret
                    
                    Jp, _ = ts._jac(m, d, ids, sid)
                    J_dls = Jp.T @ np.linalg.inv(Jp @ Jp.T + (tce.LAM_DLS**2) * np.eye(3))
                    dq_raw = J_dls @ v_task
                    
                    if variant == "BIO-les-PFL3":
                        dq_raw[0] = 0.0
                    elif variant == "BIO-shuffle":
                        dq_raw = np.roll(dq_raw, 2) * -0.8
                        
                    dq = dq_raw * dt
                    
                dq_max = tce.SERVO_SPEED * dt
                dq_clamped = np.clip(dq, -dq_max, dq_max)
                q_cmd += dq_clamped
                q_cmd = np.clip(q_cmd, ids["lo"][:5], ids["hi"][:5])
                d.ctrl[:5] = q_cmd
            else:
                tau_since = t - caught_t
                if tau_since < 0.050:
                    d.ctrl[5] = -0.25
                elif tau_since < 0.500:
                    d.ctrl[5] = -0.12
                else:
                    if f_contact < 2.0:
                        d.ctrl[5] = -0.055
                    elif f_contact > 3.8:
                        d.ctrl[5] = -0.020
                    else:
                        d.ctrl[5] = -0.038
                        
                tau_y = 0.025
                y_amp = 0.018 * (tau_since / tau_y) * np.exp(-tau_since / tau_y)
                R_tool = d.xmat[gid].reshape(3, 3)
                yield_disp = -R_tool[:, 2] * y_amp
                
                T_ret = 0.45
                s = np.clip(tau_since / T_ret, 0.0, 1.0)
                alpha_ret = 10 * (s**3) - 15 * (s**4) + 6 * (s**5)
                
                q_ret_target = tce.Q_HOME.copy()
                q_ret_target[4] = q_caught[4]
                q_cmd = (1.0 - alpha_ret) * q_caught + alpha_ret * q_ret_target
                d.ctrl[:5] = q_cmd
                
            mujoco.mj_step(m, d)
            
        v.sync()
        # Synchronizacja czasu rzeczywistego
        time.sleep(max(0.0, 0.001 - (time.time() - step_t0)))
        step += 1

print(f"\nKoniec próby (czas symulacji: {d.time:.2f} s).")
if caught_t is not None:
    f_final, _ = ts._ball_contacts(m, d, ball_geom, pads, rob)
    d_final = np.linalg.norm(d.body("ball").xpos - d.site_xpos[sid])
    held = (f_final.sum() > 0.05) or (d_final < 0.040)
    print(f"Wynik: {'SUKCES - PIŁECZKA ZŁAPANA I PRZYCIĄGNIĘTA DO BAZY!' if held else 'UPUSZCZENIE'}")
else:
    print("Wynik: CHYBIENIE / ODBICIE")

while v.is_running():
    time.sleep(0.1)
