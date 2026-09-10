# Top 10 News: Historical Homepages and Popular-Story Lists

[![CI](https://github.com/notnews/top10/actions/workflows/ci.yml/badge.svg)](https://github.com/notnews/top10/actions/workflows/ci.yml)
[![Data](https://img.shields.io/badge/data-Dataverse-blue)](https://doi.org/10.7910/DVN/OTJMYQ)
[![Code license](https://img.shields.io/badge/code-MIT-green)](LICENSE)

Historical observations of news homepages, politics pages, and popular-story lists from 2012 and 2016–2017. This package parses saved captures and converts published CSVs to Parquet. The original live collection has ended; these tools support historical reproduction.

## Data

The [Harvard Dataverse release](https://doi.org/10.7910/DVN/OTJMYQ), registered as version 1.0, holds the HTML and parsed data. File names and coverage below come from the original collection inventory; full release row counts have not been verified locally.

| Collection | Parsed files | Raw files | Coverage | Rows |
|---|---|---|---|---|
| Live homepages | `current-output-homepage.csv` | `current-homepage-html.tar.gz` | 2016–2017 | See Dataverse |
| Live politics pages | `current-output-politics-homepage.csv` | `current-politics-homepage-html.tar.gz` | 2016–2017 | See Dataverse |
| Live popular lists | `current-output-top10.csv` | `current-top10-html.tar.gz` | 2016–2017 | See Dataverse |
| Archived homepages | `ia-output-homepage-{2012,2016}-text.csv.gz` | Includes `ia-homepage-html-2012.tar.gz` | 2012 and 2016 | See Dataverse |
| Archived politics pages | `ia-output-politics-homepage-2012-2016-notext.csv.gz` | `ia-politics-html.tar.gz` | 2012 and 2016 | See Dataverse |
| Archived popular lists | `ia-output-top10-text-all.csv`, `ia-output-politics-top10-text-all.csv` | `ia-top10-html.tar.gz`, `ia-news-top10-html.tar.gz`, `ia-politics-top10-html.tar.gz` | July–November 2012 and 2016 | See Dataverse |

The original notes report homepage snapshot counts of 31,129 for NYT, 15,573 for WSJ, 16,838 for Fox, 26,667 for HuffPost, 26,545 for USA Today, and 13,991 for Yahoo. These are historical snapshot counts, not article counts. The [full collection notes](docs/collection-notes.md) retain source-specific details; [provenance/](provenance/) retains the original input inventories.

## Column dictionary

Each Parquet row is one story observed on a particular page or list. Repeated URLs across captures are retained.

| Columns | Type | Description |
|---|---|---|
| `site` | string | Source code supplied to the parser or historical CSV `src` value |
| `list_kind`, `src_list` | string | Page/list type and supplied list context, such as `most-viewed`; unknown context remains null |
| `observed_date`, `observed_time` | date, string | Capture date and time, not article publication time; a timezone is not inferred |
| `position` | int32 | Position within the matched links or the supplied legacy `order` value |
| `position_kind` | string | `document_order`, `response_order`, or `legacy_order` |
| `url` | string | Original article URL for newly parsed records; unchanged URL value for legacy CSVs, which may contain archive URLs |
| `archive_url` | string | Explicit Wayback link found in the page, if any |
| `link_text` | string | Anchor text, with whitespace normalized and punctuation preserved |
| `source_file`, `source_sha256` | string | Input file and, for newly parsed captures, SHA-256 of its decompressed content |
| `article_path`, `title`, `text`, `top_image`, `authors`, `summary`, `keywords`, `homepage_keywords` | string | Historical extraction fields when supplied; empty values become null |

JSONL also stores `record_id` for resuming. Legacy CSVs map `src`, `date`, `time`, `order`, and `path` to the corresponding columns above. Unknown CSV fields are not included in the Parquet schema. A file without a header requires an explicit `--columns` list.

## Coverage and known gaps

**Historical homepage `order` values are not reliable page positions.** The original homepage parsers collected links in a Python set and then assigned numbers while iterating over that set. Conversion preserves those numbers as `legacy_order`; it cannot reconstruct their original positions. Re-parsing raw HTML recovers document order, which may differ from visual prominence. The old archived-homepage script also offered an optional `--unique` mode that removed repeated URLs across captures; whether a particular release used that option must be established from its provenance.

“Top 10” is a project name, not a uniform measure. The collection included top-four, top-five, and top-ten lists, RSS headlines, most-viewed stories, and trending stories. NYT's popular page contains distinct lists. Use an explicit source such as `nyt_viewed` or `nyt_emailed`; the parser refuses to combine those lists into one ranking.

Archive availability varies by site and date. Historical notes report missing Google captures, unavailable politics-popularity lists, and lists loaded by JavaScript that were absent from saved HTML. They also identify roughly 56,000 archived links without fetched article text. Missing article text remains null. This package does not fill those gaps or rerun the obsolete live-site and full-text collectors.

Historical HTML selectors cover 2012 and 2016–2017 layouts for Fox, HuffPost, NYT, USA Today, WSJ, Yahoo, and some Washington Post pages. Homepage link rules also cover Google. Unknown layouts and empty matches fail visibly. Only the captured NYT fixture has been checked against a freshly retrieved archive page; the other selector tests are synthetic and do not establish complete historical coverage.

## Collection methods

| Period/source | Method |
|---|---|
| 2012 observations | Retrieve Internet Archive snapshots; extract homepage links and available popular lists |
| 2016–2017 observations | Save live pages and selected API/RSS responses; supplement with archived captures |
| Historical full text | Download linked articles and extract text with newspaper3k; availability varied by collection |
| Reproduction tools | Parse local HTML/gzip or NYT JSON/JSONP, retain observation context, and convert CSV/JSONL to typed Parquet |

The [historical implementation](https://github.com/notnews/top10/tree/db14b87b6ee2de9b0ba4fc097acc49178cd9960e) preserves the original selectors and collection scripts. Fixture sources and trimming are documented in [tests/fixtures/SOURCES.md](tests/fixtures/SOURCES.md). Re-parsed outputs may differ from historical CSVs because ordering, URL handling, and text normalization have been corrected.

## Usage

Python 3.12 or later and [uv](https://docs.astral.sh/uv/) are required. Run commands from the repository root and keep downloaded inputs and generated outputs under ignored `data/`.

### Install

```sh
uv sync --frozen --group dev
```

### Parse saved captures

```sh
uv run top10-news parse data/nyt_20121022_004730.html.gz --site nyt_viewed --kind popular --out data/observations.jsonl
uv run top10-news parse data/nyt_20121022_004730.html.gz --site nyt_viewed --kind popular --out data/observations.jsonl --resume
```

The parser reads capture dates from filenames ending in `_YYYYMMDD_HHMMSS.html[.gz]` or `_YYYYMMDDHHMMSS.html[.gz]`. Supply `--date YYYY-MM-DD` and optionally `--time HH:MM:SS` for other names. Page kinds are `homepage`, `politics_homepage`, `popular`, and `nyt_jsonp`. Use `--site nyt` for saved NYT JSON/JSONP responses.

Resume skips successful observations while preserving the same story on different dates or lists. It repairs an interrupted final JSONL line; malformed complete lines remain errors. Per-file failures go to an adjacent `.failures.jsonl` file and cause a nonzero exit status.

To retrieve the specific archive capture used by the smoke example:

```sh
uv run top10-news fetch-snapshot https://web.archive.org/web/20121022004730id_/http://www.nytimes.com/most-popular --out data/nyt_20121022_004730.html.gz
```

`fetch-snapshot` downloads one supplied timestamped URL, writes gzip atomically, and records the request URL, final response URL, and retrieval time beside it. It has bounded retries and does not search or crawl the archive.

### Convert

```sh
uv run top10-news to-parquet data/observations.jsonl --out data/top10.parquet
uv run top10-news to-parquet data/current-output-homepage.csv --kind homepage --out data/homepages.parquet
uv run top10-news to-parquet data/headerless.csv --columns date,time,src,order,url,link_text --kind popular --out data/popular.parquet
```

Use the exact column order and full column list for a headerless file. Conversion streams rows, preserves repeated observations, and replaces its output only after success.

### Upload

The upload command reads `DATAVERSE_API_TOKEN` and adds the named file to the Dataverse draft. It does not publish a dataset version.

```sh
uv run top10-news upload data/top10.parquet
```

## Development

```sh
make check
```

This runs Ruff, formatting, pytest, and pre-commit. `make ci-docker` runs lint and tests in standard Python 3.12 and 3.14 images. CI uses the same lockfile and checks. Install Git hooks with `uv run pre-commit install`.

## Citation

Use [CITATION.cff](CITATION.cff) and cite the [versioned Dataverse release](https://doi.org/10.7910/DVN/OTJMYQ). Dataset authors and version follow the [DataCite record](https://api.datacite.org/dois/10.7910/DVN/OTJMYQ): Gaurav Sood and Suriyan Laohaprapanon. Code credit follows the original repository authors.

## License

Code is [MIT licensed](LICENSE). The Dataverse deposit is registered under CC0 1.0 with restricted access. Underlying news text and archived pages retain their owners' rights; consult the release for access conditions.
