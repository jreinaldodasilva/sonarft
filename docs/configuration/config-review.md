# SonarFT — Configuration & Runtime Environment Review

**Review Date:** July 2025
**Codebase Version:** 1.0.0
**Reviewer Role:** Senior Python Engineer / Infrastructure & Operations Reviewer
**Scope:** Configuration file structure, loading behavior, validation, environment variables, file paths, Docker deployment, and runtime safety
**Follows:** [Execution & Exchange Integration Review](../trading/execution-analysis.md)

---

## 1. Configuration File Structure

### 1.1 Format

All configuration is stored as **JSON files** under `sonarftdata/`. No YAML, TOML, or Python dicts are used. No schema validation library (e.g., Pydantic, jsonschema) is present.

### 1.2 File Inventory

| File | Purpose | Format |
|---|---|---|
| `sonarftdata/config.json` | Named config sets — maps config names to file references | `{config_N: [{pathname, setup}]}` |
| `sonarftdata/config_parameters.json` | Trading parameters per setup | `{parameters_N: [{key: value}]}` |
| `sonarftdata/config_exchanges.json` | Exchange lists per setup | `{exchanges_N: [exchange_id]}` |
| `sonarftdata/config_symbols.json` | Trading pairs per setup | `{symbols_N: [{base, quotes}]}` |
| `sonarftdata/config_fees.json` | Fee rates per exchange | `{exchanges_fees_N: [{exchange, buy_fee, sell_fee}]}` |
| `sonarftdata/config_indicators.json` | Indicator setup names | `{indicators_N: [name]}` |
| `sonarftdata/config_markets.json` | Market type per setup | `{market_N: [type]}` |
| `sonarftdata/config/parameters.json` | Per-client default parameters (UI-facing) | Custom schema (exchanges/symbols toggles) |
| `sonarftdata/config/indicators.json` | Per-client default indicators (UI-facing) | Custom schema (periods/oscillators toggles) |
| `sonarftdata/config/{client_id}_parameters.json` | Per-client runtime parameters | Same as above |
| `sonarftdata/config/{client_id}_indicators.json` | Per-client runtime indicators | Same as above |
| `sonarftdata/history/{botid}_orders.json` | Order history per bot | JSON array |
| `sonarftdata/history/{botid}_trades.json` | Trade history per bot | JSON array |
| `sonarftdata/bots/{botid}.json` | Bot registry entry | `{botid: int}` |

### 1.3 All Configuration Parameters

| Parameter | File | Required | Type | Default | Validation | Purpose |
|---|---|---|---|---|---|---|
| `profit_percentage_threshold` | config_parameters.json | ✅ | float | 0.0001 | `0 < x < 1` | Min profit % to execute trade |
| `trade_amount` | config_parameters.json | ✅ | float | 1 | `> 0` | Base currency units per trade |
| `is_simulating_trade` | config_parameters.json | ✅ | int (0/1) | 1 | `in (0, 1)` | Simulation mode flag |
| `max_daily_loss` | config_parameters.json | ❌ | float | 0.0 | `>= 0` | Daily loss limit (0 = disabled) |
| `spread_increase_factor` | config_parameters.json | ❌ | float | 1.00072 | `1.0 < x < 1.01` | Spread widening factor |
| `spread_decrease_factor` | config_parameters.json | ❌ | float | 0.99936 | `0.99 < x < 1.0` | Spread narrowing factor |
| `exchanges` | config_exchanges.json | ✅ | list[str] | `["okx","binance"]` | None | Exchange IDs to use |
| `symbols` | config_symbols.json | ✅ | list[{base,quotes}] | BTC/USDT, ETH/USDT | None | Trading pairs |
| `buy_fee` / `sell_fee` | config_fees.json | ✅ | float | varies | None | Per-exchange fee rates |
| `market` | config_markets.json | ✅ | list[str] | `["crypto"]` | None | Market type |
| `indicators` | config_indicators.json | ✅ | list[str] | `["rsi"]` | None | Indicator names (loaded but unused) |

**Issue — `config_parameters.json` missing `spread_increase_factor`, `spread_decrease_factor`, `max_daily_loss`:**
```json
{
    "parameters_1": [{
        "profit_percentage_threshold": 0.0001,
        "trade_amount": 1,
        "is_simulating_trade": 1
    }]
}
```
The three optional parameters (`max_daily_loss`, `spread_increase_factor`, `spread_decrease_factor`) are not present in the default config file. They are loaded with `parameters.get(key, default)` — so they silently use hardcoded defaults. An operator who wants to configure these values has no documented example to follow.

**Issue — `config_1` and `config_2` are identical:**
Both named configs in `config.json` point to the same setups (`parameters_setup: 1`, `exchanges_setup: 1`, etc.). The second config provides no differentiation — it exists as a placeholder but offers no value.

### 1.4 Schema Validation

**⚠️ Not Found in Source Code** — No JSON schema validation is performed. Config files are loaded with raw `json.load()` and values are accessed by key. Invalid types, missing required keys, or out-of-range values will either:
- Raise a `KeyError` (missing required key) — caught by outer `try/except`, bot fails to start
- Raise a `TypeError` (wrong type) — caught similarly
- Pass silently (wrong value within valid type range) — no detection

The only validation present is `_validate_parameters()` in `sonarft_bot.py`, which checks 6 numeric parameters after loading. This is partial but better than nothing. ✅

---

## 2. Configuration Loading Behavior

### 2.1 Loading Entry Point

```
sonarft.py → SonarftServer → BotManager.create_bot()
    → SonarftBot.create_bot(config_setup)
        → load_configurations(config_setup)
            → open("sonarftdata/config.json")          [master config]
            → load_markets(pathname, setup)
            → load_parameters(pathname, setup)
            → load_symbols(pathname, setup)
            → load_exchanges(pathname, setup)
            → load_fees(pathname, setup)
            → _validate_parameters()
```

### 2.2 File Location Assumptions

All config paths are **relative to the working directory** at runtime:

```python
# sonarft_bot.py:160
pathname = "sonarftdata/config.json"
```

The bot must be launched from the `sonarft/` directory. If launched from a different directory, all config loads will fail with `FileNotFoundError`. The Dockerfile sets `WORKDIR /app` and copies files there, so Docker deployment is safe. ✅ Direct Python execution requires `cd sonarft/` first.

### 2.3 Environment Variable Overrides

**⚠️ Not Found in Source Code** — No environment variable overrides for trading parameters. The only environment variable used is `SONARFT_API_TOKEN` for API authentication.

`python-dotenv` and `python-decouple` are listed in `requirements.txt` but **neither is imported or used** anywhere in the source code. These are dead dependencies.

### 2.4 Config Merge Behavior

There is no config merging. Each named config (`config_1`, `config_2`) is a complete, independent configuration. There is no inheritance from a base config or override mechanism.

### 2.5 Missing Config Behavior

| Scenario | Behavior |
|---|---|
| `sonarftdata/config.json` missing | `FileNotFoundError` → bot fails to start, error logged |
| Named config key missing (e.g., `config_3`) | `KeyError` → bot fails to start |
| Parameter file missing | `FileNotFoundError` → bot fails to start |
| Optional parameter missing from JSON | `parameters.get(key, default)` → uses hardcoded default ✅ |
| Required parameter missing from JSON | `KeyError` → bot fails to start |

---

## 3. Per-Bot & Per-Client Configuration

### 3.1 Configuration Scopes

| Scope | What It Controls | Where Stored |
|---|---|---|
| Global (startup) | Library, config set name | CLI args (`-l`, `-c`) |
| Per-config-set | Exchanges, symbols, fees, parameters | `sonarftdata/config_*.json` |
| Per-client (runtime) | Parameters and indicators via API | `sonarftdata/config/{client_id}_*.json` |
| Per-bot | None — bots share the config set | N/A |

### 3.2 Per-Client Runtime Config

Clients can update parameters and indicators via REST API:
- `POST /bot/set_parameters/{client_id}` → writes `{client_id}_parameters.json`
- `POST /bot/set_indicators/{client_id}` → writes `{client_id}_indicators.json`

**Critical Issue — per-client config not used by running bots:**
The per-client config files are written to disk but never read back by the running `SonarftBot` instance. The bot loads its configuration once at creation and never re-reads it. The REST API gives the impression of live parameter control but has no effect on running bots.

**Issue — per-client config schema mismatch:**
The `sonarftdata/config/parameters.json` (default) contains exchange/symbol toggles:
```json
{"exchanges": {"Binance": true}, "symbols": {"BTC/USDT": true}}
```
But `SonarftBot.load_parameters` expects:
```json
{"profit_percentage_threshold": 0.0001, "trade_amount": 1, "is_simulating_trade": 1}
```
These are completely different schemas. The per-client config files written by the API are never read by the bot's config loader — they serve a different (UI display) purpose.

### 3.3 Bot Isolation

Each bot instance has its own:
- `botid` (random integer)
- Module instances (all created fresh in `InitializeModules`)
- Trade/order history files (`{botid}_orders.json`, `{botid}_trades.json`)

Bots share:
- The same config files (read-only at startup)
- The same `sonarftdata/` directory for history writes (no locking)
- The same exchange API connections (each bot creates its own instances) ✅

---

## 4. Environment Variable Usage

| Variable | Required | Default | Purpose | Security Risk |
|---|---|---|---|---|
| `SONARFT_API_TOKEN` | ❌ Optional | None (auth disabled) | Bearer token for HTTP/WS auth | Medium — if not set, all endpoints are public |
| `ACME_EMAIL` | ✅ (Docker) | None | Let's Encrypt email for TLS cert | Low |
| `TRAEFIK_DASHBOARD_USERS` | ✅ (Docker) | None | Basic auth for Traefik dashboard | Medium — must be set securely |

**Issue — auth disabled by default:**
```python
# sonarft_server.py:26-31
_API_TOKEN: Optional[str] = os.environ.get("SONARFT_API_TOKEN")

def _require_auth(...):
    if not _API_TOKEN:
        return  # auth disabled — no token configured
```
If `SONARFT_API_TOKEN` is not set, all HTTP endpoints and WebSocket connections are publicly accessible with no authentication. This is documented as "development mode only" but there is no enforcement or warning at startup.

**Issue — no API key management for exchanges:**
Exchange API keys (`api_key`, `secret_key`, `password`) are not loaded from environment variables or config files. The `setAPIKeys` method exists but is never called in the normal bot lifecycle (the call is commented out in `create_bot`). In live trading mode, the bot would attempt to place orders without authentication, which would fail with auth errors.

```python
# sonarft_bot.py:71
# await self.api_manager.setAPIKeys(self.botid)  ← COMMENTED OUT
```

**This is a critical gap for live trading** — there is no mechanism to inject exchange API keys into a running bot.


---

## 5. Defaults & Hardcoding Audit

### 5.1 Hardcoded Values Inventory

| Value | Location | Should Be Config? | Risk |
|---|---|---|---|
| `host="127.0.0.1"` | `sonarft.py:13` | ✅ Yes | Medium — cannot bind to 0.0.0.0 without code change |
| `port=5000` | `sonarft.py:13` | ✅ Yes | Low |
| `allow_origins=["https://sonarft.com","http://localhost:3000"]` | `sonarft_server.py:65` | ✅ Yes | Medium — hardcoded domain |
| `max_failures=5` | `sonarft_bot.py:89` | ✅ Yes | Low |
| `base_backoff=30` | `sonarft_bot.py:90` | ✅ Yes | Low |
| `timesleep_size = random.randint(6, 18)` | `sonarft_bot.py:121` | ✅ Yes | Low |
| `period=14, rsi_period=14, stoch_period=14` | `sonarft_prices.py:27-29` | ✅ Yes | Medium — indicator periods not configurable |
| `order_book_depth=6` | `sonarft_prices.py:32` | ✅ Yes | Low |
| `weight=12` | `sonarft_search.py:136` | ✅ Yes | Low |
| `depth=3` (price blending) | `sonarft_prices.py:99` | ✅ Yes | Low |
| `min_trading_volume_coefficient=50` | `sonarft_search.py:38,41` | ✅ Yes | Medium |
| `max_wait_seconds=120` (monitor_price) | `sonarft_execution.py:232` | ✅ Yes | Low |
| `max_wait_seconds=300` (monitor_order) | `sonarft_execution.py:278` | ✅ Yes | Low |
| `EXCHANGE_RULES` dict | `sonarft_math.py:19` | ✅ Yes | Medium — precision rules hardcoded |
| `LOW_VOLATILITY_THRESHOLD=0.1` | `sonarft_validators.py:8` | ✅ Yes | Low |
| `MEDIUM_VOLATILITY_THRESHOLD=0.5` | `sonarft_validators.py:9` | ✅ Yes | Low |
| `spread_rate_threshold=0.01` | `sonarft_indicators.py:16` | ✅ Yes | Low |
| `volatility_risk_factor=0.001` | `sonarft_prices.py:24` | ✅ Yes | Medium |
| `getcontext().prec=28` | `sonarft_math.py:10` | ❌ No | Low — correct value |

### 5.2 Unsafe Defaults

| Parameter | Default | Risk | Why Unsafe |
|---|---|---|---|
| `is_simulating_trade` | `1` (simulation ON) | Low | Safe default — simulation prevents real orders ✅ |
| `profit_percentage_threshold` | `0.0001` (0.01%) | **High** | Far below break-even for any exchange pair |
| `max_daily_loss` | `0.0` (disabled) | **High** | No loss limit — unlimited downside in live mode |
| `SONARFT_API_TOKEN` | None (auth disabled) | **High** | All endpoints publicly accessible |
| Exchange API keys | Not configured | **Critical** | Live trading impossible without keys |
| `spread_increase_factor` | `1.00072` | Low | Reasonable default |
| `spread_decrease_factor` | `0.99936` | Low | Reasonable default |

### 5.3 `config_indicators.json` — Loaded but Unused

```json
{"indicators_1": ["rsi"], "indicators_2": ["stoch rsi"]}
```

This file is referenced in `config.json` and loaded via `config["indicators_pathname"]`, but the loaded value is never used anywhere in the bot. The indicator selection is hardcoded in `weighted_adjust_prices` — all indicators (RSI, MACD, StochRSI, SMA, volatility) are always computed regardless of this config. This creates a false impression that indicators can be toggled via config.

---

## 6. Docker Runtime Assumptions

### 6.1 Dockerfile Review

```dockerfile
FROM python:3.10.6          # ✅ Pinned version
WORKDIR /app                # ✅ Explicit working directory
RUN groupadd -r appgroup && useradd -r -g appgroup appuser  # ✅ Non-root user
...
USER appuser                # ✅ Runs as non-root
EXPOSE 5000
CMD ["python3", "sonarft.py"]
```

**Strengths:**
- Pinned Python version (3.10.6) ✅
- Non-root user (`appuser`) ✅
- Explicit `WORKDIR /app` ✅
- `.env` explicitly not copied (comment explains runtime injection) ✅

**Issues:**

| Issue | Description | Severity |
|---|---|---|
| No `--no-cache-dir` on pip install | Docker layer caches pip packages — increases image size | Low |
| No `requirements.txt` hash pinning | `pip install -r requirements.txt` installs exact versions but no hash verification | Low |
| `sonarftdata/config_indicators.json` copied but unused | Dead file in image | Low |
| No health check | Docker has no way to verify the bot is running correctly | Medium |
| No `PYTHONDONTWRITEBYTECODE=1` | `.pyc` files written inside container | Low |
| No `PYTHONUNBUFFERED=1` | Log output may be buffered, delaying visibility | Medium |

### 6.2 docker-compose.yml Review

```yaml
services:
  traefik:
    image: traefik:v2.5
    command:
      - --api.insecure=false    # ✅ Dashboard not exposed insecurely
      - --certificatesresolvers.myresolver.acme.tlschallenge=true  # ✅ TLS
    labels:
      - "traefik.http.middlewares.dashboard-auth.basicauth.users=${TRAEFIK_DASHBOARD_USERS}"  # ✅ Auth

  sonarft:
    image: sonarft:latest
    volumes:
      - sonarft_history:/app/sonarftdata/history  # ✅ Persistent history
      - sonarft_bots:/app/sonarftdata/bots        # ✅ Persistent bot registry
```

**Strengths:**
- TLS via ACME (Let's Encrypt) ✅
- Traefik dashboard protected with basic auth ✅
- Trade history and bot registry on named volumes (persistent across restarts) ✅
- `api.insecure=false` ✅

**Issues:**

| Issue | Description | Severity |
|---|---|---|
| `sonarft` service has no `environment:` section | `SONARFT_API_TOKEN` must be set but there's no example of how | **High** |
| No `restart: unless-stopped` | Container won't restart on crash | Medium |
| No resource limits (`mem_limit`, `cpus`) | Bot could consume all host memory | Medium |
| `sonarft_config` not a volume | Config files are baked into the image — cannot be updated without rebuild | Medium |
| Traefik mounts `/var/run/docker.sock` | Gives Traefik full Docker API access — security risk | Medium |
| No `PYTHONUNBUFFERED` env var | Logs may be buffered | Low |

### 6.3 Server Bind Address

```python
# sonarft.py:13
config = Config(app=server.app, host="127.0.0.1", port=5000)
```

The server binds to `127.0.0.1` (localhost only). Inside a Docker container, this means Traefik cannot reach the bot — Traefik routes traffic to the container's internal IP, not localhost. The server must bind to `0.0.0.0` for Docker networking to work.

**This is a critical deployment bug** — the Docker setup as written will not work because Traefik cannot connect to a service bound to `127.0.0.1` inside the container.

---

## 7. File Paths & History Storage

### 7.1 Path Construction

| Path | Construction | Safe? |
|---|---|---|
| `sonarftdata/config.json` | Hardcoded string | ✅ |
| `sonarftdata/config/{client_id}_parameters.json` | f-string with `client_id` | ⚠️ Validated by `_validate_id` |
| `sonarftdata/history/{botid}_orders.json` | f-string with `botid` | ⚠️ Validated by `_validate_id` |
| `sonarftdata/bots/{botid}.json` | `os.path.join` | ✅ |
| `errors_history.json` | Hardcoded, no directory | ⚠️ Written to working directory |
| `balance_history.json` | Hardcoded, no directory | ⚠️ Written to working directory |

### 7.2 History Storage

Trade and order history are stored as **append-only JSON arrays** in flat files. Each write reads the entire file, appends one record, and rewrites the entire file. For a bot running 24/7, these files will grow indefinitely with no rotation or archival mechanism.

**Issue — no log rotation or file size limit:**
After months of operation, `{botid}_orders.json` could contain tens of thousands of records. Each write reads and rewrites the entire file — O(n) per write, growing slower over time.

### 7.3 Missing Directories

The Dockerfile creates `sonarftdata/history/` and `sonarftdata/bots/` but not `sonarftdata/config/`. If the config directory doesn't exist, writing per-client config files will fail with `FileNotFoundError`.

For direct Python execution (non-Docker), none of these directories are created automatically — the user must create them manually before first run.

---

## 8. Path Safety & Traversal Risks

### 8.1 `_validate_id` Protection

```python
# sonarft_server.py:22-39
_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')

def _validate_id(value: str, label: str = "identifier") -> str:
    if not _ID_PATTERN.match(value):
        raise HTTPException(status_code=400, detail=f"Invalid {label}")
    return value
```

`_validate_id` is applied to `client_id` and `botid` in all HTTP endpoints that use them in file paths. The regex `^[a-zA-Z0-9_-]{1,64}$` prevents path traversal (`../`), null bytes, and special characters. ✅

**Issue — `_validate_id` not applied in WebSocket endpoint:**
```python
# sonarft_server.py:216
async def websocket_endpoint(websocket: WebSocket, client_id: str, token: Optional[str] = None):
    ...
    _validate_id(client_id, "client_id")  # ✅ Applied
```
`_validate_id` is called in the WebSocket endpoint. ✅

**Issue — `botid` in `sonarft_helpers.py` not validated:**
```python
# sonarft_helpers.py:54-55
pathname = botid + ".json"
file_name = os.path.join('sonarftdata', 'bots', pathname)
```
`botid` here is an integer (from `random.randint`), so path traversal is not possible. ✅ However, if `botid` were ever changed to accept user input, this would be a risk.

### 8.2 Config File Path Injection

```python
# sonarft_bot.py:160-188
config = loadconfig[config_setup][0]
self.load_markets(config["markets_pathname"], ...)
```

The `markets_pathname` value comes from `config.json` — a file controlled by the operator, not user input. Path traversal via config files is a deployment-time risk, not a runtime attack vector. ✅

---

## 9. Configuration Validation

### 9.1 Validation Present

```python
# sonarft_bot.py:191-204
def _validate_parameters(self):
    if not (0 < self.profit_percentage_threshold < 1): raise ValueError(...)
    if self.trade_amount <= 0: raise ValueError(...)
    if self.is_simulating_trade not in (0, 1): raise ValueError(...)
    if self.max_daily_loss < 0: raise ValueError(...)
    if not (1.0 < self.spread_increase_factor < 1.01): raise ValueError(...)
    if not (0.99 < self.spread_decrease_factor < 1.0): raise ValueError(...)
```

**Assessment:** 6 parameters validated with range checks. ✅ Raises `ValueError` on violation — caught by `BotCreationError` handler, bot fails to start with a clear error message.

### 9.2 Validation Gaps

| Parameter | Validated? | Gap |
|---|---|---|
| `profit_percentage_threshold` | ✅ `0 < x < 1` | Range too wide — 0.5 (50%) is valid but nonsensical |
| `trade_amount` | ✅ `> 0` | No maximum — 1000 BTC is valid |
| `is_simulating_trade` | ✅ `in (0, 1)` | ✅ |
| `max_daily_loss` | ✅ `>= 0` | ✅ |
| `spread_increase_factor` | ✅ `1.0 < x < 1.01` | Very tight range — may reject valid configs |
| `spread_decrease_factor` | ✅ `0.99 < x < 1.0` | Very tight range — may reject valid configs |
| Exchange IDs | ❌ Not validated | Invalid exchange name crashes at instance creation |
| Symbol format | ❌ Not validated | Malformed symbol causes API errors |
| Fee rates | ❌ Not validated | Negative fees or fees > 1 not caught |
| Config file paths | ❌ Not validated | Path traversal possible in config.json |

---

## 10. Configuration Issues Table

| # | Issue | Location | Type | Severity | Remediation |
|---|---|---|---|---|---|
| 1 | Exchange API keys not loaded | `sonarft_bot.py:71` | Missing feature | **Critical** | Implement API key loading from env vars or secure config |
| 2 | Server binds to `127.0.0.1` | `sonarft.py:13` | Deployment bug | **Critical** | Change to `0.0.0.0` or make configurable via env var |
| 3 | `SONARFT_API_TOKEN` not set = no auth | `sonarft_server.py:26` | Security | **High** | Require token in production; add startup warning if unset |
| 4 | Per-client config not hot-reloaded | `sonarft_server.py:134` | Logic gap | **High** | Implement hot-reload or document restart requirement clearly |
| 5 | `max_daily_loss` defaults to 0 (disabled) | `config_parameters.json` | Unsafe default | **High** | Set a sensible default; require explicit opt-out |
| 6 | `profit_percentage_threshold` default too low | `config_parameters.json` | Unsafe default | **High** | Change default to ≥ 0.003 |
| 7 | `config_indicators.json` loaded but unused | `sonarft_bot.py` | Dead config | Medium | Either wire it to indicator selection or remove |
| 8 | `python-dotenv` / `python-decouple` unused | `requirements.txt` | Dead dependency | Medium | Remove from requirements.txt |
| 9 | No `restart: unless-stopped` in docker-compose | `docker-compose.yml` | Ops gap | Medium | Add restart policy |
| 10 | No health check in Dockerfile | `Dockerfile` | Ops gap | Medium | Add `HEALTHCHECK` instruction |
| 11 | `PYTHONUNBUFFERED` not set | `Dockerfile` | Ops gap | Medium | Add `ENV PYTHONUNBUFFERED=1` |
| 12 | History files grow unbounded | `sonarft_helpers.py` | Ops gap | Medium | Add rotation or size limit |
| 13 | `sonarftdata/config/` not created in Dockerfile | `Dockerfile` | Deployment gap | Medium | Add `mkdir sonarftdata/config` |
| 14 | `errors_history.json` written to working dir | `sonarft_helpers.py` | Path issue | Low | Move to `sonarftdata/` |
| 15 | `config_1` and `config_2` identical | `config.json` | Config quality | Low | Differentiate or document purpose |
| 16 | Indicator periods hardcoded in `sonarft_prices.py` | `sonarft_prices.py:27-32` | Hardcoding | Low | Move to config |
| 17 | No fee rate validation | `config_fees.json` | Validation gap | Low | Validate `0 <= fee < 0.1` |

---

## 11. Runtime Configuration Summary

| Aspect | Current Method | Safe? | Recommendation |
|---|---|---|---|
| Trading parameters | JSON file, loaded once at startup | ⚠️ No hot-reload | Add hot-reload or document restart |
| Exchange API keys | Not implemented | ❌ | Load from env vars at bot creation |
| API authentication | Optional env var | ⚠️ Disabled by default | Require in production |
| Server bind address | Hardcoded `127.0.0.1` | ❌ Breaks Docker | Make configurable via env var |
| Indicator selection | Hardcoded in source | ⚠️ | Wire to config_indicators.json |
| Config validation | Partial (6 params) | ⚠️ | Add schema validation for all files |
| Secrets management | None | ❌ | Use Docker secrets or env vars |

---

## 12. Docker Configuration Review

| Aspect | Status | Notes |
|---|---|---|
| Base image | ✅ `python:3.10.6` pinned | Good |
| Non-root user | ✅ `appuser` | Good |
| Working directory | ✅ `/app` | Good |
| TLS | ✅ ACME via Traefik | Good |
| Secrets in image | ✅ `.env` not copied | Good |
| Server bind address | ❌ `127.0.0.1` | Breaks Traefik routing |
| `SONARFT_API_TOKEN` | ❌ Not in compose | Must be added to `environment:` |
| Health check | ❌ Missing | Add `HEALTHCHECK` |
| Restart policy | ❌ Missing | Add `restart: unless-stopped` |
| Log buffering | ⚠️ `PYTHONUNBUFFERED` not set | Add to Dockerfile |
| Config updates | ❌ Requires image rebuild | Mount config as volume |
| Resource limits | ❌ Not set | Add `mem_limit`, `cpus` |

---

## 13. Conclusion

### Configuration System Maturity: **Developing** ⭐⭐

The configuration system has a solid foundation — JSON-based, named config sets, partial parameter validation, and path traversal protection. However, several critical gaps prevent production deployment.

### Critical Issues (must fix before live deployment)

1. **Exchange API keys not loaded** — The `setAPIKeys` call is commented out. Live trading is impossible without a mechanism to inject exchange credentials. Implement loading from environment variables:
   ```python
   # In create_bot, after api_manager initialization:
   for exchange_id in self.exchanges:
       api_key = os.environ.get(f"{exchange_id.upper()}_API_KEY")
       secret  = os.environ.get(f"{exchange_id.upper()}_SECRET")
       password = os.environ.get(f"{exchange_id.upper()}_PASSWORD", "")
       if api_key and secret:
           self.api_manager.setAPIKeys(exchange_id, api_key, secret, password)
   ```

2. **Server binds to `127.0.0.1`** — Change to `0.0.0.0` or read from `HOST` env var:
   ```python
   host = os.environ.get("HOST", "0.0.0.0")
   config = Config(app=server.app, host=host, port=5000)
   ```

3. **No API authentication by default** — Add a startup warning and consider requiring the token in non-development environments.

### High Priority Fixes

4. **Add `SONARFT_API_TOKEN` to `docker-compose.yml`** environment section
5. **Change `profit_percentage_threshold` default** to a value above break-even (≥ 0.003)
6. **Set `max_daily_loss`** to a non-zero default or require explicit configuration
7. **Add `restart: unless-stopped`** and `HEALTHCHECK` to Docker configuration
8. **Remove dead dependencies** (`python-dotenv`, `python-decouple`) from `requirements.txt`

---

*Generated as part of the SonarFT code review suite — Prompt 07: Configuration & Runtime Environment Review*
*Previous: [execution-analysis.md](../trading/execution-analysis.md)*
*Next: [08-security-risk.md](../prompts/08-security-risk.md)*
