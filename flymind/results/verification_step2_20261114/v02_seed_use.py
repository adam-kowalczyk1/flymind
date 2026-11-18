"""Weryfikacja kroku 2 — użycie ziaren (tylko odczyt inventory.json)."""
import json, collections, datetime as dt, os
rows = [r for r in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.json"))) if r.get("kind") == "runs"]
f = lambda t: dt.datetime.fromtimestamp(t).strftime("%d %H:%M")
TEST = {20201: "b", 20401: "c", 20601: "d", 20801: "e", 20901: "arm", 20971: "conflict"}
print("== serie według (katalog, ziarno benchmarku) ==")
g = collections.defaultdict(list)
for r in rows:
    g[(os.path.dirname(r["path"]), r["seed"])].append(r)
for (d, s), L in sorted(g.items()):
    arms = collections.Counter((r["arm"], r["glu"], r["shuffle_seed"], r["dt_ms"], r["n"]) for r in L)
    print(f"{d:42s} seed {s} {'TEST' if s in TEST else '    '} plików {len(L):2d} | prób {sorted(set(r['n'] for r in L))} | dt {sorted(set(str(r['dt_ms']) for r in L))} "
          f"| lm {sorted(set(str(r['lift_max']) for r in L))} | N {sorted(set(str(r['N']) for r in L))} | W {sorted(set(str(r['W_sha'])[:8] for r in L))} | {f(min(r['birth'] for r in L))}–{f(max(r['mtime'] for r in L))}")
print("\n== ziarna tasowań: gdzie użyte ==")
sh = collections.defaultdict(list)
for r in rows:
    if r["shuffle_seed"] is not None:
        sh[r["shuffle_seed"]].append((r["path"], r["glu"], str(r["W_sha_shuf"])[:8], str(r["W_sha"])[:8]))
for s, L in sorted(sh.items()):
    print(s, len(L)); [print("    ", x) for x in L]
print("\n== duplikaty: ta sama (ziarno, ramię, Glu, tasowanie, dt) w >1 pliku ==")
k = collections.defaultdict(list)
for r in rows:
    k[(r["seed"], r["arm"], r["glu"] if r["arm"] != "K0" else None, r["shuffle_seed"], r["dt_ms"], r["lift_max"], r["net"], str(r["inputs"]), str(r["joints"]), r["roll"])].append(r["path"])
for kk, L in sorted(k.items(), key=str):
    if len(L) > 1:
        print(kk); [print("    ", x) for x in L]
print("\n== pliki z 0 prób lub niepełne ==")
for r in rows:
    exp = 45 * (r["poses"] or 1)
    if r["n"] != exp or r["n_unique"] != r["n"]:
        print(f"{r['path']:55s} n {r['n']} uniq {r['n_unique']} oczekiwane {exp} (poses {r['poses']})")
