"""Samosprawdzenie mostu: sąsiedzi MaleCNS (1,0),(0,1),(1,1) → sąsiedzi flyvis po obrocie 30°; obrót kierunku = ROT."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from bridge_prep import to_flyvis
FLY_NB = {(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)}
for q, r in [(1, 0), (0, 1), (1, 1), (-1, 0), (0, -1), (-1, -1)]:
    x, y = q - 0.5 * r, r * np.sqrt(3) / 2
    u, v = to_flyvis(np.array([x]), np.array([y]), 30)
    assert (int(u[0]), int(v[0])) in FLY_NB, (q, r, u, v)
u, v = to_flyvis(np.array([10.0]), np.array([0.0]), 30)          # kierunek 0° w MaleCNS → 30° we flyvis
X = np.array([1.5 * v[0], -np.sqrt(3) * (u[0] + v[0] / 2)]) / np.sqrt(3)
assert abs(np.degrees(np.arctan2(X[1], X[0])) - 30) < 4, X
print("test_bridge OK")
