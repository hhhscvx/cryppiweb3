from __future__ import annotations
from typing import TYPE_CHECKING, Any
from hexbytes import HexBytes

from web3 import AsyncWeb3, Web3
from web3.contract.async_contract import AsyncContract
from web3.types import TxParams, _Hash32, TxData, TxReceipt
from web3.middleware.geth_poa import geth_poa_middleware
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

    async def wait_for_receipt(self, client: Client, timeout: int | float = 120,
                               poll_latency: float = 0.1) -> dict[str, Any]:

        self.receipt = client.transactions.wait_for_receipt(
            w3=client.w3,
            tx_hash=self.hash,
            timeout=timeout,
            poll_latency=poll_latency
        )
        return self.receipt

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

    async def max_priority_fee(self, block: dict | None = None) -> TokenAmount:
        w3 = Web3(Web3.HTTPProvider(self.client.network.rpc))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        if not block:
            block = w3.eth.get_block('latest')

        block_number = block['number']
        latest_block_transactions_count = w3.eth.get_block_transaction_count(block_number)
        max_priority_fee_per_gas_lst = []
        for i in range(latest_block_transactions_count):  # пробегаемся по всем транзакциям в блоке
            try:
                transaction = w3.eth.get_transaction_by_block(block_number, i)
                if transaction.get('maxPriorityFeePerGas'):
                    max_priority_fee_per_gas_lst.append(transaction['maxPriorityFeePerGas'])
            except:
                continue

        if not max_priority_fee_per_gas_lst:
            max_priority_fee_per_gas = 0
        else:
            max_priority_fee_per_gas_lst.sort()
            max_priority_fee_per_gas = max_priority_fee_per_gas_lst[len(max_priority_fee_per_gas_lst) // 2]
        return TokenAmount(amount=max_priority_fee_per_gas, wei=True)

    async def max_priority_fee_(self) -> TokenAmount:
        max_priority_fee = await self.client.w3.eth.max_priority_fee
        return TokenAmount(amount=max_priority_fee, wei=True)

    async def estimate_gas(self, tx_params: TxParams) -> TokenAmount:
        """Сколько газа будет"""
        gas = await self.client.w3.eth.estimate_gas(transaction=tx_params)
        return TokenAmount(amount=gas, wei=True)

    async def auto_add_params(self, tx_params: TxParams) -> TxParams:
        """Дополнение необходимых параметров для транзакции"""
        if 'chainId' not in tx_params:
            tx_params['chainId'] = await self.client.w3.eth.chain_id

        if not tx_params.get('nonce'):
            tx_params['nonce'] = await self.client.wallet.nonce()

        if 'gasPrice' not in tx_params and 'maxFeePerGas' not in tx_params:
            gas_price = (await self.gas_price()).Wei
            if self.client.network.tx_type == 2:
                tx_params['maxFeePerGas'] = gas_price
            else:
                tx_params['gasPrice'] = gas_price

        if 'gasPrice' in tx_params and not int(tx_params['gas']):
            tx_params['gas'] = (await self.gas_price()).Wei

        if 'maxFeePerGas' in tx_params and 'maxPriorityFeePerGas' not in tx_params:
            tx_params['maxPriorityFeePerGas'] = (await self.max_priority_fee()).Wei
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
            decimals=await self.client.transactions.get_decimals(contract=contract), wei=True
        )

    @staticmethod
    async def wait_for_receipt(w3: Web3 | AsyncWeb3, tx_hash: str | _Hash32,
                               timeout: int | float = 120,
                               poll_latency: float = 0.1) -> dict[str, Any]:
        """Получение чека транзакции, проверка что она прошла успешно"""
        return dict(await w3.eth.wait_for_transaction_receipt(
            transaction_hash=tx_hash, timeout=timeout, poll_latency=poll_latency))

    async def approve(
            self, token: Contract, spender: Contract, amount: Amount | None = None,
            gas_limit: GasLimit | None = None, nonce: int | None = None) -> Tx:
        """Апрув токена для той или иной свапалки"""

        spender: Contract = Web3.to_checksum_address(value=spender)
        contract_addr, _ = await self.client.contracts.get_contract_attributes(contract=token)
        contract: Contract = await self.client.contracts.default_token(address=contract_addr)

        if not amount:
            amount = CommonValue.InfinityInt

        if isinstance(amount, (int, float)):
            amount = TokenAmount(amount=amount, decimals=await self.client.transactions.get_decimals(contract=contract)).Wei
        else:
            amount = amount.Wei

        tx_args = TxArgs(spender=spender,
                         amount=amount)

        tx_params = {
            'nonce': nonce,
            'to': contract.address,
            'data': contract.encodeABI('approve',
                                       args=tx_args.tuple())
        }

        if gas_limit:
            if isinstance(gas_limit, int):
                gas_limit = TokenAmount(amount=gas_limit, wei=True)
            tx_params['gas'] = gas_limit

        return await self.sign_and_send(tx_params=tx_params)

    async def get_decimals(self, contract: Contract) -> int:
        contract_address, _ = await self.client.contracts.get_contract_attributes(contract=contract)  # контакт токена
        contract: AsyncContract = await self.client.contracts.default_token(contract_address=contract_address)
        return await contract.functions.decimals().call()

    async def sign_message(self):
        pass

    @staticmethod
    async def decode_input_data(self):
        pass
