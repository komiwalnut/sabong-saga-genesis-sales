import json
import os

CACHE_DIR = "data"
CACHE_FILE = os.path.join(CACHE_DIR, "sales_cache.json")
MAX_CACHE_ENTRIES = 100

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

if not os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "w") as f:
        json.dump([], f)


async def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return []


async def save_cache(sales):
    if len(sales) > MAX_CACHE_ENTRIES:
        sales = sales[-MAX_CACHE_ENTRIES:]
    with open(CACHE_FILE, "w") as f:
        json.dump(sales, f, indent=4)
