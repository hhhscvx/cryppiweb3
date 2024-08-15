from web3 import types
from web3.contract.async_contract import AsyncContract

from .models import TokenAmount, RawContract


Contract = str | types.Address | types.ChecksumAddress | types.ENS | AsyncContract | RawContract
Address = str | types.Address | types.ChecksumAddress | types.ENS
Amount = float | int | TokenAmount
GasPrice = int | TokenAmount
GasLimit = int | TokenAmount
