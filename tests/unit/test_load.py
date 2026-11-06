from datetime import datetime

import pytest

from ingestion import load
from ingestion.extract import FetchedFile
from ingestion.sources import EMBER_YEARLY_CSV, OWID_CO2_CSV
from ingestion.validate import ValidationResult


class FakeCursor:
    """Records SQL. `latest_sha` answers the idempotency lookup; `loaded` answers the row count."""

    def __init__(self, latest_sha=None, loaded=3, fail_on=None):
        self.sql: list[str] = []
        self.latest_sha, self.loaded, self.fail_on = latest_sha, loaded, fail_on
        self._last = ""

    def execute(self, sql, params=None):
        self._last = sql
        self.sql.append(" ".join(sql.split()))
        if self.fail_on and self.fail_on in sql:
            raise RuntimeError("boom")

    def fetchone(self):
        if "LATEST_SUCCESSFUL_LOAD WHERE" in self._last:
            return (self.latest_sha,) if self.latest_sha else None
        return (self.loaded,)

    def close(self):
        pass


class FakeConn:
    def __init__(self, cur):
        self.cur = cur

    def cursor(self):
        return self.cur


def fetched(tmp_path, sha="abc"):
    p = tmp_path / "f.csv"
    p.write_text("x", encoding="utf-8")
    return FetchedFile(p, sha, 1, datetime(2026, 1, 1), "http://u")


def statements(cur, prefix):
    return [s for s in cur.sql if s.startswith(prefix)]


def test_same_hash_is_a_noop(tmp_path):
    cur = FakeCursor(latest_sha="abc")
    res = load.load_file(FakeConn(cur), "RAW", EMBER_YEARLY_CSV, fetched(tmp_path), ValidationResult(3, 2000, 2001))
    assert res.status == "skipped"
    assert not statements(cur, "PUT") and not statements(cur, "COPY") and not statements(cur, "INSERT")


def test_new_hash_loads_and_marks_success(tmp_path):
    cur = FakeCursor(latest_sha="older")
    res = load.load_file(FakeConn(cur), "RAW", EMBER_YEARLY_CSV, fetched(tmp_path), ValidationResult(3, 2000, 2001))
    assert (res.status, res.rows) == ("loaded", 3)
    assert statements(cur, "PUT") and statements(cur, "COPY INTO RAW.EMBER.GENERATION_YEARLY")
    assert any(s.startswith("UPDATE") and "STATUS = 'SUCCESS'" in s for s in cur.sql)
    assert not any(s.startswith("UPDATE") and "'FAILED'" in s for s in cur.sql)


def test_row_count_mismatch_fails_and_cleans_up(tmp_path):
    cur = FakeCursor(loaded=2)
    with pytest.raises(load.LoadError, match="Loaded 2 rows"):
        load.load_file(FakeConn(cur), "RAW", EMBER_YEARLY_CSV, fetched(tmp_path), ValidationResult(3, 2000, 2001))
    assert statements(cur, "DELETE FROM RAW.EMBER.GENERATION_YEARLY")
    assert any(s.startswith("UPDATE") and "STATUS = 'FAILED'" in s for s in cur.sql)
    assert not any(s.startswith("UPDATE") and "STATUS = 'SUCCESS'" in s for s in cur.sql)


def test_copy_failure_cleans_up_and_reraises(tmp_path):
    cur = FakeCursor(fail_on="COPY INTO")
    with pytest.raises(RuntimeError, match="boom"):
        load.load_file(FakeConn(cur), "RAW", EMBER_YEARLY_CSV, fetched(tmp_path), ValidationResult(3, 2000, 2001))
    assert any("STATUS = 'FAILED'" in s for s in cur.sql)


def test_copy_sql_shape(tmp_path):
    sql = load.copy_sql("RAW", OWID_CO2_CSV, fetched(tmp_path), "LOADID", datetime(2026, 1, 2))
    assert f"${len(OWID_CO2_CSV.columns)}" in sql and f"${len(OWID_CO2_CSV.columns) + 1}" not in sql
    assert "'LOADID'" in sql and "ON_ERROR = ABORT_STATEMENT" in sql and "SKIP_HEADER = 1" in sql
    assert "@RAW.META.INGEST_STAGE/owid_co2_csv/LOADID/" in sql


def test_raw_table_is_all_varchar_plus_metadata(tmp_path):
    cur = FakeCursor()
    load.ensure_objects(cur, "RAW", EMBER_YEARLY_CSV)
    ddl = statements(cur, "CREATE TABLE IF NOT EXISTS RAW.EMBER.GENERATION_YEARLY")[0]
    assert "GENERATION_TWH VARCHAR" in ddl and "_LOAD_ID VARCHAR" in ddl and "NUMBER" in ddl
