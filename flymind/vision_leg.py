"""flymind/vision_leg.py — sieć z danych: wzrok (LC9) → DNp09 → przekaźniki VNC → obwody czuciowo-ruchowe obu nóg.

Jedynym wejściem są zmysły: LC9 (obraz przez encoder.py, jak LC10a w loop.py), receptory nóg (dotyk, FeCO).
Neuronów ruchowych ani przedruchowych nie pobudza się sztucznie (decyzja właściciela projektu, 2026-11-03).

Skład [DATA] (progi jak visual_path i leg_circuit, ≥ t synaps na krawędź/połączenie):
  LC9 L/R (type == 'LC9', strona = somaSide); pośredniki ≥ t od LC9 i ≥ t do DNp09; DNp09 10783 (L), 11177 (R);
  przekaźniki: cele DNp09 (≥ t) wśród vnc_intrinsic oraz ich cele vnc_intrinsic (≥ t), które dochodzą (≥ t) do obwodów
  nóg (bez neuronów wstępujących/zstępujących — patrz VNC); obwody nóg z leg_circuit.
Znaki: snn_interface.build z sign_map (glutaminian jako jawny parametr); ciała bez NT i NT spoza mapy → znak 0.
"""
import pandas as pd
import pyarrow.dataset as ds

from connectome import load_edges
from leg_circuit import select
from snn_interface import DEFAULT_SIGN, NT_COLS, ModelParams, assign_nt, build
from visual_path import ANN, NTS, WEIGHTS

DNP09 = {"L": 10783, "R": 11177}
VNC = ("vnc_intrinsic",)   # błąd do 2026-11-03: wpisane też "descending"/"ascending", których w danych nie ma
                           # (prawdziwe nazwy: descending_neuron, ascending_neuron) — faktycznie liczono tylko vnc_intrinsic


def select_all(legs=(("T2", "L"), ("T2", "R")), t=5):
    a = pd.read_feather(ANN, columns=["bodyId", "type", "somaSide", "superclass"])
    W = ds.dataset(WEIGHTS, format="ipc")

    def q(col, ids):
        return W.to_table(filter=ds.field(col).isin([int(x) for x in ids])).to_pandas()

    lc = a[a.type == "LC9"]
    lc9 = {s: sorted(lc.bodyId[lc.somaSide == s].astype(int)) for s in ("L", "R")}
    dn = list(DNP09.values())
    o = q("body_pre", lc9["L"] + lc9["R"]).groupby("body_post").weight.sum()
    i = q("body_post", dn).groupby("body_pre").weight.sum()
    mid = sorted(set(o[o >= t].index) & set(i[i >= t].index) - set(lc9["L"] + lc9["R"]) - set(dn))
    legs_sel = {f"{leg}{side}": select(leg, side, t) for leg, side in legs}
    leg_bodies = set(b for v in legs_sel.values() for b in v[0])
    vnc = set(a.bodyId[a.superclass.isin(VNC)].astype(int))
    d1 = q("body_pre", dn).groupby("body_post").weight.sum()
    hop1 = set(d1[d1 >= t].index) & vnc
    e = q("body_pre", hop1)
    e = e[e.weight >= t]
    hop2 = set(e.body_post) & vnc - leg_bodies
    e2 = q("body_pre", hop2)
    e2 = e2[(e2.weight >= t) & e2.body_post.isin(leg_bodies)]
    relay = sorted((hop1 | set(e2.body_pre)) - leg_bodies - set(dn))
    bodies = list(dict.fromkeys(lc9["L"] + lc9["R"] + [int(x) for x in mid] + dn + [int(x) for x in relay]
                                + [b for v in legs_sel.values() for b in v[0]]))
    groups = dict(LC9=lc9, mid=[int(x) for x in mid], DNp09=DNP09, relay=[int(x) for x in relay],
                  legs={k: v[1] for k, v in legs_sel.items()})
    rep = dict(t=t, sizes=dict(LC9_L=len(lc9["L"]), LC9_R=len(lc9["R"]), mid=len(mid), relay=len(relay),
                               legs={k: v[2]["sizes"] for k, v in legs_sel.items()}, total=len(bodies)))
    return bodies, groups, rep


def network(J0, glu_sign=-1.0, legs=(("T2", "L"), ("T2", "R")), t=5):
    bodies, groups, rep = select_all(legs, t)
    edges, erep = load_edges(WEIGHTS, bodies=bodies)
    nts = pd.read_feather(NTS)
    tab = nts.set_index("body").reindex(bodies)[list(NT_COLS)]
    ov = {b: ("unknown", "brak przekaźnika we wszystkich źródłach MaleCNS; znak 0") for b, r in tab.iterrows()
          if not any(isinstance(x, str) and x != "unclear" for x in r)}
    signs = {**DEFAULT_SIGN, "glutamate": glu_sign}
    found = set(assign_nt(bodies, nts, ov).nt)
    signs.update({n: 0.0 for n in found - set(signs)})
    spec = build(edges, bodies, nts, ModelParams(J0=J0, sign_map=signs), nt_overrides=ov)
    pos = {b: k for k, b in enumerate(bodies)}
    ix = lambda v: [pos[b] for b in v]  # noqa: E731
    idx = dict(LC9={s: ix(v) for s, v in groups["LC9"].items()}, DNp09={s: pos[b] for s, b in DNP09.items()},
               legs={k: dict(sensory={c: ix(v) for c, v in g["sensory"].items()}, IN=ix(g["IN"]),
                             MN={m: ix(v) for m, v in g["MN"].items()}) for k, g in groups["legs"].items()})
    rep.update(edges=erep["loaded"], unsigned=dict(no_nt=len(ov), zero_sign_nts=sorted(found - set(DEFAULT_SIGN))))
    return spec, idx, rep
