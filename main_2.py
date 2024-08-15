import asyncio
import json
import os

import aiohttp
from web3 import Web3
from web3.eth.async_eth import AsyncEth
from eth_account.signers.local import LocalAccount
from dotenv import load_dotenv

from data.config import arb_rpc


contract_address = Web3.to_checksum_address('0x9aEd3A8896A85FE9a8CAc52C9B402D092B629a30')
abi = json.loads(
    '[{"inputs":[{"internalType":"address","name":"_weth","type":"address"},{"internalType":"address","name":"_pool","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"newPool","type":"address"}],"name":"WooPoolChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"enum IWooRouterV2.SwapType","name":"swapType","type":"uint8"},{"indexed":true,"internalType":"address","name":"fromToken","type":"address"},{"indexed":true,"internalType":"address","name":"toToken","type":"address"},{"indexed":false,"internalType":"uint256","name":"fromAmount","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"toAmount","type":"uint256"},{"indexed":false,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"address","name":"rebateTo","type":"address"}],"name":"WooRouterSwap","type":"event"},{"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"approveTarget","type":"address"},{"internalType":"address","name":"swapTarget","type":"address"},{"internalType":"address","name":"fromToken","type":"address"},{"internalType":"address","name":"toToken","type":"address"},{"internalType":"uint256","name":"fromAmount","type":"uint256"},{"internalType":"uint256","name":"minToAmount","type":"uint256"},{"internalType":"address payable","name":"to","type":"address"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"externalSwap","outputs":[{"internalType":"uint256","name":"realToAmount","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"stuckToken","type":"address"}],"name":"inCaseTokenGotStuck","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"isWhitelisted","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"fromToken","type":"address"},{"internalType":"address","name":"toToken","type":"address"},{"internalType":"uint256","name":"fromAmount","type":"uint256"}],"name":"querySwap","outputs":[{"internalType":"uint256","name":"toAmount","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"quoteToken","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newPool","type":"address"}],"name":"setPool","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"target","type":"address"},{"internalType":"bool","name":"whitelisted","type":"bool"}],"name":"setWhitelisted","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"fromToken","type":"address"},{"internalType":"address","name":"toToken","type":"address"},{"internalType":"uint256","name":"fromAmount","type":"uint256"},{"internalType":"uint256","name":"minToAmount","type":"uint256"},{"internalType":"address payable","name":"to","type":"address"},{"internalType":"address","name":"rebateTo","type":"address"}],"name":"swap","outputs":[{"internalType":"uint256","name":"realToAmount","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"fromToken","type":"address"},{"internalType":"address","name":"toToken","type":"address"},{"internalType":"uint256","name":"fromAmount","type":"uint256"}],"name":"tryQuerySwap","outputs":[{"internalType":"uint256","name":"toAmount","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"wooPool","outputs":[{"internalType":"contract IWooPPV2","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"stateMutability":"payable","type":"receive"}]'
)


async def get_token_price(from_token, to_token) -> float | None:
    from_token, to_token = from_token.upper(), to_token.upper()
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"https://api.binance.com/api/v3/ticker/price?symbol={from_token}{to_token}"
        ) as resp:
            result = await resp.json()
            if 'msg' in result and result['msg'] == "Invalid symbol.":
                async with session.get(
                    url=f"https://api.binance.com/api/v3/ticker/price?symbol={to_token}{from_token}"
                ) as resp:
                    result = await resp.json()
            return float(result['price'])


async def get_min_to_amount(from_token: str, to_token: str, decimals: float = 0.5):
    token_price = await get_token_price(from_token=from_token, to_token=to_token)
    return token_price * (1 - decimals / 100)  # decimals = slippage


async def main(primary_key):
    web3 = Web3(
        Web3.AsyncHTTPProvider(
            endpoint_uri=arb_rpc,
        ),
        modules={'eth': (AsyncEth, )},
        middlewares=[]
    )
    account: LocalAccount = web3.eth.account.from_key(private_key=primary_key)
    wallet_address = account.address

    contract = web3.eth.contract(abi=abi)

    from_token = Web3.to_checksum_address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE')
    usdc_address = Web3.to_checksum_address('0xaf88d065e77c8cC2239327C5EDb3A432268e5831')
    eth_amount = 0.001
    min_to_amount = await get_min_to_amount(from_token='ETH', to_token='USDC')

    # Function: swap(address fromToken,address toToken,uint256 fromAmount,uint256 minToAmount,address to,address rebateTo)
    data = contract.encodeABI(
        'swap',
        args=(
            from_token,
            usdc_address,
            int(eth_amount * 10 ** 18),
            int(min_to_amount * 10 ** 6),  # 6 это decimals из контракта usdc
            wallet_address,
            wallet_address
        )
    )
    # function_signature = data[:10] == 0x7dc20382
    # [0]: 000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee == data[:64]

    tx = {  # эти данные смотреть в TxData (клик по transaction в estimate_gas)
        'chainId': await web3.eth.chain_id,
        'gasPrice': await web3.eth.gas_price,
        'nonce': await web3.eth.get_transaction_count(),
        'from': Web3.to_checksum_address(wallet_address),
        'to': Web3.to_checksum_address(contract_address),
        'data': data,
        'value': int(eth_amount * 10 ** 18)
    }

    tx['gas'] = await web3.eth.estimate_gas(transaction=tx)


if __name__ == "__main__":
    load_dotenv()
    primary_key = os.getenv("PRIMARY_KEY")
    asyncio.run(main(primary_key=primary_key))

# 1:08:00 досмотрю че он объясняет потом буду переписывать методы/классы
