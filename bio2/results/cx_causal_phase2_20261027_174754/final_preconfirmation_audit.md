# Final pre-confirmation audit after repair (R1 + R2) — 2026-10-27

**Status: `READY FOR CONFIRMATION`.** Nothing was run on seeds 300–399 or 0–39, no hardware was used, and nothing was
committed.

## Evidence

All of the following are in `regression/`.

| Check | Result |
|---|---|
| Runner unit tests | PASS |
| Analysis synthetic tests | 54/54 PASS |
| Runner safety tests | 24/24 PASS. An earlier run (`runner_safety_tests_run1_FAIL.txt`) exposed a real bug, now fixed. |
| Behavioural regression | 10 A2 trials bit-identical to dev4; 2 v1 trials bit-identical to dev2 |
| Dev4 cross-check | S_DN, P2a, P2b, S_bump identical to `scripts/analyze_dev4.py` |
| Persistence check on real logged dev2 data | 8/8 trials pass |
| CLI refusals | correct |
| `final_consistency_checks.txt` | all frozen hashes match; the R2 runner's own manifest matches the frozen runner, CFG, dependency hashes and package versions; trial code and CFG values are identical to v3 |
| Production files | unchanged (`repair_integrity_final.txt`) |

The independent second audit (`second_audit_independent.md`) recommended READY, with one MAJOR and five minor findings.
All six were fixed in R2.

## Problems, fixes, tests, results

| Audit problem | Fix | Test | Result |
|---|---|---|---|
| No confirmatory analysis code (BCa, Wilcoxon, Holm, exclusions, stopping rules) | `analyze_cx_causal_confirmation.py` v1.0.0 | 54 synthetic checks; dev4 cross-check | PASS |
| Stage 1: 24 vs 40 seeds; blinded vs inference; effect-dependent stage 2 | v4 §5 / C1–C2: 24 seeds, blinded variance-only internal pilot; N_final = min(100, max(40, N_req at SD_UB)); one final analysis | stage-1 output contains no means, tests or verdicts | PASS |
| Positive control missing | 16 arms; E3 invalidates the experiment | E3 test | PASS |
| Holm families from v1 | F1 (m = 1), F2 (m = 2), F3 (m = 1), F1s (m = 3) | T1–T6 | PASS |
| Passive-rotation rule excluded every Δ = 0 trial | V5 conditional on Δ | C8 and V5 tests | PASS |
| §6(ii) required the demoted Q4 | Q4 descriptive; composite updated (C10) | text check | PASS |
| Resume mixed parameters, `--jump`, configurations | Manifest identity (runner, CFG, dependencies, versions, arms, Δ, jump); refusal on mismatch | λ, jump, arms, dataset_id, dependency tests | PASS |
| Truncated last line crashed the resume | Refuse by default; `--repair-truncated` keeps the original copy and writes a report; a corrupt middle line is always refused | 3 tests | PASS |
| Missing output directory | Created before any trial | C-dir test | PASS |
| Calibration exception lost | Recorded as TECHNICAL_FAILURE; non-CX arms continue (bug fixed in R1) | C-calibration test | PASS |
| No single-writer guarantee | O_EXCL lock; refusal if it is held | lock test | PASS |
| Second audit, MAJOR: dependencies not pinned | `deps_sha256` (24 files) and versions in the manifest and in V1 | dependency test; end-to-end manifest match | PASS |
| Second audit, minor: editable `stage1_decision.json` | Final mode recomputes stage 1 and checks the record hash | 2 tamper tests | PASS |
| Second audit, minor: a NaN `e_end` was not counted | V3 extended | V3 test | PASS |
| Second audit, minor: E2 stop at stage 1 not in the protocol | §5.7 | text | PASS |
| Second audit, minor: stale v1 command in REPRODUCE | Marked "SUPERSEDED — DO NOT RUN" | text check | PASS |

## Remaining limitations (not blockers)

- **Nothing is committed to git.** Integrity rests on the frozen hashes and the dependency pinning.
- **The lock does not survive a hard kill.** A stale lock must be removed by hand; the analysis would refuse any
  resulting duplicate records.
- **N_final will probably reach the cap of 100.** With the dev SDs, a 5° benefit is likely underpowered. This is stated
  in the protocol.
- **Self-motion gate.** On dev4, CX g = 0.80 with CI [0.19, 1.41], which would fail the gate. That is a property of
  the model, not a protocol defect.
- **The output directory `confirm/` will be created by the runner at the first run.**

## Incident

An archive command overwrote the v3 runner backup. It was reconstructed with a hash match and restored (progress log,
R2 start).

## Changed and new files

**Modified:**
- `bio2/test_cx_causal_memory.py` (v3 `55925009…` → R2 `e4556363…`)
- `confirmatory_protocol_v4.md` (new)
- `causal_protocol.md` and `hypotheses_and_thresholds.md` (SUPERSEDED banner only)
- `REPRODUCE.md`
- `implementation_plan.md`
- `progress_log.md`
- `frozen_runner_sha256.txt`

**New:**
- `bio2/analyze_cx_causal_confirmation.py`
- `bio2/test_analyze_cx_causal_confirmation.py`
- `bio2/test_cx_causal_runner_safety.py`
- `frozen_manifest_v4.json`
- `repair_integrity_initial.txt` and `repair_integrity_final.txt`
- `regression/*`
- `second_audit_independent.md` (written by the independent auditor)
- this file
- `archive/pre_repair_20261027_185611/`
- `archive/repair_r1/`
