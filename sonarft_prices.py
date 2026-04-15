"""
SonarFT Prices Module
VWAP calculation, weighted price adjustment, spread logic, and support/resistance.
"""
import asyncio
from typing import Optional, Dict, List, Tuple
import logging

from sonarft_api_manager import SonarftApiManager
from sonarft_indicators import SonarftIndicators


class SonarftPrices:

    def __init__(self, api_manager: SonarftApiManager, sonarft_indicators: SonarftIndicators, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.api_manager = api_manager
        self.sonarft_indicators = sonarft_indicators

    async def weighted_adjust_prices(
        self, botid, buy_exchange: str, sell_exchange, base: str, quote: str,
        target_buy_price, target_sell_price,
        last_buy_price, last_sell_price,
        volatility_risk_factor=0.001,
    ):
        """Adjust prices using parallelised indicator fetches."""
        period = 14
        rsi_period = 14
        stoch_period = 14
        k_period = 3
        d_period = 3
        order_book_depth = 6

        # --- fetch all indicators in parallel (30s timeout) ---
        try:
            (
                market_movement_buy,
                market_movement_sell,
                market_direction_buy,
                market_direction_sell,
                market_rsi_buy,
                market_rsi_sell,
                stoch_buy,
                stoch_sell,
                market_trend_buy,
                market_trend_sell,
                volatility_buy_raw,
                volatility_sell_raw,
                order_book_buy,
                order_book_sell,
                support_price,
                resistance_price,
            ) = await asyncio.wait_for(
                asyncio.gather(
                    self.sonarft_indicators.market_movement(buy_exchange, base, quote, order_book_depth),
                    self.sonarft_indicators.market_movement(sell_exchange, base, quote, order_book_depth),
                    self.sonarft_indicators.get_market_direction(buy_exchange, base, quote, 'sma', period),
                    self.sonarft_indicators.get_market_direction(sell_exchange, base, quote, 'sma', period),
                    self.sonarft_indicators.get_rsi(buy_exchange, base, quote, rsi_period),
                    self.sonarft_indicators.get_rsi(sell_exchange, base, quote, rsi_period),
                    self.sonarft_indicators.get_stoch_rsi(buy_exchange, base, quote, rsi_period, stoch_period, k_period, d_period),
                    self.sonarft_indicators.get_stoch_rsi(sell_exchange, base, quote, rsi_period, stoch_period, k_period, d_period),
                    self.sonarft_indicators.get_short_term_market_trend(buy_exchange, base, quote, '1m', 6, 0.001),
                    self.sonarft_indicators.get_short_term_market_trend(sell_exchange, base, quote, '1m', 6, 0.001),
                    self.sonarft_indicators.get_volatility(buy_exchange, base, quote),
                    self.sonarft_indicators.get_volatility(sell_exchange, base, quote),
                    self.sonarft_indicators.get_order_book(buy_exchange, base, quote),
                    self.sonarft_indicators.get_order_book(sell_exchange, base, quote),
                    self.sonarft_indicators.get_support_price(buy_exchange, base, quote, 3),
                    self.sonarft_indicators.get_resistance_price(sell_exchange, base, quote, 3),
                ),
                timeout=30.0,
            )
        except asyncio.TimeoutError:
            self.logger.warning(f"weighted_adjust_prices timed out after 30s for {base}/{quote} — skipping adjustment")
            return 0, 0, {}

        # guard None indicators
        if stoch_buy is None or stoch_sell is None:
            self.logger.warning(f"StochRSI unavailable for {base}/{quote}, skipping adjustment")
            return 0, 0, {}
        market_stoch_rsi_buy_k, market_stoch_rsi_buy_d = stoch_buy
        market_stoch_rsi_sell_k, market_stoch_rsi_sell_d = stoch_sell

        if market_rsi_buy is None or market_rsi_sell is None:
            self.logger.warning(f"RSI unavailable for {base}/{quote}, skipping adjustment")
            return 0, 0, {}
        market_strength = (market_rsi_buy + market_rsi_sell) / 2

        # volatility adjustment (these fetch MACD/RSI — also benefits from cache)
        vol_adj_buy, vol_adj_sell = await asyncio.gather(
            self.dynamic_volatility_adjustment(market_direction_buy, market_trend_buy, buy_exchange, base, quote),
            self.dynamic_volatility_adjustment(market_direction_sell, market_trend_sell, sell_exchange, base, quote),
        )
        volatility_buy = volatility_buy_raw * vol_adj_buy
        volatility_sell = volatility_sell_raw * vol_adj_sell

        volatility = volatility_risk_factor * (volatility_buy + volatility_sell) / 2
        volatility_factor = volatility_risk_factor * market_strength
        weight = max(0.0, min(1.0, 1 - (volatility * volatility_factor)))

        depth = 3
        buy_weighted_price = self.get_weighted_price(order_book_buy['bids'], depth)
        sell_weighted_price = self.get_weighted_price(order_book_sell['asks'], depth)

        if buy_weighted_price == 0.0 or sell_weighted_price == 0.0:
            self.logger.warning(f"Zero-volume order book for {base}/{quote}, skipping adjustment")
            return 0, 0, {}

        adjusted_buy_price = weight * target_buy_price + (1 - weight) * buy_weighted_price
        adjusted_sell_price = weight * target_sell_price + (1 - weight) * sell_weighted_price

        spread_increase_factor = getattr(self, 'spread_increase_factor', 1.00072)
        spread_decrease_factor = getattr(self, 'spread_decrease_factor', 0.99936)
        spread_factor = self.sonarft_indicators.get_profit_factor(volatility)

        # bull+bull
        if market_direction_buy == 'bull' and market_trend_buy == 'bull':
            if market_rsi_buy >= 70 and market_stoch_rsi_buy_k > market_stoch_rsi_buy_d:
                adjusted_buy_price *= spread_decrease_factor
            else:
                adjusted_buy_price *= spread_increase_factor
        if market_direction_sell == 'bull' and market_trend_sell == 'bull':
            if market_rsi_sell >= 70 and market_stoch_rsi_sell_k > market_stoch_rsi_sell_d:
                adjusted_sell_price *= spread_decrease_factor
            else:
                adjusted_sell_price *= spread_increase_factor

        # bear+bear
        if market_direction_buy == 'bear' and market_trend_buy == 'bear':
            if market_rsi_buy <= 30 and market_stoch_rsi_buy_k < market_stoch_rsi_buy_d:
                adjusted_buy_price *= spread_increase_factor
            else:
                adjusted_buy_price *= spread_decrease_factor
        if market_direction_sell == 'bear' and market_trend_sell == 'bear':
            if market_rsi_sell <= 30 and market_stoch_rsi_sell_k < market_stoch_rsi_sell_d:
                adjusted_sell_price *= spread_increase_factor
            else:
                adjusted_sell_price *= spread_decrease_factor

        adjusted_buy_price *= spread_factor
        adjusted_sell_price /= spread_factor

        if support_price is not None and adjusted_buy_price < support_price:
            adjusted_buy_price = support_price
        if resistance_price is not None and adjusted_sell_price > resistance_price:
            adjusted_sell_price = resistance_price

        self.logger.info(f"BOT: {botid} | BUY: {buy_exchange} -> SELL: {sell_exchange}")
        self.logger.info(f"RSI buy={market_rsi_buy:.2f} sell={market_rsi_sell:.2f} | strength={market_strength:.2f}")
        self.logger.info(f"Direction buy={market_direction_buy} sell={market_direction_sell} | trend buy={market_trend_buy} sell={market_trend_sell}")
        self.logger.info(f"StochRSI buy_k={market_stoch_rsi_buy_k:.2f} sell_k={market_stoch_rsi_sell_k:.2f}")
        self.logger.info(f"Support={support_price} resistance={resistance_price}")

        indicators = {
            'market_direction_buy': market_direction_buy,
            'market_direction_sell': market_direction_sell,
            'market_rsi_buy': market_rsi_buy,
            'market_rsi_sell': market_rsi_sell,
            'market_stoch_rsi_buy_k': market_stoch_rsi_buy_k,
            'market_stoch_rsi_buy_d': market_stoch_rsi_buy_d,
            'market_stoch_rsi_sell_k': market_stoch_rsi_sell_k,
            'market_stoch_rsi_sell_d': market_stoch_rsi_sell_d,
        }
        return adjusted_buy_price, adjusted_sell_price, indicators

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
        macd_result = await self.sonarft_indicators.get_macd(exchange, base, quote)
        rsi = await self.sonarft_indicators.get_rsi(exchange, base, quote)
        if macd_result is None or rsi is None:
            return adjustment_factor
        macd, signal, hist = macd_result
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