"""Etap 1 (bio2) — weryfikacja sceny: 10 s, pętla 100 Hz (10 kroków fizyki po 1 ms + render kamery).

 0–6 s    ramię w pozie chwytu, szczęki otwarte; piłeczka toczy się w poprzek pola widzenia (0,1 m/s)
 1,5–3 s  przesłona wysuwa się spod stołu między kamerę a tor piłeczki (plan: 1,5 s zasłonięcia)
 7–10 s   sonda (swobodna kulka 5 cm) stoi na stole między szczękami, chwytak domyka się PWM 0,05

Zasłonięcie mierzone z SEGMENTACJI obrazu kamery (piksele należące do piłeczki), nie z harmonogramu.
Czujniki touch porównywane z niezależną siłą kontaktu MuJoCo (mj_contactForce).
Wynik: results/stage1.png
"""
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mujoco
import numpy as np

import scene2

HERE = os.path.dirname(os.path.abspath(__file__))
T = 10.0
OCC_IN, OCC_OUT = 1.5, 3.0
OCC_UP, OCC_DOWN = 0.05, -0.06          # z środka przesłony: wysunięta / schowana pod stołem
PROBE_T, CLOSE_T, HOLD_PWM = 7.0, 7.2, 0.05


def pair_force(m, d, g1, g2):
    """Suma sił normalnych kontaktów między geomami g1 i g2 [N]."""
    f6, tot = np.zeros(6), 0.0
    for i in range(d.ncon):
        c = d.contact[i]
        if {c.geom1, c.geom2} == {g1, g2}:
            mujoco.mj_contactForce(m, d, i, f6)
            tot += abs(f6[0])
    return tot


def main():
    m, d = scene2.load()
    q, err = scene2.reset_scene(m, d)
    scene2.set_mocap(m, d, "occluder", (scene2.OCC_X, 0.0, OCC_DOWN))
    rgb_r, opt = scene2.eye_renderer(m)
    seg_r, _ = scene2.eye_renderer(m)
    seg_r.enable_segmentation_rendering()
    gid = {n: m.geom(n).id for n in ("ball", "table", "occluder", "probe", "jaw_fixed", "jaw_moving", "palm")}
    n_sub = round(scene2.scene.CONTROL_DT / m.opt.timestep)
    steps = round(T / scene2.scene.CONTROL_DT)

    log = dict(t=[], ball_px=[], ball=[], touch=[], f_contact=[], ms_phys=[], ms_render=[], ms_seg=[])
    frames, frame_t = {}, [1.0, 2.2, 3.6, 9.5]
    pairs = set()
    for k in range(steps):
        t = k * scene2.scene.CONTROL_DT
        # przesłona: wysuwanie/chowanie w 0,1 s
        z = np.interp(t, [OCC_IN, OCC_IN + 0.1, OCC_OUT - 0.1, OCC_OUT], [OCC_DOWN, OCC_UP, OCC_UP, OCC_DOWN])
        scene2.set_mocap(m, d, "occluder", (scene2.OCC_X, 0.0, z))
        if abs(t - PROBE_T) < 1e-9:   # sonda na stole w punkcie chwytu, 1,5 mm od stałej szczęki i 1 mm od dłoni
            R = d.body("gripper").xmat.reshape(3, 3)
            p = d.site("grasp").xpos + R @ np.array([0.0015, 0, -0.001])
            scene2.place_free(m, d, "probe", (p[0], p[1], scene2.scene.BALL_R))
        d.ctrl[5] = -HOLD_PWM if t >= CLOSE_T else 0.0
        t0 = time.perf_counter()
        for _ in range(n_sub):
            mujoco.mj_step(m, d)
        t1 = time.perf_counter()
        rgb_r.update_scene(d, camera="eye", scene_option=opt)
        img = rgb_r.render()
        t2 = time.perf_counter()
        seg_r.update_scene(d, camera="eye", scene_option=opt)      # segmentacja: tylko do weryfikacji
        seg = seg_r.render()
        t3 = time.perf_counter()
        for c in d.contact[:d.ncon]:
            pairs.add(tuple(sorted(mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or f"#{g}"
                                   for g in (c.geom1, c.geom2))))
        log["t"].append(d.time)
        log["ball_px"].append(int(((seg[..., 0] == gid["ball"]) & (seg[..., 1] == mujoco.mjtObj.mjOBJ_GEOM)).sum()))
        log["ball"].append(d.body("ball").xpos.copy())
        log["touch"].append(d.sensordata[:3].copy())
        log["f_contact"].append([pair_force(m, d, gid["probe"], gid["jaw_fixed"]),
                                 pair_force(m, d, gid["probe"], gid["jaw_moving"])])
        log["ms_phys"].append((t1 - t0) * 1e3)
        log["ms_render"].append((t2 - t1) * 1e3)
        log["ms_seg"].append((t3 - t2) * 1e3)
        for ft in frame_t:
            if ft not in frames and d.time >= ft:
                frames[ft] = img.copy()
        if not np.isfinite(d.qpos).all():
            print("BŁĄD: niestabilna fizyka (NaN)")
            return 1
    L = {k: np.array(v) for k, v in log.items()}
    t = L["t"]

    # --- zasłonięcie z segmentacji ---
    vis = L["ball_px"] > 0
    in_win = (t > 0.5) & (t < 5.5)
    hidden = (~vis) & in_win
    runs, start = [], None
    for i, h in enumerate(hidden):
        if h and start is None:
            start = i
        if (not h or i == len(hidden) - 1) and start is not None:
            runs.append((t[start], t[i]))
            start = None
    longest = max(runs, key=lambda r: r[1] - r[0]) if runs else (np.nan, np.nan)
    hid_s = longest[1] - longest[0]
    # --- czujniki vs kontakt ---
    sel = t > 9.0
    touch, fc = L["touch"][sel][:, :2], L["f_contact"][sel]
    rel = np.abs(touch.mean(0) - fc.mean(0)) / np.maximum(fc.mean(0), 1e-9)
    cyc = L["ms_phys"] + L["ms_render"]
    ball_pairs = sorted(p for p in pairs if "ball" in p)
    arm_table = sorted(p for p in pairs if "table" in p and "ball" not in p and "probe" not in p)
    load1, ncpu = os.getloadavg()[0], os.cpu_count()

    print(f"IK pozy: błąd {err * 1000:.1f} mm; kamera „eye” {scene2.CAM_W}×{scene2.CAM_H}, fovy {scene2.CAM_FOVY:.0f}°")
    print(f"Cykl 10 ms (ściana): fizyka {L['ms_phys'].mean():.2f} ms + render RGB {L['ms_render'].mean():.2f} ms "
          f"= p99 {np.percentile(cyc, 99):.2f} ms, max {cyc.max():.2f} ms (+ segmentacja tylko do testu "
          f"{L['ms_seg'].mean():.2f} ms)")
    print(f"Obciążenie maszyny: {load1:.1f} przy {ncpu} rdzeniach"
          + ("  → POMIAR CZASU NIEWIARYGODNY (inne procesy zajmują CPU/GPU)" if load1 > ncpu else ""))
    y = L["ball"][:, 1]
    print(f"Piłeczka: y {y[0]:+.3f} → {y[600]:+.3f} m w 6 s (śr. {abs(y[600] - y[0]) / 6:.3f} m/s), "
          f"wysokość {L['ball'][:600, 2].min():.4f}–{L['ball'][:600, 2].max():.4f} m")
    print(f"Kontakty piłeczki: {ball_pairs}; ramię/przesłona–stół: {arm_table or 'brak'} (sonda–stół to stan zamierzony)")
    print(f"Zasłonięcie (segmentacja): najdłuższe {longest[0]:.2f}–{longest[1]:.2f} s = {hid_s:.2f} s "
          f"(plan {OCC_OUT - OCC_IN:.1f} s); widoczna przed: {vis[(t > 0.5) & (t < 1.4)].mean() * 100:.0f}% klatek, "
          f"po: {vis[(t > 3.2) & (t < 4.5)].mean() * 100:.0f}%; piksele kulki max {L['ball_px'].max()}")
    print(f"Sonda 9–10 s: touch stała/ruchoma {touch.mean(0).round(3)} N, siła kontaktu {fc.mean(0).round(3)} N, "
          f"różnica {np.round(rel * 100, 2)} %")

    checks = {
        "fizyka stabilna (brak NaN)": True,
        "piłeczka toczy się po stole (≥ 0,4 m w 6 s, nie podskakuje > 2 mm)":
            abs(y[600] - y[0]) >= 0.4 and np.ptp(L["ball"][:600, 2]) < 0.002,
        "piłeczka nie zderza się z ramieniem ani przesłoną": not any(
            n in p for p in ball_pairs for n in ("occluder", "jaw_fixed", "jaw_moving", "palm") if "probe" not in p),
        "brak kolizji ramię–stół": not arm_table,
        "przesłona zasłania 1,5 s ± 0,15 s (segmentacja)": abs(hid_s - 1.5) <= 0.15,
        "piłeczka widoczna przed i po zasłonięciu": vis[(t > 0.5) & (t < 1.4)].all() and vis[(t > 3.2) & (t < 4.5)].all(),
        "obie szczęki czują sondę (> 0,3 N)": (touch.mean(0) > 0.3).all(),
        "touch zgodny z siłą kontaktu (< 5 %)": (rel < 0.05).all(),
        "pętla 100 Hz z renderem w czasie rzeczywistym (p99 < 10 ms)": np.percentile(cyc, 99) < 10.0,
    }

    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    fig = plt.figure(figsize=(14, 7))
    for i, ft in enumerate(frame_t):
        a = fig.add_subplot(2, 4, i + 1)
        a.imshow(frames[ft])
        a.set_title(f"oko w dłoni, t = {ft:.1f} s", fontsize=10)
        a.axis("off")
    a = fig.add_subplot(2, 2, 3)
    a.plot(t, L["ball_px"], color="#2a78d6", lw=1.5)
    a.axvspan(OCC_IN, OCC_OUT, color="#eda100", alpha=0.15)
    a.text(OCC_IN, L["ball_px"].max() * 0.9, " przesłona (plan)", fontsize=9, color="#52514e")
    a.set_xlabel("czas [s]")
    a.set_ylabel("piksele piłeczki w obrazie")
    a.set_title(f"Zasłonięcie z segmentacji: {hid_s:.2f} s", fontsize=10)
    a = fig.add_subplot(2, 2, 4)
    a.plot(t, L["touch"][:, 0], color="#2a78d6", lw=1.5, label="touch: szczęka stała")
    a.plot(t, L["touch"][:, 1], color="#eb6834", lw=1.5, label="touch: szczęka ruchoma")
    a.plot(t, L["f_contact"][:, 0], color="#52514e", lw=1, ls="--", label="siła kontaktu (MuJoCo)")
    a.plot(t, L["f_contact"][:, 1], color="#52514e", lw=1, ls="--")
    a.set_xlim(6.8, 10)
    a.set_xlabel("czas [s]")
    a.set_ylabel("siła [N]")
    a.set_title("Czujniki nacisku vs niezależna siła kontaktu", fontsize=10)
    a.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "results", "stage1.png"), dpi=120)

    for k, v in checks.items():
        print(("OK   " if v else "BŁĄD ") + k)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
