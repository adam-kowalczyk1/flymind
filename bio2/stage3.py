"""Etap 3 (bio2) — zamknięta pętla w MuJoCo.

A  Pamięć obiektu: piłeczka toczy się w poprzek, znika za przesłoną; ramię (kamera na chwytaku) śledzi ją
   i podczas zasłonięcia obraca się na podstawie wzgórza EPG. Miara (z prawdy fizycznej): różnica azymutów
   (z osi bazy) paszczy i piłeczki w chwili, gdy piłeczka wychodzi zza przesłony (odcinek kamera→piłeczka przestaje
   przecinać przesłonę). Widoczność z segmentacji obrazu zapisuję osobno. Warianty pamięci:
   pred / static / none (agent.py).
B1 Ucieczka: czarna kula (r 8 cm) leci na kamerę → LC4/LPLC2 → DNp01 → wyrzut ramienia. Miara: odległość
   kuli od kamery w chwili pierwszego spike'a DNp01 i w chwili, gdy chwytak odsunął się o 2 cm.
B2 Chwyt: piłeczka stacza się z równi do paszczy → śledzenie DNa02 → dotyk → chwyt (Henneman, bez zgniecenia)
   → uniesienie. Miary jak w sim/stage3.py (siły z kontaktów MuJoCo, nie z czujników sterownika).
"""
import mujoco
import numpy as np

import scene2
from agent import Agent
from vision import true_bearing

F_CRUSH = 5.0


def _seg(m):
    r, opt = scene2.eye_renderer(m)
    r.enable_segmentation_rendering()
    return r, opt


def _ball_visible(m, d, sr, opt):
    sr.update_scene(d, camera="eye", scene_option=opt)
    s = sr.render()
    return int(((s[..., 0] == m.geom("ball").id) & (s[..., 1] == mujoco.mjtObj.mjOBJ_GEOM)).sum())


def _behind_occluder(d):
    """Czy odcinek kamera→środek piłeczki przecina przesłonę (prostopadłościan osiowy; test płyt). Niezależne od
    pola widzenia kamery — „piłeczka schowana za przesłoną” w sensie geometrii sceny."""
    c, b = d.cam("eye").xpos, d.body("ball").xpos
    o, h = d.body("occluder").xpos, np.array(scene2.OCC_SIZE)
    v = b - c
    with np.errstate(divide="ignore", invalid="ignore"):
        t1, t2 = (o - h - c) / v, (o + h - c) / v
    lo, hi = np.nanmax(np.minimum(t1, t2)), np.nanmin(np.maximum(t1, t2))
    return bool(lo <= hi and hi >= 0 and lo <= 1)


def setup_A(seed):
    """Scena A dla danego seeda: (m, d, poza chwytu q)."""
    rng = np.random.default_rng(seed)
    m, d = scene2.load()
    y0, vy = rng.uniform(0.12, 0.16), -rng.uniform(0.09, 0.12)
    q, _ = scene2.reset_scene(m, d, ball_y0=y0, ball_vy=vy)
    scene2.set_mocap(m, d, "occluder", (scene2.OCC_X, rng.uniform(-0.08, -0.04), 0.05))
    mujoco.mj_forward(m, d)
    return m, d, q


def scenario_A(seed, memory="pred", calib=None, record=False, T=6.0):
    m, d, q = setup_A(seed)
    ag = Agent(m, d, seed=seed, memory=memory, q_catch=q, calib=calib)
    sr, opt = _seg(m)
    truth, px, behind = [], [], []
    for k in range(int(T * 100)):
        ag.step()
        for _ in range(10):
            mujoco.mj_step(m, d)
        b = d.body("ball").xpos
        truth.append(float(np.angle(np.exp(1j * (np.arctan2(b[1], b[0]) - ag._aim_az())))))   # błąd azymutu z osi bazy
        px.append(_ball_visible(m, d, sr, opt))
        behind.append(_behind_occluder(d))
    truth, px, behind = np.array(truth), np.array(px), np.array(behind)
    vis = px > 20
    # zasłonięcie = najdłuższy odcinek „za przesłoną” (geometria); wyłonienie = jego koniec, także gdy piłeczka
    # wyłania się poza polem widzenia kamery (wtedy ramię jej nie śledzi — porażka z dużym błędem, nie NaN)
    runs, start = [], None
    for i in range(len(behind)):
        if behind[i] and start is None:
            start = i
        if not behind[i] and start is not None:
            runs.append((start, i))
            start = None
    if runs:
        s0, s1 = max(runs, key=lambda r: r[1] - r[0])
        err = float(np.degrees(truth[s1]))
        bump = float(np.degrees(ag.log["bump"][s1]))
        out = dict(seed=seed, memory=memory, hidden_s=(s1 - s0) * 0.01, err_reappear=err, ok=abs(err) < 10.0,
                   err_ring=float(np.degrees(np.angle(np.exp(1j * (truth[s1] - ag.log["bump"][s1]))))), bump_reappear=bump,
                   err_hide=float(np.degrees(truth[s0])), escapes=ag.escape_t is not None)
    else:                      # piłeczka nie wyszła zza przesłony do końca próby — porażka
        s0 = s1 = None
        out = dict(seed=seed, memory=memory, hidden_s=np.nan, err_reappear=np.nan, ok=False, err_hide=np.nan,
                   escapes=ag.escape_t is not None)
    sr.close()
    ag.close()
    if record:
        out.update(log={k: np.array(v) for k, v in ag.log.items()}, truth=np.degrees(truth), vis=vis, behind=behind,
                   s0=s0, s1=s1)
    return out


def _A_task(a):
    return scenario_A(*a)


def run_A_test(seeds=range(10), example=0):
    """Test końcowy A (seedy 0–9, raz): 3 warianty pamięci, tabela → results/stage3_A.txt, wykres → stage3_A.png."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from multiprocessing import Pool
    mems = ("pred", "static", "none")
    with Pool(4) as p:
        res = p.map(_A_task, [(s, mem) for mem in mems for s in seeds])
    ex = scenario_A(example, "pred", record=True)
    lines = ["Etap 3 A — pamięć obiektu, test seedy %s (uruchomiony raz)" % list(seeds),
             "błąd = azymut piłeczki − azymut paszczy (z osi bazy) w chwili wyjścia zza przesłony; sukces |błąd| < 10°"]
    E = {}
    for mem in mems:
        rs = [r for r in res if r["memory"] == mem]
        e = np.array([r["err_reappear"] for r in rs])
        E[mem] = e
        lines.append(f"{mem:6s}: sukces {sum(r['ok'] for r in rs)}/{len(rs)}, |błąd| < 20°: {int((abs(e) < 20).sum())}/{len(rs)}, "
                     f"mediana |błąd| {np.nanmedian(abs(e)):.1f}°, śr. błąd {np.nanmean(e):+.1f}°, zasłonięcie "
                     f"{np.nanmean([r['hidden_s'] for r in rs]):.2f} s, ucieczki {sum(r['escapes'] for r in rs)}")
        lines.append("        błędy: " + str(np.round(e).tolist()))
        if mem == "pred":
            lines.append("        w tym pamięć pierścienia (prawda − wzgórze): " + str([round(r.get("err_ring", np.nan)) for r in rs])
                         + "; ramię za wzgórzem: " + str([round(r.get("bump_reappear", np.nan)) for r in rs]))
    txt = "\n".join(lines)
    print(txt)
    open("results/stage3_A.txt", "w").write(txt + "\n")

    L, t = ex["log"], np.array(ex["log"]["t"])
    fig, ax = plt.subplots(1, 3, figsize=(18, 5), gridspec_kw=dict(width_ratios=[2, 2, 1.2]))
    beh = ex["behind"]
    ax[0].fill_between(t, 0, 1, where=beh, color="0.85", transform=ax[0].get_xaxis_transform(), label="za przesłoną")
    ax[1].fill_between(t, 0, 1, where=beh, facecolor="none", edgecolor="w", hatch="//", lw=0,
                       transform=ax[1].get_xaxis_transform())
    ax[0].plot(t, ex["truth"], "k", lw=2, label="piłeczka (prawda)")
    ax[0].plot(t, np.degrees(L["bump"]), "C1", lw=1, label="wzgórze EPG")
    ax[0].plot(t, np.degrees(L["target"]), "C0.", ms=3, label="wykrycie (siatkówka)")
    ax[0].set(xlabel="t [s]", ylabel="kierunek względem paszczy [°]", ylim=(-90, 90),
              title=f"Przykład seed {example}, pred: błąd przy wyłonieniu {ex['err_reappear']:+.0f}°")
    ax[0].legend(fontsize=8)
    W = np.roll(np.array(L["wedges"]), 8, axis=1)          # klin q ma kąt 360°·q/16 → środek osi = 0°
    ax[1].imshow(W.T, aspect="auto", origin="lower", extent=(t[0], t[-1], -191.25, 168.75), cmap="magma", zorder=0)
    ax[1].plot(t, ex["truth"], "c", lw=1)
    ax[1].set(xlabel="t [s]", ylabel="klin EPG [°]", title="Aktywność 16 klinów EPG (cyjan: piłeczka)")
    for i, mem in enumerate(mems):
        ax[2].scatter(np.full(len(E[mem]), i) + np.random.default_rng(0).uniform(-.15, .15, len(E[mem])), E[mem], s=20)
    ax[2].axhspan(-10, 10, color="g", alpha=0.15)
    ax[2].set(xticks=range(3), xticklabels=mems, ylabel="błąd przy wyłonieniu [°]", title="10 prób na wariant")
    fig.tight_layout()
    fig.savefig("results/stage3_A.png", dpi=110)


if __name__ == "__main__" and len(__import__("sys").argv) > 1 and __import__("sys").argv[1] == "testA":
    run_A_test()
elif __name__ == "__main__":
    import sys
    r = scenario_A(int(sys.argv[1]) if len(sys.argv) > 1 else 0, sys.argv[2] if len(sys.argv) > 2 else "pred", record=True)
    L = r["log"]
    print({k: v for k, v in r.items() if k not in ("log", "truth", "vis")})
    for k in range(0, len(L["t"]), 15):
        print(f"t={L['t'][k]:.2f} widać={bool(r['vis'][k])} cel_wzrok={np.degrees(L['target'][k]):6.1f} prawda={r['truth'][k]:6.1f} "
              f"wzgórze={np.degrees(L['bump'][k]):6.1f} skup={L['skup'][k]:.2f} ω={L['omega'][k]:+.2f} loom={L['loom'][k]:.2f} "
              f"szczyt={L['strength'][k]:.2f} plamka={L['n_blob'][k]}")
