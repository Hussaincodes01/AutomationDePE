# Deal Flow Engine - Production System

**AI-powered deal flow intelligence for PE/VC firms.**
Scrapes 9 sources, scores leads with AI, cold-emails PE firms automatically.

---

## Quick Start (3 steps)

```bash
cd d:\CIS\deal_flow_engine

# 1. Install dependencies (one time only)
pip install -r requirements.txt

# 2. Edit .env with your API key (already done if you followed setup)

# 3. Run everything
start.bat
```

That's it. The system scrapes leads, scores them with AI, and stores everything.

---

## What It Does

```
9 websites scraped  -->  AI scores each lead 1-10  -->  Stored in database
                                                    -->  Dashboard shows everything
PE firm emails found -->  Cold emails sent (10/day) -->  Auto follow-ups
                                                    -->  Breakup email after 12 days
```

### Data Sources (9 total)
| # | Source | What it finds |
|---|--------|--------------|
| 1 | Hacker News | Startup launches, Show HN |
| 2 | Google News RSS | "startup raises funding", "company acquired" |
| 3 | TechCrunch RSS | VC deals, startup news |
| 4 | VentureBeat RSS | AI/enterprise deals |
| 5 | SEC EDGAR API | S-1, 8-K, Form D filings |
| 6 | Crunchbase News | Funding rounds, valuations |
| 7 | Business Insider | M&A, investor news |
| 8 | Forbes | Business deals, innovation |
| 9 | Reddit | r/startups, r/venturecapital |

---

## All Commands

### Using start.bat (recommended on Windows)
```
start.bat                   Full autopilot (scrape + score + email)
start.bat --leads           Scrape + AI score only (no emails)
start.bat --email           Email PE firms only (no scraping)
start.bat --dashboard       Open web dashboard
start.bat --preview         Preview cold email templates
start.bat --status          Show stats
start.bat --schedule        Run every 6 hours
start.bat --reset           Delete all data and start fresh
```

### Using Python directly
```
python -u run.py                Full autopilot
python -u run.py --leads-only   Leads only
python -u run.py --email-only   Emails only
python -u run.py --schedule     Run every 6 hours
python -u run.py --status       Show stats
streamlit run dashboard.py      Open dashboard
```

---

## Cold Email System

### Setup
1. Add PE firm contacts to `prospects_template.csv`
2. Or let the scraper find them: `python prospects.py --scrape`
3. Run `python run.py` - emails are sent automatically

### Safety (no bans)
- **10 emails/day** (Gmail allows 500)
- **2-5 min random delay** between sends
- **Plain text only** (no HTML/images)
- **Every email is unique** (30+ template variations)
- **Auto-stops** after 2 follow-ups per contact
- Follow-up after 5 days, breakup after 12 days

### Email sequence
```
Day 0:  Initial email (personalized, mentions your lead data)
Day 5:  Follow-up (different template, shorter)
Day 12: Breakup email (polite goodbye, creates urgency)
        --> Never contacts them again
```

---

## Dashboard

Open at: **http://localhost:8501**

3 tabs:
- **Deal Leads** - All scraped leads with scores, charts, filters
- **PE/VC Prospects** - Firms found, emails, contact status
- **Email Campaigns** - Every email sent, reply tracking, timeline

---

## .env Configuration

```env
# AI (OpenRouter - access to 100+ models)
API_KEY=sk-or-v1-your-key
API_BASE_URL=https://openrouter.ai/api/v1/
AI_MODEL=openai/gpt-4o-mini

# Cold Email (Gmail)
SMTP_EMAIL=you@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SENDER_NAME=YourName
EMAIL_NICHE=healthcare SaaS
NUM_LEADS=8
```

---

## Daily Routine

**Morning:**
1. Run `start.bat` (takes ~10 min)
2. Open dashboard: `start.bat --dashboard`
3. Check Gmail for replies

**That's your entire workflow.** The system handles everything else.

---

## File Structure

```
deal_flow_engine/
  .env                 API keys & config
  config.py            All settings
  scrapers.py          9 data source scrapers
  ai_engine.py         GPT-4o-mini lead scoring
  database.py          SQLite storage
  prospects.py         PE firm email finder
  email_templates.py   Cold email generator
  cold_email.py        Gmail sender with anti-spam
  alerts.py            Hot lead email alerts
  run.py               Main autopilot script
  dashboard.py         Streamlit web dashboard
  start.bat            Windows launcher
  requirements.txt     Python dependencies
```
