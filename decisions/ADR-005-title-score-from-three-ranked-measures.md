# ADR-005: Judge each title by one score that averages its rank on audience rating, audience reach and box-office return

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Analyst, StreamVault licensing review

## Context

The brief never says what "worth licensing" means. StreamVault earns from people watching its catalogue, but the data has no viewing figures (see Could not verify). TMDb offers three relevant signals. The audience rating (`vote_average`) measures how much viewers liked a film. The number of ratings (`vote_count`) measures how many people engaged with it. Revenue ÷ budget measures commercial pull in cinemas. These sit on very different scales: 0–10, thousands to tens of thousands, and 1× to 67×. Box office also carries Finance's doubts about pre-2000 figures (F-05).

## Decision

Each film gets three percentile ranks from 0 to 100, measured against the other films in the same time window, for quality (rating), reach (number of ratings) and money (box-office multiple). Its **title score** is the average of the three. If a film's money figures are not credible (ADR-007), its score uses the other two.

## Alternatives considered

### Alternative A: Box-office multiple only

- **How it would work:** Rank films on revenue ÷ budget alone.
- **Why it is attractive:** It is the only money measure, and money is what Kwame's board speaks.
- **Why rejected:** It measures how a film did in cinemas decades ago, not how much StreamVault viewers will watch it. It is the measure most exposed to re-release income and old-era reporting (F-05). It also gave the noisiest comparison of all, with a 95% gap range of −32 to +41 points.
- **What the recommendation looks like under it:** Too close to call in **both** windows, with franchise films ahead on medians by about 11 points. Bundle picks become Lord of the Rings, Back to the Future and Star Wars (all years), and Lord of the Rings, The Avengers and Ice Age (2000 onward). *The Good, the Bad and the Ugly* tops the standalones.

### Alternative B: Audience rating only

- **How it would work:** Rank on rating alone.
- **Why it is attractive:** It is closest to "viewers like it", and not exposed to box-office doubts.
- **Why rejected:** It ignores how many people care about a film: a niche classic and a mass hit can share a rating. It is the most favourable measure for standalones, which this list over-samples from acclaimed classics.
- **What the recommendation looks like under it:** Standalone, decisively, in both windows (gap about −40 points). Bundles become Lord of the Rings, The Godfather and The Dark Knight (all years). *The Shawshank Redemption* tops the standalones.

### Alternative C: Audience measures only (rating and reach, no box office)

- **How it would work:** Average the quality and reach ranks only.
- **Why it is attractive:** It answers Finance's objection completely.
- **Why rejected:** Narrowly. It discards the only measure tied to money, which the board will ask about. I kept it as the robustness test instead: every standalone pick must be top-half on these two measures (ADR-010).
- **What the recommendation looks like under it:** Standalone, decisively, in **both** windows (−20.8 all years; −23.2 from 2000 onward, range −37.7 to −8.5). This shows that the "too close to call" verdict for 2000 onward comes entirely from box office.

### Alternative D: Profit or revenue in dollars

- **How it would work:** Rank on revenue minus budget, or on revenue alone.
- **Why it is attractive:** Big numbers that the board recognises.
- **Why rejected:** It favours the most expensive recent films and mostly measures size, not value per licensing dollar. It also needs inflation adjustment across 1966–2019, using external price data that I could not verify (ADR-008).

## Consequences

- **What this buys:** One number per title on a common 0–100 scale. A single outlier cannot dominate it, because ranks cap at 100. It balances what viewers think against what the market paid.
- **What this costs:** Equal weights are a judgement, not a fact. The score is relative: a 60 means "better than 60% of *this list*", not an absolute standard.
- **What it costs the client if I am wrong:** If cinema box office is in fact what drives streaming value, the franchise side is undervalued here, and the honest verdict is "too close to call" in both windows (Alternative A). Lord of the Rings stays the top bundle under every alternative, and four of the five standalone picks survive Alternative A.
- **What would make me revisit this:** StreamVault's own viewing data. A few quarters of hours watched per licensed title would let the weights be fitted instead of chosen.

## What this survives

Any list size: percentile ranks are a vectorised binary search, and they rescale automatically to whatever the list contains. `analysis.run(components=...)` reruns the analysis under any alternative, and `src/sensitivity.py` reruns all of them.
