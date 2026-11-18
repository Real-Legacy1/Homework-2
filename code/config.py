"""Task: define constants used throughout the assignements"""

TLD_GROUPS = {
    'generic': {'com', 'net', 'org', .....},
    'country': {'us', 'uk', 'de', 'np', ....},
    'selected': {'xyz', 'top', 'shop', ...},
}

TABLE_SUFFIXES = {'generic': 'GenericTLDRecords', 'country': 'CountryTLDRecords', 'selected': 'SelectedTLDRecords'}
ROUTES = {key: f'POST /{key}' for key in TLD_GROUPS} 
METRIC_NAMESPACE = 'Coursework/PhishingTLDTracker'
FEED_URL = 'https://raw.githubusercontent.com/openphish/public_feed/refs/heads/main/feed.txt'
