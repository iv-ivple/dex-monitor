# tests/test_config.py

from config import TOKENS, MONITORED_PAIRS

def test_token_addresses_are_checksummed():
    from web3 import Web3
    for name, addr in TOKENS.items():
        assert Web3.is_checksum_address(addr), f"{name} is not a valid checksum address"

def test_pair_addresses_are_checksummed():
    from web3 import Web3
    for pair, exchanges in MONITORED_PAIRS.items():
        for dex, addr in exchanges.items():
            assert Web3.is_checksum_address(addr), f"{pair} {dex} is not a valid checksum address"

def test_required_tokens_present():
    for token in ["WETH", "USDC", "DAI", "USDT", "WBTC"]:
        assert token in TOKENS, f"{token} missing from TOKENS"

def test_required_pairs_present():
    for pair in ["WETH/USDC", "WETH/DAI", "WETH/USDT", "USDC/DAI"]:
        assert pair in MONITORED_PAIRS, f"{pair} missing from MONITORED_PAIRS"

def test_all_pairs_have_both_dexes():
    for pair, exchanges in MONITORED_PAIRS.items():
        assert "uniswap" in exchanges, f"{pair} missing uniswap address"
        assert "sushiswap" in exchanges, f"{pair} missing sushiswap address"
