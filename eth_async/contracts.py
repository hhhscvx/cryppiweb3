from __future__ import annotations
from typing import TYPE_CHECKING

from web3 import Web3
from eth_typing import ChecksumAddress
from web3.contract.async_contract import AsyncContract

from .models import DefaultABIs


if TYPE_CHECKING:
    from .client import Client


class Contracts:
    def __init__(self, client: Client) -> None:
        self.client = client

    async def default_token(self, checksum_address: str | ChecksumAddress) -> AsyncContract:
        checksum_address = Web3.to_checksum_address(checksum_address)
        return self.client.w3.eth.contract(address=checksum_address, abi=DefaultABIs.Token)
