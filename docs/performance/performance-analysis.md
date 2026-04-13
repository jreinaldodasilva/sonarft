# SonarFT — Performance & Scalability Review

## 1. Performance Bottleneck List

### B-1: Sequential Indicator Fetches in `weighted_adjust_prices` (High Impact)

**File:** `sonarft_prices.py`, `weighted_adjust_prices`

All indicator calls are sequential `await` calls. For a single symbol with 2 exchanges, the call chain is:

```
market_movement (buy)       → 1 order book fetch
market_movement (sell)      → 1 order book fetch
get_market_direction (buy)  → 1 OHLCV fetch
get_market_direction (sell) → 1 OHLCV fetch
get_rsi (buy)               → 1 OHLCV fetch
get_rsi (sell)              → 1 OHLCV fetch
get_stoch_rsi (buy)         → 1 OHLCV fetch
get_stoch_rsi (sell)        → 1 OHLCV fetch
get_short_term_market_trend (buy) → 1 OHLCV fetch
get_short_term_market_trend (sell) → 1 OHLCV fetch
dynamic_volatility_adjustment (buy) → get_macd + get_rsi = 2 OHLCV fetches
dynamic_volatility_adjustment (sell) → get_macd + get_rsi = 2 OHLCV fetches
get_volatility (buy)        → 1 order book fetch
get_volatility (sell)       → 1 order book fetch
get_order_book (buy)        → 1 order book fetch
get_order_book (sell)       → 1 order book fetch
get_support_price           → 1 OHLCV fetch
get_resistance_price        → 1 OHLCV fetch
```

**Total: 14 OHLCV fetches + 6 order book fetches = 20 API calls, all sequential.**

With a WebSocket latency of ~50ms per call, this is ~1 second per symbol per cycle before any trade decision is made. With 5 symbols, that is ~5 seconds of sequential API calls.

**Fix:** Gather independent calls:

```python
(dir_buy, dir_sell, rsi_buy, rsi_sell, stoch_buy, stoch_sell,
 trend_buy, trend_sell, vol_buy, vol_sell) = await asyncio.gather(
    self.sonarft_indicators.get_market_direction(buy_exchange, base, quote, 'sma', period),
    self.sonarft_indicators.get_market_direction(sell_exchange, base, quote, 'sma', period),
    self.sonarft_indicators.get_rsi(buy_exchange, base, quote, rsi_period),
    self.sonarft_indicators.get_rsi(sell_exchange, base, quote, rsi_period),
    ...
)
```

---

### B-2: Duplicate Indicator Computation in `_execute_single_trade` (High Impact)

**File:** `sonarft_execution.py`, `_execute_single_trade`

`get_market_direction`, `get_rsi`, and `get_stoch_rsi` are fetched again at execution time — the same data already computed in `weighted_adjust_prices` minutes earlier. This adds 6 more sequential API calls per trade execution.

**Fix:** Pass the already-computed indicator values from `TradeProcessor` into `trade_data` and use them in `_execute_single_trade`.

---

### B-3: `get_latest_prices` Fetches Order Book and Ticker Sequentially per Exchange (Medium Impact)

**File:** `sonarft_api_manager.py`, `get_latest_prices`

```python
for exchange in self.exchanges_instances:
    await self.load_markets(exchange.id)
    order_book = await self.call_api_method(exchange.id, 'fetch_order_book', ...)
    ticker = await self.call_api_method(exchange.id, 'fetch_ticker', ...)
```

For 3 exchanges, this is 6 sequential API calls (2 per exchange). These can be parallelised across exchanges with `asyncio.gather`.

---

### B-4: `load_markets` Called on Every Price Fetch (Medium Impact)

**File:** `sonarft_api_manager.py`, `get_latest_prices`

```python
await self.load_markets(exchange.id)
```

`load_markets` is called inside the per-symbol price fetch loop — once per exchange per symbol per cycle. Market data changes rarely (new listings). This should be called once at startup and cached.

---

### B-5: `get_trade_spread_threshold` Fetches Full Trade History with `limit=None` (High Impact)

**File:** `sonarft_validators.py`, `get_trade_spread_threshold`

```python
historical_data_buy, historical_data_sell = await asyncio.gather(
    self.get_history(buy_exchange, base, quote, timeframe, limit),  # limit=None
    self.get_history(sell_exchange, base, quote, timeframe, limit),
)
```

`limit=None` fetches the maximum available OHLCV history from the exchange (often 500–1000 candles). This is called on every trade validation cycle. For 5 symbols × 2 exchanges = 10 full history fetches per cycle.

---

### B-6: `send_logs` Polls with 1-Second Sleep (Low Impact)

**File:** `sonarft_server.py`, `send_logs`

```python
while True:
    if client_id in handler.logs and handler.logs[client_id]:
        message = handler.logs[client_id].pop(0)
        await websocket.send_text(f"{message}")
    else:
        await asyncio.sleep(1)
```

`pop(0)` on a list is O(n). For high-frequency logging, this degrades. Use `collections.deque` with `popleft()` for O(1) removal.

---

## 2. Optimization Opportunities Table

| Optimization | Impact | Effort | File |
|---|---|---|---|
| Gather all indicator calls in `weighted_adjust_prices` | **High** | Medium | `sonarft_prices.py` |
| Cache OHLCV data per symbol per timeframe (TTL = candle duration) | **High** | Medium | `sonarft_api_manager.py` |
| Pass indicator values from pricing to execution (avoid re-fetch) | **High** | Low | `sonarft_execution.py`, `sonarft_search.py` |
| Call `load_markets` once at startup, not per price fetch | **Medium** | Low | `sonarft_api_manager.py` |
| Limit OHLCV history fetch in `get_trade_spread_threshold` | **High** | Low | `sonarft_validators.py` |
| Replace `list.pop(0)` with `deque.popleft()` in log handler | Low | Low | `sonarft_server.py` |
| Gather order book + ticker per exchange in `get_latest_prices` | Medium | Low | `sonarft_api_manager.py` |
| Parallelise `get_latest_prices` across exchanges | Medium | Low | `sonarft_api_manager.py` |

---

## 3. Scalability Assessment

| Dimension | Current Behaviour | Limit | Recommendation |
|---|---|---|---|
| Bots per server | Unlimited — no cap | Memory bound | Add `max_bots_per_client` config |
| Symbols per bot | Processed with `asyncio.gather` | API rate limit bound | Add symbol batch size config |
| Exchanges per bot | Sequential in `get_latest_prices` | API rate limit bound | Parallelise with gather |
| WebSocket clients | One logger per client, unbounded | Memory bound | Add max client limit |
| Trade tasks | Unbounded `trade_tasks` list | Memory bound | Add max concurrent trades limit |
| Log queue | Unbounded `asyncio.Queue` | Memory bound | Add `maxsize` to queue |
| History files | Append-only JSON — grows unbounded | Disk bound | Add rotation or database backend |

---

## 4. Priority by Impact

1. **Gather indicator calls** in `weighted_adjust_prices` — reduces cycle time by ~10× for multi-exchange setups.
2. **Cache OHLCV data** with a TTL equal to the candle duration — eliminates redundant fetches across indicators.
3. **Limit history fetch** in `get_trade_spread_threshold` — prevents unbounded API calls.
4. **Move `load_markets` to startup** — eliminates repeated market loading.
5. **Pass indicator values through trade pipeline** — eliminates duplicate computation at execution time.
