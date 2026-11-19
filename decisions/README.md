# Decision notes

Every judgement call the brief left open, one record per decision, in the house ADR format. Each record states what I assumed, why, what the real alternatives were, **what the recommendation looks like under them** (rerun, not guessed: `src/sensitivity.py` → `outputs/sensitivity.csv`), and what it costs Kwame if I am wrong.

## Index

| ADR | Decision | If I am wrong, it costs Kwame… |
|---|---|---|
| [001](ADR-001-account-for-every-row.md) | Every row gets one fate; keep the first copy of a repeat; translate IMDb ids | At most 6 repeated films mis-merged; every row is traceable |
| [002](ADR-002-fetch-politely-and-save-every-reply.md) | ≤10 requests/s, polite retries, save every reply | Figures up to one snapshot old |
| [003](ADR-003-ship-the-dated-data-snapshot.md) | Ship the 2026-11-19 data snapshot | A later TMDb correction missing until refresh |
| [004](ADR-004-franchise-means-a-bundle-on-the-list.md) | Franchise = 2+ films of a series on the list | Nothing to the verdict; the box-office gap would triple |
| [005](ADR-005-title-score-from-three-ranked-measures.md) | Title score = average rank on rating, reach, box office | If box office alone matters: "too close to call" in both windows |
| [006](ADR-006-medians-and-a-95-percent-rule.md) | Medians, a 95% range, and a winner only at 95% agreement | Under-commitment to standalones after 2000 (they lead in 93% of resamples) |
| [007](ADR-007-unreported-money-is-missing-not-zero.md) | Money < $10,000 = not reported | Nothing today; one inflated title next year at worst |
| [008](ADR-008-the-2000-onward-window.md) | Window by release year, re-ranked within it, no inflation adjustment | Re-release income inside some modern totals |
| [009](ADR-009-judge-bundles-cautiously.md) | Bundle = mean of all films, judged on the whole series if weaker | Star Wars ranked 8th instead of 4th |
| [010](ADR-010-how-the-shortlist-is-picked.md) | One-off standalones only, audience floor, modern substitutes named | Three pre-2000 picks to defend to Finance |
| [011](ADR-011-talent-counts-each-franchise-once.md) | Directors and top 3 billed; each franchise counts once; 2+ results | A star's franchise pull understated |
| [012](ADR-012-price-relative-to-a-typical-standalone.md) | Deal price as a multiple of a typical standalone, per film | Ceiling too low or too high by the curve's error |
| [013](ADR-013-sixty-second-rerun-budget.md) | 60 s live rerun; downloads before meetings | A much slower laptop could strain a meeting |

## What the recommendation looks like under every alternative

| Scenario | All years | 2000 onward | Top bundle | Bundle picks (all years) |
|---|---|---|---|---|
| **As decided** | **Standalone** | **Too close to call** | **Lord of the Rings** | **LOTR, Avengers, Harry Potter** |
| Franchise = any series (ADR-004) | Standalone | Too close to call | Lord of the Rings | Same |
| Box office only (ADR-005) | Too close to call | Too close to call | Lord of the Rings | LOTR, Back to the Future, Star Wars |
| Rating only (ADR-005) | Standalone | Standalone | Lord of the Rings | LOTR, Godfather, Dark Knight |
| Audience measures only (ADR-005) | Standalone | Standalone | Lord of the Rings | LOTR, Avengers, Dark Knight |
| Averages instead of medians (ADR-006) | Standalone | Too close to call | Lord of the Rings | Same |
| Bundles judged on films offered (ADR-009) | Standalone | Too close to call | Lord of the Rings | Same |
| Series films allowed as standalones (ADR-010) | Standalone | Too close to call | Lord of the Rings | Same |

**What survives every alternative:** franchises never win outright; Lord of the Rings is always the strongest bundle; and *Spirited Away* is a standalone pick in 15 of the 16 scenario-and-window combinations. **What depends on judgement:** whether the post-2000 answer is "standalone" or "too close to call". That turns entirely on how much weight box office gets (ADR-005).

## What survives when Adjoa reruns this next year against ~500 titles, without me

**Survives unchanged:**
- **The whole pipeline, with one command:** `.venv\Scripts\python src\run_all.py --refresh --ids <new list>.csv`. Nothing in the code assumes 127 rows, these films or these franchises.
- **Row accounting:** every row of the new list gets a fate in `id_audit.csv`, and the run stops if the totals don't reconcile.
- **Data guards:** blank lines, junk ids, IMDb ids, repeats, unknown ids, $0 or junk money, and unreleased series entries are all handled by rule, not by hand.
- **Join checks:** each one stops the run if a film is dropped or duplicated.
- **Speed:** measured at 560 films, 3.1 s median and 29.3 s worst (ADR-013).
- **Old saved data cannot leak into a new list:** only the replies for the films on the current list are read (tested with a changed list; see `improvement.md`).
- **A pre-meeting health check** (`src/health_check.py`) says, in red, amber or green, whether a rerun can be trusted and what changed since the run Kwame last saw.
- **Both windows, the verdict rule and the loud flag:** computed and printed automatically.

**Survives but needs a human eye:**
- **The diagnosis.** `src/diagnose.py` recounts every known problem automatically (`outputs/diagnosis_checks.csv`). A *new kind* of problem needs a person to spot it and add a check. Read the "Checks" table each quarter before trusting the verdict.
- **The written documents.** `data_findings.md`, the memo and the reasons quote this year's numbers. The CSVs regenerate; the prose does not.

**Will change, by design:**
- **Scores are relative to the list.** A title's score depends on what else is on the list, so a film can move between years without changing itself.
- **The verdicts may firm up.** More standalones narrow the 95% ranges, so "too close to call" may become a clear answer in either direction. The rule does this without anyone touching the code.
- **Fresh data moves figures slightly** (TMDb edits). Keep each quarter's snapshot if figures must be reproduced later (ADR-003).

**Does not survive, and should not be trusted blindly:**
- **The settings tuned to this list:** the $10,000 floor, the audience floor of 50, top 3 billed actors, and at least 2 talent results. All are named constants at the top of `src/metrics.py` and `src/analysis.py`, and each has its ADR explaining when to revisit it.
