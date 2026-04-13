# SonarFT — Financial Math & Precision Review

## 1. Precision Configuration

`decimal.getcontext().prec = 8` is set at module level in six files:

| File | Set? |
|---|---|
| `sonarft_bot.py` | Yes |
| `sonarft_search.py` | Yes |
| `sonarft_prices.py` | Yes |
| `sonarft_math.py` | Yes |
| `sonarft_execution.py` | Yes |
| `sonarft_validators.py` | Yes |
| `sonarft_helpers.py` | Yes |
| `sonarft_api_manager.py` | Yes |
| `sonarft_indicators.py` | Yes |

**Critical finding:** Setting `getcontext().prec` has **no effect** on any calculation in the codebase. Every financial calculation uses Python native `float`, not `decimal.Decimal`. The `getcontext` import is present in every file but is never used. This means all calculations are subject to IEEE 754 double-precision floating-point rounding errors.

---

## 2. Precision-Sensitive Function Inventory

| Function | File | Uses Decimal? | Float Risk |
|---|---|---|---|
| `get_weighted_prices` | `sonarft_api_manager.py` | No | VWAP accumulated in float — rounding error grows with depth |
| `get_weighted_price` | `sonarft_prices.py` | No | Same as above |
| `calculate_trade` | `sonarft_math.py` | No | All arithmetic in float, then `round()` |
| `weighted_adjust_prices` | `sonarft_prices.py` | No | Weight blend in float |
| `get_profit_factor` | `sonarft_indicators.py` | No | Linear interpolation in float |
| `verify_spread_threshold` | `sonarft_validators.py` | No | Spread ratio in float |
| `get_trade_dynamic_spread_threshold_avg` | `sonarft_validators.py` | No | Cross-product sum over 10×10 order book entries |
| `calculate_slippage_tolerance` | `sonarft_validators.py` | No | Median/IQR in float via numpy |
| `check_balance` | `sonarft_execution.py` | No | `trade_amount * price` in float |

---

## 3. Float Contamination Analysis

### VWAP (`sonarft_api_manager.py:get_weighted_prices`)

```python
bid_vwap = sum(price * volume for price, volume in bids) / total_bid_volume
```

With `depth=12` (default weight parameter), 12 float multiplications are accumulated. For BTC/USDT at ~$60,000, each `price * volume` term can be ~$600,000. Summing 12 such terms in float introduces rounding error in the 4th–5th decimal place — acceptable for price discovery but not for fee calculation.

### Fee Calculation (`sonarft_math.py:calculate_trade`)

```python
buy_fee_quote = round(buy_price * target_amount_buy * buy_fee_rate, buy_rules['fee_precision'])
```

Three float multiplications before rounding. For OKX (`fee_precision=8`), this is fine. For Binance (`fee_precision=8`, `prices_precision=2`), the price is rounded to 2 decimal places first, then multiplied — this is correct ordering.

**Issue:** `profit_percentage` is computed as:

```python
profit_percentage = round(((value_selling_with_fee - value_buying_with_fee) / value_buying_with_fee), sell_rules['fee_precision'])
```

`sell_rules['fee_precision']` is 8 for all exchanges. The profit percentage is stored as a raw ratio (e.g. `0.00012345`), not as a percentage. The threshold comparison in `sonarft_search.py` uses `profit_percentage >= percentage_threshold` where `percentage_threshold = 0.0001`. This is consistent — both are ratios. However, the field name `profit_percentage` is misleading (it is a ratio, not a percentage).

### Cross-Product Spread Calculation (`sonarft_validators.py:get_trade_dynamic_spread_threshold_avg`)

```python
trade_spread_sum = sum([
    (ask_price - bid_price) * min(ask_volume, bid_volume)
    for (bid_price, bid_volume) in buy_order_book['bids'][:10]
    for (ask_price, ask_volume) in sell_order_book['asks'][:10]
])
trade_volume_sum = sum([
    min(ask_volume, bid_volume)
    for (_, bid_volume) in buy_order_book['bids'][:10]
    for (_, ask_volume) in sell_order_book['asks'][:10]
])
trade_price_avg = trade_price_sum / 100
```

This computes a 10×10 = 100-element cross-product. `trade_price_avg` divides by hardcoded `100` regardless of how many entries are actually present. If either order book has fewer than 10 entries, the divisor is wrong.

```python
trade_price_sum = sum([
    ((ask_price + bid_price)/2)
    for bid_price, _ in buy_order_book['bids'][:100]   # slices up to 100
    for ask_price, _ in sell_order_book['asks'][:100]
])
trade_price_avg = trade_price_sum / 100  # wrong if < 100 entries
```

The outer loop uses `[:100]` but the divisor is still `100` — if either book has fewer than 100 entries, `trade_price_avg` is underestimated.

---

## 4. Rounding Strategy Assessment

| Exchange | `prices_precision` | `buy_amount_precision` | `fee_precision` | Assessment |
|---|---|---|---|---|
| OKX | 1 | 8 | 8 | Price rounded to 1 decimal — very coarse for high-value assets |
| Bitfinex | 3 | 8 | 8 | Reasonable |
| Binance | 2 | 5 | 8 | Amount rounded to 5 decimals — may cause minimum order size violations |

**Issue:** These precision values are hardcoded in `EXCHANGE_RULES` and do not reflect the actual per-symbol precision rules that exchanges enforce. Binance, for example, uses per-symbol `LOT_SIZE` and `PRICE_FILTER` filters. Using a fixed `prices_precision=2` for all Binance symbols will produce invalid orders for symbols with different tick sizes.

---

## 5. Numerical Edge Cases

| Case | Location | Risk | Remediation |
|---|---|---|---|
| `total_bid_volume == 0` in VWAP | `sonarft_api_manager.py:get_weighted_prices` | `ZeroDivisionError` | Add guard: `if total_bid_volume == 0: return 0.0, 0.0` |
| `value_buying_with_fee == 0` | `sonarft_math.py:calculate_trade` | `ZeroDivisionError` in `profit_percentage` | Guard before division |
| `previous_avg_price == 0` | `sonarft_indicators.py:get_short_term_market_trend` | `ZeroDivisionError` | Guard: `if previous_avg_price == 0: return 'neutral'` |
| `bids[0][0] + asks[0][0] == 0` | `sonarft_indicators.py:get_liquidity` | `ZeroDivisionError` | Guard before division |
| `weight < 0` | `sonarft_prices.py:weighted_adjust_prices` | Negative price blend | Clamp: `weight = max(0.0, min(1.0, weight))` |
| `profit_percentage` field name | `sonarft_math.py` | Misleading — is a ratio | Rename to `profit_ratio` or document clearly |
| `trade_price_avg` divisor hardcoded to 100 | `sonarft_validators.py` | Wrong average when order book < 100 entries | Use `len(entries)` as divisor |

---

## 6. Remediation Priority

1. **Replace all financial float arithmetic with `decimal.Decimal`** in `sonarft_math.py` — this is the only file where precision directly affects trade profitability decisions.
2. **Add zero-division guards** to `get_weighted_prices`, `calculate_trade`, `get_short_term_market_trend`, and `get_liquidity`.
3. **Fix the hardcoded `/ 100` divisor** in `get_trade_dynamic_spread_threshold_avg`.
4. **Clamp `weight` to `[0, 1]`** in `weighted_adjust_prices`.
5. **Load per-symbol precision from exchange API** (`exchange.markets[symbol]['precision']`) instead of hardcoded `EXCHANGE_RULES`.
