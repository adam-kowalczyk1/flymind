# Reproduction

Environment (preflight/env.txt): Apple M1 Max, macOS (Darwin 27.2), Python 3.12.13 from the project venv
`/Users/admin/so101_fly_project/.venv`, mujoco 3.17.0, numpy 2.5.4, scipy 1.18.1. The system `python` has no mujoco.
Repository: main @ 8f591242 plus the edits to `bio2/test_cx_working_memory_vs_kalman.py` in `script_changes.diff`
(the edited file's sha256 is in `git_integrity_final.txt`).

All commands from `/Users/admin/so101_fly_project/bio2`, with `PY=/Users/admin/so101_fly_project/.venv/bin/python`
and `OUT=results/cx_wm_audit_20261027_163059`:

```bash
$PY test_cx_working_memory_vs_kalman.py --test-unit
```

```bash
$PY test_cx_working_memory_vs_kalman.py --run-pilot --seeds 100-129 --t-occ 1.0 --variants BIO-Static,BIO-Hybrid,BIO-NoSelf,BIO-Shuffle,LastObs-PD,Kalman-PD,LastObs-Freeze-Diag,BIO-Static-Freeze-Diag --out /tmp/pilot_repro.jsonl
```

(The pilot was run as three processes split by seed range — `raw/commands.txt`; split and order do not matter because each
trial builds its own scene, SNN and RNGs from the seed. About 11 s per BIO trial and 2 s per baseline trial on this machine.
The runner skips (variant, seed, t_occ) keys already in `--out`, so an interrupted run resumes; it refuses seeds 0–39
unless `--allow-heldout` is passed.)

```bash
$PY $OUT/scripts/analyze_pilot.py $OUT/raw/pilot_100-109.jsonl $OUT/raw/pilot_110-119.jsonl $OUT/raw/pilot_120-129.jsonl $OUT/analysis
```

```bash
$PY $OUT/scripts/openloop_memory_probe.py 100 109 /tmp/openloop_probe.json
```

Diagnostics: `scripts/diag_trace.py VARIANT SEED` (per-step trace through monkeypatched logging; loop unmodified),
`scripts/check_shuffle.py SEED` (shuffle invariants).

Determinism has been verified only on this machine and library set (bit-identical reruns of 8 records). Cross-platform or
cross-version determinism is not claimed.
