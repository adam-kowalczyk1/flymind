"""F1 figures and replay video from RECORDED data only (results/<stage>/ + results/analysis_<stage>.json).
The replay re-renders and re-simulates one recorded trial deterministically and refuses to draw unless the re-simulated g streams and
DNa02 counts equal the stored ones. Writes only under figures/ (mode "x").
Run: .venv/bin/python -I -B flymind/experiments/f1_active_sensing/figures.py {pilot|confirm}
"""
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.animation import FFMpegWriter, FuncAnimation  # noqa: E402

if __name__ == "__main__" and not sys.flags.dont_write_bytecode:
    sys.exit("run with python -B")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analysis as AN  # noqa: E402
import stimulus as ST  # noqa: E402
import systems as SY  # noqa: E402

PR = AN.PR
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
C = dict(stat="#8a8984", sin="#2a78d6", jshuf="#eb6834", jvel="#1baf7a", jrms="#eda100", mt="#6250d6")
NETC = dict(DATA="#2a78d6", B1="#eb6834", SWS="#1baf7a")
A_RAMP = ["#a9c9f0", "#6aa2e6", "#2a78d6", "#14498a"]        # one hue, light → dark for A 0.5 → 4°
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "lines.linewidth": 2})


def out_dir(stage):
    d = os.path.join(HERE, "figures", stage)
    os.makedirs(d, exist_ok=True)
    return d


def save(fig, stage, name):
    p = os.path.join(out_dir(stage), name)
    with open(p, "xb") as fh:
        fig.savefig(fh, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", p)


def hits_by_bin(X, system, cond, rng, x, lo, hi, nb=7):
    h = AN.unit_hits(X.D(system, cond, rng))
    b = np.minimum((nb * (x - lo) / (hi - lo)).astype(int), nb - 1)
    centers = lo + (np.arange(nb) + 0.5) * (hi - lo) / nb
    m = np.array([h[b == i].mean() if (b == i).any() else np.nan for i in range(nb)])
    n = np.array([(b == i).sum() for i in range(nb)])
    se = np.sqrt(np.clip(m * (1 - m), 0, None) / np.maximum(n, 1))
    return centers, m, se


def fig_frequency_response(stage, res):
    g = res["grid_DATA"] if "grid_DATA" in res else None
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    for i, A in enumerate(PR["sin_A_deg"]):
        fs = PR["sin_f_hz"]
        if g:
            est = [g[f"sin_f{f:g}_A{A:g}"]["est"] for f in fs]
            lo = [g[f"sin_f{f:g}_A{A:g}"]["ci95"][0] for f in fs]
            hi = [g[f"sin_f{f:g}_A{A:g}"]["ci95"][1] for f in fs]
            ax.fill_between(fs, lo, hi, color=A_RAMP[i], alpha=0.18, lw=0)
        else:
            est = [res["pilot_grid_delta"][f"sin_f{f:g}_A{A:g}"]["DATA"] for f in fs]
        ax.plot(fs, est, "-o", color=A_RAMP[i], ms=5, label=f"A {A:g}°")
    ax.axhline(0, color=INK2, lw=1)
    ax.axhspan(-PR["sesoi_bsc"], PR["sesoi_bsc"], color=GRID, alpha=0.6, lw=0, label="±SESOI")
    ax.set_xscale("log", base=2)
    ax.set_xticks(PR["sin_f_hz"], [f"{f:g}" for f in PR["sin_f_hz"]])
    ax.set_xlabel("oscillation frequency f [Hz]")
    ax.set_ylabel("ΔBSC (sinusoid − stationary), DATA")
    ax.set_title("Frequency response of the side-report benefit" + (" (95% CI)" if g else " — pilot, no CI"), loc="left", color=INK)
    ax.legend(frameon=False, ncol=3, fontsize=8)
    save(fig, stage, "frequency_response.png")


def fig_psychometric(stage, X, conds, nets, cp):
    (a, b), (ka, kb) = AN.ranges(stage if stage != "pilot" else "pilot")
    rho, kk = X.units.rho.to_numpy(), X.units.k.to_numpy()
    panels = [(n, "D") for n in nets] + [("P", "C"), ("TH_LP", "D")]
    fig, axs = plt.subplots(1, len(panels), figsize=(3.0 * len(panels), 3.0), sharey=True)
    for ax, (s, r) in zip(axs, panels):
        x, lo, hi = (rho, a, b) if r == "D" else (kk, ka, kb)
        for c in conds:
            try:
                cx, m, se = hits_by_bin(X, s, c, r, x, lo, hi)
            except (KeyError, ValueError):
                continue
            kind = c.split("_")[0]
            ax.errorbar(cx * (100 if r == "D" else 1), m, se, color=C[kind], marker="o", ms=4, lw=2, capsize=0,
                        ls="--" if kind == "mt" else "-", label=c)
        ax.set_title(f"{s} — range {r}", loc="left", color=INK)
        ax.set_xlabel("target distance ρ [cm]" if r == "D" else "target contrast k")
    axs[0].set_ylabel("side-correct hit rate (both sides)")
    axs[-1].legend(frameon=False, fontsize=7, loc="upper right")
    save(fig, stage, "detection_performance.png")


def fig_effects(stage, res):
    rows = [("H1 Δ DATA sin−stat", res["H1"])] + [(k + " " + lab, res["secondary"][k]) for k, lab in
                                                  (("S1", "sin−J_shuf"), ("S2", "sin−J_vel"), ("S3", "ΔDATA−ΔB1"), ("S4", "ΔDATA−ΔSWS"),
                                                   ("S5", "ΔP (range C)"), ("S6", "ΔDATA−ΔTH_LP"))] \
        + [("V " + k, v) for k, v in res["validity"].items()]
    rows = [(n, r) for n, r in rows if "est" in r]
    fig, ax = plt.subplots(figsize=(6.2, 0.38 * len(rows) + 0.8))
    for i, (n, r) in enumerate(rows[::-1]):
        ax.plot(r["ci95"], [i, i], color=INK2, lw=2)
        ax.plot(r["est"], i, "o", color=NETC["DATA"], ms=7)
        ax.text(1.02, i, r["cls"], transform=ax.get_yaxis_transform(), va="center", fontsize=7.5, color=INK2)
    ax.set_yticks(range(len(rows)), [n for n, _ in rows[::-1]])
    ax.axvline(0, color=INK2, lw=1)
    ax.axvspan(-PR["sesoi_bsc"], PR["sesoi_bsc"], color=GRID, alpha=0.7, lw=0)
    ax.set_xlabel("difference in BSC (point, 95% CI); grey band = ±SESOI 0.07")
    ax.set_title("Pre-registered tests (confirm data)", loc="left", color=INK)
    save(fig, stage, "effects_forest.png")


def fig_neural(stage, res, conds, nets):
    keys = [("lc_ipsi", "LC10a ipsi spikes / 2 s"), ("sync_lc_ipsi", "LC10a ipsi synchrony r"), ("n_mid", "intermediate spikes"),
            ("dn_ipsi", "DNa02 ipsi spikes"), ("sD", "signed D"), ("lat_decision_ms", "decision latency [ms]")]
    fig, axs = plt.subplots(2, 3, figsize=(10, 5.2))
    w = 0.8 / len(nets)
    for ax, (k, lab) in zip(axs.flat, keys):
        for j, n in enumerate(nets):
            for i, c in enumerate(conds):
                v = res["neural"].get(f"{n}|{c}", {}).get(k, {})
                if v and v.get("mean") is not None:
                    ax.bar(i + (j - (len(nets) - 1) / 2) * w, v["mean"], w * 0.9, color=NETC[n], label=n if i == 0 else None)
        ax.set_xticks(range(len(conds)), [c.split("_")[0] for c in conds], fontsize=7.5)
        ax.set_title(lab, loc="left", color=INK, fontsize=9)
    axs.flat[0].legend(frameon=False, fontsize=7)
    fig.suptitle("Neural measures by motion condition (mean over target trials; descriptive)", x=0.01, ha="left", color=INK)
    fig.tight_layout()
    save(fig, stage, "neural_measures.png")


# ---------------- replay ----------------
def replay(stage, X, cp, unit=None):
    """Re-simulate one recorded unit (left target, DATA) for stat and sin(f*, A*); verify against stored data; draw frames + MP4."""
    f, A = cp["f_star"], cp["A_star"]
    sin = f"sin_f{f:g}_A{A:g}"
    if unit is None:                                           # rule: lowest unit with stat wrong and sin correct (left target),
        S = X.snn[(X.snn.system == "DATA") & (X.snn.side == "L")]   # else the unit with rho closest to the DATA stat SK threshold
        st = S[S.cond == "stat"].set_index("unit").D
        sn = S[S.cond == sin].set_index("unit").D
        cand = sorted(u for u in st.index if st[u] <= 0 < sn.get(u, 0))
        if cand:
            unit = cand[0]
        else:
            (a, b), _ = AN.ranges(stage)
            thr = AN.sk_threshold(AN.bsc(X.D("DATA", "stat"), np.arange(len(X.u))), a, b)
            unit = int(X.units.index[np.argmin(np.abs(X.units.rho - thr))])
    row = X.units.loc[unit]
    sc = ST.Scene()
    N = SY.Networks([PR[stage if stage != "pilot" else "pilot"]["b1_instances"][0]], [PR[stage if stage != "pilot" else "pilot"]["sws_instances"][0]], unit)
    noise = SY.pixel_noise(unit, PR["pixel_noise_sigma"])
    z = X.streams[unit]
    tr = {}
    for cn, kind in (("stat", "stat"), (sin, "sin")):
        theta = z[f"{cn}|theta"]
        sc.set_target(az_deg=float(row.az), rho=float(row.rho), k=1.0, r=PR["range_D"]["ball_r_m"])
        imgs, rec = sc.frames(theta)
        g, _ = SY.encode(imgs, noise)
        if not np.array_equal(g.astype(np.float32), z[f"{cn}|DL|g"]):
            raise RuntimeError(f"replay g differs from the stored stream ({cn})")
        I = np.zeros((300, len(N.spec.bodies)))
        I[:, N.idx["in_L"]], I[:, N.idx["in_R"]] = SY.L.ENC.i_max * g[:, :1], SY.L.ENC.i_max * g[:, 1:]
        spk = SY.ALIF(N.spec, SY.L.P, unit).run(np.repeat(I, 10, 0), 3000)
        D = int(spk[1000:, N.idx["DNa02_L"]].sum() - spk[1000:, N.idx["DNa02_R"]].sum())
        stored = X.snn[(X.snn.unit == unit) & (X.snn.cond == cn) & (X.snn.system == "DATA") & (X.snn.side == "L")].D.iloc[0]
        if D != stored:
            raise RuntimeError(f"replay D {D} ≠ stored {stored} ({cn})")
        noisy = np.clip(imgs.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        tr[cn] = dict(theta=theta, imgs=noisy, g=g, spk=spk, D=D, bearing=rec["bearing"])
    sc.close()
    res_bsc = {c: AN.bsc(X.D("DATA", c), np.arange(len(X.u))) for c in tr}
    _draw_replay(stage, unit, row, tr, sin, res_bsc, N)
    return unit


def _draw_replay(stage, unit, row, tr, sin, res_bsc, N):
    names = list(tr)
    t_ms = np.arange(3000)
    fig = plt.figure(figsize=(11, 7.2))
    gs = fig.add_gridspec(5, 2, height_ratios=[2.2, 0.9, 1.4, 1.0, 1.0], hspace=0.55, wspace=0.18)
    art = []
    f_, a_ = sin.replace("sin_f", "").split("_A")
    lab = {"stat": "stationary camera", sin: f"sinusoidal rotation f {f_} Hz, A {a_}°"}
    for j, cn in enumerate(names):
        d = tr[cn]
        axi = fig.add_subplot(gs[0, j])
        im = axi.imshow(d["imgs"][0], interpolation="nearest")
        axi.set_axis_off()
        axi.set_title(f"{lab[cn]} — input + pixel noise", loc="left", fontsize=8.5, color=INK)
        axt = fig.add_subplot(gs[1, j])
        axt.plot(np.arange(300) / 100, np.degrees(d["theta"]), color=C["sin"] if cn != "stat" else C["stat"])
        axt.plot(np.arange(300) / 100, np.degrees(d["bearing"]), color=INK2, lw=1, ls=":")
        axt.set_ylabel("θ / bearing [°]", fontsize=7.5)
        axt.set_xlim(0, 3)
        cur_t = axt.axvline(0, color=INK, lw=1)
        axr = fig.add_subplot(gs[2, j])
        sp = d["spk"]
        lc = np.r_[N.idx["in_L"], N.idx["in_R"]]
        yy, xx = np.nonzero(sp[:, lc].T)
        axr.scatter(xx / 1000, yy, s=0.6, color=NETC["DATA"], lw=0)
        mi = N.idx["mid"]
        y2, x2 = np.nonzero(sp[:, mi].T)
        axr.scatter(x2 / 1000, y2 + len(lc) + 5, s=0.6, color=C["jshuf"], lw=0)
        axr.axhline(len(N.idx["in_L"]) - 0.5, color=GRID, lw=0.8)
        axr.set_xlim(0, 3)
        axr.set_ylim(0, len(lc) + len(mi) + 5)
        axr.set_yticks([len(N.idx["in_L"]) / 2, len(N.idx["in_L"]) + len(N.idx["in_R"]) / 2, len(lc) + 5 + len(mi) / 2],
                       ["LC10a L", "LC10a R", "intermed."], fontsize=7)
        cur_r = axr.axvline(0, color=INK, lw=1)
        axd = fig.add_subplot(gs[3, j])
        cl = np.cumsum(sp[:, N.idx["DNa02_L"][0]])
        cr = np.cumsum(sp[:, N.idx["DNa02_R"][0]])
        lL, = axd.plot([], [], color=NETC["DATA"], label="DNa02 L")
        lR, = axd.plot([], [], color=C["jshuf"], label="DNa02 R")
        axd.set_xlim(0, 3)
        axd.set_ylim(0, max(cl[-1], cr[-1], 1) * 1.1)
        axd.set_ylabel("cum. spikes", fontsize=7.5)
        axd.axvspan(1, 3, color=GRID, alpha=0.5, lw=0)
        axd.legend(frameon=False, fontsize=7, loc="upper left")
        axs_ = fig.add_subplot(gs[4, j])
        axs_.set_axis_off()
        txt = axs_.text(0, 0.5, "", fontsize=9, color=INK, va="center", family="monospace")
        art.append((d, im, cur_t, cur_r, lL, lR, cl, cr, txt, cn))
    fig.suptitle(f"F1 Stage 0 replay — network DATA, unit {unit}, LEFT target at az {row.az:.1f}°, ρ {row.rho * 100:.1f} cm "
                 f"(recorded trial, deterministic re-simulation verified)", x=0.01, ha="left", fontsize=10, color=INK)

    def upd(k):
        ms = min(2999, k * 10 + 9)
        for d, im, cur_t, cur_r, lL, lR, cl, cr, txt, cn in art:
            im.set_data(d["imgs"][k])
            cur_t.set_xdata([k / 100])
            cur_r.set_xdata([k / 100])
            lL.set_data(t_ms[:ms] / 1000, cl[:ms])
            lR.set_data(t_ms[:ms] / 1000, cr[:ms])
            w = max(0, ms - 1000)
            dl = int(cl[ms] - cl[999]) if ms >= 1000 else 0
            dr = int(cr[ms] - cr[999]) if ms >= 1000 else 0
            dec = "LEFT" if dl > dr else "RIGHT" if dr > dl else "none"
            txt.set_text(f"t {k / 100:4.2f} s   window D = {dl - dr:+d} → report: {dec if w else '(window starts 1 s)'}\n"
                         f"BSC of DATA in this condition (all units): {res_bsc[cn]:.3f}")
        return []
    upd(0)
    for k in (0, 150, 299):
        upd(k)
        p = os.path.join(out_dir(stage), f"replay_frame_{k:03d}.png")
        with open(p, "xb") as fh:
            fig.savefig(fh, dpi=110)
        print("wrote", p)
    p = os.path.join(out_dir(stage), "replay_stationary_vs_sinusoid.mp4")
    if os.path.exists(p):
        raise FileExistsError(p)
    FuncAnimation(fig, upd, frames=300, blit=False).save(p, writer=FFMpegWriter(fps=30, bitrate=2400), dpi=100)
    plt.close(fig)
    print("wrote", p)


def main():
    stage = sys.argv[1]
    if stage == "pilot":
        r1 = json.load(open(os.path.join(HERE, "pilot_r1.json")))
        fig_frequency_response(stage, r1)
        return
    cp = json.load(open(os.path.join(HERE, "confirm_params.json")))
    res = json.load(open(os.path.join(HERE, "results", f"analysis_{stage}.json")))
    X = AN.Data(stage, th=cp["theta_TH_mV"], th_lp=cp["theta_TH_LP_mV"])
    f, A = cp["f_star"], cp["A_star"]
    conds = ["stat", f"sin_f{f:g}_A{A:g}", f"jshuf_A{A:g}", f"jvel_f{f:g}_A{A:g}", f"jrms_A{A:g}", f"mt_f{f:g}_A{A:g}"]
    fig_frequency_response(stage, res)
    fig_psychometric(stage, X, conds, ("DATA", "B1", "SWS"), cp)
    fig_effects(stage, res)
    fig_neural(stage, res, conds, ("DATA", "B1", "SWS"))
    print("replay unit", replay(stage, X, cp))


if __name__ == "__main__":
    main()
