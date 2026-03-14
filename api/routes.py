from flask import Blueprint, jsonify, request
import os
from monitor.fetcher import fetch_all_pairs, fetch_pair_data
from monitor.calculator import calculate_slippage, calculate_spread
from monitor.cache import get_or_fetch, append_price_history, get_price_history
from config import CACHE_TTL_PRICES, MONITORED_PAIRS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(get_remote_address, storage_uri=os.getenv("REDIS_URL", "redis://localhost:6379"))

bp = Blueprint("dex", __name__)

@bp.route("/api/prices/<pair_name>")
def get_pair_prices(pair_name):
    pair_name = pair_name.replace("-", "/").upper()
    if pair_name not in MONITORED_PAIRS:
        return jsonify({"error": "Pair not found"}), 404
    
    def fetch():
        result = {}
        for dex, addr in MONITORED_PAIRS[pair_name].items():
            result[dex] = fetch_pair_data(addr)
        return result
    
    data, cached = get_or_fetch(f"pair:{pair_name}", fetch, CACHE_TTL_PRICES)
    return jsonify({"pair": pair_name, "data": data, "cached": cached})

@bp.route("/api/slippage")
def get_slippage():
    """
    Query params:
      pair=WETH/USDC
      dex=uniswap
      amount=1.5   (in token0 units)
    """
    pair = request.args.get("pair", "WETH/USDC")
    dex  = request.args.get("dex", "uniswap")
    amount_in = float(request.args.get("amount", 1))
    
    if pair not in MONITORED_PAIRS or dex not in MONITORED_PAIRS[pair]:
        return jsonify({"error": "Invalid pair or dex"}), 400
    
    pair_data = fetch_pair_data(MONITORED_PAIRS[pair][dex])
    result = calculate_slippage(
        amount_in,
        pair_data["reserve0"],
        pair_data["reserve1"]
    )
    return jsonify(result)

@bp.route("/api/arbitrage")
def get_arbitrage():
    """Find pairs with spread > threshold"""
    threshold = float(request.args.get("min_spread", 0.1))
    data, _ = get_or_fetch("all_prices", fetch_all_pairs, CACHE_TTL_PRICES)
    spreads = calculate_spread(data)
    
    opportunities = {
        pair: info 
        for pair, info in spreads.items() 
        if info["spread_pct"] >= threshold
    }
    return jsonify({"opportunities": opportunities, "threshold": threshold})

@bp.route("/api/history/<pair_name>/<dex>")
def get_history(pair_name, dex):
    pair_name = pair_name.replace("-", "/").upper()
    history = get_price_history(pair_name, dex)
    return jsonify({
        "pair": pair_name,
        "dex": dex,
        "history": history,
        "count": len(history)
    })

@bp.route("/api/health")
def health():
    from monitor.cache import r
    return jsonify({
        "status": "ok",
        "redis": "connected" if r else "unavailable",
        "pairs_monitored": len(MONITORED_PAIRS)
    })

@bp.route("/api/prices")
@limiter.limit("4 per minute")
def get_all_prices():
    data, cached = get_or_fetch("all_prices", fetch_all_pairs, CACHE_TTL_PRICES)
    spreads = calculate_spread(data)
    if not cached:
        for pair, dex_data in data.items():
            for dex, info in dex_data.items():
                if isinstance(info, dict) and "price" in info:
                    append_price_history(pair, dex, info["price"])
    return jsonify({"prices": data, "spreads": spreads, "cached": cached})
