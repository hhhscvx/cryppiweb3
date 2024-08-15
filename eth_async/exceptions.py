
class WrongChainID(Exception):
    pass


class WrongCoinSymbol(Exception):
    pass


class InvalidProxy(Exception):
    pass


class HTTPException(Exception):
    def __init__(self, response, status_code) -> None:
        self.response = response
        self.status_code = status_code


class TransactionException(Exception):
    pass


class GasTooHigh(Exception):
    pass
