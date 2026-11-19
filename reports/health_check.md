# Pre-meeting health check: 🟠 AMBER

**Safe to present, but say the amber items out loud.**

Run at 2026-11-19T13:49:12+00:00 UTC.

| Check | Status | Finding | What to do |
|---|---|---|---|
| Every row accounted for | 🟢 GREEN | 127 rows in, 127 with a fate | Stop: do not present. Run src/fetch.py on its own and read its output. |
| Downloads completed | 🟢 GREEN | 0 requests failed | None. |
| Rows that cannot be assessed | 🟠 AMBER | 6.3% of rows (8) | Send the row numbers in data/processed/id_audit.csv back to the list's owners; say the count in the room. |
| Repeated rows | 🟠 AMBER | 7 repeat rows removed | Mention it; ask the list's owners to de-duplicate their sources. |
| Films without credible money figures | 🟢 GREEN | 0.0% of films scored on audience measures only | If AMBER/RED, say the cinema-takings comparison rests on fewer films. |
| Standalones from 2000 onward (sample size) | 🟠 AMBER | 12 standalones | Present the 2000-onward verdict as provisional; it can flip on a few films. |
| Bundles missing released films | 🟠 AMBER | 43% of 23 bundles | Ask each studio exactly which films its bundle includes before pricing it. |
| Age of the data | 🟢 GREEN | oldest figure fetched 0 days ago | Refresh before a board meeting: src/run_all.py --refresh (needs the key). |
| Answer the same in both periods | 🟠 AMBER | all years: standalone; 2000 onward: too close to call | Say it out loud, first: the brief requires it. |
| Changes since accepted run (all years) | 🟢 GREEN | nothing material changed since 2026-11-19 | None. |
| Changes since accepted run (2000 onward) | 🟢 GREEN | nothing material changed since 2026-11-19 | None. |

## What Kwame would hear

- **all years:** verdict *standalone*; bundles The Lord of the Rings, The Avengers, Harry Potter; standalones Pulp Fiction, Forrest Gump, Spirited Away, Schindler's List, Inception; strongest bundle worth 1.44× a typical standalone per film, weakest film outranks 94% of the list.
- **2000 onward:** verdict *too close to call*; bundles The Lord of the Rings, The Avengers, Harry Potter; standalones Spirited Away, Inception, Interstellar, Memento, WALL·E; strongest bundle worth 1.63× a typical standalone per film, weakest film outranks 96% of the list.
