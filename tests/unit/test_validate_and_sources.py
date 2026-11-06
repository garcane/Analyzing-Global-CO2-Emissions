import csv
from pathlib import Path

import pytest

from ingestion.config import DATA_DIR, mask_secret
from ingestion.sources import SOURCES, SourceSpec, raw_column_name
from ingestion.validate import ValidationError, validate_csv

SPEC = SourceSpec(
    name="t", schema="S", table="T", columns=["Area", "Year", "Value"], filename="t.csv",
    year_column="Year", year_min=1985, year_max=2100, key_columns=("Area", "Year"),
)


def write(tmp_path: Path, rows: list[list[str]]) -> Path:
    p = tmp_path / "t.csv"
    with p.open("w", encoding="utf-8", newline="") as fh:
        csv.writer(fh, lineterminator="\n").writerows(rows)
    return p


def test_valid_file(tmp_path):
    r = validate_csv(write(tmp_path, [["Area", "Year", "Value"], ["X", "2000", "1.5"], ["Y", "2020", ""]]), SPEC)
    assert (r.rows, r.year_min, r.year_max) == (2, 2000, 2020)


def test_changed_header_fails_before_load(tmp_path):
    p = write(tmp_path, [["Area", "Year", "Value (TWh)"], ["X", "2000", "1"]])
    with pytest.raises(ValidationError, match="header differs"):
        validate_csv(p, SPEC)


def test_reordered_header_is_reported(tmp_path):
    p = write(tmp_path, [["Year", "Area", "Value"], ["2000", "X", "1"]])
    with pytest.raises(ValidationError, match="different order"):
        validate_csv(p, SPEC)


def test_empty_file_and_no_rows(tmp_path):
    (tmp_path / "t.csv").write_text("", encoding="utf-8")
    with pytest.raises(ValidationError, match="empty"):
        validate_csv(tmp_path / "t.csv", SPEC)
    with pytest.raises(ValidationError, match="no data rows"):
        validate_csv(write(tmp_path, [["Area", "Year", "Value"]]), SPEC)


@pytest.mark.parametrize(
    "row,msg",
    [(["", "2000", "1"], "empty key"), (["X", "abc", "1"], "non-integer"), (["X", "1900", "1"], "outside")],
)
def test_bad_rows(tmp_path, row, msg):
    with pytest.raises(ValidationError, match=msg):
        validate_csv(write(tmp_path, [["Area", "Year", "Value"], row]), SPEC)


def test_wrong_field_count(tmp_path):
    with pytest.raises(ValidationError, match="fields"):
        validate_csv(write(tmp_path, [["Area", "Year", "Value"], ["X", "2000"]]), SPEC)


def test_raw_column_names():
    assert raw_column_name("Generation (TWh)") == "generation_twh"
    assert raw_column_name("Emissions intensity (gCO2e/kWh)") == "emissions_intensity_gco2e_kwh"


@pytest.mark.parametrize("name", list(SOURCES))
def test_raw_column_names_unique(name):
    cols = SOURCES[name].raw_columns
    assert len(cols) == len(set(cols))


@pytest.mark.parametrize("name,rows", [("ember_yearly_csv", 104256), ("owid_co2_csv", 50191)])
def test_committed_files_pass_validation(name, rows):
    spec = SOURCES[name]
    path = DATA_DIR / spec.filename
    if not path.exists():
        pytest.skip("data file not present")
    assert validate_csv(path, spec).rows == rows


def test_mask_secret():
    assert "SECRET" not in mask_secret("GET https://x/y?api_key=SECRET&a=1 failed SECRET", "SECRET")
    assert mask_secret("nothing", "") == "nothing"
