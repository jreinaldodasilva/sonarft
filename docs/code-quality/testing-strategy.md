# SonarFT — Testing Strategy

**Review Date:** July 2025
**Codebase Version:** 1.0.0

---

## 1. Current Test Coverage

**⚠️ No test files found in the codebase.**

There are zero `test_*.py` files, no `pytest` or `unittest` imports, and no test infrastructure (`conftest.py`, `pytest.ini`, `setup.cfg` test config). The codebase has **0% automated test coverage**.

This is the most critical quality gap for a financial trading system.

---

## 2. Testability Assessment

### What Makes the Code Testable

| Feature | Present? | Notes |
|---|---|---|
| Dependency injection | ✅ Yes | All modules receive dependencies via constructor |
| No global mutable state (mostly) | ⚠️ Partial | `previous_spread`, `self.volatility` are shared state |
| External dependencies mockable | ✅ Yes | `SonarftApiManager` is the single exchange boundary |
| Deterministic logic | ⚠️ Partial | `random.randint` in botid and simulation order IDs |
| Pure functions | ✅ Some | `SonarftMath.calculate_trade`, `get_weighted_prices` are pure |
| Async-first | ✅ Yes | `pytest-asyncio` handles async test cases |

### What Hinders Testability

| Hindrance | Location | Impact |
|---|---|---|
| Sync file I/O in async methods | `sonarft_helpers.py`, `sonarft_server.py` | Requires temp files in tests |
| `argparse.parse_args()` reads `sys.argv` | `sonarft_manager.py:parse_args` | Must mock `sys.argv` in tests |
| Hardcoded file paths (`sonarftdata/`) | Multiple files | Requires working directory setup |
| `random.randint` in `create_botid` | `sonarft_bot.py:158` | Non-deterministic; seed for tests |
| `asyncio.get_event_loop()` (deprecated) | `sonarft_api_manager.py`, `sonarft_execution.py` | Use `asyncio.get_running_loop()` |
| Shared instance state (`previous_spread`) | `sonarft_indicators.py` | Tests interfere with each other |

---

## 3. High-Risk Untested Code

### Priority 1 — Financial Calculations (MUST TEST)

| Function | File | Risk if Wrong |
|---|---|---|
| `calculate_trade` | `sonarft_math.py` | Incorrect profit/fee → wrong trade decisions |
| `get_weighted_prices` | `sonarft_api_manager.py` | Wrong VWAP → wrong entry prices |
| `get_weighted_price` | `sonarft_prices.py` | Wrong price blending → wrong adjusted prices |
| `weighted_adjust_prices` | `sonarft_prices.py` | Wrong spread factors → systematic profit loss |
| `verify_spread_threshold` | `sonarft_validators.py` | Wrong threshold → all trades blocked or all accepted |
| `calculate_thresholds_based_on_historical_data` | `sonarft_validators.py` | NaN thresholds → silent trade blocking |

### Priority 2 — Safety Gates (MUST TEST)

| Function | File | Risk if Wrong |
|---|---|---|
| `_validate_parameters` | `sonarft_bot.py` | Invalid config accepted → unsafe trading |
| `check_balance` | `sonarft_execution.py` | Balance not checked → over-trading |
| `is_halted` | `sonarft_search.py` | Loss limit not enforced |
| Simulation mode gate | `sonarft_execution.py:259` | Real orders in simulation mode |
| `_validate_id` | `sonarft_server.py` | Path traversal accepted |

### Priority 3 — Async Operations (SHOULD TEST)

| Function | File | Risk if Wrong |
|---|---|---|
| `run_bot` circuit breaker | `sonarft_bot.py` | Bot doesn't stop on repeated failures |
| `monitor_order` timeout | `sonarft_execution.py` | Order monitoring never times out |
| `search_trades` exception handling | `sonarft_search.py` | One symbol failure crashes all symbols |
| `BotManager` lock behavior | `sonarft_manager.py` | Race condition on concurrent bot creation |

### Priority 4 — Indicator Correctness (SHOULD TEST)

| Function | File | Risk if Wrong |
|---|---|---|
| `get_rsi` | `sonarft_indicators.py` | Wrong RSI → wrong spread direction |
| `get_stoch_rsi` | `sonarft_indicators.py` | Parameter mismatch already found |
| `get_market_direction` | `sonarft_indicators.py` | Wrong direction → wrong position |
| `get_short_term_market_trend` | `sonarft_indicators.py` | NameError on zero prices |

---

## 4. Recommended Test Suite

### Unit Tests

#### `test_sonarft_math.py`
```python
import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from sonarft_math import SonarftMath

@pytest.fixture
def math(mock_api_manager):
    api = MagicMock()
    api.get_buy_fee.return_value = 0.001
    api.get_sell_fee.return_value = 0.001
    api.get_symbol_precision.return_value = None
    return SonarftMath(api)

def test_profitable_trade(math):
    profit, pct, data = math.calculate_trade(
        60000.0, 60200.0,
        ('binance', 60000.0, 60000.0, 60000.0, 'BTC/USDT'),
        ('binance', 60200.0, 60200.0, 60200.0, 'BTC/USDT'),
        1.0, 'BTC', 'USDT'
    )
    assert profit > 0
    assert pct > 0.001  # above combined fees

def test_unprofitable_trade_below_fees(math):
    profit, pct, data = math.calculate_trade(
        60000.0, 60050.0, ...)  # spread < combined fees
    assert profit < 0

def test_zero_buy_price_returns_none(math):
    profit, pct, data = math.calculate_trade(0.0, 60200.0, ...)
    assert data is None

def test_fee_included_before_threshold(math):
    # Verify fees are deducted before profit_pct is returned
    _, pct, data = math.calculate_trade(60000.0, 60200.0, ...)
    assert data['buy_fee_quote'] > 0
    assert data['sell_fee_quote'] > 0
```

#### `test_sonarft_api_manager.py`
```python
def test_vwap_correct_formula():
    order_book = {
        'bids': [[60000, 1.0], [59990, 2.0]],
        'asks': [[60010, 1.5], [60020, 0.5]]
    }
    bid_vwap, ask_vwap = SonarftApiManager.get_weighted_prices(None, 2, order_book)
    expected_bid = (60000*1.0 + 59990*2.0) / 3.0
    assert abs(bid_vwap - expected_bid) < 0.001

def test_vwap_zero_volume_returns_zero():
    order_book = {'bids': [[60000, 0]], 'asks': [[60010, 0]]}
    bid, ask = SonarftApiManager.get_weighted_prices(None, 1, order_book)
    assert bid == 0.0 and ask == 0.0
```

#### `test_sonarft_validators.py`
```python
def test_medium_volatility_threshold_not_divided_by_100():
    # Regression test for the /100 bug
    thresholds = validator.calculate_thresholds_based_on_historical_data(
        historical_buy, historical_sell
    )
    assert thresholds['medium'] > thresholds['low'] * 0.5  # not 100x smaller

def test_empty_historical_data_returns_defaults():
    thresholds = validator.calculate_thresholds_based_on_historical_data([], [])
    assert not any(v != v for v in thresholds.values())  # no NaN
```

#### `test_sonarft_bot.py`
```python
def test_validate_parameters_rejects_zero_trade_amount():
    bot = SonarftBot('ccxtpro')
    bot.trade_amount = 0
    with pytest.raises(ValueError):
        bot._validate_parameters()

def test_validate_parameters_rejects_live_mode_flag():
    bot = SonarftBot('ccxtpro')
    bot.is_simulating_trade = 2
    with pytest.raises(ValueError):
        bot._validate_parameters()
```

### Integration Tests

#### `test_simulation_mode.py`
```python
@pytest.mark.asyncio
async def test_simulation_never_calls_create_order():
    api_mock = MagicMock()
    execution = SonarftExecution(api_mock, helpers_mock, indicators_mock, is_simulation_mode=True)
    await execution.execute_trade(botid=1, trade=sample_trade)
    api_mock.create_order.assert_not_called()

@pytest.mark.asyncio
async def test_simulation_returns_synthetic_order_id():
    result = await execution.execute_order(..., is_simulation=True)
    order_id, executed, remaining = result
    assert 'buy_' in order_id or 'sell_' in order_id
    assert executed == trade_amount
    assert remaining == 0
```

#### `test_circuit_breaker.py`
```python
@pytest.mark.asyncio
async def test_bot_stops_after_5_failures():
    bot = SonarftBot('ccxtpro')
    bot.sonarft_search = MagicMock()
    bot.sonarft_search.search_trades.side_effect = Exception("API error")
    await bot.run_bot()
    assert bot._stop_event.is_set()
    assert bot.sonarft_search.search_trades.call_count == 5
```

### Property-Based Tests

```python
from hypothesis import given, strategies as st

@given(
    buy_price=st.floats(min_value=0.01, max_value=1_000_000),
    sell_price=st.floats(min_value=0.01, max_value=1_000_000),
    amount=st.floats(min_value=0.00001, max_value=1000),
)
def test_calculate_trade_profit_sign_consistent(math, buy_price, sell_price, amount):
    profit, pct, data = math.calculate_trade(buy_price, sell_price, ...)
    if data is not None:
        assert (profit >= 0) == (pct >= 0)  # sign must be consistent
        assert (sell_price > buy_price * 1.002) == (profit > 0)  # profitable iff spread > fees
```

---

## 5. Test Infrastructure Setup

### `requirements-test.txt`
```
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-mock==3.11.0
hypothesis==6.82.0
aioresponses==0.7.4
```

### `conftest.py`
```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_api_manager():
    api = MagicMock()
    api.get_order_book = AsyncMock(return_value={
        'bids': [[60000, 1.0], [59990, 2.0]],
        'asks': [[60010, 1.5], [60020, 0.5]]
    })
    api.get_ohlcv_history = AsyncMock(return_value=[
        [1000000 + i*60000, 100+i, 105+i, 95+i, 100+i, 10.0]
        for i in range(50)
    ])
    api.get_buy_fee = MagicMock(return_value=0.001)
    api.get_sell_fee = MagicMock(return_value=0.001)
    api.get_symbol_precision = MagicMock(return_value=None)
    return api

@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
```

---

## 6. Test Coverage Targets

| Module | Current | Target | Priority |
|---|---|---|---|
| `sonarft_math.py` | 0% | 95% | P1 — financial critical |
| `sonarft_api_manager.py` (VWAP) | 0% | 90% | P1 — financial critical |
| `sonarft_validators.py` | 0% | 85% | P1 — safety gates |
| `sonarft_bot.py` (`_validate_parameters`) | 0% | 90% | P1 — safety gates |
| `sonarft_execution.py` (simulation gate) | 0% | 90% | P1 — safety critical |
| `sonarft_indicators.py` | 0% | 75% | P2 — signal correctness |
| `sonarft_prices.py` | 0% | 75% | P2 — price logic |
| `sonarft_search.py` | 0% | 70% | P2 — trade pipeline |
| `sonarft_server.py` | 0% | 60% | P3 — API layer |
| `sonarft_helpers.py` | 0% | 70% | P3 — persistence |

---

*Generated as part of the SonarFT code review suite — Prompt 10 (2/3): Testing Strategy*
