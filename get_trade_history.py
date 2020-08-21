#!/usr/bin/env python

import logging
import sys
import time
import csv
import pathlib

from crypto.utils import get_data_path
from crypto.utils import consts
from crypto.utils import pairs
import crypto.kraken as kraken

FILE_END_SEEK_OFFSET = -1024


def get_last_trade_index(csv_file_path):
    logging.debug(csv_file_path)

    if not pathlib.Path(csv_file_path).exists():
        return str(0)

    with open(csv_file_path, "rb") as f:
        try:
            f.seek(FILE_END_SEEK_OFFSET, 2)
        except:
            return str(0)

        last_trade = f.readlines()[-1].decode()
        last_timestamp = str(int(float(last_trade.split(",")[2]) * 10000) * 10 ** 5)
        logging.debug("Last trade from file %s: %s", csv_file_path, str(last_timestamp))
        return last_timestamp


def get_all_trades(pair=pairs.PAIR_XBT_USD, append=True):
    c = kraken.API()
    r = c.query_public("Time")

    csv_file_path = get_data_path(pair + consts.TRADES_AFFIX)
    logging.debug(csv_file_path)

    flag = "a" if append else "w+"
    with open(csv_file_path, flag) as f:
        writer = csv.writer(f)
        if not append:
            writer.writerow(
                ["price", "volume", "time", "buy/sell", "market/limit", "misc"]
            )

        last = get_last_trade_index(csv_file_path)
        logging.info(f"Getting all trades for {pair} as of time {last}")

        logging.info(f"starting retrieval from timestamp {last}")
        count = 0
        while True:
            if c.at_api_limit():
                continue
            try:
                r = c.query_public("Trades", data={"pair": pair, "since": last})
            except kraken.RateLimitError:
                logging.warning("Rate limit hit. Sleeping for 15 seconds...")
                time.sleep(15)
                continue

            last = r["last"]
            trades = r[pair]
            count += len(trades)
            logging.info("Received %s trades", count)
            if not trades:
                break
            for trade in trades:
                writer.writerow(trade)

        logging.info("Finished getting trades for %s", pair)
        logging.info("Total number of trades: %d", count)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    get_all_trades(pairs.PAIR_XBT_USD)
    # get_last_trade_index(PAIR_XBT_USD)
    get_all_trades(pairs.PAIR_ETH_USD)
