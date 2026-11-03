"""flymind/grip.py — KLASYCZNY sterownik szczęki SO-101 z odczytem dotyku. Bez bio2, bez mujoco.

To jest kontroler odniesienia (ramię D w protokole D3), NIE obwód muszki: progi i momenty są wyborem projektu,
źródło komend "classical:grip". Obwód dotyku z konektomu ma być z nim porównywany, nie w niego wbudowany.

Tryby: "open" (moment otwierający do q_open), "close" (moment zamykający do kontaktu OBU szczęk, potem "hold"),
"hold" (stały, mniejszy moment trzymania), "idle" (0 N·m). Moment: + = zamykanie, jak safety/so101.
touch[3] w kolejności so101.TOUCH = (cs_fixed, cs_moving, cs_palm), w N.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class GripCfg:
    tau_open: float = -0.5      # N·m
    tau_close: float = 0.5      # N·m
    tau_hold: float = 0.4       # N·m (safety.Limits.tau_max = 1,0)
    f_contact: float = 0.2      # N na każdej szczęce = kontakt
    q_open: float = 0.93        # rad (rozwarcie jak bio2)


class ClassicGrip:
    def __init__(self, cfg=GripCfg()):
        self.cfg, self.mode = cfg, "idle"

    def contact(self, touch):
        """Kontakt obu szczęk (pady stały i ruchomy) powyżej progu."""
        return touch[0] > self.cfg.f_contact and touch[1] > self.cfg.f_contact

    def step(self, q_jaw, touch):
        c = self.cfg
        if self.mode == "close" and self.contact(touch):
            self.mode = "hold"
        if self.mode == "open":
            return c.tau_open if q_jaw < c.q_open else 0.0
        return {"close": c.tau_close, "hold": c.tau_hold}.get(self.mode, 0.0)
