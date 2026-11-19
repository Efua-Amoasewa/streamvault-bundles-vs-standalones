# ADR-007: Treat any budget or revenue below $10,000 as "not reported", not as a real figure

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Analyst, StreamVault licensing review

## Context

TMDb stores an unknown budget or revenue as `0`, and sometimes as junk: *The Lion King 1½* shows revenue of **$1,465**. None of the 112 films on this year's list has the problem, but 3 of the 39 franchise films off the list do. A 500-title list will contain many more. Unguarded, $1,465 ÷ $0 produces an infinite multiple that would top every ranking.

## Decision

A budget or revenue below $10,000 is treated as missing. The box-office multiple is then left blank, and that film's title score uses rating and reach only (ADR-005). The threshold is one named setting, `metrics.MIN_CREDIBLE_DOLLARS`.

## Alternatives considered

### Alternative A: Drop any film with missing money

- **How it would work:** Remove it from the analysis.
- **Why it is attractive:** Every remaining film has complete data.
- **Why rejected:** A film with a strong rating and wide reach is still a real candidate. Dropping it shrinks the smallest group (standalones), which is already the weak point (ADR-006).

### Alternative B: Only treat exactly zero as missing

- **How it would work:** `budget == 0` → missing.
- **Why it is attractive:** It exactly matches TMDb's convention.
- **Why rejected:** It lets $1,465 through.

### Alternative C: A higher floor (e.g. $100,000)

- **How it would work:** Raise the threshold.
- **Why it is attractive:** It catches more typos, such as "5" meaning 5 million.
- **Why rejected:** Genuine low-budget films exist: *Mad Max* (1979) cost $350,000. A higher floor risks erasing real figures. $10,000 is below any plausible feature-film budget and above every junk value found.

## Consequences

- **What this buys:** No infinite or absurd multiples. The film still counts.
- **What this costs:** A wrong figure *above* $10,000 still passes (residual risk in F-09).
- **What it costs the client if I am wrong:** Today, nothing: no film on the list is affected, and the recommendation is identical with or without the floor. Next year, a typo just above the floor could inflate one title's money rank. The other two measures limit the damage to about a third of its score.
- **What would make me revisit this:** A 500-title run where the diagnosis shows many films just above the floor.

## What this survives

A 500-title list full of direct-to-video and small films with unreported figures. The check is one vectorised comparison, and `src/diagnose.py` reports how many films it caught every run, so Adjoa can see it working.
