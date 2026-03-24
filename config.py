# DEX Factory Addresses
UNISWAP_V2_FACTORY = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
SUSHISWAP_FACTORY  = "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac"

# Token Addresses
TOKENS = {
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "DAI":  "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
}

# Monitored Pairs (hardcoded pair addresses for efficiency)
MONITORED_PAIRS = {
    "WETH/USDC": {
        "uniswap":   "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
        "sushiswap": "0x397FF1542f962076d0BFE58eA045FfA2d347ACa0",
    },
    "WETH/USDT": {
        "uniswap":   "0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852",
        "sushiswap": "0x06da0fd433C1A5d7a4faa01111c044910A184553",
    },
    "WETH/DAI": {
        "uniswap":   "0xA478c2975Ab1Ea89e8196811F51A7B7Ade33eB11",
        "sushiswap": "0xC3D03e4F041Fd4cD388c549Ee2A29a9E5075882f",
    },
    "WBTC/WETH": {
        "uniswap":   "0xBb2b8038a1640196FbE3e38816F3e67Cba72D940",
        "sushiswap": "0xCEfF51756c56CeFFCA006cD410B03FFC46dd3a58",
    },
    "USDC/DAI": {
        "uniswap": "0xAE461cA67B15dc8dc81CE7615e0320dA1A9aB8D5",
        "sushiswap": "0xAaF5110db6e744ff70fB339DE037B990A20bdace",
    },
}

# Cache TTLs
CACHE_TTL_PRICES = 15        # 15 seconds for live prices
CACHE_TTL_RESERVES = 15
