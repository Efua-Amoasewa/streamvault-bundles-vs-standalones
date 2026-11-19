# ADR-008: Define the 2000-onward window by release year, rank films only against their own window, and do not adjust for inflation

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Esther Efua Acquandoh

## Context

Yaw in Finance distrusts anything released before 2000: inflation, currency reporting, and how box office used to be counted. The brief requires every comparison to be shown in both windows, with any change called out loudly. Several choices are open: the cut-off rule, whether old dollars should be inflated to today's, and whether a 2003 film should be compared with all films or only with post-2000 films.

## Decision

- "2000 onward" means a release date in 2000 or later, which keeps 71 of 112 films.
- In that window, every percentile is recomputed against the **71 modern films only**, so Finance's distrusted figures play no part in the modern result.
- A film's position in its series is still its real position, counted across all years: *Attack of the Clones* is Star Wars film 5, not film 1.
- No inflation adjustment. The box-office multiple divides revenue by budget from the same era, so general inflation cancels out.

## Alternatives considered

### Alternative A: Adjust all money to today's dollars with a price index

- **How it would work:** Multiply budget and revenue by a consumer price index factor.
- **Why it is attractive:** It is Finance's language, and it makes dollar amounts comparable.
- **Why rejected:** It does not change any ratio, so the analysis is unaffected. It would also require an external price series that is not part of the data provided and that I could not verify from TMDb. It matters only if the analysis used dollar amounts, which it deliberately does not (ADR-005, Alternative D).

### Alternative B: Score modern films against the full list

- **How it would work:** Keep all-years percentiles and simply hide pre-2000 rows.
- **Why it is attractive:** A film's score would not change between windows.
- **Why rejected:** Old films' extreme multiples would still set the scale. That is exactly the influence Finance objects to, carried quietly into the "modern" answer.

### Alternative C: A different cut-off (e.g. 1995 or 2005)

- **How it would work:** Move the year.
- **Why it is attractive:** More standalones (1995) or fewer old-reporting doubts (2005).
- **Why rejected:** 2000 is the line Finance itself draws, and the brief names it.

## Consequences

- **What this buys:** The modern window answers Yaw on his own terms. The analysis states plainly that the verdict changes between windows (ADR-006).
- **What this costs:** A film's score differs between windows. Spirited Away is 82.6 overall and 84.7 among modern films. This is intended, but it needs explaining.
- **What it costs the client if I am wrong:** If Finance also distrusts *re-release income* inside post-2000 totals, a few modern figures are still affected. This is noted under Could not verify.
- **What would make me revisit this:** Finance naming a different line, or asking for dollar figures.

## What this survives

Any list size and any future year. The cut-off is one setting (`metrics.MODERN_FROM_YEAR`), and each window is computed by the same code.
