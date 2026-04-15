"""
Sonarft Bot Control
"""
import os
import json
import random
import asyncio
import logging
from typing import Dict, List, Tuple

from sonarft_api_manager import SonarftApiManager
from sonarft_helpers import SonarftHelpers
from sonarft_validators import SonarftValidators
from sonarft_indicators import SonarftIndicators
from sonarft_math import SonarftMath
from sonarft_prices import SonarftPrices
from sonarft_execution import SonarftExecution
from sonarft_search import SonarftSearch



# ### SonarftBot Class - ##########################################
class SonarftBot:
    """ """

    def __init__(self, library: str, logger: logging.Logger = None):
        """
        Initializes the SonarftBot with a unique bot id and a logger.

        Parameters:
        library (str): The name of the library to use for trading.
        logger (logging.Logger): An optional logger object to log messages.
        """

        self.logger = logger or logging.getLogger(__name__)
        self.library = library
        self.api_manager = None
        self.stop_bot_flag = False  # kept for BotManager.run_bot reset
        self._stop_event = asyncio.Event()
        self.botid = 0

    async def create_bot(self, config_setup: str):
        """
        Creates a new bot, loads the configurations, initializes the API manager and all bot modules,
        and then starts the bot's main loop.

        Parameters:
        config_setup (str): The name of the configuration setup to load.
        """
        
        try:
            self.stop_bot_flag = False

            self.botid = self.create_botid()
            botid_path = os.path.join("sonarftdata", "bots", f"{self.botid}.json")
            with open(botid_path, "w") as f:
                json.dump({"botid": self.botid}, f)

            self.logger.info("Initializing Bot manager module...")

            self.logger.info("Loading configurations...{config_setup}")
            self.load_configurations(config_setup)

            self.logger.info("Initializing API Manager module...")
            self.api_manager = SonarftApiManager(
                self.library, self.exchanges, self.exchanges_fees, self.logger
            )

            self.logger.info("Initializing API Manager module OK")

            self._load_api_keys()
            
            self.logger.info("Initializing Bot modules...")
            await self.InitializeModules()

            self.logger.info("Loading markets...")
            await self.api_manager.load_all_markets()

            self.logger.info("Bot %s has been created!", self.botid)
        except BotCreationError as error:
            self.logger.error("Bot creation error: %s", error)
            return

        return self.botid

    async def run_bot(self):
        self.logger.info(f"Bot {self.botid} start running")
        consecutive_failures = 0
        max_failures = 5
        base_backoff = 30  # seconds
        try:
            while not self._stop_event.is_set():
                try:
                    await self.sonarft_search.search_trades(self.botid)
                    consecutive_failures = 0
                except Exception as e:
                    consecutive_failures += 1
                    backoff = base_backoff * consecutive_failures
                    self.logger.error(
                        f"Bot {self.botid}: search error ({consecutive_failures}/{max_failures}): {e}. "
                        f"Backing off {backoff}s."
                    )
                    if consecutive_failures >= max_failures:
                        self.logger.error(
                            f"Bot {self.botid}: circuit breaker tripped after {max_failures} consecutive failures. Stopping."
                        )
                        self._stop_event.set()
                        break
                    try:
                        await asyncio.wait_for(
                            asyncio.shield(self._stop_event.wait()),
                            timeout=backoff
                        )
                    except asyncio.TimeoutError:
                        pass
                    continue

                if self._stop_event.is_set():
                    break

                timesleep_size = random.randint(6, 18)
                self.logger.info(
                    f"Next trade for bot {self.botid} in {timesleep_size} secs..."
                )
                try:
                    await asyncio.wait_for(
                        asyncio.shield(self._stop_event.wait()),
                        timeout=timesleep_size
                    )
                except asyncio.TimeoutError:
                    pass
        except Exception as e:
            self.logger.error(f"Fatal error in run_bot: {e}")

    def _load_api_keys(self):
        """
        Load exchange API keys from environment variables.

        For each configured exchange, reads:
          {EXCHANGE_ID_UPPER}_API_KEY
          {EXCHANGE_ID_UPPER}_SECRET
          {EXCHANGE_ID_UPPER}_PASSWORD  (optional, defaults to empty string)

        If no keys are found for any exchange, logs a warning.
        In simulation mode this is non-blocking — keys are not required.
        In live mode (is_simulating_trade=0) missing keys will cause order
        placement to fail with an authentication error from the exchange.
        """
        keys_loaded = 0
        for exchange_id in self.exchanges:
            prefix = exchange_id.upper()
            api_key = os.environ.get(f"{prefix}_API_KEY")
            secret = os.environ.get(f"{prefix}_SECRET")
            password = os.environ.get(f"{prefix}_PASSWORD", "")
            if api_key and secret:
                self.api_manager.setAPIKeys(exchange_id, api_key, secret, password)
                self.logger.info(f"API keys loaded for exchange: {exchange_id}")
                keys_loaded += 1
            else:
                self.logger.warning(
                    f"No API keys found for exchange '{exchange_id}'. "
                    f"Set {prefix}_API_KEY and {prefix}_SECRET environment variables "
                    f"to enable live trading on this exchange."
                )
        if keys_loaded == 0 and not self.is_simulating_trade:
            self.logger.warning(
                "No API keys loaded for any exchange and simulation mode is OFF. "
                "Live order placement will fail with authentication errors."
            )

    def setAPIKeys(self, exchange: str, api_key: str, secret_key: str, password: str):
        """
        Sets the API keys for a given exchange.
        Args:
            exchange (str): The name of the exchange.
            api_key (str): The API key.
            secret_key (str): The secret key.
            password (str): The password.
        """
        self.api_manager.setAPIKeys(exchange, api_key, secret_key, password)

    def create_botid(self) -> int:
        self.logger.info("Creating Bot ID...")
        return random.randint(10001, 99999)

    async def stop_bot(self):
        """
        Signals the bot to stop and waits for the run loop to exit cleanly.
        """
        self._stop_event.set()
        self.stop_bot_flag = True
        self.logger.info(f"Bot {self.botid} stop signal sent.")

    # ### loaders *****************************************************
    def load_configurations(self, config_setup: str = "config_1"):
        pathname = "sonarftdata/config.json"
        with open(pathname, "r") as f:
            loadconfig = json.load(f)
            config = loadconfig[config_setup][0]

        self.market = self.load_markets(
            config["markets_pathname"], config["markets_setup"]
        )

        (
            self.profit_percentage_threshold,
            self.trade_amount,
            self.is_simulating_trade,
            self.max_daily_loss,
            self.spread_increase_factor,
            self.spread_decrease_factor,
        ) = self.load_parameters(
            config["parameters_pathname"], config["parameters_setup"]
        )
        self._validate_parameters()

        self.symbols = self.load_symbols(
            config["symbols_pathname"], config["symbols_setup"]
        )
        self.exchanges = self.load_exchanges(
            config["exchanges_pathname"], config["exchanges_setup"]
        )
        self.exchanges_fees = self.load_fees(
            config["fees_pathname"], config["fees_setup"]
        )

    def _validate_parameters(self):
        """Raise ValueError early if any trading parameter is out of safe range."""
        if not (0 < self.profit_percentage_threshold < 1):
            raise ValueError(f"profit_percentage_threshold must be between 0 and 1, got {self.profit_percentage_threshold}")
        if self.trade_amount <= 0:
            raise ValueError(f"trade_amount must be positive, got {self.trade_amount}")
        if self.is_simulating_trade not in (0, 1):
            raise ValueError(f"is_simulating_trade must be 0 or 1, got {self.is_simulating_trade}")
        if self.max_daily_loss < 0:
            raise ValueError(f"max_daily_loss must be >= 0, got {self.max_daily_loss}")
        if not (1.0 < self.spread_increase_factor < 1.01):
            raise ValueError(f"spread_increase_factor must be between 1.0 and 1.01, got {self.spread_increase_factor}")
        if not (0.99 < self.spread_decrease_factor < 1.0):
            raise ValueError(f"spread_decrease_factor must be between 0.99 and 1.0, got {self.spread_decrease_factor}")

    def load_markets(self, markets_pathname: str, markets_setup: str) -> str:
        """
        Loads the market data from the specified file.
        Args:
            markets_pathname (str): The path to the markets file.
            markets_setup (str): The market setup to load.
        Returns:
            str: The market loaded from the file.
        """
        self.logger.info("Loading market...")
        setup = f"market_{markets_setup}"
        with open(markets_pathname, "r") as f:
            market = json.load(f)[setup]
            self.logger.info(f"Market loaded: {market}")
        return market

    def load_parameters(self, parameters_pathname: str, parameters_setup: str) -> Tuple:
        """
        Loads the parameters data from the specified file.
        Args:
            parameters_pathname (str): The path to the parameters file.
            parameters_setup (str): The parameters setup to load.
        Returns:
            tuple: The parameters loaded from the file.
        """
        self.logger.info("Loading parameters...")
        setup = f"parameters_{parameters_setup}"
        with open(parameters_pathname, "r") as f:
            parameters = json.load(f)[setup][0]

        self.logger.info(
            f"Parameters loaded: {', '.join(f'{k}: {v}' for k, v in parameters.items())}"
        )
        return (
            parameters['profit_percentage_threshold'],
            parameters['trade_amount'],
            parameters['is_simulating_trade'],
            parameters.get('max_daily_loss', 0.0),
            parameters.get('spread_increase_factor', 1.00072),
            parameters.get('spread_decrease_factor', 0.99936),
        )

    def load_exchanges(self, exchanges_pathname: str, exchanges_setup: str) -> List:
        """
        Loads the exchanges data from the specified file.
        Args:
            exchanges_pathname (str): The path to the exchanges file.
            exchanges_setup (str): The exchanges setup to load.
        Returns:
            list: The exchanges loaded from the file.
        """
        self.logger.info("Loading exchanges...")
        setup = f"exchanges_{exchanges_setup}"
        with open(exchanges_pathname, "r") as f:
            exchanges = json.load(f)[setup]
            self.logger.info(f"Exchanges loaded: {exchanges}")
        return exchanges

    def load_symbols(self, symbols_pathname: str, symbols_setup: str) -> List:
        """
        Loads the symbols data from the specified file.
        Args:
            symbols_pathname (str): The path to the symbols file.
            symbols_setup (str): The symbols setup to load.
        Returns:
            list: The symbols loaded from the file.
        """
        self.logger.info("Loading symbols...")
        setup = f"symbols_{symbols_setup}"
        with open(symbols_pathname, "r") as f:
            symbols = json.load(f)[setup]
            self.logger.info(f"Symbols loaded: {symbols}")
        return symbols

    def load_fees(self, fees_pathname: str, fees_setup: str) -> Dict:
        """
        Loads the fees data from the specified file.
        Args:
            fees_pathname (str): The path to the fees file.
            fees_setup (str): The fees setup to load.
        Returns:
            dict: The fees loaded from the file.
        """
        setup = f"exchanges_fees_{fees_setup}"
        with open(fees_pathname, "r") as f:
            exchanges_fees = json.load(f)[setup]
        return exchanges_fees

    # ### Initialize all modules ***************************************
    async def InitializeModules(self):
        """
        Initializes all modules required for the bot's operation.
        """
        self.logger.info(f"Initializing Helpers module...")
        self.sonarft_helpers = SonarftHelpers(self.is_simulating_trade, self.logger)
        self.logger.info(f"Initializing Helpers module OK")

        self.logger.info(f"Initializing Validators module...")
        self.sonarft_validators = SonarftValidators(self.api_manager, self.logger)
        self.logger.info(f"Initializing Validators module OK")

        self.logger.info(f"Initializing Indicators module...")
        self.sonarft_indicators = SonarftIndicators(self.api_manager, self.logger)
        self.logger.info(f"Initializing Indicators module OK")

        self.logger.info(f"Initializing Math module...")
        self.sonarft_math = SonarftMath(self.api_manager)
        self.logger.info(f"Initializing Math module OK")

        self.logger.info(f"Initializing Prices module...")
        self.sonarft_prices = SonarftPrices(
            self.api_manager, self.sonarft_indicators, self.logger
        )
        self.sonarft_prices.spread_increase_factor = self.spread_increase_factor
        self.sonarft_prices.spread_decrease_factor = self.spread_decrease_factor
        self.logger.info(f"Initializing Prices module OK")

        self.logger.info(f"Initializing Execution module...")
        self.sonarft_execution = SonarftExecution(
            self.api_manager,
            self.sonarft_helpers,
            self.sonarft_indicators,
            self.is_simulating_trade,
            self.logger,
        )
        self.logger.info(f"Initializing Execution module OK")

        self.logger.info(f"Initializing Search module...")
        self.sonarft_search = SonarftSearch(
            self.sonarft_math,
            self.sonarft_prices,
            self.sonarft_validators,
            self.sonarft_execution,
            self.trade_amount,
            self.symbols,
            self.profit_percentage_threshold,
            self.is_simulating_trade,
            self.logger,
            max_daily_loss=self.max_daily_loss,
        )
        await self.sonarft_search.start()
        self.logger.info(f"Initializing Search module OK")

class BotCreationError(Exception):
    """Raised when there's an issue during the bot creation process."""

    def __init__(self, message="Failed to create the bot."):
        self.message = message
        super().__init__(self.message)
