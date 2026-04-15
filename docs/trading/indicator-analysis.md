# SonarFT — Indicator Pipeline Review

**Review Date:** July 2025
**Codebase Version:** 1.0.0
**Reviewer Role:** Quantitative Trading Reviewer / Signal Systems Analyst
**Scope:** All technical indicators — implementation correctness, data handling, lookback windows, NaN safety, signal generation, and performance
**Follows:** [Financial Math & Precision Review](./financial-math-review.md)

---

## 1. Indicator Implementation Audit

| Indicator | Function | File:Line | Data Source | Lookback Requested | Min Valid Candles | Correctness | NaN Handling |
|---|---|---|---|---|---|---|---|
| RSI | `get_rsi` | indicators:71 | OHLCV close `x[4]` | `period + 2` (16) | `period` (14) | ✅ Standard | ✅ `pd.isna` check |
| StochRSI | `get_stoch_rsi` | indicators:89 | OHLCV close `x[4]` | `rsi + stoch + d + 1` (32) | `rsi + stoch` (28) | ⚠️ Parameter mismatch | ✅ `pd.isna` check |
| SMA/EMA direction | `get_market_direction` | indicators:108 | OHLCV close `x[4]` | `period + 2` (16) | `period` (14) | ✅ Standard | ✅ `pd.isna` check |
| MACD | `get_macd` | indicators:177 | OHLCV close `x[4]` | `long + signal + warmup` (45) | `long + signal + warmup` (45) | ✅ Standard | ✅ `pd.isna` check |
| Short-term trend | `get_short_term_market_trend` | indicators:135 | OHLCV close `x[4]` | `limit` (6) | `2×N` (6) | ⚠️ Threshold bug | ✅ Zero guard |
| Volatility | `get_volatility` | indicators:346 | Order book prices | Live order book | N/A | ⚠️ Not true volatility | ✅ None guard |
| Market movement | `market_movement` | indicators:228 | Order book depth | Live order book | N/A | ⚠️ Shared state race | ❌ No guard |
| Support price | `get_support_price` | indicators:35 | OHLCV low `x[3]` | `lookback_period` (3 in prices.py) | `lookback_period` | ✅ Standard | ✅ None/length check |
| Resistance price | `get_resistance_price` | indicators:53 | OHLCV high `x[2]` | `lookback_period` (3 in prices.py) | `lookback_period` | ✅ Standard | ✅ None/length check |
| ATR | `get_atr` | indicators:266 | OHLCV H/L/C | `period + 1` (15) | `period + 1` (15) | ✅ Standard | ❌ No NaN check on return |
| 24h High/Low | `get_24h_high/low` | indicators:279 | OHLCV high/low | 1440 (1m candles) | 1440 | ✅ Standard | ❌ No NaN check |
| Historical volume | `get_historical_volume` | indicators:303 | OHLCV volume `x[5]` | `limit` | 1 | ❌ Returns only `ohlcv[0][5]` | ❌ No guard |
| Past performance | `get_past_performance` | indicators:372 | OHLCV close | `lookback_period` | 2 | ❌ Inverted index | ❌ No guard |
| Profit factor | `get_profit_factor` | indicators:19 | Volatility float | N/A | N/A | ✅ Linear interpolation | ✅ try/except |
| Liquidity | `get_liquidity` | indicators:328 | Order book | Live | N/A | ❌ Wrong formula | ✅ Empty guard |
| Current volume | `get_current_volume` | indicators:315 | Order book | Live | N/A | ✅ Standard | ❌ No None guard |
| Price change | `get_price_change` | indicators:201 | OHLCV close | `limit` (20) | `2×N` (20) | ✅ Standard | ❌ No zero guard |

---

## 2. OHLCV Data Preprocessing

### 2.1 Data Loading

All indicators fetch OHLCV via a single path:
```
SonarftIndicators.get_history()
    → SonarftApiManager.get_ohlcv_history()
        → call_api_method('fetch_ohlcv', 'fetch_ohlcv', symbol, timeframe, since=None, limit)
        → TTL cache (key: exchange:symbol:timeframe:limit)
```

**OHLCV format assumed throughout:** `[timestamp, open, high, low, close, volume]`
- Index 0: timestamp
- Index 1: open
- Index 2: high ✅ (`x[2]` used in ATR, 24h high, resistance)
- Index 3: low ✅ (`x[3]` used in ATR, 24h low, support)
- Index 4: close ✅ (`x[4]` used in RSI, MACD, StochRSI, SMA, trend)
- Index 5: volume ✅ (`x[5]` used in historical volume)

**Assessment:** OHLCV indexing is consistent and correct throughout. ✅

### 2.2 Data Validation

| Check | Present? | Location |
|---|---|---|
| `None` return from API | ✅ Most indicators | Various |
| Minimum length check | ✅ Most indicators | Various |
| Price validity (> 0) | ❌ Not Found in Source Code | — |
| Volume validity (≥ 0) | ❌ Not Found in Source Code | — |
| Timestamp ordering | ❌ Not Found in Source Code | — |
| Duplicate candles | ❌ Not Found in Source Code | — |
| Gap detection | ❌ Not Found in Source Code | — |

**Issue — no price/volume validity checks:**
If an exchange returns malformed OHLCV data (e.g., negative prices, zero close prices, or duplicate timestamps), the indicators will silently compute incorrect values. pandas-ta will process whatever data it receives.

### 2.3 Data Alignment

All indicators use a single timeframe per call (`'1m'` for most, `'1h'` for support/resistance). There is no multi-timeframe alignment — each indicator fetches its own independent OHLCV slice. This means:

- RSI (14 candles of 1m) and support/resistance (3 candles of 1h) are on different timeframes
- No synchronization between timeframes
- The most recent 1m candle and the most recent 1h candle may represent different time windows

**Assessment:** For the current use case (price adjustment signals, not precise entry timing), this is acceptable. The indicators are used directionally, not for precise timing. ✅

### 2.4 Cache Behavior

```python
# sonarft_api_manager.py
cache_key = f"{exchange_id}:{symbol}:{timeframe}:{limit}"
ttl = _TIMEFRAME_SECONDS.get(timeframe, 60)  # 60s for '1m'
```

All indicators requesting the same `(exchange, symbol, timeframe, limit)` combination within 60 seconds share the same cached OHLCV data. This means:

- RSI and SMA called with the same parameters will use the same cached data ✅ (efficient)
- RSI (limit=16) and MACD (limit=45) have **different cache keys** — two separate API calls ⚠️
- Support/resistance (limit=3, timeframe='1h') has its own cache key ✅

**Issue — MACD fetches more data than RSI but they could share:**
RSI needs 16 candles, MACD needs 45. If MACD's 45-candle response were cached and RSI used the last 16 of those, one API call would suffice. Currently they are separate cache entries.

---

## 3. Pandas & Pandas-TA Usage

### 3.1 RSI

```python
# sonarft_indicators.py:77-79
close_prices = pd.Series([x[4] for x in ohlcv])
rsi = pta.rsi(close_prices, length=moving_average_period)
value = rsi.iloc[-1]
```

**Correctness:** `pta.rsi(close, length=14)` computes Wilder's RSI using EMA smoothing — the standard definition. ✅
**Indexing:** `iloc[-1]` returns the most recent value. ✅
**NaN:** First `length` values will be NaN; `pd.isna(value)` check guards against this. ✅
**Lookback:** Requests `period + 2 = 16` candles for a 14-period RSI. pandas-ta needs at least `length + 1` candles to produce a non-NaN value. 16 candles is marginally sufficient — the last value may still be NaN if the series is too short. A safer request would be `period × 2` (28 candles).

### 3.2 StochRSI — Parameter Mismatch

```python
# sonarft_indicators.py:96
stoch_rsi = pta.stochrsi(close_prices, rsi_period, k_period, d_period)
```

The `pandas-ta` `stochrsi` signature is:
```
stochrsi(close, length=14, rsi_length=14, k=3, d=3, ...)
```

The call passes `(close_prices, rsi_period=14, k_period=3, d_period=3)` as positional arguments, mapping to `(close, length=14, rsi_length=3, k=3)` — **`rsi_length` receives `k_period=3` instead of `rsi_period=14`**.

This means StochRSI is computed with:
- Stochastic window: 14 (correct)
- RSI window: **3** (wrong — should be 14)
- %K smoothing: 3 (correct)
- %D smoothing: missing (uses default)

A 3-period RSI is extremely sensitive and noisy — it will generate far more crossover signals than a standard 14-period RSI-based StochRSI, leading to excessive false signals.

**Correct call:**
```python
stoch_rsi = pta.stochrsi(close_prices, length=stoch_period, rsi_length=rsi_period, k=k_period, d=d_period)
```

### 3.3 MACD

```python
# sonarft_indicators.py:185-191
macd = pta.macd(close_prices, short_period, long_period, signal_period)
macd_col   = f'MACD_{short_period}_{long_period}_{signal_period}'
signal_col = f'MACDs_{short_period}_{long_period}_{signal_period}'
hist_col   = f'MACDh_{short_period}_{long_period}_{signal_period}'
m, s, h = macd[macd_col].iloc[-1], macd[signal_col].iloc[-1], macd[hist_col].iloc[-1]
```

**Correctness:** Standard MACD(12,26,9). ✅
**Column naming:** pandas-ta uses `MACD_12_26_9`, `MACDs_12_26_9`, `MACDh_12_26_9` — correctly constructed. ✅
**NaN check:** `pd.isna(m) or pd.isna(s) or pd.isna(h)` ✅
**Lookback:** Requests `26 + 9 + 10 = 45` candles. MACD needs at least `long + signal - 1 = 34` candles for a valid value. 45 is adequate. ✅

### 3.4 SMA/EMA Market Direction

```python
# sonarft_indicators.py:114-125
close_prices = pd.Series([x[4] for x in history_data])
moving_average = pta.sma(close_prices, length=moving_average_period)
current_price = close_prices.iloc[-1]
ma_value = moving_average.iloc[-1]
if current_price > ma_value: return 'bull'
if current_price < ma_value: return 'bear'
return 'neutral'
```

**Correctness:** Standard SMA direction signal. ✅
**NaN check:** `pd.isna(ma_value) or pd.isna(current_price)` → returns `'neutral'` ✅
**Issue:** Returns `'neutral'` on NaN rather than `None`. This means a data failure silently produces a neutral signal rather than aborting — the trade cycle continues with a neutral direction, which then falls through the position determination logic (the unbound variable bug from Prompt 03).

### 3.5 Short-Term Market Trend

```python
# sonarft_indicators.py:141-165
N = limit // 2   # limit=6 → N=3
current_prices  = [period[4] for period in ohlcv[-N:]]    # last 3 candles
previous_prices = [period[4] for period in ohlcv[-2*N:-N]] # candles 3-6 ago
current_avg  = sum(current_prices) / N
previous_avg = sum(previous_prices) / N
price_change = 100 * (current_avg - previous_avg) / previous_avg

if price_change > threshold * 100:   # threshold=0.001 → 0.1%
    return 'bull'
elif price_change < -(threshold * 100):
    return 'bear'
else:
    return 'neutral'
```

**Correctness:** Compares average of last 3 candles vs previous 3 candles. ✅
**Threshold bug:** `threshold=0.001` is passed as a fraction, then multiplied by 100 → `0.1%`. The comparison `price_change > 0.1` is correct since `price_change` is already in percent (multiplied by 100 above). ✅ (This was previously flagged as a bug but is actually correct.)
**Zero guard:** `if previous_avg_price == 0: return 'neutral'` ✅ — but this check comes **after** the division, not before:

```python
price_change = 100 * (current_avg - previous_avg) / previous_avg  # ← division first
if previous_avg_price == 0:   # ← check after — ZeroDivisionError already raised
    return 'neutral'
```

The variable name is also wrong: `previous_avg_price` vs `previous_avg` — this check references an **undefined variable** and will raise `NameError` rather than catching the zero case.


---

## 4. Indicator-to-Signal Pipeline

### 4.1 Full Signal Flow

```
OHLCV (1m, cached 60s)
    ├── get_rsi(period=14)           → float 0–100
    ├── get_stoch_rsi(14,14,3,3)     → (float %K, float %D)  ⚠️ wrong RSI period
    ├── get_market_direction('sma',14) → 'bull'|'bear'|'neutral'
    ├── get_short_term_market_trend(limit=6, threshold=0.001) → 'bull'|'bear'|'neutral'
    └── get_macd(12,26,9)            → (macd, signal, hist)

Order book (live)
    ├── get_volatility()             → float (std dev of price deviations)
    ├── market_movement(depth=6)     → ('fast'|'slow', 'bull'|'bear')
    ├── get_order_book()             → used for price blending (depth=3)
    └── get_support/resistance(lookback=3, '1h') → float|None

All signals feed into weighted_adjust_prices():
    ├── weight = f(volatility, RSI strength)     → price blend ratio
    ├── spread_factor = get_profit_factor(vol)   → [0.99912, 0.99972]
    └── spread_increase/decrease_factor          → applied per bull/bear + RSI/StochRSI
```

### 4.2 Signal Definitions and Thresholds

| Signal | Threshold | Effect on Trade | Risk if Wrong |
|---|---|---|---|
| RSI ≥ 70 | Overbought | Triggers spread_decrease on buy (bull+bull) | Premature spread narrowing |
| RSI ≤ 30 | Oversold | Triggers spread_increase on buy (bear+bear) | Premature spread widening |
| StochRSI %K > %D | Bullish crossover | Confirms spread direction in bull market | False signal due to 3-period RSI |
| StochRSI %K < %D | Bearish crossover | Confirms spread direction in bear market | False signal due to 3-period RSI |
| SMA direction = 'bull' | Price > 14-SMA | Applies bull spread logic | Lagging signal on fast moves |
| Short trend = 'bull' | 3-candle avg > prev 3-candle avg by 0.1% | Combined with SMA for bull+bull | Very short window — noisy |
| MACD < 0 (bear+bull) | Negative MACD | vol_adj_factor = 0.75 | Reduces volatility weight |
| MACD > 0 (bull+bull, RSI<30) | Positive MACD + oversold | vol_adj_factor = 0.25 | Aggressive volatility reduction |

### 4.3 Signal Combination Logic

The spread adjustment uses a **conjunction** of SMA direction AND short-term trend:

```python
# sonarft_prices.py:111-132
if market_direction_buy == 'bull' and market_trend_buy == 'bull':   # SMA AND 3-candle trend
    if market_rsi_buy >= 70 and market_stoch_rsi_buy_k > market_stoch_rsi_buy_d:
        adjusted_buy_price *= spread_decrease_factor   # overbought confirmation
    else:
        adjusted_buy_price *= spread_increase_factor   # bull momentum
```

**Issue — `market_animal_buy` computed but never used:**
```python
# sonarft_prices.py:72-73
_, market_animal_buy = market_movement_buy    # 'bull' or 'bear'
_, market_animal_sell = market_movement_sell  # 'bull' or 'bear'
```
`market_animal_buy` and `market_animal_sell` are unpacked from `market_movement` results but never referenced in the price adjustment logic. The `market_movement` call (which fetches the order book) is wasted computation.

---

## 5. Off-by-One Error Analysis

### 5.1 OHLCV Candle Ordering

ccxt returns OHLCV data in **ascending timestamp order** — index 0 is the oldest candle, index -1 is the most recent. All indicators use `iloc[-1]` for the current value, which is correct. ✅

### 5.2 RSI Lookback

```python
ohlcv = await self.get_history(exchange, base, quote, timeframe, moving_average_period + 2)
# For period=14: requests 16 candles
```

pandas-ta RSI with `length=14` needs at minimum 15 data points to produce one non-NaN value (14 differences + 1 seed). Requesting 16 candles provides exactly 1 valid RSI value at `iloc[-1]`. This is the minimum — if the exchange returns fewer than 16 candles (e.g., new listing), the NaN check will catch it. ✅ but fragile — requesting `period * 2` would be safer.

### 5.3 StochRSI Lookback

```python
ohlcv = await self.get_history(exchange, base, quote, timeframe, rsi_period + stoch_period + d_period + 1)
# = 14 + 14 + 3 + 1 = 32 candles
```

With the parameter mismatch (RSI period effectively = 3 instead of 14), the actual minimum data needed is `3 + 14 + 3 = 20` candles. Requesting 32 provides adequate headroom. However, the minimum check uses `rsi_period + stoch_period = 28`, which is more than the actual (broken) computation needs. ✅ for the broken version, but the fix (using correct RSI period) would still be satisfied by 32 candles.

### 5.4 Support/Resistance Lookback

```python
# sonarft_prices.py:67-68
self.sonarft_indicators.get_support_price(sell_exchange, base, quote, 3)
self.sonarft_indicators.get_resistance_price(buy_exchange, base, quote, 3)
```

`lookback_period=3` with `timeframe='1h'` (default) means support/resistance is computed from only the last 3 hourly candles (3 hours of data). This is an extremely short window for support/resistance levels — these levels are typically computed over days or weeks. A 3-hour support level has very little predictive value and will change rapidly.

### 5.5 `get_past_performance` — Inverted Index Bug

```python
# sonarft_indicators.py:383-386
historical_data = await self.get_history(exchange, base, quote, timeframe, limit)
current_price = historical_data[0][4]   # ← index 0 = OLDEST candle
past_price    = historical_data[-1][4]  # ← index -1 = NEWEST candle
performance   = (current_price - past_price) / past_price
```

The variable names are inverted: `current_price` gets the oldest candle and `past_price` gets the newest. The performance calculation is therefore **negated** — a rising market shows negative performance and vice versa. This function is not currently called in the active trading pipeline, but if used, it would produce inverted signals.

---

## 6. Insufficient Lookback Windows

| Indicator | Candles Requested | Min for Valid Output | Buffer | Risk |
|---|---|---|---|---|
| RSI (14) | 16 | 15 | +1 | Low — marginal |
| StochRSI (14,14,3,3) | 32 | 20 (broken) / 34 (correct) | +12 (broken) / -2 (correct) | **High** — correct fix may need more data |
| SMA (14) | 16 | 15 | +1 | Low — marginal |
| MACD (12,26,9) | 45 | 34 | +11 | Low ✅ |
| Short trend | 6 | 6 | 0 | Medium — no buffer |
| Support/Resistance | 3 | 3 | 0 | Medium — no buffer |
| ATR (14) | 15 | 15 | 0 | Medium — no buffer |
| 24h High/Low | 1440 | 1440 | 0 | Medium — fails on new listings |

**Issue — StochRSI fix increases data requirement:**
When the StochRSI parameter mismatch is fixed (RSI period = 14 instead of 3), the minimum data requirement becomes `14 + 14 + 3 = 31` candles. The current request of 32 provides only 1 candle of buffer. Recommend requesting `(rsi_period + stoch_period) * 2 + d_period` for safety.

---

## 7. NaN & Invalid Data Handling

### 7.1 NaN Sources

| Source | Cause | Propagates? |
|---|---|---|
| RSI first `length` values | Insufficient history for EMA seed | ✅ Caught by `pd.isna` |
| StochRSI first `rsi+stoch` values | Insufficient history | ✅ Caught by `pd.isna` |
| MACD first `long+signal` values | Insufficient history | ✅ Caught by `pd.isna` |
| SMA first `length` values | Insufficient history | ✅ Caught by `pd.isna` |
| `np.mean([])` / `np.std([])` | Empty historical data | ❌ Propagates to thresholds (Prompt 04) |
| Exchange returns `None` for OHLCV | API error | ✅ Caught by `if not ohlcv` |
| Exchange returns fewer candles than requested | New listing / thin market | ✅ Length check |

### 7.2 NaN Propagation Risk

All pandas-ta indicators check `pd.isna` on the final value before returning. ✅ However:

- `get_market_direction` returns `'neutral'` on NaN instead of `None` — this silently continues the trade cycle with a neutral signal rather than aborting
- `get_atr` does **not** check for NaN on `atr.iloc[-1]` — returns raw NaN to caller
- `get_24h_high/low` do not check for NaN — `np.max([])` raises `ValueError` on empty array

### 7.3 `get_atr` Missing NaN Check

```python
# sonarft_indicators.py:276-277
atr = pta.atr(high, low, close, length=atr_period)
return atr.iloc[-1]   # ← no pd.isna() check
```

ATR is not currently used in the active trading pipeline (not called from `weighted_adjust_prices` or `_execute_single_trade`), so this is low risk today. If integrated, it would need a NaN guard.

---

## 8. Signal Generation Correctness

### 8.1 RSI Signal

**Standard definition:** RSI ≥ 70 = overbought, RSI ≤ 30 = oversold. ✅

**Usage in SonarFT:**
- RSI ≥ 70 + StochRSI %K > %D → `spread_decrease_factor` on buy price (bull+bull)
- RSI ≤ 30 + StochRSI %K < %D → `spread_increase_factor` on buy price (bear+bear)

**False positive risk:** With StochRSI using a 3-period RSI (due to parameter mismatch), %K/%D crossovers will be extremely frequent and noisy. The RSI ≥ 70 condition provides some filtering, but the combined signal will still generate more false positives than intended.

### 8.2 StochRSI Signal — Critical Bug

**Standard definition:** StochRSI = Stochastic applied to RSI values.
- %K > %D = bullish momentum
- %K < %D = bearish momentum

**Bug:** `pta.stochrsi(close_prices, rsi_period, k_period, d_period)` passes positional args as:
- `length` = `rsi_period` = 14 (stochastic window — correct)
- `rsi_length` = `k_period` = 3 (RSI period — **wrong**, should be 14)
- `k` = `d_period` = 3 (%K smoothing — correct by coincidence since k_period == d_period == 3)

A 3-period RSI oscillates violently between 0 and 100 on every candle. The resulting StochRSI will generate crossover signals on nearly every bar, making it useless as a confirmation filter.

**Correct call:**
```python
stoch_rsi = pta.stochrsi(
    close_prices,
    length=stoch_period,      # stochastic window = 14
    rsi_length=rsi_period,    # RSI window = 14
    k=k_period,               # %K smoothing = 3
    d=d_period                # %D smoothing = 3
)
```

### 8.3 Market Direction Signal

**Standard definition:** Price above SMA = uptrend (bull), below = downtrend (bear). ✅

**Issue — 14-period SMA on 1-minute candles:**
A 14-minute SMA is extremely short-term. It will flip between bull/bear frequently on normal price fluctuations. For a trading bot making decisions every 6–18 seconds, this may be appropriate, but it provides very little trend confirmation.

### 8.4 Volatility Signal

```python
# sonarft_indicators.py:355-368
mid_price = (max(bid_prices) + min(ask_prices)) / 2
price_changes = [abs(price - mid_price) for price in bid_prices + ask_prices]
volatility = np.std(price_changes)
```

**Issue — this is not standard volatility:**
Standard volatility is the standard deviation of **returns** (price changes over time). This function computes the standard deviation of **price deviations from mid-price** within a single order book snapshot. This measures order book spread dispersion, not market volatility. The result is in price units (e.g., dollars), not a dimensionless ratio.

This value is then used in:
```python
volatility = volatility_risk_factor * (volatility_buy + volatility_sell) / 2
# volatility_risk_factor = 0.001
# For BTC: std dev of order book ≈ $50 → volatility = 0.001 × 50 = 0.05
```

The scaling by `0.001` converts it to a small number suitable for the weight formula. The formula works numerically but the semantic meaning is non-standard.

---

## 9. Indicator Analysis Table

| Indicator | Function | Lookback | First Valid | NaN Risk | False Positive Risk | Severity |
|---|---|---|---|---|---|---|
| RSI | `get_rsi` | 16 candles | Candle 15 | Low ✅ | Low | Low |
| StochRSI | `get_stoch_rsi` | 32 candles | Candle 20 | Low ✅ | **High** — 3-period RSI | **High** |
| SMA direction | `get_market_direction` | 16 candles | Candle 15 | Low ✅ | Medium — 14m SMA is noisy | Low |
| MACD | `get_macd` | 45 candles | Candle 34 | Low ✅ | Low | Low |
| Short trend | `get_short_term_market_trend` | 6 candles | Candle 6 | Medium | Medium — 3-candle window | Medium |
| Volatility | `get_volatility` | Live OB | Immediate | Low | Medium — non-standard metric | Medium |
| Market movement | `market_movement` | Live OB | Immediate | **High** — shared state | Medium | **High** |
| Support price | `get_support_price` | 3h candles | Candle 3 | Low ✅ | **High** — 3h window too short | **High** |
| Resistance price | `get_resistance_price` | 3h candles | Candle 3 | Low ✅ | **High** — 3h window too short | **High** |
| ATR | `get_atr` | 15 candles | Candle 15 | Medium — no NaN check | Low | Medium |
| Past performance | `get_past_performance` | lookback | lookback | Medium | **High** — inverted index | **High** |
| Historical volume | `get_historical_volume` | limit | 1 | Medium | **High** — returns only `ohlcv[0][5]` | **High** |
| Liquidity | `get_liquidity` | Live OB | Immediate | Low | **High** — wrong formula | **High** |

---

## 10. Performance Analysis

### 10.1 Repeated Calculations

Per trade cycle, `weighted_adjust_prices` makes **18 async calls** (16 in the main gather + 2 in the volatility gather):

```
market_movement × 2        → 2 order book fetches
get_market_direction × 2   → 2 OHLCV fetches (16 candles, 1m)
get_rsi × 2                → 2 OHLCV fetches (16 candles, 1m)  ← same data as direction
get_stoch_rsi × 2          → 2 OHLCV fetches (32 candles, 1m)
get_short_term_trend × 2   → 2 OHLCV fetches (6 candles, 1m)
get_volatility × 2         → 2 order book fetches              ← same OB as market_movement
get_order_book × 2         → 2 order book fetches              ← same OB again
get_support_price × 1      → 1 OHLCV fetch (3 candles, 1h)
get_resistance_price × 1   → 1 OHLCV fetch (3 candles, 1h)
dynamic_volatility × 2     → 2 MACD + 2 RSI fetches (45 + 16 candles, 1m)
```

**Duplicate fetches per cycle:**
- Order book fetched **3 times** per exchange (market_movement, get_volatility, get_order_book) — all with the same parameters → OHLCV cache does NOT help here (order books are not cached)
- RSI fetched **twice** per exchange (once in main gather, once in dynamic_volatility) — different `limit` values (16 vs 16) → same cache key → **cache hit** ✅
- MACD fetched once per exchange in dynamic_volatility only

**Optimization opportunity:** The three order book fetches per exchange per cycle could be reduced to one by fetching the order book once and passing it to all three consumers.

### 10.2 CPU-Bound Operations in Async Context

All pandas-ta computations run synchronously in async functions, blocking the event loop:

| Operation | Estimated Duration | Frequency |
|---|---|---|
| `pta.rsi(16 values)` | < 1ms | 2× per symbol per cycle |
| `pta.stochrsi(32 values)` | < 2ms | 2× per symbol per cycle |
| `pta.macd(45 values)` | < 2ms | 2× per symbol per cycle |
| `pta.sma(16 values)` | < 1ms | 2× per symbol per cycle |
| `np.std(order book prices)` | < 0.1ms | 2× per symbol per cycle |

For 2 symbols × 2 exchanges, total pandas-ta CPU time ≈ 20–30ms per cycle. With a 6–18 second inter-cycle sleep, this is negligible. At higher symbol counts (10+ symbols), it could become noticeable.

### 10.3 Cache Effectiveness

| Data Type | Cached? | TTL | Benefit |
|---|---|---|---|
| OHLCV (1m, 16 candles) | ✅ Yes | 60s | High — RSI/SMA share cache |
| OHLCV (1m, 45 candles) | ✅ Yes | 60s | Medium — MACD only |
| OHLCV (1h, 3 candles) | ✅ Yes | 3600s | High — support/resistance |
| Order book | ❌ No | — | Fetched 3× per exchange per cycle |
| Ticker | ❌ No | — | Fetched per price request |

---

## 11. Integration Testing Recommendations

| Test Case | Indicator | Input | Expected Output |
|---|---|---|---|
| Normal bull market | RSI | 14 rising close prices | RSI > 50 |
| Overbought | RSI | 14 strongly rising prices | RSI ≥ 70 |
| Insufficient data | RSI | 5 close prices | Returns `None` |
| StochRSI correct params | StochRSI | 32 prices | %K and %D in [0, 100] |
| StochRSI crossover | StochRSI | Oscillating prices | %K crosses %D |
| Bull direction | SMA | Price > 14-period SMA | Returns `'bull'` |
| NaN on short series | SMA | 5 prices for 14-period SMA | Returns `'neutral'` (NaN path) |
| MACD signal | MACD | 45 prices | Returns (macd, signal, hist) floats |
| Empty order book | market_movement | `{'bids': [], 'asks': []}` | Should return `('slow', 'neutral')` — currently crashes |
| Zero previous avg | Short trend | All same prices | Returns `'neutral'` — currently crashes (NameError) |
| Inverted performance | Past performance | Rising prices | Currently returns negative (bug) |

---

## 12. Conclusion

### Overall Indicator Reliability: **Moderate** ⭐⭐⭐

The standard indicators (RSI, MACD, SMA) are correctly implemented using pandas-ta with proper NaN guards. The critical issue is the **StochRSI parameter mismatch** which causes the RSI period to be 3 instead of 14, generating excessive false signals that corrupt the spread adjustment logic.

### Critical Issues

1. **StochRSI parameter mismatch** (`sonarft_indicators.py:96`) — RSI period = 3 instead of 14 due to positional argument error. Fix: use keyword arguments.

2. **`get_short_term_market_trend` zero-division** (`sonarft_indicators.py:160-161`) — division before zero check, and zero check references undefined variable `previous_avg_price` instead of `previous_avg`. Fix: check before dividing.

3. **`market_animal_buy/sell` computed but never used** (`sonarft_prices.py:72-73`) — wasted order book fetch. Fix: remove `market_movement` calls or use the result.

### High Priority Issues

4. **Support/resistance lookback = 3 hours** — too short for meaningful levels. Recommend minimum 24 hours (24 candles of 1h).

5. **Order book fetched 3× per exchange per cycle** — consolidate to 1 fetch, pass to all consumers.

6. **`get_past_performance` inverted index** — `historical_data[0]` is oldest, not current. Fix: swap indices.

7. **`get_historical_volume` returns only first candle** — `ohlcv[0][5]` should be `ohlcv[-1][5]` for most recent, or sum for total volume.

### Recommendations

- Use keyword arguments for all pandas-ta calls to prevent positional parameter mismatches
- Increase support/resistance lookback to 24h minimum
- Cache order book per exchange per cycle to eliminate duplicate fetches
- Add `pd.isna` check to `get_atr` return value
- Replace `get_liquidity` formula with a dimensionally correct implementation
- Add price/volume validity checks to OHLCV preprocessing

---

*Generated as part of the SonarFT code review suite — Prompt 05: Indicator Pipeline Review*
*Previous: [financial-math-review.md](./financial-math-review.md)*
*Next: [06-execution-exchange.md](../prompts/06-execution-exchange.md)*
