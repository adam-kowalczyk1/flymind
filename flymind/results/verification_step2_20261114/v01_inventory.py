"""Weryfikacja kroku 2 — inwentarz wszystkich plików wyników (tylko odczyt).
Dla każdego JSON z listą prób: ramię, Glu, ziarno benchmarku, ziarno tasowania, zakres ziaren prób, liczba prób,
hash W, hashe kodu, czas utworzenia/modyfikacji pliku. Wynik: inventory.json + tabela na stdout."""
import glob, hashlib, json, os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "step2_whole_arm_20261113")
rows = []
for p in sorted(glob.glob(os.path.join(ROOT, "**", "*.json"), recursive=True)):
    try:
        d = json.load(open(p))
    except Exception as e:
        rows.append(dict(path=os.path.relpath(p, ROOT), error=str(e))); continue
    st = os.stat(p)
    r = dict(path=os.path.relpath(p, ROOT), birth=st.st_birthtime, mtime=st.st_mtime, size=st.st_size,
             sha256=hashlib.sha256(open(p, "rb").read()).hexdigest())
    if isinstance(d, dict) and isinstance(d.get("runs"), list):
        runs = d["runs"]
        seeds = [x.get("seed") for x in runs if isinstance(x, dict)]
        cfg = d.get("arm_cfg") or d.get("lift_cfg") or d.get("cfg") or {}
        ln = d.get("lift_net") or d.get("net") or {}
        r.update(kind="runs", tag=d.get("tag"), arm=d.get("arm"), glu=d.get("glu"), seed=d.get("seed"), poses=d.get("poses"),
                 shuffle_seed=d.get("shuffle_seed"), version=d.get("version"), n=len(runs),
                 seed_min=min(seeds) if seeds and None not in seeds else None, seed_max=max(seeds) if seeds and None not in seeds else None,
                 n_unique=len(set(seeds)), dt_ms=cfg.get("dt_ms"), lift_max=cfg.get("lift_max"), net=cfg.get("net") or cfg.get("in_rule"),
                 inputs=cfg.get("inputs"), joints=cfg.get("joints"), roll=cfg.get("roll"),
                 N=ln.get("N") if isinstance(ln, dict) else None, W_sha=(ln.get("W_sha256") if isinstance(ln, dict) else None),
                 W_sha_shuf=(ln.get("W_sha256_shuffled") if isinstance(ln, dict) else None),
                 code={k: v[:12] for k, v in (d.get("code_sha256") or {}).items()}, top_keys=sorted(d.keys()))
    else:
        r.update(kind="other", top_keys=sorted(d.keys()) if isinstance(d, dict) else type(d).__name__)
    rows.append(r)
json.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.json"), "w"), indent=1)
import datetime as dt
f = lambda t: dt.datetime.fromtimestamp(t).strftime("%d %H:%M:%S")
for r in rows:
    if r.get("kind") == "runs":
        print(f"{r['path']:52s} {str(r['arm']):3s} g{r['glu']!s:5} seed {r['seed']} sh {r['shuffle_seed']} n {r['n']:3d} uniq {r['n_unique']:3d} "
              f"[{r['seed_min']}..{r['seed_max']}] dt {r['dt_ms']} lm {r['lift_max']} net {r['net']} N {r['N']} W {str(r['W_sha'])[:8]} "
              f"Ws {str(r['W_sha_shuf'])[:8]} code {r['code']} b {f(r['birth'])} m {f(r['mtime'])}")
    else:
        print(f"{r['path']:52s} OTHER {r.get('top_keys')!s:.150}")
