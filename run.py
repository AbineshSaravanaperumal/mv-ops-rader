import json
import os
from fetchers.news_fetcher import fetch_news
from fetchers.jobs_scraper import fetch_jobs
from fetchers.founder_tracker import fetch_founder_activity

def main():
    print("Loading companies...")
    with open("companies.json") as f:
        companies = json.load(f)

    print("\n[1/3] Fetching news...")
    news = fetch_news(companies)
    with open("data/raw/news.json", "w") as f:
        json.dump(news, f, indent=2)

    print("\n[2/3] Scraping job listings...")
    jobs = fetch_jobs(companies)
    with open("data/raw/jobs.json", "w") as f:
        json.dump(jobs, f, indent=2)

    print("\n[3/3] Tracking founder activity...")
    founders = fetch_founder_activity(companies)
    with open("data/raw/founders.json", "w") as f:
        json.dump(founders, f, indent=2)

    print("\nAll data collected. Run ai_analyzer.py next.")

if __name__ == "__main__":
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/reports", exist_ok=True)
    main()