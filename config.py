import os
from dotenv import load_dotenv

load_dotenv()

# --- Security/Credentials ---
API_KEY = os.getenv("API_KEY", "")
API_BASE_URL = "https://openrouter.ai/api/v1"
AI_MODEL = "openai/gpt-4o-mini"

SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# --- Database ---
DB_NAME = "deal_flow_engine.db"

# --- Thresholds ---
HOT_LEAD_THRESHOLD = 7
WARM_LEAD_THRESHOLD = 5

# --- Email Pipeline ---
MAX_EMAILS_PER_DAY = 25
MIN_DELAY_SECONDS = 60
MAX_DELAY_SECONDS = 180

SENDER_NAME = "Hussain"
TRIAL_DAYS = 14
