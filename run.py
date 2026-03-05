import os
os.environ["PYTHONIOENCODING"] = "utf-8"

"""
============================================================
  AUTONOMOUS DEAL FLOW ENGINE - FULL AUTOPILOT
============================================================
  ONE COMMAND runs the entire business:

  python run.py

  What happens automatically:
  1. Scrape deal leads (HackerNews, SEC, Google News, Product Hunt)
  2. AI scores each lead 1-10 using GLM-5
  3. Store leads in SQLite database
  4. Scrape PE/VC firm emails from public sources
  5. Send natural cold emails to firms (max 18/day)
  6. Auto follow-up firms that didn't reply
  7. Export CSV report

  Flags:
    python run.py                # Full autopilot (everything above)
    python run.py --leads-only   # Only scrape & analyze leads (no emails)
    python run.py --email-only   # Only send cold emails (no scraping)
    python run.py --schedule     # Run full autopilot every 6 hours
    python run.py --status       # Show stats only
============================================================
"""
import sys
import time
from datetime import datetime
import pandas as pd

import config
import database
import scrapers
import ai_engine
import alerts
import prospects
import cold_email


def step_1_scrape_leads():
    """Scrape deal flow leads from multiple sources."""
    print("\n" + "=" * 60)
    print("  STEP 1/5 | [WEB] SCRAPING DEAL LEADS")
    print("=" * 60)
    
    raw_leads = scrapers.scrape_all_sources()
    
    if not raw_leads:
        print("\n   [WARN]  No leads found. Check your internet connection.")
        return []
    
    return raw_leads


def step_2_analyze_leads(raw_leads):
    """Score and classify leads with AI."""
    print("\n" + "=" * 60)
    print("  STEP 2/5 | [AI] AI SCORING LEADS")
    print("=" * 60)
    
    if not raw_leads:
        print("   ℹ️  No leads to analyze. Skipping.")
        return []

    # Filter out already saved leads before AI scoring
    conn = database.get_connection()
    cursor = conn.cursor()
    new_raw_leads = []
    for rl in raw_leads:
        cursor.execute("SELECT id FROM leads WHERE headline = ? AND source = ?", (rl['headline'], rl['source']))
        if not cursor.fetchone():
            new_raw_leads.append(rl)
    conn.close()
    
    if not new_raw_leads:
        print("   [OK] No new leads to score today. Skipping AI step.")
        enriched_leads = []
    else:
        enriched_leads = ai_engine.analyze_leads_batch(new_raw_leads)

    
    # Store in database
    print(f"\n   [SAVE] Storing {len(enriched_leads)} leads in database...")
    new_count = 0
    for lead in enriched_leads:
        was_new = database.insert_lead(
            headline=lead["headline"],
            url=lead["url"],
            source=lead["source"],
            industry=lead["industry"],
            signal_type=lead["signal_type"],
            ai_summary=lead["ai_summary"],
            lead_score=lead["lead_score"]
        )
        if was_new:
            new_count += 1
    
    print(f"   [OK] {new_count} new leads added")
    
    # Alert on hot leads
    hot_leads = [l for l in enriched_leads if l["lead_score"] >= config.HOT_LEAD_THRESHOLD]
    if hot_leads:
        print(f"\n[HOT] {len(hot_leads)} HOT LEADS found!")
        for lead in hot_leads[:5]:
            safe_hl = lead['headline'][:65].encode('ascii', errors='replace').decode('ascii')
            print(f"      [{lead['lead_score']}/10] {safe_hl}")
    
    # Export CSV
    csv_filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df = pd.DataFrame(enriched_leads)
    df.to_csv(csv_filename, index=False)
    print(f"   [FILE] CSV: {csv_filename}")
    
    return enriched_leads


def step_3_scrape_pe_emails():
    """Find PE/VC firm emails from public sources."""
    print("\n" + "=" * 60)
    print("  STEP 3/5 | [FIRM] SCRAPING PE/VC FIRM EMAILS")
    print("=" * 60)
    
    with_email = prospects.scrape_all_pe_firms()
    return with_email


def step_4_send_cold_emails():
    """Send initial cold emails to new prospects."""
    print("\n" + "=" * 60)
    print("  STEP 4/5 | [EMAIL] SENDING COLD EMAILS")
    print("=" * 60)
    
    if not cold_email.SENDER_CONFIG["sender_email"] or not cold_email.SENDER_CONFIG["sender_password"]:
        print("\n   [WARN]  Cold email not configured yet. Add to .env:")
        print("      SMTP_EMAIL=your-gmail@gmail.com")
        print("      SMTP_PASSWORD=your-app-password")
        print("      SENDER_NAME=YourName")
        print("      EMAIL_NICHE=your target niche")
        print("\n   Skipping email step. Everything else still works!")
        return
    
    cold_email.send_initial_emails()


def step_5_send_followups():
    """Send follow-ups to non-responders."""
    print("\n" + "=" * 60)
    print("  STEP 5/5 | [RETRY] SENDING FOLLOW-UPS")
    print("=" * 60)
    
    if not cold_email.SENDER_CONFIG["sender_email"] or not cold_email.SENDER_CONFIG["sender_password"]:
        print("   [WARN]  Skipped (email not configured)")
        return
    
    cold_email.send_followups()


def show_final_summary(start_time):
    """Display the final summary dashboard."""
    elapsed = round(time.time() - start_time, 1)
    
    # Lead stats
    lead_stats = database.get_stats()
    
    # Prospect stats
    total_prospects, with_email = prospects.get_total_prospect_count()
    
    print("\n" + "=" * 60)
    print("  [OK] AUTOPILOT COMPLETE")
    print("=" * 60)
    print(f"""
   [TIME]  Total time:          {elapsed}s
   
   [CHART] DEAL LEADS:
      Total in DB:          {lead_stats['total_leads']}
      Hot leads (>={config.HOT_LEAD_THRESHOLD}):       {lead_stats['hot_leads']}
      Avg score:            {lead_stats['avg_score']}/10
   
   [FIRM] PE/VC PROSPECTS:
      Total firms found:    {total_prospects}
      With email address:   {with_email}
   """)
    
    # Show email campaign stats if configured
    if cold_email.SENDER_CONFIG["sender_email"]:
        cold_email.show_campaign_status()
    
    print("=" * 60)
    print("   [TIP] Next: Run 'streamlit run dashboard.py' to see your leads!")
    print("   [TIP] Run this daily: 'python run.py' or use --schedule for auto")
    print("=" * 60)


# ===========================================================
#  MAIN MODES
# ===========================================================

def run_full_autopilot():
    """The big one. Runs EVERYTHING with one command."""
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("\n" + "=" * 60)
    print(f"  [>>] DEAL FLOW ENGINE v2.0 - FULL AUTOPILOT")
    print(f"  [DATE] {timestamp}")
    print("=" * 60)
    
    # Step 1: Scrape deal leads
    raw_leads = step_1_scrape_leads()
    
    # Step 2: AI analysis (skip if no API key)
    if config.API_KEY and config.API_KEY != "your-api-key-here":
        enriched = step_2_analyze_leads(raw_leads)
    else:
        print("\n   [WARN]  No API key set. Skipping AI analysis.")
        print("      Add your GLM-5 key to .env: API_KEY=your-key")
        enriched = []
    
    # Step 3: Scrape PE/VC firm emails
    step_3_scrape_pe_emails()
    
    # Step 4: Send cold emails
    step_4_send_cold_emails()
    
    # Step 5: Follow up on previous emails
    step_5_send_followups()
    
    # Final summary
    show_final_summary(start_time)


def run_leads_only():
    """Only scrape and analyze leads, no emails."""
    start_time = time.time()
    print("\n[FIND] Running leads-only mode...")
    raw_leads = step_1_scrape_leads()
    if config.API_KEY and config.API_KEY != "your-api-key-here":
        step_2_analyze_leads(raw_leads)
    show_final_summary(start_time)


def run_email_only():
    """Only run the email pipeline, no lead scraping."""
    start_time = time.time()
    print("\n[EMAIL] Running email-only mode...")
    step_3_scrape_pe_emails()
    step_4_send_cold_emails()
    step_5_send_followups()
    show_final_summary(start_time)


def run_scheduled():
    """Run full autopilot every 2 hours."""
    import schedule
    
    print("[CLOCK] SCHEDULING: Full autopilot every 2 hours")
    print("   Press Ctrl+C to stop.\n")
    
    run_full_autopilot()
    schedule.every(2).hours.do(run_full_autopilot)
    
    while True:
        schedule.run_pending()
        time.sleep(60)


def show_status():
    """Just show stats without doing anything."""
    print("\n[CHART] Current Status:")
    lead_stats = database.get_stats()
    total_prospects, with_email = prospects.get_total_prospect_count()
    
    print(f"   Leads in DB: {lead_stats['total_leads']} ([HOT] {lead_stats['hot_leads']} hot)")
    print(f"   PE Firms:    {total_prospects} ({with_email} with emails)")
    
    if cold_email.SENDER_CONFIG["sender_email"]:
        cold_email.show_campaign_status()


# ===========================================================
#  ENTRY POINT
# ===========================================================

if __name__ == "__main__":
    # Initialize databases
    prospects.init_db()
    
    if "--leads-only" in sys.argv:
        run_leads_only()
    elif "--email-only" in sys.argv:
        run_email_only()
    elif "--schedule" in sys.argv:
        run_scheduled()
    elif "--status" in sys.argv:
        show_status()
    else:
        run_full_autopilot()
