from __future__ import annotations
from typing import TYPE_CHECKING

from web3 import Web3
from eth_typing import ChecksumAddress
from web3.contract.async_contract import AsyncContract

from .utils.utils import async_get
from .utils.string import text_between
from .models import DefaultABIs, RawContract
from .types import Contract


if TYPE_CHECKING:
    from .client import Client


class Contracts:
    def __init__(self, client: Client) -> None:
        self.client = client

    async def default_token(self, contract_address: str | ChecksumAddress) -> AsyncContract:
        contract_address = Web3.to_checksum_address(contract_address)
        return self.client.w3.eth.contract(address=contract_address, abi=DefaultABIs.Token)

    @staticmethod
    async def get_signature(hex_signature: str) -> list | None:
        try:
            response = await async_get(f"https://www.4byte.directory/api/v1/signatures/?hex_signature={hex_signature}")
            results = response['results']
            return [m['text_signature'] for m in sorted(results, key=lambda result: result['created_at'])]
        except:
            return

    @staticmethod
    async def parse_function(text_signature: str):
        # swap(address,address,uint256,uint256,address,address)

        name, sign = text_signature.split('(', 1)
        sign = sign[:-1]
        tuples = []
        while '(' in sign:
            tuple_ = text_between(text=sign[:-1], begin='(', end=')')
            tuples.append(tuple_.split(',') or [])
            sign = sign.replace(f'({tuple_})', 'tuple')

        inputs = sign.split(',')
        if inputs == ['']:
            inputs = []

        function = {
            'type': 'function',
            'name': name,
            'inputs': [],
            'outputs': [{'type': 'uint256'}]
        }
        i = 0
        for type_ in inputs:
            input_ = {'type': type_}
            if type_ == 'tuple':
                input_['components'] = [{'type': comp_type} for comp_type in tuples[i]]
                i += 1

            function['inputs'].append(input_)

        return function

    @staticmethod
    async def get_contract_attributes(contract: Contract):
        if isinstance(contract, (AsyncContract, RawContract)):
            return contract.address, contract.abi

        return Web3.to_checksum_address(contract.address), None

    async def get(
        self, contract_address, abi: list | str | None = None
    ) -> AsyncContract | Contract:
        """
        Get a contract instance

        :return AsyncContract: the contract instance.
        """
        # если contract адрес RawContract или AsyncContract то мы распарсим его abi
        contract_address, contract_abi = await self.get_contract_attributes(contract=contract_address)

        if not abi and not contract_abi:
            raise ValueError("Can`t get abi for contract.")

        if not abi:
            abi = contract_abi

        if abi:
            return self.client.w3.eth.contract(address=contract_address, abi=abi)
        return self.client.w3.eth.contract(address=contract_address)
