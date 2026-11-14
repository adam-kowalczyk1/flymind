# Red team r1 — STAGE1B_DESIGN.md (d1)

Verdict: **PASS_WITH_FIXES.** No fatal flaw, but 2 blockers, 5 majors, 4 minors. The design is honest about margin shopping; it is not honest enough about
(a) H1b being a replication, (b) Hm4 carrying no new information, (c) mean-diluted harm tests. Re-simulation used only seeds 9 129 003, 9 129 010–017
(smoke-style, scratchpad only, nothing written to results/). All Stage-1 numbers below recomputed from `stage1/results/confirm/*.json|npz` (read-only), n = 400.

## Blockers

**B1. Harm tests are population means; the stated question is "does not harm when the target is visible" — and a visible-target subgroup IS harmed.** (§2, K-b)
- Evidence (npz, S, gated): scan engages (RMS θ_s > 5 % of sin) in 95/400 = 23.8 % of S trials, > 30 % in 13 %. In the engaged trials, tracking cost rises
  +0.82° (CI95 ±0.14; 0.6–1.7° by tertile) — above the Hm3 margin 0.5° — while the population mean is +0.17° (UB 0.23). 10.3 % of S trials get > +1° (sin: 26.8 %).
- Cause: the gate keys on |ω| (cl_sense.py:133), not on detection; once the target is centred and the V5 limit cycle is absent (S "none" path: 10th pct 1.7°, median 40°),
  ω is quiet for 1 s and the scan restarts on a visible, centred target. 343/400 S trials had 0 gate toggles, 35 had 2, 17 had 4 (reconstructed from θ_s).
- Consequence: Hm1–Hm3/Hm6 will almost surely return NOT-HARMFUL (Stage-1 UBs: Hm1 0.029 vs 0.05, Hm2 0.105 vs 1, Hm3 0.23 vs 0.5, Hm6 0.103 vs 1) and the word "bezpieczny przy widocznym celu" (K-b) would be unearned.
- Fix: add Hm7 (frozen text): "S, as-treated stratum: trials where the gated arm's injected path Σ|Δθ_s| (0.75–4.75 s) > 10 % of the sin arm's population mean; paired Δ track-cost vs the
  same unit's none; margin 0.5°; report stratum size". Post-treatment conditioning is acknowledged as descriptive-causal limited; alternatively Hm7' = fraction of S trials with
  injected path > 10 % of sin ≤ 10 % (Stage 1: 20 % → would FAIL, which is the honest result). Reword K-b to "population-mean harm absent" unless Hm7 is NOT-HARMFUL.

**B2. Feasibility/cost statement is wrong by ~2x and k = 5 is not "borderline".** (§1, §5)
- Stage-1 wall: mean 5.39 s/trial (221 s/unit, 41 trials, 4 workers); my solo run 4.7 s/trial. Design assumes 2.1 s/trial. 21 trials × 5.4 s × 400 / 3 procs ≈ **4.2 h** (≥ 3.5 h), not 1.7–2.5 h.
- k = 5 with this code gives 288 `vision_stale` invalid ticks of 600 (gate stale 288, usable 307) — float age 5·0.01 > 0.05. k = 3 and k = 4: 0 invalid, 0 flags (seed 9129003, W, gated). So "k ≤ 4 safe, 5 borderline" should read "k ≥ 5 unusable".
- Fix: replace §5 cost line with 3.5–4.5 h and state the stop rule in wall time; state k ≥ 5 invalid (measured).

## Majors

**M1. Metric shopping: disclosed, but the "calibration" arm is circular and Hm6 is vacuous.** (§0, §2, K-d, Hm3/Hm4/Hm6)
- Margins 0.5° and 5° lie between gated (+0.17 / +3.0) and sin (+0.67 / +6.7) *by choice*; sin is then declared the positive control (K-d). Sin flagging is therefore near-certain and only
  shows that the margins sit between two known values, not that the metric detects harm. K-d "sin NOT-HARMFUL → metrics do not detect" can almost never fire — no information. Say so.
- Hm6 (S10): gated − none = 0.084° CI ±0.019 vs margin 1.0° (12x). Passes by construction (gate off in S). Keeping it as a necessary condition costs nothing and means nothing; it also drops the W half of the original S10 (Hm6 lists S only). State "Hm6 = vacuous, retained only for continuity" and keep W+S as in `analysis1.py:142`.
- Better-anchored margins (anchors independent of the gated/sin outcomes):
  - Hm3: 0.5° = 10 % of the frozen success tolerance `loop.metrics(tol=5.0)`; Hm2: 1° = 20 % of it. Say that this is the anchor (it happens to equal 0.5).
  - Hm4/injected motion: use the *requested* sensing path Σ|Δθ_s| (not loop-cancelled), margin = 10 % of the full-scan path (sin mean 31.5°, 4 cycles x 4 x a_pan, measured from Stage-1 θ_s) ≈ 3.1°; Stage 1 gated = 1.81° (5.7 %), UB ≈ 2.2°, 20 % of trials > 10 %.
  - Hm1: 0.05 = half of SESOI (already a priori).
- Add to §2 an explicit table "predicted from Stage 1 → expected class" and a joint pass probability (Hm1 ≈ 0.96 x Hm4 ≈ 0.95 x H1b ≈ 0.91 ≈ 0.8); INCONCLUSIVE blocks, so 20 % of clean runs fail on noise.

**M2. H1b is a pure replication; Stage 1 already measured it.** (§2, §5)
- Same code, same ranges (`stage1_confirm_params.json`: W ρ 0.22–0.36, az 8–16), same SESOI. Stage 1 gated − none, W: +0.1225, SE 0.0179, paired SD 0.3575, discordant pairs 53 vs 4 (z ≈ 6.9).
  The only live risk is "estimate ≥ 0.10" (winner's curse). Power re-simulated from the Stage-1 paired differences (2000 reps, seed 9 129 001 stream, bootstrap of dg + shift): 0.908 / 0.7255 / 0.516 for true Δ 0.1225 / 0.11 / 0.10 — §5's 0.90/0.72/0.53 verified.
- Cost of the replication inside the 21-trial matrix is ≈ 6 of 21 trials per unit (DATA none/gated W + N), i.e. < 30 % of the 4 h; it also supplies the none arm for Hm1–4 so it is not free to drop. But the 400-unit sizing is driven by H1b's ≥ SESOI rule, not by harm tests (Hm1–Hm3 need n ≈ 100).
- Fix: label H1b "pre-registered replication on fresh seeds" (not "test glowny, nowy"); or drop the est ≥ SESOI clause for replication (use lo95 > 0 and lo95 ≥ 0.5·SESOI) and halve n; or keep 400 but say why (winner's-curse insurance). Do not call it independent evidence of the Stage-1 mechanism: same simulator, same code, same decoder.

**M3. Hm4 on measured q0 adds no information and is non-additive.** (§1 table, Hm4, §5)
- `cl_sense.run` returns `q0=q0_tr` (line 213), filled at line 141 *at the start of tick k, before `sim.act`/`step`* (state after the previous command). Radians, MuJoCo double: no quantisation, no noise (nonzero Δ min ≈ 1e-3°).
- Measured vs commanded path over 75:475 (8 units, 9 129 010–017): none 41.7 vs 41.3, sin 51.5 vs 51.1, gated 43.9 vs 43.4 — measured ≈ commanded + 1 %. §1's "zmierzone q0 może być gładsze przez serwo" is false; the Stage-1 npz (pan + θ_s) already gives the answer:
  commanded path gated − none, S: +3.01°, CI95 [2.15, 3.86] (n = 400); sin: +6.66° [4.76, 8.56]. So Hm4 is decided by existing data (UB 3.86 < 5), and "moc Hm4 jest przybliżona" is avoidable: it can be computed exactly now.
- Non-additivity / trivial pass: path is dominated by V5 limit cycle, SD 22° (none S), bimodal (9129011: 0.03°, 9129017: 3.3°, others 35–65°). Paired SD of gated − none = 8.7° (cmd, n=400) / 10.8° (n=8): a scan that perturbs the limit cycle can *lower* path (4/8 units gated < none) and offset the added scan motion. Gated could pass Hm4 by suppressing the cycle while adding scan. Use the injected-path measure (M1) or report both; if q0 is kept, say it is only a sanity duplicate.

**M4. Delay implementation: works, but the spec is incomplete.** (§4, §6, T2, K-c)
- Verified: `DelayLine(k, fill)` (latency.py:94) — `CS.DelayLine = lambda _k, init: DelayLine(k, init)` is picked up by `run` via module-global name (cl_sense.py:111) and restored in `finally` (checked `is orig`). First k ticks: `push` returns `fill=None` → `s_usable False, age 0.0, img None` (lines 170–171); gate never sees them (frames = 597 for k=3), safety gets age 0.0 → no `vision_stale`; encoder returns g = 0 (encoder.py:52). So the first 3 ticks (30 ms) are blind-by-construction and not counted invalid; real age is exactly 0.03 s ≤ 0.05.
  Say so, and note that `delay=0` arm under the same lambda must be bit-identical (below).
- Bit-exact check IS feasible: I re-ran unit 9112001 DATA gated W and S with the lambda at k=0 → e (after `np.float32`), pan, θ_s, ω, spike counts all `array_equal` to the stored npz. Needed inputs: `Networks(...)` DATA net is unit-independent (`network(L.J0)`), slope key `confirm|DATA|0` = 501.329, ranges/ω_on from `stage1_confirm_params.json`, `pixel_noise(u)`, `draw(u, ranges)`, `gain_for(tr)`, seed u for ALIF. Compare in float32 (stored e is `round(.,3)` then float32). Put this in the test text.
- T2 is ambiguous: "Δ(DATA gated, 3) − Δ(DATA gated, 0)" with Δ = gated − none per delay presumably. Define explicitly. K-c (est ≤ −0.10 and hi < 0) lets a gain collapsing from 0.12 to 0.04 pass. Add: delay-3 gain Δ3 = gated3 − none3 must itself have lo95 > 0, else no "survives delay" statement and no Stage-2 recommendation.
- Hardware camera is 50–100 ms (k = 5–10): the experiment cannot represent it (limit in §8 item 3 is right); the recommendation text must say "up to 30 ms".

**M5. Seed registry not updated; reservation exists only in the design.** (§7)
- Collision claim verified: `grep -rE '(^|[^0-9.])9[ _]?12[0-9][ _]?[0-9]{3}([^0-9]|$)' flymind bio2` → only `stage1b/STAGE1B_DESIGN.md` itself (plus a float-digit hit in `results/v5v41/analysis.json` and a hex-digest hit in `integrity_pre_snapshot.json`; neither is a seed). OK for *.py/*.md.
- But `SEED_REGISTRY.md` has no 9 12x entry (checked), and §7 text says "zarezerwowane" while the registry is the registered authority. Add the Stage-1b block to `SEED_REGISTRY.md` (not by me) before the manifest is written. Red team r1 used only 9 129 003 and 9 129 010–017 (record as consumed).
- Stat RNG: `stat_boot` uses `[seed, crc32(key)]`; new test keys (Hm1b…, T1–T3) must be new strings; list them or reuse of the Stage-1 key names (e.g. "S10S") with a new seed is fine but must be said.

## Minor

**m1. Gate chattering (Q5).** Bounded by construction: re-enable needs 1.0 s quiet + 0.25 s ramp (cl_sense.py:137–139), so ≤ ~3 on/off pairs in 4 s; observed (S): 0 toggles 343, 2 toggles 35, 4 toggles 17 (max 4); W mean 0.98, N 0. S10 sees only the 1 Hz component, Hm3/4 only means, so slow gate cycling (0.4–0.8 Hz) is invisible, but its effect is the B1 subgroup. Do not add a toggles-count *test* (no a-priori anchor); make "toggles/trial and scan-on fraction in S, W" mandatory descriptive plus Hm7 (B1).
**m2. Decision rule (§6, Q6).** INCONCLUSIVE-blocks is defensible but state the cost (≈ 20 % false block). Missing: (i) harm in range W (gate is ON 72–79 % of W; path gated − none in W +30.8°, CI [30.0, 31.6] — intended, but wear/energy is not a harm test; say "accepted by design"); (ii) safety flags and invalid trials as a **frozen STOP criterion** (design only gives > 1 % units invalid at run; add: any DATA gated safety flag in S/N > 0 → K-b); (iii) TH arm role: T1 uses TH gated, but TH none W success is 0.165 (Stage 1) — outside nothing, measurable, but `meas()` gate (0.1–0.9) should be applied as in `analysis1.tests` (S4 NOT TESTED rule) — currently unspecified; (iv) "Holm nad trzema, testy równoważności": `classify` p tests Δ = 0, EQUIVALENT uses CI90 (TOST) unadjusted; say which; (v) `harm()` returns "UNDETERMINED" (analysis1.py:78), the design says "INCONCLUSIVE" — align wording.
**m3. T1/T3 power.** T3 (gated − sin W): Stage 1 −0.005; T1 proxy (TH sin − DATA gated) paired SD 0.44 → CI90 half-width 0.036, ample for ±0.10 if true diff ≈ 0, but TH gated is a new arm: no prior. Fine; note T3 is a second replication (S7).
**m4. Runtime/ops.** `test_runner1b` must also assert `CS.DelayLine` restored after an exception (planned) and that worker processes (Pool) never share the patch (patch per trial inside the worker — state it). Planned smoke seeds 9 128 001–020 OK. Estimated disk: 21 trials x npz is small; add q0 as float32.

## Answers to the numbered attack questions (short)
1. Honest about margins being post-data (§0, §8.1) — yes; sufficient — no (M1: sin-calibration circular, Hm6 vacuous, Hm4 redundant). Anchors proposed in M1.
2. H1b = replication (M2); power numbers verified (0.908/0.7255/0.516); 400-unit/4 h is driven by the est ≥ SESOI clause, not by any harm test.
3. q0 is returned and sampled at tick start (line 141), no quantisation; measured ≈ commanded; limit-cycle dominated; can be gamed by cycle suppression (M3).
4. Patch correct; k = 3 → age 0.03, 3 initial None ticks, 0 invalid; k = 5 breaks (B2); bit-exact test feasible and I reproduced it (M4).
5. Chatter bounded; engaged subgroup is the real issue (m1, B1).
6. Rule needs delay-3 gain CI, safety-flag criterion, Hm7, wording (M4, m2).
7. Collision claim true; registry not updated (M5).
8. Also: Stage 1 W gain exists only for ρ < 30 cm (gated − none by ρ band <26 / 26–30 / ≥30 cm: 0.133 / 0.301 / 0.000, n = 113/113/174): the "recommendation" rests on a 0.26–0.30 m band; report H1b by band as pre-registered descriptive and state it in the recommendation text.
