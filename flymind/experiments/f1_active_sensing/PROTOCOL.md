# FLYMIND F1 — Stage 0 (open loop) active-sensing protocol, r3.2

r3 = r2 + the fixes of red-team round 2 (`redteam/protocol_r2_redteam.md`, PASS_WITH_FIXES); changes listed in §12.

Frozen before any pilot or confirmatory run. r1 was rejected by red team (`redteam/protocol_r1_redteam.md`, verdict FAIL:
rung aliasing against a sharp threshold, unfair jitter peaks, too few jitter realisations, phase×instance confounding, TH threshold not
matched, S5 across unrelated ladders, wrong collision regex); every finding is answered in §11. Machine parameters: `protocol.json`.
sha256 of THIS file and of protocol.json are recorded in `manifest.json`; the runner refuses to start if either differs.
Everything here is about a MODEL (ALIF network on MaleCNS-derived wiring + engineering encoder), never about Drosophila.

## 1. Question
Does a small, self-generated, known rotation of a virtual camera (robot static) improve LEFT/RIGHT reports of a weak stationary
target, and is any benefit specific to sinusoidal motion, to the SNN (vs a memoryless threshold or a linear P read-out), and to the
data-derived wiring (DATA vs B1 vs SWS)?
Scope statement: in this pipeline (no efference copy, no parallax for a pure rotation) camera rotation and target motion with the same
retinal bearing are indistinguishable except for background/gripper image motion. Stage 0 therefore tests the sensory consequence of
self-generated image motion; a moving-target control (MT) checks that background motion plays no role.

## 2. Stimuli (ENGINEERING, MuJoCo)
Scene `so101.SO101Sim()` (default), arm at loop.Q_POSE, physics never stepped. Target = scene ball placed by
`loop.place_ball(sim, az0[rad], rho)` with centre z = radius; contrast k: rgb = 0.75 + k·(default − 0.75); radius via in-memory
geom_size and geom_rbound. All changes on the in-memory model only.
Per unit u, `rng = default_rng([u, 2])` draws, in this order: rho_u ~ U(range_D.rho), |az|_u ~ U(abs_az), k_u ~ U(range_C.k),
φ_u ~ U[0, 2π). Every condition of the unit uses the same values (paired); left target az = +|az|_u, right = −|az|_u.
- Range D (SNN operating range): k 1, rho ∈ [0.22, 0.36] m (wider than the 0.26–0.34 m starting range so that every condition's
  threshold is inside it; probe: 0.26 m ≈ 6.0 mV ipsi drive, threshold ≈ 6 mV).
- Range C (P operating range): rho 0.30 m, k ∈ [0.04, 0.24] (probe: P at ceiling from k ≈ 0.2; encoder pixel threshold near k 0.13).
- No target: ball parked out of view, same motion as the unit.
- Sensor noise (EXPERIMENTAL ASSUMPTION, shared by every system): N(0, σ 10) per pixel, channel and frame, `default_rng([u, 1])`,
  rounded to int16, one array [300, 96, 128, 3] per unit reused for all its trials; added to the uint8 render, clipped to [0, 255].
- The scene is not mirror-symmetric (camera roll ≈ 2.3°, directional light, checker floor): reported (hit_L, hit_R), not corrected.

## 3. Motion (Stage 0 = virtual camera, implementation A only)
Pure rotation of the camera about the world vertical through its optical centre (cam_quat of the in-memory model; position
unchanged). θ > 0 = camera turned left; true bearing = az0 − θ. 300 frames at 10 ms; analysis window = frames 100–299 (1–3 s).
- stat: θ ≡ 0.   sin(f, A): θ = A·sin(2πft + φ_u), f ∈ {0.5, 1, 2, 4} Hz, A ∈ {0.5, 1, 2, 4}° (window = whole cycles; 100 Hz frames
  ⇒ ≥ 25 samples/cycle).
- J_shuf(A): the sin(f*, A) trajectory of the unit with frames randomly permuted within the window and within the pre-window
  (`default_rng([u, 3, c])`): identical θ distribution (same peaks, same RMS, zero window mean), temporal structure destroyed.
- J_rms(A): i.i.d. Gaussian θ, then window mean removed and scaled to window RMS A/√2 (pre-window scaled by the same factor). Peaks
  exceed A (reported).
- J_vel(f, A): white noise convolved with a Gaussian kernel σ_t = 1/(2√2πf); window mean removed; scaled to window RMS A/√2; accepted
  if the window RMS velocity is within ±20 % of 2πf·A/√2, else redrawn from the same rng (≤ 1000 draws; draws recorded).
- MT(f*, A*) moving-target control: camera static; ball moved each frame on the horizontal circle of radius rho_u around the camera
  so its true bearing = az0 − θ(t) of sin(f*, A*). Same retinal bearing as camera rotation, static background/gripper.
- Every jitter realisation is unique per (unit, condition). Recorded per frame for one stimulus of each job: θ, θ̇, θ̈ (np.gradient),
  camera position and rotation used for rendering, true bearing, ball world position.

## 4. Pipeline and systems
image + noise → `encoder.TargetEncoder(loop.ENC)` (frozen) → g_L, g_R per frame; g streams and LIN streams are stored per trial.
- SNN (MODEL): current 12·g_s to all LC10a of side s held 10 ms (= encoder.currents) → `alif.ALIF(spec, loop.P, seed u)` fresh per
  trial on `visual_path.network(0.2)`; D = #DNa02_L − #DNa02_R spikes in the window. Same sign as the motor decoder (L − R > 0 ⇒ left);
  `decoder.SteerDecoder` is not used. Networks: DATA; B1 = `block_shuffle(spec, layer_side_labels, s, "LCxLC")`; SWS =
  `shuffle_within_side(spec, layer_side_labels, s)`; unit u uses instance (u − first unit) mod n_instances (phases are continuous and
  random, so no phase×instance aliasing).
- P (ENGINEERING, = loop.py classical_p filter): p ← a·p + (1 − a)(g_L − g_R), a = exp(−0.1); D = window mean of p. Note: for a 2 s
  window this is the window mean of g_L − g_R up to a start transient — P's dynamics are inert.
- TH (CONTROL, memoryless threshold, = single-frame max detector at c = 0): D = window mean of [max(0, 12g_L − θ_TH) − max(0,
  12g_R − θ_TH)]; θ_TH from pilot rule R4.
- TH_LP (CONTROL, low-pass threshold): x_s ← I_s + (x_s − I_s)·exp(−10/20) per frame (first-order τ 20 ms on the held 12g_s,
  sampled at frame ends = the extrema of each frame), D = window mean of [max(0, x_L − θ_LP) − max(0, x_R − θ_LP)]; θ_LP by R4.
  A control is MATCHED only if |BSC_ctrl,stat − BSC_DATA,stat| ≤ 0.05 on pilot range D; an unmatched control is reported, not tested.
- LIN (CONTROL, linear null reference): window mean of Σ_px c·(S_L − S_R) with the encoder's blurred chromatic contrast c, no c_min,
  no saturation. Expected: no motion benefit; it is not an information bound.

## 5. Decision rule and metrics
Response "left" if D > c, "right" if D < −c, else "none"; c per (system, network, condition, range) = smallest c ≥ 0 with
FA = P(|D| > c | no target) ≤ 0.05 from that condition's no-target trials. For systems silent without a target (SNN, P, TH under σ 10)
this gives c = 0 and FA = 0 — the matching is then vacuous, which is reported, not hidden; FA is reported for every system.
- PRIMARY metric: balanced side-correct rate BSC = ½[P(left | left target) + P(right | right target)] over the unit sample; "none" is
  wrong. With rho_u uniform on [a, b] and a monotone psychometric function, BSC = (ρ_th − a)/(b − a) (Spearman–Kärber), so
  ΔBSC × 0.14 m = shift of the distance threshold. Measurable arm: BSC ∈ [0.1, 0.9].
  SK validity of an arm (checked BEFORE classification): hit rate (both sides pooled) ≥ 0.8 among units with rho in the nearest 15 % of
  the range and ≤ 0.2 in the farthest 15 %, and over 7 equal-width rho bins no bin's hit rate exceeds the previous bin's by > 0.15.
  ΔBSC is always reported as the difference of mean hit rates over the stimulus family; it is translated into a threshold shift
  (× 0.14 m) only if both arms are SK-valid; an EQUIVALENT class requires both arms measurable AND SK-valid.
- Secondary: hit_L, hit_R, FA; d'_LR = √2·Φ⁻¹(AUC(D_left, D_right)) (AUC clipped to [1/2n, 1 − 1/2n]; saturates — not compared
  across different n); d'_det from AUC(|D| target vs none); MI(side; response) plug-in bits (descriptive, biased upward);
  fraction D = 0 among target trials; onset latency (first ipsi DNa02 spike after t = 0) and decision latency (first spike on the reported
  side after t = 1 s), correct trials only.
- Neural (descriptive, DATA/B1/SWS): window counts LC10a L/R, intermediates, DNa02 L/R; pairwise synchrony (mean Pearson r of 5 ms
  binned counts over active neurons, V6m "paircorr5") of LC10a L, LC10a R, intermediates; first-spike latencies; Fourier amplitude and
  phase (relative to θ) at f of LC10a-L, LC10a-R population rate and of DNa02 L − R for sin and J_vel; across-unit Fano of D.
  More spikes is not more information; only BSC/d'/MI are information measures.

## 6. Units, seeds, common random numbers
Unit = resampling unit. ALIF noise seed u for every network and condition (standard_normal(N) drawn unconditionally each step, N = 424
for all networks — verified in source, tested). Pixel noise and stimulus as §2. Limitation: identical noise ≠ identical network state.
Pools: `SEED_REGISTRY.md` (collision scan corrected per RT M7: 0 seed uses; only float digits like 1.9109375 match).

## 7. Stages
- 0A pilot (EXPLORATORY, units 9 101 001–060, 5 B1 + 5 SWS pilot instances): conditions stat, 16 sin, 16 J_vel, J_shuf(A) and
  J_rms(A) for 4 A (J_shuf uses f = 2 Hz; its θ distribution does not depend on f), all on DATA, B1, SWS (range D) and P/TH/LIN
  (ranges D and C). Pilot data never enter confirmatory estimates. Mechanical rules (`analysis.py pilot-rules` → confirm_params.json):
  R1 (f*, A*) = argmax over the 16 sin cells of the equal-weight mean over DATA, B1, SWS of ΔBSC(sin − stat); ties within 0.01 →
     larger A, then lower f. Applied even if every ΔBSC ≤ 0. The DATA-only argmax is reported; f* is weakly identified (pilot SE of
     ΔBSC ≈ 0.03–0.05), so S1/S2/F-e use f* as a nominal choice.
  R2 n = max_k ceil(1.2·((z_{1−α_k/2} + z_{power_k})·SD_k/0.07)²), k ∈ {H1 (α 0.05, power 0.9), S1–S6 (α 0.05/6, power 0.8)},
     SD_k = pilot SD over units of the per-unit paired difference (pooled criteria; S5 on range C); clamped to [200, 500]. The
     cap-bound achieved power of every test is written to confirm_params.json BEFORE the confirm run, with the tests expected to end
     INCONCLUSIVE. Budget: ≈ 120 s CPU per confirm unit (render-bound) ⇒ n 500 ≈ 17 h CPU ≈ 2 h on 9 workers; runs are resumable per
     unit (existing unit files are skipped, never overwritten).
  R3 if pilot stationary BSC of P on range C ∉ [0.2, 0.8], range C := [k_th − 0.12, k_th + 0.12] (lower end ≥ 0.01), k_th = SK threshold.
  R3D if pilot DATA stat or DATA sin(f*, A*) fails the SK edge check (§5) on range D, range D := [ρ_c − 0.07, ρ_c + 0.07], ρ_c = mean of
     the two arms' SK thresholds (one step; the result is reported, the range is not iterated on confirm data).
  R4 θ_TH and θ_LP = grid values (4.00–8.00 mV, step 0.01) minimising |BSC_ctrl,stat − BSC_DATA,stat| on pilot range D (smallest on ties).
- 0B/0C confirm (n units from 9 102 001; 10 + 10 fresh instances): DATA: stat, 16 sin, J_shuf(A*), J_rms(A*), J_vel(f*, A*), MT(f*, A*);
  B1, SWS: stat, sin(f*, A*), J_shuf(A*), J_rms(A*), J_vel(f*, A*); P/TH/LIN: all DATA conditions on ranges D and C.
- 0D robustness (200 units from 9 103 001; confirm instances re-used — networks, not noise seeds): DATA, B1, SWS + P/TH/LIN on range D,
  conditions stat, sin(f*, A*), J_shuf(A*), variants |az| 4–8°, |az| 12–16°, ball r 1.8 cm (rho range × 0.72), pixel σ 20.

## 8. Hypotheses and tests (confirm data only; `analysis.py` frozen and hashed before the confirm run)
Paired bootstrap over units, 10 000 resamples (RNG 9 107 001), criteria re-estimated in every resample. Terms involving B1 or SWS use a
hierarchical bootstrap (instances with replacement, then units within each drawn instance; the same unit list is used for the DATA
term). DATA is a single network: inference about DATA is conditional on it. Percentile CIs; p = min(1, 2·min(P*(Δ ≤ 0), P*(Δ ≥ 0))),
floored at 1/10 000, = 1 if the bootstrap distribution is a point mass at 0.
Classification of an estimate (first matching rule wins): SUPPORTED (CI95 > 0 and est ≥ 0.07) → HARMFUL (CI95 < 0 and est ≤ −0.07)
→ EQUIVALENT (CI90 ⊂ (−0.07, 0.07), arms measurable and SK-valid; may be detectably non-zero, sign reported) →
DETECTABLE-BELOW-SESOI (CI95 excludes 0, sign reported) → UNMEASURABLE (an arm outside [0.1, 0.9] or SK-invalid) → INCONCLUSIVE.
"Negative" in §9 = est < 0 with CI95 < 0.
- H1 PRIMARY: Δ1 = BSC_D(DATA, sin(f*, A*)) − BSC_D(DATA, stat). Single test, α 0.05.
- Key secondary family (Holm over 6 at 0.05; equivalence by CI90):
  S1 sin(f*, A*) − J_shuf(A*), DATA: temporal structure vs amplitude distribution.
  S2 sin(f*, A*) − J_vel(f*, A*), DATA: periodic vs aperiodic motion with matched RMS displacement and velocity.
  S3 Δ(DATA) − Δ(B1);  S4 Δ(DATA) − Δ(SWS): wiring dependence (Δ = sin(f*, A*) − stat on range D).
  S5 Δ(P) on range C (own operating range): does the classical read-out benefit? Classified like H1.
  S6 Δ(DATA) − Δ(TH_LP) on range D: SNN vs matched low-pass threshold (if TH_LP is unmatched: S6 is not tested, reported as such).
- Wiring statement (descriptive): per-instance table of Δ for the 10 B1 + 10 SWS instances and the rank of DATA's Δ among them.
- Validity checks (not in Holm): sin(f*, A*) − MT(f*, A*), DATA — expected EQUIVALENT up to the light direction relative to the ball;
  otherwise background/gripper motion contributes. P and TH: sin(f*, A*) − J_shuf(A*) — expected EQUIVALENT (P is a window mean,
  TH memoryless): positive controls for S1.
- Exploratory: 16-cell grid for DATA (Holm-adjusted p reported), J_rms, LIN, TH (max detector), P/TH on range D, thresholds, all
  neural measures, 0D. Interpretation limits stated in advance: S1 > 0 for the SNN can reflect membrane smoothing of broadband jitter
  (J_shuf velocity is 3–12× the sinusoid's), not periodicity; J_vel peaks exceed A (median max|θ|/A ≈ 1.2–1.8).

## 9. Failure conditions (descriptive, not error-controlled; any one = negative F1 finding, not implementation failure)
F-a H1 not SUPPORTED. F-b S1 or S2 EQUIVALENT or negative (no sinusoid specificity). F-c S5 SUPPORTED, or S6 EQUIVALENT
or negative (not SNN-specific). F-d S3 and S4 both EQUIVALENT or negative (no wiring specificity). F-e ≤ 1 of 16 grid cells with Holm
p < 0.05 and est > 0 (narrow). F-f window LC10a-ipsi count rises (CI95 > 0) under sin(f*, A*) while H1 is not SUPPORTED.
F-g 0D: CI95 of Δ > 0 in < 3 of 4 variants (DATA). F-h under sin(f*, A*) one side's hit rate < 0.1 while the other's > 0.5.
Recommendation to consider Stage 1: H1 SUPPORTED and not F-g and not F-h (F-b/F-c/F-d change the interpretation, not the transfer
question; if F-c fires the recommendation says Stage 1 would test a threshold-convexity benefit, not an SNN-specific one). Conclusions
are phrased as hit rates at FA = 0 in a distractor-free scene; d'_det is not interpreted; 0D pix20 is the only place the FA criterion
is exercised. Stage 1 needs explicit user approval in any case.

## 10. Blocking tests, exclusions, stopping, integrity
Blocking tests (tests/test_f1.py, all must pass before the pilot): T1 zero amplitude = stationary (images, g, SNN bit-identical);
T2 mirror — horizontally flipped image swaps g_L/g_R exactly and flips the sign of D, scene mirror asymmetry reported; T3 no-target:
SNN silent and P = 0 over smoke units and phases; T4 phase: window-mean drive differs < 2 % across 4 phases, no-target drive 0;
T5 jitter: J_shuf multiset = sin multiset, window RMS exact and window mean 0 for all jitters, J_vel velocity within tolerance;
T6 ball world position constant, bearing = az0 − θ (< 1e-9 rad), camera position constant; T7 renderer camera (MjvGLCamera after
update_scene) = recorded pose, projected ball column within 1.5 px of the rendered centroid; MT: bearing = az0 − θ with static camera,
ball z = r, MT vs camera-rotation ball image: column-centroid and area differences reported (< 1 px expected);
T8 DATA W_data hash unchanged, no model edges; T9 integrity (integrity_v5v41 --compare OK, F1 pre-snapshot unchanged outside this
directory); T10 repeated run bit-identical; T11 readout sign; T12 no-target spontaneous D quantified; T14 J_vel draws ledger stored per
(unit, condition); CRN equality; analysis self-check.
No outlier exclusion; a trial with render failure, NaN or exception is excluded and listed; > 1 % ⇒ STOP. Fixed n, no interim looks.
`python -I -B` (spawned workers inherit -I -B), no bio2 import (checked), no commits, no hardware, outputs only under this directory,
mode "x". Integrity before and after each stage; manifest.json holds code + protocol hashes; confirm refuses changed analysis code.

## 11. Answers to red-team r1
C1 continuous per-unit rho/az (SK estimator, no rungs), SESOI = 1 cm, measurability gate. C2 S5 = own-range test; TH matched by R4;
LIN relabelled. C3 vacuous FA matching stated and reported; distractor not added (would change the task; deferred). C4 J_shuf added,
unique realisations per unit, window-matched RMS and mean, J_vel rejection rule. M1 continuous phases, instance index independent.
M2 stimulus sampled per unit. M3 hierarchical bootstrap for B1/SWS; DATA conditional. M4 tie rule fixed; R2 covers S1–S6 with Holm α.
M5 ordered classes, numeric F-e/F-f, p floor. M6 scope statement + MT control. M7 regex corrected and rerun. M8 blocking tests,
decision latency, PROTOCOL.md hash-locked, analysis hashed. Minor: m1 implemented; m3 stated; m4 D = 0 fraction; m5 stated;
m6 stated; m7 0D adds SWS + controls + J_shuf; m8 snapshot excludes this directory; m9 hit_L/hit_R reported. Not done: single-LIF
surrogate (C2 suggestion) — TH + B1/SWS already separate "threshold" from "network"; noted as limitation.

## 12. r3 changes (red-team r2, PASS_WITH_FIXES)
M-A SK edge + monotonicity checks before classification; R3D re-centring for range D. M-B classification order: EQUIVALENT before
DETECTABLE-BELOW-SESOI, HARMFUL needs est ≤ −SESOI, "negative" defined. M-C F-c no longer compares ΔBSC across ranges; S5 in R2.
M-D TH_LP control (τ 20 ms) + match tolerance 0.05; S6 uses TH_LP. Minor: budget + resumable units (m1), DATA-only argmax reported and
f* weakly identified (m2), R3 half-width 0.12 (m3), pre-run achieved power (m4), FA-vacuity wording (m5), Stage-1 wording (m6),
seed rows apply to all unit pools (m7), stimulus uniforms reused across 0D variants = paired (m8), MT test (m9), P/TH J_shuf positive
controls (m10), T14 ledger (m11).

## 13. Amendment r3.1 (2026-11-01, before any pilot or confirmatory run; only smoke-pool units had been run)
Reason: the smoke run (4 units, results/smoke) showed rendering is GL-bound at ≈ 240 frames/s in total regardless of the number of
workers (≈ 1 025 s per pilot unit), i.e. ≈ 4.3 h for the r3 pilot and ≈ 19 h for the r3 confirm at n 500 — not feasible. No smoke
result was looked at scientifically (4 units; the analysis dry run only checked that the code runs).
A1 Render cache (ENGINEERING, no stimulus change): within one unit and one target, an image already rendered for the same mode and θ
   (rounded to 1e-12 rad) is reused; the scene is static, so the image is identical (blocking test: cached == fresh, bit for bit).
   Stimuli are rendered in a stimulus-outer loop so J_shuf re-uses its sinusoid's renders and stat needs one render.
A2 Pilot in two parts on the same 60 units: pilot1 = stat + 16 sin (ranges D and C) → R1 → `pilot_r1.json`; pilot2 = J_shuf(A*),
   J_rms(A*), J_vel(f*, A*) (ranges D and C) → R2–R4, R3D → `confirm_params.json`. The r3 pilot's J_vel grid (16 cells) and J_shuf /
   J_rms at the other amplitudes are dropped: no rule used them. The pilot jitter-specificity estimates are therefore only at (f*, A*).
A3 Confirm: range C is rendered only for stat, sin(f*, A*), J_shuf, J_rms, J_vel, MT (P/TH/LIN on range C only there); the 15 other
   grid cells on range D + no target. 0D unchanged (range D only).
A4 n_max 500 → 400 (budget ≈ 4 h of rendering at ≈ 8 700 renders per unit). R2 unchanged otherwise; achieved power is reported.
A5 Jitter rng = default_rng([u, 3, crc32(condition name)]) (order-independent; r3 used the condition's list index).

## 14. Amendment r3.2 (2026-11-01, after pilot1 had run and BEFORE R1 was applied or any pilot1 result was looked at)
Source: code red team (`redteam/code_redteam_r1.md`, PASS_WITH_FIXES; no defect affecting pilot1 numbers). Changes:
B1 S6 gate: S6 is tested only if TH_LP is matched on the pilot range (R4) AND |BSC_TH_LP,stat − BSC_DATA,stat| ≤ 0.05 on the confirm
   range (both stationary arms only, so the gate does not look at any motion effect). The Holm family always has 6 members (an untested
   S6 enters with p = 1); R2 ignores S6 when TH_LP is unmatched on the pilot.
B2 Float-safe comparisons (tolerance 1e-9) for SESOI, measurability and the R1 tie rule.
B3 Runner: verifies the hashes of the frozen FlyMind dependencies and data files listed in the manifest; confirm/robust require a
   manifest containing confirm_params.json; unit files are written to a temporary name and renamed; the manifest hash is stored in
   every unit file; STOP (non-zero exit, no analysis) if > 1 % of units fail; pilot/smoke stimuli never read confirm_params.json.
B4 0D small_ball uses 0.72 × the (possibly R3D re-centred) range D; 0D uses 10 000 bootstrap resamples.
B5 New checks: tests/test_analysis.py, T8 full-mask block check, T9 F1 pre-snapshot (integrity_f1.py, snapshot taken before any F1
   file existed). Wording: under σ 10, P's no-target D is ≈ 0 (|D| < 1e-3), not exactly 0, so P's criterion is small but may be > 0.
