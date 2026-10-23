"""FlyRetinaFilter — cyfrowa siatkówka muchy dla obrazu z kamery „oko w dłoni”.

1. Pasmo: R odrzucony (Rh1 muchy ma szczyt ~480 nm, czerwień jest dla niej ciemna); jasność = 0,6·B + 0,4·G.
2. Ommatidia: rozmycie Gaussa (kąt akceptacji) i próbkowanie do siatki 32×24 = 768 punktów
   (rząd wielkości liczby ommatidiów oka Drosophila, ~750–800).
3. Lamina: filtr górnoprzepustowy w czasie (x − wolna średnia, τ = TAU_HP) usuwa statyczne tło;
   L1 = ON (jaśnienie, ruch jasnych krawędzi), L2 = OFF (ciemnienie, cienie / looming).
"""
import numpy as np
from scipy.ndimage import gaussian_filter

GRID_W, GRID_H = 32, 24
TAU_HP = 0.10            # s, stała filtra górnoprzepustowego laminy (nasza stała)


class FlyRetinaFilter:
    def __init__(self, dt=0.01, tau_hp=TAU_HP):
        self.a = np.exp(-dt / tau_hp)
        self.slow = None

    def photoreceptors(self, rgb):
        """RGB uint8 [H, W, 3] → jasność w paśmie muchy, siatka 24×32 (wiersze × kolumny), 0…1."""
        x = rgb.astype(np.float32) / 255.0
        lum = 0.6 * x[..., 2] + 0.4 * x[..., 1]                    # kanał R pominięty
        fy, fx = lum.shape[0] / GRID_H, lum.shape[1] / GRID_W
        blur = gaussian_filter(lum, sigma=(0.5 * fy, 0.5 * fx))     # kąt akceptacji ~ odstęp ommatidiów
        ys = ((np.arange(GRID_H) + 0.5) * fy).astype(int)
        xs = ((np.arange(GRID_W) + 0.5) * fx).astype(int)
        return blur[np.ix_(ys, xs)]

    def step(self, rgb):
        """Jedna klatka (co cykl 10 ms). Zwraca dict: photo, L1 (ON ≥ 0), L2 (OFF ≥ 0)."""
        p = self.photoreceptors(rgb)
        if self.slow is None:
            self.slow = p.copy()
        hp = p - self.slow
        self.slow = self.a * self.slow + (1 - self.a) * p
        return dict(photo=p, L1=np.maximum(hp, 0.0), L2=np.maximum(-hp, 0.0))

    def reset(self):
        self.slow = None


def reduction(in_shape):
    """Odsetek danych usuniętych przy przejściu z obrazu RGB in_shape=(H, W) do 768 ommatidiów."""
    return 1.0 - GRID_W * GRID_H / (in_shape[0] * in_shape[1] * 3)


if __name__ == "__main__":
    # samosprawdzenie: czerwień niewidoczna, statyczne tło znika, ruchoma jasna plamka → L1, ciemna → L2
    f = FlyRetinaFilter()
    img = np.zeros((96, 128, 3), np.uint8)
    img[..., 0] = 255                                        # czysta czerwień
    assert f.photoreceptors(img).max() == 0.0
    bg = np.full((96, 128, 3), 120, np.uint8)
    for _ in range(100):
        o = f.step(bg)
    assert o["L1"].max() < 1e-3 and o["L2"].max() < 1e-3     # tło statyczne wygasa
    lit = bg.copy()
    lit[40:56, 60:76] = 250
    o = f.step(lit)
    assert o["L1"].max() > 0.1 and o["L2"].max() < 1e-3      # jaśnienie → ON
    f.reset()
    for _ in range(100):
        f.step(bg)
    dark = bg.copy()
    dark[40:56, 60:76] = 10
    o = f.step(dark)
    assert o["L2"].max() > 0.1 and o["L1"].max() < 1e-3      # ciemnienie → OFF
    print(f"OK; redukcja danych: 128×96 RGB → 768: {reduction((96, 128)) * 100:.2f} %, "
          f"Full HD → 768: {reduction((1080, 1920)) * 100:.3f} %")
