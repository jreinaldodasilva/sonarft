# sonarft Prompt Suite Separation Strategy

## Overview

This document outlines the best way to separate the comprehensive prompt suite into multiple documents for better organization, usability, and maintenance.

---

## Current State vs. Recommended State

### Current: Single 47KB Document ❌
```
sonarft_comprehensive_ai_review_prompts.md (1490 lines)
├── Quick Start Guide
├── Table of Contents
├── Master Instruction
├── Prompt 1 (~350 lines)
├── Prompt 2 (~280 lines)
├── Prompt 3 (~290 lines)
├── Prompt 4 (~330 lines)
├── Prompt 5 (~330 lines)
├── Prompt 6 (~320 lines)
├── Prompt 7 (~320 lines)
├── Prompt 8 (~330 lines)
├── Prompt 9 (~280 lines)
├── Prompt 10 (~300 lines)
├── Final Consolidation (~180 lines)
├── Roadmap (~200 lines)
├── Setup & Operations (~150 lines)
└── Best Practices & Format (~100 lines)
```

**Problems:**
- Difficult to find specific prompts
- Hard to copy/paste individual prompts
- No clear file naming for programmatic access
- Mixing concerns (foundation, reviews, artifacts)

---

## Recommended: 16-Document Modular Structure ✅

### Three-Tier Organization

#### Tier 1: Foundation Documents (2 files)
Keep these separate as they're shared context:
- `00-quick-start-guide.md` — Entry point for new users
- `00-master-instruction.md` — Shared context for all prompts

#### Tier 2: Individual Review Prompts (10 files)
One file per prompt, organized by category:

**Architecture & Design**
- `01-architecture-structure.md` — Prompt 1
- `02-async-concurrency.md` — Prompt 2

**Trading Logic & Safety** (Critical)
- `03-trading-engine-logic.md` — Prompt 3
- `04-financial-math.md` — Prompt 4
- `05-indicator-pipeline.md` — Prompt 5
- `06-execution-exchange.md` — Prompt 6

**Operational & Infrastructure**
- `07-configuration-runtime.md` — Prompt 7
- `08-security-risk.md` — Prompt 8
- `09-performance-scalability.md` — Prompt 9

**Quality & Maintenance**
- `10-code-quality-testing.md` — Prompt 10

#### Tier 3: Post-Review Artifacts (4 files)
Run these AFTER individual prompts:
- `11-final-consolidation.md` — After all 10 prompts
- `12-implementation-roadmap.md` — After Final Consolidation
- `13-setup-operations-guide.md` — After architecture/config reviews
- `99-best-practices.md` — Reference document

#### Tier 4: Hub Document (1 file)
- `README.md` — Index and navigation (already created)

---

## File Structure in docs/prompts/

```
docs/prompts/
├── README.md                              ← NEW: Hub & Navigation
├── 00-quick-start-guide.md                ← NEW: Entry point
├── 00-master-instruction.md               ← NEW: Shared context
│
├── [ INDIVIDUAL PROMPTS - 10 files ]
├── 01-architecture-structure.md           ← NEW
├── 02-async-concurrency.md                ← NEW
├── 03-trading-engine-logic.md             ← NEW
├── 04-financial-math.md                   ← NEW
├── 05-indicator-pipeline.md               ← NEW
├── 06-execution-exchange.md               ← NEW
├── 07-configuration-runtime.md            ← NEW
├── 08-security-risk.md                    ← NEW
├── 09-performance-scalability.md          ← NEW
├── 10-code-quality-testing.md             ← NEW
│
├── [ POST-REVIEW ARTIFACTS - 4 files ]
├── 11-final-consolidation.md              ← NEW
├── 12-implementation-roadmap.md           ← NEW
├── 13-setup-operations-guide.md           ← NEW
├── 99-best-practices.md                   ← NEW
│
├── [ BACKUP / HISTORICAL ]
├── sonarft_comprehensive_ai_review_prompts.md.backup
└── sonarft_comprehensive_ai_review_prompts.md (KEEP AS-IS for now)
```

---

## Benefits of Separation

### 1. **Usability** ✓
- Users can quickly find the prompt they need
- Browse by category or use case
- Easier to share specific prompts with team members

### 2. **Maintainability** ✓
- Update a specific prompt without risk of breaking others
- Easier to track versions per prompt
- Clear responsibility per file

### 3. **Programmatic Access** ✓
- Scripts can easily fetch individual prompts
- CI/CD can organize prompts by type
- Easy integration with prompt management tools

### 4. **Discoverability** ✓
- README helps new users understand the suite
- Each document is focused, easier to understand
- Clear dependency relationships visible

### 5. **Flexibility** ✓
- Pick and combine prompts for custom workflows
- Easy to extend individual prompts without refactoring
- Different teams can use different subsets

---

## Implementation Plan

### Phase 1: Create New Documents (Start Here)
1. Create `README.md` as navigation hub ✅ (DONE)
2. Create `00-quick-start-guide.md` from Quick Start section
3. Create `00-master-instruction.md` from Master Instruction section
4. Create individual prompt files (01-10) from Prompts 1-10 sections
5. Create `11-final-consolidation.md` from Final Consolidation section
6. Create `12-implementation-roadmap.md` from Roadmap section
7. Create `13-setup-operations-guide.md` from Setup Guide section
8. Create `99-best-practices.md` from Best Practices section

### Phase 2: Validation
9. Verify all content migrated correctly
10. Test all cross-references work
11. Ensure consistency across documents

### Phase 3: Cleanup
12. Keep original comprehensive file as backup/historical reference
13. Add note in comprehensive file pointing to individual documents
14. Optional: Archive original file (but keep accessible)

---

## File Size Estimates

Current single file: ~47KB

After separation:
```
00-quick-start-guide.md                ~3 KB
00-master-instruction.md               ~4 KB
01-architecture-structure.md           ~5 KB
02-async-concurrency.md                ~4 KB
03-trading-engine-logic.md             ~4 KB
04-financial-math.md                   ~5 KB
05-indicator-pipeline.md               ~4 KB
06-execution-exchange.md               ~5 KB
07-configuration-runtime.md            ~5 KB
08-security-risk.md                    ~5 KB
09-performance-scalability.md          ~4 KB
10-code-quality-testing.md             ~4 KB
11-final-consolidation.md              ~3 KB
12-implementation-roadmap.md           ~4 KB
13-setup-operations-guide.md           ~3 KB
99-best-practices.md                   ~2 KB
README.md (navigation hub)             ~3 KB
                          TOTAL:      ~63 KB (files are smaller but more numerous)
```

**Note:** Total size increases slightly due to per-file formatting, but each file is much more manageable.

---

## Naming Convention Explained

### Numbering System
- `00-*` = Foundation/shared files (read first)
- `01-10` = Individual prompts (review domain by domain)
- `11-13` = Post-review artifacts (run after reviews complete)
- `99-*` = Reference/utility files (consult as needed)

### Naming Format
`NN-short-descriptive-name.md`
- `NN` = Sequence number for sorting
- `short-descriptive-name` = Clear file purpose
- Lowercase with hyphens for consistency

---

## Navigation Strategy

### For README.md Users
The hub document will:
- Explain what each prompt does
- Show prerequisites and dependencies
- Recommend reading order
- Group by category
- Link to each file

### For Direct File Access
Each individual prompt file should start with:
```markdown
# Prompt N — [Full Title]

Goal: [One-line description]
Output File: `docs/trading/trading-engine-analysis.md` (or relevant output)
Prerequisites: [What you need to read first]
Time to Run: [15-30 min, 30-60 min, etc.]

---

## When to Use This Prompt

[Use case description]

---

## The Prompt
```

---

## Recommended Usage Workflows

### Use Case 1: I need to review trading logic
```
1. Read: 00-master-instruction.md
2. Run: 03-trading-engine-logic.md
3. Run: 04-financial-math.md
4. Run: 05-indicator-pipeline.md
5. Run: 06-execution-exchange.md
→ Review output docs in docs/trading/
```

### Use Case 2: I want a quick 30-minute audit
```
1. Read: 00-quick-start-guide.md
2. Run: 10-code-quality-testing.md
→ Get quick health check
```

### Use Case 3: Full production readiness audit
```
1. Read: 00-master-instruction.md
2. Run: 01-10 in order (or assign to team)
3. Run: 11-final-consolidation.md
4. Run: 12-implementation-roadmap.md
→ Full analysis with prioritized fixes
```

---

## Backward Compatibility

### Original File Options
1. **Keep as-is** — Leave as historical reference
2. **Archive** — Move to `_archive/` folder
3. **Convert to index** — Turn into automated index (not recommended)
4. **Delete** — Remove once new structure verified

**Recommendation:** Keep the original as backup until you've verified the new structure works for your workflow.

---

## Implementation Effort

### Quick Version (Minimal Time)
- Copy/paste sections into new files
- Use same formatting
- Minimal additional work
- **Time: 30-45 minutes**

### Full Version (Better Quality)
- Create custom README with links
- Add metadata to each file (goal, time, prereqs)
- Cross-reference between files
- Add table of contents to each
- **Time: 2-3 hours**

---

## Next Steps

1. **Decide on the separation approach** (which option below?)
   - Option A: Just split sections into individual files (simple)
   - Option B: Add metadata and cross-references (recommended)
   - Option C: Full rebuild with enhanced navigation (comprehensive)

2. **Choose handling of original file**
   - Keep as backup
   - Archive in folder
   - Delete after verification

3. **Implement the separation**
   - I can help you create all the individual files
   - I can create custom README with navigation
   - I can add metadata and cross-references

---

## Recommendation

**Best approach for your use case:**
- **Implement Option B** (add metadata and cross-refs)
- **Keep original file** as reference
- **Create README.md** as hub (already done ✓)
- **Number files** for easy navigation
- **Group by category** (architecture, trading, ops, quality)

This gives you:
- ✅ Modularity (easy to use individual prompts)
- ✅ Navigation (README helps users find what they need)
- ✅ Metadata (context about what each prompt does)
- ✅ Flexibility (mix and match prompts for custom workflows)
- ✅ Maintainability (update individual prompts easily)

---

Would you like me to proceed with creating the individual prompt files using this structure?

