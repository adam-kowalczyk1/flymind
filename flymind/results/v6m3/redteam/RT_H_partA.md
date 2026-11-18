# V6m3 red team — RT-H (Part A and implementation), 2026-10-30

Scope: `v6m3.py` (run3, a_vectors, calibrate/cal_job, part_a_one, job_run Part A, the r2 fallback), Part A results and their
interpretation in `results/v6m3/REPORT.md` (DRAFT), and the r1→r2 story. MODEL level only.
Own simulations: seeds 8 499 001–099 only (new B1 LC×LC instances 8 499 001–003; noise reps 8 499 011–018; calibration
8 499 021–024; LCIRC rng 8 499 031). CPU ≈ 8.5 min. Nothing outside `results/v6m3/redteam/` was written. Scratch:
`redteam/RT_H/` (`rth_partA.py`, `rth_partA_raw.json`, `rth_analyze.py`, `rth_analyze_stdout.txt`, `repro_check.py`, `repro/`,
`rawcheck.py`, `netcheck.py`).

## 1. Implementation audit
- **Engine.** `run3` = `ALIF(data, P, sd, gain)` + `v6m2.step2` with keepleak 1. Gain multiplies `g + I + σξ`. Bias is added to I
  before noise. `t_ref` maps to blocked steps as ceil: 0 → 0, 1 → 1, 2 → 2, 2.2 → 3 (REF), 4 → 4. With t_ref 0 the **hard reset is kept**
  (v → v_reset on every spike, g kept), so MT0 removes only the block. The noise RNG is drawn for all N neurons on every step, so the
  noise is common across conditions and sources for the same seed (correct pairing). I wrote a generalized engine (adding per-neuron
  tau_syn, a synaptic-increment scale, and b_a). It equals `M3.run3` bit for bit in REF in all 128 of my cells, including the B1 sources.
- **a_vectors** touches only the intermediates (also covered by test_v6m3). LCIRC uses REF vectors. OK.
- **Calibration**: monotone curves, picks inside the grids (gain 16.10 Hz at 0.725, bias 16.31 Hz at −7.0, versus ref 16.22). OK.
- **Does gain also scale noise, and is that a confound?** It does scale noise: σ_eff = 1.45 mV at the intermediates in MT0G. It is
  **not a material confound.** The intermediates get no external I, so gain only scales g and the noise. MT0S (t_ref 0 with synaptic-only
  scaling, noise σ 2 unscaled, recalibrated on my seeds) picked the same value, 0.725. It gives D_rel +1.0 % and F_A 1.10, against
  MT0G +0.9 % and 1.09.
- **LCIRC RNG** `SeedSequence([8 446 000, 9, r])` depends on rep only. The same per-neuron offsets are therefore used for both levels,
  both sides, DATA and every B1 instance (pairing is fine), and **MAIN and REPLICATION** (so the LCIRC replication is not
  seed-independent at the manipulation level; only the noise differs). There is no collision with the count-swap stream (set_id ∈ {0,1} ≠ 9).
  It is sensible but under-specified: the protocol does not define the stream.
- **REF-vs-free identity check (V2)**: runs for the DATA source only. It is close to a tautology (same network, same seed, LC forced to
  the spikes LC would emit anyway). It does validate step2 ≡ ALIF.step and RNG alignment. It cannot detect source-construction errors or
  errors in the ablations. Valid but weak. My cross-engine identity across B1 sources and my check that B1 differs from DATA only
  inside LC×LC (10 844 entries, all within LC×LC) supplement it.
- Count-swap stream (Part B, in passing): the code uses SeedSequence([8 446 000, set, level, side, rep, source]), one generator
  consumed by DB and then by BD. The protocol §1 also lists a "neuron-block" word. This is a minor protocol/code mismatch.

## 2. r2 fallback story (file times, logs)
- Times: r1 protocol, v6m3.py and test were hashed at 17:29:21. The analysis script was hashed at 17:30:19 (mtime 17:30:17).
  calibration.json and the r1 config are from 17:30:54. Kept r1 npz were written 17:31:20–17:33:00. v6m3.py, the protocol and the test
  were edited at 17:33:44 and hashed at 17:33:46. The r2 config (17:33:53) lists 4 jobs (REP 017–020), and their npz were written
  17:34:30–34. run_done is from 17:34:34 (Stage 1 28/28), analysis.json from 17:34:47, REPORT from 17:36:00. The sequence is consistent.
- **Count error**: `stdout_r1_crashed.txt` contains **18** job results (MAIN_DATA, MAIN 001–010, REP_DATA, REP 011–016), and 18 npz
  predate the r2 edit. 18 + 4 = 22. Protocol r2 and REPORT §1 say "17/22".
- "Completed r1 jobs are identical under r2": I re-ran rep 0 of two kept jobs (REP_B1_8421016, MAIN_B1_8421003) with the r2 code
  (same inputs, no new seeds spent). A, B and `added` are **bit-identical** to the stored npz, and all checks are true. test_v6m3 passes.
  There is no archived copy of the r1 v6m3.py, so the r1 code diff itself cannot be checked; this behavioural check covers it.
- Fallback counts (017: 1, 018: 4) match stdout.txt. Both jobs would have raised in r1, which is consistent with the crash in a REP job.

## 3. Rate matching per level, per side and per subpopulation (existing raw data + mine)
- DATA intermediate ipsi rate, MT0G/MT0B vs REF. Per level: MAIN 8 mV 485/487 vs 471 (+3 %), 9 mV 667/685 vs 694 (−4/−1 %). Mine:
  8 mV 13.4/13.3 vs 13.0 Hz, 9 mV 18.8/19.3 vs 19.4 Hz. Per side it is within about ±6 %. Matching therefore holds per level and per side
  to a few %.
- **Composition is not matched.** Matching fixes the ipsi mean, but the DNa02-inhibiting intermediates (4 per side) are nearly
  silenced. D_inh (DATA) is −383 in REF, −39 in MT0G and −19 in MT0B (MAIN). Mine: −392, −44, −19.5. The mean rate of all excitatory
  intermediates drops from 7.0 to 6.1 (MT0G) and 5.6 Hz (MT0B). This does **not** drive F_A: the same compositional change with the block
  intact (RB: D_inh −4.7) leaves the deficit untouched (below). REPORT nevertheless omits D_inh, a pre-registered outcome.
- Per source: B1 is the outcome, not matched (by design).

## 4. Attempts to falsify H-IR (own seeds, 3 new B1 instances, 8 reps, 8/9 mV, L/R; CI = jackknife-t over reps)
| intermediate condition | D_rel | CI | F_A | DATA int. Hz | D_inh D / B1 | DN gap Hz |
|---|---|---|---|---|---|---|
| REF (3 blocked steps) | −10.9 % | −12.8; −9.0 | 0 | 16.2 | −392 / −409 | −23.1 |
| MT4 (4 steps) | −12.0 % | −13.9; −10.1 | −0.10 | 14.9 | | −21.8 |
| MT2 (2 steps) | −9.4 % | −11.1; −7.7 | 0.14 | 17.9 | | −25.7 |
| **MT1 (1 step)** | **−6.7 %** | −8.3; −5.0 | **0.39 (0.32; 0.47)** | 20.3 | | −29.4 |
| MT0 (0 steps, hard reset kept) | 0.0 % | −1.6; +1.5 | 1.00 | 24.3 | −340 / −526 | −32.6 |
| MT0G (gain 0.725) | +0.9 % | −0.6; +2.5 | 1.09 | 16.1 | −44 / −89 | −25.4 |
| MT0S (syn-only gain 0.725, σ unscaled) | +1.0 % | −0.7; +2.8 | 1.10 | 16.2 | | −25.4 |
| MT0B (bias −7) | +4.3 % | +2.7; +6.0 | 1.40 | 16.3 | −19.5 / −23.8 | −23.9 |
| RG: block kept + gain 0.725 | −9.7 % | −11.7; −7.7 | 0.11 | 11.4 | | −20.9 |
| RB: block kept + bias −7 | −11.0 % | −13.1; −8.9 | −0.01 | 10.1 | −4.7 / −4.7 | −20.0 |
| RBP: block kept + bias +3 | −10.8 % | −12.9; −8.7 | 0.01 | 20.0 | | −24.7 |
| RNA: block kept, b_a 0 | −11.5 % | −14.0; −9.0 | −0.05 | 23.8 | | −22.5 |
| RTS10: block kept, τ_syn 10 (charge-preserving) | −8.5 % | −10.6; −6.3 | 0.23 | 16.4 | | −21.0 |
| LCIRC (REF) | −4.7 % | −6.6; −2.8 | 0.57 (0.43; 0.71) | 16.2 | | −5.3 |
| **MT0 + LCIRC** | **−6.1 %** | −8.3; −4.0 | 0.44 | 20.9 | | −6.2 |
| **MT0B + LCIRC** | **−7.3 %** | −9.9; −4.6 | 0.34 | 11.8 | | −7.5 |

Findings:
1. **Replication**: REF, MT0, MT0G, MT0B and LCIRC reproduce the reported values within about 1.3 points on independent noise seeds and
   independent B1 instances. Per instance REF ranges −10 to −12 %, MT0G 0 to +2 % and MT0B +3.5 to +5 %.
2. **Dose-response in the block is monotone** (4 → 3 → 2 → 1 → 0 steps: −12.0, −10.9, −9.4, −6.7, 0.0 %). **t_ref 1 does not already
   remove it**: one blocked step keeps 61 % of the deficit.
3. **Specificity**: changing the rate or operating point with the block intact leaves the deficit in place: gain (RG), bias down (RB, the
   same −7 mV and the same inhibitory-intermediate silencing as MT0B), bias up (RBP), and no adaptation (RNA). Slower intermediate
   synapses (RTS10) cut the deficit by 23 %, which is consistent with a block × input-synchrony interaction. **Hard reset is not the
   cause**: MT0 keeps it and the deficit vanishes. The noise scaling under gain is not a confound (§1).
4. **"Eliminates the deficit" is a cancellation, and F_A is not a share (main correction).** Split D_rel into a synchrony-dependent part
   S = D_rel(real) − D_rel(LCIRC) and a non-synchrony residual D_rel(LCIRC):
   - REF: S = −6.2 points, residual −4.7 %.
   - MT0: S = **+6.1** points, residual **−6.1 %**.
   - MT0B: S = **+11.6** points, residual **−7.3 %**.

   Removing the block removes the synchrony penalty. It also **turns B1 synchrony into a gain** (intermediates burst, ISI ≤ 4 ms in
   62 % of B1 intervals vs 51 % in DATA). It does **not** remove the ≈ 40 % non-synchrony residual, which persists or grows (−6 to −7 %).
   The net ≈ 0 under MT0/MT0G is a near-cancellation of the two parts. MT0B's F_A > 1 is that bonus exceeding the residual. It is a
   genuine model effect, not a numerical artifact, since RB shows that bias alone does nothing. Their own MAIN LCIRC F_A of 0.63
   (0.47; 0.81) bounds the refractoriness-attributable part at roughly 0.6 of the deficit, not ≥ 1.
5. Under MT0 (unmatched), B1 recruits far more DNa02-inhibitory intermediate drive (D_inh B1/DATA: mine −526/−340; MAIN −536/−291).
   The persistent or larger DNa02 gap under MT0 (−33 Hz) is therefore not shown to be "carried by timing". Inhibition is a competing
   contributor, though small in absolute terms (about −2 % of net drive). Part A does not test timing.

## 5. Verdict: **PASS_WITH_LIMITATIONS**
The pre-registered H-IR rule is met. It replicates on independent seeds and B1 instances, the code is correct, and the r2 fallback is
honest and behaviourally verified. The block-specificity of the synchrony-dependent deficit survives all my falsification attempts.
The REPORT's interpretation overstates the result: refractoriness accounts for the synchrony-dependent ≈ 60 % of the deficit. Its
removal leaves the rest in place and offsets it with a synchrony gain.

## 6. Required corrections to REPORT.md
1. §1 and protocol r2 note: "17/22 jobs had completed" → **18/22** (stdout_r1_crashed.txt lists 18 results, and 18 npz predate the
   17:33:44 edit). Add that a re-run of kept r1 jobs under r2 was bit-identical (this review).
2. §2/§3 QA: replace "removing it … eliminates the deficit" with: removing the intermediate block abolishes the **synchrony-dependent**
   part of the deficit (≈ 0.6; LCIRC F_A 0.63 MAIN) and reverses its sign (synchrony becomes a gain). The non-synchrony residual
   (LCIRC −3.9…−4.7 %) is not removed by t_ref 0 (MT0+LCIRC −6.1 %, MT0B+LCIRC −7.3 %, RT-H). Net ≈ 0 is a cancellation.
3. State explicitly that F_A is not "the fraction caused by refractoriness". It can exceed 1 because the t_ref 0 regime adds a
   synchrony bonus. "Most" rests on the synchrony-dependent share (~0.57–0.63, CI low ≈ 0.43–0.47), which is close to 0.5. Keep the
   pre-registered label SUPPORTED, but add this qualifier.
4. Report D_inh (a pre-registered outcome) for every condition. Note that rate matching fixes the ipsi mean only: DNa02-inhibiting
   intermediates are almost silenced under MT0G/MT0B (D_inh −383 → −39/−19) and the mean excitatory-intermediate rate falls about
   15–20 %. Cite RB (block kept, the same silencing, full deficit) as showing this does not drive F_A.
5. §3: delete "now carried by timing (see QB)" for the Part A conditions, or qualify it. Under MT0, B1 recruits +55–84 % more
   inhibitory drive to DNa02, so timing is untested in Part A.
6. §4: the limitation "intermediate gain also scales intermediate noise" can be resolved. Synaptic-only scaling with σ unscaled gives
   the same calibration (0.725) and F_A 1.10 vs 1.09 (RT-H).
7. Add the dose-response and specificity results as supporting evidence: t_ref 1 keeps 61 % of the deficit (F_A 0.39); the block
   kept with gain, bias ±, or b_a 0 leaves F_A ≈ 0; τ_syn 10 gives F_A 0.23. Do not claim that "the" refractory block of 3 steps is
   needed: any non-zero block leaves a substantial deficit, and the largest single step is from 1 to 0 blocked steps.
8. Methods: document the LCIRC stream `SeedSequence([8 446 000, 9, rep])`, which is shared across levels, sides, sources and MAIN/REP.
   LCIRC replication is therefore noise-only. Also note the count-swap stream deviation (no neuron-block word; one generator for DB
   then BD).
9. Per-side heterogeneity: report that MT0 D_rel differs in sign between sides (MAIN 8 mV L −0.7 %, R −3.3 %; 9 mV R +4.8 %; mine L
   −2.6 %, R +2.3 %). "Eliminated" holds only on aggregate.
