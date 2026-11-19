# ADR-010: Pick the shortlist from the all-years ranking, require standalones to be true one-offs that are strong on audience measures alone, and name modern substitutes

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Esther Efua Acquandoh

## Context

Kwame wants three franchise targets and five standalones, each with its reason. The two windows produce different standalone lists: four of the all-years top five were released before 2000. Some high-scoring "standalones" have sequels elsewhere (*The Lion King*, *The Silence of the Lambs*), so a studio might not sell them alone (ADR-004). Box-office figures for old films are what Finance will challenge.

## Decision

- **Franchise picks:** the top 3 by bundle score (ADR-009). They are the same three in both windows: Lord of the Rings, The Avengers, Harry Potter.
- **Standalone picks:** the top 5 by title score among films that (a) belong to no series at all and (b) score at least 50 on audience measures alone (rating and reach). Ranked on all years, because old films are just as licensable. The 2000-onward picks are listed as named substitutes if Finance strikes pre-2000 titles.
- Each pick carries a generated reason that states its ranks.

## Alternatives considered

### Alternative A: Allow series films as standalone picks

- **How it would work:** Drop rule (a).
- **Why it is attractive:** It includes strong films.
- **Why rejected:** A pick the studio will not sell alone wastes a negotiating slot.
- **What the recommendation looks like under it:** *The Lion King* replaces *Inception* (all years). *The Incredibles* and *Monsters, Inc.* replace *Memento* and *WALL·E* (2000 onward). The verdicts and bundle picks do not change.

### Alternative B: Use the 2000-onward picks as the main list

- **How it would work:** Shortlist Spirited Away, Inception, Interstellar, Memento, WALL·E.
- **Why it is attractive:** Finance has nothing to object to.
- **Why rejected:** It discards *Pulp Fiction* and *Forrest Gump*, which rank in the top 9% of the list on audience rating and reach (not just box office). They are valuable back-catalog titles. The rule-(b) audience test already protects against relying on old box-office figures.

### Alternative C: No audience floor

- **How it would work:** Pure title-score ranking.
- **Why it is attractive:** One rule fewer.
- **Why rejected:** A film could make the list on an old box-office multiple alone. That is the figure Finance distrusts. Today the floor changes no pick, but it guards future lists.

## Consequences

- **What this buys:** Picks that are robust: the three bundles are the same in both windows, and two standalone picks (*Spirited Away*, *Inception*) are in both lists. Every pick can be defended without leaning on disputed figures.
- **What this costs:** Three of the five standalone picks are pre-2000 and will draw Finance's objection. The substitutes are ready.
- **What it costs the client if I am wrong:** If audiences on StreamVault prefer recent titles, the modern list is the better buy. Swapping it in costs nothing analytically.
- **What would make me revisit this:** Actual licence prices. A strong title that is costly may be worth less than a good title that is cheap.

## What this survives

Any list size. The picks are a filter and a sort, and the counts are settings (`N_FRANCHISE_PICKS`, `N_STANDALONE_PICKS`). At 500 titles the same rules simply have more candidates to choose from.
