"""
Unit tests for SonarftMath.calculate_trade and SonarftApiManager.get_weighted_prices.
These are the most financially critical functions in the codebase.
"""
import pytest
from unittest.mock import MagicMock
from sonarft_math import SonarftMath
from sonarft_api_manager import SonarftApiManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_math(buy_fee=0.001, sell_fee=0.001, precision=None):
    api = MagicMock()
    api.get_buy_fee.return_value = buy_fee
    api.get_sell_fee.return_value = sell_fee
    api.get_symbol_precision.return_value = precision
    return SonarftMath(api)


def price_list(exchange, bid, ask, last):
    return (exchange, bid, ask, last, 'BTC/USDT')


# ---------------------------------------------------------------------------
# calculate_trade — profitability
# ---------------------------------------------------------------------------

class TestCalculateTradeProfitability:

    def test_profitable_trade_returns_positive_profit(self):
        math = make_math()
        profit, pct, data = math.calculate_trade(
            60000.0, 60200.0,
            price_list('binance', 60000.0, 60010.0, 60005.0),
            price_list('okx',     59990.0, 60200.0, 60100.0),
            1.0, 'BTC', 'USDT'
        )
        assert profit > 0
        assert pct > 0

    def test_unprofitable_trade_below_fees_returns_negative(self):
        math = make_math()
        # Spread of $50 on $60000 = 0.083% — below combined fees of 0.2%
        profit, pct, data = math.calculate_trade(
            60000.0, 60050.0,
            price_list('binance', 60000.0, 60010.0, 60005.0),
            price_list('okx',     59990.0, 60050.0, 60020.0),
            1.0, 'BTC', 'USDT'
        )
        assert profit < 0
        assert pct < 0

    def test_profit_percentage_sign_matches_profit_sign(self):
        math = make_math()
        for sell_price in [60050.0, 60200.0, 60500.0]:
            profit, pct, data = math.calculate_trade(
                60000.0, sell_price,
                price_list('binance', 60000.0, 60010.0, 60005.0),
                price_list('okx',     59990.0, sell_price, sell_price),
                1.0, 'BTC', 'USDT'
            )
            if data is not None:
                assert (profit >= 0) == (pct >= 0), \
                    f"Sign mismatch: profit={profit}, pct={pct}"

    def test_break_even_spread_covers_combined_fees(self):
        """For Binance+OKX (0.1%+0.1%), break-even requires sell/buy > 1.002."""
        math = make_math(buy_fee=0.001, sell_fee=0.001)
        # Exactly at break-even: sell = buy * 1.002002
        buy = 60000.0
        sell = round(buy * 1.002002, 2)
        profit, pct, data = math.calculate_trade(
            buy, sell,
            price_list('binance', buy, buy + 10, buy + 5),
            price_list('okx',     buy - 10, sell, sell - 5),
            1.0, 'BTC', 'USDT'
        )
        # Should be approximately zero (within rounding)
        assert abs(profit) < 1.0, f"Expected near-zero profit at break-even, got {profit}"


# ---------------------------------------------------------------------------
# calculate_trade — fee inclusion
# ---------------------------------------------------------------------------

class TestCalculateTradeFees:

    def test_fees_deducted_before_profit(self):
        math = make_math(buy_fee=0.001, sell_fee=0.001)
        profit, pct, data = math.calculate_trade(
            60000.0, 60200.0,
            price_list('binance', 60000.0, 60010.0, 60005.0),
            price_list('okx',     59990.0, 60200.0, 60100.0),
            1.0, 'BTC', 'USDT'
        )
        assert data['buy_fee_quote'] > 0
        assert data['sell_fee_quote'] > 0
        # Verify: profit = net_sell - total_buy
        expected_profit = (data['sell_value'] - data['sell_fee_quote']) - \
                          (data['buy_value'] + data['buy_fee_quote'])
        assert abs(profit - expected_profit) < 1e-6

    def test_zero_fees_increases_profit(self):
        math_with_fees = make_math(buy_fee=0.001, sell_fee=0.001)
        math_no_fees   = make_math(buy_fee=0.0,   sell_fee=0.0)
        args = (
            60000.0, 60200.0,
            price_list('binance', 60000.0, 60010.0, 60005.0),
            price_list('okx',     59990.0, 60200.0, 60100.0),
            1.0, 'BTC', 'USDT'
        )
        profit_with, _, _ = math_with_fees.calculate_trade(*args)
        profit_no,   _, _ = math_no_fees.calculate_trade(*args)
        assert profit_no > profit_with

    def test_higher_fees_reduce_profit(self):
        math_low  = make_math(buy_fee=0.001, sell_fee=0.001)
        math_high = make_math(buy_fee=0.005, sell_fee=0.005)
        args = (
            60000.0, 60200.0,
            price_list('binance', 60000.0, 60010.0, 60005.0),
            price_list('okx',     59990.0, 60200.0, 60100.0),
            1.0, 'BTC', 'USDT'
        )
        profit_low,  _, _ = math_low.calculate_trade(*args)
        profit_high, _, _ = math_high.calculate_trade(*args)
        assert profit_low > profit_high


# ---------------------------------------------------------------------------
# calculate_trade — edge cases
# ---------------------------------------------------------------------------

class TestCalculateTradeEdgeCases:

    def test_zero_buy_price_returns_none_data(self):
        math = make_math()
        profit, pct, data = math.calculate_trade(
            0.0, 60200.0,
            price_list('binance', 0.0, 10.0, 5.0),
            price_list('okx',     0.0, 60200.0, 60100.0),
            1.0, 'BTC', 'USDT'
        )
        assert data is None

    def test_zero_amount_returns_none_data(self):
        math = make_math()
        profit, pct, data = math.calculate_trade(
            60000.0, 60200.0,
            price_list('binance', 60000.0, 60010.0, 60005.0),
            price_list('okx',     59990.0, 60200.0, 60100.0),
            0.0, 'BTC', 'USDT'
        )
        assert data is None

    def test_missing_fee_returns_zero_profit_none_data(self):
        api = MagicMock()
        api.get_buy_fee.return_value = None
        api.get_sell_fee.return_value = 0.001
        api.get_symbol_precision.return_value = None
        math = SonarftMath(api)
        profit, pct, data = math.calculate_trade(
            60000.0, 60200.0,
            price_list('binance', 60000.0, 60010.0, 60005.0),
            price_list('okx',     59990.0, 60200.0, 60100.0),
            1.0, 'BTC', 'USDT'
        )
        assert data is None

    def test_unknown_exchange_returns_none_data(self):
        math = make_math()
        profit, pct, data = math.calculate_trade(
            60000.0, 60200.0,
            price_list('unknown_exchange', 60000.0, 60010.0, 60005.0),
            price_list('okx',              59990.0, 60200.0, 60100.0),
            1.0, 'BTC', 'USDT'
        )
        assert data is None

    def test_same_exchange_calculates_correctly(self):
        """Same exchange is now guarded upstream, but math itself should still work."""
        math = make_math()
        profit, pct, data = math.calculate_trade(
            60000.0, 60200.0,
            price_list('binance', 60000.0, 60010.0, 60005.0),
            price_list('binance', 59990.0, 60200.0, 60100.0),
            1.0, 'BTC', 'USDT'
        )
        # Math is valid; the same-exchange guard lives in sonarft_search.py
        assert data is not None

    def test_trade_data_contains_required_keys(self):
        math = make_math()
        _, _, data = math.calculate_trade(
            60000.0, 60200.0,
            price_list('binance', 60000.0, 60010.0, 60005.0),
            price_list('okx',     59990.0, 60200.0, 60100.0),
            1.0, 'BTC', 'USDT'
        )
        required = {
            'buy_exchange', 'sell_exchange', 'base', 'quote',
            'buy_price', 'sell_price', 'buy_trade_amount', 'sell_trade_amount',
            'buy_fee_quote', 'sell_fee_quote', 'profit', 'profit_percentage',
        }
        assert required.issubset(data.keys())

    def test_trade_data_amounts_match(self):
        """Buy and sell amounts should be equal (sell uses the filled buy amount)."""
        math = make_math()
        _, _, data = math.calculate_trade(
            60000.0, 60200.0,
            price_list('binance', 60000.0, 60010.0, 60005.0),
            price_list('okx',     59990.0, 60200.0, 60100.0),
            1.0, 'BTC', 'USDT'
        )
        assert data['buy_trade_amount'] == data['sell_trade_amount']


# ---------------------------------------------------------------------------
# calculate_trade — precision
# ---------------------------------------------------------------------------

class TestCalculateTradePrecision:

    def test_decimal_precision_no_float_contamination(self):
        """Profit should be consistent regardless of minor float input variations."""
        math = make_math()
        _, pct1, _ = math.calculate_trade(
            60000.0, 60200.0,
            price_list('binance', 60000.0, 60010.0, 60005.0),
            price_list('okx',     59990.0, 60200.0, 60100.0),
            1.0, 'BTC', 'USDT'
        )
        _, pct2, _ = math.calculate_trade(
            60000.000000001, 60200.000000001,
            price_list('binance', 60000.0, 60010.0, 60005.0),
            price_list('okx',     59990.0, 60200.0, 60100.0),
            1.0, 'BTC', 'USDT'
        )
        # After rounding to exchange precision, results should be identical
        assert abs(pct1 - pct2) < 1e-6

    def test_live_precision_overrides_fallback(self):
        """When get_symbol_precision returns data, it should be used over EXCHANGE_RULES."""
        api = MagicMock()
        api.get_buy_fee.return_value = 0.001
        api.get_sell_fee.return_value = 0.001
        api.get_symbol_precision.return_value = {
            'prices_precision': 2,
            'buy_amount_precision': 8,
            'sell_amount_precision': 8,
            'cost_precision': 8,
            'fee_precision': 8,
        }
        math = SonarftMath(api)
        profit, pct, data = math.calculate_trade(
            60000.0, 60200.0,
            price_list('binance', 60000.0, 60010.0, 60005.0),
            price_list('okx',     59990.0, 60200.0, 60100.0),
            1.0, 'BTC', 'USDT'
        )
        assert data is not None
        assert profit > 0


# ---------------------------------------------------------------------------
# get_weighted_prices (VWAP)
# ---------------------------------------------------------------------------

class TestGetWeightedPrices:

    def _make_api(self):
        """Instantiate SonarftApiManager with a minimal stub to avoid ccxt import."""
        api = SonarftApiManager.__new__(SonarftApiManager)
        return api

    def test_correct_vwap_formula(self):
        api = self._make_api()
        order_book = {
            'bids': [[60000.0, 1.0], [59990.0, 2.0]],
            'asks': [[60010.0, 1.5], [60020.0, 0.5]],
        }
        bid_vwap, ask_vwap = api.get_weighted_prices(2, order_book)
        expected_bid = (60000.0 * 1.0 + 59990.0 * 2.0) / 3.0
        expected_ask = (60010.0 * 1.5 + 60020.0 * 0.5) / 2.0
        assert abs(bid_vwap - expected_bid) < 1e-9
        assert abs(ask_vwap - expected_ask) < 1e-9

    def test_zero_volume_returns_zero(self):
        api = self._make_api()
        order_book = {
            'bids': [[60000.0, 0.0]],
            'asks': [[60010.0, 0.0]],
        }
        bid_vwap, ask_vwap = api.get_weighted_prices(1, order_book)
        assert bid_vwap == 0.0
        assert ask_vwap == 0.0

    def test_empty_order_book_returns_zero(self):
        api = self._make_api()
        order_book = {'bids': [], 'asks': []}
        bid_vwap, ask_vwap = api.get_weighted_prices(5, order_book)
        assert bid_vwap == 0.0
        assert ask_vwap == 0.0

    def test_depth_clamped_to_available_levels(self):
        """Requesting depth=10 on a 2-level book should use only 2 levels."""
        api = self._make_api()
        order_book = {
            'bids': [[60000.0, 1.0], [59990.0, 1.0]],
            'asks': [[60010.0, 1.0], [60020.0, 1.0]],
        }
        bid_vwap_2,  ask_vwap_2  = api.get_weighted_prices(2,  order_book)
        bid_vwap_10, ask_vwap_10 = api.get_weighted_prices(10, order_book)
        assert bid_vwap_2 == bid_vwap_10
        assert ask_vwap_2 == ask_vwap_10

    def test_single_level_equals_that_price(self):
        api = self._make_api()
        order_book = {
            'bids': [[60000.0, 5.0]],
            'asks': [[60010.0, 3.0]],
        }
        bid_vwap, ask_vwap = api.get_weighted_prices(1, order_book)
        assert bid_vwap == 60000.0
        assert ask_vwap == 60010.0

    def test_higher_volume_levels_dominate_vwap(self):
        """A level with 10x volume should pull VWAP strongly toward its price."""
        api = self._make_api()
        order_book = {
            'bids': [[60000.0, 0.1], [59000.0, 10.0]],
            'asks': [[60010.0, 0.1], [61000.0, 10.0]],
        }
        bid_vwap, ask_vwap = api.get_weighted_prices(2, order_book)
        # VWAP should be much closer to the high-volume level
        assert bid_vwap < 59100.0   # pulled toward 59000
        assert ask_vwap > 60900.0   # pulled toward 61000
