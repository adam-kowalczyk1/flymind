"""Renderuje demonstracyjne wideo MP4 oraz animowany GIF przedstawiający pełny
wcielony, biologiczny pościg, wstępne kształtowanie, odruchowe przechwycenie i wycofanie
dla ramienia SO-101 (Etap 5.5).

Wyświetlane zjawiska:
  1. Stochastyczny wiatr boczny OU i znoszenie toru lotu piłeczki.
  2. Płynny pościg wzrokowy i naprowadzanie proporcjonalne (PN).
  3. Pre-shaping chwytaka sterowany loomingiem (1.2 -> 0.42 rad).
  4. Sprężyste ustąpienie (compliant yield, 18 mm) pochłaniające uderzenie.
  5. Odruchowy chwyt Hennemana z tonicznym utrzymaniem (~3 N) bez zgniecenia.
  6. Płynne wycofanie ramienia do pozy spoczynkowej (q_home).
"""

import os
import shutil
import subprocess
import sys

import mujoco
import numpy as np

import throw_catch_embodied as tce

FFMPEG = "/Users/admin/miniforge3/bin/ffmpeg"
DESKTOP_DIR = "/Users/admin/Desktop/Explory_Projekt_Mucha_SO101/wykresy_i_wideo"
PARENT_ARTIFACT_DIR = "/Users/admin/.gemini/antigravity/brain/a384d8fd-c23b-409b-be24-efe8fe71866f"
CURRENT_ARTIFACT_DIR = "/Users/admin/.gemini/antigravity/brain/9bd527f7-7d0f-403e-8f31-4c8f1d8eb64d"


def render_embodied_video(seed=100, out_mp4="so101_thrown_catch_embodied.mp4", out_gif="so101_thrown_catch_embodied.gif"):
    print(f"Inicjalizacja modelu wcielonego MuJoCo dla seed {seed}...")
    m, d = tce.make_embodied_model()
    
    sid = m.site("catch").id
    ids = tce.ts._ids(m)
    gid = ids["grip"]
    bid = m.body("ball").id
    ball_geom = m.geom("ball").id
    pads = [m.geom("jaw_fixed").id, m.geom("jaw_moving").id]
    rob = set(ids["robot"].tolist())
    
    thr = tce.ts.make_throw(seed, m, d)
    T = thr["T"]
    q_rest = tce.ts.rest_pose(m, d)
    tce.ts.reset_throw(m, d, thr, q_rest, q_open=tce.Q_OPEN)
    
    # Konfiguracja renderera
    width, height = 960, 720
    renderer = mujoco.Renderer(m, height, width)
    opt = mujoco.MjvOption()
    opt.sitegroup[:] = 1
    
    # Kamera overview pokazująca bazę, ramię, tor rzutu i stół
    cam = mujoco.MjvCamera()
    cam.lookat[:] = [0.35, 0.05, 0.35]
    cam.distance = 1.35
    cam.azimuth = 142
    cam.elevation = -24
    
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
    total_steps = int(round(total_time / dt))
    
    caught_t = None
    q_caught = None
    yield_disp = np.zeros(3)
    
    frames = []
    fps_render = 30
    frame_interval = int(round(1000 / fps_render))  # klatka co ~33 ms
    
    print(f"Renderowanie trajektorii i dynamiki fizycznej (T={T:.2f}s, łączny czas={total_time:.2f}s)...")
    
    for step in range(total_steps):
        t = d.time
        
        # Wiatr stochastyczny
        xi = rng.standard_normal(3)
        w += theta * (mu - w) * dt + sigma * np.sqrt(dt) * xi
        m.opt.wind = w
        
        f, other = tce.ts._ball_contacts(m, d, ball_geom, pads, rob)
        dball = np.linalg.norm(d.body("ball").xpos - d.site_xpos[sid])
        f_contact = float(f.max())
        
        if (f_contact > 0.10 or (t >= T - 0.025 and dball < 0.035)) and caught_t is None:
            caught_t = t
            q_caught = q_cmd.copy()
            print(f" >> [t={t:.3f} s] ZDARZENIE KONTAKTU: Wyzwolenie odruchu chwytu Hennemana i pochłaniania energii!")
            
        R_tool = d.xmat[gid].reshape(3, 3)
        
        # Ustąpienie lepkosprężyste (compliant yield)
        if caught_t is not None and t - caught_t < 0.060:
            u_yield = R_tool[:, 2]
            tau_y = 0.025
            target_yield = 0.018 * u_yield
            yield_disp += (dt / tau_y) * (target_yield - yield_disp)
        else:
            tau_y = 0.035
            yield_disp += (dt / tau_y) * (0.0 - yield_disp)
            
        # Pętla sterowania 100 Hz
        if step % 10 == 0:
            p_catch = d.site_xpos[sid].copy()
            p_ball = d.xpos[bid].copy()
            r_rel = p_ball - p_catch
            R_dist = np.linalg.norm(r_rel)
            u_los = r_rel / (R_dist + 1e-6)
            
            v_ball = (p_ball - p_prev_ball) / 0.010 if step > 0 else thr["v0"]
            v_catch = (p_catch - p_prev_catch) / 0.010 if step > 0 else np.zeros(3)
            v_rel = v_ball - v_catch
            p_prev_ball = p_ball.copy()
            p_prev_catch = p_catch.copy()
            
            v_clos = -np.dot(v_rel, u_los)
            v_rel_perp = v_rel - np.dot(v_rel, u_los) * u_los
            d_lambda = v_rel_perp / (R_dist + 1e-6)
            
            u_cam = -R_tool[:, 2]
            u_cam /= np.linalg.norm(u_cam)
            e_ret = u_los - np.dot(u_los, u_cam) * u_cam
            inv_tau = max(0.0, v_clos / (R_dist + 1e-6))
            i_pre = np.clip((inv_tau - 1.2) / 3.0, 0.0, 1.0)
            
            if caught_t is not None and t > caught_t + 0.15:
                # Płynne wycofanie ramienia
                r_retract = np.clip((t - (caught_t + 0.15)) / 0.450, 0.0, 1.0)
                s = r_retract * r_retract * (3.0 - 2.0 * r_retract)
                q_home = np.array([0.0, -0.35, 0.85, 0.40, q_caught[4]])
                q_target = (1.0 - s) * q_caught + s * q_home
                max_step = tce.SERVO_SPEED * 0.010
                q_cmd += np.clip(q_target - q_cmd, -max_step, max_step)
            elif caught_t is None:
                # Naprowadzanie PN
                v_task = 0.0 * u_los + R_dist * (tce.N_PN * d_lambda + tce.K_FIX * e_ret)
                Jp, Jr = tce.ts._jac(m, d, ids, sid)
                J_dls = Jp.T @ np.linalg.inv(Jp @ Jp.T + tce.LAM_DLS**2 * np.eye(3))
                dq = J_dls @ v_task
                max_step = tce.SERVO_SPEED * 0.010
                q_cmd = np.clip(q_cmd + np.clip(dq * 0.010, -max_step, max_step), ids["lo"], ids["hi"])
                
            # Sterowanie chwytakiem
            if caught_t is None:
                q_des_grip = (1.0 - i_pre) * tce.Q_OPEN + i_pre * tce.Q_READY
                torque_grip = 6.0 * (q_des_grip - d.qpos[5]) - 0.4 * d.qvel[5]
                u_grip = np.clip(torque_grip / 3.35, -1.0, 1.0)
            else:
                dt_c = t - caught_t
                if dt_c < 0.050:
                    u_grip = -0.25
                elif dt_c < 0.55:
                    u_grip = -0.12
                else:
                    if f_contact < 2.0:
                        u_grip = -0.055
                    elif f_contact > 3.8:
                        u_grip = -0.020
                    else:
                        u_grip = -0.038
                        
        if np.linalg.norm(yield_disp) > 1e-4:
            Jp, _ = tce.ts._jac(m, d, ids, sid)
            J_dls = Jp.T @ np.linalg.inv(Jp @ Jp.T + tce.LAM_DLS**2 * np.eye(3))
            dq_y = J_dls @ yield_disp
            d.ctrl[:5] = np.clip(q_cmd + dq_y, ids["lo"], ids["hi"])
        else:
            d.ctrl[:5] = q_cmd
            
        d.ctrl[5] = u_grip
        mujoco.mj_step(m, d)
        
        # Zapis klatki wideo
        if step % frame_interval == 0:
            renderer.update_scene(d, camera=cam, scene_option=opt)
            frames.append(renderer.render().copy())
            
    print(f"Wyrenderowano {len(frames)} klatek wideo. Kodowanie ffmpeg...")
    
    # 1. Kodowanie MP4
    mp4_cmd = [
        FFMPEG, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{width}x{height}",
        "-pix_fmt", "rgb24",
        "-r", str(fps_render),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "20",
        out_mp4
    ]
    p = subprocess.Popen(mp4_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    for f in frames:
        p.stdin.write(f.tobytes())
    p.stdin.close()
    p.wait()
    print(f"Zapisano wideo MP4: {out_mp4}")
    
    # 2. Kodowanie GIF (wysokiej jakości paleta lanczos)
    gif_cmd = [
        FFMPEG, "-y",
        "-i", out_mp4,
        "-vf", "fps=18,scale=540:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse",
        out_gif
    ]
    subprocess.run(gif_cmd, check=True)
    print(f"Zapisano animację GIF: {out_gif}")
    
    # 3. Kopiowanie do wymaganych lokalizacji
    os.makedirs(DESKTOP_DIR, exist_ok=True)
    os.makedirs(PARENT_ARTIFACT_DIR, exist_ok=True)
    os.makedirs(CURRENT_ARTIFACT_DIR, exist_ok=True)
    
    targets = [
        (os.path.join(DESKTOP_DIR, "so101_thrown_catch_embodied.mp4"), os.path.join(DESKTOP_DIR, "so101_thrown_catch_embodied.gif")),
        (os.path.join(PARENT_ARTIFACT_DIR, "so101_thrown_catch_embodied.mp4"), os.path.join(PARENT_ARTIFACT_DIR, "so101_thrown_catch_embodied.gif")),
        (os.path.join(CURRENT_ARTIFACT_DIR, "so101_thrown_catch_embodied.mp4"), os.path.join(CURRENT_ARTIFACT_DIR, "so101_thrown_catch_embodied.gif")),
    ]
    
    for dst_mp4, dst_gif in targets:
        shutil.copy2(out_mp4, dst_mp4)
        shutil.copy2(out_gif, dst_gif)
        print(f"Skopiowano do: {dst_mp4} oraz {dst_gif}")


if __name__ == "__main__":
    mp4_tmp = "/tmp/so101_thrown_catch_embodied.mp4"
    gif_tmp = "/tmp/so101_thrown_catch_embodied.gif"
    render_embodied_video(seed=100, out_mp4=mp4_tmp, out_gif=gif_tmp)
