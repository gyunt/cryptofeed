import logging
from typing import Tuple, Dict, List

from cryptofeed.connection import RestEndpoint, Routes, WebsocketEndpoint
from cryptofeed.defines import CANDLES, L1_BOOK, POLYGON
from cryptofeed.feed import Feed
from cryptofeed.symbols import Symbol, Symbols

LOG = logging.getLogger('feedhandler')


class Polygon(Feed):
    id = POLYGON
    websocket_endpoints = [WebsocketEndpoint('wss://socket.polygon.io/forex', sandbox=None)]
    rest_endpoints = [RestEndpoint('https://api.polygon.io', routes=Routes('/v3/reference/tickers?market=fx'))]
    valid_candle_intervals = ('1m',)

    websocket_channels = {
        CANDLES: 'CA.{}',
        L1_BOOK: 'C.{}',
    }

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
            ret[s.normalized] = ticker['ticker']
            info['instrument_type'][s.normalized] = s.type
        return ret, info
