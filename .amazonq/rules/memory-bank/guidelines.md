# SonarFT - Development Guidelines

## Code Quality Standards

### Module Header Convention
Every Python file starts with a module-level docstring describing its role:
```python
"""
SonarFT <Module Name> Module
<Brief description of responsibility>
"""
```

### Class Structure Convention
Classes follow a consistent layout:
1. Class docstring
2. `__init__` with injected dependencies (api_manager, logger, peer modules)
3. Grouped methods separated by `# ### Section Name ***` comment banners
4. Support/helper methods at the bottom

```python
# ### SonarftBot Class - ##########################################
class SonarftBot:
    """ """
    def __init__(self, library: str, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        ...

    # ### loaders *****************************************************
    def load_configurations(self, ...):
        ...

    # ### Initialize all modules ***************************************
    async def InitializeModules(self):
        ...
```

### Logger Injection Pattern
Every class accepts an optional logger and falls back to module-level logger:
```python
self.logger = logger or logging.getLogger(__name__)
```
Never use `print()` for operational messages — use `self.logger.info/warning/error`.

### Decimal Precision
Set at the top of every file that performs financial calculations:
```python
from decimal import getcontext
getcontext().prec = 8
```

### Type Annotations
All public methods use full type annotations with `typing` imports:
```python
from typing import Dict, List, Tuple, Optional, Union
async def get_latest_prices(self, base: str, quote: str, weight) -> List[Tuple[str, float, float, float, str]]:
```

---

## Async Patterns

### All I/O is async
Every exchange API call, order book fetch, indicator calculation, and order execution is `async/await`:
```python
async def get_rsi(self, exchange, base, quote, moving_average_period=14, timeframe='1m'):
    ohlcv = await self.get_history(exchange, base, quote, timeframe, moving_average_period+2)
    ...
```

### Concurrent execution with asyncio.gather
Use `asyncio.gather` for parallel operations (symbol processing, dual-exchange calls):
```python
result_01, result_02 = await asyncio.gather(
    self.sonarft_validators.deeper_verify_liquidity(buy_exchange, ...),
    self.sonarft_validators.deeper_verify_liquidity(sell_exchange, ...),
)
```

### Async task management
Long-running tasks are created with `asyncio.create_task` and tracked in a list:
```python
task = asyncio.create_task(action_method(botid or client_id))
self.tasks.append(task)
```
Completed tasks are cleaned up by checking `task.done()` and `task.exception()`.

### asyncio.Lock for shared state
Shared mutable state (bot registry) is protected with `asyncio.Lock`:
```python
async with self._lock:
    self._bots[botid] = bot
```

---

## Error Handling Patterns

### try/except with logger.error
All async methods wrap their body in try/except and log errors without re-raising (fail-safe):
```python
try:
    ...
except Exception as e:
    self.logger.error(f"Error get_rsi: {str(e)}")
    return None
```

### Return None/False on failure
Methods return `None` or `False` on error rather than raising, allowing callers to check:
```python
if result_01 is False or result_02 is False:
    return False
```

### Custom exception classes
Domain-specific errors use custom exception classes with default messages:
```python
class BotCreationError(Exception):
    def __init__(self, message="Failed to create the bot."):
        self.message = message
        super().__init__(self.message)
```

### HTTP endpoint error handling
FastAPI endpoints always catch `FileNotFoundError` (404) and generic `Exception` (500) separately:
```python
except FileNotFoundError as exc:
    raise HTTPException(status_code=404, detail="File not found") from exc
except Exception as error:
    raise HTTPException(status_code=500, detail=str(error)) from error
```

---

## Naming Conventions

### Python (snake_case throughout)
- Classes: `PascalCase` — `SonarftBot`, `BotManager`, `TradeProcessor`
- Methods: `snake_case` — `create_bot`, `load_configurations`, `get_rsi`
- Variables: `snake_case` — `buy_exchange`, `profit_percentage`, `trade_amount`
- Constants: `UPPER_SNAKE_CASE` — `LOW_VOLATILITY_THRESHOLD`, `EXCHANGE_RULES`
- Private methods: leading underscore — `_execute_single_trade`

### Exception: one PascalCase method exists
`InitializeModules` in `SonarftBot` uses PascalCase — treat as legacy, new methods use snake_case.

### Market direction strings
Use lowercase string literals `'bull'`, `'bear'`, `'neutral'` consistently across all modules.

### Exchange/symbol format
Symbols always constructed as `f"{base}/{quote}"` — never hardcoded as a full string.

---

## Dependency Injection Pattern
Modules never instantiate their own dependencies. All dependencies are passed via constructor:
```python
class SonarftPrices:
    def __init__(self, api_manager: SonarftApiManager, sonarft_indicators: SonarftIndicators, logger=None):
        self.api_manager = api_manager
        self.sonarft_indicators = sonarft_indicators
```
`SonarftBot.InitializeModules` is the single wiring point for the entire dependency graph.

---

## Configuration Pattern
All config is loaded from JSON files via named setups (e.g. `parameters_1`, `exchanges_1`):
```python
setup = f"parameters_{parameters_setup}"
with open(parameters_pathname, "r") as f:
    parameters = json.load(f)[setup][0]
```
Never hardcode trading parameters — always read from config files.

---

## API Abstraction Pattern
All exchange calls go through `SonarftApiManager.call_api_method`, which dispatches to the correct ccxt/ccxtpro method:
```python
await self.call_api_method(exchange_id, 'fetch_order_book', 'watch_order_book', symbol)
```
- First method name: ccxt (REST/sync)
- Second method name: ccxtpro (WebSocket/async)

Modules above the API layer (indicators, validators, prices) always call through thin wrapper methods:
```python
async def get_order_book(self, exchange_id, base, quote):
    return await self.api_manager.get_order_book(exchange_id, base, quote)
```

---

## Financial Calculation Patterns

### VWAP calculation
Standard pattern used in both `SonarftApiManager` and `SonarftPrices`:
```python
total_bid_volume = sum(volume for _, volume in bids)
bid_vwap = sum(price * volume for price, volume in bids) / total_bid_volume
```

### Price rounding by exchange rules
Each exchange has a `EXCHANGE_RULES` dict in `SonarftMath` defining precision per field:
```python
buy_price = round(buy_price, buy_rules['prices_precision'])
buy_fee_quote = round(buy_price * target_amount_buy * buy_fee_rate, buy_rules['fee_precision'])
```

### Indicator data format
OHLCV data is always indexed positionally: `[timestamp, open, high, low, close, volume]`
- Close price: `x[4]`
- High price: `x[2]`
- Low price: `x[3]`
- Volume: `x[5]`

### pandas-ta usage
Always convert OHLCV close prices to `pd.Series` before passing to pandas-ta:
```python
close_prices = pd.Series([x[4] for x in ohlcv])
rsi = pta.rsi(close_prices, length=moving_average_period)
return rsi.iloc[-1]
```

---

## Simulation Mode Pattern
The `is_simulating_trade` / `is_simulation_mode` boolean gates all real order placement:
```python
if not self.is_simulation_mode:
    order_placed = await self.api_manager.create_order(...)
else:
    executed_amount = trade_amount
    remaining_amount = 0
    order_placed_id = f"{side}_{random.randint(100000, 999999)}"
```
Balance checks also short-circuit in simulation mode: `if self.is_simulation_mode: return True`.

---

## WebSocket / Logging Pattern
Per-client logging is streamed over WebSocket using a custom `AsyncHandler`:
- `emit()` puts records into an `asyncio.Queue`
- `consume_logs(client_id)` is a background task that drains the queue per client
- `send_logs()` polls the per-client log list and sends over WebSocket

Log format: `"%(levelname)s - %(client_id)s - %(message)s"` with `ClientIdFilter` injecting `client_id`.

---

## C++ Model Conventions (models/)
- Use `constexpr` for compile-time constants
- Use `std::vector` with `.reserve()` for performance-critical collections
- Use `std::stable_sort` when sort stability matters
- Use `std::chrono::high_resolution_clock` for benchmarking
- Genetic algorithm parameters (population size, generations, tournament size) are hardcoded constants — adjust directly in `geneticAlgorithm()`
- Input validation checks all constraints before processing and returns `false`/`1` on violation
