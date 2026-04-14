# Prompt 8 — Security & Trading Risk Review

**Focus:** Security vulnerabilities and operational trading risks  
**Category:** Operational & Infrastructure  
**Output File:** `docs/security/security-audit.md`  
**Run After:** [00-master-instruction.md](./00-master-instruction.md)  
**Time Estimate:** 20-25 minutes  
**Prerequisites:** Have sonarft codebase uploaded to AI  

---

## When to Use This Prompt

Use this prompt to identify security vulnerabilities and operational risks. Critical before any production deployment.

**Best for:**
- Identifying secret exposure risks
- Checking input validation
- Assessing DoS vulnerabilities
- Validating trading safety controls

---

## The Prompt

Copy and paste this into your AI chat:

```text
Perform a comprehensive security and operational risk review of sonarft.

### 1. Secret & Credential Handling
- How are API keys stored/loaded?
- Secret keys management?
- Secrets in logs? (grep for "key", "secret", "password")
- Environment variable management?
- Secrets in config files?
- .gitignore compliance?

### 2. Input Validation & Injection Risks
- What input does system accept?
- Command injection possible?
- File path injection?
- JSON/SQL injection?
- API input validation?

### 3. File Path Safety
- Path construction safety?
- Path traversal (..) risks?
- Symlink handling?
- File permissions correct?

### 4. WebSocket Security
If WebSocket used:
- Authentication on connection?
- Proper authorization?
- Message validation?
- DoS risk (message flood)?
- JSON parsing safe?

### 5. API Exposure Risks
- What endpoints exist?
- Authentication on each?
- Rate limiting enforced?
- Input validation?
- Error messages leak system info?

### 6. Denial of Service (DoS) Risks
- Unbounded loops exploitable?
- Memory allocation risks?
- Computation expensive enough to block?
- Connection limits?
- Queue accumulation?

### 7. Trading Safety Controls
- Simulation mode gate enforced?
- Maximum position size limit?
- Maximum loss limit?
- Rate limiting on orders?
- Circuit breaker on errors?
- Manual stop mechanism?

### 8. Financial Risk Management
- Balance checked before trading?
- Margin requirements enforced?
- Slippage protection?
- Runaway trading prevented?
- Liquidity risk considered?

### 9. Logging & Monitoring
- What's logged?
- Sensitive values in logs?
- Log storage location?
- Log rotation?
- Error alerting?

### 10. Dependency Security
- Dependency versions pinned?
- Known vulnerabilities?
- Trusted package sources?

### 11. Security Risk Table

| Risk Category | Specific Risk | Location | Severity | Likelihood | Mitigation |
|---------------|---------------|----------|----------|------------|-----------|

Risk categories: Secrets exposure, Injection attacks, DoS, Trading safety, Financial risk, Dependency risk

### 12. Operational Risk Table

| Risk | Scenario | Impact | Preventing Control |
|------|----------|--------|-------------------|

### 13. Severity Assessment

For each finding:
- Severity level (Low/Medium/High/Critical)
- Attack/failure scenario
- Proof-of-concept
- Financial impact
- Remediation steps

### 14. Conclusion

Summarize:
- Critical security findings
- Critical trading safety findings
- Hardening recommendations
- Production readiness assessment
```

---

## What This Generates

The AI will produce **`docs/security/security-audit.md`** containing:

- **Secrets Exposure Analysis** — Where credentials are at risk
- **Input Validation Review** — Injection attack surface
- **API Security Assessment** — Endpoint security
- **DoS Vulnerability** — System resilience
- **Trading Safety Controls** — How trading is gated
- **Security Risk Table** — Severity-ranked issues
- **Operational Risk Table** — Failure scenarios
- **Remediation Steps** — How to fix each issue

---

## Critical Issues to Find

Security & trading safety bugs:
- ⚠️ API keys in source code or config
- ⚠️ Secrets logged to console or files
- ⚠️ No authentication on WebSocket
- ⚠️ Simulation mode not properly enforced
- ⚠️ No maximum loss controls
- ⚠️ Input validation missing

---

## Next Steps

1. Review `docs/security/security-audit.md` **very carefully**
2. **Flag Critical findings immediately**
3. Continue with [09-performance-scalability.md](./09-performance-scalability.md)

---

## Tips for Success

- **Trace credentials end-to-end** — Where do they go?
- **Look for logging of secrets** — Easy to miss
- **Check trading mode gates** — Can live trading happen accidentally?
- **Verify authentication** — All entry points?
- **Assess impact** — What's the financial impact of each risk?

