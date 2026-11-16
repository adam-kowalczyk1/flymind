"""Krok 6 — eksploracja (bez testu): przebieg nacisku dłoni i częstości pul w czasie sterowania siecią, próby W.
Ziarna treningowe 21 421 xxx. Uruchom: explore_slick.py GLU OUT.json [KIND SHUFFLE_SEED] [frozen]  (frozen = sieć liczy, ale ramię nie dostaje ruchu)"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brainleg as B  # noqa: E402
import reflex as R  # noqa: E402
import reflex5 as R5  # noqa: E402

glu, out = float(sys.argv[1]), sys.argv[2]
kind = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] not in ("frozen", "probe") else "N"
ss = int(sys.argv[4]) if kind != "N" else None
frozen = sys.argv[-1] == "frozen"
if sys.argv[-1] == "probe":
    import brainleg_probe
    brainleg_probe.install()
assert not os.path.exists(out)
R.F_ON = 3.0
net = B.BrainNet(glu, kind, ss)
if frozen:
    _step = net.step
    net.step = lambda *a, **k: _step(*a, **k) * 0.0
LOG = []
_tick = R.JN.ArmGrip.tick


def tick(self, tgt, mode):
    _tick(self, tgt, mode)
    if self.active:
        LOG.append([float(self.obs.touch[2]), *net.r[2].tolist(), *net.r[3].tolist(), float(self.qc[2]), float(self.qc[3])])


R.JN.ArmGrip.tick = tick
fc = R.sm.FlyCfg(glu_sign=glu, trigger="search")
ac = R.JN.ArmCfg(version="reflex", joints=(1, 2, 3), roll=False, inputs=(), in_rule="fl")
res = []
for mi in range(len(R.oh.BASE_MATS)):
    for k in range(3):
        LOG.clear()
        r = R5.trial5(R.ITEMS["W"][mi], 21421 * 1000 + mi * 10 + k, "W", net, fc, ac)
        if r["valid"]:
            L = np.array(LOG)
            res.append(dict(item=r["item"], k=k, dq2=r["dq2"], dq3=r["dq3_lev"], palm=L[:, 0].round(2).tolist(),
                            elbow=(L[:, 2] - L[:, 1]).round(1).tolist(), wrist=(L[:, 3] - L[:, 4]).round(1).tolist()))
            res[-1].update(contact_ticks=int(np.argmax(L[:, 0] < 0.05)) if (L[:, 0] < 0.05).any() else len(L))
            t1 = int(np.argmax(L[:, 0] < 0.05)) if (L[:, 0] < 0.05).any() else len(L)
            print(r["item"], k, "dq2", r["dq2"], "dq3", r["dq3_lev"], "kontakt do", t1, "taktów z", len(L), flush=True)
json.dump(res, open(out, "x"))
