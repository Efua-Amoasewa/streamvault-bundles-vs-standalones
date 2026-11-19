# ADR-013: Set the time budget at 60 seconds for a live rerun from saved data, with downloads done before meetings

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Esther Efua Acquandoh

## Context

The rubric assesses results computed "inside the client's time budget, measured", but the brief gives no number. It does say Adjoa reruns the analysis "on her own laptop, sometimes live in a meeting", and that next year's list will be about 500 titles.

## Decision

- **Live rerun from saved data:** under 60 seconds at about 500 titles, measured as a fresh process so Python start-up is included.
- **Fresh download:** done before the meeting. Target under 15 minutes at about 500 titles, within the politeness limits in ADR-002.

Measured results: 2.2 s median at 112 films; 3.1 s median and 29.3 s worst at 560 films; 56.6 s cold download for 117 ids; about 5.3 min projected cold for 500 (`reports/runtime_report.md`).

## Alternatives considered

### Alternative A: A 10-second budget

- **How it would work:** A tighter target.
- **Why it is attractive:** It feels instant in a meeting.
- **Why rejected:** It would be met today (2.2 s), but at 560 films the worst cold-disk run took 29.3 s. A target that fails on a first run is the wrong promise to make to Adjoa.

### Alternative B: Include the download in the live budget

- **How it would work:** Fetch fresh data during the meeting.
- **Why it is attractive:** Always-current numbers.
- **Why rejected:** It depends on meeting-room Wi-Fi and a shared API's speed, and fresh data moves the figures slightly (F-11). That is not something to discover in front of the board.

## Consequences

- **What this buys:** A promise with a wide margin: the worst measured case is half the budget.
- **What this costs:** Live answers come from the last snapshot, not from this minute's data.
- **What it costs the client if I am wrong:** If Adjoa's laptop is much slower, a rerun could take longer than a room will tolerate. The margin (worst 29.3 s against 60 s) covers a machine about twice as slow.
- **What would make me revisit this:** Lists of several thousand titles, or a request for live refresh in meetings.

## What this survives

Next year's 500 titles, measured. All analysis is vectorised (resampling is 36× faster than a loop), so time grows roughly in proportion to list size.
