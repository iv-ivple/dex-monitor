def calculate_slippage(amount_in, reserve0, reserve1):
    """
    Calculate slippage using the constant product AMM formula (x * y = k).

    Args:
        amount_in: Amount of token0 being swapped
        reserve0:  Pool reserve of token0
        reserve1:  Pool reserve of token1

    Returns:
        dict with amount_out, effective_price, mid_price, slippage_pct
    """
    if reserve0 <= 0 or reserve1 <= 0:
        return {"error": "Invalid reserves"}

    # Apply 0.3% fee (standard Uniswap v2)
    amount_in_with_fee = amount_in * 0.997

    # x * y = k  →  amount_out = (amount_in_with_fee * reserve1) / (reserve0 + amount_in_with_fee)
    amount_out = (amount_in_with_fee * reserve1) / (reserve0 + amount_in_with_fee)

    mid_price = reserve1 / reserve0
    effective_price = amount_out / amount_in
    slippage_pct = ((mid_price - effective_price) / mid_price) * 100

    return {
        "amount_in": amount_in,
        "amount_out": amount_out,
        "mid_price": mid_price,
        "effective_price": effective_price,
        "slippage_pct": round(slippage_pct, 4),
    }


def calculate_spread(data):
    """
    Calculate the price spread between DEXes for each trading pair.

    Args:
        data: dict shaped as { "WETH/USDC": { "uniswap": {...}, "sushiswap": {...} }, ... }
              Each DEX entry must contain a "price" key.

    Returns:
        dict shaped as {
            "WETH/USDC": {
                "prices": { "uniswap": 1800.0, ... },
                "min_price": 1800.0,
                "max_price": 1820.0,
                "spread_abs": 20.0,
                "spread_pct": 1.11,
                "best_buy":  "uniswap",
                "best_sell": "sushiswap",
            }, ...
        }
    """
    spreads = {}

    for pair, dex_data in data.items():
        prices = {
            dex: info["price"]
            for dex, info in dex_data.items()
            if isinstance(info, dict) and "price" in info and info["price"] is not None
        }

        if len(prices) < 2:
            spreads[pair] = {"prices": prices, "spread_pct": 0, "error": "Not enough DEXes to compare"}
            continue

        min_price = min(prices.values())
        max_price = max(prices.values())
        spread_abs = max_price - min_price
        spread_pct = (spread_abs / min_price) * 100 if min_price > 0 else 0

        best_buy  = min(prices, key=prices.get)   # cheapest — buy here
        best_sell = max(prices, key=prices.get)   # most expensive — sell here

        spreads[pair] = {
            "prices": prices,
            "min_price": min_price,
            "max_price": max_price,
            "spread_abs": round(spread_abs, 6),
            "spread_pct": round(spread_pct, 4),
            "best_buy": best_buy,
            "best_sell": best_sell,
        }

    return spreads
