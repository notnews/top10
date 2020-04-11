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

"""
CSV with following fields:
    date, time, src, url, text of the link, 
    title of the article, path to local content file
    * Multiple folders --- one for each news org and
    containing content of the files in a standard format
    (after newspaper package), stripped off all HTML,
    name of each file = three_letter_src_name_date_time_order
"""

CSV_HEADER = ['date', 'time', 'src', 'order', 'url', 'link_text',
              'homepage_keywords']

NEWSPAPER_HEADER = ['path', 'title', 'text', 'top_image', 'authors',
                    'summary', 'keywords']


MAX_RETRY = 5

LINKS_CONF = {'fox':
              [('20110101_000000',
                {'css': ['a'],
                 're': [r'.*/\d{4}/\d{2}/\d{2}/.*/$'
                        ],
                 'base': 'http://web.archive.org'
                 }
                )],
              'google':
              [('20110101_000000',
                {'css': ['a', {'class': 'article'}],
                 're': [r'.*'],
                 'base': 'http://web.archive.org'
                 }
                )],
              'hpmg':
              [('20110101_000000',
                {'css': ['a'],
                 're': [r'.*www.huffingtonpost.com/.{5,}/.*html$'
                        ],
                 'base': 'http://web.archive.org'
                 }
                )],
              'nyt':
              [('20110101_000000',
                {'css': ['a'],
                 're': [r'.*/\d{4}/\d{2}/\d{2}/.*html$'
                        ],
                 'base': 'http://web.archive.org'
                 }
                )],
              'usat':
              [('20120929_111519',
                {'css': ['a'],
                 're': [r'.*/\d{4}/\d{2}/\d{2}.*'
                        ],
                 'base': 'http://web.archive.org'
                 }
                ),
               ('20110101_000000',
                {'css': ['a'],
                 're': [r'.*/\d{4}-\d{2}-\d{2}.*'
                        ],
                 'base': 'http://web.archive.org'
                 }
                )],
              'wapo':
              [('20110101_000000',
                {'css': ['a'],
                 're': [r'.*'
                        ],
                 'base': 'http://web.archive.org'
                 }
                )],
              'wsj':
              [('20110101_000000',
                {'css': ['a'],
                 're': [r'.*http://online.wsj.com/article/.*'
                        ],
                 'base': 'http://web.archive.org'
                 }
                )],
              'yahoo':
              [('20120101_000000',
                {'css': ['a'],
                 're': [r'.*\.yahoo\.com/.*\d{9}(?:\-\-.*)?.html'
                        ],
                 'base': 'http://web.archive.org'
                 }
                ),
               ('20110101_000000',
                {'css': ['a'],
                 're': [r'.*http://news.yahoo.com/.*/\d{8}/.*'
                        ],
                 'base': 'http://web.archive.org'
                 }
                )],
              }

# Global to keep unique URLs
urls = set()


def setup_logger():
    """ Set up logging
    """
    logfilename = "process-ia-homepage.log"

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
            outdir = './news-ia-homepage/{0!s}'.format(r['src'])
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


def write_to_csv(writer, results, with_text=False, unique=False):
    global urls
    order = 1
    for i, r in enumerate(results):
        if unique:
            if r['url'] in urls:
                print("Duplicate")
                continue
            else:
                urls.add(r['url'])
        r['order'] = order
        if with_text:
            # FIXME: check and try to fix URL if no result from newspaper
            r = process_newspaper(r)
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
        order += 1


def process_homepage(src, d, t, fn, conf):
    if fn.endswith('.gz'):
        try:
            with gzip.open(fn, 'rb') as f:
                html = f.read()
        except:
            print("Cannot open file '{0:s}".format(fn))
            html = ''
    else:
        with open(fn, encoding='utf-8') as f:
            html = f.read()

    try:
        article = Article(url='')
        article.set_html(html)
        article.parse()
        article.nlp()
        keywords = '|'.join(article.keywords)
    except Exception as e:
        keywords = ''
    soup = BeautifulSoup(html, 'lxml')
    links = soup.find_all(*conf['css'])
    results = set()
    for r in conf['re']:
        rc = re.compile(r)
        for a in links:
            try:
                href = a['href']
                if rc.match(href):
                    url = conf['base'] + href
                    text = a.text.strip()
                    results.add((text, url))
            except:
                pass
    new_results = []
    for text, url in results:
        new_results.append({'src': src,
                            'date': d,
                            'time': t,
                            'link_text': text,
                            'url': url,
                            'homepage_keywords': keywords})
    return new_results


if __name__ == "__main__":
    logfilename = setup_logger()
    parser = argparse.ArgumentParser(description='Parse Homepage and Download Article')
    parser.add_argument('directory', help="Scraped homepages directory")
    parser.add_argument('-o', '--output', default='output-ia-homepage.csv',
                        help='Output file name')
    parser.add_argument('--with-header', dest='header', action='store_true',
                        help='Output with header at the first row')
    parser.set_defaults(header=False)

    parser.add_argument('--with-text', dest='with_text', action='store_true',
                        help='Download the article text')
    parser.set_defaults(with_text=False)

    parser.add_argument('--unique', dest='unique', action='store_true',
                        help='Keep only unique articles links')
    parser.set_defaults(unique=False)

    args = parser.parse_args()

    logging.info(args)

    # to keep scraped data
    if not os.path.exists('./news-ia-homepage'):
        os.mkdir('./news-ia-homepage')

    with open(args.output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER + NEWSPAPER_HEADER,
                                dialect='excel', quoting=csv.QUOTE_NONNUMERIC)
        if args.header:
            writer.writeheader()

        print(LINKS_CONF.keys())
        n = 1
        for fn in sorted(glob(args.directory + '/*.html') +
                         glob(args.directory + '/*.gz')):
            print("#{0:d} Processing: '{1:s}'".format(n, fn))

            m = re.match(r'(.*)_(\d{8})_?(\d{6})\.html(?:\.gz)?',
                         os.path.basename(fn))
            if m:
                src = m.group(1).split('_')[0]
                d = m.group(2)
                t = m.group(3)
            else:
                print("Cannot match file name, skipped '{0:s}'".format(fn))
                continue
            dt = '_'.join([d, t])
            if src in LINKS_CONF.keys():
                for i in LINKS_CONF[src]:
                    if dt >= i[0]:
                        results = process_homepage(src, d, t, fn, i[1])
                        write_to_csv(writer, results, arg.with_text, args.unique)
                        break
            n += 1

    logging.info("Done")
