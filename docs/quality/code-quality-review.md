# SonarFT — Code Quality, Testing & Refactoring Review

## 1. Code Quality Scorecard

| Dimension | Score | Notes |
|---|---|---|
| Naming consistency | 7/10 | snake_case throughout; one PascalCase method (`InitializeModules`); typos: `trade_sucess`, `sell_order_sucess`, `buy_order_sucess` |
| Module docstrings | 4/10 | `sonarft_search.py` has an empty module docstring `""" """`; `sonarft_prices.py` has no module docstring; others are minimal |
| Type annotations | 6/10 | Public methods annotated; internal helpers often missing return types; `SonarftBot.__init__` missing annotations |
| Function size | 6/10 | `weighted_adjust_prices` is ~130 lines; `_execute_single_trade` is ~80 lines — both should be decomposed |
| Duplication | 5/10 | `save_botid` duplicated in `SonarftBot` and `SonarftHelpers`; OHLCV wrapper methods duplicated across `SonarftIndicators`, `SonarftPrices`, `SonarftValidators` |
| Logging consistency | 6/10 | Mix of `self.logger` and `print()` — 8 `print()` calls in production code |
| Error handling | 5/10 | Broad `except Exception` everywhere; errors swallowed silently; `None` returns not consistently checked by callers |
| Dead code | 4/10 | Large commented-out blocks in `sonarft_prices.py`; unused `t = round(time.time())` in `create_botid`; unreachable loop body in `monitor_trade_tasks` |
| Test coverage | 0/10 | No test files exist anywhere in the project |
| Docstring quality | 5/10 | Many docstrings present but several are empty (`""" """`); parameter descriptions often missing types |

---

## 2. Confirmed Code Issues

### Typos in Variable Names

**File:** `sonarft_execution.py`

```python
buy_order_sucess = False      # should be: buy_order_success
sell_order_sucess = False     # should be: sell_order_success
trade_sucess = False          # should be: trade_success (also referenced before assignment)
```

These typos propagate through return values and are used in `save_trade_history` calls.

---

### `print()` in Production Code

| File | Line context |
|---|---|
| `sonarft_server.py` | `print(f"client: {client_id} - Botid: {botid} - Action: {action}")` |
| `sonarft_server.py` | `print(f"Task {task} has been created")` |
| `sonarft_server.py` | `print(f"Client: {client_id} has been disconnected")` |
| `sonarft_server.py` | `print(f"Task {task} has been removed")` (×2) |
| `sonarft_manager.py` | `print(f"Running {sonarftbot} - {botid}")` |
| `sonarft_manager.py` | `print(f"Removing {sonarftbot} - {botid}")` |
| `sonarft_api_manager.py` | `print(f"Error calling method {method}: {e}")` |
| `sonarft_api_manager.py` | `print("")` (×2 — empty prints) |

All should be replaced with `self.logger.info/warning/error`.

---

### Dead Code

| Location | Dead Code |
|---|---|
| `sonarft_bot.py:create_botid` | `t = round(time.time())` — assigned, never used |
| `sonarft_search.py:monitor_trade_tasks` | Inner `if task.done()` block — unreachable after list comprehension filter |
| `sonarft_prices.py:weighted_adjust_prices` | Large `"""" ... """` block (bull/bear mixed conditions) — commented out with triple-quote string |
| `sonarft_helpers.py:save_order_history` | `if self.is_simulation_mode: pathname = ...` and `else: pathname = ...` — both branches produce identical `pathname` |
| `sonarft_helpers.py:save_trade_history` | Same as above |
| `sonarft_server.py` | `setup_error_handlings` method defined but never called |

---

### `getcontext().prec = 8` — Unused

Set in 9 files, never used. All arithmetic uses native `float`. Either remove the imports or actually use `Decimal` for financial calculations.

---

## 3. Testing Gaps Table

| Module | Testable? | Key Test Cases Needed |
|---|---|---|
| `sonarft_math.py` | High | Zero buy price, unknown exchange, fee rate None, profit calculation accuracy |
| `sonarft_indicators.py` | High | NaN RSI return, empty OHLCV, zero previous_avg_price, market_movement direction bug |
| `sonarft_prices.py` | Medium | weight < 0 scenario, None RSI crash, support/resistance None crash |
| `sonarft_validators.py` | Medium | Empty order book, hardcoded /100 divisor, spread threshold logic |
| `sonarft_execution.py` | Medium | None result_buy_order unpack, simulation mode skips monitor_price, partial fill |
| `sonarft_api_manager.py` | Low (requires exchange mock) | VWAP zero volume, exchange not found, ccxt blocking path |
| `sonarft_manager.py` | High | Re-entrant lock deadlock, bot not found, concurrent create/remove |
| `sonarft_server.py` | Medium | Path traversal via client_id, CORS headers, WebSocket disconnect handling |
| `sonarft_bot.py` | Medium | Config key order dependency, missing config key, stop_bot deadlock |
| `sonarft_helpers.py` | High | File not found on read, concurrent write, simulation vs real pathname |

---

## 4. Refactoring Roadmap

### Phase 1 — Safety (do first)

| Task | File | Effort |
|---|---|---|
| Fix `calculate_trade` return value mismatch (3 vs 4 values) | `sonarft_math.py` | 1h |
| Add None guards for all indicator returns before arithmetic | `sonarft_prices.py`, `sonarft_execution.py` | 2h |
| Fix `handle_trade_results` None unpack crash | `sonarft_execution.py` | 1h |
| Fix `market_movement` direction assignment bug (`else: "bear"`) | `sonarft_indicators.py` | 15m |
| Fix re-entrant lock deadlock in `set_update`/`get_update` | `sonarft_manager.py` | 1h |
| Add `client_id` / `botid` path sanitisation | `sonarft_server.py` | 1h |

### Phase 2 — Correctness

| Task | File | Effort |
|---|---|---|
| Replace `tuple(parameters.values())` with key-based extraction | `sonarft_bot.py` | 30m |
| Fix `get_short_term_market_trend` threshold unit mismatch | `sonarft_indicators.py` | 15m |
| Fix hardcoded `/100` divisor in spread threshold | `sonarft_validators.py` | 30m |
| Clamp `weight` to `[0, 1]` | `sonarft_prices.py` | 15m |
| Add zero-division guards to VWAP and profit percentage | `sonarft_api_manager.py`, `sonarft_math.py` | 1h |
| Fix MACD column name hardcoding | `sonarft_indicators.py` | 30m |
| Skip `monitor_price` in simulation mode | `sonarft_execution.py` | 30m |

### Phase 3 — Quality

| Task | File | Effort |
|---|---|---|
| Replace all `print()` with `self.logger` | All files | 1h |
| Remove dead code (unused `t`, unreachable loop, duplicate pathname branches) | Multiple | 1h |
| Remove or use `getcontext` imports | All files | 30m |
| Fix typos: `sucess` → `success` | `sonarft_execution.py` | 15m |
| Add module docstrings to `sonarft_search.py` and `sonarft_prices.py` | Both | 30m |
| Decompose `weighted_adjust_prices` into sub-methods | `sonarft_prices.py` | 3h |
| Consolidate OHLCV/order book wrapper methods into `SonarftApiManager` only | Multiple | 2h |

### Phase 4 — Testing

| Task | Effort |
|---|---|
| Unit tests for `SonarftMath.calculate_trade` | 2h |
| Unit tests for all indicator functions with mock OHLCV data | 4h |
| Integration tests for `TradeProcessor.process_trade_combination` with mocked API | 4h |
| Unit tests for `SonarftValidators` spread and liquidity logic | 3h |
| Security tests for path traversal in HTTP endpoints | 1h |

---

## 5. Prioritised Action List

| Priority | Action | Severity | Effort |
|---|---|---|---|
| 1 | Fix `calculate_trade` 4-value return / 3-value unpack | Critical | 1h |
| 2 | Add None guards for indicator returns | Critical | 2h |
| 3 | Fix `handle_trade_results` None unpack | Critical | 1h |
| 4 | Sanitise `client_id` / `botid` in HTTP endpoints | Critical | 1h |
| 5 | Fix re-entrant lock deadlock | High | 1h |
| 6 | Fix `market_movement` direction bug | Medium | 15m |
| 7 | Fix `get_short_term_market_trend` threshold | Medium | 15m |
| 8 | Replace `print()` with logger | Medium | 1h |
| 9 | Add timeout to `monitor_price` / `monitor_order` | High | 2h |
| 10 | Write unit tests for `SonarftMath` and indicators | High | 6h |
