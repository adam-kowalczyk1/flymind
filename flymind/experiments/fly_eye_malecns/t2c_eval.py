"""T2c (PREREG_T2c.md): AUC zbliżań na fakturze vs negatywy testu, prawdziwe − potasowane, modele 003–008."""
import json
import os
import sys

import numpy as np

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../results/fly_eye_malecns_20261120")


def auc(p, n):
    p, n = np.asarray(p), np.asarray(n)
    return float((p[:, None] > n[None]).mean() + 0.5 * (p[:, None] == n[None]).mean())


def tex_auc(y):
    pos = [v for k, v in y.items() if k.startswith(("Tloomtex_", "Tloomself_"))]
    neg = [v for k, v in y.items() if k.startswith(("Trecede_", "Tself_", "Ttrans6_"))]
    assert len(pos) == 8 and len(neg) == 24, (len(pos), len(neg))
    return auc(pos, neg)


def main(models=range(3, 9)):
    rows, ok = [], 0
    for m in models:
        a, s = (json.load(open(f"{R}/t2c_LPLC2_full_{w}_{m}.json")) for w in ("real", "shuffle"))
        d = tex_auc(a["y"]) - tex_auc(s["y"])
        ok += d >= 0.10
        rows.append(dict(model=m, tex_real=tex_auc(a["y"]), tex_shuffle=tex_auc(s["y"]), diff=d, auc_test_real=a["auc_test"],
                         auc_test_shuffle=s["auc_test"], auc_train_real=a["auc_train"], auc_train_shuffle=s["auc_train"]))
        print(json.dumps(rows[-1]))
    res = dict(rows=rows, n_pass=int(ok), PASS=bool(ok >= 5))
    json.dump(res, open(f"{R}/t2c_result.json", "w"), indent=1)
    print("PASS" if res["PASS"] else "FAILED", ok, "/ 6")


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:                                   # sprawdzian miary na v2 (modele 0–2, znane wyniki)
        for m in range(3):
            a, s = (json.load(open(f"{R}/v2_LPLC2_full_{w}_{m}.json")) for w in ("real", "shuffle"))
            print(m, round(tex_auc(a["y"]), 3), round(tex_auc(s["y"]), 3))
    else:
        main()
