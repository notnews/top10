# Top News!

Two types of scraping and parsing jobs: 

1. [Current (continuous, till 2016 election day)](#current-2016)
    * [Organization](#organization)
    * [What is being collected?](#what-is-being-collected)
        - Homepages
        - Politics Homepages
        - Top 10
2. [Past (Internet Archive)](#internet-archive-till-2016)
    * [Organization](#organization-1)
    * [What is being collected?](#what-was-collected)

The final data is posted [here](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/OTJMYQ)

[Back](readme.md)

## Current (2016)

### Organization

* Homepage
    - current-homepage-html.tar.gz
    - current-output-homepage.csv

* Politics Homepage
    - current-politics-homepage-html.tar.gz
    - current-output-politics-homepage.csv

* Top 10
    - current-top10-html.tar.gz (split by news_org/harvested pages from links to top10)
    - current-output-top10.csv

### What is being collected?

Three kinds of things being scraped:

#### Homepages

* html file name = [fox]_ + date_time + ....
* CSV fields: date, time, src, order, url, link_text, homepage_keywords, path, title, text, top_image, authors, summary, keywords (Please note we didn't scrape & parse the article so all fields from `path` will be empty)

* Sources
    - http://www.nytimes.com
    - http://www.washingtonpost.com/
    - http://www.wsj.com/
    - http://www.foxnews.com/
    - http://www.huffingtonpost.com/
    - http://www.usatoday.com/
    - https://news.google.com/
    - https://www.yahoo.com/news/

#### Politics Homepages

* html file name =
    - [fox_politics] + date_time + ....
    - For WP last link (the most): wp_themost + date_time

* CSV fields: date, time, src, order, url, link_text, homepage_keywords, path, title, text, top_image, authors, summary, keywords (Please note we didn't scrape & parse the article so all fields from `path` will be empty)

* Sources
    - https://www.washingtonpost.com/politics/
    - http://www.nytimes.com/pages/politics/index.html
    - http://www.huffingtonpost.com/section/politics
    - http://www.foxnews.com/politics.html
    - http://www.wsj.com/news/politics
    - https://www.yahoo.com/news/politics/
    - http://www.usatoday.com/news/politics/
    - https://www.washingtonpost.com/pb/themost/

#### Top 10

* html file name + folder structure:
    * Multiple folders --- one for each news org and containing content of the files in a gzip compression of the original HTML, name of each file = three_letter_src_name_date_time_order.html.gz

* Summary of Data Being Collected
    - Top 5 overall WSJ
    - Top 4 overall USA
    - Top 10 'trending' huffpost
    - Top 5 politics, overall WP
    - Top 10 overall, national, politics for NYT and Fox
    - Top 10 overall for yahoo news, AP, reuters, google news

* CSV fields: date, time, src, url, order on the list, text of the link, title of the article, path to local content file, src_list *

* Washington Post:
    * Top 5 Most Read (left side bar): https://www.washingtonpost.com/politics/
    * Top 5 Most Read (left side bar): https://www.washingtonpost.com/regional/
    * Top 5 'The Atlantic' from here:
        - https://www.washingtonpost.com/pb/themost/

* NYT:
    * July 10-now (Aug 12) got top 10 for national section only.
    * going forward: planning to get top 10 from:
        - all sections: https://api.nytimes.com/svc/mostpopular/v2/mostviewed/all-sections/1.json
        - national section: https://api.nytimes.com/svc/mostpopular/v2/mostviewed/national/1.json
        - politics section: https://api.nytimes.com/svc/mostpopular/v2/mostviewed/politics/1.json

* WSJ
    * Has top 5 with no separate link and same top 5 everywhere (not specific to politics on politics page)

* Fox
    * July 10-now (Aug 12) got top 10 for politics section only
    * From now on, get: http://feeds.foxnews.com/foxnews/national http://feeds.foxnews.com/foxnews/most-popular

* Huffington Post:
    * July 10-now got top 10 from http://www.huffingtonpost.com/mapi/v2/us/trending?device=desktop&statsType=rawPageView&statsPlatform=desktop&algo=trending
    * Add: http://www.huffingtonpost.com/ (right bar, trending)

* USA Today:
    * Home page, right bar: http://www.usatoday.com/ (most Popular) Just 4 links, looks like indeed what we've been and will continue to get

* Yahoo:
    * July 10-now been getting:
    * Get 5 from: https://www.yahoo.com/news/
    * Get 5 from: http://news.yahoo.com/most-popular/?pt=BureoF4GVB/?format=rss
    * Going forward:
        - Will keep 5 from: https://www.yahoo.com/news/
        - Will change to 10 for http://news.yahoo.com/most-popular/?pt=BureoF4GVB/?format=rss
        - Will add Yahoo originals, AP and Reuters (not sure what's gained from https://www.yahoo.com/news/ - does not refer to most viewed/popular)

* Google News
    * July 10-now:
        - 5 from: https://news.google.com/
        - 5 from: https://news.google.com/?ned=us&topic=po (But 2nd link seems to link to old news.)
    * Starting now:
        - 10 from news.google.com
        - still 5 from other link

## Internet Archive (till 2016)

### Organization

#### Homepage

* HTML files:
    - 2012: ia-homepage-html-2012.tar.gz

* CSV files (compressed in gzip)
    - 2012: ia-output-homepage-2012-text.csv.gz
    - 2016: ia-output-homepage-2016-text.csv.gz

#### Politics Homepage

* HTML file: ia-politics-html.tar.gz
* CSV output: ia-output-politics-homepage-2012-2016-notext.csv.gz (without text data)

#### Top 10

* HTML files:
    - ia-news-top10-html.tar.gz (split by news_org/harvested pages from links to top10)
    - ia-politics-top10-html.tar.gz
    - ia-top10-html.tar.gz
- CSV files
    - ia-output-politics-top10-text-all.csv
        + it's the Top10 of politics news that we have scraped and parsed from Internet Archive for 2012 and 2016 between Jul 1 and Nov 30.
    - ia-output-top10-text-all.csv
        + it's the Top10 of all news for year 2012 and 2016 between Jul 1 and Nov 30. **But articles not scraped and parsed --- there are 56k links that need to be scraped/parsed.**

### Scraped Homepage Data Summary

The frequency with which Internet Archive takes snapshots of different websites varies for unknown reasons. Here are the total number of snapshots for each kind of page:
    * Source: nyt, 31129 snapshots
    * Source: wsj, 15573 snapshots
    * Source: fox, 16838 snapshots
    * Source: hpmg, 26667 snapshots
    * Source: usat, 26545 snapshots
    * Source: google, 0 snapshots (Page cannot be displayed due to robots.txt)
    * Source: yahoo, 13991 snapshots

-------------------------------------------------

### What was collected?

1. Yahoo:

* Homepage: http://web.archive.org/web/20110701091910/http://news.yahoo.com/
* Top10:
    - 2011/2012: http://web.archive.org/web/20110701091910/http://news.yahoo.com/
    - 2016: Nothing: http://web.archive.org/web/20160703044858/https://www.yahoo.com/news/?ref=gs

2. Google:

* Page cannot be displayed due to robots.txt
* Homepage: http://web.archive.org/web/20110701014447/http://news.google.com/

3. USA Today:

* Homepage: http://web.archive.org/web/20120701152440/http://www.usatoday.com/
* Top10:
    - 2012: http://web.archive.org/web/20120701152440/http://www.usatoday.com/
    - 2016: http://web.archive.org/web/20160701161342/http://www.usatoday.com/

4. WSJ
* Homepage: http://web.archive.org/web/20120701034332/http://online.wsj.com/home-page#
* Politics: https://web.archive.org/web/20120703083921/http://online.wsj.com/public/page/news-politics-campaign.html
* Top10:
    - 2012: http://web.archive.org/web/20120701034332/http://online.wsj.com/home-page#
    - 2016: http://web.archive.org/web/20161001010640/http://www.wsj.com/
* Top10 Politics:
    - 2012: Don't see it: https://web.archive.org/web/20120703083921/http://online.wsj.com/public/page/news-politics-campaign.html
    - 2016: https://web.archive.org/web/20160601233847/http://www.wsj.com/news/politics

5. Fox News

* Homepage: https://web.archive.org/web/20120701050401/http://www.foxnews.com/
* Politics: https://web.archive.org/web/20120701123538/http://www.foxnews.com/politics/index.html
* Top10:
    - 2012: https://web.archive.org/web/20120701050401/http://www.foxnews.com/
    - 2016: At the bottom: https://web.archive.org/web/20160531220239/http://www.foxnews.com/
* Top10 Politics:
    - 2012: https://web.archive.org/web/20120701123538/http://www.foxnews.com/politics/index.html
    - 2016: https://web.archive.org/web/20160602040203/http://www.foxnews.com/politics.html?intcmp=subnav

6. HuffPo:
* Homepage: http://web.archive.org/web/20110701031057/http://www.huffingtonpost.com/
* Politics: https://web.archive.org/web/20120711044502/http://www.huffingtonpost.com/politics/
* Top10:
    - 2012: http://web.archive.org/web/20110701031057/http://www.huffingtonpost.com/
    - 2016: don't see here
* Top10 Politics:
    - 2012: https://web.archive.org/web/20120711044502/http://www.huffingtonpost.com/politics/
    - 2016: https://web.archive.org/web/20160701011648/http://www.huffingtonpost.com/section/politics

7. NYT:

* Homepage: http://web.archive.org/web/20110701014448/http://www.nytimes.com/
* Politics: http://web.archive.org/web/20120701051437/http://www.nytimes.com/pages/politics/index.html
* Top 10:
    - Can't use API. And Politics most popular missing on Internet Archive.
    - Fetched homepage top10: http://web.archive.org/web/20121022004730/http://www.nytimes.com/most-popular

8. WaPo:
--- http://web.archive.org/web/*/washingtonpost.com seems to run into robots.txt

