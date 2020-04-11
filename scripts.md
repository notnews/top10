## Running Top 10 News!

How to we set up live scraping and parsing the data, including setting up monitoring. 

## Table of Contents

1. [General installation](#general-installation)
    * [Prerequisites](#prerequisites)
    * [Installation](#installation)
    * [Configuration File](#configuration-file)
    * [Usage](#usage)
    * [Run](#run)

2. [Scraping and Parsing Live Homepages and Top 10 Lists](live_pages.md)

3. [Scraping Archived News and Top 10 lists on Internet Archive](internet_archive.md)

[Back](readme.md)

---------------

## General Installation

### Prerequisites

- Python 3.4+
- BeautifulSoup 4
- newspaper3k
- lxml
- selenium
- [PhantomJS 2.x](http://phantomjs.org/)

### Installation

On Ubuntu 16.04.4 LTS, install additional software packages by typing in:

```
sudo apt-get install git python-virtualenv libxslt-dev
```

We recommend that you install Python virtual environment:

```
cd top10
virtualenv -p python3 venv3
. venv3/bin/activate
```

Install Python requirements:

```
cd scripts
pip install -r requirements.txt
```

You will also need to install [PhantomJS 2.x](http://phantomjs.org/download.html) and make sure it's in your PATH.

In addition, you will need to download NLTK data files by the following command:

```
python -m nltk.downloader punkt
```

### Configuration file

[Configuration File](scripts/top10.cfg): 

```
[api]
# https://developer.nytimes.com/get-started
# Create an application and enable Most Popular API
nyt_api_key=

[notification]
smtp_server = smtp.gmail.com
smtp_port = 465
# https://accounts.google.com/SignUp
# And you must enable Less secure app access in the Google Account security setting
smtp_user = ?
smtp_pass = ?
smtp_ssl = true
email_from = ?
email_to = ?

[web]
path=/opt/top10/www
url=http://104.131.176.221:81/
```

- ``nyt_api_key``  NYT API Key please get it from https://developer.nytimes.com/signup
- ``smtp_server``  stmp.gmail.com will be used for Gmail account
- ``smtp_port``    465 is default port for Gmail
- ``smtp_user``    You can get one from https://accounts.google.com/SignUp
- ``smtp_pass``    Email account password
- ``email_from``   Should be same as the email account that will be used.
- ``email_to``     Destination Email addresses (separated by a comma if multiple)
- ``path``         HTTP server data directory
- ``url``          URL to the data directory
