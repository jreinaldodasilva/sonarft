# Master Instruction — Context for All Code Reviews

**Purpose:** Shared foundational context for all review prompts  
**Read this:** Once, before running any other prompts  
**Time:** 5-10 minutes  
**Next:** Pick your review path from [00-quick-start-guide.md](./00-quick-start-guide.md)

---

## Copy This Instruction Into Your AI Chat

Use this instruction to set up the AI reviewer with proper context. Include this when pasting any other prompt from this suite.

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

Each review prompt must produce a separate Markdown document.
When working through multiple prompts, maintain consistency in terminology and risk ratings across all documents.
```

---

## How to Use This Instruction

### Step 1: Prepare Your AI Chat
1. Start a new conversation with your AI (Claude, ChatGPT, etc.)
2. Paste the **Master Instruction** above
3. Wait for AI to acknowledge (it will confirm it understands the context)

### Step 2: Upload the Codebase
Upload the sonarft codebase files to the AI. Ensure you include:
- All Python source files (*.py)
- Configuration files (JSON, YAML, etc.)
- Docker files (if present)
- Requirements/dependency files
- Key documentation

### Step 3: Run a Specific Prompt
Keep the AI in the same conversation, then:
1. Go to the specific prompt file you want to run (e.g., [01-architecture-structure.md](./01-architecture-structure.md))
2. Copy the prompt text
3. Paste it into the chat with the AI
4. AI will generate documentation based on that prompt

### Step 4: Save the Output
Each prompt specifies where to save its output. Organize generated files in your `docs/` folder.

---

## Understanding the AI's Role

The AI acts as a **senior technical reviewer** analyzing the code for:

| Focus Area | What AI Looks For |
|-----------|------------------|
| **Correctness** | Logic errors, off-by-one bugs, edge case handling |
| **Trading Safety** | Financial correctness, profit calculations, execution risks |
| **Async/Concurrency** | Race conditions, deadlocks, task management |
| **Financial Precision** | Decimal vs float, rounding errors, fee handling |
| **Architecture** | Modularity, separation of concerns, dependencies |
| **Security** | Secret exposure, input validation, injection risks |
| **Performance** | Bottlenecks, inefficiency, scalability limits |
| **Code Quality** | Readability, documentation, testability |

---

## Important Notes

### About "⚠️ Not Found in Source Code"
The AI will write this when something is not present in the actual code. This is **intentional**:
- Better than guessing or making assumptions
- Highlights what might be missing
- Identifies areas that might need investigation

### Maintaining Consistency
When running multiple prompts:
- AI will use the same **severity levels** (Low/Medium/High/Critical)
- AI will use the same **terminology** across all documents
- This makes it easier to consolidate findings

### Focus on Trading Safety
For a financial trading system:
- Trading correctness is paramount
- Financial precision is non-negotiable
- Security and execution safety are critical
- The AI will prioritize these heavily

---

## Workflow Recommendations

### For One-Time Review
1. Paste Master Instruction
2. Upload codebase
3. Run prompts in order (Prompts 1-10)
4. Run Final Consolidation
5. Done!

### For Ongoing Development
1. Set up Master Instruction in a persistent chat
2. Upload codebase once (keep it in the conversation)
3. Run individual prompts as needed during development
4. Easy to re-run prompts on updated code

### For Team Reviews
1. Each team member gets the Master Instruction
2. Each member uploads the codebase
3. Assign different prompts to different reviewers
4. Consolidate findings with [11-final-consolidation.md](./11-final-consolidation.md)

---

## Example Usage Session

```
USER: [Paste Master Instruction from above]

AI: I understand. I'm now configured as a senior technical reviewer 
    for the sonarft cryptocurrency trading system. I will focus on 
    correctness, trading safety, async integrity, financial precision, 
    architecture, security, performance, and testability.
    
    Ready to review code. What would you like me to analyze?

USER: [Upload sonarft codebase files]

AI: I've received the codebase. I can see X Python files, Y config files, etc.
    Ready to run prompts.

USER: [Copy Prompt 1 from 01-architecture-structure.md and paste it]

AI: [Generates architecture review documentation]

USER: [Save the output to docs/architecture/overview.md]

USER: [Copy Prompt 2 from 02-async-concurrency.md and paste it]

AI: [Generates async/concurrency review]

... and so on
```

---

## Customization

Feel free to adapt the Master Instruction for your needs:

- **Add exchange-specific guidance** if reviewing specific exchanges
- **Add domain-specific focus** for trading strategies
- **Adjust severity thresholds** if your risk tolerance differs
- **Add style preferences** (e.g., "always use Mermaid diagrams")
- **Specify output format** if you have custom requirements

---

## Variables You Might Customize

In the Master Instruction above, you can customize:

```
# Example customizations (edit as needed):

- "sonarft cryptocurrency trading system" → your system name
- "async-first" → your architecture style
- "CCXT/CCXTpro" → your exchange libraries
- "RSI, MACD, Stochastic, SMA" → your specific indicators
- "High, Medium, Low, Critical" → your severity scale
```

---

## Next Steps

1. **Understand the instruction** you just read
2. **Choose your path** from [00-quick-start-guide.md](./00-quick-start-guide.md)
3. **Run specific prompts** from the individual prompt files
4. **Save results** to `docs/` folder

---

## Quick Reference

| Need | Location |
|------|----------|
| Quick audit | [00-quick-start-guide.md](./00-quick-start-guide.md) |
| All prompts listed | [README.md](./README.md) |
| Planning & strategy | [SEPARATION_STRATEGY.md](./SEPARATION_STRATEGY.md) |
| Best practices | [99-best-practices.md](./99-best-practices.md) |

---

**Ready?** Start with [00-quick-start-guide.md](./00-quick-start-guide.md)

