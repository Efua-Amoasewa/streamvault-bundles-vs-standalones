# ADR-012: Express what to pay for the strongest bundle as a multiple of what a typical standalone on this list is worth, per film

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Esther Efua Acquandoh

## Context

Kwame asks what to pay for the strongest franchise "relative to everything else". The list carries no prices, asking prices or past deal values. Inventing dollar figures would be exactly what Finance attacks. What the analysis does support is how strong each title is compared with the others.

## Decision

Relative value per film = the bundle's score ÷ the median standalone's title score. For Lord of the Rings that is **1.44×** (all years) and **1.63×** (2000 onward). In plain terms, each film is worth up to about 1.4 times a typical standalone on this list, so the 3-film bundle is worth about 4.3 typical standalones. Two further anchors are reported: **2.3×** a typical bundle per film, and **1.17×** the next-best bundle (The Avengers). The single deciding number is the bundle's **weakest film, which still outranks 94% of the list**. It is the only bundle with no weak entry for a studio to hide.

## Alternatives considered

### Alternative A: A dollar price

- **How it would work:** Estimate a licence fee from box office.
- **Why it is attractive:** It is what a negotiator wants.
- **Why rejected:** There is no price data at all. Any dollar figure would be invented and indefensible in the room.

### Alternative B: Relative to the next-best bundle only

- **How it would work:** "Pay up to 17% more per film than for The Avengers."
- **Why it is attractive:** It is the most direct competing purchase.
- **Why rejected:** Kept as a secondary anchor. The brief asks for "relative to everything else", and the standalone is the alternative Kwame's other camp is arguing for.

### Alternative C: Use box-office multiples for the ratio

- **How it would work:** Lord of the Rings 10.96× ÷ the typical standalone's 5.00×, giving 2.2×.
- **Why it is attractive:** A money-based ratio.
- **Why rejected:** It inherits every box-office doubt (F-05), and it measures cinema returns, not a title's value on a streaming service.

## Consequences

- **What this buys:** A negotiating ceiling Kwame can state without inventing prices: "no more than about 1.4 times our going rate for a strong standalone, per film".
- **What this costs:** Title scores are ranks, not money, so a ratio of ranks is an approximation of relative value, not a valuation.
- **What it costs the client if I am wrong:** If value grows faster than rank at the very top (a 90-score title being worth far more than 1.5× a 60), the ceiling is too low and StreamVault could lose the bundle to a competitor. If value grows more slowly, it overpays by up to the same margin. The 94% weakest-film figure is unaffected either way.
- **What would make me revisit this:** Two quarters of StreamVault's own price-per-title and viewing data, which would turn the ratio into a fitted price curve.

## What this survives

Any list size. The deal-note numbers are recomputed by `analysis.deal_note` for whichever bundle ranks first, so next year's note writes its own numbers.
