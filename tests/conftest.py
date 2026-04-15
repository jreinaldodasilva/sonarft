"""
Shared pytest fixtures for the SonarFT test suite.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def mock_api_manager():
    """A minimal SonarftApiManager mock covering all methods used by tested classes."""
    api = MagicMock()
    api.get_buy_fee = MagicMock(return_value=0.001)
    api.get_sell_fee = MagicMock(return_value=0.001)
    api.get_symbol_precision = MagicMock(return_value=None)
    api.get_order_book = AsyncMock(return_value={
        'bids': [[60000.0, 1.0], [59990.0, 2.0], [59980.0, 0.5]],
        'asks': [[60010.0, 1.5], [60020.0, 0.5], [60030.0, 1.0]],
    })
    api.get_ohlcv_history = AsyncMock(return_value=[
        [1_000_000 + i * 60_000, 100.0 + i, 105.0 + i, 95.0 + i, 100.0 + i, 10.0]
        for i in range(50)
    ])
    api.get_trading_volume = AsyncMock(return_value=1_000_000.0)
    api.get_last_price = AsyncMock(return_value=60000.0)
    api.create_order = AsyncMock(return_value={'id': 'test_order_123'})
    api.cancel_order = AsyncMock(return_value={'id': 'test_order_123', 'status': 'canceled'})
    api.get_balance = AsyncMock(return_value={
        'free': {'BTC': 10.0, 'USDT': 1_000_000.0}
    })
    return api


@pytest.fixture
def binance_buy_list():
    return ('binance', 60000.0, 60010.0, 60005.0, 'BTC/USDT')


@pytest.fixture
def binance_sell_list():
    return ('binance', 59990.0, 60200.0, 60100.0, 'BTC/USDT')


@pytest.fixture
def okx_sell_list():
    return ('okx', 59990.0, 60200.0, 60100.0, 'BTC/USDT')
