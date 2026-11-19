# ADR-009: Value a bundle at the average of all its films, judged on the whole released series whenever that is weaker than the films offered

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Analyst, StreamVault licensing review

## Context

Studios sell bundles all-or-nothing, so StreamVault pays for the weak entries too. That is half of Kwame's team's argument. In 10 of 23 bundles, the list holds only part of what has been released, and the missing films are the newest and weakest (*The Matrix Resurrections* lost money; F-01). I can't see what each studio's bundle actually includes.

## Decision

- **Bundle score** = the **mean** title score of its films. Every film is paid for, so every film counts. Title scores are ranks capped at 100, so the mean is not distorted by extremes (ADR-006).
- The score is computed twice, on the films offered and on the whole released series, and the bundle is valued at the **lower** of the two.
- The weakest film is reported next to every bundle.
- A bundle needs at least 2 films in the window to be ranked.

## Alternatives considered

### Alternative A: Judge only the films on the list

- **How it would work:** Ignore off-list films.
- **Why it is attractive:** It is what was quoted, and it needs no extra data.
- **Why rejected:** If the studio insists on the whole series, Star Wars is really a 6.17× bundle, not 10.83×, and Jurassic Park is 4.97×, not 8.93×.
- **What the recommendation looks like under it:** The same three picks (Lord of the Rings, The Avengers and Harry Potter are complete on the list), and the same verdicts. Lower down the ranking, incomplete bundles look better than they are. That matters if a top pick fails in negotiation and the team moves down the list.

### Alternative B: Median film per bundle

- **How it would work:** The bundle's middle film.
- **Why it is attractive:** Consistent with ADR-006.
- **Why rejected:** A median ignores the weakest films entirely in a 3-film bundle, and those weak films are what the "overpaying for weak middle entries" camp is worried about.

### Alternative C: Value a bundle at its best film

- **How it would work:** Take the top film's score.
- **Why it is attractive:** The flagship film is what drives audiences to a series.
- **Why rejected:** It is the instinct that produced the underperforming trilogy deal.

## Consequences

- **What this buys:** Bundle rankings that do not reward a list for leaving out a series' weak later films. The weakest-film figure gives negotiators a concrete argument ("you are asking us to pay for *Age of Ultron* at *Avengers* prices").
- **What this costs:** Bundles that are incomplete on the list may be penalised for films the studio would not actually include.
- **What it costs the client if I am wrong:** If studios sell exactly what is listed, ten incomplete bundles are undervalued. Star Wars would rise from 8th to 4th, just behind Harry Potter (61.7 vs 63.3). None would enter the top 3, but Star Wars would become the first reserve.
- **What would make me revisit this:** The studios' actual bundle contents.

## What this survives

A 500-title list. One `/collection` request per series (not per film) fetches each series' film list, and all scoring is grouped and vectorised. `bundle_basis="on_list"` reruns Alternative A.
