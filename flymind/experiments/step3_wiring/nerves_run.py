"""Etap 1 z „nerwami” (nerves.py): ta sama próba co touch_natural.py, mózg muchy bez zmian, czucie i ruch przez model FSR/serw.
Uruchom: nerves_run.py --nerves ideal|typ|pess [--lesion none|both] --net N --glu ±1 --seed S --poses P --tag T --out DIR
(ziarna testowe tylko z NERVES_FINAL_TEST=1; cel: LOOP_TARGET_nerves_r1.md)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nerves  # noqa: E402
import touch_natural as T  # noqa: E402

TEST_NV = {21941, 21942, 21943}


def opt(name, default):
    if name not in sys.argv:
        return default
    i = sys.argv.index(name)
    v = sys.argv[i + 1]
    del sys.argv[i:i + 2]
    return v


if __name__ == "__main__":
    level, lesion = opt("--nerves", None), opt("--lesion", "none")
    assert level in nerves.LEVELS and lesion in ("none", "both", "d15", "d78"), (level, lesion)
    s = int(sys.argv[sys.argv.index("--seed") + 1])
    if s in T.USED | T.TEST_T1:
        sys.exit("ziarno zużyte")
    if s in TEST_NV and not os.environ.get("NERVES_FINAL_TEST"):
        sys.exit("ziarna testowe nerwów tylko w teście końcowym (NERVES_FINAL_TEST=1)")
    if lesion != "none":
        T.lesion_init(lesion)

    def trial(item, seed, kind, net, fc, ac):
        net.nerve_seed = seed
        r = T.trial(item, seed, kind, net, fc, ac)
        r["nerves"] = level
        if net.nv.p is not None:
            r["fsr_gain"] = [round(float(x), 3) for x in net.nv.g]
        return r

    T.R.F_ON = 3.0
    T.R.JN.ForceWorld = T.LogWorld
    T.R.TwoNet = nerves.wrap(T.B.BrainNet, level)
    T.R.trial = trial
    T.R.main()
