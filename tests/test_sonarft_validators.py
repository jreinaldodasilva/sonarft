"""
Unit tests for SonarftValidators safety gates and threshold calculations.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from sonarft_validators import SonarftValidators


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_validator(order_book=None, trading_volume=None, history=None):
    api = MagicMock()
    api.get_order_book = AsyncMock(return_value=order_book or {
        'bids': [[60000.0, 1.0], [59990.0, 2.0]] * 5,
        'asks': [[60010.0, 1.5], [60020.0, 0.5]] * 5,
    })
    api.get_trading_volume = AsyncMock(return_value=trading_volume if trading_volume is not None else 1_000_000.0)
    api.get_ohlcv_history = AsyncMock(return_value=history or [
        [1_000_000 + i * 60_000, 100.0 + i, 105.0 + i, 95.0 + i, 100.0 + i, 10.0]
        for i in range(100)
    ])
    return SonarftValidators(api)


HISTORICAL_BUY = [
    [1_000_000 + i * 60_000, 59990.0 + i * 0.1, 60010.0 + i * 0.1, 10.0]
    for i in range(50)
]
HISTORICAL_SELL = [
    [1_000_000 + i * 60_000, 59990.0 + i * 0.1, 60010.0 + i * 0.1, 10.0]
    for i in range(50)
]


# ---------------------------------------------------------------------------
# calculate_thresholds_based_on_historical_data
# ---------------------------------------------------------------------------

class TestCalculateThresholds:

    def test_empty_data_returns_zero_defaults(self):
        v = make_validator()
        result = v.calculate_thresholds_based_on_historical_data([], [])
        assert result == {'low': 0.0, 'medium': 0.0, 'high': 0.0}

    def test_no_nan_in_thresholds(self):
        v = make_validator()
        result = v.calculate_thresholds_based_on_historical_data(
            HISTORICAL_BUY, HISTORICAL_SELL
        )
        for key, val in result.items():
            assert val == val, f"NaN found in threshold '{key}'"  # NaN != NaN

    def test_threshold_ordering(self):
        """low <= medium <= high."""
        v = make_validator()
        result = v.calculate_thresholds_based_on_historical_data(
            HISTORICAL_BUY, HISTORICAL_SELL
        )
        assert result['low'] <= result['medium'] <= result['high']

    def test_medium_not_divided_by_100(self):
        """Regression: medium threshold must NOT be medium/100."""
        v = make_validator()
        result = v.calculate_thresholds_based_on_historical_data(
            HISTORICAL_BUY, HISTORICAL_SELL
        )
        # medium should equal mean, not mean/100
        assert result['medium'] > result['low'] * 0.5 or result['medium'] == 0.0


# ---------------------------------------------------------------------------
# verify_spread_threshold — volatility threshold mapping
# ---------------------------------------------------------------------------

class TestVerifySpreadThreshold:

    @pytest.mark.asyncio
    async def test_medium_threshold_not_100x_stricter_than_low(self):
        """Regression test for the /100 bug: Medium threshold must be close to Low."""
        v = make_validator()

        # Patch get_trade_spread_threshold to return controlled values
        async def mock_spread_threshold(*args, **kwargs):
            return 0.1, 0.5, 1.0, 0.5, 'Medium'

        v.get_trade_spread_threshold = mock_spread_threshold

        # A spread ratio of 0.003 (0.3%) should pass Medium (threshold=0.5)
        result = await v.verify_spread_threshold(
            'binance', 'okx', 'BTC', 'USDT',
            buy_price=60000.0, sell_price=60180.0  # spread_ratio ≈ 0.003
        )
        assert result is True, "Medium volatility threshold incorrectly rejected a valid spread"

    @pytest.mark.asyncio
    async def test_spread_above_threshold_rejected(self):
        v = make_validator()

        async def mock_spread_threshold(*args, **kwargs):
            return 0.001, 0.002, 0.003, 0.002, 'Medium'

        v.get_trade_spread_threshold = mock_spread_threshold

        # spread_ratio ≈ 0.01 >> threshold 0.002
        result = await v.verify_spread_threshold(
            'binance', 'okx', 'BTC', 'USDT',
            buy_price=60000.0, sell_price=60600.0
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_none_volatility_returns_false(self):
        v = make_validator()

        async def mock_spread_threshold(*args, **kwargs):
            return 0.1, 0.5, 1.0, 0.5, None

        v.get_trade_spread_threshold = mock_spread_threshold

        result = await v.verify_spread_threshold(
            'binance', 'okx', 'BTC', 'USDT',
            buy_price=60000.0, sell_price=60180.0
        )
        assert result is False


# ---------------------------------------------------------------------------
# deeper_verify_liquidity — empty order book guard
# ---------------------------------------------------------------------------

class TestDeeperVerifyLiquidity:

    @pytest.mark.asyncio
    async def test_empty_order_book_returns_false(self):
        v = make_validator(order_book={'bids': [], 'asks': []})
        result = await v.deeper_verify_liquidity(
            'binance', 'BTC', 'USDT', 'buy', 60000.0, 1.0, 50
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_none_order_book_returns_false(self):
        v = make_validator(order_book=None)
        v.api_manager.get_order_book = AsyncMock(return_value=None)
        result = await v.deeper_verify_liquidity(
            'binance', 'BTC', 'USDT', 'buy', 60000.0, 1.0, 50
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_sufficient_liquidity_returns_true(self):
        v = make_validator(
            order_book={
                'bids': [[60000.0, 10.0]] * 10,
                'asks': [[60010.0, 10.0]] * 10,
            },
            trading_volume=1_000_000.0
        )
        result = await v.deeper_verify_liquidity(
            'binance', 'BTC', 'USDT', 'buy', 60000.0, 1.0, 50
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_insufficient_trading_volume_returns_false(self):
        v = make_validator(
            order_book={
                'bids': [[60000.0, 10.0]] * 10,
                'asks': [[60010.0, 10.0]] * 10,
            },
            trading_volume=1.0  # way below trade_amount * 50 = 50
        )
        result = await v.deeper_verify_liquidity(
            'binance', 'BTC', 'USDT', 'buy', 60000.0, 1.0, 50
        )
        assert result is False
