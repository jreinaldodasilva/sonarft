# Prompt 7 — Configuration & Runtime Environment Review

**Focus:** Configuration system and runtime safety  
**Category:** Operational & Infrastructure  
**Output File:** `docs/configuration/config-review.md`  
**Run After:** [00-master-instruction.md](./00-master-instruction.md)  
**Time Estimate:** 15-20 minutes  
**Prerequisites:** Have sonarft codebase uploaded to AI  

---

## When to Use This Prompt

Use this prompt to audit configuration handling and runtime environment setup. Important for ensuring safe deployment.

**Best for:**
- Verifying configuration validation
- Checking hardcoded values
- Assessing runtime safety
- Validating defaults

---

## The Prompt

Copy and paste this into your AI chat:

```text
Audit the configuration system and runtime environment handling in sonarft.

### 1. Configuration File Structure
- Format (JSON, YAML, Python dict?)
- Schema (validation present?)
- Examples provided?
- Parameter documentation?
- Defaults defined?

Create table of all configuration parameters:

| Parameter | Required | Type | Default | Purpose | Validation |
|-----------|----------|------|---------|---------|------------|

### 2. Configuration Loading Behavior
- Entry point for config loading
- Expected file locations
- Environment variable overrides
- Merge behavior for multiple configs
- Fallback behavior if config missing

### 3. Per-Bot & Per-Client Configuration
If supported:
- What can be configured per-bot vs globally?
- Inheritance from global config?
- Conflict resolution?
- Bot isolation?

### 4. Environment Variable Usage
- Which are required (API keys, secrets?)
- Which are optional?
- Defaults when missing?
- Security (secrets logged?)

### 5. Defaults & Hardcoding Audit
Search for:
- Hardcoded values (should be config?)
- Unsafe defaults (could cause problems?)
- Missing parameters (all needed params in config?)

### 6. Docker Runtime Assumptions
- Base image appropriateness
- Working directory
- Config file location for Docker
- Environment setup
- Volume usage
- Entrypoint command

### 7. File Paths & History Storage
- Relative vs absolute paths
- Path construction safety
- Permission requirements
- Trade history storage location
- Log file rotation

### 8. Path Safety & Traversal Risks
- User-supplied paths controllable?
- Path traversal risks (..)?
- Symlink handling
- File permission safety

### 9. Configuration Validation
- Schema validation present?
- Type checking?
- Range validation for numeric params?
- Dependency validation (if A=X then B must=Y)?
- Clear error messages?

### 10. Configuration Issues Table

| Issue | Location | Type | Severity | Remediation |
|-------|----------|------|----------|------------|

### 11. Runtime Configuration Summary

| Aspect | Current Method | Safe? | Recommendation |
|--------|----------------|-------|-----------------|

### 12. Docker Configuration Review
- Dockerfile production-ready?
- docker-compose correct?
- Container security (non-root user?)
- Secrets handling safe?

### 13. Conclusion
Assess:
- Configuration system maturity
- Safety of defaults
- Production readiness
- Hardening recommendations
```

---

## What This Generates

The AI will produce **`docs/configuration/config-review.md`** containing:

- **Configuration Inventory** — All parameters documented
- **Loading Behavior** — How config is loaded and merged
- **Validation Assessment** — Schema and type checking
- **Defaults Review** — What happens with missing config
- **Issues Table** — Configuration problems identified
- **Docker Review** — Container configuration assessment
- **Recommendations** — How to improve configuration safety

---

## Common Issues Found

Configuration bugs:
- ⚠️ Hardcoded API endpoints or parameters
- ⚠️ No schema validation for config
- ⚠️ Unsafe defaults (e.g., simulation=false)
- ⚠️ Secrets in config files or logs
- ⚠️ Missing configuration options

---

## Next Steps

1. Review `docs/configuration/config-review.md`
2. Continue with [08-security-risk.md](./08-security-risk.md)

