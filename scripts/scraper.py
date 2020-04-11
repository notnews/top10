#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
import http.cookiejar
import os
import urllib.request
import urllib.parse
import urllib.error
import urllib.request
import urllib.error

from selenium import webdriver

cookie_filename = "cookies"


MAX_RETRY = 5

TIMEOUT = 30


class SimpleScraper():
    def __init__(self):
        self.cj = http.cookiejar.MozillaCookieJar(cookie_filename)
        if os.access(cookie_filename, os.F_OK):
            self.cj.load()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPRedirectHandler(),
            urllib.request.HTTPHandler(debuglevel=0),
            urllib.request.HTTPSHandler(debuglevel=0),
            urllib.request.HTTPCookieProcessor(self.cj)
        )
        self.opener.addheaders = [
            ('User-agent', ('Mozilla/5.0 (Windows NT 5.1; rv:24.0) Gecko/20100101 Firefox/24.0'))
        ]
        self.cj.save()

    def get(self, url, timeout=TIMEOUT):
        retry = 0
        while retry < MAX_RETRY:
            try:
                response = self.opener.open(url, timeout=timeout)
                text = ''.join(v.decode('utf-8', errors='ignore') for v in response.readlines())
                return text
            except Exception as e:
                logging.error(e)
                retry += 1
                time.sleep(retry)
                logging.warn('Retry #{0:d}...'.format(retry))
        return False

    def post(self, url, data):
        try:
            post_data = urllib.parse.urlencode(dict([k, v.encode('utf-8')]
                                               for k, v in list(data.items())))
            response = self.opener.open(url, post_data.encode())
            text = ''.join(v.decode('utf-8') for v in response.readlines())
            return text
        except:
            return False


class SeleniumScraper():
    def __init__(self, timeout=TIMEOUT):
        #  Assigning the user agent string for PhantomJS
        self.dcap = dict(webdriver.DesiredCapabilities.PHANTOMJS)
        self.dcap["phantomjs.page.settings.userAgent"] = ("Mozilla/5.0 (Windows NT 5.1; rv:24.0) Gecko/20100101 Firefox/24.0")

        # PhantomJS must be in PATH setting
        self.driver = webdriver.PhantomJS(desired_capabilities=self.dcap)

        # For testing
        #self.driver = webdriver.Firefox()

        self.driver.implicitly_wait(timeout)
        self.driver.set_page_load_timeout(timeout)

    def get(self, url):
        retry = 0
        while retry < MAX_RETRY:
            try:
                self.driver.get(url)
                html = self.driver.page_source
                return html
            except Exception as e:
                logging.error(e)
                retry += 1
                time.sleep(retry)
                logging.warn('Retry #{0:d}...'.format(retry))
        return False
