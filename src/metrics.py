"""
Shared definitions used by the diagnosis (Step 2) and the analysis (Step 3),
so both always measure the same thing. Every rule here is a judgement call
documented in decisions/.

All calculations are column-wise (vectorised): no loops over film rows.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# A money figure below this is treated as "not reported", not as a real value.
# TMDb stores unknown budget/revenue as 0, and sometimes as junk like $1,465.
MIN_CREDIBLE_DOLLARS = 10_000

MODERN_FROM_YEAR = 2000          # the "2000-onward" window Finance asked for
MIN_ENTRIES_FOR_BUNDLE = 2       # a franchise counts as a bundle when >= 2 of its films are on the list


def add_money_measures(films: pd.DataFrame) -> pd.DataFrame:
    """Add box-office multiple (revenue / budget), leaving it blank when either figure is not credible."""
    out = films.copy()
    budget = out["budget"].where(out["budget"] >= MIN_CREDIBLE_DOLLARS)
    revenue = out["revenue"].where(out["revenue"] >= MIN_CREDIBLE_DOLLARS)
    out["money_reported"] = budget.notna() & revenue.notna()
    out["box_office_multiple"] = revenue / budget
    return out


def classify(films: pd.DataFrame, rule: str = "on_list") -> pd.Series:
    """Label each film 'franchise' or 'standalone'.

    rule="on_list"   (default) franchise = its series has >= 2 films on the candidate list,
                     i.e. it is actually offered as a bundle.
    rule="tmdb_flag" franchise = TMDb says it belongs to any series at all.
    """
    in_series = films["collection_id"].notna()
    if rule == "tmdb_flag":
        is_franchise = in_series
    elif rule == "on_list":
        entries_on_list = films.groupby("collection_id")["tmdb_id"].transform("size")
        is_franchise = in_series & (entries_on_list >= MIN_ENTRIES_FOR_BUNDLE)
    else:
        raise ValueError(rule)
    return pd.Series(np.where(is_franchise, "franchise", "standalone"), index=films.index, name="group")


def prepare(films: pd.DataFrame, rule: str = "on_list") -> pd.DataFrame:
    out = add_money_measures(films)
    out["group"] = classify(out, rule)
    out["modern"] = out["year"] >= MODERN_FROM_YEAR
    return out


def window(films: pd.DataFrame, name: str) -> pd.DataFrame:
    return films if name == "all_years" else films[films["modern"]]


def headline(films: pd.DataFrame, stat: str = "median") -> dict:
    """Franchise-vs-standalone comparison for one table of films."""
    g = films.groupby("group").agg(
        n=("tmdb_id", "size"),
        multiple=("box_office_multiple", stat),
        rating=("vote_average", stat),
    )
    f, s = g.loc["franchise"], g.loc["standalone"]
    return {
        "franchise_n": int(f["n"]), "standalone_n": int(s["n"]),
        "franchise_multiple": f["multiple"], "standalone_multiple": s["multiple"],
        "multiple_gap": f["multiple"] - s["multiple"],
        "franchise_rating": f["rating"], "standalone_rating": s["rating"],
        "rating_gap": f["rating"] - s["rating"],
        "multiple_leader": "franchise" if f["multiple"] > s["multiple"] else "standalone",
        "rating_leader": "franchise" if f["rating"] > s["rating"] else "standalone",
    }


def bootstrap_gap(films: pd.DataFrame, column: str, n_boot: int = 10_000, seed: int = 7,
                  stat: str = "median") -> tuple[float, float, float]:
    """95% interval for (franchise median - standalone median), by resampling.
    Vectorised: all resamples are drawn as one matrix, no Python loop.
    stat="mean" compares averages instead (used only to test that alternative)."""
    rng = np.random.default_rng(seed)
    f = {"median": np.median, "mean": np.mean}[stat]
    fr = films.loc[films["group"].eq("franchise"), column].dropna().to_numpy()
    st = films.loc[films["group"].eq("standalone"), column].dropna().to_numpy()
    fr_med = f(fr[rng.integers(0, len(fr), (n_boot, len(fr)))], axis=1)
    st_med = f(st[rng.integers(0, len(st), (n_boot, len(st)))], axis=1)
    gaps = fr_med - st_med
    share_franchise_ahead = float((gaps > 0).mean())
    lo, hi = np.percentile(gaps, [2.5, 97.5])
    return float(lo), float(hi), share_franchise_ahead
