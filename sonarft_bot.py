"""
Sonarft Bot Control
"""
import os
import json
import time
import random
import asyncio
import logging
from decimal import getcontext
from typing import Dict, List, Tuple

from sonarft_api_manager import SonarftApiManager
from sonarft_helpers import SonarftHelpers
from sonarft_validators import SonarftValidators
from sonarft_indicators import SonarftIndicators
from sonarft_math import SonarftMath
from sonarft_prices import SonarftPrices
from sonarft_execution import SonarftExecution
from sonarft_search import SonarftSearch

getcontext().prec = 8


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
        self.stop_bot_flag = False
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
            self.save_botid(self.botid)

            self.logger.info("Initializing Bot manager module...")

            self.logger.info("Loading configurations...{config_setup}")
            self.load_configurations(config_setup)

            self.logger.info("Initializing API Manager module...")
            self.api_manager = SonarftApiManager(
                self.library, self.exchanges, self.exchanges_fees, self.logger
            )

            self.logger.info("Initializing API Manager module OK")

            # await self.api_manager.setAPIKeys(self.botid)
            
            self.logger.info("Initializing Bot modules...")
            await self.InitializeModules()

            # self.logger.info(f"Loading markets...")
            # await self.api_manager.load_markets()

            self.logger.info("Bot %s has been created!", self.botid)
        except BotCreationError as error:
            self.logger.error("Bot creation error: %s", error)
            return

        return self.botid

    async def run_bot(self):
        # Main loop that holds the bot code running
        self.logger.info(f"Bot {self.botid} start running")
        try:
            while True:
                await self.sonarft_search.search_trades(self.botid)
                if self.stop_bot_flag:
                    return

                timesleep_size = random.randint(6, 18)
                self.logger.info(
                    f"Next trade for bot {self.botid} in {timesleep_size} secs..."
                )

                await asyncio.sleep(timesleep_size)

        except Exception as e:
            self.logger.error(f"Error: {e}")

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
        """
        Creates a unique bot id.
        Returns:
            int: The unique bot id.
        """
        self.logger.info("Creating Bot ID...")
        t = round(time.time())
        n = random.randint(10001, 99999)
        botid = n
        return botid

    def save_botid(self, botid: int):
        """
        Saves the bot id to a json file.
        Args:
            botid (int): The unique bot id.
        """
        self.logger.info("Saving Bot ID...")
        pathname = str(botid) + ".json"
        file_name = os.path.join("sonarftdata", "bots", pathname)
        data = {"botid": botid}
        with open(file_name, "w") as file:
            json.dump(data, file)

    def get_botid(self) -> int:
        """
        Returns the bot id.
        Returns:
            int: The unique bot id.
        """
        return self.botid

    async def stop_bot(self):
        """
        Sets the stop_bot_flag to True and then waits for the bot to stop.
        """
        self.stop_bot_flag = True
        while self.stop_bot_flag:
            await asyncio.sleep(1)
        self.logger.info(f"Bot {self.botid} has stopped.")

    # ### loaders *****************************************************
    def load_configurations(self, config_setup: str = "config_1"):
        """
        Loads the configuration data from the config.json file.
        Args:
            config_setup (str): The configuration setup to load.
        """
        pathname = "sonarftdata/config.json"
        with open(pathname, "r") as f:
            loadconfig = json.load(f)
            config = loadconfig[config_setup][0]

        self.market = self.load_markets(
            config["markets_pathname"], config["markets_setup"]
        )

        # if self.market == "crypto":
        (
            self.profit_percentage_threshold,
            self.trade_amount,
            self.is_simulating_trade,
        ) = self.load_parameters(
            config["parameters_pathname"], config["parameters_setup"]
        )
        self.symbols = self.load_symbols(
            config["symbols_pathname"], config["symbols_setup"]
        )
        self.exchanges = self.load_exchanges(
            config["exchanges_pathname"], config["exchanges_setup"]
        )
        self.exchanges_fees = self.load_fees(
            config["fees_pathname"], config["fees_setup"]
        )

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
        return tuple(parameters.values())

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
        )
        self.logger.info(f"Initializing Search module OK")

class BotCreationError(Exception):
    """Raised when there's an issue during the bot creation process."""

    def __init__(self, message="Failed to create the bot."):
        self.message = message
        super().__init__(self.message)
