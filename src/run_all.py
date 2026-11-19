"""
One command to rerun the whole analysis, timing each stage.

    .venv\\Scripts\\python src\\run_all.py            # from saved data (fast; works without an API key)
    .venv\\Scripts\\python src\\run_all.py --refresh  # download fresh data from TMDb first (needs key)

Writes every output to outputs/ and the stage timings to outputs/timings.csv.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

import analysis
import build_tables
import diagnose
import fetch

ROOT = Path(__file__).resolve().parents[1]


def run(refresh: bool = False, ids: Path | None = None, quiet: bool = True) -> tuple[dict, pd.DataFrame]:
    timings = []

    def stage(name, fn):
        start = time.perf_counter()
        value = fn()
        timings.append({"stage": name, "seconds": time.perf_counter() - start})
        return value

    argv = (["--refresh"] if refresh else []) + (["--ids", str(ids)] if ids else [])
    if quiet:
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            code = stage("1 acquire (fetch or reuse saved replies)", lambda: fetch.main(argv))
    else:
        code = stage("1 acquire (fetch or reuse saved replies)", lambda: fetch.main(argv))
    if code != 0:
        raise SystemExit("Acquisition failed - run src/fetch.py on its own to see why.")

    tables = stage("2 flatten JSON into tables + join checks", lambda: build_tables.build_all(save=True))
    stage("3 diagnosis checks and effects", lambda: (
        diagnose.run_checks(tables).to_csv(diagnose.OUT_DIR / "diagnosis_checks.csv", index=False),
        diagnose.run_effects(tables).to_csv(diagnose.OUT_DIR / "diagnosis_effects.csv", index=False),
        diagnose.bundle_completeness(tables).to_csv(diagnose.OUT_DIR / "bundle_completeness.csv"),
    ))
    results = stage("4 analysis, both windows", lambda: analysis.run(analysis.load(tables)))
    stage("5 save outputs", lambda: analysis.save(results))

    t = pd.DataFrame(timings)
    t.loc[len(t)] = {"stage": "TOTAL", "seconds": t["seconds"].sum()}
    t.to_csv(ROOT / "outputs" / "timings.csv", index=False)
    return results, t


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--refresh", action="store_true")
    p.add_argument("--ids", type=Path)
    a = p.parse_args()
    res, t = run(refresh=a.refresh, ids=a.ids, quiet=False)
    print("\n" + t.round(2).to_string(index=False))
    print("\nVerdict, all years:   ", res["all_years"]["verdict"])
    print("Verdict, 2000 onward: ", res["2000_onward"]["verdict"])
    if res["verdict_changes_between_windows"]:
        print("*** THE VERDICT CHANGES BETWEEN THE TWO WINDOWS - say so in the memo ***")
    sys.exit(0)
