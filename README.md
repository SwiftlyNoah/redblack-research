# The Red/Black Game - papers

Two papers on **Red/Black**, a hidden-information bidding game played over a
shared 52-card deck in which only color matters. Paper I formalizes and counts
the two-player game; Paper II specifies and reports a CFR+ solve of it.

`RULES.md` in this repo is the canonical rule text both papers are derived
from, and `state_counts.py` re-derives every count in Paper I from those rules.

| | |
| --- | --- |
| **Paper I** | [Rules, Deterministic Dynamics, and Exact State Enumeration (Heads-Up)](redblack-states.pdf) - [source](redblack-states.tex) |
| **Paper II** | [Counterfactual Regret Minimization on a Decomposed Heads-Up Game](redblack-cfrplus.pdf) - [source](redblack-cfrplus.tex) |
| **Note 3** | Safe continual re-solving: the composition certificate - [source](redblack-resolving.tex) |

**Status (2026-08-03):** the solver is several generations past what the
papers report (exact-by-reflection re-solve, measured real-game
exploitability, belief carrying, a certificate program). The concrete
revision plan is [`UPDATE_PLAN.md`](UPDATE_PLAN.md); until it lands, read
Paper II's Results section as the record of the *first* full solve, not
the current state of play.

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

The paper then characterizes what that projection throws away. The certainty
bounds pin the *support* of the public posterior exactly - sound and tight
across all 5,485 reachable classes - but say nothing about its *shape*: two
histories arriving at the same public class can leave an observer with
materially different beliefs. That gap is what Paper II has to be careful
about.

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

It reports the completed solve: all 5,721 classes, a game value of **51.33%**
to the opening seat, and an evaluation against prior bots. The measurement
sections come first, deliberately - they are what make those numbers readable.
In particular the round-local meter reports uniform success while seat-mirror
antisymmetry, which that meter cannot see, is violated by up to 0.11.

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
