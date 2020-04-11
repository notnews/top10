## Scraping and Parsing Internet Archive

### Table of Contents

* [Scraping and Parse Top10](#scraping-and-parse-top10)
  * [Script](scripts/top10.py)
  * [Usage](#usage)

* [Scraping Homepages & Politics Homepages](#scraping-homepages-and-politics-homepages)
  * [Script](scripts/homepage.py)
  * [Usage](#usage-1)

* [Parsing scraped homepages](#parsing-scraped-homepages)
  * [Script](scripts/process_homepage.py)
  * [Usage](#usage-2)

* [Workflow](#workflow)

[Back](scripts.md)

## Scraping and Parse Top10

### Usage

```
usage: top10.py [-h] [-c CONFIG] [-n COUNT] [-o OUTPUT] [--with-header]
                [--compress]

Top News! scraper

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Configuration file
  -n COUNT, --count COUNT
                        Top N
  -o OUTPUT, --output OUTPUT
                        Output file name
  --with-header         Output with header at the first row
  --compress            Compress download HTML files
```

### Run

```
python top10.py
```

## Scraping Homepages and Politics Homepages

### Usage

```
usage: homepage.py [-h] [-c CONFIG] [-d DIR] [--compress] input

Homepages scraper

positional arguments:
  input

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Configuration file
  -d DIR, --dir DIR     Output directory for HTML files
  --compress            Compress download HTML files

```

### Input File For Scraping Homepages

```
no,src,url,ia_url,ia_year_begin,ia_year_end
1,nyt,http://www.nytimes.com,http://www.nytimes.com/,2012,2016
2,wapo,http://www.washingtonpost.com/,,,
3,wsj,http://www.wsj.com/,http://online.wsj.com/home-page#,2012,2016
4,fox,http://www.foxnews.com/,http://www.foxnews.com/,2012,2016
5,hpmg,http://www.huffingtonpost.com/,http://www.huffingtonpost.com/,2012,2016
6,usat,http://www.usatoday.com/,http://www.usatoday.com/,2012,2016
7,google,https://news.google.com/,http://news.google.com/,2012,2016
8,yahoo,https://www.yahoo.com/news/,http://news.yahoo.com/,2012,2016
```

- ``no``    	      Sequence number
- ``src``   	      News source
- ``url``   	      News URL
- ``ia_url``        News URL in the Internet Archive
- ``ia_year_begin`` The Internet Archive scraping script will start from this year
- ``ia_year_end``   The Internet Archive scraping script will stop at this year

### Example

```
python homepage.py homepage.csv
```

## Parsing scraped homepages

### Usage

```
usage: process_homepage.py [-h] [-o OUTPUT] [--with-header] [--with-text]
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

## Workflow

### Top10

```
top10.cfg ⇨ top10.py ⇨ current-top10-html.tar.gz (HTML files) + current-output-top10.csv (with text)
```

### Current homepage

#### All

```
homepage.csv ⇨ homepage.py ⇨ current-homepage-html.tar.gz (HTML files) ⇨ process_homepage.py ⇨ current-output-homepage.csv (without text)
```

#### Politics

```
politics_homepage.csv ⇨ homepage.py ⇨ current-politics-homepage-html.tar.gz (HTML files) ⇨ process_homepage.py ⇨ current-output-politics-homepage.csv (without text)
```
