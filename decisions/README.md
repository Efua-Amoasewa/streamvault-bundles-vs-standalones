# Decision notes

Only the judgement calls that can change Kwame's answer get a full record: six ADRs in the house format. Each states what I assumed, why, what the real alternatives were, **what the recommendation looks like under them** (rerun, not guessed: `src/sensitivity.py` → `outputs/sensitivity.csv`), and what it costs Kwame if I am wrong.

## Index

| ADR | Decision | If I am wrong, it costs Kwame… |
|---|---|---|
| [001](ADR-001-franchise-means-a-bundle-on-the-list.md) | Franchise = 2+ films of a series on the list | Nothing to the verdict; the box-office gap would triple |
| [002](ADR-002-title-score-from-three-ranked-measures.md) | Title score = average rank on rating, reach, box office | If box office alone matters: "too close to call" in both windows |
| [003](ADR-003-medians-and-a-95-percent-rule.md) | Medians, a 95% range, and a winner only at 95% agreement | Under-commitment to standalones after 2000 (they lead in 93% of resamples) |
| [004](ADR-004-the-2000-onward-window.md) | Window by release year, re-ranked within it, no inflation adjustment | Re-release income inside some modern totals |
| [005](ADR-005-judge-bundles-cautiously.md) | Bundle = mean of all films, judged on the whole series if weaker | Star Wars ranked 8th instead of 4th |
| [006](ADR-006-how-the-shortlist-is-picked.md) | One-off standalones only, audience floor, modern substitutes named | Three pre-2000 picks to defend to Finance |

## Smaller choices (not written up as ADRs)

These are routine and do not move the recommendation. Each is a named setting in the code.

- **Row accounting:** every input row gets one fate in `data/processed/id_audit.csv`; the first copy of a repeat is kept; IMDb ids are translated (`src/fetch.py`).
- **Polite fetching:** at most 10 requests a second, retries on errors, every reply saved to `data/raw/` so reruns need no network.
- **Data snapshot:** the 2026-11-19 replies are committed, so results reproduce exactly without an API key.
- **Missing money:** budget or revenue under $10,000 is treated as not reported, not as zero (`metrics.py`).
- **Talent read:** directors and top 3 billed actors; each franchise counts once per person; at least 2 separate results to be named.
- **Deal note:** price stated per film as a multiple of a typical standalone, because no real prices were available.
- **Run-time budget:** 60 seconds for a live rerun; measured at 3.1 s median for 560 films (`reports/runtime_report.md`).

## What the recommendation looks like under every alternative

| Scenario | All years | 2000 onward | Top bundle | Bundle picks (all years) |
|---|---|---|---|---|
| **As decided** | **Standalone** | **Too close to call** | **Lord of the Rings** | **LOTR, Avengers, Harry Potter** |
| Franchise = any series (ADR-001) | Standalone | Too close to call | Lord of the Rings | Same |
| Box office only (ADR-002) | Too close to call | Too close to call | Lord of the Rings | LOTR, Back to the Future, Star Wars |
| Rating only (ADR-002) | Standalone | Standalone | Lord of the Rings | LOTR, Godfather, Dark Knight |
| Audience measures only (ADR-002) | Standalone | Standalone | Lord of the Rings | LOTR, Avengers, Dark Knight |
| Averages instead of medians (ADR-003) | Standalone | Too close to call | Lord of the Rings | Same |
| Bundles judged on films offered (ADR-005) | Standalone | Too close to call | Lord of the Rings | Same |
| Series films allowed as standalones (ADR-006) | Standalone | Too close to call | Lord of the Rings | Same |

**What survives every alternative:** franchises never win outright; Lord of the Rings is always the strongest bundle; and *Spirited Away* is a standalone pick in 15 of the 16 scenario-and-window combinations. **What depends on judgement:** whether the post-2000 answer is "standalone" or "too close to call". That turns entirely on how much weight box office gets (ADR-002).

## What survives when Adjoa reruns this next year against ~500 titles, without me

**Survives unchanged:**
- **The whole pipeline, with one command:** `.venv\Scripts\python src\run_all.py --refresh --ids <new list>.csv`. Nothing in the code assumes 127 rows, these films or these franchises.
- **Row accounting:** every row of the new list gets a fate in `id_audit.csv`, and the run stops if the totals don't reconcile.
- **Data guards:** blank lines, junk ids, IMDb ids, repeats, unknown ids, $0 or junk money, and unreleased series entries are all handled by rule, not by hand.
- **Join checks:** each one stops the run if a film is dropped or duplicated.
- **Speed:** measured at 560 films, 3.1 s median and 29.3 s worst (see `reports/runtime_report.md`).
- **Old saved data cannot leak into a new list:** only the replies for the films on the current list are read (tested with a changed list; see `improvement.md`).
- **A pre-meeting health check** (`src/health_check.py`) says, in red, amber or green, whether a rerun can be trusted and what changed since the run Kwame last saw.
- **Both windows, the verdict rule and the loud flag:** computed and printed automatically.

**Survives but needs a human eye:**
- **The diagnosis.** `src/diagnose.py` recounts every known problem automatically (`outputs/diagnosis_checks.csv`). A *new kind* of problem needs a person to spot it and add a check. Read the "Checks" table each quarter before trusting the verdict.
- **The written documents.** `data_findings.md`, the memo and the reasons quote this year's numbers. The CSVs regenerate; the prose does not.

**Will change, by design:**
- **Scores are relative to the list.** A title's score depends on what else is on the list, so a film can move between years without changing itself.
- **The verdicts may firm up.** More standalones narrow the 95% ranges, so "too close to call" may become a clear answer in either direction. The rule does this without anyone touching the code.
- **Fresh data moves figures slightly** (TMDb edits). Keep each quarter's snapshot if figures must be reproduced later.

**Does not survive, and should not be trusted blindly:**
- **The settings tuned to this list:** the $10,000 floor, the audience floor of 50, top 3 billed actors, and at least 2 talent results. All are named constants at the top of `src/metrics.py` and `src/analysis.py`, each is explained above (the audience floor in ADR-006, the rest under "Smaller choices"); revisit them when the list changes size or shape.
