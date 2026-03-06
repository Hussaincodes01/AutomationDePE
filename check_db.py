import sqlite3

def check_db():
    conn = sqlite3.connect('deal_flow_engine.db')
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM prospects").fetchone()[0]
    with_email = c.execute("SELECT COUNT(*) FROM prospects WHERE email != '' AND email IS NOT NULL").fetchone()[0]
    total_emails_sent = c.execute("SELECT COUNT(*) FROM campaigns WHERE status='sent_initial'").fetchone()[0]
    
    # Niche capture tracking
    top_niche = c.execute("SELECT niche, COUNT(*) as cnt FROM leads WHERE score >= 7 GROUP BY niche ORDER BY cnt DESC LIMIT 1").fetchone()
    if top_niche:
        niche_name = top_niche[0]
    else:
        niche_name = "Enterprise SaaS"

    print(f"Total VC Prospects: {total}")
    print(f"Prospects with Emails Extracted: {with_email}")
    print(f"Total Cold Emails Sent: {total_emails_sent}")
    print(f"Current Auto-Captured Niche: {niche_name}")

if __name__ == "__main__":
    check_db()
