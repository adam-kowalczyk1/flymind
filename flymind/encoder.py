"""flymind/encoder.py — enkoder obraz → napęd populacji wejściowej SNN (V4). MODEL SENSORYCZNY, nie model oka muchy.
Bez bio2, bez mujoco, bez stanu (każda klatka niezależnie), nic nie zapisuje.

Co robi (każdy krok to decyzja modelu, nie dane connectomu):
  1. kontrast chromatyczny piksela c = (G − (R+B)/2) / średnia jasność obrazu   (normalizacja Webera: odporność na
     zmianę oświetlenia); piksel „celu” gdy c > c_min. Detektor koloru — kamera RGB to nie ommatidia (UV/zieleń, ruch).
  2. azymut kolumny obrazu z modelu kamery otworkowej (te same konwencje co sensory.project: + w lewo).
  3. czułość „oka” lewego/prawego: S_L(az) = σ(az / w), S_R = 1 − S_L — strefa obuoczna o szerokości ~±2w wokół osi.
  4. napęd strony s: g_s = 1 − exp(−Σ_piksele c·S_s(az) / e0) ∈ [0, 1); prąd neuronów wejściowych strony s = I_max·g_s.
Brak użytecznej klatki (bramka sensoryczna: no_image/stale/…) → g = (0, 0): brak bodźca, NIE powtórka starej klatki.
Pozycji celu z symulatora enkoder nie dostaje (tylko obraz) — prawda służy wyłącznie do oceny.
"""
import math
from dataclasses import dataclass

import numpy as np
from scipy.ndimage import uniform_filter


class EncoderError(ValueError):
    pass


@dataclass(frozen=True)
class EncoderParams:
    fovy_deg: float = 70.0             # pionowe pole widzenia kamery (so101.SceneCfg.cam_fovy)
    c_min: float = 0.15                # próg kontrastu chromatycznego (tło szare: c = 0; szczęka czerwona/ciemna: c < 0)
    w_deg: float = 10.0                # szerokość strefy obuocznej (model)
    e0: float = 60.0                   # stała nasycenia [piksele × kontrast]; piłeczka 5 cm z 0,45 m ≈ 250 px
    i_max: float = 12.0                # mV — ta sama amplituda co bodziec V3.2
    blur_px: int = 0                   # uśrednianie przestrzenne k×k przed kontrastem (0 = brak; V4 v2: 3 — tłumi szum pikseli)


def column_azimuth(W, H, fovy_deg):
    """Azymut [rad, + w lewo] środka każdej kolumny pikseli — odwrotność sensory.project dla el = 0."""
    tanx = math.tan(math.radians(fovy_deg) / 2) * W / H
    u = np.arange(W) + 0.5
    return -np.arctan((2 * u / W - 1) * tanx)


class TargetEncoder:
    def __init__(self, shape, params=EncoderParams()):
        H, W = shape
        self.p, self.shape = params, (H, W)
        az = column_azimuth(W, H, params.fovy_deg)
        sL = 1 / (1 + np.exp(-az / math.radians(params.w_deg)))
        self.S = np.stack([sL, 1 - sL])              # [2, W]: czułość lewego i prawego „oka” per kolumna
        self.az = az

    def encode(self, image):
        """image: uint8 [H, W, 3] albo None. Zwraca dict g [2] (L, R), n_px, az_centroid (diagnostyka) — bez prawdy."""
        if image is None:
            return dict(g=np.zeros(2), n_px=0, az_centroid=None, usable=False)
        if image.dtype != np.uint8 or image.shape != (*self.shape, 3):
            raise EncoderError(f"obraz {image.dtype} {image.shape}, oczekiwano uint8 {(*self.shape, 3)}")
        x = image.astype(np.float32)
        if self.p.blur_px > 1:
            x = uniform_filter(x, size=(self.p.blur_px, self.p.blur_px, 1), mode="nearest")
        lum = float(x.mean())
        if lum < 1.0:                                   # obraz czarny: kontrast niezdefiniowany → brak bodźca
            return dict(g=np.zeros(2), n_px=0, az_centroid=None, usable=True)
        c = (x[..., 1] - (x[..., 0] + x[..., 2]) / 2) / lum
        c = np.where(c > self.p.c_min, c, 0.0)
        col = c.sum(0)                                   # [W]
        E = self.S @ col
        g = 1 - np.exp(-E / self.p.e0)
        n = int((c > 0).sum())
        azc = float((col * self.az).sum() / col.sum()) if n else None
        return dict(g=g, n_px=n, az_centroid=azc, usable=True)

    def currents(self, g, idx_L, idx_R, N):
        """Prąd [mV] dla N neuronów sieci: I_max·g_L na idx_L, I_max·g_R na idx_R, 0 gdzie indziej."""
        I = np.zeros(N)
        I[idx_L] = self.p.i_max * g[0]
        I[idx_R] = self.p.i_max * g[1]
        return I
