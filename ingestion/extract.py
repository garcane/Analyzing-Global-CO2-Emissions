"""Download files (retry/backoff/timeout) and fingerprint them. No Snowflake code here."""

from __future__ import annotations

import hashlib
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from ingestion.config import mask_secret

log = logging.getLogger(__name__)

RETRY_STATUS = {429, 500, 502, 503, 504}


class ExtractError(RuntimeError):
    pass


@dataclass(frozen=True)
class FetchedFile:
    path: Path
    sha256: str
    size_bytes: int
    downloaded_at_utc: datetime  # naive UTC
    source_url: str | None


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def describe_local_file(path: Path, url: str | None = None) -> FetchedFile:
    """Fingerprint an existing file. The file's mtime stands in for the download time."""
    if not path.is_file():
        raise ExtractError(f"File not found: {path}")
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).replace(tzinfo=None)
    return FetchedFile(path, sha256_file(path), path.stat().st_size, mtime, url)


def http_get(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    stream: bool = False,
    timeout: float = 120,
    retries: int = 3,
    backoff: float = 2.0,
    session: requests.Session | None = None,
    sleep: Callable[[float], None] = time.sleep,
    secret: str = "",
) -> requests.Response:
    """GET with bounded retries and exponential backoff.

    Retries connection errors, timeouts and 429/5xx; never retries other 4xx. Any message that leaves
    this function has `secret` (e.g. an API key sent as a query parameter) masked out, and the original
    exception is not chained, so the key cannot appear in a traceback.
    """
    sess = session or requests.Session()
    last = "no attempt made"
    for attempt in range(1, retries + 1):
        try:
            resp = sess.get(url, params=params, stream=stream, timeout=timeout)
        except (requests.ConnectionError, requests.Timeout) as exc:
            last = f"{type(exc).__name__}: {mask_secret(str(exc), secret)}"
        except requests.RequestException as exc:
            raise ExtractError(f"Request failed: {mask_secret(str(exc), secret)}") from None
        else:
            if resp.status_code < 400:
                return resp
            if resp.status_code not in RETRY_STATUS:
                raise ExtractError(f"HTTP {resp.status_code} from {mask_secret(url, secret)} (not retried)")
            last = f"HTTP {resp.status_code}"
        if attempt < retries:
            delay = backoff ** (attempt - 1)
            log.warning("GET failed (%s), attempt %d/%d, retrying in %.1fs", last, attempt, retries, delay)
            sleep(delay)
    raise ExtractError(f"GET failed after {retries} attempts: {last}")


def download_file(
    url: str,
    dest: Path,
    *,
    session: requests.Session | None = None,
    sleep: Callable[[float], None] = time.sleep,
    **kwargs: Any,
) -> FetchedFile:
    """Download to `dest` via a temporary .part file so a failed download never leaves a partial file."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    resp = http_get(url, stream=True, session=session, sleep=sleep, **kwargs)
    try:
        with part.open("wb") as fh:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                fh.write(chunk)
        part.replace(dest)
    finally:
        part.unlink(missing_ok=True)
        resp.close()
    return FetchedFile(dest, sha256_file(dest), dest.stat().st_size, utcnow(), url)
