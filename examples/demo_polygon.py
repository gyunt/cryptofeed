import logging

from cryptofeed import FeedHandler
from cryptofeed.defines import L1_BOOK, CANDLES
from cryptofeed.exchanges import Polygon

logger = logging.getLogger('feedhandler')
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(stream_handler)


async def l1_book(l1, receipt_timestamp):
    print(f"{receipt_timestamp - l1.timestamp} l1_book update received at {receipt_timestamp}: {l1}")


async def candle(candle, receipt_timestamp):
    print(f"{receipt_timestamp - candle.timestamp} candle update received at {receipt_timestamp}: {candle}")


def main():
    path_to_config = 'config.yaml'
    polygon = Polygon(config=path_to_config,
                      channels=[CANDLES],
                      callbacks={CANDLES: candle},
                      symbols=['USD-KRW'], )

    f = FeedHandler()
    f.add_feed(polygon)
    f.run()


if __name__ == '__main__':
    main()
