import streamlit as st
from database import get_conn
import pandas as pd

st.set_page_config(page_title="Deal Flow Engine V3", layout="wide", page_icon="💸")

st.markdown("# 💸 Autonomous Deal Flow Engine")
st.markdown("Monitor market signals and outbound capital allocation natively in real-time.")

conn = get_conn()
c = conn.cursor()

# Metrics
leads_count = c.execute("SELECT count(*) FROM leads").fetchone()[0]
firms_count = c.execute("SELECT count(*) FROM prospects").fetchone()[0]
sent_count = c.execute("SELECT count(*) FROM campaigns").fetchone()[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Market Deal Signals (Last 7 Days)", leads_count)
col2.metric("PE/VC Firms Indexed", firms_count)
col3.metric("Emails Successfully Sent", sent_count)
resps = c.execute("SELECT count(*) FROM campaigns WHERE status='replied'").fetchone()[0]
col4.metric("Partner Replies", resps)

st.markdown("---")

c1, c2 = st.columns(2)
with c1:
    st.subheader("🔥 Hottest YC / SEC Market Signals")
    leads_df = pd.read_sql_query("SELECT title, niche, score, summary FROM leads ORDER BY score DESC LIMIT 10", conn)
    if not leads_df.empty:
        st.dataframe(leads_df, use_container_width=True)
    else:
        st.info("No leads found. Run the scraper.")

with c2:
    st.subheader("📬 Automated Outreach Pipeline")
    outreach_df = pd.read_sql_query("""
        SELECT p.firm_name, p.email, c.status, c.last_contacted 
        FROM campaigns c
        JOIN prospects p ON c.prospect_id = p.id
        ORDER BY c.last_contacted DESC
        LIMIT 10
    """, conn)
    if not outreach_df.empty:
        st.dataframe(outreach_df, use_container_width=True)
    else:
        st.info("No outreaches logged yet.")

conn.close()
