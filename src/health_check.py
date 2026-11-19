"""
Improvement beyond the brief: the pre-meeting health check.

One command for Adjoa before she presents. It reruns the whole analysis, then answers
two questions in plain language:
  1. Can this run be trusted?   (RED / AMBER / GREEN checks on the data and the result)
  2. What changed since the last run Kwame saw?   (verdicts, picks, deal numbers)

    .venv\\Scripts\\python src\\health_check.py                 # check the current data
    .venv\\Scripts\\python src\\health_check.py --ids new.csv   # check a new candidate list
    .venv\\Scripts\\python src\\health_check.py --accept        # after review: make this run the new reference

Writes reports/health_check.md. Exit code 1 if any check is RED, so it can also gate automation.
The reference ("what Kwame last saw") is stored in reports/accepted_run.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import analysis
import metrics as m
import run_all

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "health_check.md"
ACCEPTED = ROOT / "reports" / "accepted_run.json"

# Thresholds (each is a judgement; see improvement.md)
UNUSABLE_ROWS_AMBER, UNUSABLE_ROWS_RED = 0.05, 0.15     # share of rows that cannot be assessed at all
MONEY_MISSING_AMBER, MONEY_MISSING_RED = 0.05, 0.20     # share of films with no credible budget/revenue
STANDALONES_AMBER, STANDALONES_RED = 30, 10             # standalones in the smaller (2000-onward) window
INCOMPLETE_BUNDLES_AMBER = 0.25                         # share of bundles missing released films
SNAPSHOT_AGE_AMBER_DAYS = 100                           # older than about a quarter
GAP_SHIFT_AMBER = 5.0                                   # score-gap move vs accepted run, in points

ICON = {"RED": "🔴 RED", "AMBER": "🟠 AMBER", "GREEN": "🟢 GREEN"}


def grade(value, amber, red, higher_is_worse=True):
    if higher_is_worse:
        return "RED" if value >= red else "AMBER" if value >= amber else "GREEN"
    return "RED" if value <= red else "AMBER" if value <= amber else "GREEN"


def snapshot(results: dict) -> dict:
    """The facts Kwame acts on, in a form that can be saved and compared next quarter."""
    out = {"taken_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    for w in analysis.WINDOWS:
        r = results[w]
        out[w] = {
            "verdict": r["verdict"],
            "score_gap": round(float(r["gap"]["gap"]), 1),
            "bundle_picks": list(r["franchise_picks"]["collection_name"]),
            "standalone_picks": list(r["standalone_picks"]["title"]),
            "strongest_bundle": r["deal"]["bundle"],
            "value_vs_typical_standalone": round(float(r["deal"]["value_per_film_vs_typical_standalone"]), 2),
            "weakest_film_outranks": round(float(r["deal"]["weakest_film_outranks_share_of_list"]), 3),
        }
    return out


def data_checks(results: dict) -> list[dict]:
    root = ROOT / "data" / "processed"
    audit = pd.read_csv(root / "id_audit.csv", keep_default_na=False, dtype=str)
    log = pd.read_csv(root / "fetch_log.csv")
    films = results["all_years"]["films"]
    rows = []

    def add(name, status, finding, action):
        rows.append({"check": name, "status": status, "finding": finding, "what to do": action})

    fates = audit["fate"].value_counts()
    add("Every row accounted for", "GREEN" if fates.sum() == len(audit) else "RED",
        f"{len(audit)} rows in, {fates.sum()} with a fate",
        "Stop: do not present. Run src/fetch.py on its own and read its output.")

    failed = int(log["outcome"].eq("failed").sum())
    add("Downloads completed", "RED" if failed else "GREEN", f"{failed} requests failed",
        "Run again; only the failed items are retried." if failed else "None.")

    unusable = audit["fate"].isin(["not_found_on_tmdb", "blank", "not_an_id", "non_positive", "imdb_id_unresolved"]).mean()
    add("Rows that cannot be assessed", grade(unusable, UNUSABLE_ROWS_AMBER, UNUSABLE_ROWS_RED),
        f"{unusable:.1%} of rows ({int(round(unusable * len(audit)))})",
        "Send the row numbers in data/processed/id_audit.csv back to the list's owners; say the count in the room.")

    dup = int(fates.get("duplicate", 0))
    add("Repeated rows", "AMBER" if dup else "GREEN", f"{dup} repeat rows removed",
        "Mention it; ask the list's owners to de-duplicate their sources." if dup else "None.")

    no_money = float((~films["money_reported"]).mean())
    add("Films without credible money figures", grade(no_money, MONEY_MISSING_AMBER, MONEY_MISSING_RED),
        f"{no_money:.1%} of films scored on audience measures only",
        "If AMBER/RED, say the cinema-takings comparison rests on fewer films.")

    modern_st = int((results["2000_onward"]["films"]["group"] == "standalone").sum())
    add("Standalones from 2000 onward (sample size)", grade(modern_st, STANDALONES_AMBER, STANDALONES_RED, higher_is_worse=False),
        f"{modern_st} standalones", "Present the 2000-onward verdict as provisional; it can flip on a few films.")

    b = results["all_years"]["bundles"]
    incomplete = float((~b["complete_on_list"]).mean()) if len(b) else 0.0
    add("Bundles missing released films", "AMBER" if incomplete > INCOMPLETE_BUNDLES_AMBER else "GREEN",
        f"{incomplete:.0%} of {len(b)} bundles", "Ask each studio exactly which films its bundle includes before pricing it.")

    fetched = pd.to_datetime(films["fetched_at"], utc=True)
    age = (pd.Timestamp.now(tz="UTC") - fetched.min()).days
    add("Age of the data", "AMBER" if age > SNAPSHOT_AGE_AMBER_DAYS else "GREEN", f"oldest figure fetched {age} days ago",
        "Refresh before a board meeting: src/run_all.py --refresh (needs the key).")

    flip = results["verdict_changes_between_windows"]
    add("Answer the same in both periods", "AMBER" if flip else "GREEN",
        f"all years: {results['all_years']['verdict']}; 2000 onward: {results['2000_onward']['verdict']}",
        "Say it out loud, first: the brief requires it." if flip else "None.")
    return rows


def change_checks(now: dict, before: dict | None) -> list[dict]:
    if before is None:
        return [{"check": "Changes since the accepted run", "status": "AMBER",
                 "finding": "no accepted run yet", "what to do": "Review this run, then rerun with --accept."}]
    rows = []
    for w in analysis.WINDOWS:
        a, b = before[w], now[w]
        label = w.replace("_", " ")
        changes = []
        if a["verdict"] != b["verdict"]:
            changes.append(f"verdict {a['verdict']} → {b['verdict']}")
        if abs(a["score_gap"] - b["score_gap"]) >= GAP_SHIFT_AMBER:
            changes.append(f"score gap {a['score_gap']:+} → {b['score_gap']:+}")
        if a["strongest_bundle"] != b["strongest_bundle"]:
            changes.append(f"strongest bundle {a['strongest_bundle']} → {b['strongest_bundle']}")
        for key, name in (("bundle_picks", "bundle picks"), ("standalone_picks", "standalone picks")):
            out_, in_ = set(a[key]) - set(b[key]), set(b[key]) - set(a[key])
            if out_ or in_:
                changes.append(f"{name}: out {sorted(out_) or '-'}, in {sorted(in_) or '-'}")
        rows.append({"check": f"Changes since accepted run ({label})", "status": "AMBER" if changes else "GREEN",
                     "finding": "; ".join(changes) or f"nothing material changed since {before['taken_at'][:10]}",
                     "what to do": "Explain each change before presenting; update the memo." if changes else "None."})
    return rows


def write_report(rows: list[dict], now: dict) -> str:
    worst = "RED" if any(r["status"] == "RED" for r in rows) else "AMBER" if any(r["status"] == "AMBER" for r in rows) else "GREEN"
    headline = {"RED": "Do not present this run. Fix the red items first.",
                "AMBER": "Safe to present, but say the amber items out loud.",
                "GREEN": "Safe to present."}[worst]
    lines = [f"# Pre-meeting health check: {ICON[worst]}", "", f"**{headline}**", "",
             f"Run at {now['taken_at']} UTC.", "",
             "| Check | Status | Finding | What to do |", "|---|---|---|---|"]
    lines += [f"| {r['check']} | {ICON[r['status']]} | {r['finding']} | {r['what to do']} |" for r in rows]
    lines += ["", "## What Kwame would hear", ""]
    for w in analysis.WINDOWS:
        s = now[w]
        lines.append(f"- **{w.replace('_', ' ')}:** verdict *{s['verdict']}*; bundles {', '.join(x.replace(' Collection', '') for x in s['bundle_picks'])}; "
                     f"standalones {', '.join(s['standalone_picks'])}; strongest bundle worth {s['value_vs_typical_standalone']}× "
                     f"a typical standalone per film, weakest film outranks {s['weakest_film_outranks']:.0%} of the list.")
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return worst


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ids", type=Path, help="a different candidate list to check")
    p.add_argument("--refresh", action="store_true", help="download fresh data first (needs the key)")
    p.add_argument("--accept", action="store_true", help="store this run as the reference for next time")
    a = p.parse_args(argv)

    results, _ = run_all.run(refresh=a.refresh, ids=a.ids)
    now = snapshot(results)
    before = json.loads(ACCEPTED.read_text(encoding="utf-8")) if ACCEPTED.exists() else None
    rows = data_checks(results) + change_checks(now, before)
    worst = write_report(rows, now)

    pd.set_option("display.width", 250, "display.max_colwidth", 110)
    print(pd.DataFrame(rows)[["status", "check", "finding"]].to_string(index=False))
    print(f"\nOVERALL: {worst}   (full report: reports/health_check.md)")
    if a.accept:
        if worst == "RED":
            print("Not accepted: fix the RED items first.")
        else:
            ACCEPTED.write_text(json.dumps(now, indent=2), encoding="utf-8")
            print("Accepted: this run is now the reference for the next check.")
    return 1 if worst == "RED" else 0


if __name__ == "__main__":
    sys.exit(main())
