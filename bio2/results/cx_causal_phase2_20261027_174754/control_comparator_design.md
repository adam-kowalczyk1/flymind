# Phase 2, Workstream C: matched-comparator design (control theory)

`T:` = `bio2/test_cx_working_memory_vs_kalman.py`. §4 formulas were checked against a pure-Python linear-plant simulation
(no MuJoCo). Servo constants come from the XML.

## 0. Two findings that change the design

1. **The cue is not changed 1:1 by `w_base`.** `cue_rel` is the azimuth about the world origin, minus `aim_az` (T:495-508). The
   pan axis sits 38.8 mm off that origin (`assets/so101_upstream.xml:49`). For a point at polar radius r, the azimuth rate is
   κ·(joint rate), with κ = 1 − (a/r)cos ψ, a = 0.0388 m. With r ≈ 0.30 m this gives **κ ≈ 0.87** (0.86–0.89 over ψ = 5–30°). This
   matches Agent B's probe (0.1 rad of pan moved azimuth 5.0°, not 5.7°). A stationary target's cue changes by −κ∫w_base, so a
   unit-gain integrator over-compensates by 15%, and the CX's phase-1 gain 1.32 is effectively 1.32/0.87 ≈ **1.52**. Neither is a memory property.
2. **A scalar integrator is the sufficient statistic** for one noise-free bearing, a stationary target and a measured
   rotation rate. See the closing objection.

## 1. Information audit (what each controller consumed)

**Shared front end, all arms:**
- Camera frame plus retinal efference shift from `dpsi = −Δq_pan` (T:481, 488; `vision.py:52-54`).
- `cue_rel` (T:495-508) uses the exact camera pose `d.cam("eye")` (forward kinematics), the known table plane and ball
  radius, and exact `aim_az` (T:113, 493). The raw retinal angle (`cands[0]["az"]`) is unused.
- `ball_az` and `true_rel_az` (T:494-495) go to metrics only.

| Controller | Signals used |
|---|---|
| LastObs-PD (T:201-209) | `cue_rel`, **`aim_az`** (world-frame hold), `w_base` (kd damping) |
| Kalman-PD (T:227-235) | `cue_rel`, **`aim_az`**, `w_base`, own world velocity estimate |
| BIO-Static (T:333-390) | `cue_rel`; `w_base` via `u_for` (T:346-347); **`seen` flag** switching decoder calibration (T:369-384); K = 2.5 (T:387). `aim_az`, `t_sim` passed but unused |
| BIO-Hybrid | Static plus `tv` from `np.polyfit` of `aim_az`-based world bearings (T:334-341) |
| BIO-NoSelf | `cue_rel` only (`u_for(0)`) |
| Freeze | nothing |

Brain calibrations (`calibrate_ring`, `calibrate_steer`) inject known angles into a private copy: offline identification, not
leakage, but a tuned stage the comparator must also get (§2).

**Is a shared kinematic `cue_rel` acceptable?** Yes for matching: it is the same stream for every arm. But it is noise-free
engineered geometry, so claims are limited to "memory of a kinematically computed bearing", with nothing about retina-to-CX
transformation. Declare κ ≠ 1 and log cue error against truth on dev seeds (~2° bias while the ball moves).

## 2. Matched scalar integrator

State θ̂ (rad, wrapped), dt = 0.01. Inputs at step k: c_k (`cue_rel` or None) and w_k = `w_base`.

- Predict: θ̂⁻_k = wrap(θ̂_{k−1} − G_s·w_{k−1}·dt). This is the same zero-order hold of w that the PEN input gets.
- Update: if c_k is not None, θ̂_k = θ̂⁻_k + α·wrap(c_k − θ̂⁻_k). Otherwise θ̂_k = θ̂⁻_k.
- Init: θ̂ = first cue; before it θ̂ = 0, ω = 0. Control: ω = clip(K·c_k) when visible (shared), else clip(K·θ̂_k, ±0.6).
- α = 1 is the PI's literal "last visible cue" (sensitivity arm). **Primary uses α tuned on dev seeds** (fixed-gain 1-D Kalman
  form), because the bump is a low-passed copy of several recent cues, not the last sample.

**Dropouts.** A visible-phase `None` is indistinguishable from onset, so every arm's memory runs through it and re-anchors on
the next cue. To keep pre-onset trajectories identical, gate onset on ≥ 30 consecutive visible steps and log `n_dropout_pre`.

**Latency.** Same cue stream and indexing, no added delay. The cue-to-bump lag (~50–100 ms) is CX dynamics; the integrator's α
covers the equivalent smoothing.

**Noise: what is fair and what is weakening.**
- Fair: same information, K, w_max and actuator; best-effort tuned α and G_s for the integrator. The CX also gets a tuned
  readout window M, a bump-offset trim and one self-motion gain c_sm before `u_for` (a raw 10-ms spike-window readout may add
  ~1.5° of aim jitter via K; to be measured).
- Deliberate weakening: injecting the CX's ε₀ (~5° SD) into the comparator, adding delay, forcing α = 1 or G_s = 1 while the
  CX is calibrated. Encoding error is a CX property; equalising it hides it.
- Labelled diagnostics, never competitors:
  - **Int-from-bump:** θ̂₀ := CX bump at onset, then scalar integration. CX minus this arm = occlusion-phase dynamics; this arm
    minus the primary integrator = encoding error.
  - **Int-noisy:** ε₀ resampled from the dev-seed distribution. **Oracle:** θ̂ = truth, reference only.

## 3. Does shared tracker + memory swap isolate memory?

**Yes for the estimator.** With the dropout gate, pre-onset trajectories are bit-identical, so e₀, arm velocity and cue history
match; any e(T) difference is due to θ̂(t). It removes the tracker-lag and `seen`-switch confounds.

**It gives up:**
- It no longer tests PFL3/DNa as controller, nor CX involvement in visible pursuit.
- "CX causally drives behaviour" is true by construction (ω = K·decode(bump)); a bump-shift perturbation only checks
  Δω = K·Δθ. Informative interventions: state reset at onset (equals the θ̂₀ = 0 arm) and Int-from-bump.
- The onset hand-off jumps ω by K·ε₀ (≈ 0.2 rad/s at 5°): part of the CX encoding cost.

**Secondary DN-readout arm, one calibration (no `seen`).**
- Fit on dev seeds only, pooling visible-held and free-memory epochs (including u ≠ 0, angles ±60°). Features: bump angle θ_b,
  EPG mean rate A, DN L−R through the same τ = 0.1/0.4 s filters.
- Model y = a + s·A·sin θ_b, a single (a, s) per Brain seed. Decode θ̂_DN = asin((y−a)/(sA)).
- Prespecified acceptance: held-out residual means in visible vs memory states differ by < 2°; otherwise report "no single
  calibration exists".
- Confounds:
  - Phase 1 found state-dependent slope (~2×) and offset (3–5 Hz, i.e. 6–17°); a pooled fit biases both states unless A is modelled.
  - Noisy θ_b attenuates the slope: smooth it or instrument with the cue.
  - Filter lags, nonlinearity beyond ±1 rad, DNa01 being a model copy, L/R asymmetry.
  - Predictor is bump angle in both states, never cue in one.

## 4. Closed-loop dynamics during occlusion

Stationary ball. e = true bearing, θ̂ = memory. Servo ≈ rate source: e′ = −κω, θ̂′ = −g·ω, ω = Kθ̂ (unsaturated), where g
is the memory's self-motion gain per unit w. Define G = g/κ, onset error ε₀ = θ̂(0) − e₀, E = exp(−gKT). Then:

**e(T) = e₀·E + (1−E)·[(G−1)·e₀ − ε₀]/G**, with fixed point e* = [(G−1)e₀ − ε₀]/G, rate λ = gK.

- Perfect memory (g = κ, ε₀ = 0): e(T) = e₀·exp(−κKT), τ = 1/(κK) = **0.46 s** (0.40 s if κ were 1); at T = 1.01 s the residual
  fraction is **0.111**. A unit-gain integrator gives 0.080; a CX with g = 1.32 gives 0.036 (fast convergence to a *wrong* fixed point).
- Freeze: e(T) = e₀ (servo coast < 0.3°).
- Gain error: asymptotic bias (G−1)e₀/G: G = 1.15 → 0.13e₀; G = 1.52 → 0.34e₀. Onset error enters as −ε₀(1−E)/G, not attenuated.
- Saturation: |θ̂| > ω_max/K = 0.24 rad (13.8°) clips ω at 0.6; aim slews at κ·0.6 = 29.7°/s (≤ 30.2° in 1.01 s). G matters only
  once θ̂ < 0.24 rad.
- Windup clamp: ctrl stays within ±0.02 rad of qpos. Servo kp = 998, kv = 2.73, damping 0.6, force limit 2.94 N·m
  (`so101_upstream.xml:23-27`); steady lag (kv+b)ω/kp ≈ 3 mrad at 0.6 rad/s, and the torque limit allows ~0.88 rad/s. The clamp
  (33 ms of max-rate lag) should not bind in free motion; **log |ctrl − qpos| to confirm.** Memories use measured qvel, so any
  windup loss is seen by them. A 20 ms extra lag changed the simulation by < 0.1°.

Numbers (κ = 0.87, T = 1.01 s; degrees; ε₀ = 0 / +5 / −5):

| e₀ | Freeze | g = 0.87 (ideal) | g = 1.0 | g = 1.32 (CX nominal) |
|---|---|---|---|---|
| 6° (steady lag, 13°/s ball) | 6 | 0.7 / −3.8 / 5.1 | 1.2 / −2.8 / 5.2 | 2.2 / −1.0 / 5.4 |
| 20° | 20 | 2.4 / −1.5 / 6.7 | 4.1 / 0.4 / 8.0 | 7.3 / 4.3 / 10.5 |

Consequences:
- At e₀ ≈ 6° the endpoint is dominated by ε₀ and gain: a 5° encoding error makes an ideal memory no better than freeze.
- Dynamic range ∝ e₀: use onset strata with |e₀| ≈ 15–25° (random start azimuth or speed), not just the natural 6°.
- "~0 at reappearance" is limited by the shared visual bias at the last cue; compare to the integrator, not to 0.

## 5. Moving target

- Fair comparator: a constant-velocity filter on x = [θ_e, ν], θ̇_e = ν − G_s·w_base, measurement = cue (no `aim_az`);
  equivalently α-β. Q, R tuned on dev seeds, R from the measured cue residual.
- The bump carries bearing only. Its best is "static memory + self-motion", floor |e| ≈ νT (13.5° per 1 s). It has no
  mechanism to beat a CV filter; BIO-Hybrid's +7.3° deficit is expected.
- Phrase it as a ladder:
  1. CX-static vs Int-static equivalence on the moving target, pre-specified margin δ.
  2. **Matched-velocity** hybrid: CX ring and scalar integrator both integrate ν̂ − w with the *same* ν̂ from the CV filter:
     is the ring as good an integrator, not does it estimate velocity.
  3. CV-Kalman as upper reference only (what velocity information buys), no superiority claim.

## 6. Tuning parameters (dev seeds 100–129 only; freeze, hash, commit before seeds 0–39)

| Arm | Tuned | Fixed |
|---|---|---|
| Shared | none | K = 2.5, w_max, windup, onset gate (30 steps), e₀ strata |
| Integrator | α, G_s, optional leak λ (default 0) | wrap, ZOH |
| CX (bump) | c_sm (pre-`u_for` gain), readout window M, offset trim b₀ | Brain constants `P`, `calibrate_ring` |
| CX (DN) | (a, s) per Brain seed, amplitude model, which DN channel | filters τ = 0.1/0.4 s |
| CV filter | Q, R, κ̂, initial P | CV model |
| Diagnostics | ε₀ distribution, Int-from-bump | none |

Rules: same objective for every arm (mean |e(T)| on the stationary dev set, or internal θ̂-error) and equal evaluation
budget; report nominal and tuned settings; never tune on held-out seeds (dev seeds were seen in phase 1; label them "dev").

## Strongest objection to the PI's architecture

With one noise-free bearing, a stationary target and a measured rotation rate, the scalar integrator is the sufficient
statistic. The CX can only tie it or lose, so "causally improves beyond" is unreachable by design, and ω = K·decode(bump) makes
the CX drive behaviour by fiat. Differences will mostly reflect ε₀, gain calibration (κ = 0.87 vs `u_for` 1.32) and readout
noise, which are engineering. Reframe as a pre-specified non-inferiority claim, or add regimes where recurrence could help:
cue noise, distractors, long gaps.

---
## PI verification and corrections (2026-10-27)
- **κ is wrong in direction.** Measured on dev Exp A records (Scalar arm, seeds 200/202/204, passive ±20°), the ratio
  (true egocentric bearing change) / (∫ w_base dt) is **1.105** (range 1.101–1.107, 6 trials), not 0.87. The aim point lies in front
  of the pan axis, so the aim azimuth about the world origin changes ~10 % more than the joint angle. A unit-gain integrator
  therefore UNDER-compensates by ~10 %; the CX's open-loop gain 1.32 corresponds to ~1.19× the required value. The §4 table's
  κ = 0.87 column should be read with κ = 1.105 (τ_perfect = 1/(κK) = 0.36 s).
- Accepted: one shared, dev-derived kinematic self-motion scale λ (= κ) is applied to w_base for **both** memories
  (scalar: λ·w_base; CX: u_for(−λ·w_base)), so neither arm gets a private geometric correction.
- Accepted: the "beyond a matched integrator" question is near-unreachable as superiority in this noise-free-w_base regime;
  the protocol states the CX-vs-scalar contrast as non-inferiority with superiority only as a secondary, expected-negative test.
