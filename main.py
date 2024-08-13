__all__ = ("web3", )

import os
from web3 import Web3
from utils import read_json
from dotenv import load_dotenv
from data.config import wallet, arb_rpc


load_dotenv()
PRIMARY_KEY = os.getenv('PRIMARY_KEY')


web3 = Web3(Web3.HTTPProvider(endpoint_uri=arb_rpc))
print(f"Arb Is Connected: {web3.is_connected()}")

print(f"Current Gas: {Web3.from_wei(web3.eth.gas_price, 'gwei')} gwei")


print(f"hhhscvx [Big Whale Crypto Influencer] wallet: {Web3.from_wei(web3.eth.get_balance(wallet), 'ether')} ETH")

usdc_contract_address = Web3.to_checksum_address("0xaf88d065e77c8cc2239327c5edb3a432268e5831")
token_abi = read_json("data/abis/token.json")
usdc_contract = web3.eth.contract(address=usdc_contract_address, abi=token_abi)
print(usdc_contract.functions.balanceOf(wallet).call())
