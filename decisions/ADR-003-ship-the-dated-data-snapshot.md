# ADR-003: Ship the dated snapshot of TMDb replies with the project, so the analysis reruns identically from a clean copy

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Analyst, StreamVault licensing review

## Context

The rubric requires the analysis to run "top to bottom from a clean clone, no manual edits". A clean copy contains no API key: keys are personal and must never be shared. TMDb data also changes over time, because ratings and vote counts are edited by its community. Without the snapshot, a reviewer either cannot run the analysis at all, or runs it and gets slightly different numbers from the ones in the memo.

## Decision

`data/raw/` (306 files, 9.5 MB, fetched 2026-11-19) is part of the project. All code runs from it without a key. Fresh data is a deliberate act: `src/fetch.py --refresh`, which needs a key in `.env`. The key file stays excluded from version control, and `.env.example` shows where a key goes.

## Alternatives considered

### Alternative A: Exclude downloaded data; every user fetches with their own key

- **How it would work:** `data/raw/` is ignored, and the first run downloads everything.
- **Why it is attractive:** A smaller project, and always current data.
- **Why rejected:** The analysis cannot run from a clean copy without a key, and results would drift away from the memo (finding F-11).

### Alternative B: Ship only the flattened tables (`films.csv` etc.), not the raw replies

- **How it would work:** Commit `data/processed/` instead.
- **Why it is attractive:** Smaller, at under 0.1 MB.
- **Why rejected:** The flattening step and its join checks, which are part of what is assessed, would then never run from a clean copy. Raw replies are the only real source of truth.

## Consequences

- **What this buys:** Byte-identical results on every rerun (verified: 23 of 23 result files identical). A reviewer needs no key, and the memo's figures can always be regenerated.
- **What this costs:** 9.5 MB in the project, and the data is fixed at 2026-11-19 until refreshed.
- **What it costs the client if I am wrong:** If a figure has been corrected since the snapshot, the memo carries the old one. A refresh and rerun would show it in about a minute.
- **What would make me revisit this:** TMDb's terms of use restricting redistribution of cached replies. In that case, ship only the processed tables plus a hash of the raw snapshot.

## What this survives

Adjoa's quarterly reruns. She refreshes when she wants new data, and every other run is reproducible. At 500 titles the snapshot grows to about 40 MB, which is still reasonable to keep with the project.
