#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import csv
import logging
import gzip
from bs4 import BeautifulSoup
from scraper import SimpleScraper, SeleniumScraper
from random import randint
import requests


IA_WEB_BASE_URL = 'http://web.archive.org'


def setup_logger():
    """ Set up logging
    """
    logfilename = "ia-scraper.log"

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


def download_webpage(url, filepath, compress=False, selenium=False):
    scraper = SimpleScraper()
    html = scraper.get(url)
    if selenium:
        if not html or html.find('Redirecting to...') != -1:
            return
        scraper = SeleniumScraper()
        html = scraper.get(url)
        scraper.driver.close()
    if not html:
        html = ''

    logging.info("Saving to file {0:s}".format(filepath))

    if compress:
        with gzip.open(filepath, 'wb') as f:
            f.write(bytes(html, 'utf-8'))
    else:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)


def get_web_archive_snapshots(base_url, ia_url, year):
    url_fmt = '{0:s}/__wb/calendarcaptures?url={1:s}&selected_year={2:d}'
    url = url_fmt.format(base_url, ia_url, year)
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    headers = {'User-Agent': user_agent}
    r = requests.get(url, headers=headers)
    ts = []
    if r.status_code == 200:
        a = r.json()
        for b in a:
            for c in b:
                for d in c:
                    if d and 'ts' in d:
                        ts.extend(d['ts'])

    url_fmt = '/web/{0:d}/{1:s}'
    snapshots = []
    for s in ts:
        url = url_fmt.format(s, ia_url)
        snapshots.append(url)

    return snapshots


if __name__ == "__main__":
    logfilename = setup_logger()
    parser = argparse.ArgumentParser(description='Homepages scraper')
    parser.add_argument('input', default=None)
    parser.add_argument('-c', '--config', default='top10.cfg',
                        help='Configuration file')
    parser.add_argument('-d', '--dir', default='internet_archive',
                        help='Output directory for HTML files')
    parser.add_argument('--overwritten', dest='overwritten',
                        action='store_true',
                        help='Overwritten if HTML file exists')
    parser.set_defaults(overwritten=False)
    parser.add_argument('-s', '--statistics', dest='statistics',
                        action='store_true',
                        help='Run the script to count amount of snapshots')
    parser.set_defaults(statistics=False)
    parser.add_argument('--compress', dest='compress',
                        action='store_true',
                        help='Compress download HTML files')
    parser.set_defaults(compress=False)
    parser.add_argument('--selenium', dest='selenium',
                        action='store_true',
                        help='Use Selenium to download dynamics HTML content')
    parser.set_defaults(selenium=False)
    args = parser.parse_args()

    logging.info(args)

    # to keep scraped data
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)

    with open(args.input) as f:
        reader = csv.DictReader(f)
        total = 0
        for r in reader:
            src = r['src']
            ia_url = r['ia_url']
            if ia_url == '':
                continue
            end = int(r['ia_year_end'][:4])
            begin = int(r['ia_year_begin'][:4])
            current = end
            sub_total = 0
            while current >= begin:
                logging.info("Visit yearly snapshots: {0:d}".format(current))
                links = get_web_archive_snapshots(IA_WEB_BASE_URL, ia_url, current)
                if not args.statistics:
                    for l in links:
                        href = l
                        print(href)
                        today = href.split('/')[2]
                        logging.info("Today: {0:s}".format(today))
                        month = int(today[4:6])
                        date = today[:8]
                        if date <= r['ia_year_begin'] or date >= r['ia_year_end']:
                            continue
                        filename = '{0:s}_ia_{1:s}.html'.format(src, today)
                        filepath = os.path.join(args.dir, filename)
                        if args.compress:
                            filepath += '.gz'
                        if args.overwritten or not os.path.exists(filepath):
                            url = IA_WEB_BASE_URL + href
                            download_webpage(url, filepath, args.compress, args.selenium)
                        else:
                            logging.info("Existing, skipped...")
                        #break
                logging.info("Year: {0:d}, {1:d} snapshots"
                             .format(current, len(links)))
                sub_total += len(links)
                current -= 1
                #break
            logging.info("Source: {0:s}, {1:d} snapshots"
                         .format(src, sub_total))
            total += sub_total
            #break
        logging.info("Total: {0:d} snapshots".format(total))
    logging.info("Done")
