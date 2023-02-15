import logging

from cryptofeed.connection import RestEndpoint, Routes, WebsocketEndpoint
from cryptofeed.defines import CANDLES, L1_BOOK, POLYGON
from cryptofeed.feed import Feed

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
