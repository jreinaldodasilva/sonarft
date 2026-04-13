# SonarFT — Indicator Pipeline Review

## 1. Data Flow: OHLCV to Signal

```mermaid
flowchart LR
    A[SonarftApiManager\nget_ohlcv_history\nccxt fetch_ohlcv] --> B[SonarftIndicators\nget_history wrapper]
    B --> C[pd.Series close prices\nx4 for close]
    C --> D[pandas-ta\nrsi / macd / stochrsi / sma / ema]
    D --> E[.iloc[-1] last value]
    E --> F[SonarftPrices\nweighted_adjust_prices\nspread factor selection]
    F --> G[SonarftExecution\n_execute_single_trade\nLONG/SHORT decision]
```

OHLCV index convention used throughout: `[0]=timestamp, [1]=open, [2]=high, [3]=low, [4]=close, [5]=volume` — consistent and correct.

---

## 2. Indicator-by-Indicator Evaluation

### RSI

**File:** `sonarft_indicators.py`, `get_rsi`

```python
ohlcv = await self.get_history(exchange, base, quote, timeframe, moving_average_period+2)
if len(ohlcv) < moving_average_period:
    raise ValueError(...)
close_prices = pd.Series([x[4] for x in ohlcv])
rsi = pta.rsi(close_prices, length=moving_average_period)
return rsi.iloc[-1]
```

| Check | Result |
|---|---|
| Correct OHLCV index | Yes — `x[4]` is close |
| Sufficient lookback | Marginal — requests `period+2` candles; pandas-ta RSI needs `period+1` minimum, so `+2` is barely sufficient |
| NaN handling | None — `rsi.iloc[-1]` can be `NaN` if pandas-ta returns NaN for the last value |
| Return type | `numpy.float64` — not `float`; comparisons with Python `float` thresholds work but type is inconsistent |
| Error return | `None` on exception — callers must check for `None` before arithmetic |

**Risk:** `rsi.iloc[-1]` returns `NaN` when there are insufficient non-NaN values. `NaN >= 70` evaluates to `False` in Python, so overbought/oversold conditions are silently missed rather than raising an error.

---

### MACD

**File:** `sonarft_indicators.py`, `get_macd`

```python
ohlcv = await self.get_history(exchange, base, quote, timeframe, long_period + signal_period + warmup)
macd = pta.macd(close_prices, short_period, long_period, signal_period)
macd_value = macd['MACD_12_26_9'].iloc[-1]
```

| Check | Result |
|---|---|
| Correct OHLCV index | Yes |
| Column name hardcoded | **Issue** — `'MACD_12_26_9'` is hardcoded; if `short_period`, `long_period`, or `signal_period` are changed, the column name changes and a `KeyError` is raised |
| NaN handling | None |
| Warmup period | `warmup=10` added to lookback — reasonable |
| Return on error | `None` — callers must unpack as `macd, signal, hist = await get_macd(...)` but `None` cannot be unpacked |

**Critical:** `dynamic_volatility_adjustment` calls `get_macd` and unpacks the result:

```python
macd, signal, hist = await self.sonarft_indicators.get_macd(exchange, base, quote)
```

If `get_macd` returns `None` (on any exception), this raises `TypeError: cannot unpack non-iterable NoneType object`, crashing `weighted_adjust_prices`.

---

### Stochastic RSI

**File:** `sonarft_indicators.py`, `get_stoch_rsi`

```python
stoch_rsi = pta.stochrsi(close_prices, rsi_period, k_period, d_period)
stoch_rsi_k = stoch_rsi.iloc[-1][0]
stoch_rsi_d = stoch_rsi.iloc[-1][1]
```

| Check | Result |
|---|---|
| Correct OHLCV index | Yes |
| Lookback | `rsi_period + stoch_period + d_period + 1` — adequate |
| Column access | Uses positional `[0]` and `[1]` — fragile if pandas-ta changes column order |
| NaN handling | None — `NaN` comparisons silently fail |
| Return on error | `None` — callers unpack as `k, d = await get_stoch_rsi(...)` which raises `TypeError` on `None` |

---

### SMA / Market Direction

**File:** `sonarft_indicators.py`, `get_market_direction`

```python
moving_average = pta.sma(close_prices, length=moving_average_period)
current_price = close_prices.iloc[-1]
ma_value = moving_average.iloc[-1]
direction = 'neutral'
if current_price > ma_value: direction = 'bull'
elif current_price < ma_value: direction = 'bear'
```

| Check | Result |
|---|---|
| Correct logic | Yes |
| NaN handling | `current_price > NaN` evaluates to `False` — direction stays `'neutral'` silently |
| Return on error | `None` — callers use string comparison `== 'bull'` which evaluates to `False` for `None`, so neutral behaviour results |

---

### Volatility

**File:** `sonarft_indicators.py`, `get_volatility`

```python
mid_price = (max(bid_prices) + min(ask_prices)) / 2
price_changes = [abs(price - mid_price) for price in bid_prices + ask_prices]
volatility = np.std(price_changes)
```

| Check | Result |
|---|---|
| Method | Order book std dev — not historical volatility; measures current spread dispersion |
| Units | Raw price units (e.g. USD) — not normalised; a BTC/USDT pair will have volatility ~100× higher than ETH/USDT |
| Impact | `volatility_risk_factor * volatility` in `weighted_adjust_prices` will produce very different weights for different assets |
| Empty order book | `max([])` raises `ValueError` — no guard |

---

### Short-Term Market Trend

**File:** `sonarft_indicators.py`, `get_short_term_market_trend`

```python
price_change = 100 * (current_avg_price - previous_avg_price) / previous_avg_price
if price_change > threshold:   # threshold = 0.001
    return 'bull'
```

`threshold=0.001` is compared against `price_change` which is in **percent** (multiplied by 100). So the effective threshold is 0.001%, which is extremely sensitive — nearly any price movement triggers bull/bear. This is likely a bug: the threshold should be `0.1` (0.1%) or the multiplication by 100 should be removed.

---

### Support / Resistance

**File:** `sonarft_indicators.py`, `get_support_price` / `get_resistance_price`

```python
low_prices = [x[3] for x in history_data]
return min(low_prices)
```

Simple min/max over the lookback period. This is a naive implementation — it returns the absolute low/high, not a support/resistance level derived from price clustering or pivot points. For a 3-hour lookback (`period=3` in `weighted_adjust_prices`), this is the 3-hour low/high, which is a reasonable but simplistic bound.

**Issue:** `lookback_period` is passed as `period=3` (hours) but the function signature uses `lookback_period=24` with `timeframe='1h'`. When called from `weighted_adjust_prices` with `period=3`, only 3 candles are fetched — barely enough to establish a meaningful support/resistance level.

---

## 3. Risk Assessment

| Indicator | NaN Risk | None Unpack Risk | Incorrect Threshold | Performance |
|---|---|---|---|---|
| RSI | Medium | Low (single return) | No | Low |
| MACD | High | **Critical** (tuple unpack) | No | Low |
| StochRSI | Medium | **Critical** (tuple unpack) | No | Low |
| SMA/Direction | Low | Low | No | Low |
| Volatility | Medium | Low | No | Low |
| Short-term trend | Low | Low | **Yes** (threshold unit mismatch) | Low |
| Support/Resistance | Low | Low | No | Medium (OHLCV fetch per call) |

---

## 4. Repeated OHLCV Fetches

Per trade cycle, for a single symbol with 2 exchanges, the following OHLCV fetches occur in `weighted_adjust_prices` alone:

| Call | Fetches |
|---|---|
| `get_market_direction` × 2 | 2 |
| `get_rsi` × 2 | 2 |
| `get_stoch_rsi` × 2 | 2 |
| `get_short_term_market_trend` × 2 | 2 |
| `get_macd` × 2 (via `dynamic_volatility_adjustment`) | 2 |
| `get_support_price` × 1 | 1 |
| `get_resistance_price` × 1 | 1 |
| `get_order_book` × 2 | 2 (order book, not OHLCV) |

Total: **12 OHLCV fetches + 2 order book fetches** per symbol per cycle, all sequential (not gathered). Then `_execute_single_trade` repeats `get_market_direction`, `get_rsi`, and `get_stoch_rsi` — adding 6 more fetches.

None of these calls are parallelised with `asyncio.gather` in `weighted_adjust_prices`. This is a significant performance bottleneck.
