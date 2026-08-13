# SUPERSEDED (2026-08-13)

This plan is superseded by the 2026-08-13 restructure. The repo's
target shape is now **four documents**:

- **Flagship** `redblack-coupling.tex` (in draft): the publication
  target. Solver coupling - QRE-ladder values frozen, per-class CFR+
  policies re-solved against them; the probe-zero verdict for
  `solve-6-cfrpolicy` (eps_G >= -0.005 at n=3,200). Standalone, cites
  the series as [RB-I/II/III], no cross-paper theorem numbers.
- **Papers I-III** (revised): the expository series - I states and
  counts, II solve and metrology, III resolving and certificates -
  corrected to the solve-5/6 record and using solve names throughout.

The restructure decisions are recorded in the game repo's
`simulator/logs/solve-5-journal.md`; the live maintenance protocol is
`AGENT_NOTES.md` (see its 2026-08-13 amendments). Everything below is
kept unchanged as the audit record that motivated the 2026-08-04
rewrite.

---

# Paper update plan (2026-08-03)

> **EXECUTED 2026-08-04** as a full three-paper rewrite (going beyond
> this plan's revise-in-place scope, per operator direction): Paper I
> gained the real-game section and the belief-family theorems; Paper II
> was reframed around G/G' with the metrology and distance results;
> Note 3 was absorbed into the new Paper III
> (`redblack-solving-g.tex`). This file remains as the audit record
> that motivated the rewrite; the live maintenance protocol is
> `AGENT_NOTES.md`.

The papers stopped at the v2 solve; the solver is now four generations
past them. This is the audit of what each document must absorb to
encapsulate the project's progress, ordered so the most-wrong claims are
fixed first. Sources of record for every number: the parent repo's
`docs/solver-v3.md` .. `docs/solver-v6.md` (measured results and
journals) and `simulator/results/solver/*.json`.

## Paper II (`redblack-cfrplus.tex`) - major revision, most-stale first

The Results section (Sec. 10) reports the v2 solve as the headline:
root value +0.0266 (51.33%), the 12.1 h / $23 cloud run, and the
mirror-gap autopsy. Since then the solve itself was replaced and the
meters were replaced; the current text now under-claims in some places
and over-claims in others.

1. **Add the v3 re-solve as the solve of record.** Ordering collapse
   (order classes replace ordering-sensitive private states), mirror
   reflection (seat antisymmetry exact by construction; residual vs
   independent re-solves 1.5e-6..8.9e-6, against v2 gaps of up to
   0.114), and the JIT kernel: tol 1e-5..1e-4 in 2h02m on a laptop.
   Root value of record: **+0.02449 (51.22%)**, not +0.0266. Keep the
   v2 numbers as the "first full solve" with its mirror-gap autopsy -
   that narrative is the motivation for v3 and is already well told.
   Add the equilibrium-multiplicity caveat (cellwise `v_types` spread
   up to 6.7e-2 between a solve and its reflection is selection, not
   error; only prior-weighted aggregates are pinned).

2. **Replace the measurement chapter's aspiration with the two-axis
   scoreboard, and report the trap that forced it.** The paper's
   "composed exploitability" meter is now real (kernel best response;
   eps_lb 0.4533/game for v3/v4-base in G') - but the honest lesson is
   that G'-composed eps and real-game exploitability DIVERGE: the LBR
   probe (exact opponent-type posterior + posterior-contracted argmax)
   certifies **eps_G >= 0.598** for the stored profile while every
   G'-selection variant measures identically in real play. Also record:
   head-to-head between sibling profiles is not a solve meter (v3
   converged ~100x tighter and still "lost" a raw arena that 216,000
   games later proved a dead tie - seed-family luck plus
   pair-correlated p-values).

3. **The belief reset is now measured, not hypothesized.** Sec. 8
   ("What Is Approximated") states the reset qualitatively. Add the
   numbers: reach-weighted TV(mu_h, lambda_kappa) = **0.842** overall,
   monotone 0.66 -> 0.95 with depth; the cross-fitted refinement ladder
   (true class-conditional posterior closes ~17pp of an 84pp gap;
   public-statistic enrichment is dead - the leak is within-class);
   and the sharpest qualitative consequence: **the G' equilibrium plays
   a real-game-dominated action (the suicide flip) on path with
   p = 0.97** because the reset launders the self-reveal. That is a
   measured, reproducible instance of abstraction divergence and is
   the paper's strongest single result about decomposition solving.

4. **Equilibrium-selection experiments and their prices.** Dominance
   pruning (masked solve: -5.2e-4 G' root value, suicide rate 0, but
   +0.052/game more exploitable to an unmasked G' BR) and concealment
   tie-breaking (ship profile; +0.047/game G' eps price). Both prices
   invisible to every real-game instrument - the two-axis point again.

5. **Update the deployed-profile section.** The served profile is
   v4-tb (v3 + concealment tie-break). Current battery: 79.97-81.55%
   vs gen6, ~87% vs heuristic, self-play seat-0 rate consistent with
   the solved root. State the guard layer explicitly and that guards-on
   parity is a floor, not a finding.

6. **Rewrite "What is not established" as the bridge to the
   certificate program.** All existing meters are lower bounds or
   G'-internal; the upper-bound program (safe resolving + certified
   leaf error) is Note 3's subject. Summarize the v5 finding that
   motivates it: full belief carrying closes essentially the entire
   certified gap most of the way (0.598 -> 0.078 [0.016, 0.139]), i.e.
   the reset is not just the dominant term, it is - to this
   instrument - the whole of it. Beliefs pay in defense, not offense
   (head-to-head gain ~0).

7. Appendix candidates from the institutional ledger: the
   `eps_lb`-is-a-lower-bound trap (apparently negative eps), the
   per-state/per-row aliasing bug that voided all pre-fix composed-eps
   figures (why meters need gates too), and the two-clocks restatement
   discipline.

## Note 3 (`redblack-resolving.tex`) - bring to the audited verdict

The note is current through the composition theorem and gadget, but the
v6 window ended AFTER it was written, with an independent adversarial
audit adopted in full. The note must not read stronger than the audit.

1. **Add the audited assembly verdict.** The on-path estimate (1.958)
   substitutes a self-play mean for the theorem's sup over
   opponent-steerable chains and is NOT a bound; the licensed assembly
   over visited boundaries is vacuous (8.22); certified eps_G today is
   the trivial cap. Reach-weighting is not a sound repair (the opponent
   steers carried beliefs; self-play samples a measure-zero slice).

2. **Add the vertex-sup certification result.** Per-type dishonor of a
   FIXED promise surface is linear-fractional in the own factor, so its
   sup over the rank-1 family certifies at own-type vertices: measured
   sup dishonor of the functional surface is median ~1.0, max ~2.0 at
   both T'=2 and T'=3 - fixed promise matrices are certifiably dead at
   every layer, even where on-path margins measure 3e-4. The certified
   path is range-dependent promises (library caps at the realized
   range) + per-type enforcement, whose residual is the library
   sandwich-gap sup.

3. **Record the enforcement requirement as load-bearing.** Honorable
   promises push opponent mass out, so CFR's weighted objective ignores
   opted-out types; hybrid (tighter) promises measured actively harmful
   without per-type enforcement (T'=3 margin 0.634 vs 0.085). Post-solve
   per-type min with the capping entry (or a max-margin objective) is
   mandatory machinery, not an optimization.

4. **Carry the sound leftovers as the v7 theorem work**: eps de-dup,
   a-invariant chain assembly, root-prior weighting, and a
   chance-expectation reproof of the successor step (the verification's
   0.4-2.0 slack locates the loose inequality).

5. **State the closing sandwich** as the window's honest end state:
   probe lower bounds 0.078 (unsafe full carry, n=1000) / 0.160 (safe, stored
   promises) / 0.113 (safe, certified promises); upper bound trivial.
   The certificate is measured, complete, and fat - and the distance
   is entirely honorability of the price surface at T'>=4.

6. Keep the standing convention: every constant re-derived by
   `simulator/scripts/v6_verify_composition.py`; extend that script in
   lockstep with any new lemma.

## Paper I (`redblack-states.tex`) - durable; targeted additions

The enumeration is untouched by solver generations. Three additions:

1. **A measured epilogue to "What the Public Class Forgets" (Sec. 10).**
   The section predicted the class abstraction's belief gap; it is now
   quantified (TV 0.842/0.95, the refinement ladder, and the v6
   rank-1 factorization: reachable beliefs factorize exactly as
   prior x g0(t0) x g1(t1) because a = r + x is invariant along every
   transition - measured residual 3.3e-16 over 17,140 boundaries, now
   the "model-free conditionals" lemma in Note 3). The factorization
   is a structural fact about the game's information partition and
   belongs in this paper's frame; a short remark citing Note 3 also
   works.

2. **Register `real_game_size.py` and its counts.** The paper counts
   the class abstraction; the new script counts the perfect-recall
   public history tree of the REAL game G (order-sensitive flips, full
   bid chains, loser-dependent round composition) - the object any
   exact solver of G must index. Add its headline counts as a short
   section or appendix beside the class counts, and to the
   reproduction appendix next to `state_counts.py`.

3. **Update "What Comes Next"** to point at Paper II's results and
   Note 3 rather than promising them.

## Repo hygiene (this repo)

- `verify_against_engine.py`, `real_game_size.py`, `data/layer-t2.csv`
  and `redblack-resolving.tex` now live here (synced 2026-08-03 from
  the parent repo, which consumes this repo as a submodule).
- PDFs are rebuilt per release (`tectonic -X compile <paper>.tex`);
  the committed PDFs must never lag a committed `.tex` change.
- After any count-bearing edit: run `state_counts.py` and
  `verify_against_engine.py` (31 cross-checks; non-zero exit on any
  mismatch) against the parent repo's simulator.
