# Confirmatory protocol v4 — Exp A2 (binding)

**Status:** BINDING, frozen 2026-10-27 before any confirmation seed was run.

This document **supersedes** `causal_protocol.md` (v3) and `hypotheses_and_thresholds.md` (§1–§11). Wherever they
disagree with this document, this document wins. The older files are kept unchanged as history; copies of the
pre-repair versions are in `archive/pre_repair_20261027_185611/`.

Exact identifiers:
- runner `bio2/test_cx_causal_memory.py`, with `PROTOCOL_VERSION = "v4"`;
- analysis `bio2/analyze_cx_causal_confirmation.py`, with `ANALYSIS_VERSION`;
- their SHA-256 values are in `frozen_manifest_v4.json`.

The scientific question is unchanged from v3:

> When sensory input disappears, does the persistent state of the intact CX network causally improve target-directed
> behaviour beyond a matched non-neural memory receiving exactly the same information?

## 1. Design (unchanged from v3 / A2 except where marked)

| Item | Value |
|---|---|
| Trial | Exp A2 (`causal_protocol.md` §1 and §6). Shared visible tracker; slow-tracking onset rule; target jump ±U(10, 20)° visible 0.2 s; occlusion 2.0 s with ball stopped; passive rotation over the first 0.6 s; memory phase after that. |
| Δ (passive rotation) | {−20°, 0°, +20°} nominal |
| Required arms (**16**, C3) | Freeze, Scalar, SelfOnly, CX-Bump, CX-Bump-NoSelf, CX-DN, CX-Sham, CX-Pulse+30, CX-Pulse-30, CX-DN-Sham, CX-DN-Pulse+30, CX-DN-Pulse-30, CX-Reset, CX-Shuffle20, **Scalar-Shift+30, Scalar-Shift-30** |
| Frozen CFG | exactly the runner's `CFG`, with no CLI overrides. Its SHA-256 is `cfg_sha256` in the manifest. |
| Flags | `--jump` on; ball stopped (`--moving` off) |
| Seeds | Stage 1: 300–323. Final: 300 … 299 + N_final (§5). Never 0–39. Development seeds 200–299 are never pooled with confirmation data. |
| Dataset | One JSONL file plus `<file>.manifest.json` written by the runner. Every record carries `dataset_id`, `protocol_version`, `runner_sha256` and `cfg_sha256`. |

## 2. Validity rules

Each rule acts at one of four levels: trial, seed, contrast or experiment.

| ID | Level | Condition | Consequence |
|---|---|---|---|
| V1 | dataset | The manifest is missing, or it differs from `frozen_manifest_v4.json` in protocol version, runner hash, `cfg_sha256`, **dependency hashes (`deps_sha256`: brain, snn, scene, vision, retina, the shared helpers, the connectome JSON, the MJCF model and its meshes) or package versions**; or a record's `runner_sha256`, `cfg_sha256`, `protocol_version` or `dataset_id` differs from it; or `jump` is not true; or `ball_stop` is not true; or an arm or Δ is not in §1; or a duplicate (arm, seed, Δ) exists; or a seed is outside the planned set. | **REFUSED.** The analysis does not run. |
| V2 | dataset | A planned (arm, seed, Δ) record is absent, meaning it was never attempted. | **REFUSED** as an incomplete dataset. Missing trials are never imputed. |
| V3 | trial | `status` is TECHNICAL_FAILURE, **or** `status` is OK without a finite `e_end_deg`. | Trial invalid; it counts toward E1 through its seed. |
| V4 | trial | Onset identity. \|onset true_rel − reference\| > 1e-3°, where the reference is Freeze for the same (seed, Δ), or the median over arms if Freeze is invalid. | Trial invalid (C9). |
| V5 | trial | Realised passive rotation. For Δ = ±20: the sign differs from Δ, or \|value\| is outside [16.85°, 17.85°]. For **Δ = 0: \|value\| > 0.5°**. | Trial invalid (C8). |
| V6 | seed | Every record of the seed is NOT_CONVERGED. | Seed NOT_CONVERGED: excluded and counted. |
| V7 | seed | Some records of the seed are NOT_CONVERGED and others are not. The visible phase is shared, so this is impossible if the runner is correct. | Seed TECHNICAL_FAILURE. |
| V8 | seed | Degenerate calibration of the intact network in any intact-network CX record: min(slope_mem) < 7, or any \|offset_mem\| > 10. | Seed TECHNICAL_FAILURE for all CX contrasts. |
| V9 | trial | Intact CX bump silent (coherence < 0.2, so ω = 0). | **Not excluded.** Kept intention-to-treat and counted (C12). |
| V10 | contrast | Complete case: a seed enters a contrast only if every (arm, Δ) trial the contrast needs is valid. | Excluded seeds are counted per contrast. |
| E1 | experiment | TECHNICAL_FAILURE seeds (V7, V8, or ≥ 1 invalid trial under V3–V5) exceed 10 % of planned seeds. | **EXPERIMENT TECHNICAL_FAILURE.** No hypothesis verdicts. |
| E2 | experiment | NOT_CONVERGED seeds exceed 20 % of planned seeds. | All primary verdicts are **INCONCLUSIVE**. |
| E3 | experiment | Positive control fails: mean over seeds of S_scalar = (e(Scalar-Shift−30) − e(Scalar-Shift+30))/2 (seed mean over Δ) is < 20°. | **EXPERIMENT TECHNICAL_FAILURE** (pipeline broken) (C3). |
| E4 | contrast | Valid seeds < max(20, ⌈0.85·N⌉), where N is the number of planned seeds. | That contrast is **INCONCLUSIVE**. |

## 3. Endpoints, families and decisions

**Notation.**
- d = paired seed-level difference, in degrees.
- |e| = |e_end| at reappearance.
- Seed value = the mean over the stated Δ set.
- The t-CI is the two-sided 95 % paired-t interval.
- Decisions use t-based one-sided tests at α = 0.025 after Holm adjustment within the family. A two-sided 95 % CI bound
  is used only when the family has m = 1.

### Primary family F1, m = 1 — Q1: does the CX state reach steering?

| | Definition |
|---|---|
| Statistic | S_DN = mean over Δ ∈ {−20, 0, +20} of (e(CX-DN-Pulse−30) − e(CX-DN-Pulse+30))/2. Predicted > 0. |
| Manipulation check (validity gate) | In the CX-DN pulse arms: median measured bump shift ≥ +15° for +30 and ≤ −15° for −30; \|median\| ≤ 5° for CX-DN-Sham; \|median coherence change\| ≤ 0.1. Failure → **INCONCLUSIVE** ("no manipulation"). |
| SUPPORTED | t-CI lower bound > 5°, **and** ≥ 80 % of seeds with S_DN > 0. |
| NEGATIVE | t-CI upper bound < 5°, **or** < 60 % of seeds with S_DN > 0. |
| Otherwise | **INCONCLUSIVE** (C5) |

### Primary family F2, Holm m = 2 — Q2: is the persistent state useful? (co-primary)

| | Definition |
|---|---|
| P2a | Δ = 0 only: d = \|e\|(CX-Bump) − \|e\|(Freeze) |
| P2b | Δ ∈ {−20, +20}, seed mean: d = \|e\|(CX-Bump) − \|e\|(SelfOnly) |
| Benefit test | For each contrast, H0: μ ≥ 0 against H1: μ < 0. One-sided t; the two p-values are Holm-adjusted. |
| No-meaningful-benefit test | For each contrast, H0: μ ≤ −3 against H1: μ > −3. One-sided t; the two p-values are Holm-adjusted. |
| SUPPORTED ("useful") | Both benefit tests reject (Holm, α 0.025), **and** both point estimates are ≤ −3°. |
| NEGATIVE ("useless or harmful") | At least one no-meaningful-benefit test rejects (Holm, α 0.025). |
| Otherwise | **INCONCLUSIVE** (C6) |
| Self-motion gate (P2b only) | CX-Bump g, seed mean over ±20: point in [0.75, 1.25] **and** t-CI within [0.6, 1.5]. If it fails, P2b counts as INCONCLUSIVE ("miscalibrated"). Q2 then **cannot** be SUPPORTED, but P2a can still produce NEGATIVE. P2a is exempt from the gate (A2-8 #2). |
| Persistence check (label only) | ≥ 90 % of valid CX-Bump trials must have memory-phase coherence mean ≥ 0.6 and min ≥ 0.4. If not, the verdict is labelled "persistence check failed". It is kept intention-to-treat and not changed. |

### Primary family F3, m = 1 — Q3: is the CX non-inferior to the matched scalar?

| | Definition |
|---|---|
| Contrast | d = \|e\|(CX-Bump) − \|e\|(Scalar), seed mean over all three Δ (C7). Margin 5°. |
| SUPPORTED (non-inferior) | t-CI upper bound < 5°. |
| NEGATIVE (inferior) | t-CI lower bound > 5°. |
| Otherwise | **INCONCLUSIVE** |
| Self-motion gate | The P2b gate applies. If it fails, Q3 is INCONCLUSIVE ("miscalibrated"). |

### Robustness of every primary verdict

Each verdict is recomputed with BCa bootstrap bounds in place of the t bounds: 10 000 resamples of seeds, RNG seed
20261027, at the same confidence levels. If the t-based and BCa-based categories differ, the reported category is
**INCONCLUSIVE (fragile)** (C14). For F2, the BCa counterpart of the Holm one-sided tests is the two-sided 97.5 % BCa
interval for each contrast. This is a Bonferroni stand-in, more conservative than Holm: benefit if the upper bound is < 0;
no meaningful benefit if the lower bound is > −3. If a required BCa interval cannot be computed (degenerate data), the
verdict is **INCONCLUSIVE (BCa not computable)**.

The Wilcoxon signed-rank test is reported as sensitivity only and never changes a verdict.

### Secondary family F1s, Holm m = 3 (reported; no decision role)

- CX-DN-Pulse+30 − CX-DN-Sham (predicted < 0);
- CX-DN-Pulse−30 − CX-DN-Sham (predicted > 0);
- S_bump > 5° (bump-readout version of Q1). This is close to an identity by construction.

All are seed means over the three Δ, with two-sided t tests (one-sided for S_bump).

### Secondary, unadjusted (reported)

- Memory-content test, within Δ (A2-8 #1): slope ≤ −0.5 with CI excluding 0, and r ≤ −0.5. Reported for CX-Bump,
  CX-DN and Scalar.
- The self-motion gain g, with its CI.
- The positive control value S_scalar.

### Descriptive only (no tests, no verdicts)

- **Q4:** CX-Bump vs CX-Bump-NoSelf, and CX-Bump-NoSelf vs Freeze (C10).
- CX-DN vs Freeze.
- The "no-ring" row: CX-Reset and CX-Shuffle20 vs Freeze, maximum |difference|.
- Signed e_end, offset-removed |e|, memory-estimate error at reappearance, coherence statistics, silent-bump counts.
- **The "causal memory" composite**, formerly §6. It now requires (i) Q1 SUPPORTED, (ii) the self-motion gate passed,
  and (iii) the 95 % t-CI upper bound of the CX-Bump memory-estimate error, averaged over all Δ, below 17.3°. It is
  reported as a descriptive summary only. It **no longer** requires a Q4 benefit, because Q4 is descriptive (C10).

There are no tests across families. Q1, Q2 and Q3 are distinct claims and each is reported separately.

## 4. Verdict vocabulary

| Level | Possible values |
|---|---|
| Each primary question | SUPPORTED, NEGATIVE, INCONCLUSIVE (with reason) |
| Whole experiment | REFUSED (V1, V2), EXPERIMENT TECHNICAL_FAILURE (E1, E3), or the per-question verdicts |

No verdict may be produced from development seeds.

## 5. Stage 1 and final sample size (C1, C2)

1. **Stage 1 is a blinded internal pilot.**
   - Seeds 300–323, all 16 arms × 3 Δ.
   - The analysis script runs in `--mode stage1` and prints only:
     - validity counts and the E1, E2 and E3 conditions as PASS/FAIL, without the S_scalar value;
     - the SDs of the seed-level statistics S_DN, P2a, P2b and P3, with each SD's one-sided 80 % upper confidence
       bound SD_UB = SD·√((n−1)/χ²₀.₂₀,ₙ₋₁);
     - each required N;
     - N_final.
   - It prints **no means, no effect estimates and no tests**. Its output is saved as `stage1_decision.json`.
2. **Required N per contrast.**
   - Exact paired-t power via the noncentral t distribution, two-sided α = 0.0125, power 0.90, with SD_UB.
   - The effect sizes δ are: Q1 δ = 10° (a true 15° against the 5° threshold); P2a, P2b and P3 δ = 5°. For P3 the
     true difference is assumed to be 0 and the margin is 5°.
   - **N_final = min(100, max(40, N_Q1, N_P2a, N_P2b, N_P3)).**
3. **Continuation.** Seeds 324 … 299 + N_final are run into the **same dataset**, with the same manifest.
4. **Final analysis.** It runs exactly once, in `--mode final`, on seeds 300 … 299 + N_final, and requires
   `stage1_decision.json`. There are no interim looks at effects. Stage-1 seeds are included in the final analysis, as
   in a standard internal pilot.
5. **If N_final = 100 (the cap).** The experiment may be underpowered for a 5° benefit. This is stated in advance. It
   can still return NEGATIVE.
6. **If stage 1 triggers E1 or E3.** The experiment stops as TECHNICAL_FAILURE, with no continuation.
7. **If stage 1 triggers E2** (NOT_CONVERGED > 20 %). The experiment stops: under E2 every primary verdict would be
   INCONCLUSIVE, so continuing cannot produce a verdict.
8. **Tamper protection.** `stage1_decision.json` records `stage1_records_sha256`. `--mode final` recomputes stage 1
   from the seed-300–323 records of the same dataset and **refuses** if `n_final` or the record hash differs, or if
   stage 1 ordered STOP.

## 6. Commands (prespecified; not executed)

Run every command from `bio2/`. Use the project venv Python. Each command writes into
`results/cx_causal_phase2_20261027_174754/confirm/`.

```bash
python test_cx_causal_memory.py --run --seeds 300-323 --arms Freeze,Scalar,SelfOnly,CX-Bump,CX-Bump-NoSelf,CX-DN,CX-Sham,CX-Pulse+30,CX-Pulse-30,CX-DN-Sham,CX-DN-Pulse+30,CX-DN-Pulse-30,CX-Reset,CX-Shuffle20,Scalar-Shift+30,Scalar-Shift-30 --passive=-20,0,20 --jump --out results/cx_causal_phase2_20261027_174754/confirm/expA2_confirm.jsonl --dataset-id CX-A2-CONFIRM-v4
```

```bash
python analyze_cx_causal_confirmation.py --mode stage1 --data results/cx_causal_phase2_20261027_174754/confirm/expA2_confirm.jsonl --out results/cx_causal_phase2_20261027_174754/confirm/stage1_decision.json
```

Then repeat the first command with `--seeds 324-<299+N_final>` and the same `--out`, `--dataset-id` and arms. If
N_final is 24 or fewer, no continuation is needed; by the formula N_final is at least 40.

```bash
python analyze_cx_causal_confirmation.py --mode final --data results/cx_causal_phase2_20261027_174754/confirm/expA2_confirm.jsonl --stage1-decision results/cx_causal_phase2_20261027_174754/confirm/stage1_decision.json --out results/cx_causal_phase2_20261027_174754/confirm/final_analysis.json
```

Rules for these commands:
- Run a single writer per dataset; a lock enforces it.
- Do not pass `--lambda-*` overrides. The manifest would record them, and the analysis would REFUSE a dataset whose
  `cfg_sha256` differs from `frozen_manifest_v4.json`.
- Logs are required, so do not pass `--no-log`.

## 7. Change history (v3 → v4) with justification

| ID | Change | Justification |
|---|---|---|
| C1 | Stage 1 = seeds 300–323 (24), **blinded variance-only**. The A2-6 rule "if the stage-1 point estimate favours CX…" and A2-6's stage-1 inference are **deleted**. | A2-6 was an effect-dependent interim decision with no error control; §9 required "no interim effect looks". Blinding is the statistically conservative choice: re-estimating sample size from the variance alone keeps the type I error near nominal (Wittes & Brittain 1990, an internal-pilot design; cited from general knowledge, not re-verified here). 24 seeds are kept from the A2 command, which matches the existing plan; the precision loss relative to 40 is offset by using SD_UB and the floor of 40 (C2). |
| C2 | N_final = min(100, max(40, …)). The SD is replaced by its 80 % upper bound. N_Q1 and both Q2 co-primaries are added. α 0.0125 two-sided and power 0.90 are kept from §9. | The §9 floor (40), cap (100), α and power are unchanged. The upper bound and the extra contrasts can only increase N, which is conservative. |
| C3 | Scalar-Shift±30 restored, giving 16 arms. E3 makes it experiment-invalidating. A2-8 #3 is superseded. | §5.4 required the positive control, but the stage-1 command had dropped it, which was audit blocker 2. |
| C4 | Holm families redefined for A2: F1 (m = 1), F2 (m = 2), F3 (m = 1), F1s (m = 3). | The §8 families were for v1 (the bump readout, and Q2 with m = 1). |
| C5 | In Q1, "CI lower ≤ 0 ⇒ reject" is replaced by INCONCLUSIVE. NEGATIVE is now upper < 5 or < 60 % positive seeds. | A CI that spans both 0 and 5 is imprecision, not evidence against the claim. Labelling it NEGATIVE would be an unsupported claim. |
| C6 | Q2 rules are rewritten as explicit one-sided tests with Holm. "Useful" is an intersection-union rule over both contrasts. | A2-2 stated them as CI bounds without a multiplicity rule. The thresholds (0° and −3°) are unchanged. |
| C7 | Q3 uses the seed mean over all three Δ and is gated by the self-motion gate. | A2-3 reported Δ = 0 and ±20 separately without naming the primary. Using all Δ uses all data, and the gate keeps a miscalibrated network from producing a verdict. |
| C8 | The realised-passive validity rule is conditional on Δ (Δ = 0: \|value\| ≤ 0.5°). | Applied literally, the old rule would have excluded every Δ = 0 trial (audit §3). |
| C9 | Onset identity: tolerance 1e-3° (A2-5), replacing "bit-identical" (§7). | Dev4 showed differences of ≤ 1.2e-5°, consistent with renderer nondeterminism. |
| C10 | Q4 is descriptive only. The §6 composite no longer requires a Q4 benefit. | A2-8 #5 had demoted Q4, but §6(ii) still required it. |
| C11 | Dataset manifest; provenance fields on every record; REFUSED on mismatch. | Audit blocker 5: resume previously mixed configurations silently. |
| C12 | A silent intact bump is kept intention-to-treat and counted (unchanged), and stated as V9. | Clarification only. |
| C13 | An absent planned record means REFUSED. Complete-case is applied per contrast. | No imputation, and no silent dropping. |
| C14 | If the BCa-based and t-based verdicts differ, the result is INCONCLUSIVE (fragile). F2 uses Bonferroni 97.5 % BCa intervals. If the BCa interval cannot be computed, the result is INCONCLUSIVE. | This makes §8's "conservative reading stands" operational. |
| C15 | Development data are analysed only in `--mode dev`, which produces no verdicts. | This enforces §4: no verdicts from development seeds. |
| C16 (R2) | Dependency hashes and package versions are part of the dataset identity (runner manifest) and of V1 (analysis). | Second audit, MAJOR finding: a changed `brain.py`, scene or connectome between stage 1 and continuation would otherwise mix configurations silently. |
| C17 (R2) | An OK record without a finite `e_end` is an invalid trial (V3) and is counted. | Second audit, minor finding: it was previously dropped from the contrast without being counted toward E1. |
| C18 (R2) | Final mode recomputes stage 1 and checks `n_final` and the stage-1 record hash. | Second audit, minor finding: a hand-edited `stage1_decision.json` could otherwise allow an unblinded look at 24 seeds. |
| C19 (R2) | E2 at stage 1 stops the experiment (§5.7). | Second audit, minor finding: the code stopped on E2 but the protocol did not say so. |
