"""Command line entry point.

    uv run python -m ingestion.cli ember_yearly_csv --dry-run     # validate only, no Snowflake
    uv run python -m ingestion.cli owid_co2_csv                   # load data/owid-co2-data.csv
    uv run python -m ingestion.cli ember_yearly_csv --download    # re-download first, then load
    uv run python -m ingestion.cli ember_api                      # fetch Ember API, then load
"""

from __future__ import annotations

import argparse
import logging
import sys

from ingestion.config import DATA_DIR, ConfigError, SnowflakeSettings
from ingestion.extract import ExtractError, FetchedFile, describe_local_file, download_file
from ingestion.extract_api import extract_all
from ingestion.sources import SOURCES, SourceSpec
from ingestion.validate import ValidationError, ValidationResult, validate_csv

log = logging.getLogger("ingestion")
FILE_SOURCES = ["ember_yearly_csv", "owid_co2_csv"]


def _plan(args: argparse.Namespace) -> list[tuple[SourceSpec, FetchedFile]]:
    """Resolve the files to load. Download/fetch errors surface here, before any Snowflake call."""
    if args.source == "ember_api":
        return list(extract_all(start_date=args.start_date))
    spec = SOURCES[args.source]
    path = DATA_DIR / spec.filename
    fetched = download_file(spec.url, path) if args.download else describe_local_file(path, spec.url)
    return [(spec, fetched)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ingestion")
    parser.add_argument("source", choices=FILE_SOURCES + ["ember_api"])
    parser.add_argument("--download", action="store_true", help="re-download a file source first")
    parser.add_argument("--dry-run", action="store_true", help="validate only; do not touch Snowflake")
    parser.add_argument("--start-date", default="2000", help="first year for the Ember API (default 2000)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # Use the operating system's certificate store so networks that inspect TLS (corporate proxy,
    # antivirus) work. Harmless elsewhere; certificate verification stays on.
    try:
        import truststore

        truststore.inject_into_ssl()
    except ImportError:
        pass

    try:
        plan = _plan(args)
        validated: list[tuple[SourceSpec, FetchedFile, ValidationResult]] = []
        for spec, fetched in plan:
            result = validate_csv(fetched.path, spec)
            log.info("%s: %d rows, years %s-%s, sha256 %s...", spec.name, result.rows, result.year_min,
                     result.year_max, fetched.sha256[:12])
            validated.append((spec, fetched, result))

        if args.dry_run:
            log.info("dry run: nothing loaded")
            return 0

        from ingestion.load import connect, load_file

        settings = SnowflakeSettings.from_env()
        conn = connect(settings)
        try:
            for spec, fetched, result in validated:
                outcome = load_file(conn, settings.database, spec, fetched, result)
                log.info("%s: %s (%d rows)", spec.name, outcome.status, outcome.rows)
        finally:
            conn.close()
    except (ConfigError, ExtractError, ValidationError) as exc:
        log.error("%s", exc)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
