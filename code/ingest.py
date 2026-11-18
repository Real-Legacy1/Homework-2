"""Task: download feed text, parse URLs, classify and POST to three routes."""
import argparse
import requests
import tldextract
from urllib.parse import urlsplit
from config import FEED_URL, TLD_GROUPS

# URL: https://raw.githubusercontent.com/openphish/public_feed/refs/heads/main/feed.txt
def parse_url(url):
    """Task: extract protocol, hostname, public suffix, final TLD label, domain, subdomain, path"""
    raise NotImplementedError


def classify_tld(tld):
    """Task: return classified tld data"""
    raise NotImplementedError


def submit_record(base_url, group, record):
    """Task: submit post request to f'{base_url}/{group}'"""
    raise NotImplementedError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=100)
    args = parser.parse_args()
    # Task:integrate the above parse and post request API 
    raise NotImplementedError


if __name__ == '__main__':
    main()
