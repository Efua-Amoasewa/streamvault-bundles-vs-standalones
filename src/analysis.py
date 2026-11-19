"""
Step 3 - Analysis: franchise bundles vs standalone hits.

For each time window ("all_years" and "2000_onward") this produces:
  * the franchise-vs-standalone comparison, with a 95% range on the gap
  * how films score by their position in a series (the "weak middle entries" question)
  * every bundle scored on the films offered AND on its whole released series
  * the shortlist: 3 franchise bundles + 5 standalones, each with its reason
  * the talent read: directors and lead actors who reliably signal a strong title
  * the numbers behind the deal note for the strongest bundle

How a title is scored (see decisions/ for why):
  Each film gets three percentile scores (0-100) against the other films in the same window:
    quality = audience rating, reach = number of audience ratings, money = box-office multiple
  Its title score is the average of the three (money is skipped when not credibly reported).

All calculations are column-wise (vectorised). The only Python loops are over the
two windows and over the handful of shortlisted rows when writing reason text.

Run:  .venv\\Scripts\\python src\\analysis.py
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

COMPONENTS = {"quality": "vote_average", "reach": "vote_count", "money": "box_office_multiple"}
N_FRANCHISE_PICKS = 3
N_STANDALONE_PICKS = 5
MIN_TALENT_UNITS = 2          # a person needs results in >= 2 separate series/standalones
AUDIENCE_FLOOR = 50           # standalone picks must be top-half on audience measures alone


# ----------------------------------------------------------------------------
# Scoring
# ----------------------------------------------------------------------------
def percentile_against(reference: pd.Series, values: pd.Series) -> pd.Series:
    """Percentile (0-100) of each value within the reference distribution.
    Ties get the mid-rank. Vectorised with a binary search (searchsorted)."""
    ref = np.sort(reference.dropna().to_numpy(dtype=float))
    v = values.to_numpy(dtype=float)
    below = np.searchsorted(ref, v, side="left")
    at_or_below = np.searchsorted(ref, v, side="right")
    pct = 100 * (below + at_or_below) / 2 / len(ref)
    return pd.Series(np.where(np.isnan(v), np.nan, pct), index=values.index)


def score(frame: pd.DataFrame, reference: pd.DataFrame, components: tuple[str, ...] | None = None) -> pd.DataFrame:
    """Add pct_quality, pct_reach, pct_money and title_score, judged against `reference`.
    `components` picks which percentiles make up the title score (default: all three)."""
    out = frame.copy()
    for name, col in COMPONENTS.items():
        out[f"pct_{name}"] = percentile_against(reference[col], out[col])
    use = components or tuple(COMPONENTS)
    out["title_score"] = out[[f"pct_{n}" for n in use]].mean(axis=1, skipna=True)
    out["audience_score"] = out[["pct_quality", "pct_reach"]].mean(axis=1)
    return out


def load(t: dict | None = None) -> dict:
    t = t or build_tables.build_all(save=False)
    films = m.prepare(t["films"])
    extra = m.add_money_measures(t["films_extra"]) if len(t["films_extra"]) else t["films_extra"]
    if len(extra):
        extra["modern"] = extra["year"] >= m.MODERN_FROM_YEAR

    # Real position of each film in its series (1 = first released), counting
    # released films that are NOT on the list too. Computed once, on all years,
    # so the 2000-onward window does not renumber films.
    cols = ["tmdb_id", "collection_id", "release_date"]
    series = pd.concat([films[cols], extra[cols]] if len(extra) else [films[cols]], ignore_index=True)
    series = series[series["collection_id"].notna()]
    series["series_position"] = series.groupby("collection_id")["release_date"].rank(method="first").astype(int)
    position = series.set_index("tmdb_id")["series_position"]
    assert position.index.is_unique, "a film has two series positions"
    films["series_position"] = films["tmdb_id"].map(position).astype("Int64")
    if len(extra):
        extra["series_position"] = extra["tmdb_id"].map(position).astype("Int64")
    return {"films": films, "extra": extra, "people": t["people"], "collections": t["collections"]}


def scored_window(data: dict, window: str, components=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    films = m.window(data["films"], window)
    extra = data["extra"]
    if len(extra):
        extra = m.window(extra, window)
        # off-list films only matter for franchises that are bundles on the list
        bundle_ids = films.loc[films["group"].eq("franchise"), "collection_id"].unique()
        extra = extra[extra["collection_id"].isin(bundle_ids)]
    return score(films, films, components), (score(extra, films, components) if len(extra) else extra)


# ----------------------------------------------------------------------------
# 1. Franchise vs standalone
# ----------------------------------------------------------------------------
def compare_groups(films: pd.DataFrame) -> pd.DataFrame:
    table = films.groupby("group").agg(
        films=("tmdb_id", "size"),
        median_title_score=("title_score", "median"),
        median_rating=("vote_average", "median"),
        median_audience_ratings=("vote_count", "median"),
        median_box_office_multiple=("box_office_multiple", "median"),
    )
    return table


def score_gap(films: pd.DataFrame, stat: str = "median") -> dict:
    lo, hi, share = m.bootstrap_gap(films, "title_score", stat=stat)
    med = films.groupby("group")["title_score"].agg(stat)
    return {"gap": med["franchise"] - med["standalone"], "low": lo, "high": hi, "share_franchise_ahead": share}


def verdict(gap: dict) -> str:
    if gap["share_franchise_ahead"] >= 0.95:
        return "franchise"
    if gap["share_franchise_ahead"] <= 0.05:
        return "standalone"
    return "too close to call"


# ----------------------------------------------------------------------------
# 2. The "weak middle entries" question
# ----------------------------------------------------------------------------
def by_position(films: pd.DataFrame) -> pd.DataFrame:
    fr = films[films["group"].eq("franchise")].copy()
    pos = fr["series_position"].astype(int)
    fr["position_label"] = np.where(pos >= 4, "4th or later", pos.astype(str))
    standalone_median = films.loc[films["group"].eq("standalone"), "title_score"].median()
    fr["below_typical_standalone"] = fr["title_score"] < standalone_median
    return fr.groupby("position_label").agg(
        films=("tmdb_id", "size"),
        median_title_score=("title_score", "median"),
        median_rating=("vote_average", "median"),
        median_box_office_multiple=("box_office_multiple", "median"),
        share_below_typical_standalone=("below_typical_standalone", "mean"),
    )


# ----------------------------------------------------------------------------
# 3. Bundles
# ----------------------------------------------------------------------------
def bundles(films: pd.DataFrame, extra: pd.DataFrame, basis: str = "cautious") -> pd.DataFrame:
    """basis="cautious": judge a bundle on whichever is lower, the films offered or the
    whole released series. basis="on_list": judge only the films offered."""
    fr = films[films["group"].eq("franchise")]
    standalone_median = films.loc[films["group"].eq("standalone"), "title_score"].median()

    def summarise(df: pd.DataFrame, suffix: str) -> pd.DataFrame:
        g = df.assign(weak=df["title_score"] < standalone_median).groupby(["collection_id", "collection_name"]).agg(
            films=("tmdb_id", "size"),
            mean_score=("title_score", "mean"),       # every film in a bundle is paid for, so the mean counts them all
            weakest_score=("title_score", "min"),
            weak_films=("weak", "sum"),
            first_year=("year", "min"),
            last_year=("year", "max"),
        )
        return g.add_suffix(suffix)

    on_list = summarise(fr, "_on_list")
    whole = summarise(pd.concat([fr, extra], ignore_index=True) if len(extra) else fr, "_whole_series")
    out = on_list.join(whole, how="left", validate="one_to_one").reset_index()
    out = out[out["films_on_list"] >= m.MIN_ENTRIES_FOR_BUNDLE]
    # Cautious value: if the studio insists on the whole series, judge it on the whole series
    if basis == "cautious":
        out["bundle_score"] = out[["mean_score_on_list", "mean_score_whole_series"]].min(axis=1)
        out["weakest_film"] = out[["weakest_score_on_list", "weakest_score_whole_series"]].min(axis=1)
    else:
        out["bundle_score"] = out["mean_score_on_list"]
        out["weakest_film"] = out["weakest_score_on_list"]
    out["value_per_film_vs_typical_standalone"] = out["bundle_score"] / standalone_median
    out["complete_on_list"] = out["films_on_list"] >= out["films_whole_series"]

    worst_title = (pd.concat([fr, extra], ignore_index=True) if len(extra) and basis == "cautious" else fr) \
        .sort_values("title_score").drop_duplicates("collection_id").set_index("collection_id")["title"]
    out["weakest_title"] = out["collection_id"].map(worst_title)
    return out.sort_values("bundle_score", ascending=False).reset_index(drop=True)


# ----------------------------------------------------------------------------
# 4. Shortlist
# ----------------------------------------------------------------------------
def _ordinal_top(pct: float) -> str:
    return f"top {max(1, round(100 - pct))}%"


def shortlist(films: pd.DataFrame, bundle_table: pd.DataFrame,
              one_offs_only: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    fr = bundle_table.head(N_FRANCHISE_PICKS).copy()
    fr["reason"] = [
        f"{int(r.films_on_list)} films; average title score {r.bundle_score:.0f}/100 "
        f"({r.value_per_film_vs_typical_standalone:.2f}x a typical standalone per film); "
        f"weakest film '{r.weakest_title}' scores {r.weakest_film:.0f}"
        + ("" if r.complete_on_list else f"; list holds {int(r.films_on_list)} of {int(r.films_whole_series)} released films")
        for r in fr.itertuples()
    ]  # (loop over 3 rows only, to write the reason text)

    # A pick must be a true one-off (no series attached, so no risk of being
    # forced into a bundle) and top-half on audience measures alone, so it does
    # not rest on box-office figures Finance may dispute.
    one_off = films["collection_id"].isna() if one_offs_only else True
    st = films[films["group"].eq("standalone") & one_off & (films["audience_score"] >= AUDIENCE_FLOOR)]
    st = st.sort_values("title_score", ascending=False).head(N_STANDALONE_PICKS).copy()
    st["reason"] = [
        f"rating {r.vote_average:.1f} ({_ordinal_top(r.pct_quality)}), "
        f"{r.vote_count:,} audience ratings ({_ordinal_top(r.pct_reach)}), "
        f"earned {r.box_office_multiple:.1f}x its budget ({_ordinal_top(r.pct_money)})"
        + ("; released before 2000" if not r.modern else "")
        for r in st.itertuples()
    ]  # (loop over 5 rows only, to write the reason text)
    keep = ["tmdb_id", "title", "year", "title_score", "vote_average", "vote_count", "box_office_multiple", "reason"]
    return fr, st[keep]


# ----------------------------------------------------------------------------
# 5. Talent
# ----------------------------------------------------------------------------
def talent(films: pd.DataFrame, people: pd.DataFrame) -> pd.DataFrame:
    """Directors and lead actors whose titles score above the list's typical title.

    A franchise counts ONCE per person (its films are averaged into one result),
    so eight Harry Potter films are one piece of evidence, not eight."""
    p = people.merge(films[["tmdb_id", "title", "collection_id", "title_score"]], on="tmdb_id",
                     how="inner", validate="many_to_one")
    p["unit"] = p["collection_id"].astype("string").fillna("film-" + p["tmdb_id"].astype(str))
    units = p.groupby(["role", "person_id", "person_name", "unit"]).agg(
        unit_score=("title_score", "mean"), films=("tmdb_id", "size"), example=("title", "first")).reset_index()
    typical = films["title_score"].median()
    units["above_typical"] = units["unit_score"] > typical
    per = units.groupby(["role", "person_id", "person_name"]).agg(
        separate_results=("unit", "size"), films=("films", "sum"),
        average_score=("unit_score", "mean"), worst_result=("unit_score", "min"),
        hit_rate=("above_typical", "mean"),
        titles=("example", lambda s: "; ".join(s.head(4))),
    ).reset_index()
    per = per[per["separate_results"] >= MIN_TALENT_UNITS]
    per["lift_vs_typical"] = per["average_score"] - typical
    per["evidence"] = np.where(per["separate_results"] >= 3, "moderate", "thin (2 results)")
    return per.sort_values(["role", "lift_vs_typical"], ascending=[True, False]).reset_index(drop=True)


# ----------------------------------------------------------------------------
# 6. Deal note numbers
# ----------------------------------------------------------------------------
def deal_note(films: pd.DataFrame, bundle_table: pd.DataFrame) -> dict:
    top = bundle_table.iloc[0]
    others = bundle_table.iloc[1:]
    share_outranked = float((films["title_score"] < top["weakest_film"]).mean())
    return {
        "bundle": top["collection_name"],
        "films": int(top["films_on_list"]),
        "complete": bool(top["complete_on_list"]),
        "bundle_score": float(top["bundle_score"]),
        "value_per_film_vs_typical_standalone": float(top["value_per_film_vs_typical_standalone"]),
        "value_per_film_vs_typical_bundle": float(top["bundle_score"] / bundle_table["bundle_score"].median()),
        "value_per_film_vs_next_best_bundle": float(top["bundle_score"] / others.iloc[0]["bundle_score"]) if len(others) else np.nan,
        "next_best_bundle": others.iloc[0]["collection_name"] if len(others) else None,
        "weakest_title": top["weakest_title"],
        "weakest_film_score": float(top["weakest_film"]),
        "weakest_film_outranks_share_of_list": share_outranked,
    }


# ----------------------------------------------------------------------------
# Run everything for both windows
# ----------------------------------------------------------------------------
def run(data: dict | None = None, *, rule: str = "on_list", components: tuple[str, ...] | None = None,
        stat: str = "median", bundle_basis: str = "cautious", one_offs_only: bool = True) -> dict:
    """Defaults are the decisions in decisions/. The keyword settings exist so
    src/sensitivity.py can rerun everything under each rejected alternative."""
    data = data or load()
    if rule != "on_list":
        data = {**data, "films": data["films"].assign(group=m.classify(data["films"], rule))}
    results = {}
    for w in WINDOWS:
        films, extra = scored_window(data, w, components)
        bundle_table = bundles(films, extra, bundle_basis)
        fr_pick, st_pick = shortlist(films, bundle_table, one_offs_only)
        gap = score_gap(films, stat)
        results[w] = {
            "films": films, "comparison": compare_groups(films), "gap": gap, "verdict": verdict(gap),
            "positions": by_position(films), "bundles": bundle_table,
            "franchise_picks": fr_pick, "standalone_picks": st_pick,
            "talent": talent(films, data["people"]), "deal": deal_note(films, bundle_table),
        }
    results["verdict_changes_between_windows"] = results["all_years"]["verdict"] != results["2000_onward"]["verdict"]
    return results


def save(results: dict) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for w in WINDOWS:
        r = results[w]
        r["films"].to_csv(OUT_DIR / f"scored_films_{w}.csv", index=False)
        r["comparison"].to_csv(OUT_DIR / f"comparison_{w}.csv")
        r["positions"].to_csv(OUT_DIR / f"series_position_{w}.csv")
        r["bundles"].to_csv(OUT_DIR / f"bundles_{w}.csv", index=False)
        r["franchise_picks"].to_csv(OUT_DIR / f"shortlist_franchise_{w}.csv", index=False)
        r["standalone_picks"].to_csv(OUT_DIR / f"shortlist_standalone_{w}.csv", index=False)
        r["talent"].to_csv(OUT_DIR / f"talent_{w}.csv", index=False)
    summary = pd.DataFrame([{"window": w, "verdict": results[w]["verdict"], **{f"score_gap_{k}": v for k, v in results[w]["gap"].items()},
                             **{f"deal_{k}": v for k, v in results[w]["deal"].items()}} for w in WINDOWS])
    summary.to_csv(OUT_DIR / "headline_summary.csv", index=False)


def print_report(results: dict) -> None:
    pd.set_option("display.width", 250, "display.max_colwidth", 200, "display.max_columns", 30)
    for w in WINDOWS:
        r = results[w]
        print(f"\n{'=' * 30} {w.replace('_', ' ').upper()} {'=' * 30}")
        print(r["comparison"].round(2).to_string())
        g = r["gap"]
        print(f"Title-score gap (franchise - standalone): {g['gap']:+.1f}  95% range {g['low']:+.1f} to {g['high']:+.1f}  "
              f"-> verdict: {r['verdict'].upper()}")
        print("\nBy position in series:"); print(r["positions"].round(2).to_string())
        print("\nBundles:")
        cols = ["collection_name", "films_on_list", "films_whole_series", "bundle_score", "weakest_film", "weakest_title",
                "value_per_film_vs_typical_standalone"]
        print(r["bundles"][cols].round(2).to_string(index=False))
        print("\nFranchise picks:"); print(r["franchise_picks"][["collection_name", "reason"]].to_string(index=False))
        print("\nStandalone picks:"); print(r["standalone_picks"][["title", "year", "reason"]].to_string(index=False))
        print("\nTalent (top 8 per role):")
        print(r["talent"].groupby("role").head(8)[["role", "person_name", "separate_results", "films", "average_score",
                                                     "hit_rate", "lift_vs_typical", "evidence", "titles"]].round(2).to_string(index=False))
        print("\nDeal note:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r["deal"].items()})
    flag = results["verdict_changes_between_windows"]
    print("\n*** VERDICT CHANGES BETWEEN WINDOWS ***" if flag else "\nVerdict is the same in both windows.")


if __name__ == "__main__":
    res = run()
    save(res)
    print_report(res)
