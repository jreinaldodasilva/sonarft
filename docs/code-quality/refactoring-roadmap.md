# SonarFT — Refactoring Roadmap

**Review Date:** July 2025
**Codebase Version:** 1.0.0

---

## Refactoring Roadmap

| # | Refactoring | Complexity | Impact | Priority |
|---|---|---|---|---|
| 1 | Fix `trade_position` unbound variable | Low | **Critical** — prevents crash | P0 |
| 2 | Fix `weighted_adjust_prices` return arity (2-tuple → 3-tuple) | Low | **Critical** — prevents ValueError | P0 |
| 3 | Fix StochRSI positional parameter mismatch | Low | **Critical** — fixes false signals | P0 |
| 4 | Fix WebSocket disconnect infinite loop | Low | **High** — prevents dead socket loop | P0 |
| 5 | Fix Medium volatility threshold (`/ 100` bug) | Low | **High** — enables trades in Medium volatility | P0 |
| 6 | Add `cancel_order` to `SonarftApiManager` | Low | **High** — enables trade rollback | P1 |
| 7 | Implement exchange API key loading from env vars | Medium | **Critical** — enables live trading | P1 |
| 8 | Fix server bind address (`127.0.0.1` → `0.0.0.0`) | Low | **Critical** — fixes Docker deployment | P1 |
| 9 | Add `acme.json` and `sonarftdata/` to `.gitignore` | Low | **Critical** — prevents secret exposure | P1 |
| 10 | Remove double rate limiting | Low | **High** — halves API delay | P1 |
| 11 | Add order book cache (2s TTL) | Low | **High** — 83% fewer OB API calls | P1 |
| 12 | Fix `order_placed` None check in `execute_order` | Low | **High** — prevents TypeError crash | P1 |
| 13 | Fix `get_last_price` None check in `monitor_price` | Low | **High** — prevents TypeError crash | P1 |
| 14 | Wire `record_trade_result()` into trade completion | Low | **High** — activates daily loss limit | P1 |
| 15 | Add same-exchange arbitrage guard | Low | **High** — prevents self-arbitrage | P1 |
| 16 | Fix `get_short_term_market_trend` zero-division | Low | **High** — fixes NameError | P1 |
| 17 | Fix `bid_prices[0]` IndexError in `deeper_verify_liquidity` | Low | **High** — prevents crash on empty OB | P1 |
| 18 | Fix `np.mean/std` on empty list in threshold calculation | Low | **High** — prevents NaN thresholds | P1 |
| 19 | Consolidate 5 config loader functions into 1 | Low | Medium — reduces duplication | P2 |
| 20 | Extract HTTP endpoint error handling to decorator | Low | Medium — removes 9 duplicate try/except | P2 |
| 21 | Remove duplicate `BotCreationError` class | Low | Low — removes confusion | P2 |
| 22 | Replace sync file I/O with `aiofiles` | Medium | **High** — unblocks event loop | P2 |
| 23 | Add `deque(maxlen=1000)` to `AsyncHandler.logs` | Low | Medium — prevents memory leak | P2 |
| 24 | Add LRU eviction to `_ohlcv_cache` | Low | Medium — prevents memory growth | P2 |
| 25 | Move position determination out of `SonarftExecution` | Medium | Medium — improves separation of concerns | P2 |
| 26 | Replace `argparse` in `BotManager.create_bot` | Low | Medium — fixes server-context arg parsing | P2 |
| 27 | Add `asyncio.wait_for` timeout to `weighted_adjust_prices` gather | Low | **High** — prevents indefinite hang | P2 |
| 28 | Fix `get_exchange_by_id` linear scan → dict lookup | Low | Low — correctness improvement | P2 |
| 29 | Fix `get_liquidity` formula (dimensionally incorrect) | Low | Medium — fixes broken metric | P2 |
| 30 | Fix `get_past_performance` inverted index | Low | Medium — fixes inverted signal | P2 |
| 31 | Fix `get_historical_volume` returns `ohlcv[0][5]` | Low | Medium — fixes wrong candle | P2 |
| 32 | Fix support/resistance exchange swap | Low | Medium — fixes price clamping | P2 |
| 33 | Add `PYTHONUNBUFFERED=1` and health check to Dockerfile | Low | Medium — improves ops | P2 |
| 34 | Add `restart: unless-stopped` to docker-compose | Low | Medium — improves reliability | P2 |
| 35 | Wire `config_indicators.json` to actual indicator selection | High | Medium — makes config meaningful | P3 |
| 36 | Replace trade history JSON with SQLite | High | Medium — O(1) writes, concurrent-safe | P3 |
| 37 | Add indicator value cache | Medium | Medium — eliminates duplicate RSI | P3 |
| 38 | Offload pandas-ta to `asyncio.to_thread` | Medium | Low (now), Medium (at scale) | P3 |
| 39 | Add minimum order size validation | Medium | Medium — prevents exchange rejections | P3 |
| 40 | Add slippage model to simulation mode | High | Medium — improves backtest accuracy | P3 |
| 41 | Upgrade `pandas` to 2.x, `fastapi` to current | Medium | Medium — security patches | P3 |
| 42 | Add `pytest` test suite (P1 targets first) | High | **Critical** — zero coverage currently | P1 |

---

## Implementation Phases

### Phase 0 — Critical Bug Fixes (1–2 days)
Items 1–5: Fix crashes and silent failures that affect every trade cycle.

### Phase 1 — Production Blockers (1 week)
Items 6–18: Exchange API keys, Docker bind address, gitignore, rate limiting, order book cache, None checks, safety gate wiring.

### Phase 2 — Code Quality & Stability (2–3 weeks)
Items 19–34: Duplication removal, async file I/O, memory bounds, timeout guards, formula fixes, Docker hardening.

### Phase 3 — Architecture & Scale (1–2 months)
Items 35–42: Config wiring, SQLite history, indicator caching, test suite, dependency upgrades.

---

## Effort Estimate Summary

| Phase | Items | Estimated Effort | Risk Reduction |
|---|---|---|---|
| Phase 0 | 5 | 1–2 days | Eliminates 3 crash scenarios |
| Phase 1 | 13 | 1 week | Enables live trading safely |
| Phase 2 | 16 | 2–3 weeks | Improves stability and performance |
| Phase 3 | 8 | 1–2 months | Long-term maintainability |

---

*Generated as part of the SonarFT code review suite — Prompt 10 (3/3): Refactoring Roadmap*
