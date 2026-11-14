# FLYMIND F1 — Stage 0 (open loop) active-sensing protocol, r1

Frozen before any pilot or confirmatory run. Machine parameters: `protocol.json` (same directory; its sha256 is recorded in
`manifest.json` and checked by `runner.py`). Any change = new revision with a new hash; old outputs stay.
Everything here is about a MODEL (ALIF network on MaleCNS-derived wiring + engineering encoder), never about Drosophila.

## 1. Question
Does a small controlled rotation of a virtual camera (robot static) improve LEFT/RIGHT reporting of a weak stationary target by the
model, is any benefit specific to sinusoidal motion, to the SNN, and to the data-derived wiring?

## 2. Stimulus (ENGINEERING, MuJoCo)
- Scene: `so101.SO101Sim()` default scene, arm static at loop.Q_POSE, physics never stepped (ball cannot move; tested).
- Target: the scene ball, placed with `loop.place_ball(az0, rho)` (bearing az0 from the horizontal camera axis, horizontal distance rho).
  Contrast k: ball rgb = 0.75 + k·(default − 0.75) set on the in-memory model (table grey 0.75). Size: geom radius in memory, centre z = r.
- Ladder D (SNN operating range, user range 0.26–0.34 m): k 1, |az0| 10°, rho ∈ {0.26, 0.28, 0.30, 0.32, 0.34}.
- Ladder C (P operating range): rho 0.30, |az0| 10°, k ∈ {0.15, 0.20, 0.25, 0.30, 0.40, 0.55, 0.75}.
- Sides: left (+az0) and right (−az0) = geometric mirror about the camera axis. The scene is NOT mirror-symmetric (camera roll
  ≈ 2.3°, directional light, checker floor) — measured and reported, not corrected.
- No target: ball parked out of view (default park), same motion.
- Sensor noise (EXPERIMENTAL ASSUMPTION, shared by every system): i.i.d. Gaussian σ 10 grey levels per pixel/channel/frame added to the
  rendered uint8 image, rounded, clipped to [0, 255]. Precedent: V4 robustness condition. Without it the non-neural detectors would be
  noiseless (degenerate comparison).

## 3. Motion (virtual camera, Stage 0 = implementation A only)
Pure rotation of the camera about the world vertical through its optical centre; position unchanged; robot, ball, table unchanged.
θ > 0 = camera turned left ⇒ true target bearing = az0 − θ (tested exactly). Applied each 10 ms frame t_k = k·10 ms, k = 0..299.
- stationary: θ ≡ 0.
- sinusoid: θ(t) = A·sin(2πft + φ), f ∈ {0.5, 1, 2, 4} Hz, A ∈ {0.5, 1, 2, 4}°; φ ∈ {0, π/2, π, 3π/2} assigned by unit index mod 4
  (counterbalanced). Frame rate 100 Hz ⇒ ≥ 25 samples per cycle at 4 Hz; window 1–3 s holds whole cycles for every f.
- J_rms(A): i.i.d. Gaussian θ per frame, rescaled so RMS θ over the trial = A/√2 exactly (matches sinusoid RMS displacement; velocity not matched).
- J_vel(f, A): white Gaussian noise convolved with a Gaussian kernel σ_t = 1/(2√2·π·f) (expected RMS angular velocity / RMS displacement
  = 2πf as for the sinusoid), rescaled so RMS θ = A/√2 exactly; realized RMS velocity recorded (test: within ±20 % of 2πf·A/√2).
- Jitter realizations: 4 per condition (rng = default_rng(SeedSequence([9106000, stage, cond_index, r]))), assigned by unit index mod 4.
Recorded per frame: θ, θ̇, θ̈ (analytic for sinusoid, central differences for jitter), camera position and rotation matrix used by the
renderer, true bearing.

## 4. Pipeline (all VERIFIED IN SOURCE CODE except where marked)
image → (+ pixel noise) → `encoder.TargetEncoder` (loop.ENC, unchanged) → g_L, g_R per frame → current 12·g_s mV to every LC10a of
side s, held 10 ms (`encoder.currents`) → ALIF (loop.P: σ 2 mV, b_a 0.5, τ_a 300 ms, t_ref 2.2 ms, dt 1 ms) on
`visual_path.network(0.2)` (275 LC10a, 147 intermediates, DNa02 L/R) → spikes.
Readouts (Stage 0 EXPERIMENTAL readouts, separate from `decoder.SteerDecoder`, which is not used or changed):
- SNN: D = (# DNa02_L spikes − # DNa02_R spikes) in the window 1.0–3.0 s. Same sign convention as the motor decoder (L − R > 0 ⇒ left).
- P (classical, as loop.py classical_p): p ← a·p + (1−a)·(g_L − g_R), a = exp(−0.01/0.1), per frame; D = mean p over window frames.
- TH (non-neural static threshold): D = mean over window frames of [max(0, 12g_L − 5.99) − max(0, 12g_R − 5.99)] (5.99 mV = V5 v4.1
  DATA I_th10, fixed in advance). Tests whether a memoryless threshold explains an SNN benefit.
- LIN (image-information reference, non-neural): per frame Σ_pixels c·(S_L − S_R)(column) with the encoder's blurred chromatic contrast
  c but WITHOUT the c_min threshold and without saturation; D = window mean.
Networks: DATA; B1 = `block_shuffle.block_shuffle(spec, layer_side_labels, seed, "LCxLC")`; SWS = `side_shuffle.shuffle_within_side`
(v2, provenance: V5 v3 red-team passed). Fresh instances (pilot 5 + 5, confirm 10 + 10); unit u uses instance (u mod n_inst).

## 5. Decision rule and metrics (defined now, never changed)
Response: "left" if D > c, "right" if D < −c, otherwise "none". Criterion c per (system, network, motion condition, ladder):
smallest c ≥ 0 such that the false-alarm rate FA = P(|D| > c | no target) ≤ 0.05, estimated from that condition's no-target trials
(c = 0 if already satisfied; ties at exactly c count as "none").
- PRIMARY: balanced side-correct rate BSC = ½[P("left" | left target) + P("right" | right target)]. "none" is wrong. Silent system = 0;
  a system that answers only one side ≤ 0.5. Ladder-average BSC = mean over the ladder's levels.
- Secondary (SDT): hit rates per side; FA; d'_LR = √2·Φ⁻¹(AUC of D, left vs right trials, ties ½), AUC clipped to [1/(2n), 1−1/(2n)];
  detection d'_det from AUC of |D| target vs none; mutual information between side (L/R) and response (left/none/right), plug-in bits;
  threshold ρ_50 / k_50 = ladder value where BSC crosses 0.5 (linear interpolation; censored if never crossed).
- Neural (DATA/B1/SWS, descriptive): window spike counts LC10a ipsi/contra, intermediates, DNa02 L/R and D; LC10a-ipsi and intermediate
  pairwise synchrony (mean Pearson r of 5 ms binned counts over active neurons, = V6m "paircorr5"); first-spike latency of LC10a-ipsi and
  DNa02-ipsi after t = 0; Fourier amplitude and phase at f of LC10a-ipsi population rate and of DNa02 L−R (window), relative to θ(t);
  across-unit Fano factor of D. A spike-count increase is NOT evidence of more information (only BSC/d'/MI are).

## 6. Units, seeds, common random numbers
A unit u (seed) provides, for every motion condition × ladder level × side and one no-target trial per condition: ALIF noise seed u (all
networks: noise drawn unconditionally each step with N = 424 ⇒ identical noise sequence across conditions and networks — verified in
source, tested), pixel noise `default_rng([u, 1])` (one array [300, 96, 128, 3] reused across all conditions of the unit), phase /
jitter realization index u mod 4. Units are the resampling unit. Limitation: identical noise ≠ identical network state; CRN only reduces
variance of paired differences.
Seed pools: `SEED_REGISTRY.md` (registered before the first run; collision check of 91x xxx xx: 0 hits in flymind/ and bio2/).

## 7. Stages
- 0A pilot (EXPLORATORY): units 9 101 001–060; DATA + 5 B1 + 5 SWS on ladder D; P/TH/LIN on ladders D and C; motion: stationary,
  16 sinusoids, J_rms(A) for 4 A, J_vel(f, A) for 16 cells. Pilot data are never pooled with confirmatory data.
- Rules applied mechanically to the pilot (script `analysis.py --pilot-rules`, output `confirm_params.json`, hashed):
  R1 (f*, A*) = argmax over the 16 sinusoid cells of the mean over DATA, B1, SWS (equal weights) of ladder-D-average ΔBSC
      (sinusoid − stationary); ties within 0.01 → smaller A, then lower f. Applied even if every ΔBSC ≤ 0.
  R2 n = ceil(1.2·((1.96 + 1.2816)·SD/0.05)²) with SD = pilot SD over units of the per-unit ladder-average paired difference for DATA at
      (f*, A*); the same for the DATA − B1 interaction; n = max of the two, clamped to [200, 600] (cap = compute budget; achieved power
      reported if the cap binds). Per-unit BSC uses the pooled criterion c of the condition.
- 0B/0C confirm (n units from 9 102 001): DATA: stationary, 16 sinusoids, J_rms(A*), J_vel(f*, A*) on ladder D; B1, SWS (10 fresh
  instances each): stationary, sin(f*, A*), J_rms(A*), J_vel(f*, A*) on ladder D; P/TH/LIN: same 19 conditions on ladders D and C.
- 0D robustness (200 units from 9 103 001, after confirm): DATA + B1, stationary / sin(f*, A*) / J_rms(A*) in 4 variants: |az0| 6°,
  |az0| 14°, ball r 1.8 cm, pixel σ 20 (each a full ladder D, own criteria). Plus per-phase breakdown of the confirm data.

## 8. Hypotheses and tests (confirm data only)
Estimates: paired bootstrap over units (10 000 resamples, analysis RNG 9 107 001; criteria re-estimated inside each resample),
percentile CI; two-sided bootstrap p = 2·min(P*(Δ ≤ 0), P*(Δ ≥ 0)). SESOI = 0.05 BSC (EXPERIMENTAL ASSUMPTION: 5 percentage points of
side-correct reports; smaller changes are treated as practically nil for orienting).
- H1 PRIMARY (single test, α 0.05): Δ1 = ladder-D-average BSC(DATA, sin(f*, A*)) − BSC(DATA, stationary).
  SUPPORTED: CI95 > 0 and Δ1 ≥ 0.05. TRIVIAL: CI95 > 0, Δ1 < 0.05. NO MEANINGFUL BENEFIT: CI90 ⊂ (−0.05, 0.05). HARMFUL: CI95 < 0.
  Otherwise INCONCLUSIVE.
- Key secondary family (Holm over 6, α 0.05; each also TOST at ±0.05 with CI90 for "equal"):
  S1 sin(f*,A*) − J_rms(A*) (DATA); S2 sin(f*,A*) − J_vel(f*,A*) (DATA): frequency/waveform specificity.
  S3 Δ(DATA) − Δ(B1); S4 Δ(DATA) − Δ(SWS): wiring dependence (interaction, ladder-average).
  S5 Δ(DATA, ladder D) − Δ(P, ladder C): SNN vs classical at each system's own operating range.
  S6 Δ(DATA) − Δ(TH) on ladder D: SNN dynamics vs a memoryless threshold.
- Exploratory (no multiplicity claim): the full 16-cell sinusoid grid for DATA (Holm-adjusted p reported), per-level ΔBSC, d'/MI,
  threshold shifts, all neural measures, P/LIN on ladder D, 0D.

## 9. Failure conditions (any one is reported as a negative F1 finding, not an implementation failure)
F-a H1 not SUPPORTED. F-b S1 or S2 equivalent or jitter better (no sinusoid specificity). F-c S5 or S6 equivalent or control benefits
more (not SNN-specific / explained by a static threshold). F-d S3 and S4 equivalent or DATA benefits less (no wiring specificity).
F-e benefit only at one ladder level and one grid cell (narrow). F-f spike counts rise without a BSC/d' gain. F-g 0D: benefit
(CI95 > 0) in fewer than 3 of 4 variants. F-h side failure: hit rate of one side < 0.1 while the other > 0.5 under motion.

## 10. Exclusions, stopping, integrity
- No outlier exclusion. A trial with a render failure, NaN or exception is excluded and listed; > 1 % of trials ⇒ STOP, no analysis.
- Fixed n, no interim looks, no optional stopping. Pilot data never enter confirmatory estimates.
- Before and after every run: `integrity_v5v41.py --compare` (Stage 1 28/28, manifests, 377 protected files) and the F1 pre-snapshot
  of flymind/, bio2/, data/, assets/; sha256 of DATA W_data; code hashes in `manifest.json`. `python -I -B` only; no bio2 import; no commit;
  no hardware; outputs only under this directory, opened with mode "x".
- Stage 1 (closed loop) is NOT started. Proceed-to-Stage-1 recommendation only if H1 SUPPORTED and not F-g, and only with user approval.
