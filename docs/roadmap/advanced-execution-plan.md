# Advanced Execution Plan — SonarFT

---

## Gantt-Style Execution Timeline

The timeline assumes a 2-engineer team (Engineer A: Python/Async, Engineer B: Security/Quant) working full-time. Phases 0–2 are sequential. Phases 3 and 4 run in parallel after Phase 2 completes. Phase 5 begins after Phase 4.

```
Week        W1          W2          W3          W4          W5          W6          W7          W8
            Mon–Fri     Mon–Fri     Mon–Fri     Mon–Fri     Mon–Fri     Mon–Fri     Mon–Fri     Mon–Fri
─────────────────────────────────────────────────────────────────────────────────────────────────────
Eng A       [Phase 0 ──────────][Phase 1 ──────────────────][Phase 3 ──────────][Phase 4 ──]
Eng B       [Phase 0 ──────────][Phase 2 ──────────────────][Phase 4 ──────────][Phase 5 ──]
─────────────────────────────────────────────────────────────────────────────────────────────────────
Milestones  ^Sim Safe           ^Paper Trading              ^Perf Baseline      ^Prod Candidate
            (end W1)            (end W3)                    (end W5)            (end W7)
```

### Week-by-Week Breakdown

| Week | Engineer A | Engineer B | Milestone |
|---|---|---|---|
| W1 | T-01, T-02, T-03, T-04, T-05, T-09, T-11, T-13, T-14, T-15, T-16, T-25 | T-53, T-06 (path traversal) | **Milestone A — Safe Simulation** |
| W2 | T-10, T-12, T-17, T-23, T-24, T-26, T-27, T-28, T-29, T-30 | T-07, T-08, T-19, T-20, T-33 | — |
| W3 | T-18, T-31, T-32, T-34, T-52, T-54 | T-21, T-22, T-51, D-21 | **Milestone B — Paper Trading** |
| W4 | T-35, T-37, T-38, T-40 | T-42, T-43, T-44, T-45, T-48 | — |
| W5 | T-36, T-39, T-41 | T-46, T-49, T-50 | **Milestone C — Limited Real Trading** |
| W6 | T-47 (per-symbol precision) | Phase 5: NaN handling, config-driven indicators | — |
| W7 | Load testing, regression suite | Phase 5: support/resistance, mixed signals | — |
| W8 | Documentation, runbook, final review | Phase 5: position size validation | **Milestone D — Production** |


---

## Sprint-Ready Task Breakdown

Sprints are 5 days (1 week). Each sprint has a clear goal and defined done criteria.

---

### Sprint 1 — Eliminate Crash Paths (Phase 0, Part 1)

**Goal:** Zero unhandled exceptions in a full simulation cycle.

| Task | Owner | Effort | Done Criteria |
|---|---|---|---|
| T-01: Fix `calculate_trade` return mismatch | Eng A | 1h | Unit test passes: no `ValueError` on fee lookup failure |
| T-02: `None` guards for RSI/StochRSI | Eng A | 2h | Unit test passes: `None` RSI does not crash `weighted_adjust_prices` |
| T-03: Fix `handle_trade_results` `None` unpack | Eng A | 1h | Unit test passes: `None` order result returns gracefully |
| T-04: Fix MACD `None` unpack | Eng A | 1h | Unit test passes: `None` MACD does not crash price adjustment |
| T-05: Fix StochRSI `None` unpack | Eng A | 1h | Unit test passes: `None` StochRSI handled in all callers |
| T-09: Fix re-entrant lock deadlock | Eng A | 1h | Integration test: concurrent `set_update`/`get_update` — no deadlock |
| T-11: `asyncio.Event` for `stop_bot` | Eng A | 2h | Integration test: `stop_bot` exits cleanly while `monitor_price` runs |
| T-13: Guard unknown exchange in `EXCHANGE_RULES` | Eng A | 1h | Unit test: `calculate_trade('kraken', ...)` — no `KeyError` |
| T-14: Zero-div guard in `get_weighted_prices` | Eng A | 30m | Unit test: empty order book returns `(0.0, 0.0)` |
| T-15: Zero-div guard in `calculate_trade` | Eng A | 30m | Unit test: `buy_price=0` — no `ZeroDivisionError` |
| T-16: Clamp `weight` to `[0.0, 1.0]` | Eng A | 15m | Unit test: high volatility — `weight >= 0` |
| T-25: Fix `market_movement` direction bug | Eng A | 15m | Unit test: bear conditions return `'bear'` |
| T-06: Sanitise `client_id`/`botid` | Eng B | 2h | Security test: traversal string returns HTTP 400 |
| T-53: Add `max_daily_loss` parameter | Eng B | 3d | Simulation test: loss threshold halts bot |

**Sprint 1 Exit:** Full simulation cycle completes without exception. `stop_bot` works. Path traversal blocked.

---

### Sprint 2 — Async Stability & Config Safety (Phase 1, Part 1)

**Goal:** No infinite loops, no blocking calls, deterministic config loading.

| Task | Owner | Effort | Done Criteria |
|---|---|---|---|
| T-10: Timeout for `monitor_price`/`monitor_order` | Eng A | 2h | Unit test: price never reached — `TimeoutError` within deadline |
| T-12: `run_in_executor` for ccxt REST | Eng A | 3h | Load test: 3 bots in ccxt mode — event loop lag < 100ms |
| T-17: Skip `monitor_price` in simulation | Eng A | 30m | Simulation test: no `monitor_price` call in sim mode |
| T-23: Move task creation out of `__init__` | Eng A | 1h | Code review: no `create_task` in constructors |
| T-24: Key-based config extraction | Eng A | 30m | Unit test: reordered JSON keys — correct variable assignment |
| T-26: Fix trend threshold unit mismatch | Eng A | 15m | Unit test: trend returns `'bull'` only for meaningful moves |
| T-27: Fix `/100` divisor in spread threshold | Eng A | 30m | Unit test: 5-entry order book — divisor is 5 |
| T-28: Fix MACD column name | Eng A | 30m | Unit test: non-default periods — no `KeyError` |
| T-29: Zero-div in `get_short_term_market_trend` | Eng A | 15m | Unit test: zero previous price — returns `'neutral'` |
| T-30: Zero-div in `get_liquidity` | Eng A | 15m | Unit test: zero-price order book — no `ZeroDivisionError` |
| T-07: Restrict CORS origins | Eng B | 1h | Manual test: unlisted origin rejected |
| T-08: Secure Traefik dashboard | Eng B | 2h | Verify dashboard requires auth |
| T-19: Non-root Docker user | Eng B | 30m | `whoami` inside container returns non-root |
| T-20: Remove `.env` from image | Eng B | 1h | Image inspection: no `.env` layer |
| T-33: Replace `print()` with logger | Eng B | 1h | Code review: zero `print(` in production files |

**Sprint 2 Exit:** No blocking calls in async context. Config loading is deterministic. CORS and Docker hardened.

---

### Sprint 3 — Execution Safety & Full Security (Phase 1 Part 2 + Phase 2)

**Goal:** Partial fills handled. Authentication in place. Paper trading ready.

| Task | Owner | Effort | Done Criteria |
|---|---|---|---|
| T-18: Partial fill handler | Eng A | 2d | Integration test: partial fill — sell leg not placed prematurely |
| T-31: Cancel `send_logs` on disconnect | Eng A | 1h | Integration test: disconnect — log task cancelled |
| T-32: Fix `monitor_trade_tasks` dead code | Eng A | 30m | Code review + unit test: done task exceptions logged |
| T-34: Startup config validation | Eng A | 2h | Unit test: invalid config — `ValueError` before bot starts |
| T-52: Circuit breaker in `run_bot` | Eng A | 1d | Integration test: 5 exchange errors — backoff activates |
| T-54: Move `save_order_history` after placement | Eng A | 30m | Unit test: failed order — not recorded as attempted |
| T-21: Add authentication to all endpoints | Eng B | 3d | Security test: no token — HTTP 401 |
| T-22: Per-client bot creation limit | Eng B | 1h | Load test: 100 bots from one client — limit enforced |
| T-51: `uuid4()` for botid | Eng B | 15m | Unit test: 10,000 IDs — no collisions |
| D-21: Mount history as Docker volume | Eng B | 30m | Container restart — history persists |

**Sprint 3 Exit:** Milestone B (Paper Trading) criteria met. Authentication active. Partial fills handled.

---

### Sprint 4 — Performance (Phase 3)

**Goal:** Reduce per-cycle API call count by ≥50%. Eliminate unbounded fetches.

| Task | Owner | Effort | Done Criteria |
|---|---|---|---|
| T-35: Gather indicator calls | Eng A | 1d | Benchmark: `weighted_adjust_prices` < 200ms for 2 exchanges |
| T-37: `load_markets` at startup | Eng A | 1h | Integration test: markets loaded once per bot lifecycle |
| T-38: Bound history fetch in spread threshold | Eng A | 30m | Integration test: ≤ 100 candles fetched |
| T-40: Parallelise order book + ticker per exchange | Eng A | 2h | Benchmark: `get_latest_prices` latency reduced |
| T-41: `deque.popleft()` in `send_logs` | Eng A | 30m | Load test: high-frequency logging — no degradation |
| T-36: OHLCV cache with TTL | Eng A | 2d | Benchmark: API call count per cycle ≤ 15 per symbol |
| T-39: Pass indicators through `trade_data` | Eng A | 1d | Benchmark: 6 fewer API calls per trade execution |

**Sprint 4 Exit:** Benchmark shows ≥50% reduction in API calls. Cycle time < 500ms per symbol.

---

### Sprint 5 — Architecture & Precision (Phase 4)

**Goal:** `Decimal` arithmetic in financial calculations. No duplicate code. Clean codebase.

| Task | Owner | Effort | Done Criteria |
|---|---|---|---|
| T-42: Fix typos `sucess` → `success` | Eng A | 15m | Code review: zero `sucess` occurrences |
| T-43: Remove duplicate `save_botid` | Eng A | 30m | Code review: single implementation |
| T-44: Remove dead code | Eng A | 1h | Code review: no dead code |
| T-45: Remove unused `getcontext` imports | Eng A | 30m | Code review: no unused imports |
| T-49: Decompose `weighted_adjust_prices` | Eng A | 3h | Code review: no method > 50 lines |
| T-50: Consolidate OHLCV wrappers | Eng A | 2h | Code review: no duplicate wrappers |
| T-46: `Decimal` arithmetic in `calculate_trade` | Eng B | 1d | Unit test: `Decimal` vs `float` difference < 1e-8 |
| T-47: Per-symbol precision from exchange API | Eng B | 3d | Integration test: precision matches exchange-reported values |
| T-48: Module docstrings | Eng B | 30m | Code review: all files have module docstring |

**Sprint 5 Exit:** Financial calculations use `Decimal`. No hardcoded exchange precision. No duplicate code.

---

### Sprint 6 — Strategy Enhancements & Production Prep (Phase 5)

**Goal:** Robust indicator pipeline. Config-driven strategy. Production deployment ready.

| Task | Owner | Effort | Done Criteria |
|---|---|---|---|
| NaN handling for all pandas-ta outputs | Eng A | 1d | Unit test: NaN output — typed sentinel returned, no silent failure |
| Load `config_indicators.json` at startup | Eng A | 2d | Integration test: indicator params from config, not hardcoded |
| Mixed bull/bear signal branches | Eng A | 2d | Unit test: mixed signals produce defined spread behaviour |
| Improved support/resistance (pivot points) | Eng B | 3d | Backtest: support/resistance levels match known price clusters |
| Configurable spread factors | Eng B | 1d | Integration test: spread factors loaded from config |
| Position size validation vs balance | Eng B | 1d | Integration test: trade amount > balance — trade skipped |
| 7-day paper trading run | Both | — | Zero crashes, all metrics within thresholds |
| Operational runbook | Both | 1d | Runbook covers start, stop, rollback, incident response |

**Sprint 6 Exit:** Milestone D (Production) criteria met.


---

## Risk Heatmap

Severity (rows) × Likelihood (columns). Each cell lists task IDs that fall in that quadrant.

```
              │ Low Likelihood │ Medium Likelihood │ High Likelihood │
──────────────┼────────────────┼───────────────────┼─────────────────┤
Critical      │                │ T-53 (no loss     │ T-01, T-02,     │
Severity      │                │ limit)            │ T-03, T-04,     │
              │                │                   │ T-05, T-06      │
──────────────┼────────────────┼───────────────────┼─────────────────┤
High          │ T-18 (partial  │ T-09, T-11,       │ T-10, T-12,     │
Severity      │ fill)          │ T-21, T-47        │ T-13, T-14,     │
              │                │                   │ T-15, T-16      │
──────────────┼────────────────┼───────────────────┼─────────────────┤
Medium        │ T-46 (float    │ T-07, T-08,       │ T-24, T-25,     │
Severity      │ precision)     │ T-19, T-20        │ T-26, T-27,     │
              │                │                   │ T-28, T-33      │
──────────────┼────────────────┼───────────────────┼─────────────────┤
Low           │ T-51 (botid    │ T-42, T-43,       │ T-44, T-45,     │
Severity      │ collision)     │ T-48, T-54        │ T-41            │
──────────────┴────────────────┴───────────────────┴─────────────────┘
```

**Highest priority quadrant (Critical × High Likelihood):** T-01 through T-06 — these must be resolved in Sprint 1 before any other work.

**Second priority quadrant (High × High Likelihood):** T-10, T-12, T-13, T-14, T-15, T-16 — resolved in Sprint 1 and Sprint 2.

---

## Developer Role Assignment Suggestions

### Engineer A — Python / Async Specialist

**Primary responsibilities:**
- All async correctness fixes (T-09, T-10, T-11, T-12, T-23, T-31, T-32)
- Trading pipeline crash fixes (T-01, T-02, T-03, T-04, T-05)
- Performance optimisation (T-35, T-36, T-37, T-38, T-39, T-40, T-41)
- Architecture cleanup (T-42, T-43, T-44, T-45, T-49, T-50)

**Required skills:** Python asyncio internals, ccxt/ccxtpro, FastAPI, performance profiling

---

### Engineer B — Security / Quant Specialist

**Primary responsibilities:**
- All security fixes (T-06, T-07, T-08, T-19, T-20, T-21, T-22, T-51)
- Financial math correctness (T-46, T-47, T-53)
- Trading safety (T-18, T-52, T-54)
- Strategy enhancements (Phase 5)

**Required skills:** Web security (CORS, path traversal, JWT), Docker hardening, financial arithmetic, technical analysis

---

### Optional: QA / Test Engineer (Part-Time)

**Responsibilities:**
- Write and maintain unit and integration test suite
- Run security penetration tests
- Execute load tests and benchmarks
- Validate each sprint exit criteria

**Engagement:** Part-time from Sprint 1 exit onward (test suite built incrementally alongside fixes)

---

## CI/CD Pipeline Upgrade Recommendations

### Current State

No CI/CD pipeline exists. The project has no test files, no linting configuration, and no automated build process beyond the Dockerfile.

### Recommended Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  On every Pull Request                                          │
│                                                                 │
│  1. Lint          → ruff / flake8 (enforce no print(), types)  │
│  2. Type check    → mypy (strict mode on sonarft_math.py first) │
│  3. Unit tests    → pytest (sonarft_math, indicators, helpers)  │
│  4. Security scan → bandit (path traversal, hardcoded secrets)  │
│                                                                 │
│  On merge to main                                               │
│                                                                 │
│  5. Integration tests → pytest with mocked exchange API         │
│  6. Docker build  → docker build --no-cache                     │
│  7. Image scan    → trivy (CVE scan on base image + deps)       │
│  8. Push to registry (only if all checks pass)                  │
│                                                                 │
│  On release tag                                                 │
│                                                                 │
│  9. Load test     → locust or custom asyncio harness            │
│  10. Deploy to staging → docker-compose up (paper trading env)  │
│  11. Smoke test   → 1-hour simulation run, assert zero crashes  │
│  12. Manual approval gate before production deploy              │
└─────────────────────────────────────────────────────────────────┘
```

### Recommended Tools

| Stage | Tool | Rationale |
|---|---|---|
| Linting | `ruff` | Fast, catches `print()`, unused imports, naming issues |
| Type checking | `mypy` | Catches `None` unpack issues statically |
| Unit testing | `pytest` + `pytest-asyncio` | Native async test support |
| Mocking | `unittest.mock` + `pytest-mock` | Mock exchange API responses |
| Security scanning | `bandit` | Detects path traversal, hardcoded secrets |
| Image scanning | `trivy` | CVE scanning for Docker images |
| Load testing | Custom `asyncio` harness | Measures event loop lag under concurrent bots |
| Coverage | `pytest-cov` | Track coverage growth per sprint |

### Phased CI/CD Rollout

| Phase | CI/CD Addition |
|---|---|
| Sprint 1 | Add `ruff` lint check on PR; add `pytest` with Phase 0 unit tests |
| Sprint 2 | Add `bandit` security scan; add `mypy` on `sonarft_math.py` |
| Sprint 3 | Add integration test suite with mocked API; add Docker build check |
| Sprint 4 | Add `trivy` image scan; add benchmark regression check |
| Sprint 5 | Add `mypy` to all modules; enforce 60% coverage minimum |
| Sprint 6 | Add load test stage; add staging deploy with smoke test |

### Minimum `pyproject.toml` / `setup.cfg` additions

```toml
[tool.ruff]
select = ["E", "F", "W", "I", "N", "UP"]
ignore = []
line-length = 100

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

