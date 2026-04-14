# Prompt 10 — Code Quality, Testing & Refactoring

**Focus:** Code quality, test coverage, and maintainability  
**Category:** Quality & Maintenance  
**Output Files:**  
  - `docs/code-quality/code-quality.md`
  - `docs/code-quality/testing-strategy.md`
  - `docs/code-quality/refactoring-roadmap.md`  
**Run After:** [00-master-instruction.md](./00-master-instruction.md) (can run independently)  
**Time Estimate:** 20-25 minutes  
**Prerequisites:** Have sonarft codebase uploaded to AI  
**Note:** This prompt generates 3 documents (good for separate concerns)

---

## When to Use This Prompt

Use this prompt for quick assessment or for detailed code quality review. Can be run standalone for 30-minute health check.

**Best for:**
- Quick code health assessment
- Identifying test gaps
- Planning refactoring
- Assessing documentation

---

## The Prompt

Copy and paste this into your AI chat:

```text
Review sonarft for code quality, maintainability, and test readiness.

### 1. Naming Consistency Audit
- Variable names descriptive?
- Function names clear?
- Class names clear?
- Constant naming (UPPER_CASE)?
- Abbreviations clear or confusing?

### 2. Module Documentation
- Module docstrings present?
- Class docstrings present?
- Function docstrings?
- Type hints documented?
- Docstring quality?

### 3. Type Annotations
- Parameter types hinted?
- Return types hinted?
- Variable types clear?
- Type coverage %?
- Consistency?

### 4. Code Size & Complexity
- Large files (>500 lines)?
- Large functions (>50 lines)?
- Cyclomatic complexity?
- Parameter count?

### 5. Duplication Audit
- Copy-pasted code?
- Similar logic patterns?
- Refactoring candidates?

### 6. Error Handling Consistency
- Exception types specific?
- Error recovery?
- Error logging?
- User messages clear?

### 7. Testing Gaps Analysis
- What's tested?
- Test coverage?
- Test quality?
- Edge cases tested?

Identify untested high-risk code:
- Financial calculations (MUST test)
- Error handling (MUST test)
- Async operations (MUST test)
- Exchange integration (MUST test)

### 8. Test-Friendly Code Assessment
- Dependency injection?
- Global state?
- External dependencies mockable?
- Behavior deterministic?

### 9. Logging Consistency
- Logging levels appropriate?
- Log messages descriptive?
- Debug logging adequate?
- Production logs too verbose?

### 10. Code Quality Scorecard

| Aspect | Score (1-10) | Assessment |
|--------|-------------|-----------|

Aspects: Readability, Documentation, Type safety, Error handling, Testability, Performance awareness, Security awareness, Standards adherence

### 11. Refactoring Roadmap

| Refactoring | Complexity | Impact | Priority |
|-------------|-----------|--------|----------|

Examples:
- Extract large function
- Create base class for similar classes
- Consolidate duplicate code
- Improve error handling
- Add type hints
- Improve documentation

### 12. Testing Strategy Recommendations
- Unit test targets?
- Integration test scenarios?
- Simulation tests?
- Property-based tests?
- Test infrastructure improvements?

### 13. Conclusion
- Code quality assessment
- Top refactoring priorities
- Testing gaps and recommendations
- Effort estimate for improvements
```

---

## What This Generates

The AI will produce **three documents**:

1. **`docs/code-quality/code-quality.md`**
   - Naming and documentation audit
   - Type annotation coverage
   - Code complexity assessment
   - Code quality scorecard

2. **`docs/code-quality/testing-strategy.md`**
   - Testing gaps analysis
   - Test coverage assessment
   - Testability of code
   - Specific test recommendations

3. **`docs/code-quality/refactoring-roadmap.md`**
   - Prioritized refactoring list
   - Effort and impact estimates
   - Timeline for improvements

---

## Common Issues Found

Code quality problems often found:
- ⚠️ Missing docstrings on functions/classes
- ⚠️ No type hints (especially in complex code)
- ⚠️ Large functions doing too much
- ⚠️ Copy-pasted code (refactoring candidate)
- ⚠️ Inadequate test coverage (especially financial code)
- ⚠️ Inconsistent error handling
- ⚠️ Poor naming making code hard to understand

---

## Why This Matters

Code quality directly affects:
- **Development speed** — Easy to understand code is fast to modify
- **Bug risk** — Well-tested code has fewer surprises
- **Maintenance cost** — Clear code costs less to maintain
- **Onboarding** — New developers need clear code
- **Safety** — Testable code is verifiable code

---

## Next Steps

After running this prompt:
1. Review all three generated documents
2. If you've run all 10 prompts, move to [11-final-consolidation.md](./11-final-consolidation.md)
3. Otherwise, any other prompt you need

---

## Tips for Success

- **Assess testing especially** — Trading code MUST be tested
- **Identify code smells** — Duplication, long functions, complex logic
- **Look at financial code** — Most critical for testing
- **Check error paths** — Often have gaps in testing
- **Prioritize refactoring** — What gives most benefit for effort?

---

## Quick Assessment Mode

If using this as a quick 30-minute audit:
- Focus on generated **code quality scorecard**
- Review **testing gaps** section
- Identify if system is ready for review/production
- Skip detailed refactoring planning

