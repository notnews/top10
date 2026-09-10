# Fixture sources

| Fixture | Source and capture | Changes |
|---|---|---|
| `nyt-most-viewed-2012.html` | [NYT popular page, Wayback capture 2012-10-22 00:47:30 UTC](https://web.archive.org/web/20121022004730id_/http://www.nytimes.com/most-popular), retrieved 2026-09-10 10:51:59 UTC | Retains only the Most Viewed module's heading and first two article anchors; each article headline is shortened to five words. The selector-bearing classes and original URLs are retained. |
| `homepage.html` | Synthetic, constructed 2026-09-10 from the historical NYT homepage link pattern | Deliberately nonalphabetical article paths, a duplicate anchor, query string, punctuation, and navigation link. Not a captured news page. |
| `popular.html` | Synthetic, constructed 2026-09-10 from the original 2012 NYT selector | Two minimal article links, one politics link, with explicit Wayback wrappers. Not a captured news page. |
| `top_pages.jsonp` | Synthetic, constructed 2026-09-10 from the historical `top_pages` response shape | Two invented headlines and URLs exercise callback handling, quotes, and ordering. |
| `legacy.csv` | Synthetic, constructed 2026-09-10 from the documented CSV columns | Repeats one URL across two dates with different legacy order values and missing full text. |

The original selector and response definitions are preserved in the historical implementation linked from the repository README. Inline test HTML is also synthetic. The full retrieved NYT page and response metadata remain under ignored `data/`; full copyrighted pages are not fixtures.
