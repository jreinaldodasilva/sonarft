"""
SonarFT Helpers Module
Utility functions, Trade dataclass, and async-safe file persistence.

Trade and order history is stored in SQLite (sonarftdata/history/sonarft.db)
for O(1) writes, concurrent-safe access, and efficient querying.
Falls back to JSON append if SQLite is unavailable.
"""
from dataclasses import dataclass
import asyncio
import json
import os
import logging
import sqlite3
import time


@dataclass
class Trade:
    position: str
    base: str
    quote: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    buy_trade_amount: float
    sell_trade_amount: float
    executed_amount: float
    buy_value: float
    sell_value: float
    buy_fee_rate: float
    sell_fee_rate: float
    buy_fee_base: float
    buy_fee_quote: float
    sell_fee_quote: float
    profit: float
    profit_percentage: float
    # Pre-computed indicators passed from price adjustment to avoid re-fetch at execution
    market_direction_buy: str = None
    market_direction_sell: str = None
    market_rsi_buy: float = None
    market_rsi_sell: float = None
    market_stoch_rsi_buy_k: float = None
    market_stoch_rsi_buy_d: float = None
    market_stoch_rsi_sell_k: float = None
    market_stoch_rsi_sell_d: float = None


class SonarftHelpers:
    """
    SonarFTHelpers class contains helper functions for the trading bot.
    Trade/order history is persisted to SQLite for O(1) writes and concurrent safety.
    All file operations are async-safe via asyncio.to_thread.
    """

    _DB_PATH = os.path.join('sonarftdata', 'history', 'sonarft.db')

    def __init__(self, is_simulation_mode: bool, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.is_simulation_mode = is_simulation_mode
        self._file_locks: dict = {}
        self._db_lock = asyncio.Lock()
        # Initialise DB schema in a thread at construction time (sync context)
        try:
            self._init_db()
        except Exception as e:
            self.logger.warning(f"SQLite init failed, will fall back to JSON: {e}")

    # ### SQLite helpers *************************************************

    @classmethod
    def _init_db(cls) -> None:
        """Create tables if they don't exist. Safe to call multiple times."""
        os.makedirs(os.path.dirname(cls._DB_PATH), exist_ok=True)
        with sqlite3.connect(cls._DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    botid     TEXT NOT NULL,
                    timestamp TEXT,
                    data      TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    botid     TEXT NOT NULL,
                    timestamp TEXT,
                    data      TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_botid ON orders(botid)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_botid ON trades(botid)")
            conn.commit()

    @classmethod
    def _db_insert(cls, table: str, botid: str, timestamp: str, data: dict) -> None:
        """Insert one record into the given table. Runs in a thread."""
        with sqlite3.connect(cls._DB_PATH) as conn:
            conn.execute(
                f"INSERT INTO {table} (botid, timestamp, data) VALUES (?, ?, ?)",
                (str(botid), timestamp, json.dumps(data))
            )
            conn.commit()

    @classmethod
    def _db_query(cls, table: str, botid: str) -> list:
        """Return all records for botid as a list of dicts. Runs in a thread."""
        with sqlite3.connect(cls._DB_PATH) as conn:
            rows = conn.execute(
                f"SELECT data FROM {table} WHERE botid = ? ORDER BY id",
                (str(botid),)
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def _get_lock(self, file_name: str) -> asyncio.Lock:
        """Return (creating if needed) a per-file asyncio.Lock."""
        if file_name not in self._file_locks:
            self._file_locks[file_name] = asyncio.Lock()
        return self._file_locks[file_name]

    # ### Sync helpers (run inside to_thread) ****************************

    @staticmethod
    def _append_json(file_name: str, record: dict) -> None:
        """Read-modify-write a JSON array file. Runs in a thread."""
        if os.path.exists(file_name):
            with open(file_name, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = []
        history.append(record)
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=4)

    @staticmethod
    def _write_json(file_name: str, data: dict) -> None:
        """Write a JSON object to a file. Runs in a thread."""
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f)

    # ### Async public API ***********************************************

    async def save_botid(self, botid):
        """Save botid info to a json file."""
        file_name = os.path.join('sonarftdata', 'bots', f"{botid}.json")
        async with self._get_lock(file_name):
            await asyncio.to_thread(self._write_json, file_name, {"botid": botid})

    async def save_order_data(self, botid, order_info: dict) -> None:
        """Persist order info to SQLite (async-safe)."""
        timestamp = order_info.get('timestamp', '')
        async with self._db_lock:
            await asyncio.to_thread(self._db_insert, 'orders', botid, timestamp, order_info)
        self.logger.info("Order: Success")

    async def save_order_history(self, botid, trade: Trade, trade_position: str) -> None:
        """Save trade search info to SQLite."""
        t = time.localtime()
        current_time = time.strftime("%m-%d-%Y %H:%M:%S", t)
        trade_info = {
            'timestamp': current_time,
            'position': trade_position,
            'base': trade.base,
            'quote': trade.quote,
            'buy_exchange': trade.buy_exchange,
            'sell_exchange': trade.sell_exchange,
            'buy_price': trade.buy_price,
            'sell_price': trade.sell_price,
            'buy_trade_amount': trade.buy_trade_amount,
            'sell_trade_amount': trade.sell_trade_amount,
            'executed_amount': trade.executed_amount,
            'buy_value': trade.buy_value,
            'sell_value': trade.sell_value,
            'buy_fee_rate': trade.buy_fee_rate,
            'sell_fee_rate': trade.sell_fee_rate,
            'buy_fee_base': trade.buy_fee_base,
            'buy_fee_quote': trade.buy_fee_quote,
            'sell_fee_quote': trade.sell_fee_quote,
            'profit': trade.profit,
            'profit_percentage': trade.profit_percentage,
        }
        await self.save_order_data(botid, trade_info)

    async def save_trade_data(self, botid, trade_info: dict) -> None:
        """Persist trade info to SQLite (async-safe)."""
        timestamp = trade_info.get('timestamp', '')
        async with self._db_lock:
            await asyncio.to_thread(self._db_insert, 'trades', botid, timestamp, trade_info)
        self.logger.info("Trade: Success")

    async def save_trade_history(
        self, botid, trade: Trade,
        buy_order_id, sell_order_id, trade_position,
        order_buy_success: bool, order_sell_success: bool, trade_success: bool
    ) -> None:
        """Save execution trade info to SQLite."""
        t = time.localtime()
        current_time = time.strftime("%m-%d-%Y %H:%M:%S", t)
        trade_info = {
            'timestamp': current_time,
            'position': trade_position,
            'buy_order_id': buy_order_id,
            'sell_order_id': sell_order_id,
            'base': trade.base,
            'quote': trade.quote,
            'buy_exchange': trade.buy_exchange,
            'sell_exchange': trade.sell_exchange,
            'buy_price': trade.buy_price,
            'sell_price': trade.sell_price,
            'buy_trade_amount': trade.buy_trade_amount,
            'sell_trade_amount': trade.sell_trade_amount,
            'executed_amount': trade.executed_amount,
            'buy_value': trade.buy_value,
            'sell_value': trade.sell_value,
            'buy_fee_rate': trade.buy_fee_rate,
            'sell_fee_rate': trade.sell_fee_rate,
            'buy_fee_base': trade.buy_fee_base,
            'buy_fee_quote': trade.buy_fee_quote,
            'sell_fee_quote': trade.sell_fee_quote,
            'profit': trade.profit,
            'profit_percentage': trade.profit_percentage,
            'order_buy_success': order_buy_success,
            'order_sell_success': order_sell_success,
            'trade_success': trade_success,
        }
        await self.save_trade_data(botid, trade_info)

    async def get_orders(self, botid) -> list:
        """Retrieve all orders for a bot from SQLite."""
        async with self._db_lock:
            return await asyncio.to_thread(self._db_query, 'orders', botid)

    async def get_trades(self, botid) -> list:
        """Retrieve all trades for a bot from SQLite."""
        async with self._db_lock:
            return await asyncio.to_thread(self._db_query, 'trades', botid)

    @classmethod
    async def _async_query(cls, table: str, botid: str) -> list:
        """Classmethod async query — usable without a full instance (e.g. from HTTP endpoints)."""
        return await asyncio.to_thread(cls._db_query, table, botid)

    async def save_error(self, error_info: dict) -> None:
        """Save error info to a json file."""
        file_name = os.path.join('sonarftdata', 'errors_history.json')
        async with self._get_lock(file_name):
            await asyncio.to_thread(self._append_json, file_name, error_info)
        self.logger.info(f"Errors info saved to {file_name}")

    async def save_balance_data(self, balance_info: dict) -> None:
        """Save balance info to a json file."""
        file_name = os.path.join('sonarftdata', 'balance_history.json')
        async with self._get_lock(file_name):
            await asyncio.to_thread(self._append_json, file_name, balance_info)
        self.logger.info(f"Balance info saved to {file_name}")

    def percentage_difference(self, value1, value2):
        """Calculate the percentage difference between two values."""
        if value1 == 0 or value2 == 0 or value1 == value2:
            return 0
        return abs((value1 - value2) / ((value1 + value2) / 2)) * 100
