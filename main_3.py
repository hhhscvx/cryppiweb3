import asyncio
import os

from eth_async.client import Client
from eth_async.models import Networks, TokenAmount
from dotenv import load_dotenv

from tasks.shiba import Shiba


async def main(pk):
    client = Client(private_key=pk, network=Networks.Ethereum)
    shiba = Shiba(client=client)

    eth_amount = TokenAmount(amount=0.001)
    res = await shiba.swap_eth_to_usdc(amount=eth_amount)
    print(res)

    # usdc_amount = TokenAmount(amount=10, decimals=6)
    # res = await shiba.swap_usdc_to_eth(amount=usdc_amount)
    # print(res)

if __name__ == "__main__":
    load_dotenv()
    pk = os.getenv("PRIMARY_KEY")
    asyncio.run(main(pk))
