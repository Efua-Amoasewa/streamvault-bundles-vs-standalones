"""
Step 2 - Data diagnosis.

1. Runs automatic checks that detect each known problem (and reports how big it is).
2. Re-computes the franchise-vs-standalone headline with each problem left
   UNHANDLED, to measure how much each one moves the client's answer.

Outputs:
  outputs/diagnosis_checks.csv    one row per check: what was found, how many
  outputs/diagnosis_effects.csv   headline numbers under each scenario, both windows

Run:  .venv\\Scripts\\python src\\diagnose.py     (after fetch.py and build_tables.py)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import build_tables
import metrics as m

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs"
WINDOWS = ("all_years", "2000_onward")


def run_checks(t: dict) -> pd.DataFrame:
    audit, films, people, coll, extra = t["audit"], t["films"], t["people"], t["collections"], t["films_extra"]
    f = m.prepare(films)
    fates = audit["fate"].value_counts()
    checks = []

    def add(check, count, detail=""):
        checks.append({"check": check, "count": count, "detail": detail})

    add("input rows", len(audit))
    for fate, n in fates.items():
        add(f"rows with fate: {fate}", int(n))
    dup = audit[audit["fate"].eq("duplicate")]
    add("films listed more than once", int(dup["tmdb_id"].nunique()),
        ", ".join(f.set_index("tmdb_id").loc[dup["tmdb_id"].unique().astype(int), "title"]))
    add("ids written in another site's format (IMDb)", int(audit["kind"].isin(["imdb_id", "imdb_id_unresolved"]).sum()),
        ", ".join(audit.loc[audit["kind"].str.startswith("imdb"), "raw_value"]))

    add("films on list with budget or revenue not credible (< $10,000)", int((~f["money_reported"]).sum()))
    fe = m.add_money_measures(extra) if len(extra) else extra
    if len(fe):
        add("off-list franchise films with budget or revenue not credible", int((~fe["money_reported"]).sum()),
            ", ".join(fe.loc[~fe["money_reported"], "title"]))
    add("films on list that lost money (multiple < 1)", int((f["box_office_multiple"] < 1).sum()),
        f"lowest multiple on list: {f['box_office_multiple'].min():.2f} ({f.loc[f['box_office_multiple'].idxmin(), 'title']})")
    add("lowest audience rating on list", 0, f"{f['vote_average'].min():.2f} ({f.loc[f['vote_average'].idxmin(), 'title']})")
    add("revenue is an exact round million (likely an estimate)", int((f["revenue"] % 1_000_000 == 0).sum()),
        ", ".join(f.loc[f["revenue"] % 1_000_000 == 0, "title"]))

    single = f[f["collection_id"].notna() & f["group"].eq("standalone")]
    add("films in a series but the only one of it on the list", len(single), ", ".join(single["title"]))
    bundles = coll[coll["parts_on_list"] >= m.MIN_ENTRIES_FOR_BUNDLE]
    incomplete = bundles[bundles["parts_on_list"] < bundles["parts_released"]]
    add("bundles on the list", len(bundles))
    add("bundles missing released films", len(incomplete),
        ", ".join(f"{r.collection_name.replace(' Collection', '')} {r.parts_on_list}/{r.parts_released}"
                  for r in incomplete.itertuples()))

    pre = f[~f["modern"]].groupby("group").size()
    add("franchise films released before 2000", int(pre.get("franchise", 0)))
    add("standalone films released before 2000", int(pre.get("standalone", 0)))
    add("standalone films from 2000 onward (sample size)", int((f["group"].eq("standalone") & f["modern"]).sum()))
    add("films with more than one director", int(people[people["role"].eq("director")].groupby("tmdb_id").size().gt(1).sum()))

    # Talent concentration: how much of a frequent name's record comes from one franchise?
    p = people.merge(f[["tmdb_id", "collection_id"]], on="tmdb_id", how="left", validate="many_to_one")
    p["series_key"] = p["collection_id"].astype("string").fillna("solo-" + p["tmdb_id"].astype(str))
    per_person = p.groupby(["person_id", "person_name", "role"]).agg(films=("tmdb_id", "nunique"),
                                                                       distinct_series=("series_key", "nunique"))
    frequent = per_person[per_person["films"] >= 3]
    one_series = frequent[frequent["distinct_series"].eq(1)]
    add("people with 3+ films on the list", len(frequent))
    add("...of whom every film is in the same franchise", len(one_series),
        ", ".join(one_series.reset_index()["person_name"]))
    add("vote count, smallest on list", int(f["vote_count"].min()))
    add("data snapshot taken (UTC)", 0, f"{films['fetched_at'].min()} to {films['fetched_at'].max()}")
    return pd.DataFrame(checks)


def run_effects(t: dict) -> pd.DataFrame:
    films, extra = t["films"], t["films_extra"]
    base = m.prepare(films)
    rows = []

    def record(scenario, frame, stat="median"):
        for w in WINDOWS:
            rows.append({"scenario": scenario, "window": w, **m.headline(m.window(frame, w), stat)})

    # Baseline: duplicates removed, bundle = >= 2 films on list, medians, money guard on
    record("baseline", base)

    # F: duplicates left in (each list row counted)
    record("duplicates left in", base.loc[base.index.repeat(base["times_on_list"])])

    # F: any series membership counts as franchise
    record("franchise = any series (TMDb flag)", m.prepare(films, rule="tmdb_flag"))

    # F: averages instead of medians (sensitive to a few extreme old hits)
    record("averages instead of medians", base, stat="mean")

    # F: the whole released franchise instead of only the films on the list
    if len(extra):
        bundle_ids = base.loc[base["group"].eq("franchise"), "collection_id"].unique()
        add = m.add_money_measures(extra[extra["collection_id"].isin(bundle_ids)])
        add["group"] = "franchise"
        add["modern"] = add["year"] >= m.MODERN_FROM_YEAR
        add = add[add["money_reported"]]
        record("bundles include their off-list films", pd.concat([base, add], ignore_index=True))

    out = pd.DataFrame(rows)

    # Statistical uncertainty of the baseline gaps (resampling)
    for w in WINDOWS:
        frame = m.window(base, w)
        for col, name in (("box_office_multiple", "multiple"), ("vote_average", "rating")):
            lo, hi, share = m.bootstrap_gap(frame, col)
            mask = out["scenario"].eq("baseline") & out["window"].eq(w)
            out.loc[mask, f"{name}_gap_95_low"] = lo
            out.loc[mask, f"{name}_gap_95_high"] = hi
            out.loc[mask, f"{name}_share_resamples_franchise_ahead"] = share
    return out


def bundle_completeness(t: dict) -> pd.DataFrame:
    """Per bundle: box-office multiple of the films on the list vs the whole released series."""
    base = m.prepare(t["films"])
    on = base[base["group"].eq("franchise")]
    extra = m.add_money_measures(t["films_extra"])
    extra = extra[extra["collection_id"].isin(on["collection_id"].unique()) & extra["money_reported"]]
    def agg(df):
        g = df.groupby("collection_name").agg(n=("tmdb_id", "size"), revenue=("revenue", "sum"),
                                              budget=("budget", "sum"), worst=("box_office_multiple", "min"),
                                              rating=("vote_average", "median"))
        g["multiple"] = g["revenue"] / g["budget"]
        return g[["n", "multiple", "worst", "rating"]]
    listed = agg(on)
    whole = agg(pd.concat([on, extra], ignore_index=True))
    out = listed.add_suffix("_on_list").join(whole.add_suffix("_whole_series"), how="left", validate="one_to_one")
    out["multiple_change"] = out["multiple_whole_series"] - out["multiple_on_list"]
    return out.sort_values("multiple_change")


def main() -> None:
    t = build_tables.build_all(save=True)
    OUT_DIR.mkdir(exist_ok=True)
    checks = run_checks(t)
    effects = run_effects(t)
    completeness = bundle_completeness(t)
    checks.to_csv(OUT_DIR / "diagnosis_checks.csv", index=False)
    effects.to_csv(OUT_DIR / "diagnosis_effects.csv", index=False)
    completeness.to_csv(OUT_DIR / "bundle_completeness.csv")

    pd.set_option("display.width", 250, "display.max_colwidth", 140, "display.max_columns", 30)
    print("=== Checks ===")
    print(checks.to_string(index=False))
    print("\n=== Effect on the headline (franchise minus standalone; medians unless stated) ===")
    cols = ["scenario", "window", "franchise_n", "standalone_n", "franchise_multiple", "standalone_multiple",
            "multiple_gap", "franchise_rating", "standalone_rating", "rating_gap", "multiple_leader", "rating_leader"]
    print(effects[cols].round(2).to_string(index=False))
    print("\n=== Uncertainty of baseline gaps (95% range from 10,000 resamples) ===")
    unc = effects[effects["scenario"].eq("baseline")].filter(regex="window|_95_|share")
    print(unc.round(3).to_string(index=False))
    print("\n=== Bundles: films on the list vs the whole released series ===")
    print(completeness.round(2).to_string())
    print("\nWrote outputs/diagnosis_checks.csv, outputs/diagnosis_effects.csv, outputs/bundle_completeness.csv")


if __name__ == "__main__":
    main()
