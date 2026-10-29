# Progress log — CX working-memory vs Kalman audit (run started 2026-10-27 16:30 local)

Output dir: bio2/results/cx_wm_audit_20261027_163059
Baseline: branch main @ 8f591242; tracked tree clean; 3 untracked scripts archived to archive/ (sha256 in git_integrity_initial.txt).

## Cycle 0 — change-control baseline
- Question: what is the starting state?
- Evidence: git_integrity_initial.txt; archive/ copies of the 3 untracked scripts (byte-identical copies, hashes recorded).
- Commands: git status --short (exit 0); shasum -a 256 (exit 0); cp (exit 0).
- Decision: proceed to code reading.
- Next: read experiment + brain.py; launch literature / audit / stats subagents.

## Cycle 1 — preflight: do the metrics and controls behave as intended?
- Question: is the experiment runnable, deterministic, and are e_reappear / t_reacquire / BIO-Shuffle meaningful?
- Commands (all exit 0): `.venv/bin/python test_cx_working_memory_vs_kalman.py --test-unit` (12/12 PASS);
  `--run-single-trial --variant {LastObs-PD,Kalman-PD,BIO-Static} --seed 100 --t-occ 1.0 --t-total 3.5`;
  `scripts/diag_trace.py {LastObs-PD,Kalman-PD,BIO-Static,BIO-Shuffle} 100` (monkeypatched logging, loop unmodified);
  `scripts/check_shuffle.py 100`. Outputs in preflight/.
  NOTE: system python lacks mujoco; the project venv /Users/admin/so101_fly_project/.venv must be used.
- Evidence:
  * Exact rerun reproducibility: LastObs-PD s100 e=-14.80413367811538 and BIO-Static s100 e=-14.009431157803865 identical
    in two independent processes each.
  * Target moves ~-14.7 deg in azimuth during the 1 s occlusion (trace LastObs s100: true_rel 0.97 -> -14.66 with arm ~still).
    => for any "hold" strategy e_reappear ~ e_onset - target displacement; memory content plays a small role.
  * t_reacquire = null for LastObs, Kalman, BIO-Static on s100: steady visible tracking lag is 6–9 deg (P-control on a
    ramp + ~2 deg visual-latency bias of the cue), never inside the 5 deg band. Metric ill-posed for a moving target.
  * BIO-Shuffle s100: status DEGENERATE_CALIBRATION retained (not overwritten), but e_reappear=-1.9 deg and t_reacquire=0.10 s
    are the BEST of all controllers — produced by zero command during occlusion while the ball drifted across the aim line
    after the broken visual phase had turned the arm the wrong way. Confirms "misleadingly small error" failure mode.
    e_ring == e_reappear because bump angle = angle(0) = 0 for a silent EPG population (meaningless).
  * Shuffle invariants: per-projection weight multisets & sign preserved, non-CX weights identical, ring-profile correlations
    destroyed (EPG->EPG 0.66 -> -0.01). Shuffled EPG is silent (0 Hz) even right after the cue; ring calib flat (u_for(0)=1.0);
    slope_mem=[0,0] (min-norm lstsq with all-zero regressor); visual slope 1.6 vs 15.9 Hz/rad intact -> visual steering ~10x
    over-gained, bang-bang. The shuffle therefore breaks visual steering as well as memory: it is a broken-controller control,
    not a memory-specific control.
  * Literature agent: 24 DOIs, all verified against Crossref titles by PI (curl api.crossref.org). Stats agent: plan written
    without seeing outcomes (stats_plan.md §7).
- Decision: (1) add a pilot runner (none exists); (2) add Freeze-Null diagnostics (LastObs-Freeze-Diag, BIO-Static-Freeze-Diag)
  so that "memory vs freeze" can be tested; (3) record e_onset, onset/reappear azimuths, bump coherence, calibration values.
  Do NOT change the t_reacquire definition (would be post hoc); report it as ill-posed.
- Next: implement within the experimental script only, unit-test, single-trial schema check.

## Cycle 2 — fix permitted defects; reconcile reviewers; gate
- Question: what minimal changes make the pipeline able to run and interpret the pilot?
- Evidence: Agent B (code_audit_agentB.md, 17 findings; 2 CRITICAL: freeze-equivalent endpoint, Shuffle = zero-command null)
  and Agent C (stats_plan.md) independently converged with PI preflight. PI verified B's claims: agent.py W_MAX = 1.0 vs 0.6
  here (agent.py:43); e_ring at reappear is read after 10 ms of returned cue (code order: ctl.step before metric block).
- Changes (bio2/test_cx_working_memory_vs_kalman.py only; script_changes.diff): --run-pilot runner; Freeze-Diag arms;
  diagnostic fields incl. e_ring_lastocc_deg and n_cue_seen_pre_onset; k=-1 guard.
- Commands: --test-unit exit 0 (twice); held-out guard exit 1 as intended; schema_check.jsonl / schema_check2.jsonl exit 0;
  seed-100 primary values bit-identical before/after edits.
- Decision: integrity gate PASS, construct validity FAIL → run pilot as exploratory with Freeze-Null (pilot_gate.md).
- Next: run 240 trials (raw/commands.txt), then analysis + red team.

## Cycle 3 — pilot execution + memory-specific open-loop probe
- Question: what do the 240 pilot trials show, and does the bump itself hold a bearing / integrate self-rotation?
- Commands: raw/commands.txt (3 processes, seeds 100-109 / 110-119 / 120-129, started 16:41 CET);
  scripts/openloop_memory_probe.py 100 109 raw/openloop_memory_probe.json (started in parallel, separate process,
  read-only w.r.t. the pilot; it constructs its own Brain instances).
- Rationale for the probe: Agent A Q7 / Agent B #1 — the closed-loop endpoint cannot isolate memory, so the bump's
  persistence (coherence), accuracy (error vs cued bearing) and self-motion integration (imposed w = ±0.3 rad/s) are
  measured directly; NoSelf and shuffled networks are the contrasts.
- Open-loop probe result (exit 0; analysis_openloop_probe.txt): intact bump persists for 2 s (coherence 0.80 throughout);
  shuffled ring silent (coherence 0.00). Memory ACCURACY is poor: w=0 mean |err| 9.0 / 11.7 / 14.3 / 20.5 deg at
  0.25 / 0.5 / 1.0 / 2.0 s, with a systematic +7…+15 deg drift and SD growing 8.9 -> 21.9 deg (diffusion-like).
  Self-motion integration via PEN works partially: at t = 1 s the spread of signed error between w = -0.3 and +0.3 is
  ~11 deg with self-motion input vs ~36 deg without (ideal no-compensation spread 34.4 deg) → roughly 70 % compensation,
  asymmetric (under-compensation for w = +0.3 grows to -23 deg relative at 2 s).
  => The network does hold a persistent, self-motion-updated bearing (qualitative WM criteria met in open loop), but its
  1-s error (~14 deg) is ~5x the 3 deg NI margin, so no closed-loop NI claim against kinematic baselines is plausible.
- Pilot result (exit 0, all 3 processes): 240/240 records, 0 missing, 0 duplicates, 0 TECHNICAL_FAILURE;
  BIO-Shuffle 30/30 DEGENERATE_CALIBRATION (slope_mem = 0, j_ctrl = 0 in all). analysis/analysis.md.

## Cycle 4 — analysis per prespecified plan, reproducibility, memory fidelity
- Commands (exit 0): scripts/analyze_pilot.py raw/pilot_*.jsonl analysis; 3 diagnostic reruns (seed 117: BIO-Hybrid,
  Kalman-PD, BIO-NoSelf) → raw/diagnostic_reruns.jsonl, bit-identical to pilot; 5 preflight seed-100 records bit-identical
  to pilot records. analysis/reruns_and_memory_fidelity.txt.
- Key evidence (D = |e_A| - |e_B|, deg, 95% t-CI):
  NI-1 BIO-Static - LastObs-PD +0.49 [-2.49, 3.47], one-sided upper 2.97 (<3 nominally) BUT
  freeze-BIO BIO-Static - BIO-Static-Freeze +4.80 [1.64, 7.95] (memory-driven commands worse than freezing);
  freeze-LastObs +1.72 [1.31, 2.13]; NI-2 BIO-Hybrid - Kalman-PD +7.29 [5.07, 9.51] (clearly not noninferior);
  mech-self BIO-Static - BIO-NoSelf -2.73 [-6.31, 0.84]; Kalman-PD - LastObs-PD -8.72 [-9.30, -8.13].
  Degenerate BIO-Shuffle mean |e| 10.96 (< BIO-Static 15.07) — artefact confirmed at n = 30.
  Closed-loop memory fidelity of BIO-Static bump vs ideal static memory: mean |err| 14.1 deg, SD 17.2 — agrees with the
  open-loop probe (14.3 deg at 1 s).
- Decision rules (stats_plan §7/§9): R1 pass; R2 fail (upper 9.14 > 5); R3 fail (s_delta·1.28 ≈ 7.6 → N ≈ 60+ at
  alpha 0.0125); R4 fail (Static vs NoSelf CI includes 0); R5 fail (BIO-Static-Freeze 10.27 beats every BIO arm).
- Next: independent red-team review, PI responses, final report.

## Cycle 5 — red-team review and corrections
- Evidence: red_team_review.md (+ PI responses); analysis/redteam_verification.txt; analysis/supplementary_analysis.txt
  (scripts/supplementary_analysis.py, exit 0).
- CORRECTIONS to earlier entries (original text left in place above for audit trail):
  * Cycle 3: "roughly 70 % compensation … under-compensation" is WRONG. Self-motion gain g ≈ 1.32 (SD 0.79):
    the PEN lookup over-compensates by ~30 %. "qualitative WM criteria met" → only the persistence criterion is met;
    no prespecified acceptance criteria, no non-neural comparator.
  * Cycle 4: "memory-driven commands worse than freezing" is a geometry artefact (onset-lag sign × fixed sweep direction),
    not a mechanism finding. "R3 … N ≈ 60+" is wrong: with NI-2 mean D 7.29 > 3, no N establishes noninferiority.
    The memory-fidelity BIO-Hybrid row is not meaningful; the 14° figure includes ~5° onset encoding error.
- Decision: final status STOP — PROTOCOL INVALID, with red-team dissent (PILOT INCONCLUSIVE) preserved and NI-2 stated as a
  clean negative.
- Next: final report, final git-integrity check. No further phases.
