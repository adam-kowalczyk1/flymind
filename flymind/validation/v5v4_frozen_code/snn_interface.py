"""flymind/snn_interface.py — interfejs connectom → SNN z jawnym rozdziałem trzech warstw:

  dane       N_data[post, pre] = liczba synaps z load_edges (connectome.py); przekaźnik z body-neurotransmitters
             (kolejność: ground_truth → consensus_nt → celltype_predicted_nt; 'unclear' = brak; źródło per neuron).
  model      krawędzie dodane przez modelarza (ModelEdge z obowiązkowym uzasadnieniem) — osobna macierz N_model,
             nigdy nie nadpisuje krawędzi z danych; include_model=False daje sieć „tylko dane” (ablacja).
  parametry  przeliczenie liczby synaps na wagę: ModelParams (J0, transformacja, mapa znaków przekaźników).
             Liczba synaps NIE jest siłą fizjologiczną — J0 i transformacja to decyzje modelu, nie dane.

Wyjście (SNNSpec.W) ma format ConnectomeSNN z bio2/snn.py: W[post, pre] w mV, znak wg neuronu presynaptycznego.
Izolacja: nie importuje bio2 ani mujoco, niczego nie zapisuje.
"""
import hashlib
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from connectome import ConnectomeError

NT_COLS = ("ground_truth", "consensus_nt", "celltype_predicted_nt")
# Założenie modelu (nie dane): Glu hamuje w OUN owadów przez GluCl (Liu & Wilson 2013). Neuromodulatory
# (DA, 5HT, OA, HA) nie mają tu znaku — neuron z takim przekaźnikiem wymaga jawnej decyzji (sign_map).
DEFAULT_SIGN = {"acetylcholine": 1.0, "gaba": -1.0, "glutamate": -1.0}


@dataclass(frozen=True)
class ModelParams:
    J0: float = 1.0                   # mV na jednostkę po transformacji (model, np. Shiu 2024: 0,275 mV/synapsę)
    transform: str = "linear"         # "linear": J0·N; "log1p": J0·ln(1+N) (kompresja, wybór projektu bio2)
    sign_map: dict = field(default_factory=lambda: dict(DEFAULT_SIGN))


@dataclass(frozen=True)
class ModelEdge:
    pre: int
    post: int
    n_syn: float                      # „równoważna liczba synaps” — wartość modelowa, nie zmierzona
    reason: str


@dataclass
class SNNSpec:
    bodies: np.ndarray                # kolejność neuronów (indeks macierzy)
    nt: pd.DataFrame                  # bodyId, nt, nt_source
    sign: np.ndarray                  # znak per neuron presynaptyczny
    W_data: np.ndarray                # [post, pre] mV, tylko krawędzie z danych
    W_model: np.ndarray               # [post, pre] mV, tylko krawędzie modelowe
    report: dict

    @property
    def W(self):
        return self.W_data + self.W_model


def assign_nt(bodies, nt_df, overrides=None):
    """Przekaźnik per ciało. overrides: {bodyId: (nt, uzasadnienie)} — jedyna droga dla braków ('unclear')."""
    overrides = overrides or {}
    t = nt_df.set_index("body").reindex(bodies)
    rows = []
    for b in bodies:
        if b in overrides:
            nt, why = overrides[b]
            if not why:
                raise ConnectomeError(f"override przekaźnika {b} bez uzasadnienia")
            rows.append((b, nt, "override: " + why))
            continue
        r = t.loc[b]
        src = next((c for c in NT_COLS if isinstance(r[c], str) and r[c] != "unclear"), None)
        if src is None:
            raise ConnectomeError(f"brak przekaźnika dla {b} (wszystkie źródła puste/'unclear') — podaj override")
        rows.append((b, r[src], src))
    return pd.DataFrame(rows, columns=["bodyId", "nt", "nt_source"])


def build(edges, bodies, nt_df, params=ModelParams(), model_edges=(), include_model=True, nt_overrides=None):
    """Zbuduj SNNSpec. Krawędzie spoza `bodies` są pomijane i liczone w raporcie (nic nie znika po cichu)."""
    bodies = np.asarray(bodies, dtype=np.int64)
    if len(np.unique(bodies)) != len(bodies):
        raise ConnectomeError("powtórzone bodyId w liście neuronów")
    idx = {int(b): i for i, b in enumerate(bodies)}
    n = len(bodies)
    nt = assign_nt([int(b) for b in bodies], nt_df, nt_overrides)
    bad = sorted(set(nt.nt) - set(params.sign_map))
    if bad:
        raise ConnectomeError(f"przekaźniki bez znaku w sign_map: {bad}")
    sign = nt.nt.map(params.sign_map).to_numpy(float)

    inside = edges.body_pre.isin(idx) & edges.body_post.isin(idx)
    e = edges[inside]
    N_data = np.zeros((n, n))
    N_data[e.body_post.map(idx).to_numpy(), e.body_pre.map(idx).to_numpy()] = e.weight.to_numpy()

    N_model = np.zeros((n, n))
    for m in model_edges:
        if not m.reason:
            raise ConnectomeError(f"krawędź modelowa {m.pre}→{m.post} bez uzasadnienia")
        if m.pre not in idx or m.post not in idx:
            raise ConnectomeError(f"krawędź modelowa {m.pre}→{m.post}: neuron spoza sieci")
        if m.n_syn <= 0:
            raise ConnectomeError(f"krawędź modelowa {m.pre}→{m.post}: n_syn ≤ 0")
        i, j = idx[m.post], idx[m.pre]
        if N_data[i, j] or N_model[i, j]:
            raise ConnectomeError(f"krawędź modelowa {m.pre}→{m.post} nadpisałaby istniejącą krawędź")
        N_model[i, j] = m.n_syn

    f = {"linear": lambda x: x, "log1p": np.log1p}.get(params.transform)
    if f is None:
        raise ConnectomeError(f"nieznana transformacja {params.transform!r}")
    W_data = sign[None, :] * params.J0 * f(N_data)
    W_model = sign[None, :] * params.J0 * f(N_model) if include_model else np.zeros((n, n))
    W = W_data + W_model + 0.0        # + 0.0: −0.0 → 0.0, inaczej ta sama sieć miałaby różny hash
    report = dict(
        neurons=n, nt_sources=nt.nt_source.str.split(":").str[0].value_counts().to_dict(),
        data=dict(edges=int((N_data > 0).sum()), synapses=int(N_data.sum()), self_loops=int((np.diag(N_data) > 0).sum()),
                  dropped_outside=int((~inside).sum())),
        model=dict(edges=len(model_edges) if include_model else 0, offered=len(model_edges),
                   reasons=sorted({m.reason for m in model_edges})),
        params=dict(J0=params.J0, transform=params.transform, sign_map=params.sign_map),
        W_sha256=hashlib.sha256(np.ascontiguousarray(W).tobytes()).hexdigest())
    return SNNSpec(bodies, nt, sign, W_data, W_model, report)
