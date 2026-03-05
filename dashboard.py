"""
============================================================
  DEAL FLOW ENGINE - Full Dashboard
============================================================
  Shows EVERYTHING in one place:
  - Deal leads with AI scores
  - PE/VC firm prospects  
  - Cold email campaign stats
  - Charts & filters

  Run with:  streamlit run dashboard.py
============================================================
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import database
import config
import os

# --- Page Config -----------------------------------------
st.set_page_config(
    page_title="Deal Flow Engine",
    page_icon="[>>]",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .metric-card {
        padding: 20px 24px;
        border-radius: 16px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.15);
        margin-bottom: 8px;
    }
    .metric-card h2 { font-size: 2.4rem; margin: 0; font-weight: 800; }
    .metric-card p { font-size: 0.85rem; opacity: 0.9; margin: 4px 0 0 0; }
    
    .grad-purple { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .grad-pink { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .grad-blue { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .grad-green { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .grad-orange { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .grad-dark { background: linear-gradient(135deg, #2d3436 0%, #636e72 100%); }
    
    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        margin: 24px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #667eea;
    }
    
    .stDataFrame { border-radius: 12px; overflow: hidden; }
    div[data-testid="stTabs"] button { font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# --- Helper: Load prospect/campaign data -----------------
def load_prospect_data():
    """Load prospects and campaigns from cold_email.db."""
    db_path = "cold_email.db"
    if not os.path.exists(db_path):
        return pd.DataFrame(), pd.DataFrame()
    
    conn = sqlite3.connect(db_path)
    
    try:
        prospects_df = pd.read_sql_query("SELECT * FROM prospects ORDER BY added_at DESC", conn)
    except Exception:
        prospects_df = pd.DataFrame()
    
    try:
        campaigns_df = pd.read_sql_query("""
            SELECT c.*, p.firm_name, p.email as prospect_email 
            FROM campaigns c 
            LEFT JOIN prospects p ON c.prospect_id = p.id 
            ORDER BY c.sent_at DESC
        """, conn)
    except Exception:
        campaigns_df = pd.DataFrame()
    
    conn.close()
    return prospects_df, campaigns_df


# --- Load all data ---------------------------------------
lead_stats = database.get_stats()
all_leads = database.get_all_leads(limit=1000)
leads_df = pd.DataFrame(all_leads) if all_leads else pd.DataFrame()
prospects_df, campaigns_df = load_prospect_data()


# ===========================================================
#  HEADER
# ===========================================================
st.markdown("# [>>] Deal Flow Engine - Command Center")
st.caption("AI-powered lead intelligence • PE/VC prospecting • Cold email campaigns")

# ===========================================================
#  TOP METRICS ROW
# ===========================================================
c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    st.markdown(f'<div class="metric-card grad-purple"><h2>{lead_stats["total_leads"]}</h2><p>Total Leads</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card grad-pink"><h2>{lead_stats["hot_leads"]}</h2><p>[HOT] Hot Leads</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card grad-blue"><h2>{lead_stats["warm_leads"]}</h2><p>[WARM] Warm Leads</p></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card grad-green"><h2>{len(prospects_df)}</h2><p>[FIRM] PE Firms</p></div>', unsafe_allow_html=True)
with c5:
    emails_with = len(prospects_df[prospects_df["email"].notna() & (prospects_df["email"] != "")]) if not prospects_df.empty and "email" in prospects_df.columns else 0
    st.markdown(f'<div class="metric-card grad-orange"><h2>{emails_with}</h2><p>[EMAIL] With Email</p></div>', unsafe_allow_html=True)
with c6:
    sent_count = len(campaigns_df) if not campaigns_df.empty else 0
    st.markdown(f'<div class="metric-card grad-dark"><h2>{sent_count}</h2><p>[MAIL] Emails Sent</p></div>', unsafe_allow_html=True)


# ===========================================================
#  TABS: Leads | Prospects | Email Campaigns
# ===========================================================
tab1, tab2, tab3 = st.tabs(["[CHART] Deal Leads", "[FIRM] PE/VC Prospects", "[EMAIL] Email Campaigns"])


# --- TAB 1: Deal Leads ----------------------------------
with tab1:
    if leads_df.empty:
        st.warning("[WARN] No leads yet. Run `python run.py` to scrape and analyze leads.")
    else:
        # Sidebar filters
        st.sidebar.header("[FIND] Lead Filters")
        min_score = st.sidebar.slider("Minimum Score", 1, 10, 1)
        
        sources = leads_df["source"].unique().tolist() if "source" in leads_df.columns else []
        selected_sources = st.sidebar.multiselect("Sources", options=sources, default=sources)
        
        if "industry" in leads_df.columns and leads_df["industry"].notna().any():
            industries = leads_df["industry"].dropna().unique().tolist()
            selected_industries = st.sidebar.multiselect("Industries", options=industries, default=industries)
        else:
            selected_industries = None
        
        # Apply filters
        filtered = leads_df[
            (leads_df["lead_score"] >= min_score) &
            (leads_df["source"].isin(selected_sources))
        ]
        if selected_industries is not None and "industry" in filtered.columns:
            filtered = filtered[filtered["industry"].isin(selected_industries)]
        
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**Showing {len(filtered)} / {len(leads_df)} leads**")
        
        # Charts
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown('<p class="section-header">[CHART] Score Distribution</p>', unsafe_allow_html=True)
            fig_hist = px.histogram(
                filtered, x="lead_score", nbins=10,
                color_discrete_sequence=["#667eea"],
                labels={"lead_score": "Lead Score"},
            )
            fig_hist.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=10, b=20))
            st.plotly_chart(fig_hist, width="stretch")
        
        with chart_col2:
            st.markdown('<p class="section-header">[WEB] Leads by Source</p>', unsafe_allow_html=True)
            source_counts = filtered["source"].value_counts().reset_index()
            source_counts.columns = ["source", "count"]
            fig_pie = px.pie(source_counts, values="count", names="source", color_discrete_sequence=px.colors.sequential.Plasma_r, hole=0.4)
            fig_pie.update_layout(margin=dict(l=20, r=20, t=10, b=20), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, width="stretch")
        
        # Industry breakdown
        if "industry" in filtered.columns and filtered["industry"].notna().any():
            st.markdown('<p class="section-header">[FIRM] Leads by Industry</p>', unsafe_allow_html=True)
            ind_counts = filtered["industry"].value_counts().reset_index()
            ind_counts.columns = ["industry", "count"]
            fig_bar = px.bar(ind_counts, x="industry", y="count", color="count", color_continuous_scale="Viridis")
            fig_bar.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=10, b=20))
            st.plotly_chart(fig_bar, width="stretch")
        
        # Leads table
        st.markdown('<p class="section-header">[LIST] All Leads</p>', unsafe_allow_html=True)
        display_cols = [c for c in ["lead_score", "lead_tier", "headline", "source", "industry", "signal_type", "ai_summary", "url"] if c in filtered.columns]
        
        st.dataframe(
            filtered[display_cols].sort_values("lead_score", ascending=False),
            width="stretch",
            height=500,
            column_config={
                "lead_score": st.column_config.ProgressColumn("Score", min_value=0, max_value=10, format="%d/10"),
                "url": st.column_config.LinkColumn("Link"),
                "headline": st.column_config.TextColumn("Headline", width="large"),
                "ai_summary": st.column_config.TextColumn("AI Summary", width="large"),
            }
        )
        
        # Export
        csv_data = filtered.to_csv(index=False).encode('utf-8-sig')
        st.download_button("[IN] Download Leads CSV", data=csv_data, file_name="deal_flow_leads.csv", mime="text/csv")


# --- TAB 2: PE/VC Prospects -----------------------------
with tab2:
    if prospects_df.empty:
        st.warning("[WARN] No prospects yet. Run `python run.py` to scrape PE/VC firm emails.")
    else:
        # Prospect stats
        p1, p2, p3, p4 = st.columns(4)
        
        total_p = len(prospects_df)
        with_email_p = len(prospects_df[prospects_df["email"].notna() & (prospects_df["email"] != "")]) if "email" in prospects_df.columns else 0
        new_p = len(prospects_df[prospects_df["status"] == "new"]) if "status" in prospects_df.columns else 0
        emailed_p = len(prospects_df[prospects_df["status"] == "emailed"]) if "status" in prospects_df.columns else 0
        
        p1.metric("Total Firms", total_p)
        p2.metric("With Email", with_email_p)
        p3.metric("New (Not Contacted)", new_p)
        p4.metric("Emailed", emailed_p)
        
        # Source breakdown
        if "source" in prospects_df.columns:
            st.markdown('<p class="section-header">[CHART] Prospects by Source</p>', unsafe_allow_html=True)
            src_counts = prospects_df["source"].value_counts().reset_index()
            src_counts.columns = ["source", "count"]
            fig_src = px.bar(src_counts, x="source", y="count", color="count", color_continuous_scale="Teal")
            fig_src.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=10, b=20))
            st.plotly_chart(fig_src, width="stretch")
        
        # Status breakdown
        if "status" in prospects_df.columns:
            st.markdown('<p class="section-header">[EMAIL] Prospect Status</p>', unsafe_allow_html=True)
            status_counts = prospects_df["status"].value_counts().reset_index()
            status_counts.columns = ["status", "count"]
            
            color_map = {"new": "#43e97b", "emailed": "#4facfe", "breakup_sent": "#f5576c"}
            fig_status = px.pie(status_counts, values="count", names="status", color="status", 
                               color_discrete_map=color_map, hole=0.45)
            fig_status.update_layout(margin=dict(l=20, r=20, t=10, b=20))
            st.plotly_chart(fig_status, width="stretch")
        
        # Prospect table
        st.markdown('<p class="section-header">[FIRM] All Prospects</p>', unsafe_allow_html=True)
        
        display_p_cols = [c for c in ["firm_name", "contact_name", "email", "title", "website", "source", "status", "added_at"] if c in prospects_df.columns]
        
        st.dataframe(
            prospects_df[display_p_cols],
            width="stretch",
            height=400,
            column_config={
                "website": st.column_config.LinkColumn("Website"),
                "email": st.column_config.TextColumn("Email", width="medium"),
                "firm_name": st.column_config.TextColumn("Firm Name", width="large"),
            }
        )
        
        # Export
        csv_prospects = prospects_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("[IN] Download Prospects CSV", data=csv_prospects, file_name="pe_prospects.csv", mime="text/csv")


# --- TAB 3: Email Campaigns -----------------------------
with tab3:
    if campaigns_df.empty:
        st.warning("[WARN] No emails sent yet. Run `python run.py` to start cold outreach.")
    else:
        # Campaign stats
        e1, e2, e3, e4 = st.columns(4)
        
        initial_count = len(campaigns_df[campaigns_df["email_type"] == "initial"]) if "email_type" in campaigns_df.columns else 0
        followup_count = len(campaigns_df[campaigns_df["email_type"] == "followup"]) if "email_type" in campaigns_df.columns else 0
        breakup_count = len(campaigns_df[campaigns_df["email_type"] == "breakup"]) if "email_type" in campaigns_df.columns else 0
        reply_count = int(campaigns_df["replied"].sum()) if "replied" in campaigns_df.columns else 0
        
        e1.metric("[SENT] Initial Emails", initial_count)
        e2.metric("[RETRY] Follow-ups", followup_count)
        e3.metric("[BYE] Breakup Emails", breakup_count)
        e4.metric("[REPLY] Replies", reply_count)
        
        # Reply rate
        if initial_count > 0:
            reply_rate = (reply_count / initial_count) * 100
            st.progress(min(reply_rate / 100, 1.0), text=f"[UP] Reply Rate: {reply_rate:.1f}%")
            
            if reply_rate < 3:
                st.info("[TIP] Tip: Reply rates under 3% are normal when starting. Try refining your niche in `.env`.")
            elif reply_rate >= 10:
                st.success("[HOT] Excellent reply rate! Your messaging is resonating.")
        
        # Email type breakdown
        st.markdown('<p class="section-header">[CHART] Emails by Type</p>', unsafe_allow_html=True)
        if "email_type" in campaigns_df.columns:
            type_counts = campaigns_df["email_type"].value_counts().reset_index()
            type_counts.columns = ["type", "count"]
            color_map = {"initial": "#667eea", "followup": "#4facfe", "breakup": "#f5576c"}
            fig_types = px.bar(type_counts, x="type", y="count", color="type", color_discrete_map=color_map)
            fig_types.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=10, b=20))
            st.plotly_chart(fig_types, width="stretch")
        
        # Emails sent over time
        if "sent_at" in campaigns_df.columns and campaigns_df["sent_at"].notna().any():
            st.markdown('<p class="section-header">[DATE] Emails Sent Over Time</p>', unsafe_allow_html=True)
            campaigns_df["sent_date"] = pd.to_datetime(campaigns_df["sent_at"], errors="coerce").dt.date
            daily = campaigns_df.groupby("sent_date").size().reset_index(name="count")
            fig_timeline = px.area(daily, x="sent_date", y="count", color_discrete_sequence=["#667eea"])
            fig_timeline.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=10, b=20))
            st.plotly_chart(fig_timeline, width="stretch")
        
        # Email log table
        st.markdown('<p class="section-header">[LIST] Email Log</p>', unsafe_allow_html=True)
        display_e_cols = [c for c in ["sent_at", "firm_name", "prospect_email", "email_type", "subject", "replied", "bounced"] if c in campaigns_df.columns]
        
        st.dataframe(
            campaigns_df[display_e_cols],
            width="stretch",
            height=400,
            column_config={
                "firm_name": st.column_config.TextColumn("Firm", width="medium"),
                "subject": st.column_config.TextColumn("Subject", width="large"),
                "replied": st.column_config.CheckboxColumn("Replied"),
                "bounced": st.column_config.CheckboxColumn("Bounced"),
            }
        )
        
        csv_campaigns = campaigns_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("[IN] Download Campaign Log", data=csv_campaigns, file_name="email_campaigns.csv", mime="text/csv")


# ===========================================================
#  FOOTER
# ===========================================================
st.markdown("---")
col_refresh, col_info, _ = st.columns([1, 2, 3])
with col_refresh:
    if st.button("[RETRY] Refresh Data"):
        st.rerun()
with col_info:
    st.caption(f"AI Model: `{config.AI_MODEL}` • DB Leads: {lead_stats['total_leads']} • Avg Score: {lead_stats['avg_score']}/10")

st.caption("Built with [AI] GLM-5 + [PY] Python + [GEM] Streamlit | Autonomous Deal Flow Engine v2.0")
