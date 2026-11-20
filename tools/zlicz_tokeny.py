"""Ile tokenów wygenerowali agenci Claude Code przy projekcie (21 XI 2026). Czyta lokalne transkrypty ~/.claude/projects
(+ opcjonalnie rozpakowany backup: argument = folder z podfolderami projektów). Każda wiadomość API liczona RAZ globalnie
(forki/wznowienia kopiują historię do nowych plików — bez tego wynik jest zawyżony ~25 %).
Uruchom:  python3 tools/zlicz_tokeny.py [folder_backupu]
Zakres: cały folder repo -Users-admin-so101-fly-project + pliki z innych folderów, które wspominają „flymind”.
Koszt = ceny API z platform.claude.com z 21 XI 2026 (nie faktura: przy abonamencie płacisz abonament; nie sprawdza trybu fast).
NIE liczy: Codex/Cline/Gemini, sesji z innych urządzeń i z chmury, transkryptów już skasowanych."""
import collections, glob, json, os, sys

REPO = "-Users-admin-so101-fly-project"
roots = [os.path.expanduser("~/.claude/projects")] + sys.argv[1:]
seen = {}                                   # id wiadomości API → (usage, czy podagent)
for root in roots:
    for f in glob.glob(f"{root}/**/*.jsonl", recursive=True):
        rel = os.path.relpath(f, root)
        txt = open(f, errors="ignore").read()
        if not rel.startswith(REPO + "/") and "flymind" not in txt.lower():
            continue
        for line in txt.splitlines():
            try: o = json.loads(line)
            except Exception: continue
            m, u = o.get("message") or {}, (o.get("message") or {}).get("usage")
            if o.get("type") == "assistant" and u:
                seen[m.get("id") or o.get("uuid")] = (u, "/subagents/" in rel, m.get("model", ""))

def total(items):
    c = collections.Counter()
    for u, *_ in items:
        c["wyjście"] += u.get("output_tokens", 0)
        c["wejście świeże"] += u.get("input_tokens", 0)
        c["zapis do cache"] += u.get("cache_creation_input_tokens", 0)
        c["odczyt z cache"] += u.get("cache_read_input_tokens", 0)
    return c

# USD / mln tokenów: wyjście, świeże wejście, zapis 5 min, zapis 1 h, odczyt cache
CENY = {"opus": (20, 4, 5, 8, .2), "sonnet": (10, 2, 2.5, 4, .1), "fable": (40, 8, 10, 16, .2)}
HAIKU = ((.5, .1, .125, .2, .01), (2.5, .5, .625, 1, .05))      # prompt do 100 tys. / powyżej


def koszt(items):
    usd = collections.Counter()
    for u, _, model in items:
        cc, w1 = u.get("cache_creation") or {}, 0
        w1 = cc.get("ephemeral_1h_input_tokens", 0)
        w5 = u.get("cache_creation_input_tokens", 0) - w1
        n = (u.get("output_tokens", 0), u.get("input_tokens", 0), w5, w1, u.get("cache_read_input_tokens", 0))
        key = next((k for k in list(CENY) + ["haiku"] if k in model), None)
        if key is None:
            usd["nieznany model"] += 0
            continue
        c = CENY.get(key) or HAIKU[sum(n[1:]) > 100_000]
        usd[key] += sum(a * b for a, b in zip(n, c)) / 1e6
    return usd


for name, items in (("RAZEM", list(seen.values())), ("podagenci", [v for v in seen.values() if v[1]])):
    print(f"{name} ({len(items)} wywołań API):", {k: f"{v:,}" for k, v in total(items).items()})
    k = koszt(items)
    print("  koszt USD:", {a: round(b) for a, b in k.items()}, "razem", round(sum(k.values())))
