"""
SonarFT Search Module
Orchestrates trade search, validation, and execution dispatch across symbols.
"""
import logging
import asyncio
from typing import Optional, Dict, List

from sonarft_math import SonarftMath
from sonarft_prices import SonarftPrices
from sonarft_validators import SonarftValidators
from sonarft_execution import SonarftExecution


class TradeValidator:
    """
    """
    def __init__(self, sonarft_validators: SonarftValidators, logger=None):
        """
        """
        self.sonarft_validators = sonarft_validators
        self.logger = logger or logging.getLogger(__name__)

    async def has_requirements_for_success_carrying_out(
        self,
        buy_exchange: str,
        sell_exchange: str,
        base: str,
        quote: str,
        buy_price: float,
        sell_price: float,
        trade_amount: float,
    ) -> bool:
        """
        """
        result_01, result_02 = await asyncio.gather(
            self.sonarft_validators.deeper_verify_liquidity(
                buy_exchange, base, quote, "buy", buy_price, trade_amount, 50
            ),
            self.sonarft_validators.deeper_verify_liquidity(
                sell_exchange, base, quote, "ask", sell_price, trade_amount, 50
            ),
        )
        if result_01 is False or result_02 is False:
            return False

        if not await self.sonarft_validators.verify_spread_threshold(
            buy_exchange, sell_exchange, base, quote, buy_price, sell_price
        ):
            return False

        # slippage verification needs to be done after the spread verification
        # if not await self.sonarft_validators.check_slippage(trade):
        #     return False

        return True


class TradeExecutor:
    """
    """

    def __init__(self, sonarft_execution: SonarftExecution, logger=None):
        self.sonarft_execution = sonarft_execution
        self.logger = logger or logging.getLogger(__name__)
        self.trade_tasks = []
        self.monitor_task = None

    async def start(self):
        """Start the background monitor task. Must be called from an async context."""
        self.monitor_task = asyncio.create_task(self.monitor_trade_tasks())

    def execute_trade(self, botid, trade_data: Dict) -> None:
        trade_task = asyncio.create_task(
            self.sonarft_execution.execute_trade(botid, trade_data)
        )
        trade_task.botid = botid  # Attach the botid to the task
        self.trade_tasks.append(trade_task)

    async def monitor_trade_tasks(self):
        while True:
            done_tasks = [t for t in self.trade_tasks if t.done()]
            self.trade_tasks = [t for t in self.trade_tasks if not t.done()]
            for task in done_tasks:
                try:
                    self.logger.info(f"Trade task result: {task.result()}")
                except Exception as e:
                    self.logger.error(f"Trade task raised an exception: {e}")
            await asyncio.sleep(1)

    def cancel_trade(self, botid):
        # Cancel the task for the given botid
        for task in self.trade_tasks:
            if task.botid == botid:
                task.cancel()
                self.trade_tasks.remove(task)
                break

class TradeProcessor:
    def __init__(
        self,
        sonarft_validators: SonarftValidators,
        sonarft_execution: SonarftExecution,
        sonarft_math: SonarftMath,
        sonarft_prices: SonarftPrices,
        logger=None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.sonarft_math = sonarft_math
        self.sonarft_prices = sonarft_prices
        self.trade_validator = TradeValidator(sonarft_validators, logger)
        self.trade_executor = TradeExecutor(sonarft_execution, logger)

    async def start(self):
        """Start background tasks. Must be called from an async context."""
        await self.trade_executor.start()

    async def process_symbol(self, botid, symbol, trade_amount, percentage_threshold):
        if trade_amount <= 0:
            self.logger.warning(f"Bot {botid}: trade_amount {trade_amount} is invalid, skipping symbol")
            return

        self.logger.info(f"(v1009) - Bot {botid}: NEW TRADE SEARCHING...")
        self.logger.info(
            "-----------------------------------------------------------\n"
        )

        base = symbol["base"]
        quotes = symbol["quotes"]
        trade_amount = trade_amount
        for quote_index, quote in enumerate(quotes):
            (
                buy_prices_list,
                sell_prices_list,
            ) = await self.sonarft_prices.get_the_latest_prices(
                base, quote, trade_amount, weight=12
            )
            if not buy_prices_list or not sell_prices_list:
                return

            for buy_price_list in buy_prices_list:
                for sell_price_list in sell_prices_list:
                    await self.process_trade_combination(
                        botid,
                        base,
                        quote,
                        trade_amount,
                        buy_price_list,
                        sell_price_list,
                        percentage_threshold,
                    )

    async def process_trade_combination(
        self,
        botid,
        base: str,
        quote: str,
        trade_amount: float,
        buy_price_list: List,
        sell_price_list: List,
        percentage_threshold,
    ):
        """
        Process a trade combination
        """
        buy_exchange, buy_price, buy_ask, latest_buy_price, _ = buy_price_list
        sell_exchange, sell_bid, sell_price, latest_sell_price, _ = sell_price_list

        (
            adjusted_buy_price,
            adjusted_sell_price,
            indicators,
        ) = await self.sonarft_prices.weighted_adjust_prices(
            botid,
            buy_exchange,
            sell_exchange,
            base,
            quote,
            buy_price,
            sell_price,
            latest_buy_price,
            latest_sell_price,
        )

        # Update the buy and sell lists with the adjusted prices
        buy_price_list = (buy_exchange, adjusted_buy_price, *buy_price_list[2:])
        sell_price_list = (
            sell_exchange,
            sell_bid,
            adjusted_sell_price,
            *sell_price_list[3:],
        )

        profit, profit_percentage, trade_data = self.sonarft_math.calculate_trade(
            adjusted_buy_price,
            adjusted_sell_price,
            buy_price_list,
            sell_price_list,
            trade_amount,
            base,
            quote,
        )

        if trade_data is not None:
            trade_data.update(indicators)

        # Information about the trade
        self.logger.info(f"{base}/{quote}: Trade Amount {trade_amount}")
        self.logger.info(
            f"{base}/{quote}: Latest Buy: {latest_buy_price} - Latest Sell: {latest_sell_price}"
        )
        self.logger.info(
            f"{base}/{quote}: Target Buy: {trade_data['buy_price']} - Target Sell: {trade_data['sell_price']}"
        )
        self.logger.info(
            f"{base}/{quote}: Profit {profit} - Percentage: {profit_percentage}"
        )
        self.logger.info(
            "-----------------------------------------------------------\n"
        )

        # Verify if profit is above the profit percentage threshold
        if profit_percentage >= percentage_threshold:
            # Verify requirements for a successful trade execution
            has_requirements = (
                await self.trade_validator.has_requirements_for_success_carrying_out(
                    buy_exchange,
                    sell_exchange,
                    base,
                    quote,
                    adjusted_buy_price,
                    adjusted_sell_price,
                    trade_amount,
                )
            )

            if has_requirements:
                self.logger.info(
                    f"\n(v1009) - Bot {botid}: A NEW TRADE HAS BEEN FOUND!"
                )
                self.logger.info(
                    "------------------------------------------------------------------------------------\n"
                )
                self.trade_executor.execute_trade(botid, trade_data)



class SonarftSearch:
    """
    SonarftSearch class is responsible for finding healthy trades and executing them.
    A healthy trade is a profitable trade with the lowest risk and the highest probability of successful execution.
    """

    def __init__(
        self,
        sonarft_math: SonarftMath,
        sonarft_prices: SonarftPrices,
        sonarft_validators: SonarftValidators,
        sonarft_execution: SonarftExecution,
        trade_amount: float,
        symbols: List,
        profit_percentage_threshold: float,
        is_simulating_trade: bool,
        logger=None,
        max_daily_loss: float = 0.0,
    ):
        self.logger = logger or logging.getLogger(__name__)

        self.trade_processor = TradeProcessor(
            sonarft_validators, sonarft_execution, sonarft_math, sonarft_prices, logger
        )

        self.trade_amount = trade_amount
        self.symbols = symbols
        self.profit_percentage_threshold = profit_percentage_threshold
        self.is_simulating_trade = is_simulating_trade
        self.max_daily_loss = max_daily_loss
        self.daily_loss_accumulated = 0.0

        self.latest_executed_buy_price_order = []

    async def start(self):
        """Start background tasks. Must be called once from an async context after construction."""
        await self.trade_processor.start()

    def record_trade_result(self, profit: float):
        """Accumulate profit/loss. Call after each completed trade."""
        if profit < 0:
            self.daily_loss_accumulated += abs(profit)

    def is_halted(self) -> bool:
        """Returns True if the daily loss limit has been reached."""
        if self.max_daily_loss > 0 and self.daily_loss_accumulated >= self.max_daily_loss:
            self.logger.warning(
                f"Daily loss limit reached: {self.daily_loss_accumulated} >= {self.max_daily_loss}. Halting trades."
            )
            return True
        return False

    async def search_trades(self, botid) -> None:
        """Search for the best trades for the given symbols and trade amounts."""
        if self.is_halted():
            return

        futures = [
            self.trade_processor.process_symbol(
                botid, symbol, self.trade_amount, self.profit_percentage_threshold
            )
            for symbol in self.symbols
        ]
        results = await asyncio.gather(*futures, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Error while searching for trades: {result}\n")

