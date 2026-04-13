# external libraries
from decimal import getcontext
import random
from typing import Tuple
import time
import logging
import asyncio

# sonarft classes
from sonarft_api_manager import SonarftApiManager
from sonarft_helpers import SonarftHelpers, Trade
from sonarft_indicators import SonarftIndicators

# used to force maximum precision 8
getcontext().prec = 8

class SonarftExecution:
    """
    SonarftExecution class is responsible for executing the trades found by the SonarftTrades class.
    """

    def __init__(self,
                 api_manager: SonarftApiManager,
                 sonarft_helpers: SonarftHelpers,
                 sonarft_indicators: SonarftIndicators,
                 is_simulation_mode: bool, logger=None):
        self.logger = logger or logging.getLogger(__name__)

        self.api_manager = api_manager
        self.sonarft_helpers = sonarft_helpers
        self.sonarft_indicators = sonarft_indicators
        self.is_simulation_mode = is_simulation_mode

    # ### Entry Point for the trade execution ********************************
    async def execute_trade(self, botid, trade: dict) -> Tuple[bool, bool, bool]:
        """
        Execute the given trade.
        """
        try:
            # convert trade dict to Trade object
            trade_obj = Trade(**trade)

            buy_order_success, sell_order_sucess, trade_sucess = await self._execute_single_trade(botid, trade_obj)
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")

        return trade_sucess

    async def _execute_single_trade(self, botid, trade: Trade) -> Tuple[bool, bool, bool]:
        """
        Execute the given found trade from the SonarftTrades class.
        """
        # Extract trade data
        base = trade.base
        quote = trade.quote
        buy_exchange_id = trade.buy_exchange
        sell_exchange_id = trade.sell_exchange
        buy_price = trade.buy_price
        sell_price = trade.sell_price
        buy_trade_amount = trade.buy_trade_amount
        sell_trade_amount = trade.sell_trade_amount

        buy_order_id = None
        sell_order_id = None
        trade_position = None
        buy_order_sucess = False
        sell_order_sucess = False
        trade_success = False

        try:
            period = 14
            rsi_period = 14 
            stoch_period = 14 
            k_period = 3 
            d_period = 3 
            market_direction_buy = await self.sonarft_indicators.get_market_direction(
                buy_exchange_id, base, quote, 'sma', period)
            market_direction_sell = await self.sonarft_indicators.get_market_direction(
                sell_exchange_id, base, quote, 'sma', period)
            
            market_rsi_buy = await self.sonarft_indicators.get_rsi(
                buy_exchange_id, base, quote,  rsi_period)
            market_rsi_sell = await self.sonarft_indicators.get_rsi(
                sell_exchange_id, base, quote, rsi_period)
            
            market_stoch_rsi_buy_k, market_stoch_rsi_buy_d = await self.sonarft_indicators.get_stoch_rsi(
            buy_exchange_id, base, quote, rsi_period, stoch_period, k_period, d_period)

            market_stoch_rsi_sell_k, market_stoch_rsi_sell_d = await self.sonarft_indicators.get_stoch_rsi(
            sell_exchange_id, base, quote, rsi_period, stoch_period, k_period, d_period)


            #Long or Reverse to Short
            if market_direction_buy == 'bull' and market_direction_sell == 'bull':
                if market_rsi_buy >= 70 and market_rsi_sell >= 70 and market_stoch_rsi_buy_k > market_stoch_rsi_buy_d and market_stoch_rsi_sell_k > market_stoch_rsi_sell_d:
                    # Execute short trade
                    trade_position = 'SHORT'
                    self.sonarft_helpers.save_order_history(botid, trade, trade_position)
                    result_buy_order, result_sell_order = await self.execute_short_trade(buy_exchange_id, sell_exchange_id, base, quote, buy_trade_amount, sell_trade_amount, buy_price, sell_price)
                    buy_order_id, sell_order_id, buy_order_sucess, sell_order_sucess, trade_success = await self.handle_trade_results(trade, result_buy_order, result_sell_order)
                else:
                    # Execute long trade
                    trade_position = 'LONG'
                    self.sonarft_helpers.save_order_history(botid, trade, trade_position)
                    result_buy_order, result_sell_order = await self.execute_long_trade(buy_exchange_id, sell_exchange_id, base, quote, buy_trade_amount, sell_trade_amount, buy_price, sell_price)
                    buy_order_id, sell_order_id, buy_order_sucess, sell_order_sucess, trade_success = await self.handle_trade_results(trade, result_buy_order, result_sell_order)

            #Short or Reverse to Long
            elif market_direction_buy == 'bear' and market_direction_sell == 'bear':
                if market_rsi_buy <= 30 and market_rsi_sell <= 30 and market_stoch_rsi_buy_k < market_stoch_rsi_buy_d and market_stoch_rsi_sell_k < market_stoch_rsi_sell_d:
                    # Execute long trade
                    trade_position = 'LONG'
                    self.sonarft_helpers.save_order_history(botid, trade, trade_position)
                    result_buy_order, result_sell_order = await self.execute_long_trade(buy_exchange_id, sell_exchange_id, base, quote, buy_trade_amount, sell_trade_amount, buy_price, sell_price)
                    buy_order_id, sell_order_id, buy_order_sucess, sell_order_sucess, trade_success = await self.handle_trade_results(trade, result_buy_order, result_sell_order)
                    
                else:
                    # Execute short trade
                    trade_position = 'SHORT'
                    self.sonarft_helpers.save_order_history(botid, trade, trade_position)
                    result_buy_order, result_sell_order = await self.execute_short_trade(buy_exchange_id, sell_exchange_id, base, quote, buy_trade_amount, sell_trade_amount, buy_price, sell_price)
                    buy_order_id, sell_order_id, buy_order_sucess, sell_order_sucess, trade_success = await self.handle_trade_results(trade, result_buy_order, result_sell_order)
                    

            if trade_success:
                # Save trade history
                self.sonarft_helpers.save_trade_history(botid, trade, buy_order_id, sell_order_id, trade_position, buy_order_sucess, sell_order_sucess, trade_success)

            return buy_order_sucess, sell_order_sucess, trade_success
        except Exception as e:
            self.logger.error(str(e))
            return False, False, False

    # Long
    async def execute_long_trade(self, buy_exchange_id, sell_exchange_id, base, quote, buy_trade_amount, sell_trade_amount, buy_price, sell_price):
        result_buy_order = None
        result_sell_order = None
        buy_balance_status = await self.check_balance(buy_exchange_id, base, quote, 'buy', buy_trade_amount, buy_price)
        if buy_balance_status:
            result_buy_order = await self.create_order(buy_exchange_id, base, quote, buy_price, buy_trade_amount, 'buy', True)
            buy_order_id, buy_executed_amount, buy_remaining_amount = result_buy_order

            if buy_executed_amount == buy_trade_amount:
                sell_balance_status = await self.check_balance(sell_exchange_id, base, quote, 'sell', sell_trade_amount, sell_price)
                if sell_balance_status:
                    result_sell_order = await self.create_order(sell_exchange_id, base, quote, sell_price, sell_trade_amount, 'sell', True)
            
        return result_buy_order, result_sell_order
    
    async def execute_short_trade(self, buy_exchange_id, sell_exchange_id, base, quote, buy_trade_amount, sell_trade_amount, buy_price, sell_price):
        result_buy_order = None
        result_sell_order = None
        sell_balance_status = await self.check_balance(sell_exchange_id, base, quote, 'sell', sell_trade_amount, sell_price)
        if sell_balance_status:
            result_sell_order = await self.create_order(sell_exchange_id, base, quote, sell_price, sell_trade_amount, 'sell', True)
            sell_order_id, sell_executed_amount, sell_remaining_amount = result_sell_order

            if sell_executed_amount == sell_trade_amount:
                buy_balance_status = await self.check_balance(buy_exchange_id, base, quote, 'buy', buy_trade_amount, buy_price)
                if buy_balance_status:
                    result_buy_order = await self.create_order(buy_exchange_id, base, quote, buy_price, buy_trade_amount, 'buy', True)

        return result_buy_order, result_sell_order


    # ### Handle trade results ***********************************************
    async def handle_trade_results(self, trade: Trade, result_buy_order, result_sell_order) -> Tuple[bool, bool, bool]:
        """
        Handle the trade results.
        """

        # Get order results
        buy_order_id, buy_executed_amount, buy_remaining_amount = result_buy_order
        sell_order_id, sell_executed_amount, sell_remaining_amount = result_sell_order

        # Check if orders were placed successfully
        order_success = {
            buy_order_id: buy_remaining_amount <= 0,
            sell_order_id: sell_remaining_amount <= 0
        }

        trade_success = order_success[buy_order_id] and order_success[sell_order_id]

        return buy_order_id, sell_order_id, order_success[buy_order_id], order_success[sell_order_id], trade_success

    # ### Handle orders *******************************************************
    # Create orders
    async def create_order(self, exchange_id: str, base: str, quote: str, price: float, trade_amount: float, side: str, monitor_order) -> Tuple[str, float, float]:
        """
        Create an order on the specified exchange.
        """
        #print("")
        t = time.localtime()
        current_time = time.strftime("%m-%d-%Y %H:%M:%S", t)
        self.logger.info(
            f"{current_time}: Creating {side} order on {exchange_id} for {trade_amount} {base} at {price} {quote}...")

        latest_price = await self.monitor_price(exchange_id, base, quote, side, price)
        order_placed_id, total_executed_amount, total_remaining_amount = await self.execute_order(exchange_id, base, quote, side, trade_amount, latest_price, monitor_order)

        if total_executed_amount == trade_amount:
            self.logger.info(
                f"{current_time}: {side} order on {exchange_id} for {trade_amount} {base} at {latest_price} {quote} has been executed!")

        return order_placed_id, total_executed_amount, total_remaining_amount

    # Monitor exchange prices for sending orders only when they are closer the order book top
    async def monitor_price(self, exchange_id: str, base: str, quote: str, side, price_to_check):
        try:
            #print("")
            t = time.localtime()
            current_time = time.strftime("%m-%d-%Y %H:%M:%S", t)
            while True:
                await asyncio.sleep(3)
                price = await self.api_manager.get_last_price(exchange_id, base, quote)
                #print(f"{current_time}: Monitoring price: {price_to_check} distance from current price: {price}", end="\r")
                
                if side == 'buy' and price_to_check >= price:
                    return price
                
                if side == 'sell' and price_to_check <= price:
                    return price
                
        except Exception as e:
            self.logger.error(f"error monitoring price for {exchange_id}: {e}")
            return False
        
    # Execute the order either in real mode or simulation mode
    async def execute_order(self, exchange_id: str, base: str, quote: str, side: str, trade_amount: float, price: float, monitor_order):
        #print("")
        if not self.is_simulation_mode:
            order_placed = await self.api_manager.create_order(exchange_id, base, quote, side, trade_amount, price)
            order_placed_id = order_placed['id']
            if monitor_order:
                executed_amount, remaining_amount = await self.monitor_order(exchange_id, order_placed['id'], side, base, quote, trade_amount, price)
            else:
                executed_amount = trade_amount
                remaining_amount = 0
        else:
            # Simulation alternative
            executed_amount = trade_amount
            remaining_amount = 0
            order_placed_id = f"{side}_{random.randint(100000, 999999)}"

        return order_placed_id, executed_amount, remaining_amount
    

            

    # Monitor orders sent to the exchange
    async def monitor_order(self, exchange_id: str, order_id: str, side_order, base: str, quote: str, target_amount: float, price) -> Tuple[float, float]:
        """
        Monitor an order until it is filled or canceled.
        """
        t = time.localtime()
        current_time = time.strftime("%m-%d-%Y %H:%M:%S", t)
        self.logger.info(f"{current_time}: Monitoring {side_order} order: {order_id} at price: {price}")
        
        while True:
            await asyncio.sleep(1)
            orders = await self.api_manager.watch_orders(exchange_id, base, quote)
            
            if not orders:
                return target_amount, 0
            
            desired_order = None
            for order in orders:
                if order["id"] == order_id:
                    desired_order = order
                    break
            
            if desired_order is None:
                t = time.localtime()
                current_time = time.strftime("%m-%d-%Y %H:%M:%S", t)
                self.logger.info(f"{current_time}: {side_order} order: {order_id} already filled. Continue trading.\n")
                return target_amount, 0
            
            #print(f"{current_time}: Monitoring {desired_order['side']} order: {desired_order['id']}, {desired_order['price']}, {desired_order['amount']}, {desired_order['status']}", end="\r")
            
            if desired_order['status'] == 'closed':
                t = time.localtime()
                current_time = time.strftime("%m-%d-%Y %H:%M:%S", t)
                self.logger.info(f"{current_time}: {desired_order['side']} order: {desired_order['id']} executed. Continue trading.\n")
                return target_amount, 0
            
            elif desired_order['status'] == 'canceled':
                t = time.localtime()
                current_time = time.strftime("%m-%d-%Y %H:%M:%S", t)
                self.logger.warning(f"{current_time}: {desired_order['side']} order: {order_id} was canceled. Continue trading.\n")
                return 0, target_amount

    # ### Handle Balance **************************************************
    async def check_balance(self, exchange_id: str, base: str, quote: str, side: str, trade_amount: float, price: float) -> bool:
        try:
            if self.is_simulation_mode:
                return True
            
            await asyncio.sleep(1)
            balance = await self.api_manager.get_balance(exchange_id)

            if side == 'buy':
                amount = trade_amount*price
                if balance['free'][quote] < amount:
                    self.logger.info(
                        f"Not enough buy balance: {balance['free'][quote]} < {amount}")
                    return False
            elif side == 'sell':
                if balance['free'][base] < trade_amount:
                    self.logger.info(
                        f"Not enough sell balance: {balance['free'][base]} < {trade_amount}")
                    return False
        except Exception as e:
            self.logger.error(f"Error checking balance: {e}")
            return False

        return True

