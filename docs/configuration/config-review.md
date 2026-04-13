# SonarFT — Configuration & Runtime Environment Review

## 1. Configuration Inventory

| File | Purpose | Schema Validated? | Loaded By |
|---|---|---|---|
| `config.json` | Named config sets — maps setup names to file paths | No | `SonarftBot.load_configurations` |
| `config_parameters.json` | Trading parameters (threshold, amount, simulation flag) | No | `SonarftBot.load_parameters` |
| `config_exchanges.json` | Exchange lists per setup | No | `SonarftBot.load_exchanges` |
| `config_symbols.json` | Trading pairs per setup | No | `SonarftBot.load_symbols` |
| `config_fees.json` | Per-exchange fee rates | No | `SonarftBot.load_fees` |
| `config_indicators.json` | Indicator settings | No | Referenced in `config.json` but **never loaded** in code |
| `config_markets.json` | Market type (crypto) | No | `SonarftBot.load_markets` |
| `sonarftdata/config/{client_id}_parameters.json` | Per-client runtime parameters | No | HTTP endpoints |
| `sonarftdata/config/{client_id}_indicators.json` | Per-client runtime indicators | No | HTTP endpoints |

---

## 2. Config Loading Behaviour

### `load_parameters` (`sonarft_bot.py`)

```python
return tuple(parameters.values())
```

Parameters are returned as a positional tuple from `dict.values()`. The caller unpacks:

```python
self.profit_percentage_threshold, self.trade_amount, self.is_simulating_trade = self.load_parameters(...)
```

**Risk:** Python dicts preserve insertion order (3.7+), but if the JSON file has keys in a different order, the values are assigned to the wrong variables. For example, if `is_simulating_trade` appears before `trade_amount` in the JSON, the bot will use the simulation flag as the trade amount. There is no key-based extraction.

**Fix:**

```python
params = json.load(f)[setup][0]
return params['profit_percentage_threshold'], params['trade_amount'], params['is_simulating_trade']
```

---

### `config_indicators.json` — Never Loaded

`config.json` references `indicators_pathname` and `indicators_setup`, but `SonarftBot.load_configurations` never calls a `load_indicators` method. The indicator config file is loaded only via the HTTP endpoints (`/bot/get_indicators/{client_id}`) for per-client runtime overrides. The bot's indicator behaviour is entirely hardcoded in `sonarft_prices.py` (e.g. `period=14`, `rsi_period=14`, `order_book_depth=6`).

---

### `config_1` and `config_2` are Identical

Both entries in `config.json` point to the same setup files. The multi-config system is not exercised.

---

## 3. File Path Handling

### Path Traversal Risk

**File:** `sonarft_server.py`, HTTP endpoints

```python
with open(f"sonarftdata/config/{client_id}_parameters.json", "r") as read_file:
```

`client_id` comes directly from the URL path parameter with no sanitisation. A malicious client can supply `client_id = "../../etc/passwd"` or `client_id = "../config"` to read or write arbitrary files on the server.

**Confirmed vulnerable endpoints:**
- `GET /bot/get_parameters/{client_id}`
- `POST /bot/set_parameters/{client_id}`
- `GET /bot/get_indicators/{client_id}`
- `POST /bot/set_indicators/{client_id}`
- `GET /bot/{botid}/orders`
- `GET /bot/{botid}/trades`

**Fix:**

```python
import re
if not re.match(r'^[a-zA-Z0-9_-]+$', client_id):
    raise HTTPException(status_code=400, detail="Invalid client_id")
```

Or use `pathlib.Path` with a base directory check:

```python
from pathlib import Path
base = Path("sonarftdata/config").resolve()
target = (base / f"{client_id}_parameters.json").resolve()
if not str(target).startswith(str(base)):
    raise HTTPException(status_code=400, detail="Invalid path")
```

---

### Relative Paths

All file paths are relative (e.g. `"sonarftdata/config.json"`). The bot must be launched from the project root directory. If launched from a different working directory, all file operations fail with `FileNotFoundError`. No `__file__`-relative path resolution is used.

---

## 4. Environment Variable Usage

`python-dotenv` and `python-decouple` are listed in `requirements.txt` but are not used anywhere in the source code. The `.env` file is copied into the Docker image but its contents are unknown — it may contain API keys.

**Risk:** Copying `.env` into the Docker image bakes secrets into the image layer. If the image is pushed to a registry, secrets are exposed.

---

## 5. Docker Deployment Assumptions

| Assumption | Risk |
|---|---|
| Container runs as root (non-root user lines are commented out in Dockerfile) | **High** — root container escalation risk |
| `.env` file copied into image | **High** — secrets baked into image |
| `acme.json` mounted from host with no permission check | Medium — TLS cert exposure |
| Traefik dashboard exposed on port 8080 with `--api.insecure=true` | **High** — unauthenticated admin access |
| `sonarftdata/history/` and `sonarftdata/bots/` created at build time but not mounted as volumes | Medium — trade history lost on container restart |

---

## 6. Missing Validation Rules

| Config Field | Type | Validated? | Risk if Invalid |
|---|---|---|---|
| `profit_percentage_threshold` | float | No | Negative value → all trades pass threshold |
| `trade_amount` | float | No | Zero → division by zero in fee calc |
| `is_simulating_trade` | int (0/1) | No | Any truthy value enables simulation |
| Exchange names in `config_exchanges.json` | string | No | Unknown exchange → ccxt `AttributeError` |
| Symbol `base`/`quote` fields | string | No | Invalid symbol → exchange API error |
| Fee rates in `config_fees.json` | float | No | Negative fee → profit inflated |

---

## 7. Recommended Validation Rules

```python
assert 0 < profit_percentage_threshold < 1, "Threshold must be between 0 and 1"
assert trade_amount > 0, "Trade amount must be positive"
assert is_simulating_trade in (0, 1), "Simulation flag must be 0 or 1"
assert all(e in SUPPORTED_EXCHANGES for e in exchanges), "Unknown exchange"
assert all(0 <= fee <= 0.01 for fee in fee_rates), "Fee rate out of range"
```

These should be enforced in `load_configurations` before any module is initialised.
