#!/usr/bin/env python3
"""Every number that appears in the Red/Black state-space paper.

Self-contained: the combinatorics here are re-derived from the rules
(RULES.md) rather than imported from the solver, so the paper's counts are
an independent check on the implementation rather than a restatement of it.
`verify_against_engine.py` cross-checks the round-automaton counts against
the shipped graph builder.

Conventions (heads-up throughout):
  * deck: 26 red + 26 black = 52 cards
  * H            hand size at the deal (H = 1, 2, 5)
  * a "boundary" is a procurement resolution: the loser is known, the
    discard has not happened yet.  Plus the game root.

TWO CLOCKS -- the one thing to get right (paper, Sec. "Two clocks").

The RULES order a round  reorder -> bid -> procure -> DISCARD, so the
discard comes LAST.  But we cut the game at boundaries, and a boundary sits
between procurement and discard, so the segment between two consecutive
boundaries reads  DISCARD -> reorder -> bid -> procure: the discard comes
FIRST.  Same events, same order; only the cut points moved, by exactly one
discard.  Hence:

  * n_i          seat i's hand size AT the boundary, i.e. PRE-discard.
                 A seat with n_i == 1 is about to be eliminated, not gone.
  * T   = n_0+n_1          cards in play at the boundary (pre-discard)
  * n_i'= n_i - [i == loser]   seat i's size DURING the round that follows
  * T'  = T - [loser >= 0]     cards in play for that whole round

T' is the LAYER INDEX -- `post_total()` below.  Indexing by T' rather than T
is what makes the class space a clean DAG with one edge per round: the game
root (T=10, no discard pending) and a resolution at 5v5 (T=10, one pending)
have the same T but different amounts of play left, and belong in different
layers.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from fractions import Fraction as F
from itertools import combinations
from math import comb

RED, BLACK = 0, 1
DECK_R = DECK_B = 26
DECK = DECK_R + DECK_B


# ---------------------------------------------------------------------------
# 1. Deals - the only chance event in the game
# ---------------------------------------------------------------------------

def deal_counts(H: int) -> dict:
    """Card-level and colour-level deal counts for hand size H, heads-up."""
    card_level = comb(DECK, H) * comb(DECK - H, H)
    # Colour-level: P(seat0 holds a reds, seat1 holds b reds).
    joint: dict[tuple[int, int], F] = {}
    denom = comb(DECK, H) * comb(DECK - H, H)
    for a in range(H + 1):
        for b in range(H + 1):
            ways = (
                comb(DECK_R, a) * comb(DECK_B, H - a)
                * comb(DECK_R - a, b) * comb(DECK_B - (H - a), H - b)
            )
            if ways:
                joint[(a, b)] = F(ways, denom)
    assert sum(joint.values()) == 1, "colour-deal law must be a distribution"
    return {"card_level": card_level, "colour_level": len(joint), "joint": joint}


# ---------------------------------------------------------------------------
# 2. The round automaton - deal-independent public structure of one round
# ---------------------------------------------------------------------------
#
# A bid history is (colour, strictly increasing counts drawn from 1..T).
# Procurement is a DAG on the pair of flip counters, NOT a tree of flip
# sequences: every card flipped before the resolving one matched the bid
# colour, so the only thing the state depends on is how many cards have
# come off each deck.

def bid_nodes(T: int) -> int:
    """Bid-phase nodes: the pre-bid node plus one per (colour, chain)."""
    return 1 + 2 * (2 ** T - 1)


def bid_histories(T: int):
    """All (colour, counts) bid histories over T cards in play."""
    for size in range(1, T + 1):
        for chain in combinations(range(1, T + 1), size):
            for colour in (RED, BLACK):
                yield colour, chain


def bidder_seat(starter: int, chain: tuple[int, ...]) -> int:
    """Whoever placed the last bid. The starter bids 1st, 3rd, 5th, ..."""
    return starter if (len(chain) - 1) % 2 == 0 else 1 - starter


def proc_nodes(starter: int, n0: int, n1: int) -> int:
    """Live procurement nodes: (colour, chain, f_bidder, f_challenger) with
    every flip so far on-colour and the bid not yet made."""
    T = n0 + n1
    total = 0
    for colour, chain in bid_histories(T):
        b = chain[-1]
        sb = bidder_seat(starter, chain)
        nb, nc = (n0, n1) if sb == 0 else (n1, n0)
        total += sum(
            1
            for fb in range(nb + 1)
            for fc in range(nc + 1)
            if fb + fc <= b - 1
        )
    return total


def resolution_edges(starter: int, n0: int, n1: int) -> int:
    """Distinct round-end keys (colour, chain, fb, fc, loser_is_bidder, mm)."""
    T = n0 + n1
    keys = set()
    for colour, chain in bid_histories(T):
        b = chain[-1]
        sb = bidder_seat(starter, chain)
        nb, nc = (n0, n1) if sb == 0 else (n1, n0)
        for fb in range(nb + 1):
            for fc in range(nc + 1):
                if fb + fc > b - 1:
                    continue
                for own in (True, False):
                    if own and fb >= nb:
                        continue
                    if not own and fc >= nc:
                        continue
                    nfb, nfc = (fb + 1, fc) if own else (fb, fc + 1)
                    if nfb + nfc >= b:            # bid made, challenger loses
                        keys.add((colour, chain, nfb, nfc, False, 0))
                    keys.add((colour, chain, nfb, nfc, True, 1 if own else 2))
    return len(keys)


# ---------------------------------------------------------------------------
# 3. Public boundary state ("class")
# ---------------------------------------------------------------------------
#
# class = (loser, s_0, s_1),  s_i = (n, r_lb, b_lb),  r_lb + b_lb <= n
# loser = -1 marks the game root (no discard pending).

def seat_stats(H: int) -> list[tuple[int, int, int]]:
    return [
        (n, r, b)
        for n in range(1, H + 1)
        for r in range(n + 1)
        for b in range(n - r + 1)
    ]


def seat_stat_count(H: int) -> int:
    """sum_{n=1..H} C(n+2,2) - the closed form for the per-seat statistic."""
    return sum(comb(n + 2, 2) for n in range(1, H + 1))


def class_count(H: int) -> int:
    k = seat_stat_count(H)
    return 2 * k * k + 1


def post_total(loser: int, n0: int, n1: int) -> int:
    """T' -- the layer index: cards in play DURING the round that follows.

    n0, n1 are pre-discard (boundary) hand sizes, so this subtracts the one
    card the pending loser is about to drop. At the game root (loser = -1)
    nothing is pending and T' = T. See the module docstring, "TWO CLOCKS".
    """
    return n0 + n1 - (1 if loser >= 0 else 0)


def is_terminal(loser: int, s0, s1) -> bool:
    """A pending loser holding one card is eliminated by the forced discard."""
    return loser >= 0 and (s0 if loser == 0 else s1)[0] == 1


# ---------------------------------------------------------------------------
# 4. Exact reachability - forward closure over concrete boundary states
# ---------------------------------------------------------------------------
#
# Boundary state: (loser, (r0,b0,rlb0,blb0), (r1,b1,rlb1,blb1)).
# The discard *composition* is deliberately absent: it changes nobody's
# legal moves and no public bound, so it cannot affect which classes are
# reachable (it matters only for beliefs, which is paper two's problem).
#
# Round facts used, all forced by the rules:
#   F1  exactly one bid colour per round
#   F2  procurement stops at the FIRST off-colour flip, so at most one card
#       of the non-bid colour is ever revealed in a round, on one seat, last
#   F3  bounds fold as max(old - [discarded since], seen), never additively
#   F4  the bidder is the last raiser, so a non-starter bidder needs a
#       final count >= 2

def successors(state):
    """Every boundary state reachable from `state` in one round."""
    loser, S0, S1 = state
    hands = [list(S0), list(S1)]
    out = set()

    drops = [None] if loser < 0 else [RED, BLACK]
    for drop in drops:
        h = [list(hands[0]), list(hands[1])]
        if loser >= 0:
            r, b, rlb, blb = h[loser]
            if drop == RED:
                if r == 0:
                    continue
                r -= 1
            else:
                if b == 0:
                    continue
                b -= 1
            if r + b == 0:
                continue                      # eliminated: game over, no successor
            # the anonymous discard decays BOTH certainty bounds by one
            h[loser] = [r, b, max(0, rlb - 1), max(0, blb - 1)]

        n = [h[0][0] + h[0][1], h[1][0] + h[1][1]]
        T = n[0] + n[1]
        starter = 0 if loser < 0 else 1 - loser

        for C in (RED, BLACK):
            # cards of the bid colour / off colour held by each seat
            c = [h[i][0] if C == RED else h[i][1] for i in range(2)]
            o = [n[i] - c[i] for i in range(2)]

            for bidder in (0, 1):
                kmin = 1 if bidder == starter else 2      # F4

                # -- made: k on-colour cards produced, nothing off-colour --
                for m0 in range(c[0] + 1):
                    for m1 in range(c[1] + 1):
                        k = m0 + m1
                        if k < kmin or k > T:
                            continue
                        out.add(_settle(h, n, loser, C, [(m0, 0), (m1, 0)],
                                        1 - bidder))

                # -- bust: j on-colour, then one off-colour on seat s (F2) --
                for s in (0, 1):
                    if o[s] < 1:
                        continue
                    for ms in range(c[s] + 1):
                        for mo in range(c[1 - s] + 1):
                            j = ms + mo
                            if max(j + 1, kmin) > T:      # need a legal count k > j
                                continue
                            seen = [None, None]
                            seen[s] = (ms, 1)
                            seen[1 - s] = (mo, 0)
                            out.add(_settle(h, n, loser, C, seen, bidder))
    return out


def _settle(h, n, entry_loser, C, seen, new_loser):
    """Fold this round's sightings into the successor boundary state."""
    st = []
    for i in range(2):
        r, b, rlb, blb = h[i]
        m, e = seen[i]
        sr, sb = (m, e) if C == RED else (e, m)
        st.append((r, b, max(rlb, sr), max(blb, sb)))
    return (new_loser, st[0], st[1])


def reachable_closure(H: int):
    """Forward BFS from every colour-deal; returns visited states and the
    set of reachable classes."""
    seen_states = set()
    frontier = []
    for r0 in range(H + 1):
        for r1 in range(H + 1):
            s = (-1, (r0, H - r0, 0, 0), (r1, H - r1, 0, 0))
            if s not in seen_states:
                seen_states.add(s)
                frontier.append(s)
    while frontier:
        nxt = []
        for st in frontier:
            for s2 in successors(st):
                if s2 not in seen_states:
                    seen_states.add(s2)
                    nxt.append(s2)
        frontier = nxt

    classes = set()
    for loser, A, B in seen_states:
        sa = (A[0] + A[1], A[2], A[3])
        sb = (B[0] + B[1], B[2], B[3])
        classes.add((loser, sa, sb))
    return seen_states, classes


# ---------------------------------------------------------------------------
# 5. Termination
# ---------------------------------------------------------------------------

def round_bounds(H: int) -> tuple[int, int]:
    """Heads-up: exactly one card leaves play per round, and a seat dies at
    H discards, so the game lasts between H and 2H-1 rounds."""
    return H, 2 * H - 1


# ---------------------------------------------------------------------------

def main() -> None:
    w = sys.stdout.write
    w("=" * 72 + "\n1. DEALS\n" + "=" * 72 + "\n")
    for H in (1, 2, 5):
        d = deal_counts(H)
        w(f"  H={H}: card-level deals = {d['card_level']:,}"
          f"   colour-level (r0,r1) outcomes = {d['colour_level']}\n")
    d5 = deal_counts(5)
    w("\n  colour-deal law, H=5 (P(r0=a, r1=b)), a down / b across:\n     ")
    for b in range(6):
        w(f"{b:>9d}")
    w("\n")
    for a in range(6):
        w(f"  {a}  ")
        for b in range(6):
            w(f"{float(d5['joint'].get((a, b), 0)):9.5f}")
        w("\n")

    w("\n" + "=" * 72 + "\n2. ROUND AUTOMATON (one round, T cards in play)\n" + "=" * 72 + "\n")
    w("   T   bid nodes   formula 1+2(2^T-1)\n")
    for T in (2, 4, 10):
        w(f"  {T:2d}   {bid_nodes(T):9,d}   {1 + 2 * (2**T - 1):,d}\n")
    w("\n  procurement nodes and resolutions, by (n0,n1) with starter=0:\n")
    w("   (n0,n1)    bid nodes   proc nodes   resolutions\n")
    for n0, n1 in ((1, 1), (2, 2), (5, 5)):
        w(f"    ({n0},{n1})     {bid_nodes(n0+n1):9,d}   {proc_nodes(0,n0,n1):10,d}"
          f"   {resolution_edges(0,n0,n1):11,d}\n")

    w("\n" + "=" * 72 + "\n3. PUBLIC BOUNDARY CLASSES\n" + "=" * 72 + "\n")
    w("   H   per-seat stats   classes = 2k^2+1\n")
    for H in (1, 2, 5):
        w(f"  {H:2d}   {seat_stat_count(H):14,d}   {class_count(H):,d}\n")

    w("\n  H=5, by layer T = post-discard total:\n")
    w("    T   solvable   terminal      total\n")
    lay = defaultdict(lambda: [0, 0])
    stats = seat_stats(5)
    for loser in (0, 1):
        for s0 in stats:
            for s1 in stats:
                T = post_total(loser, s0[0], s1[0])
                lay[T][1 if is_terminal(loser, s0, s1) else 0] += 1
    lay[10][0] += 1
    tots = [0, 0]
    for T in sorted(lay):
        a, b = lay[T]
        tots[0] += a
        tots[1] += b
        w(f"   {T:2d}   {a:8,d}   {b:8,d}   {a+b:8,d}\n")
    w(f"   ALL  {tots[0]:8,d}   {tots[1]:8,d}   {sum(tots):8,d}\n")

    w("\n" + "=" * 72 + "\n4. EXACT REACHABILITY\n" + "=" * 72 + "\n")
    for H in (1, 2, 5):
        states, classes = reachable_closure(H)
        stats_h = seat_stats(H)
        naive = defaultdict(int)
        for loser in (0, 1):
            for s0 in stats_h:
                for s1 in stats_h:
                    naive[post_total(loser, s0[0], s1[0])] += 1
        naive[2 * H] += 1
        got = defaultdict(int)
        for loser, sa, sb in classes:
            got[post_total(loser, sa[0], sb[0])] += 1
        w(f"\n  H={H}: {len(states):,d} boundary states, "
          f"{len(classes):,d} reachable classes of {class_count(H):,d}\n")
        w("    T   reachable   enumerable   pruned\n")
        for T in sorted(naive):
            g, nv = got.get(T, 0), naive[T]
            w(f"   {T:2d}   {g:9,d}   {nv:10,d}   {(nv-g)/nv:6.1%}\n")

    w("\n" + "=" * 72 + "\n5. TERMINATION\n" + "=" * 72 + "\n")
    for H in (1, 2, 5):
        lo, hi = round_bounds(H)
        w(f"  H={H}: between {lo} and {hi} rounds\n")

    w("\n" + "=" * 72 + "\n6. WHAT THE CLASS FORGETS\n" + "=" * 72 + "\n")
    tight, loose = support_tightness(5)
    w(f"\n  Support completeness (Theorem: bounds are sound AND tight):\n"
      f"    classes whose realized hands exactly fill the bound box: {tight:,d}\n"
      f"    classes with a gap:                                      {loose:,d}\n")
    _report_paths(w)




# ---------------------------------------------------------------------------
# 6. Path dependence: the class summarizes KNOWLEDGE, not BELIEF
# ---------------------------------------------------------------------------
#
# Two histories can land on the same public class while leaving an observer
# with materially different posteriors over the same hand.
#
#   Path A  five cards, two revealed red in round 1, then one discarded.
#           Bound folds max(2,.) then decays by one -> r_lb = 1, n = 4.
#   Path B  five cards, nothing revealed, one discarded, then one card
#           revealed red in round 2.  Fresh sighting -> r_lb = 1, n = 4.
#
# Both are (n, r_lb, b_lb) = (4, 1, 0).  The posteriors are not close.
#
# Reference policy: uniformly random ordering and uniformly random discard.
# This is a modeling choice made only to put numbers on the gap; under ANY
# fixed policy the two posteriors differ, because Path A conditions on two
# reds having been in the hand while Path B conditions on only one.

def _hand5_law() -> dict[int, F]:
    """P(exactly k reds in a 5-card hand dealt from 26R/26B)."""
    return {k: F(comb(DECK_R, k) * comb(DECK_B, 5 - k), comb(DECK, 5))
            for k in range(6)}


def path_posteriors() -> tuple[dict[int, F], dict[int, F]]:
    """Posterior over reds in the surviving 4-card hand, for both paths."""
    prior = _hand5_law()
    A: dict[int, F] = defaultdict(F)
    B: dict[int, F] = defaultdict(F)
    for r5, p5 in prior.items():
        # --- Path A: reveal 2 of the 5 uniformly, both red; then discard 1.
        p_reveal = F(comb(r5, 2), comb(5, 2))          # both drawn cards red
        if p_reveal:
            for drop_red, p_drop in ((1, F(r5, 5)), (0, F(5 - r5, 5))):
                if p_drop:
                    A[r5 - drop_red] += p5 * p_reveal * p_drop
        # --- Path B: discard 1, then reveal 1 of the surviving 4; it is red.
        for drop_red, p_drop in ((1, F(r5, 5)), (0, F(5 - r5, 5))):
            if not p_drop:
                continue
            r4 = r5 - drop_red
            p_reveal_b = F(r4, 4)                      # revealed card is red
            if p_reveal_b:
                B[r4] += p5 * p_drop * p_reveal_b
    for d in (A, B):
        tot = sum(d.values())
        for k in list(d):
            d[k] /= tot
    return dict(A), dict(B)


def _report_paths(w) -> None:
    A, B = path_posteriors()
    w("\n  Posterior over reds held, given the SAME public class (4, 1, 0):\n")
    w("    reds in hand    Path A (2 seen, then discard)   Path B (discard, then 1 seen)\n")
    for k in range(0, 5):
        a, b = A.get(k, F(0)), B.get(k, F(0))
        w(f"      {k}                    {float(a):8.4f}                        {float(b):8.4f}\n")
    ea = sum(k * v for k, v in A.items())
    eb = sum(k * v for k, v in B.items())
    ga = sum(v for k, v in A.items() if k >= 2)
    gb = sum(v for k, v in B.items() if k >= 2)
    w(f"    expected reds        {float(ea):8.4f}                        {float(eb):8.4f}\n")
    w(f"    P(at least 2 reds)   {float(ga):8.4f}                        {float(gb):8.4f}\n")
    w(f"\n    Both paths certify exactly 'at least 1 red' -- the bound is tight\n"
      f"    for each -- yet they disagree by {float(ga-gb):.3f} on P(>= 2 reds).\n")


def support_tightness(H: int) -> tuple[int, int]:
    """For every reachable class, check that the hand compositions actually
    realized fill the whole box the certainty bounds allow.

    Soundness (nothing outside the box) is forced by the fold. Tightness
    (everything inside the box occurs) is the claim worth checking: together
    they say the class pins the SUPPORT of the public posterior exactly --
    while saying nothing about its shape. Returns (tight, loose) class
    counts; loose must be 0.
    """
    states, _ = reachable_closure(H)
    realized: dict[tuple, set] = defaultdict(set)
    for loser, A, B in states:
        sa = (A[0] + A[1], A[2], A[3])
        sb = (B[0] + B[1], B[2], B[3])
        realized[(loser, sa, sb)].add(((A[0], A[1]), (B[0], B[1])))

    tight = loose = 0
    for (loser, sa, sb), comps in realized.items():
        box = {
            ((r0, sa[0] - r0), (r1, sb[0] - r1))
            for r0 in range(sa[1], sa[0] - sa[2] + 1)
            for r1 in range(sb[1], sb[0] - sb[2] + 1)
        }
        if comps == box:
            tight += 1
        else:
            loose += 1
    return tight, loose


if __name__ == "__main__":
    main()
