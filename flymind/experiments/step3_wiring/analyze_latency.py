"""Czysty pomiar czasu pętli (zapisany PRZED pomiarem; reguły LOOP_TARGET_latency_r1.md).
Uruchom: analyze_latency.py KATALOG OUT.json"""
import glob
import json
import os
import sys

LOOP_P99_MAX = 50.0   # ms: 10 ms okres kamery + p99 obliczeń < 60 ms


def main(d, out):
    if os.path.exists(out):
        sys.exit(f"istnieje {out}")
    rows = {}
    for p in sorted(glob.glob(os.path.join(d, "*_chroma_*.json"))):
        j = json.load(open(p))
        L = j["summary"]["loop_ms"]
        rows[j["tag"]] = dict(arm=j["arm"], n_ticks=L["n"], median=L["median"], p95=L["p95"], p99=L["p99"], p999=L["p999"], max=L["max"],
                              over_50=L["over_50"], loop_closure_p99_ms=round(10 + L["p99"], 1), success=j["summary"]["success"]["k"],
                              n=j["summary"]["success"]["n"], ok=bool(L["p99"] < LOOP_P99_MAX))
    ver = {arm: bool(any(v["arm"] == arm for v in rows.values()) and all(v["ok"] for v in rows.values() if v["arm"] == arm))
           for arm in ("A_cam", "E_vis_touch")}
    res = dict(rows=rows, K3_clean=ver)
    for k, v in rows.items():
        print(k, v)
    print("K3 (czysty pomiar):", ver)
    with open(out, "x") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(*sys.argv[1:3])
