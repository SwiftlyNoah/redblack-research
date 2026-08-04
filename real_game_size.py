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
  infosets(...)     EXACT perfect-recall infosets per seat: distinct
                    (public history, own trajectory) pairs at that seat's
                    action points, restricted to realizable pairs.  Own
                    realizability is a binomial prefix-consistency count;
                    opponent realizability is Paper I's support-
                    completeness theorem (the certainty-bound interval is
                    exactly the feasible set), which turns "some opponent
                    trajectory exists" into a constant-time test.
                    Validated against explicit joint enumeration at
                    H=1 and H=2 (exact match, per-seat).

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


# ---------------------------------------------------------------------------
# Exact per-seat INFOSET counts of G (perfect recall).
#
# An infoset of seat i at one of i's action points is a distinct pair
# (public history h, i's own private trajectory), where the trajectory is
# i's initial colour multiset, every ordering string i has chosen at a
# reorder, and every discard colour i has chosen -- exactly what perfect
# recall retains.  A pair is counted iff it is realizable: consistent with
# i's own reveals (binomial prefix-consistency factors) and realizable by
# SOME opponent trajectory.  The opponent-side realizability test is Paper
# I's support-completeness theorem: the certainty bounds (max-folded
# reveals, decayed on discards) pin the opponent's feasible red-count to
# the interval [r_lb, n_opp - b_lb], and EVERY value in it is realizable.
# So "some opponent exists" == "the bounds interval accommodates the
# reveal", a constant-time test, and the count is exact rather than an
# over-count of impossible histories.
#
# Conventions (matching game() above): an "action point" is any node where
# the seat acts under the rules, including forced actions (a challenge at
# chain top, a monochrome or last-card discard); reorder is one action
# point per seat per round; the opener's colour+count choice is one node.
# ---------------------------------------------------------------------------


def my_bid_prefix_nodes(T: int, i_am_starter: bool) -> int:
    """Bid-phase action points of ME per round: the opener node if I open,
    plus every (colour, nonempty chain prefix) after which I act.  Action
    m+1 belongs to the starter iff m is even."""
    nodes = 1 if i_am_starter else 0
    for m in range(1, T + 1):
        acts = (m % 2 == 0) == i_am_starter
        if acts:
            nodes += 2 * comb(T, m)
    return nodes


def _feas(rlb: int, blb: int, pr: int, pb: int, n_opp: int) -> bool:
    """Some opponent hand consistent with bounds can reveal (pr, pb)."""
    return max(rlb, pr) + max(blb, pb) <= n_opp


@lru_cache(maxsize=None)
def infosets(n_me: int, n_opp: int, r_me: int, rlb: int, blb: int,
             i_am_starter: bool) -> int:
    """Exact # of my infosets from a round start, per unit entering
    (history, trajectory) weight.  State: my exact hand (n_me, r_me), the
    public certainty bounds on the opponent (rlb, blb), and who opens."""
    T = n_me + n_opp
    b_me = n_me - r_me
    orderings = comb(n_me, r_me)          # my colour-strings this round
    total = 1                             # my reorder action point
    total += orderings * my_bid_prefix_nodes(T, i_am_starter)

    for red_bid in (True, False):
        for c in range(1, T + 1):
            odd, even = chains_by_parity(c)
            for nch, i_bid in ((odd, i_am_starter), (even, not i_am_starter)):
                if nch == 0:
                    continue
                # --- my flip-target decisions (I am the bidder) ---
                if i_bid:
                    for k in range(c):     # k bid-colour flips so far
                        for a in range(max(0, k - n_opp), min(n_me, k) + 1):
                            pr_me, pb_me = (a, 0) if red_bid else (0, a)
                            po_r, po_b = ((k - a, 0) if red_bid
                                          else (0, k - a))
                            if pr_me > r_me or pb_me > b_me:
                                continue
                            if not _feas(rlb, blb, po_r, po_b, n_opp):
                                continue
                            total += (nch * comb(k, a)
                                      * comb(n_me - a, r_me - pr_me))
                # --- complete contest records ---
                # (j bid-colour flips, then success at j==c or one
                #  off-colour flip from deck `off_me`)
                for outcome in ("success", "fail"):
                    js = [c] if outcome == "success" else list(range(c))
                    for j in js:
                        for a in range(max(0, j - n_opp), min(n_me, j) + 1):
                            pats = comb(j, a)
                            offs = ((None,) if outcome == "success"
                                    else (True, False))
                            for off_me in offs:
                                fme = a + (1 if off_me else 0)
                                fopp = (j - a) + (1 if off_me is False else 0)
                                if fme > n_me or fopp > n_opp:
                                    continue
                                # my/opp reveals
                                if red_bid:
                                    pr_me = a
                                    pb_me = 1 if off_me else 0
                                    po_r, po_b = j - a, \
                                        (1 if off_me is False else 0)
                                else:
                                    pb_me = a
                                    pr_me = 1 if off_me else 0
                                    po_b, po_r = j - a, \
                                        (1 if off_me is False else 0)
                                if pr_me > r_me or pb_me > b_me:
                                    continue
                                if not _feas(rlb, blb, po_r, po_b, n_opp):
                                    continue
                                m_ord = comb(n_me - fme, r_me - pr_me)
                                w = nch * pats * m_ord
                                if w == 0:
                                    continue
                                i_lose = (i_bid if outcome == "fail"
                                          else not i_bid)
                                # folded opponent bounds after the round
                                nrlb, nblb = max(rlb, po_r), max(blb, po_b)
                                if i_lose:
                                    total += w        # my discard point
                                    if n_me == 1:
                                        continue      # eliminated
                                    for dr, db in ((1, 0), (0, 1)):
                                        if (dr and r_me == 0) or \
                                           (db and b_me == 0):
                                            continue
                                        total += w * infosets(
                                            n_me - 1, n_opp, r_me - dr,
                                            nrlb, nblb, False)
                                else:
                                    if n_opp == 1:
                                        continue      # opp eliminated
                                    total += w * infosets(
                                        n_me, n_opp - 1, r_me,
                                        max(nrlb - 1, 0), max(nblb - 1, 0),
                                        True)
    return total


def infosets_total(h: int) -> tuple[int, int]:
    """(starter-seat, non-starter-seat) exact infoset counts at hand h."""
    s = sum(infosets(h, h, r, 0, 0, True) for r in range(h + 1))
    ns = sum(infosets(h, h, r, 0, 0, False) for r in range(h + 1))
    return s, ns


def fmt(x: int) -> str:
    return f"{x:.3e} (10^{log10(x):.2f})" if x else "0"


# ---------------------------------------------------------------------------
# Brute-force validation of infosets() at small hand sizes: walk the JOINT
# game explicitly (both hands, both orderings, every deck choice) and
# collect the set of distinct (public history, own trajectory) pairs at
# each seat's action points.  Slow and exponential -- that is the point:
# it shares no recurrence with infosets().
# ---------------------------------------------------------------------------


def _orderings(r: int, b: int):
    """All distinct colour strings of a hand with r reds, b blacks."""
    n = r + b
    from itertools import combinations as C
    for pos in C(range(n), r):
        yield tuple("R" if i in pos else "B" for i in range(n))


def brute_infosets(h: int) -> tuple[int, int]:
    """(seat0, seat1) infoset counts of the full game at hand size h,
    seat 0 opening, by explicit joint enumeration."""
    sets: tuple[set, set] = (set(), set())

    def round_start(hands, starter, hp, trajs):
        for i in (0, 1):
            sets[i].add((hp, trajs[i]))          # reorder action point
        (r0, b0), (r1, b1) = hands
        for o0 in _orderings(r0, b0):
            for o1 in _orderings(r1, b1):
                t = (trajs[0] + (o0,), trajs[1] + (o1,))
                opener(hands, (o0, o1), starter, hp + (("re",),), t)

    def opener(hands, ords, starter, hp, t):
        T = sum(sum(x) for x in hands)
        sets[starter].add((hp, t[starter]))
        for col in "RB":
            for k in range(1, T + 1):
                bidding(hands, ords, starter, col, k, starter,
                        hp + (("bid", col, k),), t)

    def bidding(hands, ords, starter, col, last, last_bidder, hp, t):
        T = sum(sum(x) for x in hands)
        actor = 1 - last_bidder
        sets[actor].add((hp, t[actor]))
        contest(hands, ords, col, last, last_bidder,
                hp + (("chal",),), t)            # challenge
        for k in range(last + 1, T + 1):         # raises
            bidding(hands, ords, starter, col, k, actor,
                    hp + (("bid", col, k),), t)

    def contest(hands, ords, col, claim, bidder, hp, t):
        def flip(ptr, got, hp):
            sets[bidder].add((hp, t[bidder]))    # flip-target decision
            for d in (0, 1):
                if ptr[d] >= sum(hands[d]):
                    continue
                card = ords[d][ptr[d]]
                hp2 = hp + (("flip", d, card),)
                if card != col:
                    resolve(hands, bidder, hp2, t)       # bidder loses
                elif got + 1 == claim:
                    resolve(hands, 1 - bidder, hp2, t)   # challenger loses
                else:
                    p2 = list(ptr)
                    p2[d] += 1
                    flip(tuple(p2), got + 1, hp2)
        flip((0, 0), 0, hp)

    def resolve(hands, loser, hp, t):
        sets[loser].add((hp, t[loser]))          # discard action point
        r, b = hands[loser]
        if r + b == 1:
            return                               # elimination: game over
        for dc in ("R", "B"):
            if (dc == "R" and r == 0) or (dc == "B" and b == 0):
                continue
            nh = list(hands)
            nh[loser] = (r - 1, b) if dc == "R" else (r, b - 1)
            t2 = list(t)
            t2[loser] = t[loser] + (("disc", dc),)
            round_start(tuple(nh), 1 - loser,
                        hp + (("disc", loser),), tuple(t2))

    for r0 in range(h + 1):
        for r1 in range(h + 1):
            round_start(((r0, h - r0), (r1, h - r1)), 0, (),
                        ((r0,), (r1,)))
    return len(sets[0]), len(sets[1])


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

    print()
    print("exact perfect-recall infosets (per seat; seat 0 opens):")
    for h in (1, 2, 3, 4, 5):
        s, ns = infosets_total(h)
        print(f"  H={h}: starter={fmt(s)}  non-starter={fmt(ns)}  "
              f"total={fmt(s + ns)}")

    print()
    print("brute-force validation (explicit joint enumeration):")
    for h in (1, 2):
        b0, b1 = brute_infosets(h)
        s, ns = infosets_total(h)
        ok = "OK " if (b0, b1) == (s, ns) else "MISMATCH"
        print(f"  {ok} H={h}: brute=({b0:,}, {b1:,}) "
              f"recursion=({s:,}, {ns:,})")
