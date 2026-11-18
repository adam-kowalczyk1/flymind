"""flymind/leg_circuit.py — obwód czuciowo-ruchowy jednej nogi i strony z MaleCNS v1.0 (tylko dane). Bez bio2.

Definicje jak w audycie D1 (raport D1–D3, sekcja 3; zweryfikowane przez dwa niezależne przeliczenia):
  receptory  superclass czuciowy z entryNerve = nerw nogi, strona = rootSide
  MN         vnc_motor z exitNerve = nerw nogi, strona = somaSide (rootSide jest pusty dla wszystkich MN)
  IN         vnc_intrinsic z ≥ t synapsami OD receptorów tej nogi i strony ORAZ ≥ t synapsami DO jej MN (t = 5)
To [DATA]: kto z kim i ile synaps. Znak połączeń nadaje dopiero snn_interface.build (sign_map) — to założenie modelu,
a dla glutaminianu niepewne (raport D1, sekcja 7), więc zostawiamy je jawnym parametrem wywołującego.
"""
import pandas as pd
import pyarrow.dataset as ds

from connectome import ConnectomeError, load_edges
from snn_interface import DEFAULT_SIGN, NT_COLS, ModelParams, assign_nt, build
from visual_path import ANN, NTS, WEIGHTS

NERVES = {"T1": "ProLN", "T2": "MesoLN", "T3": "MetaLN"}
SENSORY = ("vnc_sensory", "vnc_sensory_tbc", "sensory_ascending", "sensory_ascending_tbc", "sensory_descending")


def select(leg="T2", side="L", t=5):
    """Zwraca (bodies, groups, raport). groups: sensory (wg subclass), IN, MN (wg type)."""
    if leg not in NERVES or side not in ("L", "R"):
        raise ConnectomeError(f"noga {leg!r} / strona {side!r}")
    nerve = NERVES[leg]
    a = pd.read_feather(ANN, columns=["bodyId", "type", "superclass", "subclass", "rootSide", "somaSide",
                                      "entryNerve", "exitNerve"])
    sens = a[a.superclass.isin(SENSORY) & (a.entryNerve == nerve) & (a.rootSide == side)]
    mn = a[(a.superclass == "vnc_motor") & (a.exitNerve == nerve) & (a.somaSide == side)]
    intrinsic = set(a.bodyId[a.superclass == "vnc_intrinsic"].astype(int))
    W = ds.dataset(WEIGHTS, format="ipc")
    out = W.to_table(filter=ds.field("body_pre").isin(sens.bodyId.astype(int).tolist())).to_pandas()
    inn = W.to_table(filter=ds.field("body_post").isin(mn.bodyId.astype(int).tolist())).to_pandas()
    s_in = out.groupby("body_post").weight.sum()
    m_out = inn.groupby("body_pre").weight.sum()
    ins = sorted((set(s_in[s_in >= t].index) & set(m_out[m_out >= t].index) & intrinsic))
    groups = dict(
        sensory={k: sorted(v.bodyId.astype(int)) for k, v in sens.groupby(sens.subclass.fillna("NA"))},
        IN=[int(b) for b in ins],
        MN={k: sorted(v.bodyId.astype(int)) for k, v in mn.groupby(mn.type.fillna("NA"))})
    bodies = sorted(sens.bodyId.astype(int)) + groups["IN"] + sorted(mn.bodyId.astype(int))
    rep = dict(leg=leg, side=side, nerve=nerve, t=t, sizes=dict(sensory=len(sens), IN=len(ins), MN=len(mn)))
    return bodies, groups, rep


def network(J0, leg="T2", side="L", t=5, sign_map=None, transform="linear"):
    """SNNSpec obwodu + indeksy grup. sign_map=None → domyślne znaki snn_interface (w tym założenie o Glu).
    Ciała bez przekaźnika w danych i przekaźniki spoza sign_map dostają znak 0 (nie modelowane), z liczbą w raporcie."""
    bodies, groups, rep = select(leg, side, t)
    edges, erep = load_edges(WEIGHTS, bodies=bodies)
    nts = pd.read_feather(NTS)
    t_nt = nts.set_index("body").reindex(bodies)[list(NT_COLS)]
    none = [b for b, r in t_nt.iterrows() if not any(isinstance(x, str) and x != "unclear" for x in r)]
    overrides = {b: ("unknown", "brak przekaźnika we wszystkich źródłach MaleCNS; znak 0") for b in none}
    signs = dict(DEFAULT_SIGN if sign_map is None else sign_map)
    found = set(assign_nt(bodies, nts, overrides).nt)
    signs.update({nt: 0.0 for nt in found - set(signs)})
    spec = build(edges, bodies, nts, ModelParams(J0=J0, transform=transform, sign_map=signs), nt_overrides=overrides)
    rep["unsigned"] = dict(no_nt=len(none), zero_sign_nts=sorted(found - set(DEFAULT_SIGN if sign_map is None else sign_map)))
    pos = {b: i for i, b in enumerate(bodies)}
    idx = dict(sensory={k: [pos[b] for b in v] for k, v in groups["sensory"].items()},
               IN=[pos[b] for b in groups["IN"]], MN={k: [pos[b] for b in v] for k, v in groups["MN"].items()})
    rep.update(edges=erep["loaded"], build=spec.report)
    return spec, idx, rep
