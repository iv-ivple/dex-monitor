# ⚡ DEX Price Monitor

A real-time multi-DEX price monitoring service built with Python, web3.py, and Flask. Tracks live prices across Uniswap V2 and SushiSwap, calculates slippage and price impact, and surfaces arbitrage opportunities — all through a self-refreshing web dashboard.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![Web3.py](https://img.shields.io/badge/web3.py-6.11-orange)
![Redis](https://img.shields.io/badge/Redis-Cache-red?logo=redis)
![Ethereum](https://img.shields.io/badge/Ethereum-Mainnet-purple?logo=ethereum)

---

## What It Does

- Reads live reserve data directly from Uniswap V2 and SushiSwap pair contracts on Ethereum mainnet
- Calculates spot prices using the AMM constant product formula (`x * y = k`)
- Computes price spreads between DEXes and flags arbitrage opportunities
- Provides a slippage and price impact calculator for any trade size
- Caches all on-chain data in Redis (15s TTL) to minimise RPC calls
- Serves everything through a REST API and an auto-refreshing Flask dashboard

---

## Monitored Pairs

| Pair | Uniswap V2 | SushiSwap |
|---|---|---|
| WETH/USDC | `0xB4e16d...` | `0x397FF1...` |
| WETH/USDT | `0x0d4a11...` | `0x06da0f...` |
| WETH/DAI | `0xA478c2...` | `0xC3D03e...` |
| WBTC/WETH | `0xBb2b80...` | `0xCEfF51...` |

---

## Architecture

```
Browser (auto-refresh every 15s)
        │
        ▼
   Flask App (app.py)
        │
   ┌────▼─────┐
   │ API Routes│  /api/prices  /api/slippage  /api/arbitrage
   └────┬─────┘
        │
   ┌────▼──────┐       HIT       ┌─────────────┐
   │   Redis   │ ◄─────────────► │  Cache Layer │  TTL: 15s
   └────┬──────┘                 └─────────────┘
        │ MISS
   ┌────▼──────┐
   │  Fetcher  │  web3.py → eth_call → getReserves()
   └────┬──────┘
        │
   Ethereum RPC (Alchemy / Infura)
```

---

## API Endpoints

### `GET /api/prices`
Returns spot prices and reserve data for all monitored pairs across all DEXes, plus the spread between them.

```json
{
  "prices": {
    "WETH/USDC": {
      "uniswap":   { "price": 3421.55, "reserve0": 1024.3, "reserve1": 3503000 },
      "sushiswap": { "price": 3419.80, "reserve0":  812.1, "reserve1": 2776000 }
    }
  },
  "spreads": {
    "WETH/USDC": {
      "spread_pct": 0.0512,
      "best_buy":  "sushiswap",
      "best_sell": "uniswap"
    }
  },
  "cached": true
}
```

---

### `GET /api/prices/<pair>`
Returns detailed data for a single pair (e.g. `/api/prices/WETH-USDC`).

---

### `GET /api/slippage`
Calculates slippage and price impact for a given trade.

| Parameter | Type | Description |
|---|---|---|
| `pair` | string | e.g. `WETH/USDC` |
| `dex` | string | `uniswap` or `sushiswap` |
| `amount` | float | Trade size in token0 units |

```json
{
  "spot_price": 3421.55,
  "effective_price": 3417.20,
  "amount_out": 3417.20,
  "slippage_pct": 0.1271,
  "price_impact": 0.1271
}
```

---

### `GET /api/arbitrage`
Returns pairs where the price spread between DEXes exceeds a threshold.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `min_spread` | float | `0.1` | Minimum spread % to flag |

---

### `GET /api/health`
Returns service status, Redis connectivity, and number of monitored pairs.

---

## Key Concepts

### AMM Pricing (`x * y = k`)

Uniswap V2 and SushiSwap use the constant product formula. The spot price of Token A in terms of Token B is simply:

```
price = reserve_B / reserve_A
```

Reserves are read directly from the on-chain `getReserves()` function and adjusted for each token's decimals.

### Slippage & Price Impact

For a trade of size `amount_in`, the actual output differs from the spot price due to how the AMM rebalances:

```
amount_out = (amount_in × (1 - fee) × reserve_out)
             ─────────────────────────────────────────
             reserve_in + (amount_in × (1 - fee))
```

Uniswap V2 charges a 0.3% fee on every swap. Price impact grows non-linearly — a 10x larger trade causes far more than 10x the slippage.

### Arbitrage Spread

A spread above ~0.3% (after gas costs) between two DEXes for the same pair represents a theoretical arbitrage opportunity: buy on the cheaper DEX, sell on the more expensive one.

---

## Project Structure

```
dex_monitor/
├── app.py                    # Flask entry point
├── config.py                 # Pair addresses, token addresses, TTL settings
├── monitor/
│   ├── fetcher.py            # web3.py contract calls, reserve reading
│   ├── calculator.py         # AMM math: price, slippage, spread
│   └── cache.py              # Redis wrapper with graceful degradation
├── api/
│   └── routes.py             # Flask Blueprint — all API endpoints
├── templates/
│   └── dashboard.html        # Dashboard UI
├── static/
│   └── dashboard.js          # Auto-refresh, sparklines, slippage calc
├── requirements.txt
└── .env.example
```

---

## Setup & Running Locally

### 1. Clone & install dependencies

```bash
git clone https://github.com/YOUR_USERNAME/dex-monitor.git
cd dex-monitor
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY
REDIS_URL=redis://localhost:6379
```

You need an Ethereum RPC endpoint from [Alchemy](https://alchemy.com) or [Infura](https://infura.io). Redis is optional — the app degrades gracefully without it.

### 3. Start Redis (optional but recommended)

```bash
# macOS
brew services start redis

# Ubuntu
sudo systemctl start redis
```

### 4. Run the app

```bash
python app.py
```

Open [http://localhost:5001](http://localhost:5001) in your browser.

---

## Deployment (Render)

This project includes a `render.yaml` for one-click deployment to [Render](https://render.com).

1. Push the repo to GitHub
2. Connect it to Render
3. Add `RPC_URL` as an environment variable in the Render dashboard
4. Redis is provisioned automatically via `render.yaml`

---

## Tech Stack

| Tool | Purpose |
|---|---|
| `web3.py 6.11` | Ethereum RPC calls, ABI decoding |
| `Flask 3.0` | REST API and HTML dashboard |
| `Redis` | 15-second price cache |
| `python-dotenv` | Environment variable management |
| `gunicorn` | Production WSGI server |

---

## What I Learned Building This

- How Uniswap V2's `x * y = k` AMM formula determines prices from on-chain reserves
- Why decimal handling is critical — USDC has 6 decimals, WETH has 18; mixing them up breaks everything
- How slippage grows non-linearly with trade size relative to pool liquidity
- How to use the Uniswap V2 Factory contract to look up pair addresses dynamically
- How to read multiple contracts efficiently and cache results to stay within RPC rate limits
- How price spreads between DEXes create arbitrage windows (usually sub-0.5%, closing fast)

---

## Resources

- [Uniswap V2 Whitepaper](https://uniswap.org/whitepaper.pdf)
- [Uniswap V2 Core Contracts](https://github.com/Uniswap/v2-core)
- [web3.py Documentation](https://web3py.readthedocs.io/)
- [SushiSwap Documentation](https://docs.sushi.com/)
- [Alchemy — Ethereum RPC](https://www.alchemy.com/)

---

## Part of My Web3 Learning Journey

This project is Week 22–24 of my ongoing Web3 development curriculum built with Python. Previous projects include an ERC-20 analytics API, a Telegram token analytics bot, and a portfolio tracker with Redis caching.

→ [View the full learning journey](./LEARNING_JOURNEY.md)
