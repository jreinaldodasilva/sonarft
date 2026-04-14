# Prompt 13 — Setup, Execution & Operations Guide

**Focus:** Installation, configuration, deployment, and operational procedures  
**Category:** Post-Review Artifacts  
**Output File:** `docs/operations/setup-and-execution-guide.md`  
**Run After:** [00-master-instruction.md](./00-master-instruction.md) and [07-configuration-runtime.md](./07-configuration-runtime.md)  
**Time Estimate:** 30-40 minutes  
**Prerequisites:** Have sonarft codebase uploaded to AI  

---

## When to Use This Prompt

Use this prompt to generate complete operational documentation covering installation, configuration, execution, and safe deployment.

**Best for:**
- Deployment teams
- Operations engineers
- System administrators
- Getting systems running safely

---

## Who Needs This?

- **DevOps/Operations teams** — How to deploy and operate
- **System administrators** — How to configure and run
- **Traders/Investors** — How to safely enable trading
- **New developers** — How to set up local environment

---

## The Prompt

This is a comprehensive operational guide. Paste this into your AI chat:

```text
You are a senior DevOps engineer, systems architect, and trading operations specialist.

Generate a complete operational guide explaining how to install, configure, execute, and safely operate sonarft.

The guide must support multiple environments and operational modes, including both safe testing and real trading scenarios.

Explain not only HOW to run the system, but also WHEN and WHY each mode should be used.

### 1. System Overview

Explain:
- What sonarft is
- Main capabilities
- Supported trading modes
- Supported exchanges
- System architecture summary
- Typical execution workflow

Include high-level system diagram (Mermaid recommended)

### 2. Prerequisites & Requirements

List all dependencies required to run the system.

Include:

**Hardware Requirements**
- Minimum CPU/RAM
- Recommended CPU/RAM
- Storage requirements
- Network requirements

**Software Requirements**
- Python version
- Required Python packages
- Docker requirements
- OS compatibility
- Exchange API requirements

Provide example verification commands.

### 3. Installation Guide

Provide step-by-step installation instructions.

Include:

**Local Installation (Python)**
- Cloning repository
- Installing dependencies
- Verifying installation

**Docker Installation**
- Building image
- Running container
- Verifying container status
- Docker-compose usage

### 4. Configuration Guide

Explain how to configure the system before execution.

Include:

**Configuration File Structure**
- Parameter files
- Indicator files
- Bot configuration files
- History storage structure

Provide example configuration snippets.

Explain key parameters:
- Profit thresholds
- Trade amounts
- Simulation flags
- Indicator parameters
- Exchange credentials

### 5. Execution Guide

Explain how to run the system.

Provide multiple execution scenarios:

**Standard Execution**
- Default startup command
- Configuration loading behavior
- Log output behavior

**Custom Configuration Execution**
- How to specify configuration files
- How to override defaults

### 6. Operational Modes Guide (CRITICAL SECTION)

This section must clearly explain all supported trading modes.

Include the following modes:

**Mode 1 — Simulation Mode**
- Purpose of simulation
- How simulated trades behave
- Order recording
- How to evaluate results
- Advantages and limitations
- Recommended use cases

**Mode 2 — Paper Trading Mode**
- How it differs from simulation
- Exchange data interaction
- Risk profile
- Safe testing workflow
- Validation strategy before real trading

**Mode 3 — Real Trading Mode**
- How to enable real trading
- API key configuration
- Safety risks (⚠️ CLEAR WARNINGS)
- Capital exposure risks
- Recommended safeguards
- Minimal safe starting capital
- Testing stages before activation

### 7. Safe Deployment Workflow

Define migration path from testing to production.

Step 1 — Simulation Testing
Step 2 — Paper Trading Validation
Step 3 — Limited Real Trading
Step 4 — Full Production Operation

Explain validation criteria between steps.

### 8. Logging & Monitoring Guide

Explain:
- Log file structure
- Runtime logs
- Error logs
- Trade logs
- How to monitor execution
- How to detect failures
- How to analyze outcomes

### 9. Troubleshooting Guide

Provide solutions for common runtime issues:
- Exchange connection failures
- Invalid configuration
- Missing dependencies
- Runtime crashes
- WebSocket failures
- Performance slowdowns

### 10. Testing Workflow Guide

Explain how to test the system safely.

Include:
- Unit testing approach
- Integration testing
- Strategy validation
- Signal verification
- Profitability logic testing

### 11. Performance & Scaling Guide

Explain:
- Running multiple bots
- Scaling across symbols
- CPU and memory optimization
- Performance tuning

### 12. Security Best Practices

Explain:
- API key storage practices
- Environment variable usage
- File permission recommendations
- Network security practices

Include strong operational warnings.

### 13. Backup & Recovery Guide

Explain:
- Backing up configuration
- Backing up trade history
- Recovering system state
- Restoring failed deployments

### 14. Upgrade & Maintenance Guide

Explain:
- Updating dependencies
- Upgrading system versions
- Maintaining compatibility
- Safe upgrade procedures

### 15. Real Trading Readiness Checklist

Create a checklist that must be completed before enabling real trading.

Include items such as:
- Simulation tests completed
- Logs validated
- Precision verified
- API limits confirmed
- Error handling validated
- Capital available and secured
- Manual stop controls tested
- Operator trained
```

---

## What This Generates

The AI will produce **`docs/operations/setup-and-execution-guide.md`** containing:

- **System Overview** — What sonarft is and does
- **Installation Instructions** — Step-by-step setup
- **Configuration Guide** — How to configure
- **Execution Procedures** — How to run in each mode
- **Operational Modes** — Simulation, Paper, Real (with warnings!)
- **Safe Deployment Workflow** — Path from testing to production
- **Logging & Monitoring** — How to observe the system
- **Troubleshooting** — Common problems and solutions
- **Testing Procedures** — How to validate before going live
- **Performance Tuning** — Optimization guidance
- **Security Practices** — Safe API key handling
- **Backup & Recovery** — Disaster recovery
- **Upgrade Procedures** — Updating safely
- **Real Trading Readiness Checklist** — Prerequisites for live trading

---

## Critical Sections

Pay special attention to:
- ⚠️ **Operational Modes** — Clear warnings about real trading risks
- ⚠️ **Safe Deployment Workflow** — Gates between stages
- ⚠️ **Real Trading Checklist** — Non-negotiable requirements

---

## Distribution

**For Operations Teams:**
- Print out "Safe Deployment Workflow"
- Use "Troubleshooting Guide" 
- Reference "Backup & Recovery"
- Post "Real Trading Checklist" in war room

**For Traders:**
- Read "Operational Modes" completely
- Complete "Real Trading Checklist"
- Understand "Safe Deployment Workflow"
- Know "Troubleshooting" procedures

**For Developers:**
- Setup local environment with "Installation Guide"
- Use "Configuration Guide" for dev config
- Reference "Testing Workflow" for validation

---

## Next Steps

1. **Use for local setup** → Follow Installation Guide
2. **Configure system** → Use Configuration Guide
3. **Run tests** → Follow Testing Workflow Guide
4. **Deploy** → Use Safe Deployment Workflow
5. **Operate** → Reference Logging & Monitoring
6. **Troubleshoot** → Use Troubleshooting Guide

---

## Tips for Success

- **Read Operational Modes carefully** — Understand each mode's purpose
- **Follow Safe Deployment Workflow** — Don't skip stages
- **Complete Real Trading Checklist** — All items before going live
- **Monitor logs continuously** — Especially in first days
- **Have runbook ready** — Print troubleshooting guide
- **Test disaster recovery** — Before you need it

