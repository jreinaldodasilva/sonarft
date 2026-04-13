# SonarFT - Project Structure

## Directory Layout
```
sonarft/
├── sonarft.py                  # Entry point: starts uvicorn/FastAPI server
├── sonarft_server.py           # HTTP + WebSocket server, client communication layer
├── sonarft_manager.py          # BotManager: lifecycle management for multiple bots
├── sonarft_bot.py              # SonarftBot: bot init, config loading, module wiring
├── sonarft_search.py           # Trade search: SonarftSearch, TradeProcessor, TradeValidator, TradeExecutor
├── sonarft_prices.py           # Price calculation: VWAP, weighted adjustment, spread logic
├── sonarft_indicators.py       # Technical indicators: RSI, MACD, StochRSI, SMA, volatility, order book
├── sonarft_math.py             # Trade profit/fee calculations
├── sonarft_execution.py        # Order execution (real and simulated)
├── sonarft_validators.py       # Liquidity and spread threshold validation
├── sonarft_api_manager.py      # Exchange API abstraction (WebSocket/ccxt)
├── sonarft_helpers.py          # Utility/helper functions
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container image definition
├── docker-compose.yml          # Traefik + bot service orchestration
├── sonarftdata/
│   ├── config.json             # Named config sets (config_1, config_2, ...)
│   ├── config_parameters.json  # Trading parameters per setup
│   ├── config_exchanges.json   # Exchange list per setup
│   ├── config_symbols.json     # Trading pairs per setup
│   ├── config_fees.json        # Fee structures per exchange
│   ├── config_indicators.json  # Indicator settings per setup
│   ├── config_markets.json     # Market type (crypto, etc.)
│   └── config/                 # Per-client runtime config (parameters, indicators)
└── models/
    ├── ga.cpp                  # Genetic algorithm model (C++)
    ├── mp.cpp                  # Additional C++ model
    └── generator.java          # Java model/generator
```

## Class Responsibilities

| Class | File | Role |
|---|---|---|
| SonarftServer | sonarft_server.py | FastAPI app, HTTP endpoints, WebSocket handler, per-client logging |
| BotManager | sonarft_manager.py | Create/run/remove bot instances, client-to-bot mapping, async lock |
| SonarftBot | sonarft_bot.py | Config loading, module initialization, main run loop |
| SonarftSearch | sonarft_search.py | Orchestrates trade search across symbols concurrently |
| TradeProcessor | sonarft_search.py | Per-symbol price fetching, adjustment, profit check, execution trigger |
| TradeValidator | sonarft_search.py | Liquidity and spread validation before execution |
| TradeExecutor | sonarft_search.py | Async task management for trade execution |
| SonarftPrices | sonarft_prices.py | VWAP, weighted price adjustment, dynamic volatility, support/resistance |
| SonarftIndicators | sonarft_indicators.py | RSI, MACD, StochRSI, SMA, market direction/trend/movement |
| SonarftMath | sonarft_math.py | Profit/fee calculation, trade data packaging |
| SonarftExecution | sonarft_execution.py | Buy/sell order placement (real or simulated) |
| SonarftValidators | sonarft_validators.py | Order book liquidity depth checks, spread threshold |
| SonarftApiManager | sonarft_api_manager.py | Exchange API calls (WebSocket default, ccxt fallback) |
| SonarftHelpers | sonarft_helpers.py | Formatting, file I/O, misc utilities |

## Architectural Patterns

- Modular OOP: each responsibility is a dedicated class in its own file
- Dependency injection: modules receive api_manager, logger, and peer modules via constructor
- Async-first: all I/O-bound operations use `async/await`; concurrent symbol processing via `asyncio.gather`
- Layered architecture:
  - Transport layer: SonarftServer (FastAPI/WebSocket)
  - Orchestration layer: BotManager → SonarftBot
  - Strategy layer: SonarftSearch → TradeProcessor → TradeValidator/TradeExecutor
  - Analysis layer: SonarftPrices + SonarftIndicators + SonarftMath
  - Infrastructure layer: SonarftApiManager + SonarftValidators + SonarftHelpers + SonarftExecution
- Configuration-driven: all trading parameters, exchanges, symbols, and fees are JSON-file driven
- Multi-tenancy: multiple bots per server, each isolated by botid and client_id
- Simulation mode: `is_simulating_trade` flag gates real order execution throughout the stack
