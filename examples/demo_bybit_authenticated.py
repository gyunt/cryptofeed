#!/usr/bin/env python

import logging

from cryptofeed import FeedHandler
from cryptofeed.defines import BYBIT, TRADES

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
websockets_logger = logging.getLogger('websockets')
websockets_logger.setLevel(logging.DEBUG)
websockets_logger.addHandler(stream_handler)

feedhandler_logger = logging.getLogger('feedhandler')
feedhandler_logger.setLevel(logging.DEBUG)
feedhandler_logger.addHandler(stream_handler)


async def order(feed, symbol, data: dict, receipt_timestamp):
    print(f"{feed}: {symbol}: Order update: {data}")


async def fill(feed, symbol, data: dict, receipt_timestamp):
    print(f"{feed}: {symbol}: Fill update: {data}")


async def trade(trade, receipt):
    print("Trade", trade)


def main():
    f = FeedHandler(config="config.yaml")
    f.add_feed(BYBIT,
               sandbox=True,
               channels=[TRADES],
               symbols=["BTC-USDC-PERP"],
               callbacks={TRADES: trade},
               timeout=-1)
    f.run()


if __name__ == '__main__':
    main()
