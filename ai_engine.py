"""
AI Analysis Engine - Scores and classifies each lead.
Uses GLM-5 via Modal.com (or any OpenAI-compatible API).
"""
from openai import OpenAI
import json
import time
import config

client = OpenAI(
    api_key=config.API_KEY,
    base_url=config.API_BASE_URL
)

def _safe(text):
    """Make any text safe to print on Windows (strip non-ASCII)."""
    if not text:
        return ""
    return text.encode('ascii', errors='replace').decode('ascii')


def analyze_lead(headline, source, retries=3):
    """
    Sends a lead headline to the AI for deep analysis.
    Returns a dict with: industry, signal_type, summary, score (1-10).
    Retries up to 3 times if the API returns empty.
    """
    
    industries_str = ", ".join(config.TARGET_INDUSTRIES)
    signals_str = ", ".join(config.DEAL_SIGNALS)
    
    prompt = f"""You are an elite Private Equity / Venture Capital analyst.

Analyze this headline scraped from "{source}":
"{headline}"

Tasks:
1. Identify the exact MICRO-NICHE of this company/deal in 2-3 words (e.g., "AI Legal Tech", "B2B SaaS Payments", "Healthcare Robotics"). Do NOT use broad terms like "Software" or "Technology".
2. Identify the DEAL SIGNAL from this list: [{signals_str}, none]
3. Write a 1-sentence SUMMARY of why a PE/VC investor should care (or shouldn't).
4. Give a LEAD SCORE from 1-10:
   - 9-10: Clear fundraising, acquisition, or IPO signal
   - 7-8: Strong growth signal (hiring spree, revenue milestone, expansion)
   - 5-6: Interesting startup but no direct deal signal
   - 3-4: Tangentially related to business/investing
   - 1-2: Not relevant to deal flow at all

RESPOND IN EXACTLY THIS JSON FORMAT (no markdown, no explanation):
{{"micro_niche": "...", "signal": "...", "summary": "...", "score": N}}
"""

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=config.AI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a VC deal flow analyst. Respond ONLY in valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=config.AI_TEMPERATURE,
                max_tokens=300
            )
            
            # Handle None/empty response
            if not response or not response.choices:
                print(f"      [RETRY {attempt+1}/{retries}] Empty response, waiting 5s...")
                time.sleep(5)
                continue
            
            content = response.choices[0].message.content
            if not content or not content.strip():
                print(f"      [RETRY {attempt+1}/{retries}] Empty content, waiting 5s...")
                time.sleep(5)
                continue
            
            raw = content.strip()
            
            # Clean up potential markdown formatting
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw
                raw = raw.rsplit("```", 1)[0] if "```" in raw else raw
                raw = raw.strip()
            
            result = json.loads(raw)
            
            # Validate and sanitize
            result["score"] = max(1, min(10, int(result.get("score", 1))))
            result["industry"] = str(result.get("micro_niche", "Emerging Tech"))
            result["signal"] = str(result.get("signal", "none"))
            result["summary"] = str(result.get("summary", "No analysis available."))
            
            return result
            
        except json.JSONDecodeError:
            print(f"      [WARN] Non-JSON response, retrying...")
            time.sleep(3)
            continue
        except Exception as e:
            error_msg = str(e)
            if "rate" in error_msg.lower() or "limit" in error_msg.lower() or "429" in error_msg:
                wait_time = 10 * (attempt + 1)
                print(f"      [RATE LIMITED] Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            else:
                print(f"      [FAIL] {_safe(error_msg[:80])}")
                break
    
    # All retries failed - return a default
    return {
        "industry": "Emerging Tech",
        "signal": "none",
        "summary": "AI could not analyze - API may be overloaded.",
        "score": 3
    }


def analyze_leads_batch(leads):
    """
    Analyzes a list of leads, adding AI analysis to each one.
    Returns the enriched leads list.
    """
    print(f"\n[AI] Analyzing {len(leads)} leads with AI...")
    print(f"   Model: {config.AI_MODEL}")
    print(f"   Retries: 3 per lead (handles rate limits)")
    print()
    
    enriched = []
    success_count = 0
    
    for i, lead in enumerate(leads):
        safe_headline = _safe(lead['headline'][:60])
        print(f"   [{i+1}/{len(leads)}] {safe_headline}...")
        
        analysis = analyze_lead(lead["headline"], lead["source"])
        
        if analysis["summary"] != "AI could not analyze - API may be overloaded.":
            success_count += 1
        
        enriched.append({
            **lead,
            "industry": analysis["industry"],
            "signal_type": analysis["signal"],
            "ai_summary": analysis["summary"],
            "lead_score": analysis["score"]
        })
        
        # Delay between calls to avoid rate limiting
        time.sleep(1.5)
    
    # Sort by score (highest first)
    enriched.sort(key=lambda x: x["lead_score"], reverse=True)
    
    hot = sum(1 for l in enriched if l["lead_score"] >= config.HOT_LEAD_THRESHOLD)
    warm = sum(1 for l in enriched if config.WARM_LEAD_THRESHOLD <= l["lead_score"] < config.HOT_LEAD_THRESHOLD)
    cold = sum(1 for l in enriched if l["lead_score"] < config.WARM_LEAD_THRESHOLD)
    
    print(f"\n   Results: {hot} hot | {warm} warm | {cold} cold")
    print(f"   AI success rate: {success_count}/{len(leads)} ({round(success_count/max(len(leads),1)*100)}%)")
    
    return enriched


def generate_custom_email(prospect, sender_config):
    """
    Dynamically generate a personalized cold email using AI for every prospect.
    No more hardcoded templates.
    """
    niche = sender_config.get("niche", "software")
    firm = prospect.get('firm_name', 'your firm')
    name = prospect.get('contact_name', '')
    if name:
        name = name.split()[0]
    else:
        name = "there"
    
    sender_name = sender_config.get('sender_name', 'Alex')
        
    prompt = f"""You are a top 1% Deal Origination Associate reaching out to a Private Equity / VC partner. 
Write a highly targeted cold email driving them to start a 14-day free trial of your proprietary data platform.

Data Points to insert:
Prospect Name: {name}
Prospect Firm: {firm}
Current Trending Deal Niche: {niche}
My Name: {sender_name}

Guidelines:
- First line MUST be the Subject Line ONLY (do not write "Subject:").
- Then write the email body below it.
- Keep it under 100 words. Be direct, authoritative, extremely confident, but casual.
- Pitch the 14-day FREE TRIAL explicitly as a way to prove your data pipeline works.
- DO NOT use placeholders like [Insert Link].
"""
    
    try:
        response = client.chat.completions.create(
            model=config.AI_MODEL,
            messages=[
                {"role": "system", "content": "You write cold emails that originate massive M&A deals."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=250
        )
        content = response.choices[0].message.content.strip()
        
        parts = content.split('\n', 1)
        subject = parts[0].replace("Subject:", "").strip()
        body = parts[1].strip() if len(parts) > 1 else content
        
        return {"subject": subject, "body": body}
        
    except Exception as e:
        print(f"   [WARN] AI Email Gen failed: {e}. Falling back to default.")
        subject = f"Trial access: Proprietary {niche} deal flow for {firm}"
        body = f"Hi {name},\n\nI run an engine tracking off-market {niche} data. I'd love to offer you a 14-day free trial of the feed.\n\nBest,\n{sender_name}"
        return {"subject": subject, "body": body}
