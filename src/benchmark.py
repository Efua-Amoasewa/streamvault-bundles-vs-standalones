"""
Measures run time against the time budget (see reports/runtime_report.md).

Scenario A - "Adjoa reruns it in a meeting": the full pipeline from saved data,
             as a fresh process each time (includes Python start-up and imports).
Scenario B - "next year's ~500-title list": the saved replies are copied 5 times
             with shifted ids (560 films, 160 franchises) into a temporary folder,
             then flattening + diagnosis + analysis are timed on that.

    .venv\\Scripts\\python src\\benchmark.py   (about 1-2 minutes)

Writes outputs/benchmark.csv.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

import analysis
import build_tables
import diagnose

ROOT = Path(__file__).resolve().parents[1]
RUNS = 5
COPIES = 5
SHIFT = 10_000_000


def time_fresh_process_runs() -> list[float]:
    times = []
    for _ in range(RUNS):
        start = time.perf_counter()
        subprocess.run([sys.executable, str(ROOT / "src" / "run_all.py")], check=True,
                       capture_output=True, cwd=ROOT)
        times.append(time.perf_counter() - start)
    return times


def _shift(body: dict, k: int, kind: str) -> dict:
    b = json.loads(json.dumps(body))
    off = k * SHIFT
    b["id"] = b["id"] + off
    if kind in ("movie", "movie_extra") and isinstance(b.get("belongs_to_collection"), dict):
        b["belongs_to_collection"]["id"] += off
    if kind == "collection":
        for part in b.get("parts", []):
            part["id"] += off
    return b


def build_scaled_copy(tmp: Path) -> pd.DataFrame:
    """Copy saved replies COPIES times with shifted ids; return a matching id_audit table."""
    ids = []
    for kind in ("movie", "credits", "collection", "movie_extra"):
        (tmp / "raw" / kind).mkdir(parents=True, exist_ok=True)
        for file in (ROOT / "data" / "raw" / kind).glob("*.json"):
            rec = json.loads(file.read_text(encoding="utf-8"))
            if rec.get("status_code") != 200:
                continue
            for k in range(COPIES):
                new = {**rec, "body": _shift(rec["body"], k, kind)}
                (tmp / "raw" / kind / f"{new['body']['id']}.json").write_text(json.dumps(new), encoding="utf-8")
                if kind == "movie":
                    ids.append(new["body"]["id"])
    n = len(ids)
    return pd.DataFrame({"row_number": np.arange(2, n + 2), "raw_value": [str(i) for i in ids],
                         "kind": "tmdb_id", "tmdb_id": pd.array(ids, dtype="Int64"),
                         "is_duplicate": False, "fate": "fetched"})


def time_scaled_runs() -> tuple[list[float], int]:
    times = []
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        audit = build_scaled_copy(tmp)
        (tmp / "processed").mkdir()
        audit.to_csv(tmp / "processed" / "id_audit.csv", index=False)
        build_tables.RAW_DIR, build_tables.PROCESSED_DIR = tmp / "raw", tmp / "processed"
        try:
            for _ in range(RUNS):
                start = time.perf_counter()
                t = build_tables.build_all(save=False)
                diagnose.run_checks(t); diagnose.run_effects(t); diagnose.bundle_completeness(t)
                analysis.run(analysis.load(t))
                times.append(time.perf_counter() - start)
            n_films = len(t["films"])
        finally:
            build_tables.RAW_DIR = ROOT / "data" / "raw"
            build_tables.PROCESSED_DIR = ROOT / "data" / "processed"
    return times, n_films


def summarise(name: str, times: list[float], target: float, films: int) -> dict:
    a = np.array(times)
    return {"scenario": name, "films": films, "runs": len(a), "median_s": np.median(a),
            "p95_s": np.percentile(a, 95), "worst_s": a.max(), "target_s": target, "target_met": bool(a.max() <= target)}


if __name__ == "__main__":
    print(f"Machine: {platform.platform()} | Python {platform.python_version()} | {platform.processor()}")
    print(f"Scenario A: {RUNS} fresh-process runs of src/run_all.py ...")
    a = time_fresh_process_runs()
    print(f"Scenario B: {RUNS} runs on a {COPIES}x copy of the data ...")
    b, n_big = time_scaled_runs()
    out = pd.DataFrame([
        summarise("A: full rerun from saved data (fresh process)", a, 60, 112),
        summarise(f"B: flatten + diagnose + analyse at {n_big} films", b, 60, n_big),
    ])
    (ROOT / "outputs").mkdir(exist_ok=True)
    out.to_csv(ROOT / "outputs" / "benchmark.csv", index=False)
    print(out.round(2).to_string(index=False))
