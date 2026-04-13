# SonarFT — Security & Trading Risk Audit

## 1. Critical Findings

### CF-1: Path Traversal via `client_id` and `botid` URL Parameters

**Severity: Critical**

**File:** `sonarft_server.py`, all HTTP endpoints

```python
with open(f"sonarftdata/config/{client_id}_parameters.json", "r") as read_file:
with open(f"sonarftdata/history/{botid}_orders.json", "r") as read_file:
with open(f"sonarftdata/config/{client_id}_parameters.json", "w") as write_file:
```

`client_id` and `botid` are taken directly from URL path parameters and interpolated into file paths without any sanitisation. An attacker can supply:

- `client_id = "../../etc/passwd"` → reads `/etc/passwd`
- `client_id = "../../sonarftdata/config_fees"` → reads fee configuration
- `client_id = "../../sonarft_server"` → reads source code
- `POST /bot/set_parameters/../../sonarftdata/config` → overwrites config files

**Mitigation:**

```python
import re
from pathlib import Path

def validate_id(value: str) -> str:
    if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', value):
        raise HTTPException(status_code=400, detail="Invalid identifier")
    return value
```

Apply to all `client_id` and `botid` parameters before file access.

---

### CF-2: Fully Open CORS Policy

**Severity: Critical**

**File:** `sonarft_server.py`

```python
self.app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

`allow_origins=["*"]` combined with `allow_credentials=True` is an invalid CORS configuration — browsers will reject credentialed requests to wildcard origins per the CORS spec. More importantly, this allows any website to make cross-origin requests to the trading API, enabling CSRF-style attacks that could trigger bot creation, parameter changes, or trade history reads.

**Mitigation:** Restrict to known frontend origins:

```python
allow_origins=["https://sonarft.com", "http://localhost:3000"],
allow_credentials=True,
allow_methods=["GET", "POST"],
allow_headers=["Authorization", "Content-Type"],
```

---

### CF-3: Traefik Dashboard Exposed Without Authentication

**Severity: Critical**

**File:** `docker-compose.yml`

```yaml
- --api.insecure=true
```

The Traefik management dashboard is exposed on port 8080 with no authentication. Anyone who can reach `monitor.sonarft.com:8080` has full visibility into routing rules, TLS certificates, and service health — and can modify routing configuration.

**Mitigation:** Remove `--api.insecure=true` and configure Traefik's dashboard with BasicAuth middleware or restrict to internal network only.

---

## 2. Security Risk Table

| # | Risk | File | Severity | Scenario | Mitigation |
|---|---|---|---|---|---|
| 1 | Path traversal via `client_id` | `sonarft_server.py` | **Critical** | Read/write arbitrary files | Validate ID format |
| 2 | Open CORS + credentials | `sonarft_server.py` | **Critical** | CSRF from any origin | Restrict `allow_origins` |
| 3 | Traefik insecure API | `docker-compose.yml` | **Critical** | Unauthenticated admin access | Remove `--api.insecure=true` |
| 4 | Container runs as root | `Dockerfile` | **High** | Container escape → host root | Uncomment non-root user lines |
| 5 | `.env` baked into Docker image | `Dockerfile` | **High** | Secrets in image layers | Use Docker secrets or env vars at runtime |
| 6 | API keys stored in memory as plain strings | `sonarft_api_manager.py:setAPIKeys` | **High** | Memory dump exposes keys | Use OS keyring or encrypted store |
| 7 | No authentication on any HTTP endpoint | `sonarft_server.py` | **High** | Any client can create/remove bots | Add API key or JWT auth |
| 8 | No authentication on WebSocket endpoint | `sonarft_server.py` | **High** | Any client can control bots | Validate token on connect |
| 9 | `print()` used for sensitive data | `sonarft_server.py`, `sonarft_manager.py` | **Medium** | Logs to stdout — may be captured | Replace with `self.logger` |
| 10 | ACME email hardcoded in docker-compose | `docker-compose.yml` | **Low** | PII in source control | Move to environment variable |
| 11 | `[object Object]_parameters.json` in config dir | `sonarftdata/config/` | **Medium** | JavaScript object serialised as filename — indicates client-side bug sending raw object as ID | Validate `client_id` server-side |

---

## 3. Operational / Trading Risk Table

| # | Risk | File | Severity | Scenario | Mitigation |
|---|---|---|---|---|---|
| 1 | No maximum loss limit | Entire execution path | **Critical** | Bot executes unlimited losing trades | Add `max_daily_loss` parameter |
| 2 | No position size limit | `sonarft_math.py` | **High** | `trade_amount` uncapped — can exceed balance | Validate against available balance before search |
| 3 | Partial fill leaves open position | `sonarft_execution.py` | **High** | Buy filled, sell not placed — unhedged exposure | Implement partial fill handler |
| 4 | `monitor_price` infinite loop | `sonarft_execution.py` | **High** | Trade task hangs, capital locked | Add timeout |
| 5 | Simulation flag is integer, not bool | `config_parameters.json` | **Medium** | `is_simulating_trade=2` is truthy — simulation on, but unexpected | Validate as `0` or `1` only |
| 6 | Order history saved before order placed | `sonarft_execution.py` | **Medium** | Failed orders appear as attempted | Move `save_order_history` after order result |
| 7 | No circuit breaker on repeated failures | `sonarft_bot.py:run_bot` | **High** | Exchange outage → bot loops at full speed, exhausting rate limits | Add failure counter with backoff |
| 8 | No rate limit on bot creation | `sonarft_server.py` | **Medium** | Client creates thousands of bots → memory exhaustion | Limit bots per client |
| 9 | `random.randint(10001, 99999)` for botid | `sonarft_bot.py:create_botid` | **Low** | Collision possible with ~89,000 possible IDs | Use `uuid4()` |
| 10 | `time.time()` computed but unused in `create_botid` | `sonarft_bot.py` | **Low** | Dead code — `t` is assigned but never used | Remove |

---

## 4. Sensitive Data Logging

**File:** `sonarft_server.py`

```python
print(f"client: {client_id} - Botid: {botid} - Action: {action}")
```

`client_id` values (which may be UUIDs or user identifiers) are printed to stdout. In a containerised environment, stdout is typically captured by log aggregators. If `client_id` is a user identifier, this constitutes PII logging.

**File:** `sonarft_manager.py`

```python
self.logger.info(f"Library: {args.library}")
self.logger.info(f"Configuration: {args.config}")
```

These are safe — no secrets logged here.

**API keys** are set via `setAPIKeys` and stored as plain attributes on the exchange object (`exchange.apiKey`, `exchange.secret`). They are never logged, which is correct. However, any exception traceback that includes the exchange object could expose them.
