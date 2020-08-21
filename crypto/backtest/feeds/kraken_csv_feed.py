from backtrader.feeds import GenericCSVData


class KrakenCSVData(GenericCSVData):
    """Kraken csv datafeed for backtrader"""

    params = (
        ("dtformat", 2),
        ("openinterest", -1),
    )
