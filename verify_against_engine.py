#!/usr/bin/env python3
"""Cross-check the paper's independently-derived counts against the shipped
round-graph builder in simulator/src/redblack/solver/graph.py.

The paper re-derives everything from the rules; this script proves the
derivation and the implementation agree, so a discrepancy is a real bug in
one of them rather than a difference of convention.

Run from research/:  ../simulator/.venv/bin/python verify_against_engine.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "simulator" / "src"))

from redblack.solver import graph, rounds                      # noqa: E402
from redblack.solver.rounds import EntryClass2, SeatStat       # noqa: E402

import state_counts as sc                                      # noqa: E402

fails = 0


def check(label: str, mine: int, theirs: int) -> None:
    global fails
    ok = mine == theirs
    fails += 0 if ok else 1
    print(f"  {'OK ' if ok else 'FAIL'}  {label:<44} paper={mine:>9,d}  engine={theirs:>9,d}")


print("round automaton: bid / procurement / resolution node counts")
for starter in (0, 1):
    for n0, n1 in ((1, 1), (2, 2), (2, 3), (5, 5), (3, 5)):
        g = graph.build_graph(starter, n0, n1)
        tag = f"starter={starter} ({n0},{n1})"
        check(f"{tag} bid nodes", sc.bid_nodes(n0 + n1), len(g.bid))
        check(f"{tag} proc nodes", sc.proc_nodes(starter, n0, n1), len(g.proc))
        ends = {
            e.target
            for acts in g.proc.values()
            for a in acts
            for e in (a.matched, a.mismatch)
            if e.kind == "round_end"
        }
        check(f"{tag} resolutions", sc.resolution_edges(starter, n0, n1), len(ends))

print("\npublic class space: per-seat statistic and total class count")
stats = [SeatStat(n, r, b) for n in range(1, 6) for r in range(n + 1) for b in range(n - r + 1)]
check("per-seat SeatStat values (H=5)", sc.seat_stat_count(5), len(stats))
engine_classes = sum(
    1
    for loser in (0, 1)
    for s0 in stats
    for s1 in stats
    if rounds.is_feasible(EntryClass2(loser, s0, s1))
) + 1
check("total classes (H=5)", sc.class_count(5), engine_classes)

print("\nterminal classes and layer assignment")
engine_terminal = sum(
    1
    for loser in (0, 1)
    for s0 in stats
    for s1 in stats
    if rounds.is_terminal(EntryClass2(loser, s0, s1))
)
mine_terminal = sum(
    1
    for loser in (0, 1)
    for s0 in sc.seat_stats(5)
    for s1 in sc.seat_stats(5)
    if sc.is_terminal(loser, s0, s1)
)
check("terminal classes (H=5)", mine_terminal, engine_terminal)

agree = all(
    sc.post_total(loser, s0.n, s1.n) == rounds.post_total(EntryClass2(loser, s0, s1))
    for loser in (-1, 0, 1)
    for s0 in stats
    for s1 in stats
)
print(f"  {'OK ' if agree else 'FAIL'}  post_total agrees on every class")
fails += 0 if agree else 1

print("\nreachability: every reachable class must be engine-feasible")
_, reach = sc.reachable_closure(5)
bad = [
    (loser, sa, sb)
    for loser, sa, sb in reach
    if not rounds.is_feasible(EntryClass2(loser, SeatStat(*sa), SeatStat(*sb)))
]
print(f"  {'OK ' if not bad else 'FAIL'}  {len(reach):,d} reachable classes, "
      f"{len(bad)} not engine-feasible")
fails += 0 if not bad else 1

print(f"\n{'ALL CHECKS PASSED' if not fails else f'{fails} CHECK(S) FAILED'}")
sys.exit(1 if fails else 0)
