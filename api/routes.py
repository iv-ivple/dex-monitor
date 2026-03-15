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
    Calculate slippage and price impact for a given swap.

    Query params:
      pair=WETH/USDC       — trading pair name (must match MONITORED_PAIRS key)
      dex=uniswap          — which DEX to use
      amount=10            — amount of token0 (as named in the pair) to swap IN
      token_in=token0      — which token you are selling: "token0" (default) or "token1"

    Example — swap 10 ETH for USDC on the WETH/USDC pair:
      /api/slippage?pair=WETH/USDC&dex=uniswap&amount=10&token_in=token0

    BUG FIX: The contract stores tokens in address-sorted order, which for USDC/ETH means
    token0=USDC and token1=WETH. When the caller wants to sell WETH they must pass
    token_in=token1 so that reserve_in/reserve_out are oriented correctly.
    Previously the route always passed reserve0/reserve1 regardless of direction.
    """
    pair      = request.args.get("pair", "WETH/USDC").upper()
    dex       = request.args.get("dex", "uniswap")
    amount_in = float(request.args.get("amount", 1))
    token_in  = request.args.get("token_in", "token0")   # "token0" or "token1"

    if pair not in MONITORED_PAIRS or dex not in MONITORED_PAIRS[pair]:
        return jsonify({"error": "Invalid pair or dex"}), 400

    pair_data = fetch_pair_data(MONITORED_PAIRS[pair][dex])

    # Orient reserves correctly based on which token the user is selling
    if token_in == "token1":
        reserve_in  = pair_data["reserve1"]
        reserve_out = pair_data["reserve0"]
        selling     = pair_data["token1"]
        buying      = pair_data["token0"]
    else:
        reserve_in  = pair_data["reserve0"]
        reserve_out = pair_data["reserve1"]
        selling     = pair_data["token0"]
        buying      = pair_data["token1"]

    result = calculate_slippage(amount_in, reserve_in, reserve_out)
    result["selling"] = selling
    result["buying"]  = buying
    return jsonify(result)


@bp.route("/api/price-impact")
def get_price_impact():
    """
    Convenience endpoint focused on sandwich-attack analysis.
    Returns price impact for a 10 ETH swap by default.

    Query params:
      pair=WETH/USDC
      dex=uniswap
      amount=10        — ETH amount to simulate (default: 10)

    For WETH/USDC the contract has token0=USDC, token1=WETH,
    so we always set token_in=token1 (selling WETH, buying USDC).
    """
    pair      = request.args.get("pair", "WETH/USDC").upper()
    dex       = request.args.get("dex", "uniswap")
    amount_in = float(request.args.get("amount", 10))

    if pair not in MONITORED_PAIRS or dex not in MONITORED_PAIRS[pair]:
        return jsonify({"error": "Invalid pair or dex"}), 400

    pair_data = fetch_pair_data(MONITORED_PAIRS[pair][dex])

    # For WETH/USDC: token0=USDC, token1=WETH — we are selling WETH
    reserve_in  = pair_data["reserve1"]   # WETH reserve
    reserve_out = pair_data["reserve0"]   # USDC reserve

    result = calculate_slippage(amount_in, reserve_in, reserve_out)
    result["selling"]       = pair_data["token1"]
    result["buying"]        = pair_data["token0"]
    result["pool_reserves"] = {
        pair_data["token0"]: round(pair_data["reserve0"], 2),
        pair_data["token1"]: round(pair_data["reserve1"], 4),
    }
    result["sandwich_note"] = (
        f"A {amount_in} ETH swap moves the pool price by "
        f"{result['price_impact_pct']}%. A sandwicher can front-run this "
        f"and extract up to that much value from your trade."
    )
    return jsonify(result)


@bp.route("/api/arbitrage")
def get_arbitrage():
    """Find pairs with spread > threshold"""
    threshold = float(request.args.get("min_spread", 0.1))
    data, _   = get_or_fetch("all_prices", fetch_all_pairs, CACHE_TTL_PRICES)
    spreads   = calculate_spread(data)

    opportunities = {
        pair: info
        for pair, info in spreads.items()
        if info["spread_pct"] >= threshold
    }
    return jsonify({"opportunities": opportunities, "threshold": threshold})


@bp.route("/api/history/<pair_name>/<dex>")
def get_history(pair_name, dex):
    pair_name = pair_name.replace("-", "/").upper()
    history   = get_price_history(pair_name, dex)
    return jsonify({
        "pair":    pair_name,
        "dex":     dex,
        "history": history,
        "count":   len(history)
    })


@bp.route("/api/health")
def health():
    from monitor.cache import r
    return jsonify({
        "status":          "ok",
        "redis":           "connected" if r else "unavailable",
        "pairs_monitored": len(MONITORED_PAIRS)
    })


@bp.route("/api/prices")
@limiter.limit("4 per minute")
def get_all_prices():
    data, cached = get_or_fetch("all_prices", fetch_all_pairs, CACHE_TTL_PRICES)
    spreads      = calculate_spread(data)
    if not cached:
        for pair, dex_data in data.items():
            for dex, info in dex_data.items():
                if isinstance(info, dict) and "price" in info:
                    append_price_history(pair, dex, info["price"])
    return jsonify({"prices": data, "spreads": spreads, "cached": cached})
