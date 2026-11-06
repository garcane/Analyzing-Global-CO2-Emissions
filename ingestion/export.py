"""Export the reporting tables to CSV for Power BI (and as a Snowflake-independent copy of the results).

    uv run python -m ingestion.export                         # as GEI_REPORTER_SVC (read-only, MARTS only)
    uv run python -m ingestion.export --use-dbt-credentials   # interim: the dbt user

Reads GEI_ANALYTICS.MARTS (production build). Files are written to data/exports/ with a stable column
and row order so reruns only produce a git diff when the data changed.
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from ingestion.config import DATA_DIR, ConfigError, SnowflakeSettings

log = logging.getLogger("ingestion.export")
EXPORT_DIR = DATA_DIR / "exports"

# (table in MARTS, ORDER BY). Only what the Power BI model uses.
EXPORTS: list[tuple[str, str]] = [
    ("DIM_GEOGRAPHY", "geography_key"),
    ("DIM_ENERGY_SOURCE", "source_key"),
    ("FCT_GENERATION_BY_SOURCE", "geography_key, year, source_key"),
    ("MART_COUNTRY_ENERGY_PROFILE", "geography_key, year"),
    ("MART_RENEWABLE_GROWTH", "geography_key, series, year"),
    ("MART_ENERGY_TRANSITION", "geography_key"),
]


def format_cell(value: Any) -> str:
    """CSV text for one value: empty for NULL, plain decimals (no exponent, no trailing zeros)."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Decimal):
        text = format(value.normalize(), "f")
        return "0" if text in ("-0", "") else text
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def export_table(cur: Any, database: str, table: str, order_by: str, out_dir: Path) -> int:
    cur.execute(f"SELECT * FROM {database}.MARTS.{table} ORDER BY {order_by}")
    columns = [d[0].lower() for d in cur.description]
    rows = cur.fetchall()
    cur.execute(f"SELECT COUNT(*) FROM {database}.MARTS.{table}")
    expected = cur.fetchone()[0]
    if len(rows) != expected:
        raise RuntimeError(f"{table}: fetched {len(rows)} rows but the table has {expected}")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{table.lower()}.csv"
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(columns)
        for row in rows:
            writer.writerow([format_cell(v) for v in row])
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ingestion.export")
    parser.add_argument("--use-dbt-credentials", action="store_true",
                        help="use the DBT_SNOWFLAKE_* user instead of the reporter user (interim)")
    parser.add_argument("--out-dir", type=Path, default=EXPORT_DIR)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    try:
        import truststore

        truststore.inject_into_ssl()
    except ImportError:
        pass

    from ingestion.load import connect

    try:
        settings = SnowflakeSettings.for_reporter(use_dbt_credentials=args.use_dbt_credentials)
    except ConfigError as exc:
        log.error("%s", exc)
        return 2

    conn = connect(settings)
    try:
        cur = conn.cursor()
        log.info("exporting as %s (role %s) from %s.MARTS", settings.user, settings.role, settings.database)
        for table, order_by in EXPORTS:
            n = export_table(cur, settings.database, table, order_by, args.out_dir)
            log.info("%s: %d rows", table.lower(), n)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
