import streamlit as st
import json
import os
import subprocess
from datetime import datetime
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
    .company-card {
        background: #1a1d24;
        border: 1px solid #2d3139;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
    }
    .digest-box {
        background: #1a1d24;
        border: 1px solid #2d3139;
        border-radius: 10px;
        padding: 1.5rem;
        line-height: 1.8;
        font-size: 0.95rem;
    }
    .metric-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    .tag {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-right: 4px;
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

def run_pipeline():
    with st.spinner("Running data collectors..."):
        result = subprocess.run(
            ["python", "run.py"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            st.error(f"Pipeline error: {result.stderr}")
            return False
    with st.spinner("Running AI analyzer..."):
        result = subprocess.run(
            ["python", "ai_analyzer.py"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            st.error(f"Analyzer error: {result.stderr}")
            return False
    return True

# ── Header ──────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("## 📡 MV Ops Radar")
    st.caption("Martell Ventures Portfolio Intelligence")
with col2:
    if st.button("🔄 Run Fresh Report", use_container_width=True, type="primary"):
        if run_pipeline():
            st.success("Report updated.")
            st.rerun()

st.divider()

report = load_latest_report()

if not report:
    st.info("No report found. Click **Run Fresh Report** to generate one.")
    st.stop()

generated_at = report.get("generated_at", "Unknown")
st.caption(f"Last updated: {generated_at}")

# ── Tabs ─────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📊 Portfolio Overview", "📋 Weekly Digest"])

with tab1:
    company_briefs = report.get("company_briefs", {})

    # Summary metrics
    statuses = [get_status_color(b)[1] for b in company_briefs.values()]
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Companies Tracked", len(company_briefs))
    col_b.metric("🔴 Flag", sum(1 for s in statuses if "Flag" in s))
    col_c.metric("🟡 Watch", sum(1 for s in statuses if "Watch" in s))
    col_d.metric("🟢 Strong", sum(1 for s in statuses if "Strong" in s))

    st.markdown("---")

    # Sort: Flag first, then Watch, then Strong
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

    if st.button("📋 Copy Digest to Clipboard"):
        st.code(digest, language=None)
        st.info("Select all text above and copy.")

    st.markdown("### All Company Briefs")
    all_briefs_text = "\n\n" + "="*50 + "\n\n".join(
        [f"{name}\n{'-'*len(name)}\n{brief}"
         for name, brief in report.get("company_briefs", {}).items()]
    )
    st.text_area("Full report (copy for email)", value=all_briefs_text, height=400)