#!/usr/bin/env python3
"""Exact size of the REAL heads-up Red/Black game G (no belief reset).

state_counts.py counts the class abstraction (public STATES: lattice-
collapsed procurement, class-merged boundaries). This script counts the
perfect-recall PUBLIC HISTORY TREE of G itself: order-sensitive flip
sequences, full bid chains, composed across rounds with loser-dependent
transitions. That tree is what any solver of the real game (CFR over
full-recall infosets, or exact public-belief-state solving) must index,
because in G every distinct public history generically induces a distinct
posterior -- there is no smaller sufficient statistic (Paper I, Sec. on
what the class forgets).

Counts, all exact bigints:
  paths(n0, n1, s)  full public histories from a round start (post-discard
                    hand sizes n0, n1 >= 1, starter s) to game end.
  dnodes(...)       public decision histories (nodes where someone acts):
                    reorder (2/round), each bid-or-challenge point, each
                    flip-target point, each discard point.
Both are lower bounds on real-game infosets: distinct public histories at
which player i acts are distinct infosets of player i (they differ in i's
own observations). Private refinement (own colours, own orderings, own
discard colours) multiplies further.

Rules encoded (RULES.md secs 4, 9, 10):
  * chain = colour x strictly increasing counts from {1..T}; challenge ends
    bidding and is legal from the second action on; bidder = last raiser
    (starter if chain length odd).
  * procurement: bidder picks a seat per flip, top card revealed; all
    pre-resolution flips are bid-colour; success = c-th bid-colour flip
    (challenger loses), failure = first off-colour flip (bidder loses);
    per-seat flips capped by that seat's hand size.
  * loser discards (no public branching); at hand 0 -> eliminated -> game
    over heads-up; winner starts next round.
"""
from functools import lru_cache
from math import comb, log10

H = 5


def seat_seqs(length: int, n0: int, n1: int) -> int:
    """Seat sequences of `length` flips, per-seat caps n0, n1."""
    return sum(comb(length, a) for a in range(max(0, length - n1),
                                              min(n0, length) + 1))


def contest_records(c: int, n0: int, n1: int) -> tuple[int, int]:
    """(#success records, #failure records) for a claim of c.

    success: exactly c flips, all bid-colour            -> challenger loses
    failure: j bid-colour then 1 off, 0 <= j <= c-1     -> bidder loses
    """
    succ = seat_seqs(c, n0, n1)
    fail = sum(seat_seqs(j + 1, n0, n1) for j in range(c))
    return succ, fail


def flip_decisions(c: int, n0: int, n1: int) -> int:
    """Bidder decision points inside one contest at claim c: before flip
    j+1 the public record is j bid-colour flips, j = 0..c-1."""
    return sum(seat_seqs(j, n0, n1) for j in range(c))


def chains_by_parity(c: int) -> tuple[int, int]:
    """#chains with final count c of (odd, even) length: choose which of
    {1..c-1} appear below the top bid."""
    odd = sum(comb(c - 1, m - 1) for m in range(1, c + 1, 2))
    even = sum(comb(c - 1, m - 1) for m in range(2, c + 1, 2))
    return odd, even


@lru_cache(maxsize=None)
def game(n0: int, n1: int, starter: int) -> tuple[int, int, int]:
    """(paths, decision_nodes, boundary_histories) from a round start."""
    T = n0 + n1
    paths = 0
    # reorder: both live players act once, one public node each
    dnodes = 2
    boundaries = 0
    # opener decision + one responder decision per nonempty chain reached;
    # weight each by the number of ways to reach it (chains are unique
    # histories, so weight 1 each)
    dnodes += 1 + 2 * (2 ** T - 1)
    for c in range(1, T + 1):
        odd, even = chains_by_parity(c)
        succ, fail = contest_records(c, n0, n1)
        fdec = flip_decisions(c, n0, n1)
        for colour in range(2):
            for nch, bidder in ((odd, starter), (even, 1 - starter)):
                if nch == 0:
                    continue
                dnodes += nch * fdec
                for records, loser in ((succ, 1 - bidder), (fail, bidder)):
                    dnodes += nch * records          # the discard decision
                    boundaries += nch * records
                    ln = (n0, n1)[loser]
                    if ln == 1:                       # elimination: game over
                        paths += nch * records
                        continue
                    nn0, nn1 = (n0 - 1, n1) if loser == 0 else (n0, n1 - 1)
                    p, d, b = game(nn0, nn1, 1 - loser)
                    paths += nch * records * p
                    dnodes += nch * records * d
                    boundaries += nch * records * b
    return paths, dnodes, boundaries


def fmt(x: int) -> str:
    return f"{x:.3e} (10^{log10(x):.2f})" if x else "0"


if __name__ == "__main__":
    p, d, b = game(H, H, 0)
    print(f"heads-up H={H}, real game G, public history tree:")
    print(f"  terminal public histories : {fmt(p)}")
    print(f"  public decision histories : {fmt(d)}")
    print(f"  boundary histories        : {fmt(b)}")
    # per-first-round-outcome sanity: one round at 5v5
    T = 2 * H
    one_round = 0
    for c in range(1, T + 1):
        odd, even = chains_by_parity(c)
        s, f = contest_records(c, H, H)
        one_round += 2 * (odd + even) * (s + f)
    print(f"  opening-round outcomes    : {one_round:,} "
          f"(paper's lattice-collapsed resolutions: 119,036)")
    # smaller games for scale
    for h in (1, 2, 3, 4):
        pp, dd, bb = game(h, h, 0)
        print(f"  H={h}: terminal={fmt(pp)}  decisions={fmt(dd)}")
