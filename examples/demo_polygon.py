#!/usr/bin/env python

from cryptofeed import FeedHandler
from cryptofeed.defines import BYBIT, ORDER_INFO, FILLS


def main():
    f = FeedHandler(config="config.yaml")
    f.add_feed(BYBIT,
               channels=[FILLS, ORDER_INFO],
               symbols=["ETH-USD-21Z31", "EOS-USD-PERP", "SOL-USDT-PERP"],
               callbacks={FILLS: fill, ORDER_INFO: order},
               timeout=-1)

    f.run()


if __name__ == '__main__':
    main()
