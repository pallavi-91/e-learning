from typing import Union, List, Optional
from .config import MONEY_FORMATS
from .exceptions import CurrencyDoesNotExist


class FormatCurrency:
    money_currency: Optional[str] = None
    money_formats = MONEY_FORMATS

    def __init__(self, money_currency: str):
        self.set_money_currency(money_currency)

    def set_money_currency(self, money_currency: str) -> None:
        self.money_currency = money_currency
        if money_currency not in self.money_formats:
            # raise CurrencyDoesNotExist
            self.money_currency = 'USD'

    def get_money_currency(self) -> str:
        return self.money_currency

    @classmethod
    def get_currency_formats(cls) -> list:
        return list(cls.money_formats.keys())

    def get_money_format(self, amount: Union[int, float, str]) -> str:
        """
        Usage:
        >>> currency = FormatCurrency('USD')
        >>> currency.get_money_format(13)
        >>> '$13'
        >>> currency.get_money_format(13.99)
        >>> '$13.99'
        >>> currency.get_money_format('13,2313,33')
        >>> '$13,2313,33'
        """
        return self.money_formats[
            self.get_money_currency()
        ]['money_format'].format(amount=amount)

    def get_money_with_currency_format(self, amount: Union[int, float, str]) -> str:
        """
        Usage:
        >>> currency = FormatCurrency('USD')
        >>> currency.get_money_with_currency_format(13)
        >>> '$13 USD'
        >>> currency.get_money_with_currency_format(13.99)
        >>> '$13.99 USD'
        >>> currency.get_money_with_currency_format('13,2313,33')
        >>> '$13,2313,33 USD'
        """
        return self.money_formats[
            self.get_money_currency()
        ]['money_with_currency_format'].format(amount=amount)

