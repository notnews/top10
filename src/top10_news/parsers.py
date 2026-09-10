"""Parse saved historical pages without fetching or executing page content."""

import json
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

BASE_URLS = {
    "fox": "https://www.foxnews.com/",
    "google": "https://news.google.com/",
    "hpmg": "https://www.huffingtonpost.com/",
    "nyt": "https://www.nytimes.com/",
    "usat": "https://www.usatoday.com/",
    "wapo": "https://www.washingtonpost.com/",
    "wsj": "https://www.wsj.com/",
    "yahoo": "https://news.yahoo.com/",
}
POPULAR_SELECTORS = {
    "fox": ("div.trending-descending h3 a", "section#trending h3 a"),
    "fox_politics": ("div.trending-descending h3 a", "div.mod-8 h3 a"),
    "fox_trending": ("div.ct-mod h3 a", "div.articles div.list > ul li a"),
    "hpmg": ("div.snp_most_popular a.snp_entry_title", "div#right-rail-trending h2 a"),
    "hpmg_politics": (
        "div.snp_most_popular a.snp_entry_title",
        "div#right-rail-trending h2 a",
    ),
    "nyt": ("div.mostPopularTabbedModule h3 a", "section#trending-list-container h2 a"),
    "nyt_politics": (
        "div.mostPopularTabbedModule h3 a",
        "section#trending-list-container h2 a",
    ),
    "usat": ("div.ranked-list a, ul.hero-list a", "div.most-popular-sidebar-content a"),
    "wsj": ("div#mostPopularTab_panel_mostRead a", "ol.wsj-popular-list a"),
    "wsj_politics": ("div#mostPopularTab_panel_mostRead a", "ol.wsj-popular-list a"),
    "yahoo": (
        "div.yom-top-story-content-0 div.txt a",
        'h3[class~="Mb(5px)"] a:not([class~="O(n):f"])',
    ),
    "wapo": (None, "div#post-most-rr a:has(div.headline)"),
}
ARTICLE_PATTERNS = {
    "fox": r"/\d{4}/\d{2}/\d{2}/.+\.html|/story/|/politics/.*\.html",
    "google": r".+",
    "hpmg": r"/entry/|/\d{4}/\d{2}/\d{2}/|_n_\d+\.html",
    "nyt": r"/\d{4}/\d{2}/\d{2}/.+\.html",
    "usat": r"/story/|/news/.+\.htm|/money/.+\.htm",
    "wapo": r"/\d{4}/\d{2}/\d{2}/|/wp-dyn/content/article/",
    "wsj": r"/article/|/articles/|\d{9,}$",
    "yahoo": r"/news/.+\.html|/\d{8}/",
}
_REPLAY = re.compile(
    r"(?:https?://web\.archive\.org)?/web/\d{1,14}(?:[a-z_]+)?/(https?://.+)"
)


def resolve_link(href: str, base_url: str) -> tuple[str, str | None]:
    """Return the original HTTP URL and any explicit Wayback replay URL."""
    href = href.strip()
    match = _REPLAY.fullmatch(href)
    archive_url = None
    if match:
        archive_url = urljoin("https://web.archive.org", href)
        href = match[1]
    url = urljoin(base_url, href)
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("link is not an HTTP URL")
    if not href or href.startswith("#"):
        raise ValueError("link has no article target")
    return url, archive_url


def _records(pairs: list[tuple[str, str]], base_url: str) -> list[dict]:
    records = []
    seen = set()
    for label, href in pairs:
        if not isinstance(label, str) or not isinstance(href, str):
            raise ValueError("link labels and URLs must be strings")
        label = " ".join(label.split())
        if not label:
            continue
        try:
            url, archive_url = resolve_link(href, base_url)
        except ValueError:
            continue
        if url in seen:
            continue
        seen.add(url)
        records.append(
            {
                "url": url,
                "archive_url": archive_url,
                "link_text": label,
                "position": len(records) + 1,
            }
        )
    if not records:
        raise ValueError(
            "no matching article links; page may be empty or use an unsupported layout"
        )
    return records


def parse_page(
    html: str | bytes, *, site: str, year: int, kind: str, base_url: str | None = None
) -> list[dict]:
    """Extract historical homepage or popular-list links in document order.

    Positions describe the matched links, not a universal popularity score or
    the visual prominence of a homepage story. Duplicate targets are collapsed
    within this page only. Punctuation and query strings are preserved.
    """
    root_site = site.split("_")[0]
    if root_site not in BASE_URLS or year not in {2012, 2016, 2017}:
        raise ValueError(
            "supported historical years are 2012, 2016, and 2017; site must be known"
        )
    base_url = base_url or BASE_URLS[root_site]
    soup = BeautifulSoup(html, "html.parser")
    if kind in {"homepage", "politics_homepage"}:
        nodes = soup.select("a.article" if root_site == "google" else "a[href]")
        pattern = re.compile(ARTICLE_PATTERNS[root_site])
        selected = []
        for node in nodes:
            try:
                target, _ = resolve_link(node.get("href", ""), base_url)
            except ValueError:
                continue
            if pattern.search(target):
                selected.append(node)
        nodes = selected
    elif kind == "popular":
        if site.startswith("nyt_") and site.split("_", 1)[1] in {
            "viewed",
            "emailed",
            "blogged",
            "searched",
            "movies",
        }:
            metric = site.split("_", 1)[1]
            for module in soup.select("div.mostPopularModule"):
                header = module.select_one("h3 a[href]")
                if header and f"most-popular-{metric}" in header["href"]:
                    rows = _records(
                        [
                            (node.get_text(" ", strip=True), node.get("href", ""))
                            for node in module.select("ol.mostPopularList li a[href]")
                        ],
                        base_url,
                    )
                    for row in rows:
                        row["src_list"] = f"most-{metric}"
                    return rows
            raise ValueError("the requested NYT list is absent")
        if site == "nyt" and soup.select("div.mostPopularModule"):
            raise ValueError(
                "multiple NYT list types: select nyt_viewed or another explicit metric"
            )
        if site not in POPULAR_SELECTORS:
            raise ValueError("no historical popular-list selector for this site")
        selector = POPULAR_SELECTORS[site][0 if year == 2012 else 1]
        if selector is None:
            raise ValueError("this source/year has no supported popular-list layout")
        nodes = soup.select(selector)
        if site == "usat" and year == 2012:
            ranked = soup.select("div.ranked-list a")
            nodes = ranked or soup.select("ul.hero-list a")
            rows = _records(
                [
                    (node.get_text(" ", strip=True), node.get("href", ""))
                    for node in nodes
                ],
                base_url,
            )
            for row in rows:
                row["src_list"] = "ranked-list" if ranked else "hero-list"
            return rows
        if site == "yahoo" and year == 2012 and not nodes:
            listing = soup.select_one("ul.yom-list-large")
            nodes = listing.select("div.txt a") if listing else []
        if site == "nyt_politics" and year == 2012:
            nodes = [node for node in nodes if "/politics/" in node.get("href", "")]
    else:
        raise ValueError("kind must be homepage, politics_homepage, or popular")
    return _records(
        [(node.get_text(" ", strip=True), node.get("href", "")) for node in nodes],
        base_url,
    )


def parse_nyt_jsonp(payload: str | bytes) -> list[dict]:
    """Parse saved NYT top-pages JSON or JSONP without evaluating JavaScript."""
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8-sig")
    payload = payload.strip()
    if not payload.startswith("{"):
        match = re.fullmatch(
            r"[\w.$]+\s*\(\s*(\{.*\})\s*\)\s*;?", payload, flags=re.DOTALL
        )
        if not match:
            raise ValueError("expected a JSON object or JSONP callback")
        payload = match[1]
    data = json.loads(payload)
    pages = data.get("top_pages", data.get("results"))
    if not isinstance(pages, list) or any(not isinstance(page, dict) for page in pages):
        raise ValueError("NYT response has no top_pages or results list")
    return _records(
        [
            (page.get("headline", page.get("title", "")), page.get("url", ""))
            for page in pages
        ],
        BASE_URLS["nyt"],
    )
