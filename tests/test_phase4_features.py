"""
Additional tests for Phase 4 features:
- SonarftHelpers SQLite persistence
- SonarftBot parameter hot-reload
- Emergency stop endpoint
"""
import pytest
import asyncio
import os
import tempfile
from unittest.mock import MagicMock, AsyncMock, patch


# ---------------------------------------------------------------------------
# SonarftHelpers — SQLite persistence
# ---------------------------------------------------------------------------

class TestSonarftHelpersSQLite:

    def _make_helpers(self, tmp_path):
        from sonarft_helpers import SonarftHelpers, Trade
        # Point DB to a temp file so tests don't pollute sonarftdata/
        SonarftHelpers._DB_PATH = str(tmp_path / "test.db")
        helpers = SonarftHelpers(is_simulation_mode=True)
        return helpers, Trade

    @pytest.mark.asyncio
    async def test_save_and_retrieve_order(self, tmp_path):
        helpers, Trade = self._make_helpers(tmp_path)
        trade = Trade(
            position='', base='BTC', quote='USDT',
            buy_exchange='binance', sell_exchange='okx',
            buy_price=60000.0, sell_price=60200.0,
            buy_trade_amount=1.0, sell_trade_amount=1.0,
            executed_amount=1.0, buy_value=60000.0, sell_value=60200.0,
            buy_fee_rate=0.001, sell_fee_rate=0.001,
            buy_fee_base=0.0, buy_fee_quote=60.0, sell_fee_quote=60.2,
            profit=79.8, profit_percentage=0.00133,
        )
        await helpers.save_order_history(botid=12345, trade=trade, trade_position='LONG')
        orders = await helpers.get_orders(12345)
        assert len(orders) == 1
        assert orders[0]['base'] == 'BTC'
        assert orders[0]['position'] == 'LONG'

    @pytest.mark.asyncio
    async def test_save_and_retrieve_trade(self, tmp_path):
        helpers, Trade = self._make_helpers(tmp_path)
        trade = Trade(
            position='', base='ETH', quote='USDT',
            buy_exchange='binance', sell_exchange='okx',
            buy_price=3000.0, sell_price=3020.0,
            buy_trade_amount=1.0, sell_trade_amount=1.0,
            executed_amount=1.0, buy_value=3000.0, sell_value=3020.0,
            buy_fee_rate=0.001, sell_fee_rate=0.001,
            buy_fee_base=0.0, buy_fee_quote=3.0, sell_fee_quote=3.02,
            profit=13.98, profit_percentage=0.00466,
        )
        await helpers.save_trade_history(
            botid=12345, trade=trade,
            buy_order_id='buy_001', sell_order_id='sell_001',
            trade_position='LONG',
            order_buy_success=True, order_sell_success=True, trade_success=True
        )
        trades = await helpers.get_trades(12345)
        assert len(trades) == 1
        assert trades[0]['base'] == 'ETH'
        assert trades[0]['trade_success'] is True

    @pytest.mark.asyncio
    async def test_multiple_bots_isolated(self, tmp_path):
        helpers, Trade = self._make_helpers(tmp_path)
        trade = Trade(
            position='', base='BTC', quote='USDT',
            buy_exchange='binance', sell_exchange='okx',
            buy_price=60000.0, sell_price=60200.0,
            buy_trade_amount=1.0, sell_trade_amount=1.0,
            executed_amount=1.0, buy_value=60000.0, sell_value=60200.0,
            buy_fee_rate=0.001, sell_fee_rate=0.001,
            buy_fee_base=0.0, buy_fee_quote=60.0, sell_fee_quote=60.2,
            profit=79.8, profit_percentage=0.00133,
        )
        await helpers.save_order_history(botid=111, trade=trade, trade_position='LONG')
        await helpers.save_order_history(botid=222, trade=trade, trade_position='SHORT')

        orders_111 = await helpers.get_orders(111)
        orders_222 = await helpers.get_orders(222)
        assert len(orders_111) == 1
        assert len(orders_222) == 1
        assert orders_111[0]['position'] == 'LONG'
        assert orders_222[0]['position'] == 'SHORT'

    @pytest.mark.asyncio
    async def test_empty_botid_returns_empty_list(self, tmp_path):
        helpers, _ = self._make_helpers(tmp_path)
        orders = await helpers.get_orders(99999)
        assert orders == []


# ---------------------------------------------------------------------------
# SonarftBot — parameter hot-reload
# ---------------------------------------------------------------------------

class TestHotReload:

    def _make_bot(self):
        from sonarft_bot import SonarftBot
        bot = SonarftBot.__new__(SonarftBot)
        bot.logger = MagicMock()
        bot.botid = 1
        bot.profit_percentage_threshold = 0.003
        bot.trade_amount = 1.0
        bot.is_simulating_trade = 1
        bot.max_daily_loss = 100.0
        bot.max_trade_amount = 0.0
        bot.max_orders_per_minute = 0
        bot.sonarft_search = None
        bot.sonarft_execution = None
        return bot

    def test_apply_parameters_updates_threshold(self):
        bot = self._make_bot()
        bot.apply_parameters({'profit_percentage_threshold': 0.005})
        assert bot.profit_percentage_threshold == 0.005

    def test_apply_parameters_updates_trade_amount(self):
        bot = self._make_bot()
        bot.apply_parameters({'trade_amount': 2.0})
        assert bot.trade_amount == 2.0

    def test_apply_parameters_updates_simulation_mode(self):
        bot = self._make_bot()
        bot.apply_parameters({'is_simulating_trade': 0})
        assert bot.is_simulating_trade == 0

    def test_apply_parameters_updates_max_daily_loss(self):
        bot = self._make_bot()
        bot.apply_parameters({'max_daily_loss': 500.0})
        assert bot.max_daily_loss == 500.0

    def test_apply_parameters_propagates_to_search(self):
        bot = self._make_bot()
        search = MagicMock()
        search.trade_amount = 1.0
        search.profit_percentage_threshold = 0.003
        search.max_daily_loss = 100.0
        bot.sonarft_search = search
        bot.apply_parameters({'trade_amount': 3.0, 'profit_percentage_threshold': 0.01})
        assert search.trade_amount == 3.0
        assert search.profit_percentage_threshold == 0.01

    def test_apply_parameters_propagates_to_execution(self):
        bot = self._make_bot()
        execution = MagicMock()
        execution.is_simulation_mode = True
        execution.max_trade_amount = 0.0
        execution.max_orders_per_minute = 0
        bot.sonarft_execution = execution
        bot.apply_parameters({'is_simulating_trade': 0, 'max_trade_amount': 5.0})
        assert execution.is_simulation_mode is False
        assert execution.max_trade_amount == 5.0

    def test_apply_parameters_ignores_unknown_keys(self):
        bot = self._make_bot()
        # Should not raise
        bot.apply_parameters({'unknown_key': 'value', 'profit_percentage_threshold': 0.004})
        assert bot.profit_percentage_threshold == 0.004


# ---------------------------------------------------------------------------
# SonarftSearch — same-exchange guard
# ---------------------------------------------------------------------------

class TestSameExchangeGuard:

    @pytest.mark.asyncio
    async def test_same_exchange_combination_skipped(self):
        """process_symbol must skip buy==sell exchange combinations."""
        from sonarft_search import TradeProcessor
        from unittest.mock import AsyncMock, MagicMock, patch

        processor = TradeProcessor.__new__(TradeProcessor)
        processor.logger = MagicMock()
        processor.sonarft_math = MagicMock()
        processor.sonarft_prices = MagicMock()
        processor.sonarft_prices.get_the_latest_prices = AsyncMock(return_value=(
            [('binance', 60000.0, 60010.0, 60005.0, 'BTC/USDT')],
            [('binance', 59990.0, 60200.0, 60100.0, 'BTC/USDT')],  # same exchange
        ))
        processor.trade_validator = MagicMock()
        processor.trade_executor = MagicMock()
        processor.process_trade_combination = AsyncMock()

        symbol = {'base': 'BTC', 'quotes': ['USDT']}
        await processor.process_symbol(botid=1, symbol=symbol, trade_amount=1.0, percentage_threshold=0.003)

        # process_trade_combination should NOT be called for same-exchange pair
        processor.process_trade_combination.assert_not_called()
