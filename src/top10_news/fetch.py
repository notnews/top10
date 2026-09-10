"""Retrieve a specified Wayback capture, retaining its response URL."""

import gzip
import json
import re
from datetime import UTC, datetime
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_CAPTURE = re.compile(r"https?://web\.archive\.org/web/\d{14}(?:[a-z_]+)?/https?://.+")


def fetch_snapshot(url: str, output: Path, *, session=None) -> dict:
    """Save one known capture atomically; reject redirects out of Wayback replay."""
    if not _CAPTURE.fullmatch(url):
        raise ValueError(
            "provide a full Wayback replay URL with a 14-digit capture timestamp"
        )
    if session is None:
        session = requests.Session()
        session.headers["User-Agent"] = (
            "top10-news/1.0 (+https://github.com/notnews/top10)"
        )
        retry = Retry(
            total=2, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
        )
        session.mount("https://", HTTPAdapter(max_retries=retry))
        session.mount("http://", HTTPAdapter(max_retries=retry))
    response = session.get(url, timeout=30)
    response.raise_for_status()
    if not _CAPTURE.fullmatch(response.url) or not response.content.strip():
        raise ValueError(
            "response is empty or redirected outside a timestamped Wayback capture"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".part")
    metadata_path = output.with_name(output.name + ".metadata.json")
    metadata_part = metadata_path.with_name(metadata_path.name + ".part")
    metadata = {
        "requested_url": url,
        "response_url": response.url,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "status": response.status_code,
    }
    try:
        temporary.write_bytes(gzip.compress(response.content, mtime=0))
        metadata_part.write_text(
            json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
        )
        temporary.replace(output)
        metadata_part.replace(metadata_path)
    finally:
        temporary.unlink(missing_ok=True)
        metadata_part.unlink(missing_ok=True)
    return metadata
