# SonarFT — Code Quality Review

**Review Date:** July 2025
**Codebase Version:** 1.0.0

---

## 1. Naming Consistency Audit

### Strengths
- Classes: `PascalCase` throughout (`SonarftBot`, `BotManager`, `TradeProcessor`) ✅
- Methods: `snake_case` throughout (`create_bot`, `load_configurations`, `get_rsi`) ✅
- Constants: `UPPER_SNAKE_CASE` (`LOW_VOLATILITY_THRESHOLD`, `EXCHANGE_RULES`) ✅
- Market direction strings: consistently `'bull'`, `'bear'`, `'neutral'` ✅
- Symbol format: consistently `f"{base}/{quote}"` ✅

### Issues

| Issue | Location | Severity |
|---|---|---|
| `InitializeModules` uses PascalCase (should be `initialize_modules`) | `sonarft_bot.py:295` | Low |
| `setAPIKeys` uses camelCase (should be `set_api_keys`) | `sonarft_bot.py:135`, `sonarft_api_manager.py:100` | Low |
| `_execute_single_trade` — "single" is redundant | `sonarft_execution.py:43` | Low |
| `market_animal_buy/sell` — unclear name for a direction string | `sonarft_prices.py:72` | Low |
| `result_01`, `result_02` — numeric suffixes instead of descriptive names | `sonarft_search.py:36` | Low |
| `d()` — single-letter helper function name in `calculate_trade` | `sonarft_math.py:74` | Low |
| `previous_avg_price` vs `previous_avg` — inconsistent naming in same function | `sonarft_indicators.py:161` | Medium |

---

## 2. Module Documentation

| File | Module Docstring | Class Docstring | Method Docstrings | Quality |
|---|---|---|---|---|
| `sonarft.py` | ✅ | N/A | ✅ | Good |
| `sonarft_server.py` | ✅ | ✅ | ✅ Most | Good |
| `sonarft_manager.py` | ✅ | ✅ | ✅ Most | Good |
| `sonarft_bot.py` | ✅ | ⚠️ Empty `""" """` | ✅ Most | Medium |
| `sonarft_search.py` | ✅ | ⚠️ Empty on TradeValidator/Executor | ⚠️ Sparse | Medium |
| `sonarft_prices.py` | ✅ | ❌ Missing | ⚠️ Sparse | Low |
| `sonarft_indicators.py` | ❌ Missing | ❌ Missing | ✅ Most | Low |
| `sonarft_math.py` | ✅ | ✅ | ✅ | Good |
| `sonarft_execution.py` | ❌ Missing | ✅ | ✅ Most | Medium |
| `sonarft_validators.py` | ❌ Missing | ❌ Missing | ⚠️ Sparse | Low |
| `sonarft_api_manager.py` | ❌ Missing | ✅ | ✅ Most | Medium |
| `sonarft_helpers.py` | ❌ Missing | ✅ | ✅ Most | Medium |

**4 of 12 files missing module-level docstrings** (`sonarft_indicators.py`, `sonarft_execution.py`, `sonarft_validators.py`, `sonarft_api_manager.py`, `sonarft_helpers.py`).

---

## 3. Type Annotations

### Coverage Assessment

| File | Param Types | Return Types | Coverage |
|---|---|---|---|
| `sonarft_api_manager.py` | ✅ High | ✅ High | ~85% |
| `sonarft_math.py` | ✅ High | ✅ High | ~90% |
| `sonarft_helpers.py` | ✅ Medium | ⚠️ Low | ~60% |
| `sonarft_indicators.py` | ⚠️ Low | ⚠️ Low | ~30% |
| `sonarft_prices.py` | ✅ Medium | ✅ Medium | ~65% |
| `sonarft_execution.py` | ✅ Medium | ✅ Medium | ~65% |
| `sonarft_validators.py` | ✅ Medium | ✅ Medium | ~70% |
| `sonarft_search.py` | ⚠️ Low | ⚠️ Low | ~35% |
| `sonarft_bot.py` | ✅ Medium | ⚠️ Low | ~50% |
| `sonarft_server.py` | ✅ Medium | ⚠️ Low | ~50% |

**Notable gaps:**
- `sonarft_indicators.py` — most async methods have no type hints on parameters or return values
- `sonarft_search.py` — `TradeValidator`, `TradeExecutor`, `TradeProcessor` methods largely unannotated
- Return type `None` vs `Optional[X]` inconsistently used when functions can return `None`

---

## 4. Code Size & Complexity

### Large Files (> 300 lines)

| File | Lines | Functions | Avg Lines/Function |
|---|---|---|---|
| `sonarft_server.py` | 485 | 34 | ~14 |
| `sonarft_indicators.py` | 420 | 24 | ~17 |
| `sonarft_bot.py` | 354 | 15 | ~24 |
| `sonarft_execution.py` | 345 | 11 | ~31 |
| `sonarft_api_manager.py` | 333 | 26 | ~13 |
| `sonarft_search.py` | 316 | 16 | ~20 |

### Large Functions (> 50 lines)

| Function | File | Approx Lines | Complexity Driver |
|---|---|---|---|
| `weighted_adjust_prices` | `sonarft_prices.py` | ~140 | 16 parallel calls + multi-signal adjustment |
| `_execute_single_trade` | `sonarft_execution.py` | ~80 | LONG/SHORT branching + indicator fallback |
| `setup_http_endpoints` | `sonarft_server.py` | ~130 | 9 endpoint definitions inline |
| `load_configurations` | `sonarft_bot.py` | ~35 | 6 sequential config loads |
| `process_trade_combination` | `sonarft_search.py` | ~65 | Full pipeline in one function |
| `get_trade_dynamic_spread_threshold_avg` | `sonarft_validators.py` | ~50 | Nested loops + threshold logic |

### High Cyclomatic Complexity

| Function | Branches | Risk |
|---|---|---|
| `weighted_adjust_prices` | ~12 (bull/bear × RSI × StochRSI) | High |
| `_execute_single_trade` | ~8 (direction × position × fallback) | High |
| `verify_spread_threshold` | ~6 (volatility × threshold) | Medium |
| `run_bot` | ~6 (failure count × stop event) | Medium |

---

## 5. Duplication Audit

### Pattern 1 — Config Loaders (5 near-identical functions)

`sonarft_bot.py` contains 5 loader functions (`load_markets`, `load_parameters`, `load_symbols`, `load_exchanges`, `load_fees`) that all follow the same pattern:

```python
def load_X(self, pathname: str, setup: str):
    self.logger.info("Loading X...")
    key = f"X_{setup}"
    with open(pathname, "r") as f:
        data = json.load(f)[key]
    return data
```

These could be consolidated into a single generic loader:
```python
def _load_config(self, pathname: str, key: str):
    with open(pathname, "r") as f:
        return json.load(f)[key]
```

### Pattern 2 — HTTP Endpoint Error Handling (9 identical try/except blocks)

Every HTTP endpoint in `sonarft_server.py` repeats:
```python
except FileNotFoundError as exc:
    raise HTTPException(status_code=404, detail="File not found") from exc
except Exception as error:
    raise HTTPException(status_code=500, detail=str(error)) from error
```

This could be a decorator or context manager.

### Pattern 3 — API Wrapper Methods (8 identical thin wrappers)

`SonarftIndicators` and `SonarftValidators` both define identical thin wrappers:
```python
async def get_order_book(self, exchange_id, base, quote):
    return await self.api_manager.get_order_book(exchange_id, base, quote)

async def get_history(self, exchange_id, base, quote, timeframe, limit):
    return await self.api_manager.get_ohlcv_history(...)
```

These could be eliminated by passing `api_manager` calls directly, or extracted to a shared mixin.

### Pattern 4 — Indicator Parameter Blocks (duplicated in prices and execution)

Both `sonarft_prices.py` and `sonarft_execution.py` define identical local variables:
```python
period = 14
rsi_period = 14
stoch_period = 14
k_period = 3
d_period = 3
```

These should be module-level constants or config-driven.

---

## 6. Error Handling Consistency

### Strengths
- All async methods wrap in `try/except Exception` ✅
- `None` returned on failure (fail-safe pattern) ✅
- Custom exception classes for domain errors (`BotCreationError`, `BotRunError`) ✅
- HTTP endpoints separate `FileNotFoundError` (404) from generic (500) ✅

### Inconsistencies

| Issue | Location | Severity |
|---|---|---|
| `BotCreationError` defined in both `sonarft_manager.py` and `sonarft_bot.py` | Both files | Medium |
| `get_market_direction` returns `'neutral'` on NaN instead of `None` | `sonarft_indicators.py:125` | Medium |
| `get_price_change` has no try/except (unlike all other indicator methods) | `sonarft_indicators.py:201` | Medium |
| `get_atr`, `get_24h_high/low` have no try/except | `sonarft_indicators.py:266,279,291` | Medium |
| Error logged as `str(e)` with no context (exchange, symbol, operation) | Multiple files | Medium |
| `setup_error_handlings` defined but never called | `sonarft_server.py` | Low |

---

## 7. Logging Consistency

### Level Usage

| Level | Used For | Appropriate? |
|---|---|---|
| `INFO` | Bot lifecycle, trade search, order placement, indicator values | ⚠️ Too verbose for production |
| `WARNING` | Validation failures, NaN indicators, insufficient data | ✅ |
| `ERROR` | Exception catches, API failures | ✅ |
| `DEBUG` | Not used anywhere | ⚠️ Missing debug level |

**Issue — no DEBUG level logging:**
All operational messages use `INFO`. In production, this creates extremely verbose logs. A `DEBUG` level for indicator values and price calculations would allow operators to reduce log verbosity without losing error visibility.

**Issue — indicator values logged at INFO:**
```python
# sonarft_prices.py:143-146
self.logger.info(f"RSI buy={market_rsi_buy:.2f} sell={market_rsi_sell:.2f}")
self.logger.info(f"Direction buy={market_direction_buy} ...")
self.logger.info(f"StochRSI buy_k={market_stoch_rsi_buy_k:.2f} ...")
self.logger.info(f"Support={support_price} resistance={resistance_price}")
```
These 4 log lines fire on every trade cycle per symbol — at 2 symbols × every 6–18 seconds, this generates ~20–40 log lines per minute of pure indicator data. Should be `DEBUG`.

---

## 8. Code Quality Scorecard

| Aspect | Score (1–10) | Assessment |
|---|---|---|
| Readability | 7 | Clean structure, good naming; large functions reduce clarity |
| Documentation | 6 | Good docstrings on most public methods; missing module docstrings; empty class docstrings |
| Type safety | 5 | Inconsistent coverage; `sonarft_indicators.py` largely unannotated |
| Error handling | 6 | Consistent fail-safe pattern; inconsistent exception types; no context in error messages |
| Testability | 4 | Good DI pattern; no tests exist; global state in indicators/validators hinders unit testing |
| Performance awareness | 5 | OHLCV caching present; double rate limiting; redundant order book fetches |
| Security awareness | 6 | Path traversal protection; auth on endpoints; `acme.json` not gitignored |
| Standards adherence | 7 | Follows project conventions; two camelCase methods; duplicate exception class |
| **Overall** | **5.75** | **Solid foundation; significant gaps in testing and type safety** |

---

*Generated as part of the SonarFT code review suite — Prompt 10 (1/3): Code Quality*
