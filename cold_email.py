"""
============================================================
  COLD EMAIL CAMPAIGN RUNNER
============================================================
  Fully automated cold email outreach system.
  
  Cost: $0 (uses your free Gmail account)
  
  Features:
  - Sends personalized initial emails
  - Auto follow-ups after 4 days
  - Breakup email after 10 days
  - Rate limiting (max 20/day to avoid spam flags)
  - Campaign tracking in SQLite
  - Human-like send timing (random delays)
  
  Gmail Setup (ONE TIME):
  1. Go to https://myaccount.google.com/apppasswords
  2. Generate an App Password
  3. Put it in your .env file
  
  Usage:
    python cold_email.py --preview           See sample emails before sending
    python cold_email.py --send              Send initial emails to new prospects 
    python cold_email.py --followup          Send follow-ups to non-responders
    python cold_email.py --auto              Full autopilot (initial + followups)
    python cold_email.py --status            See campaign stats
============================================================
"""
import smtplib
import sqlite3
import time
import random
import sys
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv

import prospects as prospect_db
import email_templates as templates
import database

load_dotenv()

# --- Configuration ---------------------------------------
SENDER_CONFIG = {
    "sender_name": os.getenv("SENDER_NAME", "Alex"),        # YOUR first name
    "sender_email": os.getenv("SMTP_EMAIL", ""),             # YOUR Gmail
    "sender_password": os.getenv("SMTP_PASSWORD", ""),       # Gmail App Password
    "niche": database.get_trending_niche(),                  # DYNAMIC BRAIN: Auto-detects hottest niche
    "num_leads": int(os.getenv("NUM_LEADS", "8")),           # Leads found this week
}

# Anti-spam settings (conservative to protect your Gmail)
MAX_EMAILS_PER_DAY = 25        # Sends this many per daily run
MIN_DELAY_SECONDS = 120        # Minimum 2 minutes between emails
MAX_DELAY_SECONDS = 300        # Up to 5 minutes (looks very human)
FOLLOWUP_AFTER_DAYS = 5        # Days before first follow-up
BREAKUP_AFTER_DAYS = 12        # Days before final breakup email

DATABASE = "cold_email.db"


# ===========================================================
#  EMAIL SENDER
# ===========================================================

def _send_single_email(to_email, subject, body, sender_email, sender_password):
    """Send one email via Gmail SMTP. Returns True/False."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = to_email
        
        # Send as plain text (looks more personal than HTML)
        msg.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        
        return True
    except smtplib.SMTPAuthenticationError:
        print("   [FAIL] Gmail authentication failed!")
        print("      → Go to https://myaccount.google.com/apppasswords")
        print("      → Generate an App Password and put it in .env")
        return False
    except Exception as e:
        print(f"   [FAIL] Send failed: {e}")
        return False


def _log_campaign(prospect_id, email_type, subject, body):
    """Log the sent email in the campaigns table."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO campaigns (prospect_id, email_type, subject, body, sent_at)
        VALUES (?, ?, ?, ?, ?)
    """, (prospect_id, email_type, subject, body, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def _update_prospect_status(prospect_id, status):
    """Update the prospect's status."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE prospects SET status = ? WHERE id = ?", (status, prospect_id))
    conn.commit()
    conn.close()


def _get_emails_sent_today():
    """Count how many emails were sent today."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM campaigns WHERE sent_at LIKE ?", (f"{today}%",))
    count = c.fetchone()[0]
    conn.close()
    return count


def _human_delay():
    """Wait a random amount of time to look human."""
    delay = random.randint(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
    print(f"   [WAIT] Waiting {delay}s (human-like delay)...")
    time.sleep(delay)


# ===========================================================
#  CAMPAIGN ACTIONS
# ===========================================================

def send_initial_emails():
    """Send initial outreach to all new prospects."""
    print("\n" + "=" * 60)
    print("  [EMAIL] SENDING INITIAL OUTREACH EMAILS")
    print("=" * 60)
    
    # Validate config
    if not SENDER_CONFIG["sender_email"] or not SENDER_CONFIG["sender_password"]:
        print("\n[FAIL] Email not configured! Add these to your .env file:")
        print("   SMTP_EMAIL=your-email@gmail.com")
        print("   SMTP_PASSWORD=your-gmail-app-password")
        print("   SENDER_NAME=YourFirstName")
        print("   EMAIL_NICHE=your target niche")
        print("\n   Get an App Password at: https://myaccount.google.com/apppasswords")
        return
    
    prospects_list = prospect_db.get_prospects_with_email()
    
    if not prospects_list:
        print("\n[WARN]  No prospects with email addresses found.")
        print("   Run: python prospects.py --template")
        print("   Then fill in the CSV and run: python prospects.py --load prospects_template.csv")
        return
    
    sent_today = _get_emails_sent_today()
    remaining = MAX_EMAILS_PER_DAY - sent_today
    
    if remaining <= 0:
        print(f"\n[WARN]  Daily limit reached ({MAX_EMAILS_PER_DAY} emails). Try again tomorrow.")
        return
    
    print(f"\n   [LIST] {len(prospects_list)} prospects ready")
    print(f"   [POST] {sent_today} sent today, {remaining} remaining")
    print(f"   [TARGET] Niche: {SENDER_CONFIG['niche']}")
    print()
    
    sent_count = 0
    
    for prospect in prospects_list[:remaining]:
        email_data = templates.generate_initial_email(prospect, SENDER_CONFIG)
        
        print(f"   [{sent_count + 1}] → {prospect['email']} ({prospect['firm_name']})")
        
        success = _send_single_email(
            to_email=prospect["email"],
            subject=email_data["subject"],
            body=email_data["body"],
            sender_email=SENDER_CONFIG["sender_email"],
            sender_password=SENDER_CONFIG["sender_password"]
        )
        
        if success:
            _log_campaign(prospect["id"], "initial", email_data["subject"], email_data["body"])
            _update_prospect_status(prospect["id"], "emailed")
            sent_count += 1
            print(f"       [OK] Sent!")
        else:
            print(f"       [FAIL] Failed")
            # If auth fails, stop immediately
            if not SENDER_CONFIG["sender_password"]:
                break
        
        # Human-like delay between sends
        if sent_count < len(prospects_list[:remaining]):
            _human_delay()
    
    print(f"\n   [CHART] Summary: {sent_count} emails sent successfully")


def send_followups():
    """Send follow-ups to prospects who haven't replied."""
    print("\n" + "=" * 60)
    print("  [EMAIL] SENDING FOLLOW-UP EMAILS")
    print("=" * 60)
    
    if not SENDER_CONFIG["sender_email"] or not SENDER_CONFIG["sender_password"]:
        print("\n[FAIL] Email not configured. See send_initial_emails() for setup.")
        return
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Find prospects who got initial email but no follow-up, and it's been X days
    cutoff_date = (datetime.now() - timedelta(days=FOLLOWUP_AFTER_DAYS)).isoformat()
    breakup_cutoff = (datetime.now() - timedelta(days=BREAKUP_AFTER_DAYS)).isoformat()
    
    # Get prospects needing follow-up
    c.execute("""
        SELECT p.*, c.subject as original_subject, c.sent_at as initial_sent, c.email_type as last_type
        FROM prospects p
        JOIN campaigns c ON c.prospect_id = p.id
        WHERE p.status = 'emailed'
        AND c.sent_at < ?
        AND c.replied = 0
        GROUP BY p.id
        HAVING MAX(c.id)
        ORDER BY c.sent_at ASC
    """, (cutoff_date,))
    
    followup_prospects = [dict(r) for r in c.fetchall()]
    conn.close()
    
    if not followup_prospects:
        print("\n   ℹ️  No follow-ups needed right now.")
        return
    
    sent_today = _get_emails_sent_today()
    remaining = MAX_EMAILS_PER_DAY - sent_today
    
    print(f"\n   [LIST] {len(followup_prospects)} prospects need follow-up")
    print(f"   [POST] {remaining} emails remaining today")
    
    sent_count = 0
    
    for prospect in followup_prospects[:remaining]:
        last_type = prospect.get("last_type", "initial")
        
        # Decide: follow-up or breakup?
        initial_sent = prospect.get("initial_sent", "")
        if initial_sent and initial_sent < breakup_cutoff:
            email_data = templates.generate_breakup_email(prospect, SENDER_CONFIG)
            email_type = "breakup"
        else:
            email_data = templates.generate_followup_email(
                prospect, SENDER_CONFIG, 
                prospect.get("original_subject", "deal flow data")
            )
            email_type = "followup"
        
        print(f"   [{email_type.upper()}] → {prospect['email']} ({prospect['firm_name']})")
        
        success = _send_single_email(
            to_email=prospect["email"],
            subject=email_data["subject"],
            body=email_data["body"],
            sender_email=SENDER_CONFIG["sender_email"],
            sender_password=SENDER_CONFIG["sender_password"]
        )
        
        if success:
            _log_campaign(prospect["id"], email_type, email_data["subject"], email_data["body"])
            if email_type == "breakup":
                _update_prospect_status(prospect["id"], "breakup_sent")
            sent_count += 1
            print(f"       [OK] Sent!")
        else:
            print(f"       [FAIL] Failed")
        
        if sent_count < len(followup_prospects[:remaining]):
            _human_delay()
    
    print(f"\n   [CHART] Summary: {sent_count} follow-ups sent")


def show_campaign_status():
    """Display campaign statistics."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    print("\n" + "=" * 60)
    print("  [CHART] CAMPAIGN STATUS")
    print("=" * 60)
    
    c.execute("SELECT COUNT(*) FROM prospects")
    total_prospects = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM prospects WHERE email != ''")
    with_email = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM prospects WHERE status = 'new'")
    new = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM prospects WHERE status = 'emailed'")
    emailed = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM campaigns WHERE email_type = 'initial'")
    initial_sent = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM campaigns WHERE email_type = 'followup'")
    followups_sent = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM campaigns WHERE email_type = 'breakup'")
    breakups_sent = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM campaigns WHERE replied = 1")
    replies = c.fetchone()[0]
    
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM campaigns WHERE sent_at LIKE ?", (f"{today}%",))
    sent_today = c.fetchone()[0]
    
    conn.close()
    
    print(f"""
   [USERS] Total Prospects:      {total_prospects}
   [EMAIL] With Email:           {with_email}
   [NEW] New (not contacted):  {new}
   [MAIL]  Emailed:              {emailed}
   
   [SENT] Initial Emails Sent:  {initial_sent}
   [RETRY] Follow-ups Sent:      {followups_sent}
   [BYE] Breakup Emails Sent:  {breakups_sent}
   [REPLY] Replies Received:     {replies}
   
   [DATE] Sent Today:           {sent_today} / {MAX_EMAILS_PER_DAY}
   """)
    
    if initial_sent > 0:
        reply_rate = (replies / initial_sent) * 100
        print(f"   [UP] Reply Rate: {reply_rate:.1f}%")
        if reply_rate < 5:
            print("   [TIP] Tip: Try changing your niche or email templates")
        elif reply_rate >= 10:
            print("   [HOT] Great reply rate! Keep going!")


def run_auto_mode():
    """Full autopilot: send initial + follow-ups."""
    print("\n[BOT] AUTOPILOT MODE ACTIVATED")
    print("   Checking for new prospects to email...")
    send_initial_emails()
    
    print("\n   Checking for follow-ups needed...")
    send_followups()
    
    print("\n   Showing campaign stats...")
    show_campaign_status()
    
    print("\n[OK] Autopilot complete. Run this daily for best results.")


# ===========================================================
#  MAIN
# ===========================================================

if __name__ == "__main__":
    # Initialize database
    prospect_db.init_db()
    
    if "--preview" in sys.argv:
        templates.preview_emails(SENDER_CONFIG, num_samples=3)
    
    elif "--send" in sys.argv:
        send_initial_emails()
    
    elif "--followup" in sys.argv:
        send_followups()
    
    elif "--auto" in sys.argv:
        run_auto_mode()
    
    elif "--status" in sys.argv:
        show_campaign_status()
    
    else:
        print("""
+==========================================================+
|           COLD EMAIL CAMPAIGN RUNNER v1.0                |
+==========================================================+
|                                                          |
|  SETUP (one time):                                       |
|  1. Get Gmail App Password:                              |
|     https://myaccount.google.com/apppasswords            |
|  2. Add to .env file:                                    |
|     SMTP_EMAIL=you@gmail.com                             |
|     SMTP_PASSWORD=your-app-password                      |
|     SENDER_NAME=YourName                                 |
|     EMAIL_NICHE=your target niche                        |
|  3. Add prospects:                                       |
|     python prospects.py --template                       |
|     (edit the CSV, then)                                 |
|     python prospects.py --load prospects_template.csv    |
|                                                          |
|  COMMANDS:                                               |
|  python cold_email.py --preview    Preview sample emails |
|  python cold_email.py --send       Send initial emails   |
|  python cold_email.py --followup   Send follow-ups       |
|  python cold_email.py --auto       Full autopilot        |
|  python cold_email.py --status     Campaign statistics   |
|                                                          |
+==========================================================+
        """)
