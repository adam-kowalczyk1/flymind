# V6m red team RT-A: implementation and replay fidelity (2026-10-30)

Reviewer RT-A. Scope: `v6m.step` / `replay` / `vectors` / `job_run` against `alif.ALIF.step` and `v5v43.step_clamped`, plus an independent re-simulation, spike-count matching, the window of the E3 manipulations, and the latency claim. I modified no existing file. I wrote only this file and `results/v6m/redteam/RT_A/` (scripts `rt_a_resim.py`, `rt_a_synth.py`, `rt_a_jitter.py`, `rt_a_boot.py`, output `rt_a_resim.json`).

**Seeds used (RT-A range only):**
- noise 8 498 001 and 8 498 002
- B1 (LCxLC) instance 8 498 010
- MCIRC rng 8 498 020+r, LCIRC rng 8 498 030+r
- synth rng 8 498 040+g (side L) and 8 498 070+g (side R)
- jitter rng 8 498 060+10·v+r
- bootstrap rng 8 498 090

**CPU:** about 2 min in total, single process.

**File hashes:** v6m.py, test_v6m.py, alif.py, v5v43.py and v5v41.py match `config_20261030T144242.json` and `protocol_sha256_before_run.txt`. v6m_analysis.py has the logged post-hash sha abb8f84d….

## 1. Line-by-line audit of `v6m.step` (v6m.py:58-81) against `alif.ALIF.step` (alif.py:70-84)

**Statement order.** The order is identical: g update, then noise, then v integration, then refractory clamp, then `ref -= dt`, then threshold, then clamp, then reset, then ref, then a, then buffer. The only additions are the following.
- `vint` probe (l.68). It is a read-only copy and consumes no RNG.
- `spk[cidx] = forced` (l.70). This is identical to step_clamped l.41.
- Subtractive reset (l.73-76). It applies only where `sub` is set, and only in E5a.
- `ref[spk] = tref[spk]` (l.77). This equals `p.t_ref` when every entry is 2.2.

**Refractory quantisation.** I checked it by hand. ref is tested (`> 0`) before the decrement, so t_ref 0/1/2/2.2/4/6 gives 0/1/2/3/4/6 blocked steps. That is a minimum ISI of 1/2/3/4/5/7 ms, and `summarise` floor = ceil(t_ref)+1 (l.186) is consistent with it. The float sequence 2.2 → 1.2000000000000002 → 0.2000000000000002 → −0.8 gives 3 blocked steps, as stated.

**Subtractive reset and the refractory clamp.** With t_ref > 0 the next step overwrites v with v_reset (l.66), so subtractive reset is a null manipulation. The protocol and test_v6m.py:39-46 already state this. E5a is therefore correctly paired with t_ref 0. A sub-reset neuron whose v is still ≥ v_th after the reset fires again at the next step, not within the same step. The cap is 1000 Hz, which is consistent with "excess" 10.6/12.3 mV.

**b_a vector.** `ALIF(spec, P, seed, b_a=ba)` (v6m.py:163) uses alif's native per-neuron b_a. LC10a entries are always 0.5. LC10a neurons are clamped, so their own v, a and ref evolve but never reach other neurons; only `buf` (spikes) propagates. Clamped intermediates in E1c/E3 work the same way.

**noinh.** `W_noinh` (v6m.py:210-214) zeroes only negative W[DN, mid] entries; the assert counts them. `net.W` is reassigned, not mutated, and `np.asarray(spec.W)` aliases `data.W`, but nothing writes to it in place. Network fact that §4 should state: most of DNa02's inhibition is CONTRALATERAL.
- DN_L receives −61.6 of −72.0 from mid_R.
- DN_R receives −57.8 of −69.0 from mid_L.

Under unilateral stimulation the contralateral side is weakly driven, so E5b removes mostly little-active inhibition.

**RNG streams.** `p.noise = 2` makes `step` draw `standard_normal(N)` every step in every condition, so noise is common across conditions and across sources. The manipulation RNGs (CIRC, J, POIS, synth) are separate generators.

The manipulation seeds `8_440_000+100·vi+r` (v6m.py:252, 261) do not depend on source, level or side. Each rep's circular-shift offsets are reused across all 11 sources × 3 levels × 2 sides, so there are only 8 realisations per manipulation. This is a paired design and the bootstrap over reps covers it, but the report should say so.

**Network composition.** N = 424 = 275 LC10a + 147 intermediates + 2 DNa02. No other neurons exist, and no DN→DN or LC→DN weights exist. So in E1c and E3 the ONLY free neurons are the two DNa02. Those experiments are therefore single-neuron tests driven by recorded input. That is a fair design, but the report should state it.

**Verdict on §1:** no unintended change found. Each ablation changes only its intended mechanism.

## 2. Independent re-simulation (own engine, not `v6m.step`)

`rt_a_resim.py` implements alif.py's equations independently:
- an integer refractory counter `ceil(t_ref/dt)`
- a ring-buffer list
- clamp, sub-reset and per-neuron b_a applied explicitly
- its own circular-shift routine

**Sources:** DATA and a new B1 instance 8 498 010. **Grid:** 7/8/9 mV × L/R × 2 noise seeds. **Conditions:** REF, E1c_DN_t0, E3_M0, E3_MCIRC, E2a_DN_b00, E1_DN_t0, E5a_DN_t0_sub, E5b_noinh, E1b_MID_t0, LCIRC.

**Results:**
- Free runs: own == `alif.ALIF.run`, 24/24 bit-identical.
- Replays: own == `v6m.replay`, 240/240 with identical DNa02 counts AND identical full 424-neuron rasters.
- The B1–DATA gaps in this small new sample have the reported sign and ordering:

| Condition | Gap (Hz) |
|---|---|
| REF | −24.0 |
| LCIRC | −4.0 |
| E3_MCIRC | −15.7 |
| E1c_DN_t0 | −21.5 |
| E2a_DN_b00 | −29.8 (enlarges) |
| E1b_MID_t0 | −31.8 (enlarges) |

The magnitudes are noisy (n = 1 instance, 2 reps).

**Replay checks on the stored raw data (no simulation):**
- T3 holds: REF == v5v43 V0 for all 11 sources.
- Exp 6 DNa02 counts == main, 11/11.
- `m0_eq_ref` and `ref_eq_free_nonlc` are all true in stdout.txt.

## 3. Do E3 / LCIRC manipulations touch only 300–1000 ms?

Yes.
- Code: `v5v43.manipulate` writes only `x[W0:W1]`.
- Raw data: in all 22 main/rep files the DNa02 rasters of every E3_* and LCIRC condition are identical to REF for t < 302 ms.
- Own runs: the earliest DNa02 difference from REF is at 303 ms (MCIRC) and 306 ms (LCIRC), which is the expected 2-step synaptic delay per layer.
- DN-local ablations first differ at 31 ms (t_ref) and 43 ms (b_a, E5b). Both are after DNa02's first spike, as expected.

## 4. Spike-count matching

**Exp 4 synth.**
- Per-neuron counts are exact in 300–1000 ms. They are asserted at v6m.py:155 and logged at 704 checks × 3 files.
- `lc_win` in the e4 raw files equals main_DATA REF exactly.

Problems:
- (a) The report's "all 792 synthetic trains" is wrong. There are 11 grid × 3 levels × 2 sides × 8 reps = **528 unique trains**. The 4 dynamics share each train, which gives 2112 checks.
- (b) In the 500–1000 ms ANALYSIS window, LC10a ipsi counts are not matched. They deviate from the source by −6.5 % to +1.0 % per grid point (mean ≈ −1.3 %). Example: level 7 mV, p 0.7 is −6.5 %. This adds non-synchrony noise to the dose–response.
- (c) ISI ≥ 4 ms is enforced only inside the window. Across the 300 ms boundary I found 0–2 violations per train (`rt_a_synth.py`), which is negligible.
- (d) **Nominal p is not the realised participation.** I measured the fraction of spikes within ±1 ms of an event (chance 0.02–0.14).

| Event rate | p 0.35 | p 0.7 | p 0.9 | p 1.0 |
|---|---|---|---|---|
| 10 Hz events | 0.28 | 0.51–0.55 | **0.38–0.46** | **0.59–0.61** |
| 40 Hz events | 0.37–0.41 | 0.65–0.67 | — | 0.86–0.87 |

  - At 10 Hz the realised participation is non-monotone in p, because n_ev is Poisson (4–12 events). A neuron can join an event at most once, and it has about 9 spikes in the window.
  - So the 10 Hz grid cannot exceed about 0.6 participation.
  - The "40 Hz events are more harmful at equal Fano10/χ²/volley" result therefore compares families that differ in realised participation and in the per-neuron fraction of spikes in volleys. It does not cleanly isolate "volley size".

**MCIRC.**
- Per-neuron counts are preserved in 300–1000 ms only.
- In the 500–1000 ms analysis window, ipsi intermediate counts versus REF/M0 are **−2.38 % (DATA) and −3.41 % (B1)** (raw, all main runs). That is a differential −1 point, which slightly enlarges the MCIRC gap, so the reported F_MCIRC is, if anything, conservative.
- LCIRC changes ipsi intermediate counts by −7.41 % (DATA) and −0.80 % (B1). LC10a counts in 500–1000 ms change by −1.06 % and −1.97 %.
- The report's "per-neuron counts are preserved by MCIRC" (§4 H3) must be qualified.

**Jitter / MPOIS losses.** "≤ 1 %" is wrong for MJ5 and MJ20.
- Raw: mean lost = 13.4 (MJ5) and 14.3 (MJ20) spikes per run.
- Own runs (8 mV): 1.3–2.9 % of the intermediate spikes in 300–1000 ms for MJ5/MJ20, versus 0–0.4 % for MJ2.
- MJ2, MJ5, MJ20 and MPOIS also create physiologically impossible ISIs < 4 ms in the clamped intermediate trains: 32–124 per run (about 5–15 % of spikes), against 0 in REF. CIRC wrap creates 0–2.
- So MPOIS and MJ change ISI structure, not only alignment. This is relevant when ranking MPOIS (F 0.49) above MCIRC (0.36).

**T5 "LC10a trains identical to the source".** `lc_counts_equal` (v6m.py:275) compares the forced spikes with the forcing array. It is tautological given the clamp, so it is a clamp-mechanics check, not an independent input check.

## 5. "Latency 41.9 ms in every condition and both sources"

This is not a bug, but the statement and its explanation are inaccurate.
- 41.9 is a mean over levels (55.8 / 38.9 / 31.0 ms at 7 / 8 / 9 mV).
- Per run, lat0 differs between sources in 128 of 528 REF runs (≤ 2 ms). The means are 41.85 for DATA and 41.81–42.00 across the B1 instances.
- E1b_MID_t0 changes lat0 in 203 runs (41.65 / 41.50). Intermediates fire about 4–5 ms before DNa02, so removing their refractoriness acts before the first DN spike.
- lat0 is identical by construction for:
  - every DN-local ablation (t_ref, b_a and reset act only after the first spike; noise is common)
  - every 300–1000 ms manipulation
- The explanation "precedes LC10a recurrence effects" is false. With RT-A seeds, the DATA and B1 LC10a trains diverge 2–4 ms after the first LC spike, which is 6–10 ms BEFORE DNa02's first spike. DNa02 onset is nearly source-independent because it is driven by the common onset volley.

## 6. Statistics (pseudoreplication check)

The same 8 noise seeds drive every source, in both the free run and the replay. I re-bootstrapped with ONE seed-index draw shared by DATA and all B1 instances (`rt_a_boot.py`). The CIs are nearly unchanged:
- REF gap [−22.1; −17.5] versus the reported [−21.9; −17.9]
- E1c F [+0.04; +0.40] versus [+0.06; +0.37]
- E3_MCIRC F [+0.29; +0.42] versus [+0.28; +0.42]
- replication MCIRC F [+0.10; +0.34] versus [+0.13; +0.33]

Correlations over seeds: B1–B1 is +0.06 to +0.36, and DATA vs the B1 mean is −0.38 to +0.83. The independent-resampling bootstrap is therefore acceptable, and no number changes.

## 7. Alternative explanations / overinterpretation

These are within RT-A scope only.
- E1c and E3 are single-neuron (DNa02) tests, so "timing route at DNa02" is a property of one ALIF neuron's integration of recorded input. That is fine, but it should be said.
- MPOIS and MJ confound alignment with ISI structure (§4).
- The Exp 4 40-vs-10 Hz contrast is confounded by realised participation (§4d).
- Fano10 for synthetic trains depends strongly on the random event count. At the same p and side it ranges from 27.1 to 35.5, which is a reason to report realised participation alongside Fano.

**Verdict: PASS_WITH_LIMITATIONS.** The engine, replay, clamp, ablation vectors, RNG pairing and windowing are correct. An independent engine reproduces v6m bit-for-bit in 240/240 replays plus 24/24 free runs. I found no artifact that could produce the reported gaps. Several factual statements in REPORT.md are wrong or overstated (below), but none reverses an H1–H5 rule outcome.

## Required corrections to REPORT.md

1. §3 "Latency …": replace with something like: "lat0 (mean 41.9 ms over levels; 55.8/38.9/31.0 ms) is unchanged by construction under DN-local ablations and 300–1000 ms manipulations; it differs between sources by ≤ 2 ms in 128/528 runs and shifts under E1b_MID_t0 (203 runs). It is driven by the common LC10a onset volley; DATA/B1 LC10a trains already diverge before it, so 'precedes recurrence effects' is incorrect. Uninformative."
2. §2 T5: replace "792 synthetic trains" with "528 unique synthetic trains (2112 checks; the 4 dynamics share each train)". State that ISI ≥ 4 ms holds inside 300–1000 ms only (0–2 boundary violations per train), and that counts are exact in 300–1000 ms but deviate −6.5 % to +1 % in the 500–1000 ms analysis window.
3. §2 "jitter losses counted (≤ 1 %)": correct to "MJ2 ≤ 0.4 %, MJ5/MJ20 ≈ 1.3–2.9 % (raw mean 13–14 spikes/run)". Add that MJ and MPOIS introduce ISIs < 4 ms (about 5–15 % of intermediate spikes) that REF trains never contain.
4. §4 H3: qualify "per-neuron counts are preserved by MCIRC" as "in 300–1000 ms; in the 500–1000 ms window ipsi intermediate counts are −2.4 % (DATA) / −3.4 % (B1) vs M0 (bias makes F_MCIRC conservative)". Report the analogous LCIRC change (−7.4 % / −0.8 %).
5. §3 Exp 4 and §5: report realised event participation per grid point (10 Hz: about 0.28 at p 0.35, about 0.6 at p 1, non-monotone at p 0.9; 40 Hz: about 0.86 at p 1). Describe p as the "placement attempt probability". Qualify the "many small volleys more harmful" statement as confounded by realised participation and event count.
6. §1/§4: state that in E1c and E3 only the two DNa02 neurons are unclamped (N = 275 + 147 + 2), so these are single-neuron integration tests on recorded input.
7. §3 E5b: state that about 85 % of the intermediate→DNa02 inhibitory weight is contralateral and weakly driven under unilateral stimulation, so E5b is a weak test of inhibition.
8. §1/§6: state that the manipulation RNG seeds depend only on rep (8 realisations, reused across sources, levels and sides; paired design).
9. §2 T5 "LC10a trains identical to the source": state that this check compares forced spikes with the forcing array (a clamp-mechanics check), and that source fidelity is established by T3 and by REF == free run.
10. §6 (optional): note that noise seeds are shared across sources, and that a seed-paired bootstrap (RT-A) gives practically the same CIs.
11. §8: cite this review (`results/v6m/redteam/RT_A_implementation.md`).
