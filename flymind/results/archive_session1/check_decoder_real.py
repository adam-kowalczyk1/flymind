import json, sys, time
sys.path.insert(0, "/Users/admin/so101_fly_project/flymind")
import numpy as np, pandas as pd, pyarrow.dataset as ds
from connectome import load_edges
from snn_interface import build, ModelEdge, ModelParams
from alif import ALIF, ALIFParams
from decoder import SteerDecoder, SteerParams, GripDecoder, fit_steer, channel_provenance, size_classes, DecoderError
D = "/Users/admin/so101_fly_project/data/malecns/"
W = D + "connectome-weights-male-cns-v1.0-minconf-0.5.feather"
c = json.load(open("/Users/admin/so101_fly_project/bio2/circuit_bio2.json"))
nt = pd.read_feather(D + "body-neurotransmitters-male-cns-v1.0.feather")
P, SEEDS = ALIFParams(noise=2.0), range(1001, 1004)

# ---------- skręt: mózg bio2 (cx, dn, loom, hs) ----------
N = [n for n in c["neurons"] if n["module"] in ("cx", "dn", "loom", "hs")]
ids = [n["bodyId"] for n in N]
e, _ = load_edges(W, bodies=ids)
pick = lambda t, s: [n["bodyId"] for n in N if n["type"] == t and n["side"] == s]
me = [ModelEdge(p, pick("DNa01", so)[0], float(w), "bio2 brain.py:111 kopia PFL3→DNa02")
      for sp, so in (("L", "R"), ("R", "L")) for p in pick("PFL3", sp)
      for w in [e.weight[(e.body_pre == p) & (e.body_post == pick("DNa02", so)[0])].sum()] if w]
mp = ModelParams(J0=0.3)
specs = dict(full=build(e, ids, nt, mp, model_edges=me), data=build(e, ids, nt, mp, model_edges=me, include_model=False))
pos = {b: i for i, b in enumerate(ids)}
idx = {f"{t}_{s}": [pos[b] for b in pick(t, s)] for t in ("DNa02", "DNa01") for s in "LR"}
PL, PR = [pos[b] for b in pick("PFL3", "L")], [pos[b] for b in pick("PFL3", "R")]
print("PFL3 L/R:", len(PL), len(PR), {k: len(v) for k, v in idx.items()})
for k, sp in specs.items():
    print(f"pochodzenie wejścia ({k}):", {ch: round(channel_provenance(sp, idx[ch])["model_frac"], 3) for ch in idx})

def drive(x):                                    # PROXY kąta: asymetria napędu PFL3 (nie wzgórze CX, nie kąt celu)
    I = np.zeros(len(ids)); I[PL] = 8 + 4 * x; I[PR] = 8 - 4 * x; return I

def diffs(sp, x, seed, ms=1000):
    dec = SteerDecoder(idx, ("DNa02", "DNa01"), [0, 0], [1, 1], SteerParams())
    net, out = ALIF(sp, P, seed), []
    I = drive(x)
    for k in range(ms // 10):
        o = dec.step(net.run(I, 10), 1.0)
        if k >= 50: out.append(o["diff_hz"])     # ostatnie 500 ms
    return np.mean(out, 0)

XC, XT = np.array([-1, -0.5, 0, 0.5, 1.0]), np.array([-0.75, -0.25, 0.25, 0.75])
t0 = time.perf_counter()
for k, sp in specs.items():
    Y = np.array([[diffs(sp, x, s) for s in SEEDS] for x in XC])           # [x, seed, kanał]
    print(f"\n## {k}: L−P [Hz] (średnia ziaren) przy x =", XC.tolist())
    print("  DNa02:", Y[..., 0].mean(1).round(1).tolist(), " DNa01:", Y[..., 1].mean(1).round(1).tolist())
    X = np.repeat(XC, len(SEEDS)); Yf = Y.reshape(-1, 2)
    for chans in (("DNa02", "DNa01"), ("DNa02",)):
        ci = [("DNa02", "DNa01").index(ch) for ch in chans]
        try:
            off, sl = fit_steer(X, Yf[:, ci], min_slope=2.0)
        except DecoderError as err:
            print(f"  {'+'.join(chans):12s} kalibracja ODMOWA: {err}"); continue
        # test na nowych x i ziarnach 1004–1006: odczyt kąta w jednostkach x (gain 1, bez przycięcia)
        est = []
        for x in XT:
            for s in range(1004, 1007):
                d = diffs(sp, x, s)[ci]
                est.append(float(((d - off) / sl).mean()))
        err_ = np.array(est) - np.repeat(XT, 3)
        print(f"  {'+'.join(chans):12s} off={off.round(2).tolist()} slope={sl.round(2).tolist()} Hz/x; "
              f"test: błąd odczytu x  śr={err_.mean():+.3f}  RMS={np.sqrt((err_**2).mean()):.3f}")
print(f"[skręt: {time.perf_counter()-t0:.0f} s]")

# ---------- chwyt: obwód grip, tylko dane ----------
G = [n for n in c["neurons"] if n["module"] == "grip"]
gids = [n["bodyId"] for n in G]
ge, rep = load_edges(W, bodies=gids)
gpos = {b: i for i, b in enumerate(gids)}
mn = {k: [n["bodyId"] for n in G if n["type"] == t] for k, t in (("flex", "Ti flexor MN"), ("ext", "Ti extensor MN"), ("ltm", "ltm MN"))}
allmn = sum(mn.values(), [])
tot = ds.dataset(W, format="ipc").to_table(filter=ds.field("body_post").isin(allmn)).to_pandas().groupby("body_post").weight.sum()
over = {b: ("glutamate", "założenie: MN owadów glutaminergiczne (jak bio2, bez danych NT)")
        for b in gids if b in (800636, 815344)}
gs = build(ge, gids, nt, ModelParams(J0=0.3), nt_overrides=over)
cls = {k: size_classes([tot.get(b, 0) for b in mn[k]], {"flex": ["fast", "int", "int", "slow", "slow"], "ext": ["fast", "slow"],
       "ltm": ["int", "int", "slow", "slow"]}[k]) for k in mn}
print("\n## chwyt: wejście MN w całym connectomie [syn]:", {k: [int(tot.get(b, 0)) for b in mn[k]] for k in mn})
print("   wejście MN wewnątrz obwodu grip [syn]:", {k: [int(ge.weight[ge.body_post == b].sum()) for b in mn[k]] for k in mn})
sens = [gpos[n["bodyId"]] for n in G if n.get("subclass") in ("campaniform sensilla", "leg")]
print("   neuronów czuciowych (campaniform/leg):", len(sens), " bez krawędzi:", rep["bodies_without_edges"])
gd = GripDecoder([gpos[b] for b in mn["flex"] + mn["ltm"]], [gpos[b] for b in mn["ext"]], cls["flex"] + cls["ltm"], cls["ext"])
for amp in (0.0, 10.0, 20.0):
    I = np.zeros(len(gids)); I[sens] = amp
    tq, r = [], []
    for s in SEEDS:
        net = ALIF(gs, P, s); gd.reset(); o = None
        sp_all = []
        for _ in range(100):
            spk = net.run(I, 10); o = gd.step(spk, 1.0); sp_all.append(spk)
        tq.append(o["torque"]); r.append(np.concatenate(sp_all)[500:].mean(0) * 1000)
    r = np.mean(r, 0)
    print(f"   czucie {amp:4.1f} mV → moment {np.mean(tq):+.3f} N·m (ziarna {[round(t, 3) for t in tq]}); MN [Hz]:",
          {k: r[[gpos[b] for b in mn[k]]].round(0).tolist() for k in mn})
