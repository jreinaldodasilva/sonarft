import asyncio
from dataclasses import dataclass
from decimal import getcontext
import logging
from typing import List, Tuple
import numpy as np

from sonarft_api_manager import SonarftApiManager
from sonarft_helpers import Trade

# Constants
LOW_VOLATILITY_THRESHOLD = 0.1
MEDIUM_VOLATILITY_THRESHOLD = 0.5

getcontext().prec = 8

class SonarftValidators:
    def __init__(self, api_manager: SonarftApiManager, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.api_manager = api_manager

    def validate(self, *args, **kwargs):
        raise NotImplementedError

    def verify_enter_position_price(self, exchange_id, base: str, quote: str, sell_price, enter_position_price_order):
        if not enter_position_price_order:
            return True

        last_enter_position = enter_position_price_order[-1]
        _, _, _, price = last_enter_position

        self.logger.warning(f"{base}/{quote}: Exchange {exchange_id} position buy price: {price}")
        if sell_price >= price:
            return True
        else:
            self.logger.warning(f"{base}/{quote}: Exchange {exchange_id} sell price {sell_price} is BELOW the position buy price: {price}")
            return False

    async def has_liquidity(self, exchange: str, base: str, quote: str, volume: float) -> bool:
        trading_volume = await self.get_trading_volume(exchange, base, quote)
        if not trading_volume:
            self.logger.warning(f"{base}/{quote}: Has Not Liquidity: Trading Volume not found for {exchange}: {base}/{quote}\n")
            return False

        if trading_volume < volume:
            self.logger.warning(f"{base}/{quote}: Has Not Liquidity: Trading Volume not enough for {exchange}: {base}/{quote}\n")
            return False

        return True

    async def deeper_verify_liquidity(self, exchange_id: str, base: str, quote: str, side: str, price: float, target_amount: float, min_trading_volume_coefficient: float) -> bool:
        order_book = await self.get_order_book(exchange_id, base, quote)
        if order_book is None:
            self.logger.warning(f"{base}/{quote}: Deeper Verify Liquidity: Order book not found for {exchange_id}: {base}/{quote}\n")
            return False

        bid_prices = [float(bid[0]) for bid in order_book['bids']]
        ask_prices = [float(ask[0]) for ask in order_book['asks']]
        spread = ask_prices[0] - bid_prices[0]
        if spread / bid_prices[0] > 0.01 and len(bid_prices) < 10 and len(ask_prices) < 10:
            self.logger.warning(f"{base}/{quote}: Deeper Verify Liquidity: Order book is not deep enough for {exchange_id}: {base}/{quote}\n")
            return False

        depth_bids = sum([float(bid[1]) for bid in order_book['bids'][:10]])
        depth_asks = sum([float(ask[1]) for ask in order_book['asks'][:10]])
        if depth_bids / depth_asks < 0.1 or depth_asks / depth_bids < 0.1:
            self.logger.warning(f"{base}/{quote}: Deeper Verify Liquidity: Market depth is not enough for {exchange_id}: {base}/{quote}\n")
            return False

        trading_volume = await self.get_trading_volume(exchange_id, base, quote)
        if trading_volume is None:
            self.logger.warning(f"{base}/{quote}: Deeper Verify Liquidity: Trading volume not found for {exchange_id}: {base}/{quote}\n")
            return False

        if trading_volume < target_amount * min_trading_volume_coefficient:
            self.logger.warning(f"{base}/{quote}: Deeper Verify Liquidity: Trading volume is not enough for {exchange_id}: {base}/{quote}\n")
            return False

        return True

    def calculate_thresholds_based_on_historical_data(self, historical_data_buy: List, historical_data_sell: List) -> dict:
        combined_data = historical_data_buy + historical_data_sell

        historical_bid_prices = [data[1] for data in combined_data]
        historical_ask_prices = [data[2] for data in combined_data]

        historical_spreads = [ask_price - bid_price for bid_price, ask_price in zip(historical_bid_prices, historical_ask_prices)]

        historical_spread_percentage = [spread / ((ask_price + bid_price) / 2) * 100 for bid_price, ask_price, spread in zip(historical_bid_prices, historical_ask_prices, historical_spreads)]
       
        historical_spread_mean = np.mean(historical_spread_percentage)
        historical_spread_std = np.std(historical_spread_percentage)

        thresholds = {
            "low": historical_spread_mean - historical_spread_std,
            "medium": historical_spread_mean,
            "high": historical_spread_mean + historical_spread_std
        }

        return thresholds

    async def get_trade_dynamic_spread_threshold_avg(self, buy_exchange_id: str, sell_exchange_id: str, base: str, quote: str, historical_data_buy: List, historical_data_sell: List) -> Tuple[float, float, float, float, str]:
        buy_order_book, sell_order_book = await asyncio.gather(
            self.get_order_book(buy_exchange_id,base, quote),
            self.get_order_book(sell_exchange_id,base, quote),
        )
        if buy_order_book is None or sell_order_book is None:
            self.logger.warning(f"{base}/{quote}: Spread Threshold: Order book not found\n")
            return 0, 0, 0, 0, None    

        trade_spread_sum = sum([(ask_price - bid_price) * min(ask_volume, bid_volume) for (bid_price, bid_volume) in buy_order_book['bids'][:10] for (ask_price, ask_volume) in sell_order_book['asks'][:10]])
        trade_volume_sum = sum([min(ask_volume, bid_volume) for (_, bid_volume) in buy_order_book['bids'][:10] for (_, ask_volume) in sell_order_book['asks'][:10]])
        trade_spread_avg = trade_spread_sum / trade_volume_sum
        trade_price_sum = sum([((ask_price + bid_price)/2) for bid_price, _ in buy_order_book['bids'][:100] for ask_price, _ in sell_order_book['asks'][:100]])

        trade_price_avg = trade_price_sum / 100
        trade_spread_percentage_avg = (trade_spread_avg / trade_price_avg) * 100

        thresholds = self.calculate_thresholds_based_on_historical_data(historical_data_buy, historical_data_sell)

        if trade_spread_percentage_avg < 0.1:
            spread_threshold = thresholds["low"]
            self.volatility = "Low"
        elif trade_spread_percentage_avg < 0.5:
            spread_threshold = thresholds["medium"]
            self.volatility = "Medium"
        else:
            spread_threshold = thresholds["high"]
            self.volatility = "High"

        return thresholds["low"], thresholds["medium"], thresholds["high"], spread_threshold, self.volatility

    async def get_trade_spread_threshold(self, buy_exchange: str, sell_exchange: str, base, quote) -> Tuple[float, float, float, float, str]:
        timeframe = "1m"
        limit = None
        historical_data_buy, historical_data_sell = await asyncio.gather(
            self.get_history(buy_exchange, base, quote, timeframe, limit),
            self.get_history(sell_exchange, base, quote, timeframe, limit),
        )
        if historical_data_buy is None or historical_data_sell is None:
            self.logger.warning(f"{base}/{quote}: Spread Threshold: Historical data not found\n")
            return False 
        
        low_spread_threshold, medium_spread_threshold, high_spread_threshold, spread_threshold, volatility = await self.get_trade_dynamic_spread_threshold_avg(buy_exchange, sell_exchange, base, quote, historical_data_buy, historical_data_sell)

        return low_spread_threshold, medium_spread_threshold, high_spread_threshold, spread_threshold, volatility

    async def verify_spread_threshold(self, buy_exchange: str, sell_exchange: str, base: str, quote: str, buy_price, sell_price) -> bool:
        spread = sell_price - buy_price
        average_price = (sell_price + buy_price) / (2)
        spread_ratio = (spread) / (average_price)

        low_spread_threshold, medium_spread_threshold, high_spread_threshold, spread_threshold, volatility = await self.get_trade_spread_threshold(buy_exchange, sell_exchange, base, quote)

        thresholds = {
            "Low": medium_spread_threshold,
            "Medium": medium_spread_threshold / 100,
            "High": spread_threshold,
        }

        try:
            if spread_ratio <= thresholds[volatility]:
                return True
            else:
                self.logger.warning(f"{base}/{quote}: Invalid spread: {buy_exchange} -> {sell_exchange} - {base}/{quote} - spread ratio: {spread_ratio} - spread_threshold: {thresholds[volatility]}\n")
                return False
        except KeyError:
            self.logger.warning(f"{base}/{quote}: Unknown volatility type: {volatility}\n")
            return False

    async def check_slippage(self, trade: Trade) -> bool:
        buy_check = await self.check_exchange_slippage(trade.buy_exchange, 'Buy', trade)
        if not buy_check:
            return False

        sell_check = await self.check_exchange_slippage(trade.sell_exchange, 'Sell', trade)
        if not sell_check:
            return False

        return True

    async def check_exchange_slippage(self, exchange: str, action: str, trade: Trade) -> bool:
        history = await self.get_trade_history(exchange, trade.base, trade.quote)
        preprocessed_data = self.preprocess_trade_data(history)
        slippage_tolerance = await self.calculate_slippage_tolerance(exchange, preprocessed_data, 1)
        if slippage_tolerance is None:
            self.logger.warning(f"Slippage tolerance not found for {exchange}: {trade.base}/{trade.quote}\n")
            return False

        order_book = await self.get_order_book(exchange, trade.base, trade.quote)
        top_price = order_book['asks'][0][0] if action == 'Buy' else order_book['bids'][0][0]
        trade_price = trade.buy_price if action == 'Buy' else trade.sell_price
        slippage = ((top_price) - trade_price) / trade_price

        if self.volatility == 'Low' and slippage_tolerance == 0:
            slippage_tolerance = 0.00001

        if slippage <= slippage_tolerance:
            return True
        else:
            self.logger.warning(f"{exchange} Has Low Volatility with too high Slippage: {slippage} - Slippage Tolerance {slippage_tolerance}\n")
            return False

    async def calculate_slippage_tolerance(self, exchange, trade_history, base_risk_factor):
        if trade_history is None:
            self.logger.warning(f"No valid trade data found for {exchange}")
            return None

        slippage_list = []
        price_changes = []
        for trade in trade_history:
            buy_price = trade['buy_price']
            sell_price = trade['sell_price']

            if buy_price > 0 and sell_price > 0:
                slippage = abs((sell_price - buy_price) / buy_price)
                slippage_list.append(slippage)
                price_changes.append(sell_price - buy_price)

        if len(slippage_list) == 0:
            self.logger.warning(f"No valid trade data found for {exchange}")
            return None

        median_slippage = np.median(slippage_list)
        q25, q75 = np.percentile(slippage_list, [25, 75])
        iqr_slippage = q75 - q25

        price_changes_std = np.std(price_changes)
        risk_factor = base_risk_factor * (1 + price_changes_std)

        slippage_tolerance = median_slippage + (risk_factor * iqr_slippage)

        return slippage_tolerance

    def preprocess_trade_data(self, trade_data):
        processed_data = []

        for i in range(len(trade_data) - 1):
            buy_price = trade_data[i]['price']
            sell_price = trade_data[i + 1]['price']
            processed_data.append({'buy_price': buy_price, 'sell_price': sell_price})

        return processed_data

    async def get_order_book(self, exchange_id: str, base: str, quote: str) -> dict:
        order_book = await self.api_manager.get_order_book(exchange_id, base, quote)
        return order_book

    async def get_trading_volume(self, exchange_id: str, base: str, quote: str) -> dict:
        trading_volume = await self.api_manager.get_trading_volume(exchange_id, base, quote)
        return trading_volume

    async def get_history(self, exchange_id: str, base: str, quote: str, timeframe:  str, limit: int) -> dict:
        history_data = await self.api_manager.get_ohlcv_history(exchange_id, base, quote, timeframe, None, limit)
        return history_data

    async def get_trade_history(self, exchange_id: str, base: str, quote: str) -> dict:
        history_trade_data = await self.api_manager.get_trades_history(exchange_id, base, quote)
        return history_trade_data

    async def stop_loss_triggered(self, trade: Trade, buy_price: float, sell_price: float, stop_loss_percentage) -> bool:
        return (sell_price - buy_price) / buy_price <= stop_loss_percentage
