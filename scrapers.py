import requests
from bs4 import BeautifulSoup
import time
import random

def _polite_get(url):
    time.sleep(random.uniform(1, 3))
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        return r if r.status_code == 200 else None
    except:
        return None

def fetch_market_headlines():
    headlines = []
    print("\n[FIND] Scraping live YCombinator & HackerNews deal signals...")
    
    url = "https://news.ycombinator.com/item?id=4327"  # Fallback for stable testing if frontpage fails
    frontpage = _polite_get("https://news.ycombinator.com/")
    if frontpage:
        soup = BeautifulSoup(frontpage.text, "html.parser")
        for item in soup.find_all('span', class_='titleline'):
            title = item.find('a').text
            # Filter for business signals
            keywords = ["raise", "seed", "series", "acquire", "launch", "revenue", "grow", "saas", "fund"]
            if any(k in title.lower() for k in keywords):
                headlines.append({"title": title, "source": "HackerNews"})
                
    # Also fetch SEC RSS feed for Form D
    print("   [+] Pulling SEC EDGAR Form D (Private Fundraises)...")
    sec_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=D&company=&dateb=&owner=include&count=40&output=atom"
    sec_resp = _polite_get(sec_url)
    if sec_resp:
        soup = BeautifulSoup(sec_resp.text, "xml")
        for entry in soup.find_all('entry'):
            tt = entry.title.text
            if "Form D" in tt:
                headlines.append({"title": f"Private Equity Raise: {tt}", "source": "SEC EDGAR"})
                
    return headlines
