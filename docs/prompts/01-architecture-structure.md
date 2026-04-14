# Prompt 1 — Architecture & Project Structure

**Focus:** System organization, technology stack, and module design  
**Category:** Architecture & Design  
**Output File:** `docs/architecture/overview.md`  
**Run After:** [00-master-instruction.md](./00-master-instruction.md)  
**Time Estimate:** 20-30 minutes  
**Prerequisites:** Have sonarft codebase uploaded to AI  

---

## When to Use This Prompt

Use this prompt to understand the overall system organization, how modules interact, and the technology stack used in sonarft. **Run this first** as it gives context for all other prompts.

**Best for:**
- Getting overview of the system
- Understanding module responsibilities
- Identifying coupling and dependencies
- Planning other reviews

---

## The Prompt

Copy and paste this into your AI chat:

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

## What This Generates

The AI will produce **`docs/architecture/overview.md`** containing:

- **Technology Stack Table** — All dependencies listed
- **Module Inventory** — Each module documented with responsibility and dependencies
- **Architecture Diagram** — Visual representation of module relationships
- **Issues Summary** — Coupling and design problems identified
- **Recommendations** — How to improve architecture

---

## Next Steps

After this prompt completes:
1. Review the generated `docs/architecture/overview.md`
2. Move on to [02-async-concurrency.md](./02-async-concurrency.md) for async/concurrency review
3. Or jump to specific domains in other prompts

---

## Tips for Success

- **Share the output with the team** — Architecture understanding helps everyone
- **Use the diagram** as a reference for other reviews
- **Note dependencies** — They matter for other analyses
- **Review coupling** — High coupling often indicates refactoring needs

