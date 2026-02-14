import feedparser
import logging
import urllib.parse
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Priority Map (Lower number = Higher Priority)
SOURCE_PRIORITY = {
    # Official Government/International Bodies (Highest Priority)
    "pib.gov.in": 1,
    "ddnews.gov.in": 1,
    "newsonair.gov.in": 1,
    "imf.org": 1,
    "worldbank.org": 1,
    "who.int": 1,
    "rbi.org.in": 1,
    "sebi.gov.in": 1,
    "isro.gov.in": 1,
    "niti.gov.in": 1,
    "mea.gov.in": 1,
    
    # Trusted News Agencies
    "thehindu.com": 3,
    "indianexpress.com": 3,
    "livemint.com": 4,
    "economictimes": 4,
    "timesofindia": 5,
    "google": 6
}

# Standard RSS feeds
RSS_FEEDS = [
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://indianexpress.com/section/india/feed/",
    "https://www.livemint.com/rss/news",
    "https://economictimes.indiatimes.com/news/economy/rssfeeds/12416805.cms",
    "https://ddnews.gov.in/rss-feeds/national", 
    "https://pib.gov.in/newsite/rss_english.aspx",
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"
]

# Google News RSS Base URL
GOOGLE_NEWS_BASE = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

def get_google_news_url(query):
    """Generates a Google News RSS URL for a specific query."""
    encoded_query = urllib.parse.quote(query)
    return GOOGLE_NEWS_BASE.format(query=encoded_query)

# "Universalized" Data Collection Queries
CUSTOM_QUERIES = [
    # International Organizations
    "site:imf.org",
    "site:worldbank.org",
    "site:who.int",
    
    # Key Ministries & Bodies (Exam Relevant)
    "site:mea.gov.in",             # External Affairs
    "site:mof.gov.in",             # Finance
    "site:mha.gov.in",             # Home Affairs
    "site:moef.gov.in",            # Environment
    "site:isro.gov.in",            # Space
    "site:rbi.org.in",             # Economy/Banking
    "site:sebi.gov.in",            # Markets
    "site: नीति आयोग OR site:niti.gov.in", # NITI Aayog
    
    # Generic Important Topics
    "Supreme Court of India verdict",
    "Govt of India Scheme",
    "Constitutional Amendment"
]

def get_priority(link):
    """Returns priority score for a link based on domain."""
    for domain, score in SOURCE_PRIORITY.items():
        if domain in link:
            return score
    return 10 # Default low priority

def is_similar(a, b):
    """Returns True if string a and b are > 70% similar."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > 0.7

def deduplicate_articles(articles):
    """
    Removes duplicate stories from the list.
    If duplicates found, keeps the one from the higher priority source.
    """
    unique_articles = []
    
    # Sort articles by priority (important sources first)
    # Sort articles by priority (important sources first)
    articles.sort(key=lambda x: get_priority(x['link']))
    
    # Optimization: Process only the top 150 articles to prevent CPU hanging on O(N^2) loop
    # This still keeps the high-priority sources since we just sorted them to the top.
    if len(articles) > 150:
        logger.info(f"Limiting processing from {len(articles)} to top 150 priority articles.")
        articles = articles[:150]
    
    for article in articles:
        is_duplicate = False
        for unique in unique_articles:
            if is_similar(article['title'], unique['title']):
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_articles.append(article)
            
    logger.info(f"Deduplicated: Reduced {len(articles)} to {len(unique_articles)} articles.")
    return unique_articles

def cluster_articles(articles):
    """
    Groups similar articles into clusters.
    Returns a list of clusters, where each cluster is a list of article dicts.
    """
    clusters = []
    
    # Sort by priority so the "main" article of a cluster is usually a high-priority one
    articles.sort(key=lambda x: get_priority(x['link']))
    
    for article in articles:
        found_cluster = False
        for cluster in clusters:
            # Check similarity with the first article in the cluster (representative)
            if is_similar(article['title'], cluster[0]['title']):
                cluster.append(article)
                found_cluster = True
                break
        
        if not found_cluster:
            clusters.append([article])
            
    logger.info(f"Clustered {len(articles)} articles into {len(clusters)} groups.")
    return clusters

def fetch_news():
    """
    Fetches news from configured RSS feeds AND Google News queries.
    Returns a deduplicated list of dictionaries.
    """
    articles = []
    
    # 1. Fetch Standard Feeds
    all_feeds = RSS_FEEDS.copy()
    
    # 2. Add Google News Feeds
    for query in CUSTOM_QUERIES:
        all_feeds.append(get_google_news_url(query))

    for feed_url in all_feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                articles.append({
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'summary': entry.get('summary', '') or entry.get('description', ''),
                    'published': entry.get('published', '')
                })
        except Exception as e:
            logger.error(f"Error fetching from {feed_url}: {e}")
            
    logger.info(f"Fetched {len(articles)} articles raw.")
    
    # 3. Deduplicate
    return deduplicate_articles(articles)
