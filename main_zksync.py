import asyncio
import os

from dotenv import load_dotenv

from tasks.mute import Mute
from eth_async.client import Client
from eth_async.models import Networks, TokenAmount


async def main(pk):
    client = Client(private_key=pk, network=Networks.ZkSync)

    mute = Mute(client=client)

    amount = TokenAmount(amount=0.001)
    print(await mute.swap_eth_to_usdc(amount=amount))

if __name__ == "__main__":
    load_dotenv()
    PRIMARY_KEY = os.getenv("PRIMARY_KEY")

    asyncio.run(main(pk=PRIMARY_KEY))
