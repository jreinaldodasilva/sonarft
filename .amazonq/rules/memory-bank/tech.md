# SonarFT - Technology Stack

## Language & Runtime
- Python 3.10.6 (pinned in Dockerfile)
- C++ (models/ga.cpp, models/mp.cpp) — genetic algorithm and optimization models
- Java (models/generator.java) — test case generator model

## Core Python Dependencies (requirements.txt)
| Package | Version | Purpose |
|---|---|---|
| fastapi | 0.100.0 | HTTP REST API and WebSocket server |
| uvicorn | 0.22.0 | ASGI server to run FastAPI |
| python-dotenv | 1.0.0 | `.env` file loading |
| python-decouple | 3.8 | Environment variable management |
| pandas | 1.5.3 | Time-series data manipulation for indicators |
| pandas-ta | 0.3.14b0 | Technical analysis indicators (RSI, MACD, StochRSI, SMA, etc.) |
| simple-websocket | 0.10.1 | WebSocket client for exchange connections |
| ccxt | 3.0.24 | REST-based multi-exchange trading library (fallback API) |

## Async Framework
- `asyncio` — all bot operations, trade search, API calls, and WebSocket handling are async
- `asyncio.gather` — concurrent symbol processing per bot cycle
- `asyncio.Lock` — thread-safe bot registry in BotManager
- `asyncio.Queue` — async log streaming to WebSocket clients

## Decimal Precision
- `decimal.getcontext().prec = 8` — set globally in sonarft_bot.py, sonarft_search.py, sonarft_prices.py for financial precision

## API Modes
- Default: WebSocket (ccxtpro) — faster, lower latency
- Fallback: REST (ccxt) — broader exchange compatibility, selected with `-l ccxt` flag

## Infrastructure
- Docker: `python:3.10.6` base image, exposes port 5000
- Docker Compose: Traefik v2.5 reverse proxy with ACME TLS, routes `sonarft.com` → bot on port 5000
- Traefik dashboard: `monitor.sonarft.com` on port 8080

## Configuration Format
- All config: JSON files under `sonarftdata/`
- Per-client runtime config stored as `{client_id}_parameters.json` and `{client_id}_indicators.json`
- Trade history stored as `{botid}_orders.json` and `{botid}_trades.json` under `sonarftdata/history/`
- Bot registry stored as `{botid}.json` under `sonarftdata/bots/`

## Development Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run server directly
python sonarft.py

# Run with custom config and library
python sonarft.py -c config_2 -l ccxt

# Build Docker image
docker build -t sonarftbot:latest .

# Run with Docker Compose
docker-compose up

# Run compiled binary (Linux)
./dist/sonarft/sonarft -c config_1
```

## Key Default Parameters (config_parameters.json)
- `profit_percentage_threshold`: 0.0001 (0.01% minimum profit)
- `trade_amount`: 1 (base currency units)
- `is_simulating_trade`: 1 (simulation mode on by default)
