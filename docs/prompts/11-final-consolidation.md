# Prompt 11 — Final Consolidation

**Focus:** Executive summary synthesizing all reviews  
**Category:** Post-Review Artifacts  
**Output File:** `docs/review/final-audit-report.md`  
**Run After:** All 10 prompts (01-10) must be completed first  
**Time Estimate:** 20-30 minutes  
**Prerequisites:** Have generated all 10 previous review documents  

---

## When to Use This Prompt

Use this prompt **after completing all 10 review prompts (01-10)**. It synthesizes all findings into an executive summary with prioritized action items.

**Best for:**
- Executive summary for stakeholders
- Prioritizing what to fix first
- Understanding critical issues
- Production readiness assessment

---

## Before Running This Prompt

Make sure you have completed and saved outputs from all 10 prompts:

- ✅ [01-architecture-structure.md](./01-architecture-structure.md) → `docs/architecture/overview.md`
- ✅ [02-async-concurrency.md](./02-async-concurrency.md) → `docs/architecture/async-concurrency.md`
- ✅ [03-trading-engine-logic.md](./03-trading-engine-logic.md) → `docs/trading/trading-engine-analysis.md`
- ✅ [04-financial-math.md](./04-financial-math.md) → `docs/trading/financial-math-review.md`
- ✅ [05-indicator-pipeline.md](./05-indicator-pipeline.md) → `docs/trading/indicator-analysis.md`
- ✅ [06-execution-exchange.md](./06-execution-exchange.md) → `docs/trading/execution-analysis.md`
- ✅ [07-configuration-runtime.md](./07-configuration-runtime.md) → `docs/configuration/config-review.md`
- ✅ [08-security-risk.md](./08-security-risk.md) → `docs/security/security-audit.md`
- ✅ [09-performance-scalability.md](./09-performance-scalability.md) → `docs/performance/performance-analysis.md`
- ✅ [10-code-quality-testing.md](./10-code-quality-testing.md) → `docs/code-quality/code-quality.md` (3 files)

---

## The Prompt

Copy and paste this into your AI chat:

```text
You have completed comprehensive reviews of the sonarft codebase across 10 different domains.

Your job now is to produce a **final consolidated audit report** that synthesizes findings from all reviews.

### 1. Executive Summary

Provide a 1-page summary that includes:
- Overall system readiness judgment
- Most critical findings (top 3)
- Highest-priority fixes
- Financial risk assessment
- Security risk assessment
- Recommendation: Not Ready / Prototype / Beta / Production-Ready

### 2. Findings Synthesis

Consolidate the most important findings from all documents:
- Cross-cutting architectural problems
- Systematic issues repeated in multiple modules
- Patterns of quality or concerns
- Highest-severity risks

### 3. Risk Ranking

Rank all issues by severity and impact:

| Rank | Issue | Category | Severity | Financial Impact | Recommendation |
|------|-------|----------|----------|------------------|-----------------|

Top 10 critical issues list.

### 4. Risk Heatmap

Create a table showing risk concentration:

| Domain | Count of Issues | Severity | Risk Level |
|--------|-----------------|----------|-----------|

Domains:
- Architecture
- Async/Concurrency
- Trading Logic
- Financial Math
- Indicators
- Exchange Integration
- Configuration
- Security
- Performance
- Code Quality

### 5. Readiness Scorecard

Assess each domain:

| Domain | Assessment | Readiness (%) |
|--------|-----------|---------------|

### 6. Production Readiness Score

Rate system 0-10:

- 0-2: Not viable, major issues
- 3-4: Very preliminary, concept stage
- 5-6: Early prototype, significant work needed
- 7-8: Near-complete, minor issues
- 9-10: Production-ready

Assign score: __/10

Justify score with key factors.

### 7. Top 20 Action Items

List the 20 highest-priority fixes:

| Priority | Action | Category | Effort | Blocking | Owner |
|----------|--------|----------|--------|----------|--------|

### 8. Go/No-Go Decision Framework

Define go/no-go criteria for each stage:

**Simulation Testing Stage**
- Criteria for safe simulation
- Blocking issues

**Paper Trading Stage**
- Criteria to move from simulation
- Blocking issues

**Real Trading Stage**
- Criteria to move to real
- Blocking issues

**Full Production Stage**
- Criteria for production
- Blocking issues

### 9. Timeline Estimate

Estimate effort to achieve production readiness:

| Phase | Tasks | Effort | Duration |
|-------|-------|--------|----------|

### 10. Risk Mitigation Strategy

For each Critical/High risk:
- Immediate mitigation
- Long-term remediation
- Testing to validate fix

### 11. Recommended Next Steps

In priority order:
1. (Most urgent)
2.
3.
...

### 12. Conclusion

Final thoughts on:
- System maturity
- Path to production
- Key success factors
- Timeline realism
```

---

## What This Generates

The AI will produce **`docs/review/final-audit-report.md`** containing:

- **Executive Summary** — One-page overview for executives
- **Findings Synthesis** — Top issues from all domains
- **Risk Ranking** — Top 20 issues prioritized
- **Risk Heatmap** — Visual risk assessment
- **Readiness Scorecard** — 0-10 score for each domain
- **Production Readiness Score** — Overall 0-10 system score
- **Top 20 Action Items** — Prioritized fixes with effort estimates
- **Go/No-Go Framework** — Criteria for each deployment stage
- **Timeline** — Effort estimate to production
- **Recommended Next Steps** — What to fix first

---

## How to Use This Document

**For Executives:**
- Read Executive Summary + Risk Ranking + Go/No-Go Framework

**For Engineering Teams:**
- Read Full Report + Top 20 Action Items
- Use for sprint planning

**For Product Managers:**
- Focus on Timeline and Readiness Score
- Use for release planning

**For Operations:**
- Read Go/No-Go Framework
- Reference for deployment decisions

---

## Next Steps

After Final Consolidation:

1. **Review the go/no-go framework** — Decide what stage you're at
2. **Prioritize top 20 items** — What to fix first?
3. **Create implementation plan** → Use [12-implementation-roadmap.md](./12-implementation-roadmap.md)
4. **Plan deployment** → Use [13-setup-operations-guide.md](./13-setup-operations-guide.md)

---

## Tips for Success

- **Use this for decision-making** — Should we go to production?
- **Share with stakeholders** — This is executive-friendly
- **Reference for prioritization** — Top 20 items guide the next weeks
- **Track progress against it** — Monitor fixes against recommendations

