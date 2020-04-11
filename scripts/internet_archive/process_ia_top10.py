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

from glob import glob

from pprint import pprint


"""
CSV with following fields:
    date, time, src, url, text of the link, 
    title of the article, path to local content file
    * Multiple folders --- one for each news org and
    containing content of the files in a standard format
    (after newspaper package), stripped off all HTML,
    name of each file = three_letter_src_name_date_time_order
"""

CSV_HEADER = ['date', 'time', 'src', 'order', 'url', 'link_text']

NEWSPAPER_HEADER = ['path', 'title', 'text', 'top_image', 'authors',
                    'summary', 'keywords']


MAX_RETRY = 5


def setup_logger():
    """ Set up logging
    """
    logfilename = "process-ia-top10.log"

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


def process_newspaper(r):
    retry = 0
    while retry < MAX_RETRY:
        try:
            logging.info("Processing URL {0:s}".format(r['url']))
            article = Article(url=r['url'])
            article.download()
            dt = r['date'].replace('-', '') + r['time'].replace(':', '')
            name = '{0!s}_{1!s}_{2:d}.html'.format(r['src'], dt, r['order'])
            outdir = './ia-news-top10/{0!s}'.format(r['src'])
            if not os.path.exists(outdir):
                os.mkdir(outdir)
            filename = os.path.join(outdir, name) + '.gz'
            with gzip.open(filename, 'wb') as f:
                f.write(bytes(article.html, 'utf-8'))
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


def write_to_csv(writer, results, with_text=False):
    for i, r in enumerate(results):
        r['order'] = i + 1
        if with_text:
            r = process_newspaper(r)
            # FIXME: check and try to fix URL if no result from newspaper
            if 'title' not in r:
                # strip off URL params
                r['url'] = r['url'].split('?')[0]
                r['order'] = int(r['order'])
                print(r['url'])
                r = process_newspaper(r)
                if 'title' not in r:
                    # try original URL directly
                    split_url = r['url'].split('http://')
                    if len(split_url) > 1:
                        r['url'] = 'http://' + split_url[-1]
                        print("New URL: %s" % r['url'])
                        r = process_newspaper(r)
        r['link_text'] = clean_text(r['link_text'])
        writer.writerow(r)


def open_html(fn):
    print(fn)
    html = ''
    if fn.endswith('.gz'):
        try:
            with gzip.open(fn, 'rb') as f:
                html = f.read()
        except:
            print("Cannot open file '{0:s}".format(fn))
    else:
        print(fn)
        with open(fn, encoding='utf-8') as f:
            html = f.read()
    return html


def parse_yahoo_news(fn, year):
    results = []
    html = open_html(fn)
    soup = BeautifulSoup(html, 'lxml')
    if year == 2012:
        top = soup.select('div.yom-top-story-content-0')
        for t in top:
            for i in t.select('div.txt'):
                a = i.find('a')
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))
        if len(results) == 0:
            # FIXME: 2012/08/25 - 2012/09/13
            top = soup.select('ul.yom-list-large')
            for t in top:
                for i in t.select('div.txt'):
                    a = i.find('a')
                    text = a.text.strip()
                    href = a['href']
                    #print(text.encode('utf-8'), href)
                    results.append((text, href))
                break
    else:
        # FIXME: To process missing Yahoo Top10 after 2016/10/21 (#28)
        # However, it's not consistently with the origianl top10 script.
        soup = BeautifulSoup(html, 'lxml')
        for a in soup.select('h3.Mb(5px) a'):
            if 'O(n):f' not in a['class']:
                href = a['href'].split('?')[0   ]
                text = a.text.strip()
                results.append((text, href))
    return results


def parse_usatoday_news(fn, year):
    results = []
    html = open_html(fn)
    soup = BeautifulSoup(html, 'lxml')
    if year == 2012:
        top = soup.select('div.ranked-list')
        for t in top:
            for a in t.select('a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))
        top = soup.select('ul.hero-list')
        for t in top:
            for a in t.select('a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))
    else:
        top = soup.select('div.most-popular-sidebar-content')
        for t in top:
            for a in t.select('a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))

    return results


def parse_wsj_news(fn, year):
    results = []
    html = open_html(fn)
    soup = BeautifulSoup(html, 'lxml')
    if year == 2012:
        top = soup.select('div#mostPopularTab_panel_mostRead')
        for t in top:
            for a in t.select('a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), )
                results.append((text, href))
    else:
        top = soup.select('ol.wsj-popular-list')
        for t in top:
            for a in t.select('a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))
    return results


def parse_wsj_news_politics(fn, year):
    results = []
    html = open_html(fn)
    soup = BeautifulSoup(html, 'lxml')
    if year == 2012:
        # FIXME: No popular section
        top = soup.select('div#mostPopularTab_panel_mostRead')
        for t in top:
            for a in t.select('a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))
    else:
        top = soup.select('ol.wsj-popular-list')
        for t in top:
            for a in t.select('a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))

    return results


def parse_fox_news(fn, year):
    results = []
    html = open_html(fn)
    soup = BeautifulSoup(html, 'lxml')
    if year == 2012:
        top = soup.select('div.trending-descending')
        for t in top:
            for a in t.select('h3 a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))
    else:
        top = soup.select('section#trending')
        for t in top:
            for a in t.select('h3 a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))
    return results


def parse_fox_news_politics(fn, year):
    results = []
    html = open_html(fn)
    soup = BeautifulSoup(html, 'lxml')
    print(year)
    if year == 2012:
        top = soup.select('div.trending-descending')
        for t in top:
            for a in t.select('h3 a'):
                text = a.text.strip()
                href = a['href']
                results.append((text, href))
                #print(text.encode('utf-8'), href)
        #sys.exit()
    else:
        top = soup.select('div.mod-8')
        for t in top:
            for a in t.select('h3 a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))
        #sys.exit()

    return results


def parse_fox_news_trending(fn, year):
    results = []
    html = open_html(fn)
    soup = BeautifulSoup(html, 'lxml')
    print(year)
    if year == 2012:
        top = soup.select('div.ct-mod')
        for t in top:
            for a in t.select('h3 a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
        #sys.exit()
    else:
        top = soup.select('div.articles div.list > ul')
        for t in top:
            for a in t.select('li a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))
        #sys.exit()

    return results


def parse_hpmg_news(fn, year):
    results = []
    html = open_html(fn)
    soup = BeautifulSoup(html, 'lxml')
    if year == 2012:
        top = soup.select('div.snp_most_popular')
        for t in top:
            for a in t.select('a.snp_entry_title'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))
        #sys.exit()
    else:
        # FIXME: No data (AJAX)
        top = soup.select('div#right-rail-trending')
        for t in top:
            for a in t.select('h2 a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))
        #sys.exit()
    return results


def parse_hpmg_news_politics(fn, year):
    results = []
    html = open_html(fn)
    soup = BeautifulSoup(html, 'lxml')
    if year == 2012:
        top = soup.select('div.snp_most_popular')
        for t in top:
            for a in t.select('a.snp_entry_title'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))
        #sys.exit()
    else:
        # FIXME: No data (AJAX)
        top = soup.select('div#right-rail-trending')
        for t in top:
            for a in t.select('h2 a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))

    return results


def parse_nyt_news(fn, year):
    results = []
    html = open_html(fn)
    soup = BeautifulSoup(html, 'lxml')
    if year == 2012:
        top = soup.select('div.mostPopularTabbedModule')
        for t in top:
            for a in t.select('h3 a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))
        #sys.exit()
    else:
        # FIXME: No data (AJAX)
        top = soup.select('section#trending-list-container')
        for t in top:
            for a in t.select('h2 a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))
        #sys.exit()
    return results


def parse_nyt_news_politics(fn, year):
    results = []
    html = open_html(fn)
    soup = BeautifulSoup(html, 'lxml')
    if year == 2012:
        top = soup.select('div.mostPopularTabbedModule')
        for t in top:
            for a in t.select('h3 a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                if href.find('politics'):
                    results.append((text, href))
        #sys.exit()
    else:
        # FIXME: No data (AJAX)
        top = soup.select('section#trending-list-container')
        for t in top:
            for a in t.select('h2 a'):
                text = a.text.strip()
                href = a['href']
                #print(text.encode('utf-8'), href)
                results.append((text, href))
        #sys.exit()
    return results


if __name__ == "__main__":
    logfilename = setup_logger()
    parser = argparse.ArgumentParser(description='Parse Homepage and Download Article')
    parser.add_argument('directory', help="Scraped homepages directory")
    parser.add_argument('-o', '--output', default='output-ia-top10.csv',
                        help='Output file name')
    parser.add_argument('--with-header', dest='header', action='store_true',
                        help='Output with header at the first row')
    parser.set_defaults(header=False)

    parser.add_argument('--with-text', dest='with_text', action='store_true',
                        help='Download the article text')
    parser.set_defaults(with_text=False)

    args = parser.parse_args()

    logging.info(args)

    # to keep scraped data
    if not os.path.exists('./ia-news-top10'):
        os.mkdir('./ia-news-top10')

    with open(args.output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER + NEWSPAPER_HEADER,
                                dialect='excel', quoting=csv.QUOTE_NONNUMERIC)
        if args.header:
            writer.writeheader()

        for fn in sorted(glob(args.directory + '/*.html') +
                   glob(args.directory + '/*.gz')):
            #print("#{0:d} Processing: '{1:s}'".format(n, fn))

            m = re.match(r'(.*)_(\d{8})_?(\d{6})\.html(?:\.gz)?',
                         os.path.basename(fn))
            if m:
                src = '_'.join(m.group(1).split('_')[0:-1])
                d = m.group(2)
                t = m.group(3)
            else:
                print("Cannot match file name, skipped '{0:s}'".format(fn))
                continue
            #dt = '_'.join([d, t])
            year = int(d[:4])
            month = int(d[4:6])
            if year in [2012, 2016]:
                if month in range(7, 13):
                    #print(src)
                    if src == 'yahoo':
                        results = parse_yahoo_news(fn, year)
                    elif src == 'usat':
                        results = parse_usatoday_news(fn, year)
                    elif src == 'hpmg':
                        results = parse_hpmg_news(fn, year)
                    elif src == 'fox':
                        results = parse_fox_news(fn, year)
                    elif src == 'wsj':
                        results = parse_wsj_news(fn, year)
                    elif src == 'nyt':
                        results = parse_nyt_news(fn, year)
                    elif src == 'fox_politics':
                        results = parse_fox_news_politics(fn, year)
                    elif src == 'fox_trending':
                        results = parse_fox_news_trending(fn, year)
                    elif src == 'hpmg_politics':
                        results = parse_hpmg_news_politics(fn, year)
                    elif src == 'wsj_politics':
                        results = parse_wsj_news_politics(fn, year)
                    elif src == 'nyt_politics':
                        results = parse_nyt_news_politics(fn, year)
                    else:
                        print("Not implement parser for this news source: '%s'" % src)
                        continue
                    new_results = []
                    for text, url in results:
                        if not url.startswith('/'):
                            url = '/' + url
                        url = 'http://web.archive.org' + url
                        new_results.append({'src': src,
                                            'date': d,
                                            'time': t,
                                            'link_text': text,
                                            'url': url})
                    write_to_csv(writer, new_results, args.with_text)
    logging.info("Done")
