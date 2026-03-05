"""
Database layer - stores all scraped leads in SQLite.
SQLite is free, requires zero setup, and stores everything in a single file.
"""
import sqlite3
from datetime import datetime
import config

def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Lets us access columns by name
    return conn

def initialize_database():
    """Create the leads table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            headline TEXT NOT NULL,
            url TEXT,
            source TEXT NOT NULL,
            industry TEXT,
            signal_type TEXT,
            ai_summary TEXT,
            lead_score INTEGER DEFAULT 0,
            lead_tier TEXT DEFAULT 'cold',
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_contacted INTEGER DEFAULT 0,
            notes TEXT
        )
    """)
    
    # Index for fast filtering
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lead_score ON leads(lead_score DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON leads(source)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scraped_at ON leads(scraped_at DESC)")
    
    conn.commit()
    conn.close()
    print("[OK] Database initialized.")

def insert_lead(headline, url, source, industry, signal_type, ai_summary, lead_score):
    """Insert a new lead into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Determine tier based on score
    if lead_score >= config.HOT_LEAD_THRESHOLD:
        tier = "[HOT] hot"
    elif lead_score >= config.WARM_LEAD_THRESHOLD:
        tier = "[WARM] warm"
    else:
        tier = "[COLD] cold"
    
    # Check for duplicates (same headline + source)
    cursor.execute("SELECT id FROM leads WHERE headline = ? AND source = ?", (headline, source))
    if cursor.fetchone():
        conn.close()
        return False  # Already exists
    
    cursor.execute("""
        INSERT INTO leads (headline, url, source, industry, signal_type, ai_summary, lead_score, lead_tier)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (headline, url, source, industry, signal_type, ai_summary, lead_score, tier))
    
    conn.commit()
    conn.close()
    return True

def get_all_leads(limit=100, min_score=0):
    """Retrieve leads, sorted by score (highest first)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM leads 
        WHERE lead_score >= ?
        ORDER BY lead_score DESC, scraped_at DESC
        LIMIT ?
    """, (min_score, limit))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_leads_by_source(source):
    """Retrieve all leads from a specific source."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE source = ? ORDER BY lead_score DESC", (source,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_hot_leads():
    """Retrieve only hot leads (score >= threshold)."""
    return get_all_leads(min_score=config.HOT_LEAD_THRESHOLD)

def get_stats():
    """Get summary statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    cursor.execute("SELECT COUNT(*) FROM leads")
    stats["total_leads"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE lead_score >= ?", (config.HOT_LEAD_THRESHOLD,))
    stats["hot_leads"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE lead_score >= ? AND lead_score < ?", 
                   (config.WARM_LEAD_THRESHOLD, config.HOT_LEAD_THRESHOLD))
    stats["warm_leads"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT source, COUNT(*) as count FROM leads GROUP BY source")
    stats["by_source"] = {row[0]: row[1] for row in cursor.fetchall()}
    
    cursor.execute("SELECT AVG(lead_score) FROM leads")
    avg = cursor.fetchone()[0]
    stats["avg_score"] = round(avg, 1) if avg else 0
    
    conn.close()
    return stats


def get_trending_niche():
    """
    Analyzes all HOT leads from the past 7 days to find the hottest micro_niche.
    Returns the reigning niche string (e.g., "AI Legal Tech") or a fallback if none.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get the most frequent micro-niche among hot leads recently
    cursor.execute("""
        SELECT industry, COUNT(*) as count 
        FROM leads 
        WHERE lead_score >= ? 
        AND industry != 'Other' 
        AND industry != 'Emerging Tech'
        AND scraped_at >= date('now', '-7 days')
        GROUP BY industry 
        ORDER BY count DESC 
        LIMIT 1
    """, (config.HOT_LEAD_THRESHOLD,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row and row['industry']:
        return row['industry']
    
    return "Emerging Tech"

# Auto-create the database when this file is imported
initialize_database()
