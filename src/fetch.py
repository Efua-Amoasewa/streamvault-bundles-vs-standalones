"""
Step 1 - Acquisition.

Reads data/id_list.csv, checks every row, and downloads from TMDb:
  * movie details  (GET /movie/{id})
  * movie credits  (GET /movie/{id}/credits)
for every unique, usable id, plus each franchise once
  * collection     (GET /collection/{id})
so we can tell whether the list holds a whole franchise or only part of it.

Design goals (see decisions/ for the reasoning):
  * Never lose track of a row: every row of the input file ends up in
    data/processed/id_audit.csv with a stated fate.
  * Be polite to a shared API: at most ~10 requests per second, honour
    "429 Too Many Requests" and back off on server errors.
  * Survive crashes: each response is saved to disk as soon as it arrives
    (data/raw/...). A rerun re-uses what is already saved and only downloads
    what is missing, so a re-run with nothing new makes zero network calls.
  * Scale: nothing here depends on there being 127 ids.

Usage (from the project folder):
    .venv\\Scripts\\python src\\fetch.py              # normal run (uses cache)
    .venv\\Scripts\\python src\\fetch.py --refresh    # ignore cache, download again
    .venv\\Scripts\\python src\\fetch.py --ids other_list.csv
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# ----------------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IDS = ROOT / "data" / "id_list.csv"
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

API_BASE = "https://api.themoviedb.org/3"
MIN_SECONDS_BETWEEN_REQUESTS = 0.1  # => at most ~10 requests/second
MAX_ATTEMPTS = 5                    # per request, before we give up and log a failure
TIMEOUT_SECONDS = 15

# Responses we are happy to store and re-use. 404 is stored too, so a rerun
# does not keep asking TMDb about an id we already know does not exist.
CACHEABLE_STATUS = {200, 404}


class AuthError(RuntimeError):
    """Raised when TMDb rejects the API key: no point continuing."""


# ----------------------------------------------------------------------------
# Part 1: read and classify every row of the id file
# ----------------------------------------------------------------------------
def read_id_list(path: Path) -> pd.DataFrame:
    """Return one row per line of the input file, with a classification.

    Everything is read as text first, so nothing is silently converted
    (e.g. 'N/A' turned into a missing value, or '155' and '155.0' merged).
    """
    # skip_blank_lines=False matters: by default pandas silently drops empty
    # lines, which would make a row of the client's list vanish unrecorded.
    raw = pd.read_csv(path, dtype=str, keep_default_na=False, skip_blank_lines=False)
    col = raw.columns[0]

    df = pd.DataFrame({
        "row_number": range(2, len(raw) + 2),   # matches the line number in the file (line 1 is the header)
        "raw_value": raw[col],
    })
    value = df["raw_value"].str.strip()

    is_blank = value.eq("")
    is_int = value.str.fullmatch(r"-?\d+")
    is_imdb = value.str.fullmatch(r"tt\d{7,}")
    as_number = pd.to_numeric(value.where(is_int), errors="coerce")

    df["kind"] = "not_an_id"                                   # e.g. 'N/A'
    df.loc[is_blank, "kind"] = "blank"
    df.loc[is_imdb, "kind"] = "imdb_id"
    df.loc[is_int & (as_number <= 0), "kind"] = "non_positive"  # e.g. -1
    df.loc[is_int & (as_number > 0), "kind"] = "tmdb_id"

    df["tmdb_id"] = as_number.where(df["kind"].eq("tmdb_id")).astype("Int64")
    return df


# ----------------------------------------------------------------------------
# Part 2: talking to TMDb politely
# ----------------------------------------------------------------------------
class TMDbClient:
    def __init__(self, key: str):
        self.session = requests.Session()
        self.session.headers["Accept"] = "application/json"
        self.params: dict[str, str] = {}
        # A v3 "API key" is 32 characters and goes in the URL; the longer v4
        # "read access token" goes in a header. Accept either. No key at all =
        # offline mode: saved data only.
        if not key:
            pass
        elif len(key) <= 40:
            self.params["api_key"] = key
        else:
            self.session.headers["Authorization"] = f"Bearer {key}"
        self._last_request = 0.0
        self.network_calls = 0

    def _wait_turn(self) -> None:
        wait = self._last_request + MIN_SECONDS_BETWEEN_REQUESTS - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.monotonic()

    def get(self, path: str, extra_params: dict | None = None) -> tuple[int | None, dict, int]:
        """Return (status_code, json_body, attempts). status_code None = gave up."""
        if not self.params and "Authorization" not in self.session.headers:
            raise AuthError(f"{path} is not in the saved data and no TMDB_API_KEY is set in .env, "
                            "so it cannot be downloaded.")
        params = {**self.params, **(extra_params or {})}
        last_error = "unknown"
        for attempt in range(1, MAX_ATTEMPTS + 1):
            self._wait_turn()
            self.network_calls += 1
            try:
                r = self.session.get(API_BASE + path, params=params, timeout=TIMEOUT_SECONDS)
            except requests.RequestException as exc:          # network hiccup, timeout ...
                last_error = type(exc).__name__
                time.sleep(2 ** attempt)
                continue

            if r.status_code == 401:
                raise AuthError("TMDb rejected the API key (401). Check TMDB_API_KEY in .env.")
            if r.status_code == 429:                          # too many requests: wait as told
                time.sleep(float(r.headers.get("Retry-After", 2 ** attempt)))
                last_error = "429 Too Many Requests"
                continue
            if r.status_code >= 500:                          # TMDb having a bad moment
                last_error = f"HTTP {r.status_code}"
                time.sleep(2 ** attempt)
                continue
            try:
                body = r.json()
            except ValueError:
                last_error = "response was not JSON"
                time.sleep(2 ** attempt)
                continue
            return r.status_code, body, attempt
        return None, {"error": last_error}, MAX_ATTEMPTS


# ----------------------------------------------------------------------------
# Part 3: cache on disk (one JSON file per request)
# ----------------------------------------------------------------------------
def cache_path(kind: str, key: str) -> Path:
    return RAW_DIR / kind / f"{key}.json"


def write_json_atomic(path: Path, payload: dict) -> None:
    """Write to a temp file then rename, so a crash never leaves half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def fetch_cached(client: TMDbClient, kind: str, key: str, path: str,
                 refresh: bool, extra_params: dict | None = None) -> dict:
    """Return a record {status_code, body, source, attempts, fetched_at}."""
    file = cache_path(kind, key)
    if file.exists() and not refresh:
        record = json.loads(file.read_text(encoding="utf-8"))
        if record.get("status_code") in CACHEABLE_STATUS:
            return {**record, "source": "cache", "attempts": 0}

    status, body, attempts = client.get(path, extra_params)
    record = {
        "request": path,
        "status_code": status,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "body": body,
    }
    if status in CACHEABLE_STATUS:
        write_json_atomic(file, record)
    return {**record, "source": "network", "attempts": attempts}


def outcome_of(status: int | None) -> str:
    return {200: "ok", 404: "not_found"}.get(status, "failed")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ids", type=Path, default=DEFAULT_IDS, help="CSV whose first column holds the ids")
    parser.add_argument("--refresh", action="store_true", help="ignore saved responses and download again")
    args = parser.parse_args(argv)

    load_dotenv(ROOT / ".env")
    key = os.getenv("TMDB_API_KEY", "").strip()
    if not key:
        if args.refresh:
            print("ERROR: --refresh needs TMDB_API_KEY. Copy .env.example to .env and add your key.")
            return 1
        print("No TMDB_API_KEY found: running from saved data only (data/raw). "
              "Anything not saved will be reported as an error.")

    started = time.perf_counter()
    client = TMDbClient(key)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # --- 1. classify every row -------------------------------------------
    audit = read_id_list(args.ids)
    print(f"Read {len(audit)} rows from {args.ids.name}")
    print(audit["kind"].value_counts().to_string(), "\n")

    # --- 2. translate IMDb ids (tt...) into TMDb ids ---------------------
    #     TMDb offers GET /find/{imdb_id}?external_source=imdb_id for this.
    imdb_rows = audit["kind"].eq("imdb_id")
    for idx in audit.index[imdb_rows]:
        imdb_id = audit.at[idx, "raw_value"].strip()
        rec = fetch_cached(client, "find", imdb_id, f"/find/{imdb_id}", args.refresh,
                           {"external_source": "imdb_id"})
        matches = (rec["body"] or {}).get("movie_results", []) if rec["status_code"] == 200 else []
        if len(matches) == 1:
            audit.at[idx, "tmdb_id"] = matches[0]["id"]
            print(f"  IMDb id {imdb_id} -> TMDb id {matches[0]['id']} ({matches[0].get('title')})")
        else:
            audit.at[idx, "kind"] = "imdb_id_unresolved"
            print(f"  IMDb id {imdb_id} could not be matched to exactly one TMDb movie")

    # --- 3. mark duplicates (keep the first time an id appears) ---------
    has_id = audit["tmdb_id"].notna()
    audit["is_duplicate"] = has_id & audit["tmdb_id"].duplicated(keep="first")
    unique_ids = audit.loc[has_id & ~audit["is_duplicate"], "tmdb_id"].astype(int).tolist()
    print(f"\nUnique usable TMDb ids to fetch: {len(unique_ids)}\n")

    # --- 4. fetch details + credits for each unique id -------------------
    log_rows = []
    try:
        for n, tmdb_id in enumerate(unique_ids, start=1):
            for endpoint, path in (("movie", f"/movie/{tmdb_id}"),
                                   ("credits", f"/movie/{tmdb_id}/credits")):
                rec = fetch_cached(client, endpoint, str(tmdb_id), path, args.refresh)
                body = rec["body"] if isinstance(rec["body"], dict) else {}
                log_rows.append({
                    "tmdb_id": tmdb_id,
                    "endpoint": endpoint,
                    "status_code": rec["status_code"],
                    "outcome": outcome_of(rec["status_code"]),
                    "returned_id": body.get("id"),
                    "source": rec["source"],
                    "attempts": rec["attempts"],
                    "fetched_at": rec.get("fetched_at"),
                    "error": body.get("error") or body.get("status_message"),
                })
            if n % 20 == 0 or n == len(unique_ids):
                print(f"  {n}/{len(unique_ids)} ids done ({client.network_calls} network calls so far)")
    except AuthError as exc:
        print(f"\nERROR: {exc}")
        return 1
    except KeyboardInterrupt:
        print("\nStopped by user. Everything downloaded so far is saved; just run again to continue.")
        return 1

    # --- 4b. fetch each franchise ("collection") once ------------------
    #     Needed to know whether the list holds the WHOLE franchise or only
    #     some of its films. One request per franchise, not per film.
    collection_ids = set()
    for tmdb_id in unique_ids:
        file = cache_path("movie", str(tmdb_id))
        if file.exists():
            body = json.loads(file.read_text(encoding="utf-8")).get("body") or {}
            coll = body.get("belongs_to_collection")
            if isinstance(coll, dict) and coll.get("id"):
                collection_ids.add(int(coll["id"]))
    try:
        for coll_id in sorted(collection_ids):
            rec = fetch_cached(client, "collection", str(coll_id), f"/collection/{coll_id}", args.refresh)
            body = rec["body"] if isinstance(rec["body"], dict) else {}
            log_rows.append({
                "tmdb_id": coll_id, "endpoint": "collection", "status_code": rec["status_code"],
                "outcome": outcome_of(rec["status_code"]), "returned_id": body.get("id"),
                "source": rec["source"], "attempts": rec["attempts"],
                "fetched_at": rec.get("fetched_at"), "error": body.get("error") or body.get("status_message"),
            })
    except AuthError as exc:
        print(f"\nERROR: {exc}")
        return 1
    print(f"  {len(collection_ids)} franchises (collections) checked")

    # --- 4c. details for franchise films that are NOT on the list --------
    #     A studio sells "all of it or none". To test whether the films the
    #     list leaves out would change a bundle's picture, fetch their
    #     details too (released films only). Kept apart in data/raw/movie_extra.
    on_list = set(unique_ids)
    extra_ids = set()
    for coll_id in collection_ids:
        file = cache_path("collection", str(coll_id))
        if file.exists():
            record = json.loads(file.read_text(encoding="utf-8"))
            body = record.get("body") or {}
            # "Released" means released by the date this franchise was fetched,
            # not by today: a rerun months later then gives the same answer
            # unless --refresh is used (same rule as build_tables.py).
            snapshot_day = (record.get("fetched_at") or "")[:10]
            for part in body.get("parts", []):
                date = part.get("release_date") or ""
                if date and date <= snapshot_day and part["id"] not in on_list:
                    extra_ids.add(int(part["id"]))
    try:
        for extra_id in sorted(extra_ids):
            rec = fetch_cached(client, "movie_extra", str(extra_id), f"/movie/{extra_id}", args.refresh)
            body = rec["body"] if isinstance(rec["body"], dict) else {}
            log_rows.append({
                "tmdb_id": extra_id, "endpoint": "movie_extra", "status_code": rec["status_code"],
                "outcome": outcome_of(rec["status_code"]), "returned_id": body.get("id"),
                "source": rec["source"], "attempts": rec["attempts"],
                "fetched_at": rec.get("fetched_at"), "error": body.get("error") or body.get("status_message"),
            })
    except AuthError as exc:
        print(f"\nERROR: {exc}")
        return 1
    print(f"  {len(extra_ids)} released franchise films not on the list checked")

    log = pd.DataFrame(log_rows)
    log.to_csv(PROCESSED_DIR / "fetch_log.csv", index=False)

    # --- 5. final fate of every input row -------------------------------
    film_log = log[log["endpoint"].isin(["movie", "credits"])]
    details = log[log["endpoint"].eq("movie")].set_index("tmdb_id")["outcome"]
    credits = log[log["endpoint"].eq("credits")].set_index("tmdb_id")["outcome"]
    audit["details_outcome"] = audit["tmdb_id"].map(details)
    audit["credits_outcome"] = audit["tmdb_id"].map(credits)

    audit["fate"] = audit["kind"]                                   # blank / not_an_id / non_positive / imdb_id_unresolved
    usable = audit["tmdb_id"].notna()
    audit.loc[usable & audit["is_duplicate"], "fate"] = "duplicate"
    first = usable & ~audit["is_duplicate"]
    audit.loc[first & audit["details_outcome"].eq("not_found"), "fate"] = "not_found_on_tmdb"
    audit.loc[first & audit["details_outcome"].eq("failed"), "fate"] = "fetch_failed"
    audit.loc[first & audit["details_outcome"].eq("ok") & audit["credits_outcome"].ne("ok"), "fate"] = "credits_missing"
    audit.loc[first & audit["details_outcome"].eq("ok") & audit["credits_outcome"].eq("ok"), "fate"] = "fetched"
    audit.to_csv(PROCESSED_DIR / "id_audit.csv", index=False)

    # --- 6. reconciliation: totals must add up --------------------------
    fate_counts = audit["fate"].value_counts()
    assert fate_counts.sum() == len(audit), "every input row must have exactly one fate"
    assert len(film_log) == 2 * len(unique_ids), "every unique id must have one details and one credits record"

    mismatched = log[log["outcome"].eq("ok") & log["returned_id"].ne(log["tmdb_id"])]
    elapsed = time.perf_counter() - started

    print("\n=== Reconciliation: fate of every row in the input file ===")
    print(fate_counts.to_string())
    print(f"TOTAL{fate_counts.sum():>24}  (input rows: {len(audit)})")
    print(f"\nNetwork calls this run: {client.network_calls}   "
          f"Re-used from disk: {(log['source'] == 'cache').sum()}   "
          f"Time: {elapsed:.1f}s")
    if len(mismatched):
        print(f"WARNING: {len(mismatched)} responses came back with a different id than requested; see fetch_log.csv")
    failed = log["outcome"].eq("failed").sum()
    if failed:
        print(f"WARNING: {failed} requests failed after {MAX_ATTEMPTS} attempts. Run again to retry just those.")
    print("\nWrote data/processed/id_audit.csv and data/processed/fetch_log.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
