# SonarFT — Implementation Schedule

**Based on:** `docs/review/final-audit-report.md`
**Started:** July 2025
**Target:** Production-ready system

Legend: ⬜ Pending | 🔄 In Progress | ✅ Done

---

## Phase 0 — Critical Bug Fixes (~2 hours) — Simulation Safe

| # | Task | File(s) | Effort | Status |
|---|---|---|---|---|
| 0.1 | Fix `trade_position` unbound variable | `sonarft_execution.py` | 30 min | ✅ |
| 0.2 | Fix `weighted_adjust_prices` return arity (2-tuple → 3-tuple) | `sonarft_prices.py` | 15 min | ✅ |
| 0.3 | Fix StochRSI positional parameter mismatch | `sonarft_indicators.py` | 15 min | ✅ |
| 0.4 | Fix WebSocket disconnect infinite loop | `sonarft_server.py` | 30 min | ✅ |
| 0.5 | Fix Medium volatility threshold `/ 100` bug | `sonarft_validators.py` | 15 min | ✅ |

---

## Phase 1 — Simulation Ready (~12 hours)

| # | Task | File(s) | Effort | Status |
|---|---|---|---|---|
| 1.1 | Add `acme.json` + `sonarftdata/` subdirs to `.gitignore` | `.gitignore` | 5 min | ✅ |
| 1.2 | Fix server bind address `127.0.0.1` → `0.0.0.0` | `sonarft.py` | 5 min | ✅ |
| 1.3 | Fix `order_placed` None check in `execute_order` | `sonarft_execution.py` | 15 min | ✅ |
| 1.4 | Fix `get_last_price` None check in `monitor_price` | `sonarft_execution.py` | 15 min | ✅ |
| 1.5 | Fix `np.mean/std` on empty list → NaN thresholds | `sonarft_validators.py` | 30 min | ✅ |
| 1.6 | Fix `bid_prices[0]` IndexError on empty order book | `sonarft_validators.py` | 15 min | ✅ |
| 1.7 | Fix `get_short_term_market_trend` NameError on zero prices | `sonarft_indicators.py` | 15 min | ✅ |
| 1.8 | Add same-exchange arbitrage guard | `sonarft_search.py` | 30 min | ✅ |
| 1.9 | Wire `record_trade_result()` into trade completion | `sonarft_search.py` | 1 hour | ✅ |
| 1.10 | Remove double rate limiting | `sonarft_api_manager.py` | 30 min | ✅ |
| 1.11 | Add order book cache (2s TTL) | `sonarft_api_manager.py` | 1 hour | ✅ |
| 1.12 | Fix `previous_spread` race condition (per-call local var) | `sonarft_indicators.py` | 30 min | ✅ |
| 1.13 | Fix `self.volatility` race condition (return value, not state) | `sonarft_validators.py` | 30 min | ✅ |
| 1.14 | Add `asyncio.wait_for` timeout to `weighted_adjust_prices` gather | `sonarft_prices.py` | 30 min | ✅ |
| 1.15 | Add `SONARFT_API_TOKEN` startup warning when unset | `sonarft_server.py` | 1 hour | ✅ |
| 1.16 | Fix 500 errors exposing internal paths (`detail=str(error)`) | `sonarft_server.py` | 30 min | ✅ |
| 1.17 | Set safe defaults in `config_parameters.json` | `sonarftdata/config_parameters.json` | 15 min | ✅ |

---

## Phase 2 — Paper Trading Ready (~40 hours)

| # | Task | File(s) | Effort | Status |
|---|---|---|---|---|
| 2.1 | Implement exchange API key loading from env vars | `sonarft_bot.py`, `sonarft_api_manager.py` | 2 hours | ✅ |
| 2.2 | Add `cancel_order` to `SonarftApiManager` | `sonarft_api_manager.py` | 1 hour | ✅ |
| 2.3 | Implement trade rollback (cancel buy if sell fails) | `sonarft_execution.py` | 2 hours | ✅ |
| 2.4 | Fix `monitor_order` partial fill detection | `sonarft_execution.py` | 1 hour | ✅ |
| 2.5 | Fix `get_liquidity` dimensionally incorrect formula | `sonarft_indicators.py` | 30 min | ✅ |
| 2.6 | Fix `get_past_performance` inverted index | `sonarft_indicators.py` | 15 min | ✅ |
| 2.7 | Fix `get_historical_volume` returns wrong candle | `sonarft_indicators.py` | 15 min | ✅ |
| 2.8 | Fix support/resistance exchange swap | `sonarft_prices.py` | 15 min | ✅ |
| 2.9 | Fix `market_animal_buy/sell` computed but never used | `sonarft_prices.py` | 15 min | ✅ |
| 2.10 | Replace `asyncio.get_event_loop()` with `asyncio.get_running_loop()` | `sonarft_api_manager.py`, `sonarft_execution.py` | 30 min | ✅ |
| 2.11 | Add `deque(maxlen=1000)` to `AsyncHandler.logs` | `sonarft_server.py` | 15 min | ✅ |
| 2.12 | Add LRU eviction to `_ohlcv_cache` | `sonarft_api_manager.py` | 1 hour | ✅ |
| 2.13 | Write unit tests for `calculate_trade` and VWAP | `tests/test_sonarft_math.py` | 4 hours | ✅ |
| 2.14 | Write unit tests for safety gates and validators | `tests/test_sonarft_validators.py` | 4 hours | ✅ |

---

## Phase 3 — Live Trading Ready (~40 hours)

| # | Task | File(s) | Effort | Status |
|---|---|---|---|---|
| 3.1 | Replace sync file I/O with `aiofiles` (server + helpers) | `sonarft_server.py`, `sonarft_helpers.py` | 4 hours | ⬜ |
| 3.2 | Add max bots per client limit (DoS protection) | `sonarft_server.py` | 1 hour | ✅ |
| 3.3 | Add order rate limiting (max N orders/minute per bot) | `sonarft_execution.py` | 2 hours | ✅ |
| 3.4 | Add maximum position size parameter | `sonarft_bot.py`, `sonarft_execution.py` | 1 hour | ✅ |
| 3.5 | Add minimum order size validation | `sonarft_execution.py` | 1 hour | ✅ |
| 3.6 | Add `restart: unless-stopped` + health check to Docker | `Dockerfile`, `docker-compose.yml` | 30 min | ✅ |
| 3.7 | Add `PYTHONUNBUFFERED=1` to Dockerfile | `Dockerfile` | 5 min | ✅ |
| 3.8 | Call `close_exchange()` on bot shutdown | `sonarft_bot.py` | 30 min | ✅ |
| 3.9 | Consolidate 5 config loaders into 1 generic loader | `sonarft_bot.py` | 1 hour | ✅ |
| 3.10 | Remove duplicate `BotCreationError` class | `sonarft_manager.py` | 15 min | ✅ |
| 3.11 | Write unit tests for indicators (RSI, MACD, StochRSI) | `tests/test_sonarft_indicators.py` | 4 hours | ✅ |
| 3.12 | Write integration tests for simulation mode gate | `tests/test_simulation.py` | 2 hours | ✅ |

---

## Phase 4 — Production Ready (~80 hours)

| # | Task | File(s) | Effort | Status |
|---|---|---|---|---|
| 4.1 | Replace trade history JSON with SQLite | `sonarft_helpers.py` | 8 hours | ⬜ |
| 4.2 | Add persistent server-side logging with rotation | `sonarft_server.py` | 4 hours | ⬜ |
| 4.3 | Add alerting for circuit breaker trips | `sonarft_bot.py` | 4 hours | ⬜ |
| 4.4 | Add emergency stop endpoint for all bots | `sonarft_server.py`, `sonarft_manager.py` | 2 hours | ⬜ |
| 4.5 | Add hot-reload for parameter changes | `sonarft_bot.py`, `sonarft_server.py` | 4 hours | ⬜ |
| 4.6 | Upgrade `pandas` to 2.x | `requirements.txt` | 4 hours | ⬜ |
| 4.7 | Upgrade `fastapi` to current stable | `requirements.txt` | 2 hours | ⬜ |
| 4.8 | Remove dead dependencies (`python-dotenv`, `python-decouple`) | `requirements.txt` | 15 min | ⬜ |
| 4.9 | Wire `config_indicators.json` to actual indicator selection | Multiple files | 8 hours | ⬜ |
| 4.10 | Add indicator value cache | `sonarft_indicators.py` | 4 hours | ⬜ |
| 4.11 | Achieve ≥ 80% overall test coverage | `tests/` | 20 hours | ⬜ |

---

## Progress Summary

| Phase | Total Tasks | Done | Remaining |
|---|---|---|---|
| Phase 0 — Critical Bug Fixes | 5 | 5 | 0 🎉 |
| Phase 1 — Simulation Ready | 17 | 17 | 0 🎉 |
| Phase 2 — Paper Trading Ready | 14 | 14 | 0 🎉 |
| Phase 3 — Live Trading Ready | 12 | 11 | 1 |
| Phase 4 — Production Ready | 11 | 0 | 11 |
| **Total** | **59** | **47** | **12** |

---

*Last updated: July 2025*
