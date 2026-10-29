# Pilot gate decision (PI, after workstreams A–C and preflight)

| Check | Result | Evidence |
|---|---|---|
| Target-state leakage | PASS — none found (PI + Agent B independently) | preflight_audit.md §2; code_audit_agentB.md |
| Endpoint computed identically across arms | PASS (101-step window, recorded at t = 1.51 s for all) | schema_check*.jsonl |
| Status handling: degenerate not counted as success | PASS in records; analysis excludes DEGENERATE from comparative tables | preflight_audit.md §3–4 |
| Runner exists, persists every attempt, resumable, held-out guard | PASS after fix (`--run-pilot`) | preflight/x.jsonl guard exit 1 |
| Determinism (exact reruns, same machine) | PASS (bit-identical, 3 reruns) | schema_check.jsonl vs schema_check2.jsonl vs single_*.txt |
| Edits leave primary behaviour unchanged | PASS (seed-100 values bit-identical before/after) | same |
| Construct validity of NI endpoint | **FAIL as a test of working memory** (freeze/null competitive; static memory penalised by target motion) | Agent B #1, preflight_audit.md §5 |

Decision: the *integrity* gate passes, so the pilot is run — as an exploratory study whose main question becomes
"does the CX memory add anything over freezing?", answered by the prespecified Freeze-Null arms (stats_plan.md §9).
The construct-validity failure is not fixable inside the permitted scope without redesigning the task (target speed /
direction / static-target condition), which would change the experiment, so it is carried forward as a limitation and
into the final status decision. Agents B and C both independently recommended null references; Agent C's decision
rule 5 makes the freeze comparison binding.

Run: seeds 100–129, t_occ = 1.0 s, t_total = CFG 3.5 s, 6 primary + 2 diagnostic arms = 240 trials, 3 independent
processes split by seed range (separate JSONL files, no shared mutable state; each trial builds its own scene and SNN).
