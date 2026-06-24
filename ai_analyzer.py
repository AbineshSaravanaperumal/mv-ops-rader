import json
import os
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def load_raw_data():
    with open("data/raw/news.json") as f:
        news = json.load(f)
    with open("data/raw/jobs.json") as f:
        jobs = json.load(f)
    with open("data/raw/founders.json") as f:
        founders = json.load(f)
    return news, jobs, founders

def build_company_brief(company_name: str, news: list, jobs: dict, founder: dict) -> str:
    news_text = "\n".join([f"- {a['title']}: {a['description']}" for a in news]) or "No news this week."
    jobs_text = f"{jobs.get('trend', 'Unknown')} (hiring signals: {jobs.get('hiring_signals', 0)}, freeze signals: {jobs.get('freeze_signals', 0)})"
    
    founder_articles = founder.get("articles", [])
    founder_text = "\n".join([f"- {a['title']}" for a in founder_articles]) or "No founder activity found."
    founder_signals = founder.get("signals", [])
    signals_text = ", ".join(founder_signals) if founder_signals else "none detected"

    prompt = f"""You are an operations analyst at a venture studio reviewing portfolio company signals.

Company: {company_name}

SIGNALS THIS WEEK:
News mentions:
{news_text}

Hiring trend: {jobs_text}

Founder activity:
{founder_text}
Detected signals: {signals_text}

Generate a structured brief with exactly this format:

STATUS: [🟢 Strong / 🟡 Watch / 🔴 Flag] — pick one based on overall signal quality
KEY SIGNAL: One sentence. The single most important thing happening at this company right now.
WINS: Up to 3 bullet points of positive signals. Skip if none.
RISKS: Up to 3 bullet points of concerns or red flags. Skip if none.
RECOMMENDATION: One action the venture studio should take this week regarding this company.

Be specific and direct. No filler. If there is genuinely no signal, say "Quiet week — no notable activity detected." and give STATUS 🟡 Watch."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=400
    )
    return response.choices[0].message.content.strip()

def build_executive_digest(all_briefs: dict) -> str:
    briefs_text = "\n\n---\n\n".join([f"{name}:\n{brief}" for name, brief in all_briefs.items()])

    prompt = f"""You are the head of operations at Martell Ventures reviewing your full portfolio for the week.

Here are the individual company briefs:

{briefs_text}

Write a concise executive digest in exactly 3 paragraphs:

Paragraph 1 — PORTFOLIO HEALTH: Which companies need immediate attention this week and why. Name them specifically.
Paragraph 2 — EMERGING PATTERNS: What trends are you seeing across multiple companies (hiring, market signals, founder activity). Be specific.
Paragraph 3 — FOCUS AREAS: The top 2 recommended actions for the venture studio leadership this week. Be direct and actionable.

No headers. No bullet points. Plain paragraphs. Write as if you are briefing Dan Martell on a Monday morning."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=600
    )
    return response.choices[0].message.content.strip()

def main():
    print("Loading raw data...")
    news, jobs, founders = load_raw_data()

    with open("companies.json") as f:
        companies = json.load(f)

    print("\nGenerating per-company briefs...")
    all_briefs = {}

    for company in companies:
        name = company["name"]
        print(f"  Analyzing: {name}...")
        try:
            brief = build_company_brief(
                company_name=name,
                news=news.get(name, []),
                jobs=jobs.get(name, {}),
                founder=founders.get(name, {})
            )
            all_briefs[name] = brief
        except Exception as e:
            print(f"  Error analyzing {name}: {e}")
            all_briefs[name] = "Analysis failed."

    print("\nGenerating executive digest...")
    try:
        digest = build_executive_digest(all_briefs)
    except Exception as e:
        print(f"  Error generating digest: {e}")
        digest = "Digest generation failed."

    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "executive_digest": digest,
        "company_briefs": all_briefs
    }

    os.makedirs("data/reports", exist_ok=True)
    report_path = f"data/reports/report_{datetime.now().strftime('%Y%m%d')}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to {report_path}")
    print("\n" + "="*60)
    print("EXECUTIVE DIGEST")
    print("="*60)
    print(digest)
    print("\n" + "="*60)
    print("COMPANY BRIEFS")
    print("="*60)
    for name, brief in all_briefs.items():
        print(f"\n[ {name} ]")
        print(brief)

if __name__ == "__main__":
    main()