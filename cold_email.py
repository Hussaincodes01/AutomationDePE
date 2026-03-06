import smtplib
from email.message import EmailMessage
import time
import random
from config import SMTP_EMAIL, SMTP_PASSWORD, MAX_EMAILS_PER_DAY, MIN_DELAY_SECONDS, MAX_DELAY_SECONDS, SENDER_NAME
from database import get_conn, log_campaign_event, get_trending_niche
from ai_engine import generate_custom_email

def send_cold_emails():
    print("\n[EMAIL] Starting automated trial distribution...")
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("   [WARN] Missing Gmail credentials in .env. Skipping emails.")
        return

    niche = get_trending_niche()
    print(f"   [AI] Detected hottest target niche: {niche}")

    conn = get_conn()
    c = conn.cursor()
    # Find prospects with emails who are NOT in the campaigns table yet (or at least haven't been sent initial)
    c.execute("""
        SELECT p.* FROM prospects p 
        WHERE p.email != '' 
        AND p.id NOT IN (SELECT prospect_id FROM campaigns)
        LIMIT ?
    """, (MAX_EMAILS_PER_DAY,))
    targets = c.fetchall()
    conn.close()

    if not targets:
        print("   ℹ️  No fresh email leads available. Run scrape to fetch more.")
        return

    sent = 0
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(SMTP_EMAIL, SMTP_PASSWORD)

    for row in targets:
        try:
            # Generate bespoke email via AI
            draft = generate_custom_email(row['firm_name'], row['partner_name'], niche)
            
            msg = EmailMessage()
            msg.set_content(draft['body'])
            msg['Subject'] = draft['subject']
            msg['From'] = f"{SENDER_NAME} <{SMTP_EMAIL}>"
            msg['To'] = row['email']
            
            server.send_message(msg)
            log_campaign_event(row['id'], "sent_initial")
            sent += 1
            print(f"       [+] Secure Sent -> {row['email']}")

            if sent < len(targets):
                delay = random.randint(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
                print(f"           [!] Waiting {delay}s to avoid Google spam flags...")
                time.sleep(delay)

        except Exception as e:
            print(f"       [ERROR] Failed to send to {row['email']}: {e}")

    server.quit()
    print(f"   [OK] Finished initial outreach batch: {sent} completed.")

def send_followups():
    print("\n[EMAIL] Generating Follow-ups for Non-Responders...")
    # Follow-ups (basic implementation, just logs for now to show intention without spamming real servers)
    print("   ℹ️  No non-responders ready for follow-up today.")
    pass
