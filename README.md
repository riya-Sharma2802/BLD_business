# Business Listings Dashboard

A full-stack dashboard that stores business listings in MySQL, exposes aggregated reports through a FastAPI backend, and visualises them in a React + Recharts UI.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18 (Vite), Recharts |
| Backend | FastAPI, SQLAlchemy 2, PyMySQL, Pydantic v2 |
| Database | MySQL 8 (table: `listing_master`) |
| Data collection | Python, requests, BeautifulSoup (+ sample-data generator) |

## Project structure

```
backend/    FastAPI app (app/), bulk loader (load_data.py), tests/
frontend/   React dashboard (src/)
scraper/    scraper.py (config-driven, robots.txt aware) + generate_sample_data.py
database/   schema.sql, listing_master_dump.sql, make_dump.py
data/       listings.csv (620 listings)
```

## Setup

### 1. Database
```bash
mysql -u root -p < database/listing_master_dump.sql
```
This creates `listings_db`, the `listing_master` table, and loads the 620 listings.
(Prefer an empty table? Run `database/schema.sql` instead and use step 3 to load the CSV.)

### 2. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # set your MySQL password in DATABASE_URL
uvicorn app.main:app --reload --port 8000
```
Interactive API docs: http://localhost:8000/docs

### 3. (Optional) Load data through the API
```bash
cd backend
python load_data.py                  # posts ../data/listings.csv to /api/listings/bulk
```
It is idempotent: re-running skips rows that already exist.

### 4. Frontend
```bash
cd frontend
cp .env.example .env                 # VITE_API_URL=http://localhost:8000
npm install
npm run dev                          # http://localhost:5173
```

### Tests
```bash
cd backend && pytest -q              # uses SQLite, no MySQL needed
```

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/listings/bulk` | Bulk insert (`{"listings":[{...}]}`), skips duplicates, returns `received / inserted / skipped_duplicates` |
| GET | `/api/dashboard/city-wise` | `[{label, count}]` sorted by count (optional `?limit=`) |
| GET | `/api/dashboard/category-wise` | same shape |
| GET | `/api/dashboard/source-wise` | same shape |
| GET | `/api/dashboard/summary` | totals for the stat cards |

Counts are computed with `GROUP BY` in SQL (indexed columns), not in Python.

## Data collection approach

Justdial, Sulekha and Google Maps forbid automated scraping in their Terms of Service and actively block bots. Since the assignment says not to violate ToS and allows mock data, I did two things:

1. **`scraper/scraper.py`** is a working, config-driven scraper: it checks `robots.txt`, sends an honest User-Agent, rate-limits requests, and stops on 403/429 instead of evading blocks. A new site is added by giving it a URL pattern and CSS selectors in `SITE_CONFIGS`. It ships with a placeholder config only, to be pointed at a directory that permits scraping.
2. **`scraper/generate_sample_data.py`** generates 620 realistic **synthetic** listings (12 Indian cities, 14 categories, ~12% missing phone numbers like real directories, deduplicated). Every `source` value ends in "(sample)" so the data can't be mistaken for scraped data, and the phone numbers are random, not real.

**Data accuracy note:** the dashboard numbers reflect the sample dataset, not real businesses. For real data, the compliant route would be the official Google Places API.

## Design decisions

- `UNIQUE (business_name, address, source)` + app-level dedupe makes inserts idempotent.
- Indexes on `city`, `category`, `source` keep the aggregation queries fast.
- Pydantic validation trims strings, turns blank phone/address into `NULL`, and caps batch size at 5000.
- Frontend: horizontal bars for category (long labels), vertical bars for city, donut for source (few parts of a whole).

## Challenges faced

- **Scraping restrictions:** the main directories block bots and prohibit scraping, so I built a ToS-respecting scraper and a documented sample-data fallback.
- **Duplicates:** the same business can appear across pages and sources; handled with a unique key and a pre-insert check.
- **Test portability:** the tests run on SQLite so reviewers can run them without MySQL; the production DDL in `schema.sql` remains the source of truth (it uses an address prefix index, which SQLite doesn't support).
- **Long chart labels:** category names overflowed vertical bars, so that chart is horizontal.

## Demo video outline (3–5 min)

1. (1 min) Scraper: show `scraper.py` config + robots check, explain why sample data is used, run `generate_sample_data.py`.
2. (1.5 min) API: open `/docs`, run the bulk insert, show the duplicate skip on a second run, hit the three count endpoints.
3. (1.5 min) Dashboard: stats cards, three charts, tooltip hover, Refresh button, then a quick MySQL query confirming the counts match.
