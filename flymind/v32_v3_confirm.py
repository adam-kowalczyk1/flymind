"""flymind/v32_v3_confirm.py — V3.2 wersja 3: POTWIERDZENIE (jednorazowe) wyniku eksploracji Red Team.
Protokół zapisany 2026-10-28 PRZED uruchomieniem; hash pliku w results/v32/v3_protocol_sha256.txt. Bez bio2, bez mujoco.

Pochodzenie hipotezy: Red Team (results/redteam/v32_v2_redteam.md) — eksploracja 108 warunków na ziarnach 1001–1005;
zweryfikowane niezależnym kodem (ziarna 1001–1003): G_INH 16 / G_DD 0,3 / J0 0,2 / b_a 0 → 39/48 prób z trwałym łukiem.
Konfiguracja wybrana PO obejrzeniu wyników na ziarnach 1001–1005, więc potwierdzenie wyłącznie na nowych ziarnach.

Sieć: jak V3.2 (EPG 46, PEN_a 20, PEN_b 22, Delta7 42; tylko krawędzie z danych, liniowo, znak wg przekaźnika), PLUS
ZMIANY MODELU (nie dane, przeniesione z decyzji bio2): wagi Delta7 → EPG/PEN ×G_INH = 16, Delta7 → Delta7 ×G_DD = 0,3;
J0 = 0,2 mV/synapsę; ALIF noise 2 mV, b_a = 0 (bez adaptacji). Bodziec 12 mV do EPG jednego glomerulusa 0–300 ms,
każdy z 16 glomerulusów; całość 2500 ms. Kąty: wariant A (cykl z epg_ring, „pairs”).
Ziarna: 2001–2005 (potwierdzające, użyte tylko tutaj); tasowanie: ziarna 2101–2105 (jedno tasowanie na ziarno szumu).
Miara (jak v2): „wzgórze trwałe” w oknie W1 = 650–1000 ms i W2 = 2150–2500 ms: C zdefiniowane ∧ dC > 0,2 ∧
|błąd fazy względem średniej kątów pobudzonych EPG| < 45°. Wynik próby = trwałe w W1 ∧ W2.

Warunki:  data       — sieć powyżej
          shuffle    — te same wagi po visual_path.shuffle (zachowane stopnie i siła wyjściowa), potem te same mnożniki
                       wg typu presynaptycznego/postsynaptycznego (Delta7 → nie-Delta7 ×16, Delta7 → Delta7 ×0,3)
          b_a=0.5    — sieć data z adaptacją domyślną flymind (kontrola znanego czynnika)
Hipotezy (α = 0,05, Bonferroni na 2 testy → 0,025):
  H1: odsetek trwałych prób w data ≥ 0,5 (jednostronny dokładny test dwumianowy p0 = 0,5 nie jest wymagany —
      kryterium opisowe: punkt ≥ 0,5 ORAZ dolna granica 95 % CI Wilsona > 0,25).
  H2: data > shuffle: test Fishera jednostronny, p < 0,025 (n = 80 vs 80; uwaga: efektywne n ≈ liczba glomerulusów,
      bo zapłon jest deterministyczny na poziomie glomerulusa — raportowany też odsetek glomerulusów z ≥ 3/5 ziaren).
  H3 (opisowa): b_a = 0,5 → odsetek ≤ 0,1.
Interpretacja ustalona teraz: H1 ∧ H2 → „wzgórze zależne od okablowania z danych PRZY modelowym wzmocnieniu hamowania
Delta7 i bez adaptacji”; H1 ∧ ¬H2 → „trwałość wynika z globalnego hamowania, nie z topologii”; ¬H1 → wynik
eksploracji nie potwierdzony. Żaden wynik nie oznacza ciągłego atraktora (RT: stany skwantowane — raportowana liczba
różnych zbiorów aktywnych EPG).

Uruchom:  .venv/bin/python -I -B flymind/v32_v3_confirm.py --out flymind/results/v32
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

if __name__ == "__main__" and not sys.flags.dont_write_bytecode:
    sys.exit("uruchom z python -B")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v32_bump as V  # noqa: E402
from alif import ALIF, ALIFParams, rates  # noqa: E402
from epg_ring import bump_metrics  # noqa: E402
from snn_interface import ModelParams, build  # noqa: E402
from visual_path import shuffle  # noqa: E402

G_INH, G_DD, J0 = 16.0, 0.3, 0.2
SEEDS, SHUF = tuple(range(2001, 2006)), tuple(range(2101, 2106))
W1, W2, TOTAL = (650, 1000), (2150, 2500), 2500


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(c - h, 3), round(c + h, 3)]


def main(out):
    t0 = time.perf_counter()
    ann, ids, edges, labels, cyc, G, meta = V.network()
    nt = pd.read_feather(V.NTS)
    typ = ann.set_index("bodyId").type.reindex(ids).to_numpy()
    d7 = typ == "Delta7"
    pos = {b: i for i, b in enumerate(ids)}
    epg = np.array([pos[int(b)] for b in labels.bodyId])
    th = V.angles(labels, cyc, G, "A")
    base = build(edges, ids, nt, ModelParams(J0=J0))

    def scaled(spec):
        spec.W_data[np.ix_(~d7, d7)] *= G_INH
        spec.W_data[np.ix_(d7, d7)] *= G_DD
        return spec

    rows = []
    for cond in ("data", "shuffle", "b_a=0.5"):
        P = ALIFParams(noise=2.0, b_a=0.5 if cond == "b_a=0.5" else 0.0)
        for seed, sh in zip(SEEDS, SHUF):
            spec = scaled(shuffle(base, sh) if cond == "shuffle" else build(edges, ids, nt, ModelParams(J0=J0)))
            for g in G:
                stim = labels.glomerulus.to_numpy() == g
                I = np.zeros((TOTAL, len(ids)))
                I[:300, epg[stim]] = 12.0
                s = ALIF(spec, P, seed).run(I, TOTAL)
                ok, act = [], None
                for w in (W1, W2):
                    r = rates(s[w[0]:w[1]], P.dt)[epg]
                    m = bump_metrics(r, th, float(np.angle(np.exp(1j * th[stim]).mean())), 0, np.random.default_rng(seed))
                    ok.append(bool(m["C"] is not None and m["dC"] > 0.2 and m["phase_err"] < np.radians(45)))
                    act = tuple(np.flatnonzero(r > 0))
                rows.append(dict(cond=cond, seed=seed, glomerulus=g, persistent=ok[0] and ok[1], w1=ok[0], w2=ok[1],
                                 active_set=act, sat=float((rates(s[:300], P.dt) >= 0.9 * P.r_max).mean())))
    df = pd.DataFrame(rows)
    summ = {}
    for c, d in df.groupby("cond"):
        k, n = int(d.persistent.sum()), len(d)
        gl = d.groupby("glomerulus").persistent.sum()
        summ[c] = dict(k=k, n=n, frac=round(k / n, 3), wilson95=wilson(k, n), glomeruli_ge3of5=int((gl >= 3).sum()),
                       distinct_active_sets=int(d[d.persistent].active_set.nunique()), max_sat_on=round(d.sat.max(), 3))
    kd, ks = summ["data"]["k"], summ["shuffle"]["k"]
    p = fisher_exact([[kd, 80 - kd], [ks, 80 - ks]], alternative="greater")[1]
    H1 = summ["data"]["frac"] >= 0.5 and summ["data"]["wilson95"][0] > 0.25
    H2 = p < 0.025
    verdict = ("wzgórze zależne od okablowania (przy modelowym G_INH i b_a = 0)" if H1 and H2 else
               "trwałość z globalnego hamowania, nie z topologii" if H1 else "eksploracja NIE potwierdzona")
    res = dict(summary=summ, fisher_p_data_gt_shuffle=p, H1=H1, H2=H2, H3=summ["b_a=0.5"]["frac"] <= 0.1, verdict=verdict,
               protocol=__doc__, wall_s=time.perf_counter() - t0, meta=meta)
    path = os.path.join(out, f"v32_v3_confirm_{time.strftime('%Y%m%dT%H%M%S')}.json")
    with open(path, "x") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: v for k, v in res.items() if k not in ("protocol", "meta")}, indent=1, default=str))
    print("zapisano:", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--out", required=True)
    main(ap.parse_args().out)
