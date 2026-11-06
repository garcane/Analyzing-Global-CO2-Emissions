"""Contract between the loader's RAW column names and the dbt staging models.

The first dbt build failed because a staging model read `share_of_generation_pct` while the loader (which
drops the "%" sign) created `share_of_generation`. This test catches that class of mistake offline.
"""

import re
from pathlib import Path

import pytest

from ingestion.sources import SOURCES

STAGING = Path(__file__).resolve().parents[2] / "dbt" / "models" / "staging"
# RAW tables also carry these loader metadata columns.
META = {"_load_id", "_source_file", "_file_sha256", "_downloaded_at_utc", "_loaded_at_utc", "_source_row_number"}
IGNORE = {
    "select", "from", "as", "int", "nullif", "try_to_number", "try_to_decimal", "try_to_boolean",
    "try_to_double", "case", "when", "then", "else", "end", "null",
}


def referenced_columns(sql: str) -> set[str]:
    """Identifiers in the SELECT list that are source columns (not aliases, functions or literals)."""
    sql = re.sub(r"--[^\n]*", "", sql)            # comments
    sql = re.sub(r"\{\{.*?\}\}", " ", sql, flags=re.DOTALL)  # jinja
    sql = re.sub(r"'[^']*'", "''", sql)          # string literals
    select_list = re.search(r"\bselect\b(.*?)\bfrom\b", sql, flags=re.DOTALL | re.IGNORECASE).group(1)
    select_list = re.sub(r"\bas\s+[a-z_][a-z0-9_]*", " ", select_list, flags=re.IGNORECASE)  # drop aliases
    tokens = re.findall(r"\b[a-z_][a-z0-9_]*\b", select_list.lower())
    return {t for t in tokens if t not in IGNORE}


def test_detects_the_bug_that_broke_the_first_build():
    bad = "select try_to_decimal(share_of_generation_pct, 18, 6) as share_of_generation_pct from {{ x }}"
    assert "share_of_generation_pct" in referenced_columns(bad)
    assert "share_of_generation_pct" not in set(SOURCES["ember_yearly_csv"].raw_columns)


@pytest.mark.parametrize("path", sorted(STAGING.glob("stg_*.sql")), ids=lambda p: p.name)
def test_staging_columns_exist_in_raw_table(path):
    sql = path.read_text(encoding="utf-8")
    source_name = re.search(r"from_latest_load\(.*?\)\s*,\s*'([a-z0-9_]+)'\)", sql.replace("\n", " ")).group(1)
    available = set(SOURCES[source_name].raw_columns) | META
    missing = referenced_columns(sql) - available
    assert not missing, f"{path.name} reads columns that RAW does not have: {sorted(missing)}"
