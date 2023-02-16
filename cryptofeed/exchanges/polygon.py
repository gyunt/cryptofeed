import logging
from decimal import Decimal
from typing import Tuple, Dict, List

from yapic import json

from cryptofeed.connection import AsyncConnection
from cryptofeed.connection import RestEndpoint, Routes, WebsocketEndpoint
from cryptofeed.defines import CANDLES, L1_BOOK, POLYGON
from cryptofeed.feed import Feed
from cryptofeed.symbols import Symbol, Symbols
from cryptofeed.types import L1Book, Candle

LOG = logging.getLogger('feedhandler')


class Polygon(Feed):
    id = POLYGON
    websocket_endpoints = [WebsocketEndpoint('wss://socket.polygon.io/forex')]
    rest_endpoints = [RestEndpoint('https://api.polygon.io', routes=Routes('/v3/reference/tickers?market=fx'))]
    valid_candle_intervals = ('1m',)

    websocket_channels = {
        CANDLES: 'CA.{}',
        L1_BOOK: 'C.{}',
    }

    @classmethod
    def is_authenticated_channel(cls, channel: str) -> bool:
        return channel in (CANDLES, L1_BOOK)

    def symbol_mapping(self, refresh=False) -> Dict:
        if Symbols.populated(self.id) and not refresh:
            return Symbols.get(self.id)[0]
        try:
            data = []
            addr = self.rest_endpoints[0].route('instruments')

            while True:
                LOG.debug("%s: reading symbol information from %s", self.id, addr)
                addr = f"{addr}&limit=1000&apiKey={self.key_id}"
                response = self.http_sync.read(addr, json=True, uuid=self.id)
                data = data + response['results']

                if 'next_url' in response:
                    addr = response['next_url']
                else:
                    break

            syms, info = self._parse_symbol_data(data)
            Symbols.set(self.id, syms, info)
            return syms
        except Exception as e:
            LOG.error("%s: Failed to parse symbol information: %s", self.id, str(e), exc_info=True)
            raise

    @classmethod
    def _parse_symbol_data(cls, data: List) -> Tuple[Dict, Dict]:
        ret = {}
        info = {'instrument_type': {}}

        for ticker in data:
            base_curr, quote_curr = ticker['base_currency_symbol'], ticker['currency_symbol']
            s = Symbol(base_curr, quote_curr)
            ret[s.normalized] = f"{base_curr}/{quote_curr}"
            info['instrument_type'][s.normalized] = s.type
        return ret, info

    async def _quote(self, quote: dict, timestamp: float):
        book = L1Book(
            self.id,
            self.exchange_symbol_to_std_symbol(quote['p']),
            quote['b'],
            Decimal(0),
            quote['a'],
            Decimal(0),
            self.timestamp_normalize(quote['t']),
            raw=quote
        )
        await self.callback(L1_BOOK, book, timestamp)

    async def _candle(self, msg: dict, timestamp: float):
        """
        {
          "ev": "CA",               // The event type.
          "pair": "USD/EUR",        // The currency pair.
          "o": 0.8687,              // The open price for this aggregate window.
          "c": 0.86889,             // The close price for this aggregate window.
          "h": 0.86889,             // The high price for this aggregate window.
          "l": 0.8686,              // The low price for this aggregate window.
          "v": 20,                  // The volume of trades during this aggregate window.
          "s": 1539145740000        // The start time for this aggregate window in Unix Milliseconds.
                                    // e, The end time for this aggregate window in Unix Milliseconds. (missing)
        }
        """
        c = Candle(self.id,
                   self.exchange_symbol_to_std_symbol(msg['pair']),
                   self.timestamp_normalize(msg['s']),
                   self.timestamp_normalize(msg['s']) + 60,
                   "1m",
                   0,
                   msg['o'],
                   msg['c'],
                   msg['h'],
                   msg['l'],
                   Decimal(msg['v']),
                   None,
                   self.timestamp_normalize(msg['s']),
                   raw=msg)
        await self.callback(CANDLES, c, timestamp)

    async def message_handler(self, msg: str, conn, timestamp: float):
        messages = json.loads(msg, parse_float=Decimal)

        for msg in messages:
            if 'ev' in msg:
                if msg['ev'] == 'status':
                    if msg['status'] == 'connected':
                        LOG.info("%s: Connected to Polygon", conn.uuid)
                    elif msg['status'] == 'auth_success':
                        LOG.info("%s: Authentication successful", conn.uuid)
                    elif msg['status'] == 'success':
                        LOG.info("%s: Subscription to %s successful", conn.uuid, msg['message'])
                    else:
                        LOG.warning("%s: Subscription to %s failed: %s", conn.uuid, msg['message'], msg)
                elif msg['ev'] == 'C':
                    await self._quote(msg, timestamp)
                elif msg['ev'] == 'CA':
                    await self._candle(msg, timestamp)
                else:
                    LOG.warning("%s: Unknown message in msg_dict: %s", conn.uuid, msg)
            else:
                LOG.warning("%s: Unknown message in msg_dict: %s", conn.uuid, msg)

    async def authenticate(self, conn: AsyncConnection):
        if self.requires_authentication:
            auth = {
                "action": "auth",
                "params": self.key_id,
            }
            await conn.write(json.dumps(auth))
            LOG.debug(f"{conn.uuid}: Authenticating with message: {auth}")
        return conn

    async def subscribe(self, conn: AsyncConnection):
        for channel in self.subscription:
            pairs = self.subscription[channel]

            channels = [f"{channel.format('C:' + pair.replace('/', '-'))}"
                        for pair in pairs]

            message = {"action": "subscribe",
                       "params": ",".join(channels)}
            await conn.write(json.dumps(message))

    @classmethod
    def timestamp_normalize(cls, ts: float) -> float:
        return ts / 1000.0
