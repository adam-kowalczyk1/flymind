"""Test fly_jaw.FlyJaw bez fizyki: brak dotyku → moment 0; dotyk 1 N na padach → moment zamykający > 0 w ciągu 10 taktów,
przy obu założeniach o glutaminianie. Bez szumu (generator losowy nieużywany), bez ziaren.
Uruchom:  .venv/bin/python -I -B flymind/test_fly_jaw.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fly_jaw import FlyJaw, FlyJawCfg  # noqa: E402


def main():
    for glu in (-1.0, 1.0):
        j = FlyJaw(FlyJawCfg(glu_sign=glu, gain_mV_per_N=40.0))
        assert all(j.step([0.0, 0.0, 0.0]) == 0.0 for _ in range(10)), "moment bez dotyku"
        tau = [j.step([1.0, 1.0, 0.0]) for _ in range(10)]
        assert tau[-1] > 0, f"Glu {glu:+.0f}: brak zamykania po dotyku, {tau}"
        print(f"  Glu {glu:+.0f}: moment po 100 ms dotyku {tau[-1]:.2f} N·m, prostownik {j.r_press:.0f} Hz, zginacz {j.r_release:.0f} Hz")
    print("OK: szczęka muchy reaguje na dotyk, milczy bez dotyku")


if __name__ == "__main__":
    main()
