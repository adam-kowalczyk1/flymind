"""Etap 2 — samodzielny test sieci (bez fizyki), sztuczne bodźce:
 0–1 s   spoczynek (stan aktywny, brak celu)            → linia bazowa
 1–3 s   cel przesuwa się z +40° (lewo) do −40° (prawo)  → huśtawka DNa02 L/R
 3–4 s   cisza                                          → powrót do linii bazowej (brak eksplozji)
 4–5 s   stan PASYWNY, nacisk szczęk 0,5 N przez 200 ms → odruch oporu (prostownik ↑, szczęka nie zamyka)
 5–6 s   stan AKTYWNY, ten sam nacisk                   → wspomaganie (zginacz + zatrzask) = odwrócenie
 6–8 s   aktywny, chwyt zatrzaśnięty, siła szczęk 0→6 N → ujemne sprzężenie; derekrutacja szybki→wolny
 8–9 s   cisza (stan pasywny)
 osobno: rampa prądu na MN zginacza → kolejność rekrutacji (zasada wielkości Hennemana)
Zapisuje stage2_raster.png.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from circuit import FlyController

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def stimulus(t):
    theta, forces, active = None, (0.0, 0.0, 0.0), True
    if 1.0 <= t < 3.0:
        theta = np.radians(40 - 80 * (t - 1.0) / 2.0)
    if 4.0 <= t < 5.0:
        active = False
        if 4.3 <= t < 4.5:
            forces = (0.5, 0.5, 0)
    if 5.3 <= t < 5.5:
        forces = (0.5, 0.5, 0)
    if 6.0 <= t < 8.0:
        f = 6.0 * (t - 6.0) / 2.0
        forces = (f, f, 0.3)
    if t >= 8.0:
        active = False
    return theta, forces, active


def henneman(seed=0):
    """Rampa prądu 0→60 mV przez 2 s na wszystkie MN zginacza (bez szumu); najwcześniejszy
    1. spike w każdej klasie [ms]."""
    fc = FlyController(seed=seed, params=dict(noise=0.0))
    ids = fc.groups["MN_flex"]
    first = {}
    for k in range(2000):
        I = fc.inputs(None, (0, 0, 0), active=False)
        I[ids] += 60.0 * k / 2000
        s = fc.net.step(I)
        for i in ids[s[ids]]:
            first.setdefault(i, k)
    out = {}
    for i in ids:
        out[fc.mn_class[i]] = min(out.get(fc.mn_class[i], np.inf), first.get(i, np.inf))
    return out, fc


def main():
    os.makedirs(OUT, exist_ok=True)
    fc = FlyController(seed=0)
    T = 9.0
    steps = int(T * 100)
    spikes, yaw, torque, thetas = [], [], [], []
    for k in range(steps):
        t = k * 0.01
        th, f, act = stimulus(t)
        y, m, s = fc.control_step(th, f, act)
        spikes.append(s)
        yaw.append(y)
        torque.append(m)
        thetas.append(np.nan if th is None else np.degrees(th))
    S = np.concatenate(spikes)            # [ms, N]
    yaw, torque = np.array(yaw), np.array(torque)
    g = fc.groups
    tms = np.arange(len(S))

    def rate(ids, a, b):                  # średnia częstość grupy [Hz] w oknie [a, b) s
        return S[int(a * 1000):int(b * 1000)][:, ids].mean() * 1000

    # maksymalna częstość pojedynczego neuronu w oknach 50 ms
    win = S[: len(S) // 50 * 50].reshape(-1, 50, fc.N).sum(1) * 20.0
    max_rate = win.max()
    base = S[200:1000].mean() * 1000
    recov = S[3300:4000].mean() * 1000
    flex = np.concatenate([g["MN_flex"], g["MN_ltm"]])
    first, _ = henneman()
    # derekrutacja w rampie siły 6–8 s: ostatni spike każdej klasy zginacza
    last = {}
    for i in g["MN_flex"]:
        sp = np.where(S[6000:8000, i])[0]
        last[fc.mn_class[i]] = max(last.get(fc.mn_class[i], -1), sp.max() if len(sp) else -1)

    res = {
        "DNa02 L>R gdy cel po lewej (1.0–1.6 s)": rate(g["DNa02_L"], 1.0, 1.6) - rate(g["DNa02_R"], 1.0, 1.6),
        "DNa02 R>L gdy cel po prawej (2.4–3.0 s)": rate(g["DNa02_R"], 2.4, 3.0) - rate(g["DNa02_L"], 2.4, 3.0),
        "pasywny: prostownik po dotyku (4.3–4.6 s) − przed (4.0–4.3 s)": rate(g["MN_ext"], 4.3, 4.6) - rate(g["MN_ext"], 4.0, 4.3),
        "pasywny: zginacz+ltm po dotyku − przed": rate(flex, 4.3, 4.6) - rate(flex, 4.0, 4.3),
        "pasywny: średni moment szczęki po dotyku [N·m]": torque[430:460].mean(),
        "aktywny: średni moment szczęki po dotyku [N·m]": torque[530:580].mean(),
        "aktywny: zginacz po dotyku (5.3–5.8 s) − przed (5.0–5.3 s)": rate(flex, 5.3, 5.8) - rate(flex, 5.0, 5.3),
        "moment zginacza przy 0,5 N − przy 6 N": torque[605:620].mean() - torque[785:800].mean(),
    }
    n_model = sum(1 for n in fc.neurons if n["circuit"] == "model")
    print(f"Neuronów: {fc.N} (MaleCNS: {fc.N - n_model}, modelowych: {n_model}), "
          f"synaps w W: {int(fc.net.nsyn.sum())}, niezerowych wag: {(fc.net.W != 0).sum()}")
    print(f"Średnia częstość sieci: spoczynek {base:.2f} Hz, po bodźcu wzrokowym {recov:.2f} Hz; "
          f"max pojedynczego neuronu (okno 50 ms) {max_rate:.0f} Hz")
    for k, v in res.items():
        print(f"  {k}: {v:+.2f}")
    print("Henneman — rekrutacja, 1. spike przy rampie prądu [ms]:", first)
    print("Henneman — derekrutacja, ostatni spike w rampie siły [ms od 6 s]:", last)
    checks = {
        "brak eksplozji: max częstość < 300 Hz": max_rate < 300,
        "powrót do linii bazowej po bodźcu (< 2× + 1 Hz)": recov < 2 * base + 1,
        "huśtawka DNa02 zgodna ze stroną celu": res["DNa02 L>R gdy cel po lewej (1.0–1.6 s)"] > 5
        and res["DNa02 R>L gdy cel po prawej (2.4–3.0 s)"] > 5,
        # W stanie pasywnym zginacze są już przed dotykiem wyciszone (0 Hz), więc „hamowanie zginacza”
        # (kryterium z wersji 1) jest niemierzalne; kryterium funkcjonalne: prostownik rośnie, a
        # wypadkowy moment nie zamyka szczęki — w stanie aktywnym ten sam dotyk ją zamyka.
        "odwrócenie odruchu: pasywny → prostownik ↑ i moment ≤ 0": res["pasywny: prostownik po dotyku (4.3–4.6 s) − przed (4.0–4.3 s)"] > 0
        and res["pasywny: średni moment szczęki po dotyku [N·m]"] <= 0,
        "odwrócenie odruchu: aktywny → zginacz pobudzony, moment > 0": res["aktywny: zginacz po dotyku (5.3–5.8 s) − przed (5.0–5.3 s)"] > 5
        and res["aktywny: średni moment szczęki po dotyku [N·m]"] > 0,
        "ujemne sprzężenie siły: moment spada ze wzrostem siły": res["moment zginacza przy 0,5 N − przy 6 N"] > 0,
        "zasada wielkości (rekrutacja): wolne < pośrednie < szybkie": first["slow"] < first["int"] < first["fast"],
        "zasada wielkości (derekrutacja): szybkie gasną pierwsze": last["fast"] < last["int"] < last["slow"],
    }

    # --- wykres ---
    fig, ax = plt.subplots(5, 1, figsize=(13, 13), sharex=True,
                           gridspec_kw=dict(height_ratios=[2.2, 4, 1, 1, 1]))
    cmap = plt.get_cmap("tab20")
    panels = [["LC10a_L", "LC10a_R"],
              ["AOTU019_L", "AOTU019_R", "AOTU025_L", "AOTU025_R", "DNa02_L", "DNa02_R",
               "SENS_fixed", "SENS_moving", "SENS_palm", "IN_ACh", "IN_GABA", "IN_Glu",
               "RR_assist", "RR_resist", "MN_ext", "MN_flex", "MN_ltm"]]
    c = 0
    for a, keys in zip(ax[:2], panels):
        row, ticks = 0, []
        for key in keys:
            ids = g[key]
            if key.startswith("LC10a"):
                ids = ids[np.argsort(fc.pref[ids])]
            for i in ids:
                tt = tms[S[:, i]] / 1000
                a.scatter(tt, np.full(len(tt), row), s=1.5 if len(keys) > 2 else 0.6, color=cmap(c % 20), marker="|")
                row += 1
            ticks.append((row - len(ids) / 2, f"{key} ({len(ids)})"))
            a.axhline(row - 0.5, color="k", lw=0.2)
            c += 1
        a.set_yticks([t for t, _ in ticks], [l for _, l in ticks], fontsize=7)
        a.set_ylim(-0.5, row - 0.5)
        for x0, x1, lab in [(1, 3, "cel 40°→−40°"), (4.3, 4.5, "dotyk (pas.)"), (5.3, 5.5, "dotyk (akt.)"),
                            (6, 8, "siła 0→6 N")]:
            a.axvspan(x0, x1, color="y", alpha=0.12)
            if a is ax[0]:
                a.text(x0, row * 1.01, lab, fontsize=8)
    ax[0].set_title(f"Raster ConnectomeSNN (MaleCNS v1.0: {fc.N - n_model} neuronów + {n_model} modelowych), dt = 1 ms\n")
    ax = ax[1:]
    tc = np.arange(steps) * 0.01
    ax[1].plot(tc, thetas, "k")
    ax[1].set_ylabel("azymut celu [°]")
    ax[2].plot(tc, yaw, "C0")
    ax[2].set_ylabel("obrót bazy\n[rad/s]")
    ax[3].plot(tc, torque, "C3")
    ax[3].set_ylabel("moment szczęki\n(+ zamyka)")
    ax[3].set_xlabel("czas [s]")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "stage2_raster.png"), dpi=130)
    for k, v in checks.items():
        print(("OK   " if v else "BŁĄD ") + k)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
