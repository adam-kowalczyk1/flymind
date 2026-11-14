# E2 — clarifications to pre-registration draft r1

**Status: CLARIFICATIONS ONLY, written 2026-11-11. NOT APPROVED TO RUN. NOT HASHED FOR A RUN.**
They belong to `E2_PREREG.md` (draft r1, SHA-256 `f3ec61707f82bdf0490e89b89e1050153c1a54ae10ea80cea7a21facb9c5680c`),
which is left byte-for-byte unchanged. **No rule written in E2 draft r1 is changed here.** C1 explains the basis of a
threshold; C2 fills a case the draft left unstated. If E2 is approved, this file is hashed together with `E2_PREREG.md`.
No code for E2 exists; nothing has been run; no reserved seed has been used. Author: Claude (Fable 5.2).

## C1 (clarification) — what the "≤ 7 discordant trials" margin rests on

- The margin is anchored on one comparison between two *different* controllers: the network with glutamate −1 versus +1
  differs on 10 of 135 trials (E2 draft §2). "≤ 7" means "closer to the network than that variant is".
- It is **not** anchored on how much the network differs from itself. The only self-repeat evidence is 0 differing trials
  out of **18** re-run trials, not a full repeat of all 135. Zero of 18 is weak: the 95 % Wilson upper bound is 17.6 %,
  which would correspond to about 24 of 135 trials. So the existing data do not show that a full self-repeat gives 0.
- The draft already covers this at run time: gate G1 (§5) re-runs the network on all 135 trials, soft and stiff, and
  requires every per-trial outcome to equal the stored one. That **is** the full self-repeat. If it is not exactly 0
  discordant, the run is void under G1 as written, and the margin is not applied at all.
- Consequence, stated so it cannot be reinterpreted later: an "equivalent" verdict is only ever issued in a run where
  the full 135-trial self-repeat was 0. If G1 fails because the simulation turns out not to be exactly repeatable, the
  margin of 7 has no measured noise floor and E2 needs a revised pre-registration, not a relaxed gate.

## C2 (clarification) — mixed results between soft and stiff contact

Draft §6 states the readings for "both hold", for "H-E2a fails (≥ 12)" and for "8–11". It does not state what is said
when the two contact types land in different bands. The readings below use only the bands already defined; H-E2a (soft)
remains the primary hypothesis.

| Soft (H-E2a) | Stiff (H-E2b) | Reading |
|---|---|---|
| ≤ 7 | ≤ 7 | as in the draft: "behaviourally equivalent to a transfer curve with linear dynamics"; the grasp task is closed as a place to look for effects of wiring |
| ≤ 7 | 8–11 | "equivalent under soft contact; close, not shown equivalent, under stiff contact". **No general equivalence claim. The grasp task is not closed by rule;** the result goes to the owner |
| ≤ 7 | ≥ 12 | "equivalent under soft contact only; not equivalent under stiff contact". Reported as dependence on contact; no general claim; task not closed |
| 8–11 | any | as in the draft: "close"; no claim of equivalence. The stiff result is reported next to it and changes nothing |
| ≥ 12 | any | as in the draft: H-E2a fails — the network does more than a curve here; not evidence about wiring |

In every mixed case no extra run, surrogate adjustment or new threshold is used to resolve the difference.
