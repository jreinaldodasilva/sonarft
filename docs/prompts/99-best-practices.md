# Prompt 99 — Best Practices & Advanced Guidance

**Focus:** Cross-cutting guidance, terminology, patterns, and advanced techniques  
**Category:** Supporting Guidance  
**Output File:** `docs/review/best-practices-and-guidelines.md`  
**Reference Material:** Use alongside [00-master-instruction.md](./00-master-instruction.md) and any prompt  
**Time Estimate:** Variable (reference/lookup only)  
**Prerequisites:** Have all prior prompts available for context  

---

## What This Document Is

This is a **reference guide** containing shared rules, patterns, and best practices that apply across **all sonarft reviews**.

Think of it as the **common vocabulary and patterns** that all reviewers should understand.

---

## When to Use This Prompt

This prompt is **for documentation generation only** — it produces a reference guide that should be **printed or bookmarked** and consulted during code reviews.

Use when you need to generate:
- Pre-review documentation
- Shared terminology guide
- Consistency standards
- Common patterns & anti-patterns
- Output format specifications

---

## The Prompt

Paste this into your AI chat to generate comprehensive best practices documentation:

```text
You are a senior architect and code review expert specializing in cryptocurrency trading systems.

Generate comprehensive best practices and advanced guidance covering all aspects of sonarft code review.

This document serves as the reference standard for all code reviews.

### 1. Shared Core Principles

State the core principles that underlie ALL reviews:

1. **Safety First**: All design decisions must prioritize preventing capital loss
2. **Clarity**: Code must be understandable to the next maintainer
3. **Correctness**: Mathematical and logical accuracy is non-negotiable
4. **Precision**: Financial calculations use proper decimal handling
5. **Resilience**: Systems fail gracefully with clear error messages
6. **Testability**: Code can be validated independently

### 2. Terminology Standards

Define standardized terms used throughout all reviews:

**Trading Concepts**
- Trade (the act of buying or selling)
- Signal (indicator condition triggering consideration)
- Entry order (buy order)
- Exit order (sell order)
- VWAP (Volume Weighted Average Price)
- Spread (bid-ask gap)
- Fee (exchange trading fee)
- Slippage (price movement during execution)

**Technical Concepts**
- Indicator (RSI, MACD, Stochastic, SMA, Volume)
- Candle/OHLCV (Open, High, Low, Close, Volume)
- History window (lookback period for calculation)
- Synchronization (keeping multiple data sources aligned)
- Concurrency (multiple coroutines running simultaneously)
- WebSocket (real-time exchange data stream)

**Architecture Concepts**
- Boss (orchestrator coroutine managing multiple bots)
- Bot (per-symbol trading worker)
- Executor (order execution layer)
- Manager (API interaction abstraction)
- Signal detector (indicator evaluation)
- State machine (bot lifecycle state)

**Code Quality Concepts**
- Cohesion (how related are functions in a module?)
- Coupling (how dependent are modules on each other?)
- Composability (can utilities combine flexibly?)
- Testability (can code be unit tested?)

### 3. Common Code Patterns to Look For

#### Pattern 1 — Configuration Injection
Describe the pattern:
- Configuration loaded from JSON files
- Configuration passed to bot initialization
- Configuration immutable during execution

Explain:
- Why this pattern works
- Benefits (testability, reproducibility)
- Common mistakes (hardcoded values, mutable config)

#### Pattern 2 — Async/Await Coroutine Management
Describe:
- gather() for concurrent tasks
- Task cancellation on exit
- Error propagation from workers

Explain:
- Why this matters (avoiding zombie tasks)
- Common mistakes (forgotten cancellation, deadlocks)

#### Pattern 3 — Data Pipeline Processing
Describe:
- OHLCV data fetching
- Indicator calculation
- Signal generation
- Order placement

Explain sequential dependencies and data flow.

#### Pattern 4 — Error Handling Strategy
Describe:
- Try/except for recoverable errors
- Logging instead of silent failures
- Graceful degradation (continue if one signal fails)

Explain error categories and responses.

#### Pattern 5 — API Abstraction Layer
Describe:
- Manager abstracts exchange differences
- Common interface across exchanges
- Error mapping from exchanges

Explain benefits and common mistakes.

#### Pattern 6 — State Machine Transitions
Describe:
- Bot states (initializing, running, stopping, stopped)
- Valid transitions
- State-dependent behavior

Explain state isolation and guard conditions.

### 4. Anti-Patterns to Flag

List and explain anti-patterns that should NOT appear:

**Anti-Pattern 1 — Silent Failures**
- Issue: Errors logged but execution continues unchecked
- What to look for: Try/except with only pass or generic logging
- How to fix: Log ERROR level with context, possibly trigger shutdown

**Anti-Pattern 2 — Hardcoded Values**
- Issue: Constants embedded in code instead of configuration
- What to look for: Magic numbers in calculations
- How to fix: Move to configuration files

**Anti-Pattern 3 — Mutable Shared State**
- Issue: Multiple coroutines modifying same dictionary/list
- What to look for: Shared collections without locks
- How to fix: Use asyncio.Lock or immutable data passing

**Anti-Pattern 4 — Fire-and-Forget Coroutines**
- Issue: Creating tasks without tracking or awaiting
- What to look for: asyncio.create_task() without tracking
- How to fix: Store task references, cancel on exit

**Anti-Pattern 5 — Type Ambiguity**
- Issue: No type hints; unclear what types flow through
- What to look for: Missing annotations on function signatures
- How to fix: Add @dataclass, TypedDict, or function type hints

**Anti-Pattern 6 — Precision Loss**
- Issue: Using float for financial calculations
- What to look for: float() conversions or arithmetic
- How to fix: Use Decimal from decimal module

**Anti-Pattern 7 — Off-by-One Errors**
- Issue: Indicators calculated with wrong history window size
- What to look for: pandas iloc with hardcoded indices
- How to fix: Use pandas rolling() and properly validate lengths

**Anti-Pattern 8 — Missing Escape Hatches**
- Issue: No manual stop mechanism for runaway trading
- What to look for: No command to halt execution
- How to fix: Implement stop signal and cleanup

**Anti-Pattern 9 — Insufficient Logging**
- Issue: Errors occur but root cause unclear from logs
- What to look for: Missing context in log messages
- How to fix: Log state, parameters, and decisions

**Anti-Pattern 10 — Test Avoidance**
- Issue: Code untestable due to tight coupling
- What to look for: Hard dependencies on external services
- How to fix: Inject dependencies, separate concerns

### 5. Naming Conventions

Define consistent naming patterns:

**Constants**
- Format: UPPER_SNAKE_CASE
- Example: PROFIT_THRESHOLD_PERCENT = 0.5

**Classes**
- Format: PascalCase
- Example: SignalDetector, TradingBot

**Functions & Methods**
- Format: snake_case
- Example: calculate_vwap(), should_place_order()

**Boolean Functions/Properties**
- Prefix: is_, should_, has_
- Example: is_price_above_threshold(), should_execute()

**Private Methods**
- Prefix: _underscore
- Example: _validate_configuration()

**Configuration Keys**
- Format: snake_case in JSON
- Example: "profit_threshold_percent", "maximum_position_size"

**Exchange Methods**
- Verb-led: fetch_ohlcv, create_order, fetch_balance
- Example: exchange.fetch_ohlcv(), exchange.create_order()

### 6. Type Annotation Standards

Explain how to annotate types:

**Function Signatures**
```
def calculate_vwap(prices: list[float], volumes: list[float]) -> float:
```

**Complex Types**
```
from typing import TypedDict
class BotConfig(TypedDict):
    symbol: str
    amount: Decimal
    enabled: bool
```

**Async Functions**
```
async def run_bot(config: BotConfig) -> None:
```

**Dataclasses**
```
from dataclasses import dataclass
@dataclass
class Trade:
    symbol: str
    entry_price: Decimal
    exit_price: Decimal
```

### 7. Test Strategy Patterns

Describe how each component should be tested:

**Unit Tests**
- Test pure functions with known inputs/outputs
- Mock any external dependencies
- Validate edge cases

**Integration Tests**
- Test multiple components together
- Use simulated exchange data
- Validate data flows correctly

**Simulation Tests**
- Run bot against historical data
- Compare profitability metrics
- Validate signal detection accuracy

**Load Tests**
- Run multiple bots concurrently
- Measure CPU/memory usage
- Identify scaling bottlenecks

### 8. Documentation Standards

Explain documentation expectations:

**Docstrings**
- Every class: Purpose and usage
- Every public function: Purpose, parameters, return, examples
- Every complex algorithm: Explanation of logic

**Type Hints Are Documentation**
- They serve as inline documentation
- Don't require separate explanation

**Comments for Why, Not What**
- Code shows WHAT it does
- Comments explain WHY
- Example: "# VWAP requires volume > 0 to be meaningful"

**Configuration Comments**
- Document every config parameter
- Explain default value and range
- Example: "# Profit threshold in percentage (0.5 = 0.5%)"

### 9. Error Handling Classification

Explain error categories:

**Recoverable Errors**
- Exchange temporarily unavailable
- Network timeout
- Invalid API response
- Response: Log, retry, possibly skip signal

**Non-Recoverable Errors**
- Invalid configuration
- Insufficient capital for order
- Exchange account restricted
- Response: Log ERROR, shutdown cleanly

**Business Logic Errors**
- Trade signal invalid
- Price outside valid range
- Precision calculation issue
- Response: Log WARNING, skip trade, continue

**Critical Errors**
- Data corruption
- State inconsistency
- Unhandled exception
- Response: Log CRITICAL, shutdown immediately

Explain how each should be handled and logged.

### 10. Diagram Conventions

If using Mermaid diagrams, use these conventions:

**Architecture Diagrams**
- Rectangles for components
- Arrows for data flow
- Show async boundaries clearly

**Sequence Diagrams**
- Timeline with participants
- Messages between components
- Highlight critical sequences

**State Diagrams**
- Circles for states
- Arrows for transitions
- Label conditions on transitions

**Class Diagrams**
- Standard UML notation
- Show inheritance and composition
- Include key methods/properties

**Example Format:**
```
graph TD
    A[Signal Detector] -->|detects signal| B[Trade Executor]
    B -->|places order| C[Exchange API]
    C -->|order status| D[State Manager]
```

### 11. Output Format Standards

Explain how review outputs should be formatted:

**Finding Format:**
```
**CATEGORY: [Architecture|Trading|Code Quality|etc]**
**SEVERITY: [Critical|High|Medium|Low]**
**LOCATION:** [file.py, lines X-Y]
**FINDING:** [One-line issue summary]

[2-3 sentence detailed explanation]

**EVIDENCE:**
[Code snippet]

**RECOMMENDATION:**
[Specific fix]
```

**Pattern Format:**
```
**PATTERN: [Pattern Name]**
**LOCATION:** [file.py, lines X-Y]
[Explanation of why this pattern is good/problematic]
```

**Risk Format:**
```
**RISK: [Risk Name]**
**SEVERITY: [Critical|High|Medium|Low]**
**IMPACT:** [What bad thing could happen]
**MITIGATION:** [How to reduce/eliminate risk]
```

### 12. Cross-Prompt Integration

Explain how different prompts relate:

**Foundation → Specialized Reviews:**
- 00-master-instruction.md provides context for all prompts
- Specialized prompts (01-10) each focus on specific domain

**Specialized → Post-Review:**
- Findings from 01-10 feed into 11-final-consolidation.md
- Consolidation informs 12-implementation-roadmap.md

**Reading Order for Quick Audits:**
1. 00-master-instruction.md (5 min)
2. 03-trading-engine-logic.md (10 min)
3. 08-security-risk.md (10 min)
4. 11-final-consolidation.md (5 min)

**Reading Order for Complete Audits:**
1. 00-master-instruction.md
2. 01-architecture-structure.md
3. 02-async-concurrency.md
4. 03-trading-engine-logic.md
5. All others in order
6. 11-final-consolidation.md
7. 12-implementation-roadmap.md

### 13. Decision Trees

Provide decision trees for common scenarios:

**When to use simulation mode:**
- First time running system? → YES
- Making indicator changes? → YES
- Trusted system in production? → NO
- Testing new signal? → YES
- Going live with real capital? → NO first

**When to flag an issue as Critical:**
- Could cause capital loss? → YES
- Could leak API keys? → YES
- Could crash system? → YES → CRITICAL
- Could produce wrong signal? → YES → HIGH
- Could improve code clarity? → NO

**When to require code changes vs recommendations:**
- Security issue? → REQUIRE change
- Mathematical error? → REQUIRE change
- Code clarity? → RECOMMEND change
- Performance optimization? → DEPEND on impact

### 14. Advanced Techniques

Explain advanced patterns for experienced reviewers:

**Technique 1 — Data Flow Analysis**
Trace how data flows through the system:
- Where does data come from?
- What transformations occur?
- Where does it go?
- What assumptions exist?

**Technique 2 — Concurrency Analysis**
Analyze async coroutines:
- What runs concurrently?
- What must be sequential?
- Are there race conditions?
- Are there deadlock risks?

**Technique 3 — Numerical Stability Analysis**
Check financial calculations:
- Are precision settings correct?
- Can values overflow/underflow?
- Are rounding rules consistent?
- Can division by zero occur?

**Technique 4 — Risk Scenario Modeling**
Consider failure modes:
- What if exchange goes down?
- What if network fails mid-order?
- What if configuration is wrong?
- What if logic produces false signals?

**Technique 5 — Comparative Analysis**
Compare implementations across bots:
- Do all bots use same logic?
- Are there inconsistencies?
- Should logic be extracted to shared module?

### 15. When to Stop Reviewing

A review is complete when:

✅ All high-risk areas reviewed  
✅ No Critical findings remain  
✅ Security validated  
✅ Logic verified  
✅ Risks documented  
✅ Recommendations actionable  

Not required for complete review:
- ❌ Every line of code
- ❌ Optional performance tweaks
- ❌ Non-critical code cleanup
- ❌ All possible scenarios

**Time-boxed reviews:**
- Quick Audit: 30 minutes (highlights only)
- Standard Audit: 2-3 hours (depth review)
- Complete Audit: 4-5 hours (comprehensive)
- Production Readiness: 1-2 days (deep investigation + testing)

### 16. Escalation Procedures

Explain when to involve others:

**Escalate to Architecture Team if:**
- Fundamental design issue found
- Major refactoring needed
- Conflicts with overall design

**Escalate to Trading Team if:**
- Signal logic appears unsound
- Risk controls insufficient
- Profit calculation questionable

**Escalate to Security Team if:**
- Credential handling unsafe
- Input validation missing
- DoS vulnerability possible

**Escalate to DevOps if:**
- Deployment issue found
- Scaling concern identified
- Infrastructure dependency issue

### 17. Reviewer Resources

Summarize key reference materials:
- Python asyncio documentation
- CCXT exchange API documentation
- pandas-ta documentation
- Decimal precision documentation
- Trading terminology glossary
- sonarft architecture documents

Provide links to each.

### 18. Common Questions & Answers

**Q: What if impact is unclear?**
A: Flag as "Medium" and document the uncertainty. Let decision-makers decide.

**Q: What if there are many findings?**
A: Prioritize by severity (Critical > High > Medium > Low). Group by category. Focus on patterns.

**Q: What if code is working but unclear?**
A: Flag for clarity. Working code that breaks later is expensive.

**Q: What if I'm not expert in this area?**
A: That's okay. Document uncertainty level in your findings. Recommend expert review.

**Q: What if I disagree with the design?**
A: Document as recommendation, not critical issue, unless actual risk exists.

**Q: How detailed should findings be?**
A: Detailed enough that a developer could fix without asking questions.

### 19. Continuous Improvement

Explain how to stay current:

- Update this guide as patterns emerge
- Document new anti-patterns discovered
- Capture lessons learned from production
- Share breakthrough techniques with team

### 20. Quick Reference Checklist

Create a one-page checklist reviewers can print:

**Before Review**
- [ ] Read 00-master-instruction.md
- [ ] Know your review focus
- [ ] Have codebase uploaded
- [ ] Know output location

**During Review**
- [ ] Follow prompt exactly
- [ ] Document evidence
- [ ] Use standard format
- [ ] Check terminology consistency
- [ ] Cross-reference related areas

**After Review**
- [ ] Format findings properly
- [ ] Prioritize by severity
- [ ] Review for clarity
- [ ] Identify patterns
- [ ] Consolidate recommendations
```

---

## What This Generates

The AI will produce **`docs/review/best-practices-and-guidelines.md`** containing:

- **Shared Core Principles** — Why we review the way we do
- **Terminology Standards** — Common vocabulary
- **Common Code Patterns** — What good looks like
- **Anti-Patterns** — What bad looks like
- **Naming Conventions** — For code, config, types
- **Type Annotation Standards** — How to annotate
- **Test Strategy Patterns** — How to validate
- **Documentation Standards** — What good docs need
- **Error Handling Classification** — Error categories and responses
- **Diagram Conventions** — Standard visual formats
- **Output Format Standards** — How to present findings
- **Cross-Prompt Integration** — How prompts fit together
- **Decision Trees** — When to apply rules
- **Advanced Techniques** — For expert reviewers
- **When to Stop Reviewing** — Completion criteria
- **Escalation Procedures** — When to involve others
- **Reviewer Resources** — Key references
- **Common Questions** — FAQ section
- **Continuous Improvement** — How to keep this guide current
- **Quick Reference Checklist** — Printable reference

---

## How to Use This Document

**Print it out:**
- Two-page checklist works on one sheet (landscape)
- Full guide works as desk reference

**Bookmark it:**
- Reference during other reviews
- Check terminology
- Validate against patterns

**Share in team meetings:**
- Discuss decision trees
- Align on anti-patterns
- Establish team standards

**Update it:**
- Add discovered patterns
- Document team decisions
- Capture lessons learned

---

## Distribution

- **All Reviewers:** Print checklist, bookmark full guide
- **Junior Reviewers:** Use decision trees and checklist
- **Everyone:** Reference terminology page
- **Team Leads:** Use escalation procedures

---

## Critical Sections

Don't work without understanding:
- **Shared Core Principles** — Why we do this
- **Terminology Standards** — Common language
- **Anti-Patterns** — Know what to flag
- **Output Format** — How to present findings
- **Quick Reference** — Printer-ready reference

---

## Next Steps

1. **Read once** → Understand scope
2. **Reference during reviews** → Use for standardization
3. **Discuss with team** → Align on standards
4. **Bookmark for lookup** → Quick reference
5. **Update as needed** → Continuous improvement

