"""„Głowa” dla sieci nogi (eksploracja „życia”, 18 XI): neurony zstępujące (DN) z ≥5 syn. do sieci „pre” + neurony mózgu
(cb_intrinsic, visual_projection, ascending, descending, cb_sensory) z ≥50 syn. do tych DN. Progi wybrane z pamięci RAM
(macierz gęsta n×n: 15 tys. → ~2 GB), nie ze skutku. Lista zapisana w head_ids.json (raz liczona)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brainleg as B  # noqa: E402

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "head_ids.json")
T_DN, T_UP = 5, 50
UP_SC = ("cb_intrinsic", "visual_projection", "ascending_neuron", "descending_neuron", "cb_sensory")


def head_ids():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))["ids"]
    import nets
    import pandas as pd
    import pyarrow.dataset as ds
    VP = nets.visual_path
    a = pd.read_feather(VP.ANN, columns=["bodyId", "superclass"])
    sc = a.set_index("bodyId").superclass.astype(str)
    net = set(nets.bodies_for("pre")[0])
    W = ds.dataset(VP.WEIGHTS, format="ipc")
    inn = W.to_table(filter=ds.field("body_post").isin(sorted(net))).to_pandas()
    dn = inn[inn.body_pre.map(sc) == "descending_neuron"].groupby("body_pre").weight.sum()
    D = sorted(int(x) for x in dn[dn >= T_DN].index)
    up = W.to_table(filter=ds.field("body_post").isin(D)).to_pandas()
    up = up[up.body_pre.map(sc).isin(UP_SC)].groupby("body_pre").weight.sum()
    ids = list(dict.fromkeys(D + sorted(int(x) for x in up[up >= T_UP].index)))
    ids = [b for b in ids if b not in net]
    json.dump(dict(T_DN=T_DN, T_UP=T_UP, n_DN=len(D), ids=ids), open(CACHE, "w"))
    return ids


LOOM_TYPES = ("LPLC2", "LC4", "LPLC1", "LC6", "LC16")   # rzutowe neurony oka czułe na zbliżanie (literatura); pobudzane modelem oka


def eye_ids():
    import nets
    import pandas as pd
    a = pd.read_feather(nets.visual_path.ANN, columns=["bodyId", "type"])
    return sorted(int(b) for b in a.bodyId[a.type.isin(LOOM_TYPES)])


class HeadLife(B.BrainNet):
    """BrainNet (noga + BM + DNge078 + DNg15) + głowa; głowa w warstwie „I” (tasowanie L w obrębie warstw)."""
    def __init__(self, glu, kind="N", shuffle_seed=None, eyes=False):
        orig = B.route_ids
        bm, d78, d15 = orig()
        have = set(bm + d78 + d15)
        h = [b for b in head_ids() if b not in have]
        if eyes:                                                      # + wszystkie komórki typów zbliżania (oko pełne)
            hs = set(h) | have
            h += [b for b in eye_ids() if b not in hs]
        B.route_ids = lambda: (bm, d78, d15 + h)
        try:
            super().__init__(glu, kind, shuffle_seed)
        finally:
            B.route_ids = orig
        self.rep["n_head"] = len(h)
        import nets                                                   # kolejność neuronów jak w nets2.build_ext
        order = list(dict.fromkeys(nets.bodies_for("pre")[0] + bm + d78 + d15 + h))
        assert len(order) == self.N
        self.pos = {b: i for i, b in enumerate(order)}


if __name__ == "__main__":
    print(len(head_ids()))
