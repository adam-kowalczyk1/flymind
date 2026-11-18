# FLYMIND F1 — Stage 0 (open loop) active-sensing protocol, r2

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
- TH (CONTROL, memoryless threshold): D = window mean of [max(0, 12g_L − θ_TH) − max(0, 12g_R − θ_TH)]; θ_TH from pilot rule R4.
- LIN (CONTROL, linear null reference): window mean of Σ_px c·(S_L − S_R) with the encoder's blurred chromatic contrast c, no c_min,
  no saturation. Expected: no motion benefit; it is not an information bound.

## 5. Decision rule and metrics
Response "left" if D > c, "right" if D < −c, else "none"; c per (system, network, condition, range) = smallest c ≥ 0 with
FA = P(|D| > c | no target) ≤ 0.05 from that condition's no-target trials. For systems silent without a target (SNN, P, TH under σ 10)
this gives c = 0 and FA = 0 — the matching is then vacuous, which is reported, not hidden; FA is reported for every system.
- PRIMARY metric: balanced side-correct rate BSC = ½[P(left | left target) + P(right | right target)] over the unit sample; "none" is
  wrong. With rho_u uniform on [a, b] and a monotone psychometric function, BSC = (ρ_th − a)/(b − a) (Spearman–Kärber), so
  ΔBSC × 0.14 m = shift of the distance threshold. Measurable arm: BSC ∈ [0.1, 0.9].
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
     larger A, then lower f. Applied even if every ΔBSC ≤ 0.
  R2 n = max_k ceil(1.2·((z_{1−α_k/2} + z_{power_k})·SD_k/0.07)²), k ∈ {H1 (α 0.05, power 0.9), S1, S2, S3, S4, S6 (α 0.05/6, power 0.8)},
     SD_k = pilot SD over units of the per-unit paired difference (pooled criteria); clamped to [200, 500]; achieved power reported.
  R3 if pilot stationary BSC of P on range C ∉ [0.2, 0.8], range C := [k_th − 0.08, k_th + 0.08] (lower end ≥ 0.01), k_th = SK threshold.
  R4 θ_TH = grid value (4.00–8.00 mV, step 0.01) minimising |BSC_TH,stat − BSC_DATA,stat| on pilot range D (smallest on ties).
- 0B/0C confirm (n units from 9 102 001; 10 + 10 fresh instances): DATA: stat, 16 sin, J_shuf(A*), J_rms(A*), J_vel(f*, A*), MT(f*, A*);
  B1, SWS: stat, sin(f*, A*), J_shuf(A*), J_rms(A*), J_vel(f*, A*); P/TH/LIN: all DATA conditions on ranges D and C.
- 0D robustness (200 units from 9 103 001; confirm instances re-used — networks, not noise seeds): DATA, B1, SWS + P/TH/LIN on range D,
  conditions stat, sin(f*, A*), J_shuf(A*), variants |az| 4–8°, |az| 12–16°, ball r 1.8 cm (rho range × 0.72), pixel σ 20.

## 8. Hypotheses and tests (confirm data only; `analysis.py` frozen and hashed before the confirm run)
Paired bootstrap over units, 10 000 resamples (RNG 9 107 001), criteria re-estimated in every resample. Terms involving B1 or SWS use a
hierarchical bootstrap (instances with replacement, then units within each drawn instance; the same unit list is used for the DATA
term). DATA is a single network: inference about DATA is conditional on it. Percentile CIs; p = min(1, 2·min(P*(Δ ≤ 0), P*(Δ ≥ 0))),
floored at 1/10 000, = 1 if the bootstrap distribution is a point mass at 0.
Classification of an estimate (first matching rule wins): SUPPORTED (CI95 > 0 and est ≥ 0.07) → DETECTABLE-BELOW-SESOI (CI95 > 0) →
HARMFUL (CI95 < 0) → EQUIVALENT (CI90 ⊂ (−0.07, 0.07) and both arms measurable) → UNMEASURABLE (an arm outside [0.1, 0.9]) →
INCONCLUSIVE.
- H1 PRIMARY: Δ1 = BSC_D(DATA, sin(f*, A*)) − BSC_D(DATA, stat). Single test, α 0.05.
- Key secondary family (Holm over 6 at 0.05; equivalence by CI90):
  S1 sin(f*, A*) − J_shuf(A*), DATA: temporal structure vs amplitude distribution.
  S2 sin(f*, A*) − J_vel(f*, A*), DATA: periodic vs aperiodic motion with matched RMS displacement and velocity.
  S3 Δ(DATA) − Δ(B1);  S4 Δ(DATA) − Δ(SWS): wiring dependence (Δ = sin(f*, A*) − stat on range D).
  S5 Δ(P) on range C (own operating range): does the classical read-out benefit? Classified like H1.
  S6 Δ(DATA) − Δ(TH) on range D: SNN vs matched memoryless threshold.
- Validity check (not in Holm): sin(f*, A*) − MT(f*, A*), DATA — expected EQUIVALENT; otherwise background/gripper motion contributes.
- Exploratory: 16-cell grid for DATA (Holm-adjusted p reported), J_rms, LIN, P/TH on range D, thresholds, all neural measures, 0D.

## 9. Failure conditions (descriptive, not error-controlled; any one = negative F1 finding, not implementation failure)
F-a H1 not SUPPORTED. F-b S1 or S2 EQUIVALENT or negative (no sinusoid specificity). F-c S5 SUPPORTED with est ≥ Δ1, or S6 EQUIVALENT
or negative (not SNN-specific). F-d S3 and S4 both EQUIVALENT or negative (no wiring specificity). F-e ≤ 1 of 16 grid cells with Holm
p < 0.05 and est > 0 (narrow). F-f window LC10a-ipsi count rises (CI95 > 0) under sin(f*, A*) while H1 is not SUPPORTED.
F-g 0D: CI95 of Δ > 0 in < 3 of 4 variants (DATA). F-h under sin(f*, A*) one side's hit rate < 0.1 while the other's > 0.5.
Recommendation to consider Stage 1: H1 SUPPORTED and not F-g and not F-h (F-b/F-c/F-d change the interpretation, not the transfer
question). Stage 1 needs explicit user approval in any case.

## 10. Blocking tests, exclusions, stopping, integrity
Blocking tests (tests/test_f1.py, all must pass before the pilot): T1 zero amplitude = stationary (images, g, SNN bit-identical);
T2 mirror — horizontally flipped image swaps g_L/g_R exactly and flips the sign of D, scene mirror asymmetry reported; T3 no-target:
SNN silent and P = 0 over smoke units and phases; T4 phase: window-mean drive differs < 2 % across 4 phases, no-target drive 0;
T5 jitter: J_shuf multiset = sin multiset, window RMS exact and window mean 0 for all jitters, J_vel velocity within tolerance;
T6 ball world position constant, bearing = az0 − θ (< 1e-9 rad), camera position constant; T7 renderer camera (MjvGLCamera after
update_scene) = recorded pose, projected ball column within 1.5 px of the rendered centroid; MT: bearing = az0 − θ with static camera;
T8 DATA W_data hash unchanged, no model edges; T9 integrity (integrity_v5v41 --compare OK, F1 pre-snapshot unchanged outside this
directory); T10 repeated run bit-identical; T11 readout sign; T12 no-target spontaneous D quantified; CRN equality; analysis self-check.
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
