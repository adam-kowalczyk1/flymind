# Reproduction (phase 2)

## Environment

- Machine: Apple M1 Max.
- Python: the project venv, `/Users/admin/so101_fly_project/.venv/bin/python` (3.12.13), with mujoco 3.17.0, numpy
  2.5.4 and scipy 1.18.1. The system Python has no mujoco.
- Repository: `main` @ 8f591242. The new file `bio2/test_cx_causal_memory.py` has its frozen sha256 in
  `frozen_runner_sha256.txt`. No production file was modified (`git_integrity_final.txt`).

## Commands

Run every command from `/Users/admin/so101_fly_project/bio2`, with:

- `PY=/Users/admin/so101_fly_project/.venv/bin/python`
- `O=results/cx_causal_phase2_20261027_174754`

Unit tests (pure Python, no MuJoCo; they also check the held-out guard):

```bash
$PY test_cx_causal_memory.py --test-unit
```

The development runs used are listed exactly in `dev/commands.txt`, in order:

- **smoke 1/2:** seed 200.
- **dev1:** seeds 200–205, 13 arms, Δ ±20, run with λ = 1.0/1.0.
  - It was run before the λ CLI flags existed, so its records carry no λ fields.
  - The current code's defaults are the frozen values, so to reproduce dev1 add `--lambda-self 1.0 --lambda-cx 1.0`.
- **Exp B dev:** seeds 200–203.
- **dev2:** seeds 206–209, λ 1.105/0.65.
- **dev3:** seeds 210–229, CX-Bump only, frozen defaults.
- **jump smoke and dev4:** revised Exp A2, `--jump`, seeds 230–235, Δ −20/0/20, with 12 arms including SelfOnly and
  the CX-DN pulse arms.
  - Analysis: `scripts/analyze_dev4.py OUT.txt dev/expA2_dev4_*.jsonl`.
  - The v1 runner is archived as `archive/test_cx_causal_memory_frozen_v1.py`.

Example (one dev2 batch):

```bash
$PY test_cx_causal_memory.py --run --seeds 206,207 --arms Freeze,Scalar,CX-Bump,CX-Bump-NoSelf,CX-Sham,CX-Pulse+30,CX-Pulse-30 --passive=-20,20 --lambda-self 1.105 --lambda-cx 0.65 --out /tmp/dev2_check.jsonl
```

Pass negative values to `--passive` as `--passive=-20,20`. Argparse reads `--passive -20,20` as an option, which is why
the first dev1 attempt failed (logs kept as `dev/log_expA_*_failed_argparse.txt`).

Analysis:

```bash
$PY $O/scripts/analyze_dev.py /tmp/analysis_dev.txt $O/dev/expA_dev_200-201.jsonl $O/dev/expA_dev_202-203.jsonl $O/dev/expA_dev_204-205.jsonl $O/dev/expB_dev_200-203.jsonl
```

Probes:

- `scripts/probe_perturb_openloop.py 200,201,202,203,204 OUT.json`
- `scripts/probe_graded_shuffle.py 200,201,202 0,0.05,0.1,0.2,0.35,0.5 OUT.json`
- `scripts/probe_scene.py OUT.json`

## Confirmation run (NOT executed; prespecified)

The current, v3 stage-1 command is the one in `causal_protocol.md` §6: seeds 300–323, `--jump`, Δ −20/0/20. The
command below is the superseded v1 version.

Seeds 300–339 in stage 1, with all Exp A arms except CV and Δ ±20. Stage-2 sizing is in
`hypotheses_and_thresholds.md` §9.

**SUPERSEDED — DO NOT RUN.** This is the v1 command, kept for history only.

```bash
$PY test_cx_causal_memory.py --run --seeds 300-339 --arms Freeze,Scalar,CX-Bump,CX-Bump-NoSelf,CX-DN,CX-Reset,CX-Shuffle20,CX-Sham,CX-Pulse+30,CX-Pulse-30,Scalar-Shift+30,Scalar-Shift-30 --passive=-20,20 --out $O/confirm/expA_stage1.jsonl
```

## Determinism

- Repeated runs with the frozen defaults reproduced the dev2 records bit-identically (`tests/frozen_default_repro.txt`,
  `tests/frozen_default_repro2.txt`, `tests/regression_v2_nojump.txt`).
- However, in dev4 the onset state differed across arms by ≤ 1.2e-5° in 2 of 216 trials
  (`verify/dev4_onset_identity.txt`), so bit-identity is not guaranteed.
- This has been checked only on this machine.

## v4 (after the pre-confirmation repair, 2026-10-27)

The binding protocol is `confirmatory_protocol_v4.md`. All hashes are in `frozen_manifest_v4.json`.

Run these from `bio2/` with the project venv Python. Tests do not use seeds 300–399 or 0–39. The runner-safety test
uses dev seed 233 and temporary directories.

Runner unit tests:

```bash
python test_cx_causal_memory.py --test-unit
```

Analysis synthetic tests (54 checks; synthetic seeds 1300+):

```bash
python test_analyze_cx_causal_confirmation.py
```

Runner safety and regression (24 checks):

```bash
python test_cx_causal_runner_safety.py results/cx_causal_phase2_20261027_174754/dev
```

Dev cross-check (no verdicts):

```bash
python analyze_cx_causal_confirmation.py --mode dev --dev-files results/cx_causal_phase2_20261027_174754/dev/expA2_dev4_230-231.jsonl results/cx_causal_phase2_20261027_174754/dev/expA2_dev4_232-233.jsonl results/cx_causal_phase2_20261027_174754/dev/expA2_dev4_234-235.jsonl
```

The confirmation commands themselves (prespecified, not run) are in `confirmatory_protocol_v4.md` §6. The older
stage-1 commands in this file and in `causal_protocol.md` are superseded.

Results of the tests above are in `regression/`.
