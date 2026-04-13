# SonarFT — Operator Guide

**Version:** 1.0.0 (Post-Audit Release)
**Last Updated:** July 2025
**Applies To:** All deployment modes — development, paper trading, live trading

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Prerequisites](#2-prerequisites)
3. [Installation](#3-installation)
4. [Project Structure Reference](#4-project-structure-reference)
5. [Configuration Guide](#5-configuration-guide)
   - 5.1 [config.json — Named Configuration Sets](#51-configjson--named-configuration-sets)
   - 5.2 [config_parameters.json — Trading Parameters](#52-config_parametersjson--trading-parameters)
   - 5.3 [config_exchanges.json — Exchange List](#53-config_exchangesjson--exchange-list)
   - 5.4 [config_symbols.json — Trading Pairs](#54-config_symbolsjson--trading-pairs)
   - 5.5 [config_fees.json — Fee Rates](#55-config_feesjson--fee-rates)
   - 5.6 [config_markets.json — Market Type](#56-config_marketsjson--market-type)
6. [Environment Variables](#6-environment-variables)
7. [Running the Bot](#7-running-the-bot)
   - 7.1 [Direct Python Execution](#71-direct-python-execution)
   - 7.2 [Docker Deployment](#72-docker-deployment)
   - 7.3 [Command-Line Flags](#73-command-line-flags)
8. [REST API Reference](#8-rest-api-reference)
9. [WebSocket Protocol](#9-websocket-protocol)
10. [Deployment Modes](#10-deployment-modes)
    - 10.1 [Simulation Mode](#101-simulation-mode)
    - 10.2 [Paper Trading Mode](#102-paper-trading-mode)
    - 10.3 [Live Trading Mode](#103-live-trading-mode)
11. [Exchange API Keys Setup](#11-exchange-api-keys-setup)
12. [Multi-Bot Operation](#12-multi-bot-operation)
13. [Monitoring and Logs](#13-monitoring-and-logs)
14. [Trade and Order History](#14-trade-and-order-history)
15. [Safety Controls](#15-safety-controls)
16. [Troubleshooting](#16-troubleshooting)
17. [Operational Advisories](#17-operational-advisories)
18. [Known Limitations](#18-known-limitations)
19. [Upgrade and Maintenance](#19-upgrade-and-maintenance)

---

## 1. System Overview

SonarFT is an automated cryptocurrency trading bot that monitors market oscillations across one or more exchanges and executes trades when profitable opportunities are detected.

### How it works

```
WebSocket Client
      │
      ▼
SonarftServer (FastAPI)
      │
      ▼
BotManager ──► SonarftBot (one per bot instance)
                    │
                    ▼
              SonarftSearch ──► per-symbol concurrent processing
                    │
                    ▼
              SonarftPrices ──► VWAP + indicator-adjusted prices
                    │
                    ▼
              SonarftMath ──► fee + profit calculation (Decimal precision)
                    │
                    ▼
              TradeValidator ──► liquidity + spread threshold checks
                    │
                    ▼
              SonarftExecution ──► order placement (real or simulated)
                    │
                    ▼
              SonarftApiManager ──► ccxtpro (WebSocket) or ccxt (REST)
```

### Core trading cycle

1. Fetch VWAP bid/ask prices from all configured exchanges in parallel
2. Adjust prices using RSI, MACD, StochRSI, SMA, and volatility signals (all fetched in parallel, OHLCV cached per candle)
3. Calculate profit after fees using `Decimal` arithmetic
4. Validate liquidity depth and spread threshold
5. Execute buy and sell orders on the respective exchanges
6. Record order and trade history to JSON files

---

## 2. Prerequisites

### Required

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10.6 | Pinned in Dockerfile; 3.10.x recommended |
| pip | Latest | For dependency installation |
| Internet access | — | Required for exchange API connections |

### Optional (for Docker deployment)

| Requirement | Version | Notes |
|---|---|---|
| Docker | 20.x+ | Container runtime |
| Docker Compose | 2.x+ | Service orchestration |

### Exchange accounts

You need active accounts on the exchanges you configure. For live trading, API keys with **spot trading** permissions are required. For simulation mode, no API keys are needed — but the exchange must still be reachable for market data.

---

## 3. Installation

### Step 1 — Clone or download the project

```bash
cd ~/Development
git clone <repository-url> sonarft
cd sonarft
```

### Step 2 — Create a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

Dependencies installed:

| Package | Version | Purpose |
|---|---|---|
| fastapi | 0.100.0 | HTTP and WebSocket server |
| uvicorn | 0.22.0 | ASGI server |
| pandas | 1.5.3 | Time-series data for indicators |
| pandas-ta | 0.3.14b0 | RSI, MACD, StochRSI, SMA |
| ccxt | 3.0.24 | Exchange API (REST fallback) |
| python-dotenv | 1.0.0 | `.env` file loading |
| python-decouple | 3.8 | Environment variable management |
| simple-websocket | 0.10.1 | WebSocket client |

### Step 4 — Create required runtime directories

```bash
mkdir -p sonarftdata/history
mkdir -p sonarftdata/bots
mkdir -p sonarftdata/config
```

### Step 5 — Verify installation

```bash
python3 -c "import fastapi, ccxt, pandas_ta; print('Dependencies OK')"
```


---

## 4. Project Structure Reference

```
sonarft/
├── sonarft.py                      # Entry point — starts uvicorn on port 5000
├── sonarft_server.py               # FastAPI app, HTTP endpoints, WebSocket handler
├── sonarft_manager.py              # BotManager — bot lifecycle, client-to-bot registry
├── sonarft_bot.py                  # SonarftBot — config loading, module wiring, run loop
├── sonarft_search.py               # Trade search orchestration, daily loss halt
├── sonarft_prices.py               # VWAP, price adjustment, spread logic
├── sonarft_indicators.py           # RSI, MACD, StochRSI, SMA, volatility
├── sonarft_math.py                 # Fee/profit calculation (Decimal precision)
├── sonarft_execution.py            # Order placement, monitor_price, monitor_order
├── sonarft_validators.py           # Liquidity depth, spread threshold validation
├── sonarft_api_manager.py          # ccxtpro/ccxt abstraction, OHLCV cache
├── sonarft_helpers.py              # Trade dataclass, order/trade history persistence
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── sonarftdata/
    ├── config.json                 # Named configuration sets
    ├── config_parameters.json      # Trading parameters per setup
    ├── config_exchanges.json       # Exchange lists per setup
    ├── config_symbols.json         # Trading pairs per setup
    ├── config_fees.json            # Fee rates per exchange
    ├── config_indicators.json      # Indicator reference (informational)
    ├── config_markets.json         # Market type (crypto, forex)
    ├── config/                     # Per-client runtime config (HTTP-managed)
    │   ├── parameters.json         # Default parameters for frontend
    │   └── indicators.json         # Default indicators for frontend
    └── history/                    # Per-bot trade and order history
        ├── {botid}_orders.json
        └── {botid}_trades.json
```

---

## 5. Configuration Guide

All trading behaviour is controlled by JSON files in `sonarftdata/`. You never need to modify Python source code to change trading parameters.

### 5.1 `config.json` — Named Configuration Sets

This is the master configuration file. Each named set points to the specific setup files to use.

```json
{
    "config_1": [
        {
            "markets_pathname": "sonarftdata/config_markets.json",
            "markets_setup": 1,
            "exchanges_pathname": "sonarftdata/config_exchanges.json",
            "exchanges_setup": 1,
            "symbols_pathname": "sonarftdata/config_symbols.json",
            "symbols_setup": 1,
            "indicators_pathname": "sonarftdata/config_indicators.json",
            "indicators_setup": 1,
            "parameters_pathname": "sonarftdata/config_parameters.json",
            "parameters_setup": 1,
            "fees_pathname": "sonarftdata/config_fees.json",
            "fees_setup": 1
        }
    ]
}
```

To create a new configuration, add a new named entry (e.g. `config_3`) and point each `_setup` number to the corresponding setup in its file. Then launch with `-c config_3`.

**Rule:** The `_setup` number in `config.json` must match a key in the corresponding config file. For example, `"exchanges_setup": 2` requires `"exchanges_2"` to exist in `config_exchanges.json`.

---

### 5.2 `config_parameters.json` — Trading Parameters

Controls the core trading behaviour of each bot instance.

```json
{
    "parameters_1": [
        {
            "profit_percentage_threshold": 0.0001,
            "trade_amount": 1,
            "is_simulating_trade": 1,
            "max_daily_loss": 0.0,
            "spread_increase_factor": 1.00072,
            "spread_decrease_factor": 0.99936
        }
    ]
}
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `profit_percentage_threshold` | float | `0.0001` | Minimum profit ratio (0.01%) required to execute a trade. Must be between 0 and 1. |
| `trade_amount` | float | `1` | Trade size in base currency units (e.g. `1` = 1 BTC for BTC/USDT). Must be > 0. |
| `is_simulating_trade` | int | `1` | `1` = simulation mode (no real orders). `0` = live trading. Must be exactly `0` or `1`. |
| `max_daily_loss` | float | `0.0` | Maximum cumulative loss in quote currency before the bot halts. `0.0` = disabled. |
| `spread_increase_factor` | float | `1.00072` | Multiplier applied to widen the spread in bull/bear conditions. Must be between 1.0 and 1.01. |
| `spread_decrease_factor` | float | `0.99936` | Multiplier applied to narrow the spread. Must be between 0.99 and 1.0. |

**Advisory:** Always start with `is_simulating_trade: 1`. Only set it to `0` after completing a successful paper trading session. See [Section 10](#10-deployment-modes) for the full progression.

**Advisory:** Set `max_daily_loss` to a value you are comfortable losing in a single day before enabling live trading. A value of `0.0` means no limit — the bot will continue trading regardless of losses.

---

### 5.3 `config_exchanges.json` — Exchange List

Defines which exchanges each setup uses.

```json
{
    "exchanges_1": ["okx", "binance"],
    "exchanges_2": ["okx", "bitfinex"],
    "exchanges_3": ["okx", "binance", "bitfinex"]
}
```

Exchange names must match the ccxt exchange ID exactly (lowercase). To find the correct ID for any exchange:

```python
import ccxt
print(ccxt.exchanges)  # lists all supported exchange IDs
```

**Supported exchanges with hardcoded precision fallback:** `okx`, `binance`, `bitfinex`. All other exchanges use live per-symbol precision loaded from the exchange API at startup.

**Advisory:** For cross-exchange arbitrage, configure at least two exchanges. For single-exchange trading, configure one exchange and the bot will evaluate buy/sell combinations within that exchange's order book.

---

### 5.4 `config_symbols.json` — Trading Pairs

Defines which base/quote pairs to trade per setup.

```json
{
    "symbols_1": [
        { "base": "BTC", "quotes": ["USDT"] },
        { "base": "ETH", "quotes": ["USDT"] }
    ],
    "symbols_2": [
        { "base": "ETH", "quotes": ["USDT"] }
    ]
}
```

Each symbol entry has:
- `base` — the asset being bought/sold (e.g. `"BTC"`)
- `quotes` — list of quote currencies to pair with (e.g. `["USDT", "BTC"]`)

The bot processes all symbols concurrently using `asyncio.gather`. Adding more symbols increases API call volume proportionally.

**Advisory:** Start with one or two symbols during initial testing. Add more only after confirming stable operation.

---

### 5.5 `config_fees.json` — Fee Rates

Defines the trading fee rates used in profit calculations.

```json
{
    "exchanges_fees_1": [
        { "exchange": "binance", "buy_fee": 0.001, "sell_fee": 0.001 },
        { "exchange": "okx",     "buy_fee": 0.0008, "sell_fee": 0.001 },
        { "exchange": "bitfinex","buy_fee": 0.001,  "sell_fee": 0.002 }
    ]
}
```

Fee values are expressed as decimals: `0.001` = 0.1%.

**Advisory:** Always use your actual fee tier, not the exchange's published maker/taker rate. If you hold the exchange's native token (e.g. BNB on Binance), your effective fee may be lower. Using a fee rate that is too low will cause the bot to execute trades that are not actually profitable.

**Advisory:** Verify your fee tier in your exchange account settings before configuring. Fee tiers change based on 30-day trading volume.

---

### 5.6 `config_markets.json` — Market Type

```json
{
    "market_1": ["crypto"],
    "market_2": ["forex"]
}
```

Currently informational. The bot operates on spot crypto markets. This field is reserved for future market type routing.


---

## 6. Environment Variables

SonarFT reads the following environment variables at startup. Set them in your shell, in a `.env` file, or via Docker environment injection.

| Variable | Required | Default | Description |
|---|---|---|---|
| `SONARFT_API_TOKEN` | Recommended | None | Bearer token required for all HTTP endpoints and WebSocket connections. If not set, authentication is disabled (development only). |

### Setting the API token

**Linux / macOS (shell):**

```bash
export SONARFT_API_TOKEN="your-secret-token-here"
python3 sonarft.py
```

**`.env` file (project root):**

```
SONARFT_API_TOKEN=your-secret-token-here
```

**Docker Compose:**

```yaml
sonarftbot:
  image: sonarftbot:latest
  environment:
    - SONARFT_API_TOKEN=your-secret-token-here
```

**Advisory:** Never commit your API token to source control. Use a randomly generated string of at least 32 characters. Generate one with:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Advisory:** If `SONARFT_API_TOKEN` is not set, any client can connect to the WebSocket and call any HTTP endpoint. This is acceptable for local development only. Always set the token before exposing the server on any network.

---

## 7. Running the Bot

### 7.1 Direct Python Execution

Always run from the project root directory so that relative paths to `sonarftdata/` resolve correctly.

```bash
cd ~/Development/sonarft
python3 sonarft.py
```

The server starts on `http://127.0.0.1:5000`. You should see:

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:5000
```

### 7.2 Docker Deployment

**Build the image:**

```bash
docker build -t sonarftbot:latest .
```

**Run with Docker Compose (includes Traefik TLS reverse proxy):**

```bash
docker-compose up
```

Before running with Docker Compose, set the required environment variables:

```bash
export SONARFT_API_TOKEN="your-secret-token-here"
export ACME_EMAIL="your-email@example.com"
export TRAEFIK_DASHBOARD_USERS="admin:$$apr1$$..."  # htpasswd format
docker-compose up
```

Generate a Traefik BasicAuth password hash:

```bash
htpasswd -nb admin yourpassword
# Output: admin:$apr1$...
# In docker-compose env vars, escape $ as $$
```

**Create the ACME certificate file before first run:**

```bash
touch acme.json
chmod 600 acme.json
```

**Run a single container without Traefik (local testing):**

```bash
docker run -p 5000:5000 \
  -e SONARFT_API_TOKEN="your-token" \
  -v $(pwd)/sonarftdata/history:/app/sonarftdata/history \
  -v $(pwd)/sonarftdata/bots:/app/sonarftdata/bots \
  sonarftbot:latest
```

### 7.3 Command-Line Flags

| Flag | Short | Default | Description |
|---|---|---|---|
| `--config` | `-c` | `config_1` | Named configuration set from `config.json` |
| `--library` | `-l` | `ccxtpro` | API library: `ccxtpro` (WebSocket) or `ccxt` (REST) |

**Examples:**

```bash
# Use config_2 with WebSocket API (default)
python3 sonarft.py -c config_2

# Use config_1 with REST API fallback
python3 sonarft.py -c config_1 -l ccxt

# Compiled binary (Linux)
./dist/sonarft/sonarft -c config_2 -l ccxt
```

**When to use `ccxt` (REST) vs `ccxtpro` (WebSocket):**

| Mode | Latency | Availability | Use When |
|---|---|---|---|
| `ccxtpro` (default) | Low (~50ms) | Most major exchanges | Normal operation |
| `ccxt` | Higher (~200ms+) | All ccxt-supported exchanges | Exchange doesn't support WebSocket, or debugging |

**Advisory:** The REST (`ccxt`) mode runs synchronous calls in a thread executor to avoid blocking the event loop. It is safe to use but will have higher latency. Do not use it for latency-sensitive strategies.


---

## 8. REST API Reference

All endpoints require a `Bearer` token in the `Authorization` header when `SONARFT_API_TOKEN` is set.

```
Authorization: Bearer your-secret-token-here
```

### Base URL

```
http://127.0.0.1:5000
```

---

### `GET /botids/{client_id}`

Returns all bot IDs associated with a client.

**Response:**
```json
{ "botids": [12345, 67890] }
```

---

### `GET /default_parameters`

Returns the default parameters JSON from `sonarftdata/config/parameters.json`. Used by the frontend to populate default UI values.

---

### `GET /default_indicators`

Returns the default indicators JSON from `sonarftdata/config/indicators.json`.

---

### `GET /bot/get_parameters/{client_id}`

Returns the current runtime parameters for a client.

**Response:**
```json
{
    "profit_percentage_threshold": 0.0001,
    "trade_amount": 1,
    "is_simulating_trade": 1
}
```

---

### `POST /bot/set_parameters/{client_id}`

Updates runtime parameters for a client. Writes to `sonarftdata/config/{client_id}_parameters.json`.

**Request body:**
```json
{
    "profit_percentage_threshold": 0.0002,
    "trade_amount": 0.5,
    "is_simulating_trade": 1
}
```

**Note:** These parameters are stored per-client but are not automatically applied to running bots. The bot reads parameters at startup from `config_parameters.json`. The HTTP endpoints are used by the frontend for display and future dynamic updates.

---

### `GET /bot/get_indicators/{client_id}`

Returns the current indicator settings for a client.

---

### `POST /bot/set_indicators/{client_id}`

Updates indicator settings for a client. Writes to `sonarftdata/config/{client_id}_indicators.json`.

---

### `GET /bot/{botid}/orders`

Returns the order history for a bot from `sonarftdata/history/{botid}_orders.json`.

**Response:** JSON array of order records.

---

### `GET /bot/{botid}/trades`

Returns the trade history for a bot from `sonarftdata/history/{botid}_trades.json`.

**Response:** JSON array of trade records.

---

### Error Responses

| Status | Meaning |
|---|---|
| `400` | Invalid `client_id` or `botid` format (path traversal attempt or non-alphanumeric characters) |
| `401` | Missing or invalid Bearer token |
| `404` | History or config file not found for the given ID |
| `500` | Unexpected server error |

---

## 9. WebSocket Protocol

Connect to:

```
ws://127.0.0.1:5000/ws/{client_id}?token=your-secret-token-here
```

- `client_id` must be alphanumeric (letters, digits, `-`, `_`), max 64 characters
- `token` query parameter is required when `SONARFT_API_TOKEN` is set
- The connection is rejected with close code `1008` if the token is invalid

### Sending Commands

All commands are JSON objects sent as text frames.

**Create a bot:**
```json
{ "type": "action", "key": "create" }
```

The server responds by streaming log messages. The bot ID is included in the log output.

**Run a bot:**
```json
{ "type": "action", "key": "run", "botid": 12345 }
```

**Remove a bot:**
```json
{ "type": "action", "key": "remove", "botid": 12345 }
```

### Receiving Logs

After connecting, the server streams log messages as plain text frames:

```
INFO - client_abc - Bot 12345 start running
INFO - client_abc - (v1009) - Bot 12345: NEW TRADE SEARCHING...
INFO - client_abc - BOT: 12345 | BUY: okx -> SELL: binance
INFO - client_abc - RSI buy=45.23 sell=48.11 | strength=46.67
INFO - client_abc - BTC/USDT: Profit 0.00234 - Percentage: 0.00012
```

### Typical Session Flow

```
1. Connect WebSocket with client_id and token
2. Send { "key": "create" }          → bot is created, botid logged
3. Send { "key": "run", "botid": X } → bot starts trading cycle
4. Monitor log stream for trade activity
5. Send { "key": "remove", "botid": X } → bot stops cleanly
6. Disconnect WebSocket
```

**Advisory:** Each WebSocket connection is associated with one `client_id`. Multiple bots can be created and run under the same `client_id`. Log messages from all bots under a client are streamed to that client's connection.

**Advisory:** If the WebSocket connection drops, running bots continue operating. Reconnect with the same `client_id` to resume log streaming. Use `GET /botids/{client_id}` to retrieve the IDs of bots still running.


---

## 10. Deployment Modes

SonarFT has four deployment modes. Always progress through them in order. Never skip directly to live trading.

---

### 10.1 Simulation Mode

**What it does:** Runs the full trade search and decision pipeline against live market data, but generates synthetic order IDs instead of placing real orders. No capital is at risk.

**Configuration:**
```json
"is_simulating_trade": 1
```

**Behaviour:**
- All indicator fetches, price adjustments, and profit calculations run normally
- `monitor_price` is skipped — the target price is used directly
- Order IDs are generated as `buy_123456` / `sell_123456`
- Balance checks always return `True`
- Trade and order history are written to disk

**Use this mode to:**
- Verify the bot starts and runs without errors
- Confirm your exchange and symbol configuration is correct
- Observe the trade decision logic in the logs
- Validate that `max_daily_loss` halts the bot correctly (set a low value and watch)

**Exit criteria before moving to paper trading:**
- Bot completes at least 100 full trade cycles without crashing
- Log output shows sensible RSI, direction, and profit values
- Order history files are being written correctly

---

### 10.2 Paper Trading Mode

Paper trading is simulation mode running continuously and unattended, typically for 24–72 hours, against live market data.

**Configuration:** Same as simulation mode (`is_simulating_trade: 1`), but run for an extended period.

**What to verify:**
- No memory leaks (monitor process RSS over time — should stay below 200MB per bot)
- No crashes or unhandled exceptions in logs
- Circuit breaker activates correctly if you simulate an exchange outage
- `max_daily_loss` halts the bot at the configured threshold
- Trade history files grow at a reasonable rate

**Monitoring command:**
```bash
# Watch memory usage of the bot process
watch -n 30 "ps aux | grep sonarft.py | grep -v grep"
```

**Exit criteria before moving to limited live trading:**
- 24-hour run with zero crashes
- Memory growth < 50MB per hour per bot
- At least one `max_daily_loss` halt test passed in simulation

---

### 10.3 Live Trading Mode

**Configuration:**
```json
"is_simulating_trade": 0,
"max_daily_loss": 50.0,
"trade_amount": 0.001
```

**Pre-flight checklist before enabling:**

- [ ] API keys configured for all exchanges (see [Section 11](#11-exchange-api-keys-setup))
- [ ] `SONARFT_API_TOKEN` set in environment
- [ ] `max_daily_loss` set to a value you accept losing in one day
- [ ] `trade_amount` set to the minimum viable amount for your exchange
- [ ] Fee rates in `config_fees.json` match your actual account tier
- [ ] Paper trading session completed successfully
- [ ] Exchange API keys have **spot trading only** — no withdrawal permissions
- [ ] Tested `stop_bot` (remove action) and confirmed clean exit

**Start with the smallest possible trade amount.** For BTC/USDT on Binance, the minimum is approximately 0.00001 BTC. Confirm the minimum order size for your exchange before setting `trade_amount`.

**Advisory:** The first live trade cycle should be monitored in real time. Watch the log stream via WebSocket and verify that orders appear in your exchange account.

---

## 11. Exchange API Keys Setup

API keys are set programmatically via the `SonarftBot.setAPIKeys` method. This is called after bot creation, before running.

### Setting API keys in code

In your client application or startup script:

```python
# After creating the bot via WebSocket, call setAPIKeys on the bot instance
# This is typically done through a custom endpoint or startup hook

bot.setAPIKeys(
    exchange="binance",
    api_key="your-api-key",
    secret_key="your-secret-key",
    password=""  # only required for OKX and some other exchanges
)
```

### OKX requires a passphrase

```python
bot.setAPIKeys(
    exchange="okx",
    api_key="your-api-key",
    secret_key="your-secret-key",
    password="your-passphrase"  # required for OKX
)
```

### Exchange API key permissions

Configure your API keys with the minimum required permissions:

| Permission | Required | Notes |
|---|---|---|
| Read (view balances, orders) | Yes | Always required |
| Spot trading | Yes | Required for live trading |
| Futures trading | No | Not used by SonarFT |
| Withdrawals | **Never** | Never grant this permission |
| IP whitelist | Strongly recommended | Restrict to your server's IP |

### Storing API keys securely

**Do not** store API keys in any JSON config file or source code. Use environment variables:

```bash
export BINANCE_API_KEY="your-key"
export BINANCE_SECRET="your-secret"
export OKX_API_KEY="your-key"
export OKX_SECRET="your-secret"
export OKX_PASSWORD="your-passphrase"
```

Then read them in your startup code:

```python
import os
bot.setAPIKeys("binance", os.environ["BINANCE_API_KEY"], os.environ["BINANCE_SECRET"], "")
bot.setAPIKeys("okx", os.environ["OKX_API_KEY"], os.environ["OKX_SECRET"], os.environ["OKX_PASSWORD"])
```

**Advisory:** Rotate API keys immediately if you suspect they have been exposed. Most exchanges allow you to create multiple API key pairs — use a dedicated pair for SonarFT.


---

## 12. Multi-Bot Operation

SonarFT supports running multiple independent bot instances on the same server. Each bot has its own state, configuration, and trade history.

### Running multiple bots

Each bot is created via a separate `create` WebSocket command. They can use different configurations:

```
Client A → create (uses config_1: BTC/USDT on okx+binance)
Client A → run botid=11111

Client B → create (uses config_2: ETH/USDT on okx+bitfinex)
Client B → run botid=22222
```

Both bots run concurrently. Their trade cycles are independent and do not share state.

### Resource considerations per bot

| Resource | Per Bot (approximate) |
|---|---|
| Memory | 50–150MB depending on symbol count |
| API calls per cycle | ~15 per symbol (after caching) |
| Cycle duration | 6–18 seconds (configurable sleep) |
| History file growth | ~1KB per trade |

### Recommended limits

| Scenario | Max Bots | Notes |
|---|---|---|
| Development / testing | 2–3 | No practical limit |
| Paper trading | 5–10 | Monitor memory |
| Live trading | 2–5 | Depends on exchange rate limits |

**Advisory:** Each bot makes independent API calls to the same exchanges. Running 5 bots on the same exchange pair multiplies the API call rate by 5. Monitor your exchange rate limit usage and add delays if you receive `429 Too Many Requests` errors.

**Advisory:** The OHLCV cache is per-bot, not shared across bots. If multiple bots trade the same symbol on the same exchange, they each maintain their own cache. A shared cache layer would reduce API calls further — this is a future improvement.

---

## 13. Monitoring and Logs

### Real-time log streaming

Connect via WebSocket to receive live logs:

```javascript
const ws = new WebSocket('ws://127.0.0.1:5000/ws/my-client?token=your-token');
ws.onmessage = (event) => console.log(event.data);
```

### Log format

```
{LEVEL} - {client_id} - {message}
```

Example output during a trade cycle:

```
INFO - client_abc - (v1009) - Bot 12345: NEW TRADE SEARCHING...
INFO - client_abc - BOT: 12345 | BUY: okx -> SELL: binance
INFO - client_abc - RSI buy=62.14 sell=58.33 | strength=60.24
INFO - client_abc - Direction buy=bull sell=bull | trend buy=bull sell=neutral
INFO - client_abc - StochRSI buy_k=71.22 sell_k=65.44
INFO - client_abc - Support=29800.0 resistance=31200.0
INFO - client_abc - BTC/USDT: Trade Amount 0.001
INFO - client_abc - BTC/USDT: Profit 0.00312 - Percentage: 0.00014
INFO - client_abc - (v1009) - Bot 12345: A NEW TRADE HAS BEEN FOUND!
INFO - client_abc - Creating buy order on okx for 0.001 BTC at 30100.0 USDT...
INFO - client_abc - Creating sell order on binance for 0.001 BTC at 30104.5 USDT...
INFO - client_abc - Next trade for bot 12345 in 11 secs...
```

### Key log signals to watch

| Log Message | Meaning | Action |
|---|---|---|
| `StochRSI unavailable` | Indicator fetch failed | Check exchange connectivity |
| `RSI unavailable` | RSI fetch failed | Check exchange connectivity |
| `Daily loss limit reached` | `max_daily_loss` triggered | Bot halted — review trades |
| `circuit breaker tripped` | 5 consecutive search failures | Bot stopped — check exchange status |
| `monitor_price timed out` | Price never reached target in 120s | Normal in low-volatility markets |
| `monitor_order timed out` | Order not filled in 300s | Check exchange order book |
| `One or both order results are None` | Order placement failed | Check balance and API keys |
| `Exchange not in EXCHANGE_RULES` | Unknown exchange precision | Add exchange to `EXCHANGE_RULES` or ensure markets are loaded |

### Persistent logging to file

To capture logs to a file while also streaming to WebSocket:

```bash
python3 sonarft.py 2>&1 | tee sonarft.log
```

Or with log rotation:

```bash
python3 sonarft.py 2>&1 | rotatelogs sonarft.log 86400
```

---

## 14. Trade and Order History

### File locations

```
sonarftdata/history/
├── {botid}_orders.json    # One entry per trade attempt
└── {botid}_trades.json    # One entry per successfully completed trade
```

### Order history record

Written when a trade position is determined (after order placement):

```json
{
    "timestamp": "07-15-2025 14:23:11",
    "position": "LONG",
    "base": "BTC",
    "quote": "USDT",
    "buy_exchange": "okx",
    "sell_exchange": "binance",
    "buy_price": 30100.0,
    "sell_price": 30104.5,
    "buy_trade_amount": 0.001,
    "sell_trade_amount": 0.001,
    "executed_amount": 0.001,
    "buy_value": 30.1,
    "sell_value": 30.1045,
    "buy_fee_rate": 0.0008,
    "sell_fee_rate": 0.001,
    "buy_fee_quote": 0.00002408,
    "sell_fee_quote": 0.0000301045,
    "profit": 0.00312,
    "profit_percentage": 0.00014
}
```

### Trade history record

Written only when both buy and sell orders complete successfully:

```json
{
    "timestamp": "07-15-2025 14:23:15",
    "position": "LONG",
    "buy_order_id": "okx-order-123456",
    "sell_order_id": "binance-order-789012",
    "base": "BTC",
    "quote": "USDT",
    "buy_exchange": "okx",
    "sell_exchange": "binance",
    "profit": 0.00312,
    "profit_percentage": 0.00014,
    "order_buy_success": true,
    "order_sell_success": true,
    "trade_success": true
}
```

### Retrieving history via API

```bash
# Get order history
curl -H "Authorization: Bearer your-token" \
     http://127.0.0.1:5000/bot/12345/orders

# Get trade history
curl -H "Authorization: Bearer your-token" \
     http://127.0.0.1:5000/bot/12345/trades
```

### History file management

History files grow indefinitely. Implement a rotation strategy for long-running deployments:

```bash
# Archive history older than 30 days
find sonarftdata/history/ -name "*.json" -mtime +30 -exec gzip {} \;
```

**Advisory:** Back up history files before restarting or upgrading. In Docker deployments, history is stored in named volumes (`sonarft_history`) and persists across container restarts.


---

## 15. Safety Controls

SonarFT includes several built-in safety mechanisms. Understanding them is essential before enabling live trading.

### 15.1 Simulation Mode Gate

`is_simulating_trade: 1` is the primary safety gate. When enabled:
- No real orders are placed on any exchange
- Balance checks always pass
- `monitor_price` is skipped (uses target price directly)
- Synthetic order IDs are generated

This flag is checked in `SonarftExecution.execute_order` and `SonarftExecution.check_balance`. It cannot be bypassed by configuration — it must be explicitly set to `0` to enable real trading.

### 15.2 Maximum Daily Loss Halt

`max_daily_loss` accumulates losses across all trades in a bot's lifetime (not reset daily — the name is conventional). When the accumulated loss reaches the threshold, `search_trades` returns immediately without processing any symbols.

```json
"max_daily_loss": 50.0
```

This means: halt the bot after losing 50 USDT (or whatever the quote currency is) in total.

**To reset the halt:** stop the bot (`remove` action) and create a new one. The accumulated loss counter resets on bot creation.

**Advisory:** Set `max_daily_loss` before your first live trade. A value of `0.0` disables the halt entirely.

### 15.3 Circuit Breaker

The circuit breaker in `run_bot` counts consecutive `search_trades` failures. After 5 consecutive failures, the bot stops itself and logs a critical error.

Backoff schedule:
- Failure 1: wait 30s
- Failure 2: wait 60s
- Failure 3: wait 90s
- Failure 4: wait 120s
- Failure 5: stop bot

A successful trade cycle resets the counter to zero.

**Advisory:** The circuit breaker protects against exchange outages and network failures. If it trips, check exchange status pages and your network connectivity before restarting.

### 15.4 Monitor Timeouts

- `monitor_price`: 120 seconds — if the live price never reaches the target, the order is skipped
- `monitor_order`: 300 seconds — if the order is not filled or cancelled, it is treated as failed

These timeouts prevent capital from being locked indefinitely in pending orders.

### 15.5 Partial Fill Protection

If a buy order is only partially filled, the sell leg is placed for the actually filled amount — not the original trade amount. This prevents selling more than was bought.

### 15.6 Input Validation

All `client_id` and `botid` values in HTTP and WebSocket endpoints are validated against the pattern `^[a-zA-Z0-9_-]{1,64}$`. Any value containing path separators, dots, or special characters is rejected with HTTP 400.

---

## 16. Troubleshooting

### Bot does not start

**Symptom:** `FileNotFoundError` on startup.

**Cause:** Bot launched from wrong directory, or `sonarftdata/` subdirectories do not exist.

**Fix:**
```bash
cd ~/Development/sonarft  # must be project root
mkdir -p sonarftdata/history sonarftdata/bots sonarftdata/config
python3 sonarft.py
```

---

### `ValueError` on bot creation

**Symptom:** Log shows `ValueError: profit_percentage_threshold must be between 0 and 1`.

**Cause:** A parameter in `config_parameters.json` is out of the valid range.

**Fix:** Review all parameters against the table in [Section 5.2](#52-config_parametersjson--trading-parameters). Common mistakes:
- `profit_percentage_threshold: 0.1` (10% — too high, should be `0.001` for 0.1%)
- `trade_amount: 0` (zero is invalid)
- `is_simulating_trade: 2` (must be exactly `0` or `1`)

---

### `KeyError` on exchange name

**Symptom:** Log shows `Exchange not in EXCHANGE_RULES`.

**Cause:** The exchange name in `config_exchanges.json` does not match the ccxt exchange ID.

**Fix:** Verify the exact ccxt ID:
```python
import ccxt
# Find your exchange
[e for e in ccxt.exchanges if 'kucoin' in e]  # example
```

---

### `StochRSI unavailable` / `RSI unavailable` in every cycle

**Symptom:** Every trade cycle logs indicator unavailability warnings.

**Cause:** Exchange API is unreachable, or the symbol is not available on the exchange.

**Fix:**
1. Verify the exchange is accessible: `ping api.binance.com`
2. Verify the symbol exists on the exchange:
```python
import ccxt
exchange = ccxt.binance()
exchange.load_markets()
print('BTC/USDT' in exchange.markets)
```
3. Check if the exchange requires API keys even for public market data (some do)

---

### Orders not appearing on exchange

**Symptom:** Simulation mode works, but live mode shows no orders on the exchange.

**Cause:** API keys not set, wrong permissions, or IP not whitelisted.

**Fix:**
1. Confirm `is_simulating_trade: 0` in config
2. Verify `setAPIKeys` is called before `run_bot`
3. Check exchange API key permissions include spot trading
4. Check IP whitelist settings on the exchange

---

### `monitor_price timed out` on every trade

**Symptom:** Every trade attempt logs a timeout from `monitor_price`.

**Cause:** The adjusted price target is too far from the current market price, so the condition `price_to_check >= price` (for buy) is never met within 120 seconds.

**Fix:** This is normal behaviour in low-volatility or trending markets. The bot skips the trade and tries again on the next cycle. If it happens consistently, consider:
- Reducing `profit_percentage_threshold` slightly
- Reviewing the spread factors in `config_parameters.json`

---

### High memory usage

**Symptom:** Bot process memory grows beyond 200MB per hour.

**Cause:** Likely unbounded log queue or history file growth.

**Fix:**
1. Verify `asyncio.Queue(maxsize=1000)` is in place in `AsyncHandler` (it is, post-audit)
2. Implement history file rotation (see [Section 14](#14-trade-and-order-history))
3. Reduce the number of symbols per bot

---

### WebSocket connection rejected with code 1008

**Symptom:** Client cannot connect to `/ws/{client_id}`.

**Cause:** `SONARFT_API_TOKEN` is set but the `token` query parameter is missing or incorrect.

**Fix:** Include the token in the WebSocket URL:
```
ws://127.0.0.1:5000/ws/my-client?token=your-secret-token
```

---

### HTTP 401 on all endpoints

**Symptom:** All API calls return `{"detail": "Unauthorized"}`.

**Cause:** `SONARFT_API_TOKEN` is set but the `Authorization` header is missing or incorrect.

**Fix:**
```bash
curl -H "Authorization: Bearer your-secret-token" \
     http://127.0.0.1:5000/botids/my-client
```

---

## 17. Operational Advisories

These advisories summarise the most important operational guidance from across this document.

### Before any deployment

1. **Always start in simulation mode.** Set `is_simulating_trade: 1` and run for at least 100 cycles before considering paper trading.

2. **Set `max_daily_loss` before live trading.** A value of `0.0` means no limit. Choose a value you are comfortable losing.

3. **Set `SONARFT_API_TOKEN`.** Any server exposed on a network without this token is open to anyone.

4. **Use accurate fee rates.** Incorrect fees cause the bot to execute trades that are not actually profitable. Verify your fee tier on each exchange.

5. **Use the minimum viable `trade_amount`.** Start with the exchange's minimum order size. Scale up only after confirming the strategy is profitable.

### During operation

6. **Monitor the circuit breaker.** If it trips, do not immediately restart. Investigate the cause — it usually indicates an exchange outage or network issue.

7. **Watch for `monitor_price timed out` frequency.** Occasional timeouts are normal. Frequent timeouts suggest the price targets are unrealistic for current market conditions.

8. **Do not run multiple bots on the same symbol/exchange pair with live trading** unless you have verified that the combined order volume does not exceed your exchange's rate limits.

9. **Back up history files regularly.** They are the only record of what the bot has done. In Docker, ensure the named volumes are backed up.

10. **Never grant withdrawal permissions to API keys.** SonarFT only needs read and spot trading permissions.

### Configuration changes

11. **Restart the bot after changing any config file.** Configuration is loaded once at bot creation. Changes to JSON files do not take effect until the bot is removed and recreated.

12. **Test configuration changes in simulation mode first.** A misconfigured `profit_percentage_threshold` or `trade_amount` can cause unexpected behaviour.

13. **Keep `config_1` and `config_2` distinct.** Currently both point to the same setups. Create genuinely different configurations to take advantage of the multi-config system.

### Exchange-specific

14. **OKX requires a passphrase** in addition to API key and secret. Pass it as the `password` argument to `setAPIKeys`.

15. **Binance has per-symbol minimum order sizes** (`LOT_SIZE` filter). If orders are rejected, check that `trade_amount` meets the minimum for your symbol. The per-symbol precision loaded from the exchange API at startup handles tick sizes, but minimum notional value must be checked manually.

16. **Bitfinex uses a different fee structure** for maker vs taker orders. The fee rates in `config_fees.json` should reflect your actual taker fee for market orders.


---

## 18. Known Limitations

These are confirmed limitations of the current implementation. They are documented here so operators can plan around them.

### Trading strategy

| Limitation | Impact | Workaround |
|---|---|---|
| Support/resistance uses simple min/max over a 3-hour window | Levels may not reflect meaningful price clusters | Use `spread_increase_factor` / `spread_decrease_factor` to compensate |
| Mixed bull/bear signal branches (bull direction + bear trend) produce neutral spread behaviour | Missed opportunities in diverging markets | Planned for Phase 5 enhancement |
| `profit_percentage` field is a ratio, not a percentage | Misleading field name — `0.0001` means 0.01%, not 0.01 | Treat all profit values as ratios in downstream analysis |
| Spread factors are applied symmetrically to buy and sell | May not be optimal for all market conditions | Tune `spread_increase_factor` and `spread_decrease_factor` per market |

### Exchange integration

| Limitation | Impact | Workaround |
|---|---|---|
| `EXCHANGE_RULES` hardcodes precision for `okx`, `binance`, `bitfinex` only | Other exchanges use live precision from API; if markets not loaded, trade is skipped | Ensure `load_all_markets` completes at startup; add exchange to `EXCHANGE_RULES` as fallback |
| No futures or margin trading support | Spot only | Not applicable for current use case |
| `monitor_order` does not handle partial fills during order monitoring | A partially filled order that stays open will time out after 300s | Partial fill at execution time is handled; partial fill during monitoring is not |

### Infrastructure

| Limitation | Impact | Workaround |
|---|---|---|
| OHLCV cache is per-bot, not shared | Multiple bots on the same symbol make redundant API calls | Run fewer bots, or implement a shared cache layer |
| History files are append-only JSON, no rotation | Files grow unbounded | Implement manual rotation (see Section 14) |
| No built-in alerting or notification system | Operator must monitor logs manually | Pipe logs to an external alerting system |
| `config_indicators.json` is not loaded at bot startup | Indicator parameters are hardcoded in `sonarft_prices.py` | Modify source defaults or use HTTP endpoints for per-client overrides |
| Bot ID uses `random.randint(10001, 99999)` | ~89,000 possible IDs; collision possible with many bots | Acceptable for current scale; replace with `uuid4()` for large deployments |

---

## 19. Upgrade and Maintenance

### Updating dependencies

```bash
# Check for outdated packages
pip list --outdated

# Update a specific package (test in simulation mode first)
pip install --upgrade ccxt

# Freeze current versions after testing
pip freeze > requirements.txt
```

**Advisory:** `ccxt` updates frequently. New versions may change exchange API behaviour. Always test in simulation mode after updating `ccxt`.

### Updating SonarFT source

```bash
# Pull latest changes
git pull origin main

# Reinstall dependencies if requirements.txt changed
pip install -r requirements.txt

# Restart all bots (configuration is loaded at bot creation)
```

### Rebuilding the Docker image

```bash
docker build --no-cache -t sonarftbot:latest .
docker-compose down
docker-compose up
```

The `--no-cache` flag ensures all layers are rebuilt with the latest source.

### Adding a new exchange

1. Add the exchange ID to `config_exchanges.json` under a new or existing setup
2. Add the fee rates to `config_fees.json`
3. Optionally add precision rules to `EXCHANGE_RULES` in `sonarft_math.py` as a fallback (live precision is loaded automatically from the exchange API)
4. Test in simulation mode with the new exchange

### Adding a new trading pair

1. Add the symbol to `config_symbols.json` under a new or existing setup
2. Verify the symbol exists on all configured exchanges
3. Test in simulation mode

### Rotating the API token

```bash
# Generate a new token
python3 -c "import secrets; print(secrets.token_hex(32))"

# Update the environment variable
export SONARFT_API_TOKEN="new-token-here"

# Restart the server
# Update all clients to use the new token
```

### Backing up runtime data

```bash
# Backup all history and bot registry files
tar -czf sonarft-backup-$(date +%Y%m%d).tar.gz \
    sonarftdata/history/ \
    sonarftdata/bots/ \
    sonarftdata/config/
```

### Health check

Verify the server is running and authenticated:

```bash
curl -s -o /dev/null -w "%{http_code}" \
     -H "Authorization: Bearer your-token" \
     http://127.0.0.1:5000/default_parameters
# Expected: 200
```

---

*End of SonarFT Operator Guide*
