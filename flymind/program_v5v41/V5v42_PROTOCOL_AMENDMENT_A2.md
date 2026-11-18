# V5 v4.2 — analysis amendment A2 (2026-10-30 ~09:45). Written while the v4.2 dynamics run was in progress; NO v4.2 dynamics
result had been opened (only structure.json summary: 301 instances, all checks OK).

Reason: V5 v4.1 red team RT3 (`results/v5v41/redteam/RT3_mechanism_skeptic.md`), verified by me from stored counts: the DATA vs
SWS difference coincides with LC10a population synchrony — LC10a ipsi population Fano factor (10 ms bins, steady window, 7–9 mV)
DATA 11.3 vs SWS 38.9 (all 50 higher); intermediate Fano 4.6 vs 11.1. Mean LC10a rate is (nearly) fixed by SWS's construction and
therefore uninformative about the locus. RT1 showed the between-instance SD is noise-level (family ≈ one network).

Added pre-specified analyses (descriptive):
1. Mediators per network: LC10a ipsi and mid ipsi population Fano factor (7–9 mV, E1 steady window, mean over sides and reps) and
   6–14 Hz relative spectral power of the LC10a ipsi population count (10 ms bins, steady window); also at noise 0 (E1n0).
2. Discrimination rules (from RT3, fixed now):
   - synchrony hypothesis supported if B1 (LC×LC) reproduces the DNa02 deficit AND SWS-level LC Fano, while B2–B4 leave LC Fano at
     DATA level;
   - alignment hypothesis supported if B2 (LC→mid) reproduces the DNa02 deficit with LC Fano at DATA level;
   - mid-recurrence / feedback hypotheses supported if B4 / B3 reproduce it.
   Even a positive B1 result locates the effect in the LC×LC block, not in a single graph statistic.
3. Effect sizes are reported as Δ with CI; std_delta (Δ/SD_between) is NOT used (RT1 L1: SD_between is noise-level).
4. Range averages: both trapezoid-weighted (as implemented) and plain mean over levels are reported (RT1 D1).
