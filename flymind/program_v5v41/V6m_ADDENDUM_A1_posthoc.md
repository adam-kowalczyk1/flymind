# V6m addendum A1 — POST-HOC diagnostic Exp 6 (written 2026-10-30 ~15:00, AFTER the V6m main results were opened)
Not pre-registered; hypothesis-generating; reported separately from the pre-specified analysis.
Motivation (from the V6m results): under intermediate-clamp + circular shift (E3_MCIRC) 64–77 % of the B1–DATA DNa02 gap remains,
i.e. it is carried by WHICH/HOW MANY intermediate spikes arrive, not by their cross-neuron alignment; and removing intermediate
refractoriness (E1b_MID_t0) equalises mean intermediate rates while enlarging the DNa02 gap.
Exp 6: re-simulate (deterministically, same seeds/sources as V6m main: DATA + B1 8 421 001–010, 7/8/9 mV, L/R, noise 8 411 001–008)
the conditions REF, LCIRC, E1b_MID_t0 and E1_DN_t0, and store per-intermediate spike counts (500–1000 ms). Compute the DNa02-ipsi
synaptic drive carried by intermediate spike counts: D_exc = Σ_j max(W[dn, j], 0)·n_j, D_inh = Σ_j min(W[dn, j], 0)·n_j (timing-free
"rate-weighted input"), and the same for the subset of intermediates with W[dn, j] > 0. Consistency check: DNa02 counts must equal the
V6m main npz for the same condition. Gap and F as in the protocol (paired bootstrap, RNG 8 419 062). No new seeds.
Question: is the residual (timing-free) part of the DNa02 gap matched by a deficit in rate-weighted intermediate drive, and does that
drive deficit vanish under LCIRC and under E1b_MID_t0?
