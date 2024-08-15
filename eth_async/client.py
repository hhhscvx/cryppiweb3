from random import randint

from web3 import Web3
from web3.eth.async_eth import AsyncEth
from eth_account.signers.local import LocalAccount
from fake_useragent import UserAgent
import requests

from .exceptions import InvalidProxy
from .models import Network, Networks
from .wallet import Wallet
from .contracts import Contracts
from .transactions import Transactions


class Client:
    def __init__(self,
                 private_key: str | None = None,
                 network: Network = Networks.Arbitrum,
                 proxy: str | None = None,
                 check_proxy: bool = True) -> None:
        self.network = network
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'user-agent': UserAgent().chrome
        }
        self.proxy = proxy
        if self.proxy:
            if 'http://' not in self.proxy:
                self.proxy = f"http://{self.proxy}"
            if check_proxy:
                ipaddr = requests.get('https://eth0.me/',
                                      proxies={'http': self.proxy, 'https': self.proxy}, timeout=10).text.strip()
                if ipaddr not in proxy:
                    raise InvalidProxy(f"Your Proxy didn`t work! Your IP: {ipaddr}")
        self.w3 = Web3(
            provider=Web3.AsyncHTTPProvider(
                endpoint_uri=self.network.rpc,
                request_kwargs={'proxy': self.proxy, 'headers': self.headers}
            ),
            modules={'eth': (AsyncEth,)},
            middlewares=[]
        )
        self.private_key = private_key
        if self.private_key:
            self.account: LocalAccount = self.w3.eth.account.from_key(private_key=self.private_key)
        elif private_key is None:
            self.account: LocalAccount = self.w3.eth.account.create(extra_entropy=str(randint(1, 999_999_999)))
        else:
            self.account = None

        self.wallet = Wallet(self)
        self.contracts = Contracts(self)
        self.transactions = Transactions(self)
