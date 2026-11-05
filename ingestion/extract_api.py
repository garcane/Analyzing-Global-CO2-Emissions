"""Ember API extractor. Writes flat CSVs that go through the same validate/load path as file sources.

Facts used (OpenAPI spec https://api.ember-energy.org/v1/openapi.json, read 2026-11-05):
- auth is an `api_key` query parameter; no pagination; no rate limit documented;
- responses look like {"stats": {...}, "data": [ {...}, ... ]}.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import requests

from ingestion.config import API_DIR, ember_api_key
from ingestion.extract import ExtractError, FetchedFile, http_get, sha256_file, utcnow
from ingestion.sources import EMBER_API_BASE, EMBER_API_ENDPOINTS, SourceSpec


def fetch_rows(
    path: str,
    api_key: str,
    *,
    start_date: str = "2000",
    base_url: str = EMBER_API_BASE,
    session: requests.Session | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    resp = http_get(
        base_url + path,
        params={"start_date": start_date, "api_key": api_key},
        session=session,
        secret=api_key,
        **kwargs,
    )
    try:
        payload = resp.json()
    except ValueError:
        raise ExtractError(f"{path}: response is not JSON") from None
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        raise ExtractError(f"{path}: response has no 'data' list")
    return data


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def write_api_csv(rows: list[dict[str, Any]], spec: SourceSpec, dest: Path) -> FetchedFile:
    """Flatten API rows to the spec's exact column order. Unknown fields fail loudly (schema change)."""
    expected = set(spec.columns)
    for row in rows:
        unknown = set(row) - expected
        if unknown:
            raise ExtractError(
                f"{spec.name}: API returned unexpected fields {sorted(unknown)}; update ingestion/sources.py"
            )
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(spec.columns)
        for row in rows:
            writer.writerow([_cell(row.get(c)) for c in spec.columns])
    return FetchedFile(dest, sha256_file(dest), dest.stat().st_size, utcnow(), EMBER_API_BASE)


def extract_all(start_date: str = "2000", session: requests.Session | None = None):
    """Fetch every configured yearly endpoint; yields (spec, FetchedFile)."""
    key = ember_api_key()
    for spec, path in EMBER_API_ENDPOINTS:
        rows = fetch_rows(path, key, start_date=start_date, session=session)
        yield spec, write_api_csv(rows, spec, API_DIR / spec.filename)
