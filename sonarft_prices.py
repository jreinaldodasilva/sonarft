import time
from typing import Optional, Dict, List, Tuple
from decimal import getcontext
import logging

from sonarft_api_manager import SonarftApiManager
from sonarft_indicators import SonarftIndicators

getcontext().prec = 8

class SonarftPrices:

    def __init__(self, api_manager: SonarftApiManager, sonarft_indicators: SonarftIndicators, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.api_manager = api_manager
        self.sonarft_indicators = sonarft_indicators

    async def weighted_adjust_prices(self, botid, buy_exchange: str, sell_exchange, base: str, quote: str,
                                 target_buy_price, target_sell_price,
                                 last_buy_price, last_sell_price,
                                 volatility_risk_factor=0.001):
        """
        Adjust prices to be the best ones to create a robust and solid trade.
        """
        t = time.localtime()
        current_time = time.strftime("%m-%d-%Y %H:%M:%S", t)
        
        # Check for fast market movement
        order_book_depth = 6
        market_movement_buy, market_animal_buy = await self.sonarft_indicators.market_movement(buy_exchange, base, quote, order_book_depth)
        market_movement_sell, market_animal_sell = await self.sonarft_indicators.market_movement(sell_exchange, base, quote, order_book_depth)
        #if market_movement_buy == 'fast' and market_movement_sell == 'fast' and market_animal_buy == 'bear':
        #    self.logger.info(f"Fast Bear Movement. Skipping trading...\n")
        #    return 0, 0

        # Get market direction and strength
        period = 14
        rsi_period = 14 
        stoch_period = 14 
        k_period = 3 
        d_period = 3 
        market_direction_buy = await self.sonarft_indicators.get_market_direction(
            buy_exchange, base, quote, 'sma', period)
        market_direction_sell = await self.sonarft_indicators.get_market_direction(
            sell_exchange, base, quote, 'sma', period)
        
        market_rsi_buy = await self.sonarft_indicators.get_rsi(
            buy_exchange, base, quote,  rsi_period)
        market_rsi_sell = await self.sonarft_indicators.get_rsi(
            sell_exchange, base, quote, rsi_period)
        
        market_stoch_rsi_buy_k, market_stoch_rsi_buy_d = await self.sonarft_indicators.get_stoch_rsi(
        buy_exchange, base, quote, rsi_period, stoch_period, k_period, d_period)

        market_stoch_rsi_sell_k, market_stoch_rsi_sell_d = await self.sonarft_indicators.get_stoch_rsi(
        sell_exchange, base, quote, rsi_period, stoch_period, k_period, d_period)

        market_strength = (market_rsi_buy + market_rsi_sell) / 2

        market_trend_buy = await self.sonarft_indicators.get_short_term_market_trend(buy_exchange, base, quote, '1m', 6, 0.001)
        market_trend_sell = await self.sonarft_indicators.get_short_term_market_trend(sell_exchange, base, quote, '1m', 6, 0.001)

          # Calculate volatility as standard deviation of recent price data
        volatility_buy = await self.sonarft_indicators.get_volatility(buy_exchange, base, quote)
        volatility_sell = await self.sonarft_indicators.get_volatility(sell_exchange, base, quote)

       # volatility adjustment for buy exchange
        volatility_buy *= await self.dynamic_volatility_adjustment(market_direction_buy, market_trend_buy, buy_exchange, base, quote)

        # volatility adjustment for sell exchange
        volatility_sell *= await self.dynamic_volatility_adjustment(market_direction_sell, market_trend_sell, sell_exchange, base, quote)


        # Calculate the weight for each exchange based on volatility and volatility factor
        # Compute the final volatility as the average of the adjusted volatilities from both exchanges
        volatility = volatility_risk_factor * (volatility_buy + volatility_sell) / 2
        volatility_factor = volatility_risk_factor * market_strength
        weight = 1 - (volatility * volatility_factor)
        #self.logger.info(f"volatility: {volatility} - volatility_factor: {volatility_factor} - weight: {weight}")

        # get current prices weighted
        order_book_buy = await self.sonarft_indicators.get_order_book(buy_exchange, base, quote)
        order_book_sell = await self.sonarft_indicators.get_order_book(sell_exchange, base, quote)

        depth = 3
        buy_weighted_price = self.get_weighted_price(order_book_buy['bids'], depth)
        sell_weighted_price = self.get_weighted_price(order_book_sell['asks'], depth)
        #self.logger.info(f"buy_weighted_price: {buy_weighted_price}")
        #self.logger.info(f"sell_weighted_price: {sell_weighted_price}")

        # Adjust the prices 
        adjusted_buy_price = weight * target_buy_price + (1 - weight) * buy_weighted_price
        adjusted_sell_price = weight * target_sell_price + (1 - weight) * sell_weighted_price
        #self.logger.info(f"adjusted_buy_price: {adjusted_buy_price}")
        #self.logger.info(f"adjusted_sell_price: {adjusted_sell_price}")
        #self.logger.info("--------------------------------\n")

        # spread for each price
        spread_increase_factor = 1.00072  # Increase spread
        spread_decrease_factor = 0.99936  # Decrease spread
        spread_factor = self.sonarft_indicators.get_profit_factor(volatility)
        #spread_factor = 0.99972
        #self.logger.info(f"spread_increase_factor: {spread_increase_factor}")
        #self.logger.info(f"spread_decrease_factor: {spread_decrease_factor}")
        #self.logger.info(f"spread_factor: {spread_factor}")

        #
        # bull bull
        if market_direction_buy == 'bull' and market_trend_buy == 'bull':
            # overbought price
            if market_rsi_buy >= 70 and market_stoch_rsi_buy_k > market_stoch_rsi_buy_d:
                adjusted_buy_price *= spread_decrease_factor
            else:
                adjusted_buy_price *= spread_increase_factor
        # bull bull
        if market_direction_sell == 'bull' and market_trend_sell == 'bull':
            # overbought price
            if market_rsi_sell >= 70 and market_stoch_rsi_sell_k > market_stoch_rsi_sell_d:
                adjusted_sell_price *= spread_decrease_factor
            else:
                adjusted_sell_price *= spread_increase_factor

        #
        # bear bear
        if market_direction_buy == 'bear' and market_trend_buy == 'bear':
            # oversold price
            if market_rsi_buy <= 30 and market_stoch_rsi_buy_k < market_stoch_rsi_buy_d:
                adjusted_buy_price *= spread_increase_factor
            else:
                adjusted_buy_price *= spread_decrease_factor
        # bear bear
        if market_direction_sell == 'bear' and market_trend_sell == 'bear':
            # oversold price
            if market_rsi_sell <= 30 and market_stoch_rsi_sell_k < market_stoch_rsi_sell_d:
                adjusted_sell_price *= spread_increase_factor
            else:
                adjusted_sell_price *= spread_decrease_factor

        """"
        # bull bear
        if market_direction_buy == 'bull' and market_trend_buy == 'bear':
            # overbought price
            if market_rsi_buy >= 70:
                adjusted_buy_price *= spread_decrease_factor
            else:
                adjusted_buy_price *= spread_increase_factor
        # bull bear
        if market_direction_sell == 'bull' and market_trend_sell == 'bear':
            # overbought price
            if market_rsi_sell >= 70:
                adjusted_sell_price *= spread_decrease_factor
            else:
                adjusted_sell_price *= spread_increase_factor

        # bear bull
        if market_direction_buy == 'bear' and market_trend_buy == 'bull':
            # oversold price
            if market_rsi_buy <= 30:
                adjusted_buy_price *= spread_increase_factor
            else:
                adjusted_buy_price *= spread_decrease_factor
        # bear bull
        if market_direction_sell == 'bear' and market_trend_sell == 'bull':
            # oversold price
            if market_rsi_sell <= 30:
                adjusted_sell_price *= spread_increase_factor
            else:
                adjusted_sell_price *= spread_decrease_factor
        """

        #self.logger.info(f"adjusted_buy_price: {adjusted_buy_price}")
        #self.logger.info(f"adjusted_sell_price: {adjusted_sell_price}")
        #self.logger.info("--------------------------------\n")

        # Apply the spread for enabling profit
        adjusted_buy_price *= spread_factor
        adjusted_sell_price /= spread_factor
        #self.logger.info(f"spreaded adjusted_buy_price: {adjusted_buy_price}")
        #self.logger.info(f"spreaded adjusted_sell_price: {adjusted_sell_price}")
        #self.logger.info("--------------------------------\n")

        # TODO: implement periods input
        # Checking if adjusted prices fall within the support and resistance levels
        # Period of 3 hours
        period = 3
        support_price = await self.sonarft_indicators.get_support_price( sell_exchange, base, quote, period)
        resistance_price = await self.sonarft_indicators.get_resistance_price( buy_exchange, base, quote, period)
        
        # Checking if adjusted prices fall within the support and resistance levels
        if adjusted_buy_price < support_price:
            #self.logger.info(f"Adjusted buy price {adjusted_buy_price} is below support price {support_price}, setting it to support price.")
            adjusted_buy_price = support_price
        if adjusted_sell_price > resistance_price:
            #self.logger.info(f"Adjusted sell price {adjusted_sell_price} is above resistance price {resistance_price}, setting it to resistance price.")
            adjusted_sell_price = resistance_price

        # Additional strategy: If prices break through support or resistance levels, potentially consider a stop-loss or take-profit action
        # This is a simplistic implementation and should be adjusted to suit your specific trading strategy
        #if last_buy_price < support_price:
            #self.logger.info(f"Price has broken through support level. Consider a stop-loss action.")
            # Insert your stop-loss logic here
        #if last_sell_price > resistance_price:
            #self.logger.info(f"Price has broken through resistance level. Consider a take-profit action.")
            # Insert your take-profit logic here
        
        self.logger.info(
            f"BOT:  {botid}")        
        self.logger.info(
            f"BUY:  {buy_exchange} --> SELL:  {sell_exchange}")
        self.logger.info(
            f"Support price {support_price} - resistance price {resistance_price}")
        self.logger.info(
            f"Market BUY side RSI:  {market_rsi_buy}")
        self.logger.info(
            f"Market SELL side RSI:  {market_rsi_sell}") 
        self.logger.info(
            f"Market BUY side StochRSI:  {market_stoch_rsi_buy_k}")
        self.logger.info(
            f"Market SELL side StochRSI:  {market_stoch_rsi_sell_k}")        
        self.logger.info(
            f"Market strength:  {market_strength}")
        self.logger.info(
            f"Market direction:__buy side: {market_direction_buy} - sell side: {market_direction_sell}")
        self.logger.info(
            f"Market trend:______buy side:  {market_trend_buy} - sell side: {market_trend_sell}")

        return adjusted_buy_price, adjusted_sell_price

    def get_weighted_price(self, price_list: list, depth: int) -> float:
        """Returns the weighted price based on the price_list and the depth"""
        if len(price_list) < depth:
            depth = len(price_list)
        total_volume = sum(volume for price, volume in price_list[:depth])
        try:
            weighted_price = sum(price * volume for price, volume in price_list[:depth]) / total_volume
        except ZeroDivisionError:
            self.logger.error("Division by zero while calculating weighted price.")
            return 0.0
        return weighted_price

    async def dynamic_volatility_adjustment(self, market_direction: str, market_trend: str, exchange: str, base: str, quote: str) -> float:
        adjustment_factor = 1.0
        macd, signal, hist = await self.sonarft_indicators.get_macd(exchange, base, quote)
        rsi = await self.sonarft_indicators.get_rsi(exchange, base, quote)
        if market_direction == 'bear' and market_trend == 'bull':
            adjustment_factor = 0.75 if macd < 0 else 1.0
        elif market_direction == 'bull' and market_trend == 'bear':
            adjustment_factor = 0.5 if rsi > 70 else 1.0
        elif market_direction == 'bull' and market_trend == 'bull':
            adjustment_factor = 0.25 if macd > 0 and rsi < 30 else 1.0
        elif market_direction == 'bear' and market_trend == 'bear':
            adjustment_factor = 1.75 if macd < 0 and rsi > 70 else 1.0
        return adjustment_factor


    async def get_the_latest_prices(self, base: str, quote: str, trade_amount: float, weight) -> Optional[Tuple[List, List]]:
        latest_prices = await self.get_latest_prices(base, quote, weight)
        if not latest_prices:
            self.logger.error(
                f"Could not find latest prices for {base}/{quote}")

        target_buy_prices, target_sell_prices = self.get_target_buy_and_sell_prices(
            latest_prices)

        if target_buy_prices is None or target_sell_prices is None:
            self.logger.error(
                f"Could not find best buy and sell prices for {base}/{quote}")

        return target_buy_prices, target_sell_prices

    async def get_latest_prices(self, base: str, quote: str, weight) -> List:
        """
        Get the latest prices for a symbol combination
        """
        latest_prices = await self.api_manager.get_latest_prices(
            base, quote, weight)
        return latest_prices

    def get_target_buy_and_sell_prices(self, filtered_latest_prices: List) -> Tuple[List, List]:
        """
        Get the buy and sell prices.
        """
        target_buy_prices = sorted(filtered_latest_prices, key=lambda x: x[1])
        target_sell_prices = sorted(
            filtered_latest_prices, key=lambda x: x[2], reverse=True)

        return target_buy_prices, target_sell_prices