
from eth_async.utils.utils import read_json
from eth_async.models import RawContract, DefaultABIs
from eth_async.classes import Singleton

from data.config import ABIS_DIR


class Contracts(Singleton):
    ETHEREUM_SHIBASWAP = RawContract(
        title="ShibaSwap",
        address="0x03f7724180AA6b939894B5Ca4314783B0b36b329",
        abi=read_json(path=(ABIS_DIR, "shiba.json"))
    )

    ETHEREUM_USDC = RawContract(
        title="USDC",
        address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        abi=DefaultABIs.Token
    )
    ETHEREUM_ETH = RawContract(
        title="ETH",
        address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        abi=DefaultABIs.Token
    )
