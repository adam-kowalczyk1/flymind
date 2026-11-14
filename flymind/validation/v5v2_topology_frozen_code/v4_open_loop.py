"""flymind/v4_open_loop.py — V4: obraz → enkoder → LC10a → (dane) → DNa02 L/R → odczyt kąta, pętla OTWARTA.
Bez bio2, bez mujoco. PROTOKÓŁ v1 — EKSPLORACJA, zapisany 2026-10-28 PRZED pierwszym uruchomieniem; zmiana = nowa wersja.

Sieć: visual_path.network(J0) — LC10a (275) + pośrednie s_min = 5 (147) + DNa02 L/R; tylko dane; ALIF(noise = 2 mV,
b_a = 0,5 — domyślne flymind). Ziarna 1001–1006 (rozwojowe; nigdy 0–39 ani 300–399).

Część A — reżim dynamiki (bez obrazu, bez zachowania):
  J0 ∈ {0,05; 0,1; 0,2; 0,3; 0,5}; bodziec g = (gL, gR) ∈ {(1,0), (0,1), (0,5,0), (0,0,5), (0,0)}, prąd 12 mV·g do LC10a
  danej strony przez 300 ms, potem 500 ms bez bodźca; ziarna 1001–1003.
  Dopuszczalność (V2, wersja 2 kryterium — poprawka słabości z V3.2): punkt stały ciszy (szum 0) ∧ w każdej próbie
  średnia częstość sieci w oknie 500–700 ms (200–400 ms po bodźcu) ≤ 1 Hz (brak samopodtrzymania/eksplozji) ∧
  odsetek nasyconych neuronów (≥ 0,9 r_max) w bodźcu < 0,1.
  Reguła wyboru J0 (ustalona teraz, niezależna od ZNAKU odpowiedzi): najmniejsze dopuszczalne J0, przy którym
  max(DNa02_L, DNa02_R) przy g = (1,0) i (0,1) (średnia ziaren, okno bodźca) ≥ 20 Hz. Brak takiego J0 → STOP części B.
  Hipoteza (raportowana, nie używana do wyboru): g = (1,0) → DNa02_L > DNa02_R; g = (0,1) → odwrotnie.

Część B — enkoder + sieć (wybrane J0), bodźce syntetyczne sensory.spot_clip (96×128, fovy 70°, plamka r = 9 px,
  zielona (40, 180, 50) na szarym (120, 120, 120)), 500 ms na bodziec, odczyt: średnia L−P DNa02 [Hz] w 250–500 ms.
  Kalibracja: azymuty rozwojowe −30…30° co 10° × ziarna 1001–1003; liniowa diff = off + slope·az; znak ustalony
  z góry: slope > 0 (L−P > 0 ⇒ obrót w lewo); slope ≤ 2 Hz/rad lub ujemny → ODMOWA (kanał nie koduje lub koduje odwrotnie).
  Test: azymuty −25…25° co 10° (rozłączne) × ziarna 1004–1006: błąd kąta (mediana |e|, RMS) w stopniach.
  Warunki dodatkowe (azymut testowy, ziarna 1004–1006): brak bodźca (puste tło), plamka poza polem widzenia (az 50°),
  brak obrazu (None), oświetlenie ×0,5 i ×1,5 (fg i bg skalowane), słaby kontrast (fg (90, 140, 95)), szum pikseli
  σ = 10, czerwona plamka (200, 40, 40) — dystraktor innego koloru (przewidywanie: brak odpowiedzi).
  Ruch: plamka az(t) = 20°·sin(2π·0,5 Hz·t) przez 4 s → opóźnienie odczytu (max korelacji wzajemnej) i amplituda.
  Kontrole sieci (te same bodźce testowe, ten sam dekoder): tasowanie krawędzi (ziarna 1101–1103), zamiana stron
  wejścia (LC10a L dostaje napęd prawy), ablacja LC10a (prąd 0).

Wynik v1 (2026-10-28, J0 = 0,05): znak zgodny, kontrole zgodne, ale odpowiedź progowa (martwa strefa |az| < 10°),
offset z dopasowania liniowego daje +7° bez bodźca, szum σ = 10 niszczy detekcję. → wersja 2.

PROTOKÓŁ v2 — EKSPLORACJA, zapisany 2026-10-28 PO obejrzeniu v1 i PRZED uruchomieniem v2. Wszystko jak v1 poza:
  (1) reguła J0: najmniejsze dopuszczalne J0 (z danych części A v1 — część A nie jest powtarzana), przy którym
      max(DNa02_L, DNa02_R) przy g = (0,5; 0) i (0; 0,5) ≥ 20 Hz (zakres dynamiczny zamiast samego progu; nadal
      niezależna od znaku). Z tabeli części A v1 wynika J0 = 0,2 — wartość wynika z reguły, nie z wyboru ręcznego.
  (2) offset dekodera := średnia L−P przy pustym obrazie (ziarna kalibracyjne), slope = MNK przez ten punkt
      (brak celu ⇒ brak skrętu z definicji, a nie z dopasowania).
  (3) enkoder blur_px = 3 (uśrednianie 3×3 przed kontrastem — model sumowania sąsiednich receptorów).
Kryteria interpretacji ustalone teraz: v2 „lepsza” tylko jeśli jednocześnie mediana |e| testu < v1 (6,0°), brak bodźca
|est| < 2°, kontrole (zamiana stron: znak odwrotny; ablacja i tasowanie: |slope| testu < 25 % intaktnej).

Uruchom:  .venv/bin/python -I -B flymind/v4_open_loop.py --part {A,B} [--version 2] --out KATALOG   (KATALOG w flymind/ lub $TMPDIR)
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

if __name__ == "__main__" and not sys.flags.dont_write_bytecode:
    sys.exit("uruchom z python -B")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from alif import ALIF, ALIFParams, rates, validate  # noqa: E402
from decoder import DecoderError, fit_steer  # noqa: E402
from encoder import EncoderParams, TargetEncoder  # noqa: E402
from sensory import spot_clip  # noqa: E402
from visual_path import network, shuffle  # noqa: E402

P = ALIFParams(noise=2.0)
J0_GRID = (0.05, 0.1, 0.2, 0.3, 0.5)
SHAPE, FOVY, R_PX, FG, BG = (96, 128), 70.0, 9, (40, 180, 50), (120, 120, 120)
CAL_AZ, TEST_AZ = np.arange(-30, 31, 10), np.arange(-25, 26, 10)
CAL_SEEDS, TEST_SEEDS, SHUF_SEEDS = (1001, 1002, 1003), (1004, 1005, 1006), (1101, 1102, 1103)
MIN_SLOPE = 2.0
VERSION = {1: dict(blur=0, offset="fit"), 2: dict(blur=3, offset="blank")}
V = VERSION[1]


def part_a():
    out = dict(rows=[], adm={})
    for J0 in J0_GRID:
        spec, idx, rep = network(J0)
        N = len(spec.bodies)
        silent = validate(spec, P, 1001, I_on=0.0, on_ms=100, off_ms=100)["silent_fixed_point"]
        late, sat = [], []
        for g in ((1, 0), (0, 1), (0.5, 0), (0, 0.5), (0, 0)):
            I = np.zeros((800, N))
            I[:300, idx["in_L"]], I[:300, idx["in_R"]] = 12 * g[0], 12 * g[1]
            for seed in CAL_SEEDS:
                s = ALIF(spec, P, seed).run(I, 800)
                r_on = rates(s[:300], P.dt)
                late.append(rates(s[500:700], P.dt).mean())
                sat.append((r_on >= 0.9 * P.r_max).mean())
                out["rows"].append(dict(J0=J0, g=g, seed=seed, dnL=float(r_on[idx["DNa02_L"]].mean()),
                                        dnR=float(r_on[idx["DNa02_R"]].mean()), mid=float(r_on[idx["mid"]].mean()),
                                        lc=float(r_on[np.r_[idx["in_L"], idx["in_R"]]].mean()),
                                        late_hz=float(late[-1]), sat=float(sat[-1])))
        out["adm"][J0] = dict(silent=bool(silent), max_late_hz=float(max(late)), max_sat=float(max(sat)),
                              admissible=bool(silent and max(late) <= 1.0 and max(sat) < 0.1))
    out["network"] = rep
    choice = None
    for J0 in J0_GRID:
        r = [x for x in out["rows"] if x["J0"] == J0 and x["g"] in ((1, 0), (0, 1))]
        peak = max(np.mean([x["dnL"] for x in r if x["g"] == g] + [0]) for g in ((1, 0), (0, 1)))
        peak = max(peak, max(np.mean([x["dnR"] for x in r if x["g"] == g]) for g in ((1, 0), (0, 1))))
        out["adm"][J0]["dn_peak_hz"] = float(peak)
        if choice is None and out["adm"][J0]["admissible"] and peak >= 20:
            choice = J0
    out["J0_choice"] = choice
    return out


class OpenLoop:
    """Enkoder + sieć + odczyt L−P DNa02 (częstość z wygładzeniem τ 50 ms, jak decoder.SteerDecoder)."""

    def __init__(self, spec, idx, seed, swap=False, ablate=False):
        self.net, self.idx, self.enc = ALIF(spec, P, seed), idx, TargetEncoder(SHAPE, EncoderParams(blur_px=V["blur"]))
        self.inL, self.inR = (idx["in_R"], idx["in_L"]) if swap else (idx["in_L"], idx["in_R"])
        self.ablate, self.N = ablate, len(spec.bodies)
        self.r = np.zeros(2)

    def tick(self, image, ms=10):
        g = self.enc.encode(image)["g"] * (0 if self.ablate else 1)
        I = self.enc.currents(g, self.inL, self.inR, self.N)
        a = math.exp(-1 / 50.0)
        for s in self.net.run(I, ms):
            x = np.array([s[self.idx["DNa02_L"]].mean(), s[self.idx["DNa02_R"]].mean()]) * 1000
            self.r = a * self.r + (1 - a) * x
        return self.r[0] - self.r[1], g


def static_diff(spec, idx, seed, img, **kw):
    ol, out = OpenLoop(spec, idx, seed, **kw), []
    for k in range(50):
        d, _ = ol.tick(img)
        if k >= 25:
            out.append(d)
    return float(np.mean(out))


def spot(az_deg, fg=FG, bg=BG):
    return spot_clip(np.radians([az_deg]), [0.0], SHAPE, FOVY, R_PX, fg, bg).images[0]


def part_b(J0):
    spec, idx, rep = network(J0)
    t0 = time.perf_counter()
    X = np.repeat(np.radians(CAL_AZ), len(CAL_SEEDS))
    Y = np.array([static_diff(spec, idx, s, spot(a)) for a in CAL_AZ for s in CAL_SEEDS])
    res = dict(J0=J0, network=rep, calib=dict(az=CAL_AZ.tolist(), diff_mean=Y.reshape(len(CAL_AZ), -1).mean(1).round(2).tolist()))
    blank = np.full((*SHAPE, 3), BG, np.uint8)
    try:
        off, slope = fit_steer(X, Y, MIN_SLOPE)
        off, slope = float(off[0]), float(slope[0])
    except DecoderError as e:
        res["calib"]["refused"] = str(e)
        return res
    if V["offset"] == "blank":                 # v2: brak celu ⇒ brak skrętu; slope MNK przez (0, off)
        off = float(np.mean([static_diff(spec, idx, s, blank) for s in CAL_SEEDS]))
        slope = float(((Y - off) * X).sum() / (X * X).sum())
    res["calib"].update(offset=off, slope_hz_per_rad=slope, sign_ok=slope > 0)
    if slope <= 0:
        res["calib"]["refused"] = "slope ujemny — sieć koduje skręt przeciwnie do przewidywania"
        return res
    est = lambda d: math.degrees((d - off) / slope)

    def test(net_spec=spec, img_of=spot, az=TEST_AZ, **kw):
        e = [(a, est(static_diff(net_spec, idx, s, img_of(a), **kw))) for a in az for s in TEST_SEEDS]
        err = np.array([b - a for a, b in e])
        x = np.array([a for a, _ in e], float)
        y = np.array([b for _, b in e])
        return dict(slope_ratio=round(float(((y - y.mean()) * (x - x.mean())).sum() / ((x - x.mean()) ** 2).sum()), 3),
                    est_by_az={int(a): round(float(np.mean([b for x, b in e if x == a])), 2) for a in az},
                    median_abs_err=round(float(np.median(np.abs(err))), 2), rms=round(float(np.sqrt((err ** 2).mean())), 2))

    res["test"] = test()
    res["no_stimulus"] = [round(est(static_diff(spec, idx, s, blank)), 2) for s in TEST_SEEDS]
    res["no_stimulus_diff_hz"] = [round(static_diff(spec, idx, s, blank), 2) for s in TEST_SEEDS]
    res["out_of_view_50deg"] = [round(est(static_diff(spec, idx, s, spot(50))), 2) for s in TEST_SEEDS]
    res["no_image"] = [round(est(static_diff(spec, idx, s, None)), 2) for s in TEST_SEEDS]
    rng = np.random.default_rng(1201)
    noisy = lambda a: np.clip(spot(a).astype(float) + rng.normal(0, 10, (*SHAPE, 3)), 0, 255).astype(np.uint8)
    scaled = lambda k: (lambda a: spot(a, tuple(min(255, int(c * k)) for c in FG), tuple(min(255, int(c * k)) for c in BG)))
    res["light_x0.5"] = test(img_of=scaled(0.5))
    res["light_x1.5"] = test(img_of=scaled(1.5))
    res["low_contrast"] = test(img_of=lambda a: spot(a, (90, 140, 95)))
    res["pixel_noise_10"] = test(img_of=noisy)
    res["red_distractor"] = test(img_of=lambda a: spot(a, (200, 40, 40)))
    res["ctrl_swap_sides"] = test(swap=True)
    res["ctrl_ablate_LC10a"] = test(ablate=True)
    res["ctrl_shuffle"] = [test(net_spec=shuffle(spec, s)) for s in SHUF_SEEDS]
    # ruch: 4 s sinus 0,5 Hz, amplituda 20°
    t = np.arange(400) * 0.01
    az_t = 20 * np.sin(2 * np.pi * 0.5 * t)
    clip = spot_clip(np.radians(az_t), np.zeros_like(t), SHAPE, FOVY, R_PX, FG, BG)
    mv = []
    for s in TEST_SEEDS:
        ol = OpenLoop(spec, idx, s)
        e = np.array([est(ol.tick(im)[0]) for im in clip.images])
        a, b = az_t[100:], e[100:]
        lags = range(0, 40)
        cc = [np.corrcoef(a[: len(a) - L], b[L:])[0, 1] for L in lags]
        L = int(np.argmax(cc))
        mv.append(dict(lag_ms=10 * L, corr=round(float(cc[L]), 3), est_amp=round(float((b.max() - b.min()) / 2), 1)))
    res["moving_0.5Hz_20deg"] = mv
    res["wall_s"] = round(time.perf_counter() - t0, 1)
    return res


def _allowed(out):
    roots = [os.path.realpath(HERE)] + ([os.path.realpath(os.environ["TMPDIR"])] if os.environ.get("TMPDIR") else [])
    p = os.path.realpath(out)
    return os.path.isdir(p) and any(p == r or p.startswith(r + os.sep) for r in roots)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--part", choices=("A", "B"), required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--version", type=int, choices=sorted(VERSION), default=1)
    ap.add_argument("--j0", type=float, help="część B: J0 z wyniku części A (reguła wyboru), nie z ręki")
    a = ap.parse_args()
    if not _allowed(a.out):
        sys.exit(f"--out {a.out}: musi istnieć i leżeć w flymind/ albo w $TMPDIR")
    V.update(VERSION[a.version])
    res = part_a() if a.part == "A" else part_b(a.j0)
    res["version"] = a.version
    res["protocol"] = __doc__
    path = os.path.join(a.out, f"v4_part{a.part}_v{a.version}_{time.strftime('%Y%m%dT%H%M%S')}.json")
    with open(path, "x") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: v for k, v in res.items() if k not in ("rows", "protocol", "network")}, indent=1, default=str)[:6000])
    print("zapisano:", path)
