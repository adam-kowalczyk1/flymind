"""Powtórka próby 45 s + odczyt sześciu osi (plan: PLAN_ODCZYT_SZESCIU.md). one_run.py bez zmian. six_readout.py PULE.json DIR_OUT"""
import hashlib
import json
import os
import sys

import numpy as np

sys.dont_write_bytecode = True
import one_run as O  # noqa: E402

src, out = sys.argv[1:3]
assert hashlib.sha256(open(O.__file__, "rb").read()).hexdigest().startswith("ac2b7c39f12404455"), "one_run.py zmieniony"
os.makedirs(out)                                                        # istniejący katalog = błąd
P = json.load(open(src))
O.T.A_MV = O.S0.O.MV
cam, (net, feco) = O.Cam(), O.build()
inv = {i: b for b, i in net.pos.items()}
G = {f"{ax}|{k}": list(map(int, v)) for ax, d in P.items() for k, v in d.items()}
G["szczęka T2|zaciskanie (Ti extensor)"] = [int(inv[i]) for i in net.press]
G["szczęka T2|zwalnianie (Ti flexor + Acc)"] = [int(inv[i]) for i in net.release]
ids = [b for v in G.values() for b in v]
assert len(ids) == len(set(ids)) == 76, (len(ids), len(set(ids)))
now = {str(j): {s: [int(inv[i]) for i in ix] for s, ix in zip("+-", pn)} for j, pn in net.pools.items()}
n0 = len(net._grp)
for b in ids:                                                           # JEDYNA różnica: maski liczone do logu
    m = np.zeros(net.N, bool)
    m[net.pos[b]] = True
    net._grp[f"id{b}"] = m
json.dump(dict(grupy=G, obecne_pule=now, kolumny_cnt=["(dawne)"] * n0 + ids), open(os.path.join(out, "neurony.json"), "w"), indent=1, ensure_ascii=False)
np.savez_compressed(os.path.join(out, "pelny_odczyt.npz"), **O.trial(net, feco, cam))
print("zapisano", out)
