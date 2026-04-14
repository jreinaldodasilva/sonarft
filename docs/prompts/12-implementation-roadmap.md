# Prompt 12 — Implementation Roadmap

**Focus:** Structured execution plan for fixes and improvements  
**Category:** Post-Review Artifacts  
**Output File:** `docs/roadmap/implementation-roadmap.md`  
**Run After:** [11-final-consolidation.md](./11-final-consolidation.md) must be completed first  
**Time Estimate:** 30-40 minutes  
**Prerequisites:** All 10 reviews + Final Consolidation complete  

---

## When to Use This Prompt

Use this prompt **after Final Consolidation** to create a detailed engineering roadmap that transforms findings into actionable tasks.

**Best for:**
- Sprint planning
- Work sequencing
- Dependency management
- Effort estimation
- Risk reduction planning

---

## What You'll Need

Before running this prompt, have ready:
- ✅ All 10 review documents (01-10)
- ✅ Final Consolidation report (Prompt 11)
- ✅ All finding summaries

Provide these to the AI: "Use all previously generated review documents as input"

---

## The Prompt

Copy and paste this into your AI chat:

```text
You are a senior technical program manager and software architect.

Your job is to generate a comprehensive technical roadmap based on all review documents you've analyzed.

The roadmap must transform issues and findings into specific, actionable engineering tasks that developers can execute.

### 1. Executive Roadmap Summary

Provide:
- Overall system readiness status before roadmap
- Estimated total effort (Small / Medium / Large / Enterprise)
- Estimated number of phases
- Primary risk domains
- Top architectural priorities for improvement

### 2. Issue-to-Task Conversion Matrix

For each significant issue found, create a task:

| Issue ID | Source | Affected Code | Severity | Task Description | Category | Complexity | Effort | Depends On | Validation |
|----------|--------|---------------|----------|------------------|----------|-----------|--------|-----------|-----------|

### 3. Phase-Based Implementation Plan

Group tasks into phases:

**Phase 0 — Critical Safety Fixes**
Focus:
- Trading correctness and logic
- Financial math safety
- Execution safety
- Fatal runtime risks

**Phase 1 — Stability & Reliability**
Focus:
- Async correctness
- Error handling and recovery
- Data validation
- Configuration validation

**Phase 2 — Security Hardening**
Focus:
- Secrets protection
- Input validation
- API security
- Safe file handling

**Phase 3 — Performance Optimization**
Focus:
- Latency optimization
- Memory efficiency
- Scalability improvements
- Monitoring and observability

**Phase 4 — Architecture Improvements**
Focus:
- Modularity and separation of concerns
- Dependency cleanup
- Code reusability
- Testing infrastructure

**Phase 5 — Enhancement & Polish**
Focus:
- Advanced indicators
- Feature additions
- User experience improvements
- Documentation

For each phase, document:
- Phase objectives and goals
- Tasks included (task IDs)
- Risk reduction impact
- Expected stability gains
- Success/exit criteria

### 4. Task Dependency Graph

Create a summary showing:
- Task prerequisites
- Blocking relationships
- Parallelizable tasks
- Critical path

### 5. Risk Reduction Mapping

For each phase:

| Phase | Critical Risks Before | Critical Risks After | Risk Reduction |
|-------|---------------------|---------------------|----------------|

### 6. Effort & Timeline Projection

For each phase:

| Phase | Tasks | Conservative Effort | Aggressive Estimate | Team Size | Duration |
|-------|-------|-------------------|-------------------|-----------| ---------|

### 7. Technical Debt Backlog

Lower-priority improvements:

| Task | Category | Benefit | Recommended Timeline |
|------|----------|---------|----------------------|

### 8. Testing & Validation Strategy

For each phase, define:
- Unit test targets
- Integration test scenarios
- System validation approach
- Regression testing plan
- Load testing requirements

### 9. Release Strategy Milestones

Define readiness gates:

**Milestone A — Safe Simulation Mode**
- Requirements
- Blocking issues
- Validation

**Milestone B — Paper Trading Mode**
- Requirements
- Blocking issues

**Milestone C — Limited Real Trading**
- Requirements
- Blocking issues

**Milestone D — Full Production Operation**
- Requirements
- Blocking issues

### 10. Success Metrics & Monitoring

Define measurable outcomes:

| Metric | Target | Measurement | Monitoring |
|--------|--------|-------------|-----------|

### 11. Developer Onboarding Plan

How will developers understand and execute this roadmap?

### 12. Final Roadmap Priorities

List the top 5 must-do items for production readiness.
```

---

## What This Generates

The AI will produce **`docs/roadmap/implementation-roadmap.md`** containing:

- **Issue-to-Task Matrix** — All issues converted to dev tasks
- **Phase-Based Plan** — 6 phases organized by priority
- **Dependency Graph** — Task sequencing
- **Risk Reduction** — How each phase reduces risk
- **Timeline & Effort** — Conservative and aggressive estimates
- **Release Milestones** — Go/no-go criteria
- **Success Metrics** — How to validate completion
- **Top 5 Priorities** — What to start with

---

## How to Use This Roadmap

**Week 1:**  
→ Execute Phase 0 (Critical Safety Fixes)  
→ Small team can parallelize

**Weeks 2-3:**  
→ Execute Phase 1 (Stability & Reliability)  
→ Requires full team

**Weeks 4-5:**  
→ Execute Phase 2 (Security)  
→ Parallel with Phase 1 work where possible

**Ongoing:**  
→ Technical debt backlog during downtime  
→ Performance optimization sprints

---

## Post-Roadmap Steps

1. Break down roadmap into sprints
2. Assign tasks to developers
3. Create CI/CD for validation
4. Track completion against milestones
5. Reference for deployment decisions

---

## Tips for Success

- **Use as sprint planning guide** — Convert to JIRA tickets
- **Track progress** — Which phase is the team in?
- **Adjust timeline** — Reestimate based on actual velocity
- **Validate at milestones** — Test before moving to next stage
- **Communicate status** — Share progress with stakeholders

---

## Next Steps

After generating this roadmap:

1. **Review with engineering team** — Do estimates feel right?
2. **Create sprint breakdown** — Convert to weekly/sprint tasks
3. **Assign owners** — Who owns which phase?
4. **Plan deployment** → Use [13-setup-operations-guide.md](./13-setup-operations-guide.md)
5. **Start Phase 0** — Begin critical fixes immediately

