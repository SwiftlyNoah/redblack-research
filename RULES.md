# Red/Black — Complete Rules

Red/Black is a hidden-information bidding game for 2–10 players. A single shared deck is dealt face-down and players bid on how many cards of a chosen color are in play across all hands. Opponents either raise the bid or challenge it, in which case the bidder must literally produce the claimed cards by flipping from any player's deck. Lose a contest → discard a card. Last player standing wins.

This document is intended to be self-contained and precise enough to implement a rules engine or a strategic bot from. All references to "the engine" describe the authoritative server logic in `packages/shared/src/engine/`.

---

## 1. Components

- **One shared 52-card deck.** Only color matters. There are exactly **26 red** cards and **26 black** cards. Suits and ranks are not used and do not exist in the game state.
- Each card has a stable identity (an opaque id) so it can be tracked across reorders and discards, but the only gameplay-relevant attribute is `color ∈ {red, black}`.
- **No card is ever drawn after the deal.** Hands only ever shrink (via discards). The total number of cards in play decreases monotonically.

## 2. Players and setup

- Supported player counts: **2 to 10** (inclusive).
- At game start, every player is dealt exactly **5 cards** from the shuffled 52-card deck. So with `N` players, `5·N` cards are dealt; the remaining `52 − 5·N` cards are removed from the game and never seen.
- Hand size of 5 is the **maximum** any player can ever hold. A player's hand only ever shrinks; cards are never drawn or returned.
- Each player sees only their own cards. All other hands are face-down (unknown color, but the **count** of cards in each opponent's hand is always public).
- Seats are arranged in a fixed circular turn order. Turn order proceeds clockwise around the table. Eliminated seats are skipped.

## 3. Hand structure (critical)

- A player's hand is an **ordered list** of cards. The order matters for procurement (see §6).
- **Index 0 is the TOP of the deck** — i.e., the first card that will be flipped if someone procures from this player.
- Players reorder their own hand secretly during the **reorder phase** (see §4). Between reorders, the order is fixed.
- A player always knows the colors and order of their own cards.

## 4. Round structure

A round consists of four phases in order:

1. **Reorder** — every non-eliminated player privately re-arranges their hand and confirms.
2. **Bidding** — the starting player bids; turn passes clockwise; each subsequent player either raises or challenges.
3. **Procurement** — triggered by a challenge; the bidder flips cards trying to produce the bid.
4. **Discard** — the loser of the procurement secretly removes one of their cards.

Then the next round begins (back to reorder), unless only one player remains, in which case the game is over.

A turn clock applies in every phase. Ranked games are fixed at **15 seconds** per turn plus a **60-second** per-player reserve; a friendly host picks a preset (`relaxed` 30s/180s, `standard` 15s/60s, `blitz` 10s/30s) or plays untimed. Running out of time has different consequences per phase - see §11.

### 4a. Reorder phase

- Every non-eliminated player reorders their hand simultaneously and privately.
- Reorder is the **only** time hand order can be changed.
- Once a player confirms their order, it is locked for the round.
- The phase ends when **all** non-eliminated players have confirmed. Then bidding begins.
- Cards revealed by flips in the previous round (see §6) are visible during the previous round's resolution but become hidden again at the start of the next reorder. A player may use that revealed information to decide their new ordering.

### 4b. Bidding phase

- The **starting player** of the round bids first.
  - In round 1, the starting player is seat 0 (the host).
  - In subsequent rounds, the **winner of the previous procurement** (the side that did not lose a card) is the starting player. If that player was somehow eliminated, turn passes clockwise to the next non-eliminated seat.
- A bid is a pair `(count, color)`, written e.g. `3 red`.
- The first bid of the round must be at least `1 red` or `1 black` (count ≥ 1).
- A bid must satisfy: `count ≤ total_cards_in_play` (sum of all non-eliminated players' hand sizes).
- After the first bid, turn passes clockwise. Each subsequent active player must do **exactly one** of:
  - **Raise**: place a new bid that
    - keeps the **same color** as the current bid, AND
    - has a strictly greater count (at least previous count + 1). There is no upper bound on the increment beyond the total-cards-in-play limit.
  - **Challenge**: declare that the current bid is a lie. This immediately ends bidding and transitions to procurement.
- A player **cannot** change colors. Once the round's first bid fixes a color, every subsequent bid in that round is on the same color, with strictly increasing counts.
- A player **cannot** pass without bidding or challenging — those are the only two legal moves once a bid exists.
- **Challenge is legal on any turn after the first bid**, including the second action of the round. It is not legal as the very first action (there is no bid yet to challenge).

### 4c. Procurement phase

When a player challenges, the most recent bid `B = (count, color)` becomes the "claim" the bidder must prove.

- The **bidder** controls procurement (the challenger does nothing; other players do nothing).
- The bidder repeatedly performs **flip** actions:
  - On each flip, the bidder selects a **target seat** (their own or any other non-eliminated player's seat).
  - The card flipped is the **current top** of that target's deck (the next un-flipped card from index 0 downwards). Each player's deck is consumed top-down independently — once you've flipped seat X's first card, the next flip from seat X reveals X's second card, and so on.
  - The flipped card's color is revealed to everyone publicly.
- The bidder may **switch target seats freely between flips** (e.g., flip seat 2's top, then seat 0's top, then seat 2's second card).
- A player whose card was flipped **cannot** prevent it; they have no action during procurement.
- After every flip, one of three things happens:
  - **Wrong color** (color ≠ bid color): procurement ends immediately. **Bidder loses** the contest.
  - **Right color** AND total revealed-of-bid-color now `< count`: procurement continues; bidder must keep flipping.
  - **Right color** AND total revealed-of-bid-color now `≥ count` (i.e., `= count`, since it can only increment by one): procurement ends. **Challenger loses** the contest.
- Equivalently: the bidder must reveal `count` cards of `color` **before** flipping a single card of the other color. The first off-color flip is fatal to the bidder. Reaching the target count is decisive for the bidder.
- The bidder must always be able to flip something (since the bid was capped at total cards in play, and only fully-flipped decks become unflippable). A human bidder who runs out of clock mid-procurement forfeits the seat; a bot-held seat falls back to flipping its own deck if it has cards left, else any non-eliminated player's (see §11).

### 4d. Discard phase

- The **loser** of procurement (bidder if any wrong-color flip occurred; challenger if the bidder reached the bid) chooses **one card from their hand** to remove.
- The choice is **private** — the discarded card's identity is not revealed to other players (it is recorded for end-of-game audit / replay only).
- **Anonymity guarantee.** Other players learn only that the hand shrank by one card. Which card left — including whether it was a card previously flipped face-up — must not be determinable from anything the game exposes. In particular, no client-visible data may allow correlating a card's identity across a discard (see §6a). Knowledge like "she still holds that black I saw flipped" becomes probabilistic the moment she discards: she may have discarded it.
- If the loser holds exactly **one** card, the discard is forced (no choice) and resolves automatically.
- Discarding their last card **eliminates** the player. They take no further actions; turn order skips them.
- After the discard, the round ends.

## 5. Win condition

- A player is **eliminated** when their hand reaches 0 cards.
- The game ends when exactly **one** non-eliminated player remains. That player wins.
- Eliminated players are ranked by the **round in which they were eliminated** (later rounds = better rank). The winner is rank 0; the first player eliminated is rank `N − 1`.

## 6. Information visibility (full specification)

This is the canonical list of what each player knows. A bot's "information set" is exactly this.

**Always public to everyone:**
- The number of players, their seats, and which seats are eliminated.
- The current phase, round number, and active seat.
- The number of cards remaining in **every** player's hand.
- The full bid history of the **current** round, in order.
- The full flip history of the **current** procurement (if in procurement), in order: which seat was flipped, which slot, what color was revealed.
- The outcome of the most recent completed round: who lost, what bid was being tested, the full sequence of flips. **The discarded card's identity is NOT public.**

**Private to each player:**
- The colors and order of their own hand.
- The identity of any card they themselves discarded (no one else learns it).

**Reset between rounds:**
- The bid history is cleared at the start of each new round.
- Flips from the previous round become hidden again at the start of the next reorder phase. The fact that a card was flipped (and what color it was) is **visible during the round it was flipped in and through that round's discard phase**, but is hidden again from public view once the next reorder begins. (Players are free to remember it; the engine simply stops surfacing it. A bot must remember it itself.)
- A card that was flipped in round K is still in its owner's hand for round K+1 unless that owner was the loser and chose to discard it — but its position in the deck is whatever the owner sets during the next reorder.

**Persistent across rounds (memory a bot should maintain):**
- The 26R / 26B global card budget. Every flipped card observed (in any round) reduces the unknown distribution — as **multiset** knowledge about that player's hand ("I have seen a black and a red flipped from her hand"), degraded by that player's subsequent discards: you can never know whether a discard removed a previously-seen card (§4d anonymity, §6a).
- Every discarded card's existence (count of total cards in play) but **not** its color or identity, **unless** the discarder voluntarily exposes it (which they cannot — there is no such action).
- Bidding behavior of opponents in past rounds (signal about their hands and their bluffing tendency).

### 6a. Card identity anonymity (implementation requirement)

Projected views must not give opponents any stable per-card identity that survives a reorder. Opponents' unflipped cards are indistinguishable card backs; a card flipped in round K is identifiable only within round K (by its slot, until the next reorder scrambles positions). After the next reorder, all of a player's cards are anonymous again: observers may remember the **colors** they saw (multiset knowledge, above), but may never re-identify which physical card is which — and therefore can never determine which card a discard removed. Any client-visible identifier (card id, stable ordering key, etc.) that would allow cross-reorder or cross-discard tracking of an opponent's card violates this rule.

## 7. Worked example

3 players: Alice (seat 0), Bob (seat 1), Carol (seat 2). Alice is dealt RRBBR, Bob BBRBR, Carol RRRBB. Each holds 5 cards.

1. **Reorder.** Each privately orders their hand. Alice puts a black on top (index 0); Bob puts a red on top; Carol leaves hers as RRRBB.
2. **Bidding.** Alice opens with `3 red`. Bob raises to `5 red`. Carol challenges.
3. **Procurement.** The current bid is `5 red`, so Bob (the bidder) must flip 5 reds before any black.
   - Bob flips Alice's top: black. **Bob loses immediately.** Procurement ends.
4. **Discard.** Bob secretly removes one card (say, a black). His hand is now 4 cards (BRBR in his private view).
5. **Next round** starts. Carol won the procurement (she didn't lose a card), so she is the new starting bidder. All players reorder, then Carol bids.

Note that everyone now publicly knows Alice's old top card was a black — but only for this current round's resolution. After Carol opens reorder for the next round, that information is no longer surfaced by the engine, though all players (and any bot) should still remember it: Alice still holds that black somewhere in her hand of 5 (she didn't lose it), and total cards in play decreased by 1.

## 8. Round 1 starting player & turn rotation

- Round 1: seat 0 (the host) starts.
- Turn order is clockwise: from seat `s`, the next active player is found by stepping clockwise (in the engine: **increasing** seat index modulo `N`) and skipping eliminated seats.
- Subsequent rounds: the **winner of the previous procurement** starts. (The engine stores this as `lastRoundOutcome.winnerSeat`.)

## 9. Bid validity — quick reference

A bid `(count, color)` placed by the active player is valid iff:
- `count` is a positive integer.
- `count ≤ Σ hand sizes of non-eliminated players` (cannot bid more than exists).
- If a previous bid `(prev_count, prev_color)` exists this round:
  - `color == prev_color`, AND
  - `count > prev_count` (strictly greater; equivalently, `count ≥ prev_count + 1`).

## 10. Challenge validity

A challenge by the active player is valid iff a bid exists in the current round's bid history. There is no other restriction — challenge is legal on the second action of the round (the player immediately after the opener) and on every turn thereafter.

## 11. Time-outs

Two different clocks, with two different consequences. (Engine: `reorderWindow` / `turnWindow` and `timeoutAction`.)

**Reorder** gets a flat window of `turnMs`, exempt from the reserve. When it expires, **every** unconfirmed player's hand auto-confirms in its **current** order and bidding begins. Nobody is penalised.

**Turn-based phases** (bidding, procurement, discard) give the active seat `turnMs` **plus whatever reserve it has left**. Acting after `turnMs` drains the reserve by the overrun; the reserve never refills. When the deadline passes - that is, once `turnMs` and the reserve are both gone - the seat is **forfeited**, with the same consequences as resigning (§12). There is no auto-bid and no auto-challenge for a human seat: running out of time loses the seat, not just the turn.

Seats played by a bot have no clock at all (a server task drives them), and an untimed game has no deadlines in any phase.

### 11a. Bot fallback actions

Separately from time-outs, a bot-held seat needs an always-legal move when no better decision is available (or its chosen one proves illegal). The engine's fallback (`safeBotAction`) is:

| Phase | Fallback |
|---|---|
| Reorder | Confirm hand in its **current** order. |
| Bidding, no bid yet | Open with `1 red`. |
| Bidding, bid exists | **Challenge.** |
| Procurement (bidder) | Flip from the bidder's **own** deck if it has cards left, else from any non-eliminated player with cards left (in seat order). |
| Discard | Discard the **rightmost** card in hand (highest index, i.e. the bottom of the deck). |

A bot should treat "fall back to challenge" as the default consequence of having no plan once a bid is on the table.

## 12. Edge cases

- **Forced discard.** If the procurement loser has exactly one card, the discard is automatic and the player is eliminated immediately.
- **All-but-one elimination via single discard.** If a discard reduces the table to one non-eliminated player, that player is the winner and the game ends without a further reorder.
- **Bid count cap.** With small hands late game, the bid count is capped by total cards in play. With 2 players holding 1 card each, the maximum bid is `2 <color>`.
- **Procurement exhaustion.** It is impossible for the bidder to "run out of cards to flip" before the procurement resolves, because the bid was constrained to ≤ total cards in play. The worst case is that the bidder must flip every card on the table — if all of them are the bid color, the challenger loses; if any are off-color, the bidder loses on that flip.
- **First-bid challenge is illegal**, but auto-action covers any case where the opener disconnects (it bids `1 red`).
- **Eliminated players and procurement targets.** The bidder may not flip from an eliminated player's (empty) seat; eliminated seats hold no cards.

## 13. State transitions (engine perspective)

```
[start] → reorder (round 1)
reorder → bidding              (when all non-eliminated players confirm)
bidding → bidding              (place_bid by active player)
bidding → procurement          (challenge by active player)
procurement → procurement      (flip, no resolution yet)
procurement → discard          (flip resolves: wrong color OR bid reached)
discard → reorder              (loser discards; >1 player remains; round++)
discard → finished             (loser discards; only 1 player remains)
```

The active seat shifts according to:
- During bidding: clockwise to the next non-eliminated seat after each bid.
- On challenge: active seat becomes the **bidder** (they control flips).
- On procurement resolution: active seat becomes the **loser** (for discard).
- After discard: active seat becomes the **procurement winner** (for next round's bidding), set during reorder confirmation.

## 14. Strategy notes for a bot

These are not rules — they are observations about the game's structure that a learning agent should be aware of when designing its policy.

### 14a. State representation

A sufficient information state for the active bot at any decision point includes:
- Own hand (ordered list of colors).
- Public hand sizes of every player (including own).
- Bid history this round.
- Flip history this procurement (and memory of previous rounds' flips, mapped to known cards still held by each player).
- Identities of cards a bot has discarded itself (private).
- Round number; phase; which seat is active; which seat starts the round.
- Turn-order distance to each opponent (who acts after the bot).

From this, a bot can compute, for each opponent, a posterior over the unordered multi-set of colors in their hand (refined by Bayesian conditioning on prior bids and the global 26R/26B budget).

### 14b. Reorder strategy

- The top card of your deck is the first thing flipped if you become a procurement target. If you put a black on top and someone procures `red`, you instantly bust them — but only if they target you first. Bidders prefer to flip players whose tops they expect to match.
- Mixing your top card across rounds (sometimes top-red, sometimes top-black) prevents opponents from inferring your hand from your reorder behavior.
- Putting your minority color on top is a defensive move (bidder hits a non-match early on you); putting majority color on top is offensive (you can flip safely from your own deck during your own procurement).

### 14c. Bidding strategy

- A bid `(count, color)` is **provable** by the bidder iff at least `count` cards of `color` are in play. The bidder's hand contributes some known reds/blacks, and the rest of the table contributes uncertain colors. Compute the posterior probability that `(your reds in hand) + (opponent reds total) ≥ count`. This is the lower bound on the chance you can survive a challenge.
- Higher counts increase the count of cards you must produce but also increase the probability the **next** bid is a challenge rather than a raise. The marginal edge of bidding `k+1 red` vs. `k red` is determined by whether the next player thinks `k+1` is true.
- Bluff equity: if you bid for cards you don't have, you rely on either (a) opponents holding more of that color than realistic, or (b) being able to flip cleverly from opponents whose top cards you can predict.
- Do not bid above the total card count in play (it's illegal).
- The round's first bid sets the color for the entire round. Choosing your minority color as the first bid forces opponents to commit to producing that color too if they raise.

### 14d. Challenge strategy

- The decision is binary: "I would rather see procurement resolved at the current count than raise it." Equivalent to: P(bid is true) < P(I can produce one more of this color in the current public state) − some risk premium.
- Tools for estimating P(bid is true): your own hand cards of that color subtract from the unknowns; opponents who have already raised credibly likely hold ≥1 of the bid color; the global 26/26 budget bounds the universe.
- The active bidder when a player challenges is the **most recent bidder**, not the challenger — so the challenger never produces cards. Only the bidder's hand and procurement choices determine the outcome.

### 14e. Procurement strategy (flip ordering)

- The bidder picks both *whom* to flip and *when to switch*. Flipping a card commits the information to public view.
- Flip from decks whose top cards you most strongly believe are the bid color.
  - Your own deck's top is known with certainty. If your top matches the bid color, flipping from yourself is a free win toward the count.
  - Opponents who recently raised to the bid color likely hold cards of that color, but you don't know which slot it's in.
- Once a player's top is consumed (off-color or on), the next slot is unknown again. Don't keep flipping from a deck whose top you've just busted.
- The optimal flip policy is a sequential decision under uncertainty. A bot can plan it as a tree search: at each step, pick the seat and slot maximizing P(success of remaining procurement), conditioned on the public state plus your private hand.
- Note that flipping reveals **public information** even on success: opponents learn that seat S held color C in slot K. In a long game this leaks information that may affect later rounds (though the order resets at the next reorder).

### 14f. Discard strategy

- Discard is private. Keeping your stronger color (or the color that will let you bid offensively next round) is usually correct.
- If you suspect future rounds will be on the opposite color, discarding from the opposite color preserves your ability to procure.
- The discarded card **does** reduce the global card budget by one (publicly known), but its color stays hidden — opponents update only their joint posterior over your hand using the constraint "lost one of (your hand) + (universe constraint)".

### 14g. Endgame

- Once total cards in play are small (e.g., ≤ 6), bid counts are mechanically bounded and bluffs are easier to detect because uncertainty shrinks.
- Heads-up (2 players), the game becomes a near-perfect-information bluff battle — your hand plus opponent's hand size plus card-budget arithmetic gives you a tight posterior on opponent's colors. Optimal play approaches a solvable extensive-form game.

### 14h. Self-play training notes

- The game is a partially-observable, finite-horizon, sequential, multi-agent game with private information. Suitable algorithms: counterfactual regret minimization (CFR/CFR+) with abstraction over hand multi-sets; or deep RL with belief-state inputs.
- A useful abstraction: opponents' hands are multi-sets `(reds, blacks)` rather than ordered lists. The order matters only during the current procurement (top-down), so during reorder/bidding decisions, an opponent's order is best modeled as a uniform distribution over permutations of their multi-set unless their behavior implies otherwise.
- Reward signal: terminal reward of +1 for the winner, 0 for everyone else. For richer training, use rank-based reward (e.g., `(rank − (N−1)/2)` normalized) to differentiate finishing 2nd from finishing last.
- Self-play caveat: deterministic bots will telegraph their hand by their reorder/bid choices. Mixed strategies are essential, especially at the reorder stage.

## 15. Glossary

| Term | Definition |
|---|---|
| **Bid** | A claim of the form `(count, color)` — that there are at least `count` cards of `color` across all in-play hands. |
| **Raise** | A new bid in the same round, same color, strictly higher count. |
| **Challenge** | An action by the active player that ends bidding and forces the most recent bidder to procure. |
| **Procurement** | The phase where the bidder flips cards trying to reach the bid count of the bid color before any off-color flip. |
| **Flip** | A single reveal of the top card of a chosen player's deck during procurement. |
| **Top of deck** | Index 0 of a hand's ordered list — the first card to be flipped. |
| **Reorder** | Pre-bidding phase where each player privately re-arranges their own hand. |
| **Discard** | The procurement loser secretly removes one card from their hand. |
| **Elimination** | Triggered when a player's hand reaches 0. |
| **Round** | One full reorder → bidding → procurement → discard cycle. |

### 15a. Player-facing wording

The engine, the code and this document use the canonical terms above. Copy shown to players (UI strings, aria-labels, marketing, SEO) must use the player-facing wording below instead.

| Canonical term | Player-facing wording |
|---|---|
| Procurement | reveal |
| Procure / prove | turn up (or show) |
| Reorder | set your order |
| A player's cards / hand | their deck |
| Bidder succeeded | "bid good" |
| Bidder failed | "bid failed" |
