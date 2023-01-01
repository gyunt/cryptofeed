#!/usr/bin/env python

import logging

from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES, UPBIT, L2_BOOK

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


async def book(book, receipt_timestamp):
    print(
        f'Book received at {receipt_timestamp} for {book.exchange} - {book.symbol}, with {len(book.book)} entries. Top of book prices: {book.book.asks.index(0)[0]} - {book.book.bids.index(0)[0]}')
    if book.delta:
        print(f"Delta from last book contains {len(book.delta[BID]) + len(book.delta[ASK])} entries.")
    if book.sequence_number:
        assert isinstance(book.sequence_number, int)


def main():
    f = FeedHandler(config="config.yaml")
    f.add_feed(UPBIT,
               sandbox=True,
               channels=[TRADES, L2_BOOK],
               symbols=["BTC-KRW"],
               callbacks={L2_BOOK: book},
               timeout=-1)
    f.run()


if __name__ == '__main__':
    main()
