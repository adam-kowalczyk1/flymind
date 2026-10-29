"""flymind/v32_bump.py — V3.2: skupienie aktywności EPG w sieci ALIF (tylko dane) po bodźcu w jednym glomerulusie.
Bez bio2, bez mujoco. Protokół ustalony PRZED uruchomieniem (nie zmieniać po zobaczeniu wyników — nowa wersja):

  sieć      typy dokładnie: EPG, PEN_a(PEN1), PEN_b(PEN2), Delta7 (adnotacje MaleCNS v1.0); EPGt i PEG wykluczone;
            krawędzie wyłącznie z danych (minconf 0,5), transformacja liniowa, znak wg przekaźnika (snn_interface)
  neurony   ALIFParams(noise=2,0 mV), b_a = 0,5 wszędzie (domyślne flymind; bio2 zeruje adaptację w CX)
  J0        siatka (0,05; 0,1; 0,14; 0,2; 0,3) mV/synapsę — raportowane WSZYSTKIE; wnioski tylko z dopuszczalnych
  V2        J0 dopuszczalne ⇔ punkt stały ciszy (validate, szum 0) ∧ w żadnej próbie średnia po bodźcu (650–1000 ms)
            nie przewyższa średniej w bodźcu (brak eksplozji) ∧ max odsetek nasyconych neuronów (≥ 0,9 r_max) < 0,1
  bodziec   12 mV do EPG jednego glomerulusa, 0–300 ms; potem brak bodźca do 1000 ms; KAŻDY z 16 glomerulusów
  ziarna    1001–1005 (szum ALIF); permutacje kątów: ziarno 1101, 100 permutacji na pomiar
  okna      „on” 0–300 ms, „late_off” 650–1000 ms; częstość EPG = spike'i / długość okna
  kąty      cykl glomerulusów z epg_ring (dokładny, agregacja „pairs”), warianty A/B/R; punkt zero i kierunek umowne
  metryki   bump_metrics: C, dC = C − C_uniform, |błąd fazy| względem średniej kołowej kątów pobudzonych EPG,
            C_perm (mediana po permutacjach kątów); Σr = 0 → niezdefiniowane (liczone osobno)

Wersja 2 (2026-10-28) — EKSPLORACJA, zapisana przed uruchomieniem; nie potwierdza niczego (wynik dodatni wymagałby
osobnego protokołu potwierdzającego na ziarnach 2001+). Wszystko jak w wersji 1 poza:
  J0        siatka (0,10; 0,11; 0,12; 0,13; 0,14) — luka między ostatnim dopuszczalnym a pierwszym niedopuszczalnym J0 v1
  b_a       czynnik {0,5; 0,0} dla całej sieci (w tej sieci wszystkie neurony to CX): 0,0 = brak adaptacji jak w bio2,
            0,5 = odniesienie do v1 (J0 0,10 i 0,14 przy b_a 0,5 muszą odtworzyć C/dC/fazę z v1 co do bitu)
  dodatkowo epg_active_outside — odsetek aktywnych EPG POZA pobudzonym glomerulusem (rozlanie generowane przez sieć);
            wzgórze_trwałe (propozycja progu, ustalona teraz): okno late_off, C zdefiniowane ∧ dC > 0,2 ∧ |błąd fazy| < 45°;
            raportowany odsetek prób spełniających — dla każdego (J0, b_a, wariant)
Wersja 1 liczy te same dodatkowe kolumny (nie zmieniają C, dC ani fazy).

Uruchom:  .venv/bin/python -I -B flymind/v32_bump.py --protocol {1,2} [--out KATALOG]   (KATALOG: flymind/ albo $TMPDIR)
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

if __name__ == "__main__" and not sys.flags.dont_write_bytecode:
    sys.exit("uruchom z python -B (inaczej powstałby flymind/__pycache__)")      # przed importem modułów flymind
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from alif import ALIF, ALIFParams, rates, validate  # noqa: E402
from connectome import load_edges, map_populations, provenance  # noqa: E402
from epg_ring import (_rng, angles, best_cycle, bump_metrics, glom_matrix, glomerulus_labels,  # noqa: E402
                      neuron_matrix, symmetric)
from snn_interface import ModelParams, build  # noqa: E402

DATA = os.path.join(os.path.dirname(HERE), "data", "malecns")
ANN = os.path.join(DATA, "body-annotations-male-cns-v1.0-minconf-0.5.feather")
NTS = os.path.join(DATA, "body-neurotransmitters-male-cns-v1.0.feather")
WEIGHTS = os.path.join(DATA, "connectome-weights-male-cns-v1.0-minconf-0.5.feather")
TYPES = ("EPG", "PEN_a(PEN1)", "PEN_b(PEN2)", "Delta7")
PROTOCOLS = {1: dict(j0=(0.05, 0.1, 0.14, 0.2, 0.3), b_a=(0.5,), status="pierwotny"),
             2: dict(j0=(0.10, 0.11, 0.12, 0.13, 0.14), b_a=(0.5, 0.0), status="EKSPLORACJA")}
BUMP_DC, BUMP_PHASE = 0.2, np.radians(45)                               # próg „wzgórza trwałego” (v2, propozycja)
STIM_MV, ON_MS, TOTAL_MS, LATE = 12.0, 300, 1000, (650, 1000)
SEEDS, PERM_SEED, N_PERM, SAT_MAX = tuple(range(1001, 1006)), 1101, 100, 0.1
VARIANTS = ("A", "B", "R")


def network():
    ann = pd.read_feather(ANN, columns=["bodyId", "type", "instance"])
    pops, prep = map_populations(ann, {t: dict(type=t) for t in TYPES})
    ids = [int(b) for t in TYPES for b in pops[t]]
    edges, erep = load_edges(WEIGHTS, bodies=ids)
    labels, lrep = glomerulus_labels(ann)
    cyc, _ = best_cycle(symmetric(glom_matrix(neuron_matrix(edges, labels), labels, "pairs")[0]))
    G = sorted(labels.glomerulus.unique(), key=lambda g: (g[0], int(g[1:])))
    return ann, ids, edges, labels, cyc, G, dict(populations=prep["sizes"], edges=erep, labels=lrep,
                                                  cycle=[G[i] for i in cyc], weights=provenance(WEIGHTS))


def run(version, out=None):
    t0 = time.perf_counter()
    ann, ids, edges, labels, cyc, G, meta = network()
    nt = pd.read_feather(NTS)
    pos = {b: i for i, b in enumerate(ids)}
    epg = np.array([pos[int(b)] for b in labels.bodyId])                # kolejność jak labels
    th = {v: angles(labels, cyc, G, v) for v in VARIANTS}
    proto = PROTOCOLS[version]
    rng = _rng(PERM_SEED)
    rows, adm = [], {}
    for J0, b_a in [(j, b) for b in proto["b_a"] for j in proto["j0"]]:
        P = ALIFParams(noise=2.0, b_a=b_a)
        spec = build(edges, ids, nt, ModelParams(J0=J0))
        silent = validate(spec, P, SEEDS[0], I_on=0.0, on_ms=100, off_ms=100)["silent_fixed_point"]
        diag = []
        for g in G:
            stim = labels.glomerulus.to_numpy() == g
            I = np.zeros((TOTAL_MS, len(ids)))
            I[:ON_MS, epg[stim]] = STIM_MV
            for seed in SEEDS:
                s = ALIF(spec, P, seed).run(I, TOTAL_MS)
                r_on, r_late = rates(s[:ON_MS], P.dt), rates(s[LATE[0]:LATE[1]], P.dt)
                diag.append(dict(runaway=r_late.mean() > r_on.mean(), sat=float((r_on >= 0.9 * P.r_max).mean())))
                for v in VARIANTS:
                    z = np.exp(1j * th[v][stim]).mean()
                    for win, r in (("on", r_on[epg]), ("late_off", r_late[epg])):
                        m = bump_metrics(r, th[v], float(np.angle(z)), N_PERM, rng)
                        rows.append(dict(J0=J0, b_a=b_a, glomerulus=g, seed=seed, variant=v, window=win,
                                         epg_rate_hz=float(r.mean()), epg_active=float((r > 0).mean()),
                                         epg_active_outside=float((r[~stim] > 0).mean()), **m))
        d = pd.DataFrame(diag)
        adm[(J0, b_a)] = dict(silent_fixed_point=bool(silent), any_runaway=bool(d.runaway.any()),
                       max_saturated_frac=float(d.sat.max()),
                       admissible=bool(silent and not d.runaway.any() and d.sat.max() < SAT_MAX))
    df = pd.DataFrame(rows)
    res = summarize(df, adm)
    res.update(version=version, status=proto["status"], meta=dict(meta, protocol=__doc__, wall_seconds=time.perf_counter() - t0))
    if out:
        path = os.path.join(out, f"v32_bump_v{version}_{time.strftime('%Y%m%dT%H%M%S')}.json")
        with open(path, "x") as f:
            json.dump(res, f, ensure_ascii=False, indent=1, default=str)
        res["saved"] = path
    return res, df


def summarize(df, adm):
    out = dict(admissibility={f"J0={k[0]}|b_a={k[1]}": v for k, v in adm.items()}, table=[])
    for (J0, b_a, v, win), d in df.groupby(["J0", "b_a", "variant", "window"]):
        ok = d[d.C.notna()]
        bump = ok[(ok.dC > BUMP_DC) & (ok.phase_err < BUMP_PHASE)]
        q = lambda x: [round(float(a), 4) for a in np.percentile(x, [25, 50, 75])] if len(x) else None
        out["table"].append(dict(
            J0=J0, b_a=b_a, variant=v, window=win, admissible=adm[(J0, b_a)]["admissible"], n=len(d),
            n_undefined=int(d.C.isna().sum()), frac_bump=round(len(bump) / len(d), 3),
            epg_active_outside_median=round(float(d.epg_active_outside.median()), 3),
            C_uniform=round(float(d.C_uniform.iloc[0]), 4), dC_q25_50_75=q(ok.dC), C_perm_median=q(ok.C_perm)[1] if len(ok) else None,
            phase_err_deg_median=round(float(np.degrees(ok.phase_err.median())), 1) if len(ok) else None,
            frac_phase_within_half_wedge=round(float((np.degrees(ok.phase_err) < 360 / 32).mean()), 3) if len(ok) else None,
            epg_rate_hz_median=round(float(d.epg_rate_hz.median()), 1), epg_active_median=round(float(d.epg_active.median()), 3)))
    return out


def _allowed(out):
    roots = [os.path.realpath(HERE)] + ([os.path.realpath(os.environ["TMPDIR"])] if os.environ.get("TMPDIR") else [])
    p = os.path.realpath(out)
    return os.path.isdir(p) and any(p == r or p.startswith(r + os.sep) for r in roots)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--protocol", type=int, choices=sorted(PROTOCOLS), required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.out and not _allowed(a.out):
        sys.exit(f"--out {a.out}: musi istnieć i leżeć w flymind/ albo w $TMPDIR")
    res, _ = run(a.protocol, a.out)
    print(f"protokół v{res['version']} ({res['status']})")
    print(json.dumps(res["admissibility"], indent=1))
    print(pd.DataFrame(res["table"]).to_string(index=False))
    print("zapisano:", res.get("saved"), "| czas:", round(res["meta"]["wall_seconds"], 1), "s")
