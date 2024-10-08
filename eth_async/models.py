from decimal import Decimal
from dataclasses import dataclass

from web3 import Web3
from eth_typing import ChecksumAddress
import requests

from . import exceptions


class TokenAmount:
    Wei: int
    Ether: Decimal
    decimals: int

    def __init__(self, amount: str | int | float | Decimal, decimals: int = 18, wei: bool = False) -> None:
        match wei:
            case True:
                self.Wei: int = int(amount)
                self.Ether: Decimal = Decimal(str(amount)) / 10 ** decimals
            case False:
                self.Wei: int = int(Decimal(str(amount)) * 10 ** decimals)
                self.Ether: Decimal = Decimal(str(amount))

        self.decimals = decimals

    def __str__(self) -> str:
        return f"{self.Ether}"


@dataclass
class DefaultABIs:
    Token = [
        {
            'constant': True,
            'inputs': [],
            'name': 'name',
            'outputs': [{'name': '', 'type': 'string'}],
            'payable': False,
            'stateMutability': 'view',
            'type': 'function'
        },
        {
            'constant': True,
            'inputs': [],
            'name': 'symbol',
            'outputs': [{'name': '', 'type': 'string'}],
            'payable': False,
            'stateMutability': 'view',
            'type': 'function'
        },
        {
            'constant': True,
            'inputs': [],
            'name': 'totalSupply',
            'outputs': [{'name': '', 'type': 'uint256'}],
            'payable': False,
            'stateMutability': 'view',
            'type': 'function'
        },
        {
            'constant': True,
            'inputs': [],
            'name': 'decimals',
            'outputs': [{'name': '', 'type': 'uint256'}],
            'payable': False,
            'stateMutability': 'view',
            'type': 'function'
        },
        {
            'constant': True,
            'inputs': [{'name': 'account', 'type': 'address'}],
            'name': 'balanceOf',
            'outputs': [{'name': '', 'type': 'uint256'}],
            'payable': False,
            'stateMutability': 'view',
            'type': 'function'
        },
        {
            'constant': True,
            'inputs': [{'name': 'owner', 'type': 'address'}, {'name': 'spender', 'type': 'address'}],
            'name': 'allowance',
            'outputs': [{'name': 'remaining', 'type': 'uint256'}],
            'payable': False,
            'stateMutability': 'view',
            'type': 'function'
        },
        {
            'constant': False,
            'inputs': [{'name': 'spender', 'type': 'address'}, {'name': 'value', 'type': 'uint256'}],
            'name': 'approve',
            'outputs': [],
            'payable': False,
            'stateMutability': 'nonpayable',
            'type': 'function'
        },
        {
            'constant': False,
            'inputs': [{'name': 'to', 'type': 'address'}, {'name': 'value', 'type': 'uint256'}],
            'name': 'transfer',
            'outputs': [], 'payable': False,
            'stateMutability': 'nonpayable',
            'type': 'function'
        }]


class Network:
    def __init__(self,
                 name: str,
                 rpc: str,
                 chain_id: int | None = None,
                 tx_type: int = 0,
                 coin_symbol: str | None = None,
                 explorer: str | None = None
                 ) -> None:
        self.name = name.lower()
        self.rpc = rpc
        self.chain_id = chain_id
        self.tx_type = tx_type
        self.coin_symbol = coin_symbol  # ex. ETH
        self.explorer = explorer

        if not self.chain_id:
            try:
                self.chain_id = Web3(Web3.HTTPProvider(endpoint_uri=self.rpc)).eth.chain_id
            except Exception as err:
                raise exceptions.WrongChainID(f"ERROR when getting chain id: {err}")

        if not self.coin_symbol:
            try:
                resp = requests.get("https://chainid.network/chains.json").json()
                for network in resp:
                    if network["chainId"] == self.chain_id:
                        self.coin_symbol = network["nativeCurrency"]["symbol"]
                        break
            except Exception as err:
                raise exceptions.WrongCoinSymbol(f"ERROR when getting coin symbol: {err}")
        if self.coin_symbol:
            self.coin_symbol = self.coin_symbol.upper()


class Networks:
    # Mainnets
    Ethereum = Network(
        name='ethereum',
        rpc='https://rpc.ankr.com/eth/',
        chain_id=1,
        tx_type=2,
        coin_symbol='ETH',
        explorer='https://etherscan.io/',
    )

    Arbitrum = Network(
        name='arbitrum',
        rpc='https://rpc.ankr.com/arbitrum/',
        chain_id=42161,
        tx_type=2,
        coin_symbol='ETH',
        explorer='https://arbiscan.io/',
    )

    ArbitrumNova = Network(
        name='arbitrum_nova',
        rpc='https://nova.arbitrum.io/rpc/',
        chain_id=42170,
        tx_type=2,
        coin_symbol='ETH',
        explorer='https://nova.arbiscan.io/',
    )

    Optimism = Network(
        name='optimism',
        rpc='https://rpc.ankr.com/optimism/',
        chain_id=10,
        tx_type=2,
        coin_symbol='ETH',
        explorer='https://optimistic.etherscan.io/',
    )

    BSC = Network(
        name='bsc',
        rpc='https://rpc.ankr.com/bsc/',
        chain_id=56,
        tx_type=0,
        coin_symbol='BNB',
        explorer='https://bscscan.com/',
    )

    Polygon = Network(
        name='polygon',
        rpc='https://rpc.ankr.com/polygon/',
        chain_id=137,
        tx_type=2,
        coin_symbol='MATIC',
        explorer='https://polygonscan.com/',
    )

    ZkSync = Network(
        name='zksync',
        rpc="https://mainnet.era.zksync.io",
        chain_id=324,
        tx_type=2,
        coin_symbol='ETH',
        explorer="https://explorer.zksync.io",
    )

    Avalanche = Network(
        name='avalanche',
        rpc='https://rpc.ankr.com/avalanche/',
        chain_id=43114,
        tx_type=2,
        coin_symbol='AVAX',
        explorer='https://snowtrace.io/',
    )

    Moonbeam = Network(
        name='moonbeam',
        rpc='https://rpc.api.moonbeam.network/',
        chain_id=1284,
        tx_type=2,
        coin_symbol='GLMR',
        explorer='https://moonscan.io/',
    )

    Fantom = Network(
        name='fantom',
        rpc='https://rpc.ftm.tools',
        chain_id=251,
        tx_type=2,
        coin_symbol="FTM"
    )

    Celo = Network(
        name='celo',
        rpc='https://forno.celo.org',
        chain_id=42220,
        tx_type=2,
        coin_symbol="FTCELOM"
    )

    Gnosis = Network(
        name='gnosis',
        rpc='https://rpc.gnosischain.com',
        chain_id=100,
        tx_type=2,
        coin_symbol="XDAI"
    )

    HECO = Network(
        name='HECO',
        rpc='https://http-mainnet.hecochain.com',
        chain_id=128,
        tx_type=2,
        coin_symbol="HT"
    )

    # Testnets
    Goerli = Network(
        name='goerli',
        rpc='https://rpc.ankr.com/eth_goerli/',
        chain_id=5,
        tx_type=2,
        coin_symbol='ETH',
        explorer='https://goerli.etherscan.io/',
    )

    Sepolia = Network(
        name='sepolia',
        rpc="https://rpc.sepolia.org",
        chain_id=11155111,
        tx_type=2,
        coin_symbol="ETH"
    )


class RawContract:
    title: str
    address: ChecksumAddress
    abi: list[dict[str]]

    def __init__(self, title: str, address: ChecksumAddress, abi: list[dict[str]] | str) -> None:
        self.title = title
        self.address = address
        self.abi = abi


@dataclass
class CommonValue:
    Null: str = '0x0000000000000000000000000000000000000000000000000000000000000000'
    InfinityStr: str = '0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
    InfinityInt: int = int('0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff', 16)


class TxArgs:
    def __init__(self, **kwargs) -> None:
        """
        Args:
            **kwargs: named arguments of a contract transaction
        """
        self.__dict__.update(kwargs)

    def list(self) -> list:
        """Get list of transaction arguments"""
        return list(self.__dict__.values())

    def tuple(self) -> tuple:
        """Get tuple of transaction arguments"""
        return tuple(self.__dict__.values())
