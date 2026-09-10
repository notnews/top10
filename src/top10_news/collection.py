"""Parse local captures with resumable observation-level checkpoints."""

import gzip
import hashlib
import json
import logging
import re
from datetime import date, time
from pathlib import Path

from top10_news.checkpoint import prepare_checkpoint
from top10_news.convert import read_records
from top10_news.parsers import parse_nyt_jsonp, parse_page

log = logging.getLogger(__name__)


def capture_time(
    path: Path, day: str | None, clock: str | None
) -> tuple[str, str | None]:
    """Read capture date/time without guessing a timezone."""
    match = re.search(r"_(\d{8})_?(\d{6})\.(?:html|json|jsonp)(?:\.gz)?$", path.name)
    day = day or (match[1] if match else None)
    clock = clock or (match[2] if match else None)
    if not day:
        raise ValueError(
            "capture date missing: provide --date or a dated historical filename"
        )
    return date.fromisoformat(day).isoformat(), time.fromisoformat(
        clock
    ).isoformat() if clock else None


def parse_files(
    paths: list[Path],
    output: Path,
    *,
    site: str,
    kind: str,
    day: str | None = None,
    clock: str | None = None,
    resume: bool = False,
    base_url: str | None = None,
) -> tuple[int, int]:
    """Append distinct observations, recording per-file failures for retry."""
    if any(path.resolve() == output.resolve() for path in paths):
        raise ValueError("output must differ from input paths")
    output.parent.mkdir(parents=True, exist_ok=True)
    completed = set()
    if resume:
        prepare_checkpoint(output)
        if output.exists():
            completed = {row["record_id"] for row in read_records(output)}
    count = failures = 0
    failure_path = output.with_suffix(".failures.jsonl")
    with (
        output.open("a" if resume else "w", encoding="utf-8") as handle,
        failure_path.open("a" if resume else "w", encoding="utf-8") as errors,
    ):
        for path in paths:
            try:
                day_value, clock_value = capture_time(path, day, clock)
                payload = (
                    gzip.decompress(path.read_bytes())
                    if path.suffix == ".gz"
                    else path.read_bytes()
                )
                digest = hashlib.sha256(payload).hexdigest()
                if kind == "nyt_jsonp":
                    if site != "nyt":
                        raise ValueError("nyt_jsonp requires --site nyt")
                    rows = parse_nyt_jsonp(payload)
                else:
                    rows = parse_page(
                        payload,
                        site=site,
                        year=int(day_value[:4]),
                        kind=kind,
                        base_url=base_url,
                    )
                for row in rows:
                    row.update(
                        site=site,
                        list_kind=kind,
                        observed_date=day_value,
                        observed_time=clock_value,
                        position_kind="response_order"
                        if kind == "nyt_jsonp"
                        else "document_order",
                        source_file=str(path),
                        source_sha256=digest,
                    )
                    identity = [
                        site,
                        kind,
                        day_value,
                        clock_value,
                        digest,
                        row["position"],
                        row["url"],
                    ]
                    row["record_id"] = hashlib.sha256(
                        json.dumps(identity).encode()
                    ).hexdigest()
                    if row["record_id"] in completed:
                        continue
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                    handle.flush()
                    completed.add(row["record_id"])
                    count += 1
            except (OSError, ValueError, TypeError, KeyError) as exc:
                failures += 1
                log.error("%s: %s", path, exc)
                errors.write(
                    json.dumps({"source_file": str(path), "error": str(exc)}) + "\n"
                )
                errors.flush()
    return count, failures
