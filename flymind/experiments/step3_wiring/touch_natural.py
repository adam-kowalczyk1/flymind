"""Etap 1 (18 XI) — odruch przy ZWYKŁYM dotyku: czy sieć sama kończy dotyk dłoni? Próba = krok 6 r1 (brainleg.py: dotyk
naturalny, ramię samo dociska dłoń do walca do F_ON 3 N, potem 0,5 s steruje sieć). Bez sondy. Niczego nie zmienia w trial5,
BrainNet ani świecie — dokłada tylko ZAPIS siły dłoni po każdym kroku świata (podklasa ForceWorld) i opcjonalne wycięcie
DNg15 i/lub DNge078 (to samo zerowanie wyjść co brainleg_lesion.py).
Dodatkowe pola rekordu W: palm_end (średnia z ostatnich 50 ms), t_off (s od oddania do pierwszego taktu < P_OFF), off_frac
(ułamek taktów sieci z dłonią < P_OFF), recontact (ile razy dotyk wrócił po zniknięciu).
Uruchom: touch_natural.py [--lesion none|d15|d78|both] --net N|F|L --glu ±1 --seed S --poses P --tag T --out DIR
(ziarno testowe tylko z TOUCH1_FINAL_TEST=1)"""
import os
import sys

import numpy as np
import scipy.sparse as sp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brainleg as B  # noqa: E402
import brainleg_lesion  # noqa: E402,F401  (tylko TEST6C do kontroli ziaren)
import brainleg_probe as BP  # noqa: E402
import reflex as R  # noqa: E402
import reflex5 as R5  # noqa: E402

TEST_T1 = {21871}        # LOOP_TARGET_touch_r1.md (zapisane PRZED testem)
USED = {21831, 21861, 21891, 21631} | B.TEST6 | BP.TEST6B
P_OFF = 0.05             # N: dłoń „puszczona”
_FW = R.JN.ForceWorld
TRACE = []


class LogWorld(_FW):
    def step(self, q_t, tau):
        obs = super().step(q_t, tau)
        if self.phase == "net":
            TRACE.append(float(obs.touch[2]))
        return obs


def trial(item, seed, kind, net, fc, ac):
    TRACE.clear()
    r = R5.trial5(item, seed, kind, net, fc, ac)
    p = np.array(TRACE)
    if kind == "W" and r.get("valid") and len(p):
        off = p < P_OFF
        r.update(palm_end=round(float(p[-5:].mean()), 4), off_frac=round(float(off.mean()), 4),
                 t_off=round(float(np.argmax(off) + 1) * 0.01, 3) if off.any() else None,
                 recontact=int(((~off[1:]) & off[:-1]).sum()), n_net=int(len(p)))
    return r


def lesion_init(which):
    _init = B.BrainNet.__init__

    def init(self, glu, kind="N", shuffle_seed=None, rule="pre"):
        _init(self, glu, kind, shuffle_seed, rule)
        bm, d78, d15 = B.route_ids()
        pos = B.nets2.build_ext(glu, bm + d78 + d15)[4]
        cut = [pos[b] for b in (d15 if which in ("d15", "both") else []) + (d78 if which in ("d78", "both") else [])]
        mask = np.ones(self.N)
        mask[cut] = 0.0
        self.W = sp.csr_matrix(self.W.multiply(mask[None, :])) if sp.issparse(self.W) else self.W * mask[None, :]
        self.rep.update(lesion=which, lesion_idx=cut)
        self.reset()

    B.BrainNet.__init__ = init


if __name__ == "__main__":
    lesion = "none"
    if "--lesion" in sys.argv:
        i = sys.argv.index("--lesion")
        lesion = sys.argv[i + 1]
        del sys.argv[i:i + 2]
    assert lesion in ("none", "d15", "d78", "both")
    s = int(sys.argv[sys.argv.index("--seed") + 1])
    if s in USED:
        sys.exit("ziarna testów kroku 6 są zużyte")
    if s in TEST_T1 and not os.environ.get("TOUCH1_FINAL_TEST"):
        sys.exit("ziarno testowe etapu 1 tylko w teście końcowym (TOUCH1_FINAL_TEST=1)")
    if lesion != "none":
        lesion_init(lesion)
    R.F_ON = 3.0
    R.JN.ForceWorld = LogWorld
    R.TwoNet = B.BrainNet
    R.trial = trial
    R.main()
