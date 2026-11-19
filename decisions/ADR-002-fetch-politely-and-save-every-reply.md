# ADR-002: Fetch at most 10 requests a second, retry politely, and save every reply to disk the moment it arrives

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Analyst, StreamVault licensing review

## Context

All data comes live from TMDb, a free API shared by many users. The rubric rewards pulling the full list "without crashing or losing track of anything, without abusing a shared API". Adjoa will rerun this every quarter on her laptop, sometimes on poor connections, and next year's list will be about four times larger.

## Decision

The script waits at least 0.1 s between requests, so it never exceeds about 10 per second. When TMDb replies "429 Too Many Requests" it waits as long as TMDb asks. Server errors and network errors are retried up to 5 times with growing waits. A rejected key stops the run immediately with a clear message. Every successful reply, and every "404 not found", is written to `data/raw/` atomically: a temporary file is written and then renamed. A rerun reuses what is on disk and asks TMDb only for what is missing. Details and credits are fetched as the two separate requests the brief names.

## Alternatives considered

### Alternative A: Fire requests in parallel, as fast as possible

- **How it would work:** A pool of 20–40 concurrent requests.
- **Why it is attractive:** A cold run would take seconds instead of about a minute.
- **Why rejected:** It is the "abuse" the rubric names, and it invites 429 responses that slow the run down anyway. Speed is not a problem in practice: the saved-data rerun Adjoa uses in meetings takes 2.2 s (see ADR-013).

### Alternative B: One request per film using `append_to_response=credits`

- **How it would work:** TMDb can return the details and the credits in a single reply.
- **Why it is attractive:** Half the requests: 117 instead of 234.
- **Why rejected:** The brief names the two endpoints explicitly. Keeping them separate also means a failed credits request does not force the details to be fetched again. The cost is 117 extra small requests per run, about 12 s, which stays within the politeness limit. This is the first thing to switch if the list grows past a few thousand titles.

### Alternative C: No saving; fetch everything each run

- **How it would work:** Keep replies in memory only.
- **Why it is attractive:** Always fresh data, with no files to manage.
- **Why rejected:** A crash at film 400 of 500 would mean starting over. Every rerun would load the shared API again. Results would also drift between runs, because TMDb's community edits ratings, so the board pack could not be reproduced.

## Consequences

- **What this buys:** Cold run: 235 requests in 56.6 s with no failures. Warm rerun: 0 requests in 0.3 s. A crash costs only the reply in flight.
- **What this costs:** Disk space (9.5 MB), and saved data that goes stale until someone deliberately runs `--refresh`.
- **What it costs the client if I am wrong:** If TMDb corrected a figure after the snapshot (2026-11-19), the analysis will not see the correction until a refresh. The saved-data reruns will still agree with each other.
- **What would make me revisit this:** TMDb publishing a stricter rate limit, or the list growing past about 5,000 titles. At that point, use Alternative B and modest concurrency within the published limit.

## What this survives

A 500-title list: about 1,320 requests, projected at around 5 minutes cold (`reports/runtime_report.md`), resumable after a crash or a lost connection. It also survives a missing API key: the run works from saved data and says so (see ADR-003).
