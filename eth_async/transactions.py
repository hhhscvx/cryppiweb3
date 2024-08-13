from __future__ import annotations
from typing import TYPE_CHECKING

from web3 import Web3

from .models import TokenAmount

if TYPE_CHECKING:
    from .client import Client


class Transactions:
    def __init__(self, client: Client) -> None:
        self.client = client

    async def gas_price(self):
        gas = await self.client.w3.eth.gas_price()
        return TokenAmount(amount=gas, wei=True)
