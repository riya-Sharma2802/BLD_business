"""
Generate a realistic SAMPLE dataset of business listings.

Why this exists
---------------
Justdial, Sulekha and Google Maps all restrict automated scraping in their
Terms of Service (and actively block bots). The assignment allows mock data
when scraping is blocked, so this script produces 600+ synthetic listings
with the same fields the real scraper (scraper.py) would collect.

Every `source` value is suffixed with "(sample)" so nobody mistakes this for
real scraped data. Phone numbers are randomly generated and not real.

Usage:
    python generate_sample_data.py            # writes ../data/listings.csv
    python generate_sample_data.py --count 800
"""
import argparse
import csv
import random
from pathlib import Path

SEED = 42

CITIES = {
    "Delhi": ["Connaught Place", "Karol Bagh", "Lajpat Nagar", "Saket", "Rohini", "Dwarka"],
    "Mumbai": ["Andheri West", "Bandra", "Dadar", "Powai", "Borivali", "Colaba"],
    "Bengaluru": ["Indiranagar", "Koramangala", "Whitefield", "Jayanagar", "HSR Layout", "Malleshwaram"],
    "Hyderabad": ["Banjara Hills", "Madhapur", "Secunderabad", "Gachibowli", "Kukatpally"],
    "Chennai": ["T. Nagar", "Adyar", "Anna Nagar", "Velachery", "Mylapore"],
    "Kolkata": ["Park Street", "Salt Lake", "Howrah", "Ballygunge", "Dum Dum"],
    "Pune": ["Kothrud", "Viman Nagar", "Hinjewadi", "Baner", "Shivajinagar"],
    "Jaipur": ["C-Scheme", "Malviya Nagar", "Vaishali Nagar", "Mansarovar"],
    "Lucknow": ["Hazratganj", "Gomti Nagar", "Aliganj", "Indira Nagar"],
    "Meerut": ["Begum Bridge Road", "Shastri Nagar", "Abu Lane", "Delhi Road", "Sadar Bazaar"],
    "Ahmedabad": ["Navrangpura", "Satellite", "Maninagar", "Bopal"],
    "Chandigarh": ["Sector 17", "Sector 35", "Sector 22", "Manimajra"],
}
# Weight bigger metros more so the charts are not perfectly flat.
CITY_WEIGHTS = {
    "Delhi": 16, "Mumbai": 15, "Bengaluru": 14, "Hyderabad": 10, "Chennai": 9,
    "Kolkata": 8, "Pune": 8, "Jaipur": 5, "Lucknow": 4, "Meerut": 4,
    "Ahmedabad": 5, "Chandigarh": 3,
}

# category -> (name patterns). {p} = a proper-noun prefix, {a} = area
CATEGORIES = {
    "Restaurants": ["{p} Kitchen", "{p} Dhaba", "The {p} Bistro", "{p} Biryani House", "{p} Restaurant"],
    "Cafes & Bakeries": ["{p} Cafe", "{p} Bakers", "Cafe {p}", "{p} Coffee Roasters"],
    "Hospitals & Clinics": ["{p} Multispeciality Hospital", "{p} Clinic", "{p} Diagnostics", "{p} Dental Care"],
    "Education & Coaching": ["{p} Coaching Classes", "{p} Academy", "{p} Institute", "{p} Tutorials"],
    "Salons & Spas": ["{p} Unisex Salon", "{p} Beauty Studio", "{p} Spa & Wellness", "Looks by {p}"],
    "Gyms & Fitness": ["{p} Fitness Club", "{p} Gym", "{p} Yoga Studio", "Iron {p} Gym"],
    "Real Estate": ["{p} Realtors", "{p} Properties", "{p} Estate Agency", "{p} Builders"],
    "Auto Services": ["{p} Motors", "{p} Auto Care", "{p} Car Service", "{p} Tyres"],
    "Electronics & Repair": ["{p} Electronics", "{p} Mobile Repair", "{p} Computers", "{p} Appliances"],
    "Hotels & Lodging": ["Hotel {p}", "{p} Residency", "{p} Inn", "{p} Guest House"],
    "Legal & Accounting": ["{p} & Associates", "{p} Legal Services", "{p} Tax Consultants", "{p} CA Firm"],
    "Travel & Tours": ["{p} Travels", "{p} Tours & Holidays", "{p} Cab Services"],
    "Grocery & Supermarkets": ["{p} Mart", "{p} Kirana Store", "{p} Fresh Supermarket", "{p} General Store"],
    "Clothing & Boutiques": ["{p} Fashions", "{p} Boutique", "{p} Garments", "{p} Textiles"],
}
CATEGORY_WEIGHTS = {
    "Restaurants": 16, "Cafes & Bakeries": 8, "Hospitals & Clinics": 10,
    "Education & Coaching": 10, "Salons & Spas": 8, "Gyms & Fitness": 6,
    "Real Estate": 7, "Auto Services": 6, "Electronics & Repair": 6,
    "Hotels & Lodging": 5, "Legal & Accounting": 4, "Travel & Tours": 4,
    "Grocery & Supermarkets": 6, "Clothing & Boutiques": 6,
}

PREFIXES = [
    "Sharma", "Gupta", "Verma", "Royal", "Shree", "Sai", "Balaji", "Ganesh", "Krishna", "Om",
    "Annapurna", "Madhur", "Sunrise", "Golden", "Silver", "Blue Moon", "Green Leaf", "Star",
    "Metro", "City", "Elite", "Prime", "Classic", "Modern", "Urban", "Lakshmi", "Durga", "Hari",
    "Kailash", "Mahalaxmi", "Ashoka", "Maurya", "Pioneer", "Apex", "Zenith", "Orchid", "Lotus",
    "Jasmine", "Saffron", "Coral", "Ruby", "Emerald", "Diamond", "Victory", "Eagle", "Phoenix",
    "Unity", "Heritage", "Kohinoor", "Nirmal", "Anand", "Siddhi", "Vinayak", "Rajdhani",
    "Mehta", "Iyer", "Reddy", "Nair", "Banerjee", "Khanna", "Singh", "Patel", "Joshi", "Kapoor",
]

SOURCES = ["Justdial (sample)", "Sulekha (sample)", "Google Maps (sample)", "IndiaMART (sample)"]
SOURCE_WEIGHTS = [38, 24, 30, 8]


def phone():
    # Indian mobile format: 10 digits starting with 6-9
    return f"+91 {random.choice('6789')}{random.randint(1000, 9999)} {random.randint(10000, 99999)}"


def pick_weighted(weights: dict):
    return random.choices(list(weights), weights=list(weights.values()), k=1)[0]


def build(count: int):
    random.seed(SEED)
    rows, seen = [], set()
    while len(rows) < count:
        city = pick_weighted(CITY_WEIGHTS)
        category = pick_weighted(CATEGORY_WEIGHTS)
        name = random.choice(CATEGORIES[category]).format(p=random.choice(PREFIXES))
        area = random.choice(CITIES[city])
        shop_no = random.randint(1, 450)
        address = f"{random.choice(['Shop', 'Plot', 'No.', 'Unit'])} {shop_no}, {area}, {city}"
        key = (name.lower(), address.lower())
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "business_name": name,
            "category": category,
            "city": city,
            "address": address,
            # ~12% of listings have no phone, like real directories
            "phone": phone() if random.random() > 0.12 else "",
            "source": random.choices(SOURCES, weights=SOURCE_WEIGHTS, k=1)[0],
        })
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=620)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "data" / "listings.csv"))
    args = ap.parse_args()

    data = build(args.count)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["business_name", "category", "city", "address", "phone", "source"])
        w.writeheader()
        w.writerows(data)
    print(f"Wrote {len(data)} sample listings to {out}")
