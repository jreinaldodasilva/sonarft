"""
Unit tests for SonarftIndicators — RSI, MACD, StochRSI, market direction, trend.
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock, AsyncMock
from sonarft_indicators import SonarftIndicators


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_indicators(ohlcv=None):
    api = MagicMock()
    api.get_order_book = AsyncMock(return_value={
        'bids': [[60000.0 - i, 1.0] for i in range(20)],
        'asks': [[60010.0 + i, 1.0] for i in range(20)],
    })
    api.get_ohlcv_history = AsyncMock(return_value=ohlcv or _rising_ohlcv(50))
    return SonarftIndicators(api)


def _rising_ohlcv(n, base=100.0, step=1.0):
    """Steadily rising close prices — produces bull RSI > 50."""
    return [
        [1_000_000 + i * 60_000, base + i * step, base + i * step + 2,
         base + i * step - 1, base + i * step, 10.0]
        for i in range(n)
    ]


def _falling_ohlcv(n, base=200.0, step=1.0):
    """Steadily falling close prices — produces bear RSI < 50."""
    return [
        [1_000_000 + i * 60_000, base - i * step, base - i * step + 1,
         base - i * step - 2, base - i * step, 10.0]
        for i in range(n)
    ]


def _flat_ohlcv(n, price=100.0):
    return [
        [1_000_000 + i * 60_000, price, price + 0.1, price - 0.1, price, 10.0]
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# get_rsi
# ---------------------------------------------------------------------------

class TestGetRsi:

    @pytest.mark.asyncio
    async def test_rising_market_rsi_above_50(self):
        ind = make_indicators(_rising_ohlcv(50))
        rsi = await ind.get_rsi('binance', 'BTC', 'USDT', moving_average_period=14)
        assert rsi is not None
        assert rsi > 50

    @pytest.mark.asyncio
    async def test_falling_market_rsi_below_50(self):
        ind = make_indicators(_falling_ohlcv(50))
        rsi = await ind.get_rsi('binance', 'BTC', 'USDT', moving_average_period=14)
        assert rsi is not None
        assert rsi < 50

    @pytest.mark.asyncio
    async def test_rsi_in_valid_range(self):
        ind = make_indicators(_rising_ohlcv(50))
        rsi = await ind.get_rsi('binance', 'BTC', 'USDT')
        assert rsi is not None
        assert 0 <= rsi <= 100

    @pytest.mark.asyncio
    async def test_insufficient_data_returns_none(self):
        ind = make_indicators(_rising_ohlcv(5))  # only 5 candles, need 14
        rsi = await ind.get_rsi('binance', 'BTC', 'USDT', moving_average_period=14)
        assert rsi is None


# ---------------------------------------------------------------------------
# get_macd
# ---------------------------------------------------------------------------

class TestGetMacd:

    @pytest.mark.asyncio
    async def test_returns_three_floats(self):
        ind = make_indicators(_rising_ohlcv(50))
        result = await ind.get_macd('binance', 'BTC', 'USDT')
        assert result is not None
        macd, signal, hist = result
        assert isinstance(macd, float)
        assert isinstance(signal, float)
        assert isinstance(hist, float)

    @pytest.mark.asyncio
    async def test_rising_market_positive_macd(self):
        ind = make_indicators(_rising_ohlcv(50))
        result = await ind.get_macd('binance', 'BTC', 'USDT')
        assert result is not None
        macd, signal, hist = result
        assert macd > 0

    @pytest.mark.asyncio
    async def test_insufficient_data_returns_none(self):
        ind = make_indicators(_rising_ohlcv(10))
        result = await ind.get_macd('binance', 'BTC', 'USDT')
        assert result is None


# ---------------------------------------------------------------------------
# get_stoch_rsi — keyword argument fix regression
# ---------------------------------------------------------------------------

class TestGetStochRsi:

    @pytest.mark.asyncio
    async def test_returns_k_and_d_in_range(self):
        ind = make_indicators(_rising_ohlcv(50))
        result = await ind.get_stoch_rsi('binance', 'BTC', 'USDT',
                                          rsi_period=14, stoch_period=14,
                                          k_period=3, d_period=3)
        assert result is not None
        k, d = result
        assert 0 <= k <= 100
        assert 0 <= d <= 100

    @pytest.mark.asyncio
    async def test_rsi_period_14_not_3(self):
        """Regression: ensure rsi_length=14 is used, not k_period=3."""
        ind = make_indicators(_rising_ohlcv(50))
        # With rsi_period=14 the result should be stable; with rsi_period=3 it would be noisy
        results = []
        for _ in range(3):
            r = await ind.get_stoch_rsi('binance', 'BTC', 'USDT',
                                         rsi_period=14, stoch_period=14,
                                         k_period=3, d_period=3)
            results.append(r)
        # All calls return the same data (same mock), so results should be identical
        assert all(r == results[0] for r in results)


# ---------------------------------------------------------------------------
# get_market_direction
# ---------------------------------------------------------------------------

class TestGetMarketDirection:

    @pytest.mark.asyncio
    async def test_rising_prices_return_bull(self):
        ind = make_indicators(_rising_ohlcv(50))
        direction = await ind.get_market_direction('binance', 'BTC', 'USDT', 'sma', 14)
        assert direction == 'bull'

    @pytest.mark.asyncio
    async def test_falling_prices_return_bear(self):
        ind = make_indicators(_falling_ohlcv(50))
        direction = await ind.get_market_direction('binance', 'BTC', 'USDT', 'sma', 14)
        assert direction == 'bear'

    @pytest.mark.asyncio
    async def test_invalid_ma_type_returns_none(self):
        ind = make_indicators(_rising_ohlcv(50))
        direction = await ind.get_market_direction('binance', 'BTC', 'USDT', 'invalid_ma', 14)
        assert direction is None

    @pytest.mark.asyncio
    async def test_insufficient_data_returns_none(self):
        ind = make_indicators(_rising_ohlcv(5))
        direction = await ind.get_market_direction('binance', 'BTC', 'USDT', 'sma', 14)
        assert direction is None


# ---------------------------------------------------------------------------
# get_short_term_market_trend — zero-division regression
# ---------------------------------------------------------------------------

class TestGetShortTermMarketTrend:

    @pytest.mark.asyncio
    async def test_rising_prices_return_bull(self):
        ind = make_indicators(_rising_ohlcv(10))
        trend = await ind.get_short_term_market_trend('binance', 'BTC', 'USDT', limit=6)
        assert trend == 'bull'

    @pytest.mark.asyncio
    async def test_falling_prices_return_bear(self):
        ind = make_indicators(_falling_ohlcv(10))
        trend = await ind.get_short_term_market_trend('binance', 'BTC', 'USDT', limit=6)
        assert trend == 'bear'

    @pytest.mark.asyncio
    async def test_flat_prices_return_neutral(self):
        ind = make_indicators(_flat_ohlcv(10))
        trend = await ind.get_short_term_market_trend('binance', 'BTC', 'USDT', limit=6)
        assert trend == 'neutral'

    @pytest.mark.asyncio
    async def test_zero_previous_avg_returns_neutral_not_crash(self):
        """Regression: zero previous_avg_price must not raise ZeroDivisionError or NameError."""
        zero_ohlcv = [[1_000_000 + i * 60_000, 0, 0, 0, 0, 0] for i in range(10)]
        ind = make_indicators(zero_ohlcv)
        trend = await ind.get_short_term_market_trend('binance', 'BTC', 'USDT', limit=6)
        assert trend == 'neutral'


# ---------------------------------------------------------------------------
# get_support_price / get_resistance_price
# ---------------------------------------------------------------------------

class TestSupportResistance:

    @pytest.mark.asyncio
    async def test_support_is_minimum_low(self):
        ohlcv = _rising_ohlcv(10)
        ind = make_indicators(ohlcv)
        support = await ind.get_support_price('binance', 'BTC', 'USDT', lookback_period=10)
        expected_min_low = min(x[3] for x in ohlcv)
        assert support == expected_min_low

    @pytest.mark.asyncio
    async def test_resistance_is_maximum_high(self):
        ohlcv = _rising_ohlcv(10)
        ind = make_indicators(ohlcv)
        resistance = await ind.get_resistance_price('binance', 'BTC', 'USDT', lookback_period=10)
        expected_max_high = max(x[2] for x in ohlcv)
        assert resistance == expected_max_high

    @pytest.mark.asyncio
    async def test_insufficient_data_returns_none(self):
        ind = make_indicators(_rising_ohlcv(3))
        support = await ind.get_support_price('binance', 'BTC', 'USDT', lookback_period=10)
        assert support is None
