# V5 v4.3 — LC10a spike-train replay: is spike TIMING the route of the LC×LC effect? (EXPLORATORY) — protocol r1, 2026-10-30 ~12:40
Written after V5 v4.1/v4.2 and their red teams; before any v4.3 simulation.

## 1. Question
V5 v4.2: shuffling only the LC10a×LC10a block (B1) lowers the ipsilateral DNa02 steady-state response by ~16 Hz at 6–9 mV while the
mean LC10a rates and rate-weighted LC→intermediate drive change by < 1 %, and LC10a population synchrony (Fano) triples.
Downstream wiring of B1 is identical to DATA. Does the timing structure of LC10a spike trains (not their rates) cause the DNa02
difference? Causal manipulation: replay recorded LC10a trains into the DATA downstream network and manipulate timing only.

## 2. Method (MODEL engine = alif.py equations, re-implemented with clamping; validated exactly, §4)
Sources: DATA and B1 instances 8 421 001–010 (10). E1 drive (unilateral, 1000 ms from rest) at 7, 8, 9 mV, both sides, noise reps
8 411 001–008 (as V5 v4.1). The LC10a spikes (all 275 LC10a, ipsi and contra) of each source run are recorded.
Replay: the DATA network is simulated with LC10a neurons CLAMPED to a (manipulated) train — LC10a membrane/recurrence ignored, their
spikes forced; intermediates and DNa02 evolve with the same ALIF equations, same noise seed as the source run (so an unmanipulated
replay of DATA's own train must reproduce the free DATA run exactly; for B1 trains it must reproduce the free B1 run exactly because
B1's downstream = DATA's). Manipulations, applied only in 300–1000 ms (0–300 ms unchanged), measured 500–1000 ms:
- V0 identity; V1–V5 per-spike jitter uniform ±J ms with J ∈ {1, 2, 5, 10, 20} (collisions merged — reported);
- V6 per-neuron circular shift (random offset within the 700 ms window): keeps every neuron's exact spike count and ISI sequence,
  destroys cross-neuron alignment;
- V7 rate-matched Bernoulli (Poisson-like) trains with each neuron's rate in the window.
RNG for manipulations: 8 430 000 + 100·variant + rep.
## 3. Measures and analysis (pre-specified, descriptive)
Per source family (DATA, B1) × variant × level: DNa02 ipsi and intermediate ipsi steady-state rate, LC10a population Fano of the
replayed train (verifies the manipulation), spike-count change from jitter collisions. Gap(V) = DN(B1 trains, V) − DN(DATA trains, V);
CI by bootstrap over B1 instances × reps (RNG 8 419 050). Interpretation rules (fixed now): timing route supported if Gap(V6) and
Gap(V7) shrink to ≤ 25 % of Gap(V0) AND DN(B1, V) rises with J toward DN(DATA, V); rate route if Gap stays ≥ 75 % of Gap(V0) under
V6/V7; otherwise partial. Note: V6/V7 also remove within-neuron/between-neuron correlations that DATA itself has; DN(DATA, V6/V7)
vs DN(DATA, V0) tells what DATA's own timing structure contributes.
## 4. Validation (must pass before analysis)
V0 replay reproduces the free source run's DNa02 and intermediate spike counts exactly (same seed) for DATA and for B1 instances.
## 5. Outputs
`flymind/v5v43.py`, `flymind/test_v5v43.py`, `results/v5v43/` (raw npz, analysis.json, REPORT.md). Open loop only, no MuJoCo.
