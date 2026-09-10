import gzip
import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pyarrow.parquet as pq
import pytest

from top10_news.cli import main
from top10_news.collection import parse_files
from top10_news.convert import SCHEMA, to_parquet
from top10_news.fetch import fetch_snapshot
from top10_news.parsers import parse_nyt_jsonp, parse_page, resolve_link

FIXTURES = Path(__file__).parent / "fixtures"


def test_homepage_order_and_punctuation():
    rows = parse_page(
        (FIXTURES / "homepage.html").read_text(), site="nyt", year=2016, kind="homepage"
    )
    assert [row["position"] for row in rows] == [1, 2]
    assert rows[0]["url"].endswith("second.html?edition=us")
    assert rows[1]["url"].endswith("first.html")
    assert rows[0]["link_text"] == "Second & distinct: news!"


def test_popular_order_and_wayback_urls():
    rows = parse_page(
        (FIXTURES / "popular.html").read_bytes(), site="nyt", year=2012, kind="popular"
    )
    assert rows[0]["url"].endswith("third.html")
    assert rows[0]["archive_url"].startswith("https://web.archive.org/web/20120701")
    assert [row["position"] for row in rows] == [1, 2]


def test_politics_filter_does_not_treat_minus_one_as_true():
    rows = parse_page(
        (FIXTURES / "popular.html").read_bytes(),
        site="nyt_politics",
        year=2012,
        kind="popular",
    )
    assert len(rows) == 1
    assert "/politics/" in rows[0]["url"]


def test_jsonp_preserves_quotes_and_response_order():
    rows = parse_nyt_jsonp((FIXTURES / "top_pages.jsonp").read_bytes())
    assert rows[0]["link_text"] == 'A quoted "headline"'
    assert rows[0]["url"].endswith("second.html")
    assert rows[1]["position"] == 2


@pytest.mark.parametrize(
    "payload", ["alert(1);", 'callback({"top_pages": []});', '{"other": []}']
)
def test_invalid_or_empty_jsonp_fails(payload):
    with pytest.raises(ValueError, match=r"expected|no matching|no top_pages"):
        parse_nyt_jsonp(payload)


def test_empty_layout_fails():
    with pytest.raises(ValueError, match="no matching article links"):
        parse_page("<html>No stories</html>", site="nyt", year=2012, kind="popular")


def test_yahoo_class_names_with_parentheses():
    html = '<h3 class="Mb(5px)"><a href="/news/story.html">Story</a></h3>'
    assert (
        parse_page(html, site="yahoo", year=2016, kind="popular")[0]["link_text"]
        == "Story"
    )


def test_unwrap_only_real_wayback_links():
    assert resolve_link("https://example.org/a?x=1", "https://www.nytimes.com") == (
        "https://example.org/a?x=1",
        None,
    )
    with pytest.raises(ValueError, match="not an HTTP URL"):
        resolve_link("javascript:alert(1)", "https://www.nytimes.com")


def test_resume_repairs_tail_and_preserves_repeat_observations(tmp_path):
    one = tmp_path / "nyt_20160701_120000.html"
    two = tmp_path / "nyt_20160702_120000.html.gz"
    html = (FIXTURES / "homepage.html").read_bytes()
    one.write_bytes(html)
    two.write_bytes(gzip.compress(html))
    output = tmp_path / "observations.jsonl"
    kwargs = {"site": "nyt", "kind": "homepage"}
    assert parse_files([one], output, **kwargs) == (2, 0)
    with output.open("a") as handle:
        handle.write('{"incomplete":')
    assert parse_files([one, two], output, resume=True, **kwargs) == (2, 0)
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert len(rows) == 4
    assert rows[0]["url"] == rows[2]["url"]
    assert rows[0]["record_id"] != rows[2]["record_id"]


def test_parse_failure_is_recorded_and_cli_nonzero(tmp_path):
    bad = tmp_path / "nyt_20160701_120000.html"
    bad.write_text("<html></html>")
    output = tmp_path / "rows.jsonl"
    assert (
        main(
            [
                "parse",
                str(bad),
                "--site",
                "nyt",
                "--kind",
                "popular",
                "--out",
                str(output),
            ]
        )
        == 1
    )
    assert (
        "no matching article links" in output.with_suffix(".failures.jsonl").read_text()
    )


def test_csv_roundtrip_keeps_legacy_order_and_repeated_urls(tmp_path):
    output = tmp_path / "legacy.parquet"
    assert to_parquet([FIXTURES / "legacy.csv"], output, kind="homepage") == 2
    table = pq.read_table(output)
    assert table.schema == SCHEMA
    rows = table.to_pylist()
    assert [row["position"] for row in rows] == [2, 1]
    assert rows[0]["position_kind"] == "legacy_order"
    assert rows[0]["observed_date"] == date(2016, 7, 1)
    assert rows[0]["url"] == rows[1]["url"]
    assert rows[0]["text"] is None
    assert rows[0]["src_list"] == "national"


def test_headerless_csv_requires_columns_and_atomic_output(tmp_path):
    source = tmp_path / "data.csv"
    source.write_text("20160701,nyt,https://example.org/a\n")
    output = tmp_path / "rows.parquet"
    output.write_bytes(b"existing")
    with pytest.raises(ValueError, match="site/src"):
        to_parquet([source], output)
    assert output.read_bytes() == b"existing"
    assert not output.with_name(output.name + ".part").exists()
    assert to_parquet([source], output, columns=["date", "src", "url"]) == 1


def test_fetch_snapshot_atomic_and_records_response_url(tmp_path):
    url = "https://web.archive.org/web/20120701120000id_/http://example.org/"
    response = SimpleNamespace(
        url=url,
        content=b"<html>Example</html>",
        status_code=200,
        raise_for_status=lambda: None,
    )
    session = SimpleNamespace(get=lambda *args, **kwargs: response)
    output = tmp_path / "page.html.gz"
    assert fetch_snapshot(url, output, session=session)["response_url"] == url
    assert gzip.decompress(output.read_bytes()) == response.content
    assert not output.with_name(output.name + ".part").exists()
    response.url = "https://example.org/"
    with pytest.raises(ValueError, match="redirected"):
        fetch_snapshot(url, output, session=session)
    assert gzip.decompress(output.read_bytes()) == response.content


def test_captured_nyt_lists_require_an_explicit_metric():
    html = (FIXTURES / "nyt-most-viewed-2012.html").read_bytes()
    with pytest.raises(ValueError, match="explicit metric"):
        parse_page(html, site="nyt", year=2012, kind="popular")
    rows = parse_page(html, site="nyt_viewed", year=2012, kind="popular")
    assert len(rows) == 2
    assert [row["position"] for row in rows] == [1, 2]
    assert all(row["src_list"] == "most-viewed" for row in rows)
    assert rows[0]["url"] != rows[1]["url"]


def test_usat_list_layouts_are_alternatives_not_one_ranking():
    html = (
        '<div class="ranked-list"><a href="/story/one">Ranked</a></div>'
        '<ul class="hero-list"><li><a href="/story/two">Hero</a></li></ul>'
    )
    rows = parse_page(html, site="usat", year=2012, kind="popular")
    assert len(rows) == 1
    assert rows[0]["src_list"] == "ranked-list"
    assert rows[0]["link_text"] == "Ranked"


def test_fox_2012_trending_returns_the_extracted_links():
    html = '<div class="ct-mod"><h3><a href="/story/one">A story</a></h3></div>'
    assert (
        parse_page(html, site="fox_trending", year=2012, kind="popular")[0]["link_text"]
        == "A story"
    )
