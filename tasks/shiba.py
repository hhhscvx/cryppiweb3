from time import time

from web3.types import TxParams
from eth_async.models import TokenAmount
from eth_async.models import TxArgs, TokenAmount

from .base import Base
from data.models import Contracts


class Shiba(Base):
    async def swap_eth_to_usdc(self, amount: TokenAmount, slippage: float = 1) -> str:
        failed_text = 'Failed swap ETH to USDC via Shiba!'

        contract = await self.client.contracts.get(contract_address=Contracts.ETHEREUM_SHIBASWAP)
        from_token = Contracts.ETHEREUM_ETH
        to_token = Contracts.ETHEREUM_USDC

        eth_price = await self.get_token_price(token_symbol='ETH')
        min_to_amount = TokenAmount(
            amount=eth_price * float(amount.Ether) * (1 - slippage / 100),
            decimals=await self.get_decimals(contract_address=to_token.address)
        )
        deadline = int(time()) + 600  # 10 минут с текущего момента

        args = TxArgs(
            amountOutMin=min_to_amount.Wei,
            path=[from_token.address, to_token.address],
            to=self.client.account.address,
            deadline=deadline,
        )

        tx_params = TxParams(
            to=contract.address,
            data=contract.encodeABI('swapExactETHForTokens', args=args.tuple()),
            value=amount.Wei
        )

        gas = await self.client.transactions.estimate_gas(tx_params=tx_params)
        if gas:
            return f'{amount.Ether} ETH was swaped to {min_to_amount.Ether} USDC via Shiba: {gas.Wei}'

        return f'{failed_text}'

    async def swap_usdc_to_eth(self, amount: TokenAmount | None = None, slippage: float = 1) -> str:
        ...
