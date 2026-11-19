# Data findings — StreamVault (back-catalog licensing review)

## Summary

Of the 127 rows on the candidate list, **112 distinct films reached the analysis**. Seven rows were repeats of films already on the list, five pointed at films that do not exist, and three were not film ids at all. Every row is traced in `data/processed/id_audit.csv`.

Once loaded, the film data itself is clean: no missing release dates, no zero or placeholder budgets on the list, and no unreleased titles. The problems that matter are about **what the list contains and how a franchise is counted**, not typos in the numbers. Five findings could change or weaken Kwame's recommendation:

1. **Bundles are incomplete.** In 10 of the 23 franchises offered as bundles, the list holds only some of the released films. The later films left off are the weakest. If a studio sells the whole series, the franchise box-office lead shrinks from +0.53× to +0.08×, which is effectively zero.
2. **There are too few standalones to separate the two options on box office.** Only 25 standalones (12 from 2000 onward). The franchise-minus-standalone box-office gap has a 95% range that crosses zero in both windows. The **audience-rating gap does not cross zero**: standalones rate 0.72 points higher, and that result holds up.
3. **The list contains no flops.** Every one of the 112 films earned back its budget; the lowest is 1.13×. The data can rank hits against hits, but it cannot measure the downside risk that hurt Kwame's earlier trilogy deal.
4. **"Franchise" can be defined two ways, and the choice triples the gap.** Nine films belong to a series but are the only entry of that series on the list. Counting them as franchise films moves the box-office gap from +0.53× to +1.78×.
5. **Old films distort averages.** Using averages instead of medians reverses the all-years winner to standalones (10.48× vs 7.94×), driven by *Jaws* (67×) and *The Good, the Bad and the Ugly* (32×). From 2000 onward it does not reverse. Medians do not reverse in either window.

All figures are from a live snapshot taken 2026-11-19 (UTC). "Box-office multiple" means worldwide revenue ÷ production budget. "Rating" means TMDb's average audience score out of 10.

## Reconciliation

| Stage | Rows | Delta | Reason |
|---|---|---|---|
| Rows in `id_list.csv` (excluding header) | 127 | — | As given. A blank line is a row: pandas drops blank lines by default, which silently lost one row on the first run. Fixed with `skip_blank_lines=False`. |
| Not usable as an id | 124 | −3 | One blank line (row 69), `-1` (row 30), `N/A` (row 111) |
| IMDb id translated to a TMDb id | 124 | 0 | `tt0468569` (row 95) → TMDb 155, *The Dark Knight* |
| Repeat rows removed (first occurrence kept) | 117 | −7 | 7 rows covering 6 films. *The Dark Knight* appears 3 times (rows 2, 91, and 95 as the IMDb id). *The Matrix*, *The Shawshank Redemption*, *The Empire Strikes Back*, *Fight Club* and *Pulp Fiction* appear twice each. |
| Not found on TMDb (HTTP 404) | 112 | −5 | 8471293, 8471294, 9412887, 9412888, 7733901 |
| Details **and** credits fetched | 112 | 0 | No request failed. Both endpoints succeeded for every film. |
| Budget and revenue both credible (≥ $10,000) | 112 | 0 | No film on the list failed this check |
| **In the analysis: all years** | **112** | — | 87 franchise films in 23 bundles, plus 25 standalones |
| In the analysis: 2000 onward | 71 | −41 | 28 franchise and 13 standalone films released before 2000. They are held out of this window, not lost. |

Extra data fetched to test findings (not part of the candidate count): 32 franchise records, and 39 released franchise films that are **not** on the list (`data/processed/films_off_list.csv`).

## Findings, ranked by risk

### F-01: Bundles on the list are missing their own later films — Severity: High

- **What it is:** The brief says studios sell franchises as all-or-nothing bundles. For 10 of the 23 franchises offered as bundles, the list holds only part of what has been released: Star Wars 6/9, Jurassic Park 3/7, Mission: Impossible 5/8, Ice Age 3/6, Terminator 4/6, Bourne 3/5, Indiana Jones 4/5, Die Hard 4/5, Matrix 3/4, Toy Story 4/5. In every case the missing films are the most recent ones, and they are the weakest commercially. Examples: *The Matrix Resurrections* 0.82× (lost money), *Indiana Jones and the Dial of Destiny* 1.30×, *Terminator: Dark Fate* 1.41×, *Mission: Impossible – The Final Reckoning* 1.50×, *Jurassic World Dominion* 1.52×.
- **How I detected it:** I fetched each franchise's full film list (`GET /collection/{id}`), counted the released entries, and compared that with the entries on the list (`collections.csv`). I then fetched the details of the off-list films and recomputed each bundle's figures (`outputs/bundle_completeness.csv`).
- **Scale:** 10 of 23 bundles; 20 released films with credible figures are missing from those bundles.
- **Effect on the client's number:** The franchise box-office lead over standalones falls from **+0.53× to +0.08×** (all years) and from **+0.56× to +0.10×** (2000 onward). In other words, it disappears. Individual bundles fall much further: Star Wars drops from 10.83× to 6.17×, Jurassic Park from 8.93× to 4.97×, and Indiana Jones from 7.11× to 4.13×. Franchise ratings fall too, so the rating gap widens from −0.72 to −0.82.
- **What I did about it:** The baseline uses the films on the list, because that is what was quoted. Every bundle is also scored on its whole released series, and the shortlist will rank on the more cautious of the two figures.
- **Residual risk:** I cannot see what each studio's bundle actually contains. If a bundle includes unreleased future films, nothing here can score them.

### F-02: Too few standalones to separate the two options on box office — Severity: High

- **What it is:** There are 25 standalones in total and 12 from 2000 onward, compared with 87 and 59 franchise films. With so few standalones, one or two films move the median.
- **How I detected it:** Group counts, then 10,000 resamples of each group (vectorised bootstrap, `metrics.bootstrap_gap`) to get a 95% range for the franchise-minus-standalone gap.
- **Scale:** Box-office gap, 95% range: −6.29× to +3.08× (all years) and −0.58× to +2.44× (2000 onward). Franchises come out ahead in about 82% of resamples. Rating gap, 95% range: −0.99 to −0.43 (all years) and −0.96 to −0.34 (2000 onward). Franchises come out ahead in **none** of the resamples.
- **Effect on the client's number:** The box-office comparison is **not decisive** in either window. The audience-rating comparison **is decisive**: standalones rate higher, and that holds in both windows.
- **What I did about it:** I report the ranges alongside every gap, and I base the recommendation on the evidence that holds up (ratings and per-bundle weak-film analysis) rather than on a box-office difference that is mostly noise.
- **Residual risk:** If next year's list adds more standalones, the box-office comparison may become decisive in either direction. Rerunning the analysis will show this.

### F-03: The list contains no flops — Severity: High

- **What it is:** All 112 films earned back their budget. The lowest is *The Shawshank Redemption* at 1.13×, the lowest rating is *The Smurfs* at 5.75, and the fewest audience votes on any film is 4,137. This is a list of well-known successes.
- **How I detected it:** Distribution checks in `outputs/diagnosis_checks.csv`, showing 0 films with a multiple below 1.
- **Scale:** 0 of 112 films lost money. By contrast, 1 of the 39 off-list franchise films with credible figures lost money, and several others were close to breaking even.
- **Effect on the client's number:** The comparison shows which kind of hit is stronger. It cannot show which kind of purchase is safer, and safety is the question behind Kwame's underperforming trilogy. Any risk statement has to come from the weakest film inside each bundle, not from the group averages.
- **What I did about it:** The analysis judges each bundle by its weakest film as well as its overall figure, and the memo states this limit plainly.
- **Residual risk:** Unmeasurable from this data. The real failure rate of back-catalog purchases is unknown.

### F-04: Nine films sit in a series but are the only entry of it on the list — Severity: High

- **What it is:** TMDb marks *Jaws*, *The Lion King*, *The Silence of the Lambs*, *Ghostbusters*, *The Incredibles*, *Monsters, Inc.*, *Mad Max: Fury Road*, *Blade Runner* and *The Smurfs* as part of a series. However, none of their sequels are on the list, so none of them is offered as a bundle.
- **How I detected it:** Compared each film's series id with the number of films from that series on the list.
- **Scale:** 9 of 112 films. That is 36% of the standalone group under my definition.
- **Effect on the client's number:** If they count as franchise films, standalones shrink from 25 to 16 (and to 8 from 2000 onward). The box-office gap moves from +0.53× to **+1.78×** (all years) and from +0.56× to +1.21× (2000 onward). Standalones still lead on ratings either way (−0.84, −0.74).
- **What I did about it:** I count a film as a franchise film only when two or more films from its series are on the list, because that is what is actually being sold as a bundle. The alternative definition is reported side by side.
- **Residual risk:** If a studio would only sell one of these films together with its sequels, it belongs in the franchise group, and the franchise box-office case would look stronger.

### F-05: Pre-2000 films carry extreme multiples that distort averages — Severity: Medium

- **What it is:** Median multiples fall steadily by decade: 1970s 40.8×, 1980s 9.9×, 1990s 5.9×, 2000s 5.0×, 2010s 4.6×. Old films had small budgets, and their revenue counts every later re-release (for example the re-releases of *Star Wars*, *Jaws* and *The Lion King*). General inflation is **not** the problem here, because revenue and budget are divided by each other.
- **How I detected it:** Compared averages with medians, and broke the multiple down by decade.
- **Scale:** 41 of 112 films are from before 2000.
- **Effect on the client's number:** On **averages**, the all-years winner reverses to standalones (10.48× vs 7.94×), and in the 2000-onward window it is franchises (5.45× vs 4.89×). **The answer changes between windows if averages are used.** On medians, franchises edge ahead in both windows, but within the noise described in F-02.
- **What I did about it:** I used medians throughout, and reported both windows on everything.
- **Residual risk:** Finance's doubt about pre-2000 revenue figures is partly justified. Re-release income is included, and it cannot be separated out from this source.

### F-06: Talent records are mostly franchise records in disguise — Severity: Medium (affects the talent read, not the bundle-versus-standalone choice)

- **What it is:** Of the 57 directors and lead actors with three or more films on the list, 39 made **all** of them in a single franchise. For example, Daniel Radcliffe has 8 films, all *Harry Potter*.
- **How I detected it:** For each person, counted their films and the number of distinct series those films belong to.
- **Scale:** 39 of 57 frequent names (68%).
- **Effect on the client's number:** A simple "most films, best average" ranking would hand Kwame's negotiators a list of franchise casts and present it as a talent signal.
- **What I did about it:** In the talent analysis, each series counts once, and a person needs results across two or more separate series or standalones to qualify.
- **Residual risk:** After that filter, very few names qualify, so the talent read will be thin.

### F-07: Repeated rows, including one hidden in another site's format — Severity: Medium

- **What it is:** Seven extra rows covering six films. *The Dark Knight* appears three times; one of those is its IMDb id (`tt0468569`) rather than its TMDb id.
- **How I detected it:** Checked for repeated ids after translating the IMDb id through TMDb's `/find` lookup.
- **Scale:** 7 of 127 rows (5.5%).
- **Effect on the client's number:** Left in, the repeats shift the standalone median from 5.00× to 4.76× and widen the franchise box-office lead from +0.53× to +0.76× (all years). They would also triple *The Dark Knight*'s weight in the director and actor figures.
- **What I did about it:** Kept the first appearance of each film and recorded every repeat in `id_audit.csv`.
- **Residual risk:** Low. Without a column naming the source, I cannot tell which of the three source lists the repeats came from.

### F-08: Eight rows cannot be evaluated at all — Severity: Medium

- **What it is:** Five ids do not exist on TMDb, and the other three rows are a blank, `-1` and `N/A`.
- **How I detected it:** HTTP 404 responses and row classification (`id_audit.csv`).
- **Scale:** 8 of 127 rows (6.3%).
- **Effect on the client's number:** Unknown. These may be real candidates whose ids were typed wrongly. If most were standalones, they would add up to 32% to the smallest group.
- **What I did about it:** Excluded them, with each row number recorded so the list's owners can correct the source.
- **Residual risk:** Up to eight possible titles have not been evaluated.

### F-09: Unreported money shown as zeros or junk figures — Severity: Low today, High next year

- **What it is:** None of the films on the list have this problem. However, 3 of the 39 off-list franchise films do: *The Lion King II* (0/0), *Buck Wild* (0/0), and *The Lion King 1½* with "revenue" of **$1,465**. On TMDb, 0 means "not reported", not a real zero.
- **How I detected it:** Applied a credibility floor of $10,000 to budget and revenue.
- **Scale:** 0 of 112 films on the list; 3 of 39 off-list films.
- **Effect on the client's number:** None today. If left unguarded, $1,465 ÷ $0 produces an infinite multiple that would top every ranking. A 500-title list will contain many more such films.
- **What I did about it:** Figures below $10,000 are treated as unreported, and the multiple is left blank for that film (`metrics.MIN_CREDIBLE_DOLLARS`).
- **Residual risk:** A wrong figure above $10,000 would still pass this check.

### F-10: Round-number revenue figures are estimates — Severity: Low

- **What it is:** Four films report revenue as an exact round million: *Monsters, Inc.*, *Star Wars: Episode III*, *Terminator 3* and *Alien Resurrection*.
- **How I detected it:** Checked for revenue values that divide exactly by 1,000,000.
- **Scale:** 4 of 112 films.
- **Effect on the client's number:** Negligible. These are estimates, not errors.
- **What I did about it:** Kept them and flagged them.
- **Residual risk:** Low.

### F-11: The source changes between runs — Severity: Low

- **What it is:** Ratings, vote counts and sometimes revenue on TMDb are edited by its community over time.
- **How I detected it:** By design: every saved response records when it was fetched.
- **Scale:** All films.
- **Effect on the client's number:** A rerun next quarter may differ slightly, so figures will not match the board pack to the decimal.
- **What I did about it:** Saved responses are reused unless `--refresh` is passed, and every output states its snapshot date.
- **Residual risk:** Low.

## Looked wrong, is not wrong

| Apparent problem | Why it looks wrong | Why it is actually fine |
|---|---|---|
| `tt0468569` in a list of numbers | Not a number | It is a valid IMDb id for *The Dark Knight*. TMDb translated it, and it turned out to be a repeat. |
| *The Shawshank Redemption*: $28.3M revenue on a $25M budget | A famous film with weak figures | It genuinely flopped in cinemas and found its audience later. |
| *Pirates of the Caribbean: On Stranger Tides* budget $379M | Implausibly high | It is the widely reported figure for one of the most expensive films ever made. |
| *Avengers: Endgame* revenue $2.94B | Implausibly high | It is a genuine record-level worldwide gross. |
| Nine films with 2–3 directors | Looks like duplicated credits | They are real co-directors (e.g. the Wachowskis, the Russo brothers). Each director is credited. |
| Franchises with more entries on TMDb than released (Avengers 6 vs 4, Ice Age 7 vs 6, Shrek 5 vs 4, Jurassic Park 8 vs 7) | Looks like missing films | The extra entries are announced but unreleased. Only films released by the snapshot date are counted. |
| Very small budgets for old films (e.g. $1.2M for *The Good, the Bad and the Ugly*) | Looks like a missing digit | That was the real cost at the time. Because revenue is divided by budget, inflation largely cancels out. |
| *Mad Max* (1979), off-list: 286× multiple | Looks like an error | It is a famously cheap film that became a hit. Medians stop it from distorting results. |
| Two non-English films (*Spirited Away*, *The Good, the Bad and the Ugly*) | Might look out of place | They are legitimate candidates, with worldwide figures reported in dollars. |

## Could not verify

- **Whether box office predicts streaming viewing.** This source has no streaming data. Box office and audience ratings are used as stand-ins for how much a title will be watched.
- **Licence prices and bundle terms.** Neither the price of each bundle nor exactly which films it includes is known (see F-01).
- **What "revenue" contains.** I believe it is lifetime worldwide cinema gross including re-releases, but I could not confirm this per film. Home video and television income are not included.
- **What "budget" contains.** It is the production cost reported publicly. Marketing spend is usually excluded and is not available here.
- **Which of the three source lists each row came from.** The list has no source column, so errors cannot be traced back to Adjoa's tracker, the inherited spreadsheet or the studio email.
- **The intended titles behind the 8 rows that could not be used** (F-08).
- **Individual figures**, e.g. *Spirited Away* at $274.9M. Some public sources report a different total; I cannot settle this from TMDb alone.
