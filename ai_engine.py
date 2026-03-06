import json
import time
from openai import OpenAI
from config import API_KEY, API_BASE_URL, AI_MODEL

client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

def analyze_lead(headline, source):
    """Parses a headline into structural data for investors."""
    prompt = f"""You are a Private Equity analyst. Analyze this business headline:
"{headline}" from {source}

Output STRICT JSON:
{{"niche": "2-3 word exact industry", "signal": "Fundraising/Acquisition/Growth", "score": N, "summary": "1 sentence why investors care"}}
N is a Deal Score from 1 to 10 (10 being a hot M&A target).
"""
    try:
        r = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0, max_tokens=150
        )
        content = r.choices[0].message.content.strip()
        if "```json" in content: content = content.split("```json")[-1].split("```")[0].strip()
        elif "```" in content: content = content.split("```")[-1].split("```")[0].strip()
        return json.loads(content)
    except Exception as e:
        print(f"      [AI ERROR] {e}")
        return {"niche": "Tech", "signal": "News", "score": 3, "summary": "Failed to parse."}

def generate_custom_email(firm_name, partner_name, trending_niche):
    """Autonomously constructs hyper-personalized 14-day trial pitches."""
    prompt = f"""You are a top 1% Deal Origination Associate. Write a very brief cold email offering a 14-day free trial of your data platform.
Data:
Firm: {firm_name}
Partner: {partner_name or 'there'}
Niche: {trending_niche}

Rules:
1. First line IS EXACTLY the Subject Line. No labels like "Subject:". E.g.: "Unlock {trending_niche} Deals"
2. The rest is the body. Under 90 words. Highly confident, casual, no placeholders. Tell them you will give them 14-days free access.
"""
    try:
        r = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7, max_tokens=200
        )
        content = r.choices[0].message.content.strip()
        parts = content.split('\n', 1)
        return {"subject": parts[0].strip(), "body": parts[1].strip() if len(parts)>1 else ""}
    except:
        return {
            "subject": f"Off-market {trending_niche} leads for {firm_name}",
            "body": f"Hi {partner_name},\n\nWould you be open to a 14-day free trial of my {trending_niche} data feed?\n\nBest,\nAutomated Lead Engine"
        }
