from decimal import getcontext

from sonarft_api_manager import SonarftApiManager

# used to force maximum precision 8
getcontext().prec = 8

class SonarftMath:
    """
    SonarFTMath class
    """

    def __init__(self, api_manager: SonarftApiManager):
        self.api_manager = api_manager
   
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
        """
        Calculate the profit and percentage values for binance
        """

        buy_exchange, _, _, _, _ = buy_price_list
        sell_exchange, _, _, _, _ = sell_price_list

        buy_fee_rate = self.api_manager.get_buy_fee(buy_exchange)
        sell_fee_rate = self.api_manager.get_sell_fee(sell_exchange)
        if buy_fee_rate is None or sell_fee_rate is None:
            return 0, 0, 0, None
        
        buy_rules = self.EXCHANGE_RULES[buy_exchange]
        sell_rules = self.EXCHANGE_RULES[sell_exchange]

        # Buying 
        buy_price = round(buy_price, buy_rules['prices_precision'])
        target_amount_buy = round(target_amount, buy_rules['buy_amount_precision'])
        buy_fee_quote = round(buy_price * target_amount_buy * buy_fee_rate, buy_rules['fee_precision'])
        value_buying = round(buy_price * target_amount_buy, buy_rules['cost_precision'])
        value_buying_with_fee = round(value_buying + buy_fee_quote, buy_rules['cost_precision'])
        
        # 
        executed_amount = target_amount_buy 

        # Selling
        sell_price = round(sell_price, sell_rules['prices_precision'])
        target_amount_sell = executed_amount
        sell_fee_quote = round(sell_price * target_amount_sell * sell_fee_rate, sell_rules['fee_precision'])
        value_selling = round(sell_price * target_amount_sell, sell_rules['cost_precision'])
        value_selling_with_fee = round(value_selling - sell_fee_quote, sell_rules['cost_precision'])

        profit = round(value_selling_with_fee - value_buying_with_fee, sell_rules['fee_precision'])
        profit_percentage = round(((value_selling_with_fee - value_buying_with_fee) / value_buying_with_fee), sell_rules['fee_precision'])

        trade_data = {
            'position': "",
            'base': base,
            'quote': quote,
            'buy_exchange': buy_exchange,
            'sell_exchange': sell_exchange,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'buy_trade_amount': target_amount_buy,
            'sell_trade_amount': target_amount_sell,
            'executed_amount': executed_amount,
            'buy_value': value_buying,          
            'sell_value': value_selling,
            'buy_fee_rate': buy_fee_rate,
            'sell_fee_rate': sell_fee_rate,
            'buy_fee_base': 0,
            'buy_fee_quote': buy_fee_quote,
            'sell_fee_quote': sell_fee_quote,
            'profit': profit,
            'profit_percentage': profit_percentage
        }

        return profit, profit_percentage, trade_data
