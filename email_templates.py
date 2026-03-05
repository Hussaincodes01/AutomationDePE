"""
============================================================
  NATURAL EMAIL TEMPLATE ENGINE
============================================================
  Generates human-sounding, personalized cold emails 
  WITHOUT any AI API calls. Zero cost.
  
  How it works:
  - Multiple template variations for each email type
  - Smart variable insertion (firm name, niche, lead data)
  - Random selection of openings, bodies, CTAs
  - Result: every email looks hand-written and unique
============================================================
"""
import random
from datetime import datetime


# ===========================================================
# INITIAL OUTREACH TEMPLATES (Trial Pitch)
# ===========================================================

SUBJECT_LINES = [
    "Trial access: Proprietary {niche} deal flow for {firm_name}",
    "Quick question about your {niche} sourcing (Trial offer)",
    "Test my {niche} deal flow engine for 14 days",
    "[Trial] {num_leads} off-market {niche} opportunities this week",
    "Sending over a live trial of {niche} deal signals",
]

OPENINGS = [
    "Hi {first_name},\n\nI run an autonomous data pipeline that monitors SEC filings, web patterns, and backend hiring data to identify {niche} businesses showing early signs of ownership transition.",
    
    "Hi {first_name},\n\nI noticed {firm_name} has been actively deploying capital in the {niche} space. I built a proprietary dataset that surfaces companies showing pre-deal signals before they hit the open market.",
    
    "Hi {first_name},\n\nI've been tracking {niche} companies across obscure public filings and hiring patterns, catching opportunities that don't seem to be on anyone's radar yet.",
]

BODIES = [
    "This week alone, the system flagged {num_leads} companies in the {niche} space with significant signals - such as {example_signal}.\n\nInstead of just telling you about it, I'd like to offer you a free trial period to test the live data feed yourself.",
    
    "For example, I recently identified {num_leads} {niche} businesses where the data suggests {example_signal}.\n\nI know deal origination tools have to prove their worth, so I'm offering a free 14-day trial of my live data feed so you can literally test the quality of these leads.",
    
    "Some patterns I caught this week in {niche}:\n- {example_signal}\n- Leadership changes at {num_leads}+ private companies\n\nI'm rolling out a new Trial Period where your team can plug directly into the live data feed and evaluate the deals right now."
]

CLOSINGS = [
    "Would a 2-minute look at the platform be worth your time? I can set up your trial access today.\n\nBest,\n{sender_name}",
    
    "No credit cards or strings attached - I just want to prove the data quality. Want me to send over the trial link?\n\nCheers,\n{sender_name}",
    
    "If you're open to it, I can provision a trial account for you right now so you can see this week's findings. Let me know.\n\nBest,\n{sender_name}",
]


# ===========================================================
# FOLLOW-UP TEMPLATES (sent 3-5 days after initial)
# ===========================================================

FOLLOWUP_SUBJECTS = [
    "Re: {original_subject}",
    "Following up on the trial - {niche} data",
]

FOLLOWUP_BODIES = [
    "Hi {first_name},\n\nJust floating this back up in case it got buried. My system just flagged {num_new_leads} new {niche} opportunities today.\n\nThe free trial offer still stands if you want to take a look inside. Let me know!\n\nBest,\n{sender_name}",
    
    "Hi {first_name},\n\nWanted to follow up briefly. I've continued to surface new {niche} deal signals - {num_new_leads} more this week.\n\nWorth setting up that free trial so you can see the data yourself? Takes 60 seconds to activate.\n\n{sender_name}",
]


# ===========================================================
# BREAKUP EMAIL (last follow-up, 7-10 days later)
# ===========================================================

BREAKUP_BODIES = [
    "Hi {first_name},\n\nI'll keep this short - I've reached out about doing a trial of my {niche} deal flow data platform.\n\nIf this isn't relevant to {firm_name}'s current strategy, no worries. I'll take the hint and won't follow up again.\n\nBut if you ever want to run a trial, my inbox is always open.\n\nAll the best,\n{sender_name}",
]


# ===========================================================
# EXAMPLE SIGNALS (rotated to make emails specific)
# ===========================================================

EXAMPLE_SIGNALS = [
    "founders over 60 posting succession-related job listings",
    "companies filing D forms with the SEC (private fundraise signals)",
    "leadership changes combined with hiring freezes",
    "businesses listing commercial property while expanding payroll",
    "companies that recently lost a key executive and haven't replaced them",
    "firms with declining web traffic but increasing patent filings",
    "recent Series A companies now showing signs of down-round pressure",
    "privately held companies suddenly hiring CFOs (pre-transaction signal)",
]


# ===========================================================
# EMAIL GENERATOR FUNCTIONS
# ===========================================================

def _fill_template(template, variables):
    """Fill in template variables safely."""
    try:
        return template.format(**variables)
    except KeyError as e:
        # If a variable is missing, leave it as-is
        return template

def generate_initial_email(prospect, sender_config):
    """
    Generate a unique initial outreach email for a prospect via AI Engine.
    """
    import ai_engine
    return ai_engine.generate_custom_email(prospect, sender_config)


def generate_followup_email(prospect, sender_config, original_subject=""):
    """Generate a follow-up email."""
    first_name = (prospect.get("contact_name", "") or "").split()[0] if prospect.get("contact_name") else "there"
    
    variables = {
        "first_name": first_name,
        "firm_name": prospect.get("firm_name", "your firm"),
        "niche": sender_config.get("niche", "technology"),
        "num_new_leads": random.randint(3, 12),
        "sender_name": sender_config.get("sender_name", "Alex"),
        "original_subject": original_subject,
        "example_signal": random.choice(EXAMPLE_SIGNALS),
    }
    
    subject = _fill_template(random.choice(FOLLOWUP_SUBJECTS), variables)
    body = _fill_template(random.choice(FOLLOWUP_BODIES), variables)
    
    return {"subject": subject, "body": body}


def generate_breakup_email(prospect, sender_config):
    """Generate the final breakup email."""
    first_name = (prospect.get("contact_name", "") or "").split()[0] if prospect.get("contact_name") else "there"
    
    variables = {
        "first_name": first_name,
        "firm_name": prospect.get("firm_name", "your firm"),
        "niche": sender_config.get("niche", "technology"),
        "sender_name": sender_config.get("sender_name", "Alex"),
    }
    
    subject = f"Last note - {sender_config.get('niche', 'deal flow')} data"
    body = _fill_template(random.choice(BREAKUP_BODIES), variables)
    
    return {"subject": subject, "body": body}


# --- Preview function -----------------------------------
def preview_emails(sender_config, num_samples=3):
    """Preview what the generated emails look like."""
    print("\n" + "=" * 60)
    print("  [EMAIL] EMAIL PREVIEW (what prospects will receive)")
    print("=" * 60)
    
    fake_prospect = {
        "firm_name": "Blackstone Growth Partners",
        "contact_name": "Michael Thompson",
        "email": "mthompson@blackstone.com",
    }
    
    for i in range(num_samples):
        email = generate_initial_email(fake_prospect, sender_config)
        print(f"\n{'-' * 50}")
        print(f"  Version {i+1}")
        print(f"{'-' * 50}")
        print(f"  Subject: {email['subject']}")
        print(f"\n{email['body']}")
    
    print(f"\n{'-' * 50}")
    print("  FOLLOW-UP (sent 4 days later)")
    print(f"{'-' * 50}")
    followup = generate_followup_email(fake_prospect, sender_config, "deal flow data")
    print(f"  Subject: {followup['subject']}")
    print(f"\n{followup['body']}")
    
    print(f"\n{'-' * 50}")
    print("  BREAKUP (sent 10 days later)")
    print(f"{'-' * 50}")
    breakup = generate_breakup_email(fake_prospect, sender_config)
    print(f"  Subject: {breakup['subject']}")
    print(f"\n{breakup['body']}")


if __name__ == "__main__":
    config = {
        "sender_name": "Alex",
        "niche": "healthcare SaaS",
        "num_leads": 8,
    }
    preview_emails(config)
