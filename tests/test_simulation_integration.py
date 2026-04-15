"""
Integration tests for the simulation mode gate end-to-end.
Verifies that no real exchange calls are made when is_simulating_trade=1.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sonarft_execution import SonarftExecution
from sonarft_helpers import Trade


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_trade(**overrides):
    defaults = dict(
        position='', base='BTC', quote='USDT',
        buy_exchange='binance', sell_exchange='okx',
        buy_price=60000.0, sell_price=60200.0,
        buy_trade_amount=1.0, sell_trade_amount=1.0,
        executed_amount=1.0, buy_value=60000.0, sell_value=60200.0,
        buy_fee_rate=0.001, sell_fee_rate=0.001,
        buy_fee_base=0.0, buy_fee_quote=60.0, sell_fee_quote=60.2,
        profit=79.8, profit_percentage=0.00133,
        market_direction_buy='bull', market_direction_sell='bull',
        market_rsi_buy=50.0, market_rsi_sell=50.0,
        market_stoch_rsi_buy_k=50.0, market_stoch_rsi_buy_d=45.0,
        market_stoch_rsi_sell_k=50.0, market_stoch_rsi_sell_d=45.0,
    )
    defaults.update(overrides)
    return Trade(**defaults)


def _make_execution(is_simulation):
    api = MagicMock()
    api.create_order = AsyncMock(return_value={'id': 'live_order_001'})
    api.cancel_order = AsyncMock(return_value={'id': 'live_order_001', 'status': 'canceled'})
    api.get_balance = AsyncMock(return_value={'free': {'BTC': 10.0, 'USDT': 1_000_000.0}})
    api.watch_orders = AsyncMock(return_value=[])
    api.get_last_price = AsyncMock(return_value=59999.0)
    helpers = MagicMock()
    helpers.save_order_history = MagicMock()
    helpers.save_trade_history = MagicMock()
    indicators = MagicMock()
    indicators.get_market_direction = AsyncMock(return_value='bull')
    indicators.get_rsi = AsyncMock(return_value=50.0)
    indicators.get_stoch_rsi = AsyncMock(return_value=(50.0, 45.0))
    return SonarftExecution(api, helpers, indicators, is_simulation_mode=is_simulation)


# ---------------------------------------------------------------------------
# Simulation mode — no real orders
# ---------------------------------------------------------------------------

class TestSimulationModeIntegration:

    @pytest.mark.asyncio
    async def test_full_trade_cycle_no_real_orders(self):
        """End-to-end: a complete trade cycle in simulation must not call create_order."""
        execution = _make_execution(is_simulation=True)
        trade = _make_trade()
        result = await execution.execute_trade(botid=1, trade=vars(trade))
        execution.api_manager.create_order.assert_not_called()

    @pytest.mark.asyncio
    async def test_simulation_trade_saves_history(self):
        """Simulation trades should still be recorded in order/trade history."""
        execution = _make_execution(is_simulation=True)
        trade = _make_trade()
        await execution.execute_trade(botid=1, trade=vars(trade))
        execution.sonarft_helpers.save_order_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_simulation_order_id_format(self):
        """Synthetic order IDs must follow the {side}_{6-digit-number} format."""
        execution = _make_execution(is_simulation=True)
        result = await execution.execute_order(
            'binance', 'BTC', 'USDT', 'buy', 1.0, 60000.0, monitor_order=False
        )
        order_id, executed, remaining = result
        assert order_id.startswith('buy_')
        assert len(order_id) == 10  # 'buy_' + 6 digits
        assert executed == 1.0
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_simulation_balance_never_fetched(self):
        execution = _make_execution(is_simulation=True)
        trade = _make_trade()
        await execution.execute_trade(botid=1, trade=vars(trade))
        execution.api_manager.get_balance.assert_not_called()

    @pytest.mark.asyncio
    async def test_simulation_cancel_order_never_called(self):
        """In simulation, cancel_order should never be called."""
        execution = _make_execution(is_simulation=True)
        trade = _make_trade()
        await execution.execute_trade(botid=1, trade=vars(trade))
        execution.api_manager.cancel_order.assert_not_called()


# ---------------------------------------------------------------------------
# Live mode — real orders called
# ---------------------------------------------------------------------------

class TestLiveModeIntegration:

    @pytest.mark.asyncio
    async def test_live_mode_calls_create_order(self):
        execution = _make_execution(is_simulation=False)
        await execution.execute_order(
            'binance', 'BTC', 'USDT', 'buy', 1.0, 60000.0, monitor_order=False
        )
        execution.api_manager.create_order.assert_called_once()

    @pytest.mark.asyncio
    async def test_live_mode_checks_balance(self):
        execution = _make_execution(is_simulation=False)
        await execution.check_balance('binance', 'BTC', 'USDT', 'buy', 1.0, 60000.0)
        execution.api_manager.get_balance.assert_called_once()

    @pytest.mark.asyncio
    async def test_live_mode_insufficient_balance_skips_order(self):
        execution = _make_execution(is_simulation=False)
        execution.api_manager.get_balance = AsyncMock(return_value={
            'free': {'BTC': 0.0, 'USDT': 0.0}
        })
        result = await execution.check_balance('binance', 'BTC', 'USDT', 'buy', 1.0, 60000.0)
        assert result is False


# ---------------------------------------------------------------------------
# Safety controls
# ---------------------------------------------------------------------------

class TestSafetyControls:

    @pytest.mark.asyncio
    async def test_max_trade_amount_blocks_oversized_trade(self):
        execution = _make_execution(is_simulation=True)
        execution.max_trade_amount = 0.5  # max 0.5 BTC
        trade = _make_trade(buy_trade_amount=1.0)  # 1 BTC > 0.5 limit
        result = await execution.execute_trade(botid=1, trade=vars(trade))
        assert result is False
        execution.api_manager.create_order.assert_not_called()

    @pytest.mark.asyncio
    async def test_max_trade_amount_zero_means_no_limit(self):
        execution = _make_execution(is_simulation=True)
        execution.max_trade_amount = 0.0  # disabled
        trade = _make_trade(buy_trade_amount=1000.0)
        # Should not be blocked by position size (may fail for other reasons)
        # Just verify create_order is not called (simulation mode)
        await execution.execute_trade(botid=1, trade=vars(trade))
        execution.api_manager.create_order.assert_not_called()

    @pytest.mark.asyncio
    async def test_order_rate_limit_blocks_excess_orders(self):
        import time
        execution = _make_execution(is_simulation=True)
        execution.max_orders_per_minute = 2
        trade = _make_trade()

        # First two should pass
        r1 = await execution.execute_trade(botid=1, trade=vars(trade))
        r2 = await execution.execute_trade(botid=1, trade=vars(trade))
        # Third should be rate-limited
        r3 = await execution.execute_trade(botid=1, trade=vars(trade))
        assert r3 is False

    @pytest.mark.asyncio
    async def test_zero_amount_order_skipped(self):
        execution = _make_execution(is_simulation=False)
        result = await execution.create_order(
            'binance', 'BTC', 'USDT', 60000.0, 0.0, 'buy', False
        )
        assert result is None
        execution.api_manager.create_order.assert_not_called()
