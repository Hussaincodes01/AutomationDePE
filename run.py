import time
from datetime import datetime
import schedule

from database import init_db, save_lead
from scrapers import fetch_market_headlines
from ai_engine import analyze_lead
from prospects import inject_mega_list, enrich_fast_emails
from cold_email import send_cold_emails, send_followups

def run_autopilot():
    st_time = time.time()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("\n" + "="*80)
    print(f" [>>] DEAL FLOW ENGINE V3 - FULL AUTOPILOT DEPLOYED")
    print(f" [TIME] {ts}")
    print("="*80)

    # 1. Initialization
    init_db()

    # 2. Extract live market signals
    headlines = fetch_market_headlines()
    added = 0
    if headlines:
        print(f"\n[AI] Processing {len(headlines)} fresh market data points...")
        for h in headlines:
            analyzed = analyze_lead(h['title'], h['source'])
            if save_lead(h['title'], analyzed.get('niche', 'Corporate'), "Acquisition/Raise", analyzed.get('score', 3), analyzed.get('summary', '')):
                added += 1
    
    print(f"   [OK] Stored {added} totally new data signals.")

    # 3. Source Prospects
    inject_mega_list()

    # 4. Enrich Missing Emails via Dorks
    enrich_fast_emails()

    # 5. Email Sequences
    send_cold_emails()
    send_followups()

    elapsed = round(time.time() - st_time, 1)
    print("\n"+"="*80)
    print(f" [OK] AUTOPILOT BATCH COMPLETE IN {elapsed} SECONDS.")
    print("      Sleeping until next scheduled window.")
    print("="*80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--schedule", action="store_true", help="Run endlessly in a 2-hour loop")
    args = parser.parse_args()

    if args.schedule:
        print("[CLOCK] Autopilot strictly set for 2-hour intervals...")
        run_autopilot()
        schedule.every(2).hours.do(run_autopilot)
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        # Run exactly once instantly
        run_autopilot()
