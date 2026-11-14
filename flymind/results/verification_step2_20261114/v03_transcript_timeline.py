"""Weryfikacja kroku 2 — niezależna oś czasu z zapisów obu sesji Claude (tylko odczyt plików .jsonl).
Wypisuje znaczniki czasu wywołań narzędzi (Write/Edit/Bash) dotyczących plików celu, rejestru ziaren i uruchomień testów."""
import json, sys, os, re, datetime as dt
P = os.path.expanduser("~/.claude/projects/-Users-admin-so101-fly-project/")
S = {"B(369d1f0a, staw b)": "369d1f0a-b85f-4cbf-9a24-5e5edfc27370.jsonl", "A(e68121d3, c-e/ramię)": "e68121d3-f40f-49b7-b122-ab6098b3179c.jsonl"}
KEY = re.compile(sys.argv[1] if len(sys.argv) > 1 else r"LOOP_TARGET|CONFLICT_TARGET|SEED_REGISTRY|CALIBRATION|STEP2_FINAL_TEST|run_test\.sh|launch_test\.sh|run_dt01|launch_arm0|launch_conflict|2091000|20952001|kill |pkill|SIGSTOP|kill -STOP")
out = []
for name, fn in S.items():
    for line in open(P + fn):
        try:
            d = json.loads(line)
        except Exception:
            continue
        ts = d.get("timestamp")
        msg = d.get("message") or {}
        c = msg.get("content")
        if not isinstance(c, list):
            continue
        for b in c:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                inp = b.get("input") or {}
                txt = json.dumps(inp, ensure_ascii=False)
                if KEY.search(txt):
                    t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime("%d %H:%M:%S") if ts else "?"
                    short = inp.get("file_path") or inp.get("command") or txt
                    out.append((t, name, b.get("name"), short.replace("\n", " ⏎ ")[: int(sys.argv[2]) if len(sys.argv) > 2 else 260]))
for r in sorted(out):
    print(" | ".join(r))
