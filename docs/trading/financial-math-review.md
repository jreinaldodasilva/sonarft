# SonarFT — Financial Math & Precision Review

**Review Date:** July 2025
**Codebase Version:** 1.0.0
**Reviewer Role:** Quantitative Trading Reviewer / Financial Safety Auditor
**Scope:** All financial calculations — precision settings, Decimal vs float usage, rounding strategy, fee accuracy, numerical stability
**Follows:** [Trading Engine & Strategy Logic Review](./trading-engine-analysis.md)

---

## 1. Precision Settings Inventory

### 1.1 Decimal Context Configuration

| File | Setting | Value | Scope |
|---|---|---|---|
| `sonarft_math.py:10` | `getcontext().prec = 28` | 28 significant digits | Module-level (global) |
| All other files | Not set | Python default (28) | Inherited |

**Assessment:** `getcontext().prec = 28` is set once at module level in `sonarft_math.py`. Python's default `decimal` context precision is also 28, so this is redundant but harmless. The setting is not overridden anywhere else. ✅

**Risk:** `getcontext()` returns the **thread-local** decimal context. In an async application running on a single thread (asyncio), this is safe — all coroutines share the same thread and therefore the same context. If the application were ever moved to a multi-threaded executor, each thread would need its own `getcontext().prec = 28` call.

### 1.2 Decimal vs Float Usage Map

| Layer | Operation | Type Used | Correct? |
|---|---|---|---|
| `sonarft_api_manager` | VWAP calculation | `float` (native Python sum) | ⚠️ Should be Decimal for monetary values |
| `sonarft_api_manager` | Ticker price (`ticker['last']`) | `float` (from ccxt) | Acceptable — display only |
| `sonarft_prices` | Price blending (`weight × target + (1-weight) × anchor`) | `float` | ⚠️ Monetary calculation in float |
| `sonarft_prices` | Spread factor multiplication | `float` | ⚠️ Monetary calculation in float |
| `sonarft_prices` | Support/resistance clamping | `float` | ⚠️ Monetary calculation in float |
| `sonarft_math` | Fee calculation | `Decimal` | ✅ Correct |
| `sonarft_math` | Profit calculation | `Decimal` | ✅ Correct |
| `sonarft_math` | Return values | `float` (converted from Decimal) | ⚠️ Precision discarded at boundary |
| `sonarft_indicators` | RSI, MACD, StochRSI | `float` (pandas Series) | Acceptable — indicator signals |
| `sonarft_indicators` | Volatility (np.std) | `float` (numpy) | Acceptable — not monetary |
| `sonarft_validators` | Spread ratio | `float` | ⚠️ Used in trade gate decision |
| `sonarft_validators` | Slippage calculation | `float` | ⚠️ Used in trade gate decision |

### 1.3 Float Contamination Risk

The precision pipeline has a clear contamination boundary:

```
Exchange API (float)
    → VWAP calculation (float)                    ← contamination starts here
    → Price blending in weighted_adjust_prices (float)
    → calculate_trade() input: buy_price (float)
        → Decimal(str(buy_price))                 ← str() conversion isolates float error
        → Decimal arithmetic (28 digits)          ← clean zone
        → float(profit_d)                         ← contamination re-introduced
    → profit_percentage >= threshold (float)      ← float comparison
```

**Key finding:** The `Decimal(str(value))` conversion in `calculate_trade` correctly isolates float contamination. Converting via `str()` rather than `Decimal(float_value)` directly avoids the classic float-to-Decimal precision trap:

```python
# WRONG (float contamination):
Decimal(0.1)  # → Decimal('0.1000000000000000055511151231257827021181583404541015625')

# CORRECT (used in sonarft_math.py):
Decimal(str(0.1))  # → Decimal('0.1')
```
✅ This is correctly implemented.

### 1.4 Rounding Strategy

| Location | Rounding Method | When Applied |
|---|---|---|
| `sonarft_math.py:76` | `ROUND_HALF_UP` via `Decimal.quantize` | All monetary values in `calculate_trade` |
| `sonarft_prices.py` | None — implicit float truncation | Price blending, spread factor application |
| `sonarft_api_manager.py` | None — implicit float | VWAP computation |
| `sonarft_validators.py` | None — implicit float | Spread ratio, slippage |
| `sonarft_indicators.py` | None — pandas/numpy default | All indicator values |

**Issue — rounding applied too late:**
Price adjustment in `weighted_adjust_prices` produces float prices that are then passed to `calculate_trade`. The `calculate_trade` function rounds these prices to exchange precision (e.g., 2 decimal places for Binance). However, the profit threshold comparison uses the **rounded** prices, not the pre-rounding prices. This means:

```
adjusted_buy_price  = 60123.4567  (float from price blending)
adjusted_sell_price = 60183.7891  (float from price blending)

After rounding in calculate_trade (Binance, 2dp):
buy_price_d  = 60123.46
sell_price_d = 60183.79

Spread before rounding: 60.3324
Spread after rounding:  60.33
Rounding error: 0.0024 per trade
```

For a 0.01% threshold on a $60,000 trade, the minimum required profit is $6.00. A $0.0024 rounding error is negligible. However, for small-value assets (e.g., DOGE/USDT at $0.10), rounding to 2 decimal places could eliminate the entire profit margin.

---

## 2. Financial Calculation Audit

| # | Calculation | Location | Uses Decimal? | Rounding Strategy | Edge Cases Handled | Risk |
|---|---|---|---|---|---|---|
| 1 | VWAP (bid/ask) | `sonarft_api_manager.py:324` | ❌ float | None (implicit) | Zero volume ✅ | Medium |
| 2 | Order book weighted price | `sonarft_prices.py:166` | ❌ float | ZeroDivisionError catch ✅ | Zero volume ✅ | Medium |
| 3 | Price blending (weight formula) | `sonarft_prices.py:103` | ❌ float | None | Zero weight ✅ (clamped 0–1) | Medium |
| 4 | Spread factor application | `sonarft_prices.py:134` | ❌ float | None | None | Medium |
| 5 | Support/resistance clamping | `sonarft_prices.py:137` | ❌ float | None | None check ✅ | Low |
| 6 | Buy price rounding | `sonarft_math.py:79` | ✅ Decimal | ROUND_HALF_UP | — | Low ✅ |
| 7 | Buy amount rounding | `sonarft_math.py:80` | ✅ Decimal | ROUND_HALF_UP | — | Low ✅ |
| 8 | Buy fee calculation | `sonarft_math.py:81` | ✅ Decimal | ROUND_HALF_UP | fee_rate None ✅ | Low ✅ |
| 9 | Buy total cost | `sonarft_math.py:83` | ✅ Decimal | ROUND_HALF_UP | Zero cost guard ✅ | Low ✅ |
| 10 | Sell fee calculation | `sonarft_math.py:91` | ✅ Decimal | ROUND_HALF_UP | — | Low ✅ |
| 11 | Net profit | `sonarft_math.py:95` | ✅ Decimal | ROUND_HALF_UP | — | Low ✅ |
| 12 | Profit percentage | `sonarft_math.py:97` | ✅ Decimal | ROUND_HALF_UP | Zero denominator ✅ | Low ✅ |
| 13 | Spread ratio | `sonarft_validators.py:171` | ❌ float | None | — | Medium |
| 14 | Historical spread % | `sonarft_validators.py:86` | ❌ float | None | Empty list ⚠️ | Medium |
| 15 | Slippage calculation | `sonarft_validators.py:213` | ❌ float | None | Zero trade_price ⚠️ | Medium |
| 16 | Volatility (std dev) | `sonarft_indicators.py:368` | ❌ numpy float | None | None order book ✅ | Low |
| 17 | Market trend % change | `sonarft_indicators.py:160` | ❌ float | None | Zero previous_avg ✅ | Low |
| 18 | Liquidity normalization | `sonarft_indicators.py:342` | ❌ float | None | Zero denominator ✅ | Low |

---

## 3. Precision-Sensitive Functions

### 3.1 `SonarftMath.calculate_trade` — Core Financial Function

```
Inputs:  buy_price (float), sell_price (float), buy_price_list (tuple),
         sell_price_list (tuple), target_amount (float), base (str), quote (str)
Outputs: profit (float), profit_pct (float), trade_data (dict of floats)

Precision path:
  float → Decimal(str()) → quantize(ROUND_HALF_UP) → float
```

| Step | Type | Precision |
|---|---|---|
| Input prices | float | ~15 significant digits |
| After `Decimal(str())` | Decimal | Exact string representation |
| After `quantize` | Decimal | Exchange precision (1–3 dp for prices) |
| Output `float()` | float | ~15 significant digits (adequate for quantized values) |

**Assessment:** The internal calculation is correct. The float→Decimal→float round-trip loses no meaningful precision for quantized exchange values. ✅

### 3.2 `SonarftApiManager.get_weighted_prices` — VWAP

```
Inputs:  depth (int), order_book (dict with float prices/volumes from ccxt)
Outputs: bid_vwap (float), ask_vwap (float)
```

All arithmetic is native Python float. For BTC at $60,000 with volumes in the range 0.001–10 BTC:
- `price × volume` ≈ 60,000 × 10 = 600,000 — well within float64 range
- Sum of 12 levels ≈ 7,200,000 — no overflow risk
- Division result ≈ 60,000 — adequate float64 precision

**Assessment:** Float is adequate for VWAP at typical crypto price/volume ranges. ✅

### 3.3 `SonarftPrices.weighted_adjust_prices` — Price Blending

```
Inputs:  target prices (float), last prices (float), volatility_risk_factor (float=0.001)
Outputs: adjusted_buy_price (float), adjusted_sell_price (float), indicators (dict)
```

The weight formula:
```python
volatility = 0.001 × (volatility_buy + volatility_sell) / 2
volatility_factor = 0.001 × market_strength   # market_strength = avg RSI (0–100)
weight = max(0.0, min(1.0, 1 - (volatility × volatility_factor)))
```

**Numerical analysis:**
- `volatility_buy` = std dev of order book price deviations — typically 0–500 for BTC
- `volatility_risk_factor = 0.001` scales this to 0–0.5
- `market_strength` = avg RSI (0–100), scaled by 0.001 → 0–0.1
- `volatility × volatility_factor` ≈ 0.5 × 0.1 = 0.05 at most
- `weight = 1 - 0.05 = 0.95` — target VWAP dominates (95% weight)

**Assessment:** The weight formula is numerically stable. The `max(0.0, min(1.0, ...))` clamp prevents out-of-range weights. ✅ However, the effective weight range (0.95–1.0) means the order book anchor has very little influence (0–5%), making the blending nearly equivalent to using the target VWAP directly.

### 3.4 `SonarftValidators.calculate_thresholds_based_on_historical_data`

```
Inputs:  historical_data_buy (list), historical_data_sell (list)
Outputs: thresholds dict {low, medium, high}
```

```python
historical_spread_percentage = [
    spread / ((ask_price + bid_price) / 2) * 100
    for bid_price, ask_price, spread in zip(...)
]
historical_spread_mean = np.mean(historical_spread_percentage)
historical_spread_std  = np.std(historical_spread_percentage)
```

**Issue — empty list not guarded:**
If `historical_data_buy` and `historical_data_sell` are both empty (no OHLCV history), `historical_spread_percentage` will be an empty list. `np.mean([])` and `np.std([])` return `nan`:
```python
np.mean([])  # → nan (with RuntimeWarning)
np.std([])   # → nan (with RuntimeWarning)
```
The resulting thresholds `{"low": nan, "medium": nan, "high": nan}` will cause all spread comparisons to return `False` (any comparison with `nan` is `False`), silently blocking all trades.


---

## 4. Fee Computation Accuracy

### 4.1 Fee Formula

```python
# sonarft_math.py:81-93
buy_fee_d  = buy_price_d × amount_d × buy_fee_rate    # rounded to fee_precision
sell_fee_d = sell_price_d × amount_d × sell_fee_rate  # rounded to fee_precision

total_buy_cost  = buy_price_d × amount_d + buy_fee_d
net_sell_value  = sell_price_d × amount_d - sell_fee_d
```

**Assessment:** Fee is applied as a percentage of the trade value (taker fee model). This is correct for limit orders on most exchanges. ✅

### 4.2 Taker vs Maker Fee

The config uses a single fee rate per exchange (no distinction between maker and maker fees):

```json
{ "exchange": "binance", "buy_fee": 0.001, "sell_fee": 0.001 }
```

**Issue:** Most exchanges charge different rates for maker (limit order that adds liquidity) vs taker (limit order that crosses the spread). SonarFT places limit orders (`create_order` uses `'limit'` type), which are typically maker orders. Binance maker fee = 0.1%, taker fee = 0.1% (same for standard tier), but OKX maker = 0.08%, taker = 0.1%. The config uses 0.08% for OKX buy — this matches the maker rate, which is correct for limit orders. ✅

### 4.3 Fee Verification — Concrete Example

**Setup:** Buy 1 BTC on Binance at $60,000, sell 1 BTC on OKX at $60,200.

```
BUY (Binance):
  buy_price_d  = Decimal('60000.00')   [precision=2]
  amount_d     = Decimal('1.00000')    [precision=5]
  buy_fee_rate = 0.001
  buy_fee_d    = 60000.00 × 1.00000 × 0.001 = Decimal('60.00000000')  [precision=8]
  value_buying = 60000.00 × 1.00000 = Decimal('60000.00000000')
  total_buy    = 60000.00000000 + 60.00000000 = Decimal('60060.00000000')

SELL (OKX):
  sell_price_d  = Decimal('60200.0')   [precision=1]
  amount_d      = Decimal('1.00000')   [same as buy]
  sell_fee_rate = 0.001
  sell_fee_d    = 60200.0 × 1.00000 × 0.001 = Decimal('60.20000000')  [precision=8]
  value_selling = 60200.0 × 1.00000 = Decimal('60200.00000000')
  net_sell      = 60200.00000000 - 60.20000000 = Decimal('60139.80000000')

PROFIT:
  profit_d     = 60139.80000000 - 60060.00000000 = Decimal('79.80000000')
  profit_pct_d = 79.80000000 / 60060.00000000 = Decimal('0.00132872')  [~0.133%]
```

**Verification:** 0.133% > 0.01% threshold → trade would be executed. ✅
**Fee accuracy:** Both fees correctly deducted. ✅

### 4.4 OKX Price Precision Issue

OKX `prices_precision = 1` (1 decimal place). For BTC/USDT at $60,200.456:

```
sell_price_d = Decimal('60200.5')   [rounded to 1dp with ROUND_HALF_UP]
```

The rounding error is at most $0.05. For a 1 BTC trade:
- Fee impact: $0.05 × 0.001 = $0.00005 — negligible ✅
- Profit impact: $0.05 — negligible for a $79.80 profit ✅

However, for high-frequency small trades or assets with prices near $0.01, 1 decimal place precision would be catastrophically wrong. The hardcoded `prices_precision = 1` for OKX is a fallback — the live market precision from `get_symbol_precision` should always be preferred.

### 4.5 Fee Precision Rounding

All fees are rounded to 8 decimal places (`fee_precision = 8`). For a $60,000 trade:
- `buy_fee = 60.00000000` — 8dp is more than adequate ✅

For a $0.001 trade (micro-trade):
- `buy_fee = 0.00000100` — still representable at 8dp ✅

---

## 5. Profit Calculation Deep Dive

### 5.1 Exact Formula

```
profit = (sell_price × amount − sell_fee_rate × sell_price × amount)
       − (buy_price × amount + buy_fee_rate × buy_price × amount)

       = amount × sell_price × (1 − sell_fee_rate)
       − amount × buy_price × (1 + buy_fee_rate)

profit_pct = profit / (buy_price × amount × (1 + buy_fee_rate))
```

### 5.2 Break-Even Spread

For a trade to be profitable (`profit_pct > 0`):

```
sell_price × (1 − sell_fee) > buy_price × (1 + buy_fee)

sell_price / buy_price > (1 + buy_fee) / (1 − sell_fee)
```

For Binance+OKX (buy_fee=0.001, sell_fee=0.001):
```
sell_price / buy_price > 1.001 / 0.999 = 1.002002...
```
The sell price must be at least **0.2002%** higher than the buy price to break even. The default threshold of 0.01% is far below this break-even point — the bot will attempt trades that are mathematically guaranteed to lose money unless the spread is at least 0.2%.

### 5.3 Edge Cases

| Edge Case | Behavior | Risk |
|---|---|---|
| `buy_price = 0` | `value_buying_with_fee_d = 0` → early return `(0, 0, None)` ✅ | Low |
| `sell_price = 0` | `value_selling_with_fee_d = 0` → `profit_d` is negative → rejected by threshold ✅ | Low |
| `target_amount = 0` | `value_buying_with_fee_d = 0` → early return ✅ | Low |
| `buy_price > sell_price` | `profit_d` is negative → rejected by threshold ✅ | Low |
| Very small amount (e.g., 0.00001 BTC) | Rounds to 0 at 5dp precision → `value_buying_with_fee_d = 0` → early return | Medium — silent skip |
| `buy_fee_rate = 0` | `buy_fee_d = 0` → profit overestimated if real fee > 0 | Medium |
| Same exchange (buy=sell) | No guard — profit calculated but arbitrage is impossible | **High** (see Prompt 03) |

### 5.4 Profit Percentage Precision

```python
profit_pct_d = d(
    (value_selling_with_fee_d - value_buying_with_fee_d) / value_buying_with_fee_d,
    sell_rules['fee_precision']  # = 8 decimal places
)
```

Rounding `profit_pct` to 8 decimal places means the minimum representable profit percentage is `0.00000001` (0.000001%). The threshold is `0.0001` (0.01%), which is `10000 × 0.00000001`. This is well above the rounding floor. ✅

**Issue — profit_pct rounded to fee_precision (8dp) not a dedicated percentage precision:**
Using `fee_precision` (8dp) for a percentage value is semantically incorrect — fee precision refers to monetary amounts, not ratios. It works numerically but is misleading. A dedicated `percentage_precision` field would be cleaner.

---

## 6. Order Book & Aggregation Math

### 6.1 VWAP Aggregation

```python
# sonarft_api_manager.py:318-325
bids = order_book['bids'][:depth]   # list of [price, volume] pairs
total_bid_volume = sum(volume for _, volume in bids)
bid_vwap = sum(price * volume for price, volume in bids) / total_bid_volume
```

**Formula:** Standard volume-weighted average price. ✅
**Precision:** Native Python float. For typical crypto order books (12 levels, BTC prices), float64 provides ~15 significant digits — adequate. ✅
**Edge case — zero volume:** Guarded with `if total_bid_volume == 0: return 0.0, 0.0`. ✅
**Edge case — empty order book:** `bids[:depth]` on empty list returns `[]`; `sum([])` = 0 → zero volume guard triggers. ✅

### 6.2 Spread Threshold Aggregation

```python
# sonarft_validators.py:113-137
trade_spread_sum = sum(
    (ask_price - bid_price) × min(ask_volume, bid_volume)
    for (bid_price, bid_volume) in buy_order_book['bids'][:10]
    for (ask_price, ask_volume) in sell_order_book['asks'][:10]
)
trade_volume_sum = sum(
    min(ask_volume, bid_volume)
    for (_, bid_volume) in buy_order_book['bids'][:10]
    for (_, ask_volume) in sell_order_book['asks'][:10]
)
trade_spread_avg = trade_spread_sum / trade_volume_sum
```

This computes a volume-weighted average cross-exchange spread across all bid×ask combinations (up to 10×10 = 100 pairs). The formula is mathematically sound for estimating the effective spread available at a given volume. ✅

**Issue — O(n²) computation:**
The nested loop over 10 bids × 10 asks = 100 iterations runs synchronously in an async context. For 10 levels this is trivial, but the `actual_count` variable uses `len(buy_bids) × len(sell_asks)` which could be up to 100×100 = 10,000 if the depth were increased.

**Issue — `trade_price_sum` uses all 100 combinations:**
```python
trade_price_sum = sum(
    (ask_price + bid_price) / 2
    for bid_price, _ in buy_bids      # up to 100 entries
    for ask_price, _ in sell_asks     # up to 100 entries
)
trade_price_avg = trade_price_sum / actual_count
```
This averages the mid-price across all 100 bid×ask combinations, giving equal weight to deep levels and top-of-book levels. A volume-weighted mid-price would be more accurate.

### 6.3 Liquidity Normalization

```python
# sonarft_indicators.py:340-342
if not bids or not asks or (bids[0][0] + asks[0][0]) == 0:
    return 0.0
liquidity = (bid_volume_sum + ask_volume_sum) / (bids[0][0] + asks[0][0]) / 2
normalized_liquidity = min(max(liquidity, 0), 1)
```

**Issue — liquidity formula is dimensionally incorrect:**
`(total_volume) / (best_bid + best_ask)` divides volume (in base currency) by price (in quote currency). The result has units of `base²/quote`, not a dimensionless ratio. The normalization to [0,1] via `min(max(...), 1)` masks this — for BTC at $60,000 with 10 BTC total volume, `liquidity = 10 / 120,000 = 0.0000833`, which normalizes to 0.0000833. This is always near 0 for high-price assets, making the function return near-zero for all practical inputs. The function is effectively broken for its intended purpose.


---

## 7. Rounding Edge Cases

### 7.1 Rounding Timing Analysis

```
Stage 1: VWAP (float, no rounding)
    ↓
Stage 2: Price blending (float, no rounding)
    ↓
Stage 3: Spread factor application (float, no rounding)
    ↓
Stage 4: Support/resistance clamping (float, no rounding)
    ↓
Stage 5: calculate_trade() — FIRST ROUNDING POINT
    → buy_price rounded to exchange precision
    → sell_price rounded to exchange precision
    → amount rounded to exchange precision
    → fees calculated on rounded values
    → profit calculated on rounded values
```

**Assessment:** Rounding happens at the correct point — just before the exchange-facing calculation. All intermediate price adjustments use full float precision. ✅

### 7.2 Rounding Direction Impact

`ROUND_HALF_UP` is used for all values. This means:
- Buy price rounds **up** on 0.5 → slightly higher buy cost → slightly lower profit
- Sell price rounds **up** on 0.5 → slightly higher sell proceeds → slightly higher profit
- The net effect is approximately neutral across many trades

**Alternative consideration:** Some exchanges use `ROUND_DOWN` for amounts (to avoid over-selling). Using `ROUND_HALF_UP` for amounts could result in placing an order for slightly more than the available balance in edge cases. `ROUND_DOWN` for amounts would be safer.

### 7.3 Small Amount Rounding to Zero

For Binance (`buy_amount_precision = 5`):
```python
d(0.000004, 5)  # → Decimal('0.00000') → 0
```
If `trade_amount` is set to a very small value (e.g., 0.000004 BTC), it rounds to zero. The `value_buying_with_fee_d == 0` guard catches this and returns `(0, 0, None)`. The trade is silently skipped with no warning. A minimum amount check before rounding would provide a clearer error.

### 7.4 Profit Erosion from Sequential Rounding

Each rounding step introduces a small error. For a chain of operations:

```
buy_price_d  = round(60123.456, 2) = 60123.46  [error: +0.004]
buy_fee_d    = round(60123.46 × 1 × 0.001, 8) = round(60.12346, 8) = 60.12346000
total_buy    = round(60123.46 + 60.12346, 8) = 60183.58346000

sell_price_d = round(60183.789, 2) = 60183.79  [error: +0.001]
sell_fee_d   = round(60183.79 × 1 × 0.001, 8) = 60.18379000
net_sell     = round(60183.79 - 60.18379, 8) = 60123.60621000

profit       = 60123.60621 - 60183.58346 = -59.97725  [LOSS]
```

Wait — this example shows a loss because buy_price > sell_price after rounding. Let me use a profitable spread:

```
buy_price  = 60000.00, sell_price = 60200.00 (0.333% spread)
After rounding (Binance 2dp): unchanged
profit_pct = 0.133% > 0.01% threshold → executed ✅
```

Rounding errors are small relative to the minimum profitable spread. ✅

---

## 8. Exchange-Specific Precision Rules

### 8.1 Hardcoded Fallback Rules

```python
# sonarft_math.py:19-43
EXCHANGE_RULES = {
    'okx':      {'prices_precision': 1, 'buy_amount_precision': 8, 'fee_precision': 8, ...},
    'bitfinex': {'prices_precision': 3, 'buy_amount_precision': 8, 'fee_precision': 8, ...},
    'binance':  {'prices_precision': 2, 'buy_amount_precision': 5, 'fee_precision': 8, ...},
}
```

| Exchange | Price Precision | Amount Precision | Notes |
|---|---|---|---|
| OKX | 1 dp | 8 dp | 1dp for price is too coarse for most symbols |
| Bitfinex | 3 dp | 8 dp | Reasonable for most pairs |
| Binance | 2 dp | 5 dp | Correct for BTC/USDT; wrong for many altcoins |

**Critical Issue — hardcoded precision is symbol-agnostic:**
Binance BTC/USDT uses 2dp for price, but Binance SHIB/USDT uses 8dp. The hardcoded `prices_precision = 2` would round SHIB prices from $0.00001234 to $0.00 — a complete loss of precision. The live market precision from `get_symbol_precision` must be used for all symbols.

### 8.2 Live Precision Lookup

```python
# sonarft_math.py:62-68
buy_rules = (
    self.api_manager.get_symbol_precision(buy_exchange, base, quote)
    or self.EXCHANGE_RULES.get(buy_exchange)
)
```

`get_symbol_precision` returns precision from loaded market data. It is preferred over `EXCHANGE_RULES`. ✅

**Issue — `get_symbol_precision` may return `None` for unloaded markets:**
If `load_all_markets` failed or the symbol is not in the loaded market data, `get_symbol_precision` returns `None`, and the fallback `EXCHANGE_RULES` is used. For symbols not in the three hardcoded exchanges, `EXCHANGE_RULES.get(exchange)` also returns `None`, causing `calculate_trade` to return `(0, 0, None)` — silently skipping the trade.

### 8.3 Minimum Order Enforcement

**⚠️ Not Found in Source Code** — No minimum order size or minimum notional value is enforced. Exchange minimums for reference:

| Exchange | Symbol | Min Amount | Min Notional |
|---|---|---|---|
| Binance | BTC/USDT | 0.00001 BTC | $10 |
| Binance | ETH/USDT | 0.0001 ETH | $10 |
| OKX | BTC/USDT | 0.00001 BTC | — |
| Bitfinex | BTC/USD | 0.00006 BTC | — |

With `trade_amount = 1` (default), all minimums are satisfied for BTC and ETH. However, if `trade_amount` is reduced (e.g., to 0.0001), Binance would reject the order with a minimum notional error.

---

## 9. Numerical Stability Issues

### 9.1 Division Operations — Complete Inventory

| Division | Location | Zero Guard | Risk |
|---|---|---|---|
| `bid_vwap = Σ(p×v) / total_bid_volume` | api_manager:324 | ✅ `if total_bid_volume == 0` | Low |
| `ask_vwap = Σ(p×v) / total_ask_volume` | api_manager:325 | ✅ `if total_ask_volume == 0` | Low |
| `weighted_price = Σ(p×v) / total_volume` | prices:166 | ✅ `ZeroDivisionError` catch | Low |
| `profit_pct = profit / value_buying_with_fee` | math:97 | ✅ `if value_buying_with_fee == 0` | Low |
| `spread_rate = (spread - prev) / prev` | indicators:246 | ✅ `if previous_spread != 0 else 0` | Low |
| `price_change = 100 × (curr - prev) / prev` | indicators:160 | ✅ `if previous_avg_price == 0` | Low |
| `liquidity = (vol_sum) / (bid[0] + ask[0]) / 2` | indicators:342 | ✅ `if (bids[0][0] + asks[0][0]) == 0` | Low |
| `spread / bid_prices[0]` | validators:57 | ❌ No guard if `bid_prices` is empty | **High** |
| `slippage = (top_price - trade_price) / trade_price` | validators:213 | ❌ No guard if `trade_price == 0` | Medium |
| `slippage = abs((sell - buy) / buy)` | validators:236 | ❌ No guard if `buy_price == 0` | Medium |
| `stop_loss = (sell - buy) / buy` | validators:282 | ❌ No guard if `buy_price == 0` | Medium |
| `trade_spread_avg = spread_sum / volume_sum` | validators:126 | ✅ `if trade_volume_sum == 0` | Low |
| `trade_price_avg = price_sum / actual_count` | validators:136 | ✅ `if actual_count == 0` | Low |
| `spread_pct = spread_avg / price_avg × 100` | validators:137 | ❌ No guard if `trade_price_avg == 0` | Medium |
| `percentage_difference = abs(v1-v2) / avg × 100` | indicators:420 | ❌ No guard if `v1 + v2 == 0` | Low |

### 9.2 Critical Zero-Division Risk — `bid_prices[0]`

```python
# sonarft_validators.py:54-57
bid_prices = [float(bid[0]) for bid in order_book['bids']]
ask_prices = [float(ask[0]) for ask in order_book['asks']]
spread = ask_prices[0] - bid_prices[0]
if spread / bid_prices[0] > 0.01 ...  # ← IndexError if bids is empty
                                       # ← ZeroDivisionError if bid_prices[0] == 0
```

If the order book has no bids (empty market), `bid_prices[0]` raises `IndexError`. If the best bid price is 0 (malformed data from exchange), it raises `ZeroDivisionError`. Neither is caught.

### 9.3 NaN/Inf Risk Analysis

| Source | NaN Risk | Inf Risk | Handled? |
|---|---|---|---|
| `np.std([])` | ✅ Returns `nan` | No | ❌ Not guarded in `calculate_thresholds_based_on_historical_data` |
| `np.mean([])` | ✅ Returns `nan` | No | ❌ Not guarded |
| `pd.isna(value)` checks in indicators | — | — | ✅ RSI, MACD, StochRSI, SMA all check for NaN |
| `float('inf')` from exchange | Possible | Possible | ❌ No guard in VWAP or price blending |
| `weight = 1 - (volatility × volatility_factor)` | No | No | ✅ Clamped to [0, 1] |

### 9.4 Overflow/Underflow Analysis

**Overflow risk:** Python `float` (IEEE 754 double) overflows at ~1.8×10³⁰⁸. Crypto prices and volumes are nowhere near this. No overflow risk. ✅

**Underflow risk:** Python float underflows (rounds to 0) below ~5×10⁻³²⁴. For fee calculations on micro-trades, `Decimal` with 28 digits handles values down to 10⁻²⁸ without underflow. ✅

**Integer overflow:** Python integers are arbitrary precision. No overflow risk. ✅

---

## 10. Precision Audit Table

| # | Function | Issue | Severity | Example | Fix |
|---|---|---|---|---|---|
| 1 | `calculate_thresholds_based_on_historical_data` | `np.mean([])` / `np.std([])` returns `nan` → all spread comparisons silently fail | **High** | Empty OHLCV history → `thresholds = {nan, nan, nan}` → all trades blocked | Guard: `if not historical_spread_percentage: return default_thresholds` |
| 2 | `deeper_verify_liquidity` | `bid_prices[0]` raises `IndexError` on empty order book | **High** | Exchange returns empty bids → crash | Guard: `if not bid_prices or not ask_prices: return False` |
| 3 | `get_liquidity` | Dimensionally incorrect formula — always near 0 for high-price assets | **High** | BTC at $60K → liquidity ≈ 0.000083 → always "illiquid" | Fix formula: `liquidity = (bid_vol + ask_vol) / trade_amount` |
| 4 | `calculate_trade` | All Decimal results converted to `float` at return boundary | Medium | Precision discarded; adequate for current threshold but fragile | Keep as `Decimal` in `trade_data`; convert only at API boundary |
| 5 | `weighted_adjust_prices` | All price arithmetic in `float` — no `Decimal` | Medium | Spread factor errors accumulate across adjustments | Use `Decimal` for price blending, or document float is acceptable |
| 6 | `verify_spread_threshold` | Medium volatility threshold divided by 100 | **High** | Medium threshold = 0.005% instead of 0.5% → all trades rejected | Remove `/ 100` |
| 7 | `slippage = (top_price - trade_price) / trade_price` | No zero guard on `trade_price` | Medium | `trade_price = 0` → `ZeroDivisionError` | Add `if trade_price == 0: return False` |
| 8 | `stop_loss_triggered` | No zero guard on `buy_price` | Medium | `buy_price = 0` → `ZeroDivisionError` | Add `if buy_price == 0: return False` |
| 9 | `EXCHANGE_RULES` fallback | OKX `prices_precision = 1` is symbol-agnostic | Medium | SHIB/USDT at $0.00001234 rounds to $0.00 | Always prefer live market precision; log warning when fallback used |
| 10 | `profit_pct` rounded to `fee_precision` | Semantically wrong field used for percentage precision | Low | Works numerically but misleading | Add `percentage_precision` field to `EXCHANGE_RULES` |
| 11 | `sell_amount_decimal_precision` | Defined in `EXCHANGE_RULES` but never used | Low | Dead configuration | Remove or implement |
| 12 | `ROUND_HALF_UP` for amounts | Could cause over-sell on 0.5 boundary | Low | Amount 0.000005 rounds to 0.00001 (2× intended) | Use `ROUND_DOWN` for amounts |
| 13 | `trade_spread_percentage_avg = spread_avg / price_avg × 100` | No zero guard on `trade_price_avg` | Low | `trade_price_avg = 0` → `ZeroDivisionError` | Add guard before division |
| 14 | `percentage_difference` in indicators | No guard if `v1 + v2 == 0` | Low | Both prices zero → `ZeroDivisionError` | Add `if v1 + v2 == 0: return 0` |

---

## 11. Conclusion & Remediation

### Overall Precision Safety: **Moderate** ⭐⭐⭐

The core profit/fee calculation in `SonarftMath.calculate_trade` is well-implemented — `Decimal` arithmetic with `ROUND_HALF_UP`, `str()` conversion to avoid float contamination, and proper fee-inclusive profit calculation. This is the most critical financial function and it is correct.

The main precision concerns are in the surrounding layers: price adjustment uses float throughout, and several division operations lack zero guards.

### Critical Fixes Required

1. **`np.mean/std` on empty list** (`sonarft_validators.py:88-89`):
   ```python
   if not historical_spread_percentage:
       return {'low': 0.0, 'medium': 0.0, 'high': 0.0}
   ```

2. **`bid_prices[0]` IndexError** (`sonarft_validators.py:54-57`):
   ```python
   if not bid_prices or not ask_prices:
       return False
   if bid_prices[0] == 0:
       return False
   ```

3. **`get_liquidity` formula** (`sonarft_indicators.py:342`):
   ```python
   # Replace dimensionally incorrect formula with:
   mid_price = (bids[0][0] + asks[0][0]) / 2
   liquidity = (bid_volume_sum + ask_volume_sum) / mid_price
   normalized_liquidity = min(max(liquidity / reference_volume, 0), 1)
   ```

### High Priority Fixes

4. **Medium volatility threshold** — remove `/ 100` (`sonarft_validators.py:180`)
5. **Zero guards** for `trade_price`, `buy_price` in slippage and stop-loss functions
6. **Log warning** when `EXCHANGE_RULES` fallback is used instead of live market precision

### Recommendations for Systematic Improvement

- **Extend `Decimal` usage** to price blending in `weighted_adjust_prices` — the monetary values flowing into `calculate_trade` should be `Decimal` from the start
- **Add input validation** to `calculate_trade` — reject negative prices, zero amounts, and `None` fee rates with explicit errors rather than silent returns
- **Add `percentage_precision`** to `EXCHANGE_RULES` for semantically correct profit percentage rounding
- **Use `ROUND_DOWN`** for order amounts to prevent over-sell edge cases
- **Add minimum notional validation** before order placement to prevent exchange rejections

---

*Generated as part of the SonarFT code review suite — Prompt 04: Financial Math & Precision Review*
*Previous: [trading-engine-analysis.md](./trading-engine-analysis.md)*
*Next: [05-indicator-pipeline.md](../prompts/05-indicator-pipeline.md)*
