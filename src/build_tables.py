"""
Turns the saved TMDb replies (nested JSON) into flat tables, one fact per row.

Output (data/processed/):
  films.csv        one row per film      (key: tmdb_id)
  film_people.csv  one row per film x person x role  (directors and top-billed actors)
  collections.csv  one row per franchise (key: collection_id)

Every join is checked: we prove no film is dropped or duplicated.

Run:  .venv\\Scripts\\python src\\build_tables.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

LEAD_ACTOR_SLOTS = 3   # "lead actors" = the top 3 billed cast members (see decisions/ADR on talent)


def _load_bodies(kind: str, ids) -> list[dict]:
    """Read the saved replies of one kind for the given ids only; keep successful ones (status 200).

    Only the requested ids are read: the folder also holds replies saved for
    earlier candidate lists, and those must never leak into this list's analysis.
    (Looping over files here is reading from disk, not analysing rows.)"""
    bodies = []
    for key in sorted({int(i) for i in ids}):
        file = RAW_DIR / kind / f"{key}.json"
        if not file.exists():
            continue
        record = json.loads(file.read_text(encoding="utf-8"))
        if record.get("status_code") == 200:
            body = record["body"]
            body["_fetched_at"] = record.get("fetched_at")
            bodies.append(body)
    return bodies


def _films_frame(bodies: list[dict]) -> pd.DataFrame:
    """Flatten movie-detail replies into one row per film."""
    raw = pd.json_normalize(bodies)
    if "belongs_to_collection.id" not in raw:
        raw["belongs_to_collection.id"] = pd.NA
        raw["belongs_to_collection.name"] = pd.NA
    films = pd.DataFrame({
        "tmdb_id": raw["id"].astype(int),
        "title": raw["title"],
        "release_date": pd.to_datetime(raw["release_date"], errors="coerce"),
        "status": raw["status"],
        "budget": raw["budget"].astype("float64"),
        "revenue": raw["revenue"].astype("float64"),
        "runtime": raw["runtime"],
        "vote_average": raw["vote_average"],
        "vote_count": raw["vote_count"],
        "original_language": raw["original_language"],
        "collection_id": raw.get("belongs_to_collection.id").astype("Int64"),
        "collection_name": raw.get("belongs_to_collection.name"),
        # genres is a list of {id, name}: keep the names as one readable text field
        "genres": raw["genres"].map(lambda g: "|".join(x["name"] for x in g)),
        "fetched_at": raw["_fetched_at"],
    })
    films["year"] = films["release_date"].dt.year.astype("Int64")
    return films


def build_films(audit: pd.DataFrame) -> pd.DataFrame:
    on_list = audit.loc[audit["fate"].eq("fetched"), "tmdb_id"].astype(float).astype(int)
    films = _films_frame(_load_bodies("movie", on_list))

    # Which rows of the client's list point at this film (useful for tracing back)
    usable = audit[audit["tmdb_id"].notna()]
    rows = usable.groupby("tmdb_id")["row_number"].agg(lambda s: "|".join(map(str, s)))
    films["list_rows"] = films["tmdb_id"].map(rows)
    films["times_on_list"] = films["tmdb_id"].map(usable.groupby("tmdb_id").size())

    fetched_ids = set(audit.loc[audit["fate"].eq("fetched"), "tmdb_id"].astype(int))
    assert films["tmdb_id"].is_unique, "a film appears twice in the film table"
    assert set(films["tmdb_id"]) == fetched_ids, "film table does not match the fetched ids in id_audit.csv"
    return films.sort_values("tmdb_id").reset_index(drop=True)


def build_people(films: pd.DataFrame) -> pd.DataFrame:
    credits = _load_bodies("credits", films["tmdb_id"])
    # json_normalize with record_path explodes the nested cast / crew lists into rows
    cast = pd.json_normalize(credits, record_path="cast", meta="id", meta_prefix="film_")
    crew = pd.json_normalize(credits, record_path="crew", meta="id", meta_prefix="film_")

    leads = cast.loc[cast["order"] < LEAD_ACTOR_SLOTS, ["film_id", "id", "name", "order"]].assign(role="lead_actor")
    directors = crew.loc[crew["job"].eq("Director"), ["film_id", "id", "name"]].assign(role="director", order=pd.NA)
    people = (pd.concat([leads, directors], ignore_index=True)
                .rename(columns={"film_id": "tmdb_id", "id": "person_id", "name": "person_name", "order": "billing_order"})
                .drop_duplicates(["tmdb_id", "person_id", "role"]))
    people["tmdb_id"] = people["tmdb_id"].astype(int)

    # Join proof: every person row must belong to a film in the film table,
    # and the join must not create extra rows.
    checked = people.merge(films[["tmdb_id"]], on="tmdb_id", how="left", validate="many_to_one", indicator=True)
    assert len(checked) == len(people), "join to films duplicated rows"
    assert checked["_merge"].eq("both").all(), "people rows found for a film not in the film table"
    return people.sort_values(["tmdb_id", "role", "billing_order"]).reset_index(drop=True)


def build_collections(films: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for body in _load_bodies("collection", films["collection_id"].dropna()):
        parts = pd.DataFrame(body.get("parts", []))
        dates = pd.to_datetime(parts.get("release_date"), errors="coerce") if len(parts) else pd.Series(dtype="datetime64[ns]")
        fetched = pd.to_datetime(body["_fetched_at"]).tz_localize(None)
        released = parts.loc[dates.notna() & (dates <= fetched)] if len(parts) else parts
        rows.append({
            "collection_id": int(body["id"]),
            "collection_name": body.get("name"),
            "parts_total": len(parts),
            "parts_released": len(released),
            "released_part_ids": "|".join(map(str, released["id"])) if len(released) else "",
        })
    coll = pd.DataFrame(rows)
    on_list = films.groupby("collection_id").size().rename("parts_on_list")
    coll = coll.merge(on_list, left_on="collection_id", right_index=True, how="left", validate="one_to_one")
    coll["parts_on_list"] = coll["parts_on_list"].fillna(0).astype(int)
    coll["share_of_released_on_list"] = coll["parts_on_list"] / coll["parts_released"]
    return coll.sort_values("collection_name").reset_index(drop=True)


def build_all(save: bool = True) -> dict[str, pd.DataFrame]:
    audit = pd.read_csv(PROCESSED_DIR / "id_audit.csv", dtype={"raw_value": str}, keep_default_na=False,
                        na_values={"tmdb_id": [""]})
    films = build_films(audit)
    people = build_people(films)
    collections = build_collections(films)
    # Franchise films NOT on the client's list (used only to test bundle completeness)
    released = collections["released_part_ids"].str.split("|").explode()
    released = pd.to_numeric(released[released.ne("")], errors="coerce").dropna().astype(int)
    extra_bodies = _load_bodies("movie_extra", set(released) - set(films["tmdb_id"]))
    films_extra = (_films_frame(extra_bodies) if extra_bodies else films.iloc[0:0].drop(columns=["list_rows", "times_on_list"]))
    assert not films_extra["tmdb_id"].isin(films["tmdb_id"]).any(), "an off-list film is also on the list"

    # Join proof for franchises: each film with a franchise finds exactly one franchise row.
    joined = films.merge(collections[["collection_id"]], on="collection_id", how="left",
                         validate="many_to_one", indicator=True)
    assert len(joined) == len(films), "franchise join changed the number of films"
    assert joined.loc[films["collection_id"].notna().values, "_merge"].eq("both").all(), \
        "a film's franchise is missing from collections.csv - rerun src/fetch.py"

    if save:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        films.to_csv(PROCESSED_DIR / "films.csv", index=False)
        people.to_csv(PROCESSED_DIR / "film_people.csv", index=False)
        collections.to_csv(PROCESSED_DIR / "collections.csv", index=False)
        films_extra.to_csv(PROCESSED_DIR / "films_off_list.csv", index=False)
    return {"audit": audit, "films": films, "people": people, "collections": collections,
            "films_extra": films_extra}


if __name__ == "__main__":
    t = build_all()
    print(f"films.csv:       {len(t['films'])} films")
    print(f"film_people.csv: {len(t['people'])} rows "
          f"({t['people']['role'].value_counts().to_dict()})")
    print(f"collections.csv: {len(t['collections'])} franchises")
    print(f"films_off_list.csv: {len(t['films_extra'])} franchise films not on the list")
    print("All join checks passed: no film dropped or duplicated.")
