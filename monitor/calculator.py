def calculate_slippage(amount_in, reserve_in, reserve_out):
    """
    Calculate slippage and price impact using the constant product AMM formula (x * y = k).

    Args:
        amount_in:   Amount of the input token being swapped
        reserve_in:  Pool reserve of the input token  (token you are selling)
        reserve_out: Pool reserve of the output token (token you are buying)

    Returns:
        dict with amount_out, effective_price, mid_price, slippage_pct, price_impact_pct
    """
    if reserve_in <= 0 or reserve_out <= 0:
        return {"error": "Invalid reserves"}

    # Apply 0.3% fee (standard Uniswap v2)
    amount_in_with_fee = amount_in * 0.997

    # x * y = k  →  amount_out = (amount_in_with_fee * reserve_out) / (reserve_in + amount_in_with_fee)
    amount_out = (amount_in_with_fee * reserve_out) / (reserve_in + amount_in_with_fee)

    mid_price        = reserve_out / reserve_in
    effective_price  = amount_out / amount_in
    slippage_pct     = ((mid_price - effective_price) / mid_price) * 100

    # Price impact: how much this trade shifts the pool price (before fee)
    # = amount_in / (reserve_in + amount_in)  expressed as a percentage
    price_impact_pct = (amount_in / (reserve_in + amount_in)) * 100

    return {
        "amount_in":        amount_in,
        "amount_out":       round(amount_out, 6),
        "mid_price":        round(mid_price, 6),
        "effective_price":  round(effective_price, 6),
        "slippage_pct":     round(slippage_pct, 4),
        "price_impact_pct": round(price_impact_pct, 4),
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

        min_price  = min(prices.values())
        max_price  = max(prices.values())
        spread_abs = max_price - min_price
        spread_pct = (spread_abs / min_price) * 100 if min_price > 0 else 0

        best_buy  = min(prices, key=prices.get)   # cheapest  — buy here
        best_sell = max(prices, key=prices.get)   # priciest  — sell here

        spreads[pair] = {
            "prices":     prices,
            "min_price":  min_price,
            "max_price":  max_price,
            "spread_abs": round(spread_abs, 6),
            "spread_pct": round(spread_pct, 4),
            "best_buy":   best_buy,
            "best_sell":  best_sell,
        }

    return spreads
