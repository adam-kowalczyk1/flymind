"""Widzenie bio2: FlyRetinaFilter + detektor małego celu (jak LC10) + detektor loomingu (jak LC4/LPLC2)
+ kopia eferentna obrotu (jak tłumienie HS przy ruchu własnym) + pomiar przepływu poziomego (wejście HS).

Kopia eferentna: zanim siatkówka policzy różnicę czasową, wolna średnia (pamięć tła) jest przesuwana o
przewidziany obrót kamery z propriocepcji bazy (Δψ → Δkolumn). Obrót własny nie zostawia wtedy na L1/L2
„przesuwającego się świata”. Bez kopii każdy obrót bazy daje szeroki sygnał OFF.
"""
import numpy as np
from scipy.ndimage import binary_dilation, label as nd_label, shift as nd_shift

from retina import GRID_H, GRID_W, FlyRetinaFilter

# --- nasze stałe (z pomiarów sygnałów w scenie, bio2/vision_calib — patrz RESULTS) ---
T_TARGET = 0.08       # min. szczyt L1+L2 celu
N_SMALL = 40          # maks. liczba komórek (>30 % szczytu) „małego” celu z 768
ASPECT = 2            # plamka zwarta: wysokość ≤ 2·szerokość + 1 i odwrotnie (krawędzie przesłony to pionowe paski
                      # h 13–16 × w 2–4 komórek; piłeczka ok. 5 × 5) — jak selektywność LC10/LC11 na małe obiekty, nie paski
N_MIN = 4             # min. komórek plamki (odłamki krawędzi mają 1–3)
BIPOLAR = 0.15        # toczący się obiekt ma krawędź ON i OFF naraz (każda ≥ 15 % sumy); krawędź przesłony — jedną
T_L2 = 0.25           # próg komórki OFF dla loomingu (silne ściemnienie — ciemny obiekt)
GROW_WIN = 5          # klatek (50 ms) — okno przyrostu obszaru OFF
G_LOOM0, G_LOOM1 = 20, 24    # przyrost obszaru OFF w połowie pola w GROW_WIN: od G0 sygnał rośnie, przy G0+G1 = 1
# G0 = 20 (było 15; stage3_b1 na seedach 100–139): przy 15 piłeczka z równi dawała fałszywą ucieczkę w 8/40 prób,
# przy 20 w 2/40, przy 25 w 0/40 (ale spike 1,3 cm później, odsunięcie na czas 28/40 zamiast 36/40)
# Zmierzone (vision_calib.py, 2026-10-24): obrót własny ±1,8 rad/s daje przyrost ≤ 24 bez kopii eferentnej i ≤ 14 z nią;
# piłeczka wjeżdżająca w paszczę ≤ 10; czarna kula r 8 cm z 1,5 m/s: 21 przy 0,25 m, 33 przy 0,20 m, 84 przy 0,16 m.


class Vision:
    def __init__(self, fovy_deg, aspect, efference=True, dt=0.01, t_l2=T_L2):
        self.ret = FlyRetinaFilter(dt=dt)
        self.t_l2 = t_l2
        self.hist = []
        self.tanx = np.tan(np.radians(fovy_deg) / 2) * aspect
        self.rad_per_col = 2 * np.arctan(self.tanx) / GRID_W
        self.efference = efference
        self.prev_photo = None
        # współrzędne obrazu środka każdej kolumny/wiersza w układzie kamery (x w prawo, y w górę, z = −1)
        self.tany = np.tan(np.radians(fovy_deg) / 2)
        self.col_x = (2 * (np.arange(GRID_W) + 0.5) / GRID_W - 1) * self.tanx
        self.row_y = (1 - 2 * (np.arange(GRID_H) + 0.5) / GRID_H) * self.tany
        self.col_az = np.arctan(-self.col_x)              # + = w lewo

    def reset(self):
        self.ret.reset()
        self.prev_photo = None
        self.hist = []

    def step(self, rgb, dpsi=0.0):
        """rgb: klatka kamery; dpsi: obrót kamery od poprzedniej klatki [rad], + w lewo (propriocepcja).
        Zwraca dict: target (azymut [rad] lub None), target_strength, loom (L, P) 0–1, flow [rad/s] (HS)."""
        if self.efference and self.ret.slow is not None and dpsi != 0.0:
            # kamera w lewo → świat przesuwa się w obrazie w prawo (rosnące kolumny)
            self.ret.slow = nd_shift(self.ret.slow, (0, dpsi / self.rad_per_col), order=1, mode="nearest")
        o = self.ret.step(rgb)
        E = o["L1"] + o["L2"]
        peak = float(E.max())
        # kandydaci na cel: spójne plamki (> 30 % szczytu), małe (≤ N_SMALL komórek) — osobno, żeby krawędź
        # przesłony (paralaksa przy obrocie) nie uśredniała się z piłeczką; wyboru dokonuje uwaga (agent)
        cands = []
        if peak >= T_TARGET:
            mask = E > 0.3 * peak
            # krawędź ON (tył) i OFF (przód) toczącej się piłeczki są rozdzielone 1–2 komórkami — łączę sąsiadów
            lab, n = nd_label(binary_dilation(mask, iterations=1), structure=np.ones((3, 3)))
            for i in range(1, n + 1):
                comp = (lab == i) & mask
                w = E * comp
                rr, cc = np.nonzero(comp)
                h, wd = np.ptp(rr) + 1, np.ptp(cc) + 1
                on, off = o["L1"][rr, cc].sum(), o["L2"][rr, cc].sum()
                if (len(rr) > N_SMALL or len(rr) < N_MIN or w.max() < T_TARGET or h > ASPECT * wd + 1
                        or wd > ASPECT * h + 1 or min(on, off) < BIPOLAR * (on + off)):
                    continue
                cx = float((w.sum(0) * self.col_x).sum() / w.sum())
                cy = float((w.sum(1) * self.row_y).sum() / w.sum())
                cands.append(dict(az=float(np.arctan(-cx)), ray=np.array([cx, cy, -1.0]), strength=float(w.max()),
                                  n=len(rr)))
            cands.sort(key=lambda c: -c["strength"])
        target = cands[0]["az"] if cands else None
        ray = cands[0]["ray"] if cands else None
        n_blob = cands[0]["n"] if cands else 0
        off = o["L2"] > self.t_l2
        half = GRID_W // 2
        areas = (int(off[:, :half].sum()), int(off[:, half:].sum()))
        self.hist.append(areas)
        old = self.hist[-GROW_WIN - 1] if len(self.hist) > GROW_WIN else self.hist[0]   # start: brak przyrostu
        grow = tuple(a - b for a, b in zip(areas, old))
        loom = tuple(float(np.clip((g - G_LOOM0) / G_LOOM1, 0, 1)) for g in grow)
        flow = self._flow(o["photo"])
        return dict(target=target, ray=ray, cands=cands, target_strength=peak, n_blob=n_blob, loom=loom, off_area=areas, grow=grow, flow=flow,
                    retina=o)

    def _flow(self, photo):
        """Przepływ poziomy (rad na klatkę → rad/s przy 100 Hz) z korelacji przesunięć kolumn."""
        prev, self.prev_photo = self.prev_photo, photo
        if prev is None:
            return 0.0
        a, b = prev - prev.mean(), photo - photo.mean()
        shifts = np.arange(-3, 4)
        c = [(np.roll(a, s, axis=1)[:, 3:-3] * b[:, 3:-3]).sum() for s in shifts]
        s = shifts[int(np.argmax(c))]
        return float(s * self.rad_per_col / 0.01)        # obraz w prawo = kamera w lewo = + w lewo


def true_bearing(d, body, cam="eye"):
    """Prawdziwy azymut ciała względem osi kamery [rad], + w lewo (do oceny, nie dla sterownika)."""
    R = d.cam(cam).xmat.reshape(3, 3)
    v = R.T @ (d.body(body).xpos - d.cam(cam).xpos)          # układ kamery: x w prawo, y w górę, −z do przodu
    return float(np.arctan2(-v[0], -v[2]))
