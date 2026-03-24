# tests/test_config_live.py  ← keep separate, needs RPC

from web3 import Web3
from config import MONITORED_PAIRS
import os
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

for pair, exchanges in MONITORED_PAIRS.items():
    for dex, addr in exchanges.items():
        code = w3.eth.get_code(addr)
        assert code != b'', f"{pair} {dex} has no bytecode at {addr}"
        print(f"✅ {pair} {dex} — contract confirmed")
