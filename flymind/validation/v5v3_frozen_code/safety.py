"""flymind/safety.py — warstwa bezpieczeństwa (krok 8) między dekoderem a SO-101. Bez bio2, bez mujoco, bez sprzętu.

To jest KLASYCZNY kod sterowania, nie model biologiczny: każde wejście ma jawne źródło („snn:…”, „classical:…”,
„script:…”), a raport liczy, ile razy warstwa zmieniła komendę danego źródła — ograniczenia nie mogą po cichu
udawać zachowania sieci. Warstwa nie wysyła niczego do ramienia; zwraca cele, które krok 9 przekaże symulatorowi.

Kanały wyjściowe:
  q_target[5]  [rad]  cele pozycyjne serw: shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll
  jaw_torque   [N·m]  moment szczęki, + = zamykanie (jak dekoder; bio2 zamienia gripper na silnik momentowy)
Kolejność ograniczeń dla stawu (każde ustawia flagę): zakres − margines → prędkość (|Δcel| ≤ v_max·dt) →
wyprzedzenie celu względem pomiaru (|cel − q| ≤ max_lead; bio2: WINDUP 0,02 rad dla bazy) → zakres ponownie.
Wstrzymanie (hold) = cel z poprzedniego taktu; dla szczęki = 0 N·m (bez przegrzewania serwa w utyku; obiekt może wypaść).
Czego NIE ma: kolizji ze stołem i przestrzeni roboczej w kartezjańskich współrzędnych (wymaga kinematyki — krok 9).
"""
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import numpy as np

ARM = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll")
SOURCES = ("snn:", "classical:", "script:")


class SafetyError(ValueError):
    pass


def ranges_from_mjcf(path, names=ARM + ("gripper",)):
    """Zakresy stawów [rad] z pliku MJCF (tylko odczyt XML, bez mujoco). Brak stawu lub zakresu → błąd."""
    j = {e.get("name"): e.get("range") for e in ET.parse(path).iter("joint")}
    miss = [n for n in names if not j.get(n)]
    if miss:
        raise SafetyError(f"{path}: brak stawów/zakresów {miss}")
    return np.array([[float(v) for v in j[n].split()] for n in names])


@dataclass(frozen=True)
class Limits:
    ranges: np.ndarray                 # [6, 2] rad: 5 stawów ramienia + gripper (ranges_from_mjcf)
    dt: float = 0.01                   # s, okres sterowania (bio2: 10 ms)
    margin: float = 0.05               # rad od krańca zakresu
    v_max: float = 1.5                 # rad/s na cel (wybór projektu; serwo STS3215 ok. 4,7 rad/s wg bio2)
    max_lead: tuple = (0.02, 0.3, 0.3, 0.3, 0.3)   # rad; baza jak bio2 WINDUP, reszta wybór projektu
    tau_max: float = 1.0               # N·m szczęki (serwo: 3,35 N·m forcerange; tu z zapasem)
    jaw_close_dir: float = -1.0        # zamykanie zmniejsza q gripper (bio2: ctrl = −τ/GRIP_TORQUE, gear > 0)
    cmd_timeout: float = 0.05          # s bez świeżej komendy → hold
    state_tol: float = 0.05            # rad poza zakresem pomiaru → błąd czujnika (fault)
    max_sensor_age: float = 0.05       # s; starszy obraz → kanały wizyjne hold
    vision_joints: tuple = (0,)        # stawy sterowane z widzenia (bio2: tylko baza)


@dataclass(frozen=True)
class Command:
    t: float                           # s, chwila wytworzenia komendy (zegar sterowania)
    q_target: dict                     # {indeks stawu 0–4: rad}; brak klucza = brak komendy (hold)
    jaw_torque: float | None           # N·m, None = brak komendy (0)
    sources: dict                      # {indeks stawu / "jaw": "snn:DNa02" | "classical:…" | "script:…"}


@dataclass
class SafetyLayer:
    lim: Limits
    stats: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.lim.ranges.shape != (6, 2) or not (np.diff(self.lim.ranges, axis=1) > 2 * self.lim.margin).all():
            raise SafetyError("ranges: [6, 2], każdy zakres szerszy niż 2·margin")
        self.prev = None               # ostatni wysłany cel [5]
        self.fault = None              # zatrzaśnięty powód (estop / błąd czujnika) — kasuje tylko clear()
        self.stats = {"ticks": 0, "hold": 0, "per_source": {}}

    def estop(self, reason):
        self.fault = "estop: " + reason

    def clear(self, reason):
        """Jawne skasowanie zatrzaśniętego błędu (np. operator); powód trafia do statystyk."""
        self.stats.setdefault("cleared", []).append((self.fault, reason))
        self.fault = None

    def _count(self, src, key):
        d = self.stats["per_source"].setdefault(src, {"ticks": 0})
        d[key] = d.get(key, 0) + 1

    def step(self, cmd, q, now, sensor_age):
        """q: zmierzone pozycje [6] (5 ramienia + gripper). Zwraca (q_target[5], jaw_torque, flags, per_joint)."""
        L, flags, per = self.lim, [], {}
        self.stats["ticks"] += 1
        q = np.asarray(q, float)
        if q.shape != (6,) or not np.isfinite(q).all():
            self.fault = self.fault or "state: pomiar NaN/inf lub zły kształt"
        elif ((q < L.ranges[:, 0] - L.state_tol) | (q > L.ranges[:, 1] + L.state_tol)).any():
            self.fault = self.fault or f"state: pomiar poza zakresem {np.round(q, 3).tolist()}"
        if self.prev is None:
            if self.fault:             # pierwszy takt bez wiarygodnego pomiaru: nie ma bezpiecznego celu
                raise SafetyError(f"brak bezpiecznego celu startowego: {self.fault}")
            self.prev = q[:5].copy()   # start: cel = pomiar (bez skoku)
        out = self.prev.copy()
        bad = [s for s in cmd.sources.values() if not s.startswith(SOURCES)]
        if bad:
            raise SafetyError(f"źródła bez etykiety {SOURCES}: {bad}")
        vals = list(cmd.q_target.values()) + ([cmd.jaw_torque] if cmd.jaw_torque is not None else [])
        if self.fault:
            flags.append("fault")
        elif now - cmd.t > L.cmd_timeout:
            flags.append("cmd_timeout")
        elif not all(math.isfinite(v) for v in vals) or not set(cmd.q_target) <= set(range(5)):
            flags.append("bad_command")
        if flags:
            self.stats["hold"] += 1
            return out, 0.0, tuple(flags), per

        lo, hi = L.ranges[:5, 0] + L.margin, L.ranges[:5, 1] - L.margin
        for j, x in cmd.q_target.items():
            src, f = cmd.sources.get(j, "classical:unlabelled"), []
            self._count(src, "ticks")
            if j in L.vision_joints and sensor_age > L.max_sensor_age:
                f.append("vision_stale")
                x = self.prev[j]
            if not lo[j] <= x <= hi[j]:
                f.append("range")
            x = min(max(x, lo[j]), hi[j])
            step = L.v_max * L.dt
            if abs(x - self.prev[j]) > step:
                f.append("rate")
                x = self.prev[j] + math.copysign(step, x - self.prev[j])
            if abs(x - q[j]) > L.max_lead[j]:
                f.append("lead")
                x = q[j] + math.copysign(L.max_lead[j], x - q[j])
            out[j] = min(max(x, lo[j]), hi[j])
            for k in f:
                self._count(src, k)
            if f:
                per[j] = tuple(f)

        tau = 0.0
        if cmd.jaw_torque is not None:
            src = cmd.sources.get("jaw", "classical:unlabelled")
            self._count(src, "ticks")
            tau, f = cmd.jaw_torque, []
            if abs(tau) > L.tau_max:
                f.append("torque")
                tau = math.copysign(L.tau_max, tau)
            # kraniec szczęki: moment pchający dalej w kraniec → 0 (zamykanie pcha w stronę jaw_close_dir)
            push = L.jaw_close_dir * tau
            if (push < 0 and q[5] <= L.ranges[5, 0] + L.margin) or (push > 0 and q[5] >= L.ranges[5, 1] - L.margin):
                f.append("jaw_end")
                tau = 0.0
            for k in f:
                self._count(src, k)
            if f:
                per["jaw"] = tuple(f)
        self.prev = out
        return out.copy(), float(tau), tuple(flags), per
