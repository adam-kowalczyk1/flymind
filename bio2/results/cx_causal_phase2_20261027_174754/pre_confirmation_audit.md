# Pre-confirmation audit before stage 1 (read-only)

**Date:** 2026-10-27, about 18:45 CET.

**Scope.**
- Runner: `bio2/test_cx_causal_memory.py`.
- Protocol: `causal_protocol.md` v3 and `hypotheses_and_thresholds.md` §1–§11, including A2-8 and A2-9.
- Analysis scripts: `scripts/`.

**What was and was not done.**
- Nothing in the code, data, protocol or configuration was modified. The only new file is this one.
- Seeds 300–399 were not used.
- The tests below ran on development seed 233 only, plus the held-out guard (seed 5, refused before any simulation).
- Test output went to the session scratch directory
  `/private/tmp/claude-501/-Users-admin-so101-fly-project/f538d846-6794-404d-80e4-c9a1b0674de6/scratchpad/preconf_184715`,
  not to the report directory.

## Verdict up front

**`STOP — confirmatory analysis not implemented; protocol internally contradictory on stage 1 (blinding, size, positive control, validity rules); resume procedure not parameter-safe`.**

The runner itself is sound:
- the hash matches;
- there is no ground-truth leakage;
- parameters are consistent with dev;
- dev4 records reproduce exactly.

Starting stage 1 now would still produce data that cannot be analysed according to one unambiguous, prespecified rule.
Details and minimal remedies follow.

## 1. Runner SHA-256 vs `frozen_runner_sha256.txt` — PASS

- `shasum -a 256 bio2/test_cx_causal_memory.py` gives `55925009032146e6a06f85029c851e4a25b7097c921763c528967f74e663efc2`.
- This is identical to `frozen_runner_sha256.txt`.
- `git status`: the tracked tree is clean; the runner is untracked.

## 2. Does the stage-1 command run A2, 14 arms, Δ ∈ {−20, 0, +20}? — PASS with one defect

The command is in `causal_protocol.md:152`:
`--seeds 300-323 --arms <14> --passive=-20,0,20 --jump --out $O/confirm/expA2_stage1.jsonl`.

What passes:
- 14 arms, all unique, all defined in `ARMS`.
- The definitions match the protocol (checked by importing the module).
- `--jump` activates the A2 target jump.
- `--passive=-20,0,20` parses correctly; the `=` form is required.

Defects:
- **The positive control is missing.** `hypotheses_and_thresholds.md:54` (§5.4) says "Positive control S_scalar ≥ 20°,
  else the pipeline is broken (experiment TECHNICAL_FAILURE)". The arms `Scalar-Shift+30/−30` are **not** in the
  14-arm command. A2-8 #3 fixed the stage-1 list at those 14 arms without retracting §5.4. A mandatory check therefore
  cannot be computed.
- **The output directory does not exist.** `confirm/` is missing. Tested: a run whose `--out` directory is missing
  computes the first trial and then crashes with `FileNotFoundError` when writing it. That trial is lost; nothing is
  corrupted.
- **Older commands are still present.** `REPRODUCE.md:68` still contains the superseded v1 stage-1 command, labelled as
  superseded. Copying the wrong command would run v1.

## 3. Exclusions, completeness, seed aggregation, CIs, BCa, Wilcoxon, Holm vs the frozen protocol — FAIL

- **None of these rules is implemented in code.** `scripts/` contains `analyze_dev.py` and `analyze_dev4.py`, which
  give t-CIs only, plus three probes. A grep for `bootstrap|BCa`, `wilcoxon` and `holm` matches nothing. Nothing
  implements §7: the onset-identity tolerance, the realised-passive tolerance, degenerate calibration (`slope_mem < 7`,
  `|offset_mem| > 10`), complete-case pairing, and the 85 % / ≥ 20 minimum valid seeds.
- **The text rules contradict each other or are out of date for A2:**
  - **Holm families** (`:71`) are still the v1 sets: Q1 {S, +30 vs Sham, −30 vs Sham}, Q2 m=1. A2-1 made S_DN
    primary and S_bump a manipulation check. A2-2 made Q2 **two** co-primary contrasts (Δ=0 vs Freeze; ±20 vs
    SelfOnly). The families were never redefined.
  - **The realised-passive validity rule** (`:64`, "outside 17.35 ± 0.5° → TECHNICAL_FAILURE") is not conditional on
    Δ. Applied literally, it would exclude every Δ = 0 trial, where the realised rotation is ≈ 0°.
  - **The causal-memory criterion §6(ii)** (`:59`) still requires a "Q4 benefit ≥ 5° with CI excluding 0", but A2-8 #5
    demoted Q4 to descriptive.
  - **Onset identity.** §7 demands bit-identical onset, while A2-5 sets a 1e-3° tolerance. This one is consistent if
    A2-5 overrides §7, but it is not stated explicitly.
  - **Seed aggregation.** `causal_protocol.md:104` (§4) says "the two Δ conditions are averaged". A2 has three Δ values,
    and A2-1 averages over all three for S_DN. A2-2 uses Δ = 0 alone for one contrast and ±20 for the other. These are
    reconcilable, but there is no single statement of aggregation.

## 4. Does stage 1 compute only the permitted Q2/Q3 variability estimate (no means, tests or effect-based decisions)? — FAIL

The two documents disagree with each other:

| Source | Stage-1 seeds | What stage 1 computes |
|---|---|---|
| `:89` (§9) | 300–339 (N = 40) | "Compute only the SD of d for Q2/Q3 (no means, no tests) … No interim effect looks." |
| `:148–155` (A2-6) | 300–323 (N = 24) | Confirmatory inference for Q1 and rejection of "useful" for Q2, then: "If the stage-1 point estimate favours CX, stage 2 is sized from the stage-1 SD." |

- A2-6 is an **effect-based adaptive decision**, with no prespecified error control.
- A2-8 claims to supersede A2-6 only "where they conflict" and resolves only the arm count. Which of the two applies is
  undecided.
- No code computes a blinded, SD-only summary: a script that reports only the SD of the seed-level differences without
  their means. Any analysis run on stage-1 data with the existing scripts would print the means.

## 5. Resume safety — PARTIAL FAIL (tested on dev seed 233, scratch file)

| Test | Result |
|---|---|
| Rerunning the same command | 0 new trials, 2 lines unchanged. No duplicates, no overwrite. ✅ |
| Rerunning with a changed parameter (`--lambda-cx 0.5`) | Existing keys skipped, **new arms appended with λ_cx = 0.5 into the same file without warning.** File ends with `[('Scalar', 0.65), ('CX-DN-Pulse+30', 0.65), ('Freeze', 0.5)]`. ❌ |
| Rerunning without `--jump` | **v1 trials appended to the same A2 file** (`('Freeze', True), ('Freeze', False)`). ❌ |
| Truncated last line (simulated crash during write) | Resume aborts with `JSONDecodeError`. Recovery needs manual editing of the data file. ❌ |
| Missing output directory | First trial computed, then `FileNotFoundError`. ❌ |
| Brain calibration exception | `calibrated_brain(...)` is called **outside** the per-trial `try` (runner lines 434/436). It would abort the process with no record of the attempt. ❌ (by inspection) |
| Concurrent writers to one file | No lock; the resume key is read only at start, so duplicates are possible. Not tested. ⚠️ |

- **The resume key** is (arm, seed, Δ, ball_stop, jump). It does not include the runner hash or the CFG, and records
  carry neither (only K, t_occ, λ_self, λ_cx and jump).
- **TECHNICAL_FAILURE records are kept and never re-run** — good, matching "never silently replace".

## 6. No access to the true target position — PASS

Read at runner lines 189–310:

- **Ground truth** (`true_rel`, from `get_ball_azimuth`, line 210) is used only in `rec`
  (`e_end_deg`, `mem_err_end_deg`, lines 235–237), in snapshots (293) and in the log (305).
- **Controllers see only:**
  - `cue` (vision with ray–table geometry; masked during occlusion, line 242);
  - `w_base` / `w_mem` (joint velocity × λ_self, lines 196–197);
  - their own internal state.
- **Arm by arm:**
  - Scalar (line 273): the same `cue_in` and `w_mem`.
  - SelfOnly: no cue during memory.
  - CX-Bump and CX-DN (250–266): the cue enters EPG only while visible. Pulses are centred on the **bump** angle
    (`_last_bump`, 253–254), not on the target. Sham uses Δ = 0.
- **The onset rule** (213–232) uses only the cue.
- **The jump** (223–227) and ball stop (240–241) are experimenter manipulations of the scene, not controller inputs.
- The DN readout uses the memory calibration of the network (`dn_readout`); no ground truth.

## 7. Are the stopping rules and the NOT_CONVERGED / TECHNICAL_FAILURE / silent-bump handling implemented? — PARTIAL

**Implemented in the runner:**
- NOT_CONVERGED (230–232). This is a seed-level property: the visible phase is shared and CX arms do not influence
  motion.
- TECHNICAL_FAILURE on an exception (311–312), a non-finite command (287–289) or a missing reappearance (318–319).
- The silent-bump rule: coherence < 0.2 gives no estimate, so ω = 0 (266, 283), kept intention-to-treat. Coherence is
  logged per step only when the log is enabled. The stage-1 command does not use `--no-log`, so it is available.

**Not implemented anywhere:**
- the stopping rules "TECHNICAL_FAILURE > 10 % of seeds → stop" and "NOT_CONVERGED > 20 % → no inference";
- the validity exclusions of §7 (see §3 above);
- the counting of silent-ring trials.

The runner does not stop; these rules would have to be applied by the missing analysis.

## 8. Is the parameter freeze consistent with code and dev results? — PASS with minor issues

| Parameter | Code CFG | Documents |
|---|---|---|
| K | 2.5 | 2.5 |
| λ_self / λ_cx | 1.105 / 0.65 | 1.105 / 0.65 |
| coh_min | 0.2 | 0.2 |
| shuffle_frac | 0.2 | 0.2 |
| Pulse | 0.2 s at 0.7 s | 0.2 s at 0.7 s |
| Passive | 0.6 s from onset | 0.6 s from onset |
| t_occ | 2.0 | 2.0 |
| Onset rule | 1.0 s / 27 of 30 / 4 °/s / 2.2 s | same |
| jump_range / jump_vis | (10, 20)° / 0.2 s | (10, 20)° / 0.2 s |

- **Dev records match.** Dev2, dev3 and dev4 records carry λ = (1.105, 0.65), and dev4 records carry `jump = True`.
- **The current runner reproduces dev4 exactly.** Scalar and CX-DN-Pulse+30, seed 233, Δ = 0: `e_end`, `snaps` and
  `jump_deg` are identical to the dev4 records.
- **Unit tests pass.** The held-out guard refuses seed 5 (exit 1).

Minor issues:
- **A code comment contradicts the freeze.** Runner line 50 labels the jump parameters "(DEV, prowizoryczne)", i.e.
  provisional.
- **Some dev4 provenance is inferred.** dev4 ran before the hash was recorded, so "dev4 used exactly this file" is
  inferred from the edit sequence (progress log, cycles 6–7) and from the reproduction above. It is not proven for all
  216 records.
- **Records do not store their own provenance.** They contain neither the runner hash nor the full CFG.

## Minimal remedies before stage 1 (not applied; each is your decision)

1. **One protocol amendment, written before any stage-1 data.** It should:
   - choose a single stage-1 definition: either §9 (blinded, SD-only, N = 40, seeds 300–339) or A2-6 (24 seeds with
     inference), and delete the other; any effect-dependent stage-2 rule needs explicit error control or should be
     removed;
   - redefine the Holm families for A2;
   - make the realised-passive rule conditional on Δ;
   - reconcile §6(ii) with the demoted Q4;
   - state the seed-aggregation rule per contrast;
   - either add `Scalar-Shift±30` to the stage-1 command or retract §5.4.
2. **A frozen confirmatory analysis script, hashed before stage 1.** It should implement §7 exclusions, complete-case
   pairing, seed aggregation, t-CI, BCa (10 000, seed 20261027), Wilcoxon, Holm and the stopping rules. If stage 1 is
   blinded, it should include a blinded SD-only mode that prints no means. Test it on dev4 records only.
3. **Runner hardening, then re-freeze and a dev-seed regression.** These are code changes, so the hash will change:
   - record the runner sha256 and the full CFG in every record, and refuse to resume a file whose records differ;
   - tolerate or flag a truncated final line without editing data;
   - wrap brain calibration so that a failure is recorded as TECHNICAL_FAILURE;
   - create the output directory, or fail before computing anything;
   - document single-writer use.
4. **Housekeeping.** Remove "prowizoryczne" from the jump comment, and mark or remove the v1 command in `REPRODUCE.md`.

## Final status

**`STOP — confirmatory analysis not implemented; protocol internally contradictory on stage 1 (blinding, size, positive control, validity rules); resume procedure not parameter-safe`**

The runner itself passes items 1, 2 (structure), 6 and 8. Stage 1 was not started.
