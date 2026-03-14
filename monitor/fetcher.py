from web3 import Web3
import os, time
from dotenv import load_dotenv
from config import MONITORED_PAIRS

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

# Minimal Pair ABI — only what we need
PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "_reserve0", "type": "uint112"},
            {"name": "_reserve1", "type": "uint112"},
            {"name": "_blockTimestampLast", "type": "uint32"}
        ],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token0",
        "outputs": [{"name": "", "type": "address"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token1",
        "outputs": [{"name": "", "type": "address"}],
        "type": "function"
    }
]

# ERC-20 ABI for token details
ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
]

def get_pair_price(pair_address):
    pair = w3.eth.contract(address=Web3.to_checksum_address(pair_address), abi=PAIR_ABI)
    
    token0_addr = pair.functions.token0().call()
    token1_addr = pair.functions.token1().call()
    reserves = pair.functions.getReserves().call()
    
    token0 = w3.eth.contract(address=token0_addr, abi=ERC20_ABI)
    token1 = w3.eth.contract(address=token1_addr, abi=ERC20_ABI)
    
    symbol0 = token0.functions.symbol().call()
    symbol1 = token1.functions.symbol().call()
    dec0 = token0.functions.decimals().call()
    dec1 = token1.functions.decimals().call()
    
    # Adjust for decimals
    reserve0 = reserves[0] / (10 ** dec0)
    reserve1 = reserves[1] / (10 ** dec1)
    
    price_0_in_1 = reserve1 / reserve0
    price_1_in_0 = reserve0 / reserve1
    
    return {
        "token0": symbol0,
        "token1": symbol1,
        "reserve0": reserve0,
        "reserve1": reserve1,
        "price": price_0_in_1,  # price of token0 in token1
        "pair_address": pair_address
    }


_token_cache = {}   # in-memory cache for token metadata

def get_token_info(address):
    if address in _token_cache:
        return _token_cache[address]
    token = w3.eth.contract(address=Web3.to_checksum_address(address), abi=ERC20_ABI)
    info = {
        "symbol": token.functions.symbol().call(),
        "decimals": token.functions.decimals().call()
    }
    _token_cache[address] = info
    return info

def fetch_pair_data(pair_address):
    pair = w3.eth.contract(address=Web3.to_checksum_address(pair_address), abi=PAIR_ABI)
    token0_addr = pair.functions.token0().call()
    token1_addr = pair.functions.token1().call()
    reserves = pair.functions.getReserves().call()
    
    t0 = get_token_info(token0_addr)
    t1 = get_token_info(token1_addr)
    
    r0 = reserves[0] / (10 ** t0["decimals"])
    r1 = reserves[1] / (10 ** t1["decimals"])
    
    return {
        "token0": t0["symbol"],
        "token1": t1["symbol"],
        "reserve0": r0,
        "reserve1": r1,
        "price": r1 / r0,
        "timestamp": time.time()
    }

def fetch_all_pairs():
    results = {}
    for pair_name, dexes in MONITORED_PAIRS.items():
        results[pair_name] = {}
        for dex_name, pair_addr in dexes.items():
            try:
                results[pair_name][dex_name] = fetch_pair_data(pair_addr)
            except Exception as e:
                results[pair_name][dex_name] = {"error": str(e)}
    return results
