# Quick Start Guide — sonarft Code Review Prompts

**When to Use:** First time using this prompt suite?  
**Time to Read:** 5-10 minutes  
**Next Step:** See recommended paths below

---

## What Is This?

This is a suite of **AI-powered code review prompts** designed specifically for the sonarft cryptocurrency trading system. Each prompt generates professional documentation covering a specific domain (architecture, trading safety, security, etc.).

---

## Three Ways to Use This Suite

### 🚀 Option 1: Quick Audit (30 minutes)
**Best for:** Quick health check or getting started

1. Read: [00-master-instruction.md](./00-master-instruction.md) (5 min)
2. Run: [10-code-quality-testing.md](./10-code-quality-testing.md)
3. Get quick assessment of code quality and testing gaps

**Output:** `docs/code-quality/code-quality.md`

---

### 🔍 Option 2: Complete System Audit (2-3 hours)
**Best for:** Comprehensive understanding of the system

**Read Foundation:**
1. [00-master-instruction.md](./00-master-instruction.md) (5 min)

**Run All Prompts in Order:**
1. [01-architecture-structure.md](./01-architecture-structure.md) — Understand overall design
2. [02-async-concurrency.md](./02-async-concurrency.md) — Check async safety
3. [03-trading-engine-logic.md](./03-trading-engine-logic.md) — Verify trading correctness (CRITICAL)
4. [04-financial-math.md](./04-financial-math.md) — Verify financial precision (CRITICAL)
5. [05-indicator-pipeline.md](./05-indicator-pipeline.md) — Check indicator correctness
6. [06-execution-exchange.md](./06-execution-exchange.md) — Verify exchange integration
7. [07-configuration-runtime.md](./07-configuration-runtime.md) — Check configuration safety
8. [08-security-risk.md](./08-security-risk.md) — Security audit
9. [09-performance-scalability.md](./09-performance-scalability.md) — Performance review
10. [10-code-quality-testing.md](./10-code-quality-testing.md) — Code quality assessment

**Consolidate Results:**
11. [11-final-consolidation.md](./11-final-consolidation.md) — Executive summary

**Output:** Complete documentation in `docs/` folder

---

### 📋 Option 3: Production Readiness (4-5 hours)
**Best for:** Before deploying to production

Follow **Option 2** (Complete System Audit), then:

12. [12-implementation-roadmap.md](./12-implementation-roadmap.md) — Create action plan
13. [13-setup-operations-guide.md](./13-setup-operations-guide.md) — Setup & operations

**Deliverables:**
- Complete audit documentation
- Prioritized fix roadmap
- Operational procedures

---

## Choosing Your Path

| Your Goal | Time | Recommended Path |
|-----------|------|------------------|
| Quick health check | 30 min | Option 1 |
| Comprehensive review | 2-3 hours | Option 2 |
| Production deployment | 4-5 hours | Option 3 |
| Specific domain review | 30-60 min | Pick individual prompts |
| Team code review | Variable | Assign prompts to team members |

---

## How Each Prompt Works

1. **Copy the prompt text** from the file
2. **Paste into your AI chat** (Claude, ChatGPT, etc.)
3. **Upload the sonarft codebase** to the AI
4. **Run the prompt** — AI generates documentation
5. **Save output** to recommended location (specified in each prompt)

---

## Understanding Dependencies

Some prompts should run in a specific order:

**Foundation First:**
- Always read [00-master-instruction.md](./00-master-instruction.md) once

**Architecture Before Details:**
- Run [01-architecture-structure.md](./01-architecture-structure.md) before other prompts
- It gives context for all other reviews

**Critical Reviews:**
- Prompts 3-6 are critical for trading safety
- Should be prioritized and reviewed carefully

**Results Consolidation:**
- [11-final-consolidation.md](./11-final-consolidation.md) requires all 10 prompts done first

**Implementation Planning:**
- [12-implementation-roadmap.md](./12-implementation-roadmap.md) requires Final Consolidation first

---

## Organizing Generated Documentation

As you run prompts, organize output like this:

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
│   └── implementation-roadmap.md (from Roadmap)
└── operations/
    └── setup-and-execution-guide.md (from Setup Guide)
```

---

## Tips for Success

### For Individual Developers
- Start with Option 1 for quick health check
- Use Option 2 for deeper understanding
- Reference specific prompts as you develop

### For Teams
- Assign different prompts to different reviewers
- Run Prompt 1 first (everyone reads architecture)
- Consolidate findings with Prompt 11
- Create roadmap with Prompt 12

### For Operations Teams
- Skip to [13-setup-operations-guide.md](./13-setup-operations-guide.md)
- You don't need full technical review
- Get deployment and operations knowledge

### For Product/Business
- Read the [00-master-instruction.md](./00-master-instruction.md) for context
- Focus on outputs from Prompts 8 (Security) and 12 (Roadmap)
- Use Final Consolidation for executive summary

---

## Need Help?

### First Time Here?
→ Read [00-master-instruction.md](./00-master-instruction.md)  
→ Then pick your path above

### Want a Specific Review?
→ See [README.md](./README.md) for prompt index

### Need More Context?
→ See [SEPARATION_STRATEGY.md](./SEPARATION_STRATEGY.md) for detailed planning

### Want Best Practices?
→ See [99-best-practices.md](./99-best-practices.md)

---

## Next Steps

**Ready to start?** Choose your path:

- [Quick Audit Path](./10-code-quality-testing.md) (30 min)
- [Complete Audit Path](./01-architecture-structure.md) (2-3 hours)  
- [Production Readiness Path](./01-architecture-structure.md) (4-5 hours)

Or visit [README.md](./README.md) for the index of all prompts.

