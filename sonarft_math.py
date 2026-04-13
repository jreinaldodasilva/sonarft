"""
SonarFT Math Module
Trade profit, fee calculation, and exchange precision rules.
"""
from decimal import Decimal, ROUND_HALF_UP, getcontext
import logging

from sonarft_api_manager import SonarftApiManager

getcontext().prec = 28

class SonarftMath:
    """Trade profit, fee calculation, and exchange precision rules."""

    def __init__(self, api_manager: SonarftApiManager, logger=None):
        self.api_manager = api_manager
        self.logger = logger or logging.getLogger(__name__)
   
        self.EXCHANGE_RULES = {
            'okx': {
                'prices_precision': 1,
                'cost_precision': 8,
                'buy_amount_precision': 8,
                'sell_amount_precision': 8,
                'sell_amount_decimal_precision': '0.000000',
                'fee_precision': 8,
            },
            'bitfinex': {
                'prices_precision': 3,
                'cost_precision': 8,
                'buy_amount_precision': 8,
                'sell_amount_precision': 8,
                'sell_amount_decimal_precision': '0.00000000',
                'fee_precision': 8,
            },
            'binance': {
                'prices_precision': 2,
                'cost_precision': 7,
                'buy_amount_precision': 5,
                'sell_amount_precision': 5,
                'sell_amount_decimal_precision': '0.00000',
                'fee_precision': 8,
            }
        }


    def calculate_trade(self, buy_price, sell_price, buy_price_list, sell_price_list, target_amount, base, quote):
        """Calculate profit and fees using Decimal arithmetic for financial precision."""
        buy_exchange, _, _, _, _ = buy_price_list
        sell_exchange, _, _, _, _ = sell_price_list

        buy_fee_rate = self.api_manager.get_buy_fee(buy_exchange)
        sell_fee_rate = self.api_manager.get_sell_fee(sell_exchange)
        if buy_fee_rate is None or sell_fee_rate is None:
            return 0, 0, None

        if buy_exchange not in self.EXCHANGE_RULES or sell_exchange not in self.EXCHANGE_RULES:
            self.logger.warning(f"Exchange not in EXCHANGE_RULES: {buy_exchange}, {sell_exchange}")
            return 0, 0, None

        buy_rules = (
            self.api_manager.get_symbol_precision(buy_exchange, base, quote)
            or self.EXCHANGE_RULES.get(buy_exchange)
        )
        sell_rules = (
            self.api_manager.get_symbol_precision(sell_exchange, base, quote)
            or self.EXCHANGE_RULES.get(sell_exchange)
        )
        if buy_rules is None or sell_rules is None:
            self.logger.warning(f"No precision rules for {buy_exchange}/{sell_exchange} {base}/{quote}")
            return 0, 0, None

        def d(value, precision):
            """Convert to Decimal and quantize to given decimal places."""
            fmt = Decimal(10) ** -precision
            return Decimal(str(value)).quantize(fmt, rounding=ROUND_HALF_UP)

        # Buying
        buy_price_d = d(buy_price, buy_rules['prices_precision'])
        target_amount_buy_d = d(target_amount, buy_rules['buy_amount_precision'])
        buy_fee_d = d(buy_price_d * target_amount_buy_d * Decimal(str(buy_fee_rate)), buy_rules['fee_precision'])
        value_buying_d = d(buy_price_d * target_amount_buy_d, buy_rules['cost_precision'])
        value_buying_with_fee_d = d(value_buying_d + buy_fee_d, buy_rules['cost_precision'])

        if value_buying_with_fee_d == 0:
            return 0, 0, None

        # Selling
        sell_price_d = d(sell_price, sell_rules['prices_precision'])
        target_amount_sell_d = target_amount_buy_d
        sell_fee_d = d(sell_price_d * target_amount_sell_d * Decimal(str(sell_fee_rate)), sell_rules['fee_precision'])
        value_selling_d = d(sell_price_d * target_amount_sell_d, sell_rules['cost_precision'])
        value_selling_with_fee_d = d(value_selling_d - sell_fee_d, sell_rules['cost_precision'])

        profit_d = d(value_selling_with_fee_d - value_buying_with_fee_d, sell_rules['fee_precision'])
        profit_pct_d = d(
            (value_selling_with_fee_d - value_buying_with_fee_d) / value_buying_with_fee_d,
            sell_rules['fee_precision']
        )

        trade_data = {
            'position': "",
            'base': base,
            'quote': quote,
            'buy_exchange': buy_exchange,
            'sell_exchange': sell_exchange,
            'buy_price': float(buy_price_d),
            'sell_price': float(sell_price_d),
            'buy_trade_amount': float(target_amount_buy_d),
            'sell_trade_amount': float(target_amount_sell_d),
            'executed_amount': float(target_amount_buy_d),
            'buy_value': float(value_buying_d),
            'sell_value': float(value_selling_d),
            'buy_fee_rate': buy_fee_rate,
            'sell_fee_rate': sell_fee_rate,
            'buy_fee_base': 0,
            'buy_fee_quote': float(buy_fee_d),
            'sell_fee_quote': float(sell_fee_d),
            'profit': float(profit_d),
            'profit_percentage': float(profit_pct_d),
        }

        return float(profit_d), float(profit_pct_d), trade_data
