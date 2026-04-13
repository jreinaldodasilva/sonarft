from typing import List, Dict, Tuple, Union, Optional
import asyncio
import logging
import time as _time


# Candle duration in seconds per timeframe — used as cache TTL
_TIMEFRAME_SECONDS: Dict[str, int] = {
    '1m': 60, '3m': 180, '5m': 300, '15m': 900,
    '30m': 1800, '1h': 3600, '4h': 14400, '1d': 86400,
}

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

        self.markets: Dict[str, dict] = {}
        self._ohlcv_cache: Dict[str, Tuple[float, list]] = {}  # key -> (expires_at, data)

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

        try:
            if self.__ccxt__:
                await self.wait_for_rate_limit(exchange)
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: method_call(*args, **kwargs))
            else:
                await self.wait_for_rate_limit(exchange)
                result = await method_call(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error calling method {method}: {e}")
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
        """Load and cache markets for a single exchange. Safe to call multiple times."""
        if exchange_id in self.markets:
            return self.markets[exchange_id]
        exchange_markets = await self.call_api_method(exchange_id, 'load_markets', 'load_markets')
        if exchange_markets:
            self.markets[exchange_id] = exchange_markets
        return self.markets.get(exchange_id, {})

    async def load_all_markets(self):
        """Load markets for all configured exchanges at startup."""
        await asyncio.gather(*[
            self.load_markets(exchange.id)
            for exchange in self.exchanges_instances
        ])

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
            self.logger.info(f"Created order {order['id']} on {exchange_id} for {amount} {base} at {price} {quote}")
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

    async def get_ohlcv_history(self, exchange_id: str, base: str, quote: str, timeframe, since, limit) -> List:
        """Fetch OHLCV history with a per-candle TTL cache."""
        symbol = f"{base}/{quote}"
        cache_key = f"{exchange_id}:{symbol}:{timeframe}:{limit}"
        ttl = _TIMEFRAME_SECONDS.get(timeframe, 60)
        now = _time.monotonic()
        cached = self._ohlcv_cache.get(cache_key)
        if cached and now < cached[0]:
            return cached[1]
        history = await self.call_api_method(exchange_id, 'fetch_ohlcv', 'fetch_ohlcv', symbol, timeframe, since, limit)
        if history:
            self._ohlcv_cache[cache_key] = (now + ttl, history)
        return history or []

    # TODO: Finish the Implementation - use the since and limit
    async def get_trades_history(self, exchange_id: str, base: str, quote: str) -> List[Dict[str, Union[int, float]]]:
        """
        Get the history for the given exchange_id, base and quote.
        """
        symbol = f"{base}/{quote}"
        trades_history = await self.call_api_method(exchange_id, 'fetch_trades', 'fetch_trades', symbol)
        return trades_history

    def get_symbol_precision(self, exchange_id: str, base: str, quote: str) -> Optional[Dict]:
        """Return precision rules for a symbol from loaded market data, or None if unavailable."""
        symbol = f"{base}/{quote}"
        market = self.markets.get(exchange_id, {}).get(symbol)
        if not market:
            return None
        precision = market.get('precision', {})
        limits = market.get('limits', {})
        price_prec = precision.get('price')
        amount_prec = precision.get('amount')
        if price_prec is None or amount_prec is None:
            return None
        # Convert to decimal places if given as a tick size (e.g. 0.01 -> 2)
        def _to_dp(v):
            if v is None:
                return 8
            if isinstance(v, int):
                return v
            s = f"{v:.10f}".rstrip('0')
            return len(s.split('.')[-1]) if '.' in s else 0
        return {
            'prices_precision': _to_dp(price_prec),
            'buy_amount_precision': _to_dp(amount_prec),
            'sell_amount_precision': _to_dp(amount_prec),
            'cost_precision': 8,
            'fee_precision': 8,
        }

    def get_exchange_by_id(self, exchange_id: str):
        """
        Get the exchange instance by its ID.
        """
        for exchange in self.exchanges_instances:
            if exchange.id == exchange_id:
                return exchange
        return None

    async def get_latest_prices(self, base: str, quote: str, weight) -> List[Tuple[str, float, float, float, str]]:
        """Get the latest prices for the given base and quote across all exchanges."""
        symbol = f"{base}/{quote}"
        prices = []

        async def _fetch_exchange(exchange):
            try:
                cached = self.markets.get(exchange.id, {})
                if symbol not in cached:
                    self.logger.warning(f"{symbol} is not available on {exchange.id}.")
                    return None
                order_book, ticker = await asyncio.gather(
                    self.call_api_method(exchange.id, 'fetch_order_book', 'watch_order_book', symbol),
                    self.call_api_method(exchange.id, 'fetch_ticker', 'watch_ticker', symbol),
                )
                if order_book is None or order_book['asks'] is None or order_book['bids'] is None:
                    self.logger.warning(f"Order book for {symbol} in {exchange.id} is invalid.")
                    return None
                bid_vwap, ask_vwap = self.get_weighted_prices(weight, order_book)
                if ticker['ask'] and ticker['ask'] != 0 and ticker['bid'] and ticker['bid'] != 0:
                    return (exchange.id, bid_vwap, ask_vwap, ticker['last'], symbol)
                self.logger.warning(f"Ticker for {symbol} in {exchange.id} is invalid.")
                return None
            except Exception as e:
                self.logger.error(f"Error fetching latest price for {exchange.id} {symbol}: {e}")
                return None

        results = await asyncio.gather(*[_fetch_exchange(ex) for ex in self.exchanges_instances])
        prices = [r for r in results if r is not None]
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

        total_bid_volume = sum(volume for _, volume in bids)
        total_ask_volume = sum(volume for _, volume in asks)

        if total_bid_volume == 0 or total_ask_volume == 0:
            return 0.0, 0.0

        bid_vwap = sum(price * volume for price, volume in bids) / total_bid_volume
        ask_vwap = sum(price * volume for price, volume in asks) / total_ask_volume

        return bid_vwap, ask_vwap

    # ###  support methods ***********************************************************************

    async def wait_for_rate_limit(self, exchange):
        rate_limit = exchange.rateLimit / 1000
        await exchange.sleep(rate_limit)
