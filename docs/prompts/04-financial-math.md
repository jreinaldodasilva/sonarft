# Prompt 4 — Financial Math & Precision Review

**Focus:** Financial calculation correctness and numerical precision  
**Category:** Trading Logic & Safety (⭐ CRITICAL)  
**Output File:** `docs/trading/financial-math-review.md`  
**Run After:** [00-master-instruction.md](./00-master-instruction.md)  
**Time Estimate:** 25-30 minutes  
**Prerequisites:** Have sonarft codebase uploaded to AI  
**⚠️ CRITICAL:** Rounding errors multiply across thousands of trades  

---

## When to Use This Prompt

Use this prompt to audit all financial calculations for correctness and precision. **This is critical** — rounding errors compound and directly impact profitability.

**Best for:**
- Verifying Decimal vs float usage
- Checking rounding strategies
- Validating fee calculations
- Assessing mathematical correctness

---

## The Prompt

Copy and paste this into your AI chat:

```text
Audit all financial calculations in sonarft with a focus on precision and correctness.

Financial systems MUST be precise. Rounding errors multiply across thousands of trades.

### 1. Precision Settings Inventory

Examine the code for:
- **Decimal precision setup** (is getcontext().prec set? Where?)
- **Which operations use Decimal vs float** (should all monetary amounts use Decimal?)
- **Float contamination risk** (where do floats leak into calculations?)
- **Rounding strategy** (where is rounding explicit? Where is it implicit?)

### 2. Financial Calculation Audit

For each calculation in the system, verify:

| Calculation | Location | Uses Decimal? | Rounding Strategy | Edge Cases | Risk Level |
|-------------|----------|---------------|-------------------|------------|-----------|

Calculations to check:
- VWAP computations
- Spread calculations
- Fee deductions
- Profit/loss calculations
- Order sizing and amount computations
- Price adjustments
- Exchange minimum requirements

### 3. Precision-Sensitive Functions

List all functions that touch money:
- **Function name and location**
- **Input types** (Decimal, float, int, string?)
- **Output types**
- **Any rounding or precision loss?**
- **Any assumptions about input precision?**

### 4. Fee Computation Accuracy

Verify for each exchange:
- **Is fee calculation correct?** (taker vs maker fees?)
- **Is fee applied before or after spreading?**
- **Does fee change with market conditions?**
- **Are fees included in profit calculation?**
- **Example calculation** (with numbers proving correctness)

### 5. Profit Calculation Deep Dive

For the profit threshold logic:
- **Formula** (show exact calculation)
- **Inputs** (buy price, sell price, amount, fees)
- **Example** (concrete example with numbers)
- **Edge cases** (very small amounts, very tight spreads, high fees)
- **Risks** (what math errors could occur?)

### 6. Order Book & Aggregation Math

If order books are aggregated:
- **Aggregation formula** (volume-weighted or simple average?)
- **Precision in aggregation**
- **Edge cases** (missing levels, size limits?)

### 7. Rounding Edge Cases

Document:
- When rounding happens (too early? too late?)
- Impact of rounding (profit/loss?)
- Examples of rounding errors
- Recommendations for fixing rounding

### 8. Exchange-Specific Precision Rules

For each exchange, verify:
- **Minimum amount** (what's the smallest order?)
- **Amount precision** (decimal places allowed?)
- **Price precision** (decimal places allowed?)
- **Code enforcement** (are these rules checked in the code?)

### 9. Numerical Stability Issues

Check:
- Zero-division risks (any 1/x operations?)
- Overflow risks (numbers getting very large?)
- Underflow risks (numbers getting very small?)
- NaN/Inf risks (when could these occur?)

### 10. Precision Audit Table

| Function | Issue | Severity | Example | Fix |
|----------|-------|----------|---------|-----|

### 11. Conclusion & Remediation

Summarize:
- Overall precision safety
- Critical fixes needed
- Recommendations for systematic improvement
```

---

## What This Generates

The AI will produce **`docs/trading/financial-math-review.md`** containing:

- **Precision Inventory** — How precisionl settings are configured
- **Decimal vs Float Analysis** — Where float contamination risks exist
- **Calculation Audit** — Each financial calculation reviewed
- **Rounding Strategy Review** — When/how rounding happens
- **Edge Case Analysis** — Small amounts, high fees, tight spreads
- **Numerical Stability** — Division, overflow, underflow risks
- **Fixes for Each Issue** — Concrete remediation steps

---

## Why This Matters

For a financial trading system:
- **Precision loss = profit loss** (compounds over time)
- **Rounding errors = systematic bias** (usually in exchange's favor)
- **Float contamination = unpredictable results** (especially across exchanges)
- **Missing edge cases = failures in extreme conditions**

---

## Example Issues to Find

Common financial math bugs:
- ⚠️ Fee calculated with float instead of Decimal
- ⚠️ Rounding happens too early (before final calculation)
- ⚠️ Amount rounded but price not, or vice versa
- ⚠️ Division by zero possible with zero volume
- ⚠️ Profit threshold comparison uses float comparison (imprecise)

---

## Next Steps

1. Review `docs/trading/financial-math-review.md` very carefully
2. **Flag all Critical/High severity issues immediately**
3. Continue with [05-indicator-pipeline.md](./05-indicator-pipeline.md)

---

## Tips for Success

- **Trace every financial operation** — Follow money from start to finish
- **Check Decimal setup** — Is context().prec correct? Is it preserved?
- **Watch for implicit rounding** — Division, integer math, comparison
- **Test edge cases** — Very small amounts, very tight spreads, high fees
- **Verify examples** — Ask AI to show actual numbers proving correctness

