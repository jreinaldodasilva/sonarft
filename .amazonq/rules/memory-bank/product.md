# SonarFT - Product Overview

## Purpose
SonarFT (System Oscillator for Navigation and Ranging in Financial Trade) is an automated cryptocurrency trading bot that monitors market oscillations and trends to identify and execute profitable trading opportunities across single or multiple exchanges.

## Key Features
- Multi-exchange and cross-exchange trading support
- Real-time market analysis using technical indicators (RSI, MACD, Stochastic, VWAP)
- Dual API support: WebSocket (default, faster) and REST via ccxt library
- Multi-bot concurrency: multiple independent bot instances per server
- Configurable trading strategies via JSON config files
- Simulation/paper trading mode (`is_simulating_trade`)
- WebSocket-based real-time communication between server and web frontend
- Per-client logging streamed live over WebSocket
- REST API for bot management, parameter/indicator configuration, and trade history
- Docker + Traefik deployment with TLS support

## Core Trading Mechanism
1. Establish initial bid/ask prices using Volume-Weighted Average Price (VWAP) from order book depth
2. Adjust prices based on market dynamics (volatility, trend, spread factors)
3. Validate price spread covers trading fees before executing orders
4. Execute buy/sell orders and record trade history

## Target Users
- Algorithmic traders seeking automated crypto market-making
- Developers building or extending trading bot infrastructure
- Operators running multi-bot, multi-exchange trading systems

## Configuration
Bots are configured via JSON files in `sonarftdata/`:
- `config.json` — named configuration sets (config_1, config_2, ...)
- `config_parameters.json` — trading parameters (profit threshold, trade amount, simulation mode)
- `config_exchanges.json` — exchange list
- `config_symbols.json` — trading pairs
- `config_fees.json` — per-exchange fee structures
- `config_indicators.json` — technical indicator settings
- `config_markets.json` — market type (e.g. crypto)

## Deployment
- Run directly: `python sonarft.py` or `./dist/sonarft/sonarft`
- Docker: `docker-compose up` with Traefik reverse proxy on port 5000
- Select config: `./sonarft -c config_2 -l ccxt`
