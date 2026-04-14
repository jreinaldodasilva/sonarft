# sonarft Code Review Prompt Suite

A complete framework for conducting structured, in-depth AI-assisted code reviews of the sonarft cryptocurrency trading system.

## Quick Navigation

### Getting Started
- **First time here?** Start with [Quick Start Guide](./00-quick-start-guide.md)
- **Need a specific prompt?** Browse the [Prompt Index](#prompt-index-by-category)

### Prompt Index by Category

#### Foundation
- [Master Instruction & Context](./00-master-instruction.md) — Core context for all reviews

#### Core Review Prompts (Pick What You Need)

**Architecture & Design** (2 prompts)
- [Prompt 1: Architecture & Project Structure](./01-architecture-structure.md)
- [Prompt 2: Async Design & Concurrency](./02-async-concurrency.md)

**Trading Logic & Safety** (4 prompts)
- [Prompt 3: Trading Engine & Strategy Logic](./03-trading-engine-logic.md)
- [Prompt 4: Financial Math & Precision](./04-financial-math.md)
- [Prompt 5: Indicator Pipeline](./05-indicator-pipeline.md)
- [Prompt 6: Execution & Exchange Integration](./06-execution-exchange.md)

**Operational & Infrastructure** (3 prompts)
- [Prompt 7: Configuration & Runtime Environment](./07-configuration-runtime.md)
- [Prompt 8: Security & Trading Risk](./08-security-risk.md)
- [Prompt 9: Performance & Scalability](./09-performance-scalability.md)

**Quality & Maintenance** (1 prompt)
- [Prompt 10: Code Quality, Testing & Refactoring](./10-code-quality-testing.md)

#### Post-Review Artifacts
- [Final Consolidation Prompt](./11-final-consolidation.md) — Executive summary across all reviews
- [Implementation Roadmap](./12-implementation-roadmap.md) — Structured execution plan
- [Setup & Operations Guide](./13-setup-operations-guide.md) — Deployment instructions

#### Reference
- [Best Practices & Standards](./99-best-practices.md) — Guidelines for all reviews

---

## Recommended Review Paths

### Quick Assessment (30 minutes)
Use only [Prompt 10](./10-code-quality-testing.md) for a rapid health check

### Complete System Audit (2-3 hours)
Run prompts in this order:
1. [Prompt 1](./01-architecture-structure.md) — Get overview
2. [Prompts 2-10](./02-async-concurrency.md) — Detailed reviews (any order)

### Production Readiness (4-5 hours)
1. Complete all 10 prompts (Prompts 1-10)
2. Run [Final Consolidation](./11-final-consolidation.md)
3. Generate [Implementation Roadmap](./12-implementation-roadmap.md)
4. Review [Setup & Operations Guide](./13-setup-operations-guide.md)

### Operations/Deployment Focus
Skip reviews, go directly to [Setup & Operations Guide](./13-setup-operations-guide.md)

---

## Document Organization

```
prompts/
├── README.md (this file)
├── 00-quick-start-guide.md
├── 00-master-instruction.md
├── 01-architecture-structure.md
├── 02-async-concurrency.md
├── 03-trading-engine-logic.md
├── 04-financial-math.md
├── 05-indicator-pipeline.md
├── 06-execution-exchange.md
├── 07-configuration-runtime.md
├── 08-security-risk.md
├── 09-performance-scalability.md
├── 10-code-quality-testing.md
├── 11-final-consolidation.md
├── 12-implementation-roadmap.md
├── 13-setup-operations-guide.md
└── 99-best-practices.md
```

---

## Key Features

- **Modular**: Each prompt is independent and can be used separately
- **Clear Dependencies**: Master instruction provides shared context for all prompts
- **Flexible**: Pick individual prompts or follow complete workflows
- **Professional**: Each document follows the same high-quality structure
- **Production-Focused**: Emphasis on safety, correctness, and readiness

---

## How to Use Each Prompt

1. **Copy the prompt text** from the relevant document
2. **Paste into your AI chat** (Claude, ChatGPT, etc.)
3. **Upload the sonarft codebase** to the AI
4. **Run the prompt** to generate documentation
5. **Save the output** to the recommended location (specified in each prompt)

---

## Integration with Generated Documentation

As you run prompts, organize generated output like this:

```
docs/
├── architecture/
│   ├── overview.md (from Prompt 1)
│   └── async-concurrency.md (from Prompt 2)
├── trading/
│   ├── trading-engine-analysis.md (from Prompt 3)
│   ├── financial-math-review.md (from Prompt 4)
│   ├── indicator-analysis.md (from Prompt 5)
│   └── execution-analysis.md (from Prompt 6)
├── configuration/
│   └── config-review.md (from Prompt 7)
├── security/
│   └── security-audit.md (from Prompt 8)
├── performance/
│   └── performance-analysis.md (from Prompt 9)
├── code-quality/
│   ├── code-quality.md (from Prompt 10)
│   ├── testing-strategy.md (from Prompt 10)
│   └── refactoring-roadmap.md (from Prompt 10)
├── review/
│   └── final-audit-report.md (from Final Consolidation)
├── roadmap/
│   ├── implementation-roadmap.md (from Roadmap)
│   └── advanced-execution-plan.md (optional)
└── operations/
    ├── setup-and-execution-guide.md (from Setup Guide)
    └── advanced-operations.md (optional)
```

---

## Workflow Recommendations

### For Individual Development
1. Read [Master Instruction](./00-master-instruction.md) once
2. Use individual prompts as needed
3. Track generated documents in `docs/` folder

### For Team Code Reviews
1. Assign prompts to team members
2. Each runs 2-3 related prompts
3. Consolidate findings with [Final Consolidation](./11-final-consolidation.md)
4. Use [Implementation Roadmap](./12-implementation-roadmap.md) for sprint planning

### For Production Deployment
1. Complete all reviews (Prompts 1-10)
2. Run Final Consolidation
3. Generate Implementation Roadmap
4. Use [Setup & Operations Guide](./13-setup-operations-guide.md) for deployment
5. Execute roadmap phases in priority order

---

## Support & Customization

These prompts are **templates, not prescriptions**. Feel free to:
- Customize severity definitions for your risk tolerance
- Add exchange-specific prompts
- Add trading-strategy-specific reviews
- Extend prompts for your architecture
- Combine prompts for your workflow

---

## Version
**v2.0** - Modularized and improved for flexible use

