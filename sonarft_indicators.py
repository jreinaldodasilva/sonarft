import pandas as pd
import pandas_ta as pta
import numpy as np
from typing import Tuple
import logging

from sonarft_api_manager import SonarftApiManager


class SonarftIndicators:
    def __init__(self, api_manager: SonarftApiManager, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.api_manager = api_manager

        self.spread_rate_threshold = 0.01
        self.price_rate_threshold = 0.01
        self.previous_spread = 1

    def get_profit_factor(self, volatility: float, min_spread: float = 0.99912, max_spread: float = 0.99972) -> float:
        """
        Calculate a dynamic spread factor based on market volatility.
        """
        try:
            normalized_volatility = min(max(volatility, 0), 1)

            # Calculate the spread factor as a linear interpolation between the minimum and maximum spread
            spread_factor = min_spread + \
                (max_spread - min_spread) * normalized_volatility

            return spread_factor
        except Exception as e:
            self.logger.error(f"Error calculating profit factor: {str(e)}")
            return None

    async def get_support_price(self, exchange_id, base, quote, lookback_period=24, timeframe='1h'):
        """
        Calculate support level based on historical data over the lookback_period.
        """
        try:
            history_data = await self.get_history(exchange_id, base, quote, timeframe, lookback_period)

            # Ensure there are enough periods to calculate
            if history_data is None or len(history_data) < lookback_period:
                return None

            # 'Low' price is at index 3 in OHLCV data
            low_prices = [x[3] for x in history_data]
            return min(low_prices)
        except Exception as e:
            self.logger.error(f"Error get_support_price: {str(e)}")
            return None

    async def get_resistance_price(self, exchange_id, base, quote, lookback_period=24, timeframe='1h'):
        """
        Calculate resistance level based on historical data over the lookback_period.
        """
        try:
            history_data = await self.get_history(exchange_id, base, quote, timeframe, lookback_period)

            # Ensure there are enough periods to calculate
            if history_data is None or len(history_data) < lookback_period:
                return None

            # 'High' price is at index 2 in OHLCV data
            high_prices = [x[2] for x in history_data]
            return max(high_prices)
        except Exception as e:
            self.logger.error(f"Error get_resistance_price: {str(e)}")
            return None

    async def get_rsi(self, exchange, base, quote, moving_average_period=14, timeframe='1m'):
        """Calculate the Relative Strength Index (RSI)."""
        try:
            ohlcv = await self.get_history(exchange, base, quote, timeframe, moving_average_period+2)
            if not ohlcv or len(ohlcv) < moving_average_period:
                raise ValueError(f"Not enough data for RSI: need {moving_average_period}, have {len(ohlcv) if ohlcv else 0}")
            close_prices = pd.Series([x[4] for x in ohlcv])
            rsi = pta.rsi(close_prices, length=moving_average_period)
            value = rsi.iloc[-1]
            if pd.isna(value):
                self.logger.warning(f"RSI returned NaN for {exchange} {base}/{quote}")
                return None
            return float(value)
        except Exception as e:
            self.logger.error(f"Error get_rsi: {str(e)}")
            return None
    

    async def get_stoch_rsi(self, exchange, base, quote, rsi_period=14, stoch_period=14, k_period=3, d_period=3, timeframe='1m'):
        """Calculate the Stochastic RSI."""
        try:
            ohlcv = await self.get_history(exchange, base, quote, timeframe, rsi_period + stoch_period + d_period + 1)
            if not ohlcv or len(ohlcv) < rsi_period + stoch_period:
                raise ValueError(f"Not enough data for StochRSI: need {rsi_period + stoch_period}, have {len(ohlcv) if ohlcv else 0}")
            close_prices = pd.Series([x[4] for x in ohlcv])
            # Use keyword arguments to avoid positional parameter mismatch.
            # pandas-ta stochrsi signature: (close, length, rsi_length, k, d)
            stoch_rsi = pta.stochrsi(close_prices, length=stoch_period, rsi_length=rsi_period, k=k_period, d=d_period)
            k_val = stoch_rsi.iloc[-1][0]
            d_val = stoch_rsi.iloc[-1][1]
            if pd.isna(k_val) or pd.isna(d_val):
                self.logger.warning(f"StochRSI returned NaN for {exchange} {base}/{quote}")
                return None
            return float(k_val), float(d_val)
        except Exception as e:
            self.logger.error(f"Error get_stoch_rsi: {str(e)}")
            return None


    async def get_market_direction(self, exchange_id, base, quote, ma_type='sma', moving_average_period=14, timeframe='1m'):
        """Get market direction via SMA or EMA."""
        try:
            history_data = await self.get_history(exchange_id, base, quote, timeframe, moving_average_period+2)
            if not history_data or len(history_data) < moving_average_period:
                raise ValueError(f"Insufficient data for market direction: {exchange_id} {base}/{quote}")
            close_prices = pd.Series([x[4] for x in history_data])
            if ma_type == 'sma':
                moving_average = pta.sma(close_prices, length=moving_average_period)
            elif ma_type == 'ema':
                moving_average = pta.ema(close_prices, length=moving_average_period)
            else:
                raise ValueError(f"Invalid ma_type: {ma_type}")
            current_price = close_prices.iloc[-1]
            ma_value = moving_average.iloc[-1]
            if pd.isna(ma_value) or pd.isna(current_price):
                self.logger.warning(f"Market direction MA returned NaN for {exchange_id} {base}/{quote}")
                return 'neutral'
            if current_price > ma_value:
                return 'bull'
            if current_price < ma_value:
                return 'bear'
            return 'neutral'
        except Exception as e:
            self.logger.error(f"Error get_market_direction: {str(e)}")
            return None    

    async def get_short_term_market_trend(self, exchange, base, quote, timeframe='1m', limit=6, threshold=0.001):
        """
        Calculate the percent price change between the last N trades and the N trades before those,
        and determine if this change indicates a bull or bear market.
        """
        try:
            N = limit // 2  # we'll consider the last N periods and the N periods before those

            # Fetch OHLCV data
            ohlcv = await self.get_history(exchange, base, quote, timeframe, limit)

            # Ensure there are enough periods to calculate a change
            if len(ohlcv) < 2*N:
                raise ValueError(
                    f"Not enough data to calculate market trend. Need {2*N} periods, have {len(ohlcv)}.")

            # Get the close prices of the most recent N periods and the N periods before those
            current_prices = [period[4] for period in ohlcv[-N:]]
            previous_prices = [period[4] for period in ohlcv[-2*N:-N]]

            # Calculate the average price for each period
            current_avg_price = sum(current_prices) / N
            previous_avg_price = sum(previous_prices) / N

            # Guard against zero division before computing percent change
            if previous_avg_price == 0:
                return 'neutral'

            # Calculate the percent change
            price_change = 100 * (current_avg_price - previous_avg_price) / previous_avg_price

            # price_change is already in percent (multiplied by 100 above).
            # threshold is treated as a percent value (e.g. 0.1 = 0.1%).
            if price_change > threshold * 100:
                return 'bull'
            elif price_change < -(threshold * 100):
                return 'bear'
            else:
                return 'neutral'
        except Exception as e:
            self.logger.error(f"Error get_short_term_market_trend: {str(e)}")
            return None    
        

    async def get_macd(self, exchange, base, quote, short_period=12, long_period=26, signal_period=9, warmup=10):
        """Calculate MACD."""
        try:
            timeframe = '1m'
            ohlcv = await self.get_history(exchange, base, quote, timeframe, long_period + signal_period + warmup)
            if not ohlcv or len(ohlcv) < long_period + signal_period + warmup:
                raise ValueError(f"Not enough data for MACD: need {long_period + signal_period + warmup}, have {len(ohlcv) if ohlcv else 0}")
            close_prices = pd.Series([x[4] for x in ohlcv])
            macd = pta.macd(close_prices, short_period, long_period, signal_period)
            macd_col = f'MACD_{short_period}_{long_period}_{signal_period}'
            signal_col = f'MACDs_{short_period}_{long_period}_{signal_period}'
            hist_col = f'MACDh_{short_period}_{long_period}_{signal_period}'
            if macd_col not in macd.columns:
                raise KeyError(f"Expected MACD column '{macd_col}' not found. Available: {list(macd.columns)}")
            m, s, h = macd[macd_col].iloc[-1], macd[signal_col].iloc[-1], macd[hist_col].iloc[-1]
            if pd.isna(m) or pd.isna(s) or pd.isna(h):
                self.logger.warning(f"MACD returned NaN for {exchange} {base}/{quote}")
                return None
            return float(m), float(s), float(h)
        except Exception as e:
            self.logger.error(f"Error get_macd: {str(e)}")
            return None
    

    async def get_price_change(self, exchange, base, quote, timeframe='1m', limit=20):
        """
        Calculate the percent price change between the last N trades and the N trades before those.
        """
        N = limit // 2  # we'll consider the last N periods and the N periods before those

        # Fetch OHLCV data
        ohlcv = await self.get_history(exchange, base, quote, timeframe, limit)

        # Ensure there are enough periods to calculate a change
        if len(ohlcv) < 2*N:
            return None

        # Get the close prices of the most recent N periods and the N periods before those
        current_prices = [period[4] for period in ohlcv[-N:]]
        previous_prices = [period[4] for period in ohlcv[-2*N:-N]]

        # Calculate the average price for each period
        current_avg_price = sum(current_prices) / N
        previous_avg_price = sum(previous_prices) / N

        # Calculate the percent change
        price_change = 100 * (current_avg_price -
                              previous_avg_price) / previous_avg_price

        return price_change

    async def market_movement(self, exchange_id: str, base: str, quote: str, order_book_depth) -> Tuple[bool, str]:
        """
        Check if the market is experiencing a fast movement and determine the movement direction (bull or bear).
        Uses a per-call previous_spread local to avoid race conditions under concurrent symbol processing.
        """

        order_book = await self.get_order_book(exchange_id, base, quote)

        depth_bids = sum([float(bid[0])
                         for bid in order_book['bids'][:order_book_depth]])
        depth_asks = sum([float(ask[0])
                         for ask in order_book['asks'][:order_book_depth]])

        # Calculate the spread
        spread = depth_asks - depth_bids

        # Use instance previous_spread as a snapshot; update atomically after reading.
        # This is a best-effort rate calculation — exact ordering is not critical.
        previous = self.previous_spread
        self.previous_spread = spread
        spread_rate = (spread - previous) / previous if previous != 0 else 0

        direction = "bull" if depth_bids > depth_asks else "bear"

        if abs(spread_rate) > self.spread_rate_threshold:
            return "fast", direction

        return "slow", direction

    async def get_atr(self, exchange_id, base, quote, atr_period=14):
        """Calculate the Average True Range (ATR) over a specified period."""
        history_data = await self.get_history(exchange_id, base, quote, '1m', atr_period+1)
        if len(history_data) < atr_period + 1:
            self.logger.warning(
                f"Not enough data to calculate ATR. Need {atr_period + 1} periods, have {len(history_data)}.")
            return None
        high = pd.Series([x[2] for x in history_data])
        low = pd.Series([x[3] for x in history_data])
        close = pd.Series([x[4] for x in history_data])
        atr = pta.atr(high, low, close, length=atr_period)
        return atr.iloc[-1]

    async def get_24h_high(self, exchange_id, base, quote):
        """
        Calculate the 24-hour high.
        """
        history_data = await self.get_history(exchange_id, base, quote, '1m', 1440)
        if len(history_data) < 1440:
            self.logger.warning(
                f"Not enough data to calculate 24h High. Need 1440 periods, have {len(history_data)}.")
            return None
        high = np.array([x[2] for x in history_data])
        return np.max(high)

    async def get_24h_low(self, exchange_id, base, quote):
        """
        Calculate the 24-hour low.
        """
        history_data = await self.get_history(exchange_id, base, quote, '1m', 1440)
        if len(history_data) < 1440:
            self.logger.warning(
                f"Not enough data to calculate 24h Low. Need 1440 periods, have {len(history_data)}.")
            return None
        low = np.array([x[3] for x in history_data])
        return np.min(low)

    async def get_historical_volume(self, exchange_id: str, base: str, quote: str, timeframe, limit) -> float:
        """
        Returns the most recent candle's volume for the given exchange and symbol.
        """
        ohlcv = await self.get_history(exchange_id, base, quote, timeframe, limit)
        if not ohlcv:
            return 0.0
        # OHLCV format: [timestamp, open, high, low, close, volume] — index -1 is most recent
        return ohlcv[-1][5]

    async def get_current_volume(self, exchange_id: str, base: str, quote: str, depth: int = 10) -> Tuple[float, float]:
        """
        Calculate the total volume of the bid and ask orders up to a certain depth in the order book.
        """
        order_book = await self.get_order_book(exchange_id, base, quote)

        bid_volume = sum(volume for price,
                         volume in order_book['bids'][:depth])
        ask_volume = sum(volume for price,
                         volume in order_book['asks'][:depth])

        return bid_volume, ask_volume

    async def get_liquidity(self, exchange_id: str, base: str, quote: str) -> float:
        """
        Calculate a normalised liquidity score for the given exchange and market pair.
        Computed as total order book volume divided by the mid-price, then clamped to [0, 1]
        relative to a reference volume of 100 units.
        """
        order_book = await self.get_order_book(exchange_id, base, quote)
        if not order_book:
            return 0.0
        bids = order_book['bids']
        asks = order_book['asks']
        if not bids or not asks:
            return 0.0

        mid_price = (bids[0][0] + asks[0][0]) / 2
        if mid_price == 0:
            return 0.0

        bid_volume_sum = sum(volume for _, volume in bids)
        ask_volume_sum = sum(volume for _, volume in asks)
        total_volume = bid_volume_sum + ask_volume_sum

        # Normalise: 100 units of base currency at mid-price = liquidity score of 1.0
        reference_volume = 100.0
        normalized_liquidity = min(total_volume / reference_volume, 1.0)
        return normalized_liquidity

    async def get_volatility(self, exchange_id: str, base: str, quote: str) -> float:
        """
        Calculate the volatility based on the order book data.
        """
        order_book = await self.get_order_book(exchange_id, base, quote)
        if order_book is None:
            return 0.0

        bids = order_book['bids']
        asks = order_book['asks']

        bid_prices = [price for price, _ in bids]
        ask_prices = [price for price, _ in asks]

        # Calculate the mid price as the average of the highest bid price and lowest ask price
        mid_price = (max(bid_prices) + min(ask_prices)) / 2

        # Calculate the price changes based on the mid price
        price_changes = [abs(price - mid_price)
                         for price in bid_prices + ask_prices]

        # Calculate the volatility as the standard deviation of the price changes
        volatility = np.std(price_changes)

        return volatility

    async def get_past_performance(self, exchange: str, base: str, quote: str, lookback_period: int = 24) -> float:
        """
        Calculate the past performance for the given exchange and market pair.
        Compares the most recent close price to the oldest close price in the lookback window.
        """
        timeframe = "1m"
        historical_data = await self.get_history(exchange, base, quote, timeframe, lookback_period)
        if not historical_data or len(historical_data) < 2:
            return 0.5  # neutral

        # OHLCV: index -1 = most recent, index 0 = oldest
        current_price = historical_data[-1][4]
        past_price = historical_data[0][4]

        if past_price == 0:
            return 0.5

        performance = (current_price - past_price) / past_price
        normalized_performance = (performance + 1) / 2
        return normalized_performance

    # @lru_cache(maxsize=None)
    async def get_order_book(self, exchange_id: str, base: str, quote: str) -> dict:
        order_book = await self.api_manager.get_order_book(
            exchange_id, base, quote)
        return order_book

    # @lru_cache(maxsize=None)
    async def get_trading_volume(self, exchange_id: str, base: str, quote: str) -> dict:
        trading_volume = await self.api_manager.get_trading_volume(
            exchange_id, base, quote)
        return trading_volume

    # @lru_cache(maxsize=None)
    async def get_history(self, exchange_id: str, base: str, quote: str, timeframe, limit) -> dict:
        history_data = await self.api_manager.get_ohlcv_history(
            exchange_id, base, quote, timeframe, None, limit)
        return history_data

    # @lru_cache(maxsize=None)
    async def get_trade_history(self, exchange_id: str, base: str, quote: str) -> dict:
        history_trade_data = await self.api_manager.get_trades_history(
            exchange_id, base, quote)
        return history_trade_data

    def percentage_difference(self, value1, value2):
        return abs((value1 - value2) / ((value1 + value2) / 2)) * 100
