"""Convert observation rows without collapsing repeated URLs across captures."""

import csv
import gzip
import json
import re
from datetime import date, time
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

SCHEMA = pa.schema(
    [
        ("site", pa.string()),
        ("list_kind", pa.string()),
        ("src_list", pa.string()),
        ("observed_date", pa.date32()),
        ("observed_time", pa.string()),
        ("position", pa.int32()),
        ("position_kind", pa.string()),
        ("url", pa.string()),
        ("archive_url", pa.string()),
        ("link_text", pa.string()),
        ("source_file", pa.string()),
        ("source_sha256", pa.string()),
        ("article_path", pa.string()),
        ("title", pa.string()),
        ("text", pa.string()),
        ("top_image", pa.string()),
        ("authors", pa.string()),
        ("summary", pa.string()),
        ("keywords", pa.string()),
        ("homepage_keywords", pa.string()),
    ]
)
ALIASES = {
    "src": "site",
    "date": "observed_date",
    "time": "observed_time",
    "order": "position",
    "path": "article_path",
}


def normalize_record(row: dict, source: str, kind: str) -> dict:
    """Type known columns and preserve supplied legacy URLs and order values."""
    row = {ALIASES.get(key, key): value for key, value in row.items()}
    if not row.get("url") or not row.get("site"):
        raise ValueError(
            "each row requires site/src and url; headerless CSV requires --columns"
        )
    record = {
        name: row.get(name) if row.get(name) != "" else None for name in SCHEMA.names
    }
    record["list_kind"] = row.get("list_kind") or kind
    record["position_kind"] = row.get("position_kind") or "legacy_order"
    record["source_file"] = row.get("source_file") or source
    if record["observed_date"]:
        record["observed_date"] = date.fromisoformat(str(record["observed_date"]))
    if record["observed_time"]:
        record["observed_time"] = time.fromisoformat(
            str(record["observed_time"])
        ).isoformat()
    if record["position"] is not None:
        raw = str(record["position"])
        if not re.fullmatch(r"\d+(?:\.0+)?", raw):
            raise ValueError(f"invalid position: {raw}")
        record["position"] = int(raw.split(".")[0])
    return record


def read_records(path: Path, columns: list[str] | None = None):
    """Read JSONL or CSV, optionally with explicit names for headerless CSV."""
    opener = gzip.open if path.suffix == ".gz" else Path.open
    suffix = path.with_suffix("").suffix if path.suffix == ".gz" else path.suffix
    with opener(path, "rt", encoding="utf-8-sig", newline="") as handle:
        if suffix == ".jsonl":
            for number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError(f"{path}:{number}: expected a JSON object")
                yield row
        elif suffix == ".csv":
            reader = csv.DictReader(handle, fieldnames=columns)
            fields = set(reader.fieldnames or [])
            if "url" not in fields or not fields.intersection({"site", "src"}):
                raise ValueError(
                    "CSV needs site/src and url; use --columns for headerless data"
                )
            for row in reader:
                if None in row or None in row.values():
                    raise ValueError(
                        f"{path}: CSV row width does not match the columns"
                    )
                yield row
        else:
            raise ValueError(
                "input must be .jsonl, .csv, or a gzip-compressed equivalent"
            )


def to_parquet(
    inputs: list[Path],
    output: Path,
    *,
    kind: str = "unknown",
    columns: list[str] | None = None,
) -> int:
    """Stream all observations into an atomic Parquet output with an explicit schema."""
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".part")
    count = 0
    try:
        with pq.ParquetWriter(temporary, SCHEMA) as writer:
            batch = []
            for path in inputs:
                for row in read_records(path, columns):
                    batch.append(normalize_record(row, str(path), kind))
                    if len(batch) == 5000:
                        writer.write_table(pa.Table.from_pylist(batch, schema=SCHEMA))
                        count += len(batch)
                        batch.clear()
            if batch:
                writer.write_table(pa.Table.from_pylist(batch, schema=SCHEMA))
                count += len(batch)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return count
