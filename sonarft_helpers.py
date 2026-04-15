"""
SonarFT Helpers Module
Utility functions, Trade dataclass, and async-safe file persistence.

All file I/O is offloaded to a thread via asyncio.to_thread so the event
loop is never blocked during history writes.
"""
from dataclasses import dataclass
import asyncio
import json
import os
import logging
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
    All file operations are async-safe via asyncio.to_thread.
    """

    def __init__(self, is_simulation_mode: bool, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.is_simulation_mode = is_simulation_mode
        # Per-file locks prevent concurrent read-modify-write corruption
        self._file_locks: dict = {}

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

    async def save_order_data(self, pathname: str, order_info: dict) -> None:
        """Append order info to a JSON history file (async-safe)."""
        file_name = os.path.join('sonarftdata', 'history', pathname)
        async with self._get_lock(file_name):
            await asyncio.to_thread(self._append_json, file_name, order_info)
        self.logger.info("Order: Success")

    async def save_order_history(self, botid, trade: Trade, trade_position: str) -> None:
        """Save trade search info to a json file."""
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
        await self.save_order_data(f"{botid}_orders.json", trade_info)

    async def save_trade_data(self, pathname: str, trade_info: dict) -> None:
        """Append trade info to a JSON history file (async-safe)."""
        file_name = os.path.join('sonarftdata', 'history', pathname)
        async with self._get_lock(file_name):
            await asyncio.to_thread(self._append_json, file_name, trade_info)
        self.logger.info("Trade: Success")

    async def save_trade_history(
        self, botid, trade: Trade,
        buy_order_id, sell_order_id, trade_position,
        order_buy_success: bool, order_sell_success: bool, trade_success: bool
    ) -> None:
        """Save execution trade info to a json file."""
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
        await self.save_trade_data(f"{botid}_trades.json", trade_info)

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
