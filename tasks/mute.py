from time import time

from web3.types import TxParams

from .base import Base
from eth_async.models import TokenAmount, TxArgs
from data.models import Contracts


class Mute(Base):
    async def swap_eth_to_usdc(self, amount: TokenAmount,
                               slippage: float = 0.1) -> str:
        to_token = Contracts.ZKSYNC_USDC

        to_token = await self.client.contracts.default_token(contract_address=to_token.address)
        print('to_token.address:', to_token)

        failed_text = f"Failed swap ETH to USDC via Mute"

        contract = await self.client.contracts.get(contract_address=Contracts.ZKSYNC_MUTE)

        eth_price = await self.get_token_price(token_symbol='ETH')
        amount_out_min = TokenAmount(
            amount=float(amount.Ether) * eth_price * (1 - slippage / 100),
            decimals=await self.client.transactions.get_decimals(contract=to_token)
        )

        tx_args = TxArgs(
            amountOutMin=amount_out_min.Wei,
            path=[Contracts.ZKSYNC_WETH.address, to_token.address],
            to=self.client.account.address,
            deadline=int(time() + 20 * 60),
            stable=[False, False]
        )


        tx_params = TxParams(
            to=contract.address,
            data=contract.encodeABI('swapExactETHForTokensSupportingFeeOnTransferTokens', args=tx_args.tuple()),
            value=amount.Wei
        )


        gas = await self.client.transactions.estimate_gas(tx_params=tx_params)

        if gas:
            return f'{amount.Ether} ETH Successfully swapped to USDC via Mute | Gas: {gas.Wei}'

        # tx = await self.client.transactions.sign_and_send(tx_params=tx_params)  # auto_add_params внутри
        # receipt = await tx.wait_for_receipt(client=self.client, timeout=300)
        # if receipt:
        #     return f'{amount.Ether} ETH Successfully swapped to {to_token_name} via Mute: {tx.hash.hex()}'

        return f'{failed_text}!'
