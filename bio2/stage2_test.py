"""Etap 2 (bio2) — samodzielny test: FlyRetinaFilter + ConnectomeSNN (mózg: CX, DN, looming, HS; VNC: chwyt).

A  Siatkówka na klatkach ze sceny Etapu 1 (piłeczka toczy się, przesłona wysuwa się na 1,5 s).
B  Pierścień EPG: bodziec ustawia wzgórze → 1,5 s bez bodźca (pamięć) → sztuczny obrót +45°/s 1 s, 0,5 s
   spoczynku, −30°/s 1 s; wzgórze porównane z całką zadanej prędkości. Statystyka na 6 ziarnach szumu.
C  Neurony zstępujące: kierunek DNa02/DNa01 względem wzgórza (PFL3), looming → DNp01, bliskość → MDN,
   stop → DNp09, ruch obrazu → HS.
D  Rdzeń brzuszny: zasada Hennemana, bramka AND stanu „trzymam”, płytka włoskowa (wyłącznik krańcowy).
Wyniki: results/stage2.png (raster, 16 klinów, wzgórze vs całka), results/stage2_retina.png
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
from brain import Brain
from retina import FlyRetinaFilter, reduction
from vnc import vnc_controller

HERE = os.path.dirname(os.path.abspath(__file__))
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]


# ------------------------------------------------------------------ A: siatkówka
def retina_test():
    m, d = scene2.load()
    scene2.reset_scene(m, d)
    r, opt = scene2.eye_renderer(m)
    f = FlyRetinaFilter()
    n_sub = round(scene2.scene.CONTROL_DT / m.opt.timestep)
    occ = lambda t: np.interp(t, [1.5, 1.6, 2.9, 3.0], [-0.06, 0.05, 0.05, -0.06])
    E1, E2, snaps = [], [], {}
    for k in range(400):
        t = k * 0.01
        scene2.set_mocap(m, d, "occluder", (scene2.OCC_X, 0.0, occ(t)))
        for _ in range(n_sub):
            mujoco.mj_step(m, d)
        r.update_scene(d, camera="eye", scene_option=opt)
        img = r.render()
        o = f.step(img)
        E1.append(o["L1"].sum())
        E2.append(o["L2"].sum())
        for ts in (1.0, 1.55, 2.2):
            if ts not in snaps and t >= ts:
                snaps[ts] = (img.copy(), o)
    E1, E2 = np.array(E1), np.array(E2)
    t = np.arange(400) * 0.01
    res = dict(reduction_128=reduction((96, 128)), reduction_hd=reduction((1080, 1920)),
               L1_rolling=float(E1[(t > 0.6) & (t < 1.4)].mean()), L2_rolling=float(E2[(t > 0.6) & (t < 1.4)].mean()),
               L2_occ_up=float(E2[(t >= 1.5) & (t < 1.7)].max()), L1_occ_up=float(E1[(t >= 1.5) & (t < 1.7)].max()),
               L_static=float((E1 + E2)[(t > 2.3) & (t < 2.8)].mean()))
    fig, ax = plt.subplots(3, 4, figsize=(14, 8), gridspec_kw=dict(width_ratios=[1.3, 1, 1, 1]))
    for i, ts in enumerate(sorted(snaps)):
        img, o = snaps[ts]
        ax[i, 0].imshow(img)
        ax[i, 0].set_title(f"kamera 128×96, t = {ts:.2f} s", fontsize=9)
        for j, (k, cm) in enumerate((("photo", "gray"), ("L1", "Greens"), ("L2", "Purples"))):
            ax[i, j + 1].imshow(o[k], cmap=cm, vmin=0, vmax=1 if k == "photo" else max(o[k].max(), 0.05))
            ax[i, j + 1].set_title({"photo": "ommatidia 32×24 (0,6·B + 0,4·G)", "L1": "L1 — ON", "L2": "L2 — OFF"}[k],
                                   fontsize=9)
        for a in ax[i]:
            a.axis("off")
    fig.suptitle("FlyRetinaFilter na klatkach ze sceny: toczenie (1,0 s), wysuwanie przesłony (1,55 s), przesłona stoi (2,2 s)")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "results", "stage2_retina.png"), dpi=110)
    return res


# ------------------------------------------------------------------ B: pierścień EPG
PROFILE = [(0.3, None, "cue"), (1.5, 0.0, "pamięć"), (1.0, 45.0, "+45°/s"), (0.5, 0.0, "spoczynek"), (1.0, -30.0, "−30°/s")]


def ring_run(seed, record=False):
    b = Brain(seed=seed)
    b.calibrate_ring()
    c0 = np.radians(60.0)
    true, est, skup, wedges, spikes = [], [], [], [], []
    ang = c0
    for dur, om, label in PROFILE:
        for _ in range(int(dur * 100)):
            if om is None:
                s = b.step10(cue=c0)
            else:
                ang += np.radians(om) * 0.01
                s = b.step10(u=b.u_for(np.radians(om)))
            a, sk, _ = b.bump(s)
            true.append(ang)
            est.append(a)
            skup.append(sk)
            if record:
                wedges.append(b.wedges(s))
                spikes.append(s)
    est = np.unwrap(est)
    true = np.array(true)
    k_cue = int(PROFILE[0][0] * 100)
    est += np.round((true[k_cue - 1] - est[k_cue - 1]) / (2 * np.pi)) * 2 * np.pi
    err = np.degrees(np.angle(np.exp(1j * (est - true))))
    out = dict(seed=seed, err=err, skup=np.array(skup), true=np.degrees(true), est=np.degrees(est))
    if record:
        out.update(wedges=np.array(wedges), spikes=np.concatenate(spikes), groups=b.groups, N=b.N, calib=b.calib)
    return out


# ------------------------------------------------------------------ C: neurony zstępujące
def dn_test():
    b = Brain(seed=0)
    g = b.groups
    res = {}
    for name, c in (("cel −60° (prawo)", -60.0), ("cel 0°", 0.0), ("cel +60° (lewo)", 60.0)):
        b.reset()
        for _ in range(40):
            b.step10(cue=np.radians(c))
        S = np.concatenate([b.step10(cue=np.radians(c)) for _ in range(50)])
        res[name] = {k: S[:, g[k]].mean() * 1000 for k in ("DNa02_L", "DNa02_R", "DNa01_L", "DNa01_R")}

    def rate(keys, **kw):
        b.reset()
        S = np.concatenate([b.step10(**kw) for _ in range(30)])
        return float(S[:, np.concatenate([g[k] for k in keys])].mean() * 1000)
    gf = ("DNp01_L", "DNp01_R")
    res["DNp01 spoczynek"] = rate(gf)
    res["DNp01 looming L"] = rate(("DNp01_L",), loom=(1.0, 0.0))
    res["DNp01 looming P (strona L)"] = rate(("DNp01_L",), loom=(0.0, 1.0))
    res["DNp01 mała piłeczka (cel, bez loomingu)"] = rate(gf, cue=0.3)
    res["MDN spoczynek"] = rate(("MDN_L", "MDN_R"))
    res["MDN blisko"] = rate(("MDN_L", "MDN_R"), near=1.0)
    res["DNp09 spoczynek"] = rate(("DNp09_L", "DNp09_R"))
    res["DNp09 stop"] = rate(("DNp09_L", "DNp09_R"), stop=1.0)
    res["HS_L ruch w lewo"] = rate(("HS_L",), flow=1.0)
    res["HS_R ruch w lewo"] = rate(("HS_R",), flow=1.0)
    return res


# ------------------------------------------------------------------ D: rdzeń brzuszny
def vnc_test():
    v = vnc_controller(seed=0, params=dict(noise=0.0))
    g = v.groups
    ids = g["MN_flex"]
    first = {}
    for k in range(2000):                       # rampa prądu 0→60 mV przez 2 s (bez szumu)
        I = v.inputs(None, (0, 0, 0), active=False)
        I[ids] += 60.0 * k / 2000
        s = v.net.step(I)
        for i in ids[s[ids]]:
            first.setdefault(v.mn_class[i], k)
    andt = {}
    for name, f in (("tylko stała 5 N", (5, 0, 0)), ("tylko ruchoma 5 N", (0, 5, 0)), ("obie 0,5 N", (0.5, 0.5, 0))):
        v2 = vnc_controller(seed=0)
        for k in range(15):
            v2.control_step(None, f, True)
        h = [v2.control_step(None, (0, 0, 0), True)[2][:, g["RR_hold"]].mean() * 1000 for _ in range(15)]
        andt[name] = float(np.mean(h[5:]))
    hp = {}
    for q in (0.5, -0.12, -0.17):
        v3 = vnc_controller(seed=0)
        for k in range(5):
            v3.control_step(None, (0, 0, 1.0), True, jaw_q=1.0)
        tau = [v3.control_step(None, (0, 0, 0), True, jaw_q=q)[1] for _ in range(30)]
        hp[q] = float(np.mean(tau[-10:]))
    return dict(first=first, andt=andt, hp=hp, n=v.N)


def main():
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    A = retina_test()
    with Pool(6) as pool:
        runs = pool.map(ring_run, range(1, 6))
    rec = ring_run(0, record=True)
    runs = [rec] + runs
    C = dn_test()
    D = vnc_test()

    t = np.arange(len(rec["err"])) * 0.01
    k_mem = (t >= 0.3) & (t < 1.8)
    k_rot = t >= 1.8
    err_mem_end = np.array([abs(r["err"][179]) for r in runs])
    err_rot_end = np.array([abs(r["err"][-1]) for r in runs])
    skup_mem = np.array([r["skup"][k_mem].mean() for r in runs])
    shift_rot = np.array([r["est"][279] - r["est"][179] for r in runs])        # +45°/s przez 1 s
    shift_neg = np.array([r["est"][-1] - r["est"][329] for r in runs])          # −30°/s przez 1 s
    S = rec["spikes"]
    win = S[: len(S) // 50 * 50].reshape(-1, 50, S.shape[1]).sum(1) * 20.0
    epg_rate = S[:, rec["groups"]["EPG"]].mean() * 1000

    print(f"A. Siatkówka: redukcja danych 128×96 RGB → 768: {A['reduction_128'] * 100:.2f} %, Full HD → 768: "
          f"{A['reduction_hd'] * 100:.3f} %")
    print(f"   toczenie piłeczki: L1 {A['L1_rolling']:.2f}, L2 {A['L2_rolling']:.2f} (suma po 768 punktach); "
          f"wysunięcie przesłony: L2 max {A['L2_occ_up']:.2f}, L1 max {A['L1_occ_up']:.2f}; "
          f"scena statyczna: L1+L2 {A['L_static']:.3f}")
    vs, us = rec["calib"]
    print("B. Pierścień EPG (6 ziaren): kalibracja u → °/s:", dict(zip(np.round(us, 2), np.round(np.degrees(vs)).astype(int))))
    print(f"   pamięć 1,5 s bez bodźca: |błąd| {err_mem_end.mean():.1f}° (max {err_mem_end.max():.1f}°), "
          f"skupienie {skup_mem.mean():.2f}")
    print(f"   obrót +45°/s × 1 s: przesunięcie {shift_rot.mean():+.1f} ± {shift_rot.std():.1f}° (cel +45°); "
          f"−30°/s × 1 s: {shift_neg.mean():+.1f} ± {shift_neg.std():.1f}° (cel −30°)")
    print(f"   błąd na końcu (po 2,5 s całkowania od zniknięcia bodźca + 1,5 s pamięci): |błąd| {err_rot_end.mean():.1f}° "
          f"(max {err_rot_end.max():.1f}°)")
    print(f"   aktywność: EPG średnio {epg_rate:.1f} Hz, max pojedynczego neuronu (okno 50 ms) {win.max():.0f} Hz")
    print("C. Neurony zstępujące [Hz]:")
    for k, v in C.items():
        print(f"   {k}: " + (", ".join(f"{a} {b:.0f}" for a, b in v.items()) if isinstance(v, dict) else f"{v:.0f}"))
    print(f"D. VNC ({D['n']} neuronów): rekrutacja MN [ms] {D['first']}; RR_hold po puszczeniu [Hz] {D['andt']}; "
          f"moment zamykania przy kącie szczęki [N·m] {D['hp']}")

    dn = C
    checks = {
        "siatkówka: toczenie → L1 i L2 > 0, statyczna scena ≈ 0 (< 5 % toczenia)":
            A["L1_rolling"] > 0.1 and A["L2_rolling"] > 0.1 and A["L_static"] < 0.05 * (A["L1_rolling"] + A["L2_rolling"]),
        "siatkówka: ciemna przesłona → L2 (OFF) > L1 (ON)": A["L2_occ_up"] > A["L1_occ_up"],
        "pierścień: jedno skupione wzgórze w pamięci (skupienie > 0,5)": skup_mem.min() > 0.5,
        "pierścień: pamięć 1,5 s, |błąd| < 30° (średnio po 6 ziarnach)": err_mem_end.mean() < 30,
        "pierścień: obrót przesuwa wzgórze we właściwą stronę (6/6 ziaren, oba kierunki)":
            (shift_rot > 0).all() and (shift_neg < 0).all(),
        "brak eksplozji: max częstość < 300 Hz, EPG średnio < 100 Hz": win.max() < 300 and epg_rate < 100,
        "PFL3→DNa02: cel po prawej → DNa02_R > L, po lewej → L > R":
            dn["cel −60° (prawo)"]["DNa02_R"] > dn["cel −60° (prawo)"]["DNa02_L"]
            and dn["cel +60° (lewo)"]["DNa02_L"] > dn["cel +60° (lewo)"]["DNa02_R"],
        "looming → DNp01 (≥ 20 Hz), mała piłeczka bez loomingu → DNp01 < 5 Hz":
            dn["DNp01 looming L"] >= 20 and dn["DNp01 mała piłeczka (cel, bez loomingu)"] < 5,
        "MDN i DNp09 odpowiadają na swoje wejścia (× 2 względem spoczynku)":
            dn["MDN blisko"] > 2 * dn["MDN spoczynek"] + 5 and dn["DNp09 stop"] > 2 * dn["DNp09 spoczynek"] + 5,
        "zasada Hennemana: wolne < pośrednie < szybkie": D["first"]["slow"] < D["first"]["int"] < D["first"]["fast"],
        "bramka AND: jedna szczęka nie włącza „trzymam”, obie tak":
            max(D["andt"]["tylko stała 5 N"], D["andt"]["tylko ruchoma 5 N"]) < 10 and D["andt"]["obie 0,5 N"] > 30,
        "płytka włoskowa: przy krańcu moment ≤ 25 % momentu daleko od krańca": D["hp"][-0.17] <= 0.25 * D["hp"][0.5],
    }

    # --- rysunek: raster, 16 klinów, wzgórze vs całka ---
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(3, 1, figsize=(13, 12), sharex=True, gridspec_kw=dict(height_ratios=[3, 1.4, 1.4]))
    g = rec["groups"]
    order = ["EPG", "PEN_a_L", "PEN_a_R", "PEN_b_L", "PEN_b_R", "Delta7", "PFL3_L", "PFL3_R", "DNa02_L", "DNa02_R",
             "DNa01_L", "DNa01_R", "MDN_L", "MDN_R", "DNp01_L", "DNp01_R", "DNp09_L", "DNp09_R", "LC4_L", "LC4_R",
             "LPLC2_L", "LPLC2_R", "HS_L", "HS_R"]
    tms = np.arange(len(S)) / 1000
    row, ticks = 0, []
    b0 = Brain(seed=0)
    for ci, key in enumerate(order):
        ids = g[key]
        if key == "EPG":
            ids = ids[np.argsort(b0.theta[ids])]
        for i in ids:
            tt = tms[S[:, i]]
            ax[0].scatter(tt, np.full(len(tt), row), s=0.8, marker="|", color=CAT[ci % len(CAT)])
            row += 1
        ticks.append((row - len(ids) / 2, f"{key} ({len(ids)})"))
        ax[0].axhline(row - 0.5, color=GRID, lw=0.5)
    ax[0].set_yticks([a for a, _ in ticks], [l for _, l in ticks], fontsize=7)
    ax[0].set_ylim(-0.5, row - 0.5)
    ax[0].set_title(f"Raster mózgu bio2 ({rec['N']} neuronów z MaleCNS v1.0), dt = 1 ms; EPG posortowane wg kąta", color=INK)
    tsum = 0
    for dur, om, label in PROFILE:
        for a in ax:
            a.axvline(tsum, color=INK2, lw=0.6, ls=":")
        ax[0].text(tsum + 0.02, row, label, fontsize=8, color=INK2, va="bottom")
        tsum += dur
    wd = rec["wedges"].T
    im = ax[1].imshow(wd, aspect="auto", origin="lower", extent=[0, t[-1], -0.5, 15.5], cmap="Blues")
    ax[1].set_ylabel("klin EB (0–15)")
    ax[1].set_title("Aktywność 16 klinów pierścienia EPG [Hz]", color=INK)
    fig.colorbar(im, ax=ax[1], pad=0.01, fraction=0.02)
    ax[2].plot(t, rec["true"], color=INK2, lw=1.5, ls="--", label="całka zadanej prędkości (prawda)")
    ax[2].plot(t, rec["est"], color=CAT[0], lw=1.5, label="wzgórze EPG (wektor populacyjny)")
    ax[2].set_ylabel("kąt [°]")
    ax[2].set_xlabel("czas [s]")
    ax[2].legend(frameon=False, fontsize=8)
    ax[2].grid(axis="y", color=GRID)
    ax[2].set_title(f"Całkowanie obrotu: |błąd| po pamięci {err_mem_end.mean():.0f}°, na końcu {err_rot_end.mean():.0f}° (6 ziaren)",
                    color=INK)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "results", "stage2.png"), dpi=110)

    for k, v in checks.items():
        print(("OK   " if v else "BŁĄD ") + k)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
