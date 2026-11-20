# ADR-001: Count a film as "franchise" only when two or more films of its series are on the candidate list

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Esther Efua Acquandoh

## Context

The whole question is franchise bundles versus standalone hits, so the boundary between them decides the answer. TMDb marks a film as part of a series (`belongs_to_collection`). Nine films on the list are in a series but are the *only* film of that series on the list: *Jaws*, *The Lion King*, *The Silence of the Lambs*, *Ghostbusters*, *The Incredibles*, *Monsters, Inc.*, *Mad Max: Fury Road*, *Blade Runner* and *The Smurfs*. The brief defines a bundle by how it is *sold* ("take all six or none") and a standalone by how it is *priced* ("one at a time").

## Decision

A film is "franchise" when at least two films of its series are on the list, because only then is it actually offered as a bundle. Everything else is "standalone". Shortlisted standalones must also have no series at all (ADR-006), so the nine edge cases cannot slip into the standalone picks.

## Alternatives considered

### Alternative A: Use TMDb's series flag directly

- **How it would work:** Any film with a `belongs_to_collection` value is franchise.
- **Why it is attractive:** It is objective, needs no rule, and matches how audiences think of these films.
- **Why rejected:** It classifies by how a film is *marketed*, not how it is *sold*. The brief's distinction is commercial. It would also shrink the standalone group from 25 to 16 films (8 from 2000 onward), making every comparison noisier.
- **What the recommendation looks like under it:** Unchanged. The verdict is still standalone for all years (gap −16.1, 95% range −31.7 to −0.6) and too close to call from 2000 onward (−8.9, range −35.2 to +3.3). The same three bundles and five standalones are picked. The box-office-only gap triples (+0.53× → +1.78×), which is the main thing this choice moves (`outputs/sensitivity.csv`, `data_findings.md` F-04).

### Alternative B: Ask the studios which titles they will sell alone

- **How it would work:** Classify from the studios' actual terms.
- **Why it is attractive:** It is the true answer.
- **Why rejected:** Not available. Kwame is out of reach before the review, and the list carries no deal terms.

## Consequences

- **What this buys:** Groups that match what Kwame can actually buy, and a larger standalone sample.
- **What this costs:** Nine films sit in the standalone group despite having sequels somewhere.
- **What it costs the client if I am wrong:** If a studio would only sell *Jaws* or *The Lion King* together with their sequels, those films' strong numbers (67× and 17× box-office multiples) belong on the franchise side. The franchise box-office case would then look stronger. The recommendation would not change (see above), and neither film is on the shortlist.
- **What would make me revisit this:** Deal terms showing which titles are sold alone.

## What this survives

Any list size. The rule is one grouped count (`metrics.classify`), and `rule="tmdb_flag"` switches to the alternative so Adjoa can show both in a meeting.
