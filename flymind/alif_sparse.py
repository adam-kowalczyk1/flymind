"""flymind/alif_sparse.py — ta sama sieć ALIF co alif.py, z macierzą wag rzadką (CSR). Bez bio2, bez mujoco.

alif.py jest przypięty sha256 w manifestach eksperymentów F1, więc go nie zmieniam: SparseALIF dziedziczy równania,
parametry i stan z ALIF i podmienia tylko przechowywanie W. Gęsta W [N, N] dla obwodu nogi (~1500 neuronów)
to 18 MB i ~N² działań na krok; rzadka — tylko niezerowe połączenia. Równoważność wyników: test_alif_sparse.py.
"""
import numpy as np
import scipy.sparse as sp

from alif import ALIF


class _Shape:
    """Atrapa spec dla ALIF.__init__: ten sam N, bez budowania gęstej macierzy."""
    def __init__(self, n):
        self.W = np.zeros((n, 0))


class SparseALIF(ALIF):
    def __init__(self, spec, params, seed, gain=None, b_a=None):
        W = sp.csr_matrix(spec.W, dtype=float)
        if W.shape[0] != W.shape[1]:
            raise ValueError(f"W musi być kwadratowa, jest {W.shape}")
        super().__init__(_Shape(W.shape[0]), params, seed, gain, b_a)
        self.W = W
