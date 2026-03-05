"""
============================================================
  PE FIRM EMAIL SCRAPER
============================================================
  Automatically finds Private Equity & Venture Capital firms 
  and their public contact emails from free sources:
  
  1. SEC EDGAR IAPD (Investment Advisor Public Disclosure)
  2. Google search for "[firm] contact email"
  3. Firm website contact page scraping
  
  Zero cost. No APIs needed.
============================================================
"""
import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import re
import os
import csv
import random

DATABASE = "cold_email.db"

HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"},
]

def _headers():
    return random.choice(HEADERS_LIST)

def _polite_get(url, timeout=15):
    """Fetch a URL with random delay and user agent."""
    time.sleep(random.uniform(2, 5))
    try:
        resp = requests.get(url, headers=_headers(), timeout=timeout)
        resp.raise_for_status()
        return resp
    except Exception as e:
        return None


# --- Database --------------------------------------------
def init_db():
    """Create the prospects & campaigns database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS prospects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firm_name TEXT NOT NULL,
            contact_name TEXT,
            email TEXT,
            title TEXT,
            website TEXT,
            source TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'new'
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER,
            email_type TEXT DEFAULT 'initial',
            subject TEXT,
            body TEXT,
            sent_at TIMESTAMP,
            opened INTEGER DEFAULT 0,
            replied INTEGER DEFAULT 0,
            bounced INTEGER DEFAULT 0,
            FOREIGN KEY (prospect_id) REFERENCES prospects(id)
        )
    """)
    
    c.execute("CREATE INDEX IF NOT EXISTS idx_prospect_email ON prospects(email)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_prospect_status ON prospects(status)")
    conn.commit()
    conn.close()


def save_prospect(firm_name, email, contact_name="", title="", website="", source=""):
    """Save one prospect, skip if duplicate."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    if email:
        c.execute("SELECT id FROM prospects WHERE email = ?", (email,))
    else:
        c.execute("SELECT id FROM prospects WHERE firm_name = ?", (firm_name,))
    
    if c.fetchone():
        conn.close()
        return False
    
    c.execute("""
        INSERT INTO prospects (firm_name, contact_name, email, title, website, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (firm_name, contact_name, email, title, website, source))
    
    conn.commit()
    conn.close()
    return True


def get_prospects_with_email():
    """Get new prospects that have email addresses."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM prospects WHERE email != '' AND status = 'new' ORDER BY added_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_total_prospect_count():
    """Count all prospects."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM prospects")
    count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE email != ''")
    with_email = c.fetchone()[0]
    conn.close()
    return count, with_email


# ===========================================================
# SOURCE 1: SEC EDGAR - Investment Adviser Search
# ===========================================================
def scrape_sec_adviser_search():
    """
    Scrapes SEC's Investment Adviser Public Disclosure (IAPD) 
    for registered PE/VC firms with their public contact info.
    """
    print("\n[CHART] Scraping SEC EDGAR Investment Advisers...")
    found = 0
    
    # SEC EDGAR company search - look for PE/VC related filings
    search_terms = [
        "private equity",
        "venture capital", 
        "growth equity",
        "capital partners",
        "investment partners",
    ]
    
    for term in search_terms:
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?company={requests.utils.quote(term)}&CIK=&type=D&dateb=&owner=include&count=20&search_text=&action=getcompany"
        
        resp = _polite_get(url)
        if not resp:
            continue
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Parse the company results table
        table = soup.find("table", class_="tableFile2")
        if not table:
            continue
        
        for row in table.find_all("tr")[1:]:  # Skip header
            cells = row.find_all("td")
            if len(cells) >= 2:
                company_link = cells[0].find("a")
                if company_link:
                    firm_name = company_link.get_text(strip=True)
                    cik_href = company_link.get("href", "")
                    
                    # Filter for PE/VC sounding names
                    pe_keywords = ["capital", "partners", "ventures", "equity", "fund", 
                                   "investment", "advisors", "management", "group"]
                    if any(kw in firm_name.lower() for kw in pe_keywords):
                        website = f"https://www.sec.gov{cik_href}" if cik_href.startswith("/") else ""
                        
                        was_new = save_prospect(
                            firm_name=firm_name,
                            email="",  # We'll find emails in step 2
                            website=website,
                            source="SEC_EDGAR"
                        )
                        if was_new:
                            found += 1
        
        if found >= 50:
            break
    
    print(f"   [OK] Found {found} PE/VC firms from SEC EDGAR")
    return found


# ===========================================================
# SOURCE 2: Top Tier Curated Firm List
# ===========================================================
def scrape_pe_directories():
    """Load a curated list of known active PE/VC firms."""
    print("\n[FIRM] Loading top tier VC and PE firm profiles...")
    
    top_firms = [
        ("Sequoia Capital", "https://www.sequoiacap.com"),
        ("Andreessen Horowitz", "https://a16z.com"),
        ("Lightspeed Venture Partners", "https://lsvp.com"),
        ("Benchmark", "https://benchmark.com"),
        ("Founders Fund", "https://foundersfund.com"),
        ("Index Ventures", "https://www.indexventures.com"),
        ("Accel", "https://www.accel.com"),
        ("Bessemer Venture Partners", "https://www.bvp.com"),
        ("Greylock Partners", "https://greylock.com"),
        ("Khosla Ventures", "https://www.khoslaventures.com"),
        ("Tiger Global Management", "https://www.tigerglobal.com"),
        ("Insight Partners", "https://www.insightpartners.com"),
        ("New Enterprise Associates", "https://www.nea.com"),
        ("General Catalyst", "https://www.generalcatalyst.com"),
        ("First Round Capital", "https://firstround.com"),
        ("Thrive Capital", "https://thrivecap.com"),
        ("Union Square Ventures", "https://www.usv.com"),
        ("Battery Ventures", "https://www.battery.com"),
        ("Redpoint Ventures", "https://www.redpoint.com"),
        ("Matrix Partners", "https://www.matrixpartners.com"),
        ("CRV", "https://www.crv.com"),
        ("Spark Capital", "https://www.sparkcapital.com"),
        ("Kleiner Perkins", "https://www.kleinerperkins.com"),
        ("GV (Google Ventures)", "https://www.gv.com"),
        ("Bain Capital Ventures", "https://baincapitalventures.com")
    ]
    
    found = 0
    for name, url in top_firms:
        was_new = save_prospect(
            firm_name=name,
            email="",
            website=url,
            source="Curated_Top_Tier"
        )
        if was_new:
            found += 1
            
    print(f"   [OK] Loaded {found} top-tier firms into pipeline")
    return found


# ===========================================================
# SOURCE 2B: High-Volume Global VC Scraping (Google Dorks)
# ===========================================================
def scrape_massive_vc_lists():
    """Dynamically discover hundreds of VC/PE firms worldwide using Crunchbase Dorks."""
    print("\n[FIRM] Executing High-Volume Crunchbase VC Indexing...")
    
    found = 0
    # Search Google for Crunchbase profiles of venture firms
    queries = [
        'site:crunchbase.com/organization "venture capital"',
        'site:crunchbase.com/organization "private equity" "investments"',
        'site:crunchbase.com/organization "Seed stage" "venture"',
        'site:crunchbase.com/organization "Series A" "lead investor"'
    ]
    
    for query in queries:
        for page in range(0, 30, 10): # Scrape multiple Google pages per query
            url = f"https://www.google.com/search?q={requests.utils.quote(query)}&start={page}"
            resp = _polite_get(url)
            if not resp:
                continue
                
            soup = BeautifulSoup(resp.text, "html.parser")
            for g in soup.find_all('div', class_='g'):
                title_elem = g.find('h3')
                if title_elem:
                    # e.g., "Andreessen Horowitz - Crunchbase Investor Profile" -> "Andreessen Horowitz"
                    raw_title = title_elem.text
                    firm_name = raw_title.split("-")[0].split("|")[0].replace("Crunchbase", "").replace("Investor Profile", "").replace("Company Profile", "").strip()
                    
                    if len(firm_name) > 3 and "http" not in firm_name:
                        # Only save the name. Website will trigger Google Email Dorking later.
                        was_new = save_prospect(
                            firm_name=firm_name,
                            email="",
                            website="", # Blank website forces the LinkedIn/Twitter Email Dork directly!
                            source="Crunchbase_Dorks"
                        )
                        if was_new:
                            found += 1
            
            time.sleep(1) # Polite delay for Google pages
            
            if found >= 150: # Cap it per run to avoid flooding the DB instantly
                break
        if found >= 150:
            break
            
    print(f"   [OK] Indexed {found} NEW global PE/VC firms via Web-Graph")
    return found



# ===========================================================
# SOURCE 3: Find emails from firm websites
# ===========================================================
import concurrent.futures

def findemails_on_website(website_url):
    """Visit a firm's website and extract HUMAN email addresses (no info@)."""
    if not website_url or not website_url.startswith("http"):
        return []
    
    emails = set()
    
    # Try pages where partners are listed
    pages_to_try = [
        website_url,
        website_url.rstrip("/") + "/team",
        website_url.rstrip("/") + "/people",
        website_url.rstrip("/") + "/about",
        website_url.rstrip("/") + "/contact",
    ]
    
    for page_url in pages_to_try:
        resp = _polite_get(page_url, timeout=10)
        if not resp:
            continue
        
        # Find all email addresses in the page
        found = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resp.text)
        
        for email in found:
            email = email.lower()
            # Junk domains/extensions
            junk = [".png", ".jpg", ".gif", ".css", ".js", "example.com", "email.com", 
                    "domain.com", "company.com", "sentry.io", "w3.org", "sentry", "wordpress"]
            
            # Generic prefixes we DO NOT want to cold email
            generic_prefixes = ["info@", "contact@", "hello@", "press@", "media@", 
                                "jobs@", "careers@", "support@", "admin@", "sales@",
                                "privacy@", "legal@", "compliance@", "team@"]
            
            if any(j in email for j in junk):
                continue
                
            if any(email.startswith(g) for g in generic_prefixes):
                continue
                
            # If it passed all filters, it's likely a real person's email (e.g., j.smith@ or john@)
            emails.add(email)
            
            # If we found 3 good personal emails, that's enough for this firm
            if len(emails) >= 3:
                return list(emails)
                
    return list(emails)


def enrich_prospects_with_emails():
    """Go through firms without emails and try to find their email from their website quickly."""
    print("\n[EMAIL] Finding partner/MD email addresses...")
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get firms without emails. We now process them even if their website is blank (we use LinkedIn Dorks)
    c.execute("SELECT * FROM prospects WHERE (email = '' OR email IS NULL) LIMIT 100")
    prospects = [dict(r) for r in c.fetchall()]
    conn.close()
    
    if not prospects:
        print("   ℹ️  No prospects need email enrichment")
        return 0
        
    enriched = 0
    print(f"   [FAST] Spinning up threads for {len(prospects)} targets...")

    def process_prospect(p):
        website = p.get('website', "")
        if website:
            emails = findemails_on_website(website)
            if emails:
                return p, emails[0], "website"
        
        # Fallback to Google Search (LinkedIn/Twitter bio Dorks)
        google_emails = _search_email_google(p['firm_name'])
        if google_emails:
            return p, google_emails[0], "google_dorks"
        
        return p, None, None

    # Run in parallel to crush the 15-minute wait down to ~15 seconds
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_prospect, prospects))

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    for p, email, found_source in results:
        if email:
            c.execute("UPDATE prospects SET email = ? WHERE id = ?", (email, p['id']))
            enriched += 1
            if found_source == "website":
                print(f"       [OK] Found on site: {email} ({p['firm_name'][:20]})")
            else:
                print(f"       [OK] Found via Dorks: {email} ({p['firm_name'][:20]})")
    conn.commit()
    conn.close()
    
    print(f"\n   [EMAIL] Enriched {enriched}/{len(prospects)} PE/VC firms with personal emails")
    return enriched


def _search_email_google(firm_name):
    """Find a firm's personal partner email via advanced Platform Dorking."""
    
    # Clean up firm name "Firm Name VC" -> "Firm Name"
    clean_name = firm_name.lower().replace(" ventures", "").replace(" capital", "").replace(" partners", "").strip()
    
    # Advanced Dork strategies for discovering emails on global platforms
    dorks = [
        f'site:linkedin.com/in "{firm_name}" (partner OR "managing director") "@*.*"',
        f'site:twitter.com "{firm_name}" OR "{clean_name}" (partner OR investor) "@*.*"',
        f'"{firm_name}" (partner OR "managing director" OR team) email'
    ]
    
    clean_emails = []
    
    for query in dorks:
        url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
        resp = _polite_get(url)
        if not resp:
            continue
            
        found = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resp.text)
        
        # Filter junk & generic addresses
        junk = ["example.com", "email.com", "google", "sentry", "w3.org", "schema", "twitter.com", "linkedin.com"]
        generic = ["info@", "contact@", "hello@", "press@", "team@", "support@", "admin@", "sales@", "jobs@", "privacy@"]
        
        for e in found:
            e = e.lower()
            if not any(j in e for j in junk) and not any(e.startswith(g) for g in generic):
                clean_emails.append(e)
                
        if clean_emails:
            # If we found personal emails utilizing this specific dork, don't ping Google anymore.
            break
            
        time.sleep(1.5)  # Be polite to Google
            
    return list(set(clean_emails))[:1]


# ===========================================================
# MANUAL CSV LOADING
# ===========================================================
def load_from_csv(filepath):
    """Load prospects from CSV (firm_name,contact_name,email,title,website)."""
    if not os.path.exists(filepath):
        print(f"   [FAIL] File not found: {filepath}")
        return 0
    
    added = 0
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            was_new = save_prospect(
                firm_name=row.get("firm_name", ""),
                email=row.get("email", ""),
                contact_name=row.get("contact_name", ""),
                title=row.get("title", ""),
                website=row.get("website", ""),
                source="Manual_CSV"
            )
            if was_new:
                added += 1
    
    print(f"   [OK] Loaded {added} new prospects from {filepath}")
    return added


def create_sample_csv():
    """Create a sample CSV template."""
    filepath = "prospects_template.csv"
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["firm_name", "contact_name", "email", "title", "website"])
        writer.writerow(["Sequoia Capital", "John Smith", "info@sequoiacap.com", "Partner", "https://www.sequoiacap.com"])
        writer.writerow(["Andreessen Horowitz", "Jane Doe", "contact@a16z.com", "Principal", "https://a16z.com"])
    print(f"   [FILE] Template created: {filepath}")
    print(f"   Edit it with real data, then the pipeline will auto-load it.")


# ===========================================================
# MASTER SCRAPE FUNCTION (called by run.py)
# ===========================================================
def scrape_all_pe_firms():
    """Run all PE firm scrapers and enrich with emails."""
    print("\n" + "=" * 60)
    print("  [FIRM] SCRAPING PE/VC FIRM EMAILS")
    print("=" * 60)
    
    init_db()
    
    # Load from CSV if it exists
    if os.path.exists("prospects_template.csv"):
        load_from_csv("prospects_template.csv")
    
    # Scrape public sources
    scrape_sec_adviser_search()
    scrape_pe_directories()
    scrape_massive_vc_lists()
    
    # Enrich with emails
    enrich_prospects_with_emails()
    
    total, with_email = get_total_prospect_count()
    print(f"\n   [CHART] Total prospects: {total} ({with_email} with email addresses)")
    
    return with_email


if __name__ == "__main__":
    import sys
    
    init_db()
    
    if "--template" in sys.argv:
        create_sample_csv()
    elif "--load" in sys.argv:
        idx = sys.argv.index("--load")
        if idx + 1 < len(sys.argv):
            load_from_csv(sys.argv[idx + 1])
    elif "--scrape" in sys.argv:
        scrape_all_pe_firms()
    else:
        print("Usage:")
        print("  python prospects.py --template     Create sample CSV")
        print("  python prospects.py --load file    Load from CSV")
        print("  python prospects.py --scrape       Scrape all sources")
