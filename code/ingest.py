"""Task: download feed text, parse URLs, classify and POST to three routes."""
import argparse
import requests
import tldextract
from urllib.parse import urlsplit
from config import FEED_URL, TLD_GROUPS
from pathlib import Path

# URL: https://raw.githubusercontent.com/openphish/public_feed/refs/heads/main/feed.txt

def parse_url(url):
    urls = urlsplit(url)
    protocol = urls.scheme
    hostname = urls.hostname
    path = urls.path
    extracted = tldextract.extract(url)
    public_suffix = extracted.suffix
    tld = public_suffix.split(".")[-1]
    sld = extracted.domain
    subdomain = extracted.subdomain
    return {
    "url": url,
    "protocol": protocol,
    "hostname": hostname,
    "path": path,
    "public_suffix": public_suffix, 
    "tld": tld,
    "second_level_domain": sld,
    "third_level_domain": subdomain
}


def classify_tld(tld):
    for i in TLD_GROUPS:
        if tld in TLD_GROUPS[i]:
            return i
    return 'unknown'


def submit_record(base_url, group, record):
    """Task: submit post request to f'{base_url}/{group}'"""
    response = requests.post(f"{base_url.rstrip('/')}/{group}", json=record, timeout=15)
    response.raise_for_status()
    return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=100)
    args = parser.parse_args()
    # Task:integrate the above parse and post request API 
    endpoint_file = Path(__file__).resolve().parent / "api_endpoint.txt"
    base_url = endpoint_file.read_text().strip()
    feed_url = FEED_URL
    response = requests.get(feed_url, timeout=15)
    response.raise_for_status()
    urls = response.text.strip().splitlines()
    urls = [line.strip() for line in urls if line.strip()]
    unmatched = 0
    successful = 0
    failed = 0
    for url in urls[:args.limit]:
        parsed = parse_url(url)
        group = classify_tld(parsed['tld'])

        if group == 'unknown':
            unmatched += 1
            continue

        try:
            submit_record(base_url, group, parsed)
            successful += 1
        except requests.RequestException as error:
            failed += 1
            print(f"Submission failed for {group}: {error}")
    processed = successful + failed + unmatched
    print(f"Processed: {processed}")
    print(f"Successful: {successful}, Failed: {failed}, Unmatched: {unmatched}")


if __name__ == '__main__':
    main()
