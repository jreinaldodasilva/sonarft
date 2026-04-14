# sonarft — Comprehensive AI Code Review Prompt Suite

A complete framework for conducting structured, in-depth AI-assisted code reviews of the sonarft cryptocurrency trading system. This suite generates professional documentation covering architecture, trading safety, execution integrity, security, performance, and operational readiness.

---

## Quick Start Guide

**New to this prompt suite?** Start here:

1. **For a Quick Audit** (30 min): Use only [Prompt 10: Code Quality & Testing](#prompt-10--code-quality-testing--refactoring-review)
2. **For a Complete System Audit** (2-3 hours): Run all 10 review prompts in sequence (Prompts 1-10)
3. **For Production Readiness** (4-5 hours): Complete all reviews + [Final Audit](#final-consolidation-prompt) + [Implementation Roadmap](#roadmap-generation-prompt--fixes--improvements-implementation-plan)
4. **For Operations/Deployment Teams**: Skip to [Setup & Execution Guide](#setup-execution--operational-modes-guide-prompt)

**Typical Workflow:**
- Generate all review documents (1-2 hours for AI)
- Review findings and prioritize (~2-4 hours for human review)  
- Generate implementation roadmap (~30 minutes)
- Create sprint plan and deploy improvements

---

## Table of Contents

### Core Sections
1. [Master Instruction](#master-instruction) — Foundational guidance for all reviews
2. [Code Review Prompts](#code-review-prompts) — 10 detailed specialized reviews

### Review Prompts (Pick What You Need)
- [Prompt 1: Architecture & Project Structure](#prompt-1--architecture--project-structure)
- [Prompt 2: Async Design & Concurrency](#prompt-2--async-design--concurrency-review)
- [Prompt 3: Trading Engine & Strategy Logic](#prompt-3--trading-engine--strategy-logic-review)
- [Prompt 4: Financial Math & Precision](#prompt-4--financial-math--precision-review)
- [Prompt 5: Indicator Pipeline](#prompt-5--indicator-pipeline-review)
- [Prompt 6: Execution & Exchange Integration](#prompt-6--execution--exchange-integration-review)
- [Prompt 7: Configuration & Runtime Environment](#prompt-7--configuration--runtime-environment-review)
- [Prompt 8: Security & Trading Risk](#prompt-8--security--trading-risk-review)
- [Prompt 9: Performance & Scalability](#prompt-9--performance--scalability-review)
- [Prompt 10: Code Quality & Testing](#prompt-10--code-quality-testing--refactoring-review)

### Post-Review Artifacts
3. [Final Consolidation Prompt](#final-consolidation-prompt) — Executive summary across all reviews
4. [Implementation Roadmap](#roadmap-generation-prompt--fixes--improvements-implementation-plan) — Structured execution plan
5. [Setup & Operations Guide](#setup-execution--operational-modes-guide-prompt) — Deployment and operations instructions

---

## Master Instruction

Copy this instruction into your prompt to establish context for all code reviews:

```text
You are a senior Python engineer, async systems architect, quantitative trading reviewer, and security auditor.

Your job is to review the uploaded sonarft codebase and produce professional Markdown documentation.

sonarft is an async-first cryptocurrency trading system with:
- multi-bot concurrency
- multi-exchange support (via CCXT/CCXTpro)
- VWAP-based pricing logic
- technical indicators (RSI, MACD, Stochastic, SMA, volatility)
- simulation/paper-trading and live trading modes
- JSON-based configuration
- FastAPI/WebSocket server infrastructure
- ccxt / ccxtpro integration for exchange connectivity
- Docker deployment support

You must analyze the code with special attention to:
- correctness and logic soundness
- trading safety and financial risk
- async integrity and task management
- financial precision and calculation accuracy
- architecture quality and modularity
- security vulnerabilities and exposure
- performance and scalability characteristics
- testability and code maintainability

Important rules:
- Do not guess or fabricate details. If something is not present in the code, write: "⚠️ Not Found in Source Code"
- Cite specific files, classes, and functions whenever possible
- Use tables, diagrams, and structured formats for clarity
- Generate all documentation in proper Markdown
- Include Mermaid diagrams when they improve understanding
- Rank risks by severity: Low, Medium, High, Critical
- Provide concrete remediation steps, not vague observations
- Clearly separate confirmed issues from assumptions or questions

Each review prompt below must produce a separate Markdown document.
When working through multiple prompts, maintain consistency in terminology and risk ratings across all documents.
```

---

## Code Review Prompts

---

## Prompt 1 — Architecture & Project Structure

**Goal**: Understand the overall system organization, technology stack, and module design

**Output File**: `docs/architecture/overview.md`

```text
Analyze the sonarft project architecture and explain how the system is organized.

Cover the following areas:

### 1. Technology Stack Inventory

List all major dependencies and technologies:
- Python runtime version and compatibility
- Async framework libraries (asyncio, others)
- HTTP/API framework (FastAPI or similar)
- Financial data processing (pandas, pandas-ta, numpy)
- Exchange integration (ccxt, ccxtpro versions)
- Container technology (Docker version/base images)
- Logging approach and libraries
- Configuration file format and validation

### 2. Project Structure & Module Responsibilities

For each major Python module, describe:
- **Module name** and primary file(s)
- **Responsibility** (one sentence)
- **Key classes and functions**
- **Dependencies** (what it imports/depends on)
- **Responsibility boundaries** (what it does NOT do)

Key modules to analyze:
- API management layer (exchange connectivity)
- Configuration and runtime setup
- Strategy/search logic
- Execution engine
- Technical indicators system
- Price calculation system
- Math utilities
- Validation and safety checks
- Helper utilities
- Boss/orchestration layer

For each, identify:
- Does it mix concerns (trading logic + API calls, etc.)?
- Is there a clear dependency direction?
- Are responsibilities well-isolated?

### 3. Dependency Design Analysis

Examine:
- Are dependencies injected or hardcoded?
- Are there circular dependencies?
- Is there tight coupling between modules?
- What modules could be reused independently?
- What implicit dependencies exist (globals, imports)?

### 4. System Architecture Diagram

Create a Mermaid diagram showing:
- Major modules as boxes
- Dependency arrows between modules
- Direction of data/control flow
- Layering (if present: transport, API, logic, calculation layers)

### 5. Module Responsibility Matrix

Create a table:

| Module | Primary Responsibility | Key Dependencies | Coupling Level | Code Complexity |
|--------|----------------------|-----------------|----------------|-----------------|

### 6. Code Complexity Hotspots

Identify files with:
- Highest line count
- Most complexity (nested logic, many functions)
- Most dependencies
- Most concurrent operations

Report findings with file names and line ranges.

### 7. Conclusion

Summarize:
- Overall architectural clarity
- Obvious design patterns (if present)
- Mixing of concerns
- Modularity strengths and weaknesses
- Recommendations for structural improvement
```

---

## Prompt 2 — Async Design & Concurrency Review

**Goal**: Verify async/await correctness and identify concurrency risks

**Output File**: `docs/architecture/async-concurrency.md`

```text
Review all async behavior in the sonarft codebase.

Focus on these critical async patterns and risks:

### 1. Async/Await Correctness

Examine every async function and report:
- **Async function name** and location
- **What it does** (one sentence)
- **Awaited calls** (list every await, confirm it's awaited properly)
- **Non-awaited coroutines** (are any coroutines created but not awaited?)
- **Blocking operations inside async functions** (file I/O, network calls, expensive computation)
- **Risk level** (None / Low / Medium / High)

Common issues to find:
- Creating async tasks/coroutines without `await` or `.create_task()`
- Calling thread-blocking functions (time.sleep, blocking file I/O) inside async code
- No exception handling for task creation/awaiting
- Tasks that never complete or garbage-collect
- Race conditions on shared state

### 2. Task Management Analysis

Examine:
- **Task creation patterns** (asyncio.create_task, gather, etc.)
- **Task cleanup** (are tasks cancelled and awaited on shutdown?)
- **Dangling tasks** (any tasks that may be abandoned?)
- **Task cancellation handling** (CancelledError caught and handled?)
- **Long-running loops** (any while True loops? Do they yield control?)

### 3. Concurrency Synchronization

Check:
- **Shared mutable state** (what global/class variables are shared?)
- **Lock usage** (asyncio.Lock for critical sections?)
- **Deadlock risks** (any scenarios where locks could deadlock?)
- **Race conditions** (any concurrent access to shared data without locks?)
- **WebSocket message concurrency** (how are concurrent messages handled?)

### 4. Async/Await Error Handling

Verify:
- Are exceptions in tasks propagated or silently lost?
- Are timeout scenarios handled?
- Is connection loss handled gracefully?
- Can the system recover from failed async operations?

### 5. Concurrency Risk Table

Create a table of all concurrency concerns:

| Location | Pattern | Risk | Severity | Remediation |
|----------|---------|------|----------|------------|

### 6. Task Lifecycle Summary

Document:
- How tasks are created
- How they are monitored
- When they are cancelled
- How they are cleaned up
- Any edge cases in the lifecycle

### 7. Concurrency Flow Diagram

Create a Mermaid sequence or flowchart showing:
- Typical execution flow
- Where concurrency occurs
- Task creation and joining points
- Critical sections

### 8. Recommendations

Identify:
- Critical async bugs
- Refactoring opportunities
- Best-practice improvements
```

---

## Prompt 3 — Trading Engine & Strategy Logic Review

**Goal**: Verify trading logic correctness and safety for financial execution

**Output File**: `docs/trading/trading-engine-analysis.md`

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

## Prompt 4 — Financial Math & Precision Review

**Goal**: Audit all financial calculations for correctness and precision

**Output File**: `docs/trading/financial-math-review.md`

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

## Prompt 5 — Indicator Pipeline Review

**Goal**: Verify indicator calculations and signal generation correctness

**Output File**: `docs/trading/indicator-analysis.md`

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

## Prompt 6 — Execution & Exchange Integration Review

**Goal**: Verify safe and correct exchange integration and order execution

**Output File**: `docs/trading/execution-analysis.md`

```text
Review the exchange integration and order execution path in sonarft.

### 1. API Abstraction Layer

Examine:
- **API Manager class** (what does it do?)
- **Exchange instances** (how are exchange connections created?)
- **Library abstraction** (does code abstract away ccxt/ccxtpro differences?)
- **Method routing** (how are API methods chosen and called?)
- **Error handling** (how are API errors handled?)

### 2. Transport Layer Options

Document:
- **WebSocket usage** (for which operations? Which exchanges?)
- **REST fallback** (does REST fallback work when WebSocket fails?)
- **Automatic failover** (is failover automatic or manual?)
- **Reconnection logic** (how is reconnection handled?)
- **Message ordering** (are messages processed in order?)

### 3. Market Data Fetching

Review:
- **Order book fetch** (how is it fetched? How often?)
- **Ticker data** (how is current price obtained?)
- **Volume data** (how is volume for indicators obtained?)
- **Data staleness** (is data age considered?)
- **API rate limits** (are API limits respected?)

### 4. Order Placement Logic

Examine:
- **Order parameters** (how is amount, price, side specified?)
- **Order validation** (pre-flight checks?)
- **Order placement** (REST vs WebSocket?)
- **Order confirmation** (how is success verified?)
- **Failures** (what happens if order placement fails?)

### 5. Simulated Order Execution

For simulation mode, verify:
- **Simulated fills** (how are orders marked as filled?)
- **Partial fills** (are partial fills simulated correctly?)
- **Slippage** (is slippage modeled?)
- **Order timing** (when are orders marked filled relative to signals?)
- **Accuracy** (are simulations realistic?)

### 6. Partial Fill Handling

Check:
- **Partial fill detection** (is code aware of partial fills?)
- **Position tracking** (is filled amount tracked?)
- **Remaining amount** (is remainder handled correctly?)
- **Exit behavior** (does partial fill affect exit logic?)

### 7. Error Handling & Retries

Examine:
- **Connection errors** (timeout, network down, etc.)
- **API errors** (rate limit, invalid order, etc.)
- **Retry logic** (is there exponential backoff? Max retries?)
- **Silent failures** (could orders execute silently without confirmation?)
- **Error logging** (are errors logged for debugging?)

### 8. Order Cancellation & Cleanup

Review:
- **Order cancellation** (how are open orders cancelled?)
- **Exit cleanup** (are all exit orders placed and confirmed?)
- **Stale orders** (are old unmatched orders cleaned up?)
- **Shutdown behavior** (what happens to open orders on shutdown?)

### 9. Exchange-Specific Assumptions

For each supported exchange:
- **Minimum amounts** (are they enforced?)
- **Precision rules** (amount and price precision?)
- **Fee structure** (maker vs taker, understood?)
- **Limits** (rate limits, concurrent connections?)
- **Quirks** (any edge behaviors?)

### 10. API Abstraction Matrix

Create a table:

| Operation | Method Name | CCXT | CCXTpro | Error Handling | Tested |
|-----------|------------|------|---------|----------------|--------|

Operations to table:
- Fetch order book
- Fetch ticker
- Fetch OHLCV
- Place order
- Cancel order
- Fetch balance
- Fetch order status

### 11. Execution Flow Diagram

Create a Mermaid flowchart:
- Signal generated → Validation → Order placement → Confirmation → Tracking → Exit

### 12. Failures & Edge Cases Table

| Scenario | Handling | Risk | Severity |
|----------|----------|------|----------|

Scenarios to cover:
- Exchange down
- API rate limit hit
- Order partially filled
- Order rejected
- Network timeout
- WebSocket disconnect
- Duplicate order attempted
- Insufficient balance

### 13. Conclusion

Summarize:
- Exchange integration safety
- Critical issues found
- Production readiness assessment
```

---

## Prompt 7 — Configuration & Runtime Environment Review

**Goal**: Audit configuration system and runtime environment handling

**Output File**: `docs/configuration/config-review.md`

```text
Audit the configuration system and runtime environment handling in sonarft.

### 1. Configuration File Structure

Examine:
- **Format** (JSON, YAML, Python dict?)
- **Schema** (is there schema validation?)
- **Examples** (are example configs provided?)
- **Documentation** (are parameters documented?)
- **Defaults** (what are the defaults?)

Create a table of all configuration parameters:

| Parameter | Required | Type | Default | Purpose | Validation |
|-----------|----------|------|---------|---------|------------|

### 2. Configuration Loading Behavior

Document:
- **Entry point** (where is config loaded?)
- **File location** (where are config files expected?)
- **Environment overrides** (can environment variables override config?)
- **Merge behavior** (how are multiple configs merged?)
- **Fallback behavior** (what happens if config is missing?)

### 3. Per-Bot & Per-Client Configuration

If supported, explain:
- **Granularity** (what can be configured per-bot vs. globally?)
- **Inheritance** (do bots inherit from global config?)
- **Conflicts** (how are conflicts resolved?)
- **Isolation** (can bots affect each other?)

### 4. Environment Variable Usage

Examine:
- **Which vars are required** (API keys, secrets?)
- **Which are optional** (debug flags?)
- **Defaults** (what if env var is missing?)
- **Security** (are secrets ever logged?)

### 5. Defaults & Hardcoding Audit

Search for:
- **Hardcoded values** (grep for string/number literals)
- **Unsafe defaults** (could dangerous defaults cause problems?)
- **Missing parameters** (are all needed parameters in config?)

For each hardcoded value found, determine:
- Should it be configurable?
- Is the hardcoded value safe?

### 6. Docker Runtime Assumptions

If Docker is used, verify:
- **Base image** (is it appropriate, up-to-date?)
- **Working directory** (where does app run from?)
- **Config location** (where does Docker expect config files?)
- **Environment setup** (how are API keys passed?)
- **Volumes** (are volumes used for persistence?)
- **Entrypoint** (what's the entrypoint command?)

### 7. File Paths & History Storage

Examine:
- **Relative vs absolute paths** (which are used? Safe?)
- **Path construction** (are paths built safely without injection?)
- **Permission requirements** (do paths need special permissions?)
- **History storage** (where are trade logs/history stored?)
- **File rotation** (are log files rotated to prevent disk full?)

### 8. Path Safety & Traversal Risks

Check:
- **User-supplied paths** (can user input control file paths?)
- **Path traversal** (can .. in paths escape intended directory?)
- **Symlinks** (are symlinks resolved safely?)
- **Permissions** (are files created with safe permissions?)

### 9. Configuration Validation

Verify:
- **Schema validation** (is config structure validated?)
- **Type checking** (are parameter types checked?)
- **Range validation** (are min/max checked for numeric params?)
- **Dependency validation** (if A=X, then B must=Y?)
- **Error messages** (when validation fails, is error message clear?)

### 10. Configuration Issues Table

| Issue | Location | Type | Severity | Remediation |
|-------|----------|------|----------|------------|

Issue types:
- Hardcoded values (should be config)
- Missing validation
- Unsafe defaults
- Security exposure
- Missing documentation

### 11. Runtime Configuration Summary

Create a table of all runtime configuration:

| Aspect | Current Method | Safe? | Recommendation |
|--------|----------------|-------|-----------------|

Aspects:
- API key management
- Feature flags (simulation mode, etc.)
- Parameter overrides
- Performance tuning
- Logging control

### 12. Docker Configuration Review

If applicable:
- **Dockerfile analysis** (is it production-ready?)
- **docker-compose** (if used, is it correct?)
- **Container security** (running as root? Should be non-root)
- **Secrets handling** (how are secrets passed? Safely?)

### 13. Conclusion

Assess:
- Configuration system maturity
- Safety of defaults
- Readiness for production
- Recommendations for hardening
```

---

## Prompt 8 — Security & Trading Risk Review

**Goal**: Identify security vulnerabilities and operational trading risks

**Output File**: `docs/security/security-audit.md`

```text
Perform a comprehensive security and operational risk review of sonarft.

### 1. Secret & Credential Handling

Examine:
- **API keys** (how are they stored? Loaded?)
- **Secret keys** (database passwords, etc.?)
- **Logging** (are secrets ever logged? Grep for "key", "secret", "password" in logs)
- **Environment variables** (how are they managed?)
- **Secrets in config** (are secrets in config files? Should not be)
- **.gitignore compliance** (are secrets excluded from version control?)

Issues to identify:
- Secrets in source code or config files
- Secrets in logs or error messages
- Hardcoded credentials
- Unencrypted credential storage

### 2. Input Validation & Injection Risks

Check:
- **User input** (what input does the system accept?)
- **Command injection** (can user input execute commands?)
- **File path injection** (can user input manipulate file paths?)
- **JSON/SQL injection** (if database used, check SQL safety)
- **API input** (validation of API requests?)

### 3. File Path Safety

Examine:
- **Path construction** (are paths built safely?)
- **Path traversal** (can ../ escape intended directory?)
- **Symlinks** (are symlinks resolved safely?)
- **File permissions** (are files created with correct permissions?)

### 4. WebSocket Security

If WebSocket is used:
- **Authentication** (is WebSocket connection authenticated?)
- **Authorization** (does each connection have proper permissions?)
- **Message validation** (are received messages validated?)
- **DoS risk** (could message flood crash the system?)
- **JSON parsing** (is JSON parsing safe against large documents?)

### 5. API Exposure Risks

Examine:
- **API endpoints** (what does each endpoint do?)
- **Authentication** (is each endpoint authenticated?)
- **Rate limiting** (are rate limits enforced?)
- **Input validation** (what validates request parameters?)
- **Error messages** (do errors leak system information?)

### 6. Denial of Service (DoS) Risks

Identify:
- **Unbounded loops** (could a request cause infinite loops?)
- **Memory allocation** (could large requests cause memory exhaust?)
- **Computation** (could expensive computation block services?)
- **Connections** (could many connections crash the system?)
- **Queues** (could messages accumulate unbounded?)

### 7. Trading Safety Controls

Verify:
- **Simulation mode gate** (is it enforced? Can't trade live in simulation?)
- **Maximum position size** (is there a max?)
- **Maximum loss limit** (can losses be limited?)
- **Rate limiting** (how many orders per second/minute?)
- **Circuit breaker** (does system halt on errors?)
- **Manual stops** (can a human stop trading?)

### 8. Financial Risk Management

Check:
- **Collateral checks** (is balance checked before trading?)
- **Margin requirements** (if margin used, checked?)
- **Slippage protection** (max acceptable slippage enforced?)
- **Runaway trading** (what prevents infinite loss?)
- **Liquidity risk** (could large orders fail to fill?)

### 9. Logging & Monitoring

Examine:
- **What's logged** (trades, errors, connections?)
- **Log sensitivity** (are sensitive values logged? They shouldn't be)
- **Log storage** (where are logs stored? How long kept?)
- **Log rotation** (are logs rotated to prevent disk full?)
- **Monitoring** (is there alerting for errors/anomalies?)

### 10. Dependency Security

Check:
- **Dependency versions** (are versions pinned or open?)
- **Outdated deps** (any known vulnerabilities in dependencies?)
- **Supply chain** (are packages from trusted sources?)

### 11. Security Risk Table

| Risk Category | Specific Risk | Location | Severity | Likelihood | Mitigation |
|---------------|---------------|----------|----------|------------|-----------|

Risk categories:
- Secrets exposure
- Injection attacks
- DoS vulnerability
- Trading safety
- Financial risk
- Dependency risk

### 12. Operational Risk Table

| Risk | Scenario | Impact | Preventing Control |
|------|----------|--------|-------------------|

Scenarios:
- API key compromise
- Runaway trading
- Exchange connection loss
- Incorrect configuration
- Accidental real trading in simulation

### 13. Severity Assessment

For each finding:
- **Severity level** (Low / Medium / High / Critical)
- **Attack/failure scenario**
- **Proof-of-concept** (if possible, show how it could happen)
- **Financial impact**
- **Remediation steps**

### 14. Conclusion

Summarize:
- Critical security findings (if any)
- Critical trading safety findings
- Recommendations for hardening
- Production readiness assessment
```

---

## Prompt 9 — Performance & Scalability Review

**Goal**: Identify performance bottlenecks and scalability issues

**Output File**: `docs/performance/performance-analysis.md`

```text
Review sonarft for performance, scalability, and resource usage.

### 1. API Call Frequency Audit

Document:
- **How often is each exchange API called?**
- **Rate limiting** (are API rate limits respected?)
- **Unnecessary calls** (are there redundant or duplicate calls?)
- **Batching opportunities** (could calls be batched?)

Create a table:

| API Call | Purpose | Frequency | Rate Limit | Optimization Potential |
|----------|---------|-----------|------------|----------------------|

### 2. Order Book Fetching Analysis

Examine:
- **Frequency** (how often is order book fetched?)
- **Necessity** (is it fetched more than needed?)
- **Caching** (is data cached? For how long?)
- **Staleness** (max acceptable age of order book data?)
- **Cost** (API cost per fetch in rate limits?)

### 3. Data Processing Performance

Check:
- **DataFrame operations** (are they efficient?)
- **Repeated calculations** (is same calculation done multiple times?)
- **Memory copies** (are unnecessary copies made?)
- **Pandas efficiency** (are vectorized operations used?)
- **Custom loops** (are there inefficient loops that could be vectorized?)

### 4. Indicator Calculation Performance

For the indicator pipeline:
- **Computational cost** (how expensive is indicator computation?)
- **Frequency** (how often are indicators recalculated?)
- **Caching** (are results cached?)
- **Optimization** (could it be done more efficiently?)

### 5. Memory Usage Analysis

Examine:
- **Task lists** (do task lists grow unbounded?)
- **Logs** (are logs kept in memory? Could grow unbounded?)
- **Order history** (is history stored in memory or on disk?)
- **DataFrame size** (how large are DataFrames in memory?)
- **Memory growth** (over time, does memory usage grow?)

### 6. Bottleneck Identification

Identify:
- **Critical path** (what's the slowest operation in the trading decision pipeline?)
- **Sequential operations** (what could be parallelized?)
- **I/O blocking** (are there blocking I/O operations in async code?)

Create a bottleneck table:

| Bottleneck | Location | Frequency | Impact | Potential Improvement |
|-----------|----------|-----------|--------|---------------------|

### 7. Concurrency & Scaling

Examine:
- **Multi-bot scaling** (can multiple bots run concurrently? How many?)
- **Multi-symbol scaling** (can system scale to many symbols?)
- **CPU scaling** (will adding CPUs help?)
- **I/O bound** (is system I/O bound or CPU bound?)
- **Scalability limits** (what limits scaling?)

### 8. Cache & Optimization Opportunities

Identify:
- **Data that could be cached** (order books, indicator values?)
- **Computation that could be cached** (repeated calculations?)
- **Batch opportunities** (operations that could be batched?)
- **Algorithm improvements** (better algorithms available?)

### 9. Latency Analysis

For each critical operation:
- **Current latency** (if measurable)
- **Acceptable latency** (what's fast enough?)
- **Latency sources** (where does time go?)
- **Improvement potential** (how much faster could it be?)

### 10. Resource Usage Summary

Document:

| Resource | Current Usage | Peak Usage | Limit | Headroom |
|----------|---------------|-----------|-------|----------|

Resources:
- CPU (% utilization)
- Memory (MB used)
- Disk (MB/hour for logs)
- Network (API calls/second)

### 11. Load Testing Recommendations

Suggest:
- Test scenarios (single bot, 10 bots, 100 symbols?)
- Metrics to measure (latency, memory, API calls?)
- Tools to use (profiler, load generator?)
- Acceptable thresholds (what's good enough?)

### 12. Performance Optimization Roadmap

Create a prioritized list:

| Optimization | Effort | Impact | Priority |
|-------------|--------|--------|----------|

### 13. Conclusion

Summarize:
- Current performance assessment
- Critical bottlenecks
- Recommendations for optimization
```

---

## Prompt 10 — Code Quality, Testing & Refactoring Review

**Goal**: Assess code quality, test coverage, and refactoring needs

**Output Files**:
- `docs/code-quality/code-quality.md`
- `docs/code-quality/testing-strategy.md`
- `docs/code-quality/refactoring-roadmap.md`

```text
Review sonarft for code quality, maintainability, and test readiness.

### 1. Naming Consistency Audit

Check:
- **Variable names** (are they descriptive and consistent?)
- **Function names** (do they clearly describe what they do?)
- **Class names** (are they clear and follow conventions?)
- **Constant names** (are they in UPPER_CASE as convention?)
- **Abbreviations** (are abbreviations clear or confusing?)

Find and document:
- Poor names that hurt readability
- Inconsistent naming patterns

### 2. Module Documentation

Examine:
- **Module docstrings** (does each module have a docstring?)
- **Class docstrings** (are classes documented?)
- **Function docstrings** (are function purposes clear?)
- **Type hints** (are parameter types documented or annotated?)
- **Docstring quality** (are they complete and accurate?)

Create a table:

| Module | Has Docstring | Class Docs | Function Docs | Quality |
|--------|---------------|-----------|---------------|---------|

### 3. Type Annotations

Check:
- **Parameter types** (are parameters type-hinted?)
- **Return types** (are return types hinted?)
- **Variable types** (in complex code, are types unclear without hints?)
- **Type coverage** (what % of code has type hints?)
- **Consistency** (is type hinting used consistently?)

### 4. Code Size & Complexity

Identify:
- **Large files** (files > 500 lines? Should they be broken up?)
- **Large functions** (functions > 50 lines? Candidates for refactoring?)
- **Cyclomatic complexity** (deeply nested code, many branches?)
- **Parameter count** (functions with many parameters? Hard to use)

Table of concerns:

| File/Function | Lines | Complexity | Issue |
|---------------|-------|-----------|-------|

### 5. Duplication Audit

Search for:
- **Copy-pasted code** (two similar functions that should be one?)
- **Similar logic** (same pattern repeated in different places?)
- **Refactoring candidates** (functions that could be extracted?)

### 6. Error Handling Consistency

Examine:
- **Exception types** (are specific exceptions caught or broad Exception?)
- **Error recovery** (does code recover from errors or crash?)
- **Logging** (are errors logged for debugging?)
- **User messages** (are error messages clear and helpful?)

### 7. Testing Gaps Analysis

Document:
- **Existing tests** (what's tested? What's not?)
- **Test coverage** (can you measure code coverage?)
- **Test quality** (are tests thorough or superficial?)
- **Edge cases** (are edge cases tested?)

Identify high-risk code that's untested:
- Financial calculations (MUST be tested)
- Error handling (MUST be tested)
- Async operations (MUST be tested)
- Exchange integration (MUST be tested)

### 8. Test-Friendly Code Assessment

Check if code is testable:
- **Dependency injection** (can dependencies be mocked?)
- **Global state** (does code use globals that complicate testing?)
- **External dependencies** (can API calls be mocked?)
- **Determinism** (is behavior deterministic or does it depend on time/randomness?)

### 9. Logging Consistency

Examine:
- **Logging levels** (are INFO/DEBUG/ERROR used appropriately?)
- **Log messages** (are they descriptive?)
- **Debug logging** (can behavior be debugged from logs?)
- **Production logs** (too verbose? Will logs grow unbounded?)

### 10. Code Quality Scorecard

Create a summary:

| Aspect | Score (1-10) | Assessment |
|--------|-------------|-----------|

Aspects:
- Readability
- Documentation
- Type safety
- Error handling
- Testability
- Performance consideration
- Security awareness
- Adherence to standards

### 11. Refactoring Roadmap

Prioritize refactoring by impact:

| Refactoring | Complexity | Impact | Priority |
|-------------|-----------|--------|----------|

Examples:
- Extract large function into smaller functions
- Create base class for similar classes
- Consolidate duplicate code
- Improve error handling in specific modules
- Add type hints
- Improve documentation

### 12. Testing Strategy Recommendations

Propose:
- Unit test targets (which modules must have unit tests?)
- Integration test scenarios (what should be integration tested?)
- Simulation tests (trade logic validation?)
- Property-based tests (for financial calculations?)
- Test infrastructure improvements

### 13. Conclusion

Summarize:
- Overall code quality assessment
- Top refactoring priorities
- Testing gaps and recommendations
- Estimated effort for quality improvements
```

---

## Final Consolidation Prompt

**Goal**: Synthesize all reviews into executive summary and final assessment

**Output File**: `docs/review/final-audit-report.md`

After completing all 10 review prompts above, run this prompt:

```text
You have completed comprehensive reviews of the sonarft codebase across 10 different domains.

Your job now is to produce a **final consolidated audit report** that synthesizes findings from all reviews.

### Key Sections to Include:

1. **Executive Summary** (1 page)
   - Overall readiness judgment
   - Top 3 critical findings
   - Highest-priority fixes
   - Financial and security risk assessment
   - Recommendation: Not Ready / Prototype / Beta / Production-Ready

2. **Findings Synthesis**
   - Cross-cutting architectural problems
   - Systematic issues repeated in multiple modules
   - Quality patterns and concerns
   - Highest-severity risks

3. **Risk Ranking (Top 20)**
   - All issues ranked by severity and impact
   - Financial impact assessment
   - Recommendation for each

4. **Risk Heatmap**
   - Risk concentration by domain
   - Overall risk level by category

5. **Readiness Scorecard**
   - Assessment of each domain (0-10%)
   - Production readiness score (0-10)

6. **Top 20 Action Items**
   - Prioritized fixes with effort estimates

7. **Go/No-Go Framework**
   - Criteria for each stage (Simulation → Paper → Real → Production)

8. **Timeline Estimate**
   - Effort to achieve production readiness

9. **Recommendations**
   - Next immediate steps

10. **Conclusion**
```

---

## Roadmap Generation Prompt — Fixes & Improvements Implementation Plan

**Goal**: Transform review findings into actionable engineering roadmap

Run this **only after all 10 review prompts and Final Audit are complete**.

**Output File**: `docs/roadmap/implementation-roadmap.md`

[See original document for complete detailed prompt structure covering:]
- Issue-to-Task Conversion Matrix
- Phase-Based Implementation Plan (Phases 0-5)
- Dependency Graph
- Risk Reduction Mapping
- Effort & Timeline Estimation
- Technical Debt Backlog
- Testing & Validation Roadmap
- Release Strategy Milestones
- Success Metrics & Monitoring
- Developer Onboarding Plan

---

## Setup, Execution & Operational Modes Guide Prompt

**Goal**: Provide complete operational and deployment guidance

Run **after architecture and configuration reviews**.

**Output File**: `docs/operations/setup-and-execution-guide.md`

[See original document for complete detailed prompt structure covering:]
- System Overview
- Prerequisites & Requirements
- Installation Guide
- Configuration Guide
- Execution Guide
- Operational Modes (Simulation, Paper, Real Trading)
- Safe Deployment Workflow
- Logging & Monitoring
- Troubleshooting
- Testing Workflow
- Performance & Scaling
- Security Best Practices
- Backup & Recovery
- Upgrade & Maintenance
- Real Trading Readiness Checklist

---

## Best Practices for All Prompts

### Core Principles

1. **Never Guess** — If information cannot be found in code, write: "⚠️ Not Found in Source Code"

2. **Always Cite** — Reference specific files, functions, classes, and line numbers

3. **Use Tables** — Tables are better than prose for comparisons and structured data

4. **Include Diagrams** — Use Mermaid for architecture, flows, and relationships

5. **Be Actionable** — Don't just identify problems; include concrete fixes

6. **Consistent Severity** — Apply consistent levels: Low / Medium / High / Critical

7. **Financial Focus** — For a trading system, financial correctness is paramount

8. **Clear Assumptions** — Distinguish confirmed findings from assumptions

9. **Production Lens** — Always assess production readiness impact

10. **Maintain Consistency** — Use same terminology and risk ratings across all documents

---

## Document Organization

All generated documents will be organized in this structure:

```
docs/
├── architecture/          (Prompts 1-2)
├── trading/              (Prompts 3-6)
├── configuration/        (Prompt 7)
├── security/             (Prompt 8)
├── performance/          (Prompt 9)
├── code-quality/         (Prompt 10)
├── review/               (Final Audit)
├── roadmap/             (Implementation Roadmap)
└── operations/          (Setup & Operations)
```

---

## Quick Reference: Which Prompt to Use

| Need | Use This Prompt |
|------|-----------------|
| Quick 30-min health check | Prompt 10 (Code Quality) |
| Understand overall architecture | Prompt 1 (Architecture) |
| Verify trading safety | Prompts 3 + 4 (Trading + Math) |
| Check security | Prompt 8 (Security) |
| Production readiness | All prompts + Final Audit |
| Implementation plan | Roadmap prompt |
| Operations/Deployment | Setup & Operations guide |
| Full deep audit | Prompts 1-10 + Final Audit + Roadmap |

---

## Version Notes

**v2.0 (Current)**
- Improved structure and navigation
- Better quick-start guide
- Clearer table of contents
- More practical guidance on usage
- Better separation of concerns
- Output file locations clearly marked

