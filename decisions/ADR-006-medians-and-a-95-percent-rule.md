# ADR-006: Compare groups with medians, show a 95% range from resampling, and call a winner only when 95% of resamples agree

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Esther Efua Acquandoh

## Context

There are only 25 standalones (12 from 2000 onward) against 87 franchise films (59). A few old films have extreme box-office multiples: *Jaws* 67×, *The Good, the Bad and the Ugly* 32×. Kwame needs to know whether a difference is real or one film's luck, because his last instinct-driven bundle is what the board remembers.

## Decision

Each group is summarised by its **median**. The franchise-minus-standalone gap gets a 95% range from 10,000 resamples, done as a single matrix calculation with no loop. The verdict names a winner only when that side is ahead in at least 95% of resamples. Otherwise it reads "too close to call". The random seed is fixed (7), so reruns give identical ranges.

## Alternatives considered

### Alternative A: Averages

- **How it would work:** Use the mean score per group.
- **Why it is attractive:** Familiar, and every film counts in proportion to its score.
- **Why rejected:** On raw box-office multiples, averages **reverse the all-years winner** to standalones (10.48× vs 7.94×), driven by two pre-1980 films. Because title scores are ranks capped at 100, averages of title scores are safer. The median is still the honest "typical film".
- **What the recommendation looks like under it:** Unchanged on title scores: standalone for all years (−13.1, range −21.9 to −4.3), too close to call from 2000 onward (−9.0, range −20.6 to +3.2). Same picks.

### Alternative B: A formal significance test (e.g. Mann-Whitney) with p < 0.05

- **How it would work:** Report a p-value per comparison.
- **Why it is attractive:** A standard statistical procedure.
- **Why rejected:** A p-value does not tell Kwame *how big* the gap might be. The 95% range does ("standalones are between 0.3 and 27 points stronger"), and it reads naturally in a memo without jargon.

### Alternative C: No uncertainty; report the point gap

- **How it would work:** "Standalones score 12.9 points higher."
- **Why it is attractive:** Simple.
- **Why rejected:** From 2000 onward, the gap's range crosses zero. Presenting −8.9 as a finding would be overclaiming, which is exactly what Finance would catch in November.

## Consequences

- **What this buys:** The verdict changes between windows (standalone → too close to call), and the analysis shows that loudly instead of hiding it. The 95% rule is strict: with only 12 standalones, a real but modest edge can still read as too close to call.
- **What this costs:** The verdict is cautious when samples are small.
- **What it costs the client if I am wrong:** If standalones really are stronger from 2000 onward (they are ahead in 93% of resamples there, just short of the 95% bar, and in more than 99.9% on audience measures alone), Kwame under-commits to them in the modern window. The memo makes this risk explicit.
- **What would make me revisit this:** A larger standalone sample. Next year's 500 titles may settle the 2000-onward window either way.

## What this survives

Any list size. Resampling costs grow linearly: about 0.03 s per comparison at 112 films, measured. A bigger list narrows the ranges automatically, so the verdict will firm up without anyone changing the code.
