# Implementation plan and status

## Smallest change set (done)

All changes are in **one new experiment-only file**, `bio2/test_cx_causal_memory.py`.

| Component | Where | Status | Test |
|---|---|---|---|
| Randomised scene direction and speed, seeded | `scene_params` | done | unit test: both directions over seeds 200–239; start side is opposite to the velocity |
| Shared non-neural visible-phase tracker | `run_trial`, block "polecenie" | done | dev: onset state bit-identical across arms (`dev/analysis_dev.txt`) |
| Convergence-gated onset (identical rule for all arms) | `run_trial`, CONV block | done | dev: 12/12 converged, t_on 1.28–1.49 s |
| Ball stopped at onset (Exp A) / not stopped (Exp B, `--moving`) | `run_trial` | done | smoke and dev records |
| Passive rotation from onset to onset + 0.6 s, arm outputs ignored | `run_trial` | done | dev: realised 17.35 ± 0.05°, trajectories identical across arms |
| ScalarMemory, the matched integrator | class | done | unit tests: integration, ±π wrap |
| CVMemory, an alpha-beta filter using cue + w_base | class | done | unit tests: velocity estimate, extrapolation, self-motion invariance |
| CX bump readout with coherence gate 0.2 | `run_trial` | done | dev |
| CX DN readout with a single memory calibration | `dn_readout` | done | dev |
| EPG pulse intervention (±30°, sham 0°) and ring reset | `run_trial` | done | open-loop probe and dev: shift +26.2 / −24.8 / +0.2° |
| Graded-shuffle structural control (f = 0.2, no gain compensation) | `calibrated_brain(shuffle_frac)` | done | `probes/graded_shuffle_summary.txt`; dev: silent ring in 12/12 |
| Shared kinematic self-motion scale λ_self | `CFG`, `--lambda-self` | done | Scalar g = 0.91 at λ = 1 (factor 1.105) |
| CX PEN-input trim λ_cx (part of the CX-arm calibration, tuned on dev) | `CFG`, `--lambda-cx` | done | dev2 verification (seeds 206–209) |
| Resumable JSONL runner; held-out guard; infrastructure-error records | `main` | done | unit test: guard |
| v2: target jump (`--jump`), SelfOnly arm, CX-DN pulse arms, Δ = 0 | `run_trial`, `SelfOnlyMemory`, `ARMS` | done | unit test (SelfOnly); no-jump regression bit-identical (`tests/regression_v2_nojump.txt`); dev4 216/216 OK |
| Production files untouched (`brain.py`, `agent.py`, scenes, connectome) | — | verified | `git_integrity_final.txt` |

## Not implemented (optional, not required for the decision)

- **Idealised cosine-ring reference network.** Useful to show whether connectome-derived profiles add anything beyond
  ring symmetry.
- **Cue-noise, distractor and long-gap regimes.** These are where an attractor could in principle beat a scalar
  integrator (`control_comparator_design.md`).
- **A non-gated readout variant.** Silent rings already give ω = 0 through angle(0) = 0, so it would change nothing for
  the Reset and Shuffle arms.

## Assumptions that cannot yet be validated

1. **The bump stands in for a remembered egocentric target bearing.** In flies the EPG bump encodes heading; this
   mapping is a model-level choice.
2. **The EPG pulse is a valid analogue of optogenetic bump relocation (Kim 2017).** Ours is 200 ms of cue-like current;
   theirs was about 1 s of two-photon stimulation.
3. **The DN readout calibration (`slope_mem`) stays valid in closed loop.**
4. **λ_cx = 0.65 generalises beyond the dev seeds.** The CX gain variance (SD 0.67) is larger than its mean error.
5. **Determinism across machines.** Verified only on this machine.
6. **Stopping the ball at onset is equivalent to a "stationary target".** Physically, the ball is teleported to rest.
