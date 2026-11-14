"""F1 Stage 1 figures + replay video from RECORDED data only (results/<stage>/, results/analysis_<stage>.json).
The replay re-simulates one recorded unit (rule fixed in advance: lowest unit whose DATA none trial in W fails and DATA sin succeeds)
and refuses to draw unless e(t) and ω(t) equal the stored traces. Writes only under figures/<stage>/ (mode x).
Run: .venv/bin/python -I -B flymind/experiments/f1_active_sensing/stage1/figures1.py {pilot|confirm}"""
import json
import math
import os
import sys
import zlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.animation import FFMpegWriter, FuncAnimation  # noqa: E402

if not sys.flags.dont_write_bytecode:
    sys.exit("run with python -B")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analysis1 as A  # noqa: E402
import cl_sense as CS  # noqa: E402
import runner1 as R  # noqa: E402

INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
MC = dict(none="#8a8984", sin="#2a78d6", jvel="#1baf7a", gated="#eda100", virtual="#6250d6", mt="#eb6834")
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "lines.linewidth": 2})


def out(stage, name):
    d = os.path.join(HERE, "figures", stage)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)


def save(fig, stage, name):
    p = out(stage, name)
    with open(p, "xb") as fh:
        fig.savefig(fh, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", p)


def fig_success(stage, units, by):
    rows = [("DATA", m) for m in ("none", "sin", "jvel", "gated", "virtual", "mt")] + \
           [(f, m) for f in ("B1", "SWS") for m in ("none", "sin")] + [("TH", m) for m in ("none", "sin", "jvel")] + \
           [("P", m) for m in ("none", "sin")]
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    for i, (f, m) in enumerate(rows):
        s = A.col(by, units, f, m, "W")
        p, n = np.nanmean(s), np.isfinite(s).sum()
        e = 1.96 * math.sqrt(p * (1 - p) / n)
        ax.barh(i, p, color=MC[m], height=0.7, edgecolor=SURF, linewidth=2)
        ax.errorbar(p, i, xerr=e, color=INK, lw=1, capsize=2)
        ax.text(min(p + e + 0.02, 0.93), i, f"{p:.2f}", va="center", fontsize=8, color=INK)
    ax.set_yticks(range(len(rows)), [f"{f} · {m}" for f, m in rows])
    ax.invert_yaxis()
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("acquisition success, weak-target range W (|e| < 5° over 5.5–6.0 s); bars ±1.96·binomial SE")
    ax.set_title(f"Closed-loop acquisition by controller and motion ({stage}, n = {len(units)} units; MODEL)", loc="left")
    save(fig, stage, "success_by_condition.png")


def fig_tests(stage, t):
    names = ["H1", "S1", "S2", "S3", "S4", "S7", "S8", "S9"]
    lab = dict(H1="H1 ΔDATA sin−none", S1="S1 sin − jvel", S2="S2 ΔDATA − ΔB1", S3="S3 ΔDATA − ΔSWS", S4="S4 ΔDATA − ΔTH_LP",
               S7="S7 gated − sin", S8="S8 virtual − sin", S9="S9 mt − sin")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw=dict(width_ratios=[1.4, 1]))
    a1.axvspan(-A.SESOI, A.SESOI, color=GRID, alpha=0.7, lw=0)
    a1.axvline(0, color=INK2, lw=1)
    for i, k in enumerate(names):
        v = t[k]
        if "est" not in v:
            a1.text(0, i, "not tested", ha="center", va="center", fontsize=8, color=INK2)
        else:
            a1.plot(v["ci95"], [i, i], color=INK2, lw=2)
            a1.plot(v["est"], i, "o", color=MC["sin"], ms=8, mec=SURF, mew=2)
        a1.text(1.02, i, v["cls"], transform=a1.get_yaxis_transform(), va="center", fontsize=8, color=INK2)
    a1.set_yticks(range(len(names)), [lab[k] for k in names])
    a1.invert_yaxis()
    a1.set_xlabel("difference in success (point, 95 % CI); grey band = ±SESOI 0.10")
    a1.set_title("Pre-registered tests", loc="left")
    harms = [("S5 success loss (S)", t["S5"]["success"]), ("S5 final |e| increase [°] (S)", t["S5"]["final_err_deg"]),
             ("S6 false turns (N)", t["S6"]), ("S10 pan f-component [°] (W)", t["S10"]["W"]), ("S10 pan f-component [°] (S)", t["S10"]["S"])]
    for i, (nm, v) in enumerate(harms):
        a2.plot(v["ci95"], [i, i], color=INK2, lw=2)
        a2.plot(v["est"], i, "o", color=MC["mt"] if v["cls"] == "HARMFUL" else MC["none"], ms=8, mec=SURF, mew=2)
        a2.plot([v["margin"]] * 2, [i - 0.35, i + 0.35], color=INK, lw=1, ls=":")
        a2.text(1.02, i, v["cls"], transform=a2.get_yaxis_transform(), va="center", fontsize=8, color=INK2)
    a2.axvline(0, color=INK2, lw=1)
    a2.set_yticks(range(len(harms)), [h[0] for h in harms])
    a2.invert_yaxis()
    a2.set_xlabel("harm (point, 95 % CI); dotted = margin")
    a2.set_title("Harm tests (no Holm)", loc="left")
    fig.tight_layout()
    save(fig, stage, "tests_forest.png")


def fig_rho(stage, units, by):
    rho = np.array([by[(u, "DATA", "none", "W")]["rho"] for u in units])
    edges = np.linspace(rho.min(), rho.max() + 1e-9, 8)
    c = (edges[:-1] + edges[1:]) / 2
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    for f, m, ls, col_ in (("DATA", "none", "-", MC["none"]), ("DATA", "sin", "-", MC["sin"]), ("B1", "sin", "--", MC["mt"]),
                           ("TH", "none", ":", "#c4c3bf"), ("TH", "sin", ":", MC["jvel"])):
        s = A.col(by, units, f, m, "W")
        y = [np.nanmean(s[(rho >= a) & (rho < b)]) for a, b in zip(edges[:-1], edges[1:])]
        ax.plot(c * 100, y, ls, color=col_, marker="o", ms=5, label=f"{f} · {m}")
    ax.set_xlabel("target distance ρ [cm]")
    ax.set_ylabel("acquisition success")
    ax.set_ylim(-0.03, 1.03)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Success vs distance, range W", loc="left")
    save(fig, stage, "success_vs_rho.png")


def pick_unit(units, by):
    c = [u for u in units if not by[(u, "DATA", "none", "W")]["success"] and by[(u, "DATA", "sin", "W")]["success"]]
    return c[0] if c else units[0]


def replay(stage, units, by):
    """Re-simulate DATA none and sin (W) of one unit with frame capture; verify against the stored traces; draw PNG + MP4."""
    u = pick_unit(units, by)
    P = json.load(open(R.PARAMS))
    C = json.load(open(R.CONF)) if stage == "confirm" else dict(ranges=P["ranges"], omega_on=P["omega_on"])
    st = CS.draw(u, C["ranges"])["W"]
    tr = dict(az0_deg=st["side"] * st["az"], rho=st["rho"])
    N = R.networks(stage)
    ps = "pilot" if stage == "pilot" else "confirm"
    slope = P["slopes"][f"{ps}|DATA|0"]
    noise = CS.pixel_noise(u)
    z = np.load(os.path.join(HERE, "results", stage, f"u{u}.npz"))
    frames = []

    class Rec(CS.SO101Sim):
        def observe(self):
            o = super().observe()
            frames.append(o.frame.image)
            return o
    orig, CS.SO101Sim = CS.SO101Sim, Rec
    runs = {}
    try:
        for m in ("none", "sin"):
            frames.clear()
            jit = CS.jvel(600, P["f_hz"], np.random.default_rng([u, 3, zlib.crc32(b"jvel")]))[0]
            r = CS.run("snn", (N.spec, N.idx), u, dict(slope_snn=slope, slope_p=P["slope_p"], slope_th=P["slope_th"]), tr,
                       motion=m, f=P["f_hz"], phase=st["phi"], noise=noise, ticks=600, slope=slope, jit=jit,
                       omega_on=C["omega_on"], g_b=CS.gain_for(tr))
            if not (np.array_equal(np.asarray(r["e_deg"], np.float32), z[f"DATA|{m}|W|e"])
                    and np.array_equal(np.asarray(r["omega"], np.float32), z[f"DATA|{m}|W|om"])):
                raise RuntimeError(f"replay differs from the stored trial (unit {u}, {m})")
            imgs = np.stack([np.clip(f.astype(np.int16) + noise[k], 0, 255).astype(np.uint8) for k, f in enumerate(frames)])
            runs[m] = dict(r=r, imgs=imgs, ok=bool(by[(u, "DATA", m, "W")]["success"]))
    finally:
        CS.SO101Sim = orig
    t = np.arange(600) * CS.DT
    fig = plt.figure(figsize=(11, 6.6))
    gs = fig.add_gridspec(3, 2, height_ratios=[2.0, 1.2, 1.0], hspace=0.5, wspace=0.18)
    art = []
    for j, m in enumerate(("none", "sin")):
        d = runs[m]
        ai = fig.add_subplot(gs[0, j])
        im = ai.imshow(d["imgs"][0], interpolation="nearest")
        ai.set_axis_off()
        ai.set_title("no sensing motion" if m == "none" else f"base sensing motion {P['f_hz']:g} Hz, ±4° bearing", loc="left", fontsize=8.5)
        ae = fig.add_subplot(gs[1, j])
        ae.axhspan(-5, 5, color=GRID, lw=0)
        ae.plot(t, d["r"]["e_deg"], color=MC[m], lw=1.5, label="bearing e (raw)")
        ae.plot(t, np.degrees(d["r"]["pan_t"]), color=INK, lw=1, label="motor pan (integrator)")
        ae.plot(t, np.degrees(d["r"]["theta_s"]), color=MC["gated"], lw=1, label="sensing offset θ_s")
        ae.axvspan(5.5, 6.0, color=MC["none"], alpha=0.15, lw=0)
        ae.set_xlim(0, 6)
        ae.set_ylabel("[°]", fontsize=8)
        ae.legend(frameon=False, fontsize=7, loc="upper right")
        cur = ae.axvline(0, color=INK, lw=1)
        ad = fig.add_subplot(gs[2, j])
        cnt = d["r"]["counts"]
        ad.plot(t, np.cumsum(cnt[:, 2]), color=MC["sin"], lw=1.5, label="DNa02 L")
        ad.plot(t, np.cumsum(cnt[:, 3]), color=MC["mt"], lw=1.5, label="DNa02 R")
        ad.set_xlim(0, 6)
        ad.set_xlabel("time [s]")
        ad.set_ylabel("cum. spikes", fontsize=8)
        ad.legend(frameon=False, fontsize=7, loc="upper left")
        cur2 = ad.axvline(0, color=INK, lw=1)
        txt = ad.text(0.99, 0.08, "", transform=ad.transAxes, ha="right", fontsize=8, family="monospace")
        art.append((d, im, cur, cur2, txt, m))
    fig.suptitle(f"F1 Stage 1 replay ({stage}) — DATA, unit {u}, target az {tr['az0_deg']:+.1f}°, ρ {tr['rho'] * 100:.1f} cm\n"
                 "camera input + pixel noise; re-simulation verified against the recorded trial; MODEL in MuJoCo, not hardware",
                 x=0.01, ha="left", fontsize=9.5)

    def upd(k):
        for d, im, cur, cur2, txt, m in art:
            im.set_data(d["imgs"][k])
            cur.set_xdata([k * CS.DT])
            cur2.set_xdata([k * CS.DT])
            txt.set_text(f"t {k * CS.DT:4.2f} s  e {d['r']['e_deg'][k]:+6.2f}°" + (f"  → {'SUCCESS' if d['ok'] else 'miss'}"
                                                                                 if k >= 550 else ""))
        return []
    for k in (0, 300, 599):
        upd(k)
        p = out(stage, f"replay_frame_{k:03d}.png")
        with open(p, "xb") as fh:
            fig.savefig(fh, dpi=110)
        print("wrote", p)
    p = out(stage, "replay_none_vs_sin.mp4")
    if os.path.exists(p):
        raise FileExistsError(p)
    FuncAnimation(fig, upd, frames=range(0, 600, 2), blit=False).save(p, writer=FFMpegWriter(fps=50, bitrate=2400), dpi=100)
    plt.close(fig)
    print("wrote", p, "| replay unit", u)


def main():
    stage = sys.argv[1]
    units, bad, by = A.load(stage)
    res = json.load(open(os.path.join(HERE, "results", f"analysis_{stage}.json")))
    fig_success(stage, units, by)
    fig_tests(stage, res["tests"])
    fig_rho(stage, units, by)
    replay(stage, units, by)


if __name__ == "__main__":
    main()
