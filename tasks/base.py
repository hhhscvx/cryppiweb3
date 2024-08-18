import asyncio
import aiohttp

from web3.contract.async_contract import AsyncContract

from eth_async.client import Client
from eth_async.models import TokenAmount


class Base:
    def __init__(self, client: Client) -> None:
        self.client = client

    @staticmethod
    async def get_token_price(token_symbol: str = 'ETH', second_token: str = "USDT") -> float | None:
        token_symbol, second_token = token_symbol.upper(), second_token.upper()
        url = f'https://api.binance.com/api/v3/depth?limit=1&symbol={token_symbol}{second_token}'
        for _ in range(5):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as r:
                        if r.status != 200:
                            return
                        result_dict = await r.json()
                        if 'asks' not in result_dict:
                            return
                        return float(result_dict['asks'][0][0])
            except:
                await asyncio.sleep(5)
        raise ValueError(f"Can`t get {token_symbol + second_token} price | Binance")

    async def approve_interface(self, token_address, spender, amount: TokenAmount | None = None) -> bool:
        """Аппрувнуто ли переданное количество"""
        balance = await self.client.wallet.balance(token_address)
        if balance.Wei <= 0:
            return False

        if not amount or amount.Wei < balance.Wei:
            amount = balance

        approved = await self.client.transactions.approved_amount(
            token=token_address,
            spender=spender,
            owner=self.client.account.address
        )

        if amount.Wei <= approved.Wei:
            """Уже аппрувнуто столько"""
            return True

        tx = await self.client.transactions.approve(
            token=token_address,
            spender=spender,
            amount=amount
        )
        receipt = await tx.wait_for_receipt(client=self.client, timeout=300)
        return True if receipt else False

    async def get_token_info(self, contract_address):
        contract: AsyncContract = await self.client.contracts.default_token(contract_address)
        print('name', await contract.functions.name().call())
        print('symbol', await contract.functions.symbol().call())
        print('decimals', await contract.functions.decimals().call())
