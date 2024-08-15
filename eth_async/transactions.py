from __future__ import annotations
from typing import TYPE_CHECKING, Any
from hexbytes import HexBytes

from web3 import Web3
from web3.types import TxParams, _Hash32, TxData, TxReceipt
from eth_account.datastructures import SignedTransaction

from .models import TokenAmount, CommonValue, TxArgs
from .exceptions import TransactionException, GasTooHigh
from .types import Contract, Address, Amount, GasPrice, GasLimit

if TYPE_CHECKING:
    from .client import Client


class Tx:
    receipt: TxReceipt

    def __init__(self, tx_hash: str | _Hash32 | None = None, params: dict | None = None) -> None:
        if not tx_hash or not params:
            raise TransactionException("'tx_hash' or 'params' required!")

        if isinstance(tx_hash, str):
            tx_hash = HexBytes(tx_hash)

        self.hash = tx_hash
        self.params = params
        self.receipt = None
        self.function_identifier = None
        self.input_data = None

    async def parse_params(self, client: Client) -> dict[str, Any]:
        tx_data: TxData = await client.w3.eth.get_transaction(transaction_hash=self.hash)
        self.params = {
            'chainId': client.network.chain_id,
            'nonce': int(tx_data.get('nonce')),
            'gasPrice': int(tx_data.get('gasPrice')),
            'gas': int(tx_data.get('gas')),
            'from': tx_data.get('from'),
            'to': tx_data.get('to'),
            'data': tx_data.get('data'),
            'value': int(tx_data.get('value')),
        }
        return self.params

    async def wait_for_receipt(
            self, client: Client, timeout: int | float = 120, poll_latency: float = 0.1
    ) -> dict[str, Any]:
        self.receipt = dict(await client.w3.eth.wait_for_transaction_receipt(
            transaction_hash=self.hash, timeout=timeout, poll_latency=poll_latency
        ))

    async def decode_input_data(self):
        pass

    async def cancel(self):
        pass

    async def speed_up(self):
        pass


class Transactions:
    def __init__(self, client: Client) -> None:
        self.client = client

    async def gas_price(self) -> TokenAmount:
        """Цена газа"""
        gas = await self.client.w3.eth.gas_price
        return TokenAmount(amount=gas, wei=True)

    async def max_priority_fee(self) -> TokenAmount:
        max_priority_fee = await self.client.w3.eth.max_priority_fee
        return TokenAmount(amount=max_priority_fee, wei=True)

    async def estimate_gas(self, tx_params: TxParams) -> TokenAmount:
        """Сколько газа будет"""
        gas = await self.client.w3.eth.estimate_gas(transaction=tx_params)
        return TokenAmount(amount=gas, wei=True)

    async def auto_add_params(self, tx_params: TxParams) -> TxParams:
        """Дополнение необходимых параметров для транзакции"""
        if 'chainId' not in tx_params:
            tx_params['chainId'] = self.client.w3.eth.chain_id

        if 'nonce' not in tx_params:
            tx_params['nonce'] = await self.client.wallet.nonce()
        if 'gasPrice' not in tx_params and 'maxFeePerGas' not in tx_params:
            gas_price = (await self.gas_price()).Wei
            if self.client.network.tx_type == 2:
                TxParams['maxFeePerGas'] = gas_price
            else:
                tx_params['gasPrice'] = gas_price

        if 'gasPrice' in tx_params and not int(tx_params['gas']):
            tx_params['gas'] = (await self.gas_price()).Wei

        if 'maxFeePerGas' in tx_params and 'MaxPriorityFeePerGas' not in tx_params:
            tx_params['MaxPriorityFeePerGas'] = (await self.max_priority_fee()).Wei
            tx_params['maxFeePerGas'] = tx_params['maxFeePerGas'] + tx_params['maxPriorityFeePerGas']

        if 'gas' not in tx_params or not int(tx_params['gas']):
            tx_params['gas'] = (await self.estimate_gas(tx_params=tx_params)).Wei

        return tx_params

    async def sign_transaction(self, tx_params: TxParams) -> SignedTransaction:
        """Подпись транзакции с client eth account"""
        return self.client.w3.eth.account.sign_transaction(
            transaction_dict=tx_params, private_key=self.client.account.key)

    async def sign_and_send(self, tx_params: TxParams):
        self.auto_add_params(tx_params=tx_params)
        signed_tx = self.transaction = await self.sign_transaction(tx_params=tx_params)
        tx_hash = self.client.w3.eth.send_raw_transaction(transaction=signed_tx)
        return Tx(tx_hash=tx_hash, params=tx_params)

    async def approved_amount(
            self, token: Contract, spender: Contract, owner: Address | None = None
    ) -> TokenAmount:
        """Проверка сколько токенов аппрувнуто той или иной свапалке"""
        contract_address, _ = await self.client.contracts.get_contract_attributes(contract=token)  # контакт токена
        contract = await self.client.contracts.default_token(contract_address)
        spender, abi = await self.client.contracts.get_contract_attributes(contract=spender)  # контракт свапалки
        if not owner:
            owner = self.client.account.address
        return TokenAmount(
            amount=await contract.functions.allowance(
                owner=owner,
                spender=spender
            ).call(),
            decimals=await contract.functions.decimals().call(), wei=True
        )

    async def wait_for_receipt(
            self, tx_hash: str | _Hash32, timeout: int | float = 120, poll_latence: float = 0.1
    ) -> dict[str, Any]:
        """Получение чека транзакции, проверка что она прошла успешно"""
        return dict(await self.client.w3.eth.wait_for_transaction_receipt(
            transaction_hash=tx_hash, timeout=timeout, poll_latency=poll_latence))

    async def approve(
        self, token: Contract, spender: Contract, amount: Amount | None = None,
        gas_price: GasPrice | None = None, gas_limit: GasLimit | None = None,
        nonce: int | None = None, check_gas_price: bool = False
    ) -> Tx:
        """Апрув токена для той или иной свапалки"""
        contract_addr, _ = await self.client.contracts.get_contract_attributes(contract=token)
        contract: Contract = await self.client.contracts.default_token(address=contract_addr)

        if not amount:
            amount = CommonValue.InfinityInt

        if isinstance(amount, (int, float)):
            amount = TokenAmount(amount=amount, decimals=contract.functions.decimals().call()).Wei
        else:
            amount = amount.Wei

        spender: Contract = Web3.to_checksum_address(value=spender)
        current_gas_price = await self.gas_price()
        if not gas_price:
            gas_price = await current_gas_price
        elif gas_price:
            if isinstance(gas_price, int):
                gas_price = TokenAmount(amount=gas_price, wei=True)

        if check_gas_price and current_gas_price.Wei > gas_price.Wei:
            raise GasTooHigh()

        if not nonce:
            nonce = await self.client.wallet.nonce()

        tx_params = {
            'chainId': self.client.network.chain_id,
            'nonce': nonce,
            'from': self.client.account.address,
            'to': contract.address,
            # TxArgs - просто args в кортеже, нужен только для удобства, чтоб аргументы могли быть именованные
            'data': contract.encodeABI('approve',
                                       args=TxArgs(spender=spender,
                                                   amount=amount).tuple())
        }
        if self.client.network.tx_type == 2:
            tx_params['maxPriorityFeePerGas'] = (await self.client.transactions.max_priority_fee()).Wei
            tx_params['maxFeePerGas'] = gas_price.Wei + tx_params['maxPriorityFeePerGas']
        else:
            tx_params['gasPrice'] = gas_price.Wei

        if not gas_limit:
            gas_limit = await self.estimate_gas(tx_params=tx_params)
        elif isinstance(gas_limit, int):
            gas_limit = TokenAmount(amount=gas_limit, wei=True)

        tx_params['gas'] = gas_limit.Wei
        return await self.sign_and_send(tx_params=tx_params)

    async def sign_message(self):
        pass

    @staticmethod
    async def decode_input_data(self):
        pass
