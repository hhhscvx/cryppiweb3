from __future__ import annotations
from typing import TYPE_CHECKING

from web3 import Web3
from eth_typing import ChecksumAddress

from .models import TokenAmount
from eth_async.types import Contract


if TYPE_CHECKING:
    from .client import Client


class Wallet:
    def __init__(self, client: Client) -> None:
        self.client = client

    async def balance(self,
                      token_address: str | ChecksumAddress | None = None,
                      address: str | ChecksumAddress | None = None,
                      decimals: int = 18) -> TokenAmount:
        if not address:
            address = self.client.account.address
        address = Web3.to_checksum_address(value=address)

        if not token_address:
            return TokenAmount(amount=await self.client.w3.eth.get_balance(address),
                               decimals=decimals,
                               wei=True)
        token_address = Web3.to_checksum_address(token_address)
        contract: Contract = self.client.contracts.default_token(token_address)
        return TokenAmount(amount=await contract.functions.balanceOf(address).call(),
                           decimals=await self.client.transactions.get_decimals(contract=contract),
                           wei=True)

    async def nonce(self, address: ChecksumAddress | None = None) -> int:
        if not address:
            address = self.client.account.address
        return await self.client.w3.eth.get_transaction_count(address)
