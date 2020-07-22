import logging
import sys
import time
import datetime
import threading
import statistics

from utils import get_data_path
from utils import pairs as pr
import kraken
import dao

logging.basicConfig(level=logging.INFO)
PAIR_SLEEP_INTERVAL = 3


def process_raw_orderbook(pair, res):
    snapshot_epoch = time.time()
    logging.info("Processing raw orderbook for snapshot_epoch %d", snapshot_epoch)
    columns = []
    for ask in res["asks"]:
        price = float(ask[0])
        volume = float(ask[1])
        order_epoch = ask[2]
        columns.append([pair, price, volume, True, order_epoch, snapshot_epoch])
    for bid in res["bids"]:
        price = float(bid[0])
        volume = float(bid[1])
        order_epoch = bid[2]
        columns.append([pair, price, volume, False, order_epoch, snapshot_epoch])

    return columns


if __name__ == "__main__":
    api = kraken.API()
    dao = dao.DAO()

    pairs = [pr.PAIR_XBT_USD, pr.PAIR_ETH_USD]
    while True:
        for pair in pairs:
            res = api.get_orderbook(pair)
            columns = process_raw_orderbook(pair, res)
            dao.bulk_insert_raw_orderbook(columns)
