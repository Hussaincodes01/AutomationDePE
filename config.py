"""
Configuration for the Autonomous Deal Flow Engine.
Set your API key as an environment variable or in a .env file.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── API Keys ────────────────────────────────────────────
# OpenRouter API (access to 100+ AI models)
API_KEY = os.getenv("API_KEY", os.getenv("OPENAI_API_KEY", "your-api-key-here"))
API_BASE_URL = os.getenv("API_BASE_URL", "https://openrouter.ai/api/v1/")

# ─── AI Model Settings ───────────────────────────────────
AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-4o-mini")  # Fast, cheap, reliable via OpenRouter
AI_TEMPERATURE = 0.2            # Low = factual. High = creative.

# --- Database --------------------------------------------
DATABASE_PATH = "deal_flow.db"

# --- Scraper Settings ------------------------------------
MAX_LEADS_PER_SOURCE = 20       # How many items to grab from each source
SCRAPE_DELAY_SECONDS = 1.5      # Delay between requests (be polite to servers)

# --- Lead Scoring Thresholds -----------------------------
HOT_LEAD_THRESHOLD = 7          # Score >= 7 out of 10 = hot lead
WARM_LEAD_THRESHOLD = 4         # Score >= 4 = warm lead, below = cold

# --- Email Alerts (Optional) -----------------------------
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # Use App Password for Gmail
ALERT_RECIPIENTS = os.getenv("ALERT_RECIPIENTS", "").split(",")

# --- Target Industries (customize for your niche) --------
TARGET_INDUSTRIES = [
    "SaaS",
    "AI/ML",
    "Fintech",
    "Healthcare",
    "E-commerce",
    "Cybersecurity",
    "Climate Tech",
    "Developer Tools",
]

# --- Target Signals (what PE/VC firms want to know) ------
DEAL_SIGNALS = [
    "fundraising",
    "acquisition",
    "IPO",
    "expansion",
    "hiring spree",
    "new product launch",
    "pivot",
    "leadership change",
    "partnerships",
    "revenue milestone",
]
