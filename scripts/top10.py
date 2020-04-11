#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import os
import argparse
import csv
import logging
import string
import gzip
from ftfy import fix_text

from zipfile import ZipFile, ZIP_DEFLATED

import newspaper
from newspaper import Article
from bs4 import BeautifulSoup
from scraper import SimpleScraper, SeleniumScraper

from datetime import datetime

from configparser import ConfigParser

from notification import Notification

import time
from selenium.webdriver.common.by import By

"""
CSV with following fields:
    date, time, src, url, order on the list, text of the link, 
    title of the article, path to local content file
    * Multiple folders --- one for each news org and
    containing content of the files in a standard format
    (after newspaper package), stripped off all HTML,
    name of each file = three_letter_src_name_date_time_order
"""

CSV_HEADER = ['date', 'time', 'src', 'src_list', 'url', 'order', 'link_text']

NEWSPAPER_HEADER = ['path', 'title', 'text', 'top_image', 'authors',
                    'summary', 'keywords']


MAX_RETRY = 5


def test_newspaper(url):
    paper = newspaper.build(url)

    for article in paper.articles:
        print(article.url)

    for category in paper.category_urls():
        print(category)


def setup_logger():
    """ Set up logging
    """
    # create logs dir if not exists
    if not os.path.exists('./logs'):
        os.makedirs('./logs')

    now = datetime.utcnow()
    logfilename = "./logs/top10-{0:s}.log".format(now.strftime('%Y%m%d%H%M%S'))

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename=logfilename,
                        filemode='a')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    return logfilename


def remove_special_chars(text):
    """remove all special characters except the period (.)
       and question mark (?)
       for instance, ">", "~", ", $, |, etc.
    """
    schars = ''.join([a for a in string.punctuation if a not in ".?"])
    text = re.sub('[%s]' % re.escape(schars), '', text)

    return text


def clean_text(text):
    text = fix_text(text)
    text = ' '.join(text.split('\n'))
    text = remove_special_chars(text)
    return text


def get_record_template(src, src_list=''):
    now = datetime.utcnow()
    data = {}
    data['date'] = now.strftime('%Y-%m-%d')
    data['time'] = now.strftime('%H:%M:%S')
    data['src'] = src
    data['src_list'] = src_list
    return data


def washingtonpost_top_politics(n=5, results=None):
    if results is None:
        results = []

    scraper = SimpleScraper()
    html = scraper.get('https://www.washingtonpost.com/politics/?nid=top_nav_politics')
    if not html:
        logging.error("Cannot get website")
        return results

    soup = BeautifulSoup(html, 'html.parser')

    for a in soup.select('.story-headline h3 a'):
        data = get_record_template('washingtonpost', 'top-politics')
        data['url'] = a['href']
        data['link_text'] = a.text
        if data not in results:
            results.append(data)
        if len(results) >= n:
            break
    return results


def washingtonpost_mostread(section='politics', n=5, results=None):
    if results is None:
        results = []
    scraper = SimpleScraper()
    html = scraper.get('https://www.washingtonpost.com/{0:s}'.format(section))
    if not html:
        logging.error("Cannot get website")
        return results

    soup = BeautifulSoup(html, 'html.parser')
    most_read = soup.find('div', {'id': 'post-most-rr'})
    for h in most_read.select('div.headline'):
        a = h.parent
        if a.name != 'a':
            continue
        data = get_record_template('washingtonpost',
                                   'mostread-{0:s}'.format(section))
        data['url'] = a['href']
        data['link_text'] = h.text
        if data not in results:
            results.append(data)
        if len(results) >= n:
            break
    return results


def washingtonpost_topmost(n=5, results=None):
    if results is None:
        results = []

    scraper = SimpleScraper()
    html = scraper.get('https://www.washingtonpost.com/pb/themost/')
    if not html:
        logging.error("Cannot get website")
        return results

    soup = BeautifulSoup(html, 'html.parser')
    for div in soup.select('.feed-link'):
        if 'feed-title' in div['class']:
            continue
        data = get_record_template('washingtonpost', 'themost-atlantic')
        try:
            data['link_text'] = div.span.text.strip()
        except:
            continue
        onclick = div['onclick']
        m = re.match("window\.open\('(.*?)'.*", onclick)
        if m:
            data['url'] = m.group(1)
            if data not in results:
                results.append(data)
            if len(results) >= n:
                break
    return results


def nyt_mostviewed(section='national', time_period=1, offet=0, n=5, results=None, api_key=''):
    if results is None:
        results = []

    """
    REF: https://developer.nytimes.com/most_popular_api_v2.json
    https://api.nytimes.com/svc/mostpopular/v2/mostviewed/all-sections/1.json?api_key=e9857cefff754d7dacad8df079a803c0
    https://api.nytimes.com/svc/mostpopular/v2/mostviewed/national/1.json?api_key=e9857cefff754d7dacad8df079a803c0
    Example :-
        {
          "status": "string",
          "copyright": "string",
          "num_results": 0,
          "results": [
            {
              "url": "string",
              "column": "string",
              "section": "string",
              "byline": "string",
              "title": "string",
              "abstract": "string",
              "published_date": "string",
              "source": "string"
            }
          ]
        }
    """
    scraper = SimpleScraper()
    url = 'https://api.nytimes.com/svc/mostpopular/v2/mostviewed/{0}/{1}.json?api-key={2}'.format(section, time_period, api_key)
    json_str = scraper.get(url)
    if not json_str:
        logging.error("Cannot get website")
        return results

    j = json.loads(json_str)
    for r in j['results']:
        data = get_record_template('nyt', 'mostviewed-{0:s}'.format(section))
        data['url'] = r['url']
        data['link_text'] = r['title']
        if data not in results:
            results.append(data)
        if len(results) >= n:
            break
    return results


def wsj_twitter_pop():
    # TODO:
    pass


def wsj_mostpop(n=5, results=None):
    if results is None:
        results = []

    scraper = SimpleScraper()
    html = scraper.get('http://www.wsj.com/')
    if not html:
        logging.error("Cannot get website")
        return results

    with open('html/wsj-mostpop.html', 'w', encoding='utf-8') as f:
        f.write(html)

    soup = BeautifulSoup(html, 'lxml')
    for a in soup.select('.wsj-popular-list.article .wsj-popular-item .pop-item-link'):
        data = get_record_template('wsj', 'mostpop')
        data['url'] = a['href']
        data['link_text'] = a.text
        if data not in results:
            results.append(data)
        if len(results) >= n:
            break
    return results


def wsj_mostpop_politics(n=5, results=None):
    if results is None:
        results = []

    scraper = SimpleScraper()
    html = scraper.get('http://www.wsj.com/news/politics')
    if not html:
        logging.error("Cannot get website")
        return results

    with open('html/wsj-mostpop-politics.html', 'w', encoding='utf-8') as f:
        f.write(html)

    soup = BeautifulSoup(html, 'lxml')
    for a in soup.select('.wsj-popular-list.article .wsj-popular-item .pop-item-link'):
        data =get_record_template('wsj', 'mostpop-politics')
        data['url'] = a['href']
        data['link_text'] = a.text
        if data not in results:
            results.append(data)
        if len(results) >= n:
            break
    return results


def foxnews_mostpop(section='politics', n=5, results=None):
    if results is None:
        results = []

    """
        There is JSON API
        http://www.foxnews.com/feeds/trending/all/feed/json?callback=articles
        http://www.foxnews.com/feeds/trending/politics/feed/json?callback=articles
    """
    scraper = SimpleScraper()
    json_str = scraper.get('http://www.foxnews.com/feeds/trending/{0:s}/feed/json?callback=articles'
                           .format(section))
    if not json_str:
        logging.error("Cannot get website")
        return results

    m = re.match('articles\((.*)\)', json_str, flags=re.S)
    if m:
        json_str = m.group(1)
    j = json.loads(json_str)
    for d in j['response']['docs']:
        data = get_record_template('foxnews', 'mostpop-{0:s}'.format(section))
        data['url'] = d['url'][0]
        data['link_text'] = d['title']
        if data not in results:
            results.append(data)
        if len(results) >= n:
            break
    return results


def foxnews_feeds(section='national', n=5, results=None):
    if results is None:
        results = []

    scraper = SimpleScraper()
    html = scraper.get('http://feeds.foxnews.com/foxnews/{0:s}'
                       .format(section))
    if not html:
        logging.error("Cannot get website")
        return results

    soup = BeautifulSoup(html, 'lxml')
    for item in soup.select('item'):
        data = get_record_template('foxnews', 'feeds-{0:s}'.format(section))
        data['url'] = item.select('guid')[0].text
        data['link_text'] = item.select('title')[0].text
        if data not in results:
            results.append(data)
        if len(results) >= n:
            break
    return results


def huffingtonpost_mostpop(n=5, results=None):
    if results is None:
        results = []

    """
    There is JSON API
    http://www.huffpost.com/mapi/v2/us/trending?device=desktop&statsType=rawPageView&statsPlatform=desktop&algo=trending
    """
    scraper = SimpleScraper()
    json_str = scraper.get('http://www.huffpost.com/mapi/v2/us/trending?device=desktop&statsType=rawPageView&statsPlatform=desktop&algo=trending')
    if not json_str:
        logging.error("Cannot get website")
        return results

    j = json.loads(json_str)
    urls = []
    for e in j['results']['entries']:
        if e['section_name'].lower() == 'politics':
            data = get_record_template('huffingtonpost', 'mostpop-politics')
            data['url'] = e['huffpost_url']
            data['link_text'] = e['label']
            if data not in results:
                results.append(data)
        if len(results) >= n:
            break
    return results


def huffingtonpost_trending(n=5, results=None):
    if results is None:
        results = []

    scraper = SeleniumScraper()
    html = scraper.get('http://www.huffpost.com/')
    if not html:
        logging.error("Cannot get website")
        return results

    soup = BeautifulSoup(html, 'lxml')
    trending = soup.find('div', {'id': 'trending-zone'})
    for a in trending.select('h2 a.card__link'):
        data = get_record_template('huffingtonpost', 'trending')
        data['url'] = a['href']
        data['link_text'] = a.text
        if data not in results:
            results.append(data)
        if len(results) >= n:
            break
    return results


def usatoday_mostpop(n=5, results=None):
    if results is None:
        results = []

    """
    There is only 4 items
    """
    scraper = SimpleScraper()
    html = scraper.get('http://www.usatoday.com/')
    if not html:
        logging.error("Cannot get website")
        return results

    with open('html/usatoday-mostpop.html', 'w', encoding='utf-8') as f:
        f.write(html)

    soup = BeautifulSoup(html, 'lxml')
    urls = []
    for a in soup.select('.hfwmm-light-list-link')[:n]:
        data = get_record_template('usatoday', 'mostpop')
        data['url'] = 'http://www.usatoday.com' + a['href']
        data['link_text'] = a.text.strip()
        if data not in results:
            results.append(data)
        if len(results) >= n:
            break

    return results


def google_news(n=5, results=None):
    if results is None:
        results = []

    scraper = SimpleScraper()
    html = scraper.get('https://news.google.com/')
    if not html:
        logging.error("Cannot get website")
        return results

    with open('html/google-news.html', 'w', encoding='utf-8') as f:
        f.write(html)

    soup = BeautifulSoup(html, 'lxml')
    for a in soup.select('.top-stories-section h2 .article'):
        data = get_record_template('google', 'mostpop')
        data['url'] = a['href']
        data['link_text'] = a.text
        if data not in results:
            results.append(data)
        if len(results) >= n:
            break
    return results


def google_news_politics(n=5, results=None):
    if results is None:
        results = []

    scraper = SimpleScraper()
    html = scraper.get('https://news.google.com/?ned=us&topic=po')
    if not html:
        logging.error("Cannot get website")
        return results

    with open('html/google-news-politics.html', 'w', encoding='utf-8') as f:
        f.write(html)

    soup = BeautifulSoup(html, 'lxml')
    for a in soup.select('h2 a.article'):
        data = get_record_template('google', 'mostpop-politics')
        data['url'] = a['href']
        data['link_text'] = a.text
        if data not in results:
            results.append(data)
        if len(results) >= n:
            break
    return results


def yahoo_news(n=5, results=None):
    if results is None:
        results = []

    scraper = SeleniumScraper()
    html = scraper.get('https://www.yahoo.com/news/')
    if not html:
        logging.error("Cannot get website")
        return results

    with open('html/yahoo-news.html', 'w', encoding='utf-8') as f:
        f.write(html)

    soup = BeautifulSoup(html, 'lxml')
    for h2 in soup.select('h2'):
        if h2.parent.name == 'a':
            href = h2.parent['href']
            if href.startswith('/news/'):
                data = get_record_template('yahoo', 'mostpop')
                data['url'] = 'https://www.yahoo.com' + href
                data['link_text'] = h2.text
                if data not in results:
                    results.append(data)
        if len(results) >= n:
            return results

    for h3 in soup.select('h3'):
        if h3.a:
            href = h3.a['href']
            if href.startswith('/news/'):
                data = get_record_template('yahoo', 'mostpop')
                data['url'] = 'https://www.yahoo.com' + href
                data['link_text'] = h3.a.text
                if data not in results:
                    results.append(data)
        if len(results) >= n:
            break
    return results


def yahoo_news_top_politics(n=5, results=None, src_list='original'):
    if results is None:
        results = []

    button = {'original': 'Yahoo Originals',
            'ap': 'AP',
            'reuters': 'Reuters'}

    prov = {'original': 'YahooNews',
            'ap': 'AssociatedPress',
            'reuters': 'Reuters'}

    # FIXME: retry a few times to workaround sometime failed change provider.
    retry = 0
    while retry < 5:
        scraper = SeleniumScraper()
        html = scraper.get('http://news.yahoo.com/most-popular/?pt=BureoF4GVB/?format=rss')
        if not html:
            logging.error("Cannot get website")
            return results

        try:
            drv = scraper.driver
            elem = drv.find_element(By.XPATH,
                                    '//a[@data-action-outcome="slcfltr" \
                                     and contains(text(), "{0}")]'
                                    .format(button[src_list]))
            elem.click()
            # FIXME: delay to make sure content updated. 
            time.sleep(5)
            html = scraper.driver.page_source
        except Exception as e:
            logging.error(str(e))
            return results

        with open('html/yahoo-news-top-politics-{0}.html'.format(src_list),
                  'w', encoding='utf-8') as f:
            f.write(html)

        soup = BeautifulSoup(html, 'lxml')

        for li in soup.select('li.content'):
            for h3 in li.select('h3'):
                if h3.a:
                    href = h3.a['href']
                    match = False
                    try:
                        data_ylk = h3.a['data-ylk']
                        meta = data_ylk.split(';')
                        for m in meta:
                            if m.startswith('prov'):
                                key, value = m.split(':')
                                if value == prov[src_list]:
                                    match = True
                                    break
                    except:
                        pass
                    if not match:
                        continue
                    if href.startswith('https://www.yahoo.com/news/'):
                        data = get_record_template('yahoo', 'mostpop-{0:s}'
                                                   .format(src_list))
                        data['url'] = href
                        data['link_text'] = h3.a.text
                        if data not in results:
                            results.append(data)
                if len(results) >= n:
                    return results
        retry += 1
        logging.info("Failed to change Yahoo news provider, retry #{0:d}"
                     .format(retry))
    return results


def rss_yahoo_news_top_politics(n=5, results=None, src_list='original'):
    if results is None:
        results = []

    sources = {'original': 'yahoo',
               'ap': 'ap.org',
               'reuters': 'reuters.com'}

    retry = 0
    while retry < 5:
        scraper = SimpleScraper()
        html = scraper.get('https://news.yahoo.com/rss/politics')
        if not html:
            logging.error("Cannot get website")
            return results

        with open('html/yahoo-news-top-politics-{0}.html'.format(src_list),
                  'w', encoding='utf-8') as f:
            f.write(html)

        soup = BeautifulSoup(html, 'xml')

        for item in soup.select('item'):
            source_url = item.source['url']
            if source_url.find(sources[src_list]) != -1:
                href = item.link.text
                if href.startswith('https://news.yahoo.com/'):
                    data = get_record_template('yahoo', 'mostpop-{0:s}'
                                               .format(src_list))
                    data['url'] = href
                    data['link_text'] = item.title.text
                    if data not in results:
                        results.append(data)
            if len(results) >= n:
                return results
        retry += 1
        logging.info("Failed to change Yahoo news provider, retry #{0:d}"
                     .format(retry))
    return results


def process_newspaper(r, compress=False):
    retry = 0
    while retry < MAX_RETRY:
        try:
            logging.info("Processing URL {0:s}".format(r['url']))
            article = Article(url=r['url'])
            article.download()
            dt = r['date'].replace('-', '') + r['time'].replace(':', '')
            name = '{0!s}_{1!s}_{2:d}.html'.format(r['src'], dt, r['order'])
            outdir = './news/{0!s}'.format(r['src'])
            if not os.path.exists(outdir):
                os.mkdir(outdir)
            filename = os.path.join(outdir, name)
            if compress:
                filename += '.gz'
                with gzip.open(filename, 'wb') as f:
                    f.write(bytes(article.html, 'utf-8'))
            else:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(article.html)
            r['path'] = filename
            article.parse()
            r['text'] = clean_text(article.text)
            r['top_image'] = article.top_image
            r['authors'] = '|'.join(article.authors)
            r['title'] = clean_text(article.title)
            #print(article.images)
            #print(article.movies)
            article.nlp()
            r['summary'] = clean_text(article.summary)
            r['keywords'] = '|'.join(article.keywords)
            break
        except Exception as e:
            logging.error(e)
            retry += 1
            logging.warn("Retry #{0:d}".format(retry))
    return r


def write_to_csv(writer, results, compress=False):
    for i, r in enumerate(results):
        r['order'] = i + 1
        r = process_newspaper(r, compress)
        r['link_text'] = clean_text(r['link_text'])
        writer.writerow(r)


def load_config(args):
    config = ConfigParser()
    config.read(args.config)
    args.nyt_api_key = config.get('api', 'nyt_api_key')
    args.web_path = config.get('web', 'path')
    args.web_url = config.get('web', 'url')


def make_output_web_link(args):
    ts_str = args.timestamp.strftime('%Y%m%d-%H%M%S')
    filename = 'top10-output-{0:s}.zip'.format(ts_str)
    logging.info("Pushing output to web server... {0:s}".format(filename))
    filepath = os.path.join(args.web_path, filename)
    with ZipFile(filepath, 'w', ZIP_DEFLATED) as zf:
        zf.write(args.output)
    return (args.web_url + filename)


if __name__ == "__main__":
    timestamp = datetime.utcnow()
    logfilename = setup_logger()
    parser = argparse.ArgumentParser(description='Top News! scraper')
    parser.add_argument('-c', '--config', default='top10.cfg',
                        help='Configuration file')
    parser.add_argument('-n', '--count', type=int, default=10,
                        help='Top N')
    parser.add_argument('-o', '--output', default='output.csv',
                        help='Output file name')
    parser.add_argument('--with-header', dest='header', action='store_true',
                        help='Output with header at the first row')
    parser.set_defaults(header=False)
    parser.add_argument('--compress', dest='compress',
                        action='store_true',
                        help='Compress download HTML files')
    parser.set_defaults(compress=False)

    args = parser.parse_args()

    args.timestamp = timestamp

    load_config(args)

    logging.info(args)

    # to keep scraped data
    if not os.path.exists('./html'):
        os.mkdir('./html')

    # to keep news data
    if not os.path.exists('./news'):
        os.mkdir('./news')

    with open(args.output, 'a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER + NEWSPAPER_HEADER,
                                dialect='excel', quoting=csv.QUOTE_NONNUMERIC)
        if args.header:
            writer.writeheader()

        logging.info("Scraping Washington Post...")
        res = washingtonpost_mostread('politics', args.count / 2)
        res += washingtonpost_mostread('regional', args.count / 2)
        res += washingtonpost_topmost(args.count / 2)
        write_to_csv(writer, res, args.compress)

        logging.info("Scraping Newyork Times...")
        res = nyt_mostviewed('all-sections', n=args.count, api_key=args.nyt_api_key)
        res += nyt_mostviewed('national', n=args.count, api_key=args.nyt_api_key)
        res += nyt_mostviewed('politics', n=args.count, api_key=args.nyt_api_key)
        write_to_csv(writer, res, args.compress)

        logging.info("Scraping Wall Street Journal...")
        # FIXME: getting same link from either homepage or politics page.
        res = wsj_mostpop(args.count)
        #res = wsj_mostpop_politics(args.count, res)
        write_to_csv(writer, res, args.compress)

        logging.info("Scraping Foxnews...")
        res = foxnews_mostpop('politics', args.count)
        res += foxnews_mostpop('all', args.count)
        # FIXME: should get same res as above
        #res += foxnews_feeds('most-popular', args.count)
        res += foxnews_feeds('national', args.count)
        write_to_csv(writer, res, args.compress)

        logging.info("Scraping Huffington Post...")
        res = huffingtonpost_mostpop(args.count)
        # FIXME: seems no trending zone in the home page.
        # res += huffingtonpost_trending(args.count)
        write_to_csv(writer, res, args.compress)

        logging.info("Scraping USA Today...")
        res = usatoday_mostpop(args.count)
        write_to_csv(writer, res, args.compress)

        """ FIXME: Skipped, will update later
        logging.info("Scraping Google News...")
        res = google_news(args.count)
        res += google_news_politics(args.count / 2)
        write_to_csv(writer, res, args.compress)
        """
        
        logging.info("Scraping Yahoo News...")
        res = rss_yahoo_news_top_politics(args.count)
        res += rss_yahoo_news_top_politics(args.count, None, 'ap')
        res += rss_yahoo_news_top_politics(args.count, None, 'reuters')
        write_to_csv(writer, res, args.compress)

    logging.info("Done")

    body = ""
    if args.web_url != '':
        web_link = make_output_web_link(args)
        body += "Latest CSV output available at {0:s}\n".format(web_link)

    ts_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    notification = Notification(args.config)
    subject = 'Top New! scraper ({0:s})'.format(ts_str)
    body += "Please check out log file for more detail."
    notification.send_email(subject, body, logfilename)
