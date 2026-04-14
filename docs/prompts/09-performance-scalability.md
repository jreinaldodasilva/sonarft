# Prompt 9 — Performance & Scalability Review

**Focus:** Performance bottlenecks and scalability assessment  
**Category:** Operational & Infrastructure  
**Output File:** `docs/performance/performance-analysis.md`  
**Run After:** [00-master-instruction.md](./00-master-instruction.md)  
**Time Estimate:** 15-20 minutes  
**Prerequisites:** Have sonarft codebase uploaded to AI  

---

## When to Use This Prompt

Use this prompt to identify performance bottlenecks and assess scalability. Important for understanding system limits.

**Best for:**
- Finding bottlenecks
- Optimizing API calls
- Assessing memory usage
- Planning scaling

---

## The Prompt

Copy and paste this into your AI chat:

```text
Review sonarft for performance, scalability, and resource usage.

### 1. API Call Frequency Audit
- How often is each exchange API called?
- API rate limits respected?
- Redundant/duplicate calls?
- Batching opportunities?

Create table:

| API Call | Purpose | Frequency | Rate Limit | Optimization Potential |
|----------|---------|-----------|------------|----------------------|

### 2. Order Book Fetching Analysis
- Fetch frequency?
- Necessity (more than needed?)
- Caching?
- Acceptable data staleness?
- API cost?

### 3. Data Processing Performance
- DataFrame operations efficient?
- Repeated calculations?
- Unnecessary copies?
- Pandas vectorization used?
- Inefficient loops?

### 4. Indicator Calculation Performance
- Computational cost?
- Recalculation frequency?
- Caching?
- More efficient approach?

### 5. Memory Usage Analysis
- Task lists unbounded?
- Logs in memory?
- Order history in memory or disk?
- DataFrame size?
- Memory growth over time?

### 6. Bottleneck Identification
- Critical path (slowest operation)?
- Sequential work that could parallelize?
- Blocking I/O in async code?

Create bottleneck table:

| Bottleneck | Location | Frequency | Impact | Potential Improvement |
|-----------|----------|-----------|--------|---------------------|

### 7. Concurrency & Scaling
- Multi-bot concurrency possible?
- Multi-symbol scaling?
- CPU scaling benefits?
- I/O or CPU bound?
- Scalability limits?

### 8. Cache & Optimization Opportunities
- Cacheable data?
- Repeated calculations?
- Batch opportunities?
- Better algorithms?

### 9. Latency Analysis
For each critical operation:
- Current latency?
- Acceptable latency?
- Latency sources?
- Improvement potential?

### 10. Resource Usage Summary

| Resource | Current | Peak | Limit | Headroom |
|----------|---------|------|-------|----------|

Resources: CPU %, Memory MB, Disk MB/hour, API calls/sec

### 11. Load Testing Recommendations
- Test scenarios?
- Metrics to measure?
- Tools to use?
- Acceptable thresholds?

### 12. Performance Optimization Roadmap

| Optimization | Effort | Impact | Priority |
|-------------|--------|--------|----------|

### 13. Conclusion
- Performance assessment
- Critical bottlenecks
- Optimization recommendations
```

---

## What This Generates

The AI will produce **`docs/performance/performance-analysis.md`** containing:

- **API Call Analysis** — Frequency and efficiency
- **Data Processing Review** — Computation efficiency
- **Memory Analysis** — Memory usage patterns
- **Bottleneck Identification** — Where time is spent
- **Scaling Assessment** — Multi-bot/multi-symbol scaling potential
- **Optimization Opportunities** — Caching, batching, algorithms
- **Load Testing Plan** — How to validate scalability
- **Optimization Roadmap** — Prioritized improvements

---

## Common Performance Issues

Bottlenecks often found:
- ⚠️ Order book fetched too frequently
- ⚠️ Same calculations repeated for every bot
- ⚠️ No caching of indicator values
- ⚠️ Logs growing unbounded in memory
- ⚠️ DataFrame copies made unnecessarily

---

## Next Steps

1. Review `docs/performance/performance-analysis.md`
2. Continue with [10-code-quality-testing.md](./10-code-quality-testing.md)

---

## Tips for Success

- **Trace expensive operations** — Where does time go?
- **Look for repeated calculations** — Can they be cached?
- **Check API frequency** — Is it necessary?
- **Assess memory growth** — Does it grow unbounded?
- **Identify parallelization opportunities** — What can run concurrently?

