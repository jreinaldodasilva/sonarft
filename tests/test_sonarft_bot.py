"""
Unit tests for SonarftBot parameter validation and simulation mode safety gate.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from sonarft_bot import SonarftBot
from sonarft_execution import SonarftExecution
from sonarft_helpers import Trade


# ---------------------------------------------------------------------------
# _validate_parameters
# ---------------------------------------------------------------------------

class TestValidateParameters:

    def _bot_with(self, **kwargs):
        bot = SonarftBot.__new__(SonarftBot)
        bot.logger = MagicMock()
        bot.profit_percentage_threshold = kwargs.get('profit_percentage_threshold', 0.003)
        bot.trade_amount               = kwargs.get('trade_amount', 1.0)
        bot.is_simulating_trade        = kwargs.get('is_simulating_trade', 1)
        bot.max_daily_loss             = kwargs.get('max_daily_loss', 100.0)
        bot.spread_increase_factor     = kwargs.get('spread_increase_factor', 1.00072)
        bot.spread_decrease_factor     = kwargs.get('spread_decrease_factor', 0.99936)
        return bot

    def test_valid_parameters_do_not_raise(self):
        bot = self._bot_with()
        bot._validate_parameters()  # should not raise

    def test_zero_profit_threshold_raises(self):
        bot = self._bot_with(profit_percentage_threshold=0.0)
        with pytest.raises(ValueError, match="profit_percentage_threshold"):
            bot._validate_parameters()

    def test_profit_threshold_above_one_raises(self):
        bot = self._bot_with(profit_percentage_threshold=1.5)
        with pytest.raises(ValueError, match="profit_percentage_threshold"):
            bot._validate_parameters()

    def test_zero_trade_amount_raises(self):
        bot = self._bot_with(trade_amount=0.0)
        with pytest.raises(ValueError, match="trade_amount"):
            bot._validate_parameters()

    def test_negative_trade_amount_raises(self):
        bot = self._bot_with(trade_amount=-1.0)
        with pytest.raises(ValueError, match="trade_amount"):
            bot._validate_parameters()

    def test_invalid_simulation_flag_raises(self):
        bot = self._bot_with(is_simulating_trade=2)
        with pytest.raises(ValueError, match="is_simulating_trade"):
            bot._validate_parameters()

    def test_negative_max_daily_loss_raises(self):
        bot = self._bot_with(max_daily_loss=-10.0)
        with pytest.raises(ValueError, match="max_daily_loss"):
            bot._validate_parameters()

    def test_zero_max_daily_loss_is_valid(self):
        """Zero means disabled — should be allowed."""
        bot = self._bot_with(max_daily_loss=0.0)
        bot._validate_parameters()  # should not raise

    def test_spread_increase_factor_out_of_range_raises(self):
        bot = self._bot_with(spread_increase_factor=1.02)
        with pytest.raises(ValueError, match="spread_increase_factor"):
            bot._validate_parameters()

    def test_spread_decrease_factor_out_of_range_raises(self):
        bot = self._bot_with(spread_decrease_factor=0.98)
        with pytest.raises(ValueError, match="spread_decrease_factor"):
            bot._validate_parameters()


# ---------------------------------------------------------------------------
# Simulation mode gate
# ---------------------------------------------------------------------------

class TestSimulationModeGate:

    def _make_execution(self, is_simulation):
        api = MagicMock()
        api.create_order = AsyncMock(return_value={'id': 'real_order_001'})
        api.get_balance = AsyncMock(return_value={'free': {'BTC': 10.0, 'USDT': 1_000_000.0}})
        api.watch_orders = AsyncMock(return_value=[])
        api.get_last_price = AsyncMock(return_value=60000.0)
        helpers = MagicMock()
        helpers.save_order_history = MagicMock()
        helpers.save_trade_history = MagicMock()
        indicators = MagicMock()
        indicators.get_market_direction = AsyncMock(return_value='bull')
        indicators.get_rsi = AsyncMock(return_value=50.0)
        indicators.get_stoch_rsi = AsyncMock(return_value=(50.0, 50.0))
        return SonarftExecution(api, helpers, indicators, is_simulation_mode=is_simulation)

    def _make_trade(self, **kwargs):
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
        defaults.update(kwargs)
        return Trade(**defaults)

    @pytest.mark.asyncio
    async def test_simulation_mode_never_calls_create_order(self):
        execution = self._make_execution(is_simulation=True)
        trade = self._make_trade()
        await execution._execute_single_trade(botid=1, trade=trade)
        execution.api_manager.create_order.assert_not_called()

    @pytest.mark.asyncio
    async def test_simulation_mode_returns_synthetic_order_id(self):
        execution = self._make_execution(is_simulation=True)
        result = await execution.execute_order(
            'binance', 'BTC', 'USDT', 'buy', 1.0, 60000.0, monitor_order=False
        )
        order_id, executed, remaining = result
        assert 'buy_' in order_id
        assert executed == 1.0
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_simulation_mode_balance_check_always_passes(self):
        execution = self._make_execution(is_simulation=True)
        result = await execution.check_balance('binance', 'BTC', 'USDT', 'buy', 1.0, 60000.0)
        assert result is True
        execution.api_manager.get_balance.assert_not_called()

    @pytest.mark.asyncio
    async def test_live_mode_calls_create_order(self):
        execution = self._make_execution(is_simulation=False)
        # Patch monitor_price to return immediately
        execution.api_manager.get_last_price = AsyncMock(return_value=59999.0)
        await execution.execute_order(
            'binance', 'BTC', 'USDT', 'buy', 1.0, 60000.0, monitor_order=False
        )
        execution.api_manager.create_order.assert_called_once()


# ---------------------------------------------------------------------------
# SonarftSearch — daily loss limit
# ---------------------------------------------------------------------------

class TestDailyLossLimit:

    def _make_search(self, max_daily_loss=100.0):
        from sonarft_search import SonarftSearch
        search = SonarftSearch.__new__(SonarftSearch)
        search.logger = MagicMock()
        search.max_daily_loss = max_daily_loss
        search.daily_loss_accumulated = 0.0
        return search

    def test_not_halted_initially(self):
        search = self._make_search(max_daily_loss=100.0)
        assert search.is_halted() is False

    def test_halted_after_loss_exceeds_limit(self):
        search = self._make_search(max_daily_loss=100.0)
        search.record_trade_result(-150.0)
        assert search.is_halted() is True

    def test_not_halted_when_limit_is_zero(self):
        """Zero means disabled."""
        search = self._make_search(max_daily_loss=0.0)
        search.record_trade_result(-999999.0)
        assert search.is_halted() is False

    def test_positive_profit_does_not_accumulate_loss(self):
        search = self._make_search(max_daily_loss=100.0)
        search.record_trade_result(50.0)
        assert search.daily_loss_accumulated == 0.0
        assert search.is_halted() is False

    def test_accumulates_multiple_losses(self):
        search = self._make_search(max_daily_loss=100.0)
        search.record_trade_result(-40.0)
        search.record_trade_result(-40.0)
        assert search.daily_loss_accumulated == 80.0
        assert search.is_halted() is False
        search.record_trade_result(-30.0)
        assert search.is_halted() is True
