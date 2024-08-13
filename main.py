from decimal import Decimal


class Token:
    def __init__(self, name: str, address: str, balance: int) -> None:
        name = name.upper()
        self.name = name
        self.address = address
        self.balance = balance

    def __str__(self) -> str:
        return f"Name: {self.name} | {self.address} | Balance: {self.balance}"


class Tokens:
    ETH = Token(name="ETH", address="0x0000000000000000", balance=100000)
    USDC = Token(name="USDC", address="0x0000000000000000", balance=100000)


print(Tokens.ETH)
