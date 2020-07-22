import pytest
import logging
from utils import seek_interval_start, Timeframe

logging.basicConfig(level=logging.DEBUG)


@pytest.mark.parametrize(
    "input_seconds,timeframe,expected",
    [
        (1439051596.2308, Timeframe.M1, 1439051640),
        (1558265222.6792, Timeframe.M5, 1558265400.0),
        (1518212517.6792, Timeframe.M30, 1518213600),
        (1552265427.6711, Timeframe.H1, 1552266000),
        (1352059731.14, Timeframe.H5, 1352070000.0),
        (1514933121.7418, Timeframe.H5, 1514934000.0),
        (1452083134.14, Timeframe.D1, 1452124800.0),
        (1458002231.14, Timeframe.D10, 1458432000.0),
    ],
)
def test_seek_interval_start(input_seconds, timeframe, expected):
    assert seek_interval_start(input_seconds, timeframe) == expected
