import json
import os
from gnews import GNews
from datetime import datetime

def fetch_news(companies: list) -> dict:
    google_news = GNews(language='en', country='US', period='7d', max_results=5)
    results = {}

    for company in companies:
        name = company["name"]
        print(f"  Fetching news: {name}...")
        try:
            articles = google_news.get_news(name)
            results[name] = [
                {
                    "title": a.get("title", ""),
                    "description": a.get("description", ""),
                    "url": a.get("url", ""),
                    "published": a.get("published date", "")
                }
                for a in articles
            ]
        except Exception as e:
            print(f"  Error fetching news for {name}: {e}")
            results[name] = []

    return results

if __name__ == "__main__":
    with open("companies.json") as f:
        companies = json.load(f)

    results = fetch_news(companies)

    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/news.json", "w") as f:
        json.dump(results, f, indent=2)

    print("News data saved to data/raw/news.json")