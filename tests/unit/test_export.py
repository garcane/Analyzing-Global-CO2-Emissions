from datetime import date
from decimal import Decimal

import pytest

from ingestion.config import ConfigError, SnowflakeSettings
from ingestion.export import EXPORTS, export_table, format_cell


class Cur:
    def __init__(self, rows, count=None):
        self.description = [("GEOGRAPHY_KEY",), ("YEAR",), ("SHARE",), ("FLAG",)]
        self.rows, self.count, self._last = rows, len(rows) if count is None else count, ""

    def execute(self, sql, params=None):
        self._last = sql

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return (self.count,)


def test_format_cell():
    assert format_cell(None) == ""
    assert format_cell(True) == "true"
    assert format_cell(Decimal("9402.742000")) == "9402.742"
    assert format_cell(Decimal("100.000000")) == "100"
    assert format_cell(Decimal("-0.000000")) == "0"
    assert format_cell(date(2020, 1, 2)) == "2020-01-02"
    assert format_cell("Côte d'Ivoire") == "Côte d'Ivoire"


def test_export_writes_header_rows_and_nulls(tmp_path):
    rows = [("DEU", 2023, Decimal("54.7000"), True), ("USA", 2023, None, False)]
    n = export_table(Cur(rows), "GEI_ANALYTICS", "MART_X", "geography_key", tmp_path)
    assert n == 2
    lines = (tmp_path / "mart_x.csv").read_text(encoding="utf-8").splitlines()
    assert lines == ["geography_key,year,share,flag", "DEU,2023,54.7,true", "USA,2023,,false"]


def test_export_fails_if_row_count_differs(tmp_path):
    with pytest.raises(RuntimeError, match="fetched 1 rows"):
        export_table(Cur([("DEU", 2023, None, True)], count=2), "GEI_ANALYTICS", "T", "geography_key", tmp_path)


def test_exports_cover_the_power_bi_tables():
    assert {t for t, _ in EXPORTS} == {
        "DIM_GEOGRAPHY", "DIM_ENERGY_SOURCE", "FCT_GENERATION_BY_SOURCE",
        "MART_COUNTRY_ENERGY_PROFILE", "MART_RENEWABLE_GROWTH", "MART_ENERGY_TRANSITION",
    }


def test_reporter_settings_use_reporter_vars_and_refuse_admin(monkeypatch, tmp_path):
    monkeypatch.setattr("ingestion.config.load_dotenv", lambda *_a, **_k: None)
    env = {"SNOWFLAKE_ACCOUNT": "A-B", "REPORTER_SNOWFLAKE_USER": "R", "REPORTER_SNOWFLAKE_PRIVATE_KEY_PATH": str(tmp_path / "k")}
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("REPORTER_SNOWFLAKE_ROLE", raising=False)
    monkeypatch.delenv("GEI_ANALYTICS_DATABASE", raising=False)
    s = SnowflakeSettings.for_reporter()
    assert (s.user, s.role, s.database, s.authenticator) == ("R", "GEI_REPORTER", "GEI_ANALYTICS", "keypair")
    monkeypatch.setenv("REPORTER_SNOWFLAKE_ROLE", "ACCOUNTADMIN")
    with pytest.raises(ConfigError, match="Refusing"):
        SnowflakeSettings.for_reporter()


def test_reporter_requires_its_variables(monkeypatch):
    monkeypatch.setattr("ingestion.config.load_dotenv", lambda *_a, **_k: None)
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "A-B")
    monkeypatch.delenv("REPORTER_SNOWFLAKE_USER", raising=False)
    with pytest.raises(ConfigError, match="REPORTER_SNOWFLAKE_USER"):
        SnowflakeSettings.for_reporter()
