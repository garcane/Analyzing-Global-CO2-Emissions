import pytest
import requests

from ingestion.extract import ExtractError, download_file, http_get, sha256_file
from ingestion.extract_api import fetch_rows, write_api_csv
from ingestion.sources import EMBER_API_DEMAND


class Resp:
    def __init__(self, status=200, body=b"", json_data=None):
        self.status_code = status
        self._body = body
        self._json = json_data

    def iter_content(self, chunk_size):
        yield self._body

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json

    def close(self):
        pass


class Session:
    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def get(self, url, params=None, stream=False, timeout=None):
        self.calls += 1
        out = self.outcomes.pop(0)
        if isinstance(out, Exception):
            raise out
        return out


NOSLEEP = lambda s: None


def test_retries_5xx_then_succeeds():
    s = Session(Resp(503), Resp(200))
    assert http_get("http://x", session=s, sleep=NOSLEEP).status_code == 200
    assert s.calls == 2


def test_does_not_retry_4xx():
    s = Session(Resp(404), Resp(200))
    with pytest.raises(ExtractError, match="not retried"):
        http_get("http://x", session=s, sleep=NOSLEEP)
    assert s.calls == 1


def test_gives_up_after_bounded_retries():
    s = Session(Resp(500), Resp(500), Resp(500))
    with pytest.raises(ExtractError, match="3 attempts"):
        http_get("http://x", session=s, sleep=NOSLEEP)


def test_api_key_never_leaks_in_errors():
    err = requests.ConnectionError("failed for https://api/x?api_key=SECRETKEY&start_date=2000")
    s = Session(err, err, err)
    with pytest.raises(ExtractError) as info:
        http_get("http://x", session=s, sleep=NOSLEEP, secret="SECRETKEY")
    assert "SECRETKEY" not in str(info.value)

    s = Session(Resp(403))
    with pytest.raises(ExtractError) as info:
        http_get("http://x?api_key=SECRETKEY", session=s, sleep=NOSLEEP, secret="SECRETKEY")
    assert "SECRETKEY" not in str(info.value)


def test_download_writes_file_and_hash(tmp_path):
    dest = tmp_path / "f.csv"
    f = download_file("http://x", dest, session=Session(Resp(200, b"a,b\n1,2\n")), sleep=NOSLEEP)
    assert dest.read_bytes() == b"a,b\n1,2\n"
    assert f.sha256 == sha256_file(dest)
    assert not (tmp_path / "f.csv.part").exists()


def test_failed_download_leaves_no_file(tmp_path):
    dest = tmp_path / "f.csv"
    with pytest.raises(ExtractError):
        download_file("http://x", dest, session=Session(Resp(500), Resp(500), Resp(500)), sleep=NOSLEEP)
    assert not dest.exists()


def test_fetch_rows_requires_data_list():
    with pytest.raises(ExtractError, match="no 'data'"):
        fetch_rows("/p", "k", session=Session(Resp(200, json_data={"stats": {}})), sleep=NOSLEEP)
    rows = fetch_rows("/p", "k", session=Session(Resp(200, json_data={"data": [{"a": 1}]})), sleep=NOSLEEP)
    assert rows == [{"a": 1}]


def test_write_api_csv_order_booleans_and_unknown_fields(tmp_path):
    row = {"entity": "France", "entity_code": "FRA", "is_aggregate_entity": False, "date": "2020",
           "demand_twh": 450.1, "demand_kwh_per_capita": None}
    f = write_api_csv([row], EMBER_API_DEMAND, tmp_path / "d.csv")
    lines = f.path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == ",".join(EMBER_API_DEMAND.columns)
    assert lines[1] == "France,FRA,false,2020,450.1,"
    with pytest.raises(ExtractError, match="unexpected fields"):
        write_api_csv([{**row, "new_field": 1}], EMBER_API_DEMAND, tmp_path / "e.csv")
