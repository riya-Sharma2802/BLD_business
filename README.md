# Business Listings Dashboard

A small full-stack app that **collects** business listings, **stores** them in MySQL, and **visualises** them on a React dashboard.

![Dashboard](screenshots/dashboard.png)

## What it does

```
OpenStreetMap  →  Python collector  →  MySQL  →  FastAPI  →  React dashboard
 (data source)      (osm_collector.py)  (listing_master)  (REST API)   (charts)
```

1. **Collect:** a Python script pulls real business listings (name, category, city, address, phone, source) from OpenStreetMap for 12 Indian cities. About 4,800 listings are loaded.
2. **Store:** the listings live in one MySQL table, `listing_master`.
3. **Serve:** FastAPI exposes a bulk-insert endpoint and three aggregation endpoints (city, category, source).
4. **Show:** the React dashboard calls the API and draws a bar chart (cities), a horizontal bar chart (categories) and a donut chart (sources), plus summary cards.
5. **Explore:** click any bar or slice to filter. All charts, cards and a searchable listings table update together (e.g. click *Delhi* to see Delhi's categories and sources). There is also a light/dark theme toggle.

## Tech stack

- **Frontend:** React (Vite), Recharts
- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **Database:** MySQL 8
- **Data collection:** Python, `requests`

## Project structure

```
backend/    FastAPI app and tests
frontend/   React dashboard
scraper/    osm_collector.py (real data), scraper.py (generic), generate_sample_data.py (fallback)
database/   schema.sql, listing_master_dump.sql, make_dump.py
data/       listings.csv
```

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/listings/bulk` | Bulk insert listings; duplicates are skipped |
| GET | `/api/dashboard/city-wise` | Count per city (optional `category`, `source` filters) |
| GET | `/api/dashboard/category-wise` | Count per category (optional `city`, `source`) |
| GET | `/api/dashboard/source-wise` | Count per source (optional `city`, `category`) |
| GET | `/api/dashboard/summary` | Totals for the summary cards (optional `city`, `category`, `source`) |
| GET | `/api/listings` | Paginated listings with `city`, `category`, `source`, `search`, `page`, `page_size` |

Interactive docs: `http://localhost:8000/docs`

## Setup

You need Python 3.10+, Node.js 18+ and MySQL 8.

**1. Database** – import the dump (it creates `listings_db` and `listing_master` with the data):
```bash
mysql -u root -p < database/listing_master_dump.sql
```
(or open the file in MySQL Workbench and run it)

**2. Backend**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # Mac/Linux: cp .env.example .env
```
Edit `.env` and put your MySQL password in `DATABASE_URL` (write `@` in a password as `%40`). Then:
```bash
uvicorn app.main:app --reload --port 8000
```

**3. Frontend** (new terminal)
```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```
Open `http://localhost:5173`.

**Optional – refresh the data**
```bash
cd scraper
python osm_collector.py              # writes data/listings_osm.csv
cd ..
python database/make_dump.py --csv data/listings_osm.csv
```
Then re-import the dump. To insert through the API instead: `python backend/load_data.py --csv data/listings_osm.csv`.

**Tests:** `cd backend && pytest -q` (uses SQLite, no MySQL needed).

## Data source and scraping approach

Justdial, Sulekha and Google Maps forbid scraping in their terms of service, so I did not scrape them. I used **OpenStreetMap** (open data, ODbL licence) through its Overpass API, which is meant for queries. The collector sends one query per city, waits between queries, identifies itself with a User-Agent, retries on busy servers, and saves progress after every city.

- Only places with a name are kept; duplicates are removed.
- If OSM has no phone, the phone is left empty. If it has no street address, the address uses the place's real coordinates (`Near lat, lon, City`).
- Each city keeps a share (default run: 10%, between 100 and 600) of the listings OSM has for it, using the collector's `--ratio` option. Bigger cities therefore keep more rows than smaller ones, which keeps the dataset a manageable size. This is a sample of OSM, not a full census.

Data © OpenStreetMap contributors. Counts reflect what OSM contains, not a full census of businesses.

## Challenges faced

- **Scraping restrictions:** the main directories block bots, so I used an open data source instead.
- **Busy servers:** the public Overpass servers sometimes return 502/504. The collector retries, falls back to mirror servers and resumes from the last saved city.
- **Incomplete data:** many OSM places lack a phone or address, so missing values are kept empty rather than invented.
- **Duplicates:** a unique key (name, address, source) and `INSERT IGNORE` keep re-imports safe.
