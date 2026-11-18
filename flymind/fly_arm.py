"""flymind/fly_arm.py — ramię SO-101 sterowane siecią muchy z danych (vision_leg: LC9 → DNp09 → VNC → nogi). Bez bio2.

Projekt i mapowanie: experiments/fj2_fly_arm/DESIGN.md. Jedynymi wejściami są zmysły: obraz (encoder.py → LC9 L/R)
i dotyk padów (→ receptory szczecinkowe nogi T2 L). Neuronów ruchowych nie pobudza się sztucznie.
Wyjście: przyrosty celów stawów 1–2 i moment szczęki, źródło "snn:vision_leg". Bezpieczeństwo robi safety.SafetyLayer.

  shoulder_lift += k·dt·(Pleural remotor/abductor − Sternal anterior rotator)     [MODEL / ANALOGIA]
  elbow_flex    += k·dt·(Tr flexor − Tr extensor)
  moment szczęki = k_jaw·(Ti extensor − Ti flexor − Acc. ti flexor)               (jak FJ1)
"""
from dataclasses import dataclass

import numpy as np

from alif import ALIFParams
from alif_sparse import SparseALIF
from encoder import TargetEncoder
from vision_leg import network

JOINTS = {1: ("Pleural remotor/abductor MN", "Sternal anterior rotator MN"), 2: ("Tr flexor MN", "Tr extensor MN")}
JAW = (("Ti extensor MN",), ("Ti flexor MN", "Acc. ti flexor MN"))


@dataclass(frozen=True)
class FlyArmCfg:
    J0: float = 0.275            # mV/synapsę (Shiu i in. 2024)
    glu_sign: float = -1.0
    leg: str = "T2L"
    k: float = 0.01              # rad/s na Hz różnicy pul (stawy 1–2)
    k_jaw: float = 0.005         # N·m na Hz (jak FJ1)
    touch_mV_per_N: float = 40.0
    touch_max_mV: float = 40.0
    rate_tau: float = 0.05       # s
    steps: int = 10              # kroków ALIF (1 ms) na takt 10 ms


class FlyArm:
    def __init__(self, cam_shape, cfg=FlyArmCfg(), spec=None):
        self.cfg = cfg
        base, self.idx, self.rep = network(cfg.J0, cfg.glu_sign)
        self.spec = base if spec is None else spec
        self.net = SparseALIF(self.spec, ALIFParams(), None)       # szum 0: generator losowy nieużywany
        self.enc = TargetEncoder(cam_shape)
        leg = self.idx["legs"][cfg.leg]
        br = leg["sensory"]["mechanosensory bristle"]
        self.pad_in = (br[: len(br) // 2], br[len(br) // 2:])
        pool = lambda names: [i for n in names for i in leg["MN"].get(n, [])]  # noqa: E731
        self.pools = {j: (pool([a]), pool([b])) for j, (a, b) in JOINTS.items()}
        self.jaw = (pool(JAW[0]), pool(JAW[1]))
        self.r = {k: np.zeros(2) for k in list(JOINTS) + ["jaw"]}
        self.N = self.spec.W.shape[0]

    def step(self, image, touch, dt=0.01):
        """Zwraca (dq {staw: rad}, moment szczęki N·m, diagnostyka)."""
        c = self.cfg
        g = self.enc.encode(image)["g"]
        X = np.zeros(self.N)
        X[self.idx["LC9"]["L"]] = self.enc.p.i_max * g[0]
        X[self.idx["LC9"]["R"]] = self.enc.p.i_max * g[1]
        for ix, f in zip(self.pad_in, touch[:2]):
            X[ix] = min(c.touch_max_mV, c.touch_mV_per_N * max(0.0, float(f)))
        s = self.net.run(X, c.steps)
        a = dt / c.rate_tau
        for key, (ag, an) in list(self.pools.items()) + [("jaw", self.jaw)]:
            now = np.array([s[:, ag].mean(), s[:, an].mean()]) * 1000
            self.r[key] += a * (now - self.r[key])
        dq = {j: c.k * dt * float(self.r[j][0] - self.r[j][1]) for j in JOINTS}
        tau = c.k_jaw * float(self.r["jaw"][0] - self.r["jaw"][1])
        dn = s[:, [self.idx["DNp09"]["L"], self.idx["DNp09"]["R"]]].mean(0) * 1000
        return dq, tau, dict(g=g, dnp09=dn, rates={k: v.round(1).tolist() for k, v in self.r.items()})
