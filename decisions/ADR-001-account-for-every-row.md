# ADR-001: Account for every row of the candidate list, keep the first copy of a repeated film, and translate ids written in another site's format

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decision owner:** Esther Efua Acquandoh

## Context

`id_list.csv` has 127 rows, merged from three sources over four years. It contains a blank line, `-1`, `N/A`, five ids that TMDb does not know, six films listed more than once, and `tt0468569`, which is an IMDb id rather than a TMDb id. The rubric asks that every id is accounted for and that totals reconcile with the list as given. Each of these rows needs a stated fate, not a silent drop.

## Decision

I read the file as text, including blank lines, and give every row exactly one fate. IMDb-style ids are translated through TMDb's `/find` lookup. When a film appears more than once, I keep its first appearance and record the others as `duplicate`. Rows that cannot be used are kept in `id_audit.csv` with their row number and reason, and the code checks that the fates add up to the number of input rows.

## Alternatives considered

### Alternative A: Read the file as numbers and let the tools drop what they can't parse

- **How it would work:** `pd.read_csv` with default settings, then cast to integer.
- **Why it is attractive:** One line of code.
- **Why rejected:** The defaults silently dropped the blank line (126 rows instead of 127), and they turn `N/A` into a missing value with no trace. The totals would not reconcile, which is exactly what the rubric checks.

### Alternative B: Treat `tt0468569` as junk

- **How it would work:** Anything that is not a whole number gets the fate `not_an_id`.
- **Why it is attractive:** It is simple, and the row turns out to be a repeat anyway.
- **Why rejected:** It reaches the right count for the wrong reason. Next year's list may contain IMDb ids for films that are *not* already on it, and Alternative B would throw those candidates away.

### Alternative C: Keep repeats, as a sign that more than one source liked the film

- **How it would work:** Count each row, so *The Dark Knight* has three times the weight.
- **Why it is attractive:** Appearing in several sources could reflect internal interest.
- **Why rejected:** The brief asks about the films, not the sources' votes. Keeping repeats changes the standalone box-office median from 5.00× to 4.76×, widens the franchise lead from +0.53× to +0.76× (all years), and triples one film's weight in the talent read.

## Consequences

- **What this buys:** 127 rows in, 127 fates out, checked by the code itself (`fetch.py` stops if they disagree). Every excluded row can be traced back by row number.
- **What this costs:** Nothing measurable. The five unknown ids and three junk rows can't be analysed under any approach.
- **What it costs the client if I am wrong:** If a repeat was meant to be a *different* film (for example a remake typed with the wrong id), one candidate goes unevaluated. Six films are affected, and each one's row numbers are listed.
- **What would make me revisit this:** A source column added to the list. Repeats could then be traced to the spreadsheet that caused them.

## What this survives

A 500-title list in any mix of TMDb ids, IMDb ids, blanks and junk. The rules are pattern-based and vectorised, and nothing assumes 127 rows. Adjoa gets an `id_audit.csv` that shows her exactly which rows to send back to their owners.
