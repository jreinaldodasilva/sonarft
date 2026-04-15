# SonarFT — Security & Trading Risk Review

**Review Date:** July 2025
**Codebase Version:** 1.0.0
**Reviewer Role:** Security Auditor / Trading Safety Reviewer
**Scope:** Secret handling, input validation, injection risks, WebSocket security, API exposure, DoS risks, trading safety controls, financial risk management, logging, and dependency security
**Follows:** [Configuration & Runtime Environment Review](../configuration/config-review.md)

---

## 1. Secret & Credential Handling

### 1.1 Exchange API Keys

**⚠️ Not Found in Source Code** — Exchange API keys (`api_key`, `secret`, `password`) are never loaded from any source in the normal bot lifecycle. The `setAPIKeys` call in `create_bot` is commented out:

```python
# sonarft_bot.py:71
# await self.api_manager.setAPIKeys(self.botid)  ← COMMENTED OUT
```

The `setAPIKeys` method exists on both `SonarftBot` and `SonarftApiManager` but is never called. In live trading mode (`is_simulating_trade = 0`), all order placement calls will fail with authentication errors from the exchange.

**Risk:** No exchange credentials = no live trading possible. However, this also means no credentials can be accidentally leaked. The risk is operational, not a security vulnerability.

### 1.2 API Token for Server Authentication

```python
# sonarft_server.py:26
_API_TOKEN: Optional[str] = os.environ.get("SONARFT_API_TOKEN")
```

- Loaded from environment variable ✅
- Not hardcoded in source ✅
- Not logged anywhere ✅
- If not set, authentication is disabled (all endpoints public) ⚠️

### 1.3 Secrets in Logs

Scanning all `logger.info/warning/error` calls for sensitive data:

| Log Statement | File | Sensitive? | Risk |
|---|---|---|---|
| `f"Library: {args.library}"` | manager:132 | No | Low |
| `f"Configuration: {args.config}"` | manager:133 | No | Low |
| `f"Exchanges loaded: {exchanges}"` | bot:261 | Exchange names only | Low |
| `f"Parameters loaded: {', '.join(f'{k}: {v}' for k, v in parameters.items())}"` | bot:237 | **Yes — logs all parameter values** | Medium |
| `f"Creating {side} order on {exchange_id} for {trade_amount} {base} at {price} {quote}"` | execution:213 | Trade details | Low |
| `f"RSI buy={...} sell={...}"` | prices:143 | Indicator values | Low |
| `f"client: {client_id} - Botid: {botid} - Action: {action}"` | server:285 | Client/bot IDs | Low |

**Issue — parameters logged at startup:**
```python
# sonarft_bot.py:237
self.logger.info(
    f"Parameters loaded: {', '.join(f'{k}: {v}' for k, v in parameters.items())}"
)
```
This logs all parameter key-value pairs including `is_simulating_trade`, `profit_percentage_threshold`, and `trade_amount`. These are operational parameters, not secrets. However, if future parameters include API keys or secrets, this log statement would expose them. The pattern is risky.

**No credentials found in logs.** ✅ No API keys, secrets, or passwords are logged anywhere.

### 1.4 Secrets in Config Files

Config files (`config_parameters.json`, `config_exchanges.json`, etc.) contain no secrets — only exchange names, trading parameters, and fee rates. ✅

### 1.5 `.gitignore` Compliance

The `.gitignore` includes:
- `.env` ✅ — environment files excluded
- `.envrc` ✅
- `env/`, `venv/` ✅ — virtual environments excluded

**Missing from `.gitignore`:**
- `sonarftdata/history/` — trade history files (contain trade amounts, prices, profits) ⚠️
- `sonarftdata/bots/` — bot registry files ⚠️
- `sonarftdata/config/` — per-client config files ⚠️
- `acme.json` — TLS certificate storage (contains private key material) ❌ **Critical**

**`acme.json` contains TLS private keys and should never be committed to version control.** It is present in the repository root and not excluded by `.gitignore`.

---

## 2. Input Validation & Injection Risks

### 2.1 HTTP Endpoint Input Validation

| Endpoint | Input | Validated? | Risk |
|---|---|---|---|
| `GET /botids/{client_id}` | `client_id` path param | ✅ `_validate_id` regex | Low |
| `GET /bot/get_parameters/{client_id}` | `client_id` path param | ✅ `_validate_id` regex | Low |
| `POST /bot/set_parameters/{client_id}` | `client_id` + JSON body | ✅ ID validated; ❌ body not validated | **High** |
| `POST /bot/set_indicators/{client_id}` | `client_id` + JSON body | ✅ ID validated; ❌ body not validated | **High** |
| `GET /bot/{botid}/orders` | `botid` path param | ✅ `_validate_id` regex | Low |
| `GET /bot/{botid}/trades` | `botid` path param | ✅ `_validate_id` regex | Low |

**Issue — JSON body written to disk without validation:**
```python
# sonarft_server.py:134-138
async def set_bot_parameters(client_id: str, new_parameters: dict = Body(...), ...):
    with open(f"sonarftdata/config/{client_id}_parameters.json", "w") as write_file:
        json.dump(new_parameters, write_file, ...)
```

Any authenticated client can write arbitrary JSON to `{client_id}_parameters.json`. While the file is not currently read by the running bot, if hot-reload is implemented in the future, this becomes a direct injection vector — an attacker could set `is_simulating_trade: 0` to enable live trading, or set `trade_amount: 1000000` to place enormous orders.

### 2.2 WebSocket Input Validation

```python
# sonarft_server.py:280-284
event = self.decode_json(data)
if not event or "type" not in event or "key" not in event:
    return
botid = event.get("botid")
action = self.actions.get(event["key"])
```

- JSON parsing is safe (malformed JSON returns `None` from `decode_json`) ✅
- `event["key"]` is looked up in `self.actions` dict — only `create`, `run`, `remove` are valid ✅
- `botid` is taken directly from the event without validation ⚠️

**Issue — `botid` from WebSocket not validated:**
```python
botid = event.get("botid")  # no _validate_id call
await self.perform_action(action, botid or client_id)
```
`botid` is passed to `BotManager.run_bot(botid)` and `BotManager.remove_bot(botid)` without validation. If `botid` contains path traversal characters, it could affect file operations in `SonarftHelpers`. However, `botid` is an integer in normal operation, so the practical risk is low.

### 2.3 Command Injection

**⚠️ Not Found in Source Code** — No `subprocess`, `os.system`, `eval`, or `exec` calls anywhere in the Python codebase. No command injection risk. ✅

### 2.4 JSON Injection

All JSON is parsed with `json.loads()` / `json.load()` — standard library, no injection risk. ✅

### 2.5 Path Traversal

`_validate_id` regex `^[a-zA-Z0-9_-]{1,64}$` prevents `../` in `client_id` and `botid` for HTTP endpoints. ✅ WebSocket `botid` is not validated but is an integer in practice. ✅

---

## 3. File Path Safety

### 3.1 Path Construction Safety

| Path | Construction | Traversal Protected? |
|---|---|---|
| `sonarftdata/config/{client_id}_parameters.json` | f-string | ✅ `_validate_id` applied |
| `sonarftdata/config/{client_id}_indicators.json` | f-string | ✅ `_validate_id` applied |
| `sonarftdata/history/{botid}_orders.json` | f-string | ✅ `_validate_id` applied |
| `sonarftdata/history/{botid}_trades.json` | f-string | ✅ `_validate_id` applied |
| `sonarftdata/bots/{botid}.json` | `os.path.join` | ✅ botid is integer |
| Config pathnames from `config.json` | Direct string from file | ⚠️ Operator-controlled |

**Assessment:** Path traversal protection is adequate for user-supplied IDs. ✅

### 3.2 File Permission Safety

The Dockerfile runs as `appuser` (non-root). The `sonarftdata/` directory is owned by `appuser`. No world-writable directories are created. ✅

---

## 4. WebSocket Security

### 4.1 Authentication

```python
# sonarft_server.py:216-219
async def websocket_endpoint(websocket: WebSocket, client_id: str, token: Optional[str] = None):
    if _API_TOKEN and token != _API_TOKEN:
        await websocket.close(code=1008)  # Policy Violation
        return
```

- Token passed as query parameter (`/ws/{client_id}?token=...`) ⚠️
- If `_API_TOKEN` is not set, all WebSocket connections are accepted without authentication ⚠️
- Token in URL query string is visible in server logs, browser history, and proxy logs

**Issue — token in URL query string:**
WebSocket tokens should be passed in the `Authorization` header or as the first message after connection, not in the URL. Query string tokens are logged by web servers, proxies, and CDNs, potentially exposing the token.

### 4.2 Message Validation

```python
# sonarft_server.py:280-284
if not event or "type" not in event or "key" not in event:
    return
action = self.actions.get(event["key"])
```

- Malformed JSON handled ✅
- Unknown `key` values result in `action = None`, which is checked before execution ✅
- No message size limit — a very large JSON message could consume memory ⚠️

### 4.3 DoS via Message Flood

A connected client can send messages as fast as the server can process them. Each message creates an `asyncio.create_task` for a bot action. Tasks are appended to `self.tasks` without a size limit. A flood of `create` messages would:
1. Create many bot instances (each consuming memory and exchange connections)
2. Fill `self.tasks` list unboundedly
3. Potentially exhaust exchange API rate limits

**No rate limiting on WebSocket messages.** ⚠️


---

## 5. API Exposure Risks

### 5.1 Endpoint Authentication Coverage

| Endpoint | Auth Required | Rate Limited | Input Validated |
|---|---|---|---|
| `GET /botids/{client_id}` | ✅ Bearer token | ❌ No | ✅ ID regex |
| `GET /default_parameters` | ✅ Bearer token | ❌ No | N/A |
| `GET /default_indicators` | ✅ Bearer token | ❌ No | N/A |
| `GET /bot/get_parameters/{client_id}` | ✅ Bearer token | ❌ No | ✅ ID regex |
| `POST /bot/set_parameters/{client_id}` | ✅ Bearer token | ❌ No | ✅ ID; ❌ body |
| `GET /bot/get_indicators/{client_id}` | ✅ Bearer token | ❌ No | ✅ ID regex |
| `POST /bot/set_indicators/{client_id}` | ✅ Bearer token | ❌ No | ✅ ID; ❌ body |
| `GET /bot/{botid}/orders` | ✅ Bearer token | ❌ No | ✅ ID regex |
| `GET /bot/{botid}/trades` | ✅ Bearer token | ❌ No | ✅ ID regex |
| `WS /ws/{client_id}` | ⚠️ Optional token | ❌ No | ✅ ID; ⚠️ botid |

**All endpoints require authentication when `SONARFT_API_TOKEN` is set.** ✅
**No endpoint has rate limiting.** ⚠️

### 5.2 Error Message Information Leakage

```python
# sonarft_server.py:100
raise HTTPException(status_code=500, detail=str(error)) from error
```

All 500 errors return `str(error)` as the detail — the raw Python exception message. This can expose:
- Internal file paths (`FileNotFoundError: [Errno 2] No such file or directory: 'sonarftdata/...'`)
- Stack trace fragments in some exception types
- Internal state information

**Fix:** Return a generic message for 500 errors; log the full error server-side:
```python
self.logger.error(f"Internal error: {error}")
raise HTTPException(status_code=500, detail="Internal server error") from error
```

### 5.3 CORS Configuration

```python
# sonarft_server.py:64-68
allow_origins=["https://sonarft.com", "http://localhost:3000"],
allow_credentials=True,
allow_methods=["GET", "POST"],
allow_headers=["Authorization", "Content-Type"],
```

- Origins are explicitly listed (not `*`) ✅
- `allow_credentials=True` with specific origins is correct ✅
- Methods restricted to GET and POST ✅
- `allow_credentials=True` with `http://localhost:3000` allows credential sharing with local development — acceptable for dev, should be removed in production ⚠️

---

## 6. Denial of Service (DoS) Risks

### 6.1 Unbounded Task Creation

```python
# sonarft_server.py:302-307
task = asyncio.create_task(action_method(botid or client_id))
self.tasks.append(task)
```

No limit on the number of tasks in `self.tasks`. A client sending rapid `create` WebSocket messages creates unlimited bot instances. Each bot:
- Loads all config files (disk I/O)
- Creates exchange instances (memory)
- Opens WebSocket connections to exchanges (network)
- Starts background tasks

**DoS scenario:** 100 rapid `create` messages → 100 bot instances → 200+ exchange WebSocket connections → exchange rate limit bans the IP.

### 6.2 Unbounded OHLCV Cache

```python
# sonarft_api_manager.py:34
self._ohlcv_cache: Dict[str, Tuple[float, list]] = {}
```

Cache grows indefinitely. With many symbols, exchanges, and timeframes, each entry stores a list of OHLCV candles. For 45 candles × many symbols × many exchanges, memory consumption grows without bound over time.

### 6.3 Log Queue Overflow

```python
# sonarft_server.py:404
self.logs_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
```

The log queue has a `maxsize=1000`. ✅ When full, `put_nowait` raises `asyncio.QueueFull`. The `emit` method uses `put_nowait` without catching this exception:

```python
# sonarft_server.py:413
def emit(self, record: logging.LogRecord) -> None:
    self.logs_queue.put_nowait(record)  # raises QueueFull if full
```

A high-frequency logging scenario (e.g., rapid trade cycles) could fill the queue and crash the log handler, silently stopping all log streaming to the client.

### 6.4 `weighted_adjust_prices` Computation Cost

Each trade cycle per symbol triggers 18 parallel API calls. With N symbols and M exchanges, the number of concurrent API calls is `N × 18 × M`. For 10 symbols × 3 exchanges = 540 concurrent API calls per cycle. This could:
- Exhaust the default thread pool (ccxt mode)
- Trigger exchange rate limits
- Cause significant memory pressure from concurrent coroutines

### 6.5 `monitor_order` Blocking Duration

`monitor_order` polls every 1 second for up to 300 seconds (5 minutes). During this time, the trade execution task holds a reference to the exchange connection and blocks completion. Multiple concurrent trades could hold many connections open simultaneously.

---

## 7. Trading Safety Controls

### 7.1 Simulation Mode Gate

| Gate | Location | Enforced? |
|---|---|---|
| Balance check bypass | `sonarft_execution.py:323` | ✅ `if self.is_simulation_mode: return True` |
| Price monitoring bypass | `sonarft_execution.py:215` | ✅ `if self.is_simulation_mode: latest_price = price` |
| Order placement bypass | `sonarft_execution.py:259` | ✅ `if not self.is_simulation_mode: create_order(...)` |

**Assessment:** Simulation mode is consistently enforced at all three real-money touchpoints. ✅ There is no code path that places a real order when `is_simulation_mode = True`.

**Risk — type coercion:**
`is_simulating_trade` is loaded as `int` (0 or 1) from JSON. Python's truthiness means `not 1 == False` (simulation) and `not 0 == True` (live). This works correctly but is fragile — a future change to `bool` type or a JSON value of `true`/`false` instead of `1`/`0` could break the gate.

### 7.2 Maximum Position Size

**⚠️ Not Found in Source Code** — No maximum position size limit. `trade_amount` is a fixed config value with no upper bound validation beyond `> 0`. An operator could set `trade_amount = 10000` BTC and the bot would attempt to place a $600M order.

### 7.3 Maximum Loss Limit

`max_daily_loss` is implemented in `SonarftSearch.is_halted()` but:
- Defaults to `0.0` (disabled) in config
- `record_trade_result()` is never called — the accumulator is never updated
- Even if called, it only halts new trade searches, not in-flight trades

**The daily loss limit is effectively non-functional.** ⚠️

### 7.4 Circuit Breaker on Errors

```python
# sonarft_bot.py:88-116
consecutive_failures = 0
max_failures = 5
base_backoff = 30

while not self._stop_event.is_set():
    try:
        await self.sonarft_search.search_trades(self.botid)
        consecutive_failures = 0
    except Exception as e:
        consecutive_failures += 1
        backoff = base_backoff * consecutive_failures
        if consecutive_failures >= max_failures:
            self._stop_event.set()
            break
        await asyncio.wait_for(asyncio.shield(self._stop_event.wait()), timeout=backoff)
```

Circuit breaker stops the bot after 5 consecutive failures with exponential backoff. ✅

### 7.5 Manual Stop Mechanism

- WebSocket `{"key": "remove"}` → `BotManager.remove_bot()` → `SonarftBot.stop_bot()` → `_stop_event.set()` ✅
- No emergency stop for all bots simultaneously ⚠️
- No pause mechanism (only full stop) ⚠️

### 7.6 Order Rate Limiting

**⚠️ Not Found in Source Code** — No limit on how many orders can be placed per minute/hour. The bot places orders as fast as trade opportunities are found. In a malfunctioning state (e.g., indicator bug generating constant false signals), the bot could place orders continuously until the exchange rate-limits the account.

---

## 8. Financial Risk Management

### 8.1 Balance Check Before Trading

```python
# sonarft_execution.py:321-335
async def check_balance(self, exchange_id, base, quote, side, trade_amount, price):
    if self.is_simulation_mode:
        return True
    balance = await self.api_manager.get_balance(exchange_id)
    if side == 'buy':
        if balance['free'][quote] < trade_amount * price:
            return False
    elif side == 'sell':
        if balance['free'][base] < trade_amount:
            return False
    return True
```

Balance is checked before each order leg. ✅ However:
- `balance['free'][quote]` raises `KeyError` if the quote currency is not in the balance — not caught ⚠️
- Balance check and order placement are not atomic — balance could change between check and order ⚠️

### 8.2 Margin Requirements

**⚠️ Not Found in Source Code** — No margin requirement checks. The bot places spot limit orders only (no futures/margin trading in the current implementation). ✅ for spot trading.

### 8.3 Slippage Protection

**⚠️ Not Found in Source Code** — No slippage protection in live trading. `monitor_price` waits for a favorable price before placing the order, but once placed, the limit order may fill at a worse price if the market moves. No maximum slippage tolerance is enforced.

### 8.4 Runaway Trading Prevention

| Control | Present? | Effective? |
|---|---|---|
| Simulation mode gate | ✅ | ✅ |
| Circuit breaker (5 failures) | ✅ | ✅ |
| Daily loss limit | ✅ (code) | ❌ (never called) |
| Max position size | ❌ | — |
| Order rate limit | ❌ | — |
| Max concurrent trades | ❌ | — |

### 8.5 Liquidity Risk

`deeper_verify_liquidity` checks order book depth and trading volume before execution. ✅ However, the `min_trading_volume_coefficient = 50` hardcoded in `has_requirements_for_success_carrying_out` means the trading volume must be at least 50× the trade amount. For `trade_amount = 1 BTC`, this requires 50 BTC of trading volume — a reasonable threshold for liquid markets.

---

## 9. Logging & Monitoring

### 9.1 What Is Logged

| Category | Logged? | Destination |
|---|---|---|
| Bot lifecycle (create/run/stop) | ✅ | WebSocket stream to client |
| Trade search results (prices, profit) | ✅ | WebSocket stream |
| Order placement (exchange, amount, price) | ✅ | WebSocket stream |
| Indicator values (RSI, StochRSI, direction) | ✅ | WebSocket stream |
| API errors | ✅ | WebSocket stream |
| Exchange API keys | ❌ Not logged | — |
| Balance values | ❌ Not logged | — |
| Exception stack traces | ❌ Only `str(e)` | — |

### 9.2 Sensitive Values in Logs

- Trade amounts, prices, and profits are logged — these are operational data, not secrets ✅
- No API keys, secrets, or passwords are logged ✅
- `Parameters loaded: {all params}` logs all config values including `is_simulating_trade` — low risk but worth noting ⚠️

### 9.3 Log Storage

Logs are streamed over WebSocket to the connected client only. There is no persistent log file, no log rotation, and no log archival. If the client disconnects, all logs are lost. There is no server-side log persistence.

**Risk:** No audit trail for trades, errors, or security events. In a production financial system, logs must be persisted and retained.

### 9.4 Error Alerting

**⚠️ Not Found in Source Code** — No alerting mechanism (email, Slack, PagerDuty, etc.) for critical errors. The circuit breaker stops the bot silently — the operator only knows if they are connected via WebSocket at the time.

---

## 10. Dependency Security

### 10.1 Pinned Versions

```
fastapi==0.100.0
uvicorn==0.22.0
pandas==1.5.3
pandas-ta==0.3.14b0
ccxt==3.0.24
```

All versions are pinned. ✅ However, these are **July 2023 versions** — approximately 2 years old at time of review.

### 10.2 Known Vulnerability Assessment

| Package | Pinned Version | Current Stable | Known CVEs |
|---|---|---|---|
| `fastapi` | 0.100.0 | 0.115.x | Multiple security fixes since 0.100.0 |
| `uvicorn` | 0.22.0 | 0.32.x | Minor fixes |
| `pandas` | 1.5.3 | 2.2.x | End-of-life; no security patches |
| `pandas-ta` | 0.3.14b0 | 0.3.14b0 | Beta version — no stable release |
| `ccxt` | 3.0.24 | 4.x | Exchange compatibility updates |
| `python-dotenv` | 1.0.0 | 1.0.1 | Minor |
| `python-decouple` | 3.8 | 3.8 | Unused — dead dependency |

**Issues:**
- `pandas 1.5.3` is end-of-life — no security patches will be issued ⚠️
- `pandas-ta 0.3.14b0` is a beta version — not production-stable ⚠️
- `fastapi 0.100.0` is significantly outdated — upgrade recommended ⚠️
- `ccxt 3.0.24` is 2 years old — exchange API changes may have broken compatibility ⚠️

### 10.3 Supply Chain Risk

All packages are from PyPI. No private package indexes or custom mirrors are used. No hash verification in `requirements.txt`. A compromised PyPI package could inject malicious code. Using `pip install --require-hashes` would mitigate this.

---

## 11. Security Risk Table

| # | Risk Category | Specific Risk | Location | Severity | Likelihood | Mitigation |
|---|---|---|---|---|---|---|
| 1 | Secrets exposure | `acme.json` (TLS private key) not in `.gitignore` | `.gitignore` | **Critical** | High | Add `acme.json` to `.gitignore` immediately |
| 2 | Trading safety | Daily loss limit never updated — non-functional | `sonarft_search.py` | **Critical** | High | Call `record_trade_result()` after each trade |
| 3 | Trading safety | No maximum position size | Config | **High** | High | Add `max_trade_amount` parameter with validation |
| 4 | API security | Auth disabled by default (`SONARFT_API_TOKEN` unset) | `sonarft_server.py:26` | **High** | High | Require token; add startup warning |
| 5 | Injection | Unvalidated JSON body written to disk | `sonarft_server.py:138,168` | **High** | Medium | Validate body schema before writing |
| 6 | DoS | Unbounded bot creation via WebSocket flood | `sonarft_server.py:302` | **High** | Medium | Limit max bots per client |
| 7 | API security | 500 errors expose internal error messages | `sonarft_server.py:100` | **High** | High | Return generic 500 message; log internally |
| 8 | Trading safety | Order rate limiting absent | `sonarft_execution.py` | **High** | Medium | Add max orders per minute limit |
| 9 | WebSocket security | Token passed in URL query string | `sonarft_server.py:216` | Medium | Medium | Use first-message auth or subprotocol header |
| 10 | DoS | Log queue `put_nowait` raises on full queue | `sonarft_server.py:413` | Medium | Medium | Catch `QueueFull`; drop oldest log |
| 11 | DoS | Unbounded OHLCV cache memory growth | `sonarft_api_manager.py:34` | Medium | High | Add LRU eviction with max size |
| 12 | Financial risk | `balance['free'][quote]` KeyError on missing currency | `sonarft_execution.py:330` | Medium | Medium | Add `.get()` with default 0 |
| 13 | Dependency | `pandas 1.5.3` end-of-life | `requirements.txt` | Medium | Low | Upgrade to pandas 2.x |
| 14 | Dependency | `pandas-ta 0.3.14b0` beta version | `requirements.txt` | Medium | Low | Monitor for stable release |
| 15 | Secrets exposure | Parameters (including sim mode) logged at startup | `sonarft_bot.py:237` | Low | High | Exclude sensitive keys from log |
| 16 | Supply chain | No hash verification in requirements.txt | `requirements.txt` | Low | Low | Use `pip install --require-hashes` |
| 17 | Ops | No persistent log storage | All files | Low | High | Add file logging handler |
| 18 | Ops | No error alerting | All files | Low | High | Add alerting for circuit breaker trips |

---

## 12. Operational Risk Table

| # | Risk | Scenario | Impact | Preventing Control |
|---|---|---|---|---|
| 1 | Untracked open position | Buy fills, network drops before sell → unhedged long | Unlimited loss | None — `cancel_order` not implemented |
| 2 | Silent live trading activation | Operator sets `is_simulating_trade=0` without API keys → all orders fail silently | No trades, false confidence | Auth errors from exchange |
| 3 | Bot runs without operator awareness | Client disconnects; bot continues trading; no alerts | Unmonitored trading | Circuit breaker (5 failures) |
| 4 | Exchange rate limit ban | Rapid trade cycles + double rate limiting → IP banned | Bot stops working | `enableRateLimit: True` (partial) |
| 5 | Config change has no effect | Operator updates parameters via API → bot ignores them | Operator confusion | Documentation (not implemented) |
| 6 | TLS cert private key committed | `acme.json` committed to git → key exposed | MITM attacks possible | None currently |
| 7 | History file corruption | Two bots write simultaneously → JSON parse error | Trade history lost | None — no file locking |
| 8 | Bot stops silently | Circuit breaker trips → bot stops → no alert | Missed trading opportunities | None — no alerting |

---

## 13. Conclusion

### Security Assessment: **Needs Hardening** ⭐⭐

The codebase shows security awareness in several areas — path traversal protection, bearer token authentication, non-root Docker user, no hardcoded credentials, and simulation mode consistently gated. However, several critical issues must be addressed before production deployment.

### Critical Security Findings

1. **`acme.json` not in `.gitignore`** — TLS private key material could be committed to version control. Add immediately:
   ```
   acme.json
   sonarftdata/history/
   sonarftdata/bots/
   sonarftdata/config/
   ```

2. **Daily loss limit non-functional** — `record_trade_result()` is never called. The `max_daily_loss` safety control provides false assurance. Fix: call it in `TradeExecutor.monitor_trade_tasks` after each completed trade.

3. **No maximum position size** — `trade_amount` has no upper bound. Add `max_trade_amount` to config with validation.

4. **500 errors expose internal paths** — Replace `detail=str(error)` with `detail="Internal server error"` in all HTTP endpoints.

### Critical Trading Safety Findings

5. **No order rate limiting** — A malfunctioning indicator could trigger continuous order placement. Add a per-bot order rate limiter (e.g., max 10 orders per minute).

6. **No emergency stop for all bots** — Add a `POST /emergency_stop` endpoint that stops all running bots simultaneously.

### Hardening Recommendations

- Add `acme.json` and `sonarftdata/` subdirectories to `.gitignore`
- Require `SONARFT_API_TOKEN` in production with startup enforcement
- Validate JSON body schema in `set_parameters` and `set_indicators` endpoints
- Add max bots per client limit (e.g., 5) to prevent DoS via bot creation flood
- Add LRU eviction to `_ohlcv_cache` with configurable max size
- Upgrade `pandas` to 2.x and `fastapi` to current stable
- Add persistent server-side logging with rotation
- Add alerting for circuit breaker trips and critical errors

### Production Readiness Assessment

| Area | Status |
|---|---|
| Authentication | ⚠️ Optional — must be required in production |
| Input validation | ⚠️ IDs validated; JSON bodies not validated |
| Secret handling | ✅ No hardcoded secrets; ❌ `acme.json` not gitignored |
| Trading safety gates | ✅ Simulation mode; ❌ Loss limit non-functional |
| DoS protection | ❌ No rate limiting on any endpoint or bot creation |
| Error handling | ⚠️ Errors caught but internal details exposed |
| Dependency security | ⚠️ Outdated packages; no hash verification |
| Audit logging | ❌ No persistent logs |

---

*Generated as part of the SonarFT code review suite — Prompt 08: Security & Trading Risk Review*
*Previous: [config-review.md](../configuration/config-review.md)*
*Next: [09-performance-scalability.md](../prompts/09-performance-scalability.md)*
