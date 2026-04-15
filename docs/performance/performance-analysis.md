# SonarFT — Performance & Scalability Review

**Review Date:** July 2025
**Codebase Version:** 1.0.0
**Reviewer Role:** Senior Python Engineer / Performance Analyst
**Scope:** API call frequency, order book fetching, data processing efficiency, memory usage, bottleneck identification, concurrency scaling, and optimization opportunities
**Follows:** [Security & Trading Risk Review](../security/security-audit.md)

---

## 1. API Call Frequency Audit

### 1.1 Calls Per Trade Cycle (Per Symbol, Per Exchange Pair)

A single trade cycle for one symbol across two exchanges triggers the following API calls:

**Phase 1 — Price Establishment (`get_latest_prices`):**

| Call | Method | Per Exchange | Total (2 exchanges) |
|---|---|---|---|
| Order book | `watch_order_book` | 1 | 2 |
| Ticker | `watch_ticker` | 1 | 2 |
| **Subtotal** | | | **4** |

**Phase 2 — Price Adjustment (`weighted_adjust_prices` — 16-call gather + 2-call vol gather):**

| Call | Method | Per Exchange | Total (2 exchanges) |
|---|---|---|---|
| `market_movement` (order book) | `watch_order_book` | 1 | 2 |
| `get_market_direction` (OHLCV 16) | `fetch_ohlcv` | 1 | 2 |
| `get_rsi` (OHLCV 16) | `fetch_ohlcv` | 1 | 2 |
| `get_stoch_rsi` (OHLCV 32) | `fetch_ohlcv` | 1 | 2 |
| `get_short_term_trend` (OHLCV 6) | `fetch_ohlcv` | 1 | 2 |
| `get_volatility` (order book) | `watch_order_book` | 1 | 2 |
| `get_order_book` (price blend) | `watch_order_book` | 1 | 2 |
| `get_support_price` (OHLCV 3, 1h) | `fetch_ohlcv` | 0.5* | 1 |
| `get_resistance_price` (OHLCV 3, 1h) | `fetch_ohlcv` | 0.5* | 1 |
| `dynamic_volatility` → `get_macd` (OHLCV 45) | `fetch_ohlcv` | 1 | 2 |
| `dynamic_volatility` → `get_rsi` (OHLCV 16) | `fetch_ohlcv` | 1 | 2 |
| **Subtotal** | | | **20** |

*Support fetched from sell exchange only; resistance from buy exchange only.

**Phase 3 — Validation (`has_requirements_for_success_carrying_out`):**

| Call | Method | Per Exchange | Total |
|---|---|---|---|
| `deeper_verify_liquidity` (order book) | `watch_order_book` | 1 | 2 |
| `deeper_verify_liquidity` (trading volume) | `watch_ticker` | 1 | 2 |
| `verify_spread_threshold` → OHLCV history | `fetch_ohlcv` | 1 | 2 |
| `verify_spread_threshold` → order books | `watch_order_book` | 1 | 2 |
| **Subtotal** | | | **8** |

**Total per symbol per cycle: ~32 API calls (2 exchanges)**

With OHLCV caching, many OHLCV calls are cache hits. Effective uncached calls:

| Call Type | Total | Cache Hits | Net API Calls |
|---|---|---|---|
| Order book | 12 | 0 (not cached) | **12** |
| OHLCV (various limits) | 16 | ~8 (same limit/timeframe) | **~8** |
| Ticker | 4 | 0 (not cached) | **4** |
| **Net total** | **32** | **~8** | **~24** |

**For 2 symbols × 2 exchanges: ~48 net API calls per cycle.**

### 1.2 Rate Limit Impact

With `enableRateLimit: True` + manual `wait_for_rate_limit` (double rate limiting):

| Exchange | `rateLimit` (ms) | Delay per call | 24 calls × delay |
|---|---|---|---|
| Binance | 50ms | 100ms (doubled) | 2.4 seconds |
| OKX | 100ms | 200ms (doubled) | 4.8 seconds |

**Estimated rate-limit sleep per cycle: 2.4–4.8 seconds** (before network latency).

With a 6–18 second inter-cycle sleep, the bot spends roughly 30–50% of its time in artificial rate-limit delays.

### 1.3 API Call Table

| API Call | Purpose | Frequency | Cached? | Optimization |
|---|---|---|---|---|
| `watch_order_book` | Price, volatility, liquidity, spread | 12× per symbol/cycle | ❌ | Fetch once, share across consumers |
| `fetch_ohlcv` (1m, 16) | RSI, SMA | 2× per symbol/cycle | ✅ 60s TTL | Already cached |
| `fetch_ohlcv` (1m, 32) | StochRSI | 2× per symbol/cycle | ✅ 60s TTL | Already cached |
| `fetch_ohlcv` (1m, 45) | MACD | 2× per symbol/cycle | ✅ 60s TTL | Already cached |
| `fetch_ohlcv` (1m, 6) | Short trend | 2× per symbol/cycle | ✅ 60s TTL | Already cached |
| `fetch_ohlcv` (1h, 3) | Support/resistance | 1× per symbol/cycle | ✅ 3600s TTL | Already cached |
| `fetch_ohlcv` (1m, 100) | Spread threshold history | 2× per symbol/cycle | ✅ 60s TTL | Already cached |
| `watch_ticker` | Volume, last price | 4× per symbol/cycle | ❌ | Cache ticker for 1–5s |
| `watch_orders` | Order monitoring | 1× per second during execution | ❌ | Acceptable |
| `fetch_balance` | Balance check | 1× per order leg | ❌ | Cache for 5s |

---

## 2. Order Book Fetching Analysis

### 2.1 Fetch Frequency

The order book is fetched **12 times per symbol per cycle** across 2 exchanges (6 per exchange):

| Consumer | Location | Depth Used |
|---|---|---|
| `market_movement` | `sonarft_indicators.py:233` | 6 levels (sum of prices) |
| `get_volatility` | `sonarft_indicators.py:350` | All levels (std dev) |
| `get_order_book` (price blend) | `sonarft_prices.py:100` | 3 levels (VWAP) |
| `deeper_verify_liquidity` | `sonarft_validators.py:49` | 10 levels |
| `get_trade_dynamic_spread_threshold_avg` | `sonarft_validators.py:100` | 100 levels |
| `get_latest_prices` | `sonarft_api_manager.py:284` | 12 levels (VWAP) |

All 6 calls per exchange fetch the **same order book** independently. In ccxtpro (WebSocket) mode, `watch_order_book` returns the cached in-memory order book maintained by the WebSocket subscription — these are fast local reads, not network requests. ✅

In ccxt (REST) mode, each `fetch_order_book` is a separate HTTP request — 12 HTTP requests per symbol per cycle just for order books. This is a significant performance concern in REST mode.

### 2.2 Optimization: Single Order Book Per Exchange Per Cycle

The most impactful optimization is to fetch the order book once per exchange per cycle and pass it to all consumers:

```python
order_book_buy, order_book_sell = await asyncio.gather(
    self.api_manager.get_order_book(buy_exchange, base, quote),
    self.api_manager.get_order_book(sell_exchange, base, quote),
)
# Pass order_book_buy/sell to all consumers
```

This reduces 12 order book fetches to 2 per symbol per cycle — an **83% reduction** in order book API calls.

---

## 3. Data Processing Performance

### 3.1 pandas-ta Operations

All indicator calculations use pandas-ta on small Series (6–45 elements). These are CPU-bound operations running synchronously in async functions:

| Indicator | Input Size | Estimated Time | Blocks Event Loop? |
|---|---|---|---|
| `pta.rsi(16)` | 16 floats | < 1ms | Yes |
| `pta.stochrsi(32)` | 32 floats | < 2ms | Yes |
| `pta.macd(45)` | 45 floats | < 2ms | Yes |
| `pta.sma(16)` | 16 floats | < 1ms | Yes |
| `pta.atr(15)` | 15 floats | < 1ms | Yes |
| `np.std(order book)` | ~20 floats | < 0.1ms | Yes |

**Total pandas-ta CPU time per symbol per cycle: ~7ms**

For 2 symbols × 2 exchanges = ~28ms of event loop blocking per cycle. With a 6–18 second inter-cycle sleep, this is negligible at current scale. At 20+ symbols, it becomes noticeable (>280ms blocking).

### 3.2 Repeated Calculations

| Calculation | Repeated? | Where |
|---|---|---|
| RSI (same params) | ✅ Twice per exchange | `weighted_adjust_prices` + `dynamic_volatility_adjustment` | 
| Order book VWAP | ✅ 3× per exchange | `get_latest_prices`, `get_order_book` (price blend), `deeper_verify_liquidity` |
| Spread calculation | ✅ 2× | `deeper_verify_liquidity` + `verify_spread_threshold` |

**RSI is computed twice per exchange per cycle** — once in the main 16-call gather and once inside `dynamic_volatility_adjustment`. Since both use the same parameters (period=14, timeframe='1m', limit=16), the OHLCV cache ensures only one API call, but the pandas-ta computation runs twice.

### 3.3 DataFrame Efficiency

```python
close_prices = pd.Series([x[4] for x in ohlcv])
rsi = pta.rsi(close_prices, length=moving_average_period)
```

- List comprehension to extract close prices: O(n) — acceptable for n ≤ 45 ✅
- `pd.Series` creation from list: O(n) — acceptable ✅
- No unnecessary DataFrame copies ✅
- No `.apply()` or row-wise operations — vectorized pandas-ta ✅

**Assessment:** Data processing is efficient for current data sizes. ✅

### 3.4 Spread Threshold Computation

```python
trade_spread_sum = sum(
    (ask_price - bid_price) * min(ask_volume, bid_volume)
    for (bid_price, bid_volume) in buy_order_book['bids'][:10]
    for (ask_price, ask_volume) in sell_order_book['asks'][:10]
)
```

This nested loop runs 10×10 = 100 iterations synchronously. For 10 levels, this is trivial. ✅


---

## 4. Indicator Calculation Performance

### 4.1 Computational Cost Summary

| Indicator | Calls Per Cycle (2 exchanges) | CPU Time | Cached OHLCV? |
|---|---|---|---|
| RSI | 4 (2 in gather + 2 in vol adj) | ~4ms | ✅ |
| StochRSI | 2 | ~4ms | ✅ |
| MACD | 2 | ~4ms | ✅ |
| SMA direction | 2 | ~2ms | ✅ |
| Short-term trend | 2 | ~1ms | ✅ |
| Volatility (np.std) | 2 | ~0.2ms | N/A (order book) |
| Support/resistance | 2 | ~0.5ms | ✅ (3600s TTL) |
| **Total** | **16** | **~16ms** | |

### 4.2 Caching Opportunities

Currently only OHLCV data is cached. Indicator values themselves are not cached — they are recomputed every cycle even when the underlying OHLCV data hasn't changed (within the 60s TTL window).

**Opportunity:** Cache computed indicator values with the same TTL as the underlying OHLCV data:

```python
# Pseudo-code for indicator caching
_indicator_cache: Dict[str, Tuple[float, Any]] = {}

async def get_rsi(self, exchange, base, quote, period=14, timeframe='1m'):
    cache_key = f"rsi:{exchange}:{base}/{quote}:{period}:{timeframe}"
    cached = self._indicator_cache.get(cache_key)
    if cached and time.monotonic() < cached[0]:
        return cached[1]
    value = ... # compute
    self._indicator_cache[cache_key] = (time.monotonic() + 60, value)
    return value
```

This would eliminate the duplicate RSI computation in `dynamic_volatility_adjustment` and reduce pandas-ta CPU time by ~50%.

---

## 5. Memory Usage Analysis

### 5.1 Memory Growth Sources

| Component | Growth Pattern | Bounded? | Size Estimate |
|---|---|---|---|
| `_ohlcv_cache` | Grows with unique (exchange, symbol, timeframe, limit) combinations | ❌ Unbounded | ~10KB per entry × N entries |
| `AsyncHandler.logs` | `deque()` with no maxlen | ❌ Unbounded | Grows with log volume |
| `SonarftServer.tasks` | Cleaned up on new WS message | ⚠️ Slow cleanup | Small |
| `TradeExecutor.trade_tasks` | Cleaned by monitor loop | ⚠️ If monitor crashes | Small |
| Trade history files | Append-only JSON | ❌ Unbounded on disk | ~1KB per trade |
| Exchange instances | Fixed at startup | ✅ | ~5MB per exchange |
| OHLCV data per cache entry | 45 candles × 6 floats | ✅ Fixed per entry | ~2KB per entry |

### 5.2 `_ohlcv_cache` Memory Growth

For a 2-exchange, 2-symbol configuration with 5 distinct OHLCV limits (6, 16, 32, 45, 100) and 2 timeframes (1m, 1h):

```
Cache entries = 2 exchanges × 2 symbols × 5 limits × 2 timeframes = 40 entries
Memory = 40 × ~2KB = ~80KB
```

For 10 symbols × 5 exchanges: 500 entries × 2KB = ~1MB — still manageable.

**However**, expired entries are never evicted — the cache only skips expired entries on read but never removes them. Over time, entries accumulate even after symbols or exchanges are removed from config.

### 5.3 `AsyncHandler.logs` — Unbounded Deque

```python
# sonarft_server.py:425-427
if client_id not in self.logs:
    self.logs[client_id] = deque()   # no maxlen
self.logs[client_id].append(log_message)
```

The `deque` has no `maxlen`. Log messages accumulate indefinitely until `send_logs` drains them. If the WebSocket client is slow to consume logs (or disconnected), the deque grows without bound.

**Fix:** Use `deque(maxlen=1000)` to automatically drop oldest logs when full.

### 5.4 Trade History File Size

Each trade appends ~500 bytes to `{botid}_orders.json` and ~700 bytes to `{botid}_trades.json`. The entire file is read and rewritten on each append:

| Trades per day | File size after 30 days | Read+write per trade |
|---|---|---|
| 100 | ~2MB | 2MB I/O |
| 1000 | ~20MB | 20MB I/O |
| 10000 | ~200MB | 200MB I/O |

At high trade frequency, the O(n) read-modify-write pattern becomes a significant bottleneck.

---

## 6. Bottleneck Identification

### 6.1 Critical Path Analysis

The critical path for a single trade cycle (sequential dependencies):

```
1. get_latest_prices()                    ~200-500ms  (2 API calls, parallel)
2. weighted_adjust_prices()               ~300-800ms  (18 API calls, parallel; rate-limit sleep dominates)
3. calculate_trade()                      ~1ms        (CPU only)
4. has_requirements_for_success()         ~200-400ms  (4 API calls, parallel)
5. execute_trade() [if triggered]         ~5-300s     (order monitoring)
```

**Dominant bottleneck: rate-limit sleep in `wait_for_rate_limit`**

With double rate limiting (ccxt `enableRateLimit` + manual `wait_for_rate_limit`), each API call sleeps for `rateLimit` ms before executing. For 24 net API calls at 100ms each = 2.4 seconds of pure sleep per cycle.

### 6.2 Bottleneck Table

| Bottleneck | Location | Frequency | Impact | Improvement |
|---|---|---|---|---|
| Double rate limiting | `sonarft_api_manager.py:65,69` | Every API call | **High** — 2-5s per cycle | Remove manual `wait_for_rate_limit`; rely on `enableRateLimit` |
| Order book fetched 6× per exchange | `sonarft_indicators.py`, `sonarft_prices.py`, `sonarft_validators.py` | Every cycle | **High** — 6 redundant calls | Fetch once, pass to consumers |
| Sync file I/O in async context | `sonarft_helpers.py`, `sonarft_server.py` | Every trade save, every HTTP request | **High** — blocks event loop | Use `aiofiles` or `asyncio.to_thread` |
| RSI computed twice per exchange | `sonarft_prices.py:57`, `sonarft_prices.py:175` | Every cycle | Medium — ~4ms CPU | Cache indicator values |
| pandas-ta in async functions | `sonarft_indicators.py` | Every cycle | Medium — ~16ms CPU | `asyncio.to_thread` for heavy indicators |
| O(n) trade history read-modify-write | `sonarft_helpers.py:70-77` | Every trade | Medium — grows with history | Use append-only file or SQLite |
| `get_exchange_by_id` linear scan | `sonarft_api_manager.py` | Every API call | Low — O(n) exchanges | Use dict lookup |
| Unbounded `_ohlcv_cache` | `sonarft_api_manager.py:34` | Grows over time | Low — memory | Add LRU eviction |

### 6.3 Sequential Work That Could Parallelize

Currently sequential in `execute_long_trade`:
```python
# sonarft_execution.py:136-154
buy_balance = await check_balance(buy_exchange, 'buy', ...)   # sequential
result_buy  = await create_order(buy_exchange, 'buy', ...)    # sequential
sell_balance = await check_balance(sell_exchange, 'sell', ...) # sequential
result_sell  = await create_order(sell_exchange, 'sell', ...)  # sequential
```

Balance checks for buy and sell could run in parallel:
```python
buy_balance, sell_balance = await asyncio.gather(
    check_balance(buy_exchange, 'buy', ...),
    check_balance(sell_exchange, 'sell', ...)
)
```

This saves one round-trip latency (~200ms) per trade.

---

## 7. Concurrency & Scaling

### 7.1 Multi-Bot Concurrency

Multiple bots run as independent asyncio tasks on the same event loop. Each bot has its own:
- Exchange instances (separate WebSocket connections)
- OHLCV cache (separate dict per `SonarftApiManager` instance)
- Trade history files (separate by `botid`)

**Scaling limit:** The single asyncio event loop processes all bots sequentially (cooperative multitasking). With N bots each making 24 API calls per cycle, the event loop handles N×24 concurrent coroutines. Python's asyncio handles thousands of concurrent coroutines efficiently — this is not a bottleneck at typical bot counts (< 20).

**Exchange connection limit:** Each bot creates its own exchange instances. With 5 bots × 2 exchanges = 10 WebSocket connections. Most exchanges allow 5–10 concurrent WebSocket connections per IP — this becomes a limit at ~5 bots.

### 7.2 Multi-Symbol Scaling

Symbols are processed in parallel via `asyncio.gather`:
```python
futures = [
    self.trade_processor.process_symbol(botid, symbol, ...)
    for symbol in self.symbols
]
results = await asyncio.gather(*futures, return_exceptions=True)
```

Adding symbols scales linearly in API calls: N symbols × 24 calls = N×24 total calls per cycle. With rate limiting, cycle time grows proportionally with symbol count.

**Practical limit:** At 10 symbols × 2 exchanges × 100ms rate limit = 24 seconds of rate-limit sleep per cycle. This exceeds the 6–18 second inter-cycle sleep, causing cycles to overlap.

### 7.3 I/O vs CPU Bound

The system is **I/O bound** — the dominant time is spent waiting for:
1. Rate-limit sleeps (artificial)
2. Exchange API responses (network)
3. Order monitoring polls (intentional)

CPU usage (pandas-ta, numpy) is negligible at current scale. asyncio is well-suited for I/O-bound workloads. ✅

### 7.4 Scalability Limits Summary

| Dimension | Current Config | Practical Limit | Bottleneck |
|---|---|---|---|
| Symbols per bot | 2 | ~5–8 | Rate limit sleep exceeds inter-cycle sleep |
| Exchanges per bot | 2 | ~3–4 | WebSocket connection limits |
| Bots per server | Unlimited | ~5 | Exchange WS connection limits per IP |
| Trade history size | Small | ~10K trades | O(n) file read-modify-write |
| Log memory | Small | ~10K messages | Unbounded deque |

---

## 8. Cache & Optimization Opportunities

### 8.1 Order Book Cache (Highest Impact)

Fetch order book once per exchange per cycle, store in a short-lived (1–2s) cache:

```python
# In SonarftApiManager
_order_book_cache: Dict[str, Tuple[float, dict]] = {}

async def get_order_book(self, exchange_id, base, quote):
    key = f"{exchange_id}:{base}/{quote}"
    cached = self._order_book_cache.get(key)
    if cached and time.monotonic() < cached[0]:
        return cached[1]
    ob = await self.call_api_method(exchange_id, 'fetch_order_book', 'watch_order_book', f"{base}/{quote}")
    if ob:
        self._order_book_cache[key] = (time.monotonic() + 2.0, ob)
    return ob
```

**Impact:** Reduces order book API calls from 12 to 2 per symbol per cycle (83% reduction).

### 8.2 Remove Double Rate Limiting (Second Highest Impact)

```python
# Remove manual wait_for_rate_limit — ccxt's enableRateLimit handles this
async def call_api_method(self, exchange_id, ccxt_method, ccxtpro_method, *args, **kwargs):
    exchange = self.get_exchange_by_id(exchange_id)
    method = ccxt_method if self.__ccxt__ else ccxtpro_method
    method_call = getattr(exchange, method)
    try:
        if self.__ccxt__:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, lambda: method_call(*args, **kwargs))
        else:
            result = await method_call(*args, **kwargs)
    except Exception as e:
        self.logger.error(f"Error calling method {method}: {e}")
    return result
```

**Impact:** Halves artificial rate-limit delay — saves 1–2.5 seconds per cycle.

### 8.3 Indicator Value Cache

Cache computed indicator values with the same TTL as OHLCV data:

**Impact:** Eliminates duplicate RSI computation (~4ms CPU saved); more significant at higher symbol counts.

### 8.4 `get_exchange_by_id` Dict Lookup

```python
# Replace linear scan with dict
self._exchange_map: Dict[str, Any] = {
    ex.id: ex for ex in self.exchanges_instances
}

def get_exchange_by_id(self, exchange_id: str):
    return self._exchange_map.get(exchange_id)
```

**Impact:** O(1) vs O(n) — negligible at 2–3 exchanges, but correct practice.

### 8.5 Trade History — Append-Only or SQLite

Replace read-modify-write JSON with either:
- **Append-only JSONL** (one JSON object per line): O(1) write, O(n) read
- **SQLite**: O(log n) write and read, concurrent-safe

**Impact:** Eliminates O(n) file I/O growth; prevents concurrent write corruption.

---

## 9. Latency Analysis

| Operation | Estimated Latency | Acceptable? | Dominant Source |
|---|---|---|---|
| Full trade cycle (no execution) | 3–8 seconds | ✅ (6–18s sleep) | Rate-limit sleep |
| `weighted_adjust_prices` | 300–800ms | ✅ | Parallel API calls |
| Order book fetch (ccxtpro) | 1–5ms | ✅ | Local WS cache |
| Order book fetch (ccxt REST) | 100–500ms | ⚠️ | Network round-trip |
| OHLCV fetch (cached) | < 1ms | ✅ | Memory lookup |
| OHLCV fetch (uncached) | 100–500ms | ✅ | Network round-trip |
| pandas-ta computation | 1–2ms per indicator | ✅ | CPU |
| Trade history write | 1–100ms (grows) | ⚠️ | Disk I/O + file size |
| Order placement | 50–200ms | ✅ | Network round-trip |
| Order monitoring | 1–300 seconds | ✅ (intentional) | Exchange fill time |

---

## 10. Resource Usage Summary

| Resource | Current (2 symbols, 2 exchanges) | Peak (10 symbols, 3 exchanges) | Limit | Headroom |
|---|---|---|---|---|
| CPU % | < 1% (I/O bound) | ~5% | 100% | High ✅ |
| Memory (Python process) | ~150MB | ~300MB | OS limit | High ✅ |
| Memory (`_ohlcv_cache`) | ~80KB | ~500KB | Unbounded | High ✅ |
| Memory (`logs` deque) | ~1MB | ~10MB | Unbounded | Medium ⚠️ |
| Disk (history/cycle) | ~1.2KB/trade | ~12KB/trade | Disk size | High ✅ |
| API calls/cycle | ~48 | ~240 | Exchange rate limit | Medium ⚠️ |
| WS connections | 2 | 15 | ~10/IP | Low ⚠️ |
| Event loop blocking | ~28ms/cycle | ~280ms/cycle | < 100ms ideal | Medium ⚠️ |

---

## 11. Load Testing Recommendations

| Test Scenario | Metric | Tool | Threshold |
|---|---|---|---|
| Single bot, 2 symbols, 2 exchanges | Cycle time, API calls/min | Manual timing + exchange logs | Cycle < 10s |
| 5 bots concurrent | Memory growth, WS connections | `memory_profiler`, exchange dashboard | Memory < 500MB |
| 10 symbols per bot | Cycle time, rate limit errors | Manual timing | Cycle < 18s |
| 1000 trades history | Trade save latency | `time.perf_counter` | Save < 50ms |
| WebSocket message flood (100 msg/s) | Task list size, memory | `asyncio` task count | Tasks < 100 |
| 24h continuous run | Memory growth, file sizes | `psutil`, `du` | No unbounded growth |

---

## 12. Performance Optimization Roadmap

| # | Optimization | Effort | Impact | Priority |
|---|---|---|---|---|
| 1 | Remove double rate limiting | Low | **High** — saves 1–2.5s/cycle | P1 |
| 2 | Order book cache (2s TTL) | Low | **High** — 83% fewer OB calls | P1 |
| 3 | Fix `deque` maxlen in `AsyncHandler` | Low | Medium — prevents memory leak | P1 |
| 4 | Replace sync file I/O with `aiofiles` | Medium | **High** — unblocks event loop | P2 |
| 5 | `get_exchange_by_id` dict lookup | Low | Low — correctness improvement | P2 |
| 6 | Indicator value cache | Medium | Medium — eliminates duplicate RSI | P2 |
| 7 | Add LRU eviction to `_ohlcv_cache` | Low | Medium — prevents memory growth | P2 |
| 8 | Parallelize balance checks in execution | Low | Low — saves ~200ms per trade | P3 |
| 9 | Replace trade history JSON with SQLite | High | Medium — O(1) writes, concurrent-safe | P3 |
| 10 | Offload pandas-ta to `asyncio.to_thread` | Medium | Low (now), Medium (at scale) | P3 |

---

## 13. Conclusion

### Performance Assessment: **Adequate for Current Scale, Needs Work for Production**

At the default configuration (2 symbols, 2 exchanges, 1 bot), the system performs adequately. The 6–18 second inter-cycle sleep provides sufficient headroom for the ~3–8 second cycle time. Memory usage is modest and CPU usage is negligible.

### Critical Bottlenecks

1. **Double rate limiting** — The combination of `enableRateLimit: True` and manual `wait_for_rate_limit` doubles all API delays. Removing the manual call saves 1–2.5 seconds per cycle with no loss of rate limit compliance.

2. **Order book fetched 12× per symbol per cycle** — In ccxt (REST) mode, this is 12 HTTP requests. A 2-second order book cache reduces this to 2 requests. In ccxtpro (WebSocket) mode, the impact is lower (local cache reads) but the redundancy is still wasteful.

3. **Sync file I/O blocks the event loop** — Every HTTP request and every trade save blocks the event loop. At low trade frequency this is acceptable; at high frequency it degrades all concurrent operations.

### Scaling Ceiling

The system can realistically support:
- **5–8 symbols** per bot before rate-limit sleep exceeds inter-cycle sleep
- **3–4 exchanges** per bot before WebSocket connection limits are hit
- **3–5 concurrent bots** per server before exchange IP connection limits are reached

Beyond these limits, the architecture requires either:
- A shared order book/ticker cache across bots (reduces API calls proportionally)
- Multiple server instances with different exchange API keys
- Adaptive inter-cycle sleep based on actual cycle duration

---

*Generated as part of the SonarFT code review suite — Prompt 09: Performance & Scalability Review*
*Previous: [security-audit.md](../security/security-audit.md)*
*Next: [10-code-quality-testing.md](../prompts/10-code-quality-testing.md)*
