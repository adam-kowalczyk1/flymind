# Preflight audit — PI synthesis (before pilot)

Line numbers `L…` refer to the baseline copy `archive/test_cx_working_memory_vs_kalman.py`
(sha256 f145bff8…bd6). Evidence files are in `preflight/`.

## 1. Causal path and what is biological

| Stage | Code | Classification |
|---|---|---|
| Camera render → FlyRetinaFilter → small-target blob detector (LC10-like), efference-shifted background | vision.py | biologically-inspired front end, hand-tuned thresholds |
| Blob ray ∩ table plane → world azimuth → minus `aim` azimuth → `cue_rel` | L485–498 | **engineered geometry** (uses camera pose from kinematics) |
| Software blanking of `cue_rel` during [0.5, 1.5) s | L501–502 | protocol |
| `cue_rel` → Gaussian current into EPG at the target's *egocentric bearing* | brain.py `inputs` | model input; the bump is re-interpreted as target bearing, not fly heading (see literature_matrix.md Q1, Q5) |
| EPG/PEN/Delta7/PFL3 recurrent weights | brain.py | connectome-derived **profiles** (mean synapse count vs phase), idealised equal spacing, Delta7 inhibition ×8, Delta7→Delta7 ×0.3 — biologically constrained but hand-scaled |
| Self-rotation → PEN L/R asymmetric current `u_for(-w_base)` | L344–346, brain.py `u_for` | biologically-inspired pathway; gain is an **engineered lookup** inverting the measured bump-velocity curve (`calibrate_ring`), w_base from joint velocity (proprioception) |
| PFL3 goal input `cos(θ − goal ± 45°)`, goal = 0 | brain.py | **model input** (FC2 not in subset), goal fixed |
| PFL3 → DNa02 (crossed) | brain.py | connectome synapse counts |
| PFL3 → DNa01 | brain.py | **engineered copy** of the DNa02 path (no data edges) |
| DN L−R rate → exp. filter (0.1/0.4 s) → `(dn − offset)/slope` → mean → ×2.5 | L357–388 | **engineered linear decoder + P gain**; offsets/slopes from `calibrate_steer` regression (separate visual vs memory calibrations) |
| ω → STS3215 position target with anti-windup clamp | L98–109 | engineered actuator layer |
| Hybrid: target angular velocity from `np.polyfit` over 0.6 s of world bearings, fed into PEN as `tv − w_base` | L333–343 | **classical estimator** outside the SNN; the ring only integrates it |

Net: the SNN contributes a recurrent bump that (a) is pushed by the visual cue, (b) is rotated by an externally supplied,
calibrated self-motion signal, and (c) is read out through PFL3/DN and an engineered linear decoder into a P-controller.
Persistence of the bump during occlusion is the genuinely network-dependent component; everything mapping it to and from
the world is engineered.

## 2. Leakage
`true_rel_az` (L489) and `ball_az` are only used in the metric blocks (L529–547). Controllers receive `cue_rel` (None when
masked), `aim_az` (gripper kinematics) and `w_base` (joint velocity). LastObs/Kalman use `aim_az` to form a world-frame
memory; BIO uses `w_base` to rotate an egocentric bump. Both are proprioception; the baselines get *position*
(drift-free) while BIO must integrate velocity — a mild information asymmetry favouring the baselines. No target-state
leakage found.

## 3. Metrics
- `e_reappear` = wrap(ball_az − aim_az) at the first step with d.time ≥ t_reappear, measured before the controller acts on
  the re-visible cue. Because d.time accumulates just below multiples of 0.01, this is t = 1.51 s and the masked window is
  101 steps (schema_check.jsonl: `n_occluded_steps` = 101, `t_reappear_actual` = 1.51). Identical for all arms.
- Sign: + = target left of gripper. Units deg.
- `t_reacquire`: time at the END of a 10-step (100 ms) in-band run, so its floor is 0.09–0.10 s; band ±5° is narrower than
  the steady visible tracking lag (6–9° in seed-100 traces, P-control on a ramp plus ~2° visual-latency bias), so it is
  mostly undefined. Ill-posed for a moving target; not used for decisions.
- `j_ctrl` = Σ ω²·dt over masked steps (rad²/s). Zero means a genuinely zero command for the whole window (Freeze arms,
  degenerate Shuffle), not an uncomputed value.
- `e_ring` = wrap(true_rel − bump); meaningless when the ring is silent (bump angle defaults to 0) → now gated on recorded
  coherence.
- Statuses: DEGENERATE_CALIBRATION is set before the loop and CONTROL_FAILURE only overwrites SUCCESS (L536), so it is
  never overwritten; TECHNICAL_FAILURE can overwrite any status on exception (L549–551).

## 4. BIO-Shuffle
Verified (check_shuffle_s100.txt): within-projection permutation preserves weight multisets and sign; non-CX weights
untouched; ring-phase structure destroyed. The shuffled ring is silent (0 Hz EPG) → `calibrate_ring` flat → `u_for` = 1.0
for all ω; `slope_mem` = [0, 0] (minimum-norm least squares with an all-zero regressor). Visual slope 1.6 vs 15.9 Hz/rad
intact → visual steering is ~10× over-gained and bang-bang. In seed 100 the arm was steered the wrong way while visible,
then held still during occlusion while the ball drifted across the aim line → |e| = 1.9° (best of all arms) and
t_reacquire = 0.10 s. Status DEGENERATE_CALIBRATION is retained.
Verdict: valid manipulation outcome (the attractor genuinely disappears) **and** a calibration/readout artefact (zero
command, misleading endpoint). It is a broken-controller control, not a memory-specific one. It must be excluded from
comparative endpoint tables and reported descriptively.

## 5. Construct validity (most important)
The ball moves ~11–16°/s in azimuth; during 1 s of occlusion it moves ~14° (seed 100). A perfect *static* memory
(BIO-Static, LastObs-PD) therefore has |e| ≈ target displacement ≫ 3° margin, and a controller that simply freezes has
|e| ≈ |e_onset + Δball|. In seed 100 the freeze arms beat their parents (LastObs 14.8 vs freeze 12.9; BIO-Static 14.0 vs
BIO-Static-Freeze 6.8) — single seed, preflight only. The NI comparison BIO-Static vs LastObs-PD can therefore "pass"
without any working memory being demonstrated. Freeze-Null arms were added (stats_plan.md §9) to test this on the pilot.

## 6. Reproducibility
RNG sources: scene `default_rng(seed)` (y0, vy); `ConnectomeSNN.rng = default_rng(seed)` consumed first by calibration
then by the trial (never reset by `Brain.reset`); shuffle `default_rng(seed)` (independent object, same seed). MuJoCo and
the renderer are deterministic on this machine: two independent processes gave bit-identical `e_reappear` for LastObs-PD
and BIO-Static seed 100 (and again in schema_check.jsonl). This does not prove determinism across machines/library versions.

## 7. Changes made (experimental script only)
See `git_integrity_final.txt` and `script_changes.diff`. Added: `--run-pilot` (resumable JSONL, never overwrites,
refuses seeds 0–39 without `--allow-heldout`, records infrastructure exceptions); two Freeze-Diag diagnostic variants;
recorded `e_onset`, onset/reappear azimuths, bump angle/coherence, `t_reappear_actual`, `n_occluded_steps`, steering
calibration; `k = -1` guard. No change to controllers, gains, endpoint definitions or primary variants' behaviour
(seed-100 values bit-identical before/after edit).
