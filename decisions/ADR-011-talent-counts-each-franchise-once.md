# ADR-011: Read talent from directors and the top 3 billed actors, count each franchise once per person, and require two separate results

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Analyst, StreamVault licensing review

## Context

Kwame's negotiators use talent as a lever, so they need to know which directors and lead actors reliably signal a strong title. The data is dominated by franchises: of the 57 people with 3 or more films on the list, **39 made all of them in one series** (F-06). A naive ranking by number of films puts Daniel Radcliffe, Emma Watson and Rupert Grint at the top. That is a Harry Potter finding presented as a talent finding. The brief does not define "lead actor".

## Decision

- **Lead actors** = the top 3 billed cast members. **Directors** = every credited director, so co-directors each count.
- A person's films in the same series are averaged into **one result**. Each standalone film is its own result.
- A person is shown only with **at least 2 separate results**. They are ranked by **lift**: their average result minus the list's typical title score. Hit rate (the share of results above typical) is shown alongside.
- Evidence is labelled "thin" for 2 results and "moderate" for 3 or more.

## Alternatives considered

### Alternative A: Rank by number of films, or by average over all films

- **How it would work:** Count every film equally.
- **Why it is attractive:** Simple, and it rewards a long track record.
- **Why rejected:** It repeats franchises: the top names are the Harry Potter cast.
- **What the recommendation looks like under it:** The talent read would be "Radcliffe, Watson, Grint, Spielberg, Ford". Negotiators would use names that only predict that one series.

### Alternative B: Only the top-billed actor

- **How it would work:** `billing_order == 0`.
- **Why it is attractive:** "Lead" in the strictest sense.
- **Why rejected:** It ignores ensemble leads, and almost no actor reaches two separate results.
- **What the recommendation looks like under it:** Directors are unchanged. Among actors, Tom Hanks, Liam Neeson, Leonardo DiCaprio and Robert Downey Jr. are still positive, all on 2 results. The overall message is the same: actor evidence is thin.

### Alternative C: Require 3 or more separate results

- **How it would work:** Raise the bar.
- **Why it is attractive:** Stronger evidence per name.
- **Why rejected:** Only a handful of people qualify. I kept the 2-result names and labelled them "thin" instead of hiding them, so negotiators can see them along with the warning.

## Consequences

- **What this buys:** A talent read that separates the person from the franchise. **Christopher Nolan** stands out: 5 separate results, all above typical, in both windows. Steven Spielberg is moderate across all years.
- **What this costs:** Most names rest on 2 results. The honest headline is that talent is a weak lever on this list, except for Nolan.
- **What it costs the client if I am wrong:** If a star's franchise work really does reflect their pull, their value is understated here. The negotiators lose a lever, but they do not overpay because of one.
- **What would make me revisit this:** A bigger list. At 500 titles, many more people will reach 3 or more separate results.

## What this survives

A 500-title list, where this read becomes more useful. The joins are checked (`validate="many_to_one"`), all grouping is vectorised, and the thresholds are settings (`LEAD_ACTOR_SLOTS`, `MIN_TALENT_UNITS`).
