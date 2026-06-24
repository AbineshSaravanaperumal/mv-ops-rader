import json
import os
from gnews import GNews

SIGNAL_KEYWORDS = {
    "hiring": ["hiring", "join our team", "open role", "head of", "vp of"],
    "launch": ["launched", "shipped", "announcing", "new feature", "released", "live"],
    "fundraise": ["raised", "funding", "series", "investment", "seed", "round"],
    "partnership": ["partnership", "partnered", "collaboration", "integrates with"],
    "struggle": ["layoffs", "shutdown", "pivot", "restructure", "difficult", "challenge"]
}

def detect_signals(text: str) -> list:
    text_lower = text.lower()
    found = []
    for signal, keywords in SIGNAL_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(signal)
    return found

def fetch_founder_activity(companies: list) -> dict:
    google_news = GNews(language='en', country='US', period='7d', max_results=5)
    results = {}

    for company in companies:
        name = company["name"]
        founder = company.get("founder", "")
        print(f"  Tracking founder: {founder} ({name})...")

        if not founder:
            results[name] = {"articles": [], "signals": []}
            continue

        try:
            query = f'"{founder}" {name}'
            articles = google_news.get_news(query)

            parsed = [
                {
                    "title": a.get("title", ""),
                    "description": a.get("description", ""),
                    "published": a.get("published date", "")
                }
                for a in articles
            ]

            all_signals = []
            for a in parsed:
                text = a["title"] + " " + a["description"]
                all_signals.extend(detect_signals(text))

            results[name] = {
                "articles": parsed,
                "signals": list(set(all_signals))
            }

        except Exception as e:
            print(f"  Error fetching activity for {founder}: {e}")
            results[name] = {"articles": [], "signals": []}

    return results

if __name__ == "__main__":
    with open("companies.json") as f:
        companies = json.load(f)

    results = fetch_founder_activity(companies)

    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/founders.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Founder data saved to data/raw/founders.json")