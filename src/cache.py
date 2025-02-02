import json
import os

CACHE_FILE = "data/sales_cache.json"
MAX_CACHE_ENTRIES = 100


async def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return []


async def save_cache(sales):
    if len(sales) > MAX_CACHE_ENTRIES:
        sales = sales[-MAX_CACHE_ENTRIES:]

    if not os.path.exists(CACHE_FILE):
        os.makedirs(CACHE_FILE)

    with open(CACHE_FILE, "w") as f:
        json.dump(sales, f)
