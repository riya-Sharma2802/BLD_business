"""
Polite, configurable directory scraper (requests + BeautifulSoup).

IMPORTANT - read before running
--------------------------------
* Only point this at sites whose Terms of Service and robots.txt ALLOW
  automated access. Justdial, Sulekha and Google Maps prohibit scraping and
  block bots, so they are intentionally NOT hard-coded here. For those, the
  project falls back to sample data (see generate_sample_data.py) or the
  official Google Places API.
* The scraper checks robots.txt, identifies itself with a User-Agent, and
  rate-limits requests (default 2s between pages).

How it works
------------
Each target is described by a small config (SITE_CONFIGS): the listing URL
pattern plus CSS selectors for the card and each field. Add a new site by
adding a config entry - no scraping logic changes needed.

Usage:
    python scraper.py --site example --city Meerut --category restaurants --pages 5
Output: ../data/scraped_<site>.csv (same columns as listings.csv)
"""
import argparse
import csv
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

USER_AGENT = "ListingsDashboardInternBot/1.0 (educational assignment; contact: you@example.com)"
DELAY_SECONDS = 2.0

# Replace the placeholder below with a directory that permits scraping.
SITE_CONFIGS = {
    "example": {
        "source": "Example Directory",
        "url": "https://directory.example.com/{city}/{category}?page={page}",
        "card": "div.listing-card",
        "fields": {
            "business_name": "h2.name",
            "address": "p.address",
            "phone": "span.phone",
        },
    },
}


def allowed_by_robots(url: str) -> bool:
    parsed = urlparse(url)
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(f"{parsed.scheme}://{parsed.netloc}/robots.txt")
    try:
        rp.read()
    except Exception:
        return False  # if we can't verify, be conservative
    return rp.can_fetch(USER_AGENT, url)


def text_of(card, selector):
    el = card.select_one(selector)
    return el.get_text(" ", strip=True) if el else ""


def scrape(site: str, city: str, category: str, pages: int):
    cfg = SITE_CONFIGS[site]
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    rows = []
    for page in range(1, pages + 1):
        url = cfg["url"].format(city=city, category=category, page=page)
        if not allowed_by_robots(url):
            print(f"robots.txt disallows or could not be read for {url}; stopping.")
            break
        resp = session.get(url, timeout=15)
        if resp.status_code in (403, 429):
            print(f"Blocked ({resp.status_code}) at page {page}; stopping instead of evading.")
            break
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select(cfg["card"])
        if not cards:
            break
        for card in cards:
            row = {k: text_of(card, sel) for k, sel in cfg["fields"].items()}
            if not row.get("business_name"):
                continue
            row.update(category=category.replace("-", " ").title(), city=city.title(), source=cfg["source"])
            rows.append(row)
        print(f"page {page}: {len(cards)} listings")
        time.sleep(DELAY_SECONDS)
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, choices=SITE_CONFIGS)
    ap.add_argument("--city", required=True)
    ap.add_argument("--category", required=True)
    ap.add_argument("--pages", type=int, default=5)
    args = ap.parse_args()

    data = scrape(args.site, args.city, args.category, args.pages)
    out = Path(__file__).resolve().parent.parent / "data" / f"scraped_{args.site}.csv"
    cols = ["business_name", "category", "city", "address", "phone", "source"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in data:
            w.writerow({c: r.get(c, "") for c in cols})
    print(f"Saved {len(data)} rows to {out}")
