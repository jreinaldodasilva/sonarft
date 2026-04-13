# SonarFT — Comprehensive AI Code Review Prompt Suite

Use this prompt suite to review the SonarFT Python crypto-trading codebase and generate structured documentation. The suite is designed for an AI reviewer and follows the modular-document style of the reference review document, but adapted to SonarFT’s async trading architecture, VWAP logic, indicator pipeline, execution flow, and configuration-driven design.

---

## Master Instruction

```text
You are a senior Python engineer, async systems architect, quantitative trading reviewer, and security auditor.

Your job is to review the uploaded SonarFT codebase and produce professional Markdown documentation.

SonarFT is an async-first cryptocurrency trading system with:
- multi-bot concurrency
- multi-exchange support
- VWAP-based pricing
- technical indicators (RSI, MACD, Stochastic, SMA, volatility)
- simulation/paper-trading mode
- JSON-based configuration
- FastAPI/WebSocket server
- ccxt / ccxtpro integration
- Docker deployment

You must analyze the code with special attention to:
- correctness
- trading safety
- async integrity
- financial precision
- architecture quality
- security
- performance
- testability

Important rules:
- Do not guess. If something is not present in the code, write: “⚠️ Not Found in Source Code”.
- Cite specific files, classes, and functions whenever possible.
- Prefer tables, bullet-free sections, and diagrams where useful.
- Generate documentation in Markdown.
- Include Mermaid diagrams when they improve understanding.
- Rank risks by severity: Low, Medium, High, Critical.
- Provide concrete remediation steps, not only observations.
- Separate confirmed issues from assumptions.

Each review prompt below must produce a separate Markdown document.
```

---

## Prompt 1 — Architecture & Project Structure

```text
Analyze the SonarFT project architecture and explain how the system is organized.

Cover the following:
1. Technology stack inventory
   - Python runtime
   - async libraries
   - FastAPI
   - pandas / pandas-ta
   - ccxt / ccxtpro
   - Docker
   - logging approach
   - configuration files

2. Project structure
   - describe each main module
   - explain responsibility boundaries
   - identify orchestration, strategy, analysis, infrastructure, and transport layers
   - note where responsibilities overlap or leak

3. Dependency design
   - confirm whether modules use dependency injection
   - detect tight coupling
   - identify circular or implicit dependencies

4. Documentation output
   - include a compact architecture summary
   - include a Mermaid diagram of the main module relationships
   - include a table for module responsibility mapping
   - highlight large or high-complexity files

Output document:
`docs/architecture/overview.md`
```

---

## Prompt 2 — Async Design & Concurrency Review

```text
Review all async behavior in the SonarFT codebase.

Focus on:
- async/await correctness
- blocking operations inside async functions
- use of asyncio.gather
- use of asyncio.create_task
- asyncio.Lock for shared mutable state
- WebSocket concurrency and message handling
- task cleanup and cancellation
- race conditions and deadlock risks
- long-running loop behavior

For each issue, state:
- file
- function
- what happens
- why it matters
- how to fix it

Add:
- a concurrency risk table
- a task lifecycle summary
- a Mermaid sequence or flow diagram if helpful

Output document:
`docs/architecture/async-concurrency.md`
```

---

## Prompt 3 — Trading Engine & Strategy Logic Review

```text
Review the core trading logic in SonarFT as a financial-safety-critical system.

Analyze:
- VWAP calculations
- spread calculations
- trade opportunity detection
- fee handling
- buy/sell trigger logic
- execution gating
- simulation mode behavior
- profit-threshold logic
- order sizing and rounding
- price adjustment rules based on market conditions

Verify whether the code correctly:
- avoids zero-division
- uses the proper OHLCV indices
- includes fees before deciding profitability
- protects against false-positive opportunities
- prevents accidental live execution in simulation mode

Deliverables:
- trade pipeline summary
- risk table
- Mermaid flowchart of the trading loop
- list of critical logic flaws with severity

Output document:
`docs/trading/trading-engine-analysis.md`
```

---

## Prompt 4 — Financial Math & Precision Review

```text
Audit all financial calculations in SonarFT.

Check:
- use of Decimal and precision settings
- float contamination in financial paths
- rounding strategy per exchange
- fee computation accuracy
- profit computation accuracy
- precision loss in price and amount calculations
- order book aggregation math

Identify:
- where calculations may drift
- where exchange-specific precision rules are missing or inconsistent
- where rounding happens too early or too late

Include:
- a table of all precision-sensitive functions
- a list of numerical edge cases
- remediation advice for each issue

Output document:
`docs/trading/financial-math-review.md`
```

---

## Prompt 5 — Indicator Pipeline Review

```text
Review the indicator subsystem in SonarFT.

Inspect:
- RSI
- MACD
- Stochastic indicators
- SMA
- volatility calculations
- support/resistance or trend helpers
- OHLCV preprocessing
- pandas-ta usage

Check:
- correctness of data slicing
- off-by-one errors
- insufficient lookback windows
- unexpected NaN handling
- indicator alignment with trade decisions
- performance issues caused by repeated DataFrame work

Deliverables:
- indicator-by-indicator evaluation table
- explanation of data flow from OHLCV to signal generation
- risk assessment for bad signal generation

Output document:
`docs/trading/indicator-analysis.md`
```

---

## Prompt 6 — Execution & Exchange Integration Review

```text
Review the exchange integration and order execution path.

Analyze:
- API abstraction layer
- WebSocket vs REST fallback behavior
- fetch order book / market data flow
- order placement logic
- simulated order execution
- partial fill handling
- error handling and retries
- cancellation and cleanup behavior
- exchange-specific assumptions

Check whether the code:
- correctly separates API access from trading logic
- handles exchange failures safely
- avoids duplicate or conflicting orders
- logs execution outcomes clearly
- protects against silent execution failures

Deliverables:
- execution flow summary
- exchange integration matrix
- failure-mode table

Output document:
`docs/trading/execution-analysis.md`
```

---

## Prompt 7 — Configuration & Runtime Environment Review

```text
Audit the configuration system and runtime environment handling in SonarFT.

Review:
- JSON configuration structure
- config loading behavior
- defaults and overrides
- per-bot / per-client configuration separation
- environment variable usage
- Docker deployment assumptions
- file paths and history storage
- missing config validation

Check for:
- hardcoded trading parameters
- unsafe fallback behavior
- invalid file access patterns
- fragile path handling
- missing schema validation

Deliverables:
- configuration inventory table
- runtime assumptions list
- recommended validation rules

Output document:
`docs/configuration/config-review.md`
```

---

## Prompt 8 — Security & Trading Risk Review

```text
Perform a security and operational risk review of SonarFT.

Analyze:
- secret handling
- API key exposure risks
- unsafe logging of sensitive data
- input validation
- file path safety
- WebSocket exposure
- denial-of-service risks
- trade safety controls
- maximum loss or runaway trading risks
- liquidity failure behavior

For each risk, specify:
- severity
- attack or failure scenario
- evidence in code
- mitigation recommendation

Deliverables:
- security risk table
- operational risk table
- critical findings section

Output document:
`docs/security/security-audit.md`
```

---

## Prompt 9 — Performance & Scalability Review

```text
Review SonarFT for performance, scalability, and resource usage.

Analyze:
- API call frequency
- repeated order book fetching
- unnecessary sequential work
- DataFrame overhead
- memory growth in logs or task lists
- cache opportunities
- concurrency scaling across bots and symbols
- bottlenecks in indicator or pricing workflows

Deliverables:
- performance bottleneck list
- optimization opportunities table
- scalability assessment
- prioritization by impact

Output document:
`docs/performance/performance-analysis.md`
```

---

## Prompt 10 — Code Quality, Testing & Refactoring Review

```text
Review SonarFT for code quality, maintainability, and test readiness.

Assess:
- naming consistency
- module docstrings
- type annotations
- function and class size
- duplication
- logging consistency
- error handling consistency
- testability of each module
- coverage gaps
- refactoring opportunities

Deliverables:
- code quality scorecard
- testing gaps table
- refactoring roadmap
- prioritized action list

Output documents:
`docs/code-quality/code-quality.md`
`docs/code-quality/testing-strategy.md`
`docs/code-quality/refactoring-roadmap.md`
```

---

## Final Consolidation Prompt

```text
After completing all review sections, produce a final consolidated audit.

The final report must:
- summarize the most important findings from all documents
- rank issues by severity and financial risk
- identify cross-cutting architectural problems
- call out the highest-priority fixes
- provide a production-readiness judgment
- include a concise executive summary

The final document must also include:
- a top-10 remediation list
- a risk heatmap table
- a readiness score from 0 to 10
- a recommendation: Not Ready / Prototype / Beta / Production-Ready

Output document:
`docs/review/final-audit-report.md`
```

---

## Required Output Format for Every Document

```text
Each generated Markdown document must use this structure:

# Title

## Executive Summary

## Scope

## Findings

## Severity Assessment

## Recommendations

## Supporting Tables

## Diagrams

## Conclusion
```

---

## Document Set

```text
docs/
├── architecture/
│   ├── overview.md
│   └── async-concurrency.md
├── trading/
│   ├── trading-engine-analysis.md
│   ├── financial-math-review.md
│   ├── indicator-analysis.md
│   └── execution-analysis.md
├── configuration/
│   └── config-review.md
├── security/
│   └── security-audit.md
├── performance/
│   └── performance-analysis.md
├── code-quality/
│   ├── code-quality.md
│   ├── testing-strategy.md
│   └── refactoring-roadmap.md
└── review/
    └── final-audit-report.md
```

---

## Usage Note

Run the prompts in order for a full audit. Use any single prompt independently for targeted review.

For the most useful results, ask the AI to:
- reference file names and function names
- quote exact logic only when necessary and within copyright-safe limits
- avoid vague claims
- produce Markdown that can be saved directly as documentation

---

# Roadmap Generation Prompt — Fixes & Improvements Implementation Plan

Use this prompt **after all review documents have been generated**. This prompt creates a structured execution roadmap to fix issues and implement improvements identified during the audit.

## Master Roadmap Prompt

```text
You are a senior technical program manager, software architect, and quantitative trading system reviewer.

Your job is to generate a **comprehensive technical roadmap** based on previously generated review documents.

Inputs:
- All review documents under docs/
- All findings, risks, and recommendations
- All severity classifications
- All performance, security, and trading safety issues

Your objective is to transform findings into an **actionable engineering roadmap** that can be executed by developers.

Important rules:
- Convert problems into implementation tasks
- Group related fixes into logical phases
- Order tasks by risk reduction priority
- Include dependencies between tasks
- Provide realistic execution sequencing
- Clearly separate mandatory fixes from optional improvements
- Focus strongly on trading safety and financial correctness

Never invent issues that were not identified.
If something lacks enough detail, write:
"⚠️ Requires Engineering Clarification"
```

---

## Roadmap Construction Requirements

Generate the roadmap using the following structure.

### 1. Executive Roadmap Summary

Provide:
- Overall system readiness status
- Estimated total effort level (Small / Medium / Large / Enterprise)
- Estimated number of implementation phases
- Primary risk domains (e.g., async safety, trading logic, security)
- Top architectural priorities

---

### 2. Issue-to-Task Conversion Matrix

Convert each issue into an actionable development task.

For each issue include:

| Field | Description |
|------|-------------|
| Issue ID | Unique identifier |
| Source Document | File where issue originated |
| Affected Files | File names |
| Severity | Low / Medium / High / Critical |
| Task Description | Concrete engineering work |
| Risk Category | Trading / Async / Security / Performance / Architecture |
| Fix Complexity | Low / Medium / High |
| Estimated Effort | Hours or Days |
| Dependencies | Other tasks required first |
| Validation Method | How correctness will be verified |

---

### 3. Phase-Based Implementation Plan

Group tasks into **phases** based on priority and dependencies.

Required phase categories:

Phase 0 — Critical Safety Fixes
Focus on:
- trading correctness
- financial math safety
- execution safety
- fatal runtime risks

Phase 1 — Stability & Reliability
Focus on:
- async correctness
- error handling
- concurrency stability
- data validation

Phase 2 — Security Hardening
Focus on:
- secret protection
- configuration safety
- API reliability

Phase 3 — Performance Optimization
Focus on:
- latency
- memory usage
- concurrency scaling

Phase 4 — Architecture Improvements
Focus on:
- modularization
- separation of concerns
- dependency cleanup

Phase 5 — Feature & Strategy Enhancements
Focus on:
- indicator optimization
- new trading logic improvements

For each phase include:

- Phase Objective
- Tasks Included
- Risk Reduction Impact
- Expected Stability Gains
- Exit Criteria

---

### 4. Dependency Graph

Create a dependency relationship summary between tasks.

Include:
- Task prerequisites
- Blocking relationships
- Parallelizable tasks

Use a Mermaid diagram when helpful.

---

### 5. Risk Reduction Mapping

Map each phase to risk reduction outcomes.

Include:

| Phase | Risk Before | Risk After | Impact Level |
|------|-------------|-------------|--------------|

Focus especially on:
- financial loss risks
- incorrect trading decisions
- concurrency failure risks

---

### 6. Effort & Timeline Estimation

Estimate development effort.

Include:

| Phase | Effort (Days) | Team Size | Duration Estimate |
|------|----------------|------------|-------------------|

Provide:
- conservative estimate
- aggressive estimate
- recommended team size

---

### 7. Technical Debt Backlog

Create a backlog of lower-priority improvements.

Include:

- refactoring tasks
- documentation gaps
- test improvements
- logging improvements

Each item must include:
- priority score
- implementation benefit
- recommended timeline window

---

### 8. Testing & Validation Roadmap

Define how each phase will be validated.

Include:

- unit test targets
- integration test targets
- simulation tests
- regression tests
- load tests

Include specific validation strategies for:

- trading logic correctness
- async task safety
- financial calculations
- exchange execution behavior

---

### 9. Release Strategy Plan

Define staged release readiness milestones.

Required milestones:

Milestone A — Safe Simulation Mode
Milestone B — Controlled Paper Trading
Milestone C — Limited Real Trading
Milestone D — Production Deployment

For each milestone include:

- readiness requirements
- blocking issues
- validation criteria
- rollback strategy

---

### 10. Success Metrics Definition

Define measurable system-quality metrics.

Examples:

- trade success accuracy
- execution latency
- error rate
- memory growth rate
- recovery success rate
- profitability signal correctness

Each metric must include:

- measurement method
- acceptable thresholds
- monitoring frequency

---

## Final Roadmap Output Document

The roadmap must be saved as:

`docs/roadmap/implementation-roadmap.md`

---

## Required Roadmap Output Format

```text
# Implementation Roadmap — SonarFT

## Executive Summary

## Issue Conversion Matrix

## Phase-Based Implementation Plan

## Dependency Graph

## Risk Reduction Mapping

## Effort & Timeline Estimation

## Technical Debt Backlog

## Testing & Validation Strategy

## Release Strategy

## Success Metrics

## Final Implementation Priorities

## Conclusion
```

---

## Optional Advanced Roadmap Extension (Recommended)

If sufficient data exists, also generate:

- Gantt-style execution timeline
- Sprint-ready task breakdown
- Risk heatmap visualization
- Developer role assignment suggestions
- CI/CD pipeline upgrade recommendations

Output optional extensions to:

`docs/roadmap/advanced-execution-plan.md`

---

## Usage Recommendation

Run this roadmap prompt **only after all review documents are completed**.

This ensures:
- all issues are accounted for
- priorities are correct
- roadmap sequencing is accurate
- engineering effort is realistic

