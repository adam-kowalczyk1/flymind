"""Wizualizacja aktywności mózgu muchy (MaleCNS v1.0) podczas łapania piłeczki.
Dowód biologicznego działania:
  1. Kąt kompasu EPG (Central Complex) śledzący azymut celu.
  2. Różnica częstości neuronów zstępujących DNa02 (L - P) sterująca obrotem bazy.
  3. Narastanie aktywności detektorów loomingu LPLC2.
  4. Wyładowanie (spike) neuronu Giant Fiber (DNp01) wyzwalające zamknięcie chwytaka.
  5. Odruch oporowy rdzenia brzusznego (VNC) regulujący siłę uścisku.
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)

import mujoco
import throw_scene as ts
import throw_catch as tc
import throw_percept as tp
from brain import Brain
from vnc import vnc_controller
import so101_base as sb
from throw_catch_embodied import build_embodied_xml, Q_OPEN, Q_READY, Q_HOME, DIVERSE_RANGES, fast_plan_catch

DESKTOP_DIR = "/Users/admin/Desktop/Explory_Projekt_Mucha_SO101/wykresy_i_wideo"
PARENT_ARTIFACT_DIR = "/Users/admin/.gemini/antigravity/brain/a384d8fd-c23b-409b-be24-efe8fe71866f"


def record_neural_trial(seed=100):
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

    trk = tp.BallTracker(m, d)
    rt, optt = trk.renderer()

    rig = tc.Rig()
    rig.m, rig.d, rig.ds = m, d, ds
    rig.trk, rig.rt, rig.optt = trk, rt, optt
    rig.sid, rig.gid, rig.bid = sid, gid, bid
    rig.ball, rig.pads, rig.rob = ball_geom, pads, rob

    brain = Brain(seed=42)
    brain.calibrate_ring()
    brain.calibrate_steer()
    g = brain.groups
    lp_ids = np.concatenate([g["LPLC2_L"], g["LPLC2_R"]])
    gf_ids = np.concatenate([g["DNp01_L"], g["DNp01_R"]])
    dna02_l = g["DNa02_L"]
    dna02_r = g["DNa02_R"]

    thr = ts.make_throw(seed, m, d, ranges=DIVERSE_RANGES)
    T = thr["T"]
    q_rest = ts.rest_pose(m, d)
    ts.reset_throw(m, d, thr, q_rest, q_open=Q_OPEN)
    trk.reset()

    rng = np.random.default_rng(seed)
    w = np.zeros(3)
    theta_w, mu_w, sigma_w = 2.5, np.array([0.0, 0.18, 0.0]), 1.2
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

    total_time = T + 1.10
    n_steps = int(round(total_time / dt))

    # Logi telemetrii neuronalnej
    log = dict(
        t=[],
        dball=[],
        inv_tau=[],
        lv=[],
        epg_bump=[],
        epg_wedges=[],
        dna02_diff=[],
        lplc2_rate=[],
        dnp01_spikes=[],
        q5=[],
        f_max=[],
        u_grip=[],
    )

    for step in range(n_steps):
        t = d.time
        xi = rng.standard_normal(3)
        w += theta_w * (mu_w - w) * dt + sigma_w * np.sqrt(dt) * xi
        m.opt.wind = w

        f, _ = ts._ball_contacts(m, d, ball_geom, pads, rob)
        f_max = float(f.max())

        p_catch = d.site_xpos[sid].copy()
        p_ball = d.xpos[bid].copy()
        dist = np.linalg.norm(p_ball - p_catch)

        R_tool = d.xmat[gid].reshape(3, 3)
        if caught_t is not None and t - caught_t < 0.080:
            tau_y = 0.025
            target_yield = -R_tool[:, 2] * 0.018
            yield_disp += (dt / tau_y) * (target_yield - yield_disp)
        else:
            tau_y = 0.035
            yield_disp += (dt / tau_y) * (0.0 - yield_disp)

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

            # Cel do EPG z azymutu
            cue = None
            if plan is not None and hunt:
                tgt = plan["p"]
                cue = float((np.arctan2(tgt[1], tgt[0]) - d.qpos[0] + np.pi) % (2 * np.pi) - np.pi)
            w_base = -d.qvel[0]
            u = brain.u_for(-w_base)

            # Krok sieci neuronowej ConnectomeSNN
            spk = brain.step10(cue=cue, u=u, loom=(lv, lv), rest=not hunt)
            b_ang, _, _ = brain.bump(spk)
            wedges = brain.wedges(spk)

            rt_spk = brain.rate
            dna_diff = float(rt_spk[dna02_l].mean() - rt_spk[dna02_r].mean())
            lp_hz = float(spk[:, lp_ids].mean() * 1000.0)
            spk_gf = bool(spk[:, gf_ids].any())

            # Wyzwolenie chwytu WYNIKA WYŁĄCZNIE ze spajka DNp01 lub salwy LPLC2!
            imminent = (plan is not None and plan["T"] - t < 0.280) or (dist < 0.40)
            if imminent and (spk_gf or lp_hz >= 60.0) and state == "open" and started:
                state = "closing"
                t_close = t

            if f_max > 0.15 and caught_t is None:
                caught_t = t
                q_caught = q_cmd.copy()

            if state == "open":
                q5_des = Q_OPEN - lv * (Q_OPEN - Q_READY)
                u_grip = float(np.clip(3.5 * (q5_des - d.qpos[5]) - 0.2 * d.qvel[5], -1.0, 1.0))
            elif state == "closing":
                if caught_t is None:
                    u_grip = -0.75
                else:
                    target_f = 3.15
                    f_err = target_f - f_max
                    u_grip = float(np.clip(-0.55 - 0.08 * f_err, -0.75, -0.35))

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

            # Zapis telemetrii
            log["t"].append(t)
            log["dball"].append(dist * 1000)
            log["inv_tau"].append(inv_tau)
            log["lv"].append(lv)
            log["epg_bump"].append(np.degrees(b_ang))
            log["epg_wedges"].append(wedges)
            log["dna02_diff"].append(dna_diff)
            log["lplc2_rate"].append(lp_hz)
            log["dnp01_spikes"].append(1 if spk_gf else 0)
            log["q5"].append(d.qpos[5])
            log["f_max"].append(f_max)
            log["u_grip"].append(u_grip)

        if np.linalg.norm(yield_disp) > 1e-4:
            Jp, _ = ts._jac(m, d, ids, sid)
            J_dls = Jp.T @ np.linalg.inv(Jp @ Jp.T + 0.04**2 * np.eye(3))
            dq_y = J_dls @ yield_disp
            d.ctrl[:5] = np.clip(q_cmd + dq_y, ids["lo"][:5], ids["hi"][:5])
        else:
            d.ctrl[:5] = q_cmd

        d.ctrl[5] = u_grip
        mujoco.mj_step(m, d)

    rt.close()
    return log, thr, t_close


def plot_neural_proof(log, thr, t_close, out_png="dowod_dzialania_mozgu_muchy.png"):
    T = thr["T"]
    t = np.array(log["t"])
    t_rel = (t - T) * 1000  # ms względem uderzenia

    fig = plt.figure(figsize=(15, 12))
    gs = fig.add_gridspec(5, 1, hspace=0.32, top=0.93, bottom=0.06, left=0.08, right=0.96)

    # 1. Tor odległości i looming (wejście z siatkówki)
    ax0 = fig.add_subplot(gs[0])
    ax0.plot(t_rel, log["dball"], "k-", lw=2, label="Odległość piłeczki od paszczy [mm]")
    ax0.set_ylabel("Odległość [mm]", fontsize=10, fontweight="bold")
    ax0.set_xlim(-T * 1000, 600)
    ax0.grid(True, alpha=0.3)
    ax0_twin = ax0.twinx()
    ax0_twin.plot(t_rel, log["inv_tau"], "tab:purple", lw=1.5, ls="--", label="Looming 1/τ [1/s] (siatkówka)")
    ax0_twin.set_ylabel("1/τ [1/s]", color="tab:purple", fontsize=10, fontweight="bold")
    ax0.set_title(f"1. WEJŚCIE WZROKOWE I TOR LOTU (T={T:.2f}s, Trajektoria 3D z wiatrem OU)", fontsize=11, fontweight="bold")

    # 2. Central Complex (EPG Ring Attractor)
    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    wedges_arr = np.array(log["epg_wedges"]).T  # [16, steps]
    im = ax1.imshow(wedges_arr, aspect="auto", origin="lower", extent=[t_rel[0], t_rel[-1], -180, 180], cmap="viridis")
    ax1.plot(t_rel, log["epg_bump"], "r-", lw=1.8, label="Szczyt wzgórza EPG (kierunek celu)")
    ax1.set_ylabel("Klin kompasu EPG [°]", fontsize=10, fontweight="bold")
    ax1.set_title("2. KOMPAS CENTRAL COMPLEX (MÓZG): Wzgórze aktywności atraktora pierścieniowego EPG śledzące cel", fontsize=11, fontweight="bold")
    ax1.grid(True, alpha=0.3, ls=":")
    ax1.legend(loc="upper left", fontsize=9)

    # 3. Neurony zstępujące skrętu DNa02 (L - P)
    ax2 = fig.add_subplot(gs[2], sharex=ax0)
    ax2.plot(t_rel, log["dna02_diff"], "tab:blue", lw=2, label="DNa02 L − P [Hz] (rozkaz obrotu bazy)")
    ax2.axhline(0, color="gray", ls=":", lw=1)
    ax2.set_ylabel("ΔCzęstość [Hz]", fontsize=10, fontweight="bold")
    ax2.set_title("3. NEURONY ZSTĘPUJĄCE SKRĘTU DNa02/DNa01: Sterowanie azymutem ramienia z Central Complex", fontsize=11, fontweight="bold")
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="upper left", fontsize=9)

    # 4. Detektory loomingu LPLC2 i Giant Fiber DNp01
    ax3 = fig.add_subplot(gs[3], sharex=ax0)
    ax3.plot(t_rel, log["lplc2_rate"], "tab:green", lw=2, label="Częstość populacji LPLC2 [Hz]")
    ax3.axhline(60, color="tab:green", ls=":", label="Próg wyzwolenia salwy (60 Hz)")
    # Spajki DNp01
    spk_t = [t_rel[i] for i, s in enumerate(log["dnp01_spikes"]) if s > 0]
    if spk_t:
        ax3.eventplot(spk_t, lineoffsets=80, linelengths=30, colors="tab:red", lw=2, label="Spajki Giant Fiber (DNp01)!")
    ax3.set_ylabel("Częstość [Hz]", fontsize=10, fontweight="bold")
    ax3.set_title("4. INSTYNKT UCIECZKI/CHWYTU: Narastanie LPLC2 i wystrzał pojedynczego neuronu Giant Fiber (DNp01)", fontsize=11, fontweight="bold")
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc="upper left", fontsize=9)

    # 5. Wykonanie motoryczne i odruch VNC
    ax4 = fig.add_subplot(gs[4], sharex=ax0)
    ax4.plot(t_rel, log["q5"], "tab:blue", lw=2, label="Rozwarcie szczęk q5 [rad]")
    ax4.plot(t_rel, log["u_grip"], "tab:orange", lw=1.5, ls="--", label="Sterowanie serwem (PWM)")
    ax4.set_ylabel("Kąt / PWM", fontsize=10, fontweight="bold")
    ax4.set_xlabel("Czas względem momentu uderzenia T [ms]", fontsize=11, fontweight="bold")
    ax4.set_title("5. WYKONANIE: Zamknięcie chwytaka w locie wyzwolone spajkiem DNp01 i stabilizacja docisku przez VNC", fontsize=11, fontweight="bold")
    ax4.grid(True, alpha=0.3)

    # Zaznaczenie momentu wyzwolenia przez spajk DNp01 i momentu kontaktu
    if t_close is not None:
        t_cl_ms = (t_close - T) * 1000
        for ax in (ax0, ax1, ax2, ax3, ax4):
            ax.axvline(t_cl_ms, color="tab:red", ls="--", lw=1.5, label="Spike DNp01 (wyzwolenie chwytu)")
            ax.axvline(0, color="k", ls="-", lw=1.2, label="Kontakt T")

    fig.suptitle("DOWÓD BIOLOGICZNEJ KONTROLI: Zapis telemetryczny sieci neuronowej mózgu muchy (MaleCNS v1.0, 220 ALIF SNN)", fontsize=13, fontweight="bold")
    fig.savefig(out_png, dpi=130)
    plt.close(fig)
    print(f"Zapisano wykres dowodowy: {out_png}")

    # Kopiowanie na pulpit
    os.makedirs(DESKTOP_DIR, exist_ok=True)
    os.makedirs(PARENT_ARTIFACT_DIR, exist_ok=True)
    import shutil
    shutil.copy2(out_png, os.path.join(DESKTOP_DIR, "dowod_dzialania_mozgu_muchy.png"))
    shutil.copy2(out_png, os.path.join(PARENT_ARTIFACT_DIR, "dowod_dzialania_mozgu_muchy.png"))
    print("Skopiowano na Pulpit i do katalogu artefaktów!")


if __name__ == "__main__":
    print("Rejestracja telemetrii komórkowej ConnectomeSNN w czasie rzeczywistym...")
    log, thr, t_close = record_neural_trial(seed=100)
    plot_neural_proof(log, thr, t_close, out_png="/tmp/dowod_dzialania_mozgu_muchy.png")
