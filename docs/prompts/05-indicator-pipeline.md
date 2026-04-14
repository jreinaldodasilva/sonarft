# Prompt 5 — Indicator Pipeline Review

**Focus:** Indicator calculations and signal generation correctness  
**Category:** Trading Logic & Safety  
**Output File:** `docs/trading/indicator-analysis.md`  
**Run After:** [00-master-instruction.md](./00-master-instruction.md)  
**Time Estimate:** 20-25 minutes  
**Prerequisites:** Have sonarft codebase uploaded to AI  

---

## When to Use This Prompt

Use this prompt to verify indicator calculations and signal generation. Important for understanding what signals trigger trades.

**Best for:**
- Verifying indicator formulas
- Checking for off-by-one errors
- Validating NaN handling
- Assessing signal reliability

---

## The Prompt

Copy and paste this into your AI chat (run [00-master-instruction.md](./00-master-instruction.md) first):

```text
Review the indicator subsystem in sonarft for correctness and reliability.

### 1. Indicator Implementation Audit

For each indicator (RSI, MACD, Stochastic, SMA, volatility, etc.):

| Indicator | Location | Data Source | Lookback | Correctness | NaN Handling |
|-----------|----------|-------------|----------|-------------|------------|

Check for each:
- **Correctness**: Does it implement the standard formula correctly?
- **Data slicing**: Are candles indexed correctly (no off-by-one)?
- **Lookback window**: Is there enough data before generating signals?
- **NaN handling**: What happens with missing or invalid data?
- **Edge cases**: First candle, insufficient data, zero values?

### 2. OHLCV Data Preprocessing

Examine:
- **Data loading** (how is OHLCV data loaded?)
- **Data validation** (are prices/volumes checked for validity?)
- **Data alignment** (when multiple timeframes used, are they synchronized?)
- **Missing data** (how are gaps handled?)
- **Timestamp accuracy** (are candle timestamps correct?)

### 3. Pandas & Pandas-TA Usage

Review:
- **DataFrame operations** (are they efficient?)
- **pandas-ta functions** (are they used correctly?)
- **Custom calculations** (are they correct?)
- **Performance** (are there repeated calculations that could be cached?)

### 4. Indicator-to-Signal Pipeline

Document the flow:
- Raw OHLCV data → Preprocessing → Indicators → Signal generation → Trading decision

For each indicator used in trading decisions:
- **What signal does it generate?**
- **Threshold values** (what value triggers a trade?)
- **How is it combined with other indicators?**
- **What's the risk if it's wrong?**

### 5. off-by-one Errors

Check for common issues:
- Candle indexing (is index 0 the oldest or newest candle?)
- Lookback window (is the window size correct?)
- Shifting operations (pandas.shift usage correct?)
- Alignment with trade timing (when is signal read vs. when is trade executed?)

### 6. Insufficient Lookback Windows

Identify:
- **First valid output** (at what candle index does each indicator become valid?)
- **Minimum data requirement** (for each indicator)
- **Risk** (could trades execute before indicators are ready?)

### 7. NaN & Invalid Data Handling

Examine:
- **NaN sources** (where do NaNs come from?)
- **NaN propagation** (do NaNs spread through calculations?)
- **NaN handling** (does code check for NaNs before using values?)
- **Risk** (could NaN values trigger bad trades?)

### 8. Signal Generation Correctness

For each indicator that generates trading signals:
- **Signal definition** (what value = buy signal, what value = sell?)
- **Examples** (show calculations with real numbers)
- **Edge cases** (what happens at extremes?)
- **False positive risk** (could it generate bad signals?)

### 9. Indicator Analysis Table

Create a comprehensive table:

| Indicator | Function | Lookback | First Valid | NaN Risk | False Positive Risk | Severity |
|-----------|----------|----------|-------------|----------|-------------------|----------|

### 10. Performance Analysis

Check:
- **Repeated calculations** (is same indicator computed multiple times?)
- **DataFrame overhead** (are copies made unnecessarily?)
- **Cache opportunities** (what could be cached?)
- **Computational cost** (how expensive is the indicator pipeline?)

### 11. Integration Testing Recommendations

Suggest:
- Test cases for each indicator
- Edge case values for testing
- Signal generation validation approach
- Performance benchmarks

### 12. Conclusion

Summarize:
- Indicator reliability assessment
- Critical issues found
- Recommendations for improvement
```

---

## What This Generates

The AI will produce **`docs/trading/indicator-analysis.md`** containing:

- **Indicator Implementation Audit** — Each indicator reviewed
- **Data Handling Assessment** — Data loading, validation, alignment
- **Off-by-One Analysis** — Index correctness
- **Signal Generation Review** — What triggers trades
- **Data Table** — Comprehensive indicator assessment
- **Performance Opportunities** — Caching, optimization
- **Testing Recommendations** — Test strategy for signals

---

## Common Issues Found

Indicator bugs that affect trading:
- ⚠️ Off-by-one errors on data indexing
- ⚠️ NaN values propagating unchecked
- ⚠️ Indicators operating on insufficient data initially
- ⚠️ Signal thresholds not matching documentation
- ⚠️ Data misalignment when using multiple timeframes

---

## Next Steps

1. Review `docs/trading/indicator-analysis.md`
2. Continue with [06-execution-exchange.md](./06-execution-exchange.md)

---

## Tips for Success

- **Trace data flow** — From OHLCV to signal
- **Check pandas operations** — Are they correct?
- **Look for NaNs** — They silently break calculations
- **Verify examples** — Ask AI to show actual calculations
- **Test edge cases** — First candle, high volatility, zero volume

