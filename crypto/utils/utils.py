import pathlib
from datetime import datetime
import math
import logging
from enum import Enum


def get_data_path(filename):
    """ get_data_path takes a filename and turns it into an absolute path in the data folder """
    data_directory = str(pathlib.Path(__file__).parent.parent.absolute()) + "/data/"
    return data_directory + filename


def seek_interval_start(seconds, timeframe):
    """
    seek_interval_start takes in a unix epoch timestamp
    and returns the closest aligned timeframe after the timestamp
    """
    try:
        t = datetime.utcfromtimestamp(seconds)
        logging.debug(f"seek interval input: {t}")
    except Exception as e:
        logging.error(e)
        return
    # seek to the closes interval AFTER seconds
    seconds = math.ceil(seconds)
    discard = seconds % timeframe.to_seconds()
    seconds = seconds - discard + timeframe.to_seconds()
    logging.debug(f"output: {datetime.utcfromtimestamp(seconds)}")
    return float(seconds)


class Timeframe(Enum):
    """
    Timeframe is a utility class for simplifying unification of timeframe for data candles
    Contains:
    M1
    M5
    M30
    H1
    H5
    D1
    D10
    """

    M1 = 1
    M5 = 2
    M30 = 3
    H1 = 4
    H5 = 5
    D1 = 6
    D10 = 7

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def to_seconds(self):
        switcher = {
            Timeframe.M1: 60,
            Timeframe.M5: 300,
            Timeframe.M30: 1800,
            Timeframe.H1: 3600,
            Timeframe.H5: 18000,
            Timeframe.D1: 86400,
            Timeframe.D10: 864000,
        }
        return switcher[self]
