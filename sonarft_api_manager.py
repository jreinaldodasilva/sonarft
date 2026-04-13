from decimal import getcontext
from typing import List, Dict, Tuple, Union, Optional
import logging

getcontext().prec = 8

class SonarftApiManager:
    """
    SonarftApiManager class is responsible for managing external API calls.
    """

    def __init__(self, library: str, exchanges: List[str], exchanges_fees: List[Dict[str, Union[str, float]]], logger: Optional[logging.Logger] = None):
        # Initialize logger
        self.logger = logger or logging.getLogger(__name__)

        # Initialize library type (ccxt or ccxtpro)
        self.library = library
        self.load_api_library()

        # Initialize exchanges and their fees
        self.exchanges_list = exchanges
        self.exchanges_fees = exchanges_fees
        self.exchanges_instances = self.load_exchanges_instances(self.exchanges_list)

        self.exchanges_fees = exchanges_fees

        self.markets = {}

    def load_api_library(self):
        """
        Load the appropriate API library based on the library type.
        """

        if self.library == "ccxt":
            import ccxt as apilib
            self.__ccxt__ = True
            self.__ccxtpro__ = False            
        elif self.library == "ccxtpro":
            import ccxt.pro as apilib
            self.__ccxt__ = False
            self.__ccxtpro__ = True

        self.apilib = apilib

    # ###  Manager Calls ***********************************************************************
    async def call_api_method(self, exchange_id, ccxt_method, ccxtpro_method, *args, **kwargs):
        """
        Call the provided method for the given exchange_id.
        """
        result = None

        exchange = self.get_exchange_by_id(exchange_id)
        method = ccxt_method if self.__ccxt__ else ccxtpro_method
        method_call = getattr(exchange, method)

        # self.logger.info(f"Calling method {method} for {exchange}...")
        try:
            if self.__ccxt__:
                self.sync_wait_for_rate_limit(exchange)
                result = method_call(*args, **kwargs)
            else:
                await self.wait_for_rate_limit(exchange)
                result = await method_call(*args, **kwargs)
        except Exception as e:
            print(f"Error calling method {method}: {e}")
        return result

    # ###  Load and Setup ***********************************************************************
    def load_exchanges_instances(self, exchanges: List[str]) -> List:
        """
        Load instances of the provided exchanges.
        """
        return [
            getattr(self.apilib, exchange)({'enableRateLimit': True}) for exchange in exchanges
        ]

    async def load_markets(self, exchange_id):
        """
        Load markets for all exchange instances.
        """
        exchange_markets = await self.call_api_method(exchange_id, 'load_markets', 'load_markets')
        if exchange_markets:
            self.markets.update(exchange_markets)

        return self.markets

    def setAPIKeys(self, exchange_id: str, api_key: str, secret: str, password: str):
        """
        Set the api keys for the given exchange_id.
        """
        exchange = self.get_exchange_by_id(exchange_id)
        exchange.apiKey = api_key
        exchange.secret = secret
        exchange.password = password
        exchange.options['defaultType'] = 'spot'

    # ###  Action ***********************************************************************
    # TODO: Finish implementation
    async def get_balance(self, exchange_id: str) -> Dict[str, Union[str, float]]:
        """
        Get the balance for the given exchange_id.
        """
        balance = await self.call_api_method(exchange_id, 'fetch_balance', 'watch_balance')
        return balance

    async def create_order(self, exchange_id: str, base: str, quote: str, side: str, amount: float, price: float) -> Dict[str, Union[str, float]]:
        """
        Create an order for the given exchange_id, base, quote, side, amount and price.
        """
        try:
            symbol = f"{base}/{quote}"
            order = await self.call_api_method(exchange_id, 'create_order', 'create_order', symbol, 'limit', side, amount, price)
            print("")
            self.logger.info(
                f"Created order {order['id']} on {exchange_id} for {amount} {base} at {price} {quote}")
        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
            order = None
        return order

    async def create_futures_order(self, exchange_id: str, base: str, quote: str, side: str, amount: float, price: float) -> Dict[str, Union[str, float]]:
        """
        Create a futures limit order for the given exchange_id, base, quote, side, amount and price.
        """
        try:
            exchange = self.get_exchange_by_id(exchange_id)
            symbol = f"{base}/{quote}"
            amount_with_precision = exchange.amount_to_precision(
                symbol, amount)
            price_with_precision = exchange.price_to_precision(symbol, price)

            self.logger.info(
                f"amount: {amount_with_precision} - price: {price_with_precision}")
            exchange.options['defaultType'] = 'future'
            order = await self.call_api_method(exchange_id, 'fapiPrivate_post_order', 'fapiPrivate_post_order', symbol, 'LIMIT', side, amount_with_precision, price_with_precision)
            self.logger.info(
                f"Created order {order['orderId']} on {exchange_id} for {amount} {base} at {price} {quote}")
        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
            order = None
        return order

    async def close_exchange(self, exchange_id: str):
        """
        Close exchange instance
        """
        exchange = self.get_exchange_by_id(exchange_id)
        await exchange.close()

    async def watch_orders(self, exchange_id, base, quote):

        symbol = f"{base}/{quote}"
        orders = await self.call_api_method(exchange_id, 'fetch_orders', 'watch_orders', symbol)

        return orders

    # ###  API Get ***********************************************************************
    # TODO: See if its possible(trust) to use api to get fees
    def get_buy_fee(self, exchange_id: str) -> Union[float, None]:
        """
        Get the buy fee for the given exchange_id.
        """
        for exchange_fee in self.exchanges_fees:
            if exchange_fee['exchange'] == exchange_id:
                return exchange_fee['buy_fee']
        return None

    def get_sell_fee(self, exchange_id: str) -> Union[float, None]:
        """
        Get the sell fee for the given exchange_id.
        """
        for exchange_fee in self.exchanges_fees:
            if exchange_fee['exchange'] == exchange_id:
                return exchange_fee['sell_fee']
        return None

    async def get_order_book(self, exchange_id: str, base: str, quote: str) -> Dict[str, Union[str, List[List[float]]]]:
        """
        Get the order book for the given exchange_id, base and quote.
        """
        symbol = f"{base}/{quote}"
        order_book = await self.call_api_method(exchange_id, 'fetch_order_book', 'watch_order_book', symbol)
        return order_book

    async def get_trading_volume(self, exchange_id: str, base: str, quote: str) -> float:
        """
        Get the trading volume for the given exchange_id, base and quote.
        """
        symbol = f"{base}/{quote}"
        trading_volume = await self.call_api_method(exchange_id, 'fetch_ticker', 'watch_ticker', symbol)
        return trading_volume['baseVolume']

    async def get_last_price(self, exchange_id: str, base: str, quote: str) -> float:
        """
        Get the last price for the given exchange_id, base and quote.
        """
        symbol = f"{base}/{quote}"
        last_price = await self.call_api_method(exchange_id, 'fetch_ticker', 'watch_ticker', symbol)
        return last_price['last']

    # TODO: Finish the Implementation - use the timeframe, since and limit
    async def get_ohlcv_history(self, exchange_id: str, base: str, quote: str, timeframe, since, limit) -> List[Dict[str, Union[int, float]]]:
        """
        Get the history for the given exchange_id, base and quote.
        """
        symbol = f"{base}/{quote}"
        history = await self.call_api_method(exchange_id, 'fetch_ohlcv', 'fetch_ohlcv', symbol, timeframe, since, limit)
        
        return history

    # TODO: Finish the Implementation - use the since and limit
    async def get_trades_history(self, exchange_id: str, base: str, quote: str) -> List[Dict[str, Union[int, float]]]:
        """
        Get the history for the given exchange_id, base and quote.
        """
        symbol = f"{base}/{quote}"
        trades_history = await self.call_api_method(exchange_id, 'fetch_trades', 'fetch_trades', symbol)
        return trades_history

    def get_exchange_and_symbol(self, exchange_id: str, base: str, quote: str):
        exchange = self.get_exchange_by_id(exchange_id)
        symbol = f"{base}/{quote}"
        return exchange, symbol

    def get_exchange_by_id(self, exchange_id: str):
        """
        Get the exchange instance by its ID.
        """
        for exchange in self.exchanges_instances:
            if exchange.id == exchange_id:
                return exchange
        return None

    # ###  Support for Trading Strategy Methods ***********************************************************************
    async def get_latest_prices(self, base: str, quote: str, weight) -> List[Tuple[str, float, float, float, str]]:
        """
        Get the latest prices for the given base and quote across all exchanges.
        """
        symbol = f"{base}/{quote}"
        prices = []
        for exchange in self.exchanges_instances:
            try:
                await self.load_markets(exchange.id)
                if symbol not in exchange.markets:
                    self.logger.warning(
                        f"{symbol} is not available on {exchange.id}.")
                    continue

                # Fetch the order book data
                order_book = await self.call_api_method(exchange.id, 'fetch_order_book', 'watch_order_book', symbol)
                if order_book['asks'] is None or order_book['bids'] is None:
                    self.logger.warning(
                        f"Order book for {symbol} in {exchange.id} is invalid: asks or bids is None")
                    continue

                bid_vwap, ask_vwap = self.get_weighted_prices(weight,
                                                                           order_book)

                ticker = await self.call_api_method(exchange.id, 'fetch_ticker', 'watch_ticker', symbol)
                if ticker['ask'] is not None and ticker['ask'] != 0 and ticker['bid'] is not None and ticker['bid'] != 0:
                    prices.append(
                        (exchange.id, bid_vwap, ask_vwap, ticker['last'], symbol))
                else:
                    self.logger.warning(
                        f"Ticker for {symbol} in {exchange.id} is invalid: ask or bid is None or 0")
            except Exception as e:
                self.logger.error(
                    f"Error fetching latest price for {exchange.id} and symbol {symbol}: {e}")
                continue

        return prices

    def get_weighted_prices(self, depth: int, order_book: Dict) -> Tuple[float, float]:
        """
        Calculate the volume-weighted average buy (bid) and sell (ask) prices.

        Parameters:
        depth (int): Depth of the order book to consider for the calculation.
        order_book (Dict): A dictionary containing 'bids' and 'asks' information.

        Returns:
        Tuple[float, float]: The volume-weighted average bid price and ask price.
        """

        bids = order_book['bids'][:depth]
        asks = order_book['asks'][:depth]

        # Calculate the total bid volume and volume-weighted bid price
        total_bid_volume = sum(volume for _, volume in bids)
        bid_vwap = sum(price * volume for price,
                       volume in bids) / total_bid_volume

        # Calculate the total ask volume and volume-weighted ask price
        total_ask_volume = sum(volume for _, volume in asks)
        ask_vwap = sum(price * volume for price,
                       volume in asks) / total_ask_volume

        return bid_vwap, ask_vwap

    # ###  support methods ***********************************************************************

    def sync_wait_for_rate_limit(self, exchange):
        """
        Wait for the rate limit to pass.
        """
        rate_limit = exchange.rateLimit / 1000
        exchange.sleep(rate_limit)

    async def wait_for_rate_limit(self, exchange):
        """
        Wait for the rate limit to pass.
        """
        rate_limit = exchange.rateLimit / 1000
        await exchange.sleep(rate_limit)
