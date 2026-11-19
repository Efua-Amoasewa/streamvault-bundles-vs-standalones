# Run time report

## Target

The brief gives no number, so I set one (see the decision records): Adjoa reruns the analysis every quarter on her own laptop, **sometimes live in a meeting**.

- **Live rerun from saved data:** under **60 seconds** at 112 films, and still under 60 seconds at about 500 films. That is about as long as a room will wait.
- **First-time download of a new list:** done before the meeting, not in it. Target: under **15 minutes** for about 500 titles, while staying under 10 requests per second to the shared API.

## Method

- **Hardware / container spec:** Windows 11 Pro laptop, Intel Core i7-10510U (4 cores, 1.8 GHz base), 32 GB RAM, local SSD. Python 3.15.2, pandas 3.1.1, NumPy 2.5.5. No container.
- **What was timed, from which event to which event:**
  - *Scenario A (full rerun):* from launching `src/run_all.py` as a fresh process to the process exiting. This includes Python start-up, imports, reading 306 saved replies, building the tables with join checks, the diagnosis, the analysis for both windows, and writing all outputs.
  - *Scenario B (about 500 titles):* the saved replies copied 5 times with shifted ids, giving **560 films and 160 franchises**. Timed from the start of `build_tables.build_all` to the end of `analysis.run`: flattening, join checks, diagnosis and analysis for both windows.
  - *Acquisition:* wall time of `src/fetch.py`, cold (every reply downloaded) and warm (every reply reused).
  - *Notebook:* `notebooks/analysis.ipynb` start to end, timed by its own first and last cells.
- **Runs, warm or cold, and which figure is reported:** Scenarios A and B use 5 runs each; the median, 95th percentile and worst are reported. Scenario B's first run is cold: its 2,800 copied files are read from disk for the first time. Cold acquisition happened once, on the first real run. Repeating it only to time it would put needless load on a shared API, so the 500-title figure is a projection from that measured rate.
- **How to reproduce:** `.venv\Scripts\python src\benchmark.py` writes `outputs/benchmark.csv`. `.venv\Scripts\python src\run_all.py` writes `outputs/timings.csv`, the per-stage split.

## Results

| Scenario | Runs | Median | p95 | Worst | Target met? |
|---|---|---|---|---|---|
| A: full rerun from saved data, 112 films, fresh process | 5 | 2.17 s | 2.20 s | 2.20 s | Yes (target 60 s) |
| B: flatten + diagnose + analyse, 560 films | 5 | 3.13 s | 24.07 s | 29.30 s (first, cold-disk run) | Yes (target 60 s) |
| Notebook, top to bottom, 112 films | 1 | 2.75 s | — | — | Yes (target 60 s) |
| Acquisition, warm (all 305 replies reused) | 1 | 0.3 s | — | — | Yes |
| Acquisition, cold, 117 ids (235 requests) | 1 | 56.6 s | — | — | Yes |
| Acquisition, cold, projected for 500 titles (~1,320 requests at the measured 0.24 s each) | — | ~5.3 min | — | — | Yes (target 15 min) |

Per-stage split for one in-process rerun at 112 films (`outputs/timings.csv`): acquire 0.19 s, flatten and join checks 0.48 s, diagnosis 0.16 s, analysis for both windows 0.18 s, save 0.02 s. Total 1.02 s. The rest of Scenario A's 2.2 s is Python start-up and imports.

Figures were re-measured after one fix: the table builder now reads only the saved replies for the films on the current list, rather than every reply on disk (found by testing the pre-meeting health check on a changed list; see `improvement.md`). The first measurement, before the fix, was 2.80 s median (A) and 4.21 s median / 31.55 s worst (B).

## Before / after

| Query / stage | Before | After | Change |
|---|---|---|---|
| Resampling for the 95% range (10,000 draws): Python loop vs one NumPy matrix | 1.003 s per call | 0.028 s per call | 36× faster. With 8 calls per run, that saves about 8 s per rerun. |
| Percentile ranks for 3 measures × 112 films: loop over rows vs binary search (`searchsorted`) | 0.0044 s | 0.0005 s | 9× faster, and the gap grows with list size |
| Acquisition: download everything vs reuse saved replies | 56.6 s (235 requests) | 0.3 s (0 requests) | 190× faster, with no load on the API |
| Blank-line handling when reading the list | 126 rows read (1 silently lost) | 127 rows read | A correctness fix, not a speed one, but it is the change that made the totals reconcile |

## Caveats

- Timings come from one laptop. Adjoa's machine may be slower, but the worst measured case is still about half the target.
- Scenario B copies the existing films, so it tests volume, not new kinds of messy data. A real 500-title list will hit the not-credible-money rule more often (see F-09). That rule is a single vectorised check, so it does not change the timing.
- The cold-download projection assumes TMDb answers at the speed it did on 2026-11-19. If TMDb asks the script to slow down, the script waits as instructed, and a run could take longer than 5 minutes without failing.
- Scenario B's worst case (29.3 s) is the first read of thousands of new files from disk. Later runs took about 3 s. In real use, Adjoa's files are already on her disk.
