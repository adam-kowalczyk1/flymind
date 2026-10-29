"""flymind/sensory.py — interfejs sensoryczny (krok 6): kontrakt klatki, znaczniki czasu, brak obrazu i utrata klatek,
odtwarzanie kontrolowanych bodźców. Bez bio2, bez mujoco; zapis tylko w save_clip (ścieżka podana jawnie).

Kontrakt klatki (Frame):
  seq        numer klatki źródła, rosnący o 1; przeskok = klatki utracone przed dostarczeniem
  t_capture  [s] chwila naświetlenia w zegarze źródła; t_receive [s] chwila odbioru — TEN SAM zegar monotoniczny
             (symulacja: czas symulacji; sprzęt: time.monotonic po stronie hosta i znacznik sterownika kamery)
  image      uint8 [H, W, 3] RGB albo None (kamera nie dała obrazu — to nie błąd, tylko brak danych)
  proprio    pozycje stawów [rad] w chwili t_capture (do kopii eferentnej) albo None
Naruszenie kontraktu (zły kształt/typ, NaN w czasie, odbiór przed naświetleniem) → SensoryError, nie cicha naprawa.

Różnica wobec bio2 (vision.py/agent.py, tylko odczyt): tam klatka nie ma znacznika czasu, filtr laminy i przepływ HS
zakładają stałe 10 ms (_flow dzieli przez 0,01 niezależnie od dt), a Δψ liczone jest z qpos odczytanego przy renderze.
Utracona lub spóźniona klatka byłaby tam po cichu traktowana jak kolejne 10 ms. Tu bramka zwraca faktyczne dt i flagi.
"""
import hashlib
import json
import math
from dataclasses import dataclass, field

import numpy as np


class SensoryError(ValueError):
    pass


@dataclass(frozen=True)
class Frame:
    seq: int
    t_capture: float
    t_receive: float
    image: np.ndarray | None
    proprio: np.ndarray | None = None
    source: str = "unknown"            # "camera" | "sim" | "replay:<sha8>" — pochodzenie, do raportów


@dataclass(frozen=True)
class Sample:
    """Wynik bramki dla jednej klatki. usable=False → konsument NIE dostaje obrazu (brak bodźca, nie powtórka)."""
    frame: Frame
    usable: bool
    flags: tuple                       # podzbiór: no_image, stale, gap, late, reset, frozen, duplicate, out_of_order
    dt: float | None                   # [s] od ostatniej użytej klatki (t_capture); None przed pierwszą użytą
    age: float                         # [s] now − t_capture
    lost: int                          # klatek utraconych tuż przed tą (przeskok seq)


@dataclass
class SensoryGate:
    shape: tuple                       # (H, W) oczekiwany rozmiar obrazu
    period: float                      # [s] nominalny okres klatek (bio2: 0,01)
    max_age: float                     # [s] starsza klatka = nieaktualna (sterowanie na niej byłoby spóźnione)
    reset_after: float                 # [s] dt powyżej → stan filtrów czasowych (lamina, przepływ) do wyzerowania
    stats: dict = field(default_factory=dict)

    def __post_init__(self):
        if not (0 < self.period <= self.max_age and self.period <= self.reset_after):
            raise SensoryError("wymagane 0 < period ≤ max_age i period ≤ reset_after")
        self.prev = None               # ostatnia klatka w kolejności (także bez obrazu / nieaktualna)
        self.last = None               # ostatnia klatka użyta (z obrazem) — od niej liczone dt
        self.last_hash = None
        self.stats = dict.fromkeys(("frames", "usable", "lost", "no_image", "stale", "late", "reset", "frozen",
                                    "duplicate", "out_of_order"), 0)

    def check(self, f):
        """Walidacja kontraktu — błąd zamiast naprawy."""
        if not (math.isfinite(f.t_capture) and math.isfinite(f.t_receive)):
            raise SensoryError(f"klatka {f.seq}: znacznik czasu NaN/inf")
        if f.t_receive < f.t_capture:
            raise SensoryError(f"klatka {f.seq}: odbiór {f.t_receive} przed naświetleniem {f.t_capture} — różne zegary?")
        if f.image is not None and (f.image.dtype != np.uint8 or f.image.shape != (*self.shape, 3)):
            raise SensoryError(f"klatka {f.seq}: obraz {f.image.dtype} {f.image.shape}, oczekiwano uint8 {(*self.shape, 3)}")
        if f.proprio is not None and not np.isfinite(f.proprio).all():
            raise SensoryError(f"klatka {f.seq}: propriocepcja NaN/inf")

    def push(self, f, now):
        """now: bieżący czas hosta [s] w zegarze t_receive (≥ t_receive)."""
        self.check(f)
        if now < f.t_receive:
            raise SensoryError(f"klatka {f.seq}: now {now} < t_receive {f.t_receive}")
        s, flags, lost, dt = self.stats, [], 0, None
        s["frames"] += 1
        age = now - f.t_capture
        if self.prev is not None and f.seq <= self.prev.seq:
            flags.append("duplicate" if f.seq == self.prev.seq else "out_of_order")
        else:
            if self.prev is not None:
                lost = f.seq - self.prev.seq - 1
                if f.t_capture <= self.prev.t_capture:
                    raise SensoryError(f"klatka {f.seq}: t_capture nie rośnie przy rosnącym seq")
                if lost:
                    flags.append("gap")
            self.prev = f
            if self.last is not None:
                # late/reset liczone od ostatniego UŻYTEGO obrazu: tyle faktycznie trwa luka w danych dla filtrów
                dt = f.t_capture - self.last.t_capture
                if dt > 1.5 * self.period:
                    flags.append("late")
                if dt > self.reset_after:
                    flags.append("reset")
            if f.image is None:
                flags.append("no_image")
            if age > self.max_age:
                flags.append("stale")
        for k in ("duplicate", "out_of_order", "no_image", "stale", "late", "reset"):
            s[k] += k in flags
        s["lost"] += lost
        usable = not {"duplicate", "out_of_order", "no_image", "stale"} & set(flags)
        if usable:
            h = hashlib.sha256(f.image.tobytes()).digest()
            # zamrożony obraz: bajtowo identyczny przy nowym seq — w kamerze z szumem matrycy oznacza zawieszony bufor;
            # w bodźcu syntetycznym bez szumu bywa poprawny, więc tylko flaga (decyzja należy do konsumenta)
            if h == self.last_hash:
                flags.append("frozen")
                s["frozen"] += 1
            self.last, self.last_hash = f, h
            s["usable"] += 1
        return Sample(f, usable, tuple(flags), dt, age, lost)


# ---------------- bodźce kontrolowane ----------------

@dataclass
class Clip:
    images: np.ndarray                 # uint8 [T, H, W, 3]
    truth: dict                        # prawda o bodźcu per klatka, np. az [rad] (+ w lewo), el [rad], visible
    meta: dict                         # parametry generatora / pochodzenie

    @property
    def sha256(self):
        return hashlib.sha256(np.ascontiguousarray(self.images).tobytes()).hexdigest()


def project(az, el, shape, fovy_deg):
    """Kierunek (az + w lewo, el + w górę) → piksel (u kolumna, v wiersz) kamery otworkowej z osią −z do przodu,
    ta sama konwencja co bio2/vision.py (x w prawo, tanx = tan(fovy/2)·W/H). Zwraca (u, v) jako float."""
    H, W = shape
    tany = math.tan(math.radians(fovy_deg) / 2)
    tanx = tany * W / H
    x, y = -np.tan(az), np.tan(el) / np.cos(az)        # punkt na płaszczyźnie z = −1
    return W / 2 * (1 + x / tanx), H / 2 * (1 - y / tany)


def spot_clip(az, el, shape, fovy_deg, radius_px=4, fg=(0, 0, 0), bg=(120, 120, 120)):
    """Plamka (koło radius_px) na jednolitym tle w kierunkach az[t], el[t] [rad]. Deterministyczne, bez szumu.
    Uwaga: tło R=G=B — siatkówka bio2 odrzuca kanał R, więc kolor bodźca ma znaczenie dla dalszych etapów."""
    az, el = np.broadcast_arrays(np.asarray(az, float), np.asarray(el, float))
    H, W = shape
    u, v = project(az, el, shape, fovy_deg)
    yy, xx = np.mgrid[:H, :W] + 0.5
    imgs = np.empty((len(az), H, W, 3), np.uint8)
    imgs[:] = bg
    visible = (np.abs(az) < math.pi / 2) & (u >= 0) & (u < W) & (v >= 0) & (v < H)
    for t in np.flatnonzero(visible):
        imgs[t][(xx - u[t]) ** 2 + (yy - v[t]) ** 2 <= radius_px ** 2] = fg
    meta = dict(kind="spot", shape=list(shape), fovy_deg=fovy_deg, radius_px=radius_px, fg=list(fg), bg=list(bg))
    return Clip(imgs, dict(az=az.copy(), el=el.copy(), visible=visible), meta)


def replay(clip, period, t0=0.0, delay=0.0, drop=(), blank=()):
    """Odtwórz klip jako strumień Frame w deterministycznym zegarze: t_capture = t0 + i·period,
    t_receive = t_capture + delay[i] (skalar lub tablica — kontrolowany jitter). drop: indeksy nie dostarczone
    (przeskok seq); blank: indeksy dostarczone bez obrazu. Prawda o bodźcu zostaje w clip.truth[seq]."""
    T = len(clip.images)
    delay = np.broadcast_to(np.asarray(delay, float), (T,))
    src = "replay:" + clip.sha256[:8]
    drop, blank = set(drop), set(blank)
    for i in range(T):
        if i in drop:
            continue
        tc = t0 + i * period
        yield Frame(i, tc, tc + delay[i], None if i in blank else clip.images[i], source=src)


def save_clip(path, clip):
    """npz bez pickle: images, truth_<klucz>, meta (JSON) z sha256 obrazów."""
    meta = json.dumps({**clip.meta, "sha256": clip.sha256})
    np.savez_compressed(path, images=clip.images, meta=np.array(meta),
                        **{"truth_" + k: np.asarray(v) for k, v in clip.truth.items()})


def load_clip(path):
    """Wczytaj i zweryfikuj klip (typ, kształt, zgodność długości prawdy, sha256)."""
    with np.load(path, allow_pickle=False) as z:
        images, meta = z["images"], json.loads(str(z["meta"]))
        truth = {k[6:]: z[k] for k in z.files if k.startswith("truth_")}
    if images.dtype != np.uint8 or images.ndim != 4 or images.shape[-1] != 3:
        raise SensoryError(f"{path}: obrazy {images.dtype} {images.shape}, oczekiwano uint8 [T, H, W, 3]")
    bad = [k for k, v in truth.items() if len(v) != len(images)]
    if bad:
        raise SensoryError(f"{path}: prawda {bad} ma inną długość niż {len(images)} klatek")
    clip = Clip(images, truth, {k: v for k, v in meta.items() if k != "sha256"})
    if clip.sha256 != meta.get("sha256"):
        raise SensoryError(f"{path}: sha256 obrazów niezgodny z meta — plik zmieniony lub uszkodzony")
    return clip
