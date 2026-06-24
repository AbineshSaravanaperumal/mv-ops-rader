import json
import os
from gnews import GNews
from datetime import datetime

HISTORY_FILE = "data/jobs_history.json"

HIRING_KEYWORDS = ["hiring", "we're hiring", "join our team", "open role", "now hiring",
                   "head of", "vp of", "engineer", "manager", "director", "looking for"]

FREEZE_KEYWORDS = ["layoffs", "laid off", "downsizing", "restructuring", "letting go", "cuts"]

def load_history() -> dict:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {}

def save_history(history: dict):
    os.makedirs("data", exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def fetch_jobs(companies: list) -> dict:
    google_news = GNews(language='en', country='US', period='7d', max_results=8)
    history = load_history()
    results = {}
    today = datetime.now().strftime("%Y-%m-%d")

    for company in companies:
        name = company["name"]
        print(f"  Scanning jobs signal: {name}...")

        try:
            query = f'"{name}" hiring OR jobs OR careers'
            articles = google_news.get_news(query)

            hiring_signals = 0
            freeze_signals = 0
            job_articles = []

            for a in articles:
                text = (a.get("title", "") + " " + a.get("description", "")).lower()
                h = sum(1 for kw in HIRING_KEYWORDS if kw in text)
                f = sum(1 for kw in FREEZE_KEYWORDS if kw in text)
                hiring_signals += h
                freeze_signals += f
                if h > 0 or f > 0:
                    job_articles.append({
                        "title": a.get("title", ""),
                        "published": a.get("published date", "")
                    })

            prev = history.get(name, {}).get("hiring_signals", hiring_signals)
            delta = hiring_signals - prev

            if freeze_signals > 2:
                trend = "↓ Freeze signals"
            elif hiring_signals > 3:
                trend = "↑ Active hiring"
            elif delta > 1:
                trend = "↑ Hiring up"
            elif delta < -1:
                trend = "↓ Hiring down"
            else:
                trend = "→ Stable"

            results[name] = {
                "hiring_signals": hiring_signals,
                "freeze_signals": freeze_signals,
                "prev_hiring_signals": prev,
                "delta": delta,
                "trend": trend,
                "articles": job_articles
            }

            history[name] = {"hiring_signals": hiring_signals, "last_updated": today}

        except Exception as e:
            print(f"  Error scanning jobs for {name}: {e}")
            results[name] = {
                "hiring_signals": 0,
                "freeze_signals": 0,
                "prev_hiring_signals": 0,
                "delta": 0,
                "trend": "→ Unknown",
                "articles": []
            }

    save_history(history)
    return results

if __name__ == "__main__":
    with open("companies.json") as f:
        companies = json.load(f)

    results = fetch_jobs(companies)

    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/jobs.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Jobs data saved to data/raw/jobs.json")