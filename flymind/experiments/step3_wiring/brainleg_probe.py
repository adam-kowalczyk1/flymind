"""Krok 6 r2 — ten sam test co brainleg.py, ale bodziec dłoni ma stały czas: w próbie W, przez całe sterowanie siecią
(0,5 s), przedmiot jest dociskany do dłoni od dołu siłą = jego ciężar + F_PROBE (jak palec szturchający głowę).
Sonda jest klasycznym otoczeniem (bodziec), o ruchu decyduje sieć. Próby C bez zmian (sonda wyłączona).
Uruchom: brainleg_probe.py --net N|F|L --glu ±1 --seed S --poses P --tag T --out DIR (ziarno testowe tylko z STEP6B_FINAL_TEST=1)"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brainleg as B  # noqa: E402
import reflex as R  # noqa: E402
import reflex5 as R5  # noqa: E402

TEST6B = {21861}
F_PROBE = 3.0          # N: docisk sondy (= próg oddania F_ON)
_FW = R.JN.ForceWorld


class ProbeWorld(_FW):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.pressed = False

    def step(self, q_t, tau):
        self.pressed |= self.phase == "press"
        on = self.pressed and self.phase == "net"
        o = self.objs[0]
        self.sim.d.xfrc_applied[o["bid"], 2] = o["mass"] * 9.81 + F_PROBE if on else 0.0
        return super().step(q_t, tau)


def install():
    R.F_ON = 3.0
    R.JN.ForceWorld = ProbeWorld
    R.TwoNet = B.BrainNet
    R.trial = R5.trial5


if __name__ == "__main__":
    if "--seed" in sys.argv and int(sys.argv[sys.argv.index("--seed") + 1]) in TEST6B | B.TEST6 and not os.environ.get("STEP6B_FINAL_TEST"):
        sys.exit("ziarna testowe kroku 6 r2 tylko w teście końcowym (STEP6B_FINAL_TEST=1)")
    install()
    R.main()
