"""pad_so101/control.py — logika: stan pada → cele 5 stawów [rad] + chwytak g (0 = zamknięty, 1 = otwarty).

Bez pygame i mujoco (testowalne). Ograniczenia (zakres, prędkość, wyprzedzenie, STOP) robi flymind/safety.py —
run.py po każdym takcie nadpisuje `ctrl.target` wyjściem warstwy bezpieczeństwa, więc całka nie „ucieka" za kraniec.
Mapa przycisków: PLAN.md.
"""
from dataclasses import dataclass, field

import numpy as np

ARM = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll")
# Poniższe wartości nadpisuje run.py z settings.json (strona ustawień); tu są wartości domyślne.
DEADZONE = 0.15
EXPO = 2.0                 # 1 = liniowo, 2 = kwadratowo (precyzja przy małym wychyleniu)
START_GEAR = 1             # indeks od 0
# nazwy przycisków na ekranie (run.py ustawia wg mapy z ustawień); klucz = nazwa logiczna używana w tym pliku
KEYS = {"BACK": "View", "START": "Menu", "RIGHTSTICK": "R3", "B": "B"}
GEARS = (("wolno", 0.35, 0.04), ("normalnie", 0.8, 0.10), ("szybko", 1.4, 0.20))   # nazwa, rad/s, m/s
GRIP_SPEED = 1.2           # pełny spust: 0→1 w ok. 0,8 s
GRIP_MIN = -0.1            # lekko „za zamknięciem" = mocniejszy ścisk przedmiotu
N_SLOTS = 4
# Znaki: kierunek pada → kierunek stawu. Sprawdzone w symulacji (test_control.py::test_sim_directions):
# +pan = chwytak w prawo, +lift = ramię w przód/dół, +elbow = chwytak w dół, +wrist_flex = nos w dół.
SIGN_PAN, SIGN_LIFT, SIGN_ELBOW, SIGN_PITCH_UP, SIGN_ROLL = +1, +1, -1, -1, +1


@dataclass(frozen=True)
class PadState:
    """Gałki −1…1 (y: + = do przodu/góry), spusty 0…1, przyciski = nazwy z pad.BUTTONS."""
    lx: float = 0.0
    ly: float = 0.0
    rx: float = 0.0
    ry: float = 0.0
    lt: float = 0.0
    rt: float = 0.0
    buttons: frozenset = frozenset()


def shape(x):
    """Martwa strefa + krzywa kwadratowa: mały wychył = precyzja, pełny = pełna prędkość."""
    a = (abs(x) - DEADZONE) / (1 - DEADZONE)
    return 0.0 if a <= 0 else float(np.sign(x) * min(a, 1.0) ** EXPO)


def dls(J, v, lam=0.02):
    """Tłumione najmniejsze kwadraty: prędkości stawów dla prędkości chwytaka v (stabilne przy wyprostowanym ramieniu)."""
    return J.T @ np.linalg.solve(J @ J.T + lam ** 2 * np.eye(len(v)), v)


@dataclass
class Controller:
    q: np.ndarray              # [5] rad, pozycja startowa (= „dom" dla Y)
    g: float                   # chwytak 0…1
    jac: object = None         # q5 → J[3,3]: (promień, wysokość, pochylenie nosa w górę) × (lift, elbow, wrist_flex); None = brak trybu KART
    slots: dict = field(default_factory=dict)   # {nr: (q5 list, g)}

    def __post_init__(self):
        self.target = np.array(self.q, float)
        self.home = (self.target.copy(), float(self.g))
        self.mode, self.gear, self.slot = "STAWY", START_GEAR, 1
        self.stopped = None    # powód STOP albo None
        self.rec = None        # lista (q5, g) w trakcie nagrywania
        self.last_rec = None   # ostatnia nagrana trasa
        self.play = None       # indeks odtwarzania
        self.goto = None       # (q5, g) cel płynnego dojazdu
        self.play_after_goto = False   # odtwarzanie startuje dopiero po dojechaniu do początku trasy (bez skoku)
        self.prev = frozenset()
        self.msg = "gotowe — ruszaj gałkami"
        self.events = []       # dla run.py: wibracje, zapis pozycji / trasy

    def _say(self, msg, event=None):
        self.msg = msg
        if event:
            self.events.append(event)

    def stop(self, why):
        if not self.stopped:
            self.stopped, self.goto, self.play, self.play_after_goto = why, None, None, False
            self._say(f"STOP ({why}) — {KEYS['START']} wznawia", "stop")

    def tick(self, pad, q_meas, dt):
        """Jeden takt. q_meas [5] = zmierzone stawy. Zwraca (target[5], g)."""
        q_meas = np.asarray(q_meas, float)
        b = pad.buttons
        pressed, self.prev = b - self.prev, b
        if "BACK" in pressed:
            self.stop("View")
        if self.stopped:
            if "START" in pressed:
                self.stopped, self.target = None, q_meas.copy()
                self._say("wznowiono", "tick")
            return self.target, self.g

        sticks = [shape(a) for a in (pad.lx, pad.ly, pad.rx, pad.ry)]
        pitch = ("RB" in b) - ("LB" in b)
        if (any(sticks) or pitch) and (self.goto or self.play is not None):
            self.goto = self.play = None
            self.play_after_goto = False
            self._say("przerwano ruchem gałki")
        self._buttons(pressed, q_meas)

        name, v_ang, v_lin = GEARS[self.gear]
        if self.play is not None:
            q5, self.g = self.last_rec[self.play]
            self.target = np.array(q5)
            self.play += 1
            if self.play >= len(self.last_rec):
                self.play = None
                self._say("koniec trasy", "tick")
        elif self.goto:
            q5, g = self.goto
            d = q5 - self.target
            step = v_ang * dt
            self.target = self.target + np.clip(d, -step, step)
            self.g += float(np.clip(g - self.g, -GRIP_SPEED * dt, GRIP_SPEED * dt))
            if np.abs(d).max() < 1e-3 and abs(g - self.g) < 1e-3:
                self.goto = None
                if self.play_after_goto:
                    self.play, self.play_after_goto = 0, False
                    self._say(f"odtwarzam trasę ({KEYS['START']} przerywa)")
                else:
                    self._say("na miejscu", "tick")
        else:
            lx, ly, rx, ry = sticks
            dq = np.zeros(5)
            dq[0] = SIGN_PAN * lx * v_ang
            dq[4] = SIGN_ROLL * rx * v_ang
            if self.mode == "STAWY":
                dq[1] = SIGN_LIFT * ly * v_ang
                dq[2] = SIGN_ELBOW * ry * v_ang
                dq[3] = SIGN_PITCH_UP * pitch * v_ang
            else:   # promień, wysokość [m/s], pochylenie [rad/s]; pochylenie 0 = chwytak trzyma kąt
                dq[1:4] = np.clip(dls(self.jac(self.target), np.array([ly * v_lin, ry * v_lin, pitch * v_ang])),
                                  -2 * v_ang, 2 * v_ang)
            self.target = self.target + dq * dt
            self.g = float(np.clip(self.g + (pad.lt - pad.rt) * GRIP_SPEED * dt, GRIP_MIN, 1.0))
        if self.rec is not None:
            self.rec.append((self.target.copy(), self.g))
        return self.target, self.g

    def _buttons(self, p, q_meas):
        if "X" in p:
            if self.jac is None:
                self._say("tryb KARTEZJAŃSKI tylko w symulacji")
            else:
                self.mode = "KART" if self.mode == "STAWY" else "STAWY"
                self._say(f"tryb {self.mode}", "tick")
        if "Y" in p:
            self.goto = self.home
            self._say("wracam do pozycji startowej")
        if "A" in p:
            s = self.slots.get(self.slot)
            if s:
                self.goto = (np.array(s[0]), s[1])
                self._say(f"jadę do slotu {self.slot}")
            else:
                self._say(f"slot {self.slot} pusty — {KEYS['B']} zapisuje")
        if "B" in p:
            self.slots[self.slot] = (q_meas.round(4).tolist(), round(self.g, 4))
            self._say(f"zapisano slot {self.slot}", "saved")
        if "DPAD_UP" in p or "DPAD_DOWN" in p:
            self.gear = int(np.clip(self.gear + ("DPAD_UP" in p) - ("DPAD_DOWN" in p), 0, len(GEARS) - 1))
            self._say(f"bieg {self.gear + 1}: {GEARS[self.gear][0]}", "tick")
        if "DPAD_LEFT" in p or "DPAD_RIGHT" in p:
            self.slot = (self.slot - 1 + ("DPAD_RIGHT" in p) - ("DPAD_LEFT" in p)) % N_SLOTS + 1
            self._say(f"slot {self.slot}" + ("" if self.slot in self.slots else " (pusty)"))
        if "RIGHTSTICK" in p:
            if self.rec is None:
                self.rec = []
                self._say(f"● nagrywam trasę ({KEYS['RIGHTSTICK']} kończy)", "tick")
            else:
                self.last_rec, self.rec = self.rec, None
                self._say(f"nagrano {len(self.last_rec)} kroków", "rec_saved")
        if "START" in p:
            if self.play is not None or self.play_after_goto:
                self.goto, self.play, self.play_after_goto = None, None, False
                self._say("przerwano odtwarzanie")
            elif self.last_rec:
                q5, g = self.last_rec[0]
                self.goto, self.play_after_goto, self.rec = (np.array(q5), g), True, None
                self._say("dojeżdżam do początku trasy")
            else:
                self._say(f"brak trasy — {KEYS['RIGHTSTICK']} nagrywa")
