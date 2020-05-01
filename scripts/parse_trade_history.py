import logging
import csv
from datetime import datetime

from utils import get_data_path, Timeframe, seek_interval_start, consts, pairs

INTERPOLATE = True

def aggregate_ohlcv(trades):
    logging.debug(f'Parsing {len(trades)} items in aggregate')
    o = float(trades[0][0])
    h = -float('inf')
    l = float('inf')
    c = float(trades[-1][0])
    v = 0.0
    for row in trades:
        logging.debug(f'{row}, {datetime.utcfromtimestamp(float(row[2]))}')
        h = max(h, float(row[0]))
        l = min(l, float(row[0]))
        v = v + float(row[1])
    return [o, h, l, c, v]
    

def resample_trade_data(pair=pairs.PAIR_XBT_USD, timeframe=Timeframe.M5):
    logging.info(f'Analyzing trade data for pair {pair}, with interval {timeframe}')

    raw_data_csv_path = get_data_path(pair + consts.TRADES_AFFIX)
    ohlcv_output_csv_path = get_data_path(pair + '_' + str(timeframe) + consts.OHLCV_AFFIX)
    logging.info(f'raw data: {raw_data_csv_path}, output ohlcv data: {ohlcv_output_csv_path}')
    logging.debug(timeframe.to_seconds())

    interval_start = None
    aggregate = []
    with open(raw_data_csv_path, 'r') as raw_f:
        with open(ohlcv_output_csv_path, 'w') as output_f:
            reader = csv.reader(raw_f)
            ohlcv_writer = csv.writer(output_f)
            for row in reader:
                # process each raw trade datapoint
                timestamp_seconds = float(row[2]) # this is in the format seconds.10^-4 seconds
                if not interval_start:
                    interval_start = seek_interval_start(timestamp_seconds, timeframe)

                if timestamp_seconds <= interval_start:
                    aggregate.append(row)
                else:
                    ohlcv = aggregate_ohlcv(aggregate)
                    logging.debug(f'ohlcv: {ohlcv}, interval ending in: {datetime.utcfromtimestamp(interval_start)}')
                    ohlcv.insert(0, interval_start)
                    ohlcv_writer.writerow(ohlcv)
                    aggregate.clear()
                    aggregate.append(row)
                    next_interval_start = seek_interval_start(timestamp_seconds, timeframe)

                    if INTERPOLATE:
                        interval_start += timeframe.to_seconds()
                        skipped_periods = int((next_interval_start - interval_start) / timeframe.to_seconds())
                        prev_close = ohlcv[3]
                        next_open = float(row[0])
                        jump = (next_open - prev_close) / (skipped_periods + 1)
                        logging.debug(f'Interpolating for {skipped_periods} periods, prev_close: {prev_close}, next_open: {next_open}, jump: {jump}')
                        interpolated_ohlcv = prev_close

                        while interval_start < next_interval_start:
                            #write row for empty aggregate
                            #or not... maybe we can interpolate here for skipped values
                            #logging.info(f'ohlcv: {ohlcv}, interval ending in: {datetime.utcfromtimestamp(interval_start)}')
                            interpolated_ohlcv += jump
                            to_write = [interpolated_ohlcv for _ in range(5)]
                            to_write.insert(0, interval_start)
                            ohlcv_writer.writerow(to_write)
                            interval_start += timeframe.to_seconds()
                    
                    else:
                        interval_start = next_interval_start

                    assert(interval_start == next_interval_start)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    resample_trade_data(pairs.PAIR_ETH_USD, Timeframe.M1)
    resample_trade_data(pairs.PAIR_XBT_USD, Timeframe.M1)