# Prompt 3 — Trading Engine & Strategy Logic Review

**Focus:** Trading logic correctness and execution safety  
**Category:** Trading Logic & Safety (⭐ CRITICAL)  
**Output File:** `docs/trading/trading-engine-analysis.md`  
**Run After:** [00-master-instruction.md](./00-master-instruction.md)  
**Time Estimate:** 25-30 minutes  
**Prerequisites:** Have sonarft codebase uploaded to AI  
**⚠️ CRITICAL:** This review focuses on financial correctness and trading safety

---

## When to Use This Prompt

Use this prompt to review the core trading logic that decides when to execute trades. **This is critical** for financial correctness.

**Best for:**
- Verifying trade detection logic
- Checking profitability calculations
- Validating safety gates
- Ensuring no accidental live trading

---

## The Prompt

Copy and paste this into your AI chat:

```text
Review the core trading logic in sonarft as a financial-safety-critical system.

This review focuses on correctness of trading decisions and execution safety.

### 1. Trade Detection Logic

Analyze:
- **Where trade opportunities are detected** (file and function)
- **Signals used** (which indicators/conditions trigger trades?)
- **Profitability calculation** (how is profit threshold computed?)
- **Risk of false positives** (could a bad signal trigger unwanted trades?)
- **Margin of safety** (how much buffer is there before executing?)

### 2. VWAP Calculation & Usage

Examine:
- **VWAP formula implementation** (is it correct?)
- **Data sources** (volume data consistency?)
- **Edge cases** (zero volume handling, missing data?)
- **Usage in pricing** (where is VWAP used for price decisions?)
- **Precision** (floating-point vs Decimal usage?)

### 3. Spread Calculation & Rules

Review:
- **Spread definition** (how is it calculated?)
- **Spread thresholds** (where are limits enforced?)
- **Profitability thresholds** (how much spread is required for profit?)
- **Risk adjustment** (does spread change with market volatility?)

### 4. Fee Handling & Profitability

Verify:
- **Exchange fees included** (are buy/sell fees deducted?)
- **Fee timing** (are fees included BEFORE deciding profitability or AFTER?)
- **Fee accuracy** (do fee computations match exchange specs?)
- **Net profit calculation** (is final profit correctly computed with all fees?)

### 5. Execution Gating & Safety Checks

Examine:
- **Pre-execution validation** (what checks happen before trade?)
- **Simulation mode gates** (is live trading prevented in simulation?)
- **Safety thresholds** (maximum loss, maximum position size?)
- **Operator controls** (can a human stop/pause execution?)
- **Risk of accidental live execution** (what could cause unintended real trades?)

### 6. Buy/Sell Trigger Logic

For each trade direction (buy/sell), document:
- **Entry signal** (what conditions trigger?)
- **Entry validation** (what prevents bad entries?)
- **Exit signal** (how is exit decided?)
- **Exit validation** (what guarantees safe exit?)
- **Order size calculation** (how much to trade?)

### 7. Rounding & Precision in Orders

Check:
- **Amount rounding** (how is order amount rounded?)
- **Price rounding** (how is order price rounded?)
- **Exchange minimums** (are minimums enforced?)
- **Precision loss** (can rounding cause profit loss?)

### 8. Trade Pipeline Flowchart

Create a Mermaid flowchart showing:
- Signal generation → Detection → Validation → Execution → Completion
- Decision branches and gating logic
- Risk checks and safeguards

### 9. Financial Risk Table

Create a table of trading safety issues:

| Issue | Location | Scenario | Financial Risk | Severity | Fix |
|-------|----------|----------|----------------|----------|-----|

### 10. Critical Logic Findings

List any critical defects:
- Logic that could cause incorrect trade decisions
- Safety gates that don't work
- Edge cases that break the system
- Fee handling errors
```

---

## What This Generates

The AI will produce **`docs/trading/trading-engine-analysis.md`** containing:

- **Trade Detection Analysis** — How trades are chosen
- **Profitability Calculation Review** — Correctness of profit logic
- **Safety Gate Assessment** — What prevents accidental badly-timed trades
- **Financial Risk Table** — Severity-ranked issues
- **Trade Pipeline Diagram** — Visual flow of trade decision process
- **Critical Findings** — Any show-stoppers for production

---

## Why This Matters

For a financial trading system:
- Wrong trade decisions = **direct financial losses**
- Fee handling bugs = **cumulative profit loss**
- Safety gate failures = **uncontrolled execution**
- No simulation mode gate = **accidental real trading**

---

## Expected Findings

Common trading logic issues:
- ⚠️ Profitability calculated AFTER fees not BEFORE
- ⚠️ Rounding causing small but systematic losses
- ⚠️ No protection against false positive signals
- ⚠️ Simulation/live trading mode not properly gated

---

## Next Steps

1. Review `docs/trading/trading-engine-analysis.md` carefully
2. **Immediately fix any Critical findings**
3. Continue with [04-financial-math.md](./04-financial-math.md) for mathematical precision

---

## Tips for Success

- **Focus on profitability logic** — This is the most critical part
- **Trace fee handling end-to-end** — Easy to miss fees in one place
- **Check simulation mode gate** — Accidental real trading must be impossible
- **Look for edge cases** — Small amounts, volatile markets, etc.

