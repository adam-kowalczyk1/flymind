"""Testy śledzenia przedmiotu kamerą na chwytaku (etap „wzrok w pętli”). SYMULACJA. Uruchom z katalogu tymczasowego:
    .venv/bin/python -I -B flymind/results/vision_manipulation/tracking.py snn v1        (albo: classical, snn_swap)

Ramię stoi w pozie patrzenia; o obrocie bazy decyduje wyjście DNa02 sieci wspólnej (snn), regulator P na enkoderze (classical)
albo sieć z zamienionymi stronami wejścia (snn_swap — kontrola znaku). Zakłócenia zadaje stanowisko testowe SIŁĄ (xfrc_applied),
nigdy przez przestawienie przedmiotu. Błąd liczony z prawdy symulatora TYLKO do oceny:
    az = kąt między osią kamery a kierunkiem do środka przedmiotu, w płaszczyźnie poziomej obrazu [°].
Sukces (jak V5): |az| < 5° przez ostatnie 0,5 s.

Scenariusze (N scen na scenariusz, ziarna 102 000 + 100·scenariusz + i; szum 18 000 000 + ziarno):
  S0 none       brak przedmiotu w kadrze przez 3 s → dryf obrotu bez bodźca
  S1 static     przedmiot pojawia się w losowym miejscu strefy
  S2 offset     baza na starcie odkręcona o ±0,35 rad (śledzenie mimo własnego ruchu robota)
  S3 push       po 1,5 s pchnięcie boczne przedmiotu (0,15 s)
  S4 occlude    kamera zasłonięta 1,0–1,6 s (brak klatek); przedmiot stoi
  S5 occl_push  jak S4, a pchnięcie następuje w czasie zasłonięcia
  S6 rotate     po 1,5 s impuls momentu obraca przedmiot; pomiar z kamery (look) przed i po
  S7 loss       po 1,5 s silne pchnięcie wyrzuca przedmiot z kadru → czas wykrycia utraty i zachowanie obrotu
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import object_handling as oh  # noqa: E402
import sensory_manipulation as sm  # noqa: E402
import vision_manipulation as vm  # noqa: E402

SCEN = ("none", "static", "offset", "push", "occlude", "occl_push", "rotate", "loss")
ITEMS = (("cube_M", "mid"), ("long", "mid"), ("cyl", "mid"), ("flat", "mid"), ("cube_S", "light"))
N, T, DT = int(os.environ.get("TRACK_N", 20)), 400, 0.01


def az_err(w, c, bid):
    k = w.sim.fk(c.obs.q)
    v = w.sim.d.xipos[bid] - k["eye"]
    return math.degrees(math.atan2(-float(v @ k["eye_R"][:, 0]), float(v @ k["eye_forward"])))


def trial(cond, factory, drv, scen, i):
    seed = 102_000 + 100 * SCEN.index(scen) + i
    rng = np.random.default_rng(seed)
    item = ITEMS[i % len(ITEMS)]
    if drv is not None:
        drv.reset(vm.SEED_NOISE + seed)
    w = oh.World([item], seed, home=vm.Q_SURVEY)
    c = factory(w, vm.CFG)
    c.swap = cond == "snn_swap"
    o, d = w.objs[0], w.sim.d
    bid, sgn = o["bid"], float(rng.choice([-1, 1]))
    mass = float(w.sim.m.body_mass[bid])
    rec = dict(scen=scen, i=i, seed=seed, item="/".join(item), sign=sgn)
    try:
        if scen == "none":                                         # nie wpuszczaj przedmiotu: podajnik czeka na zwolnienie strefy
            w.pending = False
            w.next = len(w.objs)
        if scen == "offset":
            tgt = c.home[:5].copy()
            tgt[0] += sgn * 0.35
            for _ in range(60):
                c.tick(tgt, "open")
            c.pan_t = float(tgt[0])
        else:
            for _ in range(35):                                    # przedmiot pojawia się po ok. 0,3 s
                c.tick(c.home[:5], "open")
        p0 = d.xipos[bid].copy()
        e, om, npx, pan0 = [], [], [], c.pan_t
        for k in range(T):
            t = k * DT
            c.blank = scen in ("occlude", "occl_push") and 1.0 <= t < 1.6
            push = (scen in ("push", "loss") and 1.5 <= t < 1.65) or (scen == "occl_push" and 1.2 <= t < 1.35)
            d.xfrc_applied[bid] = 0
            if push:                                               # siła boczna: pokonuje tarcie i rozpędza (loss: 4× mocniej)
                d.xfrc_applied[bid, 1] = sgn * mass * (9.81 * 0.6 + (16.0 if scen == "loss" else 4.0))
            if scen == "rotate" and 1.5 <= t < 1.6:
                d.xfrc_applied[bid, 5] = sgn * mass * 0.004
            if scen == "rotate" and k in (140, 300):
                q, tr = c.look(), oh.obb(w._cloud_world(o))
                rec.setdefault("yaw_truth_deg", []).append(math.degrees(tr["yaw"]))
                rec.setdefault("yaw_err_deg", []).append(vm.perr(dict(cam=q, truth=tr))["yaw_deg"] if q else None)
                c.pan_t -= c.vc.peer                               # wróć z widoku bocznego (ten sam obrót co przed pomiarem)
            c.gaze()
            e.append(az_err(w, c, bid) if scen != "none" else 0.0)
            om.append(c.om)
            npx.append(c.n_px)
        e, npx = np.array(e), np.array(npx)
        t_ev = {"push": 1.65, "occlude": 1.6, "occl_push": 1.6, "rotate": 1.6, "loss": 1.65}.get(scen, 0.0)
        k0 = int(t_ev / DT)
        ins = np.abs(e[k0:]) < 5.0
        stay = [j for j in range(len(ins)) if ins[j:].all()]
        rec.update(e0=float(e[0]), e_at_event=float(e[k0]), final_abs_err=float(np.abs(e[-50:]).mean()), success=bool(ins[-50:].all()),
                   t_settle=(stay[0] * DT if stay else None), e_sd_last1s=float(e[-100:].std()), moved_mm=float(1e3 * np.hypot(*(d.xipos[bid] - p0)[:2])),
                   pan_drift=float(c.pan_t - pan0), omega_abs_mean=float(np.abs(om).mean()), n_px_min=int(npx.min()), n_px_last=int(npx[-1]),
                   e_ds=e[::5].round(2).tolist())
        if scen in ("occlude", "occl_push"):
            rec["pan_drift_blank"] = float(np.ptp(np.cumsum(np.array(om[100:160]) * DT)))
        if scen == "loss":
            lost = np.flatnonzero(npx[150:] < c.vc.n_min)
            rec.update(t_loss_detect=(float(lost[0] * DT) if len(lost) else None), omega_abs_after_loss=float(np.abs(om[-100:]).mean()))
    finally:
        c.eye.close()
    return rec


def main():
    cond, suf = sys.argv[1], sys.argv[2]
    out = os.path.join(sys.argv[3] if len(sys.argv) > 3 else HERE, f"tracking_{cond}_{suf}.json")
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    factory, drv, cal = vm.make("A_cam" if cond == "classical" else "E_vis_touch", sm.FlyCfg(trigger="search"))
    runs = []
    for scen in SCEN if cond != "snn_swap" else ("static",):
        for i in range(N):
            r = trial(cond, factory, drv, scen, i)
            runs.append(r)
        s = [r for r in runs if r["scen"] == scen]
        k = sum(r["success"] for r in s)
        ts = [r["t_settle"] for r in s if r["t_settle"] is not None]
        print(f"{cond:9s} {scen:10s} sukces {k}/{len(s)} CI {vm.wilson(k, len(s))} | końcowy |az| mediana {np.median([r['final_abs_err'] for r in s]):.2f}° "
              f"| ustalenie mediana {np.median(ts) if ts else float('nan'):.2f} s | przesunięcie {np.median([r['moved_mm'] for r in s]):.0f} mm "
              f"| dryf obrotu {np.median([abs(r['pan_drift']) for r in s]):.3f} rad", flush=True)
    with open(out, "x") as f:
        json.dump(dict(cond=cond, n=N, ticks=T, calibration=cal, code=vm.code_vision(), runs=runs), f, indent=1, default=float)
    print("zapisano", out)


if __name__ == "__main__":
    main()
