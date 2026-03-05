"""
================================================================
  PRODUCTION SCRAPERS - Reliable multi-source deal flow data
================================================================
  Sources that ACTUALLY WORK and return real deal flow signals:
  1. Hacker News (Show HN, startup launches)
  2. Google News RSS (fundraising, M&A, IPO keywords)
  3. TechCrunch RSS (startup/VC news)
  4. VentureBeat RSS (AI/enterprise deals)
  5. SEC EDGAR Full-Text Search API (filings)
================================================================
"""
import requests
from bs4 import BeautifulSoup
import time
import re
import random

# Import config safely
try:
    import config
    MAX_LEADS = config.MAX_LEADS_PER_SOURCE
    DELAY = config.SCRAPE_DELAY_SECONDS
except Exception:
    MAX_LEADS = 20
    DELAY = 1.5

def _safe(text):
    """Strip non-ASCII for safe Windows printing."""
    if not text:
        return ""
    return text.encode('ascii', errors='replace').decode('ascii')

def _headers():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    ]
    return {"User-Agent": random.choice(agents)}

def _get(url, timeout=15):
    """Fetch URL with delay and random user agent."""
    time.sleep(DELAY)
    try:
        r = requests.get(url, headers=_headers(), timeout=timeout)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"   [WARN] {_safe(str(e)[:100])}")
        return None


# ============================================================
# 1. HACKER NEWS
# ============================================================
def scrape_hackernews():
    """Front page + Show HN for startup signals."""
    print("\n[1] Scraping Hacker News...")
    leads = []
    
    for page_url in ["https://news.ycombinator.com/", "https://news.ycombinator.com/shownew"]:
        r = _get(page_url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for item in soup.select(".titleline > a"):
            title = item.text.strip()
            link = item.get("href", "")
            if link.startswith("item?"):
                link = f"https://news.ycombinator.com/{link}"
            leads.append({"headline": title, "url": link, "source": "HackerNews"})
            if len(leads) >= MAX_LEADS:
                break
    
    print(f"   [OK] {len(leads)} items")
    return leads[:MAX_LEADS]


# ============================================================
# 2. GOOGLE NEWS RSS (fundraising / M&A keywords)
# ============================================================
def scrape_google_news():
    """Google News RSS for deal-related keywords."""
    print("\n[2] Scraping Google News RSS...")
    leads = []
    
    queries = [
        "startup+raises+funding+2025",
        "company+acquired+acquisition+2025",
        "Series+A+funding+round",
        "startup+IPO+filing",
        "private+equity+deal",
    ]
    
    for query in queries:
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        r = _get(url)
        if not r:
            continue
        
        try:
            soup = BeautifulSoup(r.text, "xml")
            for item in soup.find_all("item"):
                title_tag = item.find("title")
                link_tag = item.find("link")
                if title_tag and title_tag.text:
                    leads.append({
                        "headline": title_tag.text.strip(),
                        "url": link_tag.text.strip() if link_tag else "",
                        "source": "GoogleNews"
                    })
                if len(leads) >= MAX_LEADS:
                    break
        except Exception as e:
            print(f"   [WARN] XML parse: {_safe(str(e)[:60])}")
        
        if len(leads) >= MAX_LEADS:
            break
    
    print(f"   [OK] {len(leads)} items")
    return leads[:MAX_LEADS]


# ============================================================
# 3. TECHCRUNCH RSS (startup / VC news)
# ============================================================
def scrape_techcrunch():
    """TechCrunch RSS feed for startup and VC news."""
    print("\n[3] Scraping TechCrunch RSS...")
    leads = []
    
    feeds = [
        "https://techcrunch.com/feed/",
        "https://techcrunch.com/category/venture/feed/",
    ]
    
    for feed_url in feeds:
        r = _get(feed_url)
        if not r:
            continue
        
        try:
            soup = BeautifulSoup(r.text, "xml")
            for item in soup.find_all("item"):
                title_tag = item.find("title")
                link_tag = item.find("link")
                if title_tag and title_tag.text:
                    leads.append({
                        "headline": title_tag.text.strip(),
                        "url": link_tag.text.strip() if link_tag else "",
                        "source": "TechCrunch"
                    })
                if len(leads) >= MAX_LEADS:
                    break
        except Exception as e:
            print(f"   [WARN] XML parse: {_safe(str(e)[:60])}")
        
        if len(leads) >= MAX_LEADS:
            break
    
    print(f"   [OK] {len(leads)} items")
    return leads[:MAX_LEADS]


# ============================================================
# 4. VENTUREBEAT RSS (AI / enterprise deal news)
# ============================================================
def scrape_venturebeat():
    """VentureBeat RSS for enterprise AI and deal news."""
    print("\n[4] Scraping VentureBeat RSS...")
    leads = []
    
    r = _get("https://venturebeat.com/feed/")
    if not r:
        print(f"   [OK] 0 items")
        return leads
    
    try:
        soup = BeautifulSoup(r.text, "xml")
        for item in soup.find_all("item"):
            title_tag = item.find("title")
            link_tag = item.find("link")
            if title_tag and title_tag.text:
                leads.append({
                    "headline": title_tag.text.strip(),
                    "url": link_tag.text.strip() if link_tag else "",
                    "source": "VentureBeat"
                })
            if len(leads) >= MAX_LEADS:
                break
    except Exception as e:
        print(f"   [WARN] XML parse: {_safe(str(e)[:60])}")
    
    print(f"   [OK] {len(leads)} items")
    return leads[:MAX_LEADS]


# ============================================================
# 5. SEC EDGAR FULL-TEXT SEARCH API
# ============================================================
def scrape_sec_edgar():
    """SEC EDGAR full-text search for fundraising filings."""
    print("\n[5] Scraping SEC EDGAR API...")
    leads = []
    
    # Use the modern EFTS (EDGAR Full-Text Search) API
    search_url = "https://efts.sec.gov/LATEST/search-index"
    queries = ["raises funding", "Series A", "acquisition merger"]
    
    for query in queries:
        params = {
            "q": f'"{query}"',
            "dateRange": "custom",
            "startdt": "2025-01-01",
            "forms": "8-K,S-1,D",
        }
        
        try:
            r = requests.get(
                search_url, params=params,
                headers={"User-Agent": "DealFlowBot research@example.com", "Accept": "application/json"},
                timeout=15
            )
            if r.status_code != 200:
                # Fallback: try the EDGAR company search
                continue
            
            data = r.json()
            hits = data.get("hits", {}).get("hits", [])
            
            for hit in hits[:10]:
                source_data = hit.get("_source", {})
                company = source_data.get("display_names", ["Unknown"])[0] if source_data.get("display_names") else "Unknown"
                form_type = source_data.get("form_type", "")
                file_date = source_data.get("file_date", "")
                
                leads.append({
                    "headline": f"SEC {form_type}: {company} ({file_date})",
                    "url": f"https://www.sec.gov/cgi-bin/browse-edgar?company={requests.utils.quote(company)}&CIK=&type={form_type}&dateb=&owner=include&count=5&search_text=&action=getcompany",
                    "source": "SEC_EDGAR"
                })
            
            if len(leads) >= MAX_LEADS:
                break
                
        except Exception as e:
            print(f"   [WARN] EDGAR: {_safe(str(e)[:60])}")
        
        time.sleep(1)
    
    print(f"   [OK] {len(leads)} items")
    return leads[:MAX_LEADS]


# ============================================================
# 6. CRUNCHBASE NEWS RSS
# ============================================================
def scrape_crunchbase_news():
    """Crunchbase News for funding rounds and acquisitions."""
    print("\n[6] Scraping Crunchbase News RSS...")
    leads = []
    
    r = _get("https://news.crunchbase.com/feed/")
    if not r:
        print(f"   [OK] 0 items")
        return leads
    
    try:
        soup = BeautifulSoup(r.text, "xml")
        for item in soup.find_all("item"):
            title_tag = item.find("title")
            link_tag = item.find("link")
            if title_tag and title_tag.text:
                leads.append({
                    "headline": title_tag.text.strip(),
                    "url": link_tag.text.strip() if link_tag else "",
                    "source": "Crunchbase"
                })
            if len(leads) >= MAX_LEADS:
                break
    except Exception as e:
        print(f"   [WARN] XML parse: {_safe(str(e)[:60])}")
    
    print(f"   [OK] {len(leads)} items")
    return leads[:MAX_LEADS]


# ============================================================
# 7. BUSINESS INSIDER RSS
# ============================================================
def scrape_business_insider():
    """Business Insider for M&A and deal news."""
    print("\n[7] Scraping Business Insider RSS...")
    leads = []
    
    feeds = [
        "https://markets.businessinsider.com/rss/news",
    ]
    
    for feed_url in feeds:
        r = _get(feed_url)
        if not r:
            continue
        try:
            soup = BeautifulSoup(r.text, "xml")
            for item in soup.find_all("item"):
                title_tag = item.find("title")
                link_tag = item.find("link")
                if title_tag and title_tag.text:
                    leads.append({
                        "headline": title_tag.text.strip(),
                        "url": link_tag.text.strip() if link_tag else "",
                        "source": "BusinessInsider"
                    })
                if len(leads) >= MAX_LEADS:
                    break
        except Exception as e:
            print(f"   [WARN] XML parse: {_safe(str(e)[:60])}")
    
    print(f"   [OK] {len(leads)} items")
    return leads[:MAX_LEADS]


# ============================================================
# 8. FORBES BUSINESS / DEALS RSS
# ============================================================
def scrape_forbes():
    """Forbes business section for deal signals."""
    print("\n[8] Scraping Forbes RSS...")
    leads = []
    
    feeds = [
        "https://www.forbes.com/innovation/feed/",
        "https://www.forbes.com/business/feed/",
    ]
    
    for feed_url in feeds:
        r = _get(feed_url)
        if not r:
            continue
        try:
            soup = BeautifulSoup(r.text, "xml")
            for item in soup.find_all("item"):
                title_tag = item.find("title")
                link_tag = item.find("link")
                if title_tag and title_tag.text:
                    leads.append({
                        "headline": title_tag.text.strip(),
                        "url": link_tag.text.strip() if link_tag else "",
                        "source": "Forbes"
                    })
                if len(leads) >= MAX_LEADS:
                    break
        except Exception as e:
            print(f"   [WARN] XML parse: {_safe(str(e)[:60])}")
        if len(leads) >= MAX_LEADS:
            break
    
    print(f"   [OK] {len(leads)} items")
    return leads[:MAX_LEADS]


# ============================================================
# 9. REDDIT r/startups + r/venturecapital (JSON API)
# ============================================================
def scrape_reddit():
    """Reddit startup/VC subreddits for deal flow chatter."""
    print("\n[9] Scraping Reddit startup subs...")
    leads = []
    
    subs = ["startups", "venturecapital", "smallbusiness"]
    
    for sub in subs:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=15"
        r = _get(url)
        if not r:
            continue
        
        try:
            data = r.json()
            for post in data.get("data", {}).get("children", []):
                post_data = post.get("data", {})
                title = post_data.get("title", "")
                permalink = post_data.get("permalink", "")
                if title:
                    leads.append({
                        "headline": title,
                        "url": f"https://reddit.com{permalink}" if permalink else "",
                        "source": "Reddit"
                    })
                if len(leads) >= MAX_LEADS:
                    break
        except Exception as e:
            print(f"   [WARN] Reddit: {_safe(str(e)[:60])}")
        
        if len(leads) >= MAX_LEADS:
            break
    
    print(f"   [OK] {len(leads)} items")
    return leads[:MAX_LEADS]


# ============================================================
# 10. SIFTED RSS (European Startups)
# ============================================================
def scrape_sifted():
    """Sifted for European deal flow."""
    print("\n[10] Scraping Sifted (EU) RSS...")
    leads = []
    
    r = _get("https://sifted.eu/feed")
    if not r:
        return leads
    
    try:
        soup = BeautifulSoup(r.text, "xml")
        for item in soup.find_all("item"):
            title_tag = item.find("title")
            link_tag = item.find("link")
            if title_tag and title_tag.text:
                leads.append({
                    "headline": title_tag.text.strip(),
                    "url": link_tag.text.strip() if link_tag else "",
                    "source": "Sifted_EU"
                })
            if len(leads) >= MAX_LEADS:
                break
    except Exception as e:
        print(f"   [WARN] XML parse: {_safe(str(e)[:60])}")
    
    print(f"   [OK] {len(leads)} items")
    return leads[:MAX_LEADS]


# ============================================================
# 11. STRICTLYVC (Top daily VC newsletter)
# ============================================================
def scrape_strictlyvc():
    """StrictlyVC for daily deal announcements."""
    print("\n[11] Scraping StrictlyVC...")
    leads = []
    
    r = _get("https://www.strictlyvc.com/feed/")
    if not r:
        return leads
    
    try:
        soup = BeautifulSoup(r.text, "xml")
        for item in soup.find_all("item"):
            title_tag = item.find("title")
            link_tag = item.find("link")
            if title_tag and title_tag.text:
                leads.append({
                    "headline": title_tag.text.strip(),
                    "url": link_tag.text.strip() if link_tag else "",
                    "source": "StrictlyVC"
                })
            if len(leads) >= MAX_LEADS:
                break
    except Exception as e:
        print(f"   [WARN] XML parse: {_safe(str(e)[:60])}")
    
    print(f"   [OK] {len(leads)} items")
    return leads[:MAX_LEADS]


# ============================================================
# 12. GEEKWIRE (Pacific Northwest & Enterprise tech)
# ============================================================
def scrape_geekwire():
    """GeekWire for PNW and enterprise deals."""
    print("\n[12] Scraping GeekWire RSS...")
    leads = []
    
    r = _get("https://www.geekwire.com/feed/")
    if not r:
        return leads
    
    try:
        soup = BeautifulSoup(r.text, "xml")
        for item in soup.find_all("item"):
            title_tag = item.find("title")
            link_tag = item.find("link")
            if title_tag and title_tag.text:
                leads.append({
                    "headline": title_tag.text.strip(),
                    "url": link_tag.text.strip() if link_tag else "",
                    "source": "GeekWire"
                })
            if len(leads) >= MAX_LEADS:
                break
    except Exception as e:
        print(f"   [WARN] XML parse: {_safe(str(e)[:60])}")
    
    print(f"   [OK] {len(leads)} items")
    return leads[:MAX_LEADS]


# ============================================================
# 13. GLOBAL PLATFORMS (Twitter, LinkedIn, Bloomberg Dorks)
# ============================================================
def scrape_global_platforms():
    """Use Google Dorks to scrape Twitter and LinkedIn for early funding announcements."""
    print("\n[13] Scraping Global Platforms (Twitter/LinkedIn) via Dorks...")
    leads = []
    
    # "we are raising" OR "just closed our seed" OR "series a funding"
    queries = [
        'site:twitter.com ("we are raising" OR "just closed our seed" OR "announcing our series a")',
        'site:linkedin.com/posts ("we are raising" OR "just closed our seed" OR "announcing our series a")'
    ]
    
    for query in queries:
        url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
        r = _get(url)
        if not r:
            continue
            
        try:
            soup = BeautifulSoup(r.text, "html.parser")
            # Google search result blocks
            for g in soup.find_all('div', class_='g'):
                title_elem = g.find('h3')
                link_elem = g.find('a', href=True)
                
                if title_elem and link_elem:
                    headline = title_elem.text.strip()
                    url_link = link_elem['href']
                    
                    # Filter out messy Google redirect URLs if necessary
                    if url_link.startswith('/url?q='):
                        url_link = url_link.split('/url?q=')[1].split('&')[0]
                        
                    source_name = "Twitter_Lead" if "twitter.com" in query else "LinkedIn_Lead"
                    
                    leads.append({
                        "headline": headline,
                        "url": url_link,
                        "source": source_name
                    })
                if len(leads) >= MAX_LEADS:
                    break
        except Exception as e:
            print(f"   [WARN] Global platforms: {_safe(str(e)[:60])}")
            
        # Polite delay between Google queries
        time.sleep(1.5)
        
    print(f"   [OK] {len(leads)} items")
    return leads[:MAX_LEADS]


# ============================================================
# MASTER: Run all scrapers
# ============================================================
def scrape_all_sources():
    """Run ALL 13 scrapers and combine results."""
    print("=" * 50)
    print("  SCRAPING 13 SOURCES")
    print("=" * 50)
    
    all_leads = []
    
    scrapers = [
        scrape_hackernews,
        scrape_google_news,
        scrape_techcrunch,
        scrape_venturebeat,
        scrape_sec_edgar,
        scrape_crunchbase_news,
        scrape_business_insider,
        scrape_forbes,
        scrape_reddit,
        scrape_sifted,
        scrape_strictlyvc,
        scrape_geekwire,
        scrape_global_platforms,
    ]
    
    for scraper in scrapers:
        try:
            results = scraper()
            all_leads.extend(results)
        except Exception as e:
            print(f"   [FAIL] {scraper.__name__}: {_safe(str(e)[:80])}")
    
    print(f"\n[TARGET] Total leads gathered: {len(all_leads)}")
    return all_leads


if __name__ == "__main__":
    leads = scrape_all_sources()
    print(f"\nSample leads:")
    for lead in leads[:5]:
        print(f"  [{lead['source']}] {_safe(lead['headline'][:70])}")

