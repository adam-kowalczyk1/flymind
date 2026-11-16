"""Krok 6 r4 — ten sam test co r2 (sonda) / r3 (wycięcie szlaku), ale neurony z szumem prądu (ALIFParams.noise = σ mV,
jak w V5: 2 mV). Szum: nowe ziarno w każdej próbie = NOISE_BASE + numer próby w przebiegu. Bez zmian w innych plikach:
podmienia w pamięci BrainNet.reset i uruchamia brainleg_probe.py albo brainleg_lesion.py.
Uruchom: brainleg_noise.py --noise S --noise-base B [--lesion d15|d78] --net N --glu ±1 --seed S --poses P --tag T --out DIR
(ziarna testowe r4 tylko z STEP6D_FINAL_TEST=1)"""
import os
import runpy
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brainleg as B  # noqa: E402
import reflex as R  # noqa: E402

TEST6D = {21631}
HERE = os.path.dirname(os.path.abspath(__file__))


def pop(flag):
    i = sys.argv.index(flag)
    v = sys.argv[i + 1]
    del sys.argv[i:i + 2]
    return v


if __name__ == "__main__":
    sigma, base = float(pop("--noise")), int(pop("--noise-base"))
    s = int(sys.argv[sys.argv.index("--seed") + 1])
    if s in {21831, 21861, 21891}:
        sys.exit("ziarna testów r1–r3 są zużyte")
    if s in TEST6D and not os.environ.get("STEP6D_FINAL_TEST"):
        sys.exit("ziarna testowe kroku 6 r4 tylko w teście końcowym (STEP6D_FINAL_TEST=1)")
    if s in TEST6D:
        os.environ["STEP6C_FINAL_TEST"] = os.environ["STEP6B_FINAL_TEST"] = "1"   # te skrypty pilnują tylko swoich ziaren
    count = [0]

    def reset(self):
        self.net = R.SparseALIF(R.JN.LB._W(self.W), R.ALIFParams(noise=sigma), base + count[0])
        count[0] += 1
        self.r, self.rj, self.tau = R.np.zeros((5, 2)), R.np.zeros(2), 0.0
        self.rep.update(noise_mV=sigma, noise_base=base, noise_seeds_used=count[0])

    B.BrainNet.reset = reset
    target = "brainleg_lesion.py" if "--lesion" in sys.argv else "brainleg_probe.py"
    runpy.run_path(os.path.join(HERE, target), run_name="__main__")
