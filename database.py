import sqlite3
import datetime
from config import DB_NAME

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    # 1. Market Leads (Companies looking to raise/sell)
    c.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            niche TEXT,
            signal TEXT,
            score INTEGER,
            summary TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 2. PE/VC Partner Prospects (The people we are emailing)
    c.execute("""
        CREATE TABLE IF NOT EXISTS prospects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firm_name TEXT UNIQUE,
            partner_name TEXT,
            email TEXT,
            linkedin_url TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 3. Email Campaigns (Tracks outreach state)
    c.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER,
            status TEXT DEFAULT 'sent_initial',
            last_contacted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(prospect_id) REFERENCES prospects(id)
        )
    """)
    conn.commit()
    conn.close()

def save_lead(title, niche, signal, score, summary):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO leads (title, niche, signal, score, summary) VALUES (?, ?, ?, ?, ?)",
                  (title, niche, signal, score, summary))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def save_prospect(firm_name, email="", partner_name=""):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO prospects (firm_name, email, partner_name) VALUES (?, ?, ?)",
                  (firm_name, email, partner_name))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_prospect_email(firm_name, email):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE prospects SET email = ? WHERE firm_name = ?", (email, firm_name))
    conn.commit()
    conn.close()

def get_trending_niche():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT niche, COUNT(*) as cnt FROM leads WHERE score >= 7 GROUP BY niche ORDER BY cnt DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    return row["niche"] if row else "Enterprise SaaS"

def log_campaign_event(prospect_id, status):
    conn = get_conn()
    c = conn.cursor()
    # If exists update, else insert
    c.execute("SELECT id FROM campaigns WHERE prospect_id = ?", (prospect_id,))
    if c.fetchone():
        c.execute("UPDATE campaigns SET status = ?, last_contacted = CURRENT_TIMESTAMP WHERE prospect_id = ?", (status, prospect_id))
    else:
        c.execute("INSERT INTO campaigns (prospect_id, status) VALUES (?, ?)", (prospect_id, status))
    conn.commit()
    conn.close()
