import os
import asyncio
from random import randint

from web3 import Web3
from eth_async.client import Client
from dotenv import load_dotenv

from data.config import arb_rpc
from eth_async.models import Networks


async def main(pk):
    w3 = Web3(Web3.HTTPProvider(arb_rpc))
    account = w3.eth.account.create(
        extra_entropy=str(randint(1, 999_999_999)))

    client = Client(private_key=account.key, network=Networks.Ethereum)
    print(await client.wallet.balance())


if __name__ == "__main__":
    load_dotenv()
    PK = os.getenv("PRIMARY_KEY")
    asyncio.run(main(pk=PK))
