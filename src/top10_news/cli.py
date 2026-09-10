"""Command line tools for the historical dataset."""

import argparse
import logging
from pathlib import Path

from top10_news.collection import parse_files
from top10_news.convert import to_parquet
from top10_news.fetch import fetch_snapshot
from top10_news.upload import upload

log = logging.getLogger(__name__)


def main(argv=None) -> int:
    """Parse captures, convert observations, or upload an explicitly named file."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    parse = sub.add_parser("parse", help="parse saved historical HTML or NYT JSONP")
    parse.add_argument("inputs", nargs="+", type=Path)
    parse.add_argument("--site", required=True)
    parse.add_argument(
        "--kind",
        choices=["homepage", "politics_homepage", "popular", "nyt_jsonp"],
        required=True,
    )
    parse.add_argument("--date")
    parse.add_argument("--time")
    parse.add_argument("--base-url")
    parse.add_argument("--out", type=Path, default=Path("data/observations.jsonl"))
    parse.add_argument("--resume", action="store_true")
    convert = sub.add_parser(
        "to-parquet", help="convert JSONL or historical CSV observations"
    )
    convert.add_argument("inputs", nargs="+", type=Path)
    convert.add_argument("--out", type=Path, default=Path("data/top10.parquet"))
    convert.add_argument("--kind", default="unknown")
    convert.add_argument("--columns", help="comma-separated names for a headerless CSV")
    fetch = sub.add_parser(
        "fetch-snapshot", help="retrieve one known Wayback capture as gzip"
    )
    fetch.add_argument("url")
    fetch.add_argument("--out", required=True, type=Path)
    send = sub.add_parser("upload", help="add a file to the Dataverse draft")
    send.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    if args.command == "parse":
        count, failures = parse_files(
            args.inputs,
            args.out,
            site=args.site,
            kind=args.kind,
            day=args.date,
            clock=args.time,
            resume=args.resume,
            base_url=args.base_url,
        )
        log.info("%s observations written; %s files failed", count, failures)
        return int(bool(failures))
    if args.command == "to-parquet":
        count = to_parquet(
            args.inputs,
            args.out,
            kind=args.kind,
            columns=args.columns.split(",") if args.columns else None,
        )
        log.info("%s observations written to %s", count, args.out)
    elif args.command == "fetch-snapshot":
        metadata = fetch_snapshot(args.url, args.out)
        log.info("saved %s from %s", args.out, metadata["response_url"])
    else:
        log.info("%s", upload(args.path))
    return 0
