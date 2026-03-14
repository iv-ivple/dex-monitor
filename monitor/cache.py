import redis, json, os, time
from dotenv import load_dotenv

load_dotenv()

try:
    r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    r.ping()
    print("Redis connected")
except Exception:
    r = None
    print("Redis unavailable — running without cache")

def get(key):
    if not r:
        return None
    try:
        val = r.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None

def set(key, value, ttl=15):
    if not r:
        return
    try:
        r.setex(key, ttl, json.dumps(value))
    except Exception:
        pass

def get_or_fetch(key, fetch_fn, ttl=15):
    cached = get(key)
    if cached:
        return cached, True   # (data, from_cache)
    fresh = fetch_fn()
    set(key, fresh, ttl)
    return fresh, False

# In monitor/cache.py
def append_price_history(pair, dex, price, max_points=60):
    key = f"history:{pair}:{dex}"
    history = get(key) or []
    history.append({"price": price, "t": time.time()})
    history = history[-max_points:]   # keep last 60 points
    set(key, history, ttl=3600)

def get_price_history(pair, dex):
    return get(f"history:{pair}:{dex}") or []
