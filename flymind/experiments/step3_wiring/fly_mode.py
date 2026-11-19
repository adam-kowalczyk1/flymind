"""Tryb mózgu muchy ustawiany w panelu FlyMind Hub (strona „Robot i sprzęt”): mucha bez zmian albo POKAZ z wyciszonym „hamulcem”
DNg98 + DNg70 (test „hamulec” r1 PASS, results/step3_20261115/brake_r1/). Tylko dla symulacji/pokazów (brain_view.py, fsr_live.py);
testy naukowe tego nie czytają. Brak panelu / brak ustawienia = mucha bez zmian.
Ścieżka stanu panelu: $FLYMIND_HUB_STATE albo ~/FlyMind_Hub/data/state.json."""
import json
import os

import numpy as np

BRAKE_BODY = (10394, 10959, 10967, 11131)          # DNg98 ×2, DNg70 ×2 (bodyId MaleCNS; ten sam zestaw co silence_S.json)
STATE = os.environ.get("FLYMIND_HUB_STATE", os.path.expanduser("~/FlyMind_Hub/data/state.json"))


def from_hub(path=STATE):
    """'silenced' albo 'intact' (domyślnie, także gdy panelu nie ma lub plik jest uszkodzony)."""
    try:
        return "silenced" if json.load(open(path)).get("fly_mode", {}).get("brake") == "silenced" else "intact"
    except (OSError, ValueError, AttributeError):
        return "intact"


def resolve(arg):
    """--brake hub|intact|silenced → 'intact' / 'silenced'."""
    return from_hub() if arg == "hub" else arg


def apply(net, mode):
    """Wycisza wyjścia neuronów hamulca (jak wycięcie w avoid.py). Zwraca liczbę wyciszonych komórek (0 dla 'intact')."""
    if mode != "silenced":
        return 0
    import scipy.sparse as sp
    idx = [net.pos[b] for b in BRAKE_BODY if b in net.pos]
    if not idx:
        raise RuntimeError("w tej sieci nie ma neuronów hamulca DNg98/DNg70")
    mask = np.ones(net.N)
    mask[idx] = 0.0
    net.W = sp.csr_matrix(net.W.multiply(mask[None, :])) if sp.issparse(net.W) else net.W * mask[None, :]
    return len(idx)


def _check():
    import tempfile
    d = tempfile.mkdtemp()
    p = os.path.join(d, "s.json")
    assert from_hub(p) == "intact"                                  # brak pliku
    open(p, "w").write("{zepsuty")
    assert from_hub(p) == "intact"
    json.dump({"fly_mode": {"brake": "silenced"}}, open(p, "w"))
    assert from_hub(p) == "silenced"
    json.dump({"fly_mode": {"brake": "intact"}}, open(p, "w"))
    assert from_hub(p) == "intact"

    class Net:
        N, pos = 6, {10394: 1, 10967: 4, 7: 0}
        W = np.ones((6, 6))
    n = Net()
    assert apply(n, "intact") == 0 and n.W.sum() == 36
    assert apply(n, "silenced") == 2 and n.W[:, 1].sum() == 0 and n.W[:, 4].sum() == 0 and n.W[:, 0].sum() == 6
    print("fly_mode _check OK, panel teraz:", from_hub())


if __name__ == "__main__":
    _check()
