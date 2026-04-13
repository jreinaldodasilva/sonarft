# UTILITIES FUNCTIONS ******************************************************
from dataclasses import dataclass
import json
import os
import logging
import time


@dataclass
class Trade:
    position: str
    base: str
    quote: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    buy_trade_amount: float
    sell_trade_amount: float
    executed_amount: float
    buy_value: float
    sell_value: float
    buy_fee_rate: float
    sell_fee_rate: float
    buy_fee_base: float
    buy_fee_quote: float
    sell_fee_quote: float
    profit: float
    profit_percentage: float
    # Pre-computed indicators passed from price adjustment to avoid re-fetch at execution
    market_direction_buy: str = None
    market_direction_sell: str = None
    market_rsi_buy: float = None
    market_rsi_sell: float = None
    market_stoch_rsi_buy_k: float = None
    market_stoch_rsi_buy_d: float = None
    market_stoch_rsi_sell_k: float = None
    market_stoch_rsi_sell_d: float = None

class SonarftHelpers:
    """
    SonarFTHelpers class contains helper functions for the trading bot.
    """

    def __init__(self, is_simulation_mode: bool, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.is_simulation_mode = is_simulation_mode

    def save_botid(self, botid):
        """
        Save botid info to a json file.
        """

        pathname = botid + ".json"
        file_name = os.path.join('sonarftdata', 'bots', pathname)
        data = {"botid": botid}
        with open(file_name, 'w') as file:
            json.dump(data, file)

    def save_order_data(self, pathname, order_info):
        """
        Save order info to a json file.

        :param pathname: pathname of the file
        :param order_info: order info to save
        """

        file_name = os.path.join('sonarftdata', 'history', pathname)
        if os.path.exists(file_name):
            with open(file_name, 'r') as file:
                order_history = json.load(file)
        else:
            order_history = []

        order_history.append(order_info)

        with open(file_name, 'w') as file:
            json.dump(order_history, file, indent=4)

        self.logger.info(f"Order: Success")

    def save_order_history(self, botid, trade: Trade, trade_position):
        """ 
        Save trade search info to a json file
        """
        t = time.localtime()
        current_time = time.strftime("%m-%d-%Y %H:%M:%S", t)
        trade_info = {
            'timestamp': current_time,
            'position': trade_position,
            'base': trade.base,
            'quote': trade.quote,
            'buy_exchange': trade.buy_exchange,
            'sell_exchange': trade.sell_exchange,
            'buy_price': trade.buy_price,
            'sell_price': trade.sell_price,
            'buy_trade_amount': trade.buy_trade_amount,
            'sell_trade_amount': trade.sell_trade_amount,
            'executed_amount': trade.executed_amount, 
            'buy_value': trade.buy_value,
            'sell_value': trade.sell_value,
            'buy_fee_rate': trade.buy_fee_rate,
            'sell_fee_rate': trade.sell_fee_rate,
            'buy_fee_base': trade.buy_fee_base,
            'buy_fee_quote': trade.buy_fee_quote,
            'sell_fee_quote': trade.sell_fee_quote,
            'profit': trade.profit,
            'profit_percentage': trade.profit_percentage
        }
        
        pathname = str(botid) + "_orders.json"
        self.save_order_data(pathname, trade_info)
        
    def save_trade_data(self, pathname, trade_info):
        """
        Save trade info to a json file.

        :param pathname: pathname of the file
        :param trade_info: trade info to save
        """

        file_name = os.path.join('sonarftdata', 'history', pathname)
        if os.path.exists(file_name):
            with open(file_name, 'r') as file:
                trade_history = json.load(file)
        else:
            trade_history = []

        trade_history.append(trade_info)

        with open(file_name, 'w') as file:
            json.dump(trade_history, file, indent=4)

        self.logger.info(f"Trade: Success")

    def save_trade_history(self, botid, trade: Trade, buy_order_id, sell_order_id, trade_position, order_buy_success: bool, order_sell_success: bool, trade_success: bool) -> None:
        """
        Save execution trade info to a json file.
        """
        t = time.localtime()
        current_time = time.strftime("%m-%d-%Y %H:%M:%S", t)
        trade_info = {
            'timestamp': current_time,
            'position': trade_position,
            'buy_order_id': buy_order_id,
            'sell_order_id': sell_order_id,
            'base': trade.base,
            'quote': trade.quote,
            'buy_exchange': trade.buy_exchange,
            'sell_exchange': trade.sell_exchange,
            'buy_price': trade.buy_price,
            'sell_price': trade.sell_price,
            'buy_trade_amount': trade.buy_trade_amount,
            'sell_trade_amount': trade.sell_trade_amount,
            'executed_amount': trade.executed_amount,
            'buy_value': trade.buy_value,
            'sell_value': trade.sell_value,
            'buy_fee_rate': trade.buy_fee_rate,
            'sell_fee_rate': trade.sell_fee_rate,
            'buy_fee_base': trade.buy_fee_base,
            'buy_fee_quote': trade.buy_fee_quote,
            'sell_fee_quote': trade.sell_fee_quote,
            'profit': trade.profit,
            'profit_percentage': trade.profit_percentage,
            'order_buy_success': order_buy_success,
            'order_sell_success': order_sell_success,
            'trade_success': trade_success
        }
        
        pathname = str(botid) + "_trades.json"
        self.save_trade_data(pathname, trade_info)

    def save_error(self, error_info):
        """
        Save error info to a json file.

        :param error_info: error info to save
        """

        file_name = "errors_history.json"
        if os.path.exists(file_name):
            with open(file_name, 'r') as file:
                trade_errors = json.load(file)
        else:
            trade_errors = []

        trade_errors.append(error_info)

        with open(file_name, 'w') as file:
            json.dump(trade_errors, file, indent=4)
            self.logger.info(f"Errors info saved to {file_name}")

    def save_balance_data(self, balance_info):
        """
        Save balance info to a json file
        """
        file_name = "balance_history.json"
        if os.path.exists(file_name):
            with open(file_name, 'r') as file:
                balance_history = json.load(file)
        else:
            balance_history = []

        balance_history.append(balance_info)

        with open(file_name, 'w') as file:
            json.dump(balance_history, file, indent=4)

        self.logger.info(f"Balance info saved to {file_name}")

    def percentage_difference(self, value1, value2):
        """
        Calculate the percentage difference between two values.
        """
        if value1 == 0:
            return 0
        if value2 == 0:
            return 0
        if value1 == value2:
            return 0

        return abs((value1 - value2) / ((value1 + value2) / 2)) * 100
