# The Red/Black Game - papers

A three-paper series on **Red/Black**, a hidden-information bidding game
played over a shared 52-card deck in which only color matters. The spine:
define the real game exactly (I), solve its class abstraction exactly and
measure what the abstraction costs (II), then carry beliefs and pursue a
certified bound on real-game exploitability (III).

`RULES.md` in this repo is the canonical rule text all three papers are
derived from; `state_counts.py` and `real_game_size.py` re-derive every
count from those rules.

| | |
| --- | --- |
| **Paper I** | [Rules, Deterministic Dynamics, and Exact State Enumeration (Heads-Up)](redblack-states.pdf) - [source](redblack-states.tex) |
| **Paper II** | [Solving the Belief-Reset Abstraction Exactly, and Measuring the Distance to the Real Game](redblack-cfrplus.pdf) - [source](redblack-cfrplus.tex) |
| **Paper III** | [Belief Carrying, Safe Re-Solving, and the Certificate Problem](redblack-solving-g.pdf) - [source](redblack-solving-g.tex) |

**Status (2026-08-04):** rewritten as a series encapsulating solver
generations v2-v6. Headlines: the real game has exactly 2.448e33
perfect-recall infosets (counted, not estimated); the abstraction's value
is 51.22% to the opener; the solved profile's real-game exploitability is
certified >= 0.598/game and full belief carrying drives the probe's bound
to ~0.013; the certificate's upper jaw is still trivial, with the
distance located in one named quantity (Paper III). `UPDATE_PLAN.md`
records the audit that drove the rewrite; `AGENT_NOTES.md` is the
maintenance protocol, including exactly what in Paper III is a
window-snapshot to update as the certificate program advances. (Note 3,
the standalone safe-resolving note, was absorbed into Paper III;
its final text lives in git history.)

---

## Paper I - Rules, Deterministic Dynamics, and Exact State Enumeration

A complete formal account of heads-up Red/Black as a **deterministic, acyclic
finite transition system**: state set, input alphabet, transition function,
initial and final states, each counted exactly.

Three results organize it:

1. **Determinism.** Once the deal is fixed the game is fully deterministic -
   all chance is confined to the initial state - and the transition graph is
   acyclic, so every play terminates in between 5 and 9 rounds.
2. **Order irrelevance.** The order in which cards are flipped during a
   contest does not affect the state, which collapses procurement from a tree
   of flip sequences to a small lattice on two counters.
3. **Public projection.** What an observer knows reduces to two integers per
   seat plus who owes a discard: **6,051** public classes at hand size 5, of
   which exactly **5,485** are reachable. The pruning concentrates almost
   entirely in one layer, where 59% of the enumerable classes cannot occur,
   because a round tests one color and stops at the first off-color flip.

The paper then measures the object the projection summarizes - the real
game's public history tree (5.3e34 decision histories) and its exact
perfect-recall infoset count (2,448,351,139,319,171,077,272,326,424,233,304
at H=5, brute-force validated at small hand sizes) - and proves the
positive counterpart of "knowledge is not belief": under any strategy
profile, every reachable posterior factorizes over the class prior into
two per-seat tilts (rank-one factorization, with opponent-model-free
own-side conditionals). The class is the complete knowledge state; class
plus tilts is the belief state; those are the two objects Papers II and
III respectively run on.

## Paper II - CFR+ on a Decomposed Heads-Up Game

Written for a reader who has never seen counterfactual regret minimization:
it builds regret → regret matching → counterfactual regret → CFR+ from the
definition of regret, then expresses everything later in those terms.

The contribution is not CFR+ itself but the object it is run on. Rather than
solving the whole game at once, the game is cut into one subgame per round at
the boundaries identified in Paper I, each is solved exactly, and the values
are bootstrapped upward through a layered acyclic graph of **5,721 public
classes**.

The paper gives a full account of the information structure - what an
information set is, what a player's private state consists of, and exactly what
a *row* of the regret table is - together with the vector-form layout that
makes the whole solve a sequence of dense matrix operations. It is explicit
about what the decomposition approximates: by Paper I the public class pins the
support of the public posterior but not its shape, so re-deriving beliefs at a
boundary is a modeling choice, not an identity.

It reports the abstraction solved twice: a first full solve whose own
convergence meter read uniformly green while seat-mirror antisymmetry -
which the meter cannot see - was violated by up to 0.114, and a
second-generation solve (ordering collapse, mirror reflection, compiled
kernel) that re-solves the game on a laptop in two hours with mirrors
exact by construction. The value of the abstraction is **51.22%** to the
opening seat. The second half measures the distance to the real game:
reach-weighted TV 0.842 between the class prior and the true posterior,
certified real-game exploitability >= 0.598/game for a profile whose
in-abstraction meters read 1e-4, and a theorem exhibiting an action the
abstraction's equilibrium plays on path with probability 0.97 that is
dominated in the real game. Dated "incident" boxes preserve the measured
mistakes (the negative-exploitability trap, the 216,000-game
head-to-head overturn) as citable lessons.

## Paper III - Belief Carrying, Safe Re-Solving, and the Certificate Problem

The upper-bound program, shipped honestly as a program: re-solving each
boundary under the exact posterior (tracked over Paper I's belief family)
closes the probe's certified gap almost entirely (0.598 -> ~0.013, a
complete dose-response), but naive re-solving admits adversarial
counterexamples, so the paper builds the certification machinery - a
safe-resolving gadget with live-measured margins and an
opponent-model-free composition theorem, every constant re-derived by
script. Current audited status, stated plainly: the sandwich is
[0.013, trivial]; fixed promise surfaces are certifiably dead; the whole
remaining distance is honorability of the price surface at layers
T' >= 4, with a four-item program aimed at it.

---

## Reproducing the counts

`state_counts.py` re-derives every table in Paper I. It is pure standard
library - no dependencies, no virtualenv:

```bash
python3 state_counts.py
```

It deliberately does **not** import the solver's combinatorics. It re-derives
them from `RULES.md`, so agreement with the shipped rules engine is evidence
rather than tautology. `verify_against_engine.py` runs those counts against
the game's solver (31 cross-checks; requires the game repo's simulator on
disk, which is not public). `real_game_size.py` counts the perfect-recall
public history tree of the real game - the object an exact solver of the
unabstracted game must index; `data/layer-t2.csv` is a per-class dump of
layer `T'=2`.

## Building the papers

Self-contained TikZ/pgfplots, mainstream packages only - drop either `.tex`
into Overleaf and it compiles as-is. Locally:

```bash
tectonic -X compile redblack-states.tex --outdir .
tectonic -X compile redblack-cfrplus.tex --outdir .
tectonic -X compile redblack-solving-g.tex --outdir .
```

## Two clocks - read this before the counts

The rules order a round `reorder → bid → procure → DISCARD`, so the discard is
**last**. But the papers cut the game at *boundaries* - procurement
resolutions, where the loser is known but has not discarded yet - and a
boundary sits between procurement and discard. So the segment between two
boundaries reads `DISCARD → reorder → bid → procure`: the discard is
**first**. Same events, same order; only the cut points moved, by exactly one
discard.

This is the source of essentially every off-by-one in this material:

| Symbol | Meaning |
| --- | --- |
| `n_i` | seat `i`'s hand size **at** the boundary (pre-discard). `n_i == 1` means about to be eliminated, not gone |
| `T = n_0 + n_1` | cards in play at the boundary |
| `n_i'` | seat `i`'s size **during** the round that follows (post-discard) |
| `T' = T - [loser ≥ 0]` | cards in play for that whole round - **the layer index** |

Indexing by `T'` rather than `T` is what makes the class space a clean DAG with
one edge per round: the root (`T=10`, nothing pending) and a 5v5 resolution
(`T=10`, one pending) have the same `T` but different amounts of play left.

## Scope and caveats

- **Heads-up only.** General `N` is mentioned but not counted.
- Paper I covers dynamics and counting, not strategy or equilibrium.
- The posteriors in Paper I's Table 6 assume a neutral reference policy
  (uniform ordering and discard), stated in the paper. The qualitative gap
  holds for any fixed policy; the specific numbers do not.
- Paper II's solve is an approximation with stated meters, not a proof of
  optimal play. Section ordering reflects that: read the measurement sections
  before the results.

## Author

Noah Brauner - [github.com/SwiftlyNoah](https://github.com/SwiftlyNoah)
