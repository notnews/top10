#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import csv
import logging
import gzip
from datetime import datetime

from scraper import SeleniumScraper

from notification import Notification


def setup_logger():
    """ Set up logging
    """
    # create logs dir if not exists
    if not os.path.exists('./logs'):
        os.makedirs('./logs')

    now = datetime.utcnow()
    logfilename = "./logs/homepage-{0:s}.log".format(now.strftime('%Y%m%d%H%M%S'))

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename=logfilename,
                        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    return logfilename


def download_webpage(url, filepath, compress=False):
    scraper = SeleniumScraper()
    html = scraper.get(url)
    if not html:
        html = ''

    logging.info("Saving to file {0:s}".format(filepath))
    if compress:
        with gzip.open(filepath, 'wb') as f:
            f.write(bytes(html, 'utf-8'))
    else:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)


if __name__ == "__main__":
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    logfilename = setup_logger()
    parser = argparse.ArgumentParser(description='Homepages scraper')
    parser.add_argument('input', default=None)
    parser.add_argument('-c', '--config', default='top10.cfg',
                        help='Configuration file')
    parser.add_argument('-d', '--dir', default='homepages',
                        help='Output directory for HTML files')
    parser.add_argument('--compress', dest='compress',
                        action='store_true',
                        help='Compress download HTML files')
    parser.set_defaults(compress=False)
    args = parser.parse_args()

    logging.info(args)

    # to keep scraped data
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)

    with open(args.input) as f:
        reader = csv.DictReader(f)
        for r in reader:
            src = r['src']
            url = r['url']
            logging.info("Visit URL: {0:s}".format(url))
            dt = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            name = '{0:s}_{1:s}.html'.format(src, dt)
            filepath = os.path.join(args.dir, name)
            if args.compress:
                filepath += '.gz'
            download_webpage(url, filepath, args.compress)

    logging.info("Done")

    notification = Notification(args.config)
    subject = 'Homepages scraper ({0:s})'.format(timestamp)
    body = "Please check out log file for more detail."
    notification.send_email(subject, body, logfilename)
