#!/usr/bin/env bash

. /opt/top10/venv3/bin/activate
export PATH=/opt/phantomjs-2.1.1-linux-x86_64/bin:$PATH
cd /opt/top10/scripts
python top10.py
python homepage.py homepage.csv
python homepage.py -d politics_homepages politics_homepage.csv 
