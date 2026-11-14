# V6m2 red team RT-E: independent replication and implementation audit (2026-10-30)

Reviewer RT-E. Scope: an independent replay written from alif.py's equations, a replication of the MAIN-arm core cells, and an audit of v6m2.py and v6m2_analysis.py.
Seeds used: noise 8 498 501–504 (4 reps), bias calibration 8 498 511–514, manipulation SeedSequence([8 498 530, src, level, side, rep]), audit 8 498 580/581/590/591,
bootstrap 8 498 598/599. B1 instances 8 421 011–015 (not used in V6m2). CPU about 5.5 min in total. No existing file was modified, and nothing was committed.
Scratch: `results/v6m2/redteam/RT_E/` (`rt_e.py`, `rt_e_analysis.py`, `rt_e_biasgrid.py`, `rt_e_audit.py`, `*_raw.json`, `*_stdout.txt`, `rt_e_biasgrid_ci.txt`).

## 1. Own implementation (no v6m2.step2/run, no v5v43/v6m step code)
- `clamped()` is my own transcription of the ALIF step, with forced spikes. It is bit-identical to `alif.ALIF.run` when nothing is clamped (self-check, B1 8 421 011, seed 8 498 590).
- `dn_only()` is a DNa02-only replay. Its drive is W[DN, mid] · mid(t − 2). The weights show W[DN, LC] = 0 and W[DN, DN] = 0, and the network has no neurons other than LC, mid and DN.
  The DN noise is taken from the DN columns of default_rng(sd).standard_normal((T, N)). M0 × REF matched the full clamped replay bit for bit in all 144 runs.
- MASYNC uses its own sampler, a different algorithm from V6m2's. n spike-blocks of length 4 are shuffled among L − 4(n − 1) − 1 free slots. An empirical uniformity test
  (n = 2, L = 9: all 15 admissible configurations hit, each 1700–2300 of 30 000) passed. Counts were exact in 300–1000 ms, ISI ≥ 4 held, and 0–300 ms was unchanged in every run.
  MCIRC is my own per-neuron roll. MASYNC_W is new: exact counts kept separately in [300, 500) and [500, 1000), to test whether counts are being moved into the analysis window.
- Own bias calibration (DATA, M0, levels 7/8/9, L/R, 4 calibration seeds, grid −60…0 step 2): **b\* = −40 mV** (V6m2: −38). REF DATA rate 85.1 Hz.

## 2. Replication (MAIN; DATA + 5 new B1; 7/8/9 mV; L/R; 4 reps). CI = wider of hierarchical-bootstrap percentile and jackknife-t (3 df)
| statistic | RT-E | V6m2 |
|---|---|---|
| gap REF·M0 | −22.8 (−28.7; −16.9) | −20.7 |
| Δt REF (MASYNC) | +7.1 (+3.5; +10.7) | +8.1 |
| Δt T0 | −12.7 (−18.9; −7.3) | −7.2 |
| Δt T0B | −15.0 (−25.3; −4.8) | −13.0 |
| **I = Δt(REF) − Δt(T0B), Hz** | **+22.1 (+15.4; +28.8)** | +21.2 |
| **I, log** | **+0.63 (+0.51; +0.75)** | +0.55 |
| I(T0), Hz | +19.8 (+16.9; +22.6) | +15.4 |
| I(T0B) with MCIRC, Hz | +23.2 (+12.3; +34.2) | +18.2 |
| gap T0B·M0 | −3.8 (−11.1; +3.5) | −4.0 |

The primary interaction replicates in sign and size. All five B1 instances give I between +21.0 and +23.2, and both sides agree (L +19.4, R +24.8). All criteria (a)–(c) of the decision rule would also pass here.
**Count-redistribution check:** I tested whether MASYNC moves spikes from 300–500 ms into 500–1000 ms. It does slightly: it lowers B1's excitatory drive to the ipsilateral DN in 500–1000 ms by 4.4 % and DATA's by 1.4 %.
MASYNC_W keeps the counts in each window and gives Δt REF +9.5 and I +23.8 (+15.1; +32.4). So redistribution does not explain the effect.

## 3. Implementation audit (`rt_e_audit.py`, B1 8 421 011, R, 9 mV, MASYNC)
- **Does T0B's bias leak into other neurons?** No. `run()` copies I and adds the bias to the DNa02 columns only. Every non-DN row equals the clamped LC and mid trains in all six DNa02 dynamics.
  The DN trains from v6m2.run match my replay bit for bit for REF, T0, T0B (bias −37), T1, T6 and NOLEAK. Blocked steps are 3 / 0 / 1 / 6 for t_ref 2.2 / 0 / 1 / 6, as claimed.
- **Does NOLEAK keep the input scaling?** Yes. `keepleak` multiplies only (v_rest − v), and dt/τ_m still scales gain·(g + I) − a. This matches my independent implementation exactly.
- **Are the SeedSequence seeds source-specific?** Yes. The key is [8 444 000, arm, input, level, side, rep, src_id], with src_id 0 for DATA and k − 8 421 000 for B1. The draw is shared across the DNa02 dynamics of one run, which pairs the cells correctly.
  Minor: BA1 and J025 share their noise seeds (8 443 201–208) and calibration seeds (8 443 301–304). This is by protocol, but the report does not say it.
- **Sign convention:** as reported. gap = B1 − DATA, dt = gap(X) − gap(M0), and I = dt(REF) − dt(dyn). Every number I checked in the REPORT table and §2 text matches analysis.json (wider CI).
- **Analysis:** the bootstrap resamples DATA reps independently of B1 reps, although rep r uses the same replay noise seed in both. This ignores a positive pairing, so the percentile intervals are, if anything, conservative.
  The jackknife leaves rep r out jointly. The hashes of protocol r2, v6m2.py and v6m2_analysis.py match `protocol_sha256_before_run.txt`, which predates the run (15:24 < 15:26).

## 4. Falsification findings
**F1 (main finding: the sign of Δt is set by operating regime as well as refractoriness).** This is a post hoc probe (`rt_e_biasgrid.py`), using the same sources, seeds and MASYNC draws as §2.
The grid was t_ref {2.2, 1, 0} × DNa02 bias {−40…+20 mV}. With the refractory block intact (REF), hyperpolarising DNa02 alone makes synchrony neutral or beneficial:
Δt(REF, −20 mV) = −0.9 Hz (log 0.00); Δt(REF, −40 mV) = −3.1 Hz (−7.7; +1.6), log **−0.22 (−0.32; −0.13)**. In the other direction, Δt(T0, +20 mV) = −1.3 (n.s.).
T0B therefore changes two things relative to REF: it removes refractoriness, and it adds a −38/−40 mV shift into the fluctuation-driven regime. Under MASYNC the T0B DNa02 is nearly silent at 7 mV (V6m2: DATA 1.0 Hz, B1 0.4 Hz).
Decomposing the RT-E I(T0B) = +22.1 Hz / +0.63 log:
- bias only, under REF (Δt(REF, 0) − Δt(REF, −40)): +10.2 (+8.6; +11.7) Hz, +0.36 log (≈ 46 % Hz, 58 % log);
- refractoriness at equal bias −40: +12.0 (+6.0; +17.9) Hz, +0.27 log;
- refractoriness at matched DATA·M0 rate (REF +20 mV, 116 Hz vs T0 −30 mV, 107 Hz): +24.4 (+18.9; +29.9) Hz, +0.48 log.

So the *interaction* (refractoriness raises Δt) is robust. It survives matching on bias and matching on rate. The report's mechanistic sentence, however, is falsified as worded.
The sentence is that refractoriness "is what turns synchronous intermediate input into a disadvantage" and that "without it synchrony is neutral or beneficial". At strong hyperpolarisation, synchrony is beneficial even *with* the block.
**F2 (J025 is not rate-matched).** In J025 the calibration minimum lay at the grid edge, b\* = −60 mV. T0B DATA·M0 = 169.5 Hz (calibration) / 169.8 Hz (main), against REF 110.9 / 103.6 Hz, which is +60 % higher.
The REPORT says T0B is "calibrated … so DATA's DNa02 rate matches REF". That is false for J025, so "generalises across the 3 tested parameter sets" rests on an unmatched T0B in that arm. Only BA1 (58.0 vs 58.5 Hz) and MAIN are matched.
**F3 (the effect is concentrated at the highest level, and there are floor effects).** The per-level Δt(REF) is +3.3 / +5.8 / +15.3 Hz at 7 / 8 / 9 mV in V6m2 and +3.4 / +1.0 / +16.8 in RT-E. Per-level I is +4.5 / +20.7 / +38.2 (V6m2).
T0B·MASYNC is at the floor at 7 mV in MAIN and low in BA1 (DATA 15.9, B1 8.8 Hz). The log metric at those rates is unstable: RT-E IL at 7 mV is +1.74. The pooled log also inherits these low rates.
**F4 (one blocked step is not robust).** In RT-E, Δt(T1) = +1.3 (−6.7; +9.3) Hz, log +0.03 (n.s.), against V6m2 MAIN +6.6. V6m2 BA1 also gives ≈ 0.
**F5 (wording about what the block discards).** The block discards membrane integration only. g keeps accumulating and decays with τ_syn = 5 ms, so input arriving during the block is *partly* carried past it, not discarded.
**F6 (what "rate-matched" covers).** Rate matching holds only for DATA × M0. B1·M0 under T0B is +20 Hz above REF, and under MASYNC T0B runs at less than half the REF rate (47 vs 107 Hz).

## 5. Verdict: **PASS_WITH_LIMITATIONS**
The implementation is correct: it is bit-identical to an independent replay for every DNa02 dynamics, the bias and leak changes touch DNa02 only, the seeds are source-specific, and the signs are as reported.
The pre-registered primary interaction replicates with new code, new seeds and new B1 instances: +22.1 Hz against +21.2. The mechanistic interpretation and the generalisation claim overreach and must be narrowed.

## 6. Required corrections to REPORT.md
1. §1, §2, §4: say that T0B in **J025 is not rate-matched**: b\* hit the −60 mV grid edge, and T0B DATA·M0 is 169.8 Hz against REF 103.6 Hz. Re-label J025 T0B as "partially biased t_ref 0".
   Restate "generalises" as: matched in MAIN and BA1 only; J025 supports the sign with an unmatched control.
2. §3, first bullet: replace "a refractory block … is what turns synchronous input into a disadvantage; without it … the sign reverses" with a conditional statement.
   The statement should say that DNa02 refractoriness shifts Δt upward by about 12–24 Hz at matched bias or matched rate (RT-E), and that the sign of Δt also depends on the operating regime.
   With the block intact, a −40 mV DNa02 bias makes synchrony beneficial (Δt log −0.22, CI excludes 0; RT-E F1). Report that about half of I(T0B) (46 % Hz / 58 % log) is reproduced by the bias shift alone under REF.
3. §1/§2: define "rate-matched" as "DATA × M0 only". Report the T0B rates under MASYNC (MAIN DATA 47, B1 30 Hz; 7 mV DATA 1.0 / B1 0.4 Hz) and B1·M0 (86.7 vs 66.2 Hz).
4. §2: add the per-level table for Δt(REF), Δt(T0B) and I (Hz and log). State that the MAIN effect is dominated by 9 mV and that the 7 mV T0B·MASYNC cell is at the floor, which makes log metrics there and in BA1 unreliable.
5. §3: soften "1 blocked step suffices in MAIN". Independent replication gives Δt(T1) +1.3 (−6.7; +9.3), n.s., and BA1 gives ≈ 0. Write "evidence for 1 step is inconsistent".
6. §3: correct the per-volley-cap wording. The block discards membrane integration during 3 steps, while the synaptic current g persists (τ_syn 5 ms). Input during the block is attenuated, not discarded.
7. §4: disclose that BA1 and J025 share noise and calibration seeds, and that the bootstrap resamples DATA and B1 reps independently despite shared replay noise (conservative).
8. §6: cite this replication: I +22.1 (+15.4; +28.8) Hz, +0.63 log, with an independent implementation, B1 8 421 011–015, own b\* −40. Also note that the MASYNC_W (window-preserving) control rules out count redistribution.
