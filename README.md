# StreamVault Licensing Analysis: franchise bundles vs standalone hits

**Author:** Esther Efua Acquandoh

Kwame Boateng (VP Content Acquisition) has $14M to commit at the board's licensing review. This project pulls every candidate title from the public TMDb API, diagnoses the data, and answers his question in two time windows: all years, and 2000 onward.

**Answer in one line:** make standalone hits the default and buy only bundles where every film holds up. The top pick is *The Lord of the Rings*. **The verdict changes between windows:** standalones are clearly stronger across all years, but for 2000 onward the result is too close to call.

## Deliverables

| Deliverable (brief) | File | Rubric criterion |
|---|---|---|
| Data diagnosis: problems ranked by risk, full account of the list | [data_findings.md](data_findings.md) | Analyze |
| Working analysis: runs top to bottom, both windows | [notebooks/analysis.ipynb](notebooks/analysis.ipynb) (and [src/run_all.py](src/run_all.py)) | Apply / Create |
| Acquisition: every id accounted for, polite to the API | [src/fetch.py](src/fetch.py) → `data/processed/id_audit.csv` | Apply |
| Run time, measured against the time budget | [reports/runtime_report.md](reports/runtime_report.md) | Apply / Create |
| Decision notes: every judgement call, alternatives rerun, what survives next year | [decisions/](decisions/README.md) (13 ADRs plus index) | Evaluate |
| Client memo: one page, no jargon | [client_memo.md](client_memo.md) | Evaluate / Create |
| One improvement beyond the brief, built | [improvement.md](improvement.md) + [src/health_check.py](src/health_check.py) | Evaluate / Create |

## Quick start (Windows)

Needs Python 3.11 or newer; tested on 3.15.2. Run these from the project folder.

```bash
python -m venv .venv
```

```bash
.venv\Scripts\python -m pip install -r requirements.txt
```

```bash
.venv\Scripts\python src\run_all.py
```

That's all you need. The rerun uses the saved data snapshot in `data/raw/`, so **no API key is needed**, and it reproduces every result exactly in about 2 seconds.

To open the notebook, open the folder in VS Code, open `notebooks/analysis.ipynb`, choose the `.venv` interpreter as the kernel, and click **Run All**.

On macOS or Linux, use `.venv/bin/python` instead of `.venv\Scripts\python`.

### Fresh data from TMDb (optional)

1. Get a free API key at <https://www.themoviedb.org/settings/api>.
2. Copy `.env.example` to `.env` and put the key after `TMDB_API_KEY=`. `.env` is never committed.
3. Run:

```bash
.venv\Scripts\python src\run_all.py --refresh
```

Fresh data moves some figures slightly, because TMDb's community edits ratings (finding F-11). The written documents quote the snapshot from **2026-11-19**.

## How it works

```
data/id_list.csv ──► src/fetch.py ──► data/raw/            (saved TMDb replies: details, credits, series)
                          │
                          └──────────► data/processed/id_audit.csv   (fate of every input row)
data/raw/ ──► src/build_tables.py ──► data/processed/films.csv, film_people.csv, collections.csv
                                      (nested JSON → one fact per row; joins proven not to drop/duplicate)
          ──► src/diagnose.py ──────► outputs/diagnosis_*.csv        (problems found, and how much each moves the answer)
          ──► src/analysis.py ──────► outputs/*_{all_years,2000_onward}.csv  (comparison, bundles, shortlist, talent, deal note)
          ──► src/sensitivity.py ───► outputs/sensitivity.csv        (the answer under every rejected alternative)
src/run_all.py      runs fetch → build → diagnose → analyse, timing each stage (outputs/timings.csv)
src/health_check.py runs everything, then grades it RED/AMBER/GREEN and lists changes since the last accepted run
src/benchmark.py    measures run time at 112 and 560 films (outputs/benchmark.csv)
src/metrics.py      shared definitions (what counts as franchise, money floor, windows, resampling)
```

**Key design points** (each defended in [decisions/](decisions/README.md)):

- **Every row of the input gets exactly one fate.** The code stops if the fates don't add up to the number of input rows (ADR-001).
- **At most 10 requests a second,** with polite retries. Every reply is saved, so a rerun makes no network calls (ADR-002).
- **No loops over rows in the analysis.** It uses pandas grouping, NumPy matrix resampling, and binary-search percentiles (`searchsorted`). The resampling is 36× faster than a loop, measured.
- **Each title is scored 0–100** by averaging its percentile ranks on audience rating, audience reach and box-office multiple (ADR-005). Groups are compared with medians and a 95% resampling range, and a winner is named only at 95% agreement (ADR-006).

## Results at a glance

| | All years | 2000 onward |
|---|---|---|
| Films analysed (franchise / standalone) | 87 / 25 | 59 / 12 |
| Median title score (franchise / standalone) | 47 / 60 | 48 / 57 |
| Verdict | **Standalone** | **Too close to call** |
| Bundle picks | LOTR, Avengers, Harry Potter | LOTR, Avengers, Harry Potter |
| Standalone picks | Pulp Fiction, Forrest Gump, Spirited Away, Schindler's List, Inception | Spirited Away, Inception, Interstellar, Memento, WALL·E |

Candidate list: 127 rows → 112 films analysed (7 repeats, 5 unknown ids, 3 blank or junk rows; see [data_findings.md](data_findings.md)).

## Running next year's list (for Adjoa)

1. Save the new list as a CSV with the ids in the first column. TMDb ids and IMDb `tt…` ids both work.
2. Run the health check against the new list, downloading fresh data first:

```bash
.venv\Scripts\python src\health_check.py --refresh --ids path\to\new_list.csv
```

3. Read `reports/health_check.md`. **RED** means don't present. **AMBER** means say those items out loud. **GREEN** means safe. It also lists every change since the run Kwame last saw.
4. Once the run has been reviewed, make it the new reference:

```bash
.venv\Scripts\python src\health_check.py --accept --ids path\to\new_list.csv
```

5. Update the written documents. The CSVs regenerate on every run; the prose does not.

## Project layout

```
README.md            this file
client_memo.md       one-page memo to Kwame
data_findings.md     data diagnosis
improvement.md       the improvement beyond the brief
decisions/           13 decision records + index
reports/             runtime report, health check report, accepted reference run
notebooks/           analysis.ipynb (executed, with outputs)
src/                 all code
data/id_list.csv     the candidate list as given
data/raw/            saved TMDb replies (dated snapshot, committed on purpose: ADR-003)
data/processed/      flat tables built from data/raw
outputs/             every result table
requirements.txt     libraries (minimum versions); requirements-lock.txt has the exact tested versions
.env.example         where your own TMDb key goes (copy to .env)
```
