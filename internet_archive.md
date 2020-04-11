## Scraping and Parsing Internet Archive

### Table of Contents

* [Homepages](#homepages)

  * [Scraping](#scraping)
    * [Script](scripts/internet_archive/internet_archive.py)
    * [Usage](#usage)

  * [Parsing](#parsing-scraped-internet-archive)
    * [Script](scripts/internet_archive/process_ia_homepage.py)
    * [Usage](#usage-1)

* [Top 10](#top10)

  * [Scraping](#scraping-top10)
    * [Script](scripts/internet_archive/internet_archive.py)
    * [Usage](#usage-2)

  * [Parsing](#parsing-top10)
    * [Script](scripts/internet_archive/process_ia_top10.py)
    * [Usage](#usage-3)

* [Output File Format](#output-file)

* [Workflow](#workflow)

[Back](scripts.md)

--------------

## Homepages

### Scraping

#### Usage

```
usage: internet_archive.py [-h] [-c CONFIG] [-d DIR] [--overwritten]
                           [-s] [--compress] [--selenium]
                           input

Homepages scraper

positional arguments:
  input

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Configuration file
  -d DIR, --dir DIR     Output directory for HTML files
  --overwritten         Overwritten if HTML file exists
  -s, --statistics      Run the script to count amount of snapshots
  --compress            Compress download HTML files
  --selenium            Use Selenium to download dynamics HTML content
``` 

#### Input file

Using same input file as Scraping homepage.

### Parsing scraped Internet Archive

#### Usage

```
usage: process_ia_homepage.py [-h] [-o OUTPUT] [--with-header] [--with-text]
                              [--unique]
                              directory

Parse Homepage and Download Article

positional arguments:
  directory             Scraped homepages directory

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file name
  --with-header         Output with header at the first row
  --with-text           Download the article text
  --unique              Keep only unique articles links
```

## Top10

### Scraping Top10

#### Usage
```
usage: internet_archive.py [-h] [-c CONFIG] [-d DIR] [--overwritten]
                           [-s] [--compress] [--selenium]
                           input

Homepages scraper

positional arguments:
  input

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Configuration file
  -d DIR, --dir DIR     Output directory for HTML files
  --overwritten         Overwritten if HTML file exists
  -s, --statistics      Run the script to count amount of snapshots
  --compress            Compress download HTML files
  --selenium            Use Selenium to download dynamics HTML content
``` 

### Parsing Top10

#### Usage

```
usage: process_ia_top10.py [-h] [-o OUTPUT] [--with-header] [--with-text]
                           directory

Parse Homepage and Download Article

positional arguments:
  directory             Scraped homepages directory

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file name
  --with-header         Output with header at the first row
  --with-text           Download the article text
```

### Output file

```
"date","time","src","order","url","link_text","homepage_keywords","path","title","text","top_image","authors","summary","keywords"
```

- ``date``              Date
- ``time``              Time
- ``src``               News's source
- ``order``             Link's order in page
- ``url``               Link's URL
- ``link_text``         Link's text
- ``homepage_keywords`` Keywords of page
- ``path``              Path to download article
- ``title``             Title of article
- ``text``              Text of article
- ``top_image``         Top image of article
- ``authors``           Authors of article
- ``summary``           Summary of article
- ``keywords``          Keywords of article

Note that *there is no data in columns ``path`` to ``keywords`` if --with-text is not specific.*

## Workflow

### Homepage

#### All

* 2012
  ```
  homepage.csv ⇨ internet_archive.py ⇨ internet_archive (HTML files)
  ⇨ process_ia_homepage.py ⇨ ia-homepage-html-2012.tar.gz + ia-output-homepage-2012-text.csv.gz
  ```

* 2016
  ```
  homepage.csv ⇨ internet_archive.py ⇨ internet_archive (HTML files)
  ⇨ process_ia_homepage.py ⇨ ia-output-homepage-2016-text.csv.gz
  ```

#### Politics

```
politics_homepage.csv ⇨ internet_archive.py ⇨ ia-politics-html.tar.gz (HTML files between 2012~2016/08/15)
⇨ process_ia_homepage.py ⇨ ia-output-homepage-2016-text.csv.gz
```

### Top10

#### All

```
homepage_top10.csv ⇨  internet_archive.py ⇨ ia-top10-html.tar.gz (HTML files)
⇨ process_ia_top10.py ⇨ ia-news-top10-html.tar.gz (HTML files) + ia-output-top10-text-all.csv
```

#### Politics

```
politics_homepage_top10.csv ⇨  internet_archive.py ⇨ ia-top10-html.tar.gz (HTML files)
⇨ process_ia_top10.py ⇨ ia-politics-top10-html.tar.gz + ia-output-politics-top10-text-all.csv
```

#### NYT TopNews from JSONP

```
nyt_ia_jsonp-topnews.csv ⇨ internet_archive.py ⇨ HTML files
⇨ process_ia_jsonp_topnews.py ⇨ HTML files + output_nyt_ia_jsonp_topnews.csv
```
