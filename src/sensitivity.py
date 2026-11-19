"""
What does the recommendation look like under each rejected alternative?

Reruns the whole analysis once per alternative judgement call (see decisions/)
and records, for both windows: the verdict, the score gap and its 95% range,
the three bundle picks and the five standalone picks.

Run:  .venv\\Scripts\\python src\\sensitivity.py
Writes outputs/sensitivity.csv
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import analysis

ROOT = Path(__file__).resolve().parents[1]

SCENARIOS = {
    "BASELINE (as decided)": {},
    "ADR-004 alt: franchise = any series membership": {"rule": "tmdb_flag"},
    "ADR-005 alt: box-office multiple only": {"components": ("money",)},
    "ADR-005 alt: audience rating only": {"components": ("quality",)},
    "ADR-005 alt: audience measures only (no box office)": {"components": ("quality", "reach")},
    "ADR-006 alt: averages instead of medians": {"stat": "mean"},
    "ADR-009 alt: judge bundles on films offered only": {"bundle_basis": "on_list"},
    "ADR-010 alt: standalone picks may belong to a series": {"one_offs_only": False},
}


def short(name: str) -> str:
    return name.replace(" Collection", "")


def run() -> pd.DataFrame:
    data = analysis.load()
    rows = []
    for name, settings in SCENARIOS.items():
        res = analysis.run(data, **settings)
        for w in analysis.WINDOWS:
            r = res[w]
            rows.append({
                "scenario": name, "window": w, "verdict": r["verdict"],
                "score_gap": round(r["gap"]["gap"], 1),
                "gap_95_range": f"{r['gap']['low']:+.1f} to {r['gap']['high']:+.1f}",
                "verdict_changes_between_windows": res["verdict_changes_between_windows"],
                "bundle_picks": ", ".join(r["franchise_picks"]["collection_name"].map(short)),
                "standalone_picks": ", ".join(r["standalone_picks"]["title"]),
                "strongest_bundle": short(r["deal"]["bundle"]),
                "strongest_bundle_value_vs_standalone": round(r["deal"]["value_per_film_vs_typical_standalone"], 2),
            })
    out = pd.DataFrame(rows)
    (ROOT / "outputs").mkdir(exist_ok=True)
    out.to_csv(ROOT / "outputs" / "sensitivity.csv", index=False)
    return out


if __name__ == "__main__":
    pd.set_option("display.width", 300, "display.max_colwidth", 120)
    print(run().to_string(index=False))
