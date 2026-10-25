"""Renderuje demonstracyjne wideo MP4 oraz animowany GIF przedstawiający pełny
ucieleśniony, biologiczny pościg, wstępne kształtowanie, wyzwolenie chwytu loomingiem w locie,
amortyzację uderzenia i płynną retrakcję dla ramienia SO-101.
"""

import os
import shutil
import subprocess
import sys

import mujoco
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)

import scene2
import so101_base as sb
import throw_catch as tc
import throw_percept as tp
import throw_scene as ts
from brain import Brain
from throw_catch_embodied import build_embodied_xml, Q_OPEN, Q_READY, Q_HOME, DIVERSE_RANGES, fast_plan_catch
from watch_embodied import BioGripperController

FFMPEG = "/Users/admin/miniforge3/bin/ffmpeg"
DESKTOP_DIR = "/Users/admin/Desktop/Explory_Projekt_Mucha_SO101/wykresy_i_wideo"
PARENT_ARTIFACT_DIR = "/Users/admin/.gemini/antigravity/brain/a384d8fd-c23b-409b-be24-efe8fe71866f"


def render_embodied_video(seed=100, out_mp4="so101_thrown_catch_embodied.mp4", out_gif="so101_thrown_catch_embodied.gif"):
    print(f"Inicjalizacja modelu ucieleśnionego MuJoCo dla seed {seed}...")
    xml_str = build_embodied_xml()
    m = mujoco.MjModel.from_xml_string(xml_str)
    d = mujoco.MjData(m)
    ds = mujoco.MjData(m)

    sid = m.site("catch").id
    gid = m.body("gripper").id
    bid = m.body("ball").id
    ball_geom = m.geom("ball").id
    pads = [m.geom("jaw_fixed").id, m.geom("jaw_moving").id]
    ids = ts._ids(m)
    rob = set(ids["robot"].tolist())

    # Tracker oka
    trk = tp.BallTracker(m, d)
    rt, optt = trk.renderer()

    # Struktura Rig dla plan_catch
    rig = tc.Rig()
    rig.m, rig.d, rig.ds = m, d, ds
    rig.trk, rig.rt, rig.optt = trk, rt, optt
    rig.sid = sid
    rig.gid = gid
    rig.bid = bid
    rig.ball = ball_geom
    rig.pads = pads
    rig.rob = rob

    # Mózg muchy (ConnectomeSNN ALIF)
    brain = Brain(seed=42)
    brain.calibrate_ring()
    brain.calibrate_steer()
    g = brain.groups
    lp_ids = np.concatenate([g["LPLC2_L"], g["LPLC2_R"]])
    gf_ids = np.concatenate([g["DNp01_L"], g["DNp01_R"]])

    thr = ts.make_throw(seed, m, d, ranges=DIVERSE_RANGES)
    T = thr["T"]
    q_rest = ts.rest_pose(m, d)
    ts.reset_throw(m, d, thr, q_rest, q_open=Q_OPEN)
    trk.reset()

    # Konfiguracja renderera HD (kamera zewnętrzna)
    width, height = 960, 720
    renderer = mujoco.Renderer(m, height, width)
    opt = mujoco.MjvOption()
    opt.sitegroup[:] = 1

    cam = mujoco.MjvCamera()
    cam.lookat[:] = [0.35, 0.05, 0.35]
    cam.distance = 1.35
    cam.azimuth = 142
    cam.elevation = -24

    w = np.zeros(3)
    theta_w, mu_w, sigma_w = 2.5, np.array([0.0, 0.15, 0.0]), 1.2
    dt = 0.001
    rng = np.random.default_rng(seed)

    q_cmd = q_rest.copy()
    q_target = q_rest.copy()
    plan, z_prev, q_prev = None, None, q_rest.copy()
    started = False

    gripper = BioGripperController(q_open=Q_OPEN, q_preshape=0.68)
    caught_t = None
    q_caught = None
    u_grip = 0.5
    yield_disp = np.zeros(3)
    r_hist = []

    total_time = T + 1.20
    total_steps = int(round(total_time / dt))

    frames = []
    fps_render = 30
    frame_interval = int(round(1000 / fps_render))

    print(f"Renderowanie trajektorii i fizyki biologicznej (T={T:.2f}s, łączny czas={total_time:.2f}s)...")

    for step in range(total_steps):
        t = d.time

        # Wiatr stochastyczny
        xi = rng.standard_normal(3)
        w += theta_w * (mu_w - w) * dt + sigma_w * np.sqrt(dt) * xi
        m.opt.wind = w

        f, _ = ts._ball_contacts(m, d, ball_geom, pads, rob)
        f_max = float(f.max())

        p_catch = d.site_xpos[sid].copy()
        p_ball = d.xpos[bid].copy()
        dist = np.linalg.norm(p_ball - p_catch)

        # Amortyzacja lepkosprężysta po kontakcie
        R_tool = d.xmat[gid].reshape(3, 3)
        if caught_t is not None and t - caught_t < 0.080:
            tau_y = 0.025
            target_yield = -R_tool[:, 2] * 0.018
            yield_disp += (dt / tau_y) * (target_yield - yield_disp)
        else:
            tau_y = 0.035
            yield_disp += (dt / tau_y) * (0.0 - yield_disp)

        # Pętla percepcji i sieci neuronowej (100 Hz)
        if step % 10 == 0:
            hunt = trk.n >= trk.n_min
            o = None
            if plan is None or plan["T"] - t > tc.STOP_PLAN:
                rt.update_scene(d, camera="eye", scene_option=optt)
                o = trk.step(rt.render(), t)
                if o["ready"]:
                    p = fast_plan_catch(rig, trk, t, d.qpos[:5], q_prev, z_prev)
                    if p is not None:
                        plan, z_prev, q_prev = p, p["z"], p["q"]
                        if not started and p["sig_y"] < 1.0:
                            started = True
                        if started:
                            q_target = p["q"].copy()

            inv_tau, lv = 0.0, 0.0
            blob = None if o is None else o["blob"]
            if blob is not None and blob["conf"] >= 0.2 and not blob["border"] and blob["A"] >= 25.0:
                r_hist.append((t, float(np.sqrt(blob["A"] / np.pi) - trk.delta)))
            r_hist = [h for h in r_hist if t - h[0] < 0.105]
            if len(r_hist) >= 4:
                tt_, rr_ = np.array(r_hist).T
                sl, ic = np.polyfit(tt_, rr_, 1)
                r_fit = sl * t + ic
                if r_fit > 1.0:
                    inv_tau = float(sl / r_fit)
                    lv = float(np.clip((inv_tau - 2.5) / 0.5, 0.0, 1.0))

            spk = brain.step10(cue=0.0, u=0.0, loom=(lv, lv), rest=not hunt)
            lp_hz = float(spk[:, lp_ids].mean() * 1000.0)
            spk_gf = bool(spk[:, gf_ids].any())

            ttc = (plan["T"] - t) if plan is not None else (T - t)
            u_grip = gripper.step(
                t=t, dt=0.010,
                q_grip=d.qpos[5], dq_grip=d.qvel[5],
                lplc2_hz=lp_hz, gf_spike=spk_gf,
                ttc=ttc, dist_to_jaw=dist,
                contact_force=f_max
            )
            if gripper.latch_active and gripper.latch_time == t:
                print(f" >> [t={t:.3f} s, T-t={T-t:.3f} s] ZATRZASK CHWYTNY: {gripper.snap_reason}!")

            if f_max > 0.15 and caught_t is None:
                caught_t = t
                q_caught = q_cmd.copy()
                print(f" >> [t={t:.3f} s] KONTAKT: Pochłanianie energii i docisk kutykularny (F={f_max:.1f} N)!")

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

        if np.linalg.norm(yield_disp) > 1e-4:
            Jp, _ = ts._jac(m, d, ids, sid)
            J_dls = Jp.T @ np.linalg.inv(Jp @ Jp.T + 0.04**2 * np.eye(3))
            dq_y = J_dls @ yield_disp
            d.ctrl[:5] = np.clip(q_cmd + dq_y, ids["lo"][:5], ids["hi"][:5])
        else:
            d.ctrl[:5] = q_cmd

        d.ctrl[5] = u_grip
        mujoco.mj_step(m, d)

        # Zapis klatki wideo
        if step % frame_interval == 0:
            renderer.update_scene(d, camera=cam, scene_option=opt)
            frames.append(renderer.render().copy())

    rt.close()
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

    targets = [
        (os.path.join(DESKTOP_DIR, "so101_thrown_catch_embodied.mp4"), os.path.join(DESKTOP_DIR, "so101_thrown_catch_embodied.gif")),
        (os.path.join(PARENT_ARTIFACT_DIR, "so101_thrown_catch_embodied.mp4"), os.path.join(PARENT_ARTIFACT_DIR, "so101_thrown_catch_embodied.gif")),
    ]

    for dst_mp4, dst_gif in targets:
        shutil.copy2(out_mp4, dst_mp4)
        shutil.copy2(out_gif, dst_gif)
        print(f"Skopiowano do: {dst_mp4} oraz {dst_gif}")


if __name__ == "__main__":
    mp4_tmp = "/tmp/so101_thrown_catch_embodied.mp4"
    gif_tmp = "/tmp/so101_thrown_catch_embodied.gif"
    render_embodied_video(seed=100, out_mp4=mp4_tmp, out_gif=gif_tmp)
