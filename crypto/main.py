from __future__ import absolute_import, division, print_function, unicode_literals

import backtrader as bt
from datetime import datetime

from utils import get_data_path, consts, pairs
from backtest.feeds.kraken_csv_feed import KrakenCSVData
from backtest.strategies.test_strategy import TestStrategy


def test_backtrader():
    cerebro = bt.Cerebro()

    # starting cash
    cerebro.broker.set_cash(100000)

    # add strategy
    cerebro.addstrategy(TestStrategy)

    # add datas
    datapath = get_data_path(pairs.PAIR_XBT_USD + "_M1" + consts.OHLCV_AFFIX)
    data = KrakenCSVData(
        dataname=datapath,
        fromdate=datetime(2018, 1, 1),
        timeframe=bt.TimeFrame.Minutes,
        compression=1,
    )

    # plain add
    # cerebro.adddata(data)

    # resampling
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=60)

    # sizer
    # TODO: figure out fractional sizing/commisions for crypto
    cerebro.addsizer(bt.sizers.PercentSizer, percents=10)

    # commision
    cerebro.broker.setcommission(commission=0.001)

    print(f"Starting portfolio val: {cerebro.broker.getvalue():.2f}")

    cerebro.run()

    print(f"Ending portfolio val: {cerebro.broker.getvalue():.2f}")

    cerebro.plot(style="bar")


if __name__ == "__main__":
    test_backtrader()
