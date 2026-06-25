import streamlit as st
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

st.set_page_config(
    page_title="MV Ops Radar",
    page_icon="📡",
    layout="wide"
)

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .block-container { padding-top: 1.5rem; }
    .refresh-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #1a1d24;
        border: 1px solid #2d3139;
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.78rem;
        color: #888;
    }
    .live-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #00c853;
        display: inline-block;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.3; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

def load_latest_report():
    reports_dir = Path("data/reports")
    if not reports_dir.exists():
        return None
    reports = sorted(reports_dir.glob("report_*.json"), reverse=True)
    if not reports:
        return None
    with open(reports[0]) as f:
        return json.load(f)

def get_status_color(brief_text: str):
    if "🔴" in brief_text:
        return "#ff4b4b", "🔴 Flag"
    elif "🟢" in brief_text:
        return "#00c853", "🟢 Strong"
    else:
        return "#ffa726", "🟡 Watch"

def extract_key_signal(brief_text: str) -> str:
    for line in brief_text.split("\n"):
        if "KEY SIGNAL:" in line:
            return line.replace("KEY SIGNAL:", "").strip()
    return "No signal extracted."

def next_monday(from_date: datetime) -> datetime:
    days_ahead = 7 - from_date.weekday()
    if days_ahead == 7:
        days_ahead = 0
    return from_date + timedelta(days=days_ahead)

# ── Header ──────────────────────────────────────────────
col1, col2 = st.columns([3, 1])

report = load_latest_report()
generated_at = report.get("generated_at", "") if report else ""

with col1:
    st.markdown("## 📡 MV Ops Radar")
    st.caption("Martell Ventures Portfolio Intelligence")

with col2:
    if generated_at:
        try:
            last_run = datetime.strptime(generated_at, "%Y-%m-%d %H:%M")
            next_run = next_monday(last_run)
            days_until = (next_run.date() - datetime.now().date()).days
            if days_until <= 0:
                next_label = "today"
            elif days_until == 1:
                next_label = "tomorrow"
            else:
                next_label = f"in {days_until} days"

            st.markdown(f"""
            <div class="refresh-badge">
                <span class="live-dot"></span>
                Refreshes every Monday · Next refresh {next_label}
            </div>
            """, unsafe_allow_html=True)
        except:
            st.markdown('<div class="refresh-badge"><span class="live-dot"></span> Weekly refresh active</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="refresh-badge"><span class="live-dot"></span> Weekly refresh active</div>', unsafe_allow_html=True)

st.divider()

if not report:
    st.info("No report found. Pipeline runs every Monday automatically.")
    st.stop()

st.caption(f"Last updated: {generated_at}")

# ── Tabs ─────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📊 Portfolio Overview", "📋 Weekly Digest"])

with tab1:
    company_briefs = report.get("company_briefs", {})

    col_a, col_b, col_c, col_d = st.columns(4)
    statuses = [get_status_color(b)[1] for b in company_briefs.values()]
    col_a.metric("Companies Tracked", len(company_briefs))
    col_b.metric("🔴 Flag", sum(1 for s in statuses if "Flag" in s))
    col_c.metric("🟡 Watch", sum(1 for s in statuses if "Watch" in s))
    col_d.metric("🟢 Strong", sum(1 for s in statuses if "Strong" in s))

    st.markdown("---")

    def sort_key(item):
        brief = item[1]
        if "🔴" in brief: return 0
        if "🟢" in brief: return 1
        return 2

    sorted_briefs = sorted(company_briefs.items(), key=sort_key)

    for company_name, brief_text in sorted_briefs:
        color, status_label = get_status_color(brief_text)
        key_signal = extract_key_signal(brief_text)

        with st.expander(f"{status_label}  ·  **{company_name}**  —  {key_signal}"):
            st.markdown(brief_text)

with tab2:
    digest = report.get("executive_digest", "No digest available.")

    st.markdown("### Executive Digest")
    st.caption("Cross-portfolio intelligence brief for venture studio leadership")
    st.markdown("---")

    paragraphs = [p.strip() for p in digest.split("\n\n") if p.strip()]
    labels = ["📊 Portfolio Health", "📈 Emerging Patterns", "🎯 Focus Areas"]

    for i, para in enumerate(paragraphs):
        label = labels[i] if i < len(labels) else f"Section {i+1}"
        st.markdown(f"**{label}**")
        st.markdown(para)
        st.markdown("")

    st.divider()
    st.markdown("### All Company Briefs")
    all_briefs_text = "\n\n" + "="*50 + "\n\n".join(
        [f"{name}\n{'-'*len(name)}\n{brief}"
         for name, brief in report.get("company_briefs", {}).items()]
    )
    st.text_area("Full report (copy for email)", value=all_briefs_text, height=400)